import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep12 import gantry, switch, stepper, counter, pulse_train, PURPLE

def s_hook(d, t, dur):
    headline(d, ["Most 3D printers", "never check where", "the nozzle is"], t, TXT, 300, 72)
    k = prog(t, 0.4, 0.9)
    gantry(d, 100, 980, 780, 0.5 + 0.4 * math.sin(t * 1.4), k)
    if t > 1.8:
        text(d, (W // 2, 960), "?", 140, AMBER, "Bold", "mm", k=prog(t, 1.8, 2.3))
    caption(d, "So how does it know where it is?", t, 1250)

def s_count(d, t, dur):
    headline(d, ["It counts", "pulses"], t, AMBER, 270, 84)
    k = prog(t, 0.3, 0.7)
    pulse_train(d, 120, 560, 9, 30, 90, 0.6, t, AMBER, k, gap=88)
    n = int(clamp((t - 1.0) / 3.0) * 80)
    counter(d, 120, 760, "pulses", f"{n}", AMBER, prog(t, 0.8, 1.2), 820)
    counter(d, 120, 900, "moved", f"{n / 80:.2f} mm", CYAN, prog(t, 1.2, 1.6), 820)
    text(d, (W // 2, 1080), "(example: 80 pulses per mm)", 36, DIM, "Medium", "mm", k=prog(t, 1.6, 2.0))
    caption(d, "Every pulse moves the motor one tiny step.", t, 1250)

def s_home(d, t, dur):
    headline(d, ["At switch-on,", "it finds zero"], t, GREEN, 270, 80)
    k = prog(t, 0.3, 0.7)
    hx = 0.7 - 0.7 * prog(t, 0.8, 2.6)
    gantry(d, 300, 980, 720, hx, k)
    pressed = t > 2.5
    switch(d, 210, 700, pressed, k)
    if pressed:
        text(d, (200, 580), "click!", 56, GREEN, "Bold", "mm", k=prog(t, 2.5, 2.8))
        counter(d, 120, 900, "position", "0.0 mm", GREEN, prog(t, 2.7, 3.1), 820)
    caption(d, "It drives into a switch. Click: that's zero.", t, 1250)

def s_skip(d, t, dur):
    headline(d, ["Skip one step and", "it never notices"], t, RED, 270, 74)
    bx, by, lh = 260, 1160, 40
    n = int(clamp(t / 4.0) * 14)
    for i in range(n):
        off = 100 if i >= 7 else 0
        c = RED if i >= 7 else CYAN
        d.rectangle([bx + off, by - (i + 1) * lh, bx + 460 + off, by - i * lh - 6], fill=mix(BG, c, 0.7))
    if n > 8:
        text(d, (W // 2, 520), "layer shift", 60, RED, "Bold", "mm", k=prog(t, 2.4, 2.8))
    caption(d, "Big machines add sensors to check.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "From one coil to", 80, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "a smart machine", 80, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_count, 8), ("s3", s_home, 7), ("s4", s_skip, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Most hobby 3 D printers never actually check where their nozzle is. So how do they know where it is?",
 "s2": "They count. Every pulse sent to the motor moves it one tiny step. On a typical setup, eighty pulses move the head one millimetre.",
 "s3": "At switch-on, the count means nothing. So the printer drives each axis into a little switch. Click. That's zero.",
 "s4": "But if the motor skips a step, the count is wrong, and the printer never notices. That's a layer shift. Big machines add sensors to check.",
 "s5": "The whole story, from one coil of wire, is in the full video.",
}
OUTPUT = "ep12_short_printer_counts_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short12/{name}.mp4", f"short12/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short12", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short12/sheet.jpg", quality=85)
