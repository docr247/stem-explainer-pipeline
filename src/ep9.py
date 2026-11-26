import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)

# ---------------- helpers ----------------
def phone(d, x, y, w, h, k=1.0):
    """A generic phone outline (no brand)."""
    box(d, (x, y, x + w, y + h), (8, 12, 24), DIM, 40, 4, k)
    box(d, (x + 18, y + 40, x + w - 18, y + h - 40), PANEL, LINE, 16, 2, k)
    d.ellipse([x + w / 2 - 7, y + 15, x + w / 2 + 7, y + 29], fill=fade(LINE, k))

def finger(d, x, y, k=1.0, w=86, length=300):
    """A generic fingertip coming down from above; (x, y) is the tip."""
    if k <= 0: return
    d.rounded_rectangle([x - w / 2, y - length, x + w / 2, y], int(w / 2), fill=fade(mix(BG, AMBER, 0.35), k),
                        outline=fade(AMBER, k), width=4)
    d.arc([x - w / 2 + 16, y - w + 6, x + w / 2 - 16, y - 18], 200, 340, fill=fade(mix(BG, AMBER, 0.7), k), width=3)

def pen(d, x, y, k=1.0, length=320):
    """A generic plastic pen; (x, y) is the tip."""
    if k <= 0: return
    d.polygon([(x, y), (x - 18, y - 50), (x + 18, y - 50)], fill=fade(DIM, k))
    d.rectangle([x - 18, y - 50 - length, x + 18, y - 50], fill=fade(mix(BG, DIM, 0.5), k), outline=fade(DIM, k), width=3)

def tick(d, x, y, s, col, k=1.0):
    d.line([(x - s, y), (x - s / 3, y + s * 0.7), (x + s, y - s * 0.7)], fill=fade(col, k), width=7, joint="curve")

def cross(d, x, y, s, col, k=1.0):
    d.line([x - s, y - s, x + s, y + s], fill=fade(col, k), width=7)
    d.line([x - s, y + s, x + s, y - s], fill=fade(col, k), width=7)

def dashed(d, a, b, col, k=1.0, width=3, dash=14, gap=10):
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    if L == 0: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    s = 0.0
    while s < L:
        e = min(L, s + dash)
        d.line([x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e], fill=fade(col, k), width=width)
        s += dash + gap

# The capacitive grid used in chapters 4 and 5
GX, GY, GW, GH, NR, NC = 560, 330, 800, 500, 8, 12
def node(r, c): return GX + (c + 0.5) * GW / NC, GY + (r + 0.5) * GH / NR

def grid(d, k=1.0, row_hi=None, col_hi=None, dim_rows=1.0, dim_cols=1.0, rowcol=None, colcol=None):
    box(d, (GX - 20, GY - 20, GX + GW + 20, GY + GH + 20), (8, 12, 24), LINE, 14, 2, k)
    for r in range(NR):
        y = GY + (r + 0.5) * GH / NR
        hi = row_hi is not None and r in row_hi
        c = (rowcol or CYAN) if hi else mix(BG, CYAN, 0.45 * dim_rows)
        d.line([GX, y, GX + GW, y], fill=fade(c, k), width=8 if hi else 5)
    for cc in range(NC):
        x = GX + (cc + 0.5) * GW / NC
        hi = col_hi is not None and cc in col_hi
        c = (colcol or PURPLE) if hi else mix(BG, PURPLE, 0.45 * dim_cols)
        d.line([x, GY, x, GY + GH], fill=fade(c, k), width=8 if hi else 5)

def touch_ring(d, x, y, k=1.0, col=AMBER, r=44):
    if k <= 0: return
    d.ellipse([x - r, y - r, x + r, y + r], outline=fade(col, k), width=5)
    d.ellipse([x - r + 14, y - r + 14, x + r - 14, y + r - 14], fill=fade(mix(BG, col, 0.35), k))

def field(fingers, r, c, s=0.75):
    return sum(math.exp(-((r - fr) ** 2 + (c - fc) ** 2) / (2 * s * s)) for fr, fc in fingers)

def heat_col(v):
    v = clamp(v)
    if v < 0.5: return mix(PANEL, CYAN, v * 2 * 0.85)
    return mix(mix(PANEL, CYAN, 0.85), AMBER, (v - 0.5) * 2)

def heatmap(d, fingers, k=1.0, extra=None):
    cw, ch = GW / NC, GH / NR
    box(d, (GX - 20, GY - 20, GX + GW + 20, GY + GH + 20), (8, 12, 24), LINE, 14, 2, k)
    for r in range(NR):
        for c in range(NC):
            v = field(fingers, r, c) + (extra(r, c) if extra else 0)
            x, y = GX + c * cw, GY + r * ch
            d.rounded_rectangle([x + 4, y + 4, x + cw - 4, y + ch - 4], 6, fill=fade(heat_col(v), k))

def plates(d, x0, x1, ytop, ybot, k=1.0):
    d.rectangle([x0, ytop - 14, x1, ytop], fill=fade(CYAN, k))
    d.rectangle([x0, ybot, x1, ybot + 14], fill=fade(PURPLE, k))
    n = 7
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        text(d, (x, ytop - 34), "+", 32, CYAN, "Bold", "mm", k=k)
        text(d, (x, ybot + 40), "−", 32, PURPLE, "Bold", "mm", k=k)
        dashed(d, (x, ytop + 8), (x, ybot - 8), mix(BG, AMBER, 0.8), k, 3, 10, 8)

# ---------------- intro ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "A plastic pen does nothing on your phone. A fingertip works instantly. So what is the screen sensing?", t, dur)
    k = prog(t, 0.2, 0.8)
    phone(d, 340, 250, 360, 620, k)
    phone(d, 1220, 250, 360, 620, k)
    pd = 40 * clamp((t - 0.8) / 0.8)
    pen(d, 520, 380 + pd, k, 200)
    fd = 40 * clamp((t - 2.0) / 0.8)
    finger(d, 1400, 380 + fd, k, 90, 220)
    if t > 1.7:
        kk = prog(t, 1.7, 2.1)
        cross(d, 520, 640, 34, RED, kk)
        text(d, (520, 720), "nothing", 36, RED, "Bold", "mm", k=kk)
    if t > 2.9:
        kk = prog(t, 2.9, 3.3)
        rr = 40 + 30 * clamp((t - 2.9) / 0.8)
        d.ellipse([1400 - rr, 420 - rr, 1400 + rr, 420 + rr], outline=fade(GREEN, kk), width=5)
        text(d, (1400, 720), "touch!", 36, GREEN, "Bold", "mm", k=kk)
    text(d, (960, 560), "?", 120, AMBER, "Bold", "mm", k=prog(t, 3.6, 4.2))

