"""Tech 101, episode 5: UART vs SPI vs I2C, explained with an oscilloscope. Style: paper. Format: versus."""
import math, sys
from PIL import Image, ImageDraw
import style
from style import clamp, ease, prog, pop, grow, mix

S = style.get("paper")
W, H, FPS = S.W, S.H, S.FPS
VOICE, SPEED, LANG = S.VOICE, S.SPEED, S.LANG

# one colour per contender, used the same way in every scene
UC, SC, IC = S.BLUE, S.EXTRA, S.ACCENT
# SPI signal colours
C_CLK, C_MOSI, C_MISO, C_CS = S.EXTRA, S.HILITE, S.GOOD, S.BAD

# ---------------- timing helpers ----------------
BASE = 12.0
def tl(t, dur):
    """Build timeline: every scene builds over the same 0..12 'beats', stretched to the narrated length."""
    return t * BASE / max(dur, 1e-6)
def kin(T, a, d=0.45): return prog(T, a, a + d)
def drop(T, a, dist=60): return (1 - pop(T, a, a + 0.6)) * dist      # slide-into-place offset (with overshoot)
def popk(T, a, d=0.55): return pop(T, a, a + d)

# ---------------- drawing helpers (all through a style object) ----------------
def levf(events, U):
    """events: [(time, level), ...] sorted; returns lev(u) for u in 0..1 over U time units."""
    def f(u):
        x, v = u * U, events[0][1]
        for a, l in events:
            if x >= a: v = l
            else: break
        return v
    return f

def bits_events(bits, start, bw, lead_level=1, tail_level=1, end=None):
    ev = [(0, lead_level)]
    for i, b in enumerate(bits): ev.append((start + i * bw, b))
    ev.append((start + len(bits) * bw, tail_level))
    return ev

def wave(d, lev, x0, x1, ylo, yhi, col, k=1.0, reveal=1.0, width=6, tau=0.0, u0=0.0, u1=1.0, st=None):
    """Digital trace. lev(u) gives 0..1 for u in 0..1 across x0..x1. tau (px) rounds rising edges like a pull-up."""
    st = st or S
    if k <= 0.01: return None
    span, pts, v, px = x1 - x0, [], None, 0
    lim = min(u1, clamp(reveal))
    while px <= span:
        u = px / span
        if u > lim: break
        tgt = lev(u)
        if v is None or tau <= 0 or tgt < v: v = tgt
        else: v += (tgt - v) * (1 - math.exp(-2.0 / tau))
        if u >= u0: pts.append((x0 + px, ylo + (yhi - ylo) * v))
        px += 2
    if len(pts) > 1: st.line(d, pts, col, width, k)
    return pts[-1] if pts else None

def scope(d, xy, k=1.0, grid=(12, 4), st=None, tag="SCOPE"):
    """A paper 'oscilloscope screen': panel, faint grid, a corner tag."""
    st = st or S
    if k <= 0.01: return
    x0, y0, x1, y1 = xy
    st.box(d, xy, st.PANEL, st.LINE, 22, 4, k)
    gc = mix(st.PANEL, st.LINE, 0.12)
    gx, gy = grid
    for i in range(1, gx):
        x = x0 + (x1 - x0) * i / gx
        st.line(d, [(x, y0 + 12), (x, y1 - 12)], gc, 2, k)
    for j in range(1, gy):
        y = y0 + (y1 - y0) * j / gy
        st.line(d, [(x0 + 12, y), (x1 - 12, y)], gc, 2, k)
    if tag: st.text(d, (x1 - 22, y0 + 24), tag, 20, st.DIM, "Bold", "rm", k=k)

def ptbox(d, cx, cy, w, h, col, p, r=18, st=None, outline=None, width=4):
    """Box scaled by a pop factor p (0..~1.1)."""
    st = st or S
    if p <= 0.02: return
    st.box(d, (cx - w * p / 2, cy - h * p / 2, cx + w * p / 2, cy + h * p / 2), col, outline, r, width, min(1, p * 1.6))

def label_box(d, cx, cy, w, h, title, sub, col, T, a, st=None, tsize=36, ssize=24, txtcol=None):
    """A flat cut-out card with a title (and optional sub) that slides up into place."""
    st = st or S
    k = kin(T, a, 0.35)
    if k <= 0.01: return
    oy = drop(T, a, 50)
    st.box(d, (cx - w / 2, cy - h / 2 + oy, cx + w / 2, cy + h / 2 + oy), col, None, 18, 0, k)
    tc = txtcol or st.ON_ACCENT
    if sub:
        st.text(d, (cx, cy - ssize * 0.55 + oy), title, tsize, tc, "Bold", "mm", k=k)
        st.text(d, (cx, cy + tsize * 0.62 + oy), sub, ssize, tc, "SemiBold", "mm", k=k)
    else:
        st.text(d, (cx, cy + oy), title, tsize, tc, "Bold", "mm", k=k)

def dot(d, xy, r, col, k=1.0, st=None):
    (st or S).circle(d, xy, r, col, None, k=k, shadow=False)

def along(pts, u): return grow(pts, clamp(u))[-1]

def resistor(d, x, y0, y1, col, k=1.0, st=None, zig=6, wdt=16):
    st = st or S
    a, b = y0 + (y1 - y0) * 0.25, y0 + (y1 - y0) * 0.75
    pts = [(x, y0), (x, a)]
    for i in range(zig):
        pts.append((x + (wdt if i % 2 == 0 else -wdt), a + (b - a) * (i + 0.5) / zig))
    pts += [(x, b), (x, y1)]
    st.line(d, pts, col, 4, k)

def ground(d, x, y, col, k=1.0, st=None):
    st = st or S
    for i, w in enumerate((26, 17, 8)):
        st.line(d, [(x - w, y + i * 9), (x + w, y + i * 9)], col, 4, k)

def tick_mark(d, c, s, col, k=1.0, st=None):
    st = st or S
    x, y = c
    st.line(d, [(x - s * 0.5, y), (x - s * 0.12, y + s * 0.4), (x + s * 0.6, y - s * 0.45)], col, max(4, int(s / 6)), k)

def cross_mark(d, c, s, col, k=1.0, st=None):
    st = st or S
    x, y = c
    st.line(d, [(x - s / 2, y - s / 2), (x + s / 2, y + s / 2)], col, max(4, int(s / 6)), k)
    st.line(d, [(x - s / 2, y + s / 2), (x + s / 2, y - s / 2)], col, max(4, int(s / 6)), k)

def stamp(d, c, s, col, size=44, ang=-7, k=1.0, scale=1.0, st=None):
    """A tilted paper tag pasted onto the frame (used for 'FRAMING ERROR', 'SWAPPED!' ...)."""
    st = st or S
    if k <= 0.01 or scale <= 0.02: return
    f = st.font(size, "Bold")
    tw, th = int(d.textlength(s, font=f) + size * 1.4), int(size * 1.7)
    tile = Image.new("RGBA", (tw + 30, th + 30), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.rounded_rectangle([12, 15, 12 + tw, 15 + th], int(size * 0.4), fill=(90, 70, 50, 60))
    td.rounded_rectangle([6, 6, 6 + tw, 6 + th], int(size * 0.4), fill=tuple(col) + (255,))
    td.text((6 + tw / 2, 6 + th / 2), s, font=f, fill=tuple(st.ON_ACCENT) + (255,), anchor="mm")
    tile = tile.rotate(ang, expand=True, resample=Image.BICUBIC)
    if abs(scale - 1) > 0.01:
        tile = tile.resize((max(1, int(tile.width * scale)), max(1, int(tile.height * scale))), Image.BICUBIC)
    if k < 1:
        tile.putalpha(tile.getchannel("A").point(lambda a: int(a * clamp(k))))
    d._image.paste(tile, (int(c[0] - tile.width / 2), int(c[1] - tile.height / 2)), tile)

# the UART frame of the letter "A" (hex 41 = 0100 0001), LSB first
A_BITS = [1, 0, 0, 0, 0, 0, 1, 0]
UART_FRAME = [0] + A_BITS + [1]          # start, b0..b7, stop

def uart_frame_lev(lead=1.0, tail=1.0, bits=None):
    fr = [0] + (bits or A_BITS) + [1]
    U = lead + len(fr) + tail
    return levf(bits_events(fr, lead, 1.0), U), U

def mini_uart(d, x0, x1, yc, amp, col, k=1.0, reveal=1.0, st=None, width=5):
    lev, U = uart_frame_lev(1.0, 1.0)
    wave(d, lev, x0, x1, yc + amp, yc - amp, col, k, reveal, width, st=st)

def mini_spi(d, x0, x1, yc, amp, col, k=1.0, reveal=1.0, st=None, width=5, gap=None):
    gap = gap or amp * 2 + 16
    n = 8
    ev = [(0, 0)]
    for i in range(n): ev += [(0.5 + i + 0.5, 1), (0.5 + i + 1.0, 0)]
    lev = levf(ev, n + 1)
    wave(d, lev, x0, x1, yc - gap / 2 + amp, yc - gap / 2 - amp, col, k, reveal, width, st=st)
    bits = [1, 0, 1, 0, 0, 1, 0, 1]
    lev2 = levf(bits_events(bits, 0.5, 1.0, 0, 0), n + 1)
    wave(d, lev2, x0, x1, yc + gap / 2 + amp, yc + gap / 2 - amp, mix(col, (255, 255, 255), 0.0) if st is None else col,
         k, reveal, width, st=st)

def mini_i2c(d, x0, x1, yc, amp, col, k=1.0, reveal=1.0, st=None, width=5, gap=None):
    gap = gap or amp * 2 + 16
    U = 11
    sda = levf([(0, 1), (1.0, 0), (1.6, 1), (2.6, 0), (4.6, 1), (5.6, 0), (8.6, 0), (9.6, 0), (10.3, 1)], U)
    ev = [(0, 1), (1.5, 0)]
    for i in range(8): ev += [(2.0 + i, 1), (2.5 + i, 0)]
    ev += [(10.0, 1)]
    scl = levf(ev, U)
    wave(d, sda, x0, x1, yc - gap / 2 + amp, yc - gap / 2 - amp, col, k, reveal, width, tau=6, st=st)
    wave(d, scl, x0, x1, yc + gap / 2 + amp, yc + gap / 2 - amp, col, k, reveal, width, tau=6, st=st)

# ================= scenes =================
# ---------- hook + cover ----------
def s_hook(d, t, dur):
    S.chrome(d, "", "How do chips talk?", "A brain chip and its friends chat all day over a few thin wires. In one of three languages.", t, dur)
    T = tl(t, dur)
    cx, cy = 960, 520
    S.chip(d, cx - 160, cy - 90 + drop(T, 0.2), 320, 180, "MCU", "the brain", S.HILITE, kin(T, 0.2))
    friends = [("sensor", 330, 350, IC, -1), ("display", 330, 690, SC, -1),
               ("flash memory", 1590, 350, SC, 1), ("GPS module", 1590, 690, UC, 1)]
    for i, (n, fx, fy, c, side) in enumerate(friends):
        a = 0.8 + i * 0.4
        S.chip(d, fx - 150, fy - 60 + drop(T, a), 300, 120, n, None, c, kin(T, a))
        sy = cy - 40 if fy < cy else cy + 40
        mx = 650 if side < 0 else 1270
        path = [(cx + side * 160, sy), (mx, sy), (mx, fy), (fx - side * 150, fy)]
        kk = prog(T, 2.4 + i * 0.35, 3.2 + i * 0.35)
        if kk > 0: S.line(d, grow(path, kk), c, 7)
        if T > 4.2:
            for j in range(2):
                u = (t * 0.55 + i * 0.27 + j * 0.5) % 1.0
                if side > 0 and i == 3: u = 1 - u            # GPS talks back to the MCU
                dot(d, along(path, u), 10, c, prog(T, 4.2, 4.8))
    for i, (n, c) in enumerate((("UART", UC), ("SPI", SC), ("I²C", IC))):
        a = 5.2 + i * 0.6
        S.pill(d, (760 + i * 200, 262 + drop(T, a, 40)), n, 34, c, kin(T, a, 0.3))

def s_cover(d, t, dur):
    S.chrome(d, "", "Here's what we'll cover", "Read a scope trace, meet three contenders, score them head to head, then pick a winner.", t, dur)
    T = tl(t, dur)
    items = [("1", "The basics", "how to read a scope trace", S.LINE), ("2", "UART", "no clock, an agreed pace", UC),
             ("3", "SPI", "a clock and a tap on the shoulder", SC), ("4", "I²C", "two wires and a roll call", IC),
             ("5", "Head to head", "the same scorecard for all three", S.HILITE), ("6", "Which one when", "picking the right tool", S.GOOD)]
    hi = int(t / 1.4) % 6 if T > 6.0 else -1
    for i, (n, a, b, c) in enumerate(items):
        st = 0.5 + i * 0.6
        kk = kin(T, st, 0.35)
        if kk <= 0.01: continue
        col, row = i % 2, i // 2
        x, y = 170 + col * 810, 250 + row * 180 + drop(T, st, 50)
        S.box(d, (x, y, x + 760, y + 150), S.PANEL, c if i == hi else None, 20, 5, kk)
        p = popk(T, st + 0.15)
        S.circle(d, (x + 75, y + 75), 42 * max(0.01, p), c, None, k=kk)
        S.text(d, (x + 75, y + 75), n, 40, S.ON_ACCENT, "Bold", "mm", k=kk)
        S.text(d, (x + 145, y + 52), a, 42, S.TXT, "Bold", "lm", k=kk)
        S.text(d, (x + 145, y + 104), b, 30, S.DIM, "SemiBold", "lm", k=kk)

# ---------- STEP 1 · THE BASICS ----------
def s_serial(d, t, dur):
    S.chrome(d, "STEP 1 · THE BASICS", "Eight wires, or one?", "Parallel: eight wires, a byte at once. Serial: one wire, bits one after another. All three contenders are serial.", t, dur)
    T = tl(t, dur)
    byte = [0, 1, 0, 0, 0, 0, 0, 1]
    # parallel
    k1 = kin(T, 0.4)
    S.box(d, (140, 250, 900, 790), S.PANEL, None, 24, 0, k1)
    S.text(d, (520, 296), "PARALLEL", 38, S.TXT, "Bold", "mm", k=k1)
    S.box(d, (190, 350, 300, 700), S.LINE, None, 14, 0, kin(T, 0.8))
    S.box(d, (740, 350, 850, 700), S.LINE, None, 14, 0, kin(T, 0.8))
    S.text(d, (245, 525), "A", 40, S.ON_ACCENT, "Bold", "mm", k=kin(T, 0.8))
    S.text(d, (795, 525), "B", 40, S.ON_ACCENT, "Bold", "mm", k=kin(T, 0.8))
    u = (t * 0.45) % 1.0
    for i in range(8):
        y = 375 + i * 43
        kk = prog(T, 1.2 + i * 0.12, 1.6 + i * 0.12)
        S.line(d, [(300, y), (300 + 440 * kk, y)], S.DIM, 4)
        if T > 2.6:
            x = 320 + 400 * u
            S.circle(d, (x, y), 15, S.HILITE if byte[i] else S.DIM, None, k=prog(T, 2.6, 3.0), shadow=False)
            S.text(d, (x, y), str(byte[i]), 20, S.ON_ACCENT, "Bold", "mm", k=prog(T, 2.6, 3.0))
    S.text(d, (520, 748), "8 wires: a whole byte at once", 32, S.DIM, "SemiBold", "mm", k=kin(T, 3.0))
    # serial
    k2 = kin(T, 4.0)
    S.box(d, (1020, 250, 1780, 790), S.PANEL, None, 24, 0, k2)
    S.text(d, (1400, 296), "SERIAL", 38, S.TXT, "Bold", "mm", k=k2)
    S.box(d, (1070, 450, 1180, 600), S.LINE, None, 14, 0, kin(T, 4.3))
    S.box(d, (1620, 450, 1730, 600), S.LINE, None, 14, 0, kin(T, 4.3))
    S.text(d, (1125, 525), "A", 40, S.ON_ACCENT, "Bold", "mm", k=kin(T, 4.3))
    S.text(d, (1675, 525), "B", 40, S.ON_ACCENT, "Bold", "mm", k=kin(T, 4.3))
    S.line(d, [(1180, 525), (1180 + 440 * prog(T, 4.6, 5.2), 525)], S.DIM, 5)
    if T > 5.4:
        head = 1180 + ((t * 120) % 860)
        for j, b in enumerate(byte[::-1]):
            x = head - j * 56
            if 1195 < x < 1605:
                S.box(d, (x - 22, 498, x + 22, 552), S.HILITE if b else S.DIM, None, 8, 0, prog(T, 5.4, 5.8), shadow=False)
                S.text(d, (x, 525), str(b), 26, S.ON_ACCENT, "Bold", "mm", k=prog(T, 5.4, 5.8))
    S.text(d, (1400, 690), "1 wire: bits one after another", 32, S.DIM, "SemiBold", "mm", k=kin(T, 6.0))
    stamp(d, (1400, 395), "fewer pins!", S.GOOD, 34, -6, kin(T, 7.0), popk(T, 7.0))

def s_scope(d, t, dur):
    S.chrome(d, "STEP 1 · THE BASICS", "How to read a scope trace", "Up the screen is voltage, across is time. On a 3.3 V chip: near 3.3 V is a 1, near 0 V is a 0.", t, dur)
    T = tl(t, dur)
    xy = (200, 260, 1360, 770)
    scope(d, xy, kin(T, 0.3))
    bits = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]
    yh, yl = 390, 640
    x0, x1 = 260, 1300
    lev = levf(bits_events(bits, 0, 1, bits[0], bits[-1]), len(bits))
    rv = prog(T, 1.2, 7.0)
    end = wave(d, lev, x0, x1, yl, yh, S.HILITE, kin(T, 1.0), rv, 7)
    bw = (x1 - x0) / len(bits)
    for i, b in enumerate(bits):
        if rv * len(bits) > i + 0.5:
            S.text(d, (x0 + bw * (i + 0.5), (yh if b else yl) + (-36 if b else 40)), str(b), 30, S.TXT, "Bold", "mm",
                   k=prog(rv * len(bits), i + 0.5, i + 0.9))
    if end and rv < 1: S.line(d, [(end[0], 290), (end[0], 740)], S.ACCENT, 3)
    # axis cues inside the screen
    ka = kin(T, 0.8)
    S.arrow(d, (232, 720), (232, 320), S.DIM, 4, ka)
    S.text(d, (250, 300), "voltage", 24, S.DIM, "Bold", "lm", k=ka)
    S.arrow(d, (1100, 742), (1320, 742), S.DIM, 4, ka)
    S.text(d, (1090, 742), "time", 24, S.DIM, "Bold", "rm", k=ka)
    # level labels to the right
    for (y, a, s, sub, c) in ((yh, 3.0, "HIGH = 1", "near 3.3 V", S.HILITE), (yl, 4.0, "LOW = 0", "near 0 V", S.LINE)):
        kk = kin(T, a)
        S.arrow(d, (1500, y), (1380, y), c, 5, kk)
        S.box(d, (1510, y - 62 + drop(T, a, 30), 1800, y + 62 + drop(T, a, 30)), c, None, 18, 0, kk)
        S.text(d, (1655, y - 18 + drop(T, a, 30)), s, 38, S.ON_ACCENT, "Bold", "mm", k=kk)
        S.text(d, (1655, y + 28 + drop(T, a, 30)), sub, 28, S.ON_ACCENT, "SemiBold", "mm", k=kk)
    S.text(d, (1655, 760), "(example: a 3.3 V chip)", 24, S.DIM, "SemiBold", "mm", k=kin(T, 5.0))

