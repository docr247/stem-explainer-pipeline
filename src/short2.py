import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep2 import led, ASM

PURPLE = (180, 140, 255)

def s_hook(d, t, dur):
    headline(d, ["This LED is", "controlled by", "ONE address."], t, y=300)
    box(d, (110, 640, 970, 740), (6, 10, 20), LINE, 14, 3, prog(t, 0.3, 0.8))
    text(d, (540, 690), "GPIOA->ODR ^= LED;", 46, TXT, mono=True, anchor="mm", k=prog(t, 0.3, 0.8))
    on = t > 1.4 and int((t - 1.4) * 2) % 2 == 0
    led(d, 540, 960, on, 110, prog(t, 0.8, 1.3))
    caption(d, "Here's how your code flips a real pin.", t, 1200)

def s_compile(d, t, dur):
    headline(d, ["Your C becomes", "numbers"], t, CYAN, 260, 70)
    k = prog(t, 0.3, 0.8)
    box(d, (150, 440, 930, 530), (6, 10, 20), LINE, 14, 3, k)
    text(d, (540, 485), "GPIOA->ODR ^= LED;", 42, TXT, mono=True, anchor="mm", k=k)
    arrow(d, (540, 550), (540, 630), DIM, 6, prog(t, 0.9, 1.3))
    n = int(clamp((t - 1.3) / 3.0) * len(ASM) + 0.999)
    for i, (a, h) in enumerate(ASM[:n]):
        y = 660 + i * 82
        text(d, (170, y), a, 34, CYAN, mono=True)
        text(d, (910, y), "0x" + h, 40, AMBER, mono=True, anchor="ra")
    caption(d, "Every instruction is just a number in flash.", t, 1180)

def s_cycle(d, t, dur):
    headline(d, ["Fetch. Decode.", "Execute."], t, TXT, 260, 74)
    phase = ((t - 0.8) / 1.2) % 1 if t > 0.8 else -1
    for i, s in enumerate(["FETCH", "DECODE", "EXECUTE"]):
        y = 460 + i * 170
        act = t > 0.8 and int(phase * 3) == i
        box(d, (260, y, 820, y + 120), mix(BG, CYAN, 0.35) if act else PANEL, CYAN if act else LINE, 16, 4, prog(t, 0.2 + i * .15, 0.6 + i * .15))
        text(d, (540, y + 60), s, 52, TXT, "Bold", "mm", k=prog(t, 0.2 + i * .15, 0.6 + i * .15))
        if i < 2: arrow(d, (540, y + 124), (540, y + 166), DIM, 4)
    hz = int(72_000_000 * clamp((t - 2.0) / 3.5))
    text(d, (540, 1040), f"{hz:,} / s", 64, AMBER, "Bold", "mm", mono=True, k=prog(t, 2.0, 2.4))
    caption(d, "Up to 72 million times a second.", t, 1180)

def s_mmio(d, t, dur):
    headline(d, ["The secret:", "it's not memory"], t, CYAN, 260, 70)
    s = "0x48000014"
    n = int(len(s) * clamp((t - 0.5) / 1.0))
    text(d, (540, 470), s[:n], 92, AMBER, mono=True, anchor="mm")
    kk = prog(t, 1.6, 2.2)
    for b in range(8):
        x = 140 + (7 - b) * 102
        bit = 1 if (b == 5 and t > 2.8) else 0
        d.rectangle([x, 580, x + 90, 680], fill=fade(mix(BG, GREEN if bit else LINE, 0.8 if bit else 0.4), kk))
        text(d, (x + 45, 630), str(bit), 48, TXT, mono=True, anchor="mm", k=kk)
        text(d, (x + 45, 712), str(b), 28, DIM, "Medium", "mm", k=kk)
    x5 = 140 + 2 * 102 + 45
    on = t > 3.6
    k2 = prog(t, 3.0, 3.5)
    d.line([x5, 740, x5, 880], fill=fade(GREEN if on else LINE, k2), width=8)
    text(d, (x5 + 30, 820), "PA5 → 3.3 V" if on else "PA5", 40, GREEN if on else DIM, "Bold", "lm", mono=True, k=k2)
    led(d, x5, 980, on, 70, k2)
    caption(d, "That address is wired straight to the pin.", t, 1180)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "From code", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "to light", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_compile, 8), ("s3", s_cycle, 8), ("s4", s_mmio, 9), ("s5", s_cta, 5)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short2/{name}.mp4", f"short2/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short2", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short2/sheet.jpg", quality=85)