def s_cover(d, t, dur):
    chrome(d, "TODAY", "Resistive vs capacitive", "Two ways to find your finger, side by side: pressing layers together, or sensing your finger's charge.", t, dur)
    items = [("1", "The question", AMBER), ("2", "Resistive: press", AMBER), ("3", "What is capacitance?", CYAN),
             ("4", "Self-capacitance", CYAN), ("5", "Mutual capacitance", PURPLE), ("6", "Head to head", GREEN)]
    for i, (n, s, c) in enumerate(items):
        kk = prog(t, 0.6 + i * 0.5, 1.0 + i * 0.5)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 290 + row * 170
        box(d, (x, y, x + 720, y + 130), PANEL, c, 16, 3, kk)
        d.ellipse([x + 30, y + 30, x + 100, y + 100], fill=fade(mix(BG, c, 0.35), kk), outline=fade(c, kk), width=3)
        text(d, (x + 65, y + 65), n, 40, c, "Bold", "mm", k=kk)
        text(d, (x + 130, y + 65), s, 40, TXT, "Bold", "lm", k=kk)

# ---------------- 1. the question ----------------
def s_where(d, t, dur):
    chrome(d, "STEP 1 · THE QUESTION", "Find one point, fast", "Every touchscreen has one job: report an x and a y, many times a second, so a swipe feels smooth.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 300, 280, 900, 560
    box(d, (x0, y0, x0 + w, y0 + h), PANEL, LINE, 16, 3, k)
    text(d, (x0, y0 - 14), "(0, 0)", 24, DIM, "Medium", "ld", mono=True, k=k)
    u = 0.2 + 0.6 * clamp((t - 1.0) / 5.0)
    v = 0.5 + 0.28 * math.sin(u * 7)
    n = int(clamp((t - 1.0) / 5.0) * 60)
    trail = []
    for i in range(n + 1):
        uu = 0.2 + 0.6 * i / 60
        trail.append((x0 + w * uu, y0 + h * (0.5 + 0.28 * math.sin(uu * 7))))
    for i, p in enumerate(trail[::3]):
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=mix(BG, CYAN, 0.6))
    if t > 1.0:
        px, py = x0 + w * u, y0 + h * v
        touch_ring(d, px, py, prog(t, 1.0, 1.4))
        dashed(d, (px, y0), (px, py - 44), DIM, 1, 2)
        dashed(d, (x0, py), (px - 44, py), DIM, 1, 2)
    k2 = prog(t, 1.4, 2.0)
    box(d, (1300, 380, 1660, 620), (6, 10, 20), GREEN, 16, 3, k2)
    text(d, (1480, 440), f"x = {int(u * 1080)}", 44, GREEN, "Bold", "mm", mono=True, k=k2)
    text(d, (1480, 520), f"y = {int(v * 2400)}", 44, GREEN, "Bold", "mm", mono=True, k=k2)
    text(d, (1480, 660), "pixels (example)", 26, DIM, "Medium", "mm", k=k2)

