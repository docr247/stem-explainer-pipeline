import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
VREF = 3.3

# ---------------- helpers ----------------
def comparator(d, x, y, s, k=1.0, out=None, col=CYAN, plus_lab=None, minus_lab=None):
    """Triangle comparator. Returns (plus_in, minus_in, out_pt)."""
    pts = [(x, y - s), (x, y + s), (x + 1.6 * s, y)]
    d.polygon(pts, fill=fade(PANEL, k), outline=fade(col, k), width=4)
    text(d, (x + 14, y - s / 2), "+", max(18, int(s * 0.38)), GREEN, "Bold", "lm", k=k)
    text(d, (x + 14, y + s / 2), "−", max(18, int(s * 0.38)), RED, "Bold", "lm", k=k)
    pin, nin, o = (x, y - s / 2), (x, y + s / 2), (x + 1.6 * s, y)
    if out is not None:
        c = GREEN if out else DIM
        d.line([o, (o[0] + 50, o[1])], fill=fade(c, k), width=5)
        d.ellipse([o[0] + 50 - 9, o[1] - 9, o[0] + 50 + 9, o[1] + 9], fill=fade(c, k))
    if plus_lab: text(d, (x - 16, pin[1]), plus_lab, 26, TXT, "Medium", "rm", mono=True, k=k)
    if minus_lab: text(d, (x - 16, nin[1]), minus_lab, 26, TXT, "Medium", "rm", mono=True, k=k)
    return pin, nin, o

def resistor(d, x, y0, y1, k=1.0, col=DIM):
    n, a = 6, 14
    seg = (y1 - y0) / (n + 2)
    pts = [(x, y0), (x, y0 + seg)]
    for i in range(n):
        pts.append((x + (a if i % 2 == 0 else -a), y0 + seg * (1.5 + i)))
    pts += [(x, y1 - seg), (x, y1)]
    d.line(pts, fill=fade(col, k), width=3)

def sig(u):  # a smooth "sensor" signal in volts, u in 0..1
    return 1.65 + 0.95 * math.sin(2 * math.pi * (u * 1.3 + 0.1)) + 0.3 * math.sin(2 * math.pi * u * 4.1)

def axes(d, x0, y0, w, h, k, ylab=None):
    d.line([x0, y0, x0, y0 + h], fill=fade(LINE, k), width=3)
    d.line([x0, y0 + h, x0 + w, y0 + h], fill=fade(LINE, k), width=3)
    if ylab: text(d, (x0 - 14, y0), ylab, 24, DIM, "Medium", "ra", k=k)

def vy(v, y0, h): return y0 + h - v / VREF * h

def bits(d, x, y, s, cell=70, k=1.0, col=CYAN, known=None):
    for i, ch in enumerate(s):
        on = known is None or i < known
        c = col if on else LINE
        box(d, (x + i * cell, y, x + i * cell + cell - 10, y + cell - 10), PANEL, c, 10, 3, k)
        text(d, (x + i * cell + (cell - 10) / 2, y + (cell - 10) / 2), ch if on else "?", int(cell * 0.5),
             c if on else DIM, "Bold", "mm", mono=True, k=k)

TAPS = [VREF * i / 8 for i in range(1, 8)]

# ---------------- intro ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "A chip that only understands ones and zeros can still measure a smooth voltage. How?", t, dur)
    k = prog(t, 0.2, 0.8)
    x0, y0, w, h = 160, 330, 560, 380
    box(d, (x0 - 30, y0 - 50, x0 + w + 30, y0 + h + 40), PANEL, LINE, 16, 2, k)
    text(d, (x0, y0 - 24), "sensor voltage", 28, AMBER, "Bold", "lm", k=k)
    n = int(clamp((t - 0.5) / 3.0) * 200)
    pts = [(x0 + w * i / 200, vy(sig(i / 200), y0, h)) for i in range(n)]
    if len(pts) > 1: d.line(pts, fill=AMBER, width=5)
    arrow(d, (x0 + w + 50, 520), (900, 520), DIM, 5, prog(t, 2.0, 2.6))
    chip(d, 920, 400, 300, 240, "MCU", "0s and 1s only", CYAN, prog(t, 1.2, 1.8))
    if t > 3.0:
        text(d, (1070, 330), "?", 90, AMBER, "Bold", "mm", k=prog(t, 3.0, 3.5))
    arrow(d, (1250, 520), (1420, 520), DIM, 5, prog(t, 4.0, 4.6))
    k2 = prog(t, 4.4, 5.0)
    box(d, (1440, 440, 1760, 600), (6, 10, 20), GREEN, 16, 4, k2)
    text(d, (1600, 520), "2730", 76, GREEN, "Bold", "mm", mono=True, k=k2)
    text(d, (1600, 640), "a number (example)", 26, DIM, "Medium", "mm", k=k2)

def s_cover(d, t, dur):
    chrome(d, "TODAY", "Build an ADC, layer by layer", "We'll build an analog-to-digital converter from one comparator up, then add sampling, resolution and code.", t, dur)
    items = [("1", "The problem", AMBER), ("2", "One comparator", CYAN), ("3", "The flash ADC", PURPLE),
             ("4", "Successive approximation", GREEN), ("5", "Sample and hold", AMBER), ("6", "Resolution and code", CYAN)]
    for i, (n, s, c) in enumerate(items):
        kk = prog(t, 0.6 + i * 0.5, 1.0 + i * 0.5)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 290 + row * 170
        box(d, (x, y, x + 720, y + 130), PANEL, c, 16, 3, kk)
        d.ellipse([x + 30, y + 30, x + 100, y + 100], fill=fade(mix(BG, c, 0.35), kk), outline=fade(c, kk), width=3)
        text(d, (x + 65, y + 65), n, 40, c, "Bold", "mm", k=kk)
        text(d, (x + 130, y + 65), s, 40, TXT, "Bold", "lm", k=kk)

