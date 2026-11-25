import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep6 import led_lvl, pwm_wave, PURPLE

def s_hook(d, t, dur):
    headline(d, ["A pin can't do", "\"half\""], t, TXT, 300, 84)
    on = int(t * 1.2) % 2 == 0
    led_lvl(d, 540, 760, 1.0 if on else 0.0, 140, prog(t, 0.3, 0.8))
    text(d, (540, 1020), "3.3 V" if on else "0 V", 72, GREEN if on else DIM, "Bold", "mm", mono=True, k=prog(t, 0.3, 0.8))
    caption(d, "Only on, or off. So how does an LED dim?", t, 1250)

def s_fast(d, t, dur):
    headline(d, ["So it blinks.", "FAST."], t, AMBER, 280, 84)
    fast = t > 3.0
    lvl = 0.55 if fast else (1.0 if (t * 2) % 1 < 0.5 else 0.0)
    led_lvl(d, 540, 700, lvl, 130, prog(t, 0.2, 0.6))
    text(d, (540, 900), "1000× a second" if fast else "2× a second", 60, AMBER, "Bold", "mm", mono=True, k=prog(t, 0.4, 0.8))
    pwm_wave(d, 120, 980, 840, 100, 0.5, 30 if fast else 3, AMBER, prog(t, 0.4, 0.8), 1.0, 3 if fast else 5)
    caption(d, "Your eye averages it into a steady glow.", t, 1250)

def s_duty(d, t, dur):
    headline(d, ["Time ON =", "brightness"], t, CYAN, 270, 80)
    for i, duty in enumerate([0.1, 0.5, 0.9]):
        kk = prog(t, 0.6 + i * 0.8, 1.0 + i * 0.8)
        y = 470 + i * 220
        text(d, (90, y - 10), f"{int(duty * 100)}%", 52, AMBER, "Bold", "lm", mono=True, k=kk)
        pwm_wave(d, 90, y + 40, 680, 90, duty, 4, AMBER, kk)
        led_lvl(d, 900, y + 70, duty if kk > 0.5 else 0, 60, kk)
    caption(d, "That share of on-time is the duty cycle.", t, 1250)

def s_timer(d, t, dur):
    headline(d, ["A timer does it", "for free"], t, PURPLE, 270, 76)
    k = prog(t, 0.2, 0.6)
    ccr = 0.3 + 0.4 * clamp((t - 3.5) / 2.5)
    pts = []
    for i in range(3):
        a = 90 + i * 300
        pts += [(a, 760), (a + 299, 500), (a + 300, 760)]
    d.line(pts, fill=fade(CYAN, k), width=6)
    yc = 760 - 260 * ccr
    d.line([90, yc, 990, yc], fill=fade(AMBER, k), width=5)
    text(d, (100, yc - 32), "CCR", 34, AMBER, "Bold", "lm", mono=True, k=k)
    pwm_wave(d, 90, 860, 900, 100, ccr, 3, GREEN, k)
    text(d, (540, 1060), "TIM2->CCR1 = 250;", 48, TXT, "Bold", "mm", mono=True, k=prog(t, 1.5, 2.0))
    caption(d, "Count up. Compare. Flip the pin.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "How PWM", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "really works", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_fast, 7), ("s3", s_duty, 8), ("s4", s_timer, 8), ("s5", s_cta, 5)]

# Narration per scene (read by narrate.py) and the final file name.
NARRATION = {
 's1': "A microcontroller pin can't do half. It's either on, or off. So how does an LED dim?",
 's2': 'It blinks. Fast. A thousand times a second, and your eye averages it into a steady glow.',
 's3': "The more time it spends on, the brighter it looks. That's called the duty cycle.",
 's4': 'And a hardware timer does it for free. Count up, compare, flip the pin. One register sets the brightness.',
 's5': 'How P W M really works is in the full video.',
}
OUTPUT = 'ep6_short_pin_cant_do_half_narrated.mp4'

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short6/{name}.mp4", f"short6/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short6", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short6/sheet.jpg", quality=85)