def s_two(d, t, dur):
    chrome(d, "STEP 1 · THE QUESTION", "Two contenders", "Resistive screens wait for a press. Capacitive screens sense your finger, with no pressure at all.", t, dur)
    for i, (name, sub, col, st) in enumerate([("RESISTIVE", "press two layers together", AMBER, 0.5),
                                               ("CAPACITIVE", "sense your finger's charge", CYAN, 1.6)]):
        kk = prog(t, st, st + 0.6)
        x = 220 + i * 800
        box(d, (x, 300, x + 680, 780), PANEL, col, 20, 4, kk)
        text(d, (x + 340, 380), name, 56, col, "Bold", "mm", k=kk)
        text(d, (x + 340, 450), sub, 32, TXT, "Medium", "mm", k=kk)
        if i == 0:
            # two layers, one bent down
            d.line([x + 120, 600, x + 560, 600], fill=fade(CYAN, kk), width=6)
            pts = [(x + 120 + j * 4.4, 560 + 34 * math.exp(-((j - 50) / 14) ** 2)) for j in range(101)]
            d.line(pts, fill=fade(AMBER, kk), width=6)
            pen(d, x + 340, 590, kk, 70)
        else:
            for r in range(3):
                d.line([x + 140, 560 + r * 50, x + 540, 560 + r * 50], fill=fade(mix(BG, CYAN, 0.6), kk), width=5)
            for c in range(5):
                d.line([x + 180 + c * 80, 530, x + 180 + c * 80, 690], fill=fade(mix(BG, PURPLE, 0.6), kk), width=5)
            touch_ring(d, x + 340, 610, kk, AMBER, 40)
    text(d, (W // 2, 540), "VS", 64, TXT, "Bold", "mm", k=prog(t, 1.2, 1.6))

# ---------------- 2. resistive ----------------
RX0, RX1 = 300, 1560
def stack(d, k, press=0.0, px=900, show_labels=True):
    """Cross-section of a resistive screen. press 0..1 bends the top film at px."""
    def bend(x): return press * 52 * math.exp(-((x - px) / 130) ** 2)
    top = [(x, 420 + bend(x)) for x in range(RX0, RX1 + 1, 6)]
    coat = [(x, 436 + bend(x)) for x in range(RX0, RX1 + 1, 6)]
    d.line(top, fill=fade(mix(BG, DIM, 0.8), k), width=16)
    d.line(coat, fill=fade(CYAN, k), width=5)
    for x in range(RX0 + 60, RX1, 120):
        if abs(x - px) > 150 or press < 0.2:
            d.ellipse([x - 9, 458, x + 9, 476], fill=fade(DIM, k))
    d.line([RX0, 490, RX1, 490], fill=fade(PURPLE, k), width=5)
    d.rectangle([RX0, 494, RX1, 570], fill=fade(PANEL, k), outline=fade(LINE, k), width=2)
    d.rectangle([RX0, 600, RX1, 660], fill=fade(mix(BG, GREEN, 0.18), k), outline=fade(LINE, k), width=2)
    if show_labels:
        for (y, ly, s, c) in [(420, 330, "flexible top film", DIM), (436, 380, "conductive coating", CYAN),
                              (467, 440, "spacer dots", DIM), (490, 500, "conductive coating", PURPLE),
                              (535, 560, "glass", DIM), (630, 630, "display", GREEN)]:
            d.line([RX1 + 4, y, RX1 + 30, ly], fill=fade(c, k), width=2)
            text(d, (RX1 + 40, ly), s, 26, c, "Bold", "lm", k=k)

def s_layers(d, t, dur):
    chrome(d, "STEP 2 · RESISTIVE", "Two layers, a tiny gap", "A flexible film over glass. Both have a see-through conductive coating. Spacer dots keep them apart.", t, dur)
    stack(d, prog(t, 0.2, 1.0))
    k = prog(t, 2.5, 3.1)
    d.line([1100, 436, 1100, 490], fill=fade(AMBER, k), width=3)
    text(d, (1120, 300), "tiny gap: normally no contact", 30, AMBER, "Bold", "lm", k=k)
    arrow(d, (1240, 320), (1110, 450), AMBER, 3, k)

def s_press(d, t, dur):
    chrome(d, "STEP 2 · RESISTIVE", "Press, and they touch", "Push with a finger, a pen or a nail. The film bends, and the two coatings meet at that one spot.", t, dur)
    press = clamp((t - 1.0) / 1.2)
    stack(d, 1.0, ease(press), 900, show_labels=False)
    finger(d, 900, 404 + 52 * ease(press), prog(t, 0.2, 0.6), 90, 220)
    if press >= 1:
        kk = prog(t, 2.3, 2.8)
        rr = 18 + 10 * math.sin(t * 6)
        d.ellipse([900 - rr, 489 - rr, 900 + rr, 489 + rr], outline=fade(GREEN, kk), width=4)
        text(d, (1000, 720), "contact at one point", 36, GREEN, "Bold", "lm", k=kk)
        arrow(d, (990, 720), (910, 520), GREEN, 4, kk)

PX0, PY0, PW, PH = 360, 300, 980, 480
def gradient(d, x0, y0, w, h, k, horizontal=True):
    n = 60
    for i in range(n):
        u = i / n
        c = mix(PANEL, AMBER, 0.12 + 0.5 * u)
        if horizontal: d.rectangle([x0 + w * u, y0, x0 + w * (i + 1) / n, y0 + h], fill=fade(c, k))
        else: d.rectangle([x0, y0 + h * u, x0 + w, y0 + h * (i + 1) / n], fill=fade(c, k))

def s_divider(d, t, dur):
    chrome(d, "STEP 2 · RESISTIVE", "A voltage that rises evenly", "Put 3.3 V across the top coating. The touch point picks up the voltage at that spot: here, 1.1 V.", t, dur)
    k = prog(t, 0.2, 0.8)
    gradient(d, PX0, PY0, PW, PH, k)
    d.rectangle([PX0 - 24, PY0, PX0, PY0 + PH], fill=fade(DIM, k))
    d.rectangle([PX0 + PW, PY0, PX0 + PW + 24, PY0 + PH], fill=fade(AMBER, k))
    text(d, (PX0 - 12, PY0 + PH + 34), "0 V", 30, DIM, "Bold", "mm", k=k)
    text(d, (PX0 + PW + 12, PY0 + PH + 34), "3.3 V", 30, AMBER, "Bold", "mm", k=k)
    for i in range(1, 4):
        kk = prog(t, 1.0 + i * 0.4, 1.4 + i * 0.4)
        x = PX0 + PW * i / 4
        dashed(d, (x, PY0 + 10), (x, PY0 + PH - 10), TXT, kk, 2)
        text(d, (x, PY0 - 26), f"{3.3 * i / 4:.2f} V", 26, TXT, "Medium", "mm", mono=True, k=kk)
    if t > 3.2:
        kk = prog(t, 3.2, 3.7)
        cx, cy = PX0 + PW / 3, PY0 + PH * 0.6
        touch_ring(d, cx, cy, kk, GREEN, 34)
        d.line([cx, cy, cx, PY0 + PH + 80, 1520, PY0 + PH + 80, 1520, 640], fill=fade(GREEN, kk), width=4)
        box(d, (1420, 470, 1720, 640), (6, 10, 20), GREEN, 14, 3, kk)
        text(d, (1570, 530), "reads", 28, DIM, "Medium", "mm", k=kk)
        text(d, (1570, 585), "1.10 V", 48, GREEN, "Bold", "mm", mono=True, k=kk)
        text(d, (1570, 420), "= 1/3 across", 32, GREEN, "Bold", "mm", k=prog(t, 4.6, 5.1))

def s_xy(d, t, dur):
    chrome(d, "STEP 2 · RESISTIVE", "X first, then Y", "An ADC turns the voltage into x. Then the layers swap roles to measure y. Over and over.", t, dur)
    for i, (lab, horiz, st) in enumerate([("measure X", True, 0.4), ("measure Y", False, 2.6)]):
        kk = prog(t, st, st + 0.6)
        x0, y0, w, h = 220 + i * 800, 320, 640, 400
        gradient(d, x0, y0, w, h, kk, horiz)
        text(d, (x0 + w / 2, y0 - 40), lab, 40, TXT, "Bold", "mm", k=kk)
        if horiz:
            d.rectangle([x0 - 18, y0, x0, y0 + h], fill=fade(DIM, kk)); d.rectangle([x0 + w, y0, x0 + w + 18, y0 + h], fill=fade(AMBER, kk))
            sub = "drive top layer, read through bottom"
        else:
            d.rectangle([x0, y0 - 18, x0 + w, y0], fill=fade(DIM, kk)); d.rectangle([x0, y0 + h, x0 + w, y0 + h + 18], fill=fade(AMBER, kk))
            sub = "drive bottom layer, read through top"
        text(d, (x0 + w / 2, y0 + h + 50), sub, 26, DIM, "Medium", "mm", k=kk)
        cx, cy = x0 + w / 3, y0 + h * 0.6
        touch_ring(d, cx, cy, kk, GREEN, 30)
        k2 = prog(t, st + 1.0, st + 1.5)
        res = "1.10 V → x = 33%" if horiz else "1.98 V → y = 60%"
        text(d, (x0 + w / 2, y0 + h + 100), res, 36, GREEN, "Bold", "mm", mono=True, k=k2)

def s_res_pros(d, t, dur):
    chrome(d, "STEP 2 · RESISTIVE", "Resistive: the trade-offs", "Works with anything that presses, and it's cheap. But it needs a firm press, wears, and basic ones read one point.", t, dur)
    pros = ["works with a pen, nail or glove", "simple and low cost"]
    cons = ["needs a firm press", "soft top film can scratch and wear", "extra layers dim the picture a little", "basic 4-wire: one touch at a time"]
    k = prog(t, 0.2, 0.6)
    box(d, (180, 280, 900, 820), PANEL, GREEN, 18, 3, k)
    box(d, (1000, 280, 1740, 820), PANEL, RED, 18, 3, k)
    text(d, (540, 330), "GOOD", 40, GREEN, "Bold", "mm", k=k)
    text(d, (1370, 330), "NOT SO GOOD", 40, RED, "Bold", "mm", k=k)
    for i, s in enumerate(pros):
        kk = prog(t, 0.8 + i * 0.6, 1.2 + i * 0.6)
        tick(d, 240, 430 + i * 90, 18, GREEN, kk)
        text(d, (285, 430 + i * 90), s, 32, TXT, "Medium", "lm", k=kk)
    for i, s in enumerate(cons):
        kk = prog(t, 2.2 + i * 0.6, 2.6 + i * 0.6)
        cross(d, 1060, 430 + i * 90, 14, RED, kk)
        text(d, (1100, 430 + i * 90), s, 32, TXT, "Medium", "lm", k=kk)

# ---------------- 3. capacitance ----------------
def s_cap(d, t, dur):
    chrome(d, "STEP 3 · WHAT IS CAPACITANCE?", "Two conductors, close together", "Two conductors with an insulator between them store charge. Closer or bigger means more capacitance.", t, dur)
    k = prog(t, 0.2, 0.8)
    gap = 240 - 110 * prog(t, 4.0, 5.5)
    ytop = 540 - gap / 2; ybot = 540 + gap / 2
    plates(d, 560, 1160, ytop, ybot, k)
    text(d, (1200, ytop - 7), "conductor", 30, CYAN, "Bold", "lm", k=k)
    text(d, (1200, 540), "insulator", 30, AMBER, "Bold", "lm", k=k)
    text(d, (1200, ybot + 7), "conductor", 30, PURPLE, "Bold", "lm", k=k)
    k2 = prog(t, 1.5, 2.0)
    x, y0, hh = 360, 330, 420
    box(d, (x, y0, x + 70, y0 + hh), PANEL, LINE, 10, 2, k2)
    fill = (240 / gap) * 0.45
    d.rectangle([x + 5, y0 + hh - 5 - (hh - 10) * fill, x + 65, y0 + hh - 5], fill=fade(GREEN, k2))
    text(d, (x + 35, y0 + hh + 36), "charge stored", 26, GREEN, "Bold", "mm", k=k2)
    if t > 4.0:
        text(d, (1200, 760), "closer → more capacitance", 30, GREEN, "Bold", "lm", k=prog(t, 4.0, 4.5))

def s_finger(d, t, dur):
    chrome(d, "STEP 3 · WHAT IS CAPACITANCE?", "Your finger is a conductor", "Near the glass, your fingertip acts like a second plate. Some field reaches it: a tiny change, a picofarad or less.", t, dur)
    k = prog(t, 0.2, 0.7)
    d.rectangle([420, 560, 1340, 620], fill=fade(PANEL, k), outline=fade(LINE, k), width=2)
    text(d, (440, 590), "cover glass", 26, DIM, "Medium", "lm", k=k)
    d.rectangle([700, 640, 1060, 660], fill=fade(CYAN, k))
    text(d, (880, 700), "electrode", 28, CYAN, "Bold", "mm", k=k)
    near = prog(t, 1.2, 3.5)
    fy = 320 + 236 * near
    finger(d, 880, fy, k, 96, 240)
    # field lines: arcs from the electrode; when the finger is near, the inner ones reach it
    for i in range(5):
        sx = 720 + i * 80
        if near > 0.7 and 1 <= i <= 3:
            d.line([sx, 640, sx + (880 - sx) * 0.5, 600, 880 + (sx - 880) * 0.25, fy + 4], fill=fade(AMBER, k), width=3)
        else:
            hgt = 90 + 25 * abs(i - 2)
            d.arc([sx - 70, 640 - hgt, sx + 70, 640 + hgt], 180, 360, fill=fade(mix(BG, AMBER, 0.55), k), width=3)
    k2 = prog(t, 0.8, 1.3)
    x, y0, hh = 1500, 320, 420
    box(d, (x, y0, x + 80, y0 + hh), PANEL, LINE, 10, 2, k2)
    fill = 0.35 + 0.25 * near
    d.rectangle([x + 5, y0 + hh - 5 - (hh - 10) * fill, x + 75, y0 + hh - 5], fill=fade(GREEN, k2))
    text(d, (x + 40, y0 - 30), "capacitance", 28, GREEN, "Bold", "mm", k=k2)
    if near > 0.9:
        text(d, (x + 40, y0 + hh + 40), "small rise", 28, GREEN, "Bold", "mm", k=prog(t, 3.4, 3.9))

def s_grid(d, t, dur):
    chrome(d, "STEP 3 · WHAT IS CAPACITANCE?", "An invisible grid", "Under the glass: rows one way, columns the other, made of a transparent conductor such as indium tin oxide.", t, dur)
    k = prog(t, 0.2, 0.7)
    box(d, (GX - 20, GY - 20, GX + GW + 20, GY + GH + 20), (8, 12, 24), LINE, 14, 2, k)
    nr = int(clamp((t - 0.6) / 1.5) * NR + 0.999) if t > 0.6 else 0
    nc = int(clamp((t - 2.2) / 1.8) * NC + 0.999) if t > 2.2 else 0
    for r in range(nr):
        y = GY + (r + 0.5) * GH / NR
        d.line([GX, y, GX + GW, y], fill=CYAN, width=6)
    for c in range(nc):
        x = GX + (c + 0.5) * GW / NC
        d.line([x, GY, x, GY + GH], fill=PURPLE, width=6)
    text(d, (GX - 40, GY + GH / 2), "rows", 32, CYAN, "Bold", "rm", k=prog(t, 0.8, 1.2))
    text(d, (GX + GW / 2, GY - 44), "columns", 32, PURPLE, "Bold", "mm", k=prog(t, 2.4, 2.8))
    k3 = prog(t, 4.2, 4.8)
    text(d, (GX + GW + 50, GY + 120), "see-through", 30, TXT, "Bold", "lm", k=k3)
    text(d, (GX + GW + 50, GY + 165), "conductor", 30, TXT, "Bold", "lm", k=k3)
    text(d, (GX + GW + 50, GY + 270), "lines a few mm", 30, DIM, "Medium", "lm", k=prog(t, 5.0, 5.5))
    text(d, (GX + GW + 50, GY + 315), "apart (typical)", 30, DIM, "Medium", "lm", k=prog(t, 5.0, 5.5))

# ---------------- 4. self-capacitance ----------------
def line_bars(d, fingers, k, s=0.6):
    rows = [sum(math.exp(-((r - fr) ** 2) / (2 * s * s)) for fr, fc in fingers) for r in range(NR)]
    cols = [sum(math.exp(-((c - fc) ** 2) / (2 * s * s)) for fr, fc in fingers) for c in range(NC)]
    for r, v in enumerate(rows):
        y = GY + (r + 0.5) * GH / NR
        L = 150 * clamp(v)
        d.rectangle([GX - 40 - L, y - 12, GX - 40, y + 12], fill=fade(CYAN if v > 0.8 else mix(BG, CYAN, 0.4), k))
    for c, v in enumerate(cols):
        x = GX + (c + 0.5) * GW / NC
        L = 70 * clamp(v)
        d.rectangle([x - 12, GY - 30 - L, x + 12, GY - 30], fill=fade(PURPLE if v > 0.8 else mix(BG, PURPLE, 0.4), k))
    return sorted({round(fr) for fr, fc in fingers}), sorted({round(fc) for fr, fc in fingers})

def s_self(d, t, dur):
    chrome(d, "STEP 4 · SELF-CAPACITANCE", "Measure every line", "Measure each row and each column on its own. The row and column with the biggest change cross at your finger.", t, dur)
    k = prog(t, 0.2, 0.7)
    f = [(2.0, 7.0)]
    show = prog(t, 1.2, 2.2)
    hr, hc = line_bars(d, [(fr, fc) for fr, fc in f], show) if t > 1.2 else ([], [])
    grid(d, k, row_hi=hr if t > 2.5 else None, col_hi=hc if t > 2.5 else None)
    x, y = node(2, 7)
    touch_ring(d, x, y, prog(t, 0.6, 1.0))
    if t > 3.2:
        kk = prog(t, 3.2, 3.7)
        text(d, (GX + GW + 50, GY + 200), "row 3", 36, CYAN, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 250), "+ column 8", 36, PURPLE, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 320), "= the touch", 36, GREEN, "Bold", "lm", k=kk)

