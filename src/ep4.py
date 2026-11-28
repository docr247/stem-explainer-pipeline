"""Tech 101, episode 4: How does USB know what you plugged in?  (chalk style, what-happens-if format)

Follows one event, plugging a new device into a USB 2.0 port, through enumeration until it is ready to use.
"""
import math, sys
import style
from style import clamp, ease, prog, grow, mix

S = style.get("chalk")
W, H, FPS = S.W, S.H, S.FPS
VOICE, SPEED, LANG = S.VOICE, S.SPEED, S.LANG

HOSTC, DEVC = S.ACCENT, S.GOOD          # host is always chalk-blue, the device always chalk-green
DP, DM, VB, GN = S.HILITE, S.EXTRA, S.BAD, S.DIM   # D+ yellow, D- violet, VBUS pink, ground grey


# ======================================================================= helpers
def A(t, dur, a, b):
    """Progress 0..1 between fractions a and b of the scene, so animation stretches with the narration."""
    return prog(t / dur, a, b)

def lerp(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)

def chalk(d, pts, col=None, k=1.0, width=5, st=S):
    """A chalk line that draws itself: k = fraction drawn so far."""
    if k <= 0.01: return
    st.line(d, grow([tuple(p) for p in pts], clamp(k)), col, width)

def chalk_arrow(d, a, b, col=None, k=1.0, width=5, st=S):
    if k <= 0.03: return
    st.arrow(d, a, lerp(a, b, clamp(k)), col, width)

def write(d, xy, s, size=40, col=None, k=1.0, w="Bold", anchor="la", mono=False, st=S):
    """Text that appears as if written: k = fraction of characters written (left to right)."""
    if k <= 0.01 or not s: return
    n = int(math.ceil(len(s) * clamp(k)))
    if n >= len(s):
        st.text(d, xy, s, size, col, w, anchor, mono); return
    full = st.textlen(d, s, size, w, mono)
    x, y = xy
    if anchor[0] == "m": x -= full / 2
    elif anchor[0] == "r": x -= full
    st.text(d, (x, y), s[:n], size, col, w, "l" + anchor[1], mono)

def sketch_box(d, xy, col=None, k=1.0, r=16, width=4, fill=None, st=S):
    """A panel whose outline is sketched round in one stroke while the fill fades in."""
    if k <= 0.01: return
    d.rounded_rectangle(xy, r, fill=st.fade(fill or st.PANEL, clamp(k * 1.6)))
    pts = st._rr_points(xy, r)
    chalk(d, pts + [pts[0]], col or st.LINE, k, width, st)

def node(d, xy, title, col, k, sub=None, size=34, st=S):
    sketch_box(d, xy, col, k, st=st)
    x0, y0, x1, y1 = xy
    cy = (y0 + y1) / 2
    write(d, ((x0 + x1) / 2, cy - (18 if sub else 0)), title, size, col, (k - 0.3) / 0.7, "Bold", "mm", st=st)
    if sub: write(d, ((x0 + x1) / 2, cy + 26), sub, 26, st.DIM, (k - 0.5) / 0.5, "Regular", "mm", st=st)

def msg(d, a, b, label, col, k, size=30, mono=False, dy=-30, st=S):
    """One line of the host/device conversation: a chalk arrow with its words written above it."""
    if k <= 0.01: return
    chalk_arrow(d, a, b, col, k, 5, st)
    write(d, ((a[0] + b[0]) / 2, min(a[1], b[1]) + dy), label, size, col, (k - 0.25) / 0.75, "Bold", "mm", mono, st)

def dots(d, a, b, t, col, n=3, speed=0.5, r=7, k=1.0, st=S):
    """Little packets of charge travelling along a wire."""
    if k <= 0.01: return
    for i in range(n):
        x, y = lerp(a, b, (t * speed + i / n) % 1.0)
        d.ellipse([x - r, y - r, x + r, y + r], fill=st.fade(col, k))

def resistor(d, top, bot, col=None, k=1.0, st=S):
    """Vertical zig-zag resistor from top to bottom (drawn as one growing stroke)."""
    x, y0 = top; y1 = bot[1]
    L = y1 - y0; lead = L * 0.25; n = 6; zz = (L - 2 * lead) / n
    pts = [(x, y0), (x, y0 + lead)]
    for i in range(n): pts.append((x + (14 if i % 2 == 0 else -14), y0 + lead + zz * (i + 0.5)))
    pts += [(x, y1 - lead), (x, y1)]
    chalk(d, pts, col or st.LINE, k, 4, st)

def ground(d, x, y, col=None, k=1.0, st=S):
    if k <= 0.01: return
    for i, hw in enumerate((26, 16, 7)):
        st.line(d, [(x - hw, y + i * 10), (x + hw, y + i * 10)], col or st.DIM, 4, k)

def joint(d, x, y, col, k=1.0, st=S):
    if k > 0.01: d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=st.fade(col, k))

def trace(d, x0, y0, w, h, f, k, col, width=5, step=3, st=S):
    """Plot level f(u) (0..1) across w pixels; k reveals it left to right."""
    if k <= 0.01: return
    pts = [(x0 + px, y0 + h - f(px / w) * h) for px in range(0, int(w * clamp(k)) + 1, step)]
    if len(pts) > 1: st.line(d, pts, col, width)

def badge(d, c, s, col, k, r=44, size=46, st=S):
    if k <= 0.01: return
    st.circle(d, c, r, st.PANEL, col, 4, k)
    st.text(d, c, s, size, col, "Bold", "mm", mono=True, k=k)

def cross(d, c, s, col, k, st=S):
    x, y = c
    chalk(d, [(x - s, y - s), (x + s, y + s)], col, k * 2, 5, st)
    chalk(d, [(x + s, y - s), (x - s, y + s)], col, k * 2 - 1, 5, st)

def tick(d, c, s, col, k, st=S):
    x, y = c
    chalk(d, [(x - s, y), (x - s * 0.3, y + s * 0.7), (x + s, y - s * 0.8)], col, k, 6, st)

