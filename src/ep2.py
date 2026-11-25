import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome, wrap,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
C_CODE = ["while (1) {", "    GPIOA->ODR ^= LED;", "    delay_ms(500);", "}"]
ASM = [("LDR  r0, =0x48000014", "4805"), ("LDR  r1, [r0]", "6801"), ("MOVS r2, #0x20", "2220"),
       ("EORS r1, r2", "4051"), ("STR  r1, [r0]", "6001")]

def led(d, cx, cy, on, r=40, k=1.0):
    if on:
        for g in range(5):
            rr = r + 12 + g * 12
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=mix(BG, GREEN, 0.3 - g * 0.05), width=6)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fade(GREEN if on else (40, 70, 55), k), outline=fade(LINE, k), width=3)

def code_panel(d, x, y, lines, k, hl=-1, size=34, w=700, col=TXT):
    box(d, (x, y, x + w, y + 40 + len(lines) * (size + 18)), (6, 10, 20), LINE, 14, 3, k)
    for i, ln in enumerate(lines):
        if i == hl:
            d.rectangle([x + 6, y + 18 + i * (size + 18), x + w - 6, y + 18 + i * (size + 18) + size + 12], fill=mix(BG, CYAN, 0.25))
        text(d, (x + 30, y + 24 + i * (size + 18)), ln, size, col, mono=True, k=k)

def s_hook(d, t, dur):
    chrome(d, "", "", "You write a few lines of C. Seconds later, a light blinks. How does text become electricity?", t, dur)
    code_panel(d, 260, 300, C_CODE, prog(t, 0.2, 0.8), size=40, w=760)
    k = prog(t, 1.2, 1.8)
    arrow(d, (1080, 430), (1300, 430), DIM, 5, k)
    on = t > 2.0 and int((t - 2.0) * 2) % 2 == 0
    led(d, 1480, 430, on, 70, k)
    text(d, (1480, 560), "PA5 · on-board LED", 28, DIM, "Medium", "mm", k=k)

def s_compile(d, t, dur):
    chrome(d, "STEP 1 · COMPILE", "From C to numbers", "The compiler translates your C into machine instructions, and each instruction is just a number.", t, dur)
    code_panel(d, 120, 300, ["GPIOA->ODR ^= LED;"], prog(t, 0.2, 0.7), size=32, w=470)
    arrow(d, (610, 340), (690, 340), DIM, 5, prog(t, 0.8, 1.2))
    n = int(clamp((t - 1.2) / 3.0) * len(ASM) + 0.999)
    code_panel(d, 710, 300, [a for a, _ in ASM[:n]] or [""], prog(t, 1.2, 1.6), size=30, w=540, col=CYAN)
    if t > 4.6:
        k = prog(t, 4.6, 5.0)
        arrow(d, (1270, 340), (1350, 340), DIM, 5, k)
        m = int(clamp((t - 4.8) / 2.5) * len(ASM) + 0.999)
        code_panel(d, 1370, 300, [f"0x{h}" for _, h in ASM[:m]] or [""], k, size=30, w=330, col=AMBER)
    if t > 7.6:
        text(d, (1535, 650), "16-bit Thumb code", 28, DIM, "Medium", "mm", k=prog(t, 7.6, 8.2))

def s_flash(d, t, dur):
    chrome(d, "STEP 2 · FLASH", "Burned into the chip", "A programmer like ST-Link writes those numbers into the chip's flash memory, which keeps them even with the power off.", t, dur)
    chip(d, 160, 380, 340, 200, "ST-Link", "programmer", PURPLE, prog(t, 0.2, 0.8), pins=False)
    k = prog(t, 0.5, 1.1)
    box(d, (760, 260, 1760, 820), PANEL, AMBER, 14, 4, k)
    text(d, (1260, 230), "Flash memory", 34, AMBER, "Bold", "mm", k=k)
    arrow(d, (520, 480), (740, 480), DIM, 5, k)
    if 1.2 < t < 7.5:
        p = (t * 1.6) % 1
        d.rounded_rectangle([540 + p * 170 - 16, 450, 540 + p * 170 + 16, 510 - 30], 4, fill=AMBER)
    rows = 12
    hexes = ["20005000", "08000101"] + ["4805", "6801", "2220", "4051", "6001"] * 20
    f = clamp((t - 1.2) / 6.0)
    for i in range(int(rows * f)):
        addr = 0x08000000 + i * 16
        text(d, (790, 290 + i * 42), f"{addr:08X}", 26, DIM, mono=True)
        row = " ".join(hexes[(i * 4 + j) % len(hexes)] for j in range(4))
        text(d, (1000, 290 + i * 42), row, 26, AMBER if i else CYAN, mono=True)