# ---------------- 1. the problem ----------------
def s_analog(d, t, dur):
    chrome(d, "STEP 1 · THE PROBLEM", "The real world is analog", "Real signals change smoothly. Between any two values, there's always another one.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 260, 280, 1400, 520
    axes(d, x0, y0, w, h, k, "3.3 V")
    text(d, (x0 - 14, y0 + h), "0 V", 24, DIM, "Medium", "rm", k=k)
    text(d, (x0 + w, y0 + h + 30), "time", 26, DIM, "Medium", "rm", k=k)
    n = int(clamp((t - 0.6) / 4.0) * 300)
    pts = [(x0 + w * i / 300, vy(sig(i / 300), y0, h)) for i in range(n)]
    if len(pts) > 1: d.line(pts, fill=AMBER, width=6)
    if t > 5.0:
        kk = prog(t, 5.0, 5.6)
        u = 0.32; px, py = x0 + w * u, vy(sig(u), y0, h)
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=fade(TXT, kk))
        text(d, (px + 24, py - 30), f"{sig(u):.3f}… V", 32, TXT, "Bold", "lm", mono=True, k=kk)

def s_digital(d, t, dur):
    chrome(d, "STEP 1 · THE PROBLEM", "A digital pin: all or nothing", "A digital input only asks: above the threshold, or below? Everything in between is lost.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 260, 260, 1400, 330
    axes(d, x0, y0, w, h, k, "input")
    pts = [(x0 + w * i / 300, vy(sig(i / 300), y0, h)) for i in range(300)]
    d.line(pts, fill=fade(AMBER, k), width=5)
    kt = prog(t, 1.0, 1.6)
    ty = vy(1.65, y0, h)
    for xx in range(x0, x0 + w, 30): d.line([xx, ty, xx + 16, ty], fill=fade(RED, kt), width=3)
    text(d, (x0 + w + 10, ty), "threshold", 26, RED, "Bold", "lm", k=kt)
    y1, h1 = 680, 140
    k2 = prog(t, 2.2, 2.8)
    axes(d, x0, y1, w, h1, k2)
    text(d, (x0 + w + 10, y1 + h1 / 2), "pin reads", 26, CYAN, "Bold", "lm", k=k2)
    n = int(clamp((t - 2.6) / 3.0) * 300)
    out = []
    for i in range(n):
        hi = sig(i / 300) > 1.65
        out.append((x0 + w * i / 300, y1 + (10 if hi else h1 - 6)))
    if len(out) > 1: d.line(out, fill=CYAN, width=5)
    text(d, (x0 - 14, y1 + 10), "1", 30, CYAN, "Bold", "rm", mono=True, k=k2)
    text(d, (x0 - 14, y1 + h1 - 6), "0", 30, CYAN, "Bold", "rm", mono=True, k=k2)

def s_goal(d, t, dur):
    chrome(d, "STEP 1 · THE PROBLEM", "What we want: a number", "We want a number that says how big the voltage is: 0 V gives 0, full scale gives the biggest number.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, x1 = 300, 1620
    box(d, (x0, 380, x1, 450), PANEL, LINE, 12, 2, k)
    fill = 0.2 + 0.6 * (0.5 + 0.5 * math.sin(t * 0.9))
    if t > 1.0:
        d.rounded_rectangle([x0 + 4, 384, x0 + 4 + (x1 - x0 - 8) * fill, 446], 10, fill=mix(BG, AMBER, 0.8))
    text(d, (x0, 340), "0 V", 30, DIM, "Bold", "lm", k=k)
    text(d, (x1, 340), "3.3 V", 30, DIM, "Bold", "rm", k=k)
    text(d, (W // 2, 340), "input voltage", 30, AMBER, "Bold", "mm", k=k)
    arrow(d, (W // 2, 480), (W // 2, 580), DIM, 5, prog(t, 1.4, 2.0))
    k2 = prog(t, 1.8, 2.4)
    box(d, (x0, 610, x1, 680), PANEL, LINE, 12, 2, k2)
    text(d, (x0, 720), "0", 30, CYAN, "Bold", "lm", mono=True, k=k2)
    text(d, (x1, 720), "4095", 30, CYAN, "Bold", "rm", mono=True, k=k2)
    text(d, (W // 2, 645), f"{int(fill * 4095)}", 44, CYAN, "Bold", "mm", mono=True, k=k2)
    text(d, (W // 2, 790), "example: a 12-bit ADC with a 3.3 V reference", 28, DIM, "Medium", "mm", k=prog(t, 2.6, 3.2))

# ---------------- 2. one comparator ----------------
def s_comp(d, t, dur):
    chrome(d, "STEP 2 · ONE COMPARATOR", "The comparator", "If the + input is higher than the − input, the output goes high. Otherwise, low. That's all it does.", t, dur)
    k = prog(t, 0.2, 0.7)
    vp = 1.65 + 1.2 * math.sin(max(0, t - 1.5) * 0.9)
    vm = 1.65
    pin, nin, o = comparator(d, 820, 520, 150, k, out=vp > vm)
    # input level bars
    for (lab, v, y, c) in [("+", vp, pin[1], AMBER), ("−", vm, nin[1], PURPLE)]:
        d.line([560, y, pin[0], y], fill=fade(c, k), width=5)
        box(d, (300, y - 70, 360, y + 70), PANEL, LINE, 8, 2, k)
        hh = 136 * v / VREF
        d.rectangle([304, y + 68 - hh, 356, y + 68], fill=fade(c, k))
        text(d, (520, y), f"{v:.2f} V", 30, c, "Bold", "rm", mono=True, k=k)
    hi = vp > vm
    text(d, (o[0] + 90, o[1]), "1" if hi else "0", 80, GREEN if hi else DIM, "Bold", "lm", mono=True, k=k)
    text(d, (o[0] + 90, o[1] + 80), "output", 26, DIM, "Medium", "lm", k=k)

def s_onebit(d, t, dur):
    chrome(d, "STEP 2 · ONE COMPARATOR", "A one-bit ADC", "Tie the − input to half the reference, 1.65 V. Now it answers one question: top half, or bottom half?", t, dur)
    k = prog(t, 0.2, 0.7)
    vin = 2.2
    pin, nin, o = comparator(d, 760, 520, 130, k, out=t > 2.0, plus_lab="Vin = 2.2 V", minus_lab="1.65 V")
    if t > 2.0:
        text(d, (o[0] + 80, o[1]), "1", 72, GREEN, "Bold", "lm", mono=True, k=prog(t, 2.0, 2.4))
    x, y0, hh = 1460, 290, 500
    k2 = prog(t, 2.6, 3.2)
    box(d, (x, y0, x + 140, y0 + hh), PANEL, LINE, 10, 2, k2)
    d.rectangle([x + 4, y0 + 4, x + 136, y0 + hh / 2], fill=fade(mix(BG, GREEN, 0.3), k2))
    text(d, (x + 70, y0 + hh / 4), "1", 50, GREEN, "Bold", "mm", mono=True, k=k2)
    text(d, (x + 70, y0 + 3 * hh / 4), "0", 50, DIM, "Bold", "mm", mono=True, k=k2)
    d.line([x - 20, y0 + hh / 2, x + 160, y0 + hh / 2], fill=fade(PURPLE, k2), width=3)
    yy = y0 + hh - vin / VREF * hh
    d.line([x - 30, yy, x + 170, yy], fill=fade(AMBER, k2), width=5)
    text(d, (x + 180, yy), "2.2 V", 26, AMBER, "Bold", "lm", k=k2)
    text(d, (x + 180, y0 + hh / 2), "1.65 V", 26, PURPLE, "Bold", "lm", k=k2)

def s_more(d, t, dur):
    chrome(d, "STEP 2 · ONE COMPARATOR", "One answer isn't enough", "One bit gives just two levels. For more detail, we need more questions: more comparators.", t, dur)
    k = prog(t, 0.2, 0.7)
    for j, (nlev, lab, st) in enumerate([(2, "1 bit: 2 levels", 0.5), (4, "2 bits: 4 levels", 2.0), (8, "3 bits: 8 levels", 3.5)]):
        kk = prog(t, st, st + 0.6)
        x = 330 + j * 470
        box(d, (x, 300, x + 220, 780), PANEL, LINE, 10, 2, kk)
        for i in range(nlev):
            yy = 780 - (i + 1) * 480 / nlev
            d.rectangle([x + 6, yy + 3, x + 214, yy + 480 / nlev - 3], fill=fade(mix(BG, CYAN, 0.15 + 0.6 * i / max(1, nlev - 1)), kk))
        text(d, (x + 110, 830), lab, 30, TXT, "Bold", "mm", k=kk)

# ---------------- 3. flash ----------------
def ladder(d, x, top, bot, k, show_v=True):
    text(d, (x, top - 30), "Vref 3.3 V", 26, AMBER, "Bold", "mm", k=k)
    seg = (bot - top) / 8
    for i in range(8):
        resistor(d, x, top + i * seg, top + (i + 1) * seg, k)
    d.line([x - 24, bot, x + 24, bot], fill=fade(DIM, k), width=4)
    d.line([x - 14, bot + 10, x + 14, bot + 10], fill=fade(DIM, k), width=3)
    taps = []
    for i in range(1, 8):
        y = bot - i * seg
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=fade(PURPLE, k))
        if show_v: text(d, (x - 26, y), f"{TAPS[i-1] + 1e-9:.2f} V", 24, PURPLE, "Medium", "rm", mono=True, k=k)
        taps.append(y)
    return taps

def s_ladder(d, t, dur):
    chrome(d, "STEP 3 · THE FLASH ADC", "A ladder of references", "Equal resistors in a chain split the reference into evenly spaced voltages: a resistor ladder.", t, dur)
    k = prog(t, 0.2, 0.8)
    taps = ladder(d, 760, 290, 830, k)
    for i, y in enumerate(taps):
        kk = prog(t, 1.2 + i * 0.35, 1.6 + i * 0.35)
        d.line([767, y, 1000, y], fill=fade(PURPLE, kk), width=3)
        text(d, (1020, y), f"{i+1}/8 of Vref", 28, TXT, "Medium", "lm", k=kk)
    text(d, (1500, 560), "8 equal resistors", 30, DIM, "Bold", "mm", k=prog(t, 4.0, 4.6))
    text(d, (1500, 610), "→ 7 reference levels", 30, DIM, "Bold", "mm", k=prog(t, 4.0, 4.6))

def flash_bank(d, t, k, on_from=1.5, xs=520):
    taps = ladder(d, 300, 290, 830, k, show_v=False)
    vin = 2.2
    text(d, (xs + 40, 260), "Vin = 2.2 V (example)", 28, AMBER, "Bold", "lm", k=k)
    d.line([xs - 60, 270, xs - 60, 820], fill=fade(AMBER, k), width=4)
    outs = []
    for i, y in enumerate(taps):
        on = TAPS[i] < vin
        lit = on and t > on_from + i * 0.25
        pin, nin, o = comparator(d, xs, y, 30, k, col=GREEN if lit else LINE)
        d.line([307, y, xs, nin[1]], fill=fade(PURPLE, k * 0.7), width=2)
        d.line([xs - 60, pin[1], xs, pin[1]], fill=fade(AMBER, k * 0.7), width=2)
        d.ellipse([o[0] + 22, y - 12, o[0] + 46, y + 12], fill=fade(GREEN if lit else PANEL, k), outline=fade(LINE, k), width=2)
        text(d, (o[0] + 64, y), "1" if lit else "0", 36, GREEN if lit else DIM, "Bold", "lm", mono=True, k=k)
        outs.append((o[0] + 100, y))
    return outs

def s_flash(d, t, dur):
    chrome(d, "STEP 3 · THE FLASH ADC", "Seven comparators at once", "Every comparator whose reference is below the input switches on. Five light up, like a thermometer.", t, dur)
    k = prog(t, 0.2, 0.8)
    flash_bank(d, t, k)
    if t > 4.0:
        kk = prog(t, 4.0, 4.6)
        x, y0, y1 = 1300, 330, 800
        box(d, (x, y0, x + 70, y1), PANEL, LINE, 30, 3, kk)
        lev = 5 / 7
        d.rounded_rectangle([x + 10, y1 - 10 - (y1 - y0 - 20) * lev, x + 60, y1 - 10], 20, fill=fade(GREEN, kk))
        text(d, (x + 110, (y0 + y1) / 2 - 24), "thermometer", 34, GREEN, "Bold", "lm", k=kk)
        text(d, (x + 110, (y0 + y1) / 2 + 24), "code", 34, GREEN, "Bold", "lm", k=kk)

def s_encode(d, t, dur):
    chrome(d, "STEP 3 · THE FLASH ADC", "Thermometer code to binary", "An encoder counts how high the thermometer reached. Five on becomes 101, all in one step.", t, dur)
    k = prog(t, 0.2, 0.7)
    code = "0011111"
    for i, ch in enumerate(code):
        y = 300 + i * 70
        on = ch == "1"
        box(d, (300, y, 380, y + 56), PANEL, GREEN if on else LINE, 10, 3, k)
        text(d, (340, y + 28), ch, 36, GREEN if on else DIM, "Bold", "mm", mono=True, k=k)
    text(d, (340, 270), "comparators", 26, DIM, "Medium", "mm", k=k)
    arrow(d, (420, 530), (620, 530), DIM, 5, prog(t, 1.2, 1.8))
    k2 = prog(t, 1.6, 2.2)
    box(d, (640, 420, 1000, 640), PANEL, PURPLE, 16, 4, k2)
    text(d, (820, 510), "ENCODER", 44, TXT, "Bold", "mm", k=k2)
    text(d, (820, 565), "count the 1s", 28, DIM, "Medium", "mm", k=k2)
    arrow(d, (1020, 530), (1180, 530), DIM, 5, prog(t, 2.6, 3.2))
    k3 = prog(t, 3.0, 3.6)
    bits(d, 1210, 490, "101", 90, k3, GREEN)
    text(d, (1340, 640), "= 5", 50, GREEN, "Bold", "mm", mono=True, k=k3)

def s_cost(d, t, dur):
    chrome(d, "STEP 3 · THE FLASH ADC", "Fast, but expensive", "N bits need 2^N − 1 comparators. That's why flash converters are kept for jobs that need extreme speed.", t, dur)
    k = prog(t, 0.2, 0.7)
    text(d, (W // 2, 290), "comparators needed = 2ᴺ − 1", 44, AMBER, "Bold", "mm", mono=True, k=k)
    rows = [("3 bits", 7), ("8 bits", 255), ("12 bits", 4095)]
    for i, (lab, n) in enumerate(rows):
        kk = prog(t, 1.0 + i * 1.2, 1.6 + i * 1.2)
        y = 400 + i * 150
        text(d, (420, y + 40), lab, 40, TXT, "Bold", "rm", k=kk)
        cols = 64
        cells = min(n, 64 * 6)
        shown = int(cells * clamp((t - 1.0 - i * 1.2) / 1.0))
        for j in range(shown):
            r, c = divmod(j, cols)
            x, yy = 460 + c * 17, y + 6 + r * 13
            d.rectangle([x, yy, x + 12, yy + 9], fill=mix(BG, GREEN if i == 0 else (CYAN if i == 1 else RED), 0.85))
        text(d, (1580, y + 40), f"{n:,}", 44, AMBER if i < 2 else RED, "Bold", "lm", mono=True, k=kk)
    text(d, (W // 2, 860), "(12-bit row drawn partly: it would fill the screen)", 24, DIM, "Medium", "mm", k=prog(t, 4.6, 5.2))

# ---------------- 4. SAR ----------------
def s_sar(d, t, dur):
    chrome(d, "STEP 4 · SUCCESSIVE APPROXIMATION", "One comparator, many guesses", "Keep one comparator. Add a DAC that makes any test voltage we ask for. Then play a guessing game.", t, dur)
    k = prog(t, 0.2, 0.8)
    text(d, (260, 400), "Vin", 36, AMBER, "Bold", "rm", k=k)
    d.line([280, 400, 760, 400], fill=fade(AMBER, k), width=5)
    pin, nin, o = comparator(d, 760, 450, 100, k, col=CYAN)
    k2 = prog(t, 1.2, 1.8)
    box(d, (1240, 360, 1620, 540), PANEL, GREEN, 16, 4, k2)
    text(d, (1430, 430), "SAR logic", 40, TXT, "Bold", "mm", k=k2)
    text(d, (1430, 485), "keeps the guess", 26, DIM, "Medium", "mm", k=k2)
    arrow(d, (o[0], o[1]), (1230, 450), CYAN, 5, k2)
    text(d, (1080, 420), "higher?", 26, CYAN, "Bold", "mm", k=k2)
    k3 = prog(t, 2.4, 3.0)
    box(d, (720, 660, 1100, 820), PANEL, PURPLE, 16, 4, k3)
    text(d, (910, 720), "DAC", 44, TXT, "Bold", "mm", k=k3)
    text(d, (910, 775), "digital → analog", 26, DIM, "Medium", "mm", k=k3)
    d.line([1430, 540, 1430, 740], fill=fade(GREEN, k3), width=5)
    arrow(d, (1430, 740), (1110, 740), GREEN, 5, k3)
    text(d, (1270, 710), "guess", 26, GREEN, "Bold", "mm", k=k3)
    d.line([720, 740, 620, 740, 620, 500], fill=fade(PURPLE, k3), width=5)
    arrow(d, (620, 500), (755, 500), PURPLE, 5, k3)
    text(d, (600, 620), "test V", 26, PURPLE, "Bold", "rm", k=k3)

def s_game(d, t, dur):
    chrome(d, "STEP 4 · SUCCESSIVE APPROXIMATION", "Like guessing a number", "Is it above 50? Yes. Above 75? No. Each answer halves the range: a binary search.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, x1, y = 200, 1720, 520
    def X(v): return x0 + (x1 - x0) * (v - 1) / 99
    d.line([x0, y, x1, y], fill=fade(LINE, k), width=6)
    for v in (1, 25, 50, 75, 100):
        text(d, (X(v), y + 50), str(v), 28, DIM, "Medium", "mm", mono=True, k=k)
    steps = [(50, True, (51, 100)), (75, False, (51, 75)), (63, False, (51, 63)), (57, True, (58, 63))]
    lo, hi = 1, 100
    for i, (g, yes, rng) in enumerate(steps):
        st = 1.0 + i * 1.6
        if t < st: break
        kk = prog(t, st, st + 0.5)
        d.line([X(g), y - 60, X(g), y + 20], fill=fade(AMBER, kk), width=4)
        text(d, (X(g), y - 70 - i * 44), f"> {g}?  {'yes' if yes else 'no'}", 28, GREEN if yes else RED, "Bold", "mb", k=kk)
        if t > st + 0.8: lo, hi = rng
    d.rounded_rectangle([X(lo), y - 14, X(hi), y + 14], 10, fill=mix(BG, CYAN, 0.8))
    text(d, (W // 2, 720), f"still possible: {lo} to {hi}", 40, CYAN, "Bold", "mm", k=k)

def s_steps(d, t, dur):
    chrome(d, "STEP 4 · SUCCESSIVE APPROXIMATION", "Three guesses, three bits", "Convert 2.2 V with 3 bits: try 100, keep it. Try 110, too high. Try 101, keep it. Answer: 101.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 260, 280, 760, 560
    axes(d, x0, y0, w, h, k, "3.3 V")
    vin_y = vy(2.2, y0, h)
    for xx in range(x0, x0 + w, 26): d.line([xx, vin_y, xx + 14, vin_y], fill=fade(AMBER, k), width=4)
    text(d, (x0 + w + 12, vin_y), "Vin 2.2 V", 28, AMBER, "Bold", "lm", k=k)
    guesses = [("100", 1.65, True), ("110", 2.475, False), ("101", 2.0625, True)]
    for i, (code, v, keep) in enumerate(guesses):
        st = 1.0 + i * 2.6
        if t < st: break
        kk = prog(t, st, st + 0.6)
        bx = x0 + 60 + i * 240
        top = vy(v, y0, h)
        d.rectangle([bx, top, bx + 140, y0 + h], fill=fade(mix(BG, PURPLE, 0.5), kk), outline=fade(PURPLE, kk), width=3)
        text(d, (bx + 70, top + 30), f"{v + 1e-9:.2f} V", 26, TXT, "Bold", "mm", mono=True, k=kk)
        text(d, (bx + 70, y0 + h + 34), code, 32, TXT, "Bold", "mm", mono=True, k=kk)
        ky = prog(t, st + 1.0, st + 1.5)
        y = 330 + i * 140
        box(d, (1280, y, 1700, y + 110), PANEL, GREEN if keep else RED, 14, 3, ky)
        text(d, (1310, y + 34), f"try {code}", 32, TXT, "Bold", "lm", mono=True, k=ky)
        text(d, (1310, y + 78), "lower than Vin: keep 1" if keep else "too high: bit = 0", 26, GREEN if keep else RED, "Medium", "lm", k=ky)
    if t > 8.6:
        text(d, (1490, 790), "answer: 101 = 5", 40, GREEN, "Bold", "mm", mono=True, k=prog(t, 8.6, 9.2))

def s_twelve(d, t, dur):
    chrome(d, "STEP 4 · SUCCESSIVE APPROXIMATION", "Twelve bits, twelve guesses", "A 12-bit SAR repeats this 12 times, top bit first: one of 4,096 levels. Most microcontrollers use this kind.", t, dur)
    k = prog(t, 0.2, 0.7)
    target = 2730
    nb = int(clamp((t - 0.8) / 6.0) * 12 + 0.999) if t > 0.8 else 0
    code, guess, hist = 0, 0, []
    for b in range(nb):
        bit = 11 - b
        trial = code | (1 << bit)
        if trial <= target: code = trial
        hist.append(trial)
    s = format(code, "012b")
    bits(d, 250, 280, s, 120, k, CYAN, known=nb)
    x0, y0, w, h = 250, 420, 1420, 380
    axes(d, x0, y0, w, h, k)
    ty = y0 + h - target / 4096 * h
    for xx in range(x0, x0 + w, 26): d.line([xx, ty, xx + 14, ty], fill=fade(AMBER, k), width=3)
    text(d, (x0 + w + 10, ty), "Vin", 28, AMBER, "Bold", "lm", k=k)
    pts = []
    for i, tr in enumerate(hist):
        x = x0 + (i + 0.5) * w / 12
        yy = y0 + h - tr / 4096 * h
        pts.append((x, yy))
        col = GREEN if tr <= target else RED
        d.ellipse([x - 10, yy - 10, x + 10, yy + 10], fill=col)
    if len(pts) > 1: d.line(pts, fill=PURPLE, width=3)
    if nb == 12:
        text(d, (W // 2, 850), f"result: {code}  (example)", 36, GREEN, "Bold", "mm", mono=True, k=prog(t, 7.0, 7.5))

def s_dac(d, t, dur):
    chrome(d, "STEP 4 · SUCCESSIVE APPROXIMATION", "Inside the guess", "In many chips, the DAC is a bank of tiny capacitors sized in powers of two, switched in and out.", t, dur)
    k = prog(t, 0.2, 0.7)
    sizes = [1, 1, 2, 4, 8, 16, 32]
    labels = ["C", "C", "2C", "4C", "8C", "16C", "32C"]
    x = 220
    on = [0, 1, 0, 1, 1, 0, 1]
    for i, (s, lab) in enumerate(zip(sizes, labels)):
        kk = prog(t, 0.6 + i * 0.3, 1.0 + i * 0.3)
        wpl = 40 + s * 5
        cx = x + wpl / 2
        d.line([cx, 330, cx, 420], fill=fade(DIM, kk), width=3)
        d.rectangle([x, 420, x + wpl, 434], fill=fade(CYAN, kk))
        d.rectangle([x, 454, x + wpl, 468], fill=fade(CYAN, kk))
        text(d, (cx, 500), lab, 28, TXT, "Bold", "mm", k=kk)
        sw = on[i] and t > 3.5
        d.line([cx, 468, cx, 560], fill=fade(DIM, kk), width=3)
        d.line([cx, 560, cx + (24 if sw else -24), 620], fill=fade(GREEN if sw else DIM, kk), width=4)
        x += wpl + 40
    k2 = prog(t, 0.4, 0.9)
    d.line([220 + 20, 330, x - 40, 330], fill=fade(DIM, k2), width=3)
    text(d, (x - 20, 330), "to comparator", 26, DIM, "Medium", "lm", k=k2)
    text(d, (240, 680), "switches set by the guess bits", 30, GREEN, "Bold", "lm", k=prog(t, 3.5, 4.0))
    text(d, (240, 740), "simplified: real designs add sampling and reference switches", 24, DIM, "Medium", "lm", k=prog(t, 4.5, 5.0))

# ---------------- 5. sample and hold ----------------
def s_hold(d, t, dur):
    chrome(d, "STEP 5 · SAMPLE AND HOLD", "Freeze the input", "The guesses take time. So a switch charges a small capacitor, then opens, holding the voltage steady.", t, dur)
    k = prog(t, 0.2, 0.7)
    closed = t < 3.0
    text(d, (220, 360), "Vin", 34, AMBER, "Bold", "rm", k=k)
    d.line([240, 360, 420, 360], fill=fade(AMBER, k), width=5)
    d.ellipse([414, 354, 426, 366], fill=fade(TXT, k))
    d.line([420, 360, 520, 360 if closed else 310], fill=fade(GREEN if closed else RED, k), width=5)
    d.ellipse([514, 354, 526, 366], fill=fade(TXT, k))
    text(d, (470, 290), "closed: sample" if closed else "open: hold", 28, GREEN if closed else RED, "Bold", "mm", k=k)
    d.line([526, 360, 760, 360], fill=fade(DIM, k), width=5)
    d.line([680, 360, 680, 440], fill=fade(DIM, k), width=4)
    d.line([640, 440, 720, 440], fill=fade(CYAN, k), width=6)
    d.line([640, 462, 720, 462], fill=fade(CYAN, k), width=6)
    d.line([680, 462, 680, 520], fill=fade(DIM, k), width=4)
    d.line([660, 520, 700, 520], fill=fade(DIM, k), width=4)
    text(d, (740, 452), "C", 32, CYAN, "Bold", "lm", k=k)
    arrow(d, (760, 360), (880, 360), DIM, 5, k)
    text(d, (900, 360), "to the converter", 30, TXT, "Medium", "lm", k=k)
    x0, y0, w, h = 300, 580, 1320, 260
    k2 = prog(t, 0.8, 1.3)
    axes(d, x0, y0, w, h, k2)
    tt = clamp(t / 8.0)
    held = None
    pin, ph = [], []
    for i in range(int(tt * 200)):
        u = i / 200
        v = sig(u * 0.8)
        pin.append((x0 + w * u, vy(v, y0, h)))
        if u < 3.0 / 8.0: ph.append((x0 + w * u, vy(v, y0, h))); held = v
        else: ph.append((x0 + w * u, vy(held, y0, h)))
    if len(pin) > 1:
        d.line(pin, fill=mix(BG, AMBER, 0.5), width=3)
        d.line(ph, fill=CYAN, width=6)
    text(d, (x0 + w, y0 - 20), "input (faint)   held (cyan)", 24, DIM, "Medium", "rb", k=k2)

def s_rate(d, t, dur):
    chrome(d, "STEP 5 · SAMPLE AND HOLD", "Samples, again and again", "Repeat at a steady rate. Each sample is a dot. Join the dots and you get the signal back.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 260, 280, 1400, 520
    axes(d, x0, y0, w, h, k)
    pts = [(x0 + w * i / 300, vy(sig(i / 300), y0, h)) for i in range(300)]
    d.line(pts, fill=mix(BG, AMBER, 0.45 * k), width=4)
    n = int(clamp((t - 0.8) / 4.0) * 36)
    dots = []
    for i in range(n):
        u = (i + 0.5) / 36
        x, y = x0 + w * u, vy(sig(u), y0, h)
        d.line([x, y0 + h, x, y], fill=mix(BG, CYAN, 0.4), width=2)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=CYAN)
        dots.append((x, y))
    if t > 5.2 and len(dots) > 1:
        d.line(dots, fill=fade(GREEN, prog(t, 5.2, 5.8)), width=4)
    text(d, (x0 + w, y0 - 30), "36 samples across this window (example)", 26, DIM, "Medium", "rm", k=k)

def s_nyquist(d, t, dur):
    chrome(d, "STEP 5 · SAMPLE AND HOLD", "Sample fast enough", "Sample at more than twice the highest frequency. Too slow, and a fast wave fakes a slow one: aliasing.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, y0, w, h = 260, 300, 1400, 360
    axes(d, x0, y0, w, h, k)
    mid = y0 + h / 2
    f, fs = 9.0, 10.0  # cycles across window, samples across window
    pts = [(x0 + w * i / 600, mid - 150 * math.sin(2 * math.pi * f * i / 600)) for i in range(601)]
    d.line(pts, fill=mix(BG, AMBER, 0.6 * k), width=3)
    n = int(clamp((t - 1.0) / 3.0) * (fs + 1))
    for i in range(n):
        u = i / fs
        x, y = x0 + w * u, mid - 150 * math.sin(2 * math.pi * f * u + 1e-9)
        y = mid - 150 * math.sin(2 * math.pi * f * u)
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=CYAN)
    if t > 4.5:
        kk = prog(t, 4.5, 5.2)
        ap = [(x0 + w * i / 600, mid - 150 * math.sin(2 * math.pi * (f - fs) * i / 600)) for i in range(601)]
        for i in range(0, 600, 12):
            d.line([ap[i], ap[i + 6]], fill=fade(RED, kk), width=5)
        text(d, (x0 + w, y0 - 20), "what the samples suggest", 28, RED, "Bold", "rb", k=kk)
    text(d, (x0, y0 - 20), "real wave: 9 cycles · samples: 10 (too few)", 28, AMBER, "Bold", "lb", k=k)
    if t > 6.0:
        kk = prog(t, 6.0, 6.6)
        box(d, (360, 720, 1560, 830), PANEL, GREEN, 14, 3, kk)
        text(d, (960, 775), "audio CD: 44.1 kHz  >  2 × ~20 kHz (top of human hearing)", 32, GREEN, "Bold", "mm", k=kk)

# ---------------- 6. resolution and code ----------------
def stair(d, x0, y0, w, h, nbits, k, col):
    lv = 2 ** nbits
    pts = []
    for i in range(400):
        u = i / 400
        q = math.floor(u * lv) / lv
        pts.append((x0 + w * u, y0 + h - q * h))
    d.line(pts, fill=fade(col, k), width=4)
    d.line([x0, y0 + h, x0 + w, y0], fill=fade(mix(BG, AMBER, 0.6), k), width=2)

def s_res(d, t, dur):
    chrome(d, "STEP 6 · RESOLUTION", "More bits, finer steps", "3 bits: 8 levels. 5 bits: 32. 8 bits: 256. And 12 bits: 4,096, so fine it looks smooth.", t, dur)
    for i, (nb, lab, col) in enumerate([(3, "3 bits · 8 levels", RED), (5, "5 bits · 32 levels", AMBER), (8, "8 bits · 256 levels", GREEN)]):
        kk = prog(t, 0.5 + i * 1.4, 1.1 + i * 1.4)
        x0 = 180 + i * 560
        axes(d, x0, 300, 460, 460, kk)
        stair(d, x0, 300, 460, 460, nb, kk, col)
        text(d, (x0 + 230, 810), lab, 32, col, "Bold", "mm", k=kk)

def s_step(d, t, dur):
    chrome(d, "STEP 6 · RESOLUTION", "How small is one step?", "Step = Vref ÷ levels. 3.3 V ÷ 4,096 ≈ 0.8 mV. Anything inside one step gets the same number.", t, dur)
    k = prog(t, 0.2, 0.7)
    text(d, (W // 2, 300), "3.3 V ÷ 4,096 ≈ 0.8 mV per step", 56, AMBER, "Bold", "mm", mono=True, k=k)
    x0, y0 = 500, 420
    k2 = prog(t, 1.2, 1.8)
    for i in range(5):
        x = x0 + i * 200
        y = y0 + (4 - i) * 80
        d.line([x, y + 80 if i else y + 80, x, y], fill=fade(CYAN, k2), width=5)
        d.line([x, y, x + 200, y], fill=fade(CYAN, k2), width=5)
        text(d, (x + 100, y - 24), f"{2728 + i}", 28, CYAN, "Bold", "mm", mono=True, k=k2)
    d.line([x0, y0 + 400, x0 + 1000, y0], fill=fade(AMBER, k2 * 0.6), width=3)
    if t > 3.0:
        kk = prog(t, 3.0, 3.6)
        x = x0 + 2 * 200
        y = y0 + 2 * 80
        d.rectangle([x, y, x + 200, y + 80], outline=fade(GREEN, kk), width=3)
        text(d, (x + 220, y + 120), "every input in here reads 2730", 30, GREEN, "Bold", "lm", k=kk)
        text(d, (x + 220, y + 165), "= quantization error", 30, GREEN, "Medium", "lm", k=kk)

def s_ref(d, t, dur):
    chrome(d, "STEP 6 · RESOLUTION", "Everything is relative", "An ADC measures the input as a fraction of its reference. If the reference wobbles, every reading wobbles.", t, dur)
    k = prog(t, 0.2, 0.7)
    wob = 0.0 if t < 4.0 else 0.12 * math.sin((t - 4.0) * 7)
    ref = 3.3 + wob
    vin = 2.2
    for i, (lab, v, col) in enumerate([("Vin", vin, AMBER), ("Vref", ref, PURPLE)]):
        x = 420 + i * 260
        box(d, (x, 300, x + 140, 800), PANEL, LINE, 10, 2, k)
        hh = 492 * v / 3.6
        d.rectangle([x + 4, 796 - hh, x + 136, 796], fill=fade(col, k))
        text(d, (x + 70, 830), lab, 32, col, "Bold", "mm", k=k)
        text(d, (x + 70, 270), f"{v:.2f} V", 28, col, "Bold", "mm", mono=True, k=k)
    k2 = prog(t, 1.4, 2.0)
    code = round(vin / ref * 4095)
    text(d, (1060, 430), "reading =", 40, TXT, "Bold", "lm", k=k2)
    text(d, (1060, 510), "Vin ÷ Vref × 4,095", 40, CYAN, "Bold", "lm", mono=True, k=k2)
    text(d, (1060, 620), f"= {code}", 64, GREEN if wob == 0 else RED, "Bold", "lm", mono=True, k=k2)
    if t > 4.0:
        text(d, (1060, 720), "same input, different numbers", 32, RED, "Bold", "lm", k=prog(t, 4.0, 4.5))

def s_code(d, t, dur):
    chrome(d, "IN CODE", "From number back to volts", "Start a conversion, wait, read the result, then scale it: 2730 × 3.3 ÷ 4095 = 2.2 V.", t, dur)
    k = prog(t, 0.2, 0.7)
    lines = ["// illustrative: real function names depend on your chip", "",
             "adc_start();                      // sample, then 12 guesses",
             "while (!adc_done()) { }          // a few microseconds",
             "uint16_t raw = adc_read();        // e.g. 2730", "",
             "float volts = raw * 3.3f / 4095;  // = 2.20 V"]
    box(d, (160, 270, 1760, 290 + 40 + len(lines) * 62), (6, 10, 20), LINE, 14, 3, k)
    for i, ln in enumerate(lines):
        kk = prog(t, 0.5 + i * 0.5, 0.9 + i * 0.5)
        col = DIM if ln.startswith("//") else (GREEN if "volts" in ln else (AMBER if "raw" in ln else TXT))
        text(d, (200, 300 + i * 62), ln, 34, col, mono=True, k=kk)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "An ADC, built up", "One comparator. A ladder for flash. One comparator plus a DAC for SAR. Hold the input. Bits set the step.", t, dur)
    st = [("Compare", CYAN), ("Ladder", PURPLE), ("Guess", GREEN), ("Hold", AMBER), ("Bits", CYAN), ("Number", GREEN)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(st):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.2:
        text(d, (W // 2, 640), "2.2 V  →  2730", 60, AMBER, "Bold", "mm", mono=True, k=prog(t, 4.2, 4.8))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does your phone's touchscreen", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "sense your finger?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
          ("03_analog", s_analog, 8), ("04_digital", s_digital, 8), ("05_goal", s_goal, 8),
          ("06_comp", s_comp, 9), ("07_onebit", s_onebit, 8), ("08_more", s_more, 7),
          ("09_ladder", s_ladder, 8), ("10_flash", s_flash, 9), ("11_encode", s_encode, 8), ("12_cost", s_cost, 8),
          ("13_sar", s_sar, 8), ("14_game", s_game, 9), ("15_steps", s_steps, 11), ("16_twelve", s_twelve, 9), ("17_dac", s_dac, 8),
          ("18_hold", s_hold, 9), ("19_rate", s_rate, 8), ("20_nyquist", s_nyquist, 9),
          ("21_res", s_res, 8), ("22_step", s_step, 8), ("23_ref", s_ref, 8), ("24_code", s_code, 9),
          ("25_recap", s_recap, 8), ("26_end", s_end, 6)]

NARRATION = {
 "01_hook": "Your microcontroller only understands ones and zeros. Yet it can tell you the temperature of a room, or record your voice. So how does a chip that only knows numbers measure a smooth, analog voltage?",
 "02_cover": "That's the job of the analog to digital converter, or A D C. Today, we'll build one up from scratch. We'll start with a single comparator, grow it into a flash converter, then a smarter design called SAR. Then we'll add sample and hold, and finish with resolution, and real code.",
 "03_analog": "Out in the real world, things change smoothly. A temperature sensor's voltage creeps up as a room warms. A microphone's voltage wiggles with every sound wave. And between any two values, there's always another one.",
 "04_digital": "But a plain digital input pin only asks one question: is this voltage above a threshold, or below it? Everything above counts as a one. Everything below counts as a zero. All the detail in between is thrown away.",
 "05_goal": "What we really want is a number that tells us how big the voltage is. In this example, zero volts becomes zero, and the full three point three volts becomes the biggest number the converter can produce: four thousand and ninety five.",
 "06_comp": "Our first building block is the comparator. It has two inputs, plus and minus, and one output. If the plus input is higher than the minus input, the output goes high. If not, it goes low. That's all it does.",
 "07_onebit": "Connect the minus input to half the reference, one point six five volts, and you've built a one-bit A D C. It answers a single question: is the input in the top half, or the bottom half? Two point two volts? Top half. One.",
 "08_more": "But one bit only gives us two levels. To see more detail, we need to ask more questions. Two bits gives four levels. Three bits gives eight. The obvious way to get there? Use more comparators.",
 "09_ladder": "First, we need more reference voltages. Take a chain of equal resistors between the reference and ground. Each joint in the chain sits at a different voltage, evenly spaced. Eight resistors give us seven reference levels. That's a resistor ladder.",
 "10_flash": "Now give each joint its own comparator, and feed the input to all of them at once. With an input of two point two volts, every comparator whose reference is below the input switches on. Here, five of them turn on. It looks like a thermometer filling up.",
 "11_encode": "A small logic circuit called an encoder looks at how high the thermometer reached, and turns it into binary. Five comparators on means the number five, or one, zero, one. And the whole conversion happens in a single step.",
 "12_cost": "The catch? For N bits, you need two to the N, minus one comparators. Three bits takes seven. Eight bits takes two hundred and fifty five. Twelve bits would take four thousand and ninety five. So flash converters are kept for jobs that need extreme speed.",
 "13_sar": "So here's the smarter idea. Keep just one comparator. Add a D A C, a digital to analog converter, that can produce any test voltage we ask for. And add some logic to keep track of our guess. Then we play a guessing game.",
 "14_game": "You know this game. I'm thinking of a number from one to a hundred. Is it above fifty? Yes. Above seventy five? No. Above sixty three? No. Each answer cuts the possibilities in half. That's called a binary search.",
 "15_steps": "Let's convert two point two volts with three bits. First guess: one, zero, zero, which is one point six five volts. The input is higher, so we keep that one. Next, try one, one, zero, about two point four eight volts. Too high, so that bit becomes zero. Last, try one, zero, one, about two point zero six volts. That's below the input, so we keep it. The answer is one, zero, one, or five. The same answer as the flash converter.",
 "16_twelve": "A twelve-bit SAR converter does exactly the same thing, twelve times, one bit at a time, starting from the top. Each guess homes in on the input. Twelve comparisons pick one of four thousand and ninety six levels. This is the kind of A D C you'll find in most microcontrollers.",
 "17_dac": "And how does it make each test voltage? In many chips, that D A C is a bank of tiny capacitors, sized in powers of two. The guess bits switch them in and out. It's a neat trick that keeps the converter small and efficient.",
 "18_hold": "But there's a problem. Those twelve guesses take time, and the input might change halfway through. So first, a switch connects the input to a small capacitor. Then the switch opens, and the capacitor holds that voltage steady while the converter works. This is called sample and hold.",
 "19_rate": "The converter repeats this over and over, at a steady rate. Each sample is one dot. Join the dots, and you get back a picture of the original signal. The sampling rate is simply how many dots you take every second.",
 "20_nyquist": "So how fast is fast enough? The rule is: sample at more than twice the highest frequency in the signal. Sample too slowly, and a fast wave can masquerade as a slow one that was never there. That's called aliasing. It's why audio CDs use forty four point one kilohertz, comfortably above twice the roughly twenty kilohertz top of human hearing.",
 "21_res": "Next, resolution. That's the number of bits. Three bits gives eight levels: a coarse staircase. Five bits gives thirty two. Eight bits gives two hundred and fifty six. And twelve bits gives four thousand and ninety six, so fine that the staircase looks smooth.",
 "22_step": "How small is one step? Divide the reference voltage by the number of levels. With a three point three volt reference and twelve bits, one step is about zero point eight millivolts. Anything inside a single step gets the same number. That small rounding is called quantization error.",
 "23_ref": "And notice something. An A D C never measures volts directly. It measures the input as a fraction of its reference voltage. So if the reference is noisy, or drifts, every reading drifts with it. A clean, stable reference really matters.",
 "24_code": "In code, it usually looks something like this. Start a conversion, wait for it to finish, and read the result. Then turn it back into volts. In this example, a reading of two thousand seven hundred and thirty, times three point three, divided by four thousand and ninety five, gives two point two volts.",
 "25_recap": "So that's an A D C, built up. One comparator answers one question. A ladder of them makes a flash converter. One comparator, a D A C and a guessing game make a SAR. Sample and hold freezes the input. And the number of bits sets how fine each step is.",
 "26_end": "Next episode: how does your phone's touchscreen sense your finger? Subscribe so you don't miss it.",
}
OUTPUT = "how_an_adc_turns_the_real_world_into_numbers_ep8_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep8/{name}.mp4", f"ep8/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep8", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    for j in range(0, len(SCENES), 9):
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES[j:j + 9]):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save(f"ep8/sheet{j // 9 + 1}.jpg", quality=85)
