import os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, prog, mix, fade, text, box, arrow,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN)
from short import headline, caption, W, H, FPS
from ep3 import keycap, REPORT

def s_hook(d, t, dur):
    headline(d, ["Your keyboard", "never sends", "the letter A."], t, y=300)
    keycap(d, 540, 860, 320, "A", 1.6 < t < 2.1, prog(t, 0.5, 1.0))
    caption(d, "So what does it actually send?", t, 1250)

def s_matrix(d, t, dur):
    headline(d, ["It scans a", "grid of wires"], t, CYAN, 260, 70)
    k = prog(t, 0.2, 0.7)
    x0, y0, s = 200, 480, 136
    col = int(t * 4) % 5 if t > 0.8 else -1
    for c in range(5):
        x = x0 + c * s
        d.line([x, y0 - 40, x, y0 + 4 * s + 40], fill=fade(AMBER if c == col else LINE, k), width=6 if c == col else 4)
    for r in range(5):
        y = y0 + r * s
        d.line([x0 - 40, y, x0 + 4 * s + 40, y], fill=fade(LINE, k), width=4)
        for c in range(5):
            on = (r, c) == (2, 3) and t > 2.5
            x = x0 + c * s
            d.rectangle([x - 22, y - 22, x + 22, y + 22], fill=fade(mix(BG, GREEN, 0.9) if on else PANEL, k),
                        outline=fade(GREEN if on else LINE, k), width=3)
    caption(d, "One column at a time, hundreds of times a second.", t, 1250)

def s_report(d, t, dur):
    headline(d, ["It sends a", "number: 0x04"], t, AMBER, 260, 70)
    for i, b in enumerate(REPORT):
        r, c = divmod(i, 4)
        kk = prog(t, 0.8 + i * 0.2, 1.1 + i * 0.2)
        x, y = 130 + c * 210, 520 + r * 230
        hot = i == 2
        box(d, (x, y, x + 180, y + 180), mix(BG, AMBER, 0.25) if hot else PANEL, AMBER if hot else LINE, 16, 5 if hot else 2, kk)
        text(d, (x + 90, y + 90), b, 72, AMBER if hot else TXT, mono=True, anchor="mm", k=kk)
    text(d, (540, 1020), "8-byte HID report", 40, DIM, "Medium", "mm", k=prog(t, 2.6, 3.1))
    caption(d, "Code 4 just means: the key in this position.", t, 1250)

def s_layout(d, t, dur):
    headline(d, ["Your OS decides", "what it means"], t, CYAN, 260, 70)
    k = prog(t, 0.3, 0.8)
    text(d, (540, 500), "0x04", 96, AMBER, mono=True, anchor="mm", k=k)
    arrow(d, (460, 570), (320, 690), DIM, 6, prog(t, 1.0, 1.4))
    arrow(d, (620, 570), (760, 690), DIM, 6, prog(t, 1.0, 1.4))
    k2 = prog(t, 1.5, 2.0)
    keycap(d, 290, 820, 200, "a", False, k2, GREEN)
    text(d, (290, 980), "QWERTY", 44, GREEN, "Bold", "mm", k=k2)
    k3 = prog(t, 2.3, 2.8)
    keycap(d, 790, 820, 200, "q", False, k3, CYAN)
    text(d, (790, 980), "AZERTY", 44, CYAN, "Bold", "mm", k=k3)
    caption(d, "Same key, different letter. It's all in the layout.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "From fingertip", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "to pixel", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_matrix, 7), ("s3", s_report, 8), ("s4", s_layout, 8), ("s5", s_cta, 5)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short3/{name}.mp4", f"short3/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short3", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short3/sheet.jpg", quality=85)
