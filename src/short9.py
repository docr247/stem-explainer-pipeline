import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep9 import finger, pen, cross, phone, heat_col, PURPLE

def s_hook(d, t, dur):
    headline(d, ["Your phone can't", "feel a pen."], t, TXT, 300, 84)
    k = prog(t, 0.3, 0.8)
    phone(d, 330, 520, 420, 640, k)
    pen(d, 450, 700 + 40 * clamp((t - 0.8) / 0.6), k, 140)
    if t > 1.5:
        cross(d, 450, 900, 34, RED, prog(t, 1.5, 1.9))
    finger(d, 640, 700 + 40 * clamp((t - 2.0) / 0.6), prog(t, 1.8, 2.2), 90, 160)
    if t > 2.7:
        kk = prog(t, 2.7, 3.1)
        d.ellipse([640 - 60, 740 - 60, 640 + 60, 740 + 60], outline=fade(GREEN, kk), width=6)
    caption(d, "So what is it actually sensing?", t, 1250)

GX, GY, GS, N = 140, 520, 800, 6
def sgrid(d, k, hi_row=None):
    box(d, (GX - 20, GY - 20, GX + GS + 20, GY + GS * 0.6 + 20), (8, 12, 24), LINE, 16, 2, k)
    for r in range(N):
        y = GY + (r + 0.5) * GS * 0.6 / N
        d.line([GX, y, GX + GS, y], fill=fade(CYAN if r == hi_row else mix(BG, CYAN, 0.6), k), width=10 if r == hi_row else 6)
    for c in range(8):
        x = GX + (c + 0.5) * GS / 8
        d.line([x, GY, x, GY + GS * 0.6], fill=fade(mix(BG, PURPLE, 0.7), k), width=6)

def s_grid(d, t, dur):
    headline(d, ["An invisible", "grid of wires"], t, CYAN, 280, 80)
    sgrid(d, prog(t, 0.3, 0.9))
    text(d, (GX, GY + GS * 0.6 + 70), "rows", 44, CYAN, "Bold", "lm", k=prog(t, 1.0, 1.4))
    text(d, (GX + GS, GY + GS * 0.6 + 70), "columns", 44, PURPLE, "Bold", "rm", k=prog(t, 1.4, 1.8))
    caption(d, "See-through rows and columns sit under the glass.", t, 1250)

def s_steal(d, t, dur):
    headline(d, ["Your finger steals", "a little field"], t, AMBER, 280, 76)
    k = prog(t, 0.2, 0.6)
    d.rectangle([110, 880, 970, 940], fill=fade(PANEL, k), outline=fade(LINE, k), width=2)
    d.rectangle([200, 960, 480, 980], fill=fade(CYAN, k))
    d.rectangle([600, 960, 880, 980], fill=fade(PURPLE, k))
    text(d, (340, 1030), "send", 40, CYAN, "Bold", "mm", k=k)
    text(d, (740, 1030), "listen", 40, PURPLE, "Bold", "mm", k=k)
    near = prog(t, 1.0, 2.6)
    fy = 560 + 316 * near
    finger(d, 540, fy, k, 110, 200)
    for i in range(3):
        a, b = 440 - i * 70, 640 + i * 70
        hgt = 60 + i * 50
        if near > 0.7 and i >= 1:
            d.line([a, 960, a + 40, 880, 520, fy + 2], fill=fade(AMBER, k), width=4)
        else:
            d.arc([a, 960 - hgt, b, 960 + hgt], 180, 360, fill=fade(mix(BG, AMBER, 0.7), k), width=4)
    if near > 0.9:
        text(d, (540, 1130), "less signal arrives", 46, RED, "Bold", "mm", k=prog(t, 2.6, 3.0))
    caption(d, "At a crossing, your finger draws away part of the signal.", t, 1250)

def s_scan(d, t, dur):
    headline(d, ["Scan every", "crossing"], t, GREEN, 280, 84)
    k = prog(t, 0.2, 0.6)
    rows = clamp((t - 0.6) / 2.5) * N
    cur = min(N - 1, int(rows))
    if rows < N:
        sgrid(d, k, cur)
    else:
        box(d, (GX - 20, GY - 20, GX + GS + 20, GY + GS * 0.6 + 20), (8, 12, 24), LINE, 16, 2, k)
    cw, ch = GS / 8, GS * 0.6 / N
    for r in range(N):
        for c in range(8):
            if r <= int(rows) and (rows >= N or r <= cur):
                v = 1.3 * math.exp(-((r - 2.5) ** 2 + (c - 4.5) ** 2) / (2 * 0.8 ** 2))
                if rows >= N:
                    d.rounded_rectangle([GX + c * cw + 4, GY + r * ch + 4, GX + (c + 1) * cw - 4, GY + (r + 1) * ch - 4], 8, fill=heat_col(v))
                else:
                    x, y = GX + (c + 0.5) * cw, GY + (r + 0.5) * ch
                    rr = 10 + 16 * v
                    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=heat_col(0.2 + v))
    if rows >= N:
        text(d, (540, GY + GS * 0.6 + 80), "your touch", 50, AMBER, "Bold", "mm", k=prog(t, 3.2, 3.6))
    caption(d, "Many times a second. The dip is your finger.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "How touchscreens", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "really work", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_grid, 6), ("s3", s_steal, 7), ("s4", s_scan, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Tap your phone with a plastic pen, and nothing happens. Use your finger, and it works instantly. So what is the screen actually sensing?",
 "s2": "Under the glass sits an invisible grid: see-through rows, and see-through columns.",
 "s3": "The controller sends a signal along one line, and listens on a line that crosses it. Your finger is a conductor, so it draws away part of that signal.",
 "s4": "It checks every crossing, many times a second. Wherever the signal dips, that's your finger. A plastic pen doesn't change it at all.",
 "s5": "Resistive versus capacitive touchscreens, in the full video.",
}
OUTPUT = "ep9_short_cant_feel_a_pen_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short9/{name}.mp4", f"short9/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short9", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short9/sheet.jpg", quality=85)
