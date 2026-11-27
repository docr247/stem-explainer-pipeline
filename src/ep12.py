import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
BLUE = (90, 150, 255)
NORTH, SOUTH = RED, BLUE          # magnet poles, used the same way throughout
PHASE_A, PHASE_B = AMBER, CYAN    # the two stepper coils

# ---------------- helpers ----------------
def coil(d, x, y, w, h, col, on=False, k=1.0, turns=9):
    """A wire wound round an iron core; (x, y) is top-left of the core."""
    d.rectangle([x, y, x + w, y + h], fill=fade((70, 76, 100), k))
    c = col if on else DIM
    for i in range(turns):
        xx = x + 10 + i * (w - 20) / (turns - 1)
        d.line([xx, y - 10, xx + 8, y + h + 10], fill=fade(c, k), width=6)

def magnet(d, cx, cy, w, h, ang=0.0, k=1.0):
    """Bar magnet centred at (cx, cy), N end pointing along ang (radians, 0 = right)."""
    ca, sa = math.cos(ang), math.sin(ang)
    def p(u, v): return (cx + u * ca - v * sa, cy + u * sa + v * ca)
    d.polygon([p(0, -h / 2), p(w / 2, -h / 2), p(w / 2, h / 2), p(0, h / 2)], fill=fade(NORTH, k))
    d.polygon([p(-w / 2, -h / 2), p(0, -h / 2), p(0, h / 2), p(-w / 2, h / 2)], fill=fade(SOUTH, k))
    if k > 0.6:
        text(d, p(w / 4, 0), "N", int(h * 0.55), BG, "Bold", "mm")
        text(d, p(-w / 4, 0), "S", int(h * 0.55), BG, "Bold", "mm")

