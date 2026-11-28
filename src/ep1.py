"""Tech 101, episode 1: How does a computer actually boot?  (chalk style, what-happens-if format)"""
import functools, math, sys
import style
from style import clamp, prog, grow, mix

S = style.get("chalk")
W, H, FPS = S.W, S.H, S.FPS
VOICE, SPEED, LANG = S.VOICE, S.SPEED, S.LANG

# the six stops of the journey, each with its own chalk colour (used the same way throughout)
STAGES = [("Power", S.HILITE, "rails settle"), ("Reset", S.BAD, "first instruction"),
          ("Firmware", S.ACCENT, "check the hardware"), ("Boot device", S.GOOD, "find the system"),
          ("Bootloader", S.EXTRA, "load the kernel"), ("Kernel", S.BLUE, "start everything")]
C_PWR, C_RST, C_FW, C_DEV, C_BL, C_K = [c for _, c, _ in STAGES]


# ---------------- chalk drawing helpers ----------------
def write(d, xy, s, size=36, col=None, t=1e9, a=0.0, b=None, w="Bold", anchor="mm", mono=False):
    """Text that appears letter by letter, as if written on the board."""
    if b is None: b = a + max(0.35, len(s) * 0.035)
    k = clamp((t - a) / (b - a)) if b > a else 1.0
    if k <= 0: return
    n = max(1, int(round(len(s) * k)))
    tw = S.textlen(d, s, size, w, mono)
    x, y = xy
    if anchor[0] == "m": x -= tw / 2
    elif anchor[0] == "r": x -= tw
    S.text(d, (x, y), s[:n], size, col, w, "l" + anchor[1], mono)

def stroke(d, pts, col=None, k=1.0, width=5):
    if k > 0.01: S.line(d, grow(pts, k), col, width)

def head(d, p, ang, col, width=5, hl=24):
    S.line(d, [(p[0] - hl * math.cos(ang - .45), p[1] - hl * math.sin(ang - .45)), p,
               (p[0] - hl * math.cos(ang + .45), p[1] - hl * math.sin(ang + .45))], col, width)

def garrow(d, a, b, col=None, k=1.0, width=5):
    """A straight arrow that draws itself from a to b."""
    if k <= 0.01: return
    col = col or S.TXT
    e = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
    S.line(d, [a, e], col, width)
    head(d, e, math.atan2(b[1] - a[1], b[0] - a[0]), col, width)

def carrow(d, pts, col=None, k=1.0, width=5):
    """A polyline arrow that draws itself."""
    if k <= 0.01: return
    col = col or S.TXT
    g = grow(pts, k)
    if len(g) < 2: return
    S.line(d, g, col, width)
    p, q = g[-1], g[-2]
    for j in range(len(g) - 2, -1, -1):
        if math.hypot(p[0] - g[j][0], p[1] - g[j][1]) > 12: q = g[j]; break
    head(d, p, math.atan2(p[1] - q[1], p[0] - q[0]), col, width)

def sketch(d, xy, col=None, k=1.0, fill=None, r=16, width=4):
    """A box whose outline is drawn round, then filled."""
    if k <= 0.01: return
    if k >= 0.999:
        S.box(d, xy, fill or S.PANEL, col or S.LINE, r, width); return
    d.rounded_rectangle(xy, r, fill=S.fade(fill or S.PANEL, k * 0.8))
    pts = S._rr_points(xy, r)
    stroke(d, pts + [pts[0]], col or S.LINE, k, width)

def gcircle(d, c, r, col=None, k=1.0, width=4, fill=None):
    if k <= 0.01: return
    if fill: S.circle(d, c, r, fill, None, k=k)
    n = max(24, int(r / 3))
    pts = [(c[0] + r * math.cos(-math.pi / 2 + 2 * math.pi * i / n), c[1] + r * math.sin(-math.pi / 2 + 2 * math.pi * i / n))
           for i in range(n + 1)]
    stroke(d, pts, col, k, width)

def tick(d, cx, cy, s, col=None, k=1.0, width=6):
    stroke(d, [(cx - s, cy), (cx - s * 0.3, cy + s * 0.7), (cx + s, cy - s * 0.8)], col or S.GOOD, k, width)

def cross(d, cx, cy, s, col=None, k=1.0, width=6):
    col = col or S.BAD
    stroke(d, [(cx - s, cy - s), (cx + s, cy + s)], col, clamp(k * 2), width)
    stroke(d, [(cx + s, cy - s), (cx - s, cy + s)], col, clamp(k * 2 - 1), width)

def power_icon(d, cx, cy, r, col, k=1.0, width=8):
    a0, a1 = -90 + 38, 270 - 38
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / 40)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / 40)))
           for i in range(41)]
    stroke(d, pts, col, clamp(k * 1.4), width)
    stroke(d, [(cx, cy - r * 1.2), (cx, cy - r * 0.2)], col, clamp(k * 1.4 - 0.4), width)

def dot(d, c, r, col, k=1.0):
    if k > 0.01: S.circle(d, c, r, col, None, k=k)

def along(pts, u):
    """Point at fraction u along a polyline."""
    g = grow(pts, clamp(u))
    return g[-1]

def monitor(d, x0, y0, x1, y1, k=1.0, login=1.0):
    sketch(d, (x0, y0, x1, y1), S.LINE, k, r=10)
    cx = (x0 + x1) / 2
    stroke(d, [(cx, y1), (cx, y1 + 30)], S.LINE, k, 5)
    stroke(d, [(cx - 50, y1 + 32), (cx + 50, y1 + 32)], S.LINE, k, 5)
    if login > 0.01:
        h = y1 - y0
        gcircle(d, (cx, y0 + h * 0.36), h * 0.13, S.TXT, login, 4)
        sketch(d, (cx - (x1 - x0) * 0.3, y0 + h * 0.62, cx + (x1 - x0) * 0.3, y0 + h * 0.8), S.ACCENT, login, r=6, width=3)

def chip8(d, x0, y0, x1, y1, label, col, k=1.0, size=28):
    """A small 8-pin chip."""
    if k <= 0.01: return
    for i in range(4):
        y = y0 + 22 + i * (y1 - y0 - 44) / 3
        d.rectangle([x0 - 18, y - 6, x0, y + 6], fill=S.fade(S.DIM, k))
        d.rectangle([x1, y - 6, x1 + 18, y + 6], fill=S.fade(S.DIM, k))
    sketch(d, (x0, y0, x1, y1), col, k, r=8)
    S.text(d, ((x0 + x1) / 2, (y0 + y1) / 2), label, size, col, "Bold", "mm", k=k)

def ram_stick(d, x0, y0, x1, y1, col, k=1.0, spd=False):
    sketch(d, (x0, y0, x1, y1), col, k, r=6)
    if k <= 0.01: return
    n = 8; cw = (x1 - x0 - 40) / n
    for i in range(n):
        cx = x0 + 20 + i * cw
        d.rectangle([cx + 6, y0 + 16, cx + cw - 6, y1 - 34], fill=S.fade(mix(S.PANEL, col, 0.35), k))
    for i in range(int((x1 - x0) / 16)):
        d.rectangle([x0 + 8 + i * 16, y1 - 18, x0 + 16 + i * 16, y1 - 4], fill=S.fade(S.HILITE, k * 0.7))
    if spd:
        d.rectangle([x1 - 70, y1 - 32, x1 - 40, y1 - 22], fill=S.fade(S.HILITE, k))