def s_contenders(d, t, dur):
    S.chrome(d, "STEP 1 · THE BASICS", "Meet the contenders", "UART: no clock. SPI: fast, with a clock and a select wire. I²C: two wires shared by many chips.", t, dur)
    T = tl(t, dur)
    cards = [("UART", UC, ["no clock at all", "an agreed pace"], mini_uart),
             ("SPI", SC, ["a clock + a select", "built for speed"], mini_spi),
             ("I²C", IC, ["two shared wires", "chips have addresses"], mini_i2c)]
    for i, (n, c, lines, fn) in enumerate(cards):
        a = 0.5 + i * 1.3
        k = kin(T, a, 0.35)
        if k <= 0.01: continue
        cx = 400 + i * 560
        oy = drop(T, a, 70)
        S.box(d, (cx - 250, 250 + oy, cx + 250, 620 + oy), S.PANEL, None, 26, 0, k)
        S.box(d, (cx - 250, 250 + oy, cx + 250, 340 + oy), c, None, 26, 0, k, shadow=False)
        S.text(d, (cx, 296 + oy), n, 60, S.ON_ACCENT, "Bold", "mm", k=k)
        for j, ln in enumerate(lines):
            S.text(d, (cx, 380 + j * 44 + oy), ln, 32, S.TXT, "SemiBold", "mm", k=k)
        fn(d, cx - 200, cx + 200, 540 + oy, 22, c, k, prog(T, a + 0.4, a + 2.4))
    crit = ["wires", "clock", "speed", "how many chips", "typical uses"]
    S.text(d, (960, 680), "scored on the same things:", 28, S.DIM, "SemiBold", "mm", k=kin(T, 5.2))
    xs = [440, 680, 910, 1170, 1460]
    for i, cname in enumerate(crit):
        a = 5.6 + i * 0.4
        S.pill(d, (xs[i], 745 + drop(T, a, 30)), cname, 28, S.LINE, kin(T, a, 0.3))

# ---------- STEP 2 · UART ----------
def s_uart_wires(d, t, dur):
    S.chrome(d, "STEP 2 · UART", "Two wires, crossed over", "TX goes to RX, and RX to TX, so both can talk at once. Plus a shared ground.", t, dur)
    T = tl(t, dur)
    S.chip(d, 220, 360 + drop(T, 0.3), 380, 240, "Chip A", "e.g. microcontroller", S.HILITE, kin(T, 0.3), pins=False)
    S.chip(d, 1320, 360 + drop(T, 0.7), 380, 240, "Chip B", "e.g. GPS module", UC, kin(T, 0.7), pins=False)
    ka = kin(T, 1.2)
    for (x, y, s, an) in ((590, 420, "TX", "rm"), (590, 540, "RX", "rm"), (1330, 420, "TX", "lm"), (1330, 540, "RX", "lm")):
        S.text(d, (x, y), s, 30, S.ON_ACCENT, "Bold", an, k=ka)
    pa = [(600, 420), (820, 420), (1100, 540), (1320, 540)]
    pb = [(1320, 420), (1100, 420), (820, 540), (600, 540)]
    k1, k2 = prog(T, 1.8, 3.0), prog(T, 3.0, 4.2)
    if k1 > 0:
        S.line(d, grow(pa, k1), S.HILITE, 7)
        if k1 >= 1: S.arrow(d, (1240, 540), (1316, 540), S.HILITE, 7)
    if k2 > 0:
        S.line(d, grow(pb, k2), UC, 7)
        if k2 >= 1: S.arrow(d, (680, 540), (604, 540), UC, 7)
    if T > 4.4:
        for j in range(3):
            dot(d, along(pa, (t * 0.4 + j / 3) % 1), 9, S.HILITE)
            dot(d, along(pb, (t * 0.33 + j / 3 + 0.15) % 1), 9, UC)
    kg = prog(T, 5.0, 6.0)
    gp = [(410, 600), (410, 700), (1510, 700), (1510, 600)]
    if kg > 0: S.line(d, grow(gp, kg), S.DIM, 6)
    ground(d, 960, 712, S.DIM, kin(T, 6.0))
    S.text(d, (960, 670), "shared ground (GND)", 28, S.DIM, "Bold", "mm", k=kin(T, 6.0))
    S.pill(d, (760, 290 + drop(T, 2.2, 30)), "TX = transmit", 28, S.HILITE, kin(T, 2.2, 0.3))
    S.pill(d, (1160, 290 + drop(T, 3.4, 30)), "RX = receive", 28, UC, kin(T, 3.4, 0.3))

def dial(d, c, r, ang, col, k, st=None):
    st = st or S
    st.circle(d, c, r, st.PANEL, None, k=k)
    st.circle(d, c, r, None, col, 6, k=k, shadow=False)
    for i in range(12):
        a = i * math.pi / 6
        st.line(d, [(c[0] + (r - 14) * math.cos(a), c[1] + (r - 14) * math.sin(a)),
                    (c[0] + (r - 4) * math.cos(a), c[1] + (r - 4) * math.sin(a))], st.DIM, 3, k)
    st.line(d, [c, (c[0] + (r - 22) * math.cos(ang), c[1] + (r - 22) * math.sin(ang))], col, 6, k)
    st.circle(d, c, 8, col, None, k=k, shadow=False)

def s_uart_baud(d, t, dur):
    S.chrome(d, "STEP 2 · UART", "No clock, just an agreed pace", "No clock wire. Both sides agree a speed: the baud rate. Example: 115 200 baud, about 8.7 µs per bit.", t, dur)
    T = tl(t, dur)
    ang = -math.pi / 2 + (int(t * 3) % 12) * math.pi / 6
    for i, (x, n, c) in enumerate(((430, "sender's own timer", S.HILITE), (1490, "receiver's own timer", UC))):
        a = 0.4 + i * 0.6
        p = popk(T, a)
        if p > 0.02: dial(d, (x, 420), 95 * p, ang, c, kin(T, a, 0.3))
        S.text(d, (x, 548), n, 28, S.TXT, "SemiBold", "mm", k=kin(T, a + 0.3))
    kk = kin(T, 1.8)
    for i in range(14):
        x = 560 + i * 58
        S.line(d, [(x, 420), (x + 30, 420)], S.DIM, 5, kk)
    S.circle(d, (960, 420), 46 * max(0.01, popk(T, 2.4)), S.PANEL, None, k=kin(T, 2.4, 0.3))
    cross_mark(d, (960, 420), 44, S.BAD, kin(T, 2.4, 0.3))
    S.text(d, (960, 494), "no clock wire", 28, S.BAD, "Bold", "mm", k=kin(T, 2.6))
    stamp(d, (960, 290), "115 200 baud (example)", UC, 34, 0, kin(T, 4.0), popk(T, 4.0))
    # bit ruler
    x0, bw, y = 360, 120, 640
    n_on = int(prog(T, 5.2, 7.0) * 10 + 0.001)
    sweep = int(t * 2.5) % 10
    for i in range(10):
        if i < n_on:
            c = UC if (i == sweep and T > 7.2) else mix(S.PANEL, UC, 0.25)
            S.box(d, (x0 + i * bw + 4, y, x0 + (i + 1) * bw - 4, y + 70), c, None, 10, 0, 1.0, shadow=False)
            S.text(d, (x0 + i * bw + bw / 2, y + 35), "1 bit", 24, S.TXT if c != UC else S.ON_ACCENT, "Bold", "mm")
    S.text(d, (960, 750), "each bit ≈ 1 ÷ 115 200 s ≈ 8.7 µs", 32, S.TXT, "SemiBold", "mm", k=kin(T, 7.4))

