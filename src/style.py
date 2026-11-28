"""Visual + voice styles for Tech 101.

Every new episode picks ONE style and draws everything through it, so the same scene code
works in any style:

    import style
    S = style.get("chalk")                 # long-form, 1920x1080
    V = style.get("chalk", vertical=True)  # Short, 1080x1920

Styles (rotate in this order, see RUNBOOK "Styles"):
    blueprint  dark navy, cyan/amber, Inter;          voice am_michael (US male),  measured
    chalk      green chalkboard, hand-drawn lines, Kalam; voice bm_george (UK male), calm lecture
    paper      cream paper cut-outs, soft shadows, Fredoka/Nunito; voice af_heart (US female), upbeat

Semantic colours (same names in every style):
    BG, PANEL, LINE, TXT, DIM, ACCENT, HILITE, GOOD, BAD, EXTRA, BLUE, ON_ACCENT
    (legacy aliases: CYAN=ACCENT, AMBER=HILITE, GREEN=GOOD, RED=BAD)
"""
import math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def prog(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def pop(t, a, b):
    """0 -> 1 with a small overshoot (paper cut-outs popping in). Use as a scale or offset factor."""
    x = clamp((t - a) / (b - a)) if b > a else float(t >= a)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def grow(pts, k):
    """Return the first fraction k (0..1) of a polyline, by length: for lines that draw themselves."""
    if k >= 1 or len(pts) < 2: return list(pts)
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:])]
    target, out = sum(seg) * max(0.0, k), [pts[0]]
    for (a, b), L in zip(zip(pts[:-1], pts[1:]), seg):
        if target <= L:
            u = target / L if L else 0
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)); return out
        out.append(b); target -= L
    return out
def mix(c1, c2, k): return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))
def wrap(s, n):
    out, cur = [], ""
    for wd in s.split():
        if len(cur) + len(wd) + 1 > n and cur: out.append(cur); cur = wd
        else: cur = (cur + " " + wd).strip()
    if cur: out.append(cur)
    return out

INTER = "/usr/share/fonts/opentype/inter/"
EXTRA = "/usr/share/fonts/truetype/extra/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WEIGHTS = {"Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900}

PALETTES = {
    "blueprint": dict(BG=(11, 16, 32), PANEL=(22, 30, 54), LINE=(52, 66, 104), TXT=(230, 236, 250), DIM=(130, 144, 180),
                      ACCENT=(64, 214, 255), HILITE=(255, 184, 64), GOOD=(90, 230, 140), BAD=(255, 96, 96),
                      EXTRA=(180, 140, 255), BLUE=(90, 150, 255), ON_ACCENT=(11, 16, 32)),
    "chalk":     dict(BG=(38, 62, 50), PANEL=(48, 76, 62), LINE=(200, 212, 202), TXT=(238, 238, 230), DIM=(160, 182, 168),
                      ACCENT=(126, 204, 240), HILITE=(250, 224, 112), GOOD=(156, 232, 150), BAD=(250, 140, 140),
                      EXTRA=(206, 176, 244), BLUE=(140, 176, 250), ON_ACCENT=(38, 62, 50)),
    "paper":     dict(BG=(247, 241, 229), PANEL=(255, 253, 248), LINE=(64, 60, 78), TXT=(40, 42, 66), DIM=(122, 118, 134),
                      ACCENT=(0, 146, 158), HILITE=(240, 128, 32), GOOD=(52, 160, 84), BAD=(220, 64, 64),
                      EXTRA=(128, 88, 200), BLUE=(56, 104, 216), ON_ACCENT=(255, 253, 248)),
}
VOICES = {  # (voice, speed for long-form, lang); Shorts run 8% faster
    "blueprint": ("am_michael", 1.0, "en-us"),
    "chalk": ("bm_george", 0.95, "en-gb"),
    "paper": ("af_heart", 1.04, "en-us"),
}
ORDER = ["blueprint", "chalk", "paper"]

_cache = {}