def s_vector(d, t, dur):
    chrome(d, "STEP 3 · RESET", "Two words decide everything", "On reset, the core reads two words: the starting stack pointer and the address of the reset handler. Startup code prepares RAM, then calls main().", t, dur)
    k = prog(t, 0.2, 0.8)
    box(d, (160, 290, 860, 520), PANEL, LINE, 14, 3, k)
    text(d, (190, 320), "0x08000000", 30, DIM, mono=True, k=k)
    text(d, (190, 420), "0x08000004", 30, DIM, mono=True, k=k)
    text(d, (450, 320), "initial SP", 30, CYAN, "Bold", k=prog(t, 1.2, 1.7))
    text(d, (450, 420), "Reset_Handler", 30, GREEN, "Bold", k=prog(t, 2.0, 2.5))
    text(d, (450, 362), "0x20005000", 26, CYAN, mono=True, k=prog(t, 1.2, 1.7))
    text(d, (450, 462), "0x08000101", 26, GREEN, mono=True, k=prog(t, 2.0, 2.5))
    steps = [("Copy .data from flash to RAM", AMBER), ("Zero the .bss section", AMBER),
             ("Set up the clock (SystemInit)", PURPLE), ("Call main()", GREEN)]
    for i, (s, c) in enumerate(steps):
        st = 3.2 + i * 1.3; kk = prog(t, st, st + 0.4)
        if kk <= 0: continue
        y = 290 + i * 110
        box(d, (1000, y, 1760, y + 84), PANEL, c, 12, 3, kk)
        text(d, (1040, y + 42), s, 32, TXT, "Medium", "lm", k=kk)
        if i < 3: arrow(d, (1380, y + 86), (1380, y + 106), DIM, 3, kk)
    arrow(d, (870, 460), (990, 330), GREEN, 4, prog(t, 2.8, 3.2))

def s_cycle(d, t, dur):
    chrome(d, "STEP 4 · FETCH, DECODE, EXECUTE", "The loop at the heart of every CPU", "Fetch the instruction at the program counter. Decode it. Execute it. Move on. Forever.", t, dur)
    k = prog(t, 0.1, 0.6)
    code_panel(d, 120, 280, [a for a, _ in ASM], k, hl=-1, size=30, w=560, col=CYAN)
    step = int(clamp((t - 1.0) / 8.0) * 5)
    step = min(step, 4)
    phase = ((t - 1.0) / 1.6) % 1 if t > 1.0 else 0
    y = 280 + 18 + step * 48
    d.rectangle([126, y, 674, y + 42], outline=AMBER, width=3)
    text(d, (110, y + 21), "PC →", 26, AMBER, "Bold", "rm", k=k)
    stages = ["FETCH", "DECODE", "EXECUTE"]
    for i, s in enumerate(stages):
        x = 790 + i * 300
        active = int(phase * 3) == i and t > 1.0
        box(d, (x, 290, x + 260, 390), mix(BG, CYAN, 0.35) if active else PANEL, CYAN if active else LINE, 14, 3, k)
        text(d, (x + 130, 340), s, 34, TXT, "Bold", "mm", k=k)
        if i < 2: arrow(d, (x + 262, 340), (x + 296, 340), DIM, 3, k)
    regs = [("r0", ["--------", "48000014", "48000014", "48000014", "48000014"]),
            ("r1", ["--------", "--------", "00000000", "00000000", "00000020"]),
            ("r2", ["--------", "--------", "--------", "00000020", "00000020"])]
    done = step + (1 if phase > 0.66 else 0)
    for i, (r, vals) in enumerate(regs):
        yy = 460 + i * 80
        box(d, (790, yy, 1280, yy + 64), PANEL, LINE, 10, 2, k)
        text(d, (820, yy + 32), r, 32, PURPLE, "Bold", "lm", mono=True, k=k)
        text(d, (900, yy + 32), "0x" + vals[min(done, 4)], 32, TXT, "Medium", "lm", mono=True, k=k)
    on = done >= 5
    led(d, 1560, 560, on, 60, k)
    text(d, (1560, 680), "STR → LED on" if on else "LED", 30, GREEN if on else DIM, "Bold", "mm", k=k)

