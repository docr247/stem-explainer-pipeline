"""Tech 101, episode 2 Short: your code is just numbers.  (style: paper, vertical)"""
import math, sys
import style
from style import clamp, prog, pop, mix
import ep2
from ep2 import led, field_cols, ASM

V = style.get("paper", vertical=True)
W, H, FPS = V.W, V.H, V.FPS
VOICE, SPEED, LANG = V.VOICE, V.SPEED, V.LANG
BG, PANEL, LINE, TXT, DIM = V.BG, V.PANEL, V.LINE, V.TXT, V.DIM
ACC, HIL, GOOD, BAD, EXTRA, BLUE, ONA = V.ACCENT, V.HILITE, V.GOOD, V.BAD, V.EXTRA, V.BLUE, V.ON_ACCENT
SOFT = ep2.SOFT
CX = 500   # centre of the safe area (x 70..930)

def card(d, xy, col, t, a, r=20, label=None, size=44, tcol=None, mono=False, w="Bold", outline=None, width=4):
    if t < a: return 0.0
    s = max(0.0, pop(t, a, a + 0.5)); k = prog(t, a, a + 0.25)
    x0, y0, x1, y1 = ep2._scale(xy, s)
    if x1 - x0 < 4: return s
    V.box(d, (x0, y0, x1, y1), col, outline, int(min(r, (x1 - x0) / 2, (y1 - y0) / 2)), width, k)
    if label:
        V.text(d, ((x0 + x1) / 2, (y0 + y1) / 2), label, max(6, int(size * s)),
               tcol or (TXT if col in (PANEL, SOFT) else ONA), w, "mm", mono=mono, k=k)
    return s

def head(d, lines, t, col=None, y=250, size=80):
    for i, ln in enumerate(lines):
        k = prog(t, 0.1 + i * 0.25, 0.6 + i * 0.25)
        V.text(d, (CX, y + i * (size + 16)), ln, size, col or TXT, "Bold", "mm", k=k)

