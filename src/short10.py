import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep10 import wave, router, phone, dot, PURPLE, BLUE

def s_hook(d, t, dur):
    headline(d, ["Your Wi-Fi wiggles", "2.4 billion", "times a second"], t, TXT, 300, 76)
    k = prog(t, 0.4, 0.9)
    wave(d, 90, 990, 820, 110, CYAN, k, cyc=7, t=t, speed=1.2, width=7)
    caption(d, "So where are the bits?", t, 1150)

def s_change(d, t, dur):
    headline(d, ["Bits change", "the wave"], t, AMBER, 270, 80)
    bits = "1011"
    rows = [("amplitude", AMBER, dict(ampf=lambda u: 1.0 if bits[min(3, int(u * 4))] == "1" else 0.3)),
            ("frequency", PURPLE, dict(freqf=lambda u: 1.5 if bits[min(3, int(u * 4))] == "1" else 0.7)),
            ("phase", GREEN, dict(phasef=lambda u: 0.0 if bits[min(3, int(u * 4))] == "1" else math.pi))]
    for i, (n, c, kw) in enumerate(rows):
        kk = prog(t, 0.6 + i * 0.9, 1.1 + i * 0.9)
        y = 560 + i * 230
        text(d, (90, y - 90), n, 40, c, "Bold", "lm", k=kk)
        wave(d, 90, 990, y, 60, c, kk, cyc=8, width=6, **kw)
    caption(d, "Its size, its speed, or its timing.", t, 1250)

def s_points(d, t, dur):
    headline(d, ["16 points =", "4 bits each"], t, CYAN, 270, 80)
    k = prog(t, 0.2, 0.6)
    cx, cy, s = 540, 760, 110
    d.line([cx - 300, cy, cx + 300, cy], fill=fade(LINE, k), width=3)
    d.line([cx, cy - 300, cx, cy + 300], fill=fade(LINE, k), width=3)
    for i, a in enumerate([-3, -1, 1, 3]):
        for j, b in enumerate([-3, -1, 1, 3]):
            hot = (i, j) == (3, 2) and t > 2.6
            dot(d, cx + a * s * 0.8, cy - b * s * 0.8, 26 if hot else 18, AMBER if hot else CYAN,
                prog(t, 0.5 + (i * 4 + j) * 0.08, 0.9 + (i * 4 + j) * 0.08))
    if t > 2.6: text(d, (cx + 3 * s * 0.8, cy - s * 0.8 - 60), "1011", 52, AMBER, "Bold", "mm", mono=True, k=prog(t, 2.6, 3.1))
    caption(d, "Amplitude and phase, changed together.", t, 1250)

def s_hop(d, t, dur):
    headline(d, ["Bluetooth hops", "1,600 times", "a second"], t, BLUE, 270, 76)
    import random
    rnd = random.Random(4)
    x0, x1, y0, y1 = 110, 970, 560, 1150
    d.rectangle([x0, y0, x1, y1], fill=(8, 12, 24), outline=LINE, width=3)
    n = int(clamp((t - 0.6) / 3.5) * 24)
    prev = None
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / 24
        y = y1 - (rnd.randrange(79) + 0.5) * (y1 - y0) / 79
        d.rectangle([x - 12, y - 8, x + 12, y + 8], fill=BLUE)
        if prev: d.line([prev, (x, y)], fill=mix(BG, BLUE, 0.4), width=3)
        prev = (x, y)
    text(d, (x0, y1 + 40), "79 channels (Classic Bluetooth)", 34, DIM, "Medium", "lm")
    caption(d, "A pattern both sides know.", t, 1300)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "How Wi-Fi and", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Bluetooth send bits", 76, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_change, 8), ("s3", s_points, 7), ("s4", s_hop, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Your Wi-Fi signal wiggles about two point four billion times every second. So where are the bits?",
 "s2": "The radio changes the wave. Its size, its frequency, or its timing, called phase. Each change means something.",
 "s3": "Wi-Fi changes size and phase together. Sixteen possible points means every symbol carries four bits.",
 "s4": "Classic Bluetooth does something else. It hops between seventy nine channels, sixteen hundred times a second.",
 "s5": "How Wi-Fi and Bluetooth really work is in the full video.",
}
OUTPUT = "ep10_short_wifi_wiggles_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short10/{name}.mp4", f"short10/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short10", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short10/sheet.jpg", quality=85)