def s_ghost(d, t, dur):
    chrome(d, "STEP 4 · SELF-CAPACITANCE", "Two fingers, four answers", "Two rows and two columns light up. They cross in four places: two real touches and two ghosts.", t, dur)
    k = prog(t, 0.2, 0.7)
    f = [(2.0, 3.0), (6.0, 9.0)]
    hr, hc = line_bars(d, f, prog(t, 0.8, 1.6))
    grid(d, k, row_hi=hr if t > 1.6 else None, col_hi=hc if t > 1.6 else None)
    fk = 1 - prog(t, 3.0, 3.8)
    for fr, fc in f:
        touch_ring(d, *node(round(fr), round(fc)), fk * k)
    if t > 3.0:
        kk = prog(t, 3.4, 4.0)
        for r in hr:
            for c in hc:
                x, y = node(r, c)
                d.ellipse([x - 34, y - 34, x + 34, y + 34], outline=fade(RED, kk), width=5)
                text(d, (x, y), "?", 40, RED, "Bold", "mm", k=kk)
        text(d, (GX + GW + 50, GY + 220), "4 candidates", 34, RED, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 270), "only 2 are real", 34, TXT, "Bold", "lm", k=prog(t, 4.6, 5.1))

# ---------------- 5. mutual capacitance ----------------
def s_mutual(d, t, dur):
    chrome(d, "STEP 5 · MUTUAL CAPACITANCE", "Drive one line, listen on another", "A transmitter line is driven; the crossing receiver picks up some signal. A finger draws part of it away.", t, dur)
    k = prog(t, 0.2, 0.7)
    d.rectangle([380, 560, 1380, 610], fill=fade(PANEL, k), outline=fade(LINE, k), width=2)
    text(d, (400, 585), "cover glass", 26, DIM, "Medium", "lm", k=k)
    d.rectangle([520, 630, 820, 650], fill=fade(CYAN, k))
    d.rectangle([940, 630, 1240, 650], fill=fade(PURPLE, k))
    text(d, (670, 690), "transmitter (row)", 28, CYAN, "Bold", "mm", k=k)
    text(d, (1090, 690), "receiver (column)", 28, PURPLE, "Bold", "mm", k=k)
    # drive signal
    pts = [(420 + i, 760 + 22 * math.sin(i / 10 - t * 8)) for i in range(0, 200, 3)]
    d.line(pts, fill=fade(CYAN, k), width=3)
    text(d, (520, 810), "changing drive signal", 24, CYAN, "Medium", "mm", k=k)
    near = prog(t, 3.0, 4.6)
    fy = 300 + 254 * near
    finger(d, 880, fy, prog(t, 2.6, 3.0), 96, 220)
    for i in range(4):
        a, b = 760 - i * 60, 1000 + i * 60
        hgt = 60 + i * 45
        cx = (a + b) / 2
        steal = near > 0.7 and i >= 1
        col = AMBER if steal else mix(BG, AMBER, 0.7)
        if steal:
            d.line([a, 630, a + 40, 560, 860 - i * 6, fy + 2], fill=fade(col, k), width=3)
        else:
            d.arc([a, 630 - hgt, b, 630 + hgt], 180, 360, fill=fade(col, k), width=3)
    k2 = prog(t, 1.2, 1.7)
    x, y0, hh = 1520, 320, 420
    box(d, (x, y0, x + 80, y0 + hh), PANEL, LINE, 10, 2, k2)
    fill = 0.85 - 0.35 * near
    d.rectangle([x + 5, y0 + hh - 5 - (hh - 10) * fill, x + 75, y0 + hh - 5], fill=fade(PURPLE, k2))
    text(d, (x + 40, y0 - 50), "signal at", 26, PURPLE, "Bold", "mm", k=k2)
    text(d, (x + 40, y0 - 18), "receiver", 26, PURPLE, "Bold", "mm", k=k2)
    if near > 0.9:
        text(d, (x + 40, y0 + hh + 40), "drops", 32, RED, "Bold", "mm", k=prog(t, 4.6, 5.1))

