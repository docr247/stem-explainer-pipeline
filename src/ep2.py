"""Tech 101, episode 2: How does a microcontroller actually run your code?  (style: paper, format: build-up)

Running example: a generic 32-bit Arm Cortex-M microcontroller. All addresses and values are examples.
"""
import math, sys
import style
from style import clamp, ease, prog, pop, grow, mix, wrap

S = style.get("paper")
W, H, FPS = S.W, S.H, S.FPS
VOICE, SPEED, LANG = S.VOICE, S.SPEED, S.LANG
BG, PANEL, LINE, TXT, DIM = S.BG, S.PANEL, S.LINE, S.TXT, S.DIM
ACC, HIL, GOOD, BAD, EXTRA, BLUE, ONA = S.ACCENT, S.HILITE, S.GOOD, S.BAD, S.EXTRA, S.BLUE, S.ON_ACCENT
SOFT = mix(BG, LINE, 0.12)          # pale tint for empty cells

# ============================================================ helpers
def lerp(a, b, u): return a + (b - a) * u
def lerp2(p, q, u): return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))
def along(pts, u):
    return grow(pts, clamp(u))[-1]

def _scale(xy, s):
    x0, y0, x1, y1 = xy; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (cx + (x0 - cx) * s, cy + (y0 - cy) * s, cx + (x1 - cx) * s, cy + (y1 - cy) * s)

def card(d, xy, col, t, a, r=18, outline=None, width=3, label=None, size=34, tcol=None, w="Bold",
         sub=None, subsize=24, mono=False, dx=0, dy=0):
    """A paper cut-out that pops in (with overshoot) at time a. dx/dy: slide in from that offset."""
    if t < a: return 0.0
    s = max(0.0, pop(t, a, a + 0.5)); k = prog(t, a, a + 0.25)
    off = 1 - prog(t, a, a + 0.6)
    xy = (xy[0] + dx * off, xy[1] + dy * off, xy[2] + dx * off, xy[3] + dy * off)
    x0, y0, x1, y1 = _scale(xy, s)
    if x1 - x0 < 4 or y1 - y0 < 4: return s
    S.box(d, (x0, y0, x1, y1), col, outline, int(min(r, (x1 - x0) / 2, (y1 - y0) / 2)), width, k)
    if label:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        tc = tcol or (TXT if col in (PANEL, BG, SOFT) else ONA)
        S.text(d, (cx, cy - (subsize * 0.62 * s if sub else 0)), label, max(6, int(size * s)), tc, w, "mm", mono=mono, k=k)
        if sub:
            S.text(d, (cx, cy + size * 0.6 * s), sub, max(6, int(subsize * s)), tc, "Medium", "mm", k=k)
    return s

def ptext(d, xy, s, size, col, t, a, w="Bold", anchor="mm", mono=False):
    """Text that pops in."""
    if t < a: return
    sc = max(0.0, pop(t, a, a + 0.45))
    if sc < 0.05: return
    S.text(d, xy, s, max(6, int(size * sc)), col, w, anchor, mono=mono, k=prog(t, a, a + 0.25))

def ftext(d, xy, s, size, col, t, a, w="SemiBold", anchor="la", mono=False, dx=-30):
    """Text that slides in and fades."""
    if t < a: return
    off = (1 - prog(t, a, a + 0.5)) * dx
    S.text(d, (xy[0] + off, xy[1]), s, size, col, w, anchor, mono=mono, k=prog(t, a, a + 0.4))

def garrow(d, a, b, col, t, t0, width=6, span=0.5):
    k = prog(t, t0, t0 + span)
    if k <= 0.02: return
    S.arrow(d, a, lerp2(a, b, k), col, width, 1.0)

def gline(d, pts, col, t, t0, width=6, span=0.8):
    k = prog(t, t0, t0 + span)
    if k <= 0.01: return
    S.line(d, grow(pts, k), col, width)

def dots(d, pts, t, col, n=6, speed=0.35, r=8, k=1.0):
    for i in range(n):
        p = along(pts, (t * speed + i / n) % 1.0)
        S.circle(d, p, r, col, None, k=k, shadow=False)

def check(d, cx, cy, s, col, k=1.0):
    S.line(d, [(cx - s, cy), (cx - s * 0.3, cy + s * 0.7), (cx + s, cy - s * 0.8)], col, max(4, int(s / 3)), k)

def led(d, cx, cy, level, k=1.0, r=36, col=None):
    """A flat cut-out LED, dome centred at (cx, cy). level 0..1 = brightness. Returns (anode_bottom, cathode_bottom)."""
    col = col or GOOD
    rim = cy + 0.8 * r + 12
    la, lc = (cx - 0.35 * r, rim + 1.5 * r), (cx + 0.35 * r, rim + 1.2 * r)
    if k <= 0.01: return la, lc
    if level > 0.03:
        for g in range(5):
            rr = r + 12 + g * 13
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=S.fade(mix(BG, col, (0.42 - g * 0.08) * level), k), width=9)
    S.line(d, [(la[0], rim), la], LINE, 5, k)
    S.line(d, [(lc[0], rim), lc], LINE, 5, k)
    lit = mix(mix(col, BG, 0.6), mix(col, (255, 255, 236), 0.28), level)
    S.shadow(d, (cx - r, cy - r, cx + r, rim), int(r * 0.8), k)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=S.fade(lit, k))
    d.rectangle([cx - r, cy, cx + r, cy + 0.8 * r], fill=S.fade(lit, k))
    d.rounded_rectangle([cx - r - 7, cy + 0.8 * r, cx + r + 7, rim], 5, fill=S.fade(mix(lit, LINE, 0.2), k))
    d.ellipse([cx - r * 0.55, cy - r * 0.7, cx - r * 0.15, cy - r * 0.2], fill=S.fade(mix(lit, (255, 255, 255), 0.55), k))
    return la, lc

def led_symbol(d, x, y0, y1, level, k=1.0, col=None):
    """Schematic LED (triangle + bar), anode at top, between y0 and y1 on a vertical wire at x."""
    col = col or GOOD
    my = (y0 + y1) / 2
    if level > 0.03:
        for g in range(5):
            rr = 50 + g * 14
            d.ellipse([x - rr, my - rr, x + rr, my + rr], outline=S.fade(mix(BG, col, (0.4 - g * 0.075) * level), k), width=9)
    S.line(d, [(x, y0), (x, y0 + 14)], LINE, 5, k)
    S.line(d, [(x, y1 - 14), (x, y1)], LINE, 5, k)
    tri = [(x - 30, y0 + 14), (x + 30, y0 + 14), (x, y1 - 18)]
    d.polygon(tri, fill=S.fade(mix(mix(col, BG, 0.45), col, level), k))
    S.line(d, [(x - 30, y1 - 16), (x + 30, y1 - 16)], LINE, 6, k)
    for j in range(2):
        ax, ay = x + 40 + j * 18, my - 14 + j * 18
        S.arrow(d, (ax, ay), (ax + 30, ay - 26), mix(BG, HIL, 0.3 + 0.7 * level), 4, k)

def resistor(d, a, b, k=1.0, col=None, n=6, amp=14, width=5):
    col = col or LINE
    ax, ay = a; bx, by = b
    L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L; px, py = -uy, ux
    pts = [a, (ax + ux * L * 0.2, ay + uy * L * 0.2)]
    for i in range(n):
        u = 0.2 + 0.6 * (i + 0.5) / n
        sgn = 1 if i % 2 == 0 else -1
        pts.append((ax + ux * L * u + px * amp * sgn, ay + uy * L * u + py * amp * sgn))
    pts += [(ax + ux * L * 0.8, ay + uy * L * 0.8), b]
    S.line(d, pts, col, width, k)

def ground(d, x, y, k=1.0):
    S.line(d, [(x, y - 24), (x, y)], LINE, 5, k)
    for i, hw in enumerate((26, 17, 8)):
        S.line(d, [(x - hw, y + i * 10), (x + hw, y + i * 10)], LINE, 5, k)

def mcu(d, xy, t, a, label="MCU", sub=None, col=None, pins_tb=6, pins_lr=4):
    """Microcontroller cut-out with pins on all four sides; pops in at a."""
    col = col or ACC
    if t < a: return
    s = max(0.0, pop(t, a, a + 0.5)); k = prog(t, a, a + 0.25)
    x0, y0, x1, y1 = _scale(xy, s)
    w, h = x1 - x0, y1 - y0
    if w < 8: return
    pl = 16 * s
    for i in range(pins_tb):
        px = x0 + w * (i + 1) / (pins_tb + 1)
        d.rectangle([px - 6 * s, y0 - pl, px + 6 * s, y0], fill=S.fade(LINE, k))
        d.rectangle([px - 6 * s, y1, px + 6 * s, y1 + pl], fill=S.fade(LINE, k))
    for i in range(pins_lr):
        py = y0 + h * (i + 1) / (pins_lr + 1)
        d.rectangle([x0 - pl, py - 6 * s, x0, py + 6 * s], fill=S.fade(LINE, k))
        d.rectangle([x1, py - 6 * s, x1 + pl, py + 6 * s], fill=S.fade(LINE, k))
    S.box(d, (x0, y0, x1, y1), col, None, int(18 * s), 0, k)
    d.ellipse([x0 + 16 * s, y0 + 16 * s, x0 + 32 * s, y0 + 32 * s], fill=S.fade(mix(col, LINE, 0.35), k))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    S.text(d, (cx, cy - (16 * s if sub else 0)), label, max(6, int(40 * s)), ONA, "Bold", "mm", k=k)
    if sub: S.text(d, (cx, cy + 30 * s), sub, max(6, int(24 * s)), ONA, "Medium", "mm", k=k)

def gear(d, cx, cy, r, teeth, ang, col, k=1.0):
    if k <= 0.01: return
    pts, w = [], 2 * math.pi / teeth
    for i in range(teeth):
        a0 = ang + i * w
        for da, rr in ((-0.3, r * 0.8), (-0.18, r), (0.18, r), (0.3, r * 0.8)):
            a = a0 + da * w * 1.6
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=S.fade(col, k))
    d.ellipse([cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32], fill=S.fade(PANEL, k))

def code_card(d, x, y, lines, t, a, size=30, w=None, hl=-1, hlcol=None, lh=None, reveal=None, dx=0):
    """Paper card of monospace code. '//' comments are drawn dimmer. Returns the card box."""
    lh = lh or int(size * 1.6)
    w = w or int(max(S.textlen(d, ln, size, mono=True) for ln in lines) + 64)
    h = 30 + len(lines) * lh
    s = card(d, (x, y, x + w, y + h), PANEL, t, a, 20, dx=dx)
    if s <= 0: return (x, y, x + w, y + h)
    k = prog(t, a + 0.2, a + 0.5)
    off = dx * (1 - prog(t, a, a + 0.6))
    n = len(lines) if reveal is None else int(reveal)
    for i, ln in enumerate(lines[:n]):
        yy = y + 15 + i * lh
        if i == hl:
            d.rounded_rectangle([x + off + 10, yy, x + off + w - 10, yy + lh - 4], 10, fill=S.fade(mix(PANEL, hlcol or HIL, 0.3), k))
        code, _, com = ln.partition("//")
        ty = yy + lh / 2 - 2
        S.text(d, (x + off + 30, ty), code, size, TXT, "Regular", "lm", mono=True, k=k)
        if com:
            cx = x + off + 30 + S.textlen(d, code, size, mono=True)
            S.text(d, (cx, ty), "//" + com, size, DIM, "Regular", "lm", mono=True, k=k)
    return (x, y, x + w, y + h)

def bitrow(d, x, y, bits, t, a, cw=74, ch=78, gap=8, cols=None, step=0.1, size=40, labels=None):
    """A row of bit cells that pop in one by one. cols: per-cell fill (None = soft)."""
    for i, b in enumerate(bits):
        c = cols[i] if cols else (HIL if b == "1" else SOFT)
        cx = x + i * (cw + gap)
        card(d, (cx, y, cx + cw, y + ch), c, t, a + i * step, 12, label=b, size=size, mono=True,
             tcol=(TXT if c == SOFT else ONA))
        if labels: ptext(d, (cx + cw / 2, y - 22), labels[i], 22, DIM, t, a + i * step, "Medium")

