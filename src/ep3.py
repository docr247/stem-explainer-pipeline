"""Tech 101, episode 3 (deep-dive, blueprint style): What really happens when you press a key?"""
import math, sys
from PIL import Image, ImageDraw, ImageFont
import style
from style import clamp, ease, prog, mix, grow

S = style.get("blueprint")
W, H, FPS = S.W, S.H, S.FPS
VOICE, SPEED, LANG = S.VOICE, S.SPEED, S.LANG
BG, PANEL, LINE, TXT, DIM = S.BG, S.PANEL, S.LINE, S.TXT, S.DIM
CY, AM, GR, RD, PU, BL = S.ACCENT, S.HILITE, S.GOOD, S.BAD, S.EXTRA, S.BLUE
DARK = (8, 12, 24)
SCREEN = (16, 24, 44)


def ph(t, dur, a, b):
    """Progress between fractions a and b of the scene (scenes stretch to fit the narration)."""
    return prog(t, a * dur, b * dur)


def press_at(t, t0, t1, ramp=0.12):
    """0 -> 1 while a key is held between t0 and t1 (with short ramps)."""
    return clamp((t - t0) / ramp) * clamp((t1 - t) / ramp)


# ---------------- drawing helpers (shared with short3.py) ----------------
def glow(d, pts, col, w=6, k=1.0):
    """A glowing signal line."""
    if k <= 0.01 or len(pts) < 2: return
    S.line(d, pts, mix(BG, col, 0.14), w + 16, k)
    S.line(d, pts, mix(BG, col, 0.32), w + 7, k)
    S.line(d, pts, col, w, k)


def glow_dot(d, c, r, col, k=1.0):
    for m, a in ((2.6, 0.10), (1.8, 0.22), (1.3, 0.45)):
        S.circle(d, c, r * m, mix(BG, col, a), k=k)
    S.circle(d, c, r, col, k=k)


def keycap(d, cx, cy, s, label, press=0.0, k=1.0, col=None, size=None):
    """A keycap seen from the front; press 0..1 pushes it down and lights its edge."""
    if k <= 0.01: return
    col = col or CY
    dy = s * 0.06 * press
    r = int(s * 0.12)
    S.box(d, (cx - s / 2, cy - s / 2 + s * 0.08, cx + s / 2, cy + s / 2 + s * 0.08), DARK, DARK, r, 2, k)
    if press > 0.05:
        S.box(d, (cx - s / 2 - 10, cy - s / 2 + dy - 10, cx + s / 2 + 10, cy + s / 2 + dy + 10),
              mix(BG, col, 0.10 * press), mix(BG, col, 0.35 * press), r + 8, 3, k)
    S.box(d, (cx - s / 2, cy - s / 2 + dy, cx + s / 2, cy + s / 2 + dy), PANEL, mix(LINE, col, max(press, 0.4)), r, 5, k)
    S.text(d, (cx, cy + dy), label, size or int(s * 0.42), TXT, "Bold", "mm", k=k)


def report_row(d, x, y, vals, k=1.0, t=None, t0=0.0, step=0.12, bw=150, bh=120, gap=16, hot=(), labels=None,
               size=46, lsize=24, hotcol=None):
    """The 8 bytes of a keyboard report as boxes. Returns the x centre of each box."""
    hotcol = hotcol or AM
    xs = []
    for i, v in enumerate(vals):
        kk = k if t is None else k * prog(t, t0 + i * step, t0 + i * step + 0.3)
        xx = x + i * (bw + gap)
        xs.append(xx + bw / 2)
        h = i in hot
        S.box(d, (xx, y, xx + bw, y + bh), mix(BG, hotcol, 0.22) if h else PANEL, hotcol if h else LINE, 12, 4 if h else 2, kk)
        S.text(d, (xx + bw / 2, y + bh / 2), v, size, hotcol if h else TXT, "Bold", "mm", mono=True, k=kk)
        if labels: S.text(d, (xx + bw / 2, y + bh + 30), labels[i], lsize, DIM, "Medium", "mm", k=kk)
    return xs


def keyboard_icon(d, x, y, w, h, k=1.0, hot=None, col=None, hotk=1.0):
    """A generic keyboard seen from above: 4 rows of keys and a space bar."""
    col = col or CY
    S.box(d, (x, y, x + w, y + h), PANEL, LINE, 18, 3, k)
    cols, rows = 10, 3
    kw, kh = (w - 40) / cols, (h - 40) / (rows + 1)
    for r in range(rows):
        for c in range(cols):
            x0, y0 = x + 20 + c * kw + 4, y + 20 + r * kh + 4
            lit = hot == (r, c)
            S.box(d, (x0, y0, x0 + kw - 8, y0 + kh - 8), mix(DARK, col, 0.6 * hotk) if lit else DARK,
                  col if lit and hotk > 0.3 else LINE, 6, 2, k)
    y0 = y + 20 + rows * kh + 4
    S.box(d, (x + 20 + 2.5 * kw, y0, x + 20 + 7.5 * kw - 8, y0 + kh - 8), DARK, LINE, 6, 2, k)


def computer_icon(d, x, y, w, h, k=1.0, label="", col=None):
    col = col or PU
    S.box(d, (x, y, x + w, y + h), PANEL, col, 16, 4, k)
    S.box(d, (x + 18, y + 18, x + w - 18, y + h - 18), SCREEN, LINE, 8, 2, k)
    S.box(d, (x + w / 2 - 20, y + h, x + w / 2 + 20, y + h + 40), PANEL, LINE, 4, 2, k)
    S.box(d, (x + w / 2 - 90, y + h + 40, x + w / 2 + 90, y + h + 56), PANEL, LINE, 6, 2, k)
    if label: S.text(d, (x + w / 2, y + h / 2), label, 34, col, "Bold", "mm", k=k)


def diode(d, c, s, ang, col, k=1.0):
    """Diode symbol: a triangle pointing the way current may flow, with a bar at the tip."""
    if k <= 0.01: return
    cx, cy = c
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    tip = (cx + ux * s / 2, cy + uy * s / 2)
    b1 = (cx - ux * s / 2 + vx * s / 2, cy - uy * s / 2 + vy * s / 2)
    b2 = (cx - ux * s / 2 - vx * s / 2, cy - uy * s / 2 - vy * s / 2)
    d.polygon([tip, b1, b2], fill=S.fade(col, k))
    S.line(d, [(tip[0] + vx * s / 2, tip[1] + vy * s / 2), (tip[0] - vx * s / 2, tip[1] - vy * s / 2)], col, 5, k)


def ground(d, x, y, col, k=1.0):
    S.line(d, [(x - 34, y), (x + 34, y)], col, 5, k)
    S.line(d, [(x - 22, y + 12), (x + 22, y + 12)], col, 5, k)
    S.line(d, [(x - 10, y + 24), (x + 10, y + 24)], col, 5, k)


def resistor(d, x, y0, y1, col, k=1.0):
    n = 6
    pts = [(x, y0), (x, y0 + 20)]
    seg = (y1 - y0 - 40) / n
    for i in range(n):
        pts.append((x + (22 if i % 2 == 0 else -22), y0 + 20 + seg * (i + 0.5)))
    pts += [(x, y1 - 20), (x, y1)]
    S.line(d, pts, col, 5, k)


def bounce_level(u):
    """Raw switch signal (1 = high/released, 0 = low/pressed) with contact bounce between u=0.25 and 0.39."""
    edges = [0.25, 0.268, 0.285, 0.305, 0.322, 0.338, 0.352, 0.364, 0.376, 0.386]
    if u < edges[0]: return 1
    n = sum(1 for e in edges if u >= e)
    return 0 if n % 2 == 1 else 1


def trace(d, x0, y_hi, y_lo, w, fn, reveal, col, width=5, k=1.0, glowing=True):
    pts = []
    for px in range(0, int(w * clamp(reveal)) + 1, 2):
        pts.append((x0 + px, y_hi if fn(px / w) else y_lo))
    if len(pts) > 1:
        (glow if glowing else S.line)(d, pts, col, width, k=k)


_raster = {}
def glyph_bitmap(ch="a", n=18):
    """Rasterise one character into an n x n anti-aliased bitmap (values 0..255), as a font renderer would."""
    key = (ch, n)
    if key not in _raster:
        im = Image.new("L", (n, n), 0)
        f = ImageFont.truetype(style.INTER + "Inter-Medium.otf", int(n * 0.95))
        ImageDraw.Draw(im).text((n / 2, n * 0.62), ch, font=f, fill=255, anchor="ms")
        _raster[key] = [[im.getpixel((x, y)) for x in range(n)] for y in range(n)]
    return _raster[key]


