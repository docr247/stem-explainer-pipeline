import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
OFF = (36, 60, 48)

def led_lvl(d, cx, cy, lvl, r=60, k=1.0):
    lvl = clamp(lvl)
    if lvl > 0.02:
        for g in range(6):
            rr = r + 10 + g * 14
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=mix(BG, GREEN, (0.32 - g * 0.05) * lvl * k), width=7)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fade(mix(OFF, GREEN, lvl), k), outline=fade(LINE, k), width=3)

def pwm_wave(d, x0, y0, w, h, duty, periods, col, k=1.0, reveal=1.0, width=5):
    pts = []
    pw = w / periods
    xe = x0 + w * reveal
    for i in range(periods):
        a = x0 + i * pw; b = a + pw * duty; c = a + pw
        for (px, py) in [(a, y0 + h), (a, y0), (b, y0), (b, y0 + h), (c, y0 + h)]:
            pts.append((min(px, xe), py))
    if len(pts) > 1: d.line(pts, fill=fade(col, k), width=width)

def s_hook(d, t, dur):
    chrome(d, "", "", "A microcontroller pin can only be fully on or fully off. So how does it make an LED glow at half brightness?", t, dur)
    lvl = 0.5 + 0.5 * math.sin((t - 1.0) * 1.6) if t > 1.0 else 1.0
    led_lvl(d, W // 2, 430, lvl, 120, prog(t, 0.2, 0.7))
    text(d, (W // 2, 660), f"{int(lvl * 100):3d}%", 60, GREEN, "Bold", "mm", mono=True, k=prog(t, 1.0, 1.5))

def s_digital(d, t, dur):
    chrome(d, "THE PROBLEM", "A pin is a switch", "A digital pin has exactly two settings: 3.3 volts, or zero. There's no setting for half-way.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 200, 340, 340, 260, "MCU", "GPIO pin", PURPLE, k)
    on = int(t * 0.8) % 2 == 0 if t > 1.0 else True
    d.line([540, 470, 900, 470], fill=fade(GREEN if on else LINE, k), width=8)
    led_lvl(d, 980, 470, 1.0 if on else 0.0, 70, k)
    for i, (lab, col, sel) in enumerate([("3.3 V", GREEN, on), ("0 V", DIM, not on), ("1.65 V ?", RED, False)]):
        kk = prog(t, 1.2 + i * 0.6, 1.6 + i * 0.6)
        y = 330 + i * 120
        box(d, (1260, y, 1640, y + 90), mix(BG, col, 0.25) if sel else PANEL, col, 14, 4 if sel else 2, kk)
        text(d, (1450, y + 45), lab, 40, col, "Bold", "mm", mono=True, k=kk)
    if t > 3.4:
        kk = prog(t, 3.4, 3.8)
        d.line([1270, 650, 1630, 580], fill=fade(RED, kk), width=6)

def s_blink(d, t, dur):
    chrome(d, "THE TRICK", "Blink faster than your eye", "So instead, it blinks. Once a second, you see the flicker. But speed it up to hundreds or thousands of times a second, and your eye just averages it into a steady glow.", t, dur)
    k = prog(t, 0.2, 0.7)
    stages = [(1.0, 1, "1 Hz"), (4.0, 8, "8 Hz"), (7.0, 1000, "1 kHz")]
    freq, lab = 1, "1 Hz"
    for st, f, l in stages:
        if t >= st: freq, lab = f, l
    if freq < 100:
        lvl = 1.0 if (t * freq) % 1 < 0.5 else 0.0
    else:
        lvl = 0.55
    led_lvl(d, 560, 470, lvl, 110, k)
    text(d, (560, 690), lab, 56, AMBER, "Bold", "mm", mono=True, k=k)
    periods = 2 if freq == 1 else (8 if freq == 8 else 40)
    pwm_wave(d, 900, 380, 840, 140, 0.5, periods, AMBER, k, 1.0, 4 if periods == 40 else 5)
    if t > 7.6:
        text(d, (1320, 620), "looks steady", 40, GREEN, "Bold", "mm", k=prog(t, 7.6, 8.1))

def s_duty(d, t, dur):
    chrome(d, "DUTY CYCLE", "Brightness = time on", "The trick is the duty cycle: the share of each cycle the pin spends on. On ten percent of the time, the LED looks dim. On ninety percent, it looks bright.", t, dur)
    for i, duty in enumerate([0.1, 0.5, 0.9]):
        kk = prog(t, 0.6 + i * 1.0, 1.1 + i * 1.0)
        y = 280 + i * 180
        text(d, (230, y + 55), f"{int(duty * 100)}%", 52, AMBER, "Bold", "mm", mono=True, k=kk)
        pwm_wave(d, 340, y + 10, 1000, 100, duty, 6, AMBER, kk, clamp((t - 0.6 - i * 1.0) / 1.2))
        led_lvl(d, 1560, y + 60, duty if kk > 0.5 else 0, 50, kk)
        avg_y = y + 10 + 100 * (1 - duty)
        if t > 4.5:
            d.line([340, avg_y, 1340, avg_y], fill=fade(GREEN, prog(t, 4.5, 5.0)), width=3)
    if t > 4.5:
        text(d, (840, 820 - 20), "green line = average voltage", 30, GREEN, "Bold", "mm", k=prog(t, 4.5, 5.0))

def s_timer(d, t, dur):
    chrome(d, "IN HARDWARE", "A counter and a compare", "The chip doesn't do this in code. A hardware timer counts up, over and over. While the count is below a compare value, the pin is high. Above it, the pin goes low. Move the compare value, and the brightness changes.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, w, periods = 300, 1300, 4
    pw = w / periods
    ccr = 0.3 + 0.4 * clamp((t - 5.0) / 3.0)
    rv = clamp((t - 0.8) / 3.5)
    text(d, (x0 - 30, 330), "CNT", 30, CYAN, "Bold", "rm", mono=True, k=k)
    pts = []
    for i in range(periods):
        a = x0 + i * pw
        pts += [(a, 480), (a + pw - 1, 280), (a + pw, 480)]
    xe = x0 + w * rv
    pts = [(min(px, xe), py if px <= xe else py) for px, py in pts]
    clipped = []
    for px, py in pts:
        if px <= xe: clipped.append((px, py))
    if len(clipped) > 1: d.line(clipped, fill=CYAN, width=5)
    yc = 480 - 200 * ccr
    d.line([x0, yc, x0 + w, yc], fill=fade(AMBER, k), width=4)
    text(d, (x0 + w + 20, yc), "CCR", 30, AMBER, "Bold", "lm", mono=True, k=k)
    text(d, (x0 + w + 20, 280), "ARR", 30, DIM, "Bold", "lm", mono=True, k=k)
    text(d, (x0 - 30, 620), "PIN", 30, GREEN, "Bold", "rm", mono=True, k=k)
    pwm_wave(d, x0, 570, w, 100, ccr, periods, GREEN, k, rv)
    if t > 5.0:
        text(d, (W // 2, 760), f"duty = CCR / ARR = {int(ccr * 100)}%", 36, AMBER, "Bold", "mm", mono=True, k=prog(t, 5.0, 5.4))

def s_code(d, t, dur):
    chrome(d, "IN CODE", "One register, any brightness", "Set the timer up once. With a period of one thousand counts, writing two hundred and fifty to the compare register gives you twenty-five percent brightness. The hardware does the rest, while your code does something else.", t, dur)
    k = prog(t, 0.2, 0.7)
    lines = ["// 72 MHz / 72 = 1 MHz tick", "TIM2->PSC  = 71;", "TIM2->ARR  = 999;   // 1 kHz PWM", "",
             "TIM2->CCR1 = 250;   // 25%"]
    box(d, (160, 290, 1140, 290 + 40 + len(lines) * 62), (6, 10, 20), LINE, 14, 3, k)
    for i, ln in enumerate(lines):
        kk = prog(t, 0.6 + i * 0.5, 1.0 + i * 0.5)
        col = DIM if ln.startswith("//") else (AMBER if "CCR1" in ln else TXT)
        text(d, (200, 314 + i * 62), ln, 38, col, mono=True, k=kk)
    lvl = 0.25 if t > 3.2 else 0
    led_lvl(d, 1480, 450, lvl, 90, prog(t, 0.6, 1.1))
    text(d, (1480, 620), f"{int(lvl * 100)}%", 52, GREEN, "Bold", "mm", mono=True, k=prog(t, 3.2, 3.7))

def s_uses(d, t, dur):
    chrome(d, "NOT JUST LEDS", "PWM is everywhere", "The same trick controls motor speed, positions hobby servos with pulses between one and two milliseconds, makes simple sounds, and runs the power supply charging your phone.", t, dur)
    items = [("Motor speed", "more on-time = faster", CYAN), ("Servo angle", "1–2 ms pulse, 50 Hz", AMBER),
             ("Sound", "buzzers, simple audio", PURPLE), ("Power supplies", "switching regulators", GREEN)]
    for i, (n, s, c) in enumerate(items):
        kk = prog(t, 0.5 + i * 0.6, 0.9 + i * 0.6)
        x = 160 + (i % 2) * 820; y = 290 + (i // 2) * 250
        box(d, (x, y, x + 760, y + 200), PANEL, c, 16, 4, kk)
        text(d, (x + 40, y + 70), n, 44, TXT, "Bold", "lm", k=kk)
        text(d, (x + 40, y + 140), s, 32, DIM, "Medium", "lm", k=kk)
        pwm_wave(d, x + 520, y + 60, 200, 60, [0.7, 0.1, 0.5, 0.4][i], 3, c, kk)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "On, off, fast", "A pin can't do half-way. So it switches on and off, fast. The duty cycle sets the average, and a hardware timer does it all for free.", t, dur)
    st = [("On/off only", RED), ("Switch fast", AMBER), ("Duty cycle", CYAN), ("Timer + CCR", PURPLE), ("Any brightness", GREEN)]
    x0, x1, y = 260, 1660, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 3.6), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(st):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 4
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 3.8:
        led_lvl(d, W // 2, 670, 0.5 + 0.5 * math.sin((t - 3.8) * 2), 60, prog(t, 3.8, 4.3))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "Interrupts: how a CPU", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "gets tapped on the shoulder", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_digital", s_digital, 9), ("03_blink", s_blink, 11),
          ("04_duty", s_duty, 10), ("05_timer", s_timer, 11), ("06_code", s_code, 11),
          ("07_uses", s_uses, 10), ("08_recap", s_recap, 9), ("09_end", s_end, 6)]

# Narration per scene (read by narrate.py) and the final file name.
NARRATION = {
 '01_hook': 'A microcontroller pin can only be fully on, or fully off. So how does it make an LED glow at half brightness? Or a motor spin at half speed?',
 '02_digital': "Here's the problem. A digital pin has exactly two settings: three point three volts, or zero. There is no setting for half-way.",
 '03_blink': "So instead, it cheats. It blinks. Once a second, you can see the flicker. Eight times a second, it's still annoying. But speed it up to a thousand times a second, and your eye just averages it into a steady glow.",
 '04_duty': 'The secret is the duty cycle: the share of each cycle the pin spends switched on. On for ten percent of the time, the LED looks dim. Fifty percent, medium. Ninety percent, bright. The average voltage follows the duty cycle.',
 '05_timer': "And the CPU doesn't do this in code. A hardware timer counts up, over and over, and resets. While the count is below a compare value, the pin is high. Once it passes it, the pin goes low. Move the compare value, and the brightness changes.",
 '06_code': 'In code, you set the timer up once. Divide the seventy two megahertz clock down to one megahertz, and count to a thousand, for a one kilohertz signal. Then, writing two hundred and fifty to the compare register gives you twenty five percent. The hardware does the rest, while your code does something else.',
 '07_uses': "And it's not just LEDs. The same trick controls motor speed, sets the angle of a hobby servo with pulses between one and two milliseconds, makes simple sounds, and runs the switching power supply charging your phone.",
 '08_recap': "A pin can't do half-way. So it switches on and off, fast. The duty cycle sets the average, and a hardware timer does it all for free.",
 '09_end': "Next episode: interrupts. How does a CPU get tapped on the shoulder? Subscribe so you don't miss it.",
}
OUTPUT = 'how_pwm_dims_an_led_ep6_narrated.mp4'

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep6/{name}.mp4", f"ep6/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep6", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    s = Image.new("RGB", (W * 3, H * 3))
    for i, (_, fn, dur) in enumerate(SCENES):
        s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
    s.resize((2880, 1620)).save("ep6/sheet.jpg", quality=85)
