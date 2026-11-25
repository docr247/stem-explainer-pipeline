import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)

def button(d, cx, cy, r, pressed, k=1.0):
    dy = 8 if pressed else 0
    d.ellipse([cx - r - 14, cy - r - 14 + 10, cx + r + 14, cy + r + 14 + 10], fill=fade((8, 12, 24), k))
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=fade(PANEL, k), outline=fade(LINE, k), width=4)
    if pressed:
        for g in range(5):
            rr = r + 20 + g * 12
            d.ellipse([cx - rr, cy - rr + dy, cx + rr, cy + rr + dy], outline=mix(BG, RED, (0.3 - g * 0.05) * k), width=6)
    d.ellipse([cx - r, cy - r + dy, cx + r, cy + r + dy], fill=fade(RED if pressed else (150, 50, 60), k))

def stack_regs(d, x, y, n, k, col=AMBER):
    regs = ["xPSR", "PC", "LR", "R12", "R3", "R2", "R1", "R0"]
    for i in range(min(n, 8)):
        yy = y - i * 52
        box(d, (x, yy, x + 220, yy + 44), mix(BG, col, 0.2), col, 8, 2, k)
        text(d, (x + 110, yy + 22), regs[i], 28, col, "Bold", "mm", mono=True, k=k)

def s_hook(d, t, dur):
    chrome(d, "", "", "Your CPU is busy running code, millions of instructions a second. You press a button, and it reacts instantly. But it was never checking the button.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 300, 330, 380, 260, "CPU", "busy in main()", CYAN, k)
    for i in range(6):
        y = 360 + i * 36
        a = (t * 3 + i) % 6 / 6
        d.rectangle([720, y, 720 + 260 * (0.4 + 0.6 * a), y + 18], fill=fade(mix(BG, CYAN, 0.5), k))
    pressed = 3.0 < t < 3.6
    button(d, 1440, 460, 90, pressed, prog(t, 0.8, 1.3))
    if t > 3.6:
        text(d, (1440, 640), "noticed instantly?", 40, AMBER, "Bold", "mm", k=prog(t, 3.6, 4.1))

def s_polling(d, t, dur):
    chrome(d, "THE SLOW WAY", "Polling: \"Is it pressed yet?\"", "One way is polling: the CPU keeps asking the button, over and over. It wastes time, and a quick press can slip through while the CPU is busy elsewhere.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 200, 340, 340, 240, "CPU", "", CYAN, k)
    button(d, 1500, 460, 80, 4.8 < t < 5.1, k)
    for i in range(int(clamp((t - 0.8) / 5.5) * 7)):
        y = 300 + i * 70
        box(d, (620, y, 1300, y + 56), PANEL, LINE, 10, 2, k)
        text(d, (650, y + 28), "if (button_pressed())", 30, TXT, "Medium", "lm", mono=True, k=k)
        missed = i == 5
        text(d, (1270, y + 28), "missed!" if missed else "no", 30, RED if missed else DIM, "Bold", "rm", k=k)

def s_irq(d, t, dur):
    chrome(d, "STEP 1 · THE IRQ LINE", "The button taps the CPU", "Instead, the pin is wired to an interrupt controller, called the NVIC on ARM chips. When the button is pressed, it raises an interrupt request, and the controller taps the CPU on the shoulder.", t, dur)
    k = prog(t, 0.2, 0.7)
    button(d, 260, 460, 70, 2.0 < t < 2.6, k)
    box(d, (720, 380, 1100, 540), PANEL, PURPLE, 14, 4, k)
    text(d, (910, 440), "NVIC", 44, TXT, "Bold", "mm", k=k)
    text(d, (910, 490), "interrupt controller", 24, DIM, "Medium", "mm", k=k)
    chip(d, 1420, 340, 340, 240, "CPU", "", CYAN, k)
    hot = t > 2.0
    d.line([360, 460, 720, 460], fill=RED if hot else LINE, width=7)
    d.line([1100, 460, 1420, 460], fill=RED if t > 2.8 else LINE, width=7)
    text(d, (540, 420), "EXTI13", 28, RED if hot else DIM, "Bold", "mm", mono=True, k=k)
    text(d, (1260, 420), "IRQ!", 34, RED if t > 2.8 else DIM, "Bold", "mm", mono=True, k=k)
    if t > 3.4:
        text(d, (1590, 640), "\"stop what you're doing\"", 30, AMBER, "Bold", "mm", k=prog(t, 3.4, 3.9))

def s_save(d, t, dur):
    chrome(d, "STEP 2 · SAVE AND JUMP", "Bookmark, then jump", "The CPU finishes its current instruction, then saves its place: eight registers pushed onto the stack, automatically. Then it looks up the handler's address in the vector table, and jumps there.", t, dur)
    k = prog(t, 0.2, 0.6)
    text(d, (330, 280), "stack", 32, AMBER, "Bold", "mm", k=k)
    stack_regs(d, 220, 720, int(clamp((t - 1.0) / 2.6) * 8 + 0.999) if t > 1.0 else 0, k)
    box(d, (700, 330, 1300, 690), PANEL, LINE, 14, 3, prog(t, 3.6, 4.1))
    text(d, (1000, 300), "vector table", 32, PURPLE, "Bold", "mm", k=prog(t, 3.6, 4.1))
    rows = [("SysTick_Handler", False), ("USART2_IRQHandler", False), ("EXTI15_10_IRQHandler", True), ("TIM2_IRQHandler", False)]
    for i, (n, hot) in enumerate(rows):
        kk = prog(t, 3.8 + i * 0.2, 4.2 + i * 0.2)
        y = 360 + i * 80
        on = hot and t > 5.0
        box(d, (730, y, 1270, y + 64), mix(BG, AMBER, 0.25) if on else PANEL, AMBER if on else LINE, 10, 3 if on else 1, kk)
        text(d, (760, y + 32), n, 28, AMBER if on else TXT, "Medium", "lm", mono=True, k=kk)
    if t > 5.4:
        arrow(d, (1290, 552), (1450, 552), AMBER, 5, prog(t, 5.4, 5.9))
        text(d, (1470, 552), "jump", 36, AMBER, "Bold", "lm", k=prog(t, 5.4, 5.9))

def s_isr(d, t, dur):
    chrome(d, "STEP 3 · THE HANDLER", "Do a little, then return", "The interrupt handler runs. A good one is short: clear the flag, note what happened, and return. The CPU pops its registers back, and main carries on exactly where it left off.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, x1, y = 200, 1720, 430
    d.line([x0, y, x1, y], fill=fade(LINE, k), width=4)
    text(d, (x0, y - 40), "main()", 30, CYAN, "Bold", "lm", mono=True, k=k)
    p = clamp((t - 0.8) / 6.0)
    seg = [(0.0, 0.35, CYAN, "main"), (0.35, 0.42, AMBER, "save"), (0.42, 0.66, RED, "ISR"), (0.66, 0.73, AMBER, "restore"), (0.73, 1.0, CYAN, "main")]
    for a, b, c, lab in seg:
        if p <= a: continue
        e = min(p, b)
        yy = y if c == CYAN else y + 120
        d.rectangle([x0 + (x1 - x0) * a, yy - 18, x0 + (x1 - x0) * e, yy + 18], fill=c)
        text(d, (x0 + (x1 - x0) * (a + b) / 2, yy + 50), lab, 28, c, "Bold", "mm", k=k)
    if t > 5.0:
        text(d, (W // 2, 720), "main() never knew it was paused", 34, GREEN, "Bold", "mm", k=prog(t, 5.0, 5.5))

def s_prio(d, t, dur):
    chrome(d, "STEP 4 · PRIORITIES", "Who gets to interrupt whom", "Interrupts have priorities. If something more urgent arrives while a handler is running, it can interrupt the interrupt. That's called nesting, and it keeps the urgent work on time.", t, dur)
    k = prog(t, 0.2, 0.6)
    lanes = [("main()", CYAN, 0), ("button  (priority 2)", AMBER, 1), ("timer  (priority 0, urgent)", RED, 2)]
    for i, (n, c, _) in enumerate(lanes):
        y = 320 + i * 150
        text(d, (200, y - 52), n, 30, c, "Bold", "lm", mono=True, k=k)
        d.line([200, y, 1720, y], fill=fade(LINE, k), width=2)
    p = clamp((t - 0.8) / 6.0)
    spans = [(0, 0.2, 0), (0.2, 0.4, 1), (0.4, 0.6, 2), (0.6, 0.75, 1), (0.75, 1.0, 0)]
    for a, b, lane in spans:
        if p <= a: continue
        e = min(p, b)
        c = lanes[lane][1]
        y = 320 + lane * 150
        d.rectangle([200 + 1520 * a, y - 20, 200 + 1520 * e, y + 20], fill=c)

def s_code(d, t, dur):
    chrome(d, "IN CODE", "A real handler", "On an STM32 Nucleo board, the blue user button is on pin C13. Its handler checks the pending flag, clears it, and sets a variable for main to deal with. That's it. In and out in microseconds.", t, dur)
    k = prog(t, 0.2, 0.7)
    lines = ["volatile int button_pressed = 0;", "",
             "void EXTI15_10_IRQHandler(void) {",
             "    if (EXTI->PR & (1 << 13)) {   // PC13",
             "        EXTI->PR = (1 << 13);     // clear flag",
             "        button_pressed = 1;       // tell main",
             "    }", "}"]
    box(d, (160, 270, 1500, 270 + 40 + len(lines) * 56), (6, 10, 20), LINE, 14, 3, k)
    for i, ln in enumerate(lines):
        kk = prog(t, 0.5 + i * 0.35, 0.9 + i * 0.35)
        col = AMBER if "PR" in ln else (GREEN if "button_pressed = 1" in ln else TXT)
        text(d, (200, 292 + i * 56), ln, 34, col, mono=True, k=kk)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "The tap on the shoulder", "Event, request, save, jump, handle, return. Your CPU never wastes time checking, yet it reacts within a fraction of a microsecond.", t, dur)
    st = [("Event", RED), ("IRQ", PURPLE), ("Save", AMBER), ("Jump", AMBER), ("Handle", RED), ("Return", CYAN)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(st):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.2:
        button(d, W // 2, 660, 60, 4.6 < t < 5.0, prog(t, 4.2, 4.7))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does an ADC turn the", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "real world into numbers?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_polling", s_polling, 9), ("03_irq", s_irq, 10),
          ("04_save", s_save, 11), ("05_isr", s_isr, 10), ("06_prio", s_prio, 10),
          ("07_code", s_code, 10), ("08_recap", s_recap, 9), ("09_end", s_end, 6)]

NARRATION = {
 "01_hook": "Your CPU is busy running code, millions of instructions every second. You press a button, and it reacts instantly. But here's the thing: it was never checking the button. So how did it know?",
 "02_polling": "One way to watch a button is polling. The CPU keeps asking: is it pressed yet? No. Is it pressed yet? No. It wastes time, and if the CPU is busy elsewhere, a quick press can slip right through.",
 "03_irq": "So instead, the button's pin is wired to an interrupt controller. On ARM chips it's called the N V I C. When you press the button, it raises an interrupt request, and the controller taps the CPU on the shoulder.",
 "04_save": "The CPU finishes the instruction it's on, then saves its place. Eight registers, including the program counter, are pushed onto the stack, automatically, in hardware. Then it looks up the handler's address in the vector table, and jumps there.",
 "05_isr": "Now the interrupt handler runs. A good handler is short: clear the flag, note what happened, and return. The CPU pops its registers back off the stack, and main carries on exactly where it left off. It never even knew it was paused.",
 "06_prio": "Interrupts also have priorities. If something more urgent arrives while a handler is running, like a timer that must never be late, it can interrupt the interrupt. That's called nesting, and it keeps the urgent work on time.",
 "07_code": "Here's a real handler. On an S T M 32 Nucleo board, the blue user button is on pin C thirteen. The handler checks the pending flag, clears it, and sets a variable for main to deal with later. That's it. In and out in microseconds.",
 "08_recap": "Event. Request. Save. Jump. Handle. Return. Your CPU never wastes time checking, yet it reacts within a fraction of a microsecond.",
 "09_end": "Next episode: how does an A D C turn the real world into numbers? Subscribe so you don't miss it.",
}
OUTPUT = "interrupts_how_a_cpu_gets_tapped_on_the_shoulder_ep7_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep7/{name}.mp4", f"ep7/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep7", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    s = Image.new("RGB", (W * 3, H * 3))
    for i, (_, fn, dur) in enumerate(SCENES):
        s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
    s.resize((2880, 1620)).save("ep7/sheet.jpg", quality=85)