SCAN_F = [(4.3, 6.6)]
def s_scan(d, t, dur):
    chrome(d, "STEP 5 · MUTUAL CAPACITANCE", "Scan, row by row", "Drive row 1 and listen to every column at once. Then row 2, row 3… until every crossing has a reading.", t, dur)
    k = prog(t, 0.2, 0.7)
    rows_done = clamp((t - 1.0) / 6.0) * NR
    cur = min(NR - 1, int(rows_done))
    grid(d, k, row_hi=[cur] if t > 1.0 and rows_done < NR else None, col_hi=list(range(NC)) if t > 1.0 and rows_done < NR else None,
         rowcol=CYAN, colcol=mix(BG, PURPLE, 0.85))
    for r in range(NR):
        for c in range(NC):
            if r < int(rows_done) or (r == cur and t > 1.0):
                v = field(SCAN_F, r, c)
                x, y = node(r, c)
                rr = 9 + 14 * v
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=heat_col(0.2 + v))
    if t > 1.0 and rows_done < NR:
        y = node(cur, 0)[1]
        text(d, (GX - 40, y), "drive ▶", 28, CYAN, "Bold", "rm")
    text(d, (GX + GW / 2, GY - 44), "listen on all columns", 28, PURPLE, "Bold", "mm", k=prog(t, 1.0, 1.4))
    k3 = prog(t, 6.0, 6.6)
    text(d, (GX + GW + 50, GY + 180), "8 rows × 12 cols", 32, TXT, "Bold", "lm", k=k3)
    text(d, (GX + GW + 50, GY + 230), "= 96 crossings", 32, GREEN, "Bold", "lm", k=k3)
    text(d, (GX + GW + 50, GY + 280), "(example grid)", 26, DIM, "Medium", "lm", k=k3)

HEAT_F = [(2.0, 3.0), (5.4, 8.6)]
def s_heatmap(d, t, dur):
    chrome(d, "STEP 5 · MUTUAL CAPACITANCE", "A picture of your touch", "All the readings make a map of where the signal dropped. Each finger is its own blob. No ghosts.", t, dur)
    k = prog(t, 0.2, 0.8)
    heatmap(d, HEAT_F, k)
    if t > 2.0:
        kk = prog(t, 2.0, 2.6)
        for i, (fr, fc) in enumerate(HEAT_F):
            x, y = node(fr, fc)
            d.ellipse([x - 70, y - 70, x + 70, y + 70], outline=fade(GREEN, kk), width=4)
            text(d, (x + 80, y - 60), f"finger {i + 1}", 30, GREEN, "Bold", "lm", k=kk)
    k2 = prog(t, 3.0, 3.6)
    x = GX + GW + 70
    for i in range(6):
        d.rectangle([x, GY + 60 + i * 50, x + 50, GY + 100 + i * 50], fill=fade(heat_col(1 - i / 5), k2))
    text(d, (x + 70, GY + 80), "big drop", 26, AMBER, "Bold", "lm", k=k2)
    text(d, (x + 70, GY + 330), "no change", 26, DIM, "Bold", "lm", k=k2)