def stepper(d, cx, cy, r, ang, active, k=1.0, label=True):
    """Simplified 4-pole stepper seen end-on. active: dict pole_index -> 'N'/'S' for energised poles."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fade(LINE, k), width=6, fill=fade(PANEL, k))
    for i in range(4):
        a = -math.pi / 2 + i * math.pi / 2
        x0, y0 = cx + r * 0.92 * math.cos(a), cy + r * 0.92 * math.sin(a)
        x1, y1 = cx + r * 0.52 * math.cos(a), cy + r * 0.52 * math.sin(a)
        ph = PHASE_A if i % 2 == 0 else PHASE_B
        pol = active.get(i)
        col = (NORTH if pol == "N" else SOUTH) if pol else (60, 66, 90)
        d.line([x0, y0, x1, y1], fill=fade(col, k), width=int(r * 0.26))
        if label:
            lx, ly = cx + r * 1.18 * math.cos(a), cy + r * 1.18 * math.sin(a)
            text(d, (lx, ly), ("A" if i % 2 == 0 else "B") + ("" if i < 2 else "'"), 30, ph, "Bold", "mm", k=k)
    magnet(d, cx, cy, r * 0.82, r * 0.26, ang, k)

def gantry(d, x0, x1, y, hx, k=1.0, col=CYAN):
    """A generic side view of one axis: rail, carriage with nozzle at hx (0..1)."""
    d.rounded_rectangle([x0, y - 14, x1, y + 14], 8, fill=fade(LINE, k))
    cx = x0 + 60 + (x1 - x0 - 120) * hx
    box(d, (cx - 70, y - 60, cx + 70, y + 40), PANEL, col, 12, 4, k)
    d.polygon([(cx - 26, y + 40), (cx + 26, y + 40), (cx, y + 84)], fill=fade(AMBER, k))
    return cx

def pulley(d, cx, cy, r, ang, k=1.0, teeth=20, col=TXT):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fade((60, 66, 90), k), outline=fade(col, k), width=4)
    for i in range(teeth):
        a = ang + i * 2 * math.pi / teeth
        d.line([cx + (r - 10) * math.cos(a), cy + (r - 10) * math.sin(a), cx + (r + 8) * math.cos(a), cy + (r + 8) * math.sin(a)],
               fill=fade(col, k), width=5)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=fade(BG, k))
    d.line([cx, cy, cx + (r - 18) * math.cos(ang), cy + (r - 18) * math.sin(ang)], fill=fade(AMBER, k), width=5)

def switch(d, x, y, pressed, k=1.0):
    """A small microswitch; body ends at x, lever points right."""
    box(d, (x - 100, y - 50, x, y + 50), PANEL, GREEN if pressed else DIM, 8, 4, k)
    tip = (x + 60, y - (18 if pressed else 44))
    d.line([(x - 6, y - 30), tip], fill=fade(GREEN if pressed else TXT, k), width=6)
    d.ellipse([tip[0] - 10, tip[1] - 10, tip[0] + 10, tip[1] + 10], fill=fade(TXT, k))

def counter(d, x, y, label, val, col=AMBER, k=1.0, w=520):
    box(d, (x, y, x + w, y + 100), (6, 10, 20), col, 14, 3, k)
    text(d, (x + 30, y + 50), label, 30, DIM, "Bold", "lm", k=k)
    text(d, (x + w - 30, y + 50), val, 44, col, "Bold", "rm", mono=True, k=k)

def pulse_train(d, x0, y0, n, wpx, h, t0, t, col, k=1.0, gap=None):
    gap = gap or wpx * 2
    pts = [(x0, y0 + h)]
    for i in range(n):
        if t < t0 + i * 0.25: break
        x = x0 + i * gap
        pts += [(x, y0 + h), (x, y0), (x + wpx, y0), (x + wpx, y0 + h)]
    pts.append((pts[-1][0] + gap - wpx, y0 + h))
    d.line(pts, fill=fade(col, k), width=5)

def disc(d, cx, cy, r, ang, k=1.0, slots=24):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fade((60, 66, 90), k), outline=fade(TXT, k), width=4)
    for i in range(slots):
        a0 = ang + i * 2 * math.pi / slots
        a1 = a0 + math.pi / slots
        poly = [(cx + (r - 40) * math.cos(a0), cy + (r - 40) * math.sin(a0)), (cx + (r - 8) * math.cos(a0), cy + (r - 8) * math.sin(a0)),
                (cx + (r - 8) * math.cos(a1), cy + (r - 8) * math.sin(a1)), (cx + (r - 40) * math.cos(a1), cy + (r - 40) * math.sin(a1))]
        d.polygon(poly, fill=fade(BG, k))
    d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=fade(PANEL, k), outline=fade(TXT, k), width=3)

def square(d, x0, y0, wpx, h, phase, cycles, col, k=1.0):
    pts = []
    per = wpx / cycles
    for i in range(int(wpx)):
        u = ((i / per) + phase) % 1.0
        pts.append((x0 + i, y0 + (0 if u < 0.5 else h)))
    d.line(pts, fill=fade(col, k), width=5)

# ---------------- chapter 0 ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "In most hobby 3D printers, nothing measures where the print head is while it prints. So how does it know?", t, dur)
    k = prog(t, 0.2, 0.7)
    hx = 0.5 + 0.38 * math.sin(t * 1.3)
    cx = gantry(d, 300, 1620, 420, hx, k)
    d.rectangle([300, 600, 1620, 620], fill=fade(LINE, k))
    d.line([300 + 60 + 1200 * 0.12, 590, 300 + 60 + 1200 * 0.12 + 1200 * 0.76 * clamp(t / 6), 590], fill=fade(AMBER, k), width=8)
    if t > 2.0:
        kk = prog(t, 2.0, 2.5)
        text(d, (cx, 300), "?", 90, AMBER, "Bold", "mm", k=kk)
    if t > 3.6:
        kk = prog(t, 3.6, 4.1)
        counter(d, 700, 680, "it counts:", f"{int((t - 3.6) * 2417):,}", AMBER, kk)

def s_cover(d, t, dur):
    chrome(d, "", "Here's what we'll build", "We'll start with one coil of wire, and add one layer at a time, until we have a machine that knows where it is.", t, dur)
    items = [("1", "One coil", "a wire becomes a magnet", AMBER), ("2", "Steps", "a motor that moves in clicks", CYAN),
             ("3", "Motion", "turning clicks into millimetres", GREEN), ("4", "Counting", "the firmware keeps score", PURPLE),
             ("5", "Homing", "finding zero after power-on", RED), ("6", "Feedback", "when counting isn't enough", BLUE)]
    for i, (n, a, b, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.45, 0.8 + i * 0.45)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 270 + row * 170
        box(d, (x, y, x + 720, y + 130), PANEL, c, 16, 3, kk)
        d.ellipse([x + 26, y + 30, x + 96, y + 100], fill=fade(c, kk))
        text(d, (x + 61, y + 65), n, 38, BG, "Bold", "mm", k=kk)
        text(d, (x + 130, y + 46), a, 40, TXT, "Bold", "lm", k=kk)
        text(d, (x + 130, y + 94), b, 28, DIM, "Medium", "lm", k=kk)

# ---------------- chapter 1: one coil ----------------
def s_coil(d, t, dur):
    chrome(d, "STEP 1 · ONE COIL", "A wire becomes a magnet", "Wind a wire round a piece of iron and pass a current through it. It becomes an electromagnet, and it attracts a magnet nearby.", t, dur)
    k = prog(t, 0.2, 0.6)
    on = t > 2.2
    coil(d, 360, 420, 520, 120, PHASE_A, on, k)
    d.line([370, 560, 370, 680, 870, 680, 870, 560], fill=fade(PHASE_A if on else DIM, k), width=5)
    box(d, (560, 650, 680, 710), PANEL, PHASE_A if on else DIM, 10, 3, k)
    text(d, (620, 680), "ON" if on else "OFF", 28, PHASE_A if on else DIM, "Bold", "mm", mono=True, k=k)
    if on:
        kk = prog(t, 2.2, 2.6)
        text(d, (350, 480), "S", 44, SOUTH, "Bold", "rm", k=kk)
        text(d, (880, 380), "N", 44, NORTH, "Bold", "mm", k=kk)
        for g in range(3):
            rr = 40 + g * 34
            d.arc([880 - rr, 480 - rr, 880 + rr, 480 + rr], -60, 60, fill=fade(mix(BG, NORTH, 0.6 - g * 0.15), kk), width=4)
    mx = 1400 - 260 * prog(t, 3.0, 4.0) if on else 1400
    magnet(d, mx, 480, 240, 80, 0.0, k)
    text(d, (1400, 640), "permanent magnet", 28, DIM, "Medium", "mm", k=k)

def s_rotor(d, t, dur):
    chrome(d, "STEP 1 · ONE COIL", "Switch coils, the magnet turns", "Put a magnet on a shaft between several coils. Energise one coil and the magnet lines up with it. Switch to the next, and it turns to follow.", t, dur)
    k = prog(t, 0.2, 0.6)
    st = int(clamp((t - 1.6) / 1.3) * 4) if t > 1.6 else -1
    st = min(st, 3)
    poles = [{}, {0: "S", 2: "N"}, {1: "S", 3: "N"}, {2: "S", 0: "N"}, {3: "S", 1: "N"}][st + 1]
    target = [-math.pi / 2, -math.pi / 2, 0, math.pi / 2, math.pi][st + 1]
    stepper(d, 700, 500, 230, target, poles, k)
    seq = ["A", "B", "A'", "B'"]
    for i, s in enumerate(seq):
        on = i == st
        c = PHASE_A if i % 2 == 0 else PHASE_B
        box(d, (1150 + i * 150, 440, 1270 + i * 150, 540), mix(BG, c, 0.3) if on else PANEL, c if on else LINE, 12, 4 if on else 2, k)
        text(d, (1210 + i * 150, 490), s, 40, c if on else DIM, "Bold", "mm", k=k)
    text(d, (1435, 600), "energise in turn", 30, DIM, "Medium", "mm", k=k)
    text(d, (1435, 660), "(simplified: 4 positions per turn)", 26, DIM, "Medium", "mm", k=prog(t, 3.0, 3.5))

def s_teeth(d, t, dur):
    chrome(d, "STEP 1 · ONE COIL", "Teeth make the clicks tiny", "Real stepper motors have fine teeth on the rotor and the stator. A very common type moves in 200 steps per turn: 1.8 degrees each.", t, dur)
    k = prog(t, 0.2, 0.6)
    cx, cy, r = 620, 500, 250
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fade(PANEL, k), outline=fade(LINE, k), width=6)
    rot = (int(clamp((t - 2.0) / 4.0) * 12) if t > 2.0 else 0) * 2 * math.pi / 200
    rr = 170
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fade((60, 66, 90), k))
    for i in range(50):
        a = rot + i * 2 * math.pi / 50
        d.line([cx + (rr - 6) * math.cos(a), cy + (rr - 6) * math.sin(a), cx + (rr + 14) * math.cos(a), cy + (rr + 14) * math.sin(a)], fill=fade(TXT, k), width=7)
    d.line([cx, cy, cx + (rr - 30) * math.cos(rot - math.pi / 2), cy + (rr - 30) * math.sin(rot - math.pi / 2)], fill=fade(AMBER, k), width=8)
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=fade(BG, k))
    kk = prog(t, 1.0, 1.5)
    text(d, (1100, 360), "200 steps", 80, AMBER, "Bold", "lm", k=kk)
    text(d, (1100, 450), "per turn (very common)", 34, DIM, "Medium", "lm", k=kk)
    kk = prog(t, 2.4, 2.9)
    text(d, (1100, 560), "360° ÷ 200 = 1.8°", 50, TXT, "Bold", "lm", mono=True, k=kk)
    text(d, (1100, 640), "per step", 34, DIM, "Medium", "lm", k=kk)

# ---------------- chapter 2: steps ----------------
def s_sequence(d, t, dur):
    chrome(d, "STEP 2 · STEPS", "Two coils, four-beat rhythm", "A stepper has two coil groups, A and B. Pulse them in a fixed order, A, B, A reversed, B reversed, and the shaft clicks forward one step per beat.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1 = 420, 1720
    for i, (n, c, ph) in enumerate([("coil A", PHASE_A, 0), ("coil B", PHASE_B, 1)]):
        y = 380 + i * 200
        text(d, (x0 - 30, y), n, 34, c, "Bold", "rm", k=k)
        d.line([x0, y, x1, y], fill=fade(LINE, k), width=2)
        pts = []
        pp = prog(t, 0.6, 5.0)
        for px in range(0, int((x1 - x0) * pp), 3):
            beat = int(px / ((x1 - x0) / 8))
            v = [1, 0, -1, 0][(beat - ph) % 4]
            pts.append((x0 + px, y - v * 70))
        if len(pts) > 1: d.line(pts, fill=fade(c, k), width=6)
    for b in range(8):
        x = x0 + (b + 0.5) * (x1 - x0) / 8
        if prog(t, 0.6, 5.0) * 8 > b + 0.5:
            text(d, (x, 740), f"step {b + 1}", 26, GREEN, "Bold", "mm", k=k)

def s_micro(d, t, dur):
    chrome(d, "STEP 2 · STEPS", "Microstepping: steps between steps", "Instead of switching coils fully on and off, the driver blends the two currents smoothly. The rotor settles in between, so one step becomes, say, sixteen microsteps.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1 = 220, 1080
    for i, (n, c, f) in enumerate([("A", PHASE_A, math.cos), ("B", PHASE_B, math.sin)]):
        y = 400 + i * 220
        text(d, (x0 - 30, y), n, 36, c, "Bold", "rm", k=k)
        d.line([x0, y, x1, y], fill=fade(LINE, k), width=2)
        pts = []
        pp = prog(t, 0.6, 4.5)
        for px in range(0, int((x1 - x0) * pp), 2):
            step = int(px / ((x1 - x0) / 64))
            pts.append((x0 + px, y - 80 * f(step * 2 * math.pi / 64)))
        if len(pts) > 1: d.line(pts, fill=fade(c, k), width=5)
    text(d, ((x0 + x1) / 2, 740), "currents in small stairs (shape simplified)", 26, DIM, "Medium", "mm", k=k)
    kk = prog(t, 2.6, 3.1)
    rows = [("full steps", "200 per turn", DIM), ("× 16 microsteps", "(example)", DIM), ("=", "3,200 per turn", AMBER)]
    for i, (a, b, c) in enumerate(rows):
        kj = prog(t, 2.6 + i * 0.5, 3.0 + i * 0.5)
        text(d, (1220, 380 + i * 110), a, 40, TXT, "Bold", "lm", k=kj)
        text(d, (1220, 430 + i * 110), b, 32, c, "Bold", "lm", mono=True, k=kj)

def s_driver(d, t, dur):
    chrome(d, "STEP 2 · STEPS", "Two wires: STEP and DIR", "The main board doesn't drive the coils itself. It talks to a driver chip with two signals: DIR sets the direction, and every pulse on STEP moves one microstep.", t, dur)
    k = prog(t, 0.2, 0.6)
    chip(d, 160, 360, 360, 220, "Controller", "runs the firmware", PURPLE, k)
    chip(d, 820, 360, 340, 220, "Driver", "powers the coils", GREEN, prog(t, 0.5, 1.0))
    kk = prog(t, 1.0, 1.5)
    text(d, (540, 410), "DIR", 30, CYAN, "Bold", "lm", mono=True, k=kk)
    d.line([540, 440, 800, 440], fill=fade(CYAN, kk), width=5)
    text(d, (540, 500), "STEP", 30, AMBER, "Bold", "lm", mono=True, k=kk)
    pulse_train(d, 560, 520, 6, 14, 40, 1.6, t, AMBER, kk, gap=38)
    stepper(d, 1520, 470, 150, -math.pi / 2 + math.pi + (int(clamp((t - 1.6) / 1.5) * 6) * 0.25), {}, prog(t, 0.8, 1.3), label=False)
    for j in range(2):
        d.line([1160, 440 + j * 60, 1370, 440 + j * 60], fill=fade(PHASE_A if j == 0 else PHASE_B, kk), width=5)
    if t > 3.4:
        text(d, (W // 2, 720), "1 pulse = 1 microstep", 44, AMBER, "Bold", "mm", k=prog(t, 3.4, 3.9))

# ---------------- chapter 3: motion ----------------
def s_belt(d, t, dur):
    chrome(d, "STEP 3 · MOTION", "From turning to sliding: the belt", "To move the print head, a toothed pulley on the motor pulls a toothed belt. A common setup: 20 teeth, 2 millimetres apart. One turn moves the belt 40 millimetres.", t, dur)
    k = prog(t, 0.2, 0.6)
    turn = prog(t, 2.2, 5.2)
    ang = -math.pi / 2 + turn * 2 * math.pi
    pulley(d, 300, 470, 80, ang, k)
    pulley(d, 1620, 470, 80, 0, k, col=DIM)
    for yy in (390, 550):
        d.line([300, yy, 1620, yy], fill=fade(LINE, k), width=12)
        for i in range(0, 1320, 26):
            xx = 300 + (i + (turn * 40 * 6.6 if yy == 390 else -turn * 40 * 6.6)) % 1320
            d.line([xx, yy - 6, xx, yy + 6], fill=fade((40, 48, 76), k), width=4)
    hx = 700 + turn * 40 * 6.6
    box(d, (hx - 60, 300, hx + 60, 400), PANEL, CYAN, 12, 4, k)
    d.polygon([(hx - 22, 400), (hx + 22, 400), (hx, 440)], fill=fade(AMBER, k))
    if t > 2.0:
        kk = prog(t, 2.0, 2.5)
        d.line([700, 700, hx, 700], fill=fade(AMBER, kk), width=5)
        text(d, ((700 + hx) / 2, 750), f"{turn * 40:4.1f} mm", 36, AMBER, "Bold", "mm", mono=True, k=kk)
    text(d, (300, 600), "20 teeth × 2 mm", 28, TXT, "Bold", "mm", k=prog(t, 1.0, 1.5))
    text(d, (300, 640), "(example)", 24, DIM, "Medium", "mm", k=prog(t, 1.0, 1.5))

def s_stepsmm(d, t, dur):
    chrome(d, "STEP 3 · MOTION", "Steps per millimetre", "Now the key number. 3,200 microsteps per turn, divided by 40 millimetres per turn, gives 80 steps per millimetre. One pulse moves the head about one eightieth of a millimetre.", t, dur)
    rows = [("3,200", "microsteps per turn", AMBER), ("÷ 40", "mm per turn", GREEN), ("= 80", "steps per mm", CYAN)]
    for i, (a, b, c) in enumerate(rows):
        kk = prog(t, 0.4 + i * 0.9, 0.9 + i * 0.9)
        y = 320 + i * 130
        text(d, (820, y), a, 80, c, "Bold", "rm", mono=True, k=kk)
        text(d, (860, y), b, 40, TXT, "Medium", "lm", k=kk)
    kk = prog(t, 3.4, 3.9)
    box(d, (420, 700, 1500, 790), PANEL, AMBER, 14, 3, kk)
    text(d, (960, 745), "1 step = 1/80 mm = 0.0125 mm (on paper)", 36, AMBER, "Bold", "mm", k=kk)

def s_screw(d, t, dur):
    chrome(d, "STEP 3 · MOTION", "Or a screw: slower, stronger, finer", "For up and down, or for a CNC cutting metal, a screw is common instead. A typical printer lead screw moves 8 millimetres per turn, giving 400 steps per millimetre.", t, dur)
    k = prog(t, 0.2, 0.6)
    turn = prog(t, 1.4, 6.0) * 2
    x0, x1, y = 280, 1500, 470
    d.rectangle([x0, y - 34, x1, y + 34], fill=fade((60, 66, 90), k))
    for i in range(0, x1 - x0, 40):
        xx = x0 + (i - turn * 40) % (x1 - x0)
        d.line([xx, y - 34, xx + 24, y + 34], fill=fade(TXT, k), width=5)
    box(d, (150, y - 90, 280, y + 90), PANEL, AMBER, 12, 4, k)
    text(d, (215, y), "motor", 26, AMBER, "Bold", "mm", k=k)
    nx = 600 + turn * 8 * 18
    box(d, (nx - 70, y - 80, nx + 70, y + 80), mix(BG, GREEN, 0.25), GREEN, 12, 4, k)
    text(d, (nx, y - 120), "nut + carriage", 28, GREEN, "Bold", "mm", k=k)
    kk = prog(t, 2.6, 3.1)
    text(d, (W // 2, 660), "3,200 ÷ 8 mm = 400 steps per mm", 44, CYAN, "Bold", "mm", mono=True, k=kk)
    text(d, (W // 2, 730), "(example values: 8 mm lead, 16 microsteps)", 26, DIM, "Medium", "mm", k=kk)

# ---------------- chapter 4: counting ----------------
def s_count(d, t, dur):
    chrome(d, "STEP 4 · COUNTING", "The firmware keeps score", "Here's the trick. The firmware keeps a counter for each axis. Every pulse it sends adds one, or takes one away. Position is simply that count, divided by steps per millimetre.", t, dur)
    k = prog(t, 0.2, 0.6)
    n = int(clamp((t - 1.0) / 4.0) * 2400)
    counter(d, 220, 320, "X steps sent", f"{n:,}", AMBER, k, 640)
    text(d, (540, 470), "÷ 80 steps per mm", 34, DIM, "Bold", "mm", mono=True, k=prog(t, 1.6, 2.1))
    counter(d, 220, 530, "X position", f"{n / 80:5.1f} mm", CYAN, prog(t, 2.0, 2.5), 640)
    hx = n / 2400 * 0.8
    gantry(d, 1000, 1760, 520, hx, k)
    text(d, (1380, 680), "the head is never measured", 30, RED, "Bold", "mm", k=prog(t, 4.0, 4.5))

def s_gcode(d, t, dur):
    chrome(d, "STEP 4 · COUNTING", "G-code: move to here", "The slicer turns your model into G-code, a list of moves. Say it asks to go from zero to X 50, Y 20. That's 4,000 pulses on X and 1,600 on Y, timed so both axes finish together.", t, dur)
    k = prog(t, 0.2, 0.6)
    box(d, (160, 300, 760, 420), (6, 10, 20), LINE, 14, 3, k)
    text(d, (200, 360), "G1 X50 Y20", 52, TXT, "Bold", "lm", mono=True, k=k)
    kk = prog(t, 1.4, 1.9)
    text(d, (200, 490), "X: 50 mm × 80 = 4,000 steps", 32, AMBER, "Bold", "lm", mono=True, k=kk)
    text(d, (200, 550), "Y: 20 mm × 80 = 1,600 steps", 32, CYAN, "Bold", "lm", mono=True, k=prog(t, 2.0, 2.5))
    text(d, (200, 640), "(example: 80 steps per mm on both)", 26, DIM, "Medium", "lm", k=kk)
    ox, oy, s = 1000, 760, 14
    d.line([ox, oy, ox + 60 * s, oy], fill=fade(LINE, k), width=3)
    d.line([ox, oy, ox, oy - 34 * s], fill=fade(LINE, k), width=3)
    text(d, (ox + 60 * s, oy + 30), "X", 28, AMBER, "Bold", "mm", k=k)
    text(d, (ox - 30, oy - 34 * s), "Y", 28, CYAN, "Bold", "mm", k=k)
    p = prog(t, 2.8, 5.0)
    ex, ey = ox + 50 * s * p, oy - 20 * s * p
    d.line([ox, oy, ex, ey], fill=fade(GREEN, k), width=6)
    d.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], fill=fade(GREEN, k))
    if p > 0.98: text(d, (ex, ey - 40), "(50, 20)", 30, GREEN, "Bold", "mm", mono=True)

def s_accel(d, t, dur):
    chrome(d, "STEP 4 · COUNTING", "Speed up, cruise, slow down", "A motor can't jump straight to full speed. So the firmware ramps the pulse rate up, cruises, then ramps down. Ask too much, too fast, and the rotor can fall behind.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y0, y1 = 260, 1660, 300, 640
    d.line([x0, y1, x1, y1], fill=fade(LINE, k), width=3)
    d.line([x0, y0, x0, y1], fill=fade(LINE, k), width=3)
    text(d, (x0 - 20, y0), "pulse rate", 28, DIM, "Bold", "rm", k=k)
    text(d, (x1, y1 + 40), "time", 28, DIM, "Bold", "rm", k=k)
    p = prog(t, 0.6, 4.0)
    pts = [(x0, y1), (x0 + 350, y0 + 40), (x1 - 350, y0 + 40), (x1, y1)]
    seg = []
    for i in range(0, 101):
        u = i / 100
        if u > p: break
        xx = x0 + (x1 - x0) * u
        if xx < x0 + 350: yy = y1 - (y1 - y0 - 40) * (xx - x0) / 350
        elif xx > x1 - 350: yy = y1 - (y1 - y0 - 40) * (x1 - xx) / 350
        else: yy = y0 + 40
        seg.append((xx, yy))
    if len(seg) > 1: d.line(seg, fill=fade(GREEN, k), width=6)
    for (a, b, nme) in [(x0, x0 + 350, "accelerate"), (x0 + 350, x1 - 350, "cruise"), (x1 - 350, x1, "decelerate")]:
        text(d, ((a + b) / 2, y1 + 40), nme, 28, TXT, "Bold", "mm", k=prog(t, 1.0, 1.5))
    if t > 4.4:
        kk = prog(t, 4.4, 4.9)
        d.line([x0, y1, x0 + 80, y0 - 10], fill=fade(RED, kk), width=5)
        text(d, (x0 + 100, y0 - 20), "too steep: missed steps", 30, RED, "Bold", "lm", k=kk)

# ---------------- chapter 5: homing ----------------
def s_unknown(d, t, dur):
    chrome(d, "STEP 5 · HOMING", "Switch it on: where am I?", "But a counter only tells you how far you've moved from where you started. With the power off, you can push the head anywhere by hand. At switch-on, the count means nothing.", t, dur)
    k = prog(t, 0.2, 0.6)
    hx = 0.3 + 0.35 * prog(t, 1.4, 3.0)
    cx = gantry(d, 300, 1620, 440, hx, k, DIM)
    if 1.2 < t < 3.2:
        kk = prog(t, 1.2, 1.6)
        arrow(d, (cx - 240, 360), (cx - 90, 360), TXT, 6, kk)
        text(d, (cx - 250, 300), "pushed by hand", 30, TXT, "Bold", "mm", k=kk)
    counter(d, 660, 620, "X steps since power-on", "0", AMBER, prog(t, 3.2, 3.7), 600)
    text(d, (960, 780 - 20), "true position: unknown", 34, RED, "Bold", "mm", k=prog(t, 4.0, 4.5))

def s_endstop(d, t, dur):
    chrome(d, "STEP 5 · HOMING", "Homing: drive until it clicks", "So the first thing a printer does is home. It moves each axis slowly towards a small switch at one end. The moment the switch clicks, the firmware says: this is zero.", t, dur)
    k = prog(t, 0.2, 0.6)
    p = prog(t, 0.8, 3.0)
    hx = 0.65 - 0.65 * p
    if t > 3.4: hx = 0.04 * prog(t, 3.4, 3.8)
    if t > 3.9: hx = 0.04 - 0.04 * prog(t, 3.9, 4.6)
    cx = gantry(d, 360, 1620, 460, hx, k)
    pressed = (t > 2.9 and t < 3.5) or t > 4.5
    switch(d, 270, 440, pressed, k)
    if pressed:
        text(d, (220, 340), "click!", 34, GREEN, "Bold", "mm")
    if t > 4.6:
        kk = prog(t, 4.6, 5.1)
        counter(d, 660, 620, "X position", "0.0 mm", GREEN, kk, 600)
    text(d, (1380, 360), "fast first, then a slower second touch", 26, DIM, "Medium", "mm", k=prog(t, 3.4, 3.9))

def s_sensors(d, t, dur):
    chrome(d, "STEP 5 · HOMING", "Many ways to say 'here'", "The switch can be mechanical, optical, or magnetic. Some driver chips can even feel the motor stall against the end of the rail, so no switch is needed at all.", t, dur)
    k = prog(t, 0.2, 0.6)
    items = [("mechanical", "a lever closes a contact", GREEN), ("optical", "a flag breaks a light beam", AMBER),
             ("magnetic", "a magnet near a Hall sensor", RED), ("sensorless", "driver senses the stall", PURPLE)]
    for i, (a, b, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.7, 0.9 + i * 0.7)
        x = 140 + i * 420
        box(d, (x, 300, x + 380, 700), PANEL, c, 18, 3, kk)
        cx, cy = x + 190, 440
        if i == 0:
            switch(d, cx + 10, cy, True, kk)
        elif i == 1:
            d.rectangle([cx - 90, cy - 60, cx - 50, cy + 60], fill=fade(DIM, kk)); d.rectangle([cx + 50, cy - 60, cx + 90, cy + 60], fill=fade(DIM, kk))
            d.line([cx - 50, cy, cx + 50, cy], fill=fade(RED, kk), width=4)
            d.rectangle([cx - 12, cy - 90, cx + 12, cy - 10 + 60 * ((t % 2) < 1)], fill=fade(AMBER, kk))
        elif i == 2:
            magnet(d, cx - 40, cy, 100, 50, 0, kk)
            box(d, (cx + 30, cy - 30, cx + 90, cy + 30), (6, 10, 20), RED, 6, 3, kk)
        else:
            pts = [(cx - 130 + j * 5, cy - 40 * math.sin(j * 0.35) * (1 if j < 30 else 0.25)) for j in range(52)]
            d.line(pts, fill=fade(PURPLE, kk), width=5)
        text(d, (x + 190, 590), a, 36, c, "Bold", "mm", k=kk)
        text(d, (x + 190, 640), b, 24, DIM, "Medium", "mm", k=kk)

def s_probe(d, t, dur):
    chrome(d, "STEP 5 · HOMING", "Feeling the bed", "Height is extra fussy: the first layer is only a fraction of a millimetre thick. So many printers touch a probe to the bed at a grid of points, and correct for any tilt or warp as they print.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 300, 1620, 600
    pts = [(x0 + (x1 - x0) * i / 60, y + 26 * math.sin(i / 60 * math.pi * 1.3) - 14 * i / 60) for i in range(61)]
    d.line(pts, fill=fade(TXT, k), width=6)
    n = int(clamp((t - 1.0) / 3.2) * 7) if t > 1.0 else 0
    for j in range(7):
        u = (j + 0.5) / 7
        px = x0 + (x1 - x0) * u
        py = y + 26 * math.sin(u * math.pi * 1.3) - 14 * u
        if j < n:
            d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=GREEN)
            text(d, (px, py + 50), f"{(py - y) / 100:+.2f}", 24, GREEN, "Bold", "mm", mono=True)
        if j == min(n, 6):
            d.rectangle([px - 18, 380, px + 18, py - 40], fill=fade(PURPLE, k))
            d.ellipse([px - 14, py - 46, px + 14, py - 18], fill=fade(PURPLE, k))
    text(d, (W // 2, 330), "mm, measured at each point (illustration)", 26, DIM, "Medium", "mm", k=prog(t, 3.0, 3.5))
    if t > 4.6:
        kk = prog(t, 4.6, 5.1)
        pts2 = [(x, yy - 20) for x, yy in pts]
        d.line(pts2, fill=fade(AMBER, kk), width=4)
        text(d, (300, 470), "first layer follows the bed", 28, AMBER, "Bold", "lm", k=kk)

# ---------------- chapter 6: feedback ----------------
def s_skip(d, t, dur):
    chrome(d, "STEP 6 · FEEDBACK", "When the count lies", "Counting has one weakness. If the nozzle snags, or a move is too fast, the motor can skip steps. The counter doesn't know. Every layer after that is printed in the wrong place.", t, dur)
    k = prog(t, 0.2, 0.6)
    bx, by, lh = 860, 760, 28
    n = int(clamp(t / 5.0) * 14)
    for i in range(n):
        off = 70 if i >= 7 else 0
        c = RED if i >= 7 else CYAN
        d.rectangle([bx + off, by - (i + 1) * lh, bx + 400 + off, by - i * lh - 4], fill=mix(BG, c, 0.7))
    if n > 7:
        kk = prog(t, 2.6, 3.1)
        text(d, (bx + 520, by - 8 * lh), "layer shift", 40, RED, "Bold", "lm", k=kk)
        counter(d, 120, 330, "firmware thinks", "X = 50.0 mm", AMBER, kk, 660)
        counter(d, 120, 460, "head is really at", "X ≈ 47 mm", RED, prog(t, 3.4, 3.9), 660)
    text(d, (W // 2, 805), "(illustration)", 24, DIM, "Medium", "mm", k=k)

def s_encoder(d, t, dur):
    chrome(d, "STEP 6 · FEEDBACK", "Add a sensor: the encoder", "The fix is to measure. A rotary encoder is a slotted disc on the motor shaft. Light shines through the slots onto two sensors, A and B, a quarter of a slot apart.", t, dur)
    k = prog(t, 0.2, 0.6)
    ang = t * 0.6
    disc(d, 560, 500, 240, ang, k)
    for j, (c, dy) in enumerate([(PHASE_A, -30), (PHASE_B, 30)]):
        d.ellipse([560 - 12 + 220 - 24, 500 + dy - 12 - 220 + 220, 560 + 12 + 220 - 24, 500 + dy + 12], fill=fade(c, k))
    kk = prog(t, 1.4, 1.9)
    text(d, (1000, 360), "A", 36, PHASE_A, "Bold", "mm", k=kk)
    text(d, (1000, 560), "B", 36, PHASE_B, "Bold", "mm", k=kk)
    square(d, 1040, 330, 660, 60, -ang * 24 / (2 * math.pi), 6, PHASE_A, kk)
    square(d, 1040, 530, 660, 60, -ang * 24 / (2 * math.pi) + 0.25, 6, PHASE_B, kk)
    text(d, (1370, 680), "which one leads tells the direction", 30, TXT, "Bold", "mm", k=prog(t, 3.2, 3.7))
    text(d, (1370, 730), "counting edges tells the distance", 30, TXT, "Bold", "mm", k=prog(t, 3.8, 4.3))

def s_loop(d, t, dur):
    chrome(d, "STEP 6 · FEEDBACK", "Closing the loop", "Now the controller compares where the axis should be with where the encoder says it is. Any error, and it pushes harder to correct it. That's closed-loop control, and it's how servo motors work.", t, dur)
    k = prog(t, 0.2, 0.6)
    boxes = [(160, "target", AMBER), (560, "controller", PURPLE), (960, "motor", GREEN), (1360, "axis", CYAN)]
    for i, (x, n, c) in enumerate(boxes):
        kk = prog(t, 0.4 + i * 0.4, 0.8 + i * 0.4)
        box(d, (x, 380, x + 320, 500), PANEL, c, 16, 3, kk)
        text(d, (x + 160, 440), n, 36, c, "Bold", "mm", k=kk)
        if i < 3: arrow(d, (x + 320, 440), (x + 400 - 6, 440), DIM, 5, kk)
    kk = prog(t, 2.2, 2.7)
    d.line([1520, 500, 1520, 640, 720, 640], fill=fade(BLUE, kk), width=5)
    arrow(d, (720, 640), (720, 506), BLUE, 5, kk)
    box(d, (1000, 600, 1260, 680), PANEL, BLUE, 12, 3, kk)
    text(d, (1130, 640), "encoder", 30, BLUE, "Bold", "mm", k=kk)
    if t > 3.6:
        kj = prog(t, 3.6, 4.1)
        e = 2.5 * math.exp(-(t - 3.6) * 1.2) * math.cos((t - 3.6) * 5)
        text(d, (720, 330), f"error = {e:+.2f} mm", 34, RED if abs(e) > 0.3 else GREEN, "Bold", "mm", mono=True, k=kj)
        text(d, (1520, 330), "(illustration)", 24, DIM, "Medium", "mm", k=kj)

def s_scale(d, t, dur):
    chrome(d, "STEP 6 · FEEDBACK", "Measure the table itself", "An encoder on the motor can't see slack in the screw or the belt. So precise machine tools often add a linear scale: a ruler along the axis, read by a sensor on the moving table.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1 = 240, 1680
    d.rectangle([x0, 420, x1, 460], fill=fade((60, 66, 90), k))
    for i in range(0, x1 - x0, 12):
        h = 30 if i % 120 == 0 else 14
        d.line([x0 + i, 420, x0 + i, 420 + h], fill=fade(TXT, k), width=2)
    tx = 600 + 600 * prog(t, 1.2, 4.5)
    box(d, (tx - 200, 500, tx + 200, 640), PANEL, CYAN, 14, 4, k)
    text(d, (tx, 570), "table", 36, CYAN, "Bold", "mm", k=k)
    box(d, (tx - 40, 380, tx + 40, 500), mix(BG, BLUE, 0.35), BLUE, 8, 4, k)
    text(d, (tx, 340), "read head", 28, BLUE, "Bold", "mm", k=k)
    text(d, (W // 2, 720), "measures the real position, after all the slack", 32, AMBER, "Bold", "mm", k=prog(t, 3.4, 3.9))

def s_compare(d, t, dur):
    chrome(d, "STEP 6 · FEEDBACK", "Open loop or closed loop?", "Most hobby printers stay open loop: steppers are cheap and, run within their limits, they rarely skip. Many industrial CNC machines close the loop with servos and encoders.", t, dur)
    cols = [("OPEN LOOP", AMBER, ["count the pulses", "home at start-up", "cheap and simple", "can't see a skipped step"], "most hobby 3D printers"),
            ("CLOSED LOOP", GREEN, ["measure the position", "correct any error", "more parts, more cost", "catches mistakes"], "many industrial CNC machines")]
    for i, (n, c, lines, who) in enumerate(cols):
        x = 200 + i * 800
        kk = prog(t, 0.4 + i * 1.4, 0.9 + i * 1.4)
        box(d, (x, 260, x + 720, 790), PANEL, c, 18, 3, kk)
        text(d, (x + 360, 320), n, 50, c, "Bold", "mm", k=kk)
        for j, ln in enumerate(lines):
            text(d, (x + 60, 410 + j * 70), "•  " + ln, 34, TXT, "Medium", "lm", k=kk)
        text(d, (x + 360, 730), who, 30, DIM, "Bold", "mm", k=kk)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "From one coil to a machine that knows", "Coils make a stepper click. Pulses become steps, steps become millimetres, and firmware counts them. Homing finds zero. Encoders catch what counting misses.", t, dur)
    stg = [("Coil", AMBER), ("Steps", CYAN), ("Motion", GREEN), ("Count", PURPLE), ("Home", RED), ("Feedback", BLUE)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(stg):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.2:
        gantry(d, 560, 1360, 640, 0.5 + 0.3 * math.sin(t * 1.5), prog(t, 4.2, 4.7))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does a smartwatch", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "read your heart rate?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
          ("03_coil", s_coil, 8), ("04_rotor", s_rotor, 8), ("05_teeth", s_teeth, 8),
          ("06_sequence", s_sequence, 8), ("07_micro", s_micro, 8), ("08_driver", s_driver, 8),
          ("09_belt", s_belt, 8), ("10_stepsmm", s_stepsmm, 8), ("11_screw", s_screw, 8),
          ("12_count", s_count, 8), ("13_gcode", s_gcode, 8), ("14_accel", s_accel, 8),
          ("15_unknown", s_unknown, 8), ("16_endstop", s_endstop, 8), ("17_sensors", s_sensors, 8), ("18_probe", s_probe, 8),
          ("19_skip", s_skip, 8), ("20_encoder", s_encoder, 8), ("21_loop", s_loop, 8), ("22_scale", s_scale, 8), ("23_compare", s_compare, 8),
          ("24_recap", s_recap, 8), ("25_end", s_end, 6)]

NARRATION = {
 "01_hook": "This print head has to put each line of plastic in the right place, to within a fraction of a millimetre, for hours. But in most hobby 3D printers, nothing actually measures where the head is while it prints. So how does it know where it is? It counts.",
 "02_cover": "Today, we'll build the answer up from scratch. We'll start with one coil of wire, and turn it into a motor that moves in tiny clicks. Then we'll turn clicks into millimetres, let the firmware count them, find zero when the machine switches on, and finally, add sensors for when counting isn't enough.",
 "03_coil": "Step one: one coil. Wind a wire around a piece of iron, and pass a current through it. The coil becomes an electromagnet, with a north end and a south end. Bring a permanent magnet close, and it gets pulled in. Switch the current off, and the pull disappears.",
 "04_rotor": "Now put a magnet on a shaft, and surround it with coils. Energise one pair of coils, and the magnet swings round to line up with them. Switch to the next pair, and it turns to follow. Keep switching in order, and the shaft rotates, one position at a time. That's the basic idea of a stepper motor.",
 "05_teeth": "Four positions per turn would be far too coarse. So real stepper motors have fine teeth, on the rotor and on the coils around it. A very common type moves in two hundred steps per turn. Three hundred and sixty degrees, divided by two hundred, is one point eight degrees per step.",
 "06_sequence": "Step two: steps. Inside, a typical stepper has two groups of coils, called A and B. To turn it, the driver energises them in a fixed four-beat rhythm. A forwards, B forwards, A reversed, B reversed, and repeat. Each beat moves the shaft forward one step. Play the rhythm backwards, and it turns the other way.",
 "07_micro": "Modern drivers go further, with microstepping. Instead of switching each coil fully on or off, they blend the two currents in small stairs, following a smooth wave. The rotor settles at positions in between the full steps. Split each step into sixteen, for example, and two hundred steps per turn becomes three thousand two hundred.",
 "08_driver": "The main board doesn't power the coils itself. That's the job of a driver chip, one for each motor. The board talks to it with just two signals. The direction pin says which way to turn. And every single pulse on the step pin means: move one microstep. One pulse, one microstep.",
 "09_belt": "Step three: motion. We need sliding, not turning. On many printers, a toothed pulley on the motor pulls a toothed rubber belt, and the belt is clamped to the print head. A common setup has twenty teeth, two millimetres apart. So one full turn of the motor moves the belt forty millimetres.",
 "10_stepsmm": "Now we can work out the number that matters most: steps per millimetre. Three thousand two hundred microsteps per turn, divided by forty millimetres per turn, gives eighty steps per millimetre. So on paper, one pulse moves the head one eightieth of a millimetre. In practice, the belt and frame limit the real accuracy.",
 "11_screw": "For moving the bed up and down, or for a C N C machine pushing a cutter through metal, a screw is common instead. The motor turns the screw, and a nut on the screw carries the load. A typical printer lead screw moves eight millimetres per turn. With the same driver, that's four hundred steps per millimetre. Slower, but stronger, and finer.",
 "12_count": "Step four: counting. Here's the trick. The firmware keeps a counter for every axis. Each pulse it sends in one direction adds one. Each pulse in the other direction takes one away. The position is simply that count, divided by the steps per millimetre. Notice what's missing. Nothing ever measures the head.",
 "13_gcode": "So where do the moves come from? Your slicer turns the 3 D model into G-code, a long list of simple instructions. Say the head is at zero, and the next line says go to X fifty, Y twenty. At eighty steps per millimetre, that's four thousand pulses on X, and one thousand six hundred on Y, timed so that both axes arrive at the same moment.",
 "14_accel": "But a motor, and the head it's carrying, can't jump straight to full speed. So the firmware plans every move. It ramps the pulse rate up, cruises, then ramps it down before the corner. If you ask for too much speed, too quickly, the rotor can't keep up with the pulses. It falls behind, and steps are lost.",
 "15_unknown": "Step five: homing. A counter only tells you how far you've moved since you started counting. With the power off, the motors hold nothing, and you can push the head anywhere by hand. So when the printer switches on, the count is zero, but the true position could be anywhere.",
 "16_endstop": "That's why the first thing most printers do is home. Each axis moves towards a small switch at one end of its travel. The moment the switch clicks, the firmware says, this is zero, and resets the counter. Many machines touch it quickly first, back off, then touch it again slowly, for a more repeatable zero.",
 "17_sensors": "That end stop can take different forms. A mechanical switch, where a lever closes a contact. An optical sensor, where a flag breaks a beam of light. Or a magnet and a Hall effect sensor. Some driver chips can even sense the motor stalling against the end of the rail, so no switch is needed at all.",
 "18_probe": "Height is extra fussy, because the first layer is only a fraction of a millimetre thick. So many printers carry a probe. It touches the bed at a grid of points, and records how high each one is. Then, as it prints the first layers, the firmware nudges the height up and down, to follow any tilt or warp in the bed.",
 "19_skip": "Step six: feedback. Counting has one weakness. If the nozzle snags on a curled-up edge, or a move is simply too fast, the motor can skip steps. The counter has no idea. It still believes the head is where it sent it. And every layer printed after that point is shifted sideways. That's the classic layer shift.",
 "20_encoder": "The cure is to stop trusting, and start measuring. A rotary encoder is a disc with slots, fixed to the motor shaft. Light shines through the slots onto two sensors, called A and B, placed a quarter of a slot apart. Counting the pulses tells you how far the shaft has turned. And which sensor changes first tells you the direction.",
 "21_loop": "Now the controller can compare two things: where the axis should be, and where the encoder says it is. The difference is the error. If there's any error, the controller drives the motor harder, or backs it off, to shrink it. That's closed-loop control, and it's the idea behind a servo motor.",
 "22_scale": "But an encoder on the motor still only sees the motor. It can't see slack in the screw, or stretch in a belt. So precise machine tools often add a linear scale. It's like a very fine ruler fixed along the axis, read by a sensor that rides on the moving table. It measures where the table really is.",
 "23_compare": "So which is better? Most hobby 3 D printers stay open loop. Steppers are cheap, and if you run them within their limits, they rarely skip. Many industrial C N C machines close the loop, with servos, encoders, and sometimes linear scales, because a ruined part, or a broken tool, costs far more than a sensor.",
 "24_recap": "Let's recap. A coil becomes a magnet, and coils switched in order make a stepper click. Pulses become steps. Steps become millimetres. The firmware counts them. Homing finds zero at switch-on. And when counting isn't enough, encoders and scales close the loop.",
 "25_end": "Next episode: how does a smartwatch read your heart rate, with nothing but a light? Subscribe so you don't miss it.",
}
OUTPUT = "how_a_3d_printer_knows_where_it_is_ep12_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep12/{name}.mp4", f"ep12/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep12", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    for j in range(0, len(SCENES), 9):
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES[j:j + 9]):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save(f"ep12/sheet{j // 9 + 1}.jpg", quality=85)
