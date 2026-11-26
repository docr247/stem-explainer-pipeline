import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
BLUE = (90, 150, 255)

# Task colours, used the same way throughout the episode
BRAKE, DISP, LOG = RED, CYAN, PURPLE

# ---------------- helpers ----------------
def car(d, x, y, w=520, k=1.0, col=DIM):
    """A generic side-view car outline (no brand); (x, y) is the bottom-left of the body."""
    h = w * 0.22
    d.rounded_rectangle([x, y - h, x + w, y], 24, outline=fade(col, k), width=5, fill=fade(PANEL, k))
    d.polygon([(x + w * 0.22, y - h), (x + w * 0.36, y - h * 1.9), (x + w * 0.70, y - h * 1.9), (x + w * 0.84, y - h)],
              outline=fade(col, k), fill=fade(PANEL, k))
    d.line([(x + w * 0.53, y - h * 1.88), (x + w * 0.53, y - h)], fill=fade(col, k), width=4)
    for cx in (x + w * 0.22, x + w * 0.78):
        r = w * 0.1
        d.ellipse([cx - r, y - r, cx + r, y + r], fill=fade((8, 12, 24), k), outline=fade(col, k), width=6)

def ecu(d, x, y, k=1.0, col=CYAN, s=1.0):
    d.rounded_rectangle([x - 26 * s, y - 18 * s, x + 26 * s, y + 18 * s], 6, fill=fade(mix(BG, col, 0.35), k), outline=fade(col, k), width=3)

def task_box(d, x, y, w, h, name, col, state=None, k=1.0, hot=False):
    box(d, (x, y, x + w, y + h), mix(BG, col, 0.25) if hot else PANEL, col, 14, 4 if hot else 2, k)
    text(d, (x + 24, y + 40), name, 36, col, "Bold", "lm", k=k)
    if state:
        sc = {"RUNNING": GREEN, "READY": AMBER, "BLOCKED": DIM}[state]
        text(d, (x + w - 24, y + 40), state, 26, sc, "Bold", "rm", mono=True, k=k)

def lane_chart(d, lanes, spans, x0, x1, y0, gap, p, k=1.0, labels=True):
    """lanes: [(name, col)], spans: [(lane, a, b)] in 0..1; drawn up to progress p."""
    for i, (n, c) in enumerate(lanes):
        y = y0 + i * gap
        if labels: text(d, (x0 - 24, y), n, 30, c, "Bold", "rm", k=k)
        d.line([x0, y, x1, y], fill=fade(LINE, k), width=2)
    for lane, a, b in spans:
        if p <= a: continue
        e = min(p, b)
        c = lanes[lane][1]
        y = y0 + lane * gap
        d.rectangle([x0 + (x1 - x0) * a, y - 24, x0 + (x1 - x0) * e, y + 24], fill=c)

def code(d, lines, x, y, t, k=1.0, size=32, gap=50, start=0.4, step=0.3, hl=None):
    w = max(len(s) for s in lines) * size * 0.61 + 80
    box(d, (x, y, x + w, y + 40 + len(lines) * gap), (6, 10, 20), LINE, 14, 3, k)
    for i, ln in enumerate(lines):
        kk = prog(t, start + i * step, start + 0.4 + i * step)
        col = (hl or {}).get(i, TXT)
        text(d, (x + 40, y + 22 + i * gap), ln, size, col, mono=True, k=kk)

def lock(d, cx, cy, s, col, k=1.0, open_=False):
    d.arc([cx - s * 0.6, cy - s * 1.3 - (s * 0.4 if open_ else 0), cx + s * 0.6, cy - s * 0.1 - (s * 0.4 if open_ else 0)],
          180, 360, fill=fade(col, k), width=int(s * 0.22))
    d.rounded_rectangle([cx - s, cy - s * 0.6, cx + s, cy + s * 0.9], int(s * 0.2), fill=fade(col, k))
    d.ellipse([cx - s * 0.18, cy - s * 0.05, cx + s * 0.18, cy + s * 0.31], fill=fade(BG, k))

