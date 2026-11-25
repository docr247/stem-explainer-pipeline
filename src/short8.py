import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep8 import comparator, sig, bits, PURPLE

VREF = 3.3

def s_hook(d, t, dur):
    headline(d, ["Your chip only", "speaks 0s and 1s."], t, TXT, 300, 80)
    k = prog(t, 0.4, 0.9)
    x0, y0, w, h = 110, 560, 820, 420
    box(d, (x0 - 20, y0 - 20, x0 + w + 20, y0 + h + 20), PANEL, LINE, 16, 2, k)
    n = int(clamp((t - 0.6) / 2.5) * 200)
    pts = [(x0 + w * i / 200, y0 + h - sig(i / 200) / VREF * h) for i in range(n)]
    if len(pts) > 1: d.line(pts, fill=AMBER, width=6)
    if t > 3.0: text(d, (540, 1100), "how many volts?", 50, AMBER, "Bold", "mm", mono=True, k=prog(t, 3.0, 3.5))
    caption(d, "So how does it measure anything?", t, 1250)

def s_comp(d, t, dur):
    headline(d, ["It asks yes/no", "questions"], t, CYAN, 270, 76)
    k = prog(t, 0.2, 0.6)
    pin, nin, o = comparator(d, 400, 760, 140, k, out=t > 1.5)
    text(d, (380, pin[1]), "input 2.2 V", 36, AMBER, "Bold", "rm", k=k)
    text(d, (380, nin[1]), "test 1.65 V", 36, PURPLE, "Bold", "rm", k=k)
    if t > 1.5: text(d, (o[0] + 80, o[1]), "YES", 56, GREEN, "Bold", "lm", k=prog(t, 1.5, 1.9))
    caption(d, "A comparator: is the input higher than this test voltage?", t, 1250)

def s_search(d, t, dur):
    headline(d, ["Like guessing", "a number"], t, AMBER, 270, 80)
    k = prog(t, 0.2, 0.6)
    rows = [("> 1.65 V?", "yes", "1", GREEN), ("> 2.48 V?", "no", "0", RED), ("> 2.06 V?", "yes", "1", GREEN)]
    for i, (q, a, b, c) in enumerate(rows):
        kk = prog(t, 0.6 + i * 1.0, 1.0 + i * 1.0)
        y = 520 + i * 160
        box(d, (90, y, 920, y + 130), PANEL, c, 14, 4, kk)
        text(d, (130, y + 65), q, 46, TXT, "Bold", "lm", mono=True, k=kk)
        text(d, (680, y + 65), a, 46, c, "Bold", "lm", k=kk)
        text(d, (860, y + 65), b, 56, c, "Bold", "mm", mono=True, k=kk)
    caption(d, "Each answer halves the range and gives one bit.", t, 1250)

def s_twelve(d, t, dur):
    headline(d, ["12 questions =", "4,096 levels"], t, GREEN, 270, 80)
    k = prog(t, 0.2, 0.6)
    nb = int(clamp((t - 0.6) / 3.0) * 12 + 0.999) if t > 0.6 else 0
    s = "101010101010"
    bits(d, 105, 560, s[:6], 140, k, CYAN, known=min(nb, 6))
    bits(d, 105, 720, s[6:], 140, k, CYAN, known=max(0, nb - 6))
    if nb == 12:
        text(d, (540, 960), "= 2730  →  2.2 V", 56, AMBER, "Bold", "mm", mono=True, k=prog(t, 3.8, 4.3))
        text(d, (540, 1040), "example, 3.3 V reference", 32, DIM, "Medium", "mm", k=prog(t, 3.8, 4.3))
    caption(d, "A SAR converter, inside most microcontrollers.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "How an ADC", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "really works", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_comp, 7), ("s3", s_search, 8), ("s4", s_twelve, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Your microcontroller only understands ones and zeros. So how does it measure a smooth voltage, like two point two volts?",
 "s2": "It asks yes or no questions. A comparator checks: is the input higher than this test voltage?",
 "s3": "Higher than one point six five? Yes, that's a one. Higher than two point four eight? No, a zero. Each answer halves the range.",
 "s4": "Twelve questions pick one of four thousand and ninety six levels. That's a SAR converter, inside most microcontrollers.",
 "s5": "How an A D C really works is in the full video.",
}
OUTPUT = "ep8_short_twelve_questions_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short8/{name}.mp4", f"short8/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short8", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short8/sheet.jpg", quality=85)