# ---------------- intro ----------------
def s_hook(d, t, dur):
    S.chrome(d, "", "", "You press a key and a letter appears. But your keyboard never actually sends the letter.", t, dur)
    k = prog(t, 0.2, 0.7)
    p = press_at(t, 1.0, 1.7)
    keycap(d, 470, 430, 280, "A", p, k)
    # cable with a glowing signal
    kk = prog(t, 0.6, 1.1)
    S.line(d, [(640, 430), (980, 430)], LINE, 6, kk)
    if 1.2 < t < 2.0:
        x = 640 + (t - 1.2) / 0.8 * 340
        glow_dot(d, (x, 430), 10, AM)
    # a text box on a screen
    S.box(d, (1000, 270, 1740, 590), PANEL, LINE, 18, 3, kk)
    S.box(d, (1030, 300, 1710, 560), SCREEN, LINE, 10, 2, kk)
    typed = t > 1.9
    if typed: S.text(d, (1080, 430), "a", 120, TXT, "Medium", "lm")
    if int(t * 2) % 2 == 0 and kk > 0.5:
        x = 1160 if typed else 1080
        d.rectangle([x, 370, x + 6, 490], fill=CY)
    k2 = ph(t, dur, 0.25, 0.32)
    S.text(d, (W // 2, 660), "what actually travels down the cable:", 32, DIM, "Medium", "mm", k=k2)
    report_row(d, 520, 700, ["00", "00", "04", "00", "00", "00", "00", "00"], k2, bw=100, bh=80, gap=14, hot=(2,), size=38)
    S.pill(d, (810, 362), "a few milliseconds", 26, CY, ph(t, dur, 0.12, 0.18))


def s_cover(d, t, dur):
    S.chrome(d, "", "Here's what we'll cover", "Seven steps, zooming in each time: switch, matrix, debounce, report, USB, inside the computer, and the screen.", t, dur)
    items = [("1", "The switch", "a contact closes", CY), ("2", "The matrix", "rows, columns and scanning", AM),
             ("3", "Debounce", "one press, not five", RD), ("4", "The report", "numbers, not letters", AM),
             ("5", "USB", "the host does the asking", PU), ("6", "Inside the computer", "interrupt and driver", BL),
             ("7", "To the screen", "layout, glyph, pixels", GR)]
    for i, (n, a, b, c) in enumerate(items):
        kk = ph(t, dur, 0.05 + i * 0.08, 0.10 + i * 0.08)
        col, row = i % 2, i // 2
        x, y = 170 + col * 820, 245 + row * 132
        if i == 6: x = 170 + 410
        S.box(d, (x, y, x + 760, y + 112), PANEL, c, 16, 3, kk)
        S.circle(d, (x + 58, y + 56), 34, c, k=kk)
        S.text(d, (x + 58, y + 56), n, 36, BG, "Bold", "mm", k=kk)
        S.text(d, (x + 120, y + 38), a, 38, TXT, "Bold", "lm", k=kk)
        S.text(d, (x + 120, y + 82), b, 27, DIM, "Medium", "lm", k=kk)


# ---------------- step 1: the switch ----------------
def s_press(d, t, dur):
    S.chrome(d, "STEP 1 · THE SWITCH", "Every key is a switch", "Under every key is a simple switch. Press it and two contacts touch. Membrane or mechanical, it's either open or closed.", t, dur)
    k = prog(t, 0.2, 0.7)
    cyc = (t - 1.0) % 3.2 if t > 1.0 else 0
    p = press_at(cyc, 1.0, 2.4, 0.25) if t > 1.0 else 0
    cx = 560
    # base plate and the two contact sheets
    S.box(d, (240, 700, 880, 730), PANEL, LINE, 4, 2, k)
    S.line(d, [(250, 688), (870, 688)], DIM, 6, k)                       # bottom sheet
    S.box(d, (250, 660, 330, 684), LINE, LINE, 2, 1, k)                  # spacers
    S.box(d, (790, 660, 870, 684), LINE, LINE, 2, 1, k)
    sag = 18 * p
    top = [(250, 656), (cx - 120, 656), (cx - 40, 656 + sag), (cx + 40, 656 + sag), (cx + 120, 656), (870, 656)]
    S.line(d, top, DIM, 6, k)                                              # top sheet
    closed = p > 0.85
    pad = GR if closed else AM
    d.rectangle([cx - 40, 680, cx + 40, 686], fill=S.fade(pad, k))        # bottom contact
    d.rectangle([cx - 40, 660 + sag, cx + 40, 666 + sag], fill=S.fade(pad, k))  # top contact
    if closed: glow(d, [(cx - 40, 683), (cx + 40, 683)], GR, 6)
    # rubber dome
    h = 150 - 110 * p
    dome = [(cx - 150 + 30 * p, 652)] + [(cx + 110 * math.cos(math.pi - math.pi * i / 16) * (1 + 0.2 * p),
             652 - h * math.sin(math.pi * i / 16)) for i in range(17)] + [(cx + 150 - 30 * p, 652)]
    S.line(d, dome, PU, 6, k)
    # keycap and stem
    ky = 652 - h - 110
    S.box(d, (cx - 22, ky + 80, cx + 22, 652 - h + 4), PANEL, LINE, 4, 2, k)
    S.box(d, (cx - 170, ky, cx + 170, ky + 90), PANEL, CY, 14, 4, k)
    S.text(d, (cx, ky + 45), "A", 50, TXT, "Bold", "mm", k=k)
    # labels
    kl = ph(t, dur, 0.15, 0.22)
    S.text(d, (220, ky + 45), "keycap", 28, CY, "Bold", "rm", k=kl)
    S.text(d, (220, 560), "rubber dome", 28, PU, "Bold", "rm", k=kl)
    S.text(d, (220, 672), "contact sheets", 28, AM, "Bold", "rm", k=kl)
    S.text(d, (cx, 780), "membrane keyboard (side view, simplified)", 26, DIM, "Medium", "mm", k=kl)
    # schematic switch
    ks = ph(t, dur, 0.3, 0.38)
    a, b = (1180, 520), (1560, 520)
    wc = GR if closed else LINE
    (glow if closed else S.line)(d, [(1080, 520), a], wc, 6, k=ks)
    (glow if closed else S.line)(d, [b, (1680, 520)], wc, 6, k=ks)
    ang = math.radians(28 * (1 - p))
    lever = (a[0] + 380 * math.cos(ang), a[1] - 380 * math.sin(ang))
    (glow if closed else S.line)(d, [a, lever], wc if closed else TXT, 6, k=ks)
    S.circle(d, a, 12, BG, TXT, 4, k=ks)
    S.circle(d, b, 12, BG, TXT, 4, k=ks)
    S.text(d, (1370, 360), "CLOSED" if closed else "OPEN", 46, GR if closed else DIM, "Bold", "mm", k=ks)
    S.text(d, (1370, 620), "the same thing, as a circuit symbol", 26, DIM, "Medium", "mm", k=ks)
    S.text(d, (1370, 700), "mechanical keyboards: one switch per key,", 26, DIM, "Medium", "mm", k=ph(t, dur, 0.55, 0.62))
    S.text(d, (1370, 736), "metal contacts inside. Same idea.", 26, DIM, "Medium", "mm", k=ph(t, dur, 0.55, 0.62))


def s_pullup(d, t, dur):
    S.chrome(d, "STEP 1 · THE SWITCH", "High means up, low means pressed", "A pull-up resistor holds the input pin high. Closing the switch connects it to ground, so the voltage drops low.", t, dur)
    k = prog(t, 0.2, 0.7)
    cyc = (t - 1.0) % 4.0 if t > 1.0 else 0
    p = press_at(cyc, 1.5, 3.0, 0.05) if t > 1.0 else 0
    closed = p > 0.5
    nx, ny = 980, 500
    # supply, resistor, node
    S.line(d, [(860, 290), (1100, 290)], AM, 6, k)
    S.text(d, (980, 262), "supply voltage", 26, AM, "Bold", "mm", k=k)
    resistor(d, nx, 290, 460, TXT, k)
    S.text(d, (nx - 40, 375), "pull-up", 26, TXT, "Bold", "rm", k=k)
    S.text(d, (nx - 40, 405), "resistor", 26, TXT, "Bold", "rm", k=k)
    S.line(d, [(nx, 460), (nx, ny)], TXT, 5, k)
    S.circle(d, (nx, ny), 9, TXT, k=k)
    # wire to MCU pin
    wire_col = DIM if closed else AM
    (S.line if closed else glow)(d, [(nx, ny), (1300, ny)], wire_col, 5, k=k)
    S.chip(d, 1300, 400, 380, 200, "MCU", "input pin", CY, k)
    S.text(d, (1490, 680), "pin reads: " + ("LOW  0" if closed else "HIGH  1"), 34, GR if closed else AM, "Bold", "mm", mono=True, k=k)
    # switch to ground
    S.line(d, [(nx, ny), (nx, 560)], TXT, 5, k)
    sa, sb = (nx, 560), (nx, 680)
    ang = math.radians(90 - 30 * (1 - p))
    lever = (sa[0] + 120 * math.cos(ang) * (1 if not closed else 0.0), sa[1] + 120 * math.sin(ang))
    S.line(d, [sa, lever], GR if closed else TXT, 6, k)
    S.circle(d, sa, 9, BG, TXT, 4, k=k)
    S.circle(d, sb, 9, BG, TXT, 4, k=k)
    S.text(d, (nx + 60, 620), "key", 26, GR if closed else DIM, "Bold", "lm", k=k)
    S.line(d, [sb, (nx, 730)], TXT, 5, k)
    ground(d, nx, 730, TXT, k)
    S.text(d, (nx + 60, 748), "ground (0 V)", 24, DIM, "Medium", "lm", k=k)
    # voltage trace at the pin
    kt = ph(t, dur, 0.25, 0.32)
    x0, w = 170, 560
    S.box(d, (x0 - 20, 300, x0 + w + 20, 640), SCREEN, LINE, 12, 2, kt)
    S.text(d, (x0, 330), "voltage at the pin", 26, DIM, "Bold", "lm", k=kt)
    S.text(d, (x0 + w, 400), "high", 22, AM, "Medium", "rm", k=kt)
    S.text(d, (x0 + w, 596), "low", 22, GR, "Medium", "rm", k=kt)
    if t > 1.0:
        pts = []
        for px in range(0, w, 3):
            tt = t - (w - px) / w * 4.0
            if tt < 1.0: c2 = 0
            else:
                c2 = press_at((tt - 1.0) % 4.0, 1.5, 3.0, 0.05)
            pts.append((x0 + px, 430 + 150 * (c2 > 0.5)))
        glow(d, pts, GR if closed else AM, 5, kt)


# ---------------- step 2: the matrix ----------------
def s_matrix_why(d, t, dur):
    S.chrome(d, "STEP 2 · THE MATRIX", "About a hundred keys, far fewer wires", "A wire for every key would need about a hundred pins. A grid of 8 rows and 13 columns covers 104 keys with just 21 wires.", t, dur)
    k = ph(t, dur, 0.02, 0.08)
    # left: one wire per key
    S.text(d, (510, 270), "one wire per key", 32, RD, "Bold", "mm", k=k)
    S.chip(d, 170, 440, 170, 160, "MCU", None, RD, k, pins=False)
    n = int(100 * ph(t, dur, 0.05, 0.3))
    for i in range(n):
        r, c = divmod(i, 10)
        px, py = 470 + c * 38, 330 + r * 40
        S.line(d, [(340, 470 + (i % 20) * 5), (px, py)], mix(BG, RD, 0.35), 1, k)
        S.circle(d, (px, py), 6, RD, k=k)
    S.text(d, (510, 760), "≈ 100 keys → ≈ 100 pins", 30, RD, "Bold", "mm", k=ph(t, dur, 0.28, 0.33))
    # right: a grid
    kg = ph(t, dur, 0.38, 0.45)
    S.text(d, (1400, 270), "a grid of rows and columns", 32, GR, "Bold", "mm", k=kg)
    gx, gy, sx, sy = 1060, 330, 56, 52
    for c in range(13):
        S.line(d, [(gx + c * sx, gy - 20), (gx + c * sx, gy + 7 * sy + 20)], CY, 3, kg)
    for r in range(8):
        S.line(d, [(gx - 20, gy + r * sy), (gx + 12 * sx + 20, gy + r * sy)], AM, 3, kg)
    nk = int(104 * ph(t, dur, 0.45, 0.65))
    for i in range(nk):
        r, c = divmod(i, 13)
        S.box(d, (gx + c * sx - 11, gy + r * sy - 11, gx + c * sx + 11, gy + r * sy + 11), PANEL, GR, 3, 2, kg)
    kt = ph(t, dur, 0.62, 0.68)
    S.text(d, (1400, 740), "8 rows + 13 columns = 21 wires", 30, GR, "Bold", "mm", k=kt)
    S.text(d, (1400, 780), "8 × 13 = 104 key positions", 26, TXT, "Medium", "mm", k=kt)
    S.pill(d, (1700, 270), "example", 22, AM, kt)
    S.line(d, [(930, 300), (930, 780)], LINE, 2, k)


MX_X0, MX_Y0, MX_SX, MX_SY = 660, 350, 170, 120
def s_scan(d, t, dur):
    S.chrome(d, "STEP 2 · THE MATRIX", "Scanning: one column at a time", "Each key sits where a row crosses a column. Drive one column low, read every row. A low row means that key is pressed.", t, dur)
    k = prog(t, 0.2, 0.8)
    rows, cols = 4, 6
    x0, y0, sx, sy = MX_X0, MX_Y0, MX_SX, MX_SY
    col = int((t - 1.0) * 1.4) % cols if t > 1.0 else -1
    hit = (2, 3)
    pressed = t > dur * 0.3
    S.chip(d, 150, 400, 260, 260, "MCU", "scanning", CY, k)
    # drive bus from the chip to the column tops
    S.line(d, [(280, 384), (280, 270), (x0 + (cols - 1) * sx, 270)], LINE, 4, k)
    for c in range(cols):
        x = x0 + c * sx
        act = c == col
        if act: glow(d, [(x, 270), (x, y0 + (rows - 1) * sy + 40)], AM, 6)
        else: S.line(d, [(x, 270), (x, y0 + (rows - 1) * sy + 40)], LINE, 4, k)
        S.text(d, (x + 14, 300), f"C{c}", 24, AM if act else DIM, "Bold", "lm", k=k)
    for r in range(rows):
        y = y0 + r * sy
        lit = pressed and col == hit[1] and r == hit[0]
        if lit: glow(d, [(410, y), (x0 + (cols - 1) * sx + 40, y)], GR, 6)
        else: S.line(d, [(410, y), (x0 + (cols - 1) * sx + 40, y)], LINE, 4, k)
        S.text(d, (x0 + (cols - 1) * sx + 60, y), f"R{r}", 24, GR if lit else DIM, "Bold", "lm", k=k)
        for c in range(cols):
            x = x0 + c * sx
            on = pressed and (r, c) == hit
            S.box(d, (x - 20, y - 20, x + 20, y + 20), mix(BG, GR, 0.8) if on else PANEL, GR if on else LINE, 5, 3, k)
    if col >= 0:
        S.pill(d, (x0 + col * sx, 236), "driven LOW", 22, AM, k)
    kk = ph(t, dur, 0.35, 0.42)
    found = pressed and col == hit[1]
    S.text(d, (W // 2 + 100, 790), "R2 reads LOW while C3 is driven → key at (R2, C3)", 30,
           GR if found else DIM, "Bold", "mm", mono=True, k=kk)


def s_keymap(d, t, dur):
    S.chrome(d, "STEP 2 · THE MATRIX", "From a position to a key code", "A keymap table in the firmware turns the position into a key code. The whole grid is scanned many times every second.", t, dur)
    k = prog(t, 0.2, 0.7)
    # small matrix with one key pressed
    gx, gy, s = 200, 300, 90
    for c in range(4):
        S.line(d, [(gx + c * s, gy - 20), (gx + c * s, gy + 3 * s + 20)], CY, 3, k)
        S.text(d, (gx + c * s, gy - 40), f"C{c}", 22, DIM, "Bold", "mm", k=k)
    for r in range(4):
        S.line(d, [(gx - 20, gy + r * s), (gx + 3 * s + 20, gy + r * s)], AM, 3, k)
        S.text(d, (gx - 46, gy + r * s), f"R{r}", 22, DIM, "Bold", "mm", k=k)
        for c in range(4):
            on = (r, c) == (2, 1) and t > dur * 0.1
            S.box(d, (gx + c * s - 16, gy + r * s - 16, gx + c * s + 16, gy + r * s + 16),
                  mix(BG, GR, 0.8) if on else PANEL, GR if on else LINE, 4, 2, k)
    S.text(d, (gx + 1.5 * s, gy + 3 * s + 70), "pressed: R2, C1", 28, GR, "Bold", "mm", mono=True, k=ph(t, dur, 0.1, 0.15))
    ka = ph(t, dur, 0.18, 0.24)
    S.arrow(d, (540, 435), (660, 435), DIM, 5, ka)
    # keymap table
    kt = ph(t, dur, 0.2, 0.28)
    S.box(d, (680, 280, 1260, 600), PANEL, CY, 16, 3, kt)
    S.text(d, (970, 316), "keymap (in the firmware)", 28, CY, "Bold", "mm", k=kt)
    rows = [("R1, C1", "14", "Q"), ("R2, C1", "04", "A"), ("R3, C1", "1D", "Z"), ("R2, C2", "16", "S")]
    for i, (pos, code, nm) in enumerate(rows):
        y = 380 + i * 56
        h = i == 1
        if h: S.box(d, (700, y - 24, 1240, y + 24), mix(BG, AM, 0.2), AM, 8, 2, ph(t, dur, 0.3, 0.36))
        S.text(d, (730, y), pos, 30, AM if h else TXT, "Bold", "lm", mono=True, k=kt)
        S.text(d, (930, y), "→", 30, DIM, "Bold", "mm", k=kt)
        S.text(d, (990, y), f"code {code}", 30, AM if h else TXT, "Bold", "lm", mono=True, k=kt)
        S.text(d, (1220, y), f"({nm})", 26, DIM, "Medium", "rm", k=kt)
    S.text(d, (970, 630), "example wiring; codes are hex", 22, DIM, "Medium", "mm", k=kt)
    ko = ph(t, dur, 0.34, 0.4)
    S.arrow(d, (1280, 435), (1390, 435), DIM, 5, ko)
    S.box(d, (1410, 360, 1740, 510), mix(BG, AM, 0.15), AM, 16, 4, ko)
    S.text(d, (1575, 410), "key code", 28, DIM, "Bold", "mm", k=ko)
    S.text(d, (1575, 462), "04", 56, AM, "Bold", "mm", mono=True, k=ko)
    # scan timeline
    kl = ph(t, dur, 0.5, 0.56)
    x0, x1, y = 200, 1740, 730
    S.line(d, [(x0, y), (x1, y)], LINE, 3, kl)
    n = 24
    lit = int((t * 8) % n)
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        c = CY if i == lit else mix(BG, CY, 0.5)
        S.box(d, (x - 22, y - 26, x + 22, y - 4), mix(BG, c, 0.5), c, 4, 2, kl)
    S.text(d, (x0, y + 34), "scan", 22, DIM, "Medium", "lm", k=kl)
    S.text(d, (x1, y + 34), "many full scans per second: typically hundreds to thousands", 24, CY, "Bold", "rm", k=kl)


# ghost / diode geometry: switch branch hangs off the row, goes down, then right into the column
GX0, GX1, GY0, GY1, BR = 720, 1140, 360, 600, 110
def _ghost_grid(d, k, diodes=False, pressed=((0, 0), (0, 1), (1, 1)), ghost_k=0.0, col_lit=True):
    cols, rows = (GX0, GX1), (GY0, GY1)
    S.chip(d, 140, 330, 230, 360, "MCU", "reads rows", CY, k, pins=False)
    for ci, x in enumerate(cols):
        c = AM if (ci == 0 and col_lit) else LINE
        S.line(d, [(x, 270), (x, GY1 + 140)], c, 5, k)
        S.text(d, (x + 16, 286), f"C{ci}", 26, c if c == AM else DIM, "Bold", "lm", k=k)
    for ri, y in enumerate(rows):
        S.line(d, [(370, y), (GX1 + 90, y)], LINE, 5, k)
        S.text(d, (GX1 + 110, y), f"R{ri}", 26, DIM, "Bold", "lm", k=k)
    for ri, y in enumerate(rows):
        for ci, x in enumerate(cols):
            bx = x - BR
            S.line(d, [(bx, y), (bx, y + 80), (x, y + 80)], LINE, 4, k)
            S.circle(d, (bx, y), 8, TXT, k=k)
            S.circle(d, (x, y + 80), 8, TXT, k=k)
            on = (ri, ci) in pressed
            S.box(d, (bx - 20, y + 20, bx + 20, y + 60), mix(BG, GR, 0.8) if on else PANEL, GR if on else LINE, 5, 3, k)
            if diodes: diode(d, (bx + BR / 2, y + 80), 30, 0, TXT, k)
    if col_lit: S.pill(d, (GX0, 236), "C0 driven LOW", 22, AM, k)
    if ghost_k > 0.01:
        bx, y = GX0 - BR, GY1
        S.box(d, (bx - 24, y + 16, bx + 24, y + 64), mix(BG, RD, 0.25), RD, 6, 4, ghost_k)
        S.text(d, (bx, y + 40), "?", 30, RD, "Bold", "mm", k=ghost_k)


def _sneak_path():
    # current flows from the R1 pull-up, through C, up C1, backwards through B, along R0, through A, into C0
    return [(370, GY1), (GX1 - BR, GY1), (GX1 - BR, GY1 + 80), (GX1, GY1 + 80), (GX1, GY0 + 80),
            (GX1 - BR, GY0 + 80), (GX1 - BR, GY0), (GX0 - BR, GY0), (GX0 - BR, GY0 + 80), (GX0, GY0 + 80), (GX0, 270)]


def s_ghost(d, t, dur):
    S.chrome(d, "STEP 2 · THE MATRIX", "Ghost keys", "Hold three keys at three corners of a rectangle, and current can sneak backwards through them. The fourth corner looks pressed: a ghost.", t, dur)
    k = prog(t, 0.2, 0.7)
    gk = ph(t, dur, 0.5, 0.56)
    _ghost_grid(d, k, ghost_k=gk)
    pk = ph(t, dur, 0.2, 0.5)
    glow(d, grow(_sneak_path(), pk), RD, 6)
    kl = ph(t, dur, 0.08, 0.14)
    S.text(d, (GX0 - BR - 34, GY0 + 40), "A", 28, GR, "Bold", "rm", k=kl)
    S.text(d, (GX1 - BR - 34, GY0 + 40), "B", 28, GR, "Bold", "rm", k=kl)
    S.text(d, (GX1 - BR - 34, GY1 + 40), "C", 28, GR, "Bold", "rm", k=kl)
    S.box(d, (1380, 300, 1800, 700), PANEL, RD, 16, 3, gk)
    S.text(d, (1590, 350), "held: A, B, C", 32, GR, "Bold", "mm", k=gk)
    S.text(d, (1590, 420), "R1 reads LOW", 30, TXT, "Medium", "mm", k=gk)
    S.text(d, (1590, 460), "while C0 is driven", 30, TXT, "Medium", "mm", k=gk)
    S.text(d, (1590, 540), "→ (R1, C0) looks", 32, RD, "Bold", "mm", k=gk)
    S.text(d, (1590, 582), "pressed too", 32, RD, "Bold", "mm", k=gk)
    S.text(d, (1590, 650), "a \"ghost\" key", 28, DIM, "Medium", "mm", k=gk)


def s_diodes(d, t, dur):
    S.chrome(d, "STEP 2 · THE MATRIX", "One diode per key", "A diode lets current flow one way only, so the sneak path is blocked. With a diode on every key, every key reads correctly: N-key rollover.", t, dur)
    k = prog(t, 0.2, 0.7)
    _ghost_grid(d, k, diodes=True)
    path = _sneak_path()[:6]          # stops at B's diode (it would flow backwards there)
    pk = ph(t, dur, 0.15, 0.4)
    glow(d, grow(path, pk), RD, 6)
    if pk >= 1:
        bx, by = GX1 - BR / 2, GY0 + 80
        kx = ph(t, dur, 0.4, 0.45)
        S.line(d, [(bx - 26, by - 26), (bx + 26, by + 26)], RD, 8, kx)
        S.line(d, [(bx - 26, by + 26), (bx + 26, by - 26)], RD, 8, kx)
        S.text(d, (bx, by + 54), "blocked", 26, RD, "Bold", "mm", k=kx)
    kl = ph(t, dur, 0.05, 0.1)
    S.text(d, (GX0 - BR / 2 - 60, GY1 + 168), "diode: current flows one way only", 24, TXT, "Medium", "mm", k=kl)
    kp = ph(t, dur, 0.5, 0.56)
    S.box(d, (1380, 290, 1810, 700), PANEL, GR, 16, 3, kp)
    S.text(d, (1595, 340), "diode on every key", 30, GR, "Bold", "mm", k=kp)
    S.text(d, (1595, 390), "no ghosts, so every", 28, TXT, "Medium", "mm", k=kp)
    S.text(d, (1595, 428), "key can be read", 28, TXT, "Medium", "mm", k=kp)
    S.text(d, (1595, 490), "N-KEY ROLLOVER", 34, AM, "Bold", "mm", k=kp)
    kq = ph(t, dur, 0.72, 0.78)
    S.text(d, (1595, 570), "no diodes? firmware", 26, DIM, "Medium", "mm", k=kq)
    S.text(d, (1595, 606), "blocks the confusing", 26, DIM, "Medium", "mm", k=kq)
    S.text(d, (1595, 642), "combinations instead", 26, DIM, "Medium", "mm", k=kq)


# ---------------- step 3: debounce ----------------
def s_bounce(d, t, dur):
    S.chrome(d, "STEP 3 · DEBOUNCE", "Contacts bounce", "Contacts don't close cleanly. They bounce open and shut for a few milliseconds, and a fast scan could count several presses.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, w, yh, yl = 300, 1340, 340, 560
    S.box(d, (x0 - 40, 270, x0 + w + 40, 640), SCREEN, LINE, 14, 2, k)
    for i in range(1, 10):
        S.line(d, [(x0 + i * w / 10, 290), (x0 + i * w / 10, 620)], mix(SCREEN, LINE, 0.5), 1, k)
    S.text(d, (x0 - 60, yh), "released", 26, AM, "Bold", "rm", k=k)
    S.text(d, (x0 - 60, yl), "pressed", 26, GR, "Bold", "rm", k=k)
    rv = ph(t, dur, 0.08, 0.4)
    trace(d, x0, yh, yl, w, bounce_level, rv, AM, 5, k)
    kb = ph(t, dur, 0.42, 0.48)
    xa, xb = x0 + 0.25 * w, x0 + 0.39 * w
    S.line(d, [(xa, 660), (xa, 680), (xb, 680), (xb, 660)], AM, 3, kb)
    S.text(d, ((xa + xb) / 2, 712), "bounce: typically a few ms", 28, AM, "Bold", "mm", k=kb)
    # scan samples
    ks = ph(t, dur, 0.55, 0.6)
    count, prev = 0, 1
    nmax = int(70 * ph(t, dur, 0.55, 0.8))
    for i in range(nmax):
        u = (i + 0.5) / 70
        v = bounce_level(u)
        if v == 0 and prev == 1: count += 1
        prev = v
        S.circle(d, (x0 + u * w, yh if v else yl), 6, CY, k=ks)
    S.text(d, (x0 + w, 712), f"fast scan sees {count} presses!", 30, RD if count > 1 else DIM, "Bold", "rm", k=ks)
    S.text(d, (x0 + w, 290), "illustration", 22, DIM, "Medium", "rm", k=ks)


def s_debounce(d, t, dur):
    S.chrome(d, "STEP 3 · DEBOUNCE", "One press, not five", "Debouncing: wait until the contact has been stable for a few ms, or report at once and ignore changes for a few ms.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, w = 460, 1200
    lanes = [("raw contact", AM, bounce_level, 0.05),
             ("wait until stable", GR, lambda u: u < 0.46, 0.25),
             ("report, then ignore", CY, lambda u: u < 0.25, 0.5)]
    for i, (name, c, fn, st) in enumerate(lanes):
        y = 290 + i * 180
        kk = ph(t, dur, st, st + 0.06)
        S.text(d, (x0 - 40, y + 50), name, 30, c, "Bold", "rm", k=kk)
        S.line(d, [(x0, y + 110), (x0 + w, y + 110)], LINE, 2, kk)
        trace(d, x0, y, y + 100, w, fn, ph(t, dur, st, st + 0.18), c, 5, kk)
        if i == 1:
            ka = ph(t, dur, st + 0.18, st + 0.22)
            xa, xb = x0 + 0.386 * w, x0 + 0.46 * w
            S.line(d, [(xa, y - 14), (xb, y - 14)], GR, 3, ka)
            S.text(d, ((xa + xb) / 2, y - 36), "stable a few ms", 22, GR, "Bold", "mm", k=ka)
        if i == 2:
            ka = ph(t, dur, st + 0.18, st + 0.22)
            xa, xb = x0 + 0.25 * w, x0 + 0.42 * w
            S.box(d, (xa, y - 6, xb, y + 108), mix(BG, CY, 0.08), mix(BG, CY, 0.4), 6, 2, ka)
            S.text(d, ((xa + xb) / 2, y - 26), "ignore changes", 22, CY, "Bold", "mm", k=ka)
        if i > 0:
            S.pill(d, (x0 + w + 90, y + 50), "1 press", 26, GR, ph(t, dur, st + 0.2, st + 0.24))


# ---------------- step 4: the report ----------------
def s_usage(d, t, dur):
    S.chrome(d, "STEP 4 · THE REPORT", "Not a letter: a usage ID", "The keyboard doesn't send the letter a. It sends a usage ID from a standard table. The key in the A position is hex 04.", t, dur)
    k = prog(t, 0.2, 0.7)
    p = press_at(t, 1.0, 1.8)
    keycap(d, 290, 470, 220, "A", p, k)
    ka = ph(t, dur, 0.1, 0.16)
    S.arrow(d, (420, 470), (540, 470), DIM, 5, ka)
    S.text(d, (480, 430), "sends", 22, DIM, "Medium", "mm", k=ka)
    S.text(d, (290, 640), "usage 0x04", 40, AM, "Bold", "mm", mono=True, k=ka)
    tab = [("A", "04"), ("B", "05"), ("C", "06"), ("Z", "1D"), ("1", "1E"), ("2", "1F"),
           ("Enter", "28"), ("Esc", "29"), ("Backspace", "2A"), ("Tab", "2B"), ("Space", "2C"), ("…", "")]
    kt = ph(t, dur, 0.15, 0.2)
    S.text(d, (1180, 262), "keyboard usage IDs (hex), from the USB HID usage tables", 26, DIM, "Bold", "mm", k=kt)
    for i, (nm, code) in enumerate(tab):
        c, r = i % 3, i // 3
        x, y = 620 + c * 380, 300 + r * 104
        kk = ph(t, dur, 0.2 + i * 0.03, 0.24 + i * 0.03)
        h = i == 0
        S.box(d, (x, y, x + 350, y + 84), mix(BG, AM, 0.2) if h else PANEL, AM if h else LINE, 12, 3 if h else 2, kk)
        S.text(d, (x + 30, y + 42), nm, 32, TXT, "Bold", "lm", k=kk)
        if code: S.text(d, (x + 320, y + 42), code, 36, AM if h else CY, "Bold", "rm", mono=True, k=kk)
    S.text(d, (1180, 744), "key names shown for a US layout: the ID means a position, not a letter", 24, DIM, "Medium", "mm",
           k=ph(t, dur, 0.6, 0.66))


REPORT_LBL = ["modifiers", "reserved", "key 1", "key 2", "key 3", "key 4", "key 5", "key 6"]
def s_bytes(d, t, dur):
    S.chrome(d, "STEP 4 · THE REPORT", "The 8-byte boot report", "The classic boot keyboard report is 8 bytes: one for modifier keys, one reserved, and six slots for keys held at once.", t, dur)
    k = prog(t, 0.2, 0.7)
    pressed = t > dur * 0.6
    vals = ["00", "00", "04" if pressed else "00", "00", "00", "00", "00", "00"]
    x0 = (W - (8 * 150 + 7 * 16)) // 2
    for i in range(8):
        S.text(d, (x0 + i * 166 + 75, 330), f"byte {i}", 22, DIM, "Medium", "mm", k=ph(t, dur, 0.05 + i * 0.02, 0.1 + i * 0.02))
    report_row(d, x0, 360, vals, k, t=t, t0=0.6, step=0.15, hot=(2,) if pressed else (), labels=REPORT_LBL)
    # braces
    def brace(xa, xb, y, s, c, kk, sub=None):
        S.line(d, [(xa, y), (xa, y + 16), (xb, y + 16), (xb, y)], c, 3, kk)
        S.text(d, ((xa + xb) / 2, y + 50), s, 28, c, "Bold", "mm", k=kk)
        if sub: S.text(d, ((xa + xb) / 2, y + 88), sub, 24, DIM, "Medium", "mm", k=kk)
    brace(x0, x0 + 150, 590, "Shift, Ctrl, Alt…", CY, ph(t, dur, 0.2, 0.26), "1 byte")
    brace(x0 + 166, x0 + 316, 590, "unused", DIM, ph(t, dur, 0.3, 0.36), "1 byte")
    brace(x0 + 332, x0 + 8 * 166 - 16, 590, "up to six keys held at the same time", AM, ph(t, dur, 0.4, 0.46), "6 bytes")
    S.pill(d, (x0 + 332 + 75, 262), "you press A", 24, AM, 1.0 if pressed else 0.0)


MOD_NAMES = [("R", "GUI"), ("R", "Alt"), ("R", "Shift"), ("R", "Ctrl"), ("L", "GUI"), ("L", "Alt"), ("L", "Shift"), ("L", "Ctrl")]
def s_mods(d, t, dur):
    S.chrome(d, "STEP 4 · THE REPORT", "One bit per modifier key", "Each bit of byte 0 is one modifier key. Shift + A sends modifier 02 and key 04: facts about keys, not a capital letter.", t, dur)
    k = prog(t, 0.2, 0.7)
    shift = t > dur * 0.45
    bw, gap = 160, 14
    x0 = (W - (8 * bw + 7 * gap)) // 2
    S.text(d, (x0, 262), "byte 0, bit by bit", 28, CY, "Bold", "lm", k=k)
    for i, (side, nm) in enumerate(MOD_NAMES):
        x = x0 + i * (bw + gap)
        on = shift and i == 6
        kk = ph(t, dur, 0.04 + i * 0.03, 0.08 + i * 0.03)
        S.text(d, (x + bw / 2, 312), f"bit {7 - i}", 22, DIM, "Medium", "mm", k=kk)
        S.box(d, (x, 334, x + bw, 424), mix(BG, CY, 0.3) if on else PANEL, CY if on else LINE, 10, 4 if on else 2, kk)
        S.text(d, (x + bw / 2, 379), "1" if on else "0", 44, CY if on else TXT, "Bold", "mm", mono=True, k=kk)
        S.text(d, (x + bw / 2, 452), ("Left " if side == "L" else "Right ") + nm, 22, CY if on else TXT, "Bold", "mm", k=kk)
    S.text(d, (x0 + 8 * (bw + gap) - gap, 262), "GUI = the system key", 22, DIM, "Medium", "rm", k=ph(t, dur, 0.3, 0.36))
    kr = ph(t, dur, 0.45, 0.5)
    S.text(d, (W // 2, 520), "binary 00000010 = hex 02", 28, CY, "Bold", "mm", mono=True, k=kr)
    S.text(d, (330, 615), "Shift + A:", 34, TXT, "Bold", "rm", k=kr)
    report_row(d, 370, 570, ["02", "00", "04", "00", "00", "00", "00", "00"], kr, bw=120, bh=90, gap=14, hot=(0, 2), size=40)
    S.text(d, (W // 2, 730), "still no capital letter: just which keys are down", 30, AM, "Bold", "mm", k=ph(t, dur, 0.62, 0.68))


def s_release(d, t, dur):
    S.chrome(d, "STEP 4 · THE REPORT", "Key up, and too many keys", "Let go and the slot returns to zero. Hold more than six keys and every slot reads hex 01: too many keys. N-key keyboards use a bigger report.", t, dur)
    rows = [("A pressed", ["00", "00", "04", "00", "00", "00", "00", "00"], (2,), AM, 0.05),
            ("A released", ["00", "00", "00", "00", "00", "00", "00", "00"], (), GR, 0.25),
            ("7+ keys held", ["00", "00", "01", "01", "01", "01", "01", "01"], (2, 3, 4, 5, 6, 7), RD, 0.45)]
    for i, (lbl, vals, hot, c, st) in enumerate(rows):
        y = 280 + i * 150
        kk = ph(t, dur, st, st + 0.06)
        S.text(d, (560, y + 50), lbl, 34, c, "Bold", "rm", k=kk)
        report_row(d, 620, y, vals, kk, bw=120, bh=100, gap=14, hot=hot, size=40, hotcol=c)
    ke = ph(t, dur, 0.55, 0.6)
    S.text(d, (W // 2 + 100, 755), "hex 01 = \"error: too many keys\" (rollover error)", 28, RD, "Bold", "mm", k=ke)


# ---------------- step 5: USB ----------------
def s_host(d, t, dur):
    S.chrome(d, "STEP 5 · USB", "The host speaks first", "On USB the keyboard can't just speak up. The computer, the host, runs the bus. Devices only talk when the host asks.", t, dur)
    k = prog(t, 0.2, 0.7)
    hot = press_at(t, dur * 0.25, dur * 0.35, 0.2)
    keyboard_icon(d, 170, 400, 520, 230, k, hot=(1, 0), col=GR, hotk=hot)
    S.text(d, (430, 370), "keyboard (device)", 30, CY, "Bold", "mm", k=k)
    computer_icon(d, 1260, 330, 480, 300, k, "HOST", PU)
    S.text(d, (1500, 300), "computer", 30, PU, "Bold", "mm", k=k)
    glow(d, [(690, 515), (980, 515), (980, 480), (1260, 480)], CY, 5, k * 0.7)
    kq = ph(t, dur, 0.3, 0.36)
    if kq > 0:
        pulse = 0.6 + 0.4 * math.sin(t * 5)
        S.box(d, (360, 660, 500, 710), mix(BG, AM, 0.3 * pulse), AM, 8, 3, kq)
        S.text(d, (430, 685), "report", 24, AM, "Bold", "mm", k=kq)
        S.text(d, (430, 742), "waits to be asked", 26, AM, "Bold", "mm", k=kq)
    kh = ph(t, dur, 0.45, 0.5)
    S.pill(d, (1500, 740), "decides who talks, and when", 24, PU, kh)
    S.text(d, (980, 420), "USB cable", 24, DIM, "Medium", "mm", k=k)


def s_poll(d, t, dur):
    S.chrome(d, "STEP 5 · USB", "Polling: \"anything new?\"", "At a set interval the host asks the keyboard's interrupt endpoint: anything new? Usually it answers NAK. After a press, it sends the report.", t, dur)
    k = prog(t, 0.2, 0.7)
    S.chip(d, 150, 380, 400, 220, "Keyboard", "interrupt endpoint", CY, k, pins=False)
    S.chip(d, 1370, 380, 400, 220, "Host", "USB controller", PU, k, pins=False)
    S.line(d, [(550, 450), (1370, 450)], LINE, 4, k)
    S.line(d, [(550, 530), (1370, 530)], LINE, 4, k)
    S.text(d, (960, 420), "host → keyboard", 22, DIM, "Medium", "mm", k=k)
    S.text(d, (960, 566), "keyboard → host", 22, DIM, "Medium", "mm", k=k)
    cyc = 1.8
    press_t = dur * 0.4
    if t > 0.8:
        n = int((t - 0.8) / cyc); p = ((t - 0.8) % cyc) / cyc
        start = 0.8 + n * cyc
        has_data = start > press_t and int((press_t - 0.8) / cyc) == n - 1
        if p < 0.42:
            x = 1370 - ease(p / 0.42) * 820
            S.box(d, (x - 80, 430, x + 80, 470), PU, PU, 10, 1)
            S.text(d, (x, 450), "anything new?", 20, BG, "Bold", "mm")
        elif p > 0.5:
            x = 550 + ease((p - 0.5) / 0.42) * 820
            c = AM if has_data else DIM
            if has_data: glow(d, [(x - 100, 530), (x + 100, 530)], AM, 30)
            S.box(d, (x - 100, 510, x + 100, 550), c, c, 10, 1)
            S.text(d, (x, 530), "00 00 04 00…" if has_data else "NAK", 22, BG, "Bold", "mm", mono=True)
        S.text(d, (W // 2, 680), f"poll #{n + 1}", 32, DIM, "Bold", "mm", mono=True)
    S.text(d, (350, 650), "key pressed!", 28, GR, "Bold", "mm", k=1.0 if t > press_t else 0)
    S.text(d, (W // 2, 740), "slowed right down to show it", 24, DIM, "Medium", "mm", k=ph(t, dur, 0.1, 0.15))


def s_interval(d, t, dur):
    S.chrome(d, "STEP 5 · USB", "How often does it ask?", "The keyboard asks for a polling interval when it's plugged in: typically 1 to 10 ms. A new report can wait up to one interval.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, x1 = 300, 1700
    span = 40.0
    def tl(y, iv, press, lbl, c, kk):
        S.text(d, (x0 - 30, y), lbl, 28, c, "Bold", "rm", k=kk)
        S.line(d, [(x0, y), (x1, y)], LINE, 3, kk)
        polls = [i * iv for i in range(int(span / iv) + 1)]
        for pt in polls:
            x = x0 + pt / span * (x1 - x0)
            S.line(d, [(x, y - 22), (x, y + 22)], c, 4, kk)
        nxt = min(pt for pt in polls if pt >= press)
        xp, xn = x0 + press / span * (x1 - x0), x0 + nxt / span * (x1 - x0)
        kw = kk * ph(t, dur, 0.3, 0.36)
        glow_dot(d, (xp, y), 9, GR, kw)
        S.text(d, (xp, y - 48), "key ready", 22, GR, "Bold", "mm", k=kw)
        if xn - xp > 4: glow(d, [(xp, y + 40), (xn, y + 40)], AM, 5, kw)
        S.text(d, (xn + 14, y + 64), f"waits {nxt - press:g} ms", 22, AM, "Bold", "lm", k=kw)
    tl(370, 8, 13, "8 ms interval", PU, ph(t, dur, 0.05, 0.12))
    tl(590, 1, 13.4, "1 ms interval", CY, ph(t, dur, 0.18, 0.24))
    kk = ph(t, dur, 0.05, 0.12)
    for ms in range(0, 41, 10):
        x = x0 + ms / span * (x1 - x0)
        S.text(d, (x, 690), f"{ms} ms", 22, DIM, "Medium", "mm", k=kk)
    S.text(d, (x1, 270), "example intervals", 22, DIM, "Medium", "rm", k=kk)
    S.text(d, (W // 2, 760), "typical for keyboards: about 1 to 10 ms", 32, TXT, "Bold", "mm", k=ph(t, dur, 0.55, 0.6))


# ---------------- step 6: inside the computer ----------------
def s_dma(d, t, dur):
    S.chrome(d, "STEP 6 · INSIDE THE COMPUTER", "Into memory, then an interrupt", "The USB host controller writes the report straight into memory, then signals the CPU with an interrupt: new data!", t, dur)
    k = prog(t, 0.2, 0.7)
    S.chip(d, 180, 440, 380, 180, "USB host", "controller", PU, k)
    S.line(d, [(80, 530), (180, 530)], CY, 5, k)
    S.text(d, (60, 410), "from the cable", 22, DIM, "Medium", "lm", k=k)
    # RAM
    S.box(d, (880, 260, 1460, 480), PANEL, AM, 14, 3, k)
    S.text(d, (1170, 290), "memory (RAM)", 26, AM, "Bold", "mm", k=k)
    fill = ph(t, dur, 0.2, 0.4)
    rep = ["00", "00", "04", "00", "00", "00", "00", "00"]
    for r in range(3):
        for c in range(8):
            x, y = 910 + c * 66, 320 + r * 50
            if r == 1 and c < int(fill * 8.99):
                S.box(d, (x, y, x + 58, y + 40), mix(BG, AM, 0.3), AM, 4, 2, k)
                S.text(d, (x + 29, y + 20), rep[c], 22, AM, "Bold", "mm", mono=True, k=k)
            else:
                S.box(d, (x, y, x + 58, y + 40), DARK, LINE, 4, 1, k)
    pw = [(560, 500), (720, 500), (720, 365), (880, 365)]
    S.line(d, pw, LINE, 5, k)
    if 0 < fill < 1:
        glow(d, grow(pw, fill), AM, 6)
    S.text(d, (730, 300), "writes the report", 24, AM, "Bold", "mm", k=ph(t, dur, 0.2, 0.25))
    S.text(d, (730, 330), "directly into memory", 24, AM, "Bold", "mm", k=ph(t, dur, 0.2, 0.25))
    # CPU and interrupt line
    S.chip(d, 1240, 600, 400, 160, "CPU", "busy with other work", BL, k)
    iw = [(560, 580), (900, 580), (900, 680), (1240, 680)]
    ki = ph(t, dur, 0.45, 0.5)
    if ki > 0:
        flick = 0.7 + 0.3 * math.sin(t * 12)
        glow(d, iw, RD, 6, ki * flick)
        S.pill(d, (1010, 740), "INTERRUPT", 26, RD, ki)
    else:
        S.line(d, iw, LINE, 4, k)


def s_handler(d, t, dur):
    S.chrome(d, "STEP 6 · INSIDE THE COMPUTER", "Pause, handle, carry on", "The CPU pauses, runs a short interrupt handler, and the USB driver passes the report up to the HID driver. Then it carries on.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, x1, y = 200, 1720, 290
    S.text(d, (x0, y - 18), "what the CPU is doing", 24, DIM, "Bold", "lm", k=k)
    rv = ph(t, dur, 0.05, 0.5)
    xa, xb = x0 + 0.42 * (x1 - x0), x0 + 0.52 * (x1 - x0)
    xr = x0 + rv * (x1 - x0)
    S.box(d, (x0, y + 10, min(xr, xa), y + 80), mix(BG, BL, 0.3), BL, 8, 2, k)
    S.text(d, (x0 + 30, y + 45), "other work", 26, TXT, "Bold", "lm", k=k if xr > x0 + 200 else 0)
    if xr > xa:
        S.box(d, (xa, y + 10, min(xr, xb), y + 80), mix(BG, RD, 0.35), RD, 8, 3, k)
        S.arrow(d, (xa, y + 150), (xa, y + 88), RD, 4, k)
        S.text(d, (xa, y + 172), "interrupt", 24, RD, "Bold", "mm", k=k)
    if xr > xb:
        S.box(d, (xb, y + 10, xr, y + 80), mix(BG, BL, 0.3), BL, 8, 2, k)
        S.text(d, (xb + 30, y + 45), "back to other work", 26, TXT, "Bold", "lm", k=k if xr > xb + 300 else 0)
    S.text(d, ((xa + xb) / 2, y + 45), "handler", 22, TXT, "Bold", "mm", k=k if xr > xb else 0)
    # software layers
    layers = [("USB driver", PU), ("HID driver", CY), ("input system", GR)]
    kl = ph(t, dur, 0.5, 0.56)
    for i, (nm, c) in enumerate(layers):
        x = 320 + i * 470
        S.box(d, (x, 560, x + 380, 680), PANEL, c, 14, 3, kl)
        S.text(d, (x + 190, 620), nm, 34, c, "Bold", "mm", k=kl)
        if i < 2: S.arrow(d, (x + 390, 620), (x + 460, 620), DIM, 5, kl)
    pk = ph(t, dur, 0.6, 0.85)
    if 0 < pk:
        x = 320 + 190 + pk * 940
        S.box(d, (x - 70, 500, x + 70, 540), AM, AM, 8, 1, kl)
        S.text(d, (x, 520), "report", 22, BG, "Bold", "mm", k=kl)
    S.text(d, (W // 2, 740), "(simplified: real systems have more layers)", 24, DIM, "Medium", "mm", k=kl)


def s_events(d, t, dur):
    S.chrome(d, "STEP 6 · INSIDE THE COMPUTER", "Compare, then key down or up", "The HID driver compares each report with the last. A new code is key down; a missing one is key up. Auto-repeat comes from the OS.", t, dur)
    k = prog(t, 0.2, 0.7)
    stage = 0 if t < dur * 0.4 else 1
    prev = ["00", "00", "00", "00", "00", "00", "00", "00"] if stage == 0 else ["00", "00", "04", "00", "00", "00", "00", "00"]
    new = ["00", "00", "04", "00", "00", "00", "00", "00"] if stage == 0 else ["00", "00", "00", "00", "00", "00", "00", "00"]
    S.text(d, (440, 320), "last report", 28, DIM, "Bold", "rm", k=k)
    S.text(d, (440, 420), "new report", 28, TXT, "Bold", "rm", k=k)
    report_row(d, 470, 280, prev, k, bw=90, bh=80, gap=10, hot=(2,) if stage == 1 else (), size=32, hotcol=DIM)
    report_row(d, 470, 380, new, k, bw=90, bh=80, gap=10, hot=(2,) if stage == 0 else (), size=32)
    S.arrow(d, (1290, 370), (1390, 370), DIM, 5, k)
    if stage == 0: S.pill(d, (1580, 370), "KEY DOWN  04", 32, GR, k)
    else: S.pill(d, (1580, 370), "KEY UP  04", 32, RD, k)
    # hold and auto-repeat
    kh = ph(t, dur, 0.6, 0.66)
    x0, x1, y = 470, 1740, 610
    S.text(d, (440, y), "key held", 28, AM, "Bold", "rm", k=kh)
    glow(d, [(x0, y), (x0 + (x1 - x0) * ph(t, dur, 0.62, 0.9), y)], AM, 6, kh)
    S.text(d, (x0, y + 46), "reports stay the same: no new events from the keyboard", 24, DIM, "Medium", "lm", k=kh)
    S.text(d, (440, y + 130), "on screen", 28, GR, "Bold", "rm", k=kh)
    nr = int(ph(t, dur, 0.66, 0.92) * 14)
    S.text(d, (x0, y + 130), "a" + "a" * nr, 44, GR, "Medium", "lm", mono=True, k=kh)
    S.text(d, (x1, y + 130), "repeats made by the OS", 24, GR, "Bold", "rm", k=ph(t, dur, 0.72, 0.78))


def mini_layout(d, x, y, top, home, lab, c, k, out):
    S.text(d, (x + 290, y - 40), lab, 30, c, "Bold", "mm", k=k)
    for r, row in enumerate((top, home)):
        for i, ch in enumerate(row):
            kx = x + i * 98 + (30 if r else 0)
            ky = y + r * 98
            h = r == 1 and i == 0
            S.box(d, (kx, ky, kx + 86, ky + 86), mix(BG, c, 0.3) if h else PANEL, c if h else LINE, 12, 4 if h else 2, k)
            S.text(d, (kx + 43, ky + 43), ch, 36, TXT, "Bold", "mm", k=k)
    S.arrow(d, (x + 73, y + 196), (x + 73, y + 250), c, 5, k)
    S.text(d, (x + 73, y + 300), out, 72, c, "Bold", "mm", k=k)


def s_layout(d, t, dur):
    S.chrome(d, "STEP 6 · INSIDE THE COMPUTER", "Your layout picks the letter", "The OS looks the usage up in your keyboard layout. On US QWERTY, 04 is a. On French AZERTY, the same key and code types q.", t, dur)
    k = prog(t, 0.2, 0.7)
    S.box(d, (760, 250, 1160, 340), mix(BG, AM, 0.2), AM, 16, 4, k)
    S.text(d, (960, 295), "usage 0x04", 40, AM, "Bold", "mm", mono=True, k=k)
    ka = ph(t, dur, 0.15, 0.2)
    S.arrow(d, (800, 345), (600, 398), DIM, 5, ka)
    S.arrow(d, (1120, 345), (1320, 398), DIM, 5, ka)
    mini_layout(d, 220, 470, "QWERTY", "ASDFG", "US QWERTY", GR, ph(t, dur, 0.25, 0.32), "a")
    mini_layout(d, 1120, 470, "AZERTY", "QSDFG", "French AZERTY", CY, ph(t, dur, 0.45, 0.52), "q")
    S.text(d, (960, 640), "same key,", 28, DIM, "Bold", "mm", k=ph(t, dur, 0.55, 0.6))
    S.text(d, (960, 676), "same code", 28, DIM, "Bold", "mm", k=ph(t, dur, 0.55, 0.6))
    S.text(d, (960, 770), "+ Shift → A / Q", 28, TXT, "Bold", "mm", k=ph(t, dur, 0.7, 0.75))


# ---------------- step 7: to the screen ----------------
def window(d, xy, title, k, focus=False, dim=False):
    x0, y0, x1, y1 = xy
    c = CY if focus else LINE
    S.box(d, xy, mix(BG, PANEL, 0.6 if dim else 1.0), c, 12, 4 if focus else 2, k)
    S.box(d, (x0, y0, x1, y0 + 44), mix(BG, c, 0.25), c, 12, 2, k)
    S.text(d, (x0 + 20, y0 + 22), title, 22, TXT if focus else DIM, "Bold", "lm", k=k)


def s_focus(d, t, dur):
    S.chrome(d, "STEP 7 · TO THE SCREEN", "Only the focused window hears it", "The OS sends the key event only to the window with keyboard focus: the one with the blinking cursor.", t, dur)
    k = prog(t, 0.2, 0.7)
    S.box(d, (150, 440, 470, 600), PANEL, BL, 16, 3, k)
    S.text(d, (310, 495), "OS", 40, BL, "Bold", "mm", k=k)
    S.text(d, (310, 550), "key event: \"a\"", 26, TXT, "Bold", "mm", k=k)
    window(d, (720, 260, 1300, 560), "music player", k, dim=True)
    window(d, (1250, 300, 1780, 600), "file browser", k, dim=True)
    window(d, (860, 430, 1560, 790), "text editor  (focused)", k, focus=True)
    S.box(d, (890, 500, 1530, 760), SCREEN, LINE, 6, 1, k)
    typed = t > dur * 0.55
    S.text(d, (920, 560), "Dear Sam, here is" + (" a" if typed else ""), 34, TXT, "Medium", "lm", k=k)
    tx = 920 + S.textlen(d, "Dear Sam, here is" + (" a" if typed else ""), 34, "Medium") + 4
    if int(t * 2) % 2 == 0: d.rectangle([tx, 538, tx + 4, 582], fill=S.fade(CY, k))
    pk = ph(t, dur, 0.3, 0.55)
    path = [(470, 520), (700, 520), (760, 620), (880, 620)]
    S.line(d, path, LINE, 4, k)
    if 0 < pk < 1: glow_dot(d, grow(path, pk)[-1], 12, AM)
    if pk >= 1: glow(d, path, AM, 4, 0.8)
    S.pill(d, (1210, 820 - 30), "focus", 24, CY, ph(t, dur, 0.2, 0.25))


def s_glyph(d, t, dur):
    S.chrome(d, "STEP 7 · TO THE SCREEN", "From curves to pixels", "The app inserts the letter at the cursor. The font stores it as curves, and a font renderer turns those curves into pixels.", t, dur)
    k = prog(t, 0.2, 0.7)
    S.text(d, (380, 270), "in the font: an outline", 26, CY, "Bold", "mm", k=k)
    if k > 0.01:
        d.text((380, 560), "a", font=S.font(420, "Medium"), fill=BG, anchor="mm", stroke_width=5, stroke_fill=S.fade(CY, k))
    ka = ph(t, dur, 0.3, 0.35)
    S.arrow(d, (620, 520), (740, 520), DIM, 5, ka)
    S.text(d, (680, 480), "render", 22, DIM, "Medium", "mm", k=ka)
    n, cs = 18, 24
    gx, gy = 780, 310
    bmp = glyph_bitmap("a", n)
    kc = ph(t, dur, 0.33, 0.38)
    rev = int(ph(t, dur, 0.35, 0.65) * n * n)
    for j in range(n * n):
        r, c = divmod(j, n)
        v = bmp[r][c] / 255 if j < rev else 0
        d.rectangle([gx + c * cs, gy + r * cs, gx + c * cs + cs - 2, gy + r * cs + cs - 2],
                    fill=S.fade(mix(SCREEN, TXT, v), kc))
    S.text(d, (gx + n * cs / 2, 270), "pixels, with soft edges", 26, AM, "Bold", "mm", k=kc)
    S.text(d, (gx + n * cs / 2, gy + n * cs + 36), "(enlarged)", 22, DIM, "Medium", "mm", k=kc)
    kd = ph(t, dur, 0.68, 0.74)
    S.arrow(d, (1240, 520), (1340, 520), DIM, 5, kd)
    S.box(d, (1360, 420, 1780, 620), SCREEN, LINE, 10, 2, kd)
    S.text(d, (1390, 520), "here is a", 36, TXT, "Medium", "lm", k=kd)
    cx = 1390 + S.textlen(d, "here is a", 36, "Medium") + 4
    if int(t * 2) % 2 == 0: d.rectangle([cx, 498, cx + 4, 542], fill=S.fade(CY, kd))
    S.text(d, (1570, 390), "drawn at the cursor", 24, GR, "Bold", "mm", k=kd)


def s_refresh(d, t, dur):
    S.chrome(d, "STEP 7 · TO THE SCREEN", "Wait for the next refresh", "Every window is combined into the next frame, often with the GPU's help. The screen shows it on its next refresh.", t, dur)
    k = prog(t, 0.2, 0.7)
    # layers being composited
    for i, (c, nm) in enumerate(((LINE, "other windows"), (BL, "desktop"), (CY, "your app"))):
        off = 26 * (2 - i) * (1 - ph(t, dur, 0.15, 0.3))
        x, y = 200 + i * 30 + off, 290 + i * 40 - off
        S.box(d, (x, y, x + 340, y + 220), mix(BG, c, 0.25), c, 10, 3, k)
        S.text(d, (x + 20, y + 30), nm, 22, TXT, "Bold", "lm", k=k)
    S.text(d, (400, 620), "combined into one frame", 26, DIM, "Bold", "mm", k=k)
    S.arrow(d, (620, 420), (720, 420), DIM, 5, k)
    # the display
    shown_t = dur * 0.55
    computer_icon(d, 760, 290, 440, 260, k)
    if t > shown_t: S.text(d, (980, 420), "here is a", 40, TXT, "Medium", "mm", k=k)
    else: S.text(d, (980, 420), "here is", 40, TXT, "Medium", "mm", k=k)
    S.text(d, (1500, 340), "a faster refresh rate", 28, TXT, "Bold", "mm", k=ph(t, dur, 0.7, 0.75))
    S.text(d, (1500, 380), "means a shorter wait", 28, TXT, "Bold", "mm", k=ph(t, dur, 0.7, 0.75))
    # refresh timeline
    kt = ph(t, dur, 0.25, 0.3)
    x0, x1, y = 200, 1720, 720
    span = 55.0
    S.line(d, [(x0, y), (x1, y)], LINE, 3, kt)
    for i in range(4):
        ms = i * 1000 / 60
        x = x0 + ms / span * (x1 - x0)
        S.line(d, [(x, y - 24), (x, y + 24)], CY, 5, kt)
        S.text(d, (x, y + 50), f"{ms:.1f} ms", 22, DIM, "Medium", "mm", k=kt)
    S.text(d, (x0, y - 50), "refreshes", 22, CY, "Bold", "lm", k=kt)
    S.pill(d, (x1 - 80, y - 50), "example: 60 Hz", 22, AM, kt)
    xr = x0 + 22 / span * (x1 - x0); xs = x0 + 33.33 / span * (x1 - x0)
    kr = ph(t, dur, 0.35, 0.4)
    glow_dot(d, (xr, y), 9, AM, kr)
    S.text(d, (xr, y - 50), "frame ready", 22, AM, "Bold", "mm", k=kr)
    glow(d, [(xr, y), (xr + (xs - xr) * ph(t, dur, 0.4, 0.55), y)], AM, 5, kr)
    ks = 1.0 if t > shown_t else 0.0
    glow_dot(d, (xs, y), 11, GR, ks)
    S.text(d, (xs + 20, y - 50), "shown!", 24, GR, "Bold", "lm", k=ks)


def s_latency(d, t, dur):
    S.chrome(d, "STEP 7 · TO THE SCREEN", "Adding it all up", "Scan and debounce, the poll, the OS and app, the next refresh. Typically a few to a few tens of milliseconds in total.", t, dur)
    k = prog(t, 0.2, 0.7)
    segs = [("scan + debounce", CY, 0.16), ("wait for poll", PU, 0.18), ("OS + app", BL, 0.2), ("draw + refresh", GR, 0.46)]
    x0, x1, y = 200, 1720, 380
    x = x0
    for i, (nm, c, f) in enumerate(segs):
        kk = ph(t, dur, 0.08 + i * 0.12, 0.14 + i * 0.12)
        w = (x1 - x0) * f
        S.box(d, (x + 3, y, x + w - 3, y + 110), mix(BG, c, 0.3), c, 10, 3, kk)
        S.text(d, (x + w / 2, y + 55), nm, 24, TXT, "Bold", "mm", k=kk)
        x += w
    S.text(d, (x0, y - 40), "keypress", 24, DIM, "Bold", "lm", k=k)
    S.text(d, (x1, y - 40), "letter on screen", 24, DIM, "Bold", "rm", k=k)
    S.text(d, (W // 2, y + 150), "illustration: widths not to scale, every system differs", 24, DIM, "Medium", "mm", k=ph(t, dur, 0.5, 0.55))
    kt = ph(t, dur, 0.58, 0.64)
    S.text(d, (W // 2, 650), "typical total: a few ms to a few tens of ms", 46, AM, "Bold", "mm", k=kt)
    S.text(d, (W // 2, 730), "still quicker than the blink of an eye", 30, TXT, "Medium", "mm", k=ph(t, dur, 0.7, 0.75))


# ---------------- outro ----------------
def s_recap(d, t, dur):
    S.chrome(d, "RECAP", "From fingertip to pixel", "Switch, scan, debounce, an 8-byte report, a USB poll, an interrupt, your layout, and the next frame.", t, dur)
    st = [("Switch", "contact closes", CY), ("Scan", "rows × columns", AM), ("Debounce", "a few ms", RD),
          ("Report", "usage 04", AM), ("Poll", "host asks", PU), ("Interrupt", "CPU alerted", RD),
          ("Layout", "a or q", BL), ("Draw", "next frame", GR)]
    x0, x1, y = 200, 1720, 480
    S.line(d, [(x0, y), (x0 + (x1 - x0) * ph(t, dur, 0.05, 0.75), y)], LINE, 6)
    for i, (nm, sub, c) in enumerate(st):
        s0 = 0.05 + i * 0.09
        kk = ph(t, dur, s0, s0 + 0.05)
        x = x0 + i * (x1 - x0) / 7
        glow_dot(d, (x, y), 18, c, kk)
        S.text(d, (x, y - 64), nm, 32, c, "Bold", "mm", k=kk)
        S.text(d, (x, y + 60), sub, 22, DIM, "Medium", "mm", k=kk)
    u = ph(t, dur, 0.05, 0.75)
    glow_dot(d, (x0 + (x1 - x0) * u, y), 9, TXT, 1.0 if 0 < u < 1 else 0)
    kc = ph(t, dur, 0.78, 0.84)
    keycap(d, 760, 680, 110, "A", press_at(t, dur * 0.8, dur * 0.86), kc)
    S.arrow(d, (850, 680), (1010, 680), DIM, 5, kc)
    S.box(d, (1030, 630, 1180, 730), SCREEN, LINE, 10, 2, kc)
    S.text(d, (1105, 680), "a", 60, TXT, "Medium", "mm", k=kc if t > dur * 0.86 else 0)


def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    # a generic plug and socket with a question mark
    S.box(d, (760, 250, 1000, 340), PANEL, CY, 12, 4, k)
    S.box(d, (1000, 270, 1080, 320), LINE, LINE, 4, 1, k)
    S.box(d, (1040, 280, 1060, 310), BG, BG, 2, 1, k)
    S.text(d, (1150, 295), "?", 80, AM, "Bold", "mm", k=k)
    S.text(d, (W // 2, 430), "NEXT EPISODE", 34, CY, "Bold", "mm", k=k)
    S.text(d, (W // 2, 530), "How does USB know", 76, TXT, "Bold", "mm", k=k)
    S.text(d, (W // 2, 620), "what you just plugged in?", 76, TXT, "Bold", "mm", k=k)
    S.text(d, (W // 2, 760), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))


SCENES = [("01_hook", s_hook, 9), ("02_cover", s_cover, 10),
          ("03_press", s_press, 12), ("04_pullup", s_pullup, 12),
          ("05_matrix_why", s_matrix_why, 12), ("06_scan", s_scan, 12), ("07_keymap", s_keymap, 12),
          ("08_ghost", s_ghost, 12), ("09_diodes", s_diodes, 12),
          ("10_bounce", s_bounce, 12), ("11_debounce", s_debounce, 12),
          ("12_usage", s_usage, 12), ("13_bytes", s_bytes, 12), ("14_mods", s_mods, 12), ("15_release", s_release, 12),
          ("16_host", s_host, 12), ("17_poll", s_poll, 12), ("18_interval", s_interval, 12),
          ("19_dma", s_dma, 12), ("20_handler", s_handler, 12), ("21_events", s_events, 12), ("22_layout", s_layout, 12),
          ("23_focus", s_focus, 12), ("24_glyph", s_glyph, 12), ("25_refresh", s_refresh, 12), ("26_latency", s_latency, 12),
          ("27_recap", s_recap, 12), ("28_end", s_end, 7)]

NARRATION = {
 "01_hook": "You press a key, and a letter appears on your screen. But in those few milliseconds, a surprising chain of events just happened. And here's the twist: your keyboard never sent the letter at all. Let's follow one key press, from fingertip to pixels.",
 "02_cover": "We'll zoom in, step by step. First, the switch under the key. Then the grid of wires the keyboard scans. Then debouncing, and the code the keyboard actually sends. Then the U S B link, what happens inside the computer, and finally, how the letter reaches your screen.",
 "03_press": "Step one: the switch. Under every key is a simple switch. Press it, and two contacts touch. In many keyboards, a rubber dome pushes two thin plastic sheets together, so printed contacts on them meet. Mechanical keyboards give each key its own switch, with metal contacts. Either way, it's open, or closed.",
 "04_pullup": "How does a chip notice? A small microcontroller inside the keyboard watches the switch through an input pin. A pull-up resistor holds that pin at a high voltage. When the switch closes, it connects the pin to ground, and the voltage drops low. So high means released, and low means pressed.",
 "05_matrix_why": "Step two: the key matrix. A full keyboard has around a hundred keys. A separate wire for every key would need about a hundred inputs. So instead, the keys are wired in a grid. For example, eight rows and thirteen columns give a hundred and four crossing points, using just twenty one wires.",
 "06_scan": "Each key sits where one row crosses one column. The microcontroller scans the grid. It drives one column low, and reads every row. If a row reads low too, the key at that crossing must be pressed. Then it moves to the next column, round and round.",
 "07_keymap": "When the scan finds a pressed key, the firmware only knows a position, say, row two, column one. A lookup table in the firmware, called a keymap, turns that position into a code for that key. And it repeats the whole scan many times a second, typically hundreds or even thousands.",
 "08_ghost": "But a simple grid has a weakness. Hold three keys at three corners of a rectangle. Now current can sneak backwards through those three switches, and the key at the fourth corner looks pressed too, even though nobody touched it. That phantom key is called a ghost.",
 "09_diodes": "The fix is a diode in series with every switch. A diode lets current flow only one way, so the backward path is blocked. With a diode on every key, the controller can tell every key apart. That's called N key rollover. Keyboards without diodes usually just block the confusing combinations instead.",
 "10_bounce": "Step three: debouncing. When two contacts close, they don't meet cleanly. They bounce, opening and closing several times, typically for a few milliseconds. The microcontroller scans so quickly that, without some help, it would see one press as several quick presses.",
 "11_debounce": "So the firmware debounces the signal. One way: when a key changes, wait until it's been stable for a few milliseconds, then believe it. Another way: report the press straight away, then ignore any more changes for a few milliseconds. Either way, one press counts as exactly one press.",
 "12_usage": "Step four: the report. The keyboard doesn't send the letter a. It sends a number called a usage I D, from a standard table in the U S B specification for human interface devices, or H I D. The key in the A position is usage hex, zero four. B is hex, zero five, and so on.",
 "13_bytes": "Those numbers travel in a small packet called a report. The classic boot keyboard report is eight bytes long. The first byte holds the modifier keys. The second byte is reserved. And the last six bytes have room for up to six keys held at once. Press A, and the third byte becomes hex, zero four.",
 "14_mods": "Each bit of that first byte is one modifier key: Control, Shift, Alt, and the system key, which the spec calls G U I, on the left and on the right. Hold left Shift with A, and the report says modifiers hex, zero two, plus key hex, zero four. Still not a capital letter. Just facts about keys.",
 "15_release": "Let go, and the keyboard sends a new report with that slot back to zero. So the computer always knows which keys are down. Hold more than six keys, and the boot report runs out of room. Every slot fills with hex, zero one, meaning too many keys. N key keyboards use a bigger report format.",
 "16_host": "Step five: the U S B link. On U S B, the keyboard can't just speak up when you press a key. The computer, called the host, is in charge of the bus. It decides who talks, and when. Devices only send data when asked.",
 "17_poll": "So the host polls. The keyboard has an interrupt endpoint, a little mailbox for its reports. At a set interval, the host asks it: anything new? Most of the time, the keyboard answers with a NAK, meaning nothing new. But after your key press, it answers with the eight byte report.",
 "18_interval": "How often does the host ask? The keyboard requests an interval when it's first plugged in. For keyboards, it's typically somewhere between one and ten milliseconds. So once a new report is ready, it may wait up to one whole interval before the host collects it. On average, about half an interval.",
 "19_dma": "Step six: inside the computer. The U S B host controller is a chip that handles all this polling by itself. When the report arrives, the controller writes it straight into memory, without needing the C P U. Then it signals the C P U with an interrupt, meaning: new data is waiting.",
 "20_handler": "The C P U pauses what it was doing, and runs a short piece of code called an interrupt handler. The U S B driver looks at the new data, and passes the report up to the H I D driver. Then the C P U goes back to its other work.",
 "21_events": "The H I D driver compares the new report with the previous one. A code that just appeared means a key went down. A code that just disappeared means a key came up. Hold a key, and the reports just stay the same. The repeating letters come from the O S, not from the keyboard.",
 "22_layout": "Now, finally, a letter. The O S looks up the usage in your chosen keyboard layout. On a US qwerty layout, usage hex, zero four, is the letter a. Switch to a French azerty layout, and the very same key, sending the very same code, types a q. Hold Shift, and you get the capital.",
 "23_focus": "Step seven: to the screen. Your computer might have lots of windows open. The O S sends the key event only to the one that has keyboard focus, usually the one with the blinking cursor. The event joins that app's queue, and the app reads it.",
 "24_glyph": "The app inserts the letter into its text, at the cursor. Now it has to be drawn. A font stores each letter as an outline made of curves. A font renderer turns those curves into pixels, with softly shaded edges, so the letter looks smooth at any size.",
 "25_refresh": "Next, the app's new pixels are combined with every other window into one full frame, usually with help from the G P U. Then the display shows that frame on its next refresh. A sixty hertz screen refreshes about every sixteen point seven milliseconds, so this alone can add up to a frame of waiting.",
 "26_latency": "So how long does the whole trip take? Add it up. Scanning and debouncing, waiting for the poll, the O S and the app, and the next screen refresh. Typically, it's somewhere from a few milliseconds to a few tens of milliseconds. It varies a lot between keyboards, computers and screens.",
 "27_recap": "Let's recap. A switch closes. The keyboard scans its matrix, and debounces the contact. It packs a usage I D into an eight byte report. The host polls for it, and an interrupt wakes the driver. Your layout turns the code into a letter, and the app draws it on the next frame.",
 "28_end": "Next episode: how does U S B know what you just plugged in? Subscribe so you don't miss it.",
}
OUTPUT = "what_happens_when_you_press_a_key_ep3_narrated.mp4"


def render(name, fn, dur): S.render_to("ep3", name, fn, dur)


if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    S.preview("ep3", SCENES)