# ---------------- chapter 0 ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "Your car is full of small computers. One of them must react to a locking wheel within milliseconds, every time, even when it's busy.", t, dur)
    k = prog(t, 0.2, 0.7)
    car(d, 600, 640, 720, k)
    pts = [(780, 520), (960, 480), (1150, 520), (1240, 600), (700, 600), (860, 610), (1020, 560), (1100, 610)]
    for i, (x, y) in enumerate(pts):
        ecu(d, x, y, prog(t, 0.8 + i * 0.2, 1.1 + i * 0.2), col=CYAN, s=0.7)
    if t > 3.0:
        kk = prog(t, 3.0, 3.5)
        cx = 600 + 720 * 0.78
        d.ellipse([cx - 90, 640 - 90, cx + 90, 640 + 90], outline=fade(RED, kk), width=6)
        text(d, (cx + 120, 700), "wheel locking!", 40, RED, "Bold", "lm", k=kk)
    if t > 4.4:
        text(d, (W // 2, 300), "what if its computer is busy?", 48, AMBER, "Bold", "mm", k=prog(t, 4.4, 4.9))

def s_cover(d, t, dur):
    chrome(d, "", "Here's what we'll cover", "We'll follow one event through a car's computer, and see how a real-time operating system keeps it on time.", t, dur)
    items = [("1", "The superloop", "one big loop, and its problem", AMBER), ("2", "Tasks", "split the work up", CYAN),
             ("3", "The scheduler", "priorities and preemption", GREEN), ("4", "Follow the event", "sensor to brake valve", RED),
             ("5", "Sharing safely", "locks and a famous bug", PURPLE), ("6", "Deadlines", "hard, soft, and watchdogs", BLUE)]
    for i, (n, a, b, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.45, 0.8 + i * 0.45)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 270 + row * 170
        box(d, (x, y, x + 720, y + 130), PANEL, c, 16, 3, kk)
        d.ellipse([x + 26, y + 30, x + 96, y + 100], fill=fade(c, kk))
        text(d, (x + 61, y + 65), n, 38, BG, "Bold", "mm", k=kk)
        text(d, (x + 130, y + 46), a, 40, TXT, "Bold", "lm", k=kk)
        text(d, (x + 130, y + 94), b, 28, DIM, "Medium", "lm", k=kk)

# ---------------- chapter 1: the superloop ----------------
def s_superloop(d, t, dur):
    chrome(d, "STEP 1 · THE SUPERLOOP", "One big loop", "Simple firmware is one endless loop: read the sensors, control the brakes, update the display, write the log, repeat.", t, dur)
    k = prog(t, 0.2, 0.6)
    code(d, ["while (1) {", "    read_sensors();", "    control_brakes();", "    update_display();", "    write_log();", "}"],
         160, 280, t, k, hl={2: BRAKE, 3: DISP, 4: LOG})
    cx, cy, r = 1400, 520, 200
    steps = [("sensors", AMBER), ("brakes", BRAKE), ("display", DISP), ("log", LOG)]
    for i, (n, c) in enumerate(steps):
        a = -math.pi / 2 + i * math.pi / 2
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        box(d, (x - 90, y - 34, x + 90, y + 34), PANEL, c, 30, 3, prog(t, 2.2 + i * 0.3, 2.6 + i * 0.3))
        text(d, (x, y), n, 30, c, "Bold", "mm", k=prog(t, 2.2 + i * 0.3, 2.6 + i * 0.3))
    if t > 3.6:
        ang = -math.pi / 2 + (t - 3.6) * 2.2
        dot = (cx + (r - 90) * math.cos(ang), cy + (r - 90) * math.sin(ang))
        d.ellipse([dot[0] - 14, dot[1] - 14, dot[0] + 14, dot[1] + 14], fill=TXT)

def s_problem(d, t, dur):
    chrome(d, "STEP 1 · THE SUPERLOOP", "What if the wheel locks... now?", "If the wheel starts locking just after the brake step, the loop must finish the slow display and log steps before it can react.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 200, 1720, 470
    seg = [("sensors", AMBER, 0.08), ("brakes", BRAKE, 0.12), ("display", DISP, 0.30), ("log  (slow flash write)", LOG, 0.42), ("sensors", AMBER, 0.08)]
    x = x0
    p = prog(t, 0.4, 3.0)
    tot = sum(s[2] for s in seg)
    for n, c, w in seg:
        ww = (x1 - x0) * w / tot
        if (x - x0) / (x1 - x0) > p: break
        e = min(x + ww, x0 + (x1 - x0) * p)
        d.rectangle([x, y - 40, e, y + 40], fill=mix(BG, c, 0.75))
        if e - x > 120: text(d, ((x + e) / 2, y), n, 26, BG, "Bold", "mm")
        x += ww
    ev = x0 + (x1 - x0) * 0.21
    if t > 3.2:
        kk = prog(t, 3.2, 3.6)
        arrow(d, (ev, 300), (ev, y - 50), RED, 6, kk)
        text(d, (ev, 270), "wheel starts to lock", 32, RED, "Bold", "mm", k=kk)
    if t > 4.2:
        kk = prog(t, 4.2, 4.7)
        xr = x0 + (x1 - x0) * (1 - 0.08 / tot) + 8
        d.line([ev, y + 90, xr, y + 90], fill=fade(AMBER, kk), width=4)
        arrow(d, (ev + 60, y + 90), (ev, y + 90), AMBER, 4, kk); arrow(d, (xr - 60, y + 90), (xr, y + 90), AMBER, 4, kk)
        text(d, ((ev + xr) / 2, y + 140), "waiting...", 36, AMBER, "Bold", "mm", k=kk)

def s_worst(d, t, dur):
    chrome(d, "STEP 1 · THE SUPERLOOP", "The worst case keeps growing", "The worst-case reaction time is the whole loop. Add one more feature, and every other job gets slower to respond.", t, dur)
    k = prog(t, 0.2, 0.6)
    feats = [("sensors", AMBER, 80), ("brakes", BRAKE, 110), ("display", DISP, 260), ("log", LOG, 330), ("diagnostics", GREEN, 260), ("network", BLUE, 220)]
    x0, y = 200, 420
    n = 4 + int(clamp((t - 2.0) / 2.0) * 2.999) if t > 2.0 else 4
    x = x0
    for i, (nm, c, w) in enumerate(feats[:n]):
        kk = prog(t, 0.4 + i * 0.25, 0.8 + i * 0.25) if i < 4 else prog(t, 2.0 + (i - 4) * 1.0, 2.5 + (i - 4) * 1.0)
        d.rectangle([x, y - 40, x + w * kk, y + 40], fill=mix(BG, c, 0.75 * kk))
        if kk > 0.8 and w > 100: text(d, (x + w / 2, y), nm, 26, BG, "Bold", "mm")
        x += w * kk
    d.line([x0, y + 90, x, y + 90], fill=RED, width=5)
    text(d, (x0, y + 140), "worst-case reaction time", 32, RED, "Bold", "lm", k=k)
    text(d, (W // 2, 720), "everything waits for everything", 36, DIM, "Medium", "mm", k=prog(t, 4.6, 5.1))

# ---------------- chapter 2: tasks ----------------
def s_tasks(d, t, dur):
    chrome(d, "STEP 2 · TASKS", "Split the work into tasks", "An RTOS lets you split the work into tasks. Each one is its own little loop, with its own stack, as if it had the CPU to itself.", t, dur)
    k = prog(t, 0.2, 0.6)
    tasks = [("brake_task", BRAKE, ["while (1) {", "  wait_for_wheel_event();", "  set_valves();", "}"]),
             ("display_task", DISP, ["while (1) {", "  draw_screen();", "  sleep(50 ms);", "}"]),
             ("log_task", LOG, ["while (1) {", "  wait_for_log_data();", "  write_flash();", "}"])]
    for i, (n, c, lines) in enumerate(tasks):
        kk = prog(t, 0.4 + i * 0.8, 0.9 + i * 0.8)
        x = 130 + i * 570
        box(d, (x, 280, x + 530, 680), PANEL, c, 16, 3, kk)
        text(d, (x + 30, 320), n, 34, c, "Bold", "lm", mono=True, k=kk)
        for j, ln in enumerate(lines):
            text(d, (x + 30, 390 + j * 52), ln, 26, TXT, mono=True, k=kk)
        box(d, (x + 30, 610, x + 500, 660), (8, 12, 24), LINE, 8, 2, kk)
        text(d, (x + 265, 635), "own stack", 24, DIM, "Medium", "mm", k=kk)
    text(d, (W // 2, 740), "(example task names and timings)", 26, DIM, "Medium", "mm", k=prog(t, 3.2, 3.7))

def s_states(d, t, dur):
    chrome(d, "STEP 2 · TASKS", "Running, ready, or blocked", "Only one task runs at a time on a single core. The others are ready and waiting for a turn, or blocked, waiting for something to happen.", t, dur)
    k = prog(t, 0.2, 0.6)
    pos = {"RUNNING": (W // 2, 340), "READY": (520, 640), "BLOCKED": (1400, 640)}
    cols = {"RUNNING": GREEN, "READY": AMBER, "BLOCKED": DIM}
    for i, (s, (x, y)) in enumerate(pos.items()):
        kk = prog(t, 0.4 + i * 0.5, 0.9 + i * 0.5)
        box(d, (x - 190, y - 60, x + 190, y + 60), mix(BG, cols[s], 0.2), cols[s], 30, 4, kk)
        text(d, (x, y), s, 40, cols[s], "Bold", "mm", mono=True, k=kk)
    ka = prog(t, 2.2, 2.7)
    arrow(d, (600, 575), (800, 405), AMBER, 4, ka); text(d, (590, 470), "scheduler picks it", 26, AMBER, "Bold", "rm", k=ka)
    arrow(d, (1130, 405), (1330, 575), DIM, 4, ka); text(d, (1290, 470), "waits for an event", 26, DIM, "Bold", "lm", k=ka)
    kb = prog(t, 3.2, 3.7)
    arrow(d, (1200, 650), (720, 650), AMBER, 4, kb); text(d, (960, 690), "event arrives", 26, AMBER, "Bold", "mm", k=kb)

def s_blocked(d, t, dur):
    chrome(d, "STEP 2 · TASKS", "Blocked tasks cost nothing", "A blocked task uses no CPU time at all. The brake task can sit blocked for minutes, then wake the instant its event arrives.", t, dur)
    k = prog(t, 0.2, 0.6)
    task_box(d, 200, 300, 620, 80, "brake_task", BRAKE, "BLOCKED" if t < 4.2 else "RUNNING", k, hot=t > 4.2)
    task_box(d, 200, 420, 620, 80, "display_task", DISP, "RUNNING" if t < 4.2 else "READY", k, hot=t < 4.2)
    task_box(d, 200, 540, 620, 80, "log_task", LOG, "BLOCKED", k)
    x0, x1, y = 960, 1720, 460
    text(d, (x0, 300), "CPU time used", 30, TXT, "Bold", "lm", k=k)
    for i, (n, c, v) in enumerate([("brake", BRAKE, 0.02 if t < 4.2 else 0.3), ("display", DISP, 0.6), ("log", LOG, 0.05), ("idle", DIM, 0.33)]):
        y2 = 370 + i * 80
        text(d, (x0, y2), n, 28, c, "Bold", "lm", k=k)
        d.rectangle([x0 + 150, y2 - 18, x0 + 150 + (x1 - x0 - 150) * v * k, y2 + 18], fill=c)
    if t > 4.2:
        text(d, (510, 690), "event! brake task wakes", 34, RED, "Bold", "mm", k=prog(t, 4.2, 4.7))

# ---------------- chapter 3: the scheduler ----------------
def s_priority(d, t, dur):
    chrome(d, "STEP 3 · THE SCHEDULER", "Every task gets a priority", "You give each task a priority. The rule is simple: the highest-priority task that's ready always gets the CPU.", t, dur)
    k = prog(t, 0.2, 0.6)
    rows = [("brake_task", BRAKE, "HIGH", 3), ("display_task", DISP, "MEDIUM", 2), ("log_task", LOG, "LOW", 1)]
    for i, (n, c, p, lv) in enumerate(rows):
        kk = prog(t, 0.4 + i * 0.5, 0.9 + i * 0.5)
        y = 300 + i * 150
        box(d, (300, y, 1620, y + 110), PANEL, c, 14, 3, kk)
        text(d, (340, y + 55), n, 38, c, "Bold", "lm", mono=True, k=kk)
        for j in range(3):
            d.rectangle([1100 + j * 70, y + 70 - j * 18 - 14, 1150 + j * 70, y + 85], fill=fade(c if j < lv else LINE, kk))
        text(d, (1580, y + 55), p, 32, c, "Bold", "rm", k=kk)
    text(d, (W // 2, 790), "highest ready task runs. always.", 40, AMBER, "Bold", "mm", k=prog(t, 2.8, 3.3))

def s_preempt(d, t, dur):
    chrome(d, "STEP 3 · THE SCHEDULER", "Preemption: no waiting your turn", "When a higher-priority task becomes ready, the scheduler pauses whatever is running, right away, and switches to it.", t, dur)
    k = prog(t, 0.2, 0.6)
    lanes = [("brake", BRAKE), ("display", DISP), ("log", LOG)]
    spans = [(2, 0.0, 0.25), (1, 0.25, 0.45), (0, 0.45, 0.62), (1, 0.62, 0.80), (2, 0.80, 1.0)]
    lane_chart(d, lanes, spans, 400, 1700, 340, 150, prog(t, 0.4, 5.0), k)
    if t > 2.6:
        xe = 400 + 1300 * 0.45
        kk = prog(t, 2.6, 3.0)
        d.line([xe, 280, xe, 700], fill=fade(RED, kk), width=3)
        text(d, (xe, 255), "event: brake task ready", 30, RED, "Bold", "mm", k=kk)
        text(d, (xe + 20, 740), "display paused instantly", 28, DIM, "Medium", "lm", k=prog(t, 3.2, 3.7))

def s_tick(d, t, dur):
    chrome(d, "STEP 3 · THE SCHEDULER", "The tick: the RTOS heartbeat", "A hardware timer interrupts at a steady rate, often every millisecond. Each tick, the scheduler checks timeouts and sleeping tasks.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 200, 1720, 420
    d.line([x0, y, x1, y], fill=fade(LINE, k), width=3)
    n = int(clamp((t - 0.6) / 4.0) * 10)
    for i in range(10):
        x = x0 + (i + 0.5) * (x1 - x0) / 10
        on = i < n
        d.line([x, y - 70, x, y], fill=fade(AMBER if on else LINE, k), width=6)
        if on: d.ellipse([x - 10, y - 80, x + 10, y - 60], fill=AMBER)
        text(d, (x, y + 40), f"{i} ms", 24, DIM, "Medium", "mm", k=k)
    kk = prog(t, 2.6, 3.1)
    box(d, (560, 560, 1360, 760), PANEL, LINE, 14, 2, kk)
    for j, s in enumerate(["any timeouts expired?", "any sleeping task due to wake?", "does a higher priority need the CPU?"]):
        text(d, (600, 600 + j * 52), "• " + s, 30, TXT, "Medium", "lm", k=prog(t, 2.8 + j * 0.4, 3.2 + j * 0.4))
    text(d, (x1, y - 110), "tick rate: example 1 kHz", 26, DIM, "Medium", "rm", k=kk)

def s_context(d, t, dur):
    chrome(d, "STEP 3 · THE SCHEDULER", "The context switch", "To switch tasks, the RTOS saves the running task's registers onto its stack, then restores the next task's registers. Like the interrupts episode.", t, dur)
    k = prog(t, 0.2, 0.6)
    regs = ["R0", "R1", "R2", "R3", "R12", "LR", "PC", "xPSR"]
    p1 = prog(t, 0.6, 2.4)
    text(d, (420, 290), "display_task stack", 30, DISP, "Bold", "mm", mono=True, k=k)
    text(d, (1500, 290), "brake_task stack", 30, BRAKE, "Bold", "mm", mono=True, k=k)
    for i, r in enumerate(regs):
        y = 720 - i * 50
        if i < int(p1 * 8 + 0.999) and p1 > 0:
            box(d, (310, y, 530, y + 42), mix(BG, DISP, 0.2), DISP, 8, 2, 1)
            text(d, (420, y + 21), r, 24, DISP, "Bold", "mm", mono=True)
        p2 = prog(t, 2.8, 4.4)
        if i >= int(p2 * 8):
            box(d, (1390, y, 1610, y + 42), mix(BG, BRAKE, 0.2), BRAKE, 8, 2, k)
            text(d, (1500, y + 21), r, 24, BRAKE, "Bold", "mm", mono=True, k=k)
    chip(d, 790, 420, 340, 200, "CPU", "registers", GREEN, k)
    if 0.6 < t < 2.6: arrow(d, (780, 520), (560, 520), DISP, 5, k)
    if 2.8 < t < 4.6: arrow(d, (1380, 520), (1140, 520), BRAKE, 5, k)
    if t > 4.6: text(d, (960, 680), "now running: brake_task", 32, BRAKE, "Bold", "mm", k=prog(t, 4.6, 5.0))

# ---------------- chapter 4: follow the event ----------------
def s_isr(d, t, dur):
    chrome(d, "STEP 4 · FOLLOW THE EVENT", "1. The sensor interrupts", "A wheel-speed sensor shows the wheel slowing too fast. An interrupt fires, and a tiny handler sends a signal to the brake task.", t, dur)
    k = prog(t, 0.2, 0.6)
    cx, cy = 320, 520
    d.ellipse([cx - 140, cy - 140, cx + 140, cy + 140], outline=fade(DIM, k), width=10)
    for i in range(12):
        a = i * math.pi / 6 + t * (2.0 if t < 2 else 0.6)
        d.rectangle([cx + 110 * math.cos(a) - 8, cy + 110 * math.sin(a) - 8, cx + 110 * math.cos(a) + 8, cy + 110 * math.sin(a) + 8], fill=fade(AMBER, k))
    text(d, (cx, cy + 190), "toothed ring + sensor", 26, DIM, "Medium", "mm", k=k)
    d.rectangle([cx + 150, cy - 30, cx + 210, cy + 30], fill=fade(PANEL, k), outline=fade(AMBER, k), width=3)
    hot = t > 2.2
    d.line([cx + 210, cy, 760, cy], fill=RED if hot else LINE, width=6)
    if hot: text(d, (600, cy - 40), "IRQ", 30, RED, "Bold", "mm", mono=True)
    code(d, ["void WHEEL_IRQHandler(void) {", "    clear_flag();", "    give_semaphore(&wheel_evt);", "}"], 780, 400, t, prog(t, 2.4, 2.9),
         size=30, gap=48, start=2.6, step=0.3, hl={2: RED})
    text(d, (1240, 680), "short: no braking logic in here", 28, DIM, "Medium", "mm", k=prog(t, 4.2, 4.7))

def s_wake(d, t, dur):
    chrome(d, "STEP 4 · FOLLOW THE EVENT", "2. The brake task wakes up", "That signal moves the brake task from blocked to ready. It's the highest priority, so the scheduler switches to it as soon as the handler finishes.", t, dur)
    k = prog(t, 0.2, 0.6)
    state = "BLOCKED" if t < 1.8 else ("READY" if t < 3.2 else "RUNNING")
    task_box(d, 260, 300, 640, 80, "brake_task", BRAKE, state, k, hot=t > 3.2)
    task_box(d, 260, 430, 640, 80, "display_task", DISP, "RUNNING" if t < 3.2 else "READY", k, hot=t < 3.2)
    task_box(d, 260, 560, 640, 80, "log_task", LOG, "BLOCKED", k)
    box(d, (1100, 330, 1640, 610), PANEL, RED, 16, 3, prog(t, 1.0, 1.5))
    text(d, (1370, 380), "wheel_evt", 34, RED, "Bold", "mm", mono=True, k=prog(t, 1.0, 1.5))
    text(d, (1370, 430), "(a semaphore)", 26, DIM, "Medium", "mm", k=prog(t, 1.0, 1.5))
    lit = t > 1.4
    d.ellipse([1340, 490, 1400, 550], fill=RED if lit else LINE)
    if t > 1.8: arrow(d, (1090, 470), (920, 340), RED, 5, prog(t, 1.8, 2.2))

def s_act(d, t, dur):
    chrome(d, "STEP 4 · FOLLOW THE EVENT", "3. Act, then block again", "The brake task works out a new valve setting, commands the brake valves, and blocks again. Then the display picks up where it left off.", t, dur)
    k = prog(t, 0.2, 0.6)
    steps = [("read wheel speeds", AMBER), ("compute slip", BRAKE), ("set valve: ease pressure", RED), ("block: wait again", DIM)]
    for i, (s, c) in enumerate(steps):
        kk = prog(t, 0.4 + i * 0.7, 0.8 + i * 0.7)
        y = 290 + i * 120
        box(d, (200, y, 840, y + 90), PANEL, c, 14, 3, kk)
        text(d, (240, y + 45), f"{i + 1}. {s}", 34, TXT, "Bold", "lm", k=kk)
    vx, vy = 1350, 520
    open_ = 0.5 + 0.5 * math.sin(t * 6) if 2.0 < t < 3.6 else 0.0
    box(d, (vx - 220, vy - 130, vx + 220, vy + 130), PANEL, LINE, 16, 2, k)
    text(d, (vx, vy - 170), "brake valve (simplified)", 28, DIM, "Medium", "mm", k=k)
    d.rectangle([vx - 220, vy - 20, vx + 220, vy + 20], fill=fade(mix(BG, RED, 0.5), k))
    d.rectangle([vx - 40, vy - 110 + 70 * open_, vx + 40, vy - 20 + 70 * open_ - 70 * open_], fill=fade(DIM, k))
    if t > 3.8: text(d, (vx, vy + 190), "display_task resumes", 30, DISP, "Bold", "mm", k=prog(t, 3.8, 4.3))

def s_timeline(d, t, dur):
    chrome(d, "STEP 4 · FOLLOW THE EVENT", "The whole event, start to finish", "Interrupt, signal, switch, act, block, resume. The key is not just speed: the worst case is short and predictable.", t, dur)
    k = prog(t, 0.2, 0.6)
    lanes = [("ISR", AMBER), ("brake", BRAKE), ("display", DISP), ("log", LOG)]
    spans = [(2, 0.0, 0.30), (0, 0.30, 0.34), (1, 0.34, 0.58), (2, 0.58, 0.86), (3, 0.86, 1.0)]
    lane_chart(d, lanes, spans, 400, 1700, 310, 120, prog(t, 0.4, 4.6), k)
    for x, lab in [(0.30, "interrupt"), (0.34, "switch"), (0.58, "block")]:
        kk = prog(t, 0.4 + x * 4.2, 0.8 + x * 4.2)
        xx = 400 + 1300 * x
        d.line([xx, 260, xx, 690], fill=fade(mix(BG, TXT, 0.5), kk), width=2)
    text(d, (W // 2, 760), "bounded, predictable reaction time", 36, GREEN, "Bold", "mm", k=prog(t, 4.6, 5.1))

# ---------------- chapter 5: sharing safely ----------------
def s_shared(d, t, dur):
    chrome(d, "STEP 5 · SHARING SAFELY", "Two tasks, one piece of data", "Tasks often share data. If one is paused halfway through updating it, another task can read a half-written mess.", t, dur)
    k = prog(t, 0.2, 0.6)
    box(d, (720, 380, 1200, 600), PANEL, AMBER, 16, 3, k)
    text(d, (960, 420), "wheel_data", 34, AMBER, "Bold", "mm", mono=True, k=k)
    p = prog(t, 0.8, 2.4)
    fl = "FL: 82" if p > 0.3 else "FL: 80"
    fr = "FR: 79"
    text(d, (960, 490), fl, 32, TXT, "Bold", "mm", mono=True, k=k)
    text(d, (960, 545), fr, 32, RED if t > 2.6 else TXT, "Bold", "mm", mono=True, k=k)
    task_box(d, 160, 440, 440, 80, "log_task", LOG, None, k)
    task_box(d, 1320, 440, 440, 80, "brake_task", BRAKE, None, k)
    arrow(d, (610, 480), (710, 480), LOG, 5, k)
    if t > 2.6:
        kk = prog(t, 2.6, 3.0)
        arrow(d, (1310, 480), (1210, 480), BRAKE, 5, kk)
        text(d, (960, 680), "paused mid-update: new FL, old FR", 32, RED, "Bold", "mm", k=kk)
    text(d, (960, 330), "(example values)", 24, DIM, "Medium", "mm", k=k)

def s_mutex(d, t, dur):
    chrome(d, "STEP 5 · SHARING SAFELY", "The mutex: one at a time", "The fix is a mutex, a lock. Take it before touching the data, give it back after. Anyone else who wants it waits.", t, dur)
    k = prog(t, 0.2, 0.6)
    box(d, (720, 380, 1200, 600), PANEL, AMBER, 16, 3, k)
    text(d, (960, 440), "wheel_data", 34, AMBER, "Bold", "mm", mono=True, k=k)
    held = 1.0 < t < 3.6
    lock(d, 960, 530, 34, LOG if held else (BRAKE if t > 4.0 else GREEN), k, open_=not held and t < 4.0)
    task_box(d, 160, 440, 440, 80, "log_task", LOG, None, k, hot=held)
    task_box(d, 1320, 440, 440, 80, "brake_task", BRAKE, None, k, hot=t > 4.0)
    if 2.0 < t < 3.6: text(d, (1540, 580), "waits for the lock", 26, DIM, "Medium", "mm")
    code(d, ["take(&data_mutex);", "  ...update wheel_data...", "give(&data_mutex);"], 560, 660, t, prog(t, 1.0, 1.4), size=28, gap=42, start=1.2, step=0.3)

def s_inversion(d, t, dur):
    chrome(d, "STEP 5 · SHARING SAFELY", "Priority inversion", "But locks bring a trap. Low holds the lock. High waits for it. Then Medium preempts Low, and High is stuck behind a task it outranks.", t, dur)
    k = prog(t, 0.2, 0.6)
    lanes = [("high", BRAKE), ("medium", DISP), ("low", LOG)]
    spans = [(2, 0.0, 0.18), (0, 0.18, 0.22), (2, 0.22, 0.28), (1, 0.28, 0.85), (2, 0.85, 0.92), (0, 0.92, 1.0)]
    lane_chart(d, lanes, spans, 400, 1700, 330, 150, prog(t, 0.4, 5.0), k)
    p = prog(t, 0.4, 5.0)
    if p > 0.22:
        a, b = 400 + 1300 * 0.22, 400 + 1300 * min(p, 0.92)
        d.rectangle([a, 330 - 8, b, 330 + 8], fill=mix(BG, BRAKE, 0.35))
        text(d, ((a + b) / 2, 280), "high is blocked, waiting...", 28, RED, "Bold", "mm")
    if p > 0.05: text(d, (400 + 1300 * 0.09, 690), "low takes lock", 24, LOG, "Bold", "mm")

def s_inherit(d, t, dur):
    chrome(d, "STEP 5 · SHARING SAFELY", "The fix: priority inheritance", "This famously reset NASA's Mars Pathfinder lander in 1997. The fix: while Low holds a lock High needs, Low borrows High's priority.", t, dur)
    k = prog(t, 0.2, 0.6)
    lanes = [("high", BRAKE), ("medium", DISP), ("low", LOG)]
    spans = [(2, 0.0, 0.18), (0, 0.18, 0.22), (2, 0.22, 0.36), (0, 0.36, 0.60), (1, 0.60, 1.0)]
    lane_chart(d, lanes, spans, 400, 1700, 330, 150, prog(t, 0.4, 5.0), k)
    p = prog(t, 0.4, 5.0)
    if p > 0.22:
        a = 400 + 1300 * 0.22
        b = 400 + 1300 * min(p, 0.36)
        d.rectangle([a, 630 - 34, b, 630 + 34], outline=AMBER, width=4)
        text(d, (a + 40, 700), "low runs at HIGH priority, releases lock", 26, AMBER, "Bold", "lm")
    if p > 0.6: text(d, (400 + 1300 * 0.48, 280), "high finishes on time", 28, GREEN, "Bold", "mm")

# ---------------- chapter 6: deadlines ----------------
def s_hardsoft(d, t, dur):
    chrome(d, "STEP 6 · DEADLINES", "Hard versus soft real time", "A hard deadline must never be missed, like brake control. A soft one can slip now and then, like a screen update.", t, dur)
    k = prog(t, 0.2, 0.6)
    for i, (n, c, desc, miss) in enumerate([("HARD", BRAKE, "brake control", "a miss is a failure"), ("SOFT", DISP, "display update", "a miss is a glitch")]):
        x = 220 + i * 780
        kk = prog(t, 0.4 + i * 1.4, 0.9 + i * 1.4)
        box(d, (x, 290, x + 700, 740), PANEL, c, 18, 3, kk)
        text(d, (x + 350, 350), n, 56, c, "Bold", "mm", k=kk)
        text(d, (x + 350, 420), desc, 32, TXT, "Medium", "mm", k=kk)
        d.line([x + 60, 560, x + 640, 560], fill=fade(LINE, kk), width=3)
        dl = x + 460
        d.line([dl, 490, dl, 630], fill=fade(c, kk), width=4)
        text(d, (dl, 470), "deadline", 24, c, "Bold", "mm", k=kk)
        d.rectangle([x + 80, 540, x + (500 if i else 420), 580], fill=fade(mix(BG, c, 0.7), kk))
        text(d, (x + 350, 690), miss, 30, DIM, "Medium", "mm", k=kk)

def s_watchdog(d, t, dur):
    chrome(d, "STEP 6 · DEADLINES", "The watchdog", "A watchdog timer counts down on its own. Healthy software keeps resetting it. If the software hangs, it hits zero and resets the chip.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 300, 1620, 520
    box(d, (x0 - 20, y - 60, x1 + 20, y + 60), (8, 12, 24), LINE, 14, 2, k)
    if t < 3.0:
        v = 1.0 - ((t * 1.4) % 0.7)
        col = GREEN
    else:
        v = max(0.0, 1.0 - (t - 3.0) * 0.45)
        col = AMBER if v > 0.2 else RED
    d.rectangle([x0, y - 40, x0 + (x1 - x0) * v * k, y + 40], fill=col)
    text(d, (x0, y - 100), "watchdog counter", 30, TXT, "Bold", "lm", k=k)
    if t < 3.0: text(d, (W // 2, y + 140), "\"I'm alive\" — counter refilled", 32, GREEN, "Bold", "mm", k=k)
    elif v > 0: text(d, (W // 2, y + 140), "software stuck... no refill", 32, AMBER, "Bold", "mm")
    else: text(d, (W // 2, y + 140), "RESET → restart in a safe state", 36, RED, "Bold", "mm")

def s_where(d, t, dur):
    chrome(d, "STEP 6 · DEADLINES", "Where you'll find an RTOS", "Real-time operating systems run inside cars, drones, industrial robots, medical devices, routers and wearables. In cars, many follow a standard called AUTOSAR.", t, dur)
    k = prog(t, 0.2, 0.6)
    items = [("car ECUs", RED), ("drones", CYAN), ("industrial robots", AMBER), ("medical devices", GREEN), ("network gear", BLUE), ("wearables", PURPLE)]
    for i, (n, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.35, 0.8 + i * 0.35)
        col, row = i % 3, i // 3
        x, y = 240 + col * 500, 300 + row * 220
        box(d, (x, y, x + 440, y + 170), PANEL, c, 18, 3, kk)
        ecu(d, x + 70, y + 85, kk, c, 1.2)
        text(d, (x + 130, y + 85), n, 34, TXT, "Bold", "lm", k=kk)

def s_vs(d, t, dur):
    chrome(d, "STEP 6 · DEADLINES", "Why not just use a desktop OS?", "A desktop OS aims for good average speed and fairness. An RTOS aims for a guaranteed worst case. For brakes, the worst case is what counts.", t, dur)
    k = prog(t, 0.2, 0.6)
    import random
    for i, (n, c, spread) in enumerate([("desktop OS", DIM, 1.0), ("RTOS", GREEN, 0.15)]):
        y = 380 + i * 230
        kk = prog(t, 0.4 + i * 1.2, 0.9 + i * 1.2)
        text(d, (200, y), n, 36, c, "Bold", "lm", k=kk)
        d.line([500, y, 1700, y], fill=fade(LINE, kk), width=2)
        rnd = random.Random(i + 3)
        for j in range(40):
            v = abs(rnd.gauss(0, 1)) * spread
            x = 560 + min(v, 3.2) * 320 * (1 if i == 0 else 2)
            d.ellipse([x - 7, y - 7 + (j % 5 - 2) * 9, x + 7, y + 7 + (j % 5 - 2) * 9], fill=fade(c, kk))
        mx = 560 + (3.2 * 320 if i == 0 else 0.5 * 640)
        d.line([mx, y - 60, mx, y + 60], fill=fade(RED if i == 0 else GREEN, kk), width=4)
        text(d, (mx, y + 90), "worst case", 24, RED if i == 0 else GREEN, "Bold", "mm", k=kk)
    text(d, (1100, 820 - 40), "reaction time →   (illustration)", 26, DIM, "Medium", "mm", k=prog(t, 3.0, 3.5))

def s_recap(d, t, dur):
    chrome(d, "RECAP", "Keeping the brakes on time", "One loop makes everything wait. An RTOS splits work into tasks, runs the highest-priority ready one, and guards shared data with locks.", t, dur)
    stg = [("Superloop", AMBER), ("Tasks", CYAN), ("Scheduler", GREEN), ("Event", RED), ("Locks", PURPLE), ("Deadlines", BLUE)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(stg):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.2:
        car(d, 760, 720, 400, prog(t, 4.2, 4.7))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does a 3D printer or CNC", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "machine know where it is?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
          ("03_superloop", s_superloop, 8), ("04_problem", s_problem, 8), ("05_worst", s_worst, 8),
          ("06_tasks", s_tasks, 8), ("07_states", s_states, 8), ("08_blocked", s_blocked, 8),
          ("09_priority", s_priority, 8), ("10_preempt", s_preempt, 8), ("11_tick", s_tick, 8), ("12_context", s_context, 8),
          ("13_isr", s_isr, 8), ("14_wake", s_wake, 8), ("15_act", s_act, 8), ("16_timeline", s_timeline, 8),
          ("17_shared", s_shared, 8), ("18_mutex", s_mutex, 8), ("19_inversion", s_inversion, 8), ("20_inherit", s_inherit, 8),
          ("21_hardsoft", s_hardsoft, 8), ("22_watchdog", s_watchdog, 8), ("23_where", s_where, 8), ("24_vs", s_vs, 8),
          ("25_recap", s_recap, 8), ("26_end", s_end, 6)]

NARRATION = {
 "01_hook": "Your car is full of small computers, often dozens of them. One of them watches your wheels while you brake. If a wheel starts to lock, it has to react within milliseconds. Every single time. Even when it's busy doing something else. So what happens if it's busy?",
 "02_cover": "Today, we'll follow one event, a wheel starting to lock, through a car's computer. First, the simple way to write firmware, and why it breaks down. Then tasks, the scheduler, and that one event, step by step. Then how tasks share data safely, and how a real-time system makes sure deadlines are met.",
 "03_superloop": "Step one: the superloop. The simplest firmware is one endless loop. Read the sensors. Control the brakes. Update the display. Write a log. Then go round again, forever. It's easy to write, and for small gadgets, it works perfectly well.",
 "04_problem": "But here's the what-if. Suppose a wheel starts to lock just after the loop has finished its brake step. Now the CPU is busy drawing the display, and then writing the log to flash memory, which is slow. The brake logic won't run again until the loop comes all the way back around.",
 "05_worst": "So the worst-case reaction time is the length of the whole loop. And every feature you add makes it longer. Add diagnostics, add networking, and every job in the loop gets slower to respond. In a superloop, everything waits for everything.",
 "06_tasks": "Step two: tasks. A real-time operating system, or R T O S, lets you split the work into separate tasks. Each task is its own little loop, with its own stack, written as if it had the whole CPU to itself. One task for the brakes, one for the display, one for logging.",
 "07_states": "On a single core, only one task can actually run at a time. So every task is in one of a few states. Running: it has the CPU. Ready: it could run, and is waiting for a turn. Or blocked: it's waiting for something to happen, like a timer or a message.",
 "08_blocked": "And here's the important bit. A blocked task uses no CPU time at all. The brake task can sit blocked for minutes, costing nothing, while other tasks get on with their work. Then, the instant its event arrives, it wakes up.",
 "09_priority": "Step three: the scheduler. Each task gets a priority. The brake task is high. The display is medium. The logger is low. And the scheduler follows one simple rule: the highest-priority task that is ready to run always gets the CPU.",
 "10_preempt": "This is called preemption. The logger runs, then the display. Now the brake task becomes ready. The scheduler doesn't wait for the display to finish. It pauses the display right there, and switches to the brake task. When the brake task blocks again, the display carries on.",
 "11_tick": "Most R T O S kernels also have a heartbeat, called the tick. A hardware timer interrupts at a steady rate, often a thousand times a second. On each tick, the scheduler checks: have any timeouts expired? Is a sleeping task due to wake up? Should a different task be running now?",
 "12_context": "Switching tasks is called a context switch. The R T O S saves the running task's registers onto that task's own stack. Then it restores the next task's saved registers, including its program counter. It's the same trick you saw in the interrupts episode, and it takes only a short time.",
 "13_isr": "Step four: let's follow the event. A toothed ring on the wheel spins past a sensor, and the controller sees the wheel slowing down far too fast. An interrupt fires. The interrupt handler is tiny. It clears the flag, and gives a semaphore, a signal, to the brake task. No braking logic goes in here.",
 "14_wake": "That signal moves the brake task from blocked to ready. It's the highest priority task that's ready, so when the handler finishes, the scheduler switches straight to it, instead of going back to the display. The display task is paused, and simply left ready.",
 "15_act": "Now the brake task does its job. It reads the wheel speeds, works out how much the wheel is slipping, and commands the brake valves to ease the pressure on that wheel, so it can grip again. Then it blocks, waiting for the next event. And the display task picks up exactly where it left off.",
 "16_timeline": "Here's the whole thing on one timeline. Interrupt. Signal. Switch. Act. Block. Resume. The point isn't just that it's fast. It's that the worst-case reaction time is short, and known in advance, no matter what the display or the logger happen to be doing.",
 "17_shared": "Step five: sharing safely. Tasks often share data. Say the logger is copying the wheel speeds, and gets paused halfway through. The brake task runs, and updates the values. Now the logger resumes, and saves a mix of new and old numbers that never existed together.",
 "18_mutex": "The fix is a mutex, a lock. Before touching the shared data, a task takes the mutex. When it's done, it gives it back. If another task wants the data in the meantime, it blocks until the lock is free. One at a time, always consistent.",
 "19_inversion": "But locks hide a trap, called priority inversion. The low task takes the lock. The high task wakes up, needs the same lock, and has to wait. So far, that's fine. But then a medium task becomes ready. It preempts the low task, so the lock is never released, and the high task is stuck behind a task it outranks.",
 "20_inherit": "This really happened. In nineteen ninety seven, priority inversion caused NASA's Mars Pathfinder lander to keep resetting itself, until engineers fixed it from Earth. The usual fix is priority inheritance. While the low task holds a lock the high task needs, it borrows the high priority. It finishes quickly, releases the lock, and the high task runs on time.",
 "21_hardsoft": "Step six: deadlines. Real-time doesn't just mean fast. It means on time. A hard deadline must never be missed, like brake control. Missing it counts as a failure. A soft deadline can slip now and then, like a screen update. A late frame is just a glitch.",
 "22_watchdog": "And what if the software hangs? Safety systems use a watchdog. It's a timer that counts down on its own. Healthy software keeps refilling it. If the software gets stuck and stops refilling it, the watchdog reaches zero, and resets the chip, so it can restart in a safe state.",
 "23_where": "You'll find real-time operating systems in car control units, drones, industrial robots, medical devices, network equipment, and wearables. In cars, many control units run an operating system that follows a standard called AUTOSAR, so software from different suppliers can work together.",
 "24_vs": "So why not just use a desktop operating system? A desktop OS is designed for good average speed, and to be fair to every program. Most of the time it's quick, but now and then, something takes much longer. An R T O S is designed so the worst case is guaranteed. And for brakes, the worst case is the only case that counts.",
 "25_recap": "Let's recap. A superloop makes every job wait for every other job. An R T O S splits the work into tasks, and always runs the highest priority one that's ready. Interrupts wake tasks up, locks keep shared data safe, priority inheritance avoids inversion, and a watchdog catches the rest.",
 "26_end": "Next episode: how does a 3 D printer or a C N C machine know where it is? Subscribe so you don't miss it.",
}
OUTPUT = "what_is_an_rtos_and_why_your_car_needs_one_ep11_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep11/{name}.mp4", f"ep11/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep11", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    for j in range(0, len(SCENES), 9):
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES[j:j + 9]):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save(f"ep11/sheet{j // 9 + 1}.jpg", quality=85)