def doc(d, xy, label, col, t, a, dx=0):
    """A file cut-out with a folded corner."""
    s = card(d, xy, PANEL, t, a, 10, dx=dx)
    if s <= 0: return
    k = prog(t, a, a + 0.3); off = dx * (1 - prog(t, a, a + 0.6))
    x0, y0, x1, y1 = xy; x0 += off; x1 += off
    d.polygon([(x1 - 30, y0), (x1, y0 + 30), (x1 - 30, y0 + 30)], fill=S.fade(mix(PANEL, LINE, 0.25), k))
    d.rectangle([x0, y0, x0 + 14, y1], fill=S.fade(col, k))
    S.text(d, (x0 + 36, (y0 + y1) / 2), label, 32, TXT, "Bold", "lm", mono=False, k=k)

def hexw(v): return f"0x{v >> 16:04X} {v & 0xFFFF:04X}"

def blink(t, t0, rate=1.0):
    return 1.0 if t > t0 and int((t - t0) * rate * 2) % 2 == 0 else 0.0

ASM = [("LDR  r0, =0x48000014", "load the register's address", "4805"),
       ("LDR  r1, [r0]", "read its current value", "6801"),
       ("MOVS r2, #0x20", "make a mask: only bit 5 set", "2220"),
       ("EORS r1, r2", "flip bit 5 (exclusive or)", "4051"),
       ("STR  r1, [r0]", "write the result back", "6001")]
C_PROG = ["int main(void) {", "  gpio_setup();", "  while (1) {", "    OUT ^= 1u << 5;   // flip bit 5",
          "    delay_ms(500);", "  }", "}"]
FIELDS = [(0, 6, BLUE, "010000", "data-processing group"), (6, 10, EXTRA, "0001", "operation: EOR"),
          (10, 13, GOOD, "010", "Rm = r2"), (13, 16, BAD, "001", "Rdn = r1")]

def field_cols():
    cols = []
    for a, b, c, _, _ in FIELDS: cols += [c] * (b - a)
    return cols

# ============================================================ captions (shorter versions of the narration)
CAP = {
 "01_hook": "Ever wondered how a few lines of text make a real light blink on a tiny chip? Let's build it up, one piece at a time.",
 "02_cover": "Code into numbers, numbers into the chip, wake it up, watch it run, touch the pins, keep time. Example: a 32-bit Cortex-M chip.",
 "03_source": "Step one: compile. Your chip can't read C, so a compiler translates it into machine instructions.",
 "04_asm": "One line becomes a few small steps: load, read, make a mask, flip the bit, write back. Output varies by compiler.",
 "05_number": "Each instruction is just a number. EORS r1, r2 is hex 4051: some bits pick the operation, the rest pick registers.",
 "06_linker": "Step two: into the chip. The linker joins your files and, following a linker script, gives everything an address.",
 "07_sections": "Code and constants go in flash. Variables with starting values live in RAM, but their values are saved in flash too.",
 "08_programmer": "A debug probe connects through two signal wires plus ground. It erases flash, writes your program, then checks it.",
 "09_nonvolatile": "Pull the power and RAM forgets. Flash keeps your program for years. Rewriting it is slow, a whole block at a time.",
 "10_reset": "Step three: wake up. The chip holds its core in reset until the power is steady, then lets go. But where does it start?",
 "11_vector": "The core loads the first word of the vector table into the stack pointer, and the second word into the program counter.",
 "12_table": "The rest of the table: where to jump for faults and interrupts. The lowest bit of each address is 1: Thumb code.",
 "13_startup": "Startup code copies starting values from flash into RAM, then fills the zero section, .bss, with zeros.",
 "14_main": "It usually sets up the clocks too (the order varies), then calls main. Main typically never returns: it loops forever.",
 "15_registers": "Step four: run. Registers are tiny, super-fast slots, 32 bits each. The star of the show is the program counter.",
 "16_fetch": "The program counter is a bookmark: the address of the next instruction. Fetch reads that instruction out of flash.",
 "17_decode": "Decode: the core reads the bits and sets its internal switches, so the right registers connect to the arithmetic unit.",
 "18_execute": "Execute: r1 and r2 flow through the ALU, the result lands in r1, and the PC moves on two bytes.",
 "19_pipeline": "Many Cortex-M cores overlap the steps like an assembly line. A branch at the end sends the loop back to the top.",
 "20_memmap": "Step five: touch the pins. To the core, everything is an address. Arm splits the 4 GB space into regions.",
 "21_register": "This example address is a GPIO output register. Each bit is wired to a pin. Set bit 5 to one, and pin 5 goes high.",
 "22_setup": "On most chips you first switch on the port's clock, then set the pin to output mode. Then writing the bit works.",
 "23_led": "The bit closes a tiny switch to the supply. Current flows out of the pin, through a resistor and the LED, to ground.",
 "24_volatile": "Compilers may skip writes that seem useless. 'volatile' says: every read and write here matters. Keep them all, in order.",
 "25_clock": "Step six: keep time. A clock ticks the core along: an example 48 MHz is 48 million ticks a second.",
 "26_toofast": "Without a delay the pin flips millions of times a second. Your eyes can't keep up: the LED just looks dimly on.",
 "27_delay": "Wait with a busy loop, or better, a hardware timer like SysTick: count 48,000 ticks for 1 ms, and sleep in between.",
 "28_recap": "Compile, link, flash. Reset, vector table, startup, main. Fetch, decode, execute with the clock. One write lights the LED.",
 "29_end": "Next episode: what really happens when you press a key? Subscribe so you don't miss it.",
}

# ============================================================ intro
def s_hook(d, t, dur):
    S.chrome(d, "", "", CAP["01_hook"], t, dur)
    ptext(d, (W / 2, 290), "How does text on a screen", 64, TXT, t, 3.4)
    ptext(d, (W / 2, 370), "make a real light blink?", 64, HIL, t, 3.8)
    # one wire to an LED (the tiny first piece)
    lvl = blink(t, 1.6, 1.0)
    la, lc = led(d, 1600, 560, lvl * prog(t, 1.6, 1.8), prog(t, 0.2, 0.6), r=42)
    gline(d, [(1300, la[1]), (1390, la[1])], LINE, t, 0.8, 5, 0.3)
    if t > 1.0: resistor(d, (1390, la[1]), (1510, la[1]), prog(t, 1.0, 1.3))
    gline(d, [(1510, la[1]), la], LINE, t, 1.2, 5, 0.3)
    gline(d, [lc, (lc[0], 730)], LINE, t, 1.2, 5, 0.3)
    if t > 1.4: ground(d, lc[0], 754, prog(t, 1.4, 1.7))
    mcu(d, (1000, 470, 1290, 730), t, 2.0, "MCU", "example chip", ACC)
    # then the code
    code_card(d, 150, 470, ["while (1) {", "  OUT ^= 1u << 5;", "  delay_ms(500);", "}"], t, 2.6, size=34, dx=-60)
    garrow(d, (740, 600), (960, 600), DIM, t, 3.0)
    card(d, (820, 520, 890, 580), HIL, t, 3.1, 35, label="?", size=40)