FRAME_LABELS = ["start", "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "stop"]
def uart_scope_frame(d, T, t, xy, yh, yl, reveal, k, show_labels=True, st=None, lsize=24, vsize=30):
    """The 'A' frame on a scope, with tinted bit cells. Returns (x_of_start_edge, bit_width)."""
    st = st or S
    x0, y0, x1, y1 = xy
    lead, tail = 1.2, 0.8
    lev, U = uart_frame_lev(lead, tail)
    tx0, tx1 = x0 + 30, x1 - 30
    bw = (tx1 - tx0) / U
    xs = tx0 + lead * bw
    nrev = reveal * U - lead
    for i, b in enumerate(UART_FRAME):
        if nrev <= i: break
        kk = prog(nrev, i, i + 0.6) * k
        c = st.HILITE if i == 0 else (st.GOOD if i == 9 else UC)
        st.box(d, (xs + i * bw + 3, y0 + 46, xs + (i + 1) * bw - 3, y1 - 16), mix(st.PANEL, c, 0.16), None, 8, 0, kk, shadow=False)
        if show_labels:
            st.text(d, (xs + (i + 0.5) * bw, y0 + 70), FRAME_LABELS[i], lsize, c, "Bold", "mm", k=kk)
            st.text(d, (xs + (i + 0.5) * bw, (yh + 38) if b else (yl + 38)), str(b), vsize, st.TXT, "Bold", "mm", k=kk)
    if reveal * U > 0.3:
        st.text(d, (tx0 + lead * bw / 2, yh - 34), "idle", lsize, st.DIM, "Bold", "mm", k=k)
    wave(d, lev, tx0, tx1, yl, yh, UC, k, reveal, 7, st=st)
    return xs, bw

def s_uart_frame(d, t, dur):
    S.chrome(d, "STEP 2 · UART", "Sending the letter A", "Idle high. Start bit low. Eight data bits, least significant first. Stop bit high.", t, dur)
    T = tl(t, dur)
    xy = (140, 250, 1780, 640)
    scope(d, xy, kin(T, 0.3))
    rv = prog(T, 0.8, 7.0)
    uart_scope_frame(d, T, t, xy, 360, 560, rv, kin(T, 0.6))
    k = kin(T, 7.2)
    S.box(d, (300, 668 + drop(T, 7.2, 30), 1620, 790 + drop(T, 7.2, 30)), S.PANEL, None, 20, 0, k)
    oy = drop(T, 7.2, 30)
    S.text(d, (340, 702 + oy), "A  =  hex 41  =  0100 0001", 34, S.TXT, "Bold", "lm", mono=True, k=k)
    S.text(d, (340, 756 + oy), "sent LSB first:  1 0 0 0 0 0 1 0", 34, UC, "Bold", "lm", mono=True, k=k)
    S.pill(d, (1470, 729 + oy), "backwards!", 28, S.HILITE, kin(T, 8.0, 0.3))

def s_uart_sample(d, t, dur):
    S.chrome(d, "STEP 2 · UART", "Sampling in the middle", "The receiver spots the start bit's falling edge, counts ticks to the middle of each bit, and samples there.", t, dur)
    T = tl(t, dur)
    xy = (140, 250, 1780, 600)
    scope(d, xy, kin(T, 0.3), (12, 3))
    x0, bw = 360, 440
    yh, yl = 340, 520
    U = (1780 - 30 - (140 + 30))
    ev = [(0, 1), (x0, 0), (x0 + bw, 1), (x0 + 2 * bw, 0), (x0 + 3 * bw, 0)]
    lev = levf([(a - 170, l) for a, l in ev], U)
    rv = prog(T, 0.6, 3.0)
    wave(d, lev, 170, 1750, yl, yh, UC, kin(T, 0.5), rv, 7)
    for i, s in enumerate(("start", "b0 = 1", "b1 = 0")):
        S.text(d, (x0 + bw * (i + 0.5), 290), s, 28, S.HILITE if i == 0 else UC, "Bold", "mm", k=kin(T, 1.0 + i * 0.6))
    # edge detected
    ke = kin(T, 3.0)
    S.circle(d, (x0, (yh + yl) / 2), 30 * max(0.01, popk(T, 3.0)), None, S.BAD, 5, k=ke)
    S.text(d, (x0 - 40, yl + 50), "edge detected", 26, S.BAD, "Bold", "rm", k=ke)
    # 16 ticks per bit
    nt = int(prog(T, 3.6, 7.4) * 40)
    for i in range(40):
        x = x0 + i * bw / 16
        if i < nt:
            big = (i % 16 == 8)
            S.line(d, [(x, 620), (x, 650 if not big else 672)], S.HILITE if big else S.DIM, 4 if big else 3)
    S.text(d, (x0 + bw * 0.25, 700), "16 ticks per bit", 26, S.DIM, "Bold", "mm", k=kin(T, 4.0))
    for i in range(3):
        a = 4.4 + i * 1.4
        if nt > 8 + i * 16:
            xx = x0 + bw * (i + 0.5)
            yy = [yl, yh, yl][i]
            kk = kin(T, a, 0.3)
            S.line(d, [(xx, 600), (xx, yy + 14)], S.HILITE, 3, kk)
            S.circle(d, (xx, yy), 16 * max(0.01, popk(T, a)), S.HILITE, None, k=kk)
    S.text(d, (x0 + bw * 0.5, 740), "tick 8: the middle", 26, S.HILITE, "Bold", "mm", k=kin(T, 5.0))
    S.pill(d, (1450, 720 + drop(T, 8.0, 30)), "often 16× oversampling", 28, S.HILITE, kin(T, 8.0, 0.3))

def s_uart_mismatch(d, t, dur):
    S.chrome(d, "STEP 2 · UART", "When the pace doesn't match", "Receiver set too fast: its samples drift onto the wrong bits. Stop bit reads low: a framing error.", t, dur)
    T = tl(t, dur)
    xy = (140, 250, 1780, 600)
    scope(d, xy, kin(T, 0.3))
    xs, bw = uart_scope_frame(d, T, t, xy, 350, 520, 1.0, kin(T, 0.5), show_labels=True, lsize=22, vsize=0 or 26)
    ratio = 0.88                                      # example: receiver about 12% too fast
    reads = []
    for j in range(10):
        pos = (j + 0.5) * ratio
        idx = min(9, int(pos))
        reads.append(UART_FRAME[idx])
    n = int(prog(T, 1.6, 7.0) * 10 + 0.001)
    for j in range(10):
        ideal = xs + (j + 0.5) * bw
        actual = xs + (j + 0.5) * ratio * bw
        if j < n:
            kk = 1.0
            S.line(d, [(ideal, 590), (ideal, 610)], S.GOOD, 4, kk)
            yy = 350 if reads[j] else 520
            S.line(d, [(actual, 590), (actual, yy + 12)], S.BAD, 3, kk)
            S.circle(d, (actual, yy), 13, S.BAD, None, k=kk, shadow=False)
    S.text(d, (300, 640), "green: where it should sample", 24, S.GOOD, "Bold", "lm", k=kin(T, 2.0))
    S.text(d, (1620, 640), "red: where it does sample", 24, S.BAD, "Bold", "rm", k=kin(T, 2.0))
    # sent vs read
    ky = kin(T, 7.2)
    if ky > 0.01:
        sent = "".join(str(b) for b in A_BITS)
        got = "".join(str(b) for b in reads[1:9])
        S.box(d, (300, 676, 1250, 792), S.PANEL, None, 18, 0, ky)
        S.text(d, (330, 708), f"sent:  {sent}   stop 1", 30, S.TXT, "Bold", "lm", mono=True, k=ky)
        S.text(d, (330, 758), f"read:  {got}   stop {reads[9]}", 30, S.BAD, "Bold", "lm", mono=True, k=ky)
    stamp(d, (1510, 728), "FRAMING ERROR", S.BAD, 38, -7, kin(T, 8.2), popk(T, 8.2))
    S.text(d, (1780, 230), "(example: receiver about 12% too fast)", 24, S.DIM, "SemiBold", "rm", k=kin(T, 1.0))

def s_uart_extras(d, t, dur):
    S.chrome(d, "STEP 2 · UART", "Parity, and voltage levels", "Optional parity bit; 8N1 is common. On a board: logic levels. RS-232 uses bigger, inverted voltages.", t, dur)
    T = tl(t, dur)
    # left: frame with parity
    k = kin(T, 0.3)
    S.box(d, (130, 250, 900, 790), S.PANEL, None, 24, 0, k)
    S.text(d, (515, 292), "an optional parity bit", 34, S.TXT, "Bold", "mm", k=k)
    cells = [("S", S.HILITE)] + [(f"{b}", UC) for b in A_BITS] + [("P", S.EXTRA), ("1", S.GOOD)]
    for i, (s, c) in enumerate(cells):
        a = 0.6 + i * 0.18
        if i == 9: a = 2.6
        p = popk(T, a)
        ptbox(d, 190 + i * 65, 400, 56, 70, c, p, 10)
        if p > 0.5: S.text(d, (190 + i * 65, 400), s, 30, S.ON_ACCENT, "Bold", "mm")
    S.arrow(d, (775, 500), (775, 446), S.EXTRA, 5, kin(T, 3.0))
    S.text(d, (775, 530), "parity: a simple check", 26, S.EXTRA, "Bold", "rm", k=kin(T, 3.0))
    S.text(d, (775, 564), "(catches some single-bit errors)", 22, S.DIM, "SemiBold", "rm", k=kin(T, 3.0))
    ke = kin(T, 4.2)
    S.box(d, (180, 620 + drop(T, 4.2, 30), 850, 750 + drop(T, 4.2, 30)), mix(S.PANEL, UC, 0.12), None, 18, 0, ke, shadow=False)
    S.text(d, (515, 660 + drop(T, 4.2, 30)), "common setting:  8N1", 34, UC, "Bold", "mm", k=ke)
    S.text(d, (515, 712 + drop(T, 4.2, 30)), "8 data bits · No parity · 1 stop bit", 26, S.TXT, "SemiBold", "mm", k=ke)
    # right: voltage levels
    k2 = kin(T, 5.2)
    S.box(d, (1000, 250, 1790, 790), S.PANEL, None, 24, 0, k2)
    S.text(d, (1395, 292), "same frame, two voltage styles", 32, S.TXT, "Bold", "mm", k=k2)
    lev, U = uart_frame_lev(1.0, 1.0)
    rv = prog(T, 5.6, 7.6)
    S.text(d, (1040, 350), "logic level (on the board)", 26, UC, "Bold", "lm", k=k2)
    S.line(d, [(1040, 480), (1760, 480)], mix(S.PANEL, S.LINE, 0.25), 2, k2)
    wave(d, lev, 1150, 1760, 480, 385, UC, k2, rv, 5)
    S.text(d, (1130, 386), "3.3 V", 22, S.DIM, "SemiBold", "rm", k=k2)
    S.text(d, (1130, 480), "0 V", 22, S.DIM, "SemiBold", "rm", k=k2)
    k3 = kin(T, 6.4)
    S.text(d, (1040, 540), "RS-232 (older ports)", 26, S.BAD, "Bold", "lm", k=k3)
    inv = lambda u: 1 - lev(u)
    S.line(d, [(1150, 650), (1760, 650)], mix(S.PANEL, S.LINE, 0.25), 2, k3)
    wave(d, inv, 1150, 1760, 710, 590, S.BAD, k3, prog(T, 6.6, 8.4), 5)
    S.text(d, (1130, 590), "+ V", 22, S.DIM, "SemiBold", "rm", k=k3)
    S.text(d, (1130, 650), "0 V", 22, S.DIM, "SemiBold", "rm", k=k3)
    S.text(d, (1130, 710), "− V", 22, S.DIM, "SemiBold", "rm", k=k3)
    S.text(d, (1395, 755), "inverted, larger voltages: needs a converter chip", 24, S.TXT, "SemiBold", "mm", k=kin(T, 8.6))

# ---------- STEP 3 · SPI ----------
SPI_PERIPH = [("Chip 1", "e.g. display", 820), ("Chip 2", "e.g. flash", 1190), ("Chip 3", "e.g. ADC", 1560)]
def s_spi_wires(d, t, dur):
    S.chrome(d, "STEP 3 · SPI", "A conductor with a baton", "One controller drives the clock. Data out on MOSI, back on MISO. Each chip gets its own chip select.", t, dur)
    T = tl(t, dur)
    ytop = 640
    S.chip(d, 140, 280 + drop(T, 0.3), 300, 320, "Controller", None, SC, kin(T, 0.3), pins=False)
    for i, (n, sub, cx) in enumerate(SPI_PERIPH):
        a = 0.7 + i * 0.3
        S.chip(d, cx - 140, ytop + drop(T, a), 280, 120, n, sub, S.LINE, kin(T, a), pins=False)
    sel = int(t / 2.6) % 3 if T > 7.0 else 1
    # shared bus: three horizontal lines, each chip taps down to them
    names = [("SCLK", C_CLK), ("MOSI (COPI)", C_MOSI), ("MISO (CIPO)", C_MISO)]
    kb = prog(T, 1.8, 3.4)
    for j, (nm, c) in enumerate(names):
        y = 440 + j * 40
        if kb > 0: S.line(d, [(440, y), (440 + (1760 - 440) * kb, y)], c, 5)
        S.text(d, (460, y - 16), nm, 22, c, "Bold", "lm", k=kin(T, 2.4))
        if kb >= 1:
            for (_, _, cx) in SPI_PERIPH:
                tx = cx - 60 + j * 30
                S.line(d, [(tx, y), (tx, ytop)], c, 4)
                S.circle(d, (tx, y), 6, c, None, shadow=False)
    # chip selects: one private wire each, routed above the bus
    kc = prog(T, 3.8, 5.4)
    for i, (_, _, cx) in enumerate(SPI_PERIPH):
        y0 = 360 - i * 30
        xx = cx + 70
        path = [(440, y0), (xx, y0), (xx, ytop)]
        act = (i == sel and T > 5.6)
        if kc > 0: S.line(d, grow(path, kc), C_CS if act else mix(S.PANEL, C_CS, 0.55), 8 if act else 5)
        S.text(d, (460, y0 - 14), f"CS{i + 1}", 22, C_CS, "Bold", "lm", k=kin(T, 4.2))
    if T > 5.6:
        cx = SPI_PERIPH[sel][0 + 2]
        k = kin(T, 5.6)
        d.rounded_rectangle([cx - 152, ytop - 12, cx + 152, ytop + 132], 24, outline=S.fade(C_CS, k), width=6)
        stamp(d, (cx + 130, ytop - 20), "you!", C_CS, 26, -8, k, 1.0)
        S.text(d, (300, 680), "selected chip:", 24, C_CS, "Bold", "mm", k=kin(T, 6.0))
        S.text(d, (300, 712), "its CS goes LOW", 24, C_CS, "Bold", "mm", k=kin(T, 6.0))
        for j in range(3):
            u = (t * 0.5 + j / 3) % 1
            dot(d, (440 + 1320 * u, 440), 8, C_CLK)
    S.pill(d, (1300, 262 + drop(T, 6.6, 30)), "everyone follows one clock", 26, C_CLK, kin(T, 6.6, 0.3))

def spi_lev():
    """SPI mode 0, MSB first: CS, SCLK, MOSI (hex A5), MISO (hex 3C). Time units: bits start at 1.3."""
    U, b0 = 10.6, 1.3
    cs = levf([(0, 1), (1.0, 0), (9.6, 1)], U)
    ev = [(0, 0)]
    for i in range(8): ev += [(b0 + i + 0.5, 1), (b0 + i + 1.0, 0)]
    clk = levf(ev, U)
    mosi_b = [1, 0, 1, 0, 0, 1, 0, 1]
    miso_b = [0, 0, 1, 1, 1, 1, 0, 0]
    mosi = levf(bits_events(mosi_b, b0, 1.0, 0, 0), U)
    miso = levf(bits_events(miso_b, b0, 1.0, 0, 0), U)
    return U, b0, cs, clk, mosi, miso, mosi_b, miso_b

def s_spi_scope(d, t, dur):
    S.chrome(d, "STEP 3 · SPI", "One tick, one bit, both ways", "Chip select drops low. Eight clock ticks: on each, one bit goes out on MOSI and one comes back on MISO.", t, dur)
    T = tl(t, dur)
    xy = (140, 240, 1780, 800)
    scope(d, xy, kin(T, 0.3), (12, 4))
    U, b0, cs, clk, mosi, miso, mb, ib = spi_lev()
    x0, x1 = 360, 1740
    bw = (x1 - x0) / U
    rows = [("CS", cs, C_CS, 310), ("SCLK", clk, C_CLK, 430), ("MOSI", mosi, C_MOSI, 550), ("MISO", miso, C_MISO, 670)]
    rv = prog(T, 1.2, 8.0)
    for i, (n, lev, c, yc) in enumerate(rows):
        k = kin(T, 0.5 + i * 0.2)
        S.text(d, (180, yc), n, 30, c, "Bold", "lm", k=k)
        if n == "MISO":
            # high impedance (nobody driving) before CS falls and after it rises
            kk = k
            for (ua, ub) in ((0, 1.0 / U), (9.6 / U, 1.0)):
                if rv > ua:
                    xa, xb = x0 + ua * (x1 - x0), x0 + min(ub, rv) * (x1 - x0)
                    xx = xa
                    while xx < xb - 6:
                        S.line(d, [(xx, yc), (min(xx + 14, xb), yc)], S.DIM, 3, kk); xx += 26
            wave(d, lev, x0, x1, yc + 36, yc - 36, c, k, rv, 6, u0=1.0 / U, u1=9.6 / U)
        else:
            wave(d, lev, x0, x1, yc + 36, yc - 36, c, k, rv, 6)
    # sampling edges (mode 0: rising edges)
    for i in range(8):
        xe = x0 + (b0 + i + 0.5) * bw
        if rv * U > b0 + i + 0.5:
            kk = prog(rv * U, b0 + i + 0.5, b0 + i + 0.9)
            for yy in range(400, 712, 22): S.line(d, [(xe, yy), (xe, yy + 10)], S.DIM, 2, kk)
            S.text(d, (x0 + (b0 + i) * bw + bw * 0.25, 512), str(mb[i]), 24, C_MOSI, "Bold", "mm", k=kk)
            S.text(d, (x0 + (b0 + i) * bw + bw * 0.25, 632), str(ib[i]), 24, C_MISO, "Bold", "mm", k=kk)
    k = kin(T, 8.4)
    S.text(d, (380, 752), "out: hex A5", 28, C_MOSI, "Bold", "lm", k=k)
    S.text(d, (620, 752), "back: hex 3C", 28, C_MISO, "Bold", "lm", k=k)
    S.text(d, (1740, 752), "(example bytes · mode 0 · MSB first)", 24, S.DIM, "SemiBold", "rm", k=k)
    S.text(d, (x0 + 0.5 * bw, 270), "CS low = selected", 22, C_CS, "Bold", "lm", k=kin(T, 2.0))

def s_spi_shift(d, t, dur):
    S.chrome(d, "STEP 3 · SPI", "Two shift registers, swapping", "Each side has an 8-bit shift register, joined in a loop. After eight ticks, the bytes have swapped.", t, dur)
    T = tl(t, dur)
    xs = [560 + i * 100 for i in range(8)]
    yt, yb = 380, 620
    xr, xl = 1440, 420
    k = kin(T, 0.3)
    S.text(d, (960, 300), "controller's register", 30, SC, "Bold", "mm", k=k)
    S.text(d, (960, 700), "peripheral's register", 30, S.LINE, "Bold", "mm", k=kin(T, 0.6))
    for i, x in enumerate(xs):
        S.box(d, (x - 46, yt - 46, x + 46, yt + 46), mix(S.PANEL, SC, 0.12), None, 12, 0, k)
        S.box(d, (x - 46, yb - 46, x + 46, yb + 46), mix(S.PANEL, S.LINE, 0.10), None, 12, 0, kin(T, 0.6))
    kr = prog(T, 1.2, 2.2)
    ring = [(xs[7] + 50, yt), (xr, yt), (xr, yb), (xs[7] + 50, yb)]
    ring2 = [(xs[0] - 50, yb), (xl, yb), (xl, yt), (xs[0] - 50, yt)]
    if kr > 0:
        S.line(d, grow(ring, kr), C_MOSI, 6)
        S.line(d, grow(ring2, kr), C_MISO, 6)
    if kr >= 1:
        S.arrow(d, (xr, 470), (xr, 540), C_MOSI, 6)
        S.arrow(d, (xl, 540), (xl, 470), C_MISO, 6)
    S.text(d, (xr + 24, 500), "MOSI", 28, C_MOSI, "Bold", "lm", k=kin(T, 2.0))
    S.text(d, (xl - 24, 500), "MISO", 28, C_MISO, "Bold", "rm", k=kin(T, 2.0))
    # slot positions around the loop (clockwise): top row left->right, down the right, bottom row right->left, up the left
    slots = [(x, yt) for x in xs] + [(x, yb) for x in xs[::-1]]
    def seg(i):
        a, b = slots[i % 16], slots[(i + 1) % 16]
        if i % 16 == 7: return [a, (xr, yt), (xr, yb), b]
        if i % 16 == 15: return [a, (xl, yb), (xl, yt), b]
        return [a, b]
    ticks = clamp((T - 3.0) / 0.62, 0, 8)
    n = int(ticks); f = ease((ticks - n) / 0.7) if n < 8 else 0
    ctrl = [1, 0, 1, 0, 0, 1, 0, 1]   # hex A5
    per = [0, 0, 1, 1, 1, 1, 0, 0]    # hex 3C
    tokens = [(ctrl[7 - i], SC) for i in range(8)] + [(per[i], S.LINE) for i in range(8)]
    # token at slot j starts at position j; MSB sits at the right end of the top row (next out)
    kt = kin(T, 1.0)
    for j, (b, c) in enumerate(tokens):
        s = j + n
        pos = along(seg(s), f) if f > 0 else slots[s % 16]
        S.box(d, (pos[0] - 36, pos[1] - 36, pos[0] + 36, pos[1] + 36), c, None, 10, 0, kt)
        S.text(d, pos, str(b), 36, S.ON_ACCENT, "Bold", "mm", k=kt)
    S.text(d, (960, 770), f"clock ticks: {n} of 8", 30, C_CLK, "Bold", "mm", mono=False, k=kin(T, 2.8))
    if n >= 8:
        stamp(d, (1640, 270), "swapped!", S.HILITE, 34, -7, 1.0, popk(T, 3.0 + 8 * 0.62))

def clock_mode_panel(d, x, y, w, h, mode, k, t):
    cpol, cpha = mode >> 1, mode & 1
    S.box(d, (x, y, x + w, y + h), S.PANEL, None, 20, 0, k)
    S.text(d, (x + w / 2, y + 40), f"Mode {mode}", 36, C_CLK, "Bold", "mm", k=k)
    S.text(d, (x + w / 2, y + 84), f"CPOL {cpol} · CPHA {cpha}", 26, S.TXT, "SemiBold", "mm", k=k)
    U = 7
    ev = [(0, cpol)]
    for i in range(3): ev += [(1.5 + i * 1.6, 1 - cpol), (2.3 + i * 1.6, cpol)]
    lev = levf(ev, U)
    x0, x1, yh, yl = x + 24, x + w - 24, y + 150, y + 230
    wave(d, lev, x0, x1, yl, yh, C_CLK, k, 1.0, 5)
    for i in range(3):
        e = (1.5 + i * 1.6) if cpha == 0 else (2.3 + i * 1.6)
        xe = x0 + e / U * (x1 - x0)
        rising = (cpol == 0) == (cpha == 0)
        blink = 0.6 + 0.4 * math.sin(t * 5 + i)
        S.circle(d, (xe, (yh + yl) / 2), 11, S.HILITE, None, k=k * blink, shadow=False)
    S.text(d, (x + w / 2, y + 290), "rests " + ("LOW" if cpol == 0 else "HIGH"), 26, S.TXT, "SemiBold", "mm", k=k)
    edge = "rising" if ((cpol == 0) == (cpha == 0)) else "falling"
    S.text(d, (x + w / 2, y + 330), f"samples on {edge}", 26, S.TXT, "SemiBold", "mm", k=k)
    S.text(d, (x + w / 2, y + 366), "(1st edge)" if cpha == 0 else "(2nd edge)", 24, S.DIM, "SemiBold", "mm", k=k)

def s_spi_modes(d, t, dur):
    S.chrome(d, "STEP 3 · SPI", "Clock modes must match", "CPOL: does the clock rest low or high? CPHA: sample on the first edge or the second? Four modes.", t, dur)
    T = tl(t, dur)
    for m in range(4):
        a = 0.6 + m * 1.0
        clock_mode_panel(d, 130 + m * 425, 260 + drop(T, a, 60), 390, 410, m, kin(T, a, 0.35), t)
    S.circle(d, (560, 742), 11, S.HILITE, None, k=kin(T, 5.2), shadow=False)
    S.text(d, (585, 742), "= where data is sampled", 28, S.TXT, "SemiBold", "lm", k=kin(T, 5.2))
    S.pill(d, (1360, 742 + drop(T, 6.4, 30)), "controller and chip must agree", 28, S.BAD, kin(T, 6.4, 0.3))

def s_spi_cost(d, t, dur):
    S.chrome(d, "STEP 3 · SPI", "Fast, but wire-hungry", "Push-pull outputs give sharp edges: many MHz. But each chip needs its own CS, and there's no acknowledge.", t, dur)
    T = tl(t, dur)
    k = kin(T, 0.3)
    S.box(d, (130, 250, 900, 790), S.PANEL, None, 24, 0, k)
    S.text(d, (515, 292), "push-pull output", 34, S.TXT, "Bold", "mm", k=k)
    hi = (int(t * 1.6) % 2) == 0
    S.line(d, [(220, 360), (520, 360)], S.BAD, 5, k)
    S.text(d, (230, 340), "supply", 22, S.BAD, "Bold", "lm", k=k)
    ground(d, 370, 690, S.LINE, k)
    S.line(d, [(370, 360), (370, 420)], S.LINE, 5, k)
    S.line(d, [(370, 610), (370, 690)], S.LINE, 5, k)
    # top switch
    S.line(d, [(370, 420), (370 + (0 if hi else 40), 490)], S.HILITE if hi else S.DIM, 6, k)
    S.line(d, [(370, 490), (370, 540)], S.LINE, 5, k)
    S.line(d, [(370, 540), (370 + (40 if hi else 0), 610)], S.HILITE if not hi else S.DIM, 6, k)
    S.circle(d, (370, 515), 9, S.LINE, None, k=k, shadow=False)
    S.line(d, [(370, 515), (520, 515)], S.LINE, 5, k)
    S.text(d, (425, 452), "pushes high", 22, S.DIM, "SemiBold", "lm", k=k)
    S.text(d, (425, 580), "pulls low", 22, S.DIM, "SemiBold", "lm", k=k)
    ev = [(0, 1)]
    for i in range(1, 12): ev.append((i, i % 2 == 0))
    lev = levf([(a, 1 if l else 0) for a, l in ev], 12)
    wave(d, lev, 540, 870, 560, 470, SC, kin(T, 1.0), 1.0, 5)
    S.circle(d, (540, 515), 9, S.LINE, None, k=k, shadow=False)
    S.text(d, (705, 610), "sharp edges", 26, SC, "Bold", "mm", k=kin(T, 1.0))
    S.pill(d, (515, 730 + drop(T, 2.0, 30)), "often many megahertz", 30, SC, kin(T, 2.0, 0.3))
    # right: wire count
    k2 = kin(T, 3.6)
    S.box(d, (1000, 250, 1790, 790), S.PANEL, None, 24, 0, k2)
    S.text(d, (1395, 292), "wires needed", 34, S.TXT, "Bold", "mm", k=k2)
    for r in range(4):
        a = 4.0 + r * 0.7
        kk = kin(T, a, 0.3)
        y = 370 + r * 82
        S.text(d, (1030, y), f"{r + 1} chip" + ("s" if r else ""), 26, S.TXT, "SemiBold", "lm", k=kk)
        for j in range(3 + r + 1):
            c = (C_CLK, C_MOSI, C_MISO)[j] if j < 3 else C_CS
            p = popk(T, a + j * 0.06)
            ptbox(d, 1200 + j * 54, y, 34, 52, c, p, 8)
        S.text(d, (1760, y), str(4 + r), 38, S.TXT, "Bold", "rm", k=kk)
    S.text(d, (1395, 702), "3 shared + one chip select each", 24, S.DIM, "SemiBold", "mm", k=kin(T, 6.8))
    stamp(d, (1395, 752), "no acknowledge", S.BAD, 28, 4, kin(T, 7.8), popk(T, 7.8))

# ---------- STEP 4 · I²C ----------
I2C_DEV = [("sensor", "addr 0x48", 760), ("EEPROM", "addr 0x50", 1060), ("clock chip", "addr 0x68", 1360), ("display", "addr 0x3C", 1660)]
def i2c_bus(d, T, t, k, ysda=430, yscl=500, x0=250, x1=1780, st=None, devs=None, ytop=300, chip_y=640, call=None):
    st = st or S
    devs = devs if devs is not None else I2C_DEV
    st.line(d, [(x0 - 40, ytop), (440, ytop)], st.BAD, 5, k)
    st.text(d, (x0 - 40, ytop - 24), "supply", 22, st.BAD, "Bold", "lm", k=k)
    for x, y in ((300, ysda), (380, yscl)):
        resistor(d, x, ytop, y, st.LINE, k, st)
        st.circle(d, (x, y), 7, st.LINE, None, k=k, shadow=False)
    st.text(d, (420, ytop + 60), "pull-up resistors", 22, st.DIM, "Bold", "lm", k=k)
    st.line(d, [(x0 + 40, ysda), (x1, ysda)], IC, 6, k)
    st.line(d, [(x0 + 40, yscl), (x1, yscl)], mix(IC, st.TXT, 0.45), 6, k)
    st.text(d, (x1, ysda - 24), "SDA (data)", 24, IC, "Bold", "rm", k=k)
    st.text(d, (x1, yscl + 26), "SCL (clock)", 24, mix(IC, st.TXT, 0.45), "Bold", "rm", k=k)

def s_i2c_bus(d, t, dur):
    S.chrome(d, "STEP 4 · I²C", "Two wires, one roll call", "Just two wires, SDA and SCL, shared by every chip. Each has an address, and only the one called answers.", t, dur)
    T = tl(t, dur)
    ysda, yscl = 430, 500
    i2c_bus(d, T, t, kin(T, 0.4), ysda, yscl)
    # controller
    S.chip(d, 380, 600 + drop(T, 0.8), 260, 120, "Controller", None, IC, kin(T, 0.8), pins=False)
    for xx, yy in ((470, ysda), (550, yscl)):
        S.line(d, [(xx, 600), (xx, yy)], IC if yy == ysda else mix(IC, S.TXT, 0.45), 4, kin(T, 0.8))
        S.circle(d, (xx, yy), 7, IC, None, k=kin(T, 0.8), shadow=False)
    calls = [1, 0, 3]
    ci = calls[int(t / 3.2) % 3] if T > 6.5 else 1
    for i, (n, ad, cx) in enumerate(I2C_DEV):
        a = 1.6 + i * 0.5
        kk = kin(T, a)
        if kk <= 0.01: continue
        oy = drop(T, a)
        lit = (i == ci and T > 4.8)
        S.chip(d, cx - 125, 610 + oy, 250, 110, n, ad, IC if lit else S.LINE, kk, pins=False)
        for xx, yy in ((cx - 40, ysda), (cx + 40, yscl)):
            S.line(d, [(xx, 610 + oy), (xx, yy)], IC if yy == ysda else mix(IC, S.TXT, 0.45), 4, kk)
            S.circle(d, (xx, yy), 7, IC, None, k=kk, shadow=False)
    if T > 4.2:
        n, ad, cx = I2C_DEV[ci]
        S.pill(d, (700, 330 + drop(T, 4.2, 30)), f"calling {ad[5:]}...", 28, S.HILITE, kin(T, 4.2, 0.3))
        ph = (t % 3.2) / 3.2
        if ph < 0.55:
            dot(d, (470 + (cx - 40 - 470) * (ph / 0.55), ysda), 11, S.HILITE, kin(T, 4.2))
        if T > 4.8 and ph > 0.45:
            stamp(d, (cx, 345), "here!", S.GOOD, 30, -6, 1.0, pop(ph, 0.45, 0.6))

def s_i2c_opendrain(d, t, dur):
    S.chrome(d, "STEP 4 · I²C", "Pull low, never push high", "Open drain: chips can only pull the line low, or let go. A pull-up resistor brings it back high.", t, dur)
    T = tl(t, dur)
    k = kin(T, 0.3)
    yl = 440
    S.line(d, [(200, 290), (420, 290)], S.BAD, 5, k)
    S.text(d, (210, 268), "supply", 22, S.BAD, "Bold", "lm", k=k)
    resistor(d, 300, 290, yl, S.LINE, k)
    S.text(d, (330, 350), "pull-up", 24, S.TXT, "Bold", "lm", k=k)
    S.text(d, (330, 380), "e.g. 4.7 kΩ", 24, S.DIM, "SemiBold", "lm", k=k)
    # schedule of who pulls low (loops every 8 s)
    sched = [(0.0, (0, 0)), (1.6, (1, 0)), (3.0, (0, 0)), (4.2, (0, 1)), (5.4, (1, 1)), (6.4, (0, 0))]
    def state(tt):
        tt = tt % 8.0; s = (0, 0)
        for a, v in sched:
            if tt >= a: s = v
        return s
    live = T > 3.0
    tt = (t - 0.0) if live else 0.0
    s1, s2 = state(tt) if live else (0, 0)
    low = (s1 or s2)
    lc = S.HILITE if not low else S.LINE
    S.line(d, [(300, yl), (1080, yl)], lc, 8, kin(T, 0.8))
    S.text(d, (1080, yl - 30), "the line: " + ("LOW" if low else "HIGH"), 28, lc, "Bold", "rm", k=kin(T, 3.0))
    for i, (x, on) in enumerate(((560, s1), (860, s2))):
        a = 1.2 + i * 0.6
        kk = kin(T, a)
        S.circle(d, (x, yl), 8, S.LINE, None, k=kk, shadow=False)
        S.line(d, [(x, yl), (x, 540)], S.LINE, 5, kk)
        S.line(d, [(x, 540), (x + (0 if on else 46), 610)], IC if on else S.DIM, 7, kk)
        S.line(d, [(x, 620), (x, 660)], S.LINE, 5, kk)
        ground(d, x, 664, S.LINE, kk)
        S.text(d, (x + 30, 520), f"chip {i + 1}", 26, IC, "Bold", "lm", k=kk)
        S.text(d, (x + 60, 590), "pulling" if on else "let go", 22, IC if on else S.DIM, "SemiBold", "lm", k=kk)
    # trace of the line voltage over the last few seconds
    xy = (1160, 260, 1790, 640)
    scope(d, xy, kin(T, 2.0), (6, 3))
    if live:
        win, n = 6.0, 200
        v, pts = 1.0, []
        t0 = max(0.0, tt - win)
        steps = int((tt - t0) / 0.01)
        v = 1.0
        hist = []
        for i in range(steps + 1):
            ti = t0 + i * 0.01
            a, b = state(ti)
            if a or b: v = 0.0
            else: v += (1 - v) * (1 - math.exp(-0.01 / 0.12))
            hist.append((ti, v))
        for ti, vv in hist[::2]:
            x = 1190 + (ti - (tt - win)) / win * 570
            pts.append((x, 590 - vv * 260))
        if len(pts) > 1: S.line(d, pts, S.HILITE, 5)
    S.text(d, (1475, 610), "line voltage over time", 22, S.DIM, "Bold", "mm", k=kin(T, 2.0))
    S.text(d, (1475, 690), "rises gently: the resistor does it", 26, S.TXT, "SemiBold", "mm", k=kin(T, 6.0))
    S.pill(d, (690, 752 + drop(T, 7.4, 30)), "any chip pulls low = line is low. No fights.", 28, IC, kin(T, 7.4, 0.3))

def i2c_addr_lev():
    """START, address 0x48 (1001000) + W(0), then ACK, MSB first. Returns sda, scl, U, slot0."""
    U, s0 = 11.6, 1.5
    bits = [1, 0, 0, 1, 0, 0, 0, 0]     # 7-bit address + R/W
    ev = [(0, 1), (1.0, 0)]             # START: SDA falls while SCL high
    for i, b in enumerate(bits): ev.append((s0 + i + 0.12, b))
    ev += [(s0 + 8 + 0.12, 0), (s0 + 9 + 0.12, 1)]   # ACK slot (driven by the peripheral), then released
    sda = levf(ev, U)
    cev = [(0, 1), (1.5, 0)]
    for i in range(9): cev += [(s0 + i + 0.5, 1), (s0 + i + 1.0, 0)]
    scl = levf(cev, U)
    return sda, scl, U, s0, bits

def s_i2c_start(d, t, dur):
    S.chrome(d, "STEP 4 · I²C", "Start, address, acknowledge", "START: SDA falls while SCL is high. A 7-bit address plus read/write. On clock 9, the chip pulls SDA low: ACK.", t, dur)
    T = tl(t, dur)
    xy = (140, 240, 1780, 800)
    scope(d, xy, kin(T, 0.3), (12, 4))
    sda, scl, U, s0, bits = i2c_addr_lev()
    x0, x1 = 300, 1740
    bw = (x1 - x0) / U
    rv = prog(T, 1.0, 7.6)
    S.text(d, (170, 380), "SDA", 30, IC, "Bold", "lm", k=kin(T, 0.5))
    S.text(d, (170, 560), "SCL", 30, mix(IC, S.TXT, 0.45), "Bold", "lm", k=kin(T, 0.5))
    # slot tints
    nrev = rv * U
    tints = [(s0 + i, s0 + i + 1, S.HILITE if i < 7 else (S.EXTRA if i == 7 else S.GOOD)) for i in range(9)]
    for i, (a, b, c) in enumerate(tints):
        if nrev > a:
            S.box(d, (x0 + a * bw + 3, 300, x0 + b * bw - 3, 640), mix(S.PANEL, c, 0.14), None, 8, 0, prog(nrev, a, a + 0.5), shadow=False)
    wave(d, sda, x0, x1, 420, 340, IC, kin(T, 0.6), rv, 6, tau=5, u1=(s0 + 8 + 0.1) / U)
    wave(d, sda, x0, x1, 420, 340, S.GOOD, kin(T, 0.6), rv, 7, tau=5, u0=(s0 + 8 + 0.1) / U, u1=(s0 + 9.1) / U)
    wave(d, sda, x0, x1, 420, 340, IC, kin(T, 0.6), rv, 6, tau=5, u0=(s0 + 9.1) / U)
    wave(d, scl, x0, x1, 600, 520, mix(IC, S.TXT, 0.45), kin(T, 0.6), rv, 6, tau=5)
    labels = [str(b) for b in bits[:7]] + ["W=0", "ACK"]
    for i, s in enumerate(labels):
        if nrev > s0 + i + 0.5:
            c = S.HILITE if i < 7 else (S.EXTRA if i == 7 else S.GOOD)
            S.text(d, (x0 + (s0 + i + 0.5) * bw, 470), s, 26, c, "Bold", "mm", k=prog(nrev, s0 + i + 0.5, s0 + i + 0.9))
    # START marker
    ks = kin(T, 2.0)
    S.circle(d, (x0 + 1.0 * bw, 380), 34 * max(0.01, popk(T, 2.0)), None, S.BAD, 5, k=ks, shadow=False)
    S.text(d, (x0 + 1.0 * bw, 680), "START", 28, S.BAD, "Bold", "mm", k=ks)
    S.text(d, (x0 + 1.0 * bw, 714), "SDA falls,", 22, S.DIM, "SemiBold", "mm", k=ks)
    S.text(d, (x0 + 1.0 * bw, 742), "SCL high", 22, S.DIM, "SemiBold", "mm", k=ks)
    ka = kin(T, 5.0)
    S.text(d, (x0 + (s0 + 3.5) * bw, 690), "address: hex 48 (example)", 28, S.HILITE, "Bold", "mm", k=ka)
    S.text(d, (x0 + (s0 + 7.5) * bw, 690), "0 = write", 24, S.EXTRA, "Bold", "mm", k=kin(T, 6.0))
    S.text(d, (x0 + (s0 + 7.5) * bw, 724), "1 = read", 24, S.EXTRA, "Bold", "mm", k=kin(T, 6.0))
    kk = kin(T, 7.8)
    S.text(d, (x0 + (s0 + 8.5) * bw, 752), "the chip pulls", 22, S.GOOD, "Bold", "mm", k=kk)
    S.text(d, (x0 + (s0 + 8.5) * bw, 778), "SDA low: ACK", 22, S.GOOD, "Bold", "mm", k=kk)
    S.text(d, (x0 + (s0 + 8.5) * bw, 270), "clock 9", 22, S.GOOD, "Bold", "mm", k=kk)

def s_i2c_stop(d, t, dur):
    S.chrome(d, "STEP 4 · I²C", "Data, then stop", "Data bytes follow, each with its own ACK. No pull-down means NACK. STOP: SDA rises while SCL is high.", t, dur)
    T = tl(t, dur)
    xy = (140, 240, 1780, 800)
    scope(d, xy, kin(T, 0.3), (12, 4))
    U, s0 = 12.0, 0.4
    bits = [0, 0, 1, 0, 1, 0, 1, 0]     # example data byte hex 2A
    ev = [(0, 0)]
    for i, b in enumerate(bits): ev.append((s0 + i + 0.12, b))
    ev += [(s0 + 8 + 0.12, 0), (s0 + 9 + 0.12, 0), (10.9, 1)]       # ACK, then hold low, STOP rise while SCL high
    sda = levf(ev, U)
    cev = [(0, 0)]
    for i in range(9): cev += [(s0 + i + 0.5, 1), (s0 + i + 1.0, 0)]
    cev += [(10.4, 1)]
    scl = levf(cev, U)
    x0, x1 = 300, 1740
    bw = (x1 - x0) / U
    rv = prog(T, 0.8, 7.0)
    nrev = rv * U
    S.text(d, (170, 380), "SDA", 30, IC, "Bold", "lm", k=kin(T, 0.5))
    S.text(d, (170, 560), "SCL", 30, mix(IC, S.TXT, 0.45), "Bold", "lm", k=kin(T, 0.5))
    for i in range(9):
        a = s0 + i
        c = S.ACCENT if i < 8 else S.GOOD
        if nrev > a:
            S.box(d, (x0 + a * bw + 3, 300, x0 + (a + 1) * bw - 3, 640), mix(S.PANEL, c, 0.12), None, 8, 0, prog(nrev, a, a + 0.5), shadow=False)
    ua = (s0 + 8.1) / U; ub = (s0 + 9.1) / U
    wave(d, sda, x0, x1, 420, 340, IC, kin(T, 0.6), rv, 6, tau=5, u1=ua)
    wave(d, sda, x0, x1, 420, 340, S.GOOD, kin(T, 0.6), rv, 7, tau=5, u0=ua, u1=ub)
    wave(d, sda, x0, x1, 420, 340, IC, kin(T, 0.6), rv, 6, tau=5, u0=ub)
    wave(d, scl, x0, x1, 600, 520, mix(IC, S.TXT, 0.45), kin(T, 0.6), rv, 6, tau=5)
    for i, b in enumerate(bits):
        if nrev > s0 + i + 0.5:
            S.text(d, (x0 + (s0 + i + 0.5) * bw, 470), str(b), 26, IC, "Bold", "mm", k=prog(nrev, s0 + i + 0.5, s0 + i + 0.9))
    S.text(d, (x0 + (s0 + 4) * bw, 690), "data byte (example: hex 2A)", 28, IC, "Bold", "mm", k=kin(T, 4.0))
    # NACK ghost
    kn = kin(T, 5.4)
    if kn > 0.01:
        xa, xb = x0 + (s0 + 8.15) * bw, x0 + (s0 + 9.1) * bw
        xx = xa
        while xx < xb:
            S.line(d, [(xx, 340), (min(xx + 12, xb), 340)], S.BAD, 4, kn); xx += 22
        S.text(d, ((xa + xb) / 2, 300), "NACK if", 20, S.BAD, "Bold", "mm", k=kn)
        S.text(d, ((xa + xb) / 2, 322), "left high", 20, S.BAD, "Bold", "mm", k=kn)
    S.text(d, (x0 + (s0 + 8.5) * bw, 690), "ACK", 26, S.GOOD, "Bold", "mm", k=kin(T, 5.0))
    ks = kin(T, 7.0)
    S.circle(d, (x0 + 10.9 * bw, 380), 34 * max(0.01, popk(T, 7.0)), None, S.BAD, 5, k=ks, shadow=False)
    S.text(d, (x0 + 10.9 * bw, 680), "STOP", 28, S.BAD, "Bold", "mm", k=ks)
    S.text(d, (x0 + 10.9 * bw, 714), "SDA rises,", 22, S.DIM, "SemiBold", "mm", k=ks)
    S.text(d, (x0 + 10.9 * bw, 742), "SCL high", 22, S.DIM, "SemiBold", "mm", k=ks)
    S.text(d, (960, 768), "rule: SDA only changes while SCL is low (except START and STOP)", 24, S.TXT, "SemiBold", "mm", k=kin(T, 8.4))

def s_i2c_speed(d, t, dur):
    S.chrome(d, "STEP 4 · I²C", "Gentle edges, and clock stretching", "Pull-ups make rounded edges: 100 kHz and 400 kHz are standard. A chip can hold SCL low to say: wait.", t, dur)
    T = tl(t, dur)
    # left: edge shapes
    k = kin(T, 0.3)
    S.box(d, (130, 250, 900, 790), S.PANEL, None, 24, 0, k)
    S.text(d, (515, 292), "why I²C is gentler", 34, S.TXT, "Bold", "mm", k=k)
    ev = [(0, 0)] + [(i, (i % 2)) for i in range(1, 8)]
    lev = levf(ev, 8)
    S.text(d, (170, 350), "push-pull (like SPI): sharp", 24, SC, "Bold", "lm", k=kin(T, 0.8))
    wave(d, lev, 170, 860, 470, 380, SC, kin(T, 0.8), prog(T, 0.8, 2.4), 5)
    S.text(d, (170, 520), "open drain + pull-up: rounded", 24, IC, "Bold", "lm", k=kin(T, 2.4))
    wave(d, lev, 170, 860, 640, 550, IC, kin(T, 2.4), prog(T, 2.4, 4.0), 5, tau=22)
    for i, (s, c) in enumerate((("standard: 100 kHz", IC), ("fast: 400 kHz", IC))):
        a = 4.2 + i * 0.5
        S.pill(d, (330 + i * 360, 712 + drop(T, a, 30)), s, 26, c, kin(T, a, 0.3))
    S.text(d, (515, 768), "(faster modes exist too)", 22, S.DIM, "SemiBold", "mm", k=kin(T, 5.2))
    # right: clock stretching
    k2 = kin(T, 5.6)
    S.box(d, (1000, 250, 1790, 790), S.PANEL, None, 24, 0, k2)
    S.text(d, (1395, 292), "clock stretching", 34, S.TXT, "Bold", "mm", k=k2)
    cev = [(0, 1), (0.5, 0), (1.0, 1), (1.5, 0), (4.5, 1), (5.0, 0), (5.5, 1), (6.0, 0)]
    clev = levf(cev, 6.5)
    xa, xb = 1040, 1750
    bw = (xb - xa) / 6.5
    kb = kin(T, 7.0)
    S.box(d, (xa + 2.0 * bw, 360, xa + 4.5 * bw, 560), mix(S.PANEL, S.HILITE, 0.2), None, 10, 0, kb, shadow=False)
    S.text(d, (xa + 3.25 * bw, 390), "chip holds SCL low", 24, S.HILITE, "Bold", "mm", k=kb)
    S.text(d, (xa + 3.25 * bw, 420), "\"wait for me\"", 24, S.HILITE, "Bold", "mm", k=kb)
    # where the controller wanted to release (dashed ghost)
    kg = kin(T, 7.6)
    if kg > 0.01:
        xx = xa + 2.0 * bw
        for yy in range(450, 540, 16): S.line(d, [(xx, yy), (xx, yy + 8)], S.DIM, 3, kg)
        S.text(d, (xx - 10, 596), "controller wanted", 20, S.DIM, "SemiBold", "rm", k=kg)
        S.text(d, (xx - 10, 620), "to go high here", 20, S.DIM, "SemiBold", "rm", k=kg)
    wave(d, clev, xa, xb, 540, 460, mix(IC, S.TXT, 0.45), k2, prog(T, 6.0, 8.0), 6, tau=6)
    S.text(d, (xa, 460), "SCL", 24, mix(IC, S.TXT, 0.45), "Bold", "lm", k=k2)
    S.text(d, (1395, 700), "the controller waits until SCL", 26, S.TXT, "SemiBold", "mm", k=kin(T, 8.4))
    S.text(d, (1395, 736), "really goes high, then carries on", 26, S.TXT, "SemiBold", "mm", k=kin(T, 8.4))

# ---------- STEP 5 · HEAD TO HEAD ----------
def contender_cols(d, T, a0=0.3):
    out = []
    for i, (n, c) in enumerate((("UART", UC), ("SPI", SC), ("I²C", IC))):
        a = a0 + i * 0.3
        k = kin(T, a, 0.35)
        cx = 400 + i * 560
        oy = drop(T, a, 50)
        S.box(d, (cx - 250, 250 + oy, cx + 250, 790 + oy), S.PANEL, None, 26, 0, k)
        S.box(d, (cx - 250, 250 + oy, cx + 250, 326 + oy), c, None, 26, 0, k, shadow=False)
        S.text(d, (cx, 288 + oy), n, 46, S.ON_ACCENT, "Bold", "mm", k=k)
        out.append((cx, c, k, oy))
    return out

def s_round_wires(d, t, dur):
    S.chrome(d, "STEP 5 · HEAD TO HEAD", "Round 1: wires", "UART: two per link. SPI: three shared, plus a chip select each. I²C: two, however many chips. Plus ground.", t, dur)
    T = tl(t, dur)
    cols = contender_cols(d, T)
    flow = (t * 0.5) % 1
    # UART: two chips, two crossed wires
    cx, c, k, oy = cols[0]
    if T > 1.4:
        kk = kin(T, 1.4)
        S.box(d, (cx - 210, 400, cx - 120, 520), S.LINE, None, 10, 0, kk)
        S.box(d, (cx + 120, 400, cx + 210, 520), S.LINE, None, 10, 0, kk)
        S.line(d, [(cx - 120, 430), (cx - 40, 430), (cx + 40, 490), (cx + 120, 490)], c, 5, kk)
        S.line(d, [(cx + 120, 430), (cx + 40, 430), (cx - 40, 490), (cx - 120, 490)], c, 5, kk)
        dot(d, along([(cx - 120, 430), (cx - 40, 430), (cx + 40, 490), (cx + 120, 490)], flow), 7, S.HILITE, kk)
    # SPI: controller + 2 chips
    cx, c, k, oy = cols[1]
    if T > 3.0:
        kk = kin(T, 3.0)
        S.box(d, (cx - 220, 380, cx - 140, 560), c, None, 10, 0, kk)
        for j, yy in enumerate((400, 500)):
            S.box(d, (cx + 130, yy, cx + 220, yy + 60), S.LINE, None, 10, 0, kk)
        for j in range(3):
            y = 400 + j * 14
            col = (C_CLK, C_MOSI, C_MISO)[j]
            S.line(d, [(cx - 140, y + 6), (cx + 60 + j * 14, y + 6), (cx + 60 + j * 14, 520 + j * 10), (cx + 130, 520 + j * 10)], col, 3, kk)
            S.line(d, [(cx + 60 + j * 14, 420 + j * 10), (cx + 130, 420 + j * 10)], col, 3, kk)
        S.line(d, [(cx - 140, 520), (cx - 20, 520), (cx - 20, 450), (cx + 130, 450)], C_CS, 4, kk)
        S.line(d, [(cx - 140, 545), (cx + 0, 545), (cx + 0, 550), (cx + 130, 550)], C_CS, 4, kk)
    # I2C: two lines, 4 chips
    cx, c, k, oy = cols[2]
    if T > 4.6:
        kk = kin(T, 4.6)
        S.line(d, [(cx - 220, 420), (cx + 220, 420)], c, 5, kk)
        S.line(d, [(cx - 220, 450), (cx + 220, 450)], mix(c, S.TXT, 0.45), 5, kk)
        for j in range(4):
            x = cx - 165 + j * 110
            S.line(d, [(x - 12, 420), (x - 12, 500)], c, 3, kk)
            S.line(d, [(x + 12, 450), (x + 12, 500)], mix(c, S.TXT, 0.45), 3, kk)
            S.box(d, (x - 40, 500, x + 40, 560), S.LINE, None, 10, 0, kk)
    # scores
    for i, (big, sub) in enumerate((("2", "TX + RX, per link"), ("3 + 1", "+ one CS per chip"), ("2", "shared by every chip"))):
        cx, c, k, oy = cols[i]
        a = 2.0 + i * 1.6
        p = popk(T, a)
        if p > 0.02:
            S.circle(d, (cx, 655), 62 * p, c, None, k=kin(T, a, 0.3))
            S.text(d, (cx, 655), big, 46 if len(big) < 3 else 38, S.ON_ACCENT, "Bold", "mm", k=kin(T, a, 0.3))
        S.text(d, (cx, 752), sub, 28, S.TXT, "SemiBold", "mm", k=kin(T, a + 0.3))
    S.pill(d, (1450, 150 + drop(T, 7.0, 20)), "all three also need a common ground", 26, S.LINE, kin(T, 7.0, 0.3))

def s_round_speed(d, t, dur):
    S.chrome(d, "STEP 5 · HEAD TO HEAD", "Round 2: speed", "I²C: 100 or 400 kHz. UART: often 9600 to 115 200 baud, some faster. SPI: often many megahertz. SPI wins.", t, dur)
    T = tl(t, dur)
    xa, xb = 520, 1720
    lo, hi = 3, 8                               # 1 k .. 100 M bits per second (log scale)
    X = lambda v: xa + (math.log10(v) - lo) / (hi - lo) * (xb - xa)
    k = kin(T, 0.3)
    S.line(d, [(xa, 700), (xb, 700)], S.LINE, 4, k)
    for v, s in ((1e3, "1 k"), (1e4, "10 k"), (1e5, "100 k"), (1e6, "1 M"), (1e7, "10 M"), (1e8, "100 M")):
        S.line(d, [(X(v), 692), (X(v), 712)], S.LINE, 4, k)
        S.text(d, (X(v), 738), s, 26, S.DIM, "Bold", "mm", k=k)
    S.text(d, (xb, 774), "bits per second, roughly (log scale)", 22, S.DIM, "SemiBold", "rm", k=k)
    rows = [("I²C", IC, 1e5, 4e5, 1e6, "100 k or 400 kHz", 1.2),
            ("UART", UC, 9600, 115200, 1e6, "often 9 600 to 115 200 baud", 3.2),
            ("SPI", SC, 1e6, 2e7, 5e7, "often many megahertz", 5.2)]
    for i, (n, c, a, b, ext, lab, st) in enumerate(rows):
        y = 330 + i * 125
        kk = kin(T, st, 0.3)
        S.text(d, (xa - 40, y), n, 44, c, "Bold", "rm", k=kk)
        g = prog(T, st + 0.2, st + 1.2)
        if g > 0:
            x0 = X(a); x1 = X(b); x2 = X(ext)
            S.box(d, (x0, y - 18, x0 + (x2 - x0) * g, y + 18), mix(S.PANEL, c, 0.35), None, 18, 0, 1.0, shadow=False)
            S.box(d, (x0, y - 26, x0 + (x1 - x0) * g, y + 26), c, None, 20, 0, 1.0)
            S.text(d, (x0, y + 52), lab, 26, c, "Bold", "lm", k=prog(T, st + 0.8, st + 1.2))
    S.text(d, (xa - 160, 690), "(typical ranges,", 22, S.DIM, "SemiBold", "mm", k=kin(T, 6.6))
    S.text(d, (xa - 160, 716), "not hard limits)", 22, S.DIM, "SemiBold", "mm", k=kin(T, 6.6))
    stamp(d, (1500, 395), "SPI wins this round", SC, 30, -5, kin(T, 7.4), popk(T, 7.4))

def s_round_chips(d, t, dur):
    S.chrome(d, "STEP 5 · HEAD TO HEAD", "Round 3: how many chips?", "UART: two. SPI: a few, one select each. I²C: many, each with its own address. Watch for clashes.", t, dur)
    T = tl(t, dur)
    cols = contender_cols(d, T)
    cx, c, k, oy = cols[0]
    kk = kin(T, 1.2)
    S.box(d, (cx - 190, 420, cx - 80, 520), S.LINE, None, 12, 0, kk)
    S.box(d, (cx + 80, 420, cx + 190, 520), S.LINE, None, 12, 0, kk)
    S.line(d, [(cx - 80, 455), (cx + 80, 455)], c, 5, kk)
    S.line(d, [(cx - 80, 485), (cx + 80, 485)], c, 5, kk)
    S.text(d, (cx, 640), "2", 80, c, "Bold", "mm", k=kin(T, 1.6))
    S.text(d, (cx, 720), "point to point", 28, S.TXT, "SemiBold", "mm", k=kin(T, 1.6))
    cx, c, k, oy = cols[1]
    kk = kin(T, 2.6)
    S.box(d, (cx - 210, 380, cx - 120, 560), c, None, 12, 0, kk)
    for j in range(3):
        y = 380 + j * 66
        p = popk(T, 2.8 + j * 0.3)
        ptbox(d, cx + 160, y + 25, 90, 50, S.LINE, p, 10)
        S.line(d, [(cx - 120, y + 25), (cx + 115, y + 25)], C_CS, 4, kin(T, 2.8 + j * 0.3))
    S.text(d, (cx, 640), "a few", 64, c, "Bold", "mm", k=kin(T, 3.8))
    S.text(d, (cx, 720), "one chip select each", 28, S.TXT, "SemiBold", "mm", k=kin(T, 3.8))
    cx, c, k, oy = cols[2]
    kk = kin(T, 4.6)
    S.line(d, [(cx - 220, 400), (cx + 220, 400)], c, 5, kk)
    S.line(d, [(cx - 220, 420), (cx + 220, 420)], mix(c, S.TXT, 0.45), 5, kk)
    addrs = ["0x48", "0x50", "0x68", "0x3C", "0x48", "0x1E"]
    n = int(prog(T, 4.8, 6.6) * 6 + 0.001)
    clash = T > 6.8
    fixed = T > 8.2
    for j in range(n):
        x = cx - 180 + (j % 3) * 180
        y = 470 if j < 3 else 540
        ad = addrs[j]
        if j == 4 and fixed: ad = "0x49"
        bad = clash and not fixed and (j in (0, 4))
        S.line(d, [(x, 420), (x, y - 22)], S.LINE, 2)
        S.box(d, (x - 68, y - 22, x + 68, y + 22), S.BAD if bad else S.LINE, None, 10, 0, 1.0, shadow=False)
        S.text(d, (x, y), ad, 24, S.ON_ACCENT, "Bold", "mm")
    S.text(d, (cx, 640), "many", 64, c, "Bold", "mm", k=kin(T, 6.0))
    S.text(d, (cx, 720), "each needs its own address", 28, S.TXT, "SemiBold", "mm", k=kin(T, 6.0))
    if clash and not fixed:
        stamp(d, (cx, 590), "clash!", S.BAD, 30, -6, 1.0, popk(T, 6.8))
    if fixed:
        S.text(d, (cx, 760), "many chips: an address pin", 22, S.GOOD, "Bold", "mm", k=kin(T, 8.2))

def icon_pin(d, c, s, col, k):
    x, y = c
    S.circle(d, (x, y - s * 0.25), s * 0.42, col, None, k=k, shadow=False)
    d.polygon([(x - s * 0.36, y - s * 0.05), (x + s * 0.36, y - s * 0.05), (x, y + s * 0.55)], fill=S.fade(col, k))
    S.circle(d, (x, y - s * 0.25), s * 0.16, S.PANEL, None, k=k, shadow=False)

def icon_terminal(d, c, s, col, k, t=0):
    x, y = c
    S.box(d, (x - s * 0.6, y - s * 0.45, x + s * 0.6, y + s * 0.45), S.TXT, None, 8, 0, k, shadow=False)
    S.text(d, (x - s * 0.45, y - s * 0.12), ">_", int(s * 0.32), S.GOOD, "Bold", "lm", mono=True, k=k)
    S.line(d, [(x - s * 0.45, y + s * 0.2), (x + s * 0.2, y + s * 0.2)], S.GOOD, 3, k)

def icon_screen(d, c, s, col, k, t=0):
    x, y = c
    S.box(d, (x - s * 0.62, y - s * 0.42, x + s * 0.62, y + s * 0.42), S.TXT, None, 8, 0, k, shadow=False)
    for i in range(5):
        for j in range(3):
            on = ((i + j + int(t * 3)) % 3) == 0
            S.box(d, (x - s * 0.5 + i * s * 0.2, y - s * 0.3 + j * s * 0.2, x - s * 0.36 + i * s * 0.2, y - s * 0.16 + j * s * 0.2),
                  col if on else mix(S.TXT, col, 0.3), None, 2, 0, k, shadow=False)

def icon_chip(d, c, s, col, k, label=""):
    x, y = c
    for i in range(4):
        px = x - s * 0.36 + i * s * 0.24
        d.rectangle([px - 4, y - s * 0.5, px + 4, y + s * 0.5], fill=S.fade(S.LINE, k))
    S.box(d, (x - s * 0.5, y - s * 0.36, x + s * 0.5, y + s * 0.36), col, None, 8, 0, k, shadow=False)
    if label: S.text(d, (x, y), label, int(s * 0.24), S.ON_ACCENT, "Bold", "mm", k=k)

def icon_wave(d, c, s, col, k, t=0):
    x, y = c
    pts = [(x - s * 0.6 + i * 2, y + s * 0.3 * math.sin((i * 2) / (s * 0.18) + t * 3)) for i in range(int(s * 0.6))]
    S.line(d, pts, col, 4, k)

def icon_thermo(d, c, s, col, k):
    x, y = c
    S.box(d, (x - s * 0.12, y - s * 0.5, x + s * 0.12, y + s * 0.2), S.PANEL, S.LINE, 10, 3, k, shadow=False)
    S.circle(d, (x, y + s * 0.3), s * 0.2, S.BAD, None, k=k, shadow=False)
    S.box(d, (x - s * 0.05, y - s * 0.2, x + s * 0.05, y + s * 0.2), S.BAD, None, 4, 0, k, shadow=False)

def icon_sliders(d, c, s, col, k, t=0):
    x, y = c
    for i in range(3):
        xx = x - s * 0.35 + i * s * 0.35
        S.line(d, [(xx, y - s * 0.45), (xx, y + s * 0.45)], S.LINE, 4, k)
        yy = y + s * 0.3 * math.sin(t * 1.5 + i * 2)
        S.box(d, (xx - 12, yy - 8, xx + 12, yy + 8), col, None, 4, 0, k, shadow=False)

def s_round_uses(d, t, dur):
    S.chrome(d, "STEP 5 · HEAD TO HEAD", "Round 4: where you'll meet them", "UART: GPS modules, debug consoles. SPI: displays, flash, SD cards, fast ADCs. I²C: sensors, EEPROMs, settings.", t, dur)
    T = tl(t, dur)
    cols = contender_cols(d, T)
    uses = [[("GPS module", icon_pin), ("debug console", icon_terminal), ("some radio modules", None)],
            [("displays", icon_screen), ("flash, SD cards", lambda d, c, s, col, k: icon_chip(d, c, s, col, k, "FLASH")),
             ("fast ADCs", icon_wave)],
            [("sensors", icon_thermo), ("small EEPROMs", lambda d, c, s, col, k: icon_chip(d, c, s, col, k, "MEM")),
             ("chip settings", icon_sliders)]]
    for i, items in enumerate(uses):
        cx, c, k, oy = cols[i]
        for j, (lab, ic) in enumerate(items):
            a = 1.4 + i * 2.0 + j * 0.45
            kk = kin(T, a, 0.3)
            y = 410 + j * 130 + drop(T, a, 30)
            p = popk(T, a)
            if ic is not None and p > 0.05:
                try: ic(d, (cx - 150, y), 90 * p, c, kk, t)
                except TypeError: ic(d, (cx - 150, y), 90 * p, c, kk)
            elif p > 0.05:
                S.circle(d, (cx - 150, y), 34 * p, c, None, k=kk, shadow=False)
                for r in (48, 64):
                    d.arc([cx - 150 - r, y - r, cx - 150 + r, y + r], -60, 60, fill=S.fade(c, kk), width=4)
            S.text(d, (cx - 80, y), lab, 30, S.TXT, "SemiBold", "lm", k=kk)

def s_scorecard(d, t, dur):
    S.chrome(d, "STEP 5 · HEAD TO HEAD", "The full scorecard", "Same questions, three answers. No single winner: each one is best at something.", t, dur)
    T = tl(t, dur)
    x0, xl, cw = 170, 520, 410
    y0, rh = 250, 76
    heads = [("UART", UC), ("SPI", SC), ("I²C", IC)]
    for i, (n, c) in enumerate(heads):
        a = 0.3 + i * 0.25
        S.box(d, (xl + i * cw + 6, y0, xl + (i + 1) * cw - 6, y0 + 64), c, None, 16, 0, kin(T, a, 0.3))
        S.text(d, (xl + i * cw + cw / 2, y0 + 32), n, 38, S.ON_ACCENT, "Bold", "mm", k=kin(T, a, 0.3))
    rows = [("wires", ["TX + RX", "3 + one CS each", "2, shared"]),
            ("clock", ["none: agreed baud", "from the controller", "from the controller"]),
            ("speed", ["moderate", "fastest", "gentle"]),
            ("chips", ["2", "a few", "many"]),
            ("direction", ["both at once", "both at once", "one at a time"]),
            ("acknowledge", ["no", "no", "every byte"])]
    sweep = int(t / 1.3) % len(rows) if T > 8.6 else -1
    for r, (n, cells) in enumerate(rows):
        a = 1.2 + r * 1.1
        kk = kin(T, a, 0.35)
        y = y0 + 80 + r * rh
        if kk <= 0.01: continue
        bg = mix(S.PANEL, S.HILITE, 0.18) if r == sweep else S.PANEL
        S.box(d, (x0, y, xl + 3 * cw - 6, y + rh - 8), bg, None, 14, 0, kk, shadow=False)
        S.text(d, (x0 + 24, y + (rh - 8) / 2), n, 30, S.DIM, "Bold", "lm", k=kk)
        for i, s in enumerate(cells):
            S.text(d, (xl + i * cw + cw / 2, y + (rh - 8) / 2 + drop(T, a + i * 0.12, 16)), s, 30, heads[i][1], "Bold", "mm",
                   k=kin(T, a + i * 0.12, 0.3))

# ---------- STEP 6 · WHICH ONE WHEN ----------
def s_which(d, t, dur):
    S.chrome(d, "STEP 6 · WHICH ONE WHEN", "Which one when?", "Two devices, simple link: UART. Speed or lots of data: SPI. Many slow chips, few pins: I²C.", t, dur)
    T = tl(t, dur)
    qs = [("Just two devices, a simple link?", "UART", "GPS module, debug console", UC),
          ("Need speed, or lots of data?", "SPI", "display, flash memory", SC),
          ("Many slow chips, only two pins?", "I²C", "sensors, EEPROM", IC)]
    for i, (q, a_, ex, c) in enumerate(qs):
        a = 0.6 + i * 2.2
        kk = kin(T, a, 0.35)
        y = 300 + i * 160
        oy = drop(T, a, 40)
        S.box(d, (150, y - 62 + oy, 1080, y + 62 + oy), S.PANEL, None, 22, 0, kk)
        S.text(d, (190, y + oy), q, 38, S.TXT, "Bold", "lm", k=kk)
        ka = prog(T, a + 0.7, a + 1.3)
        if ka > 0: S.arrow(d, (1100, y), (1100 + 150 * ka, y), c, 7)
        p = popk(T, a + 1.2)
        if p > 0.02:
            S.box(d, (1280, y - 62 * p, 1280 + 470 * p, y + 62 * p), c, None, 22, 0, min(1, p * 1.5))
            S.text(d, (1300 + 10, y - 16), a_, 44, S.ON_ACCENT, "Bold", "lm", k=kin(T, a + 1.4, 0.3))
            S.text(d, (1300 + 10, y + 30), "e.g. " + ex, 24, S.ON_ACCENT, "SemiBold", "lm", k=kin(T, a + 1.4, 0.3))
    S.pill(d, (960, 768 + drop(T, 8.0, 30)), "often, the chip you choose decides for you", 26, S.LINE, kin(T, 8.0, 0.3))

def s_recap(d, t, dur):
    S.chrome(d, "RECAP", "Three ways to talk", "UART: agreed baud, start and stop bits. SPI: a clock, both ways, a chip select each. I²C: two wires, addresses, ACKs.", t, dur)
    T = tl(t, dur)
    cards = [("UART", UC, mini_uart, ["no clock: agreed baud", "start, 8 data, stop", "LSB first", "point to point"]),
             ("SPI", SC, mini_spi, ["controller's clock", "data both ways at once", "one chip select each", "fastest"]),
             ("I²C", IC, mini_i2c, ["two shared wires", "open drain + pull-ups", "address + ACK", "many chips"])]
    for i, (n, c, fn, lines) in enumerate(cards):
        a = 0.4 + i * 1.6
        k = kin(T, a, 0.35)
        if k <= 0.01: continue
        cx = 400 + i * 560
        oy = drop(T, a, 60)
        S.box(d, (cx - 255, 245 + oy, cx + 255, 800 + oy), S.PANEL, None, 26, 0, k)
        S.box(d, (cx - 255, 245 + oy, cx + 255, 325 + oy), c, None, 26, 0, k, shadow=False)
        S.text(d, (cx, 285 + oy), n, 50, S.ON_ACCENT, "Bold", "mm", k=k)
        fn(d, cx - 200, cx + 200, 410 + oy, 22, c, k, prog(T, a + 0.3, a + 1.8))
        for j, ln in enumerate(lines):
            kk = kin(T, a + 0.6 + j * 0.3, 0.3)
            S.circle(d, (cx - 205, 520 + j * 66 + oy), 9, c, None, k=kk, shadow=False)
            S.text(d, (cx - 182, 520 + j * 66 + oy), ln, 29, S.TXT, "SemiBold", "lm", k=kk)

def s_end(d, t, dur):
    T = tl(t, dur)
    k = kin(T, 0.3, 0.6)
    S.pill(d, (W // 2, 270 + drop(T, 0.3, 30)), "NEXT EPISODE", 30, S.ACCENT, k)
    S.text(d, (W // 2, 380), "How does PWM dim an LED?", 84, S.TXT, "Bold", "mm", k=kin(T, 0.8, 0.6))
    # a little PWM wave + LED whose brightness follows the duty cycle
    duty = 0.2 + 0.6 * (0.5 + 0.5 * math.sin(t * 1.3))
    kw = kin(T, 2.0)
    pts = []
    x0, x1, yh, yl = 520, 1240, 520, 640
    per = 120
    for px in range(0, x1 - x0 + 1, 2):
        ph = (px % per) / per
        pts.append((x0 + px, yh if ph < duty else yl))
    S.line(d, pts, S.HILITE, 6, kw)
    S.text(d, (x0, 680), f"duty: {int(duty * 100)}%", 28, S.DIM, "Bold", "lm", k=kw)
    led = mix(S.PANEL, S.HILITE, duty)
    for r in (110, 90):
        S.circle(d, (1420, 580), r * max(0.01, popk(T, 2.4)), mix(S.BG, S.HILITE, duty * (0.25 if r == 110 else 0.5)), None, k=kw, shadow=False)
    S.circle(d, (1420, 580), 62 * max(0.01, popk(T, 2.4)), led, S.LINE, 4, k=kw)
    S.text(d, (W // 2, 790), "Subscribe so you don't miss it", 40, S.DIM, "SemiBold", "mm", k=kin(T, 3.4))

SCENES = [("01_hook", s_hook, 12), ("02_cover", s_cover, 12),
          ("03_serial", s_serial, 12), ("04_scope", s_scope, 12), ("05_contenders", s_contenders, 12),
          ("06_uart_wires", s_uart_wires, 12), ("07_uart_baud", s_uart_baud, 12), ("08_uart_frame", s_uart_frame, 12),
          ("09_uart_sample", s_uart_sample, 12), ("10_uart_mismatch", s_uart_mismatch, 12), ("11_uart_extras", s_uart_extras, 12),
          ("12_spi_wires", s_spi_wires, 12), ("13_spi_scope", s_spi_scope, 12), ("14_spi_shift", s_spi_shift, 12),
          ("15_spi_modes", s_spi_modes, 12), ("16_spi_cost", s_spi_cost, 12),
          ("17_i2c_bus", s_i2c_bus, 12), ("18_i2c_opendrain", s_i2c_opendrain, 12), ("19_i2c_start", s_i2c_start, 12),
          ("20_i2c_stop", s_i2c_stop, 12), ("21_i2c_speed", s_i2c_speed, 12),
          ("22_round_wires", s_round_wires, 12), ("23_round_speed", s_round_speed, 12), ("24_round_chips", s_round_chips, 12),
          ("25_round_uses", s_round_uses, 12), ("26_scorecard", s_scorecard, 12),
          ("27_which", s_which, 12), ("28_recap", s_recap, 12), ("29_end", s_end, 8)]

NARRATION = {
 "01_hook": "Look at almost any circuit board, and you'll find a little brain chip surrounded by friends: a sensor, a display, some memory, a GPS module. They chat all day over a few thin wires. But how? Usually in one of three languages: you-art, S P I, and I squared C.",
 "02_cover": "Here's the plan. First, a quick lesson in reading an oscilloscope. Then we'll meet our three contenders, and watch each one's signals on the scope. Then we'll score them head to head. And finally: which one should you pick, and when?",
 "03_serial": "Step one: the basics. A chip could send a byte over eight wires at once. That's parallel. But wires cost pins and board space. So most chips send bits one after another down one wire, like carriages on a train. That's serial, and all three contenders work this way.",
 "04_scope": 'To see those bits, we use an oscilloscope. Voltage goes up the screen, and time goes across. On a three point three volt chip, for example, near three point three volts means a one, and near zero means a zero. So every bit is a little step, high or low.',
 "05_contenders": "Meet the contenders! You-art has no clock at all. S P I is fast, with a clock and a select wire. And I squared C uses just two wires, shared by many chips. We'll score all three on wires, clock, speed, how many chips, and typical uses.",
 "06_uart_wires": 'Step two: you-art. Each side has a transmit pin, T X, and a receive pin, R X. The wires cross over: my transmit goes to your receive, and yours to mine. So both can talk at once. Plus a shared ground, so both agree on zero volts.',
 "07_uart_baud": "Here's the twist: there's no clock wire. It's like two people agreeing to speak at the same pace, without a metronome. Both sides are set to the same speed, the baud rate. A common example is one hundred and fifteen thousand, two hundred baud. So each bit lasts about eight point seven microseconds.",
 "08_uart_frame": "Let's send the letter A. That's hex, four one. When idle, the line rests high. Then it drops low for one bit: the start bit. Here it comes! Next, eight data bits, least significant bit first, so the byte arrives backwards. Finally, the line goes high for the stop bit.",
 "09_uart_sample": "How does the receiver read this without a clock? It watches for the falling edge of the start bit. Then it counts ticks on its own faster clock, often sixteen per bit. Eight ticks later, it's in the middle of the start bit. From there, it samples every sixteen ticks.",
 "10_uart_mismatch": 'What if the two sides disagree? Say the receiver runs about twelve percent too fast. Each sample lands a little early, until it reads the wrong bits. Where it expects a high stop bit, it finds a low: a framing error. The speeds usually need to match within a few percent.',
 "11_uart_extras": "An optional parity bit adds a simple error check. A common setting is eight N one: eight data bits, no parity, one stop bit. And on a board, you-art uses the chip's logic levels. The older R S two three two standard uses bigger, inverted voltages, so it needs a converter chip.",
 "12_spi_wires": 'Step three: S P I. Think of a conductor with a baton. The controller drives a clock that everyone follows. Data goes out on M O S I, and back on M I S O, also called C O P I and C I P O. And each chip has its own chip select: a tap on the shoulder.',
 "13_spi_scope": "Here it is on the scope. Chip select drops low, which means: you're selected. Then the controller ticks the clock eight times. On every tick, one bit goes out on M O S I, and one comes back on M I S O. Most chips send the most significant bit first.",
 "14_spi_shift": "Inside, it's simple. Each side holds an eight bit shift register, joined in a loop. Every clock tick pushes everything along by one place. After eight ticks, the two bytes have swapped. That's why S P I is full duplex: sending and receiving are the same action.",
 "15_spi_modes": 'One setting you must get right is the clock mode. Clock polarity says whether the clock rests low or high. Clock phase says whether data is sampled on the first edge of each pulse, or the second. That gives four modes. The controller and the chip must use the same one.',
 "16_spi_cost": "Why is S P I so fast? Its outputs are push pull: they actively drive the line both high and low, so the edges are sharp. Clocks of many megahertz are common. The price? Every extra chip needs another chip select wire. And there's no acknowledge, so nobody confirms they heard.",
 "17_i2c_bus": "Step four: I squared C. Just two wires: S D A for data, and S C L for clock, shared by every chip. So how do you pick one? It's like a classroom roll call. Every chip has an address. The controller calls one out, and only that chip answers: here!",
 "18_i2c_opendrain": "These chips never drive the line high. Their pins are open drain: they can only pull the line down, or let go. A pull up resistor, often a few kilohms, brings the line back high. So if any chip pulls low, the line is low. No fights.",
 "19_i2c_start": "Let's watch a message. First, the start condition: S D A falls while S C L is high. Next, a seven bit address, here hex, four eight, as an example. One more bit means write, or read. On the ninth clock, the chip pulls S D A low: the acknowledge.",
 "20_i2c_stop": 'Data bytes follow, each acknowledged on its own ninth clock. If nobody pulls S D A low, it stays high: a not acknowledge. Then the stop condition: S D A rises while S C L is high. Otherwise, data only changes while the clock is low.',
 "21_i2c_speed": "Because resistors pull the lines up, rising edges are gentle and rounded, and that limits speed. Common speeds are one hundred and four hundred kilohertz, and faster modes exist. And if a chip needs a moment, it can hold the clock low. That's clock stretching: the controller simply waits.",
 "22_round_wires": 'Step five: head to head! Round one, wires. You-art needs two signal wires per link. S P I needs three shared wires, plus a chip select for every chip. I squared C needs just two, however many chips you add. And all three need a common ground.',
 "23_round_speed": 'Round two, speed. I squared C usually runs at one hundred or four hundred kilohertz. You-art often runs between nine thousand six hundred and one hundred and fifteen thousand, two hundred baud, sometimes faster. S P I wins, often at many megahertz.',
 "24_round_chips": 'Round three: how many chips? You-art is point to point: two chips. S P I has one controller and a few chips, one select each. I squared C can host many, if each has its own address. Two identical sensors would clash! But many chips have an address pin to change it.',
 "25_round_uses": 'Round four: where will you meet them? You-art links GPS modules, debug consoles, and some radio modules. S P I drives displays, flash memory, S D cards and fast A D Cs. I squared C connects sensors, small E E prom memories, and chips that need a few settings.',
 "26_scorecard": "Here's the full scorecard. You-art: two wires, no clock, moderate speed, two chips. S P I: more wires, a controller clock, the fastest, a few chips. I squared C: two wires, gentle speeds, many chips, and an acknowledge for every byte.",
 "27_which": 'Step six: which one, when? Two devices and a simple link, like a GPS module? Use you-art. Need speed, or lots of data, like a display? Use S P I. Lots of slow chips, like sensors, and only two pins? Use I squared C. Often, the chip you choose decides for you.',
 "28_recap": "Let's recap! You-art: no clock, an agreed baud rate, a start bit, data least significant bit first, then a stop bit. S P I: a controller clock, data both ways at once, and a chip select for each chip. I squared C: two shared open drain wires, pull ups, addresses and acknowledges.",
 "29_end": "Next episode: how does P W M dim an LED, or control a motor? Subscribe so you don't miss it!",
}
OUTPUT = "uart_vs_spi_vs_i2c_ep5_narrated.mp4"

def render(name, fn, dur): S.render_to("ep5", name, fn, dur)

if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    S.preview("ep5", SCENES)
