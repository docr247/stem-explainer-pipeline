import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep11 import car, ecu, lock, PURPLE, BRAKE, DISP, LOG

def s_hook(d, t, dur):
    headline(d, ["Your brakes can't", "wait for the", "dashboard"], t, TXT, 300, 76)
    k = prog(t, 0.4, 0.9)
    car(d, 140, 960, 800, k)
    if t > 2.0:
        cx = 140 + 800 * 0.78
        d.ellipse([cx - 110, 960 - 110, cx + 110, 960 + 110], outline=fade(RED, prog(t, 2.0, 2.4)), width=8)
    caption(d, "So who decides what runs first?", t, 1250)

def s_loop(d, t, dur):
    headline(d, ["One big loop", "makes it wait"], t, AMBER, 270, 80)
    k = prog(t, 0.2, 0.6)
    seg = [("brakes", BRAKE, 160), ("display", DISP, 300), ("log", LOG, 340)]
    x = 140
    for i, (n, c, w) in enumerate(seg):
        kk = prog(t, 0.5 + i * 0.5, 0.9 + i * 0.5)
        d.rectangle([x, 660, x + w, 780], fill=fade(mix(BG, c, 0.75), kk))
        text(d, (x + w / 2, 720), n, 40, BG, "Bold", "mm", k=kk)
        x += w
    if t > 2.2:
        kk = prog(t, 2.2, 2.6)
        arrow(d, (330, 570), (330, 650), RED, 7, kk)
        text(d, (330, 540), "wheel locks", 40, RED, "Bold", "mm", k=kk)
        d.line([330, 840, 940, 840], fill=fade(AMBER, kk), width=6)
        text(d, (635, 900), "waiting...", 48, AMBER, "Bold", "mm", k=kk)
    caption(d, "The brakes wait for the screen and the log.", t, 1250)

def s_prio(d, t, dur):
    headline(d, ["An RTOS runs", "the most urgent", "task first"], t, GREEN, 270, 76)
    rows = [("brakes", BRAKE, "HIGH"), ("display", DISP, "MED"), ("log", LOG, "LOW")]
    for i, (n, c, p) in enumerate(rows):
        kk = prog(t, 0.6 + i * 0.4, 1.0 + i * 0.4)
        y = 600 + i * 170
        box(d, (120, y, 960, y + 130), mix(BG, c, 0.25) if i == 0 and t > 2.6 else PANEL, c, 16, 4, kk)
        text(d, (160, y + 65), n, 52, c, "Bold", "lm", k=kk)
        text(d, (920, y + 65), p, 44, c, "Bold", "rm", k=kk)
    caption(d, "The instant brakes need the CPU, they get it.", t, 1250)

def s_mars(d, t, dur):
    headline(d, ["A lock bug once", "reset a Mars lander"], t, PURPLE, 270, 72)
    k = prog(t, 0.3, 0.8)
    lock(d, 540, 760, 110, PURPLE, k)
    text(d, (540, 1000), "priority inversion · 1997", 44, AMBER, "Bold", "mm", k=prog(t, 1.4, 1.9))
    caption(d, "The fix was sent all the way from Earth.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "Why your car", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "needs an RTOS", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_loop, 8), ("s3", s_prio, 7), ("s4", s_mars, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "When a wheel starts to lock, your car's brake computer can't wait for the dashboard. So who decides what runs first?",
 "s2": "In one big loop, the brake code waits its turn, behind the display, and a slow log write.",
 "s3": "A real-time operating system gives each task a priority. The moment the brake task needs the CPU, it gets it.",
 "s4": "Get the locks wrong, and you get priority inversion. In nineteen ninety seven, it kept resetting NASA's Mars Pathfinder lander.",
 "s5": "Why your car needs an R T O S is in the full video.",
}
OUTPUT = "ep11_short_brakes_cant_wait_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short11/{name}.mp4", f"short11/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short11", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short11/sheet.jpg", quality=85)
