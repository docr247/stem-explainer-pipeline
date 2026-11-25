import math, os, subprocess
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, wrap,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)

W, H, FPS = 1080, 1920, 30
SAFE_L, SAFE_R = 70, 930   # keep clear of the Shorts side buttons

def headline(d, lines, t, col=TXT, y=260, size=74):
    for i, ln in enumerate(lines):
        k = prog(t, 0.1 + i * 0.25, 0.6 + i * 0.25)
        text(d, (W // 2, y + i * (size + 16)), ln, size, col, "Bold", "mm", k=k)

def caption(d, s, t, y=1330):
    n = int(len(s) * clamp((t - 0.4) / 2.0))
    for i, ln in enumerate(wrap(s[:n], 26)):
        text(d, (W // 2, y + i * 66), ln, 54, TXT, "SemiBold", "ma")

def scope(d, x0, y0, w, h, t, start, name, col, settle):
    text(d, (x0, y0 - 8), name, 32, col, "Bold", "ld", mono=True)
    d.line([x0, y0 + h, x0 + w, y0 + h], fill=LINE, width=2)
    tt = clamp((t - 0.6) / 6.0) * w
    pts = []
    for px in range(0, int(tt), 4):
        st = px / w * 8.0
        v = 0 if st < start else (1 - math.exp(-(st - start) * 3)) + (
            0.15 * math.exp(-(st - start) * 2.5) * math.sin((st - start) * 30) if settle else 0)
        pts.append((x0 + px, y0 + h - v * h))
    if len(pts) > 1: d.line(pts, fill=col, width=6)

def s_hook(d, t, dur):
    headline(d, ["Your CPU wakes up", "knowing just", "ONE thing."], t, y=330)
    cx, cy, r = W // 2, 900, 190
    press = 1 - 0.08 * math.sin(math.pi * clamp((t - 1.6) / 0.35))
    r = int(r * press); on = t > 1.8; col = CYAN if on else DIM
    if on:
        for g in range(6):
            rr = r + 20 + g * 16
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=mix(BG, CYAN, 0.25 - g * 0.04), width=5)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PANEL, outline=col, width=10)
    d.arc([cx - 80, cy - 72, cx + 80, cy + 88], 300, 240, fill=col, width=15)
    d.line([cx, cy - 100, cx, cy + 8], fill=col, width=15)
    caption(d, "Here's what happens the instant you press power.", t, 1250)

def s_power(d, t, dur):
    headline(d, ["Step 1: wait for", "stable power"], t, CYAN, 250, 66)
    rows = [("+12V", AMBER, .3, True), ("+5V", CYAN, .5, True), ("+3.3V", GREEN, .7, True),
            ("PWR_OK", TXT, 3.6, False), ("RESET#", RED, 5.6, False)]
    for i, (n, c, s, st) in enumerate(rows):
        scope(d, SAFE_L + 20, 470 + i * 150, 840, 80, t, s, n, c, st)
    caption(d, "Voltages ring and settle. Only then does Power Good go high and reset let go.", t, 1300)

def s_vector(d, t, dur):
    headline(d, ["Step 2: the", "first instruction"], t, CYAN, 250, 66)
    chip(d, 290, 450, 500, 200, "CPU", "just out of reset", CYAN, prog(t, 0.2, 0.8))
    chip(d, 290, 900, 500, 200, "SPI Flash", "firmware ROM", AMBER, prog(t, 0.5, 1.1))
    k = prog(t, 0.9, 1.4)
    d.line([460, 666, 460, 884], fill=fade(LINE, k), width=6)
    d.line([620, 666, 620, 884], fill=fade(LINE, k), width=6)
    if 2.4 < t < 4.0:
        p = ease((t - 2.4) / 1.4); y = 666 + p * 218
        d.ellipse([446, y - 14, 474, y + 14], fill=CYAN)
    if 4.0 < t < 5.6:
        p = ease((t - 4.0) / 1.4); y = 884 - p * 218
        d.ellipse([606, y - 14, 634, y + 14], fill=AMBER)
    s = "0xFFFFFFF0"
    n = int(len(s) * clamp((t - 1.2) / 1.2))
    text(d, (W // 2, 1200), s[:n], 96, AMBER, mono=True, anchor="mm")
    caption(d, "Hard-wired into every x86 chip. It's called the reset vector.", t, 1330)

def s_chain(d, t, dur):
    headline(d, ["Then 5 more", "handoffs"], t, TXT, 250, 74)
    st = [("Power", AMBER), ("Reset", RED), ("Firmware", CYAN), ("Bootloader", GREEN),
          ("Kernel", (180, 140, 255)), ("Login", TXT)]
    for i, (nm, c) in enumerate(st):
        k = prog(t, 0.6 + i * 0.5, 1.0 + i * 0.5)
        y = 470 + i * 125
        d.ellipse([300, y - 22, 344, y + 22], fill=fade(c, k))
        text(d, (380, y), nm, 54, c, "Bold", "lm", k=k)
        if i < 5 and k > 0: d.line([322, y + 30, 322, y + 95], fill=fade(LINE, k), width=5)
    caption(d, "All in a few seconds, before you ever see a login screen.", t, 1300)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "Full breakdown", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "of all 6 steps", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")  if k2 > 0.5 else None
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_power, 9), ("s3", s_vector, 9), ("s4", s_chain, 8), ("s5", s_cta, 5)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short/{name}.mp4", f"short/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

if __name__ == "__main__":
    import sys
    os.makedirs("short", exist_ok=True)
    if sys.argv[1:] == ["preview"]:
        ims = [frame(fn, dur * 0.85, dur) for _, fn, dur in SCENES]
        sheet = Image.new("RGB", (W * 5, H))
        for i, im in enumerate(ims): sheet.paste(im, (i * W, 0))
        sheet.resize((W * 5 // 3, H // 3)).save("short/sheet.jpg", quality=85)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor() as ex: list(ex.map(render, *zip(*SCENES)))