CEN = [[8, 30, 12], [25, 90, 40], [6, 22, 10]]
def s_centroid(d, t, dur):
    chrome(d, "STEP 5 · MUTUAL CAPACITANCE", "Finer than the grid", "A weighted average of the crossings around a blob places your finger between the lines.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, cs = 300, 300, 170
    tot = sum(sum(r) for r in CEN)
    for r in range(3):
        for c in range(3):
            v = CEN[r][c]
            kk = prog(t, 0.4 + (r * 3 + c) * 0.12, 0.8 + (r * 3 + c) * 0.12)
            x, y = x0 + c * cs, y0 + r * cs
            d.rounded_rectangle([x + 6, y + 6, x + cs - 6, y + cs - 6], 10, fill=fade(heat_col(v / 90), kk))
            text(d, (x + cs / 2, y + 40), str(v), 38, BG if v > 45 else TXT, "Bold", "mm", mono=True, k=kk)
    cx = sum(CEN[r][c] * (c - 1) for r in range(3) for c in range(3)) / tot
    cy = sum(CEN[r][c] * (r - 1) for r in range(3) for c in range(3)) / tot
    gx, gy = x0 + 1.5 * cs, y0 + 1.5 * cs
    if t > 2.0:
        kk = prog(t, 2.0, 2.5)
        d.line([gx - 14, gy, gx + 14, gy], fill=fade(DIM, kk), width=3)
        d.line([gx, gy - 14, gx, gy + 14], fill=fade(DIM, kk), width=3)
    if t > 4.0:
        kk = prog(t, 4.0, 4.6)
        px, py = gx + cx * cs * prog(t, 4.0, 5.0), gy + cy * cs * prog(t, 4.0, 5.0)
        d.ellipse([px - 14, py - 14, px + 14, py + 14], fill=fade(GREEN, kk))
    k2 = prog(t, 1.4, 2.0)
    text(d, (1000, 360), "position =", 40, TXT, "Bold", "lm", k=k2)
    text(d, (1000, 430), "Σ (reading × place)", 40, CYAN, "Bold", "lm", mono=True, k=k2)
    d.line([1000, 470, 1460, 470], fill=fade(CYAN, k2), width=3)
    text(d, (1230, 510), "Σ reading", 40, CYAN, "Bold", "mm", mono=True, k=k2)
    k3 = prog(t, 4.6, 5.2)
    text(d, (1000, 620), f"x ≈ +{cx:.2f}  y ≈ {cy:.2f}", 36, GREEN, "Bold", "lm", mono=True, k=k3)
    text(d, (1000, 670), "in line spacings, from the centre (example)", 26, DIM, "Medium", "lm", k=k3)

def s_multi(d, t, dur):
    chrome(d, "STEP 5 · MUTUAL CAPACITANCE", "Every finger, tracked", "Each blob gets an ID and is followed from scan to scan. Blobs moving apart? That's a pinch to zoom.", t, dur)
    k = prog(t, 0.2, 0.7)
    s = ease(clamp((t - 1.5) / 4.0))
    f1 = (3.6 - 1.8 * s, 5.4 - 3.2 * s)
    f2 = (4.4 + 1.8 * s, 6.6 + 3.2 * s)
    heatmap(d, [f1, f2], k)
    for i, (a, b, col) in enumerate([((3.6, 5.4), f1, CYAN), ((4.4, 6.6), f2, PURPLE)]):
        pa, pb = node(*a), node(*b)
        if s > 0.02:
            dashed(d, pa, pb, TXT, k, 3)
        d.ellipse([pb[0] - 30, pb[1] - 30, pb[0] + 30, pb[1] + 30], fill=fade(BG, k), outline=fade(col, k), width=4)
        text(d, pb, str(i + 1), 34, col, "Bold", "mm", k=k)
    if t > 5.0:
        kk = prog(t, 5.0, 5.5)
        text(d, (GX + GW + 50, GY + 220), "pinch", 40, GREEN, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 270), "to zoom", 40, GREEN, "Bold", "lm", k=kk)

def s_speed(d, t, dur):
    chrome(d, "STEP 5 · MUTUAL CAPACITANCE", "Fast, and filtered", "The grid is scanned many times a second, often over 100. Tiny changes mean noise must be filtered out first.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 200, 330, 520, 360
    box(d, (x0 - 14, y0 - 14, x0 + w + 14, y0 + h + 14), (8, 12, 24), LINE, 12, 2, k)
    cur = int((t * 24) % 6)
    for r in range(6):
        y = y0 + (r + 0.5) * h / 6
        d.line([x0, y, x0 + w, y], fill=fade(CYAN if r == cur else mix(BG, CYAN, 0.4), k), width=7 if r == cur else 4)
    for c in range(8):
        x = x0 + (c + 0.5) * w / 8
        d.line([x, y0, x, y0 + h], fill=fade(mix(BG, PURPLE, 0.5), k), width=4)
    text(d, (x0 + w / 2, y0 + h + 60), "whole grid, again and again", 30, TXT, "Bold", "mm", k=k)
    text(d, (x0 + w / 2, y0 + h + 105), "often 100+ times a second (typical)", 26, DIM, "Medium", "mm", k=k)
    k2 = prog(t, 2.0, 2.6)
    px0, py0, pw, ph = 900, 330, 820, 360
    d.line([px0, py0 + ph, px0 + pw, py0 + ph], fill=fade(LINE, k2), width=3)
    d.line([px0, py0, px0, py0 + ph], fill=fade(LINE, k2), width=3)
    def clean(u): return 0.15 + 0.6 * clamp((u - 0.45) / 0.06)
    raw, filt = [], []
    for i in range(201):
        u = i / 200
        nz = 0.12 * math.sin(u * 173) + 0.09 * math.sin(u * 291 + 1.3) + 0.06 * math.sin(u * 517)
        raw.append((px0 + pw * u, py0 + ph - ph * (clean(u) + nz)))
        filt.append((px0 + pw * u, py0 + ph - ph * clean(u)))
    n = int(clamp((t - 2.4) / 2.5) * 201)
    if n > 1:
        d.line(raw[:n], fill=mix(BG, RED, 0.6), width=2)
    if t > 4.2:
        m = int(clamp((t - 4.2) / 2.0) * 201)
        if m > 1: d.line(filt[:m], fill=CYAN, width=5)
    ty = py0 + ph - ph * 0.5
    dashed(d, (px0, ty), (px0 + pw, ty), GREEN, k2, 2)
    text(d, (px0 + pw, ty - 14), "touch threshold", 24, GREEN, "Bold", "rb", k=k2)
    text(d, (px0, py0 - 20), "raw (red) · filtered (cyan)", 26, DIM, "Medium", "lb", k=k2)
    text(d, (px0 + pw / 2, py0 + ph + 60), "noise from the display or a charger", 28, TXT, "Bold", "mm", k=prog(t, 3.0, 3.5))

# ---------------- 6. head to head ----------------
def s_gloves(d, t, dur):
    chrome(d, "STEP 6 · HEAD TO HEAD", "Gloves and pens", "Resistive needs only pressure. Capacitive needs something conductive: plastic pens and ordinary gloves don't work.", t, dur)
    k = prog(t, 0.2, 0.6)
    rows = [("fingertip", True, True), ("plastic pen, ordinary glove", True, False), ("touchscreen glove, capacitive stylus", True, True)]
    text(d, (1180, 300), "RESISTIVE", 34, AMBER, "Bold", "mm", k=k)
    text(d, (1560, 300), "CAPACITIVE", 34, CYAN, "Bold", "mm", k=k)
    for i, (lab, a, b) in enumerate(rows):
        kk = prog(t, 0.8 + i * 1.3, 1.3 + i * 1.3)
        y = 390 + i * 150
        box(d, (180, y, 1740, y + 120), PANEL, LINE, 14, 2, kk)
        text(d, (220, y + 60), lab, 36, TXT, "Bold", "lm", k=kk)
        (tick if a else cross)(d, 1180, y + 60, 24, GREEN if a else RED, kk)
        (tick if b else cross)(d, 1560, y + 60, 24, GREEN if b else RED, kk)
    text(d, (220, 860), "conductive tip = works", 28, DIM, "Medium", "lm", k=prog(t, 4.6, 5.2))

def s_water(d, t, dur):
    chrome(d, "STEP 6 · HEAD TO HEAD", "Rain on the screen", "Water conducts, so drops can fake small touches. Controllers reject shapes that don't look like a finger.", t, dur)
    k = prog(t, 0.2, 0.7)
    drops = [(1.0, 9.6), (6.4, 2.0), (2.6, 10.6), (6.8, 6.0)]
    wk = prog(t, 1.2, 2.2)
    def extra(r, c): return wk * 0.35 * sum(math.exp(-((r - a) ** 2 + (c - b) ** 2) / (2 * 0.4 ** 2)) for a, b in drops)
    heatmap(d, [(3.4, 4.2)], k, extra)
    for a, b in drops:
        x, y = node(a, b)
        d.ellipse([x - 22, y - 26, x + 22, y + 18], outline=fade(CYAN, wk), width=3)
    if t > 3.2:
        kk = prog(t, 3.2, 3.8)
        x, y = node(3.4, 4.2)
        d.ellipse([x - 70, y - 70, x + 70, y + 70], outline=fade(GREEN, kk), width=4)
        for a, b in drops:
            xx, yy = node(a, b)
            cross(d, xx, yy, 14, RED, kk)
        text(d, (GX + GW + 50, GY + 160), "finger-shaped:", 30, GREEN, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 200), "keep", 30, GREEN, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 280), "small, odd:", 30, RED, "Bold", "lm", k=kk)
        text(d, (GX + GW + 50, GY + 320), "ignore", 30, RED, "Bold", "lm", k=kk)
    text(d, (GX + GW / 2, GY - 50), "resistive: mostly ignores drops (no pressure)", 28, AMBER, "Bold", "mm", k=prog(t, 5.0, 5.5))

