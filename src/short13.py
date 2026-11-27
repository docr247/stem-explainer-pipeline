import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep13 import ppg_trace, ppg_shape, heart, photon_path, LED_G, SKIN, SKIN2, BLOOD, PURPLE

def s_hook(d, t, dur):
    headline(d, ["Your watch reads", "your pulse with", "a green light"], t, TXT, 300, 72)
    k = prog(t, 0.4, 0.9)
    for g in range(4):
        rr = 70 + g * 45
        d.ellipse([W // 2 - rr, 800 - rr, W // 2 + rr, 800 + rr], outline=fade(mix(BG, LED_G, 0.5 - g * 0.09), k), width=6)
    d.ellipse([W // 2 - 50, 750, W // 2 + 50, 850], fill=fade(LED_G, k))
    if t > 1.6:
        ppg_trace(d, 110, 1050, 860, 120, t, 72, LED_G, prog(t, 1.6, 2.0), reveal=(t - 1.6) / 3.0, secs=4)
    caption(d, "No wires on your chest. So how?", t, 1260)

def s_blood(d, t, dur):
    headline(d, ["Blood soaks up", "green light"], t, LED_G, 270, 84)
    k = prog(t, 0.3, 0.7)
    p = ppg_shape((t * 60 / 60) % 1.0) / 1.15
    d.rectangle([110, 640, 970, 680], fill=fade(SKIN2, k))
    d.rectangle([110, 680, 970, 1060], fill=fade(SKIN, k))
    r = 34 + 20 * p
    d.rounded_rectangle([110, 900 - r, 970, 900 + r], int(r), fill=fade(mix(SKIN, BLOOD, 0.55 + 0.35 * p), k))
    box(d, (250, 520, 830, 630), PANEL, LINE, 24, 4, k)
    d.rectangle([370, 610, 430, 632], fill=fade(LED_G, k))
    d.rectangle([650, 610, 710, 632], fill=fade((40, 50, 80), k), outline=fade(CYAN, k), width=3)
    for i in range(5):
        if i > 3 * (1 - p) + 1: continue
        u = (t * 0.5 + i / 5) % 1.0
        photon_path(d, (400, 650), (680, 650), 820, u, LED_G, k, r=9)
    text(d, (W // 2, 1150), "each beat: more blood, less light back", 38, AMBER, "Bold", "mm", k=prog(t, 1.5, 2.0))
    caption(d, "Each heartbeat swells the tiny vessels, so less light comes back.", t, 1260)

def s_count(d, t, dur):
    headline(d, ["Count the", "bumps"], t, AMBER, 270, 84)
    k = prog(t, 0.3, 0.7)
    secs = 3.2
    ppg_trace(d, 110, 560, 860, 260, t, 75, LED_G, k, secs=secs)
    per = 0.8
    pk = [(0.18 + i) * per for i in range(4) if (0.18 + i) * per < secs]
    for i, s in enumerate(pk):
        kk = prog(t, 0.8 + i * 0.4, 1.1 + i * 0.4)
        x = 110 + s / secs * 860
        y = 820 - ppg_shape(0.18) / 1.15 * 260
        d.ellipse([x - 12, y - 12, x + 12, y + 12], outline=fade(AMBER, kk), width=5)
        if i > 0:
            xp = 110 + pk[i - 1] / secs * 860
            d.line([xp, 880, x, 880], fill=fade(AMBER, kk), width=4)
            text(d, ((xp + x) / 2, 920), "0.8 s", 34, AMBER, "Bold", "mm", mono=True, k=kk)
    text(d, (W // 2, 1060), "60 ÷ 0.8 = 75 bpm", 64, TXT, "Bold", "mm", mono=True, k=prog(t, 2.2, 2.7))
    caption(d, "Time the gaps between beats.", t, 1260)

def s_move(d, t, dur):
    headline(d, ["Running can", "fool it"], t, RED, 270, 84)
    k = prog(t, 0.3, 0.7)
    text(d, (110, 440), "light sensor", 34, RED, "Bold", "lm", k=k)
    ppg_trace(d, 110, 560, 860, 70, t, 150, RED, k, motion=0.9, mf=2.7, noise=0.25, secs=3)
    kk = prog(t, 1.2, 1.7)
    text(d, (110, 790), "accelerometer: arm swing", 34, PURPLE, "Bold", "lm", k=kk)
    pts = [(110 + px, 900 - 60 * math.sin(2 * math.pi * 2.7 * px / 860 * 3 + 0.7)) for px in range(0, 860, 3)]
    d.line(pts, fill=fade(PURPLE, kk), width=5)
    kj = prog(t, 2.4, 2.9)
    text(d, (110, 1040), "what's left: your pulse", 34, LED_G, "Bold", "lm", k=kj)
    ppg_trace(d, 110, 1080, 860, 100, t, 150, LED_G, kj, secs=3)
    caption(d, "A motion sensor helps it ignore your steps.", t, 1290)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "How a green light", 80, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "finds your heart", 80, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_blood, 7), ("s3", s_count, 7), ("s4", s_move, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Your smartwatch reads your heart rate with no wires on your chest. Just a tiny green light. So how does that work?",
 "s2": "Blood soaks up green light. Every heartbeat swells the tiny vessels in your wrist, so a little less light bounces back to the sensor.",
 "s3": "That makes one bump per beat. Time the gaps. Zero point eight seconds apart means seventy five beats per minute.",
 "s4": "But running shakes the signal. So a motion sensor feels your arm swing, and the watch ignores that rhythm to find your pulse.",
 "s5": "The whole story, step by step, is in the full video.",
}
OUTPUT = "ep13_short_green_light_pulse_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short13/{name}.mp4", f"short13/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short13", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short13/sheet.jpg", quality=85)