def s_mmio(d, t, dur):
    chrome(d, "STEP 5 · MEMORY-MAPPED I/O", "An address that is a wire", "The secret: address 0x48000014 isn't memory at all. It's a register wired straight to the GPIO pins. Writing a 1 to bit 5 drives pin PA5 high.", t, dur)
    k = prog(t, 0.2, 0.8)
    chip(d, 140, 340, 320, 200, "CPU", "STR r1, [r0]", CYAN, k)
    d.line([480, 440, 820, 440], fill=fade(LINE, k), width=6)
    if 1.0 < t < 2.6:
        x = 480 + ease((t - 1.0) / 1.4) * 340
        d.ellipse([x - 14, 426, x + 14, 454], fill=AMBER)
        text(d, (x, 400), "0x48000014", 26, AMBER, mono=True, anchor="mm")
    kk = prog(t, 2.4, 3.0)
    text(d, (1240, 300), "GPIOA_ODR  @ 0x48000014", 32, AMBER, "Bold", "mm", mono=True, k=kk)
    for b in range(16):
        x = 840 + (15 - b) * 50
        bit = 1 if (b == 5 and t > 3.6) else 0
        col = GREEN if bit else LINE
        d.rectangle([x, 350, x + 44, 410], fill=fade(mix(BG, col, 0.8 if bit else 0.4), kk))
        text(d, (x + 22, 380), str(bit), 28, TXT, mono=True, anchor="mm", k=kk)
        text(d, (x + 22, 430), str(b), 18, DIM, "Medium", "mm", k=kk)
    x5 = 840 + 10 * 50 + 22
    on = t > 4.6
    kk2 = prog(t, 3.8, 4.4)
    d.line([x5, 450, x5, 640], fill=fade(GREEN if on else LINE, kk2), width=6)
    text(d, (x5 + 20, 560), "PA5  3.3 V" if on else "PA5  0 V", 30, GREEN if on else DIM, "Bold", "lm", mono=True, k=kk2)
    led(d, x5, 700, on, 50, kk2)

def s_clock(d, t, dur):
    chrome(d, "STEP 6 · THE CLOCK", "Millions of times a second", "A crystal oscillator sets the pace. At 72 MHz, this little loop could run millions of times every second. That's why we need delay_ms().", t, dur)
    k = prog(t, 0.2, 0.8)
    text(d, (160, 330), "CLK", 34, CYAN, "Bold", mono=True, k=k)
    pts = []
    per = 80; off = (t * 160) % per
    y0, y1 = 420, 320
    for x in range(260, 1760, 2):
        ph = ((x - 260 + off) % per) < per / 2
        pts.append((x, y1 if ph else y0))
    if k > 0.3: d.line(pts, fill=CYAN, width=4)
    hz = int(72_000_000 * clamp((t - 1.0) / 4.0))
    text(d, (W // 2, 560), f"{hz:,} cycles/s", 72, AMBER, "Bold", "mm", mono=True, k=prog(t, 1.0, 1.4))
    text(d, (W // 2, 680), "1 cycle ≈ 13.9 ns", 36, DIM, "Medium", "mm", k=prog(t, 5.2, 5.8))

def s_recap(d, t, dur):
    chrome(d, "RECAP", "From text to light", "Compile, flash, reset, fetch, decode, execute, and a write to the right address. That's every program you'll ever run.", t, dur)
    st = [("Compile", CYAN), ("Flash", AMBER), ("Reset", RED), ("Fetch", PURPLE), ("Decode", PURPLE), ("Execute", PURPLE), ("I/O", GREEN)]
    x0, x1, y = 200, 1720, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.2), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(st):
        s = 0.5 + i * 0.55; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 6
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.6:
        on = int((t - 4.6) * 2) % 2 == 0
        led(d, W // 2, 680, on, 60, prog(t, 4.6, 5.2))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "What really happens", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "when you press a key?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_compile", s_compile, 10), ("03_flash", s_flash, 10),
          ("04_vector", s_vector, 11), ("05_cycle", s_cycle, 12), ("06_mmio", s_mmio, 11),
          ("07_clock", s_clock, 9), ("08_recap", s_recap, 9), ("09_end", s_end, 6)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep2/{name}.mp4", f"ep2/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

if __name__ == "__main__":
    os.makedirs("ep2", exist_ok=True)
    if sys.argv[1:] == ["preview"]:
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save("ep2/sheet.jpg", quality=85)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor() as ex: list(ex.map(render, *zip(*SCENES)))