def s_cover(d, t, dur):
    S.chrome(d, "", "Here's what we'll cover", CAP["02_cover"], t, dur)
    items = [("1", "Compile", "code into numbers", ACC), ("2", "Flash", "numbers into the chip", HIL),
             ("3", "Reset", "how it wakes up", EXTRA), ("4", "Run", "fetch, decode, execute", BLUE),
             ("5", "Pins", "touching the real world", GOOD), ("6", "Timing", "a clock sets the pace", BAD)]
    for i, (n, a, b, c) in enumerate(items):
        st = 0.5 + i * 0.6
        x, y = 160 + (i % 3) * 540, 280 + (i // 3) * 200
        s = card(d, (x, y, x + 500, y + 160), PANEL, t, st, 22, dy=40)
        if s <= 0: continue
        k = prog(t, st, st + 0.3)
        S.circle(d, (x + 70, y + 80), 44 * min(1.0, s), c, k=k)
        S.text(d, (x + 70, y + 80), n, 44, ONA, "Bold", "mm", k=k)
        S.text(d, (x + 140, y + 60), a, 44, TXT, "Bold", "lm", k=k)
        S.text(d, (x + 140, y + 110), b, 28, DIM, "Medium", "lm", k=k)
    S.pill(d, (W / 2, 770), "Example chip: a generic 32-bit Arm Cortex-M microcontroller", 30, ACC, prog(t, 4.6, 5.0))

# ============================================================ STEP 1: compile
def s_source(d, t, dur):
    S.chrome(d, "STEP 1 · COMPILE", "Start with one line of C", CAP["03_source"], t, dur)
    code_card(d, 130, 260, C_PROG, t, 0.3, size=30, hl=3 if t > 2.0 else -1, dx=-60)
    ftext(d, (150, 760), "C: written for people", 30, DIM, t, 1.2)
    # the highlighted line travels into the compiler
    u = prog(t, 3.0, 4.6)
    if t > 3.0 and t < 4.8:
        p = lerp2((300, 440), (1040, 520), u)
        s = 1 - 0.6 * u
        S.box(d, (p[0], p[1], p[0] + 420 * s, p[1] + 56 * s), mix(PANEL, HIL, 0.3), None, 12, 0, 1.0)
        S.text(d, (p[0] + 20 * s, p[1] + 28 * s), "OUT ^= 1u << 5;", max(8, int(28 * s)), TXT, "Regular", "lm", mono=True)
    s = card(d, (1000, 380, 1360, 660), EXTRA, t, 1.8, 26)
    if s > 0:
        k = prog(t, 1.8, 2.1)
        gear(d, 1110, 470, 52 * min(1, s), 9, t * 1.2, mix(EXTRA, ONA, 0.35), k)
        gear(d, 1220, 520, 38 * min(1, s), 7, -t * 1.6 + 0.2, mix(EXTRA, ONA, 0.55), k)
        S.text(d, (1180, 610), "COMPILER", 38, ONA, "Bold", "mm", k=k)
    garrow(d, (1380, 520), (1490, 520), DIM, t, 4.8)
    for i, (_, _, hx) in enumerate(ASM):
        card(d, (1520, 300 + i * 92, 1780, 372 + i * 92), HIL, t, 5.2 + i * 0.5, 14, label=hx, size=36, mono=True, dx=-80)
    ftext(d, (1650, 790), "machine code: for the chip", 30, DIM, t, 7.8, "SemiBold", "mm", dx=0)

def s_asm(d, t, dur):
    S.chrome(d, "STEP 1 · COMPILE", "One line becomes a few instructions", CAP["04_asm"], t, dur)
    card(d, (140, 260, 700, 330), mix(PANEL, HIL, 0.3), t, 0.3, 14, label="OUT ^= 1u << 5;", size=32, mono=True,
         tcol=TXT, w="Regular")
    garrow(d, (420, 340), (420, 380), DIM, t, 0.9, 5, 0.3)
    for i, (asm, note, _) in enumerate(ASM):
        st = 1.4 + i * 1.6
        y = 395 + i * 88
        card(d, (140, y, 700, y + 70), ACC, t, st, 14, label=asm, size=30, mono=True, w="Regular", dx=-80)
        garrow(d, (720, y + 35), (780, y + 35), DIM, t, st + 0.4, 4, 0.3)
        ftext(d, (800, y + 35), note, 34, TXT, t, st + 0.5, "SemiBold", "lm")
    S.pill(d, (1560, 290), "EXAMPLE compiler output", 28, HIL, prog(t, 9.6, 10.0))
    # a live register value: bit 5 flips when EORS lights up
    hl = int((t - 9.5) / 0.7) % 5 if t > 9.5 else -1
    if hl >= 0:
        y = 395 + hl * 88
        d.rounded_rectangle([130, y - 8, 710, y + 78], 18, outline=S.fade(HIL, 1), width=5)

def s_number(d, t, dur):
    S.chrome(d, "STEP 1 · COMPILE", "Each instruction is just a number", CAP["05_number"], t, dur)
    card(d, (300, 260, 720, 350), ACC, t, 0.3, 16, label="EORS r1, r2", size=40, mono=True, w="Regular")
    garrow(d, (740, 305), (880, 305), DIM, t, 1.0)
    card(d, (900, 260, 1240, 350), HIL, t, 1.4, 16, label="0x4051", size=48, mono=True)
    garrow(d, (1260, 305), (1400, 305), DIM, t, 2.0)
    ptext(d, (1540, 305), "16 bits", 44, TXT, t, 2.4)
    bits = "0100000001010001"
    x0 = (W - 16 * 82 + 8) / 2
    labels = [str(15 - i) for i in range(16)]
    k2 = prog(t, 6.0, 6.6)
    cols = [mix(HIL if b == "1" else SOFT, c, k2) for b, c in zip(bits, field_cols())] if t > 6.0 else None
    bitrow(d, x0, 450, bits, t, 3.0, cols=cols, step=0.13, labels=labels)
    for j, (a, b, c, val, lab) in enumerate(FIELDS):
        st = 6.4 + j * 0.8
        xa, xb = x0 + a * 82, x0 + b * 82 - 8
        k = prog(t, st, st + 0.4)
        if k <= 0: continue
        d.rounded_rectangle([xa, 550, xa + (xb - xa) * k, 562], 6, fill=S.fade(c, k))
        ptext(d, ((xa + xb) / 2, 600), val, 30, c, t, st + 0.1, "Bold", mono=True)
        ptext(d, ((xa + xb) / 2, 645), lab, 28, TXT, t, st + 0.2, "SemiBold")
    S.pill(d, (W / 2, 760), "On Cortex-M, most instructions are 16 or 32 bits long", 30, BLUE, prog(t, 10.0, 10.5))

# ============================================================ STEP 2: flash
def s_linker(d, t, dur):
    S.chrome(d, "STEP 2 · FLASH", "The linker gives everything an address", CAP["06_linker"], t, dur)
    files = [("main.o", ACC), ("gpio.o", GOOD), ("startup.o", EXTRA), ("C library", BLUE)]
    for i, (n, c) in enumerate(files):
        st = 0.4 + i * 0.4
        y = 270 + i * 125
        u = prog(t, 4.5 + i * 0.3, 5.3 + i * 0.3)
        if u < 1:
            dxm = u * 380
            doc(d, (140 + dxm, y, 440 + dxm, y + 95), n, c, t, st, dx=-60)
    s = card(d, (580, 380, 880, 640), EXTRA, t, 2.0, 26)
    if s > 0:
        k = prog(t, 2.0, 2.3)
        gear(d, 680, 470, 48 * min(1, s), 9, t * 1.1, mix(EXTRA, ONA, 0.35), k)
        gear(d, 780, 510, 34 * min(1, s), 7, -t * 1.5, mix(EXTRA, ONA, 0.55), k)
        S.text(d, (730, 600), "LINKER", 38, ONA, "Bold", "mm", k=k)
    # linker script note
    card(d, (520, 690, 940, 790), PANEL, t, 3.0, 16, outline=EXTRA, label="linker script", size=30,
         sub="a map of the chip's memory", subsize=24, tcol=TXT)
    garrow(d, (900, 510), (1010, 510), DIM, t, 6.2)
    # memory map
    card(d, (1040, 270, 1390, 840), PANEL, t, 3.4, 20, outline=HIL, width=4)
    card(d, (1440, 270, 1790, 840), PANEL, t, 3.8, 20, outline=GOOD, width=4)
    ptext(d, (1215, 310), "FLASH", 36, HIL, t, 3.6)
    ptext(d, (1615, 310), "RAM", 36, GOOD, t, 4.0)
    ptext(d, (1215, 350), "starts at 0x0800 0000", 24, DIM, t, 3.7, "Medium", mono=True)
    ptext(d, (1615, 350), "starts at 0x2000 0000", 24, DIM, t, 4.1, "Medium", mono=True)
    blocks = [("vector table", BLUE, 60), ("main", ACC, 80), ("gpio_setup", GOOD, 70), ("startup", EXTRA, 60), ("library", BLUE, 90)]
    y = 390
    for i, (n, c, hgt) in enumerate(blocks):
        card(d, (1070, y, 1360, y + hgt - 8), c, t, 6.6 + i * 0.4, 12, label=n, size=26, dy=-60)
        y += hgt
    S.pill(d, (1615, 600), "example addresses", 24, HIL, prog(t, 8.8, 9.2))

def s_sections(d, t, dur):
    S.chrome(d, "STEP 2 · FLASH", "Code in flash, variables in RAM", CAP["07_sections"], t, dur)
    secs = [(".text", "your code + constants", ACC), (".data", "int count = 3;", HIL),
            (".bss", "int total;   (starts at 0)", GOOD), ("stack", "grows as functions run", EXTRA)]
    for i, (n, sub, c) in enumerate(secs):
        st = 0.4 + i * 0.5
        y = 270 + i * 140
        card(d, (130, y, 250, y + 110), c, t, st, 16, label=n, size=30, dx=-60)
        ftext(d, (275, y + 55), sub, 30, TXT, t, st + 0.2, "SemiBold", "lm")
    fx, rx = (900, 1240), (1440, 1780)
    card(d, (fx[0], 260, fx[1], 840), PANEL, t, 0.6, 20, outline=HIL, width=4)
    card(d, (rx[0], 260, rx[1], 840), PANEL, t, 0.8, 20, outline=GOOD, width=4)
    ptext(d, ((fx[0] + fx[1]) / 2, 300), "FLASH", 36, HIL, t, 0.8)
    ptext(d, ((rx[0] + rx[1]) / 2, 300), "RAM", 36, GOOD, t, 1.0)
    ftext(d, ((rx[0] + rx[1]) / 2, 800), "higher addresses", 22, DIM, t, 1.2, "Medium", "mm", dx=0)
    def fly(src, dst, col, label, st, dashed=False):
        u = prog(t, st, st + 1.0)
        if t < st: return
        x0, y0 = lerp2(src, dst[:2], u)
        w, h = dst[2] - dst[0], dst[3] - dst[1]
        S.box(d, (x0, y0, x0 + w, y0 + h), col if not dashed else PANEL, col if dashed else None, 12, 4)
        S.text(d, (x0 + w / 2, y0 + h / 2), label, 26, ONA if not dashed else col, "Bold", "mm")
    fly((130, 270), (fx[0] + 25, 340, fx[1] - 25, 480), ACC, "code + constants", 3.0)
    fly((130, 410), (fx[0] + 25, 495, fx[1] - 25, 570), HIL, "starting values", 4.6, dashed=True)
    fly((130, 410), (rx[0] + 25, 340, rx[1] - 25, 420), HIL, ".data  count = 3", 5.6)
    fly((130, 550), (rx[0] + 25, 435, rx[1] - 25, 515), GOOD, ".bss  total = 0", 7.0)
    fly((130, 690), (rx[0] + 25, 680, rx[1] - 25, 770), EXTRA, "stack", 8.4)
    if t > 9.4:
        k = prog(t, 9.4, 9.9)
        yy = 670 - 40 * ((t - 9.4) % 1.5) / 1.5
        S.arrow(d, (rx[1] - 60, 670), (rx[1] - 60, yy - 20), EXTRA, 5, k)
        S.text(d, (rx[0] + 30, 640), "grows down", 24, EXTRA, "Bold", "lm", k=k)

def s_programmer(d, t, dur):
    S.chrome(d, "STEP 2 · FLASH", "A debug probe writes the flash", CAP["08_programmer"], t, dur)
    # computer
    s = card(d, (130, 320, 470, 540), LINE, t, 0.3, 18)
    if s > 0:
        k = prog(t, 0.3, 0.6)
        S.box(d, (150, 340, 450, 520), mix(BG, BLUE, 0.25), None, 10, 0, k, shadow=False)
        S.text(d, (300, 430), "your computer", 30, TXT, "Bold", "mm", k=k)
        d.rectangle([280, 540, 320, 580], fill=S.fade(LINE, k))
        d.rounded_rectangle([220, 580, 380, 596], 8, fill=S.fade(LINE, k))
    gline(d, [(470, 450), (620, 450)], LINE, t, 0.9, 8, 0.4)
    ptext(d, (545, 420), "USB", 24, DIM, t, 1.1, "Bold")
    card(d, (620, 390, 860, 510), EXTRA, t, 1.2, 18, label="debug probe", size=30)
    # three wires to the chip
    names = ["SWDIO", "SWCLK", "GND"]
    for i, n in enumerate(names):
        y = 400 + i * 60
        pts = [(860, 450 + (i - 1) * 30), (960, 450 + (i - 1) * 30), (1000, y), (1110, y)]
        gline(d, pts, [HIL, BLUE, LINE][i], t, 2.0 + i * 0.25, 6, 0.5)
        ptext(d, (1050, y - 20), n, 20, DIM, t, 2.4 + i * 0.25, "Bold", mono=True)
        if 4.0 < t and i < 2 and t < 11.5:
            dots(d, pts, t + i * 0.3, [HIL, BLUE][i], 4, 0.6, 7)
    # chip with a flash grid
    mcu(d, (1120, 300, 1780, 720), t, 1.6, "", None, ACC, 8, 5)
    if t > 2.0:
        k = prog(t, 2.0, 2.3)
        S.text(d, (1450, 340), "flash memory", 30, ONA, "Bold", "mm", k=k)
        rows, cols = 5, 8
        for r in range(rows):
            for c in range(cols):
                i = r * cols + c
                x, y = 1170 + c * 70, 380 + r * 62
                er = prog(t, 3.2 + i * 0.015, 3.4 + i * 0.015)
                wr = 1.0 if t > 5.0 + i * 0.12 else 0.0
                col = mix(mix(PANEL, ACC, 0.45), PANEL, er) if not wr else HIL
                S.box(d, (x, y, x + 60, y + 50), col, None, 8, 0, k, shadow=False)
                txt = "FF" if er > 0.5 and not wr else (["48", "05", "68", "01", "22", "20", "40", "51"][c] if wr else "")
                if txt: S.text(d, (x + 30, y + 25), txt, 22, TXT if not wr else ONA, "Regular", "mm", mono=True, k=k)
    steps = [("1  erase", 3.2), ("2  write", 5.0), ("3  verify", 10.2)]
    for i, (n, st) in enumerate(steps):
        on = t > st
        S.pill(d, (520 + i * 230, 790), n, 30, HIL if on else DIM, prog(t, 1.0 + i * 0.2, 1.4 + i * 0.2))
    if t > 10.4: check(d, 1450, 790, 26, GOOD, prog(t, 10.4, 10.8))
    ftext(d, (1110, 250), "erased flash typically reads as all ones (FF)", 24, DIM, t, 4.0, "Medium", "la", dx=0)

def s_nonvolatile(d, t, dur):
    S.chrome(d, "STEP 2 · FLASH", "Flash remembers. RAM forgets.", CAP["09_nonvolatile"], t, dur)
    off = 3.5 < t < 7.5
    # power switch
    s = card(d, (840, 280, 1080, 360), PANEL, t, 0.3, 40, outline=LINE, width=4)
    if s > 0:
        kx = prog(t, 3.5, 3.8) - prog(t, 7.5, 7.8)
        cx = lerp(1040, 880, kx)
        S.circle(d, (cx, 320), 30, GOOD if not off else BAD, k=1.0)
        S.text(d, (960, 395), "POWER " + ("OFF" if off else "ON"), 28, BAD if off else GOOD, "Bold", "mm", k=prog(t, 0.4, 0.8))
    for side, (x0, name, col) in enumerate([(160, "FLASH", HIL), (1120, "RAM", GOOD)]):
        card(d, (x0, 430, x0 + 640, 690), PANEL, t, 0.6 + side * 0.3, 22, outline=col, width=4)
        ptext(d, (x0 + 320, 465), name, 34, col, t, 0.8 + side * 0.3)
        for r in range(3):
            for c in range(8):
                i = r * 8 + c
                x, y = x0 + 30 + c * 74, 500 + r * 60
                st = 1.0 + side * 0.3 + i * 0.03
                if t < st: continue
                k = prog(t, st, st + 0.3)
                val = format((i * 37 + 11) % 256, "02X")
                cc = col
                if side == 1 and t > 3.6:
                    gone = prog(t, 3.6 + c * 0.06, 4.0 + c * 0.06)
                    cc = mix(col, SOFT, gone)
                    if gone > 0.5: val = "??" if t > 7.6 else ""
                    if t > 7.6: val = format((i * 91 + int(t * 3) * 7) % 256, "02X") if t < 8.8 else "??"
                S.box(d, (x, y, x + 62, y + 50), cc, None, 8, 0, k, shadow=False)
                if val: S.text(d, (x + 31, y + 25), val, 22, ONA if cc == col else TXT, "Regular", "mm", mono=True, k=k)
    ftext(d, (480, 725), "keeps its data with no power", 30, TXT, t, 2.0, "SemiBold", "mm", dx=0)
    ftext(d, (1440, 725), "loses it when the power goes", 30, TXT, t, 2.2, "SemiBold", "mm", dx=0)
    S.pill(d, (480, 800), "like a notebook: rewrite a whole page at a time", 26, HIL, prog(t, 9.0, 9.4))
    S.pill(d, (1440, 800), "like a whiteboard wiped in a power cut", 26, GOOD, prog(t, 9.6, 10.0))
    if t > 7.8 and t < 11.0:
        ptext(d, (1440, 400), "at power-up: random leftovers", 26, BAD, t, 7.8, "Bold")

# ============================================================ STEP 3: reset
def s_reset(d, t, dur):
    S.chrome(d, "STEP 3 · RESET", "Power on, wait, then let go", CAP["10_reset"], t, dur)
    gx0, gx1 = 200, 1100
    card(d, (150, 260, 1150, 820), PANEL, t, 0.2, 22)
    k = prog(t, 0.4, 0.8)
    S.line(d, [(gx0, 760), (gx1, 760)], DIM, 3, k)
    S.text(d, (gx1, 785), "time", 24, DIM, "Medium", "rm", k=k)
    # supply voltage
    S.text(d, (gx0, 300), "supply voltage", 28, BLUE, "Bold", "lm", k=k)
    S.text(d, (gx1, 300), "example: 3.3 V", 24, DIM, "Medium", "rm", k=k)
    pv = [(gx0 + i * 9, 480 - 140 * (1 - math.exp(-max(0, i * 9 - 60) / 110))) for i in range(101)]
    gline(d, pv, BLUE, t, 1.0, 6, 3.0)
    # reset line (active low)
    S.text(d, (gx0, 560), "reset line", 28, BAD, "Bold", "lm", k=k)
    xr = 760
    pr = [(gx0, 720), (xr, 720), (xr, 620), (gx1, 620)]
    gline(d, pr, BAD, t, 1.0, 6, 3.0)
    if t > 2.0: S.text(d, (420, 690), "held in reset", 26, BAD, "SemiBold", "mm", k=prog(t, 2.0, 2.4))
    if t > 3.6: S.text(d, (930, 650), "released!", 26, BAD, "Bold", "mm", k=prog(t, 3.6, 4.0))
    # the chip: asleep, then awake and puzzled
    awake = t > 4.2
    mcu(d, (1300, 400, 1700, 680), t, 0.6, "core", "awake" if awake else "in reset", EXTRA if awake else DIM, 5, 3)
    if not awake and t > 1.0:
        for i in range(3):
            u = ((t - 1.0) * 0.6 + i / 3) % 1
            S.text(d, (1640 + u * 60, 380 - u * 90), "z", 30 + i * 6, DIM, "Bold", "mm", k=1 - u)
    if awake:
        s = card(d, (1330, 250, 1780, 340), PANEL, t, 4.8, 40, outline=EXTRA, label="Where do I start?", size=34, tcol=TXT)
        if s > 0: d.polygon([(1440, 340), (1480, 340), (1450, 380)], fill=S.fade(PANEL, prog(t, 4.8, 5.1)))
        ftext(d, (1500, 740), "no variables, no plan", 28, DIM, t, 6.0, "SemiBold", "mm", dx=0)

def s_vector(d, t, dur):
    S.chrome(d, "STEP 3 · RESET", "Two words decide where to start", CAP["11_vector"], t, dur)
    ftext(d, (150, 270), "vector table  (starts at address 0; on many chips that's flash)", 26, DIM, t, 0.3, "Medium")
    rows = [("+0x00", "initial stack pointer", 0x20005000, EXTRA), ("+0x04", "reset handler address", 0x08000101, HIL)]
    for i, (o, n, v, c) in enumerate(rows):
        y = 320 + i * 150
        card(d, (150, y, 850, y + 130), PANEL, t, 0.6 + i * 0.5, 18, outline=c, width=4)
        ptext(d, (220, y + 65), o, 30, DIM, t, 0.8 + i * 0.5, "Bold", mono=True)
        ptext(d, (560, y + 40), n, 30, TXT, t, 0.9 + i * 0.5, "Bold")
        card(d, (400, y + 70, 720, y + 116), c, t, 1.2 + i * 0.5, 12, label=hexw(v), size=28, mono=True)
    card(d, (150, 630, 850, 690), SOFT, t, 1.8, 14, label="... more entries ...", size=26, tcol=DIM, w="Medium")
    # the core
    card(d, (1140, 280, 1780, 780), mix(BG, EXTRA, 0.18), t, 0.5, 26)
    ptext(d, (1460, 320), "the core", 34, EXTRA, t, 0.7)
    for i, (n, c) in enumerate([("SP", EXTRA), ("PC", HIL)]):
        y = 400 + i * 170
        card(d, (1190, y, 1300, y + 90), c, t, 1.0 + i * 0.3, 14, label=n, size=36)
        card(d, (1320, y, 1730, y + 90), PANEL, t, 1.1 + i * 0.3, 14)
        st = 3.0 + i * 2.6
        u = prog(t, st, st + 1.2)
        if t > st:
            src = (400, 390 + i * 150)
            p = lerp2(src, (1360, y + 22), u)
            S.box(d, (p[0], p[1], p[0] + 330, p[1] + 46), c, None, 12, 0, 1.0)
            S.text(d, (p[0] + 165, p[1] + 23), hexw(rows[i][2]), 28, ONA, "Bold", "mm", mono=True)
        if t > st + 1.2:
            ptext(d, (1525, y + 128), ["stack starts at the top of RAM", "jump to the reset handler"][i], 24, DIM, t, st + 1.2, "SemiBold")
    S.pill(d, (500, 760), "EXAMPLE values", 28, HIL, prog(t, 8.0, 8.4))

def s_table(d, t, dur):
    S.chrome(d, "STEP 3 · RESET", "The rest of the table, and one odd bit", CAP["12_table"], t, dur)
    rows = [("+0x00", "initial SP", EXTRA), ("+0x04", "Reset", HIL), ("+0x08", "NMI", BLUE), ("+0x0C", "HardFault", BAD),
            ("...", "", SOFT), ("+0x3C", "SysTick", GOOD), ("+0x40", "interrupt 0", ACC), ("...", "more interrupts", SOFT)]
    for i, (o, n, c) in enumerate(rows):
        st = 0.4 + i * 0.35
        y = 260 + i * 72
        card(d, (150, y, 320, y + 60), c, t, st, 12, label=o, size=26, mono=True, tcol=(DIM if c == SOFT else ONA), dx=-60)
        ftext(d, (345, y + 30), n, 30, TXT if c != SOFT else DIM, t, st + 0.15, "SemiBold", "lm")
    ftext(d, (150, 852), "each entry: an address to jump to", 24, DIM, t, 3.4, "Medium", "lm", dx=0)
    # zoom on the reset entry
    s = card(d, (820, 270, 1780, 380), HIL, t, 3.8, 20, label="0x0800 0101", size=56, mono=True)
    if t > 5.2:
        k = prog(t, 5.2, 5.6)
        lx = 1300 + S.textlen(d, "0x0800 0101", 56, mono=True) / 2
        d.rounded_rectangle([lx - 42, 282, lx + 6, 368], 12, outline=S.fade(LINE, k), width=5)
        garrow(d, (lx - 18, 375), (1456, 470), LINE, t, 5.4, 5, 0.3)
    bitrow(d, 1180, 480, "0001", t, 5.8, cw=72, ch=78, gap=8, step=0.15, labels=["bit 3", "2", "1", "bit 0"])
    if t > 6.8:
        k = prog(t, 6.8, 7.2)
        d.ellipse([1403, 466, 1509, 572], outline=S.fade(BAD, k), width=6)
    ptext(d, (1300, 640), "bit 0 = 1 means: this is Thumb code", 34, BAD, t, 7.4)
    ptext(d, (1300, 700), "Cortex-M only runs Thumb instructions", 28, TXT, t, 8.2, "SemiBold")
    card(d, (1000, 750, 1600, 820), PANEL, t, 9.0, 16, outline=HIL, label="real address: 0x0800 0100", size=30, mono=True, tcol=TXT)

def s_startup(d, t, dur):
    S.chrome(d, "STEP 3 · RESET", "Startup code gets RAM ready", CAP["13_startup"], t, dur)
    card(d, (140, 270, 700, 820), PANEL, t, 0.3, 22, outline=HIL, width=4)
    card(d, (1220, 270, 1780, 820), PANEL, t, 0.5, 22, outline=GOOD, width=4)
    ptext(d, (420, 310), "FLASH", 34, HIL, t, 0.5)
    ptext(d, (1500, 310), "RAM", 34, GOOD, t, 0.7)
    vals = [("count", "3"), ("level", "7"), ("answer", "42")]
    ptext(d, (420, 370), "saved starting values", 26, DIM, t, 0.9, "SemiBold")
    for i, (n, v) in enumerate(vals):
        card(d, (330, 400 + i * 75, 510, 465 + i * 75), HIL, t, 1.0 + i * 0.2, 12, label=v, size=32, mono=True)
    ptext(d, (1500, 370), ".data", 28, HIL, t, 1.2, "Bold", mono=True)
    for i, (n, v) in enumerate(vals):
        y = 400 + i * 75
        S.text(d, (1300, y + 32), n, 28, TXT, "SemiBold", "lm", k=prog(t, 1.3, 1.6))
        copied = t > 3.6 + i * 0.9
        card(d, (1520, y, 1700, y + 65), HIL if copied else SOFT, t, 1.4 + i * 0.1, 12, label=v if copied else "?", size=32,
             mono=True, tcol=ONA if copied else DIM)
        st = 2.6 + i * 0.9
        if st < t < st + 1.0:
            u = ease(t - st)
            p = lerp2((330, y), (1520, y), u)
            p = (p[0], p[1] - 120 * math.sin(math.pi * u))
            S.box(d, (p[0], p[1], p[0] + 180, p[1] + 65), HIL, None, 12, 0, 1.0)
            S.text(d, (p[0] + 90, p[1] + 32), v, 32, ONA, "Bold", "mm", mono=True)
    S.pill(d, (920, 420), "1  copy .data", 30, HIL, prog(t, 2.4, 2.8))
    # .bss
    ptext(d, (1500, 645), ".bss", 28, GOOD, t, 1.5, "Bold", mono=True)
    for i, n in enumerate(["total", "ticks"]):
        y = 672 + i * 74
        S.text(d, (1300, y + 30), n, 28, TXT, "SemiBold", "lm", k=prog(t, 1.6, 1.9))
        z = t > 7.2 + i * 0.5
        card(d, (1520, y, 1700, y + 62), GOOD if z else SOFT, t, 1.7 + i * 0.1, 12, label="0" if z else "?", size=32,
             mono=True, tcol=ONA if z else DIM)
    S.pill(d, (920, 690), "2  zero .bss", 30, GOOD, prog(t, 6.8, 7.2))
    if t > 6.9 and t < 8.4:
        x = lerp(1500, 1720, prog(t, 6.9, 8.2))
        d.rectangle([x, 668, x + 12, 812], fill=GOOD)

def s_main(d, t, dur):
    S.chrome(d, "STEP 3 · RESET", "Clocks on, then call main()", CAP["14_main"], t, dur)
    steps = [("copy .data", HIL), ("zero .bss", GOOD), ("set up clocks (usually)", BLUE), ("call main()", ACC)]
    for i, (n, c) in enumerate(steps):
        st = 0.5 + i * 1.3
        y = 280 + i * 125
        card(d, (150, y, 820, y + 100), PANEL, t, st, 18, outline=c, width=4, dy=-40)
        if t > st + 0.2:
            k = prog(t, st + 0.2, st + 0.5)
            S.circle(d, (210, y + 50), 30, c, k=k)
            if i < 3: check(d, 210, y + 52, 16, ONA, k)
            else: S.text(d, (210, y + 50), "go", 26, ONA, "Bold", "mm", k=k)
            S.text(d, (265, y + 50), n, 36, TXT, "Bold", "lm", k=k)
    S.pill(d, (480, 815), "the exact order varies from chip to chip", 26, DIM, prog(t, 6.0, 6.4))
    garrow(d, (850, 540), (1040, 540), DIM, t, 4.6)
    # main(): a loop that spins forever
    cx, cy = 1400, 520
    s = card(d, (1180, 400, 1620, 640), ACC, t, 5.0, 26, label="main()", size=48, sub="while (1) { ... }", subsize=30)
    if s > 0:
        k = prog(t, 5.6, 6.0)
        R = 220
        a0 = t * 2.2
        pts = [(cx + R * math.cos(a0 + i * 0.05) * 1.25, cy + R * math.sin(a0 + i * 0.05) * 0.95) for i in range(40)]
        S.line(d, pts, HIL, 8, k)
        e = pts[-1]; e2 = pts[-3]
        S.arrow(d, e2, (e[0] + (e[0] - e2[0]) * 2, e[1] + (e[1] - e2[1]) * 2), HIL, 8, k)
    ptext(d, (1400, 800), "main usually never returns", 30, TXT, t, 7.2, "SemiBold")

# ============================================================ STEP 4: run
REGS = [f"r{i}" for i in range(13)] + ["SP", "LR", "PC"]

def s_registers(d, t, dur):
    S.chrome(d, "STEP 4 · RUN", "Meet the registers", CAP["15_registers"], t, dur)
    for i, n in enumerate(REGS):
        c, r = i % 4, i // 4
        x, y = 140 + c * 275, 270 + r * 140
        col = {"SP": EXTRA, "LR": BLUE, "PC": HIL}.get(n, ACC)
        st = 0.4 + i * 0.18
        s = card(d, (x, y, x + 255, y + 120), PANEL, t, st, 16, outline=col, width=4)
        if s <= 0: continue
        k = prog(t, st, st + 0.3)
        S.text(d, (x + 20, y + 32), n, 32, col, "Bold", "lm", k=k)
        if i < 13: v = (i * 2654435761 + int(t * 2.5 + i) * 40503) & 0xFFFFFFFF if t > 4.0 else 0
        elif n == "SP": v = 0x20004FF0
        elif n == "LR": v = 0x08000135
        else: v = 0x08000200 + 2 * (int(max(0, t - 4) * 1.5) % 6)
        S.text(d, (x + 20, y + 82), hexw(v), 26, TXT, "Regular", "lm", mono=True, k=k)
    if t > 3.4:
        k = prog(t, 3.4, 3.8)
        x, y = 140 + 3 * 275, 270 + 3 * 140
        d.rounded_rectangle([x - 10, y - 10, x + 265, y + 130], 22, outline=S.fade(HIL, k), width=6)
    notes = [("32 bits each", TXT), ("r0 to r12: general work", ACC), ("SP: stack pointer", EXTRA),
             ("LR: where to return", BLUE), ("PC: next instruction", HIL)]
    for i, (n, c) in enumerate(notes):
        ftext(d, (1280, 300 + i * 100), n, 34, c, t, 4.4 + i * 0.9, "Bold", "lm")
    S.pill(d, (1500, 800), "EXAMPLE values", 26, HIL, prog(t, 9.4, 9.8))

FLASH_ROWS = [(0x08000200, "4805", "LDR"), (0x08000202, "6801", "LDR"), (0x08000204, "2220", "MOVS"),
              (0x08000206, "4051", "EORS"), (0x08000208, "6001", "STR")]

def flash_list(d, t, a, hl=-1, x=140, y=290):
    card(d, (x, y - 30, x + 600, y + 5 * 90 + 20), PANEL, t, a, 20, outline=HIL, width=4)
    for i, (ad, hx, mn) in enumerate(FLASH_ROWS):
        yy = y + i * 90
        k = prog(t, a + 0.3 + i * 0.15, a + 0.6 + i * 0.15)
        if k <= 0: continue
        if i == hl: S.box(d, (x + 14, yy - 6, x + 586, yy + 70), mix(PANEL, HIL, 0.35), None, 12, 0, k, shadow=False)
        S.text(d, (x + 36, yy + 32), f"{ad >> 16:04X} {ad & 0xFFFF:04X}", 28, DIM, "Regular", "lm", mono=True, k=k)
        S.box(d, (x + 290, yy + 6, x + 420, yy + 60), HIL, None, 10, 0, k, shadow=False)
        S.text(d, (x + 355, yy + 33), hx, 28, ONA, "Bold", "mm", mono=True, k=k)
        S.text(d, (x + 450, yy + 32), mn, 28, TXT, "SemiBold", "lm", k=k)

def s_fetch(d, t, dur):
    S.chrome(d, "STEP 4 · RUN", "Fetch: read at the program counter", CAP["16_fetch"], t, dur)
    step = min(3, int(max(0, t - 2.0) / 1.4))
    flash_list(d, t, 0.3, hl=step if t > 2.0 else -1)
    ptext(d, (440, 790), "flash (EXAMPLE addresses)", 26, DIM, t, 0.8, "SemiBold")
    # bookmark ribbon pointing at the current row
    if t > 2.0:
        yy = 290 + step * 90 + 32
        k = prog(t, 2.0, 2.4)
        d.polygon([(760, yy), (800, yy - 28), (900, yy - 28), (900, yy + 28), (800, yy + 28)], fill=S.fade(HIL, k))
        S.text(d, (855, yy), "PC", 28, ONA, "Bold", "mm", k=k)
    # the core
    card(d, (1060, 280, 1780, 780), mix(BG, BLUE, 0.15), t, 0.6, 26)
    ptext(d, (1420, 320), "the core", 34, BLUE, t, 0.8)
    card(d, (1110, 380, 1220, 460), HIL, t, 1.0, 14, label="PC", size=34)
    card(d, (1240, 380, 1730, 460), PANEL, t, 1.1, 14)
    if t > 1.4:
        ad = FLASH_ROWS[step][0] if t > 2.0 else FLASH_ROWS[0][0]
        S.text(d, (1485, 420), hexw(ad), 32, TXT, "Bold", "mm", mono=True, k=prog(t, 1.4, 1.7))
    ptext(d, (1420, 530), "instruction just fetched", 26, DIM, t, 1.6, "SemiBold")
    card(d, (1250, 570, 1590, 670), PANEL, t, 1.7, 16, outline=LINE, width=3)
    if t > 2.2:
        st = 2.0 + step * 1.4 + 0.3
        u = prog(t, st, st + 0.8)
        src = (430, 296 + step * 90)
        p = lerp2(src, (1355, 590), u)
        S.box(d, (p[0], p[1], p[0] + 130, p[1] + 60), HIL, None, 10, 0, 1.0)
        S.text(d, (p[0] + 65, p[1] + 30), FLASH_ROWS[step][1], 30, ONA, "Bold", "mm", mono=True)
    if t > 7.2: ptext(d, (1420, 730), "hex 4051 = our EORS", 30, HIL, t, 7.2)

def s_decode(d, t, dur):
    S.chrome(d, "STEP 4 · RUN", "Decode: what do the bits mean?", CAP["17_decode"], t, dur)
    bits = "0100000001010001"
    x0 = (W - 16 * 82 + 8) / 2
    bitrow(d, x0, 270, bits, t, 0.3, cols=field_cols(), step=0.06)
    targets = [("ALU: exclusive or", EXTRA, (0, 10), 380), ("read r2", GOOD, (10, 13), 1040), ("read + write r1", BAD, (13, 16), 1520)]
    for j, (lab, c, (a, b), tx) in enumerate(targets):
        st = 2.0 + j * 1.2
        mx = x0 + (a + b) / 2 * 82 - 4
        garrow(d, (mx, 362), (tx, 470), c, t, st, 6, 0.5)
        card(d, (tx - 210, 480, tx + 210, 570), c, t, st + 0.4, 18, label=lab, size=34)
    # switchboard
    sw = [("ALU op", EXTRA, 2.4), ("register A", GOOD, 3.6), ("register B", BAD, 4.8), ("write back", BAD, 5.6)]
    card(d, (300, 620, 1620, 820), PANEL, t, 1.0, 22)
    for i, (n, c, st) in enumerate(sw):
        x = 470 + i * 330
        k = prog(t, 1.2, 1.6)
        on = prog(t, st + 0.6, st + 1.0)
        S.box(d, (x - 70, 650, x + 70, 710), mix(SOFT, c, on), None, 30, 0, k, shadow=False)
        S.circle(d, (lerp(x - 40, x + 40, on), 680), 24, PANEL, outline=LINE, width=3, k=k)
        S.text(d, (x, 760), n, 28, TXT, "SemiBold", "mm", k=k)

def alu(d, xy, t, a, label="ALU"):
    x0, y0, x1, y1 = xy
    if t < a: return
    s = max(0, pop(t, a, a + 0.5)); k = prog(t, a, a + 0.3)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    def P(x, y): return (cx + (x - cx) * s, cy + (y - cy) * s)
    poly = [P(x0, y0), P(x0 + (x1 - x0) * 0.4, y0), P(cx, y0 + 50), P(x1 - (x1 - x0) * 0.4, y0), P(x1, y0),
            P(x1 - 60, y1), P(x0 + 60, y1)]
    d.polygon([(px + 6, py + 9) for px, py in poly], fill=mix(BG, (90, 70, 50), 0.22 * k))
    d.polygon(poly, fill=S.fade(EXTRA, k))
    S.text(d, (cx, cy + 25), label, max(6, int(38 * s)), ONA, "Bold", "mm", k=k)

def s_execute(d, t, dur):
    S.chrome(d, "STEP 4 · RUN", "Execute: do it, then move on", CAP["18_execute"], t, dur)
    card(d, (140, 270, 560, 350), PANEL, t, 0.3, 14, outline=BAD, width=4, label="r1  0x0000 0000", size=30, mono=True, tcol=TXT)
    card(d, (140, 380, 560, 460), PANEL, t, 0.6, 14, outline=GOOD, width=4, label="r2  0x0000 0020", size=30, mono=True, tcol=TXT)
    gline(d, [(560, 310), (660, 310), (720, 330)], BAD, t, 1.2, 6, 0.4)
    gline(d, [(560, 420), (660, 420), (720, 400)], GOOD, t, 1.3, 6, 0.4)
    alu(d, (700, 270, 1060, 470), t, 1.0, "ALU: XOR")
    if 1.8 < t < 3.4:
        dots(d, [(560, 310), (660, 310), (760, 330)], t, BAD, 3, 0.9, 7)
        dots(d, [(560, 420), (660, 420), (760, 400)], t, GOOD, 3, 0.9, 7)
    gline(d, [(880, 470), (880, 510), (1150, 510), (1150, 410)], HIL, t, 3.0, 6, 0.6)
    card(d, (1170, 360, 1610, 450), HIL, t, 3.6, 14, label="r1  0x0000 0020", size=32, mono=True)
    ptext(d, (1390, 485), "result lands back in r1", 28, TXT, t, 3.9, "SemiBold")
    # low 8 bits view
    rows = [("r1", "00000000", BAD), ("r2", "00100000", GOOD), ("result", "00100000", HIL)]
    for i, (n, b, c) in enumerate(rows):
        y = 560 + i * 82
        ftext(d, (300, y + 33), n, 30, c, t, 4.6 + i * 0.6, "Bold", "rm", dx=0)
        bitrow(d, 330, y, b, t, 4.6 + i * 0.6, cw=60, ch=64, gap=6, step=0.04, size=32,
               cols=[(c if ch == "1" else SOFT) for ch in b])
    if t > 6.6:
        k = prog(t, 6.6, 7.0)
        x = 330 + 2 * 66
        d.rounded_rectangle([x - 8, 548, x + 68, 800], 14, outline=S.fade(LINE, k), width=5)
        S.text(d, (x + 30, 826), "bit 5", 24, TXT, "Bold", "mm", k=k)
    ftext(d, (330, 530), "low 8 bits:", 24, DIM, t, 4.4, "Medium", "lm", dx=0)
    # PC moves on
    card(d, (1060, 640, 1180, 720), HIL, t, 7.4, 14, label="PC", size=34)
    if t > 7.6:
        ad = 0x08000206 if t < 8.8 else 0x08000208
        card(d, (1200, 640, 1600, 720), PANEL, t, 7.6, 14, label=hexw(ad), size=32, mono=True, tcol=TXT)
        if t > 8.4: card(d, (1620, 650, 1760, 710), GOOD, t, 8.4, 30, label="+2", size=32)
        ptext(d, (1400, 770), "16-bit instruction = 2 bytes", 26, DIM, t, 9.0, "SemiBold")
    S.pill(d, (1640, 290), "EXAMPLE values", 24, HIL, prog(t, 9.6, 10.0))

def s_pipeline(d, t, dur):
    S.chrome(d, "STEP 4 · RUN", "Over and over, overlapping", CAP["19_pipeline"], t, dur)
    for i, (n, c) in enumerate([("F  fetch", BLUE), ("D  decode", EXTRA), ("E  execute", HIL)]):
        S.pill(d, (1180 + i * 240, 160), n, 26, c, prog(t, 0.3 + i * 0.2, 0.7 + i * 0.2))
    names = ["LDR", "LDR", "MOVS", "EORS", "STR"]
    cw, x0, y0 = 182, 400, 300
    ncol = int(clamp((t - 1.0) / 1.0, 0, 7.99) + 1) if t > 1.0 else 0
    for j in range(7):
        ptext(d, (x0 + j * cw + 80, 270), f"tick {j + 1}", 22, DIM, t, 1.0 + j * 1.0, "Medium")
    if 1.0 < t < 8.5:
        j = min(6, int(t - 1.0))
        S.box(d, (x0 + j * cw - 6, 290, x0 + j * cw + 166, 780), mix(BG, HIL, 0.12), None, 16, 0, 1, shadow=False)
    for i, n in enumerate(names):
        y = y0 + i * 96
        card(d, (140, y, 340, y + 76), PANEL, t, 0.5 + i * 0.2, 14, outline=LINE, width=3, label=n, size=30, mono=True, tcol=TXT)
        for s_, (lab, c) in enumerate([("F", BLUE), ("D", EXTRA), ("E", HIL)]):
            j = i + s_
            if j >= 7: continue
            card(d, (x0 + j * cw, y, x0 + j * cw + 160, y + 76), c, t, 1.0 + j * 1.0, 14, label=lab, size=36)
    S.pill(d, (900, 830), "at the end of the loop, a branch sets the PC back to the top", 26, ACC, prog(t, 8.8, 9.2))

# ============================================================ STEP 5: pins
def s_memmap(d, t, dur):
    S.chrome(d, "STEP 5 · PINS", "To the core, everything is an address", CAP["20_memmap"], t, dur)
    regions = [("Code / flash", 0x00000000, 0.125, HIL), ("SRAM", 0x20000000, 0.125, GOOD), ("Peripherals", 0x40000000, 0.125, ACC),
               ("External RAM", 0x60000000, 0.25, SOFT), ("External devices", 0xA0000000, 0.25, SOFT), ("System", 0xE0000000, 0.125, EXTRA)]
    y = 260; bx0, bx1 = 430, 790
    tot = 600
    geo = {}
    for i, (n, a, f, c) in enumerate(regions):
        h = tot * f
        st = 0.5 + i * 0.4
        card(d, (bx0, y, bx1, y + h - 6), c, t, st, 10, label=n, size=28, tcol=(DIM if c == SOFT else ONA), dx=-50)
        ftext(d, (bx0 - 20, y + 4), hexw(a), 22, DIM, t, st + 0.2, "Regular", "ra", mono=True, dx=0)
        geo[n] = (y, y + h - 6)
        y += h
    ftext(d, (bx0 - 20, 838), "0xFFFF FFFF", 22, DIM, t, 3.0, "Regular", "ra", mono=True, dx=0)
    ptext(d, (610, 236 - 0), "", 1, DIM, t, 9)
    # zoom wedge from Peripherals to a panel
    py0, py1 = geo["Peripherals"]
    k = prog(t, 4.0, 4.6)
    if k > 0:
        S.line(d, [(bx1, py0), (1000, 280)], DIM, 3, k)
        S.line(d, [(bx1, py1), (1000, 800)], DIM, 3, k)
    card(d, (1000, 280, 1790, 800), mix(BG, ACC, 0.12), t, 4.3, 24)
    ptext(d, (1395, 320), "peripherals: control registers", 30, ACC, t, 4.6)
    blocks = [("GPIO port A", GOOD), ("GPIO port B", GOOD), ("timer", BAD), ("serial port", BLUE), ("ADC", EXTRA), ("...", SOFT)]
    for i, (n, c) in enumerate(blocks):
        x, yy = 1040 + (i % 2) * 370, 370 + (i // 2) * 120
        card(d, (x, yy, x + 340, yy + 100), c, t, 5.2 + i * 0.4, 16, label=n, size=32, tcol=(DIM if c == SOFT else ONA))
    ftext(d, (1395, 755), "which ones, and where: depends on the chip", 24, DIM, t, 7.8, "Medium", "mm", dx=0)

def s_register(d, t, dur):
    S.chrome(d, "STEP 5 · PINS", "A register that's really wires", CAP["21_register"], t, dur)
    S.pill(d, (W / 2, 275), "EXAMPLE address  0x4800 0014  =  GPIO output register (low 16 bits shown)", 28, HIL, prog(t, 0.3, 0.7))
    x0 = (W - 16 * 82 + 8) / 2
    set5 = t > 5.0
    bits = "".join("1" if (15 - i == 5 and set5) else "0" for i in range(16))
    cols = [(HIL if b == "1" else SOFT) for b in bits]
    bitrow(d, x0, 380, bits, t, 1.0, cols=cols, step=0.06, labels=[str(15 - i) for i in range(16)])
    # chip edge with pins
    k = prog(t, 2.0, 2.5)
    card(d, (x0 - 40, 600, x0 + 16 * 82 + 32, 660), ACC, t, 2.0, 14, label="", size=10)
    for i in range(16):
        cx = x0 + i * 82 + 37
        bit_on = bits[i] == "1"
        kk = prog(t, 2.4 + i * 0.05, 2.7 + i * 0.05)
        S.line(d, [(cx, 458), (cx, 600)], HIL if bit_on else mix(BG, LINE, 0.35), 8 if bit_on else 4, kk)
        d.rectangle([cx - 9, 660, cx + 9, 690], fill=S.fade(HIL if bit_on else LINE, kk))
    S.text(d, (x0 - 20, 630), "", 10, ONA, k=k)
    ptext(d, (W / 2, 630), "inside the chip: one wire per bit", 26, ONA, t, 2.6, "Bold")
    # pin 5 drives a small LED
    p5 = x0 + 10 * 82 + 37
    ptext(d, (p5, 712), "pin 5", 24, TXT, t, 3.0, "Bold")
    if t > 5.0:
        k5 = prog(t, 5.0, 5.4)
        S.text(d, (p5 + 60, 712), "HIGH", 26, HIL, "Bold", "lm", k=k5)
    led(d, p5 - 170, 760, prog(t, 5.2, 5.6), prog(t, 3.4, 3.8), r=26)
    gline(d, [(p5, 735), (p5, 790), (p5 - 120, 790)], LINE, t, 3.6, 4, 0.4)
    card(d, (220, 730, 760, 800), PANEL, t, 6.4, 16, outline=HIL, label="like a row of light switches", size=28, tcol=TXT)

def s_setup(d, t, dur):
    S.chrome(d, "STEP 5 · PINS", "First, set the pin up", CAP["22_setup"], t, dur)
    steps = [("1", "switch on the port's clock", "unused parts are often off"), ("2", "set pin 5 to output", "pins usually start as inputs"),
             ("3", "write the output bit", "now the pin follows the bit")]
    for i, (n, a, b) in enumerate(steps):
        st = 0.5 + i * 2.2
        x = 140 + i * 560
        s = card(d, (x, 270, x + 520, 560), PANEL, t, st, 24, outline=[BLUE, EXTRA, HIL][i], width=4, dy=40)
        if s <= 0: continue
        k = prog(t, st, st + 0.3)
        c = [BLUE, EXTRA, HIL][i]
        S.circle(d, (x + 60, 320), 32, c, k=k)
        S.text(d, (x + 60, 320), n, 36, ONA, "Bold", "mm", k=k)
        ix, iy = x + 260, 400
        if i == 0:   # a little clock face
            S.circle(d, (ix, iy), 52, PANEL, outline=c, width=6, k=k)
            a1 = t * 2.5
            S.line(d, [(ix, iy), (ix + 36 * math.cos(a1), iy + 36 * math.sin(a1))], c, 6, k)
            S.line(d, [(ix, iy), (ix + 22 * math.cos(a1 / 12), iy + 22 * math.sin(a1 / 12))], c, 6, k)
        elif i == 1:  # pin with an outward arrow
            S.box(d, (ix - 80, iy - 40, ix - 10, iy + 40), ACC, None, 10, 0, k)
            d.rectangle([ix - 10, iy - 8, ix + 20, iy + 8], fill=S.fade(LINE, k))
            u = (t * 0.8) % 1
            S.arrow(d, (ix + 30, iy), (ix + 70 + 30 * u, iy), c, 7, k)
        else:         # a bit flipping 0 -> 1
            on = blink(t, st + 0.6, 0.7)
            S.box(d, (ix - 40, iy - 42, ix + 40, iy + 42), HIL if on else SOFT, None, 12, 0, k)
            S.text(d, (ix, iy), "1" if on else "0", 44, ONA if on else TXT, "Bold", "mm", mono=True, k=k)
        S.text(d, (x + 260, 490), a, 30, TXT, "Bold", "mm", k=k)
        S.text(d, (x + 260, 530), b, 24, DIM, "Medium", "mm", k=k)
        if i < 2: garrow(d, (x + 525, 415), (x + 555, 415), DIM, t, st + 1.0, 5, 0.3)
    code_card(d, 380, 610, ["CLOCK_EN |= PORT_A;   // 1", "MODE5     = OUTPUT;   // 2", "OUT      ^= 1u << 5;  // 3"],
              t, 6.8, size=28, lh=46)
    S.pill(d, (1470, 700), "made-up names: real ones depend on the chip", 24, DIM, prog(t, 7.6, 8.0))

def s_led(d, t, dur):
    S.chrome(d, "STEP 5 · PINS", "From one bit to a glowing LED", CAP["23_led"], t, dur)
    on = prog(t, 4.0, 4.3)
    card(d, (130, 270, 780, 640), PANEL, t, 0.3, 24, outline=ACC, width=5)
    ptext(d, (250, 300), "inside the chip", 24, ACC, t, 0.5, "Bold")
    # supply rail and switch
    k = prog(t, 0.8, 1.2)
    S.line(d, [(420, 350), (720, 350)], BAD, 6, k)
    S.text(d, (570, 325), "supply, e.g. 3.3 V", 24, BAD, "Bold", "mm", k=k)
    S.line(d, [(620, 350), (620, 400)], LINE, 5, k)
    S.circle(d, (620, 400), 8, LINE, k=k, shadow=False)
    S.circle(d, (620, 490), 8, LINE, k=k, shadow=False)
    ang = math.radians(lerp(-35, 0, on))
    S.line(d, [(620, 400), (620 + 90 * math.sin(ang), 400 + 90 * math.cos(ang))], LINE, 6, k)
    S.line(d, [(620, 490), (780, 490)], LINE, 6, k)
    d.rectangle([780, 478, 812, 502], fill=S.fade(LINE, k))
    S.text(d, (796, 530), "pin", 24, TXT, "Bold", "mm", k=k)
    # the bit controls the switch
    card(d, (180, 400, 290, 490), HIL if on > 0.5 else SOFT, t, 1.4, 14, label="1" if on > 0.5 else "0", size=44, mono=True,
         tcol=ONA if on > 0.5 else TXT)
    ptext(d, (235, 520), "bit 5", 24, TXT, t, 1.6, "Bold")
    if t > 2.0:
        S.line(d, [(300, 445), (560, 445)], mix(BG, HIL, 0.6), 4, prog(t, 2.0, 2.4))
        S.arrow(d, (540, 445), (595, 445), HIL, 4, prog(t, 2.0, 2.4))
        S.text(d, (420, 420), "controls", 22, DIM, "Medium", "mm", k=prog(t, 2.0, 2.4))
    ftext(d, (180, 600), "push it: the pin connects to the supply", 24, DIM, t, 4.4, "Medium", "lm", dx=0)
    # outside: wire, resistor, LED, ground
    path = [(812, 490), (930, 490)]
    gline(d, path, LINE, t, 2.4, 6, 0.3)
    if t > 2.6: resistor(d, (930, 490), (1150, 490), prog(t, 2.6, 2.9), amp=18)
    ptext(d, (1040, 440), "resistor", 26, TXT, t, 2.8, "Bold")
    ptext(d, (1040, 560), "limits the current", 22, DIM, t, 3.0, "Medium")
    gline(d, [(1150, 490), (1320, 490), (1320, 560)], LINE, t, 2.9, 6, 0.3)
    led_symbol(d, 1320, 560, 680, on, prog(t, 3.1, 3.4))
    gline(d, [(1320, 680), (1320, 770)], LINE, t, 3.3, 6, 0.3)
    if t > 3.4: ground(d, 1320, 794, prog(t, 3.4, 3.7))
    ptext(d, (1250, 820), "ground", 22, DIM, t, 3.6, "Medium")
    if on > 0.5:
        flow = [(620, 360), (620, 490), (812, 490), (1150, 490), (1320, 490), (1320, 770)]
        dots(d, flow, t, HIL, 9, 0.25, 8)
        S.pill(d, (1040, 620), "a few mA (example)", 24, HIL, prog(t, 4.6, 5.0))
    la, lc = led(d, 1640, 480, on, prog(t, 3.6, 4.0), r=50)
    ptext(d, (1640, 700), "the real thing", 26, DIM, t, 4.0, "SemiBold")

def s_volatile(d, t, dur):
    S.chrome(d, "STEP 5 · PINS", "Why hardware registers say volatile", CAP["24_volatile"], t, dur)
    ptext(d, (500, 280), "a plain variable", 32, BAD, t, 0.3)
    b = code_card(d, 150, 320, ["out = 1;   // LED on?", "out = 0;   // LED off"], t, 0.5, size=32, w=700)
    if t > 2.4:
        k = prog(t, 2.4, 3.0)
        y = 320 + 15 + 51 / 2
        S.line(d, [(170, y + 2), (170 + 650 * k, y + 2)], BAD, 7)
    card(d, (180, 500, 820, 590), BAD, t, 3.2, 18, label="optimiser: 'never read... skip it!'", size=28)
    ftext(d, (500, 640), "only the last write survives", 28, TXT, t, 4.2, "SemiBold", "mm", dx=0)
    led(d, 500, 730, 0.0, prog(t, 4.4, 4.8), r=26)
    # volatile
    ptext(d, (1400, 280), "a hardware register", 32, GOOD, t, 5.4)
    code_card(d, 1000, 320, ["#define OUT (*(volatile uint32_t *)", "             0x48000014)", "OUT = 1;  OUT = 0;"],
              t, 5.6, size=28, w=800, lh=46)
    if t > 6.4:
        k = prog(t, 6.4, 6.9)
        x = 1030 + S.textlen(d, "#define OUT (*(", 28, mono=True)
        d.rounded_rectangle([x - 6, 340, x + S.textlen(d, "volatile", 28, mono=True) + 6, 380], 8, outline=S.fade(GOOD, k), width=4)
    for i, n in enumerate(["every write happens", "every read happens", "kept in order"]):
        st = 7.4 + i * 0.8
        if t > st:
            check(d, 1060, 560 + i * 70, 18, GOOD, prog(t, st, st + 0.3))
            ftext(d, (1100, 560 + i * 70), n, 32, TXT, t, st, "SemiBold", "lm")
    S.pill(d, (1400, 800), "address: EXAMPLE", 24, HIL, prog(t, 9.4, 9.8))

# ============================================================ STEP 6: timing
def square(d, x0, x1, ylo, yhi, period, phase, col, k=1.0, width=5, reveal=1.0):
    pts, x = [], x0
    xend = lerp(x0, x1, clamp(reveal))
    if xend <= x0 + 2: return
    def lvl(xx): return ((xx - x0 + phase) % period) < period / 2
    y = yhi if lvl(x0) else ylo
    pts.append((x0, y))
    step = 2
    xx = x0
    while xx < xend:
        xx += step
        ny = yhi if lvl(xx) else ylo
        if ny != y:
            pts.append((xx, y)); pts.append((xx, ny)); y = ny
    pts.append((xend, y))
    S.line(d, pts, col, width, k)

def s_clock(d, t, dur):
    S.chrome(d, "STEP 6 · TIMING", "A clock sets the pace", CAP["25_clock"], t, dur)
    chain = [("oscillator", "inside the chip, or a crystal", BLUE), ("multiplier", "a PLL, often", EXTRA), ("core clock", "example: 48 MHz", HIL)]
    for i, (a, b, c) in enumerate(chain):
        x = 160 + i * 560
        card(d, (x, 260, x + 480, 390), c, t, 0.4 + i * 1.0, 22, label=a, size=38, sub=b, subsize=24, dx=-60)
        if i < 2: garrow(d, (x + 490, 325), (x + 550, 325), DIM, t, 1.0 + i * 1.0, 5, 0.3)
    k = prog(t, 3.2, 3.6)
    card(d, (140, 440, 1780, 660), PANEL, t, 3.0, 22)
    square(d, 180, 1740, 610, 490, 120, t * 120, HIL, k, 6, reveal=prog(t, 3.4, 5.0))
    if t > 5.0:
        S.line(d, [(180 + 60 * 0, 630), (180 + 120, 630)], LINE, 3, prog(t, 5.0, 5.3))
        S.text(d, (240, 645), "one tick", 22, TXT, "Bold", "mm", k=prog(t, 5.0, 5.3))
    n = int(max(0, t - 5.6) * 48e6) if t > 5.6 else 0
    ftext(d, (160, 720), f"ticks so far: {n:,}", 34, TXT, t, 5.6, "Bold", "lm", mono=True, dx=0)
    S.pill(d, (1400, 720), "1 tick = 1/48,000,000 s, about 21 ns", 28, HIL, prog(t, 7.6, 8.0))
    ftext(d, (1450, 800), "(shown slowed down a lot)", 24, DIM, t, 8.4, "Medium", "mm", dx=0)

def eye(d, cx, cy, k=1.0, look=0.0):
    pts = [(cx + 90 * math.cos(a), cy + 46 * math.sin(a) * (1 if math.sin(a) > 0 else 1)) for a in [i * math.pi / 20 for i in range(41)]]
    d.polygon(pts, fill=S.fade(PANEL, k), outline=S.fade(LINE, k))
    S.circle(d, (cx + look * 20, cy), 30, BLUE, k=k, shadow=False)
    S.circle(d, (cx + look * 20, cy), 13, LINE, k=k, shadow=False)

def s_toofast(d, t, dur):
    S.chrome(d, "STEP 6 · TIMING", "Too fast to see", CAP["26_toofast"], t, dur)
    S.pill(d, (W / 2, 270), "many simple instructions: 1 tick each  =  tens of millions per second", 28, BLUE, prog(t, 0.3, 0.7))
    code_card(d, 140, 330, ["while (1) {", "  OUT ^= 1u << 5;", "  // no delay!", "}"], t, 0.6, size=30)
    card(d, (720, 330, 1300, 560), PANEL, t, 1.4, 22)
    ptext(d, (1010, 360), "pin 5 voltage", 26, DIM, t, 1.6, "SemiBold")
    per = max(3.0, 140 * math.exp(-max(0, t - 2.4) * 0.6))
    square(d, 750, 1270, 520, 400, per, t * 60, HIL, prog(t, 1.8, 2.2), 4, reveal=prog(t, 1.8, 2.6))
    ftext(d, (1010, 600), "flips millions of times a second", 28, TXT, t, 4.0, "Bold", "mm", dx=0)
    eye(d, 1450, 450, prog(t, 4.6, 5.0), math.sin(t * 9) * 0.6 if t > 5.0 else 0)
    ptext(d, (1450, 530), "can't keep up", 24, DIM, t, 5.2, "Bold")
    led(d, 1680, 420, 0.45 if t > 2.4 else blink(t, 1.8, 2.0), prog(t, 1.0, 1.4), r=46)
    ptext(d, (1680, 640), "looks dimly on", 26, TXT, t, 6.0, "Bold")
    ptext(d, (1680, 680), "(about half brightness)", 22, DIM, t, 6.2, "Medium")
    card(d, (420, 720, 1500, 800), BAD, t, 7.6, 20, label="no blinking at all: we need to wait", size=34)

def s_delay(d, t, dur):
    S.chrome(d, "STEP 6 · TIMING", "Two ways to wait", CAP["27_delay"], t, dur)
    for i, (n, c) in enumerate([("busy loop", BAD), ("hardware timer: SysTick", GOOD)]):
        x = 140 + i * 840
        card(d, (x, 260, x + 800, 820), PANEL, t, 0.3 + i * 0.4, 24, outline=c, width=4)
        ptext(d, (x + 400, 300), n, 36, c, t, 0.5 + i * 0.4)
    # busy loop
    code_card(d, 190, 350, ["for (i = 0; i < N; i++) { }"], t, 1.2, size=28)
    cnt = int(800000 - ((t * 310000) % 800000)) if t > 1.8 else 800000
    ftext(d, (540, 520), f"i = {800000 - cnt:,}", 40, TXT, t, 1.8, "Bold", "mm", mono=True, dx=0)
    k = prog(t, 2.4, 2.8)
    if k > 0:
        S.box(d, (220, 600, 860, 650), SOFT, None, 16, 0, k, shadow=False)
        S.box(d, (220, 600, 220 + 640 * (0.96 + 0.04 * math.sin(t * 9)), 650), BAD, None, 16, 0, k, shadow=False)
        S.text(d, (540, 625), "core: 100% busy", 26, ONA, "Bold", "mm", k=k)
        S.text(d, (540, 700), "wastes power, timing depends on", 24, DIM, "Medium", "mm", k=k)
        S.text(d, (540, 734), "the clock and the compiler", 24, DIM, "Medium", "mm", k=k)
    # SysTick
    x0 = 980
    s = card(d, (x0 + 120, 350, x0 + 680, 470), GOOD, t, 3.6, 20)
    if s > 0:
        v = 48000 - int(((t - 4.0) * 30000) % 48000) if t > 4.0 else 48000
        S.text(d, (x0 + 400, 410), f"{v:,}", 56, ONA, "Bold", "mm", mono=True, k=prog(t, 3.6, 3.9))
    ptext(d, (x0 + 400, 500), "counts down, in hardware (shown slowed)", 26, DIM, t, 4.2, "SemiBold")
    if t > 4.0 and ((t - 4.0) * 30000) % 48000 < 9000:
        card(d, (x0 + 560, 320, x0 + 740, 380), HIL, t, 4.0 + 1.6 * int((t - 4.0) / 1.6), 30, label="1 ms!", size=30)
    # sleeping core
    k2 = prog(t, 5.4, 5.8)
    if k2 > 0:
        S.box(d, (x0 + 120, 570, x0 + 420, 690), EXTRA, None, 18, 0, k2)
        S.text(d, (x0 + 270, 630), "core", 32, ONA, "Bold", "mm", k=k2)
        for i in range(3):
            u = ((t - 5.4) * 0.5 + i / 3) % 1
            S.text(d, (x0 + 440 + u * 50, 600 - u * 60), "z", 28 + i * 5, EXTRA, "Bold", "mm", k=k2 * (1 - u))
        S.text(d, (x0 + 610, 610), "sleeps between", 26, TXT, "SemiBold", "mm", k=k2)
        S.text(d, (x0 + 610, 645), "ticks (WFI)", 26, TXT, "SemiBold", "mm", k=k2)
    S.pill(d, (x0 + 400, 760), "example: 48 MHz, 48,000 ticks = 1 ms", 24, HIL, prog(t, 6.6, 7.0))

# ============================================================ recap + end
def s_recap(d, t, dur):
    S.chrome(d, "RECAP", "The whole system", CAP["28_recap"], t, dur)
    row1 = [("C code", ACC), ("compiler", EXTRA), ("numbers", HIL), ("linker", EXTRA), ("flash", HIL)]
    row2 = [("vector table", BLUE), ("startup code", EXTRA), ("main()", ACC), ("fetch, decode, execute", BLUE)]
    cw, gap = 270, 62
    for i, (n, c) in enumerate(row1):
        x = 150 + i * (cw + gap)
        card(d, (x, 270, x + cw, 370), c, t, 0.4 + i * 0.6, 18, label=n, size=32, dy=-30)
        if i < 4: garrow(d, (x + cw + 6, 320), (x + cw + gap - 6, 320), DIM, t, 0.7 + i * 0.6, 5, 0.3)
    gline(d, [(150 + 4 * (cw + gap) + cw / 2, 375), (150 + 4 * (cw + gap) + cw / 2, 410), (230, 410), (230, 440)], DIM, t, 3.4, 5, 0.5)
    S.text(d, (900, 395), "reset", 24, DIM, "Bold", "mm", k=prog(t, 3.6, 3.9))
    xs = [150, 520, 890, 1260]
    ws = [330, 330, 330, 500]
    for i, (n, c) in enumerate(row2):
        card(d, (xs[i], 450, xs[i] + ws[i], 550), c, t, 3.8 + i * 0.6, 18, label=n, size=32, dy=-30)
        if i < 3: garrow(d, (xs[i] + ws[i] + 6, 500), (xs[i + 1] - 6, 500), DIM, t, 4.1 + i * 0.6, 5, 0.3)
    # clock under fetch/decode/execute
    card(d, (1260, 610, 1500, 700), HIL, t, 6.4, 18, label="clock", size=32)
    square(d, 1520, 1760, 690, 620, 40, t * 80, HIL, prog(t, 6.6, 7.0), 4)
    gline(d, [(1380, 610), (1380, 555)], DIM, t, 6.6, 5, 0.3)
    # the write to the pin
    gline(d, [(1510, 555), (1510, 590), (1100, 590), (1100, 640)], DIM, t, 7.2, 5, 0.5)
    card(d, (720, 640, 1180, 740), GOOD, t, 7.6, 18, label="write a GPIO bit", size=32)
    garrow(d, (720, 690), (560, 690), DIM, t, 8.2, 5, 0.4)
    led(d, 480, 650, blink(t, 8.6, 1.0), prog(t, 8.4, 8.8), r=40)

def s_end(d, t, dur):
    S.chrome(d, "", "", CAP["29_end"], t, dur)
    S.pill(d, (W / 2, 300), "NEXT EPISODE", 30, ACC, prog(t, 0.2, 0.6))
    ptext(d, (W / 2, 400), "What really happens when you press a key?", 64, TXT, t, 0.6)
    # a key being pressed
    press = max(0, math.sin(t * 3.0)) ** 4 if t > 1.6 else 0
    s = card(d, (840, 500 + 18 * press, 1080, 700 + 18 * press), PANEL, t, 1.2, 26, outline=LINE, width=5)
    if s > 0:
        k = prog(t, 1.2, 1.5)
        S.box(d, (870, 520 + 18 * press, 1050, 660 + 18 * press), mix(PANEL, BLUE, 0.12), None, 18, 0, k, shadow=False)
        S.text(d, (960, 590 + 18 * press), "A", 80, TXT, "Bold", "mm", k=k)
    S.pill(d, (W / 2, 790), "Subscribe so you don't miss it", 30, BAD, prog(t, 2.4, 2.8))

SCENES = [
    ("01_hook", s_hook, 10), ("02_cover", s_cover, 10),
    ("03_source", s_source, 12), ("04_asm", s_asm, 13), ("05_number", s_number, 13),
    ("06_linker", s_linker, 12), ("07_sections", s_sections, 12), ("08_programmer", s_programmer, 13), ("09_nonvolatile", s_nonvolatile, 12),
    ("10_reset", s_reset, 10), ("11_vector", s_vector, 12), ("12_table", s_table, 12), ("13_startup", s_startup, 11), ("14_main", s_main, 10),
    ("15_registers", s_registers, 12), ("16_fetch", s_fetch, 10), ("17_decode", s_decode, 10), ("18_execute", s_execute, 12), ("19_pipeline", s_pipeline, 12),
    ("20_memmap", s_memmap, 11), ("21_register", s_register, 10), ("22_setup", s_setup, 11), ("23_led", s_led, 10), ("24_volatile", s_volatile, 12),
    ("25_clock", s_clock, 11), ("26_toofast", s_toofast, 11), ("27_delay", s_delay, 11),
    ("28_recap", s_recap, 12), ("29_end", s_end, 7),
]

NARRATION = {
 "01_hook": "Ever wondered how a few lines of text on your screen make a real light blink on a tiny chip? No magic: just numbers, a clock, and one special address. So let's build it up, one piece at a time.",
 "02_cover": "First, we turn your code into numbers, and store them inside the chip. Then we wake it up, watch it run, touch the outside world, and keep time. Our example is a generic thirty two bit Arm Cortex M microcontroller.",
 "03_source": "Step one: compile. Here's a tiny program that blinks a light. Let's zoom in on one line. It says: flip bit five of an output register. But your chip can't read C at all. So a compiler translates it into the chip's own language: machine instructions.",
 "04_asm": "That single line turns into about five small steps. Load the register's address. Read its current value. Make a number with only bit five set. Flip that bit, with an exclusive or. And write it back. The exact instructions depend on your compiler, so treat these as an example.",
 "05_number": "Here's the fun part. Each instruction is just a number. Exclusive or, r one with r two, is hex, four zero five one. That's sixteen ones and zeros. Some bits say what kind of operation it is, and the rest pick the registers. On Cortex M, most instructions are sixteen or thirty two bits long.",
 "06_linker": "Step two: get it into the chip. Real programs are split across several files, each compiled separately. The linker glues them together, and decides exactly where everything lives. It follows a map of the chip's memory, called a linker script, so it knows where flash and R A M begin.",
 "07_sections": "Here's how it sorts things. Code and constants go in flash. A variable with a starting value, like count equals three, lives in R A M, but its starting value is saved in flash too. Variables that start at zero just need space in R A M. And the stack grows down from the top.",
 "08_programmer": "Now we copy those numbers into the chip. A small debug probe connects to it, often through just two signal wires, called serial wire debug, plus ground. It erases flash, writes your program in, and reads it back to check. Some chips can also load code through a built-in bootloader.",
 "09_nonvolatile": "So why flash? Pull the power, and R A M forgets everything. Flash keeps your program with no power at all, for years. Think of R A M as a whiteboard that's wiped whenever the lights go out. Flash is more like a notebook, where you rewrite a whole page at a time.",
 "10_reset": "Step three: wake up. When power arrives, or you press reset, the chip holds its core in reset until the supply is steady. Then it lets go. At that instant, the core knows nothing about your program. No variables. No plan. So where does it even start?",
 "11_vector": "On Cortex M, the answer is built in. The core reads the first word of the vector table into the stack pointer. Then it reads the second word, the address of the reset handler, into the program counter. The table starts at address zero, and on many chips, that's flash.",
 "12_table": "The rest of the table is more addresses: where to jump when a fault happens, or an interrupt fires. And here's a quirky detail. Each address has its lowest bit set to one. That's not a typo. It marks Thumb code, the only kind a Cortex M runs.",
 "13_startup": "The reset handler is startup code, and it runs before main. First, it copies your variables' starting values from flash into R A M. That's how count becomes three. Then it fills the zero section, called B S S, with zeros. Now every variable holds what your code promised.",
 "14_main": "Startup code usually sets up the clocks too, so the chip runs at the speed you want. The exact order varies from chip to chip. Finally, it calls main. And in most embedded programs, main never returns. It ends in a loop that runs until the power goes off.",
 "15_registers": "Step four: run. Inside the core is a small set of super fast slots, called registers. Each holds one thirty two bit number. Thirteen are for general work. Then there's the stack pointer, the link register, which remembers where to return, and the star of the show: the program counter.",
 "16_fetch": "The program counter is like a bookmark. It holds the address of the next instruction. Fetch means the core reads the instruction at that address, out of flash. Now it points here. Out comes hex, four zero five one.",
 "17_decode": "Decode means the core looks at those bits, and works out what they mean. These bits say: exclusive or. These pick register two, and these pick register one. Decoding flips the core's internal switches, so the right registers connect to the arithmetic unit.",
 "18_execute": "Execute means it actually happens. The values in r one and r two flow into the arithmetic logic unit, and the result lands back in r one. Look: bit five has flipped. Then the program counter moves on two bytes, because this instruction was sixteen bits long.",
 "19_pipeline": "Fetch, decode, execute, again and again. To go faster, many Cortex M cores overlap the steps, like a little assembly line. While one instruction executes, the next is decoded, and the one after is fetched. At the end of our loop, a branch jumps back to the top.",
 "20_memmap": "Step five: touch the pins. To the core, everything is an address. Thirty two bits can count to about four billion, and Arm splits that space into regions. Code at the bottom. R A M from hex, two zero zero zero, zero zero zero zero. And above that, peripherals.",
 "21_register": "Peripheral addresses aren't memory at all. Take this example: hex, four eight zero zero, zero zero one four. On our example chip, it's a G P I O output register. Each bit is wired to one pin, like a row of light switches. Set bit five to one, and pin five goes high.",
 "22_setup": "There's a catch. On most chips, you can't just write the bit straight away. First, you switch on the clock for that G P I O port, because unused parts are often kept off to save power. Then you set pin five to output, since pins usually start as inputs.",
 "23_led": "Now follow the bit. Inside the chip, it controls a tiny switch that connects the pin to the supply, say three point three volts. Current flows out of the pin, through a resistor that limits it to a few milliamps, through the L E D, and down to ground. Light!",
 "24_volatile": "One more thing. Compilers love to tidy up, and may skip a write if nothing seems to read it. For a pin, that's a disaster. So hardware registers are marked volatile. It tells the compiler: every read and write here matters. Don't skip any, and keep them in order.",
 "25_clock": "Step six: keep time. Everything in the core moves in step with a clock, a square wave ticking up and down. It comes from an oscillator inside the chip, or an external crystal, often multiplied up. Say it runs at forty eight megahertz. That's forty eight million ticks a second.",
 "26_toofast": "On Cortex M, many simple instructions take just one tick. So our chip runs tens of millions of instructions a second. Without a delay, our loop flips the pin millions of times a second. Your eyes can't keep up, so the L E D just looks dimly on. No blinking at all.",
 "27_delay": "So we have to wait. The simple way is a busy loop: count to a big number, doing nothing useful. The better way is a hardware timer. Cortex M cores usually include one called SysTick. At forty eight megahertz, forty eight thousand ticks is one millisecond. In between, the core can sleep.",
 "28_recap": "Let's recap. A compiler turns your C into numbers. The linker gives them addresses, and a probe writes them into flash. At reset, the core reads the vector table, startup code prepares R A M, and main begins. Fetch, decode, execute, in time with the clock. And one write lights an L E D.",
 "29_end": "Now you know the whole story. Next episode: what really happens when you press a key? Subscribe so you don't miss it.",
}
OUTPUT = "how_a_microcontroller_runs_code_ep2_narrated.mp4"

def render(name, fn, dur): S.render_to("ep2", name, fn, dur)

if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    print(S.preview("ep2", SCENES))