def icon(d, kind, cx, cy, s, col, k, st=S):
    """Generic hand-drawn device sketches (no brands)."""
    if k <= 0.01: return
    ln = lambda pts, w=4: chalk(d, pts, col, k, w, st)
    if kind == "keyboard":
        x0, y0, x1, y1 = cx - 90 * s, cy - 38 * s, cx + 90 * s, cy + 38 * s
        ln([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
        for r in range(3):
            for c in range(8):
                kx, ky = x0 + 12 * s + c * 20.5 * s, y0 + 10 * s + r * 17 * s
                d.rectangle([kx, ky, kx + 13 * s, ky + 10 * s], fill=st.fade(col, k * 0.8))
        d.rectangle([cx - 45 * s, y1 - 15 * s, cx + 45 * s, y1 - 6 * s], fill=st.fade(col, k * 0.8))
    elif kind == "mouse":
        pts = st._rr_points((cx - 32 * s, cy - 48 * s, cx + 32 * s, cy + 48 * s), 30 * s)
        ln(pts + [pts[0]])
        ln([(cx, cy - 48 * s), (cx, cy - 12 * s)]); ln([(cx - 32 * s, cy - 12 * s), (cx + 32 * s, cy - 12 * s)])
    elif kind == "drive":
        ln([(cx - 70 * s, cy - 28 * s), (cx + 30 * s, cy - 28 * s), (cx + 30 * s, cy + 28 * s), (cx - 70 * s, cy + 28 * s), (cx - 70 * s, cy - 28 * s)])
        ln([(cx + 30 * s, cy - 18 * s), (cx + 72 * s, cy - 18 * s), (cx + 72 * s, cy + 18 * s), (cx + 30 * s, cy + 18 * s)])
        for yy in (-8, 4):
            d.rectangle([cx + 44 * s, cy + yy * s, cx + 56 * s, cy + (yy + 6) * s], fill=st.fade(col, k))
    elif kind == "headset":
        arc = [(cx + 62 * s * math.cos(a), cy + 62 * s * math.sin(a)) for a in [math.pi + i * math.pi / 16 for i in range(17)]]
        ln(arc, 5)
        for sx in (-1, 1):
            x = cx + sx * 62 * s
            pts = st._rr_points((x - 16 * s, cy - 8 * s, x + 16 * s, cy + 40 * s), 10 * s)
            ln(pts + [pts[0]])
        ln([(cx - 62 * s, cy + 36 * s), (cx - 40 * s, cy + 60 * s), (cx - 10 * s, cy + 62 * s)])
        d.ellipse([cx - 14 * s, cy + 56 * s, cx - 2 * s, cy + 68 * s], fill=st.fade(col, k))
    elif kind == "pad":
        pts = st._rr_points((cx - 80 * s, cy - 34 * s, cx + 80 * s, cy + 34 * s), 30 * s)
        ln(pts + [pts[0]])
        ln([(cx - 52 * s, cy), (cx - 28 * s, cy)]); ln([(cx - 40 * s, cy - 12 * s), (cx - 40 * s, cy + 12 * s)])
        for dx, dy in ((40, -10), (56, 6)):
            st.circle(d, (cx + dx * s, cy + dy * s), 7 * s, None, col, 3, k)
    elif kind == "card":
        ln([(cx - 55 * s, cy - 32 * s), (cx + 55 * s, cy - 32 * s), (cx + 55 * s, cy + 32 * s), (cx - 55 * s, cy + 32 * s), (cx - 55 * s, cy - 32 * s)])
        ln([(cx - 34 * s, cy - 32 * s), (cx - 34 * s, cy - 6 * s), (cx + 34 * s, cy - 6 * s), (cx + 34 * s, cy - 32 * s)])
    elif kind == "disk":
        pts = st._rr_points((cx - 60 * s, cy - 40 * s, cx + 60 * s, cy + 40 * s), 12 * s)
        ln(pts + [pts[0]])
        d.ellipse([cx + 34 * s, cy + 20 * s, cx + 44 * s, cy + 30 * s], fill=st.fade(col, k))
    elif kind == "hub":
        pts = st._rr_points((cx - 80 * s, cy - 26 * s, cx + 80 * s, cy + 26 * s), 12 * s)
        ln(pts + [pts[0]])
        for i in range(4):
            x = cx - 60 * s + i * 40 * s
            d.rectangle([x - 12 * s, cy - 6 * s, x + 12 * s, cy + 6 * s], fill=st.fade(col, k))
    elif kind == "computer":
        ln([(cx - 110 * s, cy - 80 * s), (cx + 110 * s, cy - 80 * s), (cx + 110 * s, cy + 60 * s), (cx - 110 * s, cy + 60 * s), (cx - 110 * s, cy - 80 * s)])
        ln([(cx, cy + 60 * s), (cx, cy + 86 * s)]); ln([(cx - 50 * s, cy + 88 * s), (cx + 50 * s, cy + 88 * s)])
    elif kind == "chip":
        ln([(cx - 50 * s, cy - 40 * s), (cx + 50 * s, cy - 40 * s), (cx + 50 * s, cy + 40 * s), (cx - 50 * s, cy + 40 * s), (cx - 50 * s, cy - 40 * s)])
        for i in range(4):
            y = cy - 27 * s + i * 18 * s
            ln([(cx - 66 * s, y), (cx - 50 * s, y)], 3); ln([(cx + 50 * s, y), (cx + 66 * s, y)], 3)

def plug(d, x, y, s, col, k, dirn=1, st=S):
    """Generic plug seen from the side (body + metal shell), tip at (x, y), pointing right (dirn=1) or left (-1). No logo."""
    if k <= 0.01: return
    f = lambda dx: x + dirn * dx * s
    bx = sorted((f(-210), f(-90)))
    sketch_box(d, (bx[0], y - 34 * s, bx[1], y + 34 * s), col, k, int(10 * s), st=st)
    chalk(d, [(f(-90), y - 22 * s), (f(0), y - 22 * s), (f(0), y + 22 * s), (f(-90), y + 22 * s)], st.LINE, k, 4, st)
    for xx in (-60, -32):
        a, b = sorted((f(xx), f(xx + 14)))
        d.rectangle([a, y - 10 * s, b, y - 2 * s], fill=st.fade(st.DIM, k))


# ======================================================================= chapter 0
def s_hook(d, t, dur):
    S.chrome(d, "", "", "Plug in a keyboard and it just works. But at first, the computer has no idea what it is. So it asks.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    # the computer, with a port on its right-hand side
    sketch_box(d, (220, 300, 760, 700), HOSTC, k)
    write(d, (490, 345), "computer", 36, HOSTC, (k - 0.4) / 0.6, "Bold", "mm")
    chalk(d, [(760, 470), (720, 470), (720, 540), (760, 540)], S.LINE, k, 4)
    # the keyboard and its cable; the plug slides in
    pin = ease(clamp((t / dur - 0.06) / 0.16))
    px = 1160 - 420 * pin
    icon(d, "keyboard", 1520, 720, 1.5, DEVC, A(t, dur, 0.02, 0.1))
    chalk(d, [(px + 190, 505), (px + 260, 505), (1380, 600), (1450, 668)], S.DIM, k, 5)
    plug(d, px, 505, 0.9, DEVC, k, -1)
    # the question marks
    kq = A(t, dur, 0.24, 0.32)
    write(d, (490, 520), "?", 190, S.HILITE, kq, "Bold", "mm")
    qs = ["Who made it?", "What is it?", "How fast can it talk?"]
    for i, q in enumerate(qs):
        write(d, (1080, 300 + i * 70), q, 42, S.TXT, A(t, dur, 0.34 + i * 0.1, 0.42 + i * 0.1), "Bold", "la")
    if t / dur > 0.7:
        S.pill(d, (1580, 560), "it has to ask", 32, S.HILITE, A(t, dur, 0.7, 0.76))


def s_cover(d, t, dur):
    S.chrome(d, "", "Here's what we'll cover", "One plug-in, start to finish: attach, reset, who are you, an address, configuration, and a driver.", t, dur)
    items = [("Attach", "a resistor says hello"), ("Reset", "everyone starts at zero"), ("Who are you?", "the device descriptor"),
             ("An address", "a number of its own"), ("Configuration", "what's inside, and what kind"), ("Driver", "matched, and ready to use")]
    cols = [DP, VB, HOSTC, DEVC, DM, S.BLUE]
    for i, (a, b) in enumerate(items):
        kk = A(t, dur, 0.05 + i * 0.09, 0.14 + i * 0.09)
        col, row = i // 3, i % 3
        x, y = 200 + col * 800, 270 + row * 175
        sketch_box(d, (x, y, x + 720, y + 140), cols[i], kk)
        S.circle(d, (x + 70, y + 70), 40, None, cols[i], 4, kk)
        S.text(d, (x + 70, y + 72), str(i + 1), 44, cols[i], "Bold", "mm", k=kk)
        write(d, (x + 140, y + 50), a, 42, S.TXT, (kk - 0.3) / 0.7, "Bold", "lm")
        write(d, (x + 140, y + 100), b, 30, S.DIM, (kk - 0.5) / 0.5, "Regular", "lm")
    # a chalk arrow that follows the order: down the left, then down the right
    kp = A(t, dur, 0.62, 0.8)
    chalk_arrow(d, (950, 330), (950, 760), S.DIM, kp, 4)


# ======================================================================= chapter 1: attach
def s_wires(d, t, dur):
    S.chrome(d, "STEP 1 · ATTACH", "Four wires that matter", "Classic USB 2.0: VBUS at 5 V, ground, and a data pair called D+ and D−.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    # the plug face, seen end-on (a generic rectangle with four contacts)
    sketch_box(d, (200, 290, 1000, 470), S.LINE, k, 20)
    write(d, (600, 270), "plug, seen end-on", 28, S.DIM, (k - 0.5) / 0.5, "Regular", "mm")
    pins = [(300, "1", "V bus", "5 V", VB), (500, "2", "D−", "data", DM), (700, "3", "D+", "data", DP), (900, "4", "GND", "ground", GN)]
    for i, (x, n, nm, sub, c) in enumerate(pins):
        kk = A(t, dur, 0.08 + i * 0.08, 0.16 + i * 0.08)
        d.rectangle([x - 40, 400, x + 40, 440], fill=S.fade(c, kk))
        S.text(d, (x, 365), n, 30, S.DIM, "Bold", "mm", k=kk)
        chalk(d, [(x, 440), (x, 650)], c, kk, 5)
        write(d, (x, 690), nm, 42, c, (kk - 0.4) / 0.6, "Bold", "mm")
        write(d, (x, 740), sub, 28, S.DIM, (kk - 0.6) / 0.4, "Regular", "mm")
    # right: the data pair carries data as a difference
    k2 = A(t, dur, 0.45, 0.55)
    write(d, (1450, 300), "the data pair", 36, S.TXT, k2, "Bold", "mm")
    rev = A(t, dur, 0.5, 0.75)
    bits = [1, 0, 0, 1, 0, 1, 1, 0, 1, 0]
    f = lambda u: 0.85 if bits[min(9, int(u * 10))] else 0.15
    write(d, (1130, 410), "D+", 32, DP, k2, "Bold", "rm")
    trace(d, 1150, 360, 600, 100, f, rev, DP)
    write(d, (1130, 560), "D−", 32, DM, k2, "Bold", "rm")
    trace(d, 1150, 510, 600, 100, lambda u: 1 - f(u), rev, DM)
    write(d, (1450, 660), "always opposite:", 30, S.DIM, A(t, dur, 0.72, 0.8), "Regular", "mm")
    write(d, (1450, 705), "data = the difference", 34, S.HILITE, A(t, dur, 0.76, 0.84), "Bold", "mm")
    S.pill(d, (1450, 780), "illustration", 24, S.DIM, A(t, dur, 0.78, 0.84))


def schem(d, t, dur, mode):
    """Host-side pull-downs on D+ and D−, plus (mode 'full') a device pulling D+ up."""
    k = A(t, dur, 0.0, 0.08)
    yp, ym = 440, 580
    sketch_box(d, (100, 270, 620, 800), HOSTC, k)
    write(d, (360, 310), "HOST (or hub) PORT", 32, HOSTC, (k - 0.4) / 0.6, "Bold", "mm")
    full = mode == "full"
    plug_t = 0.3
    kw = A(t, dur, 0.04, 0.2)
    xend = 1180
    for x0, y, c, nm in ((300, yp, DP, "D+"), (460, ym, DM, "D−")):
        chalk(d, [(x0, y), (xend, y)], c, kw, 5)
        write(d, (880, y - 34), nm, 34, c, kw, "Bold", "mm")
    # pull-down resistors to ground
    kr = A(t, dur, 0.1, 0.24)
    for x, y, side in ((300, yp, "l"), (460, ym, "r")):
        joint(d, x, y, S.LINE, kr)
        resistor(d, (x, y), (x, 740), S.LINE, kr)
        ground(d, x, 740, S.DIM, kr)
        lx = x - 28 if side == "l" else x + 28
        S.text(d, (lx, 640 if side == "l" else 680), "15 kΩ", 26, S.TXT, "Bold", "rm" if side == "l" else "lm", mono=True, k=kr)
    write(d, (200, 400), "pull-downs", 28, S.DIM, A(t, dur, 0.2, 0.28), "Regular", "mm")
    if not full:
        ke = A(t, dur, 0.25, 0.35)
        sketch_box(d, (1180, 380, 1440, 640), S.DIM, ke, 12, 3, fill=S.BG)
        write(d, (1310, 490), "empty", 34, S.DIM, (ke - 0.3) / 0.7, "Bold", "mm")
        write(d, (1310, 535), "port", 34, S.DIM, (ke - 0.3) / 0.7, "Bold", "mm")
        kv = A(t, dur, 0.4, 0.48)
        for y, c in ((yp, DP), (ym, DM)):
            S.pill(d, (1040, y - 34), "0 V", 28, c, kv)
        write(d, (1620, 470), "both lines", 36, S.TXT, A(t, dur, 0.55, 0.62), "Bold", "mm")
        write(d, (1620, 520), "held near 0 V", 36, S.TXT, A(t, dur, 0.58, 0.66), "Bold", "mm")
        write(d, (1620, 600), "= nothing attached", 34, S.HILITE, A(t, dur, 0.66, 0.74), "Bold", "mm")
        for y, c in ((yp, DP), (ym, DM)):
            dots(d, (1170, y), (1170, y), t, c, 1, 0, 0)
        return
    # the device arrives
    kd = A(t, dur, 0.14, 0.24)
    sketch_box(d, (1340, 270, 1800, 800), DEVC, kd)
    write(d, (1570, 760), "FULL-SPEED DEVICE", 30, DEVC, (kd - 0.4) / 0.6, "Bold", "mm")
    kc = A(t, dur, 0.24, plug_t)
    for y, c in ((yp, DP), (ym, DM)):
        chalk(d, [(xend, y), (1700, y)], c, kc, 5)
    kr2 = A(t, dur, 0.18, 0.28)
    chalk(d, [(1480, 330), (1640, 330)], VB, kr2, 5)
    write(d, (1660, 330), "3.3 V", 28, VB, kr2, "Bold", "lm")
    resistor(d, (1560, 330), (1560, yp), DP, kr2)
    joint(d, 1560, yp, DP, kr2)
    S.text(d, (1584, 386), "1.5 kΩ", 26, DP, "Bold", "lm", mono=True, k=kr2)
    write(d, (1520, 520), "pull-up", 28, S.DIM, kr2, "Regular", "mm")
    # voltage on D+ rises once plugged in
    v = 3.0 * A(t, dur, plug_t, plug_t + 0.08)
    if t / dur > plug_t: dots(d, (1560, 360), (1560, yp - 10), t, DP, 2, 0.9, 6)
    S.pill(d, (1040, yp - 34), f"{v:.1f} V", 28, DP, kw)
    S.pill(d, (1040, ym - 34), "0.0 V", 28, DM, kw)
    write(d, (980, 300), "3.3 V × 15 ÷ (15 + 1.5) ≈ 3.0 V", 30, S.TXT, A(t, dur, 0.5, 0.62), "Bold", "mm")
    write(d, (420, 380), "device attached!", 30, S.GOOD, A(t, dur, 0.42, 0.5), "Bold", "mm")
    # little graph of D+ against time
    kg = A(t, dur, 0.3, 0.38)
    gx, gy, gw, gh = 700, 650, 560, 150
    chalk(d, [(gx, gy), (gx, gy + gh), (gx + gw, gy + gh)], S.LINE, kg, 3)
    write(d, (gx + 12, gy + 4), "D+ voltage", 24, DP, kg, "Regular", "la")
    write(d, (gx + gw, gy + gh - 18), "time", 24, S.DIM, kg, "Regular", "rm")
    trace(d, gx, gy, gw, gh, lambda u: 0.05 if u < 0.4 else 0.05 + 0.75 * (1 - math.exp(-(u - 0.4) * 40)),
          A(t, dur, 0.3, 0.5), DP, 5)
    write(d, (gx + 0.4 * gw, gy + gh + 20), "plug in", 22, S.DIM, A(t, dur, 0.36, 0.42), "Regular", "mm")


def s_pulldown(d, t, dur):
    S.chrome(d, "STEP 1 · ATTACH", "Waiting, with two resistors", "The host ties D+ and D− to ground through 15 kilohm pull-downs. Empty port: both near 0 V.", t, dur)
    schem(d, t, dur, "empty")


def s_pullup(d, t, dur):
    S.chrome(d, "STEP 1 · ATTACH", "The device pulls a line up", "A full-speed device pulls D+ up through about 1.5 kilohms. D+ jumps to about 3 V: something is here.", t, dur)
    schem(d, t, dur, "full")


def mini_lines(d, x, y, which, k, t):
    """A tiny D+/D− sketch with a pull-up on one line (which = 'D+' or 'D-')."""
    yp, ym, rail = y + 90, y + 160, y
    chalk(d, [(x + 40, rail), (x + 420, rail)], VB, k, 4)
    write(d, (x + 30, rail), "3.3 V", 24, VB, k, "Bold", "rm")
    endp = x + 300 if which == "D-" else x + 440
    chalk(d, [(x + 40, yp), (endp, yp)], DP, k, 5)
    chalk(d, [(x + 40, ym), (x + 440, ym)], DM, k, 5)
    write(d, (x + 30, yp), "D+", 26, DP, k, "Bold", "rm")
    write(d, (x + 30, ym), "D−", 26, DM, k, "Bold", "rm")
    if which == "D+":
        resistor(d, (x + 240, rail), (x + 240, yp), DP, k); joint(d, x + 240, yp, DP, k)
        dots(d, (x + 240, rail + 10), (x + 240, yp - 8), t, DP, 2, 0.8, 5, k)
    else:
        resistor(d, (x + 380, rail), (x + 380, ym), DM, k); joint(d, x + 380, ym, DM, k)
        dots(d, (x + 380, rail + 10), (x + 380, ym - 8), t, DM, 2, 0.8, 5, k)


def s_speed(d, t, dur):
    S.chrome(d, "STEP 1 · ATTACH", "Which line? That's the speed", "Low speed pulls up D−. Full speed pulls up D+. High speed starts as full speed, then proves it can go faster.", t, dur)
    cards = [("LOW SPEED", "1.5 Mbit/s", "D-", "pulls up D−", DM), ("FULL SPEED", "12 Mbit/s", "D+", "pulls up D+", DP),
             ("HIGH SPEED", "480 Mbit/s", "D+", "starts as full speed", S.GOOD)]
    for i, (nm, sp, wh, note, c) in enumerate(cards):
        kk = A(t, dur, 0.06 + i * 0.2, 0.18 + i * 0.2)
        x = 120 + i * 570
        sketch_box(d, (x, 260, x + 530, 810), c, kk)
        write(d, (x + 265, 310), nm, 40, c, (kk - 0.2) / 0.8, "Bold", "mm")
        write(d, (x + 265, 365), sp, 34, S.TXT, (kk - 0.4) / 0.6, "Bold", "mm")
        mini_lines(d, x + 70, 440, wh, kk, t)
        write(d, (x + 265, 690), note, 32, S.TXT, (kk - 0.6) / 0.4, "Bold", "mm")
        if i == 2:
            write(d, (x + 265, 745), "then 'chirps' (step 2)", 28, S.DIM, (kk - 0.7) / 0.3, "Regular", "mm")
        if i == 0:
            write(d, (x + 265, 745), "e.g. some simple mice", 28, S.DIM, (kk - 0.7) / 0.3, "Regular", "mm")
        if i == 1:
            write(d, (x + 265, 745), "many everyday devices", 28, S.DIM, (kk - 0.7) / 0.3, "Regular", "mm")


def s_hub(d, t, dur):
    S.chrome(d, "STEP 1 · ATTACH", "The hub passes on the news", "Every port belongs to a hub. The hub flags the change; the host, checking in, sees it, then lets things settle.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    node(d, (120, 290, 500, 450), "HOST", HOSTC, k, "computer")
    kh = A(t, dur, 0.06, 0.14)
    sketch_box(d, (760, 290, 1200, 450), S.LINE, kh)
    write(d, (980, 330), "HUB", 36, S.TXT, kh, "Bold", "mm")
    ports = []
    for i in range(4):
        x = 820 + i * 107
        d.rectangle([x - 30, 400, x + 30, 430], fill=S.fade(S.DIM, kh))
        S.text(d, (x, 380), str(i + 1), 24, S.DIM, "Bold", "mm", k=kh)
        ports.append(x)
    chalk(d, [(500, 370), (760, 370)], S.LINE, kh, 4)
    # device plugged into port 3
    kd = A(t, dur, 0.12, 0.2)
    chalk(d, [(ports[2], 432), (ports[2], 600)], DEVC, kd, 5)
    icon(d, "keyboard", ports[2], 660, 1.0, DEVC, kd)
    # the change flag on port 3, waving
    kf = A(t, dur, 0.2, 0.26)
    if kf > 0.01:
        fx, fy = ports[2] + 40, 470
        wv = 6 * math.sin(t * 6)
        chalk(d, [(fx, fy + 60), (fx, fy)], S.HILITE, kf, 4)
        d.polygon([(fx, fy), (fx + 60, fy + 12 + wv), (fx, fy + 28)], fill=S.fade(S.HILITE, kf))
        write(d, (fx + 72, fy + 14), "change!", 28, S.HILITE, kf, "Bold", "lm")
    # the host keeps asking; a reply comes back
    cyc = (t / 2.2) % 1.0
    if t / dur > 0.08:
        chalk_arrow(d, (510, 520), (750, 520), HOSTC, ease(clamp(cyc * 2)), 5)
        write(d, (630, 492), "any changes?", 28, HOSTC, A(t, dur, 0.08, 0.16), "Bold", "mm")
    kr = A(t, dur, 0.34, 0.44)
    msg(d, (750, 610), (510, 610), "port 3: new device", S.HILITE, kr, 28, dy=-28)
    # then wait for the plug to settle
    kw = A(t, dur, 0.5, 0.56)
    cx, cy = 1560, 460
    S.circle(d, (cx, cy), 90, None, S.LINE, 4, kw)
    if kw > 0.01:
        a = -math.pi / 2 + 2 * math.pi * clamp((t / dur - 0.5) / 0.3)
        S.line(d, [(cx, cy), (cx + 70 * math.cos(a), cy + 70 * math.sin(a))], S.HILITE, 5, kw)
    write(d, (cx, 600), "wait about", 32, S.TXT, A(t, dur, 0.56, 0.62), "Bold", "mm")
    write(d, (cx, 645), "100 ms to settle", 32, S.TXT, A(t, dur, 0.58, 0.66), "Bold", "mm")
    write(d, (960, 800), "even the computer's own ports sit on a built-in 'root' hub", 30, S.DIM, A(t, dur, 0.68, 0.8), "Regular", "mm")


# ======================================================================= chapter 2: reset
def s_reset(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "Reset: both lines low", "The host drives D+ and D− low together for at least 10 ms. That's 'SE0': it means start fresh.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    x0, w = 300, 1400
    a0, a1 = 0.25, 0.72
    f_dp = lambda u: 0.0 if a0 <= u < a1 else 1.0
    f_dm = lambda u: 0.0
    rev = A(t, dur, 0.06, 0.6)
    write(d, (270, 340), "D+", 40, DP, k, "Bold", "rm")
    write(d, (270, 540), "D−", 40, DM, k, "Bold", "rm")
    chalk(d, [(x0, 400), (x0 + w, 400)], mix(S.BG, S.LINE, 0.3), k, 2)
    chalk(d, [(x0, 600), (x0 + w, 600)], mix(S.BG, S.LINE, 0.3), k, 2)
    trace(d, x0, 290, w, 110, f_dp, rev, DP, 6)
    trace(d, x0, 490, w, 110, f_dm, rev, DM, 6)
    # SE0 window
    ks = A(t, dur, 0.4, 0.48)
    xa, xb = x0 + a0 * w, x0 + a1 * w
    for xx in (xa, xb):
        for yy in range(270, 640, 28):
            S.line(d, [(xx, yy), (xx, yy + 14)], S.HILITE, 3, ks)
    write(d, ((xa + xb) / 2, 470), "SE0: both low", 40, S.HILITE, A(t, dur, 0.44, 0.54), "Bold", "mm")
    kd = A(t, dur, 0.5, 0.6)
    chalk_arrow(d, ((xa + xb) / 2, 700), (xa + 6, 700), S.HILITE, kd, 4)
    chalk_arrow(d, ((xa + xb) / 2, 700), (xb - 6, 700), S.HILITE, kd, 4)
    write(d, ((xa + xb) / 2, 745), "at least 10 ms", 36, S.HILITE, A(t, dur, 0.56, 0.64), "Bold", "mm")
    write(d, (x0 + a0 * w / 2, 700), "idle", 30, S.DIM, A(t, dur, 0.2, 0.28), "Regular", "mm")
    write(d, (x0 + (a1 + 1) * w / 2, 700), "idle again", 30, S.DIM, A(t, dur, 0.6, 0.68), "Regular", "mm")
    write(d, (960, 810), "(full-speed device; not to scale)", 26, S.DIM, A(t, dur, 0.66, 0.74), "Regular", "mm")


def zigzag(d, a, b, n, amp, col, k, width=4):
    pts = []
    for i in range(n * 2 + 1):
        x, y = lerp(a, b, i / (n * 2))
        pts.append((x, y + (amp if i % 2 else -amp) * (0 if i in (0, n * 2) else 1)))
    chalk(d, pts, col, k, width)


def s_chirp(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "A quick chirp for high speed", "During reset, a high-speed device chirps. If the host chirps back, both switch to high speed.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    node(d, (120, 300, 480, 760), "HOST", HOSTC, k, "high-speed")
    node(d, (1440, 300, 1800, 760), "DEVICE", DEVC, k, "high-speed capable")
    kc = A(t, dur, 0.1, 0.26)
    zigzag(d, (1420, 400), (1420 - 900 * kc, 400), 3, 0, DEVC, 0)
    msg(d, (1420, 400), (500, 400), "device: chirp", DEVC, kc, 32, dy=-36)
    if kc > 0.05:
        x = 1420 - 900 * kc
        zigzag(d, (x + 100, 440), (x + 10, 440), 2, 12, DEVC, 1)
    kh = A(t, dur, 0.3, 0.5)
    msg(d, (500, 520), (1420, 520), "host: chirp, chirp, chirp...", HOSTC, kh, 32, dy=-36)
    if kh > 0.05:
        x = 500 + 900 * kh
        zigzag(d, (x - 180, 560), (x - 10, 560), 4, 12, HOSTC, 1)
    ku = A(t, dur, 0.55, 0.64)
    for cx in (300, 1620):
        S.pill(d, (cx, 700), "480 Mbit/s", 28, S.GOOD, ku)
    kn = A(t, dur, 0.66, 0.76)
    sketch_box(d, (620, 640, 1300, 790), S.DIM, kn, 14, 3)
    write(d, (960, 685), "no chirps back?", 32, S.TXT, (kn - 0.3) / 0.7, "Bold", "mm")
    write(d, (960, 740), "it simply stays at full speed", 30, S.DIM, (kn - 0.5) / 0.5, "Regular", "mm")


def s_addr0(d, t, dur):
    S.chrome(d, "STEP 2 · RESET", "Everyone starts at address 0", "After reset, a device answers at address 0. So the host sets up new devices one at a time.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    node(d, (120, 300, 440, 480), "HOST", HOSTC, k)
    chalk(d, [(440, 390), (1800, 390)], S.LINE, A(t, dur, 0.04, 0.16), 5)
    write(d, (1700, 360), "the bus", 26, S.DIM, k, "Regular", "mm")
    # the device being set up
    ka = A(t, dur, 0.12, 0.2)
    chalk(d, [(860, 390), (860, 540)], DEVC, ka, 4)
    sketch_box(d, (720, 540, 1000, 760), DEVC, ka)
    icon(d, "keyboard", 860, 690, 0.9, DEVC, ka)
    pulse = 1 + 0.06 * math.sin(t * 5)
    badge(d, (860, 595), "0", S.HILITE, ka, int(38 * pulse), 40)
    write(d, (860, 800), "new device", 28, DEVC, ka, "Bold", "mm")
    # others wait their turn
    for i, (x, kind) in enumerate(((1260, "drive"), (1560, "mouse"))):
        kw = A(t, dur, 0.26 + i * 0.08, 0.34 + i * 0.08)
        bob = 5 * math.sin(t * 2 + i)
        chalk(d, [(x, 390), (x, 540)], S.DIM, kw, 3)
        sketch_box(d, (x - 120, 540 + bob, x + 120, 720 + bob), S.DIM, kw, fill=S.BG)
        icon(d, kind, x, 630 + bob, 0.9, S.DIM, kw)
        write(d, (x, 770), "waits its turn", 28, S.DIM, kw, "Regular", "mm")
    km = A(t, dur, 0.18, 0.3)
    msg(d, (450, 450), (820, 520), "address 0?", HOSTC, km, 30, dy=-10)
    # why: two at address 0 would clash
    kx = A(t, dur, 0.55, 0.65)
    sketch_box(d, (130, 560, 600, 790), S.BAD, kx, 14, 3, fill=S.BG)
    write(d, (365, 600), "if two answered at 0...", 28, S.BAD, (kx - 0.3) / 0.7, "Bold", "mm")
    badge(d, (290, 690), "0", S.BAD, kx, 34, 34)
    badge(d, (440, 690), "0", S.BAD, kx, 34, 34)
    zigzag(d, (330, 690), (400, 690), 2, 14, S.BAD, A(t, dur, 0.64, 0.7))


# ======================================================================= chapter 3: who are you?
def mailbox(d, x, y, label, sub, col, k):
    sketch_box(d, (x, y, x + 200, y + 150), col, k, 12)
    chalk(d, [(x + 40, y + 40), (x + 160, y + 40)], col, k, 6)
    write(d, (x + 100, y + 88), label, 32, col, (k - 0.3) / 0.7, "Bold", "mm")
    write(d, (x + 100, y + 125), sub, 24, S.DIM, (k - 0.5) / 0.5, "Regular", "mm")


def s_ep0(d, t, dur):
    S.chrome(d, "STEP 3 · WHO ARE YOU?", "Endpoint zero: the control pipe", "Endpoints are like numbered mailboxes. Endpoint 0 exists on every device and carries control transfers.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    sketch_box(d, (1000, 270, 1800, 640), DEVC, k)
    write(d, (1400, 310), "DEVICE", 34, DEVC, k, "Bold", "mm")
    mailbox(d, 1040, 370, "EP 0", "control", S.HILITE, A(t, dur, 0.08, 0.16))
    mailbox(d, 1300, 370, "EP 1 IN", "example", S.DIM, A(t, dur, 0.14, 0.22))
    mailbox(d, 1560, 370, "EP 2 OUT", "example", S.DIM, A(t, dur, 0.18, 0.26))
    node(d, (120, 340, 480, 560), "HOST", HOSTC, k)
    cyc = ease(clamp(((t / dur - 0.2) * dur / 2.4) % 1.0 * 1.6))
    if t / dur > 0.2:
        msg(d, (500, 420), (1030, 420), "request", HOSTC, cyc, 30)
        msg(d, (1030, 500), (500, 500), "reply", DEVC, clamp(cyc * 1.4 - 0.4), 30)
    write(d, (1400, 600), "every device has endpoint 0", 28, S.TXT, A(t, dur, 0.3, 0.38), "Bold", "mm")
    # a control transfer has three stages
    write(d, (120, 680), "a control transfer:", 32, S.TXT, A(t, dur, 0.45, 0.5), "Bold", "lm")
    stages = [("SETUP", "the question"), ("DATA", "the answer"), ("STATUS", "all done")]
    for i, (a, b) in enumerate(stages):
        kk = A(t, dur, 0.5 + i * 0.08, 0.58 + i * 0.08)
        x = 480 + i * 430
        sketch_box(d, (x, 640, x + 340, 790), S.HILITE if i == 0 else S.LINE, kk, 12)
        write(d, (x + 170, 690), a, 36, S.HILITE if i == 0 else S.TXT, (kk - 0.3) / 0.7, "Bold", "mm")
        write(d, (x + 170, 745), b, 28, S.DIM, (kk - 0.5) / 0.5, "Regular", "mm")
        if i < 2: chalk_arrow(d, (x + 350, 715), (x + 420, 715), S.DIM, kk, 4)


def s_setup(d, t, dur):
    S.chrome(d, "STEP 3 · WHO ARE YOU?", "The first question: 8 bytes", "Every control transfer starts with an 8-byte setup packet. This one asks for the device descriptor.", t, dur)
    k = A(t, dur, 0.0, 0.06)
    write(d, (260, 280), "setup packet, host to device (bytes in hex)", 30, S.DIM, k, "Regular", "lm")
    vals = ["80", "06", "00", "01", "00", "00", "12", "00"]
    x0, cw = 260, 180
    for i, v in enumerate(vals):
        kk = A(t, dur, 0.05 + i * 0.04, 0.1 + i * 0.04)
        x = x0 + i * cw
        sketch_box(d, (x, 330, x + cw - 14, 450), S.HILITE if i in (1,) else S.LINE, kk, 10, 3)
        write(d, (x + (cw - 14) / 2, 390), v, 52, S.TXT, (kk - 0.3) / 0.7, "Bold", "mm", mono=True)
        S.text(d, (x + (cw - 14) / 2, 470), str(i), 22, S.DIM, "Regular", "mm", k=kk)
    groups = [(0, 0, 545, "direction + type", "device to host, standard", S.ACCENT),
              (1, 1, 660, "request: 6", "GET_DESCRIPTOR", S.HILITE),
              (2, 3, 545, "which one", "type 1 = device", S.GOOD),
              (4, 5, 660, "index", "0 here", S.DIM),
              (6, 7, 545, "length", "18 bytes", S.EXTRA)]
    for j, (a, b, ly, l1, l2, c) in enumerate(groups):
        kk = A(t, dur, 0.4 + j * 0.07, 0.47 + j * 0.07)
        xa, xb = x0 + a * cw + 6, x0 + b * cw + cw - 20
        chalk(d, [(xa, 492), (xa, 504), (xb, 504), (xb, 492)], c, kk, 4)
        xm = (xa + xb) / 2
        chalk(d, [(xm, 506), (xm, ly - 24)], c, kk, 3)
        write(d, (xm, ly), l1, 30, c, (kk - 0.3) / 0.7, "Bold", "mm")
        write(d, (xm, ly + 42), l2, 26, S.TXT, (kk - 0.5) / 0.5, "Regular", "mm")
    write(d, (960, 790), "two-byte values travel low byte first", 28, S.DIM, A(t, dur, 0.78, 0.84), "Regular", "mm")
    S.pill(d, (1640, 280), "example", 26, S.HILITE, A(t, dur, 0.1, 0.16))


DESC = [  # (name, value, meaning, bytes, colour)
    ("bLength", "18", "size of this descriptor", 1, S.DIM),
    ("bDescriptorType", "1", "1 = device", 1, S.DIM),
    ("bcdUSB", "2.00", "USB version it follows", 2, S.ACCENT),
    ("Class / Sub / Protocol", "00 00 00", "00 = see each interface", 3, S.EXTRA),
    ("bMaxPacketSize0", "64", "biggest packet on EP 0", 1, S.BLUE),
    ("idVendor", "0x1234", "who made it", 2, S.HILITE),
    ("idProduct", "0x5678", "which model", 2, S.HILITE),
    ("bcdDevice", "1.00", "the device's own version", 2, S.DIM),
    ("string indexes", "1  2  3", "maker, product, serial", 3, S.GOOD),
    ("bNumConfigurations", "1", "how many configurations", 1, S.BAD),
]


def s_desc(d, t, dur):
    S.chrome(d, "STEP 3 · WHO ARE YOU?", "The 18-byte device descriptor", "The reply: 18 bytes. USB version, class, packet size, vendor ID, product ID, and more.", t, dur)
    # byte ruler: the reply arriving, byte by byte
    x0, cw = 160, 1600 / 18
    n_in = int(18 * A(t, dur, 0.04, 0.3))
    i = 0
    for fi, (_, _, _, nb, c) in enumerate(DESC):
        for _ in range(nb):
            if i < n_in:
                x = x0 + i * cw
                d.rectangle([x + 3, 262, x + cw - 3, 302], fill=S.fade(c, 0.85))
            i += 1
    if n_in > 0:
        S.text(d, (x0 + 1600, 322), f"{n_in} / 18 bytes", 24, S.DIM, "Regular", "rm")
    # the fields, written row by row
    for j, (nm, v, mean, nb, c) in enumerate(DESC):
        kk = A(t, dur, 0.18 + j * 0.05, 0.24 + j * 0.05)
        col, row = j // 5, j % 5
        x, y = 160 + col * 830, 360 + row * 92
        d.rectangle([x, y + 6, x + 12, y + 70], fill=S.fade(c, kk))
        S.text(d, (x + 30, y + 24), nm, 26, S.ACCENT if c != S.HILITE else S.HILITE, "Bold", "lm", mono=True, k=kk)
        write(d, (x + 760, y + 24), v, 34, S.HILITE if c == S.HILITE else S.TXT, kk, "Bold", "rm", mono=True)
        write(d, (x + 30, y + 62), mean, 28, S.DIM, (kk - 0.3) / 0.7, "Regular", "lm")
    S.pill(d, (1700, 830), "example values", 24, S.HILITE, A(t, dur, 0.72, 0.78))


def s_vidpid(d, t, dur):
    S.chrome(d, "STEP 3 · WHO ARE YOU?", "Vendor ID + product ID", "Vendor ID: who made it. Product ID: which model. Together they name one exact kind of device.", t, dur)
    for i, (nm, v, l1, l2, x) in enumerate((("VENDOR ID", "0x1234", "who made it", "assigned to the company", 180),
                                           ("PRODUCT ID", "0x5678", "which model", "chosen by the company", 1080))):
        kk = A(t, dur, 0.05 + i * 0.18, 0.14 + i * 0.18)
        sketch_box(d, (x, 280, x + 660, 580), S.HILITE, kk)
        write(d, (x + 330, 330), nm, 40, S.HILITE, (kk - 0.2) / 0.8, "Bold", "mm")
        write(d, (x + 330, 425), v, 84, S.TXT, (kk - 0.3) / 0.7, "Bold", "mm", mono=True)
        write(d, (x + 330, 500), l1, 34, S.TXT, (kk - 0.5) / 0.5, "Bold", "mm")
        write(d, (x + 330, 545), l2, 28, S.DIM, (kk - 0.6) / 0.4, "Regular", "mm")
        S.text(d, (x + 330, 590 + 26), "16 bits", 24, S.DIM, "Regular", "mm", k=kk)
    write(d, (960, 430), "+", 90, S.TXT, A(t, dur, 0.32, 0.36), "Bold", "mm")
    kk = A(t, dur, 0.4, 0.5)
    chalk(d, [(510, 650), (510, 690), (1410, 690), (1410, 650)], S.HILITE, kk, 4)
    chalk_arrow(d, (960, 690), (960, 730), S.HILITE, kk, 4)
    write(d, (960, 770), "= one exact model", 46, S.HILITE, A(t, dur, 0.48, 0.58), "Bold", "mm")
    S.pill(d, (1660, 770), "example values", 24, S.DIM, A(t, dur, 0.5, 0.56))
    write(d, (230, 770), "some hosts read just", 26, S.DIM, A(t, dur, 0.65, 0.72), "Regular", "lm")
    write(d, (230, 805), "the first 8 bytes first", 26, S.DIM, A(t, dur, 0.68, 0.76), "Regular", "lm")


# ======================================================================= chapter 4: an address
def s_setaddr(d, t, dur):
    S.chrome(d, "STEP 4 · AN ADDRESS", "SET_ADDRESS: a number of its own", "The host sends SET_ADDRESS with a number from 1 to 127. Here, 5. Address 0 is free again.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    node(d, (120, 300, 480, 760), "HOST", HOSTC, k)
    sketch_box(d, (1440, 300, 1800, 760), DEVC, k)
    write(d, (1620, 350), "DEVICE", 34, DEVC, k, "Bold", "mm")
    icon(d, "keyboard", 1620, 450, 1.1, DEVC, k)
    km = A(t, dur, 0.1, 0.3)
    msg(d, (500, 430), (1420, 430), "SET_ADDRESS (5)", HOSTC, km, 34, dy=-36)
    kr = A(t, dur, 0.34, 0.46)
    msg(d, (1420, 540), (500, 540), "OK", DEVC, kr, 34, dy=-36)
    # the badge: 0 rubbed out, 5 written in
    sw = 0.5
    if t / dur < sw + 0.05:
        badge(d, (1620, 640), "0", S.HILITE, k, 56, 56)
    else:
        S.circle(d, (1620, 640), 56, S.PANEL, S.GOOD, 4)
        write(d, (1620, 640), "5", 56, S.GOOD, A(t, dur, sw + 0.05, sw + 0.1), "Bold", "mm", mono=True)
    ke = A(t, dur, sw - 0.04, sw + 0.05)
    if 0.01 < ke < 1:  # the duster rubbing out the 0
        ex = 1560 + 120 * ((ke * 4) % 1.0)
        d.rounded_rectangle([ex - 30, 600, ex + 30, 680], 8, fill=S.fade(S.DIM, 0.6))
    kf = A(t, dur, 0.62, 0.7)
    write(d, (960, 660), "address 0 is free again", 36, S.HILITE, kf, "Bold", "mm")
    write(d, (960, 710), "for the next newcomer", 30, S.DIM, A(t, dur, 0.66, 0.74), "Regular", "mm")
    S.pill(d, (960, 790), "5 is just an example", 24, S.DIM, A(t, dur, 0.72, 0.78))


def s_bus(d, t, dur):
    S.chrome(d, "STEP 4 · AN ADDRESS", "Why 1 to 127?", "The address field is 7 bits, and 0 is kept for newcomers. Up to 127 devices per host controller, hubs included.", t, dur)
    nodes = {"host": (560, 300, "HOST", HOSTC), "hub1": (560, 440, "hub · 1", S.LINE), "kbd": (250, 580, "keyboard · 2", S.LINE),
             "hub3": (560, 580, "hub · 3", S.LINE), "new": (870, 580, "new device · 5", S.GOOD), "drv": (560, 720, "drive · 4", S.LINE)}
    edges = [("host", "hub1"), ("hub1", "kbd"), ("hub1", "hub3"), ("hub1", "new"), ("hub3", "drv")]
    order = ["host", "hub1", "kbd", "hub3", "drv", "new"]
    for i, nm in enumerate(order):
        x, y, lab, c = nodes[nm]
        kk = A(t, dur, 0.04 + i * 0.06, 0.1 + i * 0.06)
        for a, b in edges:
            if b == nm:
                xa, ya = nodes[a][:2]
                chalk(d, [(xa, ya + 36), (xa, (ya + y) / 2), (x, (ya + y) / 2), (x, y - 36)], S.DIM, kk, 4)
        sketch_box(d, (x - 135, y - 36, x + 135, y + 36), c, kk, 12, 3)
        write(d, (x, y), lab, 28, c if c != S.LINE else S.TXT, (kk - 0.3) / 0.7, "Bold", "mm")
    # the 7-bit field
    x0 = 1140
    write(d, (x0, 300), "address field: 7 bits", 32, S.TXT, A(t, dur, 0.4, 0.46), "Bold", "lm")
    for r, (bits, lab, c) in enumerate((("0000101", "= 5", S.GOOD), ("1111111", "= 127", S.HILITE), ("0000000", "= 0 (newcomers)", S.DIM))):
        kk = A(t, dur, 0.46 + r * 0.1, 0.54 + r * 0.1)
        y = 360 + r * 140
        for i, b in enumerate(bits):
            x = x0 + i * 66
            sketch_box(d, (x, y, x + 58, y + 70), c, kk, 8, 3)
            S.text(d, (x + 29, y + 35), b, 36, S.TXT, "Bold", "mm", mono=True, k=kk)
        write(d, (x0 + 7 * 66 + 14, y + 35), lab, 30, c, (kk - 0.3) / 0.7, "Bold", "lm")
    write(d, (1180, 800), "in practice, power and bandwidth run out first", 28, S.DIM, A(t, dur, 0.76, 0.84), "Regular", "lm")


# ======================================================================= chapter 5: configuration
def s_cfgtree(d, t, dur):
    S.chrome(d, "STEP 5 · CONFIGURATION", "One request, a whole bundle", "GET_DESCRIPTOR(configuration) returns a bundle: the configuration, its interfaces, and their endpoints.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    write(d, (960, 270), "host asks: GET_DESCRIPTOR (configuration), at address 5", 30, HOSTC, k, "Bold", "mm")
    tree = [("cfg", 960, 360, "configuration 1", S.HILITE, None), ("i0", 560, 500, "interface 0", S.EXTRA, "cfg"),
            ("i1", 1360, 500, "interface 1", S.EXTRA, "cfg"), ("e1", 560, 640, "endpoint 1 IN", S.ACCENT, "i0"),
            ("e2", 1220, 640, "endpoint 2 IN", S.ACCENT, "i1"), ("e3", 1500, 640, "endpoint 3 OUT", S.ACCENT, "i1")]
    pos = {}
    for i, (nm, x, y, lab, c, par) in enumerate(tree):
        kk = A(t, dur, 0.08 + i * 0.07, 0.15 + i * 0.07)
        pos[nm] = (x, y)
        if par:
            px, py = pos[par]
            chalk(d, [(px, py + 34), (px, (py + y) / 2), (x, (py + y) / 2), (x, y - 34)], S.DIM, kk, 4)
        w = 150 if nm in ("e2", "e3") else 180
        sketch_box(d, (x - w + 10, y - 34, x + w - 10, y + 34), c, kk, 12, 3)
        write(d, (x, y), lab, 28 if w == 150 else 32, c, (kk - 0.3) / 0.7, "Bold", "mm")
    # the bundle, back-to-back bytes
    segs = [("config", 9, S.HILITE), ("interface", 9, S.EXTRA), ("endpoint", 7, S.ACCENT), ("interface", 9, S.EXTRA),
            ("endpoint", 7, S.ACCENT), ("endpoint", 7, S.ACCENT)]
    kb = A(t, dur, 0.55, 0.72)
    total = sum(s[1] for s in segs)
    x, w = 380, 1400
    write(d, (360, 765), "sent as one bundle:", 28, S.TXT, A(t, dur, 0.52, 0.58), "Bold", "rm")
    for j, (lab, n, c) in enumerate(segs):
        sw = w * n / total
        kk = clamp(kb * len(segs) - j)
        if kk > 0.01:
            d.rectangle([x + 2, 740, x + sw - 2, 790], fill=S.fade(mix(S.BG, c, 0.45), kk))
            S.text(d, (x + sw / 2, 765), lab, 22, S.TXT, "Bold", "mm", k=kk)
        x += sw
    S.pill(d, (1760, 330), "example", 24, S.DIM, A(t, dur, 0.3, 0.36))
    write(d, (1660, 815), "(simplified: some devices add extra class descriptors)", 22, S.DIM, A(t, dur, 0.74, 0.8), "Regular", "rm")


def s_class(d, t, dur):
    S.chrome(d, "STEP 5 · CONFIGURATION", "What kind of thing is it?", "Class codes, often in the interface descriptor: hex 03 HID, 08 mass storage, 01 audio, 09 hub.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    write(d, (960, 280), "device descriptor class 00 often means: look in each interface", 30, S.DIM, k, "Regular", "mm")
    rows = [("03", "HID: human interface device", "keyboards, mice, game controllers", "keyboard", S.ACCENT),
            ("08", "Mass storage", "flash drives, card readers", "drive", S.HILITE),
            ("01", "Audio", "headsets, microphones", "headset", S.EXTRA),
            ("09", "Hub", "more ports", "hub", S.GOOD)]
    for i, (code, nm, ex, ic, c) in enumerate(rows):
        kk = A(t, dur, 0.08 + i * 0.12, 0.18 + i * 0.12)
        y = 330 + i * 120
        sketch_box(d, (160, y, 1760, y + 100), c, kk, 14, 3)
        S.text(d, (200, y + 50), "hex", 26, S.DIM, "Regular", "lm", k=kk)
        write(d, (262, y + 50), code, 50, c, (kk - 0.2) / 0.8, "Bold", "lm", mono=True)
        write(d, (400, y + 50), nm, 38, S.TXT, (kk - 0.3) / 0.7, "Bold", "lm")
        write(d, (1020, y + 50), ex, 30, S.DIM, (kk - 0.5) / 0.5, "Regular", "lm")
        bob = 4 * math.sin(t * 3 + i)
        icon(d, ic, 1650, y + 50 + bob, 0.55, c, kk)


def s_composite(d, t, dur):
    S.chrome(d, "STEP 5 · CONFIGURATION", "One device, several jobs", "A headset might have audio interfaces for sound and a HID interface for its buttons. Each gets its own driver.", t, dur)
    k = A(t, dur, 0.0, 0.1)
    sketch_box(d, (130, 330, 600, 730), DEVC, k)
    icon(d, "headset", 365, 500, 1.6, DEVC, k)
    write(d, (365, 680), "headset (example)", 30, DEVC, (k - 0.4) / 0.6, "Bold", "mm")
    for i, (y, nm, code, drv, c) in enumerate(((330, "audio interfaces", "class 01", "audio driver", S.EXTRA),
                                               (590, "HID interface", "class 03", "HID driver", S.ACCENT))):
        kk = A(t, dur, 0.15 + i * 0.2, 0.25 + i * 0.2)
        chalk_arrow(d, (610, 530), (740, y + 70), c, kk, 4)
        node(d, (760, y, 1200, y + 140), nm, c, kk, code, 36)
        kd = A(t, dur, 0.5 + i * 0.1, 0.6 + i * 0.1)
        chalk_arrow(d, (1210, y + 70), (1360, y + 70), c, kd, 4)
        node(d, (1380, y, 1780, y + 140), drv, c, kd, None, 36)
    # sound waves and a button press, so you can see both jobs happening
    if t / dur > 0.3:
        for j in range(3):
            r = 30 + ((t * 40 + j * 25) % 75)
            ang = [(-0.5 + i / 10) for i in range(11)]
            pts = [(445 + r * math.cos(a), 520 + r * math.sin(a)) for a in ang]
            S.line(d, pts, S.EXTRA, 3, 0.6 * (1 - (r - 30) / 75))
    if t / dur > 0.5 and (t * 1.3) % 1.0 < 0.3:
        d.ellipse([265, 500, 285, 520], fill=S.ACCENT)
    write(d, (960, 800), "the host treats each interface separately", 30, S.DIM, A(t, dur, 0.72, 0.8), "Regular", "mm")


def s_endpoints(d, t, dur):
    S.chrome(d, "STEP 5 · CONFIGURATION", "Endpoints: the actual pipes", "Each endpoint: number, direction, transfer type, packet size. IN means towards the host.", t, dur)
    types = [("control", "requests and replies", S.HILITE), ("bulk", "big data, when there's time", S.ACCENT),
             ("interrupt", "small, regular check-ins", S.GOOD), ("isochronous", "steady streams, like audio", S.EXTRA)]
    write(d, (140, 280), "four transfer types", 32, S.TXT, A(t, dur, 0.0, 0.06), "Bold", "lm")
    for i, (a, b, c) in enumerate(types):
        kk = A(t, dur, 0.05 + i * 0.07, 0.12 + i * 0.07)
        y = 340 + i * 115
        sketch_box(d, (140, y, 880, y + 95), c, kk, 12, 3)
        write(d, (170, y + 30), a, 34, c, (kk - 0.2) / 0.8, "Bold", "lm")
        write(d, (170, y + 70), b, 28, S.TXT, (kk - 0.4) / 0.6, "Regular", "lm")
    k = A(t, dur, 0.35, 0.42)
    sketch_box(d, (980, 280, 1080, 800), HOSTC, k, 14)
    for j, ch in enumerate("HOST"):
        S.text(d, (1030, 420 + j * 60), ch, 40, HOSTC, "Bold", "mm", k=k)
    kd = A(t, dur, 0.42, 0.5)
    sketch_box(d, (1440, 290, 1790, 470), DEVC, kd, 14)
    icon(d, "keyboard", 1615, 360, 0.9, DEVC, kd)
    write(d, (1615, 440), "keyboard", 28, DEVC, kd, "Bold", "mm")
    chalk_arrow(d, (1430, 380), (1090, 380), S.GOOD, kd, 4)
    write(d, (1260, 345), "EP1 IN · interrupt", 26, S.GOOD, kd, "Bold", "mm")
    write(d, (1260, 420), "checked every few ms", 24, S.DIM, kd, "Regular", "mm")
    dots(d, (1420, 380), (1100, 380), t, S.GOOD, 2, 0.4, 6, kd)
    kf = A(t, dur, 0.55, 0.63)
    sketch_box(d, (1440, 560, 1790, 780), DEVC, kf, 14)
    icon(d, "drive", 1615, 640, 1.0, DEVC, kf)
    write(d, (1615, 735), "flash drive", 28, DEVC, kf, "Bold", "mm")
    chalk_arrow(d, (1430, 610), (1090, 610), S.ACCENT, kf, 4)
    chalk_arrow(d, (1090, 720), (1430, 720), S.ACCENT, kf, 4)
    write(d, (1260, 575), "EP1 IN · bulk", 26, S.ACCENT, kf, "Bold", "mm")
    write(d, (1260, 685), "EP2 OUT · bulk", 26, S.ACCENT, kf, "Bold", "mm")
    dots(d, (1420, 610), (1100, 610), t, S.ACCENT, 3, 0.7, 6, kf)
    dots(d, (1100, 720), (1420, 720), t, S.ACCENT, 3, 0.7, 6, kf)
    S.pill(d, (1615, 830), "examples", 24, S.DIM, A(t, dur, 0.66, 0.72))


def s_strings(d, t, dur):
    S.chrome(d, "STEP 5 · CONFIGURATION", "Names are optional extras", "Readable names come from optional string descriptors. The host asks for string 2, and gets text back.", t, dur)
    cells = [("iManufacturer", "1"), ("iProduct", "2"), ("iSerialNumber", "3")]
    write(d, (960, 270), "from the device descriptor:", 28, S.DIM, A(t, dur, 0.0, 0.06), "Regular", "mm")
    for i, (nm, v) in enumerate(cells):
        kk = A(t, dur, 0.04 + i * 0.05, 0.1 + i * 0.05)
        x = 320 + i * 440
        hot = i == 1
        sketch_box(d, (x, 300, x + 400, 390), S.HILITE if hot else S.LINE, kk, 12, 3)
        S.text(d, (x + 30, 345), nm, 28, S.ACCENT, "Bold", "lm", mono=True, k=kk)
        S.text(d, (x + 370, 345), v, 40, S.HILITE if hot else S.TXT, "Bold", "rm", mono=True, k=kk)
    km = A(t, dur, 0.22, 0.32)
    chalk_arrow(d, (960, 400), (960, 470), S.HILITE, km, 4)
    S.pill(d, (960, 510), "GET_DESCRIPTOR (string 2)", 30, HOSTC, km)
    kr = A(t, dur, 0.36, 0.44)
    chalk_arrow(d, (960, 550), (960, 600), DEVC, kr, 4)
    sketch_box(d, (560, 610, 1360, 740), DEVC, kr, 16)
    write(d, (960, 665), "\"Example Keyboard\"", 56, S.TXT, A(t, dur, 0.42, 0.6), "Bold", "mm")
    write(d, (960, 715), "text, in Unicode", 26, S.DIM, A(t, dur, 0.55, 0.62), "Regular", "mm")
    write(d, (200, 640), "string 0 =", 28, S.DIM, A(t, dur, 0.62, 0.7), "Regular", "lm")
    write(d, (200, 680), "list of languages", 28, S.DIM, A(t, dur, 0.64, 0.72), "Regular", "lm")
    write(d, (1720, 640), "no strings?", 28, S.DIM, A(t, dur, 0.7, 0.76), "Regular", "rm")
    write(d, (1720, 680), "a generic name", 28, S.DIM, A(t, dur, 0.72, 0.8), "Regular", "rm")
    S.pill(d, (960, 800), "example name", 24, S.DIM, A(t, dur, 0.6, 0.66))


def s_power(d, t, dur):
    S.chrome(d, "STEP 5 · CONFIGURATION", "How much current may it take?", "USB 2.0: up to 100 mA before it's configured, then up to what it asked for, at most 500 mA.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    x0, x1, y0, y1 = 260, 1660, 470, 540
    sc = (x1 - x0) / 500
    sketch_box(d, (x0 - 6, y0 - 6, x1 + 6, y1 + 6), S.LINE, k, 10, 3, fill=S.BG)
    for ma in range(0, 501, 100):
        x = x0 + ma * sc
        S.line(d, [(x, y1 + 8), (x, y1 + 26)], S.LINE, 3, k)
        S.text(d, (x, y1 + 52), f"{ma} mA", 26, S.DIM, "Bold", "mm", mono=True, k=k)
    u = t / dur
    lvl = 100 * prog(u, 0.1, 0.22) + 400 * prog(u, 0.6, 0.72)
    if lvl > 1:
        c = S.HILITE if lvl <= 101 else S.GOOD
        d.rectangle([x0, y0, x0 + lvl * sc, y1], fill=S.fade(c, 0.85))
    ka = A(t, dur, 0.2, 0.3)
    xa = x0 + 100 * sc
    chalk(d, [(xa, y0 - 10), (xa, 400)], S.HILITE, ka, 3)
    write(d, (xa - 20, 340), "before configuration:", 30, S.HILITE, ka, "Bold", "lm")
    write(d, (xa - 20, 380), "up to 100 mA (one 'unit load')", 28, S.TXT, A(t, dur, 0.26, 0.36), "Regular", "lm")
    if 0.48 < u < 0.62:
        S.pill(d, (1100, 640), "SET_CONFIGURATION", 30, HOSTC, A(t, dur, 0.48, 0.52))
    kb = A(t, dur, 0.68, 0.76)
    write(d, (x1, 640), "once configured: what it asked for,", 30, S.GOOD, kb, "Bold", "rm")
    write(d, (x1, 682), "up to 500 mA", 30, S.GOOD, A(t, dur, 0.72, 0.8), "Bold", "rm")
    # current flowing along VBUS: more dots once configured
    write(d, (240, 770), "V bus", 30, VB, k, "Bold", "rm")
    chalk(d, [(260, 770), (1660, 770)], VB, k, 5)
    n = 2 if lvl < 150 else 7
    dots(d, (260, 770), (1660, 770), t, VB, n, 0.25, 7, k)
    S.pill(d, (420, 640), "USB 2.0 figures", 24, S.DIM, A(t, dur, 0.1, 0.16))


# ======================================================================= chapter 6: driver
def s_match(d, t, dur):
    S.chrome(d, "STEP 6 · DRIVER", "Finding a driver", "The OS looks for a driver: exact vendor and product ID first, then the class. Most specific match wins.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    sketch_box(d, (120, 300, 640, 700), S.HILITE, k)
    write(d, (380, 345), "this device", 36, S.HILITE, k, "Bold", "mm")
    for i, ln in enumerate(["vendor  1234", "product 5678", "class   03", "sub 01  proto 01"]):
        S.text(d, (170, 420 + i * 62), ln, 32, S.TXT, "Bold", "lm", mono=True, k=A(t, dur, 0.04 + i * 0.04, 0.1 + i * 0.04))
    S.pill(d, (380, 760), "example values", 24, S.DIM, A(t, dur, 0.1, 0.16))
    kl = A(t, dur, 0.2, 0.28)
    chalk_arrow(d, (650, 500), (790, 500), S.DIM, kl, 5)
    sketch_box(d, (810, 270, 1800, 800), S.LINE, kl)
    write(d, (1305, 310), "drivers this computer knows (example)", 30, S.DIM, kl, "Regular", "mm")
    rows = [("1234 : 9ABC", "a maker's own driver", False), ("ABCD : 0001", "another maker's driver", False),
            ("class 08", "storage class driver", False), ("class 03", "HID class driver", True)]
    scan = A(t, dur, 0.3, 0.7) * 4
    for i, (key, nm, ok) in enumerate(rows):
        y = 370 + i * 105
        kk = A(t, dur, 0.24 + i * 0.03, 0.3 + i * 0.03)
        active = i <= scan < i + 1
        done = scan >= i + 0.6
        if active or (ok and done):
            d.rounded_rectangle([840, y, 1770, y + 86], 12, fill=S.fade(mix(S.BG, S.GOOD if ok and done else S.LINE, 0.25), 1))
        S.text(d, (870, y + 43), key, 32, S.ACCENT, "Bold", "lm", mono=True, k=kk)
        write(d, (1170, y + 43), nm, 32, S.TXT, kk, "Bold", "lm")
        if done:
            (tick if ok else cross)(d, (1720, y + 43), 18, S.GOOD if ok else S.BAD, clamp((scan - i - 0.6) * 3))


def s_classdrv(d, t, dur):
    S.chrome(d, "STEP 6 · DRIVER", "Why so many things 'just work'", "The OS ships class drivers. One HID driver, many keyboards and mice. Follow the class rules: no install.", t, dur)
    groups = [(500, "HID class driver", S.ACCENT, [("keyboard", 200, 340), ("mouse", 500, 320), ("pad", 800, 340)]),
              (1420, "storage class driver", S.HILITE, [("drive", 1120, 340), ("card", 1420, 330), ("disk", 1720, 340)])]
    for g, (cx, nm, c, devs) in enumerate(groups):
        kb = A(t, dur, 0.05 + g * 0.3, 0.14 + g * 0.3)
        node(d, (cx - 230, 560, cx + 230, 660), nm, c, kb, None, 36)
        for i, (kind, x, y) in enumerate(devs):
            kk = A(t, dur, 0.12 + g * 0.3 + i * 0.05, 0.2 + g * 0.3 + i * 0.05)
            bob = 4 * math.sin(t * 2.5 + i + g)
            icon(d, kind, x, y + bob, 1.0, S.TXT, kk)
            chalk(d, [(x, y + 60), (cx + (x - cx) * 0.4, 556)], c, kk, 3)
            dots(d, (x, y + 64), (cx + (x - cx) * 0.4, 552), t, c, 1, 0.5 + 0.1 * i, 5, kk)
        write(d, (cx, 700), "...and many more", 28, S.DIM, A(t, dur, 0.24 + g * 0.3, 0.3 + g * 0.3), "Regular", "mm")
    write(d, (960, 790), "follow the class rules, and no install is needed", 40, S.HILITE, A(t, dur, 0.68, 0.8), "Bold", "mm")


def s_setconfig(d, t, dur):
    S.chrome(d, "STEP 6 · DRIVER", "SET_CONFIGURATION: switched on", "SET_CONFIGURATION (1): the endpoints switch on. Attached, powered, default, address: now configured.", t, dur)
    k = A(t, dur, 0.0, 0.08)
    node(d, (120, 270, 480, 520), "HOST", HOSTC, k, "+ driver")
    sketch_box(d, (1440, 270, 1800, 520), DEVC, k)
    write(d, (1620, 310), "DEVICE · 5", 32, DEVC, k, "Bold", "mm")
    icon(d, "keyboard", 1620, 410, 1.0, DEVC, k)
    km = A(t, dur, 0.06, 0.22)
    msg(d, (500, 340), (1420, 340), "SET_CONFIGURATION (1)", HOSTC, km, 32, dy=-30)
    kr = A(t, dur, 0.24, 0.32)
    msg(d, (1420, 420), (500, 420), "OK", DEVC, kr, 30, dy=-26)
    # the device state ladder (the states named in the USB 2.0 spec)
    states = ["Attached", "Powered", "Default", "Address", "Configured"]
    x0, x1, y = 240, 1680, 680
    kl = A(t, dur, 0.02, 0.12)
    chalk(d, [(x0, y), (x1, y)], S.LINE, kl, 4)
    pos = 3 + A(t, dur, 0.34, 0.46)
    for i, s in enumerate(states):
        x = x0 + i * (x1 - x0) / 4
        lit = i <= pos + 0.01
        c = S.GOOD if (i == 4 and pos >= 3.99) else (S.HILITE if lit else S.DIM)
        S.circle(d, (x, y), 20, S.fade(c, 0.9) if lit else S.PANEL, c, 4, kl)
        write(d, (x, y - 50), s, 32, c, kl, "Bold", "mm")
    mx = x0 + pos * (x1 - x0) / 4
    if kl > 0.5: chalk(d, [(mx - 16, y + 46), (mx, y + 28), (mx + 16, y + 46)], S.HILITE, 1, 5)
    write(d, (960, 780), "device states, as the USB 2.0 spec names them", 26, S.DIM, A(t, dur, 0.4, 0.48), "Regular", "mm")
    # the driver starts work: a regular check-in
    if t / dur > 0.55:
        cyc = (t * 0.7) % 1.0
        x = 500 + 920 * (cyc * 2 if cyc < 0.5 else 2 - cyc * 2)
        d.ellipse([x - 9, 491, x + 9, 509], fill=S.HILITE)
        write(d, (960, 560), "driver at work: \"any keys pressed?\"", 30, S.HILITE, A(t, dur, 0.56, 0.64), "Bold", "mm")
    S.pill(d, (1620, 575), "ready!", 34, S.GOOD, A(t, dur, 0.48, 0.54))


def s_timeline(d, t, dur):
    S.chrome(d, "STEP 6 · DRIVER", "The whole conversation", "Attach, reset, descriptor, address, configuration, driver, SET_CONFIGURATION. Usually well under a second.", t, dur)
    hx, dx = 420, 1500
    k = A(t, dur, 0.0, 0.06)
    write(d, (hx, 270), "HOST", 34, HOSTC, k, "Bold", "mm")
    write(d, (dx, 270), "DEVICE", 34, DEVC, k, "Bold", "mm")
    chalk(d, [(hx, 295), (hx, 800)], HOSTC, k, 3)
    chalk(d, [(dx, 295), (dx, 800)], DEVC, k, 3)
    msgs = [(0, "attach: D+ pulled up (then wait ~100 ms)", DP), (1, "reset (at least 10 ms)", VB),
            (1, "GET_DESCRIPTOR (device), at address 0", HOSTC), (0, "device descriptor: 18 bytes", DEVC),
            (1, "SET_ADDRESS (5)", HOSTC), (1, "GET_DESCRIPTOR (configuration)", HOSTC),
            (0, "configuration + interfaces + endpoints", DEVC), (1, "SET_CONFIGURATION (1)", HOSTC)]
    for i, (to_dev, lab, c) in enumerate(msgs):
        kk = A(t, dur, 0.06 + i * 0.075, 0.13 + i * 0.075)
        y = 345 + i * 58
        a, b = ((hx + 10, y), (dx - 10, y)) if to_dev else ((dx - 10, y), (hx + 10, y))
        msg(d, a, b, lab, c, kk, 26, dy=-20)
    kd = A(t, dur, 0.68, 0.74)
    S.pill(d, (hx, 820), "driver loaded", 26, S.GOOD, kd)
    S.pill(d, (dx, 820), "ready to use", 26, S.GOOD, kd)
    write(d, (1680, 470), "time", 26, S.DIM, k, "Regular", "mm")
    chalk_arrow(d, (1680, 500), (1680, 700), S.DIM, k, 3)
    write(d, (230, 520), "(simplified;", 24, S.DIM, A(t, dur, 0.72, 0.78), "Regular", "mm")
    write(d, (230, 555), "strings and", 24, S.DIM, A(t, dur, 0.72, 0.78), "Regular", "mm")
    write(d, (230, 590), "retries omitted)", 24, S.DIM, A(t, dur, 0.72, 0.78), "Regular", "mm")


# ======================================================================= recap + end
def s_recap(d, t, dur):
    S.chrome(d, "RECAP", "From plug to ready", "Pull-up, reset to address 0, device descriptor, SET_ADDRESS, configuration, driver, SET_CONFIGURATION.", t, dur)
    pts = [(300, 380), (960, 380), (1620, 380), (1620, 660), (960, 660), (300, 660)]
    items = [("Attach", "a pull-up says hello", DP), ("Reset", "SE0, then address 0", VB), ("Who are you?", "device descriptor", HOSTC),
             ("Address", "1 to 127", DEVC), ("Configure", "interfaces, endpoints", DM), ("Driver", "then SET_CONFIGURATION", S.BLUE)]
    path = [pts[0], pts[1], pts[2], (1700, 380), (1700, 660), pts[3], pts[4], pts[5]]
    chalk(d, path, S.DIM, A(t, dur, 0.04, 0.7), 4)
    for i, (p, (a, b, c)) in enumerate(zip(pts, items)):
        kk = A(t, dur, 0.05 + i * 0.11, 0.13 + i * 0.11)
        S.circle(d, p, 40, S.PANEL, c, 5, kk)
        S.text(d, p, str(i + 1), 40, c, "Bold", "mm", k=kk)
        write(d, (p[0], p[1] + 75), a, 40, c, (kk - 0.2) / 0.8, "Bold", "mm")
        write(d, (p[0], p[1] + 120), b, 30, S.DIM, (kk - 0.4) / 0.6, "Regular", "mm")
    # a little "ready" packet travels the path
    if t / dur > 0.72:
        u = ((t / dur - 0.72) * 2.5) % 1.0
        seg = grow(path, u)
        x, y = seg[-1]
        d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=S.HILITE)


def s_end(d, t, dur):
    k = A(t, dur, 0.02, 0.14)
    write(d, (W // 2, 300), "NEXT EPISODE", 40, S.ACCENT, k, "Bold", "mm")
    write(d, (W // 2, 420), "UART vs SPI vs I²C", 110, S.TXT, A(t, dur, 0.08, 0.3), "Bold", "mm")
    write(d, (W // 2, 540), "how do chips actually talk to each other?", 50, S.HILITE, A(t, dur, 0.26, 0.5), "Bold", "mm")
    kc = A(t, dur, 0.4, 0.55)
    icon(d, "chip", 700, 700, 1.0, S.TXT, kc)
    icon(d, "chip", 1220, 700, 1.0, S.TXT, kc)
    for i, c in enumerate((DP, DM, S.ACCENT)):
        y = 670 + i * 30
        chalk(d, [(780, y), (1140, y)], c, A(t, dur, 0.5 + i * 0.05, 0.6 + i * 0.05), 4)
        dots(d, (780, y), (1140, y), t + i * 0.3, c, 2, 0.6, 5, A(t, dur, 0.6, 0.65))
    write(d, (W // 2, 860), "Subscribe so you don't miss it", 40, S.DIM, A(t, dur, 0.5, 0.65), "Regular", "mm")


# ======================================================================= scenes + narration
SCENES = [
    ("01_hook", s_hook, 14), ("02_cover", s_cover, 16),
    ("03_wires", s_wires, 16), ("04_pulldown", s_pulldown, 16), ("05_pullup", s_pullup, 16), ("06_speed", s_speed, 16), ("07_hub", s_hub, 16),
    ("08_reset", s_reset, 16), ("09_chirp", s_chirp, 16), ("10_addr0", s_addr0, 16),
    ("11_ep0", s_ep0, 16), ("12_setup", s_setup, 16), ("13_desc", s_desc, 16), ("14_vidpid", s_vidpid, 16),
    ("15_setaddr", s_setaddr, 16), ("16_bus", s_bus, 16),
    ("17_cfgtree", s_cfgtree, 16), ("18_class", s_class, 16), ("19_composite", s_composite, 16), ("20_endpoints", s_endpoints, 16),
    ("21_strings", s_strings, 16), ("22_power", s_power, 16),
    ("23_match", s_match, 16), ("24_classdrv", s_classdrv, 16), ("25_setconfig", s_setconfig, 16), ("26_timeline", s_timeline, 16),
    ("27_recap", s_recap, 16), ("28_end", s_end, 8),
]

NARRATION = {
 "01_hook": "Plug a keyboard you've never used into a computer, and within a second or so, it's typing. Yet when the plug went in, the computer had no idea what it was. Not who made it. Not even that it was a keyboard. So how does it find out? It asks. Let's follow that conversation.",
 "02_cover": "Right. Here's the plan. We'll follow one plug-in, from start to finish. First, how the computer notices anything is there. Then a reset. Then the big question: who are you? Then the device gets an address, describes what's inside, and finally, the computer picks a driver.",
 "03_wires": "Step one: attach. Let's draw the connection. Classic U S B two point oh uses four wires. V bus carries five volts of power, and there's a ground. Between them sit two data wires, D plus and D minus. They work as a pair: the data is the difference between them. Newer connectors keep this pair too.",
 "04_pulldown": "Now, inside the host, or inside the hub that the port belongs to, each data line is tied to ground through a fifteen kilo-ohm resistor. These are called pull-downs. With nothing plugged in, they hold both D plus and D minus at about zero volts. The host reads that as: empty port.",
 "05_pullup": "Now, here's the clever bit. A full-speed device has a resistor of its own: about one point five kilo-ohms, from D plus up to roughly three point three volts. Plug it in, and this small resistor easily beats the big one. D plus jumps to around three volts, and the host knows something has arrived.",
 "06_speed": "Which line gets pulled up also tells the host the speed. A low-speed device, at one point five megabits per second, pulls up D minus instead. A full-speed device, at twelve megabits, pulls up D plus. And a high-speed device starts out looking like full speed, then proves it can go faster.",
 "07_hub": "Every port belongs to a hub, even the ones built into your computer. The hub notices the change on its port, and flags it. The host keeps checking in with its hubs, sees the flag, and then waits about a tenth of a second, so the plug can settle.",
 "08_reset": "Step two: reset. The host now resets that port. It drives both D plus and D minus low, at the same time, for at least ten milliseconds. Engineers call this state S E zero, short for single-ended zero. To the device, it means: forget whatever you were doing, and start fresh.",
 "09_chirp": "During that reset, a high-speed device gets a word in. It sends a short signal called a chirp. If the host is high-speed too, it chirps back, rapidly. Both sides then switch up to four hundred and eighty megabits per second. If no chirps come back, the device simply stays at full speed.",
 "10_addr0": "After the reset, the device listens on one special address: zero. Every newly reset device uses address zero. So if two were reset together, both would answer at once, and their replies would collide. That's why the host sets up new devices one at a time.",
 "11_ep0": "Step three: who are you? Inside every U S B device are endpoints. Think of them as numbered mailboxes. Endpoint zero is special. Every device has one, and it carries control transfers: short requests from the host, each with a reply. A control transfer has a setup stage, an optional data stage, and a status stage.",
 "12_setup": "Every control transfer begins with an eight-byte setup packet. Let's write out the host's first question. Hex, eight zero means: device to host, a standard request. Hex, zero six means get descriptor. The next two bytes say which one: type one, the device descriptor. The last two say how many bytes to send.",
 "13_desc": "The device replies with its device descriptor: eighteen bytes. It gives the U S B version it follows, its class, subclass and protocol, and the biggest packet endpoint zero can handle. Then a vendor I D, a product I D, a device version, pointers to its names, and how many configurations it has.",
 "14_vidpid": "The two most important fields are the I Ds. The vendor I D is a sixteen-bit number assigned to the company that made the device. The product I D is chosen by that company, for each model. Together, they point to one exact kind of device. Some hosts read just the first eight bytes at this stage.",
 "15_setaddr": "Step four: an address of its own. The host sends another control request, set address, with a number from one to one hundred and twenty seven. Here, we'll say five. The device confirms, and from then on, it answers only to five. Address zero is free again, for the next newcomer.",
 "16_bus": "Why one to one hundred and twenty seven? The address field is seven bits long, and zero is kept for newcomers. So one host controller can address up to a hundred and twenty seven devices, and hubs count too. In practice, power and bandwidth usually run out long before that.",
 "17_cfgtree": "Step five: configuration. Using the new address, the host asks for the configuration descriptor. Back comes a whole bundle: the configuration itself, then one or more interfaces, and under each interface, its endpoints. Often the host asks twice: once to learn the total length, then again for everything.",
 "18_class": "Each interface usually carries a class code, saying what kind of thing it is. Hex, zero three is H I D, human interface devices, like keyboards and mice. Hex, zero eight is mass storage. Hex, zero one is audio, and hex, zero nine is a hub. Often, the class lives in the interface descriptor.",
 "19_composite": "And because the class lives in each interface, one device can do several jobs at once. A headset, for example, might have audio interfaces for the sound, and a separate H I D interface for its volume buttons. The host treats each interface separately, and each can get its own driver.",
 "20_endpoints": "Each endpoint descriptor describes one pipe. Its number and direction: in means towards the host. Its transfer type: control, bulk, interrupt, or isochronous. And its biggest packet. A keyboard might have one interrupt endpoint, checked every few milliseconds. A flash drive uses bulk endpoints, in and out.",
 "21_strings": "So where does the friendly name come from? Optional string descriptors. The device descriptor holds index numbers pointing to them: maker, product, and serial number. The host asks for string two, say, and gets readable text back, in Unicode. No strings at all? The system can fall back to a generic name.",
 "22_power": "The configuration also says how much power the device wants. Until it's configured, a U S B two point oh device should take no more than one unit load, which is a hundred milliamps. Once the host accepts a configuration, the device may draw what it asked for, up to five hundred milliamps.",
 "23_match": "Step six: the driver. The operating system now has everything it needs, so it looks for a match. Is there a driver for this exact vendor and product I D? If not, is there one for this class, subclass and protocol? Generally, the most specific match wins. Here, the class match does the job.",
 "24_classdrv": "And here's why so many things just work. Operating systems ship with class drivers, written once for a whole class. One H I D driver handles almost any keyboard or mouse. One storage driver handles almost any flash drive. If the maker follows the class rules, there's nothing extra to install.",
 "25_setconfig": "Finally, the host sends set configuration, choosing configuration one. The device switches its endpoints on, and may draw its full current. In the spec's own words, it has gone from attached, to powered, to default, to address, and now, configured. The driver gets to work.",
 "26_timeline": "Let's draw the whole conversation in one go. Attach, and settle. Reset. Ask for the device descriptor. Set the address. Ask for the configuration. Pick a driver. Set the configuration. On a typical computer, that's usually all over in well under a second, though a brand-new driver can take longer.",
 "27_recap": "Right, let's recap. A pull-up resistor announces the device, and its speed. A reset puts it at address zero. The device descriptor says who made it, and what it is. Set address gives it a number of its own. The configuration describes what's inside. And a driver is matched, before set configuration brings it to life.",
 "28_end": "Next episode: U-ART, S P I and I squared C. How do chips actually talk to each other? Thanks for watching, and subscribe, so you don't miss it.",
}
OUTPUT = "how_usb_knows_what_you_plugged_in_ep4_narrated.mp4"


def render(name, fn, dur): S.render_to("ep4", name, fn, dur)


if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    print(S.preview("ep4", SCENES))