def s_hook(d, t, dur):
    head(d, ["Your code is", "just numbers"], t, None, 260)
    card(d, (110, 480, 890, 580), PANEL, t, 0.5, 20, "OUT ^= 1u << 5;", 46, mono=True, w="Regular")
    if t > 1.0:
        V.arrow(d, (CX, 600), (CX, 600 + 70 * prog(t, 1.0, 1.4)), DIM, 7, 1.0)
    for i, (_, _, hx) in enumerate(ASM):
        x = 110 + (i % 3) * 270; y = 710 + (i // 3) * 120
        if i == 3: x = 245
        if i == 4: x = 515
        card(d, (x, y, x + 240, y + 96), HIL, t, 1.4 + i * 0.3, 18, hx, 50, mono=True)
    led(d, CX, 1060, ep2.blink(t, 3.0, 1.0), prog(t, 2.6, 3.0), r=60)
    V.caption_v(d, "So how does a chip turn them into light?", t, 1330)

def s_store(d, t, dur):
    head(d, ["Each instruction", "is a number"], t, HIL, 260)
    card(d, (180, 450, 820, 560), ACC, t, 0.4, 20, "EORS r1, r2", 50, mono=True, w="Regular")
    card(d, (300, 600, 700, 700), HIL, t, 1.0, 20, "0x4051", 60, mono=True)
    bits = "0100000001010001"; cols = field_cols()
    for i, b in enumerate(bits):
        r, c = i // 8, i % 8
        x, y = 110 + c * 100, 760 + r * 110
        card(d, (x, y, x + 88, y + 92), cols[i], t, 1.6 + i * 0.08, 14, b, 50, mono=True)
    # flash fills
    k = prog(t, 3.2, 3.6)
    if k > 0:
        V.box(d, (110, 1010, 890, 1250), PANEL, HIL, 22, 5, k)
        V.text(d, (CX, 1050), "stored in flash", 40, HIL, "Bold", "mm", k=k)
        for i in range(12):
            x, y = 150 + (i % 6) * 120, 1090 + (i // 6) * 75
            on = t > 3.6 + i * 0.12
            V.box(d, (x, y, x + 100, y + 60), HIL if on else SOFT, None, 10, 0, k, shadow=False)
    V.caption_v(d, "Compiled, then kept safe in flash.", t, 1310)

def s_run(d, t, dur):
    head(d, ["Fetch. Decode.", "Execute."], t, BLUE, 260)
    cx, cy, R = CX, 760, 240
    items = [("FETCH", BLUE), ("DECODE", EXTRA), ("EXECUTE", HIL)]
    active = int(max(0, t - 1.5) * 2.5) % 3 if t > 1.5 else -1
    k = prog(t, 0.6, 1.0)
    pts = [(cx + R * math.cos(a / 40 * 2 * math.pi), cy + R * math.sin(a / 40 * 2 * math.pi)) for a in range(41)]
    V.line(d, pts, mix(BG, LINE, 0.3), 8, k)
    for i, (n, c) in enumerate(items):
        a = -math.pi / 2 + i * 2 * math.pi / 3
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        grow = 1.12 if i == active else 1.0
        card(d, (x - 150 * grow, y - 55 * grow, x + 150 * grow, y + 55 * grow), c if (i == active or active < 0) else mix(c, BG, 0.45),
             t, 0.8 + i * 0.3, 26, n, 40)
    card(d, (cx - 90, cy - 50, cx + 90, cy + 50), PANEL, t, 1.4, 20, "PC", 50, outline=HIL)
    V.pill(d, (CX, 1120), "tens of millions per second", 40, HIL, prog(t, 2.6, 3.0))
    V.text(d, (CX, 1200), "(example: a 48 MHz clock)", 32, DIM, "Medium", "mm", k=prog(t, 3.0, 3.4))
    V.caption_v(d, "Tens of millions of times a second.", t, 1310)

def s_wires(d, t, dur):
    head(d, ["One address is", "really wires"], t, GOOD, 260)
    V.pill(d, (CX, 470), "EXAMPLE  0x4800 0014", 40, HIL, prog(t, 0.4, 0.8))
    set5 = t > 2.4
    for i in range(8):
        b = 7 - i
        on = (b == 5 and set5)
        x = 120 + i * 100
        card(d, (x, 580, x + 88, 670), HIL if on else SOFT, t, 0.8 + i * 0.06, 14, "1" if on else "0", 50, mono=True)
        V.text(d, (x + 44, 550), str(b), 28, DIM, "Medium", "mm", k=prog(t, 0.8, 1.1))
        V.line(d, [(x + 44, 680), (x + 44, 790)], HIL if on else mix(BG, LINE, 0.35), 10 if on else 5, prog(t, 1.2, 1.6))
    card(d, (100, 790, 900, 860), ACC, t, 1.2, 16, "pins", 36)
    x5 = 120 + 2 * 100 + 44
    if t > 1.6:
        k = prog(t, 1.6, 2.0)
        V.line(d, [(x5, 860), (x5, 980), (CX, 980), (CX, 1010)], HIL if set5 else LINE, 8 if set5 else 5, k)
    led(d, CX, 1080, prog(t, 2.6, 2.9), prog(t, 1.8, 2.2), r=60)
    V.caption_v(d, "Set bit 5, and pin 5 goes high.", t, 1330)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    V.text(d, (CX, 600), "From code", 86, TXT, "Bold", "mm", k=k)
    V.text(d, (CX, 700), "to light", 86, HIL, "Bold", "mm", k=k)
    led(d, CX, 880, ep2.blink(t, 0.8, 1.0), prog(t, 0.4, 0.8), r=50)
    card(d, (140, 1080, 860, 1210), ACC, t, 1.0, 65, "Watch the full video", 54)
    if t > 1.6: V.arrow(d, (CX, 1380), (CX, 1240), ACC, 9, prog(t, 1.6, 2.1))

SCENES = [("s1", s_hook, 6), ("s2", s_store, 7), ("s3", s_run, 7), ("s4", s_wires, 7), ("s5", s_cta, 4)]

NARRATION = {
 "s1": "Here's a secret: your code is just numbers. So how does a tiny chip turn numbers into a blinking light?",
 "s2": "A compiler turns your C into instructions, and each one is a number, like hex, four zero five one. They're stored in flash, which remembers them without power.",
 "s3": "Then the core loops. Fetch an instruction. Decode it. Execute it. Tens of millions of times a second.",
 "s4": "And here's the trick. Some addresses aren't memory at all. Write a one to bit five of this example register, and pin five goes high. The L E D lights up.",
 "s5": "The whole journey, step by step, is in the full video.",
}
OUTPUT = "ep2_short_microcontroller_code_narrated.mp4"

def render(name, fn, dur): V.render_to("short2", name, fn, dur)

if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    print(V.preview("short2", SCENES))