class Style:
    def __init__(self, name, vertical=False):
        assert name in PALETTES, name
        self.NAME, self.vertical = name, vertical
        self.W, self.H, self.FPS = (1080, 1920, 30) if vertical else (1920, 1080, 30)
        for k, v in PALETTES[name].items(): setattr(self, k, v)
        self.CYAN, self.AMBER, self.GREEN, self.RED = self.ACCENT, self.HILITE, self.GOOD, self.BAD
        v, sp, lang = VOICES[name]
        self.VOICE, self.SPEED, self.LANG = v, round(sp * (1.08 if vertical else 1.0), 3), lang
        self.SAFE_L, self.SAFE_R, self.SAFE_B = (70, 930, 1500) if vertical else (80, 1840, 1080)
        self._fc = {}

    # ---------- fonts and colour ----------
    def font(self, size, w="SemiBold", mono=False):
        key = (size, w, mono)
        if key in self._fc: return self._fc[key]
        if mono:
            f = ImageFont.truetype(MONO_B if w in ("Bold", "ExtraBold", "Black") else MONO, size)
        elif self.NAME == "blueprint":
            f = ImageFont.truetype(INTER + f"Inter-{w}.otf", size)
        elif self.NAME == "chalk":
            fn = {"Light": "Kalam-Light.ttf", "Regular": "Kalam-Regular.ttf", "Medium": "Kalam-Regular.ttf"}.get(w, "Kalam-Bold.ttf")
            f = ImageFont.truetype(EXTRA + fn, int(size * 1.08))
        else:  # paper: Fredoka for heavy weights (headings), Nunito for body
            heavy = WEIGHTS.get(w, 600) >= 700
            f = ImageFont.truetype(EXTRA + ("Fredoka%5Bwdth,wght%5D.ttf" if heavy else "Nunito%5Bwght%5D.ttf"), size)
            try:
                f.set_variation_by_axes([min(700, WEIGHTS.get(w, 600) - 100), 100] if heavy else [WEIGHTS.get(w, 600)])
            except Exception:
                pass
        self._fc[key] = f
        return f

    def fade(self, c, k): return mix(self.BG, c, clamp(k))
    def textlen(self, d, s, size=40, w="SemiBold", mono=False): return d.textlength(s, font=self.font(size, w, mono))

    def text(self, d, xy, s, size=40, col=None, w="SemiBold", anchor="la", mono=False, k=1.0):
        if k <= 0.01: return
        d.text(xy, s, font=self.font(size, w, mono), fill=self.fade(col or self.TXT, k), anchor=anchor)

    # ---------- strokes ----------
    def _wobble(self, pts, closed=False):
        """Chalk: break each segment into ~30 px pieces with a small, deterministic sideways wobble."""
        if closed: pts = list(pts) + [pts[0]]
        out = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(L / 30))
            nx, ny = (-(y1 - y0) / L, (x1 - x0) / L) if L else (0, 0)
            seed = (x0 * 0.013 + y0 * 0.021 + x1 * 0.017 + y1 * 0.011)
            for i in range(n + (1 if (x1, y1) == pts[-1] else 0)):
                u = i / n
                a = 2.2 * math.sin(u * math.pi) * (math.sin(u * 6.1 + seed * 7) * 0.7 + math.sin(u * 13.7 + seed * 3) * 0.3)
                out.append((x0 + (x1 - x0) * u + nx * a, y0 + (y1 - y0) * u + ny * a))
        return out

    def line(self, d, pts, col=None, width=5, k=1.0, closed=False):
        if k <= 0.01 or len(pts) < 2: return
        c = self.fade(col or self.LINE, k)
        pts = [tuple(p) for p in pts]
        if self.NAME == "chalk":
            wp = self._wobble(pts, closed)
            d.line(wp, fill=c, width=width, joint="curve")
            d.line([(x + 1.2, y - 0.8) for x, y in wp], fill=mix(self.BG, c, 0.55), width=max(1, width // 2), joint="curve")
        else:
            if closed: pts = pts + [pts[0]]
            d.line(pts, fill=c, width=width, joint="curve")

    def arrow(self, d, a, b, col=None, width=5, k=1.0):
        if k <= 0.01: return
        col = col or self.TXT
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        hl = 14 + width * 1.6
        base = (b[0] - hl * 0.8 * math.cos(ang), b[1] - hl * 0.8 * math.sin(ang))
        self.line(d, [a, base], col, width, k)
        p = [b, (b[0] - hl * math.cos(ang - .45), b[1] - hl * math.sin(ang - .45)),
             (b[0] - hl * math.cos(ang + .45), b[1] - hl * math.sin(ang + .45))]
        if self.NAME == "chalk":
            self.line(d, [p[1], b, p[2]], col, width, k)
        else:
            d.polygon(p, fill=self.fade(col, k))

    def _rr_points(self, xy, r, steps=6):
        x0, y0, x1, y1 = xy
        r = max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(steps + 1):
                a = math.radians(a0 + 90 * i / steps)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def shadow(self, d, xy, r=18, k=1.0, ellipse=False):
        if self.NAME != "paper" or k <= 0.01: return
        x0, y0, x1, y1 = xy
        c = mix(self.BG, (90, 70, 50), 0.22 * clamp(k))
        if ellipse: d.ellipse([x0 + 6, y0 + 9, x1 + 6, y1 + 9], fill=c)
        else: d.rounded_rectangle([x0 + 6, y0 + 9, x1 + 6, y1 + 9], r, fill=c)

    def box(self, d, xy, col=None, outline=None, r=18, width=3, k=1.0, shadow=True):
        """Filled panel. col = fill (default PANEL), outline = border colour (default LINE)."""
        if k <= 0.01: return
        col = col or self.PANEL
        x0, y0, x1, y1 = xy
        if self.NAME == "chalk":
            d.rounded_rectangle(xy, r, fill=self.fade(col, k))
            self.line(d, self._rr_points(xy, r), outline or self.LINE, max(3, width), k, closed=True)
        elif self.NAME == "paper":
            if shadow: self.shadow(d, xy, r, k)
            d.rounded_rectangle(xy, r, fill=self.fade(col, k),
                                outline=self.fade(outline, k) if outline else None, width=width if outline else 0)
        else:
            d.rounded_rectangle(xy, r, fill=self.fade(col, k), outline=self.fade(outline or self.LINE, k), width=width)

    def circle(self, d, c, r, col=None, outline=None, width=4, k=1.0, shadow=True):
        if k <= 0.01: return
        x, y = c; xy = [x - r, y - r, x + r, y + r]
        if self.NAME == "paper" and shadow and col: self.shadow(d, xy, k=k, ellipse=True)
        if col: d.ellipse(xy, fill=self.fade(col, k))
        if outline:
            if self.NAME == "chalk":
                n = max(16, int(r / 4))
                self.line(d, [(x + r * math.cos(2 * math.pi * i / n), y + r * math.sin(2 * math.pi * i / n)) for i in range(n)],
                          outline, width, k, closed=True)
            else:
                d.ellipse(xy, outline=self.fade(outline, k), width=width)

    def chip(self, d, x, y, w, h, label, sub=None, col=None, k=1.0, pins=True):
        col = col or self.ACCENT
        if pins and k > 0.01:
            pc = self.DIM if self.NAME != "paper" else self.LINE
            for i in range(6):
                px = x + 30 + i * (w - 60) / 5
                d.rectangle([px - 6, y - 16, px + 6, y], fill=self.fade(pc, k))
                d.rectangle([px - 6, y + h, px + 6, y + h + 16], fill=self.fade(pc, k))
        if self.NAME == "paper":
            self.box(d, (x, y, x + w, y + h), col, None, 18, 0, k)
            self.text(d, (x + w / 2, y + h / 2 - (18 if sub else 0)), label, 40, self.ON_ACCENT, "Bold", "mm", k=k)
            if sub: self.text(d, (x + w / 2, y + h / 2 + 28), sub, 26, self.ON_ACCENT, "Medium", "mm", k=k)
        else:
            self.box(d, (x, y, x + w, y + h), self.PANEL, col, 14, 4, k)
            self.text(d, (x + w / 2, y + h / 2 - (18 if sub else 0)), label, 40, self.TXT, "Bold", "mm", k=k)
            if sub: self.text(d, (x + w / 2, y + h / 2 + 28), sub, 26, self.DIM, "Medium", "mm", k=k)

    def pill(self, d, xy_center, s, size=30, col=None, k=1.0, anchor="mm"):
        """A small rounded tag with text (good for labels and 'example value' badges)."""
        if k <= 0.01: return
        col = col or self.HILITE
        f = self.font(size, "Bold")
        tw = d.textlength(s, font=f); x, y = xy_center
        if anchor == "lm": x += tw / 2 + size * 0.6
        bx = (x - tw / 2 - size * 0.6, y - size * 0.85, x + tw / 2 + size * 0.6, y + size * 0.85)
        if self.NAME == "paper":
            self.box(d, bx, col, None, int(size * 0.85), 0, k)
            self.text(d, (x, y), s, size, self.ON_ACCENT, "Bold", "mm", k=k)
        else:
            self.box(d, bx, self.PANEL, col, int(size * 0.85), 3, k)
            self.text(d, (x, y), s, size, col, "Bold", "mm", k=k)

    # ---------- layout ----------
    def chrome(self, d, step, title, caption, t, dur):
        """Long-form scene furniture: step label + title at top left, typed caption at the bottom."""
        k = prog(t, 0, 0.6)
        if self.NAME == "paper":
            if step: self.pill(d, (120, 92), step, 26, self.ACCENT, k, anchor="lm")
            self.text(d, (120, 136), title, 64, self.TXT, "Bold", k=k)
        elif self.NAME == "chalk":
            if step: self.text(d, (120, 84), step, 32, self.HILITE, "Bold", k=k)
            self.text(d, (120, 124), title, 68, self.TXT, "Bold", k=k)
            tw = self.textlen(d, title, 68, "Bold")
            self.line(d, [(120, 212), (120 + tw * prog(t, 0.3, 1.0), 214)], self.HILITE, 4, k)
        else:
            if step: self.text(d, (120, 90), step, 30, self.ACCENT, "Bold", k=k)
            self.text(d, (120, 130), title, 64, self.TXT, "Bold", k=k)
        if caption:
            full = wrap(caption, 64)
            n = int(len(caption) * clamp((t - 0.3) / 2.2))
            lines = wrap(caption[:n], 64) if n < len(caption) else full
            y = self.H - 70 - 52 * len(full)
            if self.NAME == "paper":
                wmax = max(self.textlen(d, ln, 40, "Medium") for ln in full)
                self.box(d, (self.W / 2 - wmax / 2 - 36, y - 18, self.W / 2 + wmax / 2 + 36, y + 52 * len(full) + 8),
                         self.PANEL, None, 22, 0, prog(t, 0.1, 0.5))
            for ln in lines:
                self.text(d, (self.W // 2, y), ln, 40, self.TXT, "Medium", "ma"); y += 52

    def headline(self, d, lines, t, col=None, y=260, size=74):
        """Short (vertical): stacked bold headline lines that pop in one by one."""
        for i, ln in enumerate(lines):
            k = prog(t, 0.1 + i * 0.25, 0.6 + i * 0.25)
            self.text(d, (self.W // 2, y + i * (size + 16)), ln, size, col or self.TXT, "Bold", "mm", k=k)

    def caption_v(self, d, s, t, y=1330):
        """Short (vertical): typed caption, max ~26 chars per line, keep y + lines*66 under 1500."""
        n = int(len(s) * clamp((t - 0.4) / 2.0))
        full = wrap(s, 26)
        if self.NAME == "paper":
            wmax = max(self.textlen(d, ln, 54, "SemiBold") for ln in full)
            self.box(d, (self.W / 2 - wmax / 2 - 30, y - 16, self.W / 2 + wmax / 2 + 30, y + 66 * len(full) + 6),
                     self.PANEL, None, 26, 0, prog(t, 0.2, 0.6))
        for i, ln in enumerate(wrap(s[:n], 26)):
            self.text(d, (self.W // 2, y + i * 66), ln, 54, self.TXT, "SemiBold", "ma")

    # ---------- canvas, grain, frames, rendering ----------
    def _bg(self, w, h):
        key = (self.NAME, w, h, "bg")
        if key in _cache: return _cache[key]
        rng = np.random.default_rng(7)
        base = np.ones((h, w, 3), np.float32) * np.array(self.BG, np.float32)
        if self.NAME == "chalk":
            # old smudges of rubbed-out chalk + fine grain
            sm = Image.fromarray((rng.random((h // 16, w // 16)) * 255).astype("uint8")).resize((w, h), Image.BICUBIC)
            sm = np.asarray(sm.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255.0
            base += (sm[..., None] - 0.5) * 22
            base += rng.normal(0, 3.0, (h, w, 1))
        elif self.NAME == "paper":
            fib = Image.fromarray((rng.random((h // 3, w // 3)) * 255).astype("uint8")).resize((w, h), Image.BICUBIC)
            base += (np.asarray(fib, np.float32)[..., None] / 255.0 - 0.5) * 7
            yy, xx = np.mgrid[0:h, 0:w]
            vig = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2)
            base -= vig[..., None] * 26
        im = Image.fromarray(np.clip(base, 0, 255).astype("uint8"))
        _cache[key] = im
        return im

    def _grain(self, w, h):
        key = (self.NAME, w, h, "grain")
        if key not in _cache:
            rng = np.random.default_rng(11)
            g = rng.random((h, w))
            m = np.where(g < 0.22, 120 + 100 * rng.random((h, w)), 255).astype("uint8")
            _cache[key] = Image.fromarray(m, "L")
        return _cache[key]

    def new_frame(self, w=None, h=None):
        return self._bg(w or self.W, h or self.H).copy()

    def finish(self, im):
        """Chalk: break strokes up with grain so they look like chalk on a board."""
        if self.NAME == "chalk":
            return Image.composite(im, self._bg(*im.size), self._grain(*im.size))
        return im

    def frame(self, fn, t, dur, fade_s=0.35):
        im = self.new_frame()
        fn(ImageDraw.Draw(im), t, dur)
        im = self.finish(im)
        a = min(clamp(t / fade_s), clamp((dur - t) / fade_s))
        if a >= 1: return im
        to = Image.new("RGB", im.size, (0, 0, 0)) if self.NAME == "blueprint" else self._bg(*im.size)
        return Image.blend(to, im, a)

    def render_to(self, outdir, name, fn, dur):
        os.makedirs(outdir, exist_ok=True)
        out, tmp = f"{outdir}/{name}.mp4", f"{outdir}/{name}.tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{self.W}x{self.H}", "-r", str(self.FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                              "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for i in range(int(round(dur * self.FPS))):
            p.stdin.write(self.frame(fn, i / self.FPS, dur).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, out)

    def preview(self, outdir, scenes, at=0.85):
        """Contact sheets of every scene at `at` of its duration: outdir/sheet1.jpg, sheet2.jpg, ..."""
        os.makedirs(outdir, exist_ok=True)
        W, H = self.W, self.H
        cols = 3 if not self.vertical else 5
        per = 9 if not self.vertical else 5
        paths = []
        for j in range(0, len(scenes), per):
            chunk = scenes[j:j + per]
            rows = math.ceil(len(chunk) / cols)
            s = Image.new("RGB", (W * cols, H * rows), (0, 0, 0))
            for i, (_, fn, dur) in enumerate(chunk):
                s.paste(self.frame(fn, dur * at, dur), ((i % cols) * W, (i // cols) * H))
            scale = 2880 / s.width
            p = f"{outdir}/sheet{j // per + 1}.jpg"
            s.resize((2880, int(s.height * scale))).save(p, quality=85)
            paths.append(p)
        return paths

    # ---------- thumbnails ----------
    def thumb_canvas(self, w=1280, h=720):
        """Background for a 1280x720 thumbnail in this style (returns Image, Draw)."""
        im = self._bg(w, h).copy()
        d = ImageDraw.Draw(im)
        if self.NAME == "blueprint":
            for x in range(0, w, 40): d.line([x, 0, x, h], fill=(24, 33, 61), width=1)
            for y in range(0, h, 40): d.line([0, y, w, y], fill=(24, 33, 61), width=1)
        return im, d


def get(name, vertical=False):
    return Style(name, vertical)

def for_episode(n):
    """Fallback only: queue.json's "style" field decides. Episodes 1-5: chalk, paper, blueprint, chalk, paper;
    6-13: blueprint; from 14 the rotation is chalk, paper, blueprint, ..."""
    if n <= 5: return ["chalk", "paper", "blueprint"][(n - 1) % 3]
    if n <= 13: return "blueprint"
    return ["chalk", "paper", "blueprint"][(n - 14) % 3]