def cores(d, x0, y0, n_cols, n_rows, size, gap, lit, k=1.0, col=None, labels=False, t=0):
    """A grid of processor cores; lit is a list of how lit each is (0..1)."""
    col = col or C_RST
    for i in range(n_cols * n_rows):
        cx, cy = x0 + (i % n_cols) * (size + gap), y0 + (i // n_cols) * (size + gap)
        L = lit[i] if i < len(lit) else 0
        sketch(d, (cx, cy, cx + size, cy + size), mix(S.DIM, col, L), k, fill=mix(S.PANEL, col, 0.25 * L), r=10)
        if labels:
            S.text(d, (cx + size / 2, cy + size / 2), f"core {i}", 24, mix(S.DIM, S.TXT, L), "Bold", "mm", k=k)

def strip(d, idx, t):
    """'You are here' strip at the top right: the six stops, the current one pulsing."""
    x0, x1, y = 1450, 1800, 96
    S.line(d, [(x0, y), (x1, y)], S.DIM, 3)
    for i, (n, c, _) in enumerate(STAGES):
        x = x0 + i * (x1 - x0) / 5
        if i < idx: dot(d, (x, y), 10, c)
        elif i == idx:
            dot(d, (x, y), 13 + 2 * math.sin(t * 4), c)
        else:
            S.circle(d, (x, y), 9, S.BG, S.DIM, 3)
    S.text(d, (x1, y + 38), STAGES[idx][0].lower(), 24, STAGES[idx][1], "Bold", "rm")

def tag(d, xy, s, col=None, k=1.0, size=24):
    S.pill(d, xy, s, size, col or S.DIM, k)


# ---------------- journey map (cover + recap) ----------------
JPTS = [(200 + i * 265, 440 if i % 2 == 0 else 650) for i in range(6)]
JPATH = JPTS + [(1700, 470)]

def journey(d, t, a=0.3, per=0.55, travel=True, words=None):
    kpath = prog(t, a, a + per * 6 + 0.3)
    stroke(d, JPATH, S.DIM, kpath, 4)
    for i, ((x, y), (name, c, sub)) in enumerate(zip(JPTS, STAGES)):
        kk = prog(t, a + i * per, a + i * per + 0.4)
        if kk <= 0: continue
        S.circle(d, (x, y), 56, S.BG, None, k=1.0)
        gcircle(d, (x, y), 56, c, kk, 5, fill=S.PANEL)
        S.text(d, (x, y), str(i + 1), 44, c, "Bold", "mm", k=kk)
        top = y < 500
        ly = y - 120 if top else y + 100
        write(d, (x, ly), name, 38, c, t, a + i * per + 0.1, a + i * per + 0.5)
        write(d, (x, ly + 40), (words or [s for _, _, s in STAGES])[i], 26, S.DIM, t, a + i * per + 0.3, a + i * per + 0.8, "Medium")
    kl = prog(t, a + 6 * per, a + 6 * per + 0.5)
    monitor(d, 1640, 390, 1820, 510, kl, kl)
    write(d, (1730, 590), "login", 30, S.TXT, t, a + 6 * per + 0.3)
    if travel and t > a:
        u = ((t - a) / (per * 6 + 0.6)) % 1.15
        if u <= 1: dot(d, along(JPATH, u), 12, S.TXT)


# =====================================================================
# chapter 0: hook + cover
# =====================================================================
def s_hook(d, t, dur):
    S.chrome(d, "", "", "Press one button, and seconds later there's a login screen. But the processor starts out knowing almost nothing.", t, dur)
    cx, cy, r = 400, 540, 140
    gcircle(d, (cx, cy), r, S.LINE, prog(t, 0.1, 0.8), 6, fill=S.PANEL)
    press = prog(t, 1.3, 1.5) - prog(t, 1.5, 1.8)
    power_icon(d, cx, cy + 8, r * 0.48 * (1 - 0.06 * press), mix(S.TXT, S.HILITE, prog(t, 1.3, 1.6)), prog(t, 0.3, 1.2), 10)
    if t > 1.4:
        for g in range(3):
            u = ((t - 1.4) * 0.6 + g / 3) % 1.0
            gcircle(d, (cx, cy), r + 20 + u * 120, mix(S.BG, S.HILITE, 0.8 * (1 - u)), 1.0, 4)
    path = [(cx + r + 60, cy)] + [(620 + i * 20, cy + 70 * math.sin(i * 0.16)) for i in range(34)] + [(1330, cy)]
    kp = prog(t, 1.8, 4.2)
    stroke(d, path, S.DIM, kp, 4)
    for i, (_, c, _) in enumerate(STAGES):
        u = (i + 0.7) / 6.6
        if kp >= u: dot(d, along(path, u), 16, c, prog(t, 1.8 + u * 2.4, 2.1 + u * 2.4))
    write(d, (980, 360), "what happens in here?", 40, S.HILITE, t, 2.4, 3.4)
    kl = prog(t, 3.8, 4.4)
    monitor(d, 1380, 380, 1780, 660, kl, prog(t, 4.3, 4.9))
    write(d, (1580, 780), "a few seconds later", 32, S.DIM, t, 4.6, 5.4, "Medium")
    write(d, (cx, 780), "press", 34, S.HILITE, t, 1.2, 1.6)

def s_cover(d, t, dur):
    S.chrome(d, "", "The journey we'll follow", "Six stops: power, reset, firmware, finding a boot device, the bootloader, and the kernel. Then the login screen.", t, dur)
    journey(d, t)


# =====================================================================
# STEP 1 · POWER
# =====================================================================
def s_button(d, t, dur):
    S.chrome(d, "STEP 1 · POWER", "The button is only a request", "Standby power keeps a small circuit awake. Your press makes it ask the power supply to switch on.", t, dur)
    strip(d, 0, t)
    # wall plug
    k0 = prog(t, 0.2, 0.7)
    stroke(d, [(110, 540), (190, 540)], S.LINE, k0, 6)
    sketch(d, (190, 500, 250, 580), S.LINE, k0, r=8)
    write(d, (220, 620), "mains", 26, S.DIM, t, 0.5, w="Medium")
    # power supply
    sketch(d, (300, 380, 700, 760), C_PWR, prog(t, 0.3, 1.1))
    write(d, (500, 420), "power supply", 36, C_PWR, t, 0.8, 1.4)
    stroke(d, [(250, 540), (300, 540)], S.LINE, k0, 6)
    # motherboard
    sketch(d, (980, 330, 1780, 800), S.LINE, prog(t, 0.6, 1.5), fill=mix(S.PANEL, S.BG, 0.3))
    write(d, (1380, 370), "motherboard", 36, S.TXT, t, 1.1, 1.7)
    sketch(d, (1040, 590, 1380, 730), S.GOOD, prog(t, 1.0, 1.6))
    write(d, (1210, 640), "power-on circuit", 28, S.GOOD, t, 1.4, 2.0)
    write(d, (1210, 690), "(awake on standby)", 24, S.DIM, t, 1.7, 2.3, "Medium")
    # standby rail: always on
    ks = prog(t, 1.6, 2.2)
    stroke(d, [(700, 680), (1040, 680)], S.GOOD, ks, 5)
    write(d, (870, 720), "standby 5 V: always on", 26, S.GOOD, t, 1.9, 2.6)
    if t > 2.2:
        for i in range(3):
            u = ((t - 2.2) * 0.7 + i / 3) % 1.0
            dot(d, (700 + 340 * u, 680), 8, S.GOOD)
    # the button
    bx, by = 1620, 660
    gcircle(d, (bx, by), 56, S.LINE, prog(t, 1.2, 1.8), 5, fill=S.PANEL)
    pressed = prog(t, 2.8, 3.0)
    power_icon(d, bx, by + 4, 22, mix(S.TXT, S.HILITE, pressed), prog(t, 1.5, 2.0), 6)
    stroke(d, [(1564, 660), (1380, 660)], S.LINE, prog(t, 1.6, 2.0), 4)
    if 2.8 < t < 4.0:
        gcircle(d, (bx, by), 70 + (t - 2.8) * 60, mix(S.BG, S.HILITE, 1 - (t - 2.8) / 1.2), 1.0, 4)
    write(d, (bx, 750), "you press", 26, S.HILITE, t, 2.8, 3.2)
    # request back to the PSU
    kr = prog(t, 3.2, 3.9)
    carrow(d, [(1210, 590), (1210, 520), (710, 520)], S.HILITE, kr, 5)
    write(d, (960, 490), "\"please switch on\"", 28, S.HILITE, t, 3.5, 4.2)
    # main rails come on
    km = prog(t, 4.4, 5.0)
    garrow(d, (700, 430), (970, 430), C_PWR, km, 8)
    write(d, (840, 400), "main rails on", 26, C_PWR, t, 4.6, 5.2)

def rail_v(V, u, delay):
    """Illustrative rail ramp: rises with a little overshoot and settles."""
    x = (u - delay) * 9
    if x <= 0: return 0.0
    return V * (1 - math.exp(-x) * math.cos(1.6 * x) * 1.0)

def s_rails(d, t, dur):
    S.chrome(d, "STEP 1 · POWER", "Three rails ramp up", "The 12 V, 5 V and 3.3 V rails ramp up in milliseconds, then settle near target: typically within ±5%.", t, dur)
    strip(d, 0, t)
    x0, y0, w, h = 320, 270, 1240, 540
    k = prog(t, 0.2, 0.8)
    stroke(d, [(x0, y0), (x0, y0 + h), (x0 + w, y0 + h)], S.LINE, k, 4)
    write(d, (x0 + w, y0 + h + 40), "time  (a few milliseconds)", 26, S.DIM, t, 0.6, w="Medium", anchor="rm")
    write(d, (x0 - 20, y0 - 20), "volts", 26, S.DIM, t, 0.6, w="Medium", anchor="rm")
    vy = lambda v: y0 + h - v / 13.5 * h
    for V, c, delay, name in ((12, C_PWR, 0.05, "12 V"), (5, S.ACCENT, 0.09, "5 V"), (3.3, S.EXTRA, 0.12, "3.3 V")):
        kb = prog(t, 2.6, 3.2)
        if kb > 0:
            d.rectangle([x0 + 6, vy(V * 1.05), x0 + w, vy(V * 0.95)], fill=S.fade(mix(S.BG, c, 0.22), kb))
        reveal = prog(t, 0.9, 3.0)
        pts = []
        for px in range(0, int(w * reveal), 5):
            pts.append((x0 + px, vy(rail_v(V, px / w, delay))))
        if len(pts) > 1: S.line(d, pts, c, 5)
        write(d, (x0 - 20, vy(V)), name, 30, c, t, 1.0, anchor="rm")
    kb = prog(t, 2.8, 3.4)
    garrow(d, (1180, 300), (1180, vy(12 * 1.05) - 6), C_PWR, kb, 4)
    write(d, (1180, 290), "must settle in this band (about ±5%)", 26, C_PWR, t, 3.0, 4.0, anchor="mm")
    write(d, (x0 + w, vy(1.2)), "(shapes illustrative)", 24, S.DIM, t, 3.6, w="Medium", anchor="rm")

def s_powergood(d, t, dur):
    S.chrome(d, "STEP 1 · POWER", "Power Good: the all-clear", "Power Good stays low until every rail is steady, then waits a little longer, typically 0.1 to 0.5 s, before going high.", t, dur)
    strip(d, 0, t)
    x0, x1 = 470, 1720
    X = lambda u: x0 + (x1 - x0) * u
    rows = [("button", S.TXT, [(0, 0), (0.06, 0), (0.06, 1), (0.1, 1), (0.1, 0), (1, 0)]),
            ("turn-on request", S.HILITE, [(0, 0), (0.11, 0), (0.11, 1), (1, 1)]),
            ("main rails", C_PWR, [(0, 0), (0.13, 0), (0.18, 0.9), (0.2, 1.04), (0.23, 1), (1, 1)]),
            ("Power Good", S.GOOD, [(0, 0), (0.6, 0), (0.6, 1), (1, 1)]),
            ("processor reset", S.BAD, [(0, 0), (0.7, 0), (0.7, 1), (1, 1)])]
    reveal = prog(t, 0.6, 4.2)
    for i, (name, c, wave) in enumerate(rows):
        yb = 340 + i * 95
        write(d, (x0 - 30, yb - 22), name, 28, c, t, 0.3 + i * 0.15, anchor="rm")
        stroke(d, [(X(u), yb - 46 * v) for u, v in wave], c, reveal, 5)
    write(d, (X(0.71) + 10, 700 + 95 * 0 - 2 * 46 - 4), "released", 24, S.BAD, t, 3.9, 4.4, anchor="lm")
    kd = prog(t, 3.2, 3.8)
    if kd > 0:
        for u in (0.23, 0.6):
            for yy in range(260, 760, 22):
                S.line(d, [(X(u), yy), (X(u), yy + 10)], S.DIM, 2, kd)
        garrow(d, (X(0.415), 800), (X(0.6) - 4, 800), S.HILITE, kd, 4)
        garrow(d, (X(0.415), 800), (X(0.23) + 4, 800), S.HILITE, kd, 4)
        write(d, (X(0.415), 840), "waits: typically 0.1 to 0.5 s", 28, S.HILITE, t, 3.5, 4.3)
    write(d, (x1, 250), "(timing not to scale)", 24, S.DIM, t, 4.0, w="Medium", anchor="rm")

def coil(x0, y, L, turns=4, r=16):
    return [(x0 + u * L + r * 0.8 * math.sin(2 * math.pi * turns * u), y - r * (1 - math.cos(2 * math.pi * turns * u)))
            for u in [i / 120 for i in range(121)]]

def s_vrm(d, t, dur):
    S.chrome(d, "STEP 1 · POWER", "One more step down", "The processor's core needs roughly one volt and a lot of current, so regulators next to the socket step 12 V down.", t, dur)
    strip(d, 0, t)
    k = prog(t, 0.2, 0.8)
    stroke(d, [(160, 560), (520, 560)], C_PWR, k, 7)
    write(d, (300, 520), "12 V rail", 32, C_PWR, t, 0.4)
    stroke(d, [(520, 380), (520, 740)], C_PWR, prog(t, 0.6, 1.0), 6)
    sketch(d, (560, 300, 1120, 800), S.LINE, prog(t, 0.6, 1.4), fill=mix(S.PANEL, S.BG, 0.3))
    write(d, (840, 340), "voltage regulators", 32, S.TXT, t, 1.0, 1.6)
    for i in range(4):
        y = 430 + i * 95
        kk = prog(t, 1.2 + i * 0.3, 1.7 + i * 0.3)
        stroke(d, [(520, y), (620, y)], C_PWR, kk, 5)
        sketch(d, (620, y - 30, 720, y + 30), S.ACCENT, kk, r=8)
        S.text(d, (670, y), "switch", 20, S.ACCENT, "Bold", "mm", k=kk)
        stroke(d, coil(760, y + 10, 220), S.LINE, kk, 4)
        stroke(d, [(720, y + 10), (760, y + 10)], S.LINE, kk, 4)
        stroke(d, [(980, y + 10), (1160, y + 10)], S.GOOD, kk, 5)
    stroke(d, [(1160, 440), (1160, 725)], S.GOOD, prog(t, 2.4, 2.8), 6)
    garrow(d, (1160, 580), (1300, 580), S.GOOD, prog(t, 2.6, 3.0), 10)
    kc = prog(t, 2.6, 3.3)
    S.chip(d, 1320, 460, 420, 240, "processor", "core: about 1 V", C_RST, kc)
    if t > 3.0:
        for i in range(8):
            u = ((t - 3.0) * 0.9 + i / 8) % 1.0
            for j in range(4):
                dot(d, (980 + 180 * u, 440 + j * 95), 6, S.GOOD, 0.9)
    tag(d, (1530, 790), "example values: core voltage varies by chip and load", S.HILITE, prog(t, 3.4, 3.9))
    write(d, (840, 780), "(simplified)", 24, S.DIM, t, 3.6, w="Medium")


# =====================================================================
# STEP 2 · RESET
# =====================================================================
def s_reset(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "Held in reset", "The board holds the processor in reset. Inside, registers sit at fixed starting values. When power is good, reset lets go.", t, dur)
    strip(d, 1, t)
    rel = 3.0
    S.chip(d, 620, 380, 420, 260, "processor", "waiting" if t < rel else "running!", C_RST, prog(t, 0.2, 0.9))
    stroke(d, [(160, 510), (620, 510)], S.BAD if t < rel else S.GOOD, prog(t, 0.6, 1.2), 6)
    write(d, (390, 470), "RESET line", 30, S.BAD if t < rel else S.GOOD, t, 0.9)
    # small waveform of the reset line above it
    x0, x1, yb = 180, 600, 400
    sw = clamp((t - 1.0) / (rel - 1.0 + 1.2))
    wave = [(x0, yb), (x0 + 0.62 * (x1 - x0), yb), (x0 + 0.62 * (x1 - x0), yb - 60), (x1, yb - 60)]
    stroke(d, wave, S.TXT, sw * 1.0, 4)
    write(d, (x0, 340), "held", 24, S.BAD, t, 1.2, anchor="lm", w="Medium")
    write(d, (x1, 310), "let go", 24, S.GOOD, t, rel, anchor="rm", w="Medium")
    # clamp: a padlock-ish block on the line while held
    if t < rel:
        k = prog(t, 1.0, 1.4)
        sketch(d, (470, 540, 570, 610), S.BAD, k, r=10)
        S.text(d, (520, 575), "hold", 24, S.BAD, "Bold", "mm", k=k)
    else:
        for g in range(2):
            u = ((t - rel) * 0.8 + g / 2) % 1.0
            gcircle(d, (830, 510), 150 + u * 90, mix(S.BG, S.GOOD, 0.7 * (1 - u)), 1.0, 4)
    # registers
    kr = prog(t, 1.4, 2.0)
    sketch(d, (1200, 320, 1780, 780), S.LINE, kr)
    write(d, (1490, 365), "registers after reset", 30, S.TXT, t, 1.6)
    regs = [("instruction pointer", "FFF0"), ("code segment", "F000"), ("its base address", "FFFF 0000"), ("everything else", "set defaults")]
    for i, (a, b) in enumerate(regs):
        y = 450 + i * 80
        write(d, (1230, y), a, 26, S.DIM, t, 1.9 + i * 0.3, w="Medium", anchor="lm")
        write(d, (1750, y), b, 30, S.HILITE if i < 3 else S.TXT, t, 2.1 + i * 0.3, anchor="rm")
    tag(d, (1490, 740), "x86, values in hex", S.DIM, prog(t, 3.0, 3.4))

def s_helper(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "A hidden first step", "On many modern PCs, a small helper processor starts before the main cores and checks the firmware. Details vary by design.", t, dur)
    strip(d, 1, t)
    k = prog(t, 0.2, 0.9)
    sketch(d, (160, 320, 700, 780), S.DIM, k)
    write(d, (430, 360), "main cores", 32, S.DIM, t, 0.5)
    cores(d, 230, 420, 2, 2, 150, 90, [0, 0, 0, 0], k)
    for i in range(4):
        cx, cy = 230 + (i % 2) * 240 + 75, 420 + (i // 2) * 240 + 75
        z = (t * 0.6 + i * 0.25) % 1.0
        S.text(d, (cx + 30 * z, cy - 20 - 40 * z), "z", 30 + int(10 * z), S.DIM, "Bold", "mm", k=k * (1 - z))
    kh = prog(t, 0.9, 1.5)
    sketch(d, (800, 450, 1100, 640), S.HILITE, kh, fill=mix(S.PANEL, S.HILITE, 0.15))
    write(d, (950, 520), "helper", 32, S.HILITE, t, 1.2)
    write(d, (950, 570), "processor", 32, S.HILITE, t, 1.4)
    write(d, (950, 690), "starts first", 26, S.HILITE, t, 1.6, w="Medium")
    chip8(d, 1380, 440, 1600, 660, "firmware", C_FW, prog(t, 1.6, 2.2), 28)
    write(d, (1490, 710), "flash chip", 26, S.DIM, t, 2.0, w="Medium")
    ka = prog(t, 2.2, 2.8)
    garrow(d, (1110, 545), (1350, 545), S.HILITE, ka, 5)
    write(d, (1230, 500), "check it", 26, S.HILITE, t, 2.4)
    # magnifier sweeping the flash chip
    if t > 2.6:
        mx = 1490 + 60 * math.sin((t - 2.6) * 2.2)
        gcircle(d, (mx, 520), 48, S.TXT, prog(t, 2.6, 3.0), 5)
        stroke(d, [(mx + 34, 554), (mx + 80, 600)], S.TXT, prog(t, 2.8, 3.1), 8)
    tick(d, 1700, 420, 30, S.GOOD, prog(t, 3.6, 4.0), 8)
    tag(d, (960, 820), "on many modern PCs  ·  details vary by maker", S.HILITE, prog(t, 3.0, 3.5))

def s_bsp(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "One core goes first", "Only one core starts: the bootstrap processor. It begins in real mode, the old 16-bit mode of the original PC processors.", t, dur)
    strip(d, 1, t)
    k = prog(t, 0.2, 0.9)
    lit = [prog(t, 1.2, 1.8)] + [0] * 7
    cores(d, 260, 330, 4, 2, 170, 40, lit, k, C_RST, labels=True)
    write(d, (200, 770), "bootstrap processor: runs", 30, C_RST, t, 1.6, anchor="lm")
    carrow(d, [(215, 740), (215, 415), (250, 415)], C_RST, prog(t, 1.6, 2.2), 4)
    for i in range(1, 8):
        cx = 260 + (i % 4) * 210 + 85; cy = 330 + (i // 4) * 210 + 30
        z = (t * 0.5 + i * 0.13) % 1.0
        S.text(d, (cx + 40 + 20 * z, cy - 10 - 30 * z), "z", 24 + int(8 * z), S.DIM, "Bold", "mm", k=k * (1 - z))
    write(d, (680, 820), "the others wait to be woken later", 26, S.DIM, t, 2.2, w="Medium")
    kb = prog(t, 2.6, 3.2)
    sketch(d, (1160, 330, 1760, 740), C_RST, kb)
    write(d, (1460, 390), "starts in real mode", 34, C_RST, t, 2.9)
    write(d, (1460, 510), "16-bit", 80, S.HILITE, t, 3.2, 3.6)
    write(d, (1460, 610), "like the original PC", 28, S.TXT, t, 3.6, w="Medium")
    write(d, (1460, 660), "processors of the 1980s", 28, S.TXT, t, 3.9, w="Medium")

def s_vector(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "The reset vector", "On x86, the first instruction comes from hex FFFF FFF0, 16 bytes below 4 GB, where the firmware appears.", t, dur)
    strip(d, 1, t)
    bx0, bx1, by0, by1 = 520, 660, 280, 840
    k = prog(t, 0.2, 0.9)
    sketch(d, (bx0, by0, bx1, by1), S.LINE, k, r=6)
    write(d, (bx0 - 20, by1 - 10), "0", 30, S.DIM, t, 0.6, anchor="rm")
    write(d, (bx0 - 20, by0 + 12), "4 GB", 30, S.DIM, t, 0.8, anchor="rm")
    write(d, (bx0 - 20, (by0 + by1) / 2), "addresses", 26, S.DIM, t, 0.9, w="Medium", anchor="rm")
    kf = prog(t, 1.0, 1.6)
    if kf > 0:
        d.rectangle([bx0 + 5, by0 + 5, bx1 - 5, by0 + 90], fill=S.fade(mix(S.PANEL, C_FW, 0.45), kf))
    write(d, (bx1 + 20, by0 + 70), "firmware chip shows up here", 26, C_FW, t, 1.3, anchor="lm")
    kr = prog(t, 1.2, 1.8)
    if kr > 0:
        d.rectangle([bx0 + 5, by1 - 250, bx1 - 5, by1 - 5], fill=S.fade(mix(S.PANEL, S.DIM, 0.25), kr))
    write(d, (bx1 + 20, by1 - 120), "RAM lives down here (not ready yet)", 26, S.DIM, t, 1.5, w="Medium", anchor="lm")
    # the arrow at the very top
    ka = prog(t, 2.0, 2.6)
    garrow(d, (1000, by0 + 14), (bx1 + 10, by0 + 14), C_RST, ka, 6)
    write(d, (1020, by0 + 14), "hex FFFF FFF0", 54, S.HILITE, t, 2.3, 3.1, anchor="lm")
    # zoom panel: the last sixteen bytes
    kz = prog(t, 3.0, 3.6)
    px0, py0, px1, py1 = 1000, 470, 1780, 650
    sketch(d, (px0, py0, px1, py1), C_RST, kz)
    write(d, ((px0 + px1) / 2, py0 + 40), "the last 16 bytes below 4 GB", 28, S.TXT, t, 3.3)
    cw = (px1 - px0 - 40) / 16
    for i in range(16):
        ki = prog(t, 3.4 + i * 0.05, 3.6 + i * 0.05)
        x = px0 + 20 + i * cw
        sketch(d, (x + 2, py0 + 80, x + cw - 2, py0 + 140), C_RST if i == 0 else S.DIM, ki, r=4, width=3)
    write(d, (px0 + 20, py1 + 30), "FFFF FFF0", 24, S.HILITE, t, 4.0, anchor="lm")
    write(d, (px1 - 20, py1 + 30), "FFFF FFFF", 24, S.DIM, t, 4.2, anchor="rm")
    write(d, ((px0 + px1) / 2, 770), "\"reset vector\": the same address every time", 30, C_RST, t, 4.4)

def s_jump(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "Sixteen bytes: room for a jump", "Sixteen bytes isn't much, so the code there is usually a jump into the main firmware. The RAM isn't usable yet.", t, dur)
    strip(d, 1, t)
    x0, cw, y0 = 260, 80, 290
    for i in range(16):
        ki = prog(t, 0.2 + i * 0.04, 0.5 + i * 0.04)
        col = C_RST if i < 5 else S.DIM
        sketch(d, (x0 + i * cw + 2, y0, x0 + (i + 1) * cw - 2, y0 + 70), col, ki, r=4, width=3,
               fill=mix(S.PANEL, C_RST, 0.25) if i < 5 else None)
    kj = prog(t, 1.0, 1.5)
    stroke(d, [(x0 + 4, y0 + 90), (x0 + 5 * cw - 4, y0 + 90)], S.HILITE, kj, 4)
    write(d, (x0 + 2.5 * cw, y0 + 125), "a jump instruction", 28, S.HILITE, t, 1.2)
    write(d, (x0 + 16 * cw, y0 + 110), "(typical: the exact bytes depend on the firmware)", 22, S.DIM, t, 1.6, w="Medium", anchor="rm")
    kf = prog(t, 1.6, 2.3)
    sketch(d, (260, 560, 1060, 820), C_FW, kf, fill=mix(S.PANEL, C_FW, 0.15))
    write(d, (660, 620), "the main firmware code", 32, C_FW, t, 2.0)
    for i in range(4):
        stroke(d, [(320, 680 + i * 32), (320 + [600, 480, 560, 380][i], 680 + i * 32)], S.DIM, prog(t, 2.2 + i * 0.15, 2.6 + i * 0.15), 3)
    path = [(x0 + 2.5 * cw, y0 + 150 + 5)] + [(x0 + 2.5 * cw - 60 * math.sin(u * math.pi), y0 + 155 + u * 170) for u in [i / 20 for i in range(1, 21)]]
    carrow(d, path, C_RST, prog(t, 2.4, 3.2), 6)
    write(d, (x0 + 2.5 * cw + 30, 480), "jump!", 32, C_RST, t, 3.0, anchor="lm")
    kr = prog(t, 3.2, 3.8)
    ram_stick(d, 1240, 600, 1740, 740, S.DIM, kr)
    write(d, (1490, 560), "RAM", 34, S.DIM, t, 3.4)
    cross(d, 1490, 670, 70, S.BAD, prog(t, 3.8, 4.4), 9)
    write(d, (1490, 800), "not set up yet: can't use it", 28, S.BAD, t, 4.2)


# =====================================================================
# STEP 3 · FIRMWARE
# =====================================================================
def s_firmware(d, t, dur):
    S.chrome(d, "STEP 3 · FIRMWARE", "The first real program", "Firmware lives in a flash chip: BIOS on older PCs, UEFI on modern ones. Its first scratch memory is often the cache.", t, dur)
    strip(d, 2, t)
    sketch(d, (160, 300, 860, 800), S.LINE, prog(t, 0.2, 1.0), fill=mix(S.PANEL, S.BG, 0.3))
    write(d, (510, 340), "motherboard", 30, S.DIM, t, 0.6)
    chip8(d, 400, 420, 620, 600, "flash", C_FW, prog(t, 0.6, 1.2), 34)
    write(d, (510, 640), "firmware lives here", 28, C_FW, t, 1.0)
    write(d, (510, 700), "and keeps it with the power off", 24, S.DIM, t, 1.3, w="Medium")
    kn = prog(t, 1.6, 2.2)
    sketch(d, (960, 300, 1340, 420), C_FW, kn)
    write(d, (1150, 345), "BIOS", 40, C_FW, t, 1.8)
    write(d, (1150, 392), "older PCs", 24, S.DIM, t, 2.0, w="Medium")
    kn2 = prog(t, 2.2, 2.8)
    sketch(d, (1400, 300, 1780, 420), C_FW, kn2)
    write(d, (1590, 345), "UEFI", 40, C_FW, t, 2.4)
    write(d, (1590, 392), "the modern standard", 24, S.DIM, t, 2.6, w="Medium")
    garrow(d, (630, 450), (950, 370), C_FW, prog(t, 1.6, 2.0), 4)
    # cache as scratch memory
    kc = prog(t, 3.0, 3.6)
    S.chip(d, 1060, 540, 300, 200, "processor", None, C_RST, kc, pins=True)
    sketch(d, (1460, 560, 1760, 720), S.HILITE, prog(t, 3.3, 3.9), fill=mix(S.PANEL, S.HILITE, 0.12))
    write(d, (1610, 610), "its cache,", 28, S.HILITE, t, 3.6)
    write(d, (1610, 660), "borrowed as RAM", 28, S.HILITE, t, 3.9)
    garrow(d, (1370, 640), (1450, 640), S.HILITE, prog(t, 3.5, 3.9), 5)
    write(d, (1410, 790), "(on many systems, until the real RAM is ready)", 22, S.DIM, t, 4.2, w="Medium")

def s_post(d, t, dur):
    S.chrome(d, "STEP 3 · FIRMWARE", "POST: the Power-On Self-Test", "The firmware checks memory, graphics, storage and USB. A serious fault often means beeps or a code light.", t, dur)
    strip(d, 2, t)
    items = ["processor", "chipset", "memory", "graphics", "storage", "USB, keyboard"]
    for i, it in enumerate(items):
        y = 300 + i * 88
        a = 0.4 + i * 0.5
        sketch(d, (220, y - 26, 272, y + 26), S.LINE, prog(t, a - 0.2, a + 0.1), r=6, width=3)
        write(d, (300, y), it, 36, S.TXT, t, a, anchor="lm")
        tick(d, 246, y - 2, 20, S.GOOD, prog(t, a + 0.3, a + 0.6), 6)
    ks = prog(t, 3.4, 4.0)
    sketch(d, (1000, 320, 1760, 800), S.BAD, ks)
    write(d, (1380, 370), "if something essential fails", 30, S.BAD, t, 3.6)
    write(d, (1380, 420), "the screen may not work yet, so...", 24, S.DIM, t, 3.9, w="Medium")
    # speaker + waves
    kk = prog(t, 4.0, 4.5)
    sp = [(1080, 540), (1120, 540), (1170, 500), (1170, 640), (1120, 600), (1080, 600), (1080, 540)]
    stroke(d, sp, S.TXT, kk, 5)
    for g in range(3):
        rr = 30 + g * 28 + 6 * math.sin(t * 6 + g)
        pts = [(1180 + rr * math.cos(a), 570 + rr * math.sin(a)) for a in [(-0.8 + 1.6 * i / 12) for i in range(13)]]
        stroke(d, pts, S.HILITE, kk, 4)
    write(d, (1150, 700), "beeps", 30, S.HILITE, t, 4.2)
    # code display
    kd = prog(t, 4.4, 4.9)
    sketch(d, (1420, 510, 1680, 640), S.LINE, kd, r=8, fill=(20, 30, 26))
    if kd > 0.5:
        S.text(d, (1550, 575), "8 8" if int(t * 2) % 2 else "- -", 56, S.BAD, "Bold", "mm")
    write(d, (1550, 700), "or a code light", 30, S.HILITE, t, 4.6)
    write(d, (1380, 760), "(what they mean depends on the board)", 22, S.DIM, t, 5.0, w="Medium")

def eye_y(u, level, j):
    """One trace through a simplified 'data eye': crossings at u=0 and u=1."""
    s = 0.5 - 0.5 * math.cos(math.pi * clamp(u * 3.2 if u < 0.32 else (1 - u) * 3.2 if u > 0.68 else 1))
    return level * s + j

def s_training(d, t, dur):
    S.chrome(d, "STEP 3 · FIRMWARE", "Memory training", "Read each stick's info chip, then tune the timing to sample every bit in the sweet spot. New RAM: slower first boot.", t, dur)
    strip(d, 2, t)
    ram_stick(d, 160, 330, 820, 480, C_FW, prog(t, 0.2, 0.9), spd=True)
    write(d, (490, 300), "memory stick", 30, C_FW, t, 0.5)
    ka = prog(t, 1.0, 1.4)
    carrow(d, [(765, 490), (765, 560), (700, 600)], S.HILITE, ka, 4)
    write(d, (460, 600), "small info chip:", 28, S.HILITE, t, 1.2)
    write(d, (460, 645), "size, speed, timings", 28, S.HILITE, t, 1.5)
    write(d, (460, 740), "firmware reads it first", 26, S.DIM, t, 1.8, w="Medium")
    # data eye
    x0, x1, ym, A = 1000, 1720, 560, 150
    ke = prog(t, 1.8, 2.6)
    sketch(d, (x0 - 40, 300, x1 + 40, 820), S.LINE, ke, fill=mix(S.PANEL, S.BG, 0.3))
    write(d, ((x0 + x1) / 2, 340), "one data signal, many bits overlaid", 26, S.DIM, t, 2.0, w="Medium")
    for i, (lev, j) in enumerate(((-A, 0), (A, 0), (-A, 8), (A, -8), (-A, -6), (A, 6))):
        pts = [(x0 + (x1 - x0) * u, ym + eye_y(u, lev, j) * 1.0) for u in [q / 60 for q in range(61)]]
        stroke(d, pts, S.ACCENT, prog(t, 2.0 + i * 0.1, 2.6 + i * 0.1), 3)
        pts2 = [(x0 + (x1 - x0) * u, ym + eye_y(u, lev, j)) for u in [q / 60 for q in range(61)]]
    # sampling point sweeps, then settles in the centre
    if t > 2.8:
        sw = clamp((t - 2.8) / 2.4)
        u = 0.08 + 0.84 * (0.5 - 0.5 * math.cos(sw * 3 * math.pi)) if sw < 1 else 0.5
        if sw >= 1: u = 0.5
        good = 1 - clamp(abs(u - 0.5) / 0.3)
        c = mix(S.BAD, S.GOOD, good)
        xx = x0 + (x1 - x0) * u
        S.line(d, [(xx, ym - A - 40), (xx, ym + A + 40)], c, 5)
        S.circle(d, (xx, ym), 12, c)
        if sw >= 1:
            write(d, (xx, ym + A + 80), "best moment to sample", 30, S.GOOD, t, 5.2)
    write(d, (x0 + 10, 790), "(simplified)", 22, S.DIM, t, 3.0, w="Medium", anchor="lm")

def s_devices(d, t, dur):
    S.chrome(d, "STEP 3 · FIRMWARE", "Map the machine, pick a route", "With memory working, the firmware finds graphics, drives and USB, then reads your saved boot order: where to look first.", t, dur)
    strip(d, 2, t)
    root = (330, 560)
    gcircle(d, root, 90, C_FW, prog(t, 0.2, 0.8), 5, fill=S.PANEL)
    write(d, root, "firmware", 30, C_FW, t, 0.5)
    devs = [("graphics", S.EXTRA), ("drives", S.GOOD), ("USB ports", S.ACCENT), ("network", S.BLUE)]
    for i, (n, c) in enumerate(devs):
        y = 330 + i * 150
        a = 0.8 + i * 0.4
        carrow(d, [(425, 560), (520, 560), (560, y), (640, y)], S.LINE, prog(t, a, a + 0.5), 4)
        sketch(d, (650, y - 45, 950, y + 45), c, prog(t, a + 0.3, a + 0.7))
        write(d, (800, y), n, 32, c, t, a + 0.5)
    kb = prog(t, 2.6, 3.2)
    sketch(d, (1150, 300, 1760, 800), C_FW, kb)
    write(d, (1455, 350), "saved setting: boot order", 30, C_FW, t, 2.8)
    rows = ["1.  internal drive", "2.  USB stick", "3.  network"]
    for i, r in enumerate(rows):
        y = 460 + i * 100
        if i == 0 and t > 4.0:
            w = 3 + 2 * math.sin(t * 5)
            sketch(d, (1190, y - 40, 1720, y + 40), S.HILITE, 1.0, r=10, width=int(w), fill=mix(S.PANEL, S.HILITE, 0.12))
        write(d, (1220, y), r, 34, S.TXT, t, 3.1 + i * 0.3, anchor="lm")
    write(d, (1455, 760), "(example order: yours is in the settings)", 22, S.DIM, t, 3.8, w="Medium")


# =====================================================================
# STEP 4 · BOOT DEVICE
# =====================================================================
def s_mbr(d, t, dur):
    S.chrome(d, "STEP 4 · BOOT DEVICE", "Legacy BIOS: the first sector", "Old BIOS reads the disk's first 512-byte sector. If it ends in hex 55 AA, it's copied to address hex 7C00 and run.", t, dur)
    strip(d, 3, t)
    x0, x1 = 200, 1720
    n = 24; cw = (x1 - x0) / n
    for i in range(n):
        sketch(d, (x0 + i * cw + 2, 280, x0 + (i + 1) * cw - 2, 330), C_DEV if i == 0 else S.DIM, prog(t, 0.2 + i * 0.03, 0.5 + i * 0.03),
               r=4, width=3, fill=mix(S.PANEL, C_DEV, 0.3) if i == 0 else None)
    write(d, (x1, 360), "the disk, sector by sector", 24, S.DIM, t, 0.8, w="Medium", anchor="rm")
    write(d, (x0, 360), "sector 0", 24, C_DEV, t, 0.9, anchor="lm")
    kz = prog(t, 1.2, 1.7)
    stroke(d, [(x0, 332), (x0, 440)], C_DEV, kz, 3)
    stroke(d, [(x0 + cw, 332), (x1, 440)], C_DEV, kz, 3)
    segs = [("start-up code", "446 bytes", S.ACCENT, 1040), ("partition table", "64 bytes", S.EXTRA, 300), ("55 AA", "2 bytes", S.HILITE, 180)]
    x = x0
    for i, (a, b, c, w) in enumerate(segs):
        kk = prog(t, 1.6 + i * 0.5, 2.1 + i * 0.5)
        sketch(d, (x + 3, 450, x + w - 3, 560), c, kk, fill=mix(S.PANEL, c, 0.15))
        write(d, (x + w / 2, 490), a, 34 if i < 2 else 40, c, t, 1.8 + i * 0.5)
        write(d, (x + w / 2, 535), b, 24, S.DIM, t, 2.0 + i * 0.5, w="Medium")
        x += w
    write(d, (x1, 590), "512 bytes in all  (boxes not to scale)", 24, S.DIM, t, 3.0, w="Medium", anchor="rm")
    # check, then load
    tick(d, x1 - 90, 640, 26, S.GOOD, prog(t, 3.3, 3.7), 7)
    write(d, (x1 - 130, 645), "signature found?", 28, S.GOOD, t, 3.3, anchor="rm")
    km = prog(t, 3.8, 4.4)
    sketch(d, (x0, 700, x0 + 860, 790), S.LINE, km, r=8)
    write(d, (x0 + 20, 745), "memory", 28, S.DIM, t, 4.0, anchor="lm")
    sketch(d, (x0 + 420, 712, x0 + 620, 778), S.ACCENT, prog(t, 4.4, 4.8), r=6, fill=mix(S.PANEL, S.ACCENT, 0.25))
    write(d, (x0 + 520, 745), "7C00", 30, S.HILITE, t, 4.6)
    carrow(d, [(x0 + 520, 565), (x0 + 520, 700)], S.ACCENT, prog(t, 4.1, 4.6), 5)
    write(d, (x0 + 900, 745), "copy it here, then jump to it", 30, S.TXT, t, 4.8, anchor="lm")

def folder(d, x, y, name, col, k, size=28):
    if k <= 0.01: return
    pts = [(x, y - 16), (x + 16, y - 16), (x + 22, y - 10), (x + 44, y - 10), (x + 44, y + 16), (x, y + 16), (x, y - 16)]
    stroke(d, pts, col, k, 3)
    S.text(d, (x + 58, y), name, size, col, "Bold", "lm", k=k)

def s_uefi(d, t, dur):
    S.chrome(d, "STEP 4 · BOOT DEVICE", "UEFI: a file, not a sector", "UEFI reads partitions and files. It finds the EFI system partition, a small FAT partition holding bootloaders as files.", t, dur)
    strip(d, 3, t)
    x0, x1 = 200, 1720
    k = prog(t, 0.2, 0.8)
    sketch(d, (x0, 280, x0 + 130, 370), S.DIM, k, r=6)
    write(d, (x0 + 65, 325), "table", 24, S.DIM, t, 0.5)
    sketch(d, (x0 + 140, 280, x0 + 520, 370), C_DEV, prog(t, 0.6, 1.2), fill=mix(S.PANEL, C_DEV, 0.2))
    write(d, (x0 + 330, 312), "EFI system partition", 26, C_DEV, t, 0.9)
    write(d, (x0 + 330, 348), "small, FAT file system", 22, S.DIM, t, 1.2, w="Medium")
    sketch(d, (x0 + 530, 280, x1, 370), S.LINE, prog(t, 0.9, 1.5))
    write(d, ((x0 + 530 + x1) / 2, 325), "the operating system's own partition", 26, S.DIM, t, 1.2, w="Medium")
    write(d, (x1, 400), "the disk  (partitions not to scale)", 22, S.DIM, t, 1.4, w="Medium", anchor="rm")
    kz = prog(t, 1.6, 2.1)
    stroke(d, [(x0 + 140, 372), (x0 + 60, 450)], C_DEV, kz, 3)
    stroke(d, [(x0 + 520, 372), (x0 + 760, 450)], C_DEV, kz, 3)
    sketch(d, (x0 + 60, 450, x0 + 760, 820), C_DEV, prog(t, 1.8, 2.4))
    tree = [(0, "EFI", S.TXT), (1, "BOOT", S.TXT), (2, "BOOTX64.EFI", S.HILITE), (1, "an OS folder", S.TXT), (2, "its bootloader.efi", S.HILITE)]
    for i, (lvl, nm, c) in enumerate(tree):
        y = 500 + i * 64
        a = 2.2 + i * 0.35
        if lvl > 0:
            stroke(d, [(x0 + 100 + (lvl - 1) * 60, y - 44), (x0 + 100 + (lvl - 1) * 60, y), (x0 + 100 + lvl * 60 - 12, y)], S.DIM, prog(t, a, a + 0.3), 3)
        if nm.endswith((".EFI", ".efi")):
            sketch(d, (x0 + 100 + lvl * 60, y - 18, x0 + 136 + lvl * 60, y + 18), c, prog(t, a, a + 0.3), r=4, width=3)
            write(d, (x0 + 150 + lvl * 60, y), nm, 28, c, t, a + 0.1, anchor="lm")
        else:
            folder(d, x0 + 100 + lvl * 60, y, nm, c, prog(t, a, a + 0.3))
    write(d, (x0 + 410, 800), "(names are examples; the first is the standard fallback)", 20, S.DIM, t, 4.0, w="Medium")
    # boot entries in the firmware
    kb = prog(t, 3.4, 4.0)
    sketch(d, (1100, 450, 1740, 820), C_FW, kb)
    write(d, (1420, 495), "boot entries, stored by the firmware", 26, C_FW, t, 3.6)
    ent = ["1:  OS folder / its bootloader", "2:  USB stick", "3:  network"]
    for i, e in enumerate(ent):
        write(d, (1140, 580 + i * 70), e, 28, S.TXT, t, 3.9 + i * 0.3, anchor="lm")
    write(d, (1420, 790), "(example list)", 22, S.DIM, t, 4.6, w="Medium")

def s_compare(d, t, dur):
    S.chrome(d, "STEP 4 · BOOT DEVICE", "Two ways to boot", "Legacy BIOS runs one raw sector, in 16-bit mode. UEFI runs a program from a file, usually already in 64-bit mode.", t, dur)
    strip(d, 3, t)
    cols = [("LEGACY BIOS", S.DIM, ["reads one raw sector", "checks for 55 AA", "runs it in 16-bit mode", "older partition scheme"]),
            ("UEFI", C_DEV, ["reads a file from a partition", "understands FAT", "often already in 64-bit mode", "can check signatures"])]
    for i, (n, c, lines) in enumerate(cols):
        x = 180 + i * 800
        a = 0.3 + i * 1.6
        sketch(d, (x, 260, x + 760, 780), c, prog(t, a, a + 0.6))
        write(d, (x + 380, 330), n, 48, c if i else S.TXT, t, a + 0.3)
        stroke(d, [(x + 60, 380), (x + 700, 380)], c, prog(t, a + 0.4, a + 0.8), 3)
        for j, ln in enumerate(lines):
            write(d, (x + 60, 450 + j * 80), "•  " + ln, 32, S.TXT, t, a + 0.6 + j * 0.25, anchor="lm", w="Medium")
    tag(d, (960, 830), "most modern PCs boot the UEFI way", C_DEV, prog(t, 4.2, 4.6), 26)

def key_icon(d, x, y, col, k, s=1.0):
    gcircle(d, (x, y), 22 * s, col, k, 4)
    stroke(d, [(x + 22 * s, y), (x + 90 * s, y)], col, k, 5)
    stroke(d, [(x + 70 * s, y), (x + 70 * s, y + 18 * s)], col, k, 4)
    stroke(d, [(x + 86 * s, y), (x + 86 * s, y + 14 * s)], col, k, 4)

def file_icon(d, x, y, w, h, label, col, k):
    sketch(d, (x, y, x + w, y + h), col, k, r=6)
    for i in range(3):
        stroke(d, [(x + 20, y + 40 + i * 26), (x + w - 20 - i * 18, y + 40 + i * 26)], S.DIM, k, 3)
    S.text(d, (x + w / 2, y + h + 26), label, 24, col, "Bold", "mm", k=k)

def s_secure(d, t, dur):
    S.chrome(d, "STEP 4 · BOOT DEVICE", "Secure Boot: check the signature", "With Secure Boot, the firmware checks a bootloader's digital signature against trusted keys. Unsigned or altered: refused.", t, dur)
    strip(d, 3, t)
    sketch(d, (160, 300, 560, 620), C_FW, prog(t, 0.2, 0.8))
    write(d, (360, 345), "firmware", 34, C_FW, t, 0.4)
    write(d, (360, 395), "trusted keys", 26, S.DIM, t, 0.7, w="Medium")
    for i in range(3):
        key_icon(d, 240, 460 + i * 50, S.HILITE, prog(t, 0.8 + i * 0.2, 1.1 + i * 0.2), 0.8)
    # two candidate files
    file_icon(d, 760, 290, 130, 160, "signed", S.GOOD, prog(t, 1.4, 1.9))
    gcircle(d, (870, 430), 26, S.GOOD, prog(t, 1.8, 2.2), 4, fill=mix(S.PANEL, S.GOOD, 0.3))
    file_icon(d, 760, 540, 130, 160, "altered", S.BAD, prog(t, 2.0, 2.5))
    stroke(d, [(780, 600), (800, 590), (820, 615), (845, 585), (870, 610)], S.BAD, prog(t, 2.3, 2.6), 4)
    garrow(d, (570, 420), (740, 370), S.LINE, prog(t, 2.6, 3.0), 4)
    garrow(d, (570, 520), (740, 620), S.LINE, prog(t, 2.6, 3.0), 4)
    write(d, (650, 470), "check", 26, S.TXT, t, 2.8)
    tick(d, 1000, 365, 34, S.GOOD, prog(t, 3.1, 3.5), 8)
    write(d, (1060, 370), "run it", 32, S.GOOD, t, 3.3, anchor="lm")
    cross(d, 1000, 620, 30, S.BAD, prog(t, 3.5, 3.9), 8)
    write(d, (1060, 620), "refuse", 32, S.BAD, t, 3.7, anchor="lm")
    # chain of trust
    chain = [("firmware", C_FW), ("bootloader", C_BL), ("kernel", C_K)]
    for i, (n, c) in enumerate(chain):
        x = 1340 + (i % 2) * 0
        y = 330 + i * 170
        a = 4.0 + i * 0.4
        sketch(d, (1330, y, 1730, y + 90), c, prog(t, a, a + 0.4))
        write(d, (1530, y + 45), n, 32, c, t, a + 0.2)
        if i < 2:
            garrow(d, (1530, y + 95), (1530, y + 165), S.GOOD, prog(t, a + 0.3, a + 0.6), 4)
            write(d, (1560, y + 130), "checks", 22, S.GOOD, t, a + 0.5, anchor="lm", w="Medium")
    write(d, (1530, 830), "a chain of trust", 28, S.HILITE, t, 5.2)


# =====================================================================
# STEP 5 · BOOTLOADER
# =====================================================================
def disk_icon(d, cx, top, w, h, col, k):
    if k <= 0.01: return
    e = 30
    pts_top = [(cx + w / 2 * math.cos(a), top + e / 2 * math.sin(a)) for a in [2 * math.pi * i / 40 for i in range(41)]]
    stroke(d, pts_top, col, k, 4)
    pts_bot = [(cx + w / 2 * math.cos(a), top + h + e / 2 * math.sin(a)) for a in [math.pi * i / 20 for i in range(21)]]
    stroke(d, pts_bot, col, k, 4)
    stroke(d, [(cx - w / 2, top), (cx - w / 2, top + h)], col, k, 4)
    stroke(d, [(cx + w / 2, top), (cx + w / 2, top + h)], col, k, 4)

def s_loader(d, t, dur):
    S.chrome(d, "STEP 5 · BOOTLOADER", "The bootloader's one job", "The bootloader copies the kernel into RAM, often with starter files, and leaves notes for the kernel.", t, dur)
    strip(d, 4, t)
    kb = prog(t, 0.2, 0.8)
    sketch(d, (700, 270, 1220, 470), C_BL, kb)
    write(d, (960, 310), "bootloader", 38, C_BL, t, 0.4)
    for i, m in enumerate(["> system A", "   system B"]):
        write(d, (800, 370 + i * 44), m, 28, S.TXT if i == 0 else S.DIM, t, 0.9 + i * 0.3, anchor="lm", w="Medium")
    write(d, (1210, 440), "(optional menu)", 20, S.DIM, t, 1.4, w="Medium", anchor="rm")
    disk_icon(d, 360, 560, 320, 200, S.DIM, prog(t, 0.6, 1.3))
    write(d, (360, 520), "disk", 30, S.DIM, t, 0.9)
    write(d, (360, 700), "kernel file", 28, C_K, t, 1.4)
    write(d, (360, 640), "starter files", 28, S.ACCENT, t, 1.7)
    # RAM column
    rx0, rx1, ry0, ry1 = 1380, 1740, 280, 820
    sketch(d, (rx0, ry0, rx1, ry1), S.LINE, prog(t, 0.8, 1.4), r=8)
    write(d, ((rx0 + rx1) / 2, ry1 + 30), "RAM", 30, S.TXT, t, 1.2)
    blocks = [("kernel", C_K, 560, 700, 2.2), ("starter file system", S.ACCENT, 420, 540, 3.0), ("notes: memory map,", S.HILITE, 300, 400, 3.8)]
    for n, c, y0, y1, a in blocks:
        kk = prog(t, a + 0.4, a + 0.9)
        sketch(d, (rx0 + 16, y0, rx1 - 16, y1), c, kk, r=6, fill=mix(S.PANEL, c, 0.2))
        write(d, ((rx0 + rx1) / 2, (y0 + y1) / 2 - (14 if c == S.HILITE else 0)), n, 24, c, t, a + 0.6)
    write(d, ((rx0 + rx1) / 2, 364), "options", 24, S.HILITE, t, 4.6)
    for (n, c, y0, y1, a), sy in zip(blocks[:2], (700, 640)):
        u = prog(t, a, a + 0.8)
        carrow(d, [(540, sy), (1000, sy - 40), (rx0 - 10, (y0 + y1) / 2)], c, u, 5)
    carrow(d, [(1000, 480), (1100, 350), (rx0 - 10, 350)], S.HILITE, prog(t, 3.8, 4.4), 4)

def s_modes(d, t, dur):
    S.chrome(d, "STEP 5 · BOOTLOADER", "Climbing through modes", "16-bit real mode, to 32-bit protected mode, to 64-bit long mode. Under UEFI, the firmware usually did it already.", t, dur)
    strip(d, 4, t)
    steps = [("16-bit", "real mode", 260, 760, C_RST), ("32-bit", "protected mode", 760, 620, S.ACCENT), ("64-bit", "long mode", 1260, 480, C_BL)]
    pts = []
    for i, (a, b, x, y, c) in enumerate(steps):
        kk = prog(t, 0.3 + i * 0.6, 0.8 + i * 0.6)
        stroke(d, [(x, y), (x + 460, y)], c, kk, 7)
        if i < 2:
            stroke(d, [(x + 460, y), (x + 460, steps[i + 1][3])], S.LINE, kk, 5)
        write(d, (x + 230, y - 90), a, 54, c, t, 0.5 + i * 0.6)
        write(d, (x + 230, y - 40), b, 30, S.TXT, t, 0.7 + i * 0.6, w="Medium")
        pts += [(x + 40, y - 18), (x + 440, y - 18)]
    # a dot climbing the stairs
    if t > 2.2:
        u = clamp((t - 2.2) / 2.4)
        pathp = [(300, 742), (700, 742), (740, 602), (1200, 602), (1240, 462), (1680, 462)]
        dot(d, along(pathp, u), 16, S.HILITE)
    tag(d, (520, 840), "legacy BIOS: bootloader or kernel climbs", S.DIM, prog(t, 3.6, 4.0), 24)
    tag(d, (1360, 840), "UEFI: firmware usually did it already", C_DEV, prog(t, 4.2, 4.6), 24)

def boot_shape(cx, cy, s):
    p = [(-0.5, -1.0), (0.05, -1.0), (0.05, 0.2), (0.55, 0.45), (0.75, 0.7), (0.75, 0.95), (-0.55, 0.95), (-0.55, 0.3), (-0.5, -1.0)]
    return [(cx + x * s, cy + y * s) for x, y in p]

def s_relay(d, t, dur):
    S.chrome(d, "STEP 5 · BOOTLOADER", "A relay race", "Each stage loads the next and hands over. That's 'bootstrapping': where the word 'boot' comes from.", t, dur)
    strip(d, 4, t)
    stages = [("reset vector", C_RST, 140), ("firmware", C_FW, 220), ("bootloader", C_BL, 290), ("kernel", C_K, 380)]
    x = 170; xs = []
    for i, (n, c, w) in enumerate(stages):
        h = 70 + w * 0.4
        y0 = 460 - h / 2
        a = 0.3 + i * 0.8
        sketch(d, (x, y0, x + w, y0 + h), c, prog(t, a, a + 0.5))
        write(d, (x + w / 2, 460), n, 28 if i else 24, c, t, a + 0.2)
        xs.append((x, w))
        if i < 3:
            garrow(d, (x + w + 10, 460), (x + w + 100, 460), S.TXT, prog(t, a + 0.5, a + 0.8), 5)
        x += w + 110
    # the baton
    if t > 0.8:
        u = clamp((t - 0.8) / 3.4)
        bx = xs[0][0] + xs[0][1] / 2 + u * (xs[3][0] + xs[3][1] / 2 - xs[0][0] - xs[0][1] / 2)
        dot(d, (bx, 340 - 20 * abs(math.sin(u * 12))), 14, S.HILITE)
    write(d, (960, 640), "each stage loads the next, then jumps to it", 34, S.TXT, t, 3.0, 4.0)
    kb = prog(t, 4.0, 4.8)
    stroke(d, boot_shape(1640, 700, 100), S.HILITE, kb, 6)
    loop = [(1595 + 22 * math.cos(a), 590 + 30 * math.sin(a)) for a in [math.pi + 2 * math.pi * i / 24 for i in range(25)]]
    stroke(d, loop, S.HILITE, prog(t, 4.6, 5.0), 5)
    write(d, (1500, 760), "boot  =  bootstrap", 32, S.HILITE, t, 4.8, anchor="rm")


# =====================================================================
# STEP 6 · KERNEL
# =====================================================================
def s_kernel(d, t, dur):
    S.chrome(d, "STEP 6 · KERNEL", "The kernel takes charge", "The kernel unpacks itself, sets up memory tables so each program gets a private view, then wakes the other cores.", t, dur)
    strip(d, 5, t)
    ku = prog(t, 0.6, 1.8)
    sw = 120 + 260 * ku
    sh = 100 + 120 * ku
    cx, cy = 360, 540
    sketch(d, (cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2), C_K, prog(t, 0.1, 0.6), fill=mix(S.PANEL, C_K, 0.15))
    if ku < 1:
        for i in range(3):
            stroke(d, [(cx - sw / 2 + 16 + j * 10, cy - 20 + i * 20 + 6 * math.sin(j)) for j in range(int((sw - 32) / 10))], S.DIM, 1.0, 2)
    write(d, (cx, cy), "kernel" if ku >= 1 else "", 40, C_K, t, 1.8)
    write(d, (cx, 330), "packed, then unpacked", 30, S.DIM, t, 0.4, w="Medium")
    # memory tables
    gx, gy, cs = 680, 360, 70
    write(d, (gx + 3 * cs, 320), "memory tables", 30, C_K, t, 2.0)
    cols = [S.ACCENT, S.GOOD, S.EXTRA, S.HILITE]
    for i in range(24):
        r, c = i // 6, i % 6
        kk = prog(t, 2.0 + i * 0.05, 2.3 + i * 0.05)
        sketch(d, (gx + c * cs + 3, gy + r * cs + 3, gx + (c + 1) * cs - 3, gy + (r + 1) * cs - 3), cols[(i * 7) % 4], kk, r=4, width=3,
               fill=mix(S.PANEL, cols[(i * 7) % 4], 0.25))
    write(d, (gx + 3 * cs, gy + 4 * cs + 40), "each program: its own private view", 26, S.TXT, t, 3.2, w="Medium")
    # cores waking
    write(d, (1500, 320), "wake the other cores", 30, C_RST, t, 3.6)
    lit = [1.0] + [prog(t, 3.8 + i * 0.25, 4.1 + i * 0.25) for i in range(7)]
    cores(d, 1250, 370, 4, 2, 110, 30, lit, prog(t, 3.4, 3.8), C_RST)

def s_drivers(d, t, dur):
    S.chrome(d, "STEP 6 · KERNEL", "Drivers, one by one", "A driver knows how to talk to one kind of hardware. The kernel loads storage first, then graphics, input, network and sound.", t, dur)
    strip(d, 5, t)
    c0 = (960, 560)
    gcircle(d, c0, 100, C_K, prog(t, 0.2, 0.8), 6, fill=S.PANEL)
    write(d, c0, "kernel", 40, C_K, t, 0.5)
    devs = [("storage", S.GOOD), ("graphics", S.EXTRA), ("keyboard, mouse", S.ACCENT), ("network", S.BLUE), ("sound", S.HILITE), ("USB", S.BAD)]
    for i, (n, c) in enumerate(devs):
        ang = math.radians(-90 + i * 60 + 0)
        ex, ey = c0[0] + 560 * math.cos(ang), c0[1] + 230 * math.sin(ang)
        a = 1.0 + i * 0.55
        sx, sy = c0[0] + 110 * math.cos(ang), c0[1] + 105 * math.sin(ang)
        stroke(d, [(sx, sy), (ex - 0.25 * (ex - c0[0]), ey - 0.15 * (ey - c0[1]))], S.DIM, prog(t, a, a + 0.4), 4)
        bw = S.textlen(d, n, 30) / 2 + 30
        sketch(d, (ex - bw, ey - 34, ex + bw, ey + 34), c, prog(t, a + 0.3, a + 0.6), fill=mix(S.PANEL, c, 0.15 * prog(t, a + 0.5, a + 0.8)))
        write(d, (ex, ey), n, 30, c, t, a + 0.4)
        tick(d, ex + bw + 30, ey - 6, 16, S.GOOD, prog(t, a + 0.6, a + 0.9), 5)
    write(d, (1760, 840), "(order shown is a simplification)", 22, S.DIM, t, 4.4, w="Medium", anchor="rm")

def s_rootfs(d, t, dur):
    S.chrome(d, "STEP 6 · KERNEL", "Mounting the root file system", "With storage working, the kernel mounts the root file system: the top of the folder tree, on your real disk.", t, dur)
    strip(d, 5, t)
    disk_icon(d, 300, 470, 260, 180, S.GOOD, prog(t, 0.2, 0.9))
    write(d, (300, 430), "your disk", 30, S.GOOD, t, 0.5)
    carrow(d, [(450, 560), (700, 400)], S.HILITE, prog(t, 1.0, 1.5), 5)
    write(d, (560, 520), "mount", 30, S.HILITE, t, 1.3, anchor="lm")
    root = (1150, 330)
    gcircle(d, root, 48, S.HILITE, prog(t, 1.3, 1.8), 5, fill=S.PANEL)
    write(d, root, "/", 44, S.HILITE, t, 1.6)
    write(d, (1230, 330), "the root", 28, S.HILITE, t, 1.8, anchor="lm")
    kids = ["system", "programs", "users", "settings"]
    for i, n in enumerate(kids):
        x = 800 + i * 240
        a = 2.0 + i * 0.4
        stroke(d, [(root[0], root[1] + 48), (root[0], 420), (x, 420), (x, 470)], S.LINE, prog(t, a, a + 0.5), 4)
        folder(d, x - 60, 510, n, S.TXT, prog(t, a + 0.4, a + 0.7), 26)
        for j in range(2):
            y = 600 + j * 70
            stroke(d, [(x - 40, 530), (x - 40, y), (x - 10, y)], S.DIM, prog(t, a + 0.8 + j * 0.2, a + 1.1 + j * 0.2), 3)
            sketch(d, (x, y - 20, x + 34, y + 20), S.DIM, prog(t, a + 1.0 + j * 0.2, a + 1.3 + j * 0.2), r=4, width=3)
    write(d, (1240, 820), "(folder names are examples; they vary by system)", 22, S.DIM, t, 4.4, w="Medium")

def s_init(d, t, dur):
    S.chrome(d, "STEP 6 · KERNEL", "Process number one", "The first user program (process 1 on Linux-like systems) starts everything else, ending with the login screen.", t, dur)
    strip(d, 5, t)
    c1 = (330, 540)
    gcircle(d, c1, 90, C_K, prog(t, 0.2, 0.9), 6, fill=S.PANEL)
    write(d, c1, "1", 80, S.HILITE, t, 0.7)
    write(d, (c1[0], 680), "the first process", 30, C_K, t, 1.0)
    kids = [("background services", S.ACCENT), ("networking", S.BLUE), ("sound", S.HILITE), ("graphical display", S.EXTRA)]
    for i, (n, c) in enumerate(kids):
        y = 330 + i * 125
        a = 1.4 + i * 0.5
        carrow(d, [(425, 540), (560, 540), (620, y), (700, y)], S.LINE, prog(t, a, a + 0.5), 4)
        sketch(d, (710, y - 42, 1120, y + 42), c, prog(t, a + 0.3, a + 0.7))
        write(d, (915, y), n, 30, c, t, a + 0.4)
    carrow(d, [(1130, 705), (1290, 705), (1350, 620)], S.GOOD, prog(t, 3.6, 4.1), 5)
    kl = prog(t, 4.0, 4.6)
    monitor(d, 1360, 340, 1760, 620, kl, prog(t, 4.4, 5.0))
    write(d, (1560, 730), "the login screen!", 40, S.GOOD, t, 4.8)


# =====================================================================
# wrap-up
# =====================================================================
def s_timeline(d, t, dur):
    S.chrome(d, "", "How long does each step take?", "It varies. Roughly: power, a fraction of a second; firmware, a few seconds; bootloader, quick; kernel, a few more.", t, dur)
    x0, x1, y0, y1 = 200, 1720, 470, 560
    segs = [("power", C_PWR, 0.06, "a fraction of a second"), ("firmware", C_FW, 0.4, "often a few seconds; longer with new RAM"),
            ("loader", C_BL, 0.08, "usually quick"), ("kernel + services", C_K, 0.46, "a few seconds more")]
    x = x0
    for i, (n, c, f, desc) in enumerate(segs):
        w = (x1 - x0) * f
        a = 0.4 + i * 0.7
        sketch(d, (x + 2, y0, x + w - 2, y1), c, prog(t, a, a + 0.5), r=8, fill=mix(S.PANEL, c, 0.3))
        top = i % 2 == 0
        tx = x + w / 2
        if top:
            stroke(d, [(tx, y0 - 6), (tx, y0 - 60)], c, prog(t, a + 0.3, a + 0.5), 3)
            write(d, (tx, y0 - 125), n, 32, c, t, a + 0.3)
            write(d, (max(tx, 360), y0 - 85), desc, 24, S.TXT, t, a + 0.5, w="Medium")
        else:
            stroke(d, [(tx, y1 + 6), (tx, y1 + 60)], c, prog(t, a + 0.3, a + 0.5), 3)
            write(d, (tx, y1 + 95), n, 32, c, t, a + 0.3)
            write(d, (tx, y1 + 135), desc, 24, S.TXT, t, a + 0.5, w="Medium")
        x += w
    if t > 3.4:
        u = clamp((t - 3.4) / 2.5)
        xx = x0 + (x1 - x0) * u
        S.line(d, [(xx, y0 - 20), (xx, y1 + 20)], S.TXT, 5)
    tag(d, (W // 2, 810), "rough example only: real machines vary widely", S.HILITE, prog(t, 3.0, 3.5))

def s_recap(d, t, dur):
    S.chrome(d, "RECAP", "From button to login", "Power Good. Reset vector. POST and memory training. A 55 AA sector or an EFI file. Bootloader, kernel, login.", t, dur)
    journey(d, t, a=0.3, per=0.7, travel=True,
            words=["Power Good", "FFFF FFF0", "POST, RAM", "55 AA / EFI", "kernel into RAM", "process 1"])

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    write(d, (W // 2, 360), "NEXT EPISODE", 38, S.ACCENT, t, 0.2, 0.8)
    write(d, (W // 2, 480), "How does a microcontroller", 80, S.TXT, t, 0.6, 1.8)
    write(d, (W // 2, 580), "actually run your code?", 80, S.TXT, t, 1.6, 2.6)
    tw = S.textlen(d, "actually run your code?", 80, "Bold")
    stroke(d, [(W / 2 - tw / 2, 650), (W / 2 + tw / 2, 654)], S.HILITE, prog(t, 2.6, 3.2), 5)
    write(d, (W // 2, 760), "Subscribe so you don't miss it", 38, S.DIM, t, 3.0, 3.8, w="Medium")


def _paced(fn, d, t, dur):
    """Once narration stretches a scene, spread its build over roughly the first 60% instead of the first few seconds."""
    f = min(1.8, max(1.0, dur * 0.6 / 6.0))
    fn(d, t / f, dur)

def paced(fn):
    return functools.partial(_paced, fn)   # picklable, for narrate.py's process pool

SCENES = [
    ("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
    ("03_button", s_button, 8), ("04_rails", s_rails, 8), ("05_powergood", s_powergood, 8), ("06_vrm", s_vrm, 8),
    ("07_reset", s_reset, 8), ("08_helper", s_helper, 8), ("09_bsp", s_bsp, 8), ("10_vector", s_vector, 8), ("11_jump", s_jump, 8),
    ("12_firmware", s_firmware, 8), ("13_post", s_post, 8), ("14_training", s_training, 8), ("15_devices", s_devices, 8),
    ("16_mbr", s_mbr, 8), ("17_uefi", s_uefi, 8), ("18_compare", s_compare, 8), ("19_secure", s_secure, 8),
    ("20_loader", s_loader, 8), ("21_modes", s_modes, 8), ("22_relay", s_relay, 8),
    ("23_kernel", s_kernel, 8), ("24_drivers", s_drivers, 8), ("25_rootfs", s_rootfs, 8), ("26_init", s_init, 8),
    ("27_timeline", s_timeline, 8), ("28_recap", s_recap, 8), ("29_end", s_end, 6),
]
SCENES = [(n, paced(fn), m) for n, fn, m in SCENES]

NARRATION = {
 "01_hook": "You press one button, and a few seconds later, there's a login screen. But at the moment you press it, the processor knows almost nothing. Not how much memory it has. Not which disks are plugged in. So how does a computer start itself? Let's follow that one button press, all the way.",
 "02_cover": "Right. Here's our route. First, power, which has to settle before anything runs. Then reset, and the processor's very first instruction. Then the firmware, which checks the hardware. Then the hunt for a boot device. Then the bootloader. And finally the kernel, which takes you to the login screen.",
 "03_button": "Step one: power. In a desktop P C, the power button doesn't switch the power on directly. While it's plugged in, the power supply keeps a small standby supply running, at five volts. That keeps a little circuit on the motherboard awake. Press the button, and that circuit asks the supply to switch on properly.",
 "04_rails": "The supply now brings up its main outputs, called rails. Twelve volts, five volts, and three point three volts. They can't jump there instantly. Each one ramps up over a few milliseconds, and must settle close to its target, typically within about five percent.",
 "05_powergood": "Now, here's the clever bit. The supply has one more wire, called Power Good. It stays low until every rail is steady, then waits a little longer, typically between a tenth and half a second. Only then does Power Good go high. It's the all-clear.",
 "06_vrm": "But a processor doesn't run on twelve volts. Its core needs something closer to one volt, and a lot of current. So regulators on the motherboard, right beside the processor, step the twelve volts down, switching rapidly through small coils.",
 "07_reset": "Step two: reset. All this time, the processor has been held in reset by the motherboard. Think of it as a hand on its shoulder, saying, wait. Meanwhile, its registers sit at fixed starting values. Once the power is good, the board lets go, and the processor begins.",
 "08_helper": "On many modern P Cs, there's a hidden first step. A small helper processor, in the chipset or the processor package, starts before the main cores. It checks that the firmware looks genuine. The details vary a lot between designs, so we'll leave it there.",
 "09_bsp": "Even if your processor has many cores, only one starts running. It's called the bootstrap processor. The others wait to be woken later. And that core starts in an old, simple mode called real mode: the sixteen-bit mode of the original P C processors.",
 "10_vector": "So where does the first instruction come from? It's hard-wired. On x eighty six, the processor fetches it from address hex, F F F F, F F F zero. That's just sixteen bytes below the four gigabyte mark, and the motherboard makes the firmware chip appear right there. This is the reset vector.",
 "11_jump": "Sixteen bytes isn't much room. So the code there is usually a jump, to the real start of the firmware, further down the same chip. And notice what isn't involved yet: your R A M. It hasn't been set up, so the processor can't use it at all.",
 "12_firmware": "Step three: firmware. This is the program stored in that flash chip, which keeps it with the power off. On older P Cs, it's called the B I O S. Modern ones follow a standard called U E F I. With no working R A M yet, many systems borrow the processor's cache as temporary scratch memory.",
 "13_post": "First job: the Power-On Self-Test, or post. The firmware sets up the chipset, and looks for memory, graphics, storage and U S B devices. If something essential is broken, it may not be able to show a message yet. So many boards use beeps, or a code on a small light.",
 "14_training": "Then one of the biggest jobs: memory training. Each memory stick carries a tiny chip describing its size and speed. The firmware reads it, then tunes the timing of the signals, sliding the moment it samples each bit until it finds the sweet spot. That's why new R A M can make the first boot noticeably slow.",
 "15_devices": "With memory working, the firmware maps out the rest of the machine: graphics, drives, U S B ports and the network. It also reads your saved boot order. That's simply a list, saying where to look for an operating system first, second, and third.",
 "16_mbr": "Step four: finding a boot device. The old B I O S way is wonderfully simple. Read the first sector of the disk, just five hundred and twelve bytes. Check that the last two bytes are hex, five five, A A. If they are, copy the sector into memory at hex, seven C zero zero, and jump to it.",
 "17_uefi": "U E F I is smarter. It understands partitions and files. It looks for a small partition called the E F I system partition, usually formatted with the simple FAT file system. Bootloaders sit inside as ordinary files, and the firmware keeps a list of boot entries pointing at them.",
 "18_compare": "So, two styles. Legacy B I O S loads one raw sector, and runs whatever is in it, still in sixteen-bit mode. U E F I loads a proper program from a file, and on a modern P C, the processor is often already in sixty-four-bit mode. Most modern P Cs boot the U E F I way.",
 "19_secure": "U E F I can also do Secure Boot. The firmware stores a set of trusted keys. Before running a bootloader, it checks the file's digital signature against them. Signed by a trusted key? It runs. Altered, or unsigned? Refused. Each stage can then check the next: a chain of trust.",
 "20_loader": "Step five: the bootloader. It's a small program with one job: get the operating system's kernel into memory. It may show a menu first. Then it copies the kernel into R A M, often with a small starter file system, and leaves notes for the kernel, like a map of the memory.",
 "21_modes": "Remember, the processor woke up in sixteen-bit mode. To run a modern system, it has to climb, through thirty-two-bit protected mode, up to sixty-four-bit long mode. With legacy B I O S, the bootloader or kernel makes that climb. With U E F I, the firmware usually did it already.",
 "22_relay": "Then the bootloader jumps into the kernel, and its job is done. Notice the pattern. Each stage loads the next, then hands over, like a relay race. And each runner is bigger and smarter than the last. That's where the word boot comes from: bootstrapping, pulling yourself up by your own bootstraps.",
 "23_kernel": "Step six: the kernel, the heart of the operating system. It's often stored compressed, so it may start by unpacking itself. Then it takes charge of memory, setting up tables that give every program its own private view. And at last, it wakes the other cores.",
 "24_drivers": "Next, drivers. A driver is code that knows how to talk to one kind of hardware. The kernel detects the devices and loads the matching drivers. Storage matters most, so it can read the disk. Then graphics, keyboards, networking and sound.",
 "25_rootfs": "With storage working, the kernel can mount the root file system. That's the top of the folder tree, where everything else hangs. It's the moment the operating system can finally reach its own files, on your real disk.",
 "26_init": "Finally, the kernel starts the very first user program. On Linux and similar systems, it's literally process number one. Its job is to start everything else: background services, networking, sound, and the display. And the last thing it brings up is the login screen.",
 "27_timeline": "How long does all this take? It varies a lot, but roughly: the power settles in a fraction of a second. The firmware often takes a few seconds, longer if it's training new memory. The bootloader is usually quick. And the kernel and its services take a few seconds more.",
 "28_recap": "Let's recap. Power: the rails settle, and Power Good goes high. Reset: one core wakes, and fetches from the reset vector. Firmware: post, and memory training. Boot device: a sector ending in five five, A A, or a file on the E F I partition. Then the bootloader, the kernel, and the login screen.",
 "29_end": "Next episode: how does a microcontroller actually run your code? Subscribe, so you don't miss it.",
}
OUTPUT = "how_a_computer_boots_ep1_narrated.mp4"


def render(name, fn, dur): S.render_to("ep1", name, fn, dur)

if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    print(S.preview("ep1", SCENES))
