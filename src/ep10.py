import math, os, random, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
BLUE = (90, 150, 255)

# ---------------- helpers ----------------
def wave(d, x0, x1, yc, amp, col, k=1.0, cyc=6.0, t=0.0, speed=0.0, ampf=None, freqf=None, phasef=None,
         width=5, reveal=1.0):
    """A sine wave from x0 to x1. ampf/freqf/phasef take u in [0, 1] and shape the wave."""
    if k <= 0: return
    pts, ph = [], -speed * t * 2 * math.pi
    n = max(2, int((x1 - x0) / 3))
    du = 1.0 / n
    for i in range(int(n * clamp(reveal)) + 1):
        u = i * du
        a = ampf(u) if ampf else 1.0
        p = phasef(u) if phasef else 0.0
        pts.append((x0 + (x1 - x0) * u, yc - amp * a * math.sin(ph + p)))
        ph += 2 * math.pi * cyc * (freqf(u) if freqf else 1.0) * du
    if len(pts) > 1: d.line(pts, fill=fade(col, k), width=width, joint="curve")

def phone(d, x, y, w=150, h=280, k=1.0):
    """A generic phone outline (no brand)."""
    box(d, (x, y, x + w, y + h), (8, 12, 24), DIM, 28, 4, k)
    box(d, (x + 12, y + 28, x + w - 12, y + h - 28), PANEL, LINE, 10, 2, k)

def router(d, x, y, k=1.0, col=CYAN):
    """A generic box with two antennas; (x, y) is the top-left of the body."""
    d.line([x + 40, y, x + 20, y - 110], fill=fade(DIM, k), width=10)
    d.line([x + 200, y, x + 220, y - 110], fill=fade(DIM, k), width=10)
    box(d, (x, y, x + 240, y + 90), PANEL, col, 16, 4, k)
    for i in range(4):
        d.ellipse([x + 40 + i * 30, y + 38, x + 54 + i * 30, y + 52], fill=fade(GREEN if i < 3 else LINE, k))

def earbud(d, cx, cy, k=1.0, col=BLUE):
    d.ellipse([cx - 45, cy - 45, cx + 45, cy + 45], fill=fade(PANEL, k), outline=fade(col, k), width=5)
    d.rounded_rectangle([cx - 14, cy + 20, cx + 14, cy + 130], 14, fill=fade(PANEL, k), outline=fade(col, k), width=5)

def rings(d, cx, cy, t, col, k=1.0, n=5, gap=70, speed=90, maxr=520):
    for i in range(n):
        r = (t * speed + i * gap) % (n * gap)
        if r > maxr: continue
        a = (1 - r / (n * gap)) * k
        d.arc([cx - r, cy - r, cx + r, cy + r], -60, 60, fill=mix(BG, col, a * 0.8), width=5)

def block(d, x, y, w, h, label, sub, col, k=1.0, hot=False):
    box(d, (x, y, x + w, y + h), mix(BG, col, 0.25) if hot else PANEL, col if hot else LINE, 14, 4 if hot else 2, k)
    text(d, (x + w / 2, y + h / 2 - (16 if sub else 0)), label, 34, col if hot else TXT, "Bold", "mm", k=k)
    if sub: text(d, (x + w / 2, y + h / 2 + 26), sub, 22, DIM, "Medium", "mm", k=k)

def bits_row(d, bits, x0, x1, y, k=1.0, col=AMBER, size=44):
    n = len(bits)
    for i, b in enumerate(bits):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        text(d, (x, y), b, size, col, "Bold", "mm", mono=True, k=k)
    for i in range(1, n):
        x = x0 + i * (x1 - x0) / n
        d.line([x, y - 30, x, y + 300], fill=fade(mix(BG, LINE, 0.7), k), width=2)

def axis_circle(d, cx, cy, r, k=1.0):
    d.line([cx - r - 30, cy, cx + r + 30, cy], fill=fade(LINE, k), width=2)
    d.line([cx, cy - r - 30, cx, cy + r + 30], fill=fade(LINE, k), width=2)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fade(mix(BG, LINE, 0.8), k), width=2)

def dot(d, x, y, r, col, k=1.0):
    d.ellipse([x - r, y - r, x + r, y + r], fill=fade(col, k))

