import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep7 import button, stack_regs, PURPLE

def s_hook(d, t, dur):
    headline(d, ["Your CPU never", "checks this", "button."], t, TXT, 300, 80)
    button(d, 540, 860, 150, 2.0 < t < 2.6, prog(t, 0.4, 0.9))
    caption(d, "Yet it reacts instantly. How?", t, 1250)

def s_tap(d, t, dur):
    headline(d, ["The button taps it", "on the shoulder"], t, RED, 270, 68)
    k = prog(t, 0.2, 0.6)
    button(d, 540, 520, 80, 1.0 < t < 1.6, k)
    box(d, (340, 700, 740, 820), PANEL, PURPLE, 14, 4, k)
    text(d, (540, 760), "NVIC", 52, TXT, "Bold", "mm", k=k)
    chip(d, 340, 960, 400, 160, "CPU", "", CYAN, k, pins=False)
    d.line([540, 615, 540, 700], fill=RED if t > 1.0 else LINE, width=8)
    d.line([540, 820, 540, 960], fill=RED if t > 1.8 else LINE, width=8)
    if t > 1.8: text(d, (580, 890), "IRQ!", 48, RED, "Bold", "lm", mono=True)
    caption(d, "An interrupt request. Stop what you're doing.", t, 1250)

def s_steps(d, t, dur):
    headline(d, ["Save. Jump.", "Handle. Return."], t, AMBER, 270, 76)
    k = prog(t, 0.2, 0.6)
    stack_regs(d, 120, 1060, int(clamp((t - 0.6) / 2.4) * 8 + 0.999) if t > 0.6 else 0, k)
    steps = [("Save 8 registers", AMBER), ("Jump to handler", PURPLE), ("Clear flag, set note", RED), ("Pop back, carry on", CYAN)]
    for i, (s, c) in enumerate(steps):
        kk = prog(t, 0.8 + i * 0.8, 1.2 + i * 0.8)
        y = 500 + i * 150
        box(d, (400, y, 960, y + 120), PANEL, c, 14, 4, kk)
        text(d, (430, y + 60), s, 40, TXT, "Bold", "lm", k=kk)
    caption(d, "All in hardware, automatically.", t, 1250)

def s_fast(d, t, dur):
    headline(d, ["In just", "12 clock cycles"], t, CYAN, 270, 80)
    k = prog(t, 0.3, 0.8)
    n = int(12 * clamp((t - 0.8) / 2.5))
    for i in range(12):
        x = 110 + i * 72
        d.rectangle([x, 560, x + 56, 660], fill=fade(mix(BG, CYAN, 0.8) if i < n else PANEL, k), outline=fade(LINE, k), width=2)
    text(d, (540, 800), "≈ 0.17 µs at 72 MHz", 60, AMBER, "Bold", "mm", mono=True, k=prog(t, 3.4, 3.9))
    text(d, (540, 900), "(ARM Cortex-M3/M4)", 36, DIM, "Medium", "mm", k=prog(t, 3.4, 3.9))
    caption(d, "Faster than you could ever press it twice.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "How interrupts", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "really work", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_tap, 7), ("s3", s_steps, 8), ("s4", s_fast, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Your CPU never checks this button. Yet the moment you press it, the CPU reacts. How?",
 "s2": "The button taps it on the shoulder. It sends an interrupt request through the interrupt controller: stop what you're doing.",
 "s3": "The CPU saves eight registers, jumps to the handler, deals with the button, then pops everything back and carries on.",
 "s4": "On an ARM Cortex M four, that takes just twelve clock cycles. At seventy two megahertz, that's under a fifth of a microsecond.",
 "s5": "How interrupts really work is in the full video.",
}
OUTPUT = "ep7_short_cpu_never_checks_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short7/{name}.mp4", f"short7/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short7", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short7/sheet.jpg", quality=85)