def s_table(d, t, dur):
    chrome(d, "STEP 6 · HEAD TO HEAD", "The scorecard", "Pressure vs your finger. One touch vs many. Any stylus vs a light touch on hard, clear glass.", t, dur)
    k = prog(t, 0.2, 0.6)
    rows = [("senses", "pressure", "your finger"), ("touches", "basic: one", "many"),
            ("stylus", "anything", "conductive tip"), ("feel", "firm press", "light touch"),
            ("surface", "soft film", "hard glass"), ("picture", "a little dimmer", "clearer")]
    text(d, (980, 280), "RESISTIVE", 34, AMBER, "Bold", "mm", k=k)
    text(d, (1460, 280), "CAPACITIVE", 34, CYAN, "Bold", "mm", k=k)
    for i, (a, b, c) in enumerate(rows):
        kk = prog(t, 0.6 + i * 0.6, 1.0 + i * 0.6)
        y = 320 + i * 88
        box(d, (300, y, 1700, y + 76), PANEL if i % 2 else (18, 25, 46), LINE, 10, 1, kk)
        text(d, (340, y + 38), a, 32, DIM, "Bold", "lm", k=kk)
        text(d, (980, y + 38), b, 32, TXT, "Medium", "mm", k=kk)
        text(d, (1460, y + 38), c, 32, TXT, "Medium", "mm", k=kk)

def s_where_used(d, t, dur):
    chrome(d, "STEP 6 · HEAD TO HEAD", "Where you'll find each", "Resistive: some industrial panels, older devices and kiosks. Capacitive: phones, tablets, touchpads, many car screens.", t, dur)
    for i, (name, col, items, st) in enumerate([
            ("RESISTIVE", AMBER, ["some industrial panels", "older handheld devices", "some kiosks and terminals"], 0.4),
            ("CAPACITIVE", CYAN, ["phones and tablets", "laptop touchpads", "many car screens"], 2.6)]):
        kk = prog(t, st, st + 0.6)
        x = 220 + i * 800
        box(d, (x, 290, x + 680, 800), PANEL, col, 20, 4, kk)
        text(d, (x + 340, 360), name, 48, col, "Bold", "mm", k=kk)
        for j, s in enumerate(items):
            k2 = prog(t, st + 0.6 + j * 0.5, st + 1.0 + j * 0.5)
            d.ellipse([x + 70, 480 + j * 100 - 10, x + 90, 480 + j * 100 + 10], fill=fade(col, k2))
            text(d, (x + 120, 480 + j * 100), s, 36, TXT, "Medium", "lm", k=k2)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "Resistive vs capacitive", "Resistive: press, read a voltage for x, then y. Capacitive: a grid, a finger, a scan, and a weighted average.", t, dur)
    for i, (name, col, steps, st) in enumerate([
            ("RESISTIVE", AMBER, ["Press", "Layers touch", "Voltage → x", "Swap → y"], 0.3),
            ("CAPACITIVE", CYAN, ["Grid", "Finger draws field", "Scan crossings", "Average → x, y"], 2.4)]):
        y = 380 + i * 260
        text(d, (200, y), name, 40, col, "Bold", "lm", k=prog(t, st, st + 0.4))
        x0, x1 = 640, 1700
        d.line([x0, y, x0 + (x1 - x0) * prog(t, st, st + 2.0), y], fill=LINE, width=5)
        for j, s in enumerate(steps):
            kk = prog(t, st + 0.3 + j * 0.4, st + 0.7 + j * 0.4)
            if kk <= 0: continue
            x = x0 + j * (x1 - x0) / 3
            d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=fade(col, kk))
            text(d, (x, y + 56), s, 30, TXT, "Bold", "mm", k=kk)

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How do Wi-Fi and Bluetooth chips", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "send bits through the air?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
          ("03_where", s_where, 8), ("04_two", s_two, 8),
          ("05_layers", s_layers, 8), ("06_press", s_press, 8), ("07_divider", s_divider, 9), ("08_xy", s_xy, 9), ("09_res_pros", s_res_pros, 9),
          ("10_cap", s_cap, 8), ("11_finger", s_finger, 9), ("12_grid", s_grid, 8),
          ("13_self", s_self, 8), ("14_ghost", s_ghost, 8),
          ("15_mutual", s_mutual, 9), ("16_scan", s_scan, 8), ("17_heatmap", s_heatmap, 7), ("18_centroid", s_centroid, 8),
          ("19_multi", s_multi, 8), ("20_speed", s_speed, 8),
          ("21_gloves", s_gloves, 8), ("22_water", s_water, 8), ("23_table", s_table, 8), ("24_where", s_where_used, 8),
          ("25_recap", s_recap, 8), ("26_end", s_end, 6)]