# ---------------- chapter 0: hook and cover ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "Your phone streams video with no wires. The wave carrying it wiggles about 2.4 billion times a second. How do bits ride on it?", t, dur)
    k = prog(t, 0.2, 0.7)
    router(d, 220, 470, k)
    phone(d, 1560, 330, 160, 300, k)
    wave(d, 480, 1530, 500, 60, CYAN, prog(t, 0.6, 1.2), cyc=9, t=t, speed=1.2)
    if t > 2.6:
        kk = prog(t, 2.6, 3.2)
        text(d, (W // 2, 330), "2,400,000,000", 84, AMBER, "Bold", "mm", mono=True, k=kk)
        text(d, (W // 2, 410), "wiggles every second", 34, DIM, "Medium", "mm", k=kk)
    if t > 4.4:
        text(d, (W // 2, 700), "where are the bits?", 44, TXT, "Bold", "mm", k=prog(t, 4.4, 4.9))

def s_cover(d, t, dur):
    chrome(d, "", "Here's what we'll cover", "Six steps: waves, modulation, inside the chip, Wi-Fi, Bluetooth, and sharing the air.", t, dur)
    items = [("1", "Radio waves", "what a 2.4 GHz wave is", CYAN), ("2", "Modulation", "how bits change a wave", AMBER),
             ("3", "Inside the chip", "transmit and receive", PURPLE), ("4", "Wi-Fi", "many carriers at once", GREEN),
             ("5", "Bluetooth", "hopping channels", BLUE), ("6", "Sharing the air", "same band, two jobs", RED)]
    for i, (n, a, b, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.45, 0.8 + i * 0.45)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 270 + row * 170
        box(d, (x, y, x + 720, y + 130), PANEL, c, 16, 3, kk)
        d.ellipse([x + 26, y + 30, x + 96, y + 100], fill=fade(c, kk))
        text(d, (x + 61, y + 65), n, 38, BG, "Bold", "mm", k=kk)
        text(d, (x + 130, y + 46), a, 40, TXT, "Bold", "lm", k=kk)
        text(d, (x + 130, y + 94), b, 28, DIM, "Medium", "lm", k=kk)

# ---------------- chapter 1: radio waves ----------------
def s_wave(d, t, dur):
    chrome(d, "STEP 1 · RADIO WAVES", "Shake charge, make a wave", "Push electrons back and forth in an antenna, fast, and it launches a radio wave that spreads out at the speed of light.", t, dur)
    k = prog(t, 0.2, 0.6)
    ax, ay = 420, 560
    d.line([ax, ay - 200, ax, ay + 200], fill=fade(DIM, k), width=12)
    d.rectangle([ax - 50, ay + 200, ax + 50, ay + 250], fill=fade(PANEL, k), outline=fade(LINE, k), width=3)
    s = math.sin(t * 2 * math.pi * 1.0)
    for i in range(5):
        y = ay - 160 + i * 80 + s * 30
        d.ellipse([ax - 9, y - 9, ax + 9, y + 9], fill=fade(AMBER, k))
    arrow(d, (ax - 60, ay - 40 * s), (ax - 60, ay + 40 * s - 1 if abs(s) > 0.05 else ay + 1), AMBER, 4, k * abs(s))
    text(d, (ax - 90, ay), "electrons", 28, AMBER, "Bold", "rm", k=k)
    rings(d, ax, ay, t, CYAN, prog(t, 1.0, 1.6), n=6, gap=60, speed=80, maxr=330)
    if t > 3.5:
        text(d, (1400, 330), "≈ 300,000 km/s", 48, CYAN, "Bold", "mm", mono=True, k=prog(t, 3.5, 4.0))
        text(d, (1400, 390), "the speed of light", 30, DIM, "Medium", "mm", k=prog(t, 3.5, 4.0))

def s_freq(d, t, dur):
    chrome(d, "STEP 1 · RADIO WAVES", "Frequency and wavelength", "2.4 GHz means 2.4 billion cycles a second. Light-speed divided by that gives a wavelength of about 12.5 centimetres.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, yc = 200, 1720, 500
    d.line([x0, yc, x1, yc], fill=fade(LINE, k), width=2)
    wave(d, x0, x1, yc, 140, CYAN, k, cyc=4, reveal=prog(t, 0.3, 2.0))
    lam = (x1 - x0) / 4
    xa, xb = x0 + lam * 0.25, x0 + lam * 1.25
    kk = prog(t, 2.2, 2.7)
    if kk > 0:
        d.line([xa, 330, xa, 680], fill=fade(AMBER, kk), width=2)
        d.line([xb, 330, xb, 680], fill=fade(AMBER, kk), width=2)
        arrow(d, ((xa + xb) / 2, 320), (xa + 4, 320), AMBER, 4, kk)
        arrow(d, ((xa + xb) / 2, 320), (xb - 4, 320), AMBER, 4, kk)
        text(d, ((xa + xb) / 2, 280), "one wavelength", 32, AMBER, "Bold", "mm", k=kk)
    k3 = prog(t, 3.4, 3.9)
    box(d, (980, 640, 1720, 800), PANEL, LINE, 14, 2, k3)
    text(d, (1350, 690), "300,000 km/s ÷ 2.4 GHz", 36, TXT, "Bold", "mm", mono=True, k=k3)
    text(d, (1350, 750), "≈ 12.5 cm", 44, AMBER, "Bold", "mm", mono=True, k=prog(t, 4.2, 4.7))

def s_bands(d, t, dur):
    chrome(d, "STEP 1 · RADIO WAVES", "Two radios, one band", "Wi-Fi uses the 2.4 and 5 GHz bands, and 6 GHz on newer gear. Bluetooth lives in the same 2.4 GHz band.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 200, 1720, 640
    def X(f): return x0 + (f - 2.0) / (7.5 - 2.0) * (x1 - x0)
    d.line([x0, y, x1, y], fill=fade(LINE, k), width=4)
    for f in range(2, 8):
        d.line([X(f), y, X(f), y + 16], fill=fade(DIM, k), width=3)
        text(d, (X(f), y + 46), f"{f} GHz", 28, DIM, "Medium", "mm", k=k)
    bands = [(2.4, 2.4835, "2.4 GHz", GREEN, 0.8), (5.15, 5.85, "5 GHz", GREEN, 1.8), (5.925, 7.125, "6 GHz (newer)", GREEN, 2.6)]
    for a, b, lab, c, st in bands:
        kk = prog(t, st, st + 0.5)
        xa, xb = X(a), max(X(b), X(a) + 18)
        d.rectangle([xa, y - 220, xb, y - 4], fill=fade(mix(BG, c, 0.3), kk), outline=fade(c, kk), width=3)
        text(d, ((xa + xb) / 2, y - 250), lab, 30, c, "Bold", "mm", k=kk)
    kk = prog(t, 3.6, 4.1)
    xa = X(2.4)
    d.rectangle([xa - 6, y - 140, xa + 24, y - 4], fill=fade(BLUE, kk))
    text(d, (X(6.3), y - 310), "Wi-Fi bands", 34, GREEN, "Bold", "mm", k=prog(t, 0.8, 1.3))
    if kk > 0:
        arrow(d, (xa + 160, 300), (xa + 30, y - 150), BLUE, 4, kk)
        text(d, (xa + 180, 290), "Bluetooth shares 2.4 GHz", 32, BLUE, "Bold", "lm", k=kk)

# ---------------- chapter 2: modulation ----------------
def s_carrier(d, t, dur):
    chrome(d, "STEP 2 · MODULATION", "A perfect wave says nothing", "A steady wave carries no information. To send bits, the radio has to change something about it.", t, dur)
    k = prog(t, 0.2, 0.6)
    wave(d, 200, 1720, 430, 110, CYAN, k, cyc=10, t=t, speed=0.8)
    if t > 2.0:
        kk = prog(t, 2.0, 2.5)
        for i, (lab, c) in enumerate([("amplitude", AMBER), ("frequency", PURPLE), ("phase", GREEN)]):
            x = 420 + i * 540
            box(d, (x - 200, 680, x + 200, 790), PANEL, c, 14, 3, prog(t, 2.0 + i * 0.5, 2.5 + i * 0.5))
            text(d, (x, 735), lab, 40, c, "Bold", "mm", k=prog(t, 2.0 + i * 0.5, 2.5 + i * 0.5))
        text(d, (W // 2, 620), "three things you can change", 32, DIM, "Medium", "mm", k=kk)

def s_ask(d, t, dur):
    chrome(d, "STEP 2 · MODULATION", "Change the amplitude", "The simplest trick: a big wave for 1, a small wave for 0. That's amplitude shift keying.", t, dur)
    k = prog(t, 0.2, 0.6)
    bits = "10110"
    x0, x1 = 260, 1660
    bits_row(d, bits, x0, x1, 300, k)
    def A(u): return 1.0 if bits[min(4, int(u * 5))] == "1" else 0.25
    wave(d, x0, x1, 520, 140, AMBER, k, cyc=15, ampf=A, reveal=prog(t, 0.6, 3.6))
    text(d, (W // 2, 760), "big = 1   ·   small = 0", 34, DIM, "Medium", "mm", k=prog(t, 3.6, 4.1))

def s_fsk(d, t, dur):
    chrome(d, "STEP 2 · MODULATION", "Change the frequency", "Or shift the frequency: slightly higher for 1, slightly lower for 0. Bluetooth uses a smooth version of this, called GFSK.", t, dur)
    k = prog(t, 0.2, 0.6)
    bits = "10110"
    x0, x1 = 260, 1660
    bits_row(d, bits, x0, x1, 300, k)
    def F(u): return 1.5 if bits[min(4, int(u * 5))] == "1" else 0.7
    wave(d, x0, x1, 520, 140, PURPLE, k, cyc=12, freqf=F, reveal=prog(t, 0.6, 3.6))
    text(d, (W // 2, 760), "faster = 1   ·   slower = 0   (exaggerated)", 34, DIM, "Medium", "mm", k=prog(t, 3.6, 4.1))

def s_psk(d, t, dur):
    chrome(d, "STEP 2 · MODULATION", "Change the phase", "Or flip the wave's timing, its phase. Two phases give 1 bit per symbol. Four phases give 2 bits.", t, dur)
    k = prog(t, 0.2, 0.6)
    bits = "1001"
    x0, x1 = 160, 1060
    def P(u): return 0.0 if bits[min(3, int(u * 4))] == "1" else math.pi
    text(d, (x0, 300), "1 bit per symbol", 30, GREEN, "Bold", "lm", k=k)
    for i, b in enumerate(bits):
        text(d, (x0 + (i + 0.5) * (x1 - x0) / 4, 360), b, 40, AMBER, "Bold", "mm", mono=True, k=k)
    wave(d, x0, x1, 500, 100, GREEN, k, cyc=8, phasef=P, reveal=prog(t, 0.6, 3.0))
    for i in range(1, 4):
        x = x0 + i * (x1 - x0) / 4
        d.line([x, 390, x, 620], fill=fade(mix(BG, LINE, 0.7), k), width=2)
    cx, cy, r = 1480, 520, 200
    kk = prog(t, 3.2, 3.7)
    axis_circle(d, cx, cy, r, kk)
    text(d, (cx, 280), "4 phases = 2 bits", 30, GREEN, "Bold", "mm", k=kk)
    for i, lab in enumerate(["00", "01", "11", "10"]):
        a = math.pi / 4 + i * math.pi / 2
        px, py = cx + r * math.cos(a), cy - r * math.sin(a)
        dot(d, px, py, 16, GREEN, prog(t, 3.6 + i * 0.3, 4.0 + i * 0.3))
        text(d, (px + (40 if math.cos(a) > 0 else -40), py - 36), lab, 30, AMBER, "Bold", "mm", mono=True,
             k=prog(t, 3.6 + i * 0.3, 4.0 + i * 0.3))

def s_qam(d, t, dur):
    chrome(d, "STEP 2 · MODULATION", "Change two things at once", "Wi-Fi changes amplitude and phase together. Sixteen possible points means each symbol carries 4 bits.", t, dur)
    k = prog(t, 0.2, 0.6)
    cx, cy, s = 700, 560, 90
    d.line([cx - 330, cy, cx + 330, cy], fill=fade(LINE, k), width=2)
    d.line([cx, cy - 300, cx, cy + 300], fill=fade(LINE, k), width=2)
    text(d, (cx + 340, cy), "I", 30, DIM, "Bold", "lm", k=k)
    text(d, (cx, cy - 320), "Q", 30, DIM, "Bold", "mm", k=k)
    lv = [-3, -1, 1, 3]
    gray = ["00", "01", "11", "10"]
    for i, a in enumerate(lv):
        for j, b in enumerate(lv):
            kk = prog(t, 0.6 + (i * 4 + j) * 0.1, 1.0 + (i * 4 + j) * 0.1)
            hot = (i, j) == (3, 2) and t > 3.2
            dot(d, cx + a * s / 1.0 * 0.85, cy - b * s * 0.85, 22 if hot else 14, AMBER if hot else CYAN, kk)
    if t > 3.2:
        kk = prog(t, 3.2, 3.7)
        px, py = cx + 3 * s * 0.85, cy - 1 * s * 0.85
        d.ellipse([px - 36, py - 36, px + 36, py + 36], outline=fade(AMBER, kk), width=4)
        arrow(d, (1200, 420), (px + 44, py - 20), AMBER, 4, kk)
        box(d, (1200, 330, 1700, 500), PANEL, AMBER, 14, 3, kk)
        text(d, (1450, 380), "this point means (example)", 30, DIM, "Medium", "mm", k=kk)
        text(d, (1450, 448), gray[3] + gray[2], 60, AMBER, "Bold", "mm", mono=True, k=kk)
    k4 = prog(t, 4.2, 4.7)
    text(d, (1450, 620), "16 points = 4 bits", 40, TXT, "Bold", "mm", k=k4)
    text(d, (1450, 690), "1024 points = 10 bits", 34, DIM, "Medium", "mm", k=prog(t, 4.8, 5.3))
    text(d, (1450, 740), "(used by recent Wi-Fi)", 26, DIM, "Medium", "mm", k=prog(t, 4.8, 5.3))

def s_noise(d, t, dur):
    chrome(d, "STEP 2 · MODULATION", "Noise blurs the points", "Noise smears every point. Close to the router, points stay tight. Far away they blur, so the radio drops to fewer points.", t, dur)
    k = prog(t, 0.2, 0.6)
    rnd = random.Random(10)
    for p, (cx, lab, sig, n, col) in enumerate([(560, "close: 64 points", 7, 8, GREEN), (1360, "far: 4 points", 28, 2, AMBER)]):
        kk = prog(t, 0.4 + p * 1.6, 0.9 + p * 1.6)
        box(d, (cx - 320, 260, cx + 320, 800), (8, 12, 24), LINE, 14, 2, kk)
        text(d, (cx, 300), lab, 32, col, "Bold", "mm", k=kk)
        cy, span = 550, 420
        for i in range(n):
            for j in range(n):
                x = cx - span / 2 + (i + 0.5) * span / n
                y = cy - span / 2 + (j + 0.5) * span / n
                for _ in range(10 if n == 8 else 60):
                    dx, dy = rnd.gauss(0, sig), rnd.gauss(0, sig)
                    d.ellipse([x + dx - 3, y + dy - 3, x + dx + 3, y + dy + 3], fill=fade(mix(BG, col, 0.8), kk))
    text(d, (W // 2, 840 - 20), "", 10, DIM, k=k)

# ---------------- chapter 3: inside the chip ----------------
TX = [("bits", "", AMBER), ("DSP", "symbols", PURPLE), ("DAC", "digital → analog", CYAN), ("mixer", "× 2.4 GHz", GREEN), ("PA", "power amp", RED)]
RX = [("LNA", "low-noise amp", RED), ("mixer", "× 2.4 GHz", GREEN), ("ADC", "analog → digital", CYAN), ("DSP", "decode", PURPLE), ("bits", "", AMBER)]

def chain(d, t, items, antenna_first, k):
    x0, w, gap, y, h = 160 if antenna_first else 120, 240, 50, 500, 140
    if antenna_first: x0 = 380
    hot = int(clamp((t - 1.0) / 5.0) * len(items) - 1e-6) if t > 1.0 else -1
    for i, (a, b, c) in enumerate(items):
        x = x0 + i * (w + gap)
        block(d, x, y, w, h, a, b, c, k, hot == i)
        if i < len(items) - 1:
            arrow(d, (x + w + 4, y + h / 2), (x + w + gap - 4, y + h / 2), DIM if hot <= i else c, 4, k)
    ax = x0 + len(items) * (w + gap) + 40 if not antenna_first else 220
    d.line([ax, y - 120, ax, y + h / 2], fill=fade(DIM, k), width=10)
    if antenna_first:
        arrow(d, (ax + 6, y + h / 2), (x0 - 6, y + h / 2), DIM if hot < 0 else RED, 4, k)
        rings(d, ax, y - 120, -t, CYAN, k * 0.8, n=4, gap=45, speed=60, maxr=170)
    else:
        lx = x0 + (len(items) - 1) * (w + gap) + w
        arrow(d, (lx + 4, y + h / 2), (ax - 6, y + h / 2), RED if hot >= len(items) - 1 else DIM, 4, k)
        if t > 6.0: rings(d, ax, y - 120, t, CYAN, prog(t, 6.0, 6.4), n=4, gap=45, speed=70, maxr=170)

def s_tx(d, t, dur):
    chrome(d, "STEP 3 · INSIDE THE CHIP", "The transmit chain", "Bits become symbols, a DAC turns them into a voltage, a mixer lifts it up to 2.4 GHz, and an amplifier drives the antenna.", t, dur)
    k = prog(t, 0.2, 0.6)
    chain(d, t, TX, False, k)
    text(d, (W // 2, 740), "all on one small chip, plus a few parts around it", 32, DIM, "Medium", "mm", k=prog(t, 5.6, 6.1))

def s_rx(d, t, dur):
    chrome(d, "STEP 3 · INSIDE THE CHIP", "The receive chain", "Receiving runs it backwards: amplify a faint signal, mix it back down, and use an ADC, like in episode 8, to turn it into numbers.", t, dur)
    k = prog(t, 0.2, 0.6)
    chain(d, t, RX, True, k)
    text(d, (1360, 740), "the ADC from episode 8", 30, CYAN, "Bold", "mm", k=prog(t, 4.0, 4.5))

def s_antenna(d, t, dur):
    chrome(d, "STEP 3 · INSIDE THE CHIP", "The antenna is a tuned wire", "Many antennas are about a quarter of a wavelength long. At 2.4 GHz that's around 3 centimetres: a short trace on the board.", t, dur)
    k = prog(t, 0.2, 0.6)
    box(d, (300, 300, 1300, 780), (12, 50, 36), (40, 110, 80), 18, 4, k)
    chip(d, 520, 450, 260, 200, "radio", "Wi-Fi + BT", CYAN, k)
    d.line([780, 550, 1000, 550], fill=fade(AMBER, k), width=8)
    kk = prog(t, 1.2, 2.4)
    pts = [(1000, 550), (1000, 360), (1000 + 220 * kk, 360)]
    d.line(pts, fill=fade(AMBER, k), width=10, joint="curve")
    d.line([1060, 550, 1060, 360], fill=fade(AMBER, kk), width=10)
    d.line([1060, 550, 1060, 600], fill=fade(DIM, kk), width=6)
    text(d, (1060, 630), "ground", 24, DIM, "Medium", "mm", k=kk)
    k3 = prog(t, 2.8, 3.3)
    if k3 > 0:
        d.line([1000, 320, 1220, 320], fill=fade(TXT, k3), width=2)
        text(d, (1110, 290), "≈ 3 cm (example)", 28, TXT, "Bold", "mm", k=k3)
    wave(d, 1360, 1760, 540, 70, CYAN, prog(t, 3.6, 4.1), cyc=1, reveal=prog(t, 3.6, 4.6), width=4)
    d.line([1360, 640, 1460, 640], fill=fade(AMBER, prog(t, 4.6, 5.1)), width=6)
    text(d, (1560, 690), "¼ of 12.5 cm", 30, AMBER, "Bold", "mm", k=prog(t, 4.6, 5.1))
    text(d, (1560, 400), "one wavelength", 26, DIM, "Medium", "mm", k=prog(t, 3.6, 4.1))

# ---------------- chapter 4: Wi-Fi ----------------
def s_ofdm(d, t, dur):
    chrome(d, "STEP 4 · WI-FI", "Many slow carriers, side by side", "Wi-Fi splits its channel into many narrow subcarriers, each carrying its own symbol. Classic 20 MHz Wi-Fi uses 52.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 260, 1660, 640
    d.line([x0 - 40, y, x1 + 40, y], fill=fade(LINE, k), width=3)
    text(d, (x1 + 40, y + 40), "frequency", 26, DIM, "Medium", "rm", k=k)
    k1 = prog(t, 0.4, 1.0) * (1 - prog(t, 2.0, 2.6))
    if k1 > 0:
        d.rectangle([x0, y - 260, x1, y], fill=fade(mix(BG, GREEN, 0.25), k1), outline=fade(GREEN, k1), width=3)
        text(d, (W // 2, y - 300), "one 20 MHz channel", 32, GREEN, "Bold", "mm", k=k1)
    n = 52
    for i in range(n):
        kk = prog(t, 2.2 + i * 0.03, 2.6 + i * 0.03)
        if kk <= 0: continue
        x = x0 + (i + 0.5) * (x1 - x0) / n
        hh = 220 if i % 13 != 6 else 180
        col = PURPLE if i % 13 == 6 else GREEN
        d.line([x, y, x, y - hh * kk], fill=fade(col, kk), width=10)
    k3 = prog(t, 4.4, 4.9)
    text(d, (W // 2, 330), "52 subcarriers (48 data + 4 pilot)", 34, TXT, "Bold", "mm", k=k3)
    text(d, (W // 2, 720), "wider channels and newer Wi-Fi use many more", 28, DIM, "Medium", "mm", k=k3)

def s_multipath(d, t, dur):
    chrome(d, "STEP 4 · WI-FI", "Why slow symbols win: echoes", "Indoors, the signal bounces off walls, so echoes arrive late. Long, slow symbols with a short guard gap let echoes fade first.", t, dur)
    k = prog(t, 0.2, 0.6)
    d.rectangle([140, 270, 1060, 290], fill=fade(LINE, k))
    d.rectangle([140, 770, 1060, 790], fill=fade(LINE, k))
    router(d, 180, 560, k)
    phone(d, 880, 440, 130, 240, k)
    p = prog(t, 0.6, 2.2)
    arrow(d, (430, 590), (430 + (870 - 430) * p, 590), CYAN, 5, k)
    p2 = prog(t, 1.4, 3.0)
    if p2 > 0:
        mid = (650, 292)
        if p2 < 0.5:
            q = p2 / 0.5; d.line([(420, 540), (420 + (650 - 420) * q, 540 + (292 - 540) * q)], fill=AMBER, width=4)
        else:
            q = (p2 - 0.5) / 0.5
            d.line([(420, 540), mid], fill=AMBER, width=4)
            arrow(d, mid, (650 + (875 - 650) * q, 292 + (480 - 292) * q), AMBER, 4)
    p3 = prog(t, 1.8, 3.4)
    if p3 > 0:
        mid = (620, 768)
        if p3 < 0.5:
            q = p3 / 0.5; d.line([(420, 650), (420 + (620 - 420) * q, 650 + (768 - 650) * q)], fill=PURPLE, width=4)
        else:
            q = (p3 - 0.5) / 0.5
            d.line([(420, 650), mid], fill=PURPLE, width=4)
            arrow(d, mid, (620 + (875 - 620) * q, 768 + (660 - 768) * q), PURPLE, 4)
    k4 = prog(t, 3.6, 4.1)
    x0, y = 1180, 420
    for i in range(3):
        x = x0 + i * 220
        d.rectangle([x, y, x + 40, y + 80], fill=fade(mix(BG, DIM, 0.4), k4))
        d.rectangle([x + 40, y, x + 210, y + 80], fill=fade(mix(BG, GREEN, 0.4), k4), outline=fade(GREEN, k4), width=2)
    text(d, (x0 + 20, y - 30), "guard", 24, DIM, "Bold", "mm", k=k4)
    text(d, (x0 + 125, y + 40), "symbol", 26, TXT, "Bold", "mm", k=k4)
    text(d, (x0 + 320, y + 140), "echoes die down in the guard gap", 28, DIM, "Medium", "mm", k=prog(t, 4.4, 4.9))
    text(d, (x0 + 320, y + 190), "(about 4 µs per symbol in classic Wi-Fi)", 24, DIM, "Medium", "mm", k=prog(t, 4.4, 4.9))

def s_csma(d, t, dur):
    chrome(d, "STEP 4 · WI-FI", "Listen before you talk", "Only one device should talk at a time on a channel. So each one listens first, waits a random moment, then sends.", t, dur)
    k = prog(t, 0.2, 0.6)
    lanes = [("laptop", CYAN), ("phone", GREEN), ("tablet", PURPLE)]
    x0, x1 = 400, 1720
    p = clamp((t - 0.6) / 5.4)
    for i, (n, c) in enumerate(lanes):
        y = 340 + i * 150
        text(d, (360, y), n, 32, c, "Bold", "rm", k=k)
        d.line([x0, y, x1, y], fill=fade(LINE, k), width=2)
    spans = [(0, 0.0, 0.28, CYAN, "sending"), (1, 0.28, 0.40, DIM, "wait"), (2, 0.28, 0.48, DIM, "wait"),
             (1, 0.40, 0.66, GREEN, "sending"), (2, 0.66, 0.74, DIM, "wait"), (2, 0.74, 0.98, PURPLE, "sending")]
    for lane, a, b, c, lab in spans:
        if p <= a: continue
        e = min(p, b)
        y = 340 + lane * 150
        xa, xb = x0 + (x1 - x0) * a, x0 + (x1 - x0) * e
        if c == DIM:
            d.rectangle([xa, y - 10, xb, y + 10], fill=mix(BG, DIM, 0.4))
        else:
            d.rectangle([xa, y - 26, xb, y + 26], fill=c)
        if e - a > 0.06: text(d, ((xa + xb) / 2, y - 50), lab, 24, c if c != DIM else DIM, "Bold", "mm")
    text(d, (W // 2, 790), "busy? wait a random backoff, then try", 32, DIM, "Medium", "mm", k=prog(t, 4.0, 4.5))

def s_packet(d, t, dur):
    chrome(d, "STEP 4 · WI-FI", "Anatomy of one packet", "Each packet starts with a known preamble to sync up, then a header, then your data. The receiver answers with a short ACK.", t, dur)
    k = prog(t, 0.2, 0.6)
    parts = [("preamble", "sync up", PURPLE, 260), ("header", "rate, length", CYAN, 240), ("data", "your bits", GREEN, 700)]
    x, y = 200, 420
    for i, (a, b, c, w) in enumerate(parts):
        kk = prog(t, 0.5 + i * 0.7, 0.9 + i * 0.7)
        box(d, (x, y, x + w, y + 150), mix(BG, c, 0.25), c, 10, 3, kk)
        text(d, (x + w / 2, y + 55), a, 36, TXT, "Bold", "mm", k=kk)
        text(d, (x + w / 2, y + 105), b, 26, DIM, "Medium", "mm", k=kk)
        x += w + 10
    kk = prog(t, 3.2, 3.7)
    box(d, (x + 90, y + 30, x + 270, y + 120), mix(BG, AMBER, 0.25), AMBER, 10, 3, kk)
    text(d, (x + 180, y + 75), "ACK", 36, AMBER, "Bold", "mm", k=kk)
    text(d, (x + 45, y + 200), "gap", 24, DIM, "Medium", "mm", k=kk)
    text(d, (W // 2, 720), "no ACK? the sender tries again", 32, DIM, "Medium", "mm", k=prog(t, 4.2, 4.7))

# ---------------- chapter 5: Bluetooth ----------------
def hop_grid(d, t, k, nch, x0, x1, y0, y1, seed, busy=None, start=0.8, rate=6.0, col=BLUE):
    d.rectangle([x0, y0, x1, y1], fill=fade((8, 12, 24), k), outline=fade(LINE, k), width=2)
    if busy:
        a, b = busy
        ya, yb = y1 - (b + 1) * (y1 - y0) / nch, y1 - a * (y1 - y0) / nch
        d.rectangle([x0, ya, x1, yb], fill=fade(mix(BG, GREEN, 0.25), k))
        text(d, (x1 - 20, (ya + yb) / 2), "busy Wi-Fi channel", 26, GREEN, "Bold", "rm", k=k)
    rnd = random.Random(seed)
    n = int(clamp((t - start) / 5.0) * 40)
    slot = (x1 - x0) / 40
    prev = None
    for i in range(n):
        while True:
            c = rnd.randrange(nch)
            if not busy or not (busy[0] <= c <= busy[1]): break
        x = x0 + (i + 0.5) * slot
        y = y1 - (c + 0.5) * (y1 - y0) / nch
        d.rectangle([x - slot * 0.35, y - 6, x + slot * 0.35, y + 6], fill=col)
        if prev: d.line([prev, (x, y)], fill=mix(BG, col, 0.35), width=2)
        prev = (x, y)
    text(d, (x0 - 20, y0 + 10), "channel", 24, DIM, "Medium", "rm", k=k)
    text(d, (x1, y1 + 30), "time", 24, DIM, "Medium", "rm", k=k)

def s_hop(d, t, dur):
    chrome(d, "STEP 5 · BLUETOOTH", "Hop, hop, hop", "Classic Bluetooth splits the band into 79 narrow channels and hops between them 1,600 times a second, in a pattern both sides know.", t, dur)
    k = prog(t, 0.2, 0.6)
    hop_grid(d, t, k, 79, 360, 1500, 260, 780, 3)
    k2 = prog(t, 3.6, 4.1)
    text(d, (1720, 400), "79", 72, BLUE, "Bold", "mm", k=k2)
    text(d, (1720, 460), "channels, 1 MHz", 26, DIM, "Medium", "mm", k=k2)
    text(d, (1720, 600), "1,600", 72, AMBER, "Bold", "mm", k=prog(t, 4.2, 4.7))
    text(d, (1720, 660), "hops a second", 26, DIM, "Medium", "mm", k=prog(t, 4.2, 4.7))

def s_ble(d, t, dur):
    chrome(d, "STEP 5 · BLUETOOTH", "Bluetooth Low Energy: mostly asleep", "Low Energy uses 40 wider channels; 3 are for advertising. The radio wakes, sends a tiny burst, then sleeps again.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 200, 1720, 380
    for i in range(40):
        x = x0 + i * (x1 - x0) / 40
        adv = i in (0, 12, 39)
        kk = prog(t, 0.4 + i * 0.03, 0.7 + i * 0.03)
        d.rectangle([x + 3, y - (110 if adv else 60), x + (x1 - x0) / 40 - 3, y], fill=fade(AMBER if adv else mix(BG, BLUE, 0.6), kk))
    text(d, (x0, y + 40), "40 channels, 2 MHz each", 28, BLUE, "Bold", "lm", k=k)
    text(d, (x1, y + 40), "3 advertising channels", 28, AMBER, "Bold", "rm", k=k)
    k3 = prog(t, 2.6, 3.1)
    ty = 680
    d.line([x0, ty, x1, ty], fill=fade(LINE, k3), width=3)
    text(d, (x0, ty - 80), "radio on", 26, DIM, "Medium", "lm", k=k3)
    p = clamp((t - 2.8) / 3.0)
    for i in range(6):
        x = x0 + 60 + i * 270
        if (x - x0) / (x1 - x0) > p: break
        d.rectangle([x, ty - 70, x + 18, ty], fill=GREEN)
    if p > 0.9:
        text(d, (W // 2, ty + 50), "asleep most of the time · a coin cell can last months (example)", 28, DIM, "Medium", "mm", k=prog(t, 5.6, 6.0))

def s_afh(d, t, dur):
    chrome(d, "STEP 5 · BLUETOOTH", "Hopping around Wi-Fi", "Bluetooth can also learn which channels are noisy, such as a busy Wi-Fi channel, and leave them out of its hopping.", t, dur)
    k = prog(t, 0.2, 0.6)
    hop_grid(d, t, k, 79, 360, 1560, 260, 780, 5, busy=(20, 42))
    text(d, (W // 2, 820 - 0), "", 10, DIM, k=k)

# ---------------- chapter 6: sharing the air ----------------
def s_compare(d, t, dur):
    chrome(d, "STEP 6 · SHARING THE AIR", "Same band, different jobs", "Wi-Fi is built for speed and range. Bluetooth is built for low power and small links. Typical figures, not limits.", t, dur)
    k = prog(t, 0.2, 0.6)
    cols = [(760, "Wi-Fi", GREEN), (1320, "Bluetooth LE", BLUE)]
    rows = [("job", "your internet", "earbuds, watches, sensors"), ("speed", "hundreds of Mbit/s+", "up to about 2 Mbit/s"),
            ("range", "a home or office", "typically a room or two"), ("power", "plugged in or big battery", "a coin cell can do")]
    for x, n, c in cols: text(d, (x, 290), n, 42, c, "Bold", "mm", k=k)
    for i, (a, b, c) in enumerate(rows):
        kk = prog(t, 0.6 + i * 0.6, 1.0 + i * 0.6)
        y = 380 + i * 105
        box(d, (200, y - 40, 1720, y + 40), PANEL, LINE, 10, 2, kk)
        text(d, (240, y), a, 32, DIM, "Bold", "lm", k=kk)
        text(d, (760, y), b, 32, TXT, "Medium", "mm", k=kk)
        text(d, (1320, y), c, 32, TXT, "Medium", "mm", k=kk)

def s_combo(d, t, dur):
    chrome(d, "STEP 6 · SHARING THE AIR", "One chip, taking turns", "In many phones, one combo chip runs both radios and often shares the antenna. It coordinates them so they don't talk over each other.", t, dur)
    k = prog(t, 0.2, 0.6)
    chip(d, 240, 400, 380, 240, "combo chip", "Wi-Fi + Bluetooth", PURPLE, k)
    d.line([620, 520, 760, 520], fill=fade(DIM, k), width=6)
    d.line([760, 520, 760, 360], fill=fade(DIM, k), width=10)
    text(d, (760, 320), "shared antenna", 26, DIM, "Medium", "mm", k=k)
    x0, x1, y = 900, 1720, 520
    text(d, (x0, y - 100), "who gets the air", 30, TXT, "Bold", "lm", k=k)
    p = clamp((t - 0.8) / 5.0)
    seq = [GREEN, GREEN, BLUE, GREEN, GREEN, GREEN, BLUE, GREEN, BLUE, GREEN, GREEN, BLUE]
    sw = (x1 - x0) / len(seq)
    for i, c in enumerate(seq):
        if i / len(seq) > p: break
        d.rectangle([x0 + i * sw + 2, y - 40, x0 + (i + 1) * sw - 2, y + 40], fill=mix(BG, c, 0.8))
    kk = prog(t, 3.0, 3.5)
    d.rectangle([x0, y + 90, x0 + 30, y + 120], fill=fade(GREEN, kk)); text(d, (x0 + 46, y + 105), "Wi-Fi", 26, TXT, "Medium", "lm", k=kk)
    d.rectangle([x0 + 220, y + 90, x0 + 250, y + 120], fill=fade(BLUE, kk)); text(d, (x0 + 266, y + 105), "Bluetooth", 26, TXT, "Medium", "lm", k=kk)

def s_journey(d, t, dur):
    chrome(d, "STEP 6 · SHARING THE AIR", "The whole trip, end to end", "App, bits, symbols, a 2.4 GHz wave, through the air, into an antenna, back to numbers, back to bits. Thousands of times a second.", t, dur)
    k = prog(t, 0.2, 0.6)
    st = [("app", AMBER), ("bits", AMBER), ("symbols", PURPLE), ("wave", CYAN), ("air", CYAN), ("antenna", RED), ("ADC", CYAN), ("bits", AMBER)]
    cx, cy, rx, ry = W // 2, 540, 700, 230
    n = len(st)
    p = clamp((t - 0.6) / 5.0)
    for i, (nm, c) in enumerate(st):
        a = math.pi + i * 2 * math.pi / n
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a) * -1
        kk = 1.0 if i / n <= p else 0.25
        box(d, (x - 110, y - 40, x + 110, y + 40), mix(BG, c, 0.25 * kk), fade(c, kk), 30, 3, k)
        text(d, (x, y), nm, 32, c, "Bold", "mm", k=k * kk)
    ang = math.pi + p * 2 * math.pi * (n - 1) / n
    dot(d, cx + (rx - 150) * math.cos(ang), cy - (ry - 70) * math.sin(ang), 14, TXT, k)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "Bits through the air", "Change a wave's amplitude, frequency or phase. Wi-Fi spreads data over many subcarriers. Bluetooth hops. They share the band by taking turns.", t, dur)
    stg = [("Wave", CYAN), ("Modulate", AMBER), ("Chip", PURPLE), ("Wi-Fi", GREEN), ("Bluetooth", BLUE), ("Share", RED)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(stg):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.2:
        wave(d, 560, 1360, 680, 40, CYAN, prog(t, 4.2, 4.7), cyc=8, t=t, speed=1.0, width=4)

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "What is an RTOS, and why", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "does your car need one?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
          ("03_wave", s_wave, 8), ("04_freq", s_freq, 8), ("05_bands", s_bands, 8),
          ("06_carrier", s_carrier, 8), ("07_ask", s_ask, 8), ("08_fsk", s_fsk, 8), ("09_psk", s_psk, 8),
          ("10_qam", s_qam, 8), ("11_noise", s_noise, 8),
          ("12_tx", s_tx, 8), ("13_rx", s_rx, 8), ("14_antenna", s_antenna, 8),
          ("15_ofdm", s_ofdm, 8), ("16_multipath", s_multipath, 8), ("17_csma", s_csma, 8), ("18_packet", s_packet, 8),
          ("19_hop", s_hop, 8), ("20_ble", s_ble, 8), ("21_afh", s_afh, 8),
          ("22_compare", s_compare, 8), ("23_combo", s_combo, 8), ("24_journey", s_journey, 8),
          ("25_recap", s_recap, 8), ("26_end", s_end, 6)]

NARRATION = {
 "01_hook": "Right now, your phone might be streaming video, with no wires at all. The radio wave carrying it wiggles about two point four billion times every second. But a wave is just a wiggle. So where, exactly, are the bits? And how does a tiny chip put them there?",
 "02_cover": "Today we'll go step by step. First, what a radio wave actually is. Then modulation: the tricks that turn bits into changes in a wave. Then we'll look inside a radio chip. Then how Wi-Fi sends so much data, how Bluetooth hops around, and how they share the same air.",
 "03_wave": "Step one: radio waves. Push electrons back and forth in a piece of metal, an antenna, and you create changing electric and magnetic fields. Those fields spread outward as a radio wave, at the speed of light. That's about three hundred thousand kilometres every second.",
 "04_freq": "How fast the electrons swing is the frequency. Two point four gigahertz means two point four billion cycles every second. Divide the speed of light by that, and you get the wavelength: the distance from one peak to the next. At two point four gigahertz, it's about twelve and a half centimetres.",
 "05_bands": "Wi-Fi mostly uses two bands: around two point four gigahertz, and around five gigahertz. Newer equipment can also use a band around six gigahertz. Bluetooth lives in that same two point four gigahertz band, right alongside Wi-Fi. Keep that in mind. It matters later.",
 "06_carrier": "Step two: modulation. Here's the catch. A perfect, steady wave carries no information at all. It just repeats. To send bits, the radio has to change something about the wave. And there are three things you can change: its amplitude, its frequency, and its phase.",
 "07_ask": "The simplest trick is to change the amplitude. Make the wave big for a one, and small for a zero. That's called amplitude shift keying. It's easy to understand, but noise also changes amplitude, so on its own it's easy to fool.",
 "08_fsk": "Another trick is to change the frequency. Nudge it slightly higher for a one, and slightly lower for a zero. The real shift is tiny, much smaller than in this drawing. Bluetooth uses a smoothed version of this, called G F S K, short for Gaussian frequency shift keying.",
 "09_psk": "The third trick is to change the phase: the timing of the wave. Flip it half a cycle, and the receiver sees the peaks arrive at a different moment. With two phases, each symbol carries one bit. With four phases, each symbol carries two bits.",
 "10_qam": "Now combine them. Change the amplitude and the phase at the same time, and you can make a grid of possible points. This picture is called a constellation. With sixteen points, each symbol carries four bits. Recent Wi-Fi versions can use one thousand and twenty four points. That's ten bits in every symbol.",
 "11_noise": "So why not use millions of points? Noise. Every received point gets smeared a little. Close to the router, the signal is strong, the points stay tight, and the radio can use a dense grid. Far away, the points blur into each other, so the radio switches to fewer, more spread out points. Slower, but reliable.",
 "12_tx": "Step three: inside the chip. Here's the transmit side. The digital part turns your bits into symbols. A D A C, a digital to analog converter, turns them into a changing voltage. A mixer shifts that signal up to two point four gigahertz. And a power amplifier pushes it out through the antenna.",
 "13_rx": "Receiving runs it backwards. The antenna picks up an incredibly faint signal. A low-noise amplifier boosts it. A mixer shifts it back down. Then an A D C, just like the one from episode eight, turns it into numbers. And the digital part decodes those numbers back into bits.",
 "14_antenna": "And the antenna? Often it's just a carefully shaped strip of copper on the circuit board. Many small antennas are about a quarter of a wavelength long. At two point four gigahertz, a quarter of twelve and a half centimetres is roughly three centimetres. The exact shape depends on the design.",
 "15_ofdm": "Step four: Wi-Fi. Wi-Fi doesn't send one fast stream on one frequency. It splits its channel into lots of narrow subcarriers, side by side, each carrying its own slow symbol. In classic twenty megahertz Wi-Fi, fifty two are used: forty eight for data, and four pilots for keeping in sync. This is called O F D M.",
 "16_multipath": "Why bother? Echoes. Indoors, the signal bounces off walls, floors and furniture, so copies arrive slightly late. With long, slow symbols, and a short guard gap before each one, those echoes can die down before the next symbol starts. In classic Wi-Fi, each symbol lasts about four microseconds.",
 "17_csma": "There's another problem. Every device on a channel shares the same air, and only one should talk at a time. So Wi-Fi listens before it talks. If the channel is busy, a device waits, then waits an extra random moment, so two devices don't jump in together.",
 "18_packet": "Each Wi-Fi packet starts with a preamble: a known pattern that lets the receiver lock on, and measure the channel. Then a header that says how fast the data is coded, and how long it is. Then your data. After a short gap, the receiver sends back a tiny acknowledgement. No ACK? The sender tries again.",
 "19_hop": "Step five: Bluetooth. Classic Bluetooth splits the two point four gigahertz band into seventy nine narrow channels, each one megahertz wide. Then it hops between them, one thousand six hundred times a second, in a pattern both devices know. If one channel is noisy, the next hop is probably fine.",
 "20_ble": "Bluetooth Low Energy, used by watches, trackers and sensors, uses forty channels, each two megahertz wide. Three of them are for advertising: that's how devices find each other. And the key to low energy is sleep. The radio wakes up, sends a tiny burst, and goes straight back to sleep. A coin cell can last months.",
 "21_afh": "Bluetooth can be even smarter. With adaptive frequency hopping, it notices which channels keep failing, perhaps because a busy Wi-Fi network is right there, and it leaves those channels out of its pattern. Same band, but it steps around the traffic.",
 "22_compare": "Step six: sharing the air. Wi-Fi and Bluetooth have different jobs. Wi-Fi is built for speed and range: your internet, across a home or office. Bluetooth Low Energy is built for tiny amounts of power: earbuds, watches and sensors, usually within a room or two. These are typical figures, not hard limits.",
 "23_combo": "In many phones and laptops, one combo chip handles both Wi-Fi and Bluetooth, and they often share an antenna. So the chip coordinates them. It hands out turns, a slice for Wi-Fi, a slice for Bluetooth, so they don't talk over each other, and your music keeps playing while you browse.",
 "24_journey": "So here's the whole trip. An app hands over data. It becomes bits, then symbols. The chip turns them into a two point four gigahertz wave. It crosses the air, hits an antenna, gets amplified, mixed down, and measured by an A D C. And the numbers turn back into bits. Over and over, thousands of times a second.",
 "25_recap": "Let's recap. A radio wave is a fast wiggle. To carry bits, you change its amplitude, frequency or phase. A chip does that with a D A C, a mixer and an amplifier. Wi-Fi spreads data over many subcarriers. Bluetooth hops. And they share the same band by taking turns.",
 "26_end": "Next episode: what is an R T O S, and why does your car need one? Subscribe so you don't miss it.",
}
OUTPUT = "how_wifi_and_bluetooth_send_bits_ep10_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep10/{name}.mp4", f"ep10/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep10", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    for j in range(0, len(SCENES), 9):
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES[j:j + 9]):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save(f"ep10/sheet{j // 9 + 1}.jpg", quality=85)