NARRATION = {
 "01_hook": "Tap your phone screen with a plastic pen, and nothing happens. Tap it with your fingertip, and it responds instantly. Yet on many older kiosk screens, that same pen works fine. So what is your phone actually sensing? And why are the two so different?",
 "02_cover": "Today, it's a head to head: resistive touchscreens versus capacitive ones. We'll see how a resistive screen feels your press. Then how a capacitive screen senses your finger with no pressure at all, in two flavours: self capacitance, and mutual capacitance. Then we'll put them side by side.",
 "03_where": "Every touchscreen has the same job. Find one point, an x and a y, and report it to the processor. Then do it again, and again, many times every second, so that a swipe feels smooth instead of jumpy.",
 "04_two": "There are two classic ways to do it. A resistive screen waits for you to press two layers together. A capacitive screen senses the electric charge your finger can hold, and doesn't need any pressure at all. Let's take them one at a time.",
 "05_layers": "First, resistive. It's a sandwich. On top, a flexible plastic film. Below it, a sheet of glass. On the sides that face each other, both carry a thin, see-through conductive coating. Tiny spacer dots keep them apart, so normally, the two coatings never touch.",
 "06_press": "Now press with a finger, a pen, or even a fingernail. The top film bends down, and at that one spot, the two coatings make contact. Electrically, the two layers are now connected, exactly where you pressed.",
 "07_divider": "Here's the clever part. The controller puts a voltage across the top coating: zero volts on the left edge, three point three volts on the right. The voltage rises evenly from one side to the other. The bottom layer touches it at one point, and simply picks up the voltage there. In this example, one point one volts means one third of the way across.",
 "08_xy": "That voltage goes to an A D C, just like in the last episode, and becomes a number. That's the x position. Then the controller swaps roles. It puts the voltage across the bottom layer, from top to bottom, and reads it through the top layer. That gives y. X, then y, over and over.",
 "09_res_pros": "So resistive screens work with anything that presses: a pen, a fingernail, a thick glove. They're also simple and cheap. But you have to press firmly. The soft top film can scratch and wear. The extra layers dim the picture a little. And a basic four-wire design reads only one point at a time.",
 "10_cap": "Now, capacitive. First, what is capacitance? Put two conductors close together, with an insulator between them, and they can store electric charge. That's a capacitor. Bring them closer, or make them bigger, and they store more. That amount is the capacitance.",
 "11_finger": "Here's the key fact. Your body conducts electricity, a little. So when your fingertip comes near an electrode under the glass, it acts like another plate of a capacitor. Some of the electric field now reaches your finger. The change is tiny, around a picofarad or less. But a good controller can measure it.",
 "12_grid": "So under the glass of a capacitive screen sits a grid of electrodes: rows running one way, and columns running the other. They're made from a transparent conductor, such as indium tin oxide, so you see right through them. The lines are typically a few millimetres apart.",
 "13_self": "The simplest way to read the grid is called self capacitance. The controller measures each row, and each column, on its own. A finger near the glass adds capacitance to the lines closest to it. The row with the biggest change, and the column with the biggest change, cross right at your finger.",
 "14_ghost": "But try it with two fingers. Now two rows light up, and two columns light up. Those lines cross in four places. Two of them are real fingers, and two are ghosts. From rows and columns alone, the controller can't always tell which pair is real. That's the ghost touch problem.",
 "15_mutual": "The fix is mutual capacitance. Instead of measuring each line alone, the controller drives one line with a changing signal. That's the transmitter. And it listens on a line that crosses it, the receiver. Some of the signal couples across. A finger nearby draws away part of that field, so less signal reaches the receiver.",
 "16_scan": "Now the controller can test every single crossing. It drives the first row, and listens to all the columns at once. Then the next row, and the next. With eight rows and twelve columns, like this example grid, that's ninety six crossings, each with its own reading.",
 "17_heatmap": "Put all those readings together, and you get a picture: a little map of where the signal dropped. Each finger shows up as its own bright blob. Two fingers? Two blobs, in the right places. No ghosts this time.",
 "18_centroid": "The grid lines are millimetres apart, but your finger can land anywhere. So the controller looks at the crossings around each blob, and takes a weighted average of their positions. Bigger changes pull harder. That places your finger between the lines, much more precisely than the grid spacing.",
 "19_multi": "Each blob gets its own I D, and the controller follows it from one scan to the next. That's multi-touch. When two blobs move apart, your phone sees a pinch to zoom. When one blob slides across the grid, it's a swipe.",
 "20_speed": "All of this happens fast. Phones typically scan the whole grid many times a second, often more than a hundred. And because the changes are so small, the controller also has to filter out electrical noise, from the display or a charger, before it decides that a touch is real.",
 "21_gloves": "So, head to head. Gloves and pens first. A resistive screen only needs pressure, so anything works. A capacitive screen needs something conductive, close to the glass. An ordinary glove or a plastic pen is an insulator, so it's ignored. Touchscreen gloves and capacitive styluses fix that with a conductive tip.",
 "22_water": "Next, water. Drops of water conduct too, so on a capacitive screen they can look like extra small touches, or smear a real one. Controllers try to reject shapes that don't look like a finger. A resistive screen mostly ignores drops, because water doesn't press the layers together.",
 "23_table": "Here's the scorecard. Resistive senses pressure. Capacitive senses your finger. A basic resistive screen reads one point, while capacitive reads many. Resistive takes any stylus. Capacitive needs only a light touch, sits under hard glass, and keeps the picture clearer.",
 "24_where": "That's why you'll still find resistive screens on some industrial panels, older devices, and some kiosks, where gloves and cost matter. But your phone, your tablet, your laptop's touchpad, and many car screens use capacitive sensing, usually reading the grid with mutual capacitance.",
 "25_recap": "So, resistive versus capacitive. Resistive: press two layers together, then read a voltage for x, and another for y. Capacitive: a hidden grid, a finger that draws away a little electric field, a scan of every crossing, and a weighted average to find exactly where you touched.",
 "26_end": "Next episode: how do Wi-Fi and Bluetooth chips send bits through the air? Subscribe so you don't miss it.",
}
OUTPUT = "resistive_vs_capacitive_touchscreens_ep9_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep9/{name}.mp4", f"ep9/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep9", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    for j in range(0, len(SCENES), 9):
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES[j:j + 9]):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save(f"ep9/sheet{j // 9 + 1}.jpg", quality=85)
