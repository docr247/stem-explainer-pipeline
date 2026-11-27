import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
BLUE = (90, 150, 255)
LED_G = (70, 235, 120)           # the green LED light, used the same way throughout
IRED = (200, 60, 90)             # infrared (shown as deep red)
SKIN = (120, 84, 72)
SKIN2 = (150, 100, 86)
BLOOD = (200, 40, 60)

# ---------------- helpers ----------------
def ppg_shape(u):
    """One simplified pulse (blood volume) over a beat, u in 0..1: fast rise, slower fall, small second bump."""
    u = u % 1.0
    sig = 0.07 if u < 0.18 else 0.15
    return math.exp(-((u - 0.18) / sig) ** 2) + 0.25 * math.exp(-((u - 0.5) / 0.1) ** 2)

def ppg_trace(d, x0, y0, w, h, t, bpm, col, k=1.0, reveal=None, inverted=False, noise=0.0, motion=0.0, mf=2.6, secs=5.0, width=5):
    """Draw a PPG-like trace across w pixels covering `secs` seconds."""
    pts = []
    n = int(w * (clamp(reveal) if reveal is not None else 1.0))
    for px in range(0, n, 3):
        s = px / w * secs
        v = ppg_shape(s * bpm / 60.0) / 1.15
        if inverted: v = 1 - v
        v += noise * math.sin(px * 0.9) * math.sin(px * 0.13) + motion * math.sin(2 * math.pi * mf * s + 0.7)
        pts.append((x0 + px, y0 + h - v * h))
    if len(pts) > 1: d.line(pts, fill=fade(col, k), width=width)

def skin_section(d, x0, y0, x1, y1, k=1.0, pulse=0.0, vy=None):
    """Cross-section: skin on top, tissue below, one artery-like vessel. pulse 0..1 swells the vessel."""
    d.rectangle([x0, y0, x1, y0 + 40], fill=fade(SKIN2, k))
    d.rectangle([x0, y0 + 40, x1, y1], fill=fade(SKIN, k))
    vy = vy or (y0 + (y1 - y0) * 0.62)
    r = 26 + 14 * pulse
    d.rounded_rectangle([x0, vy - r, x1, vy + r], int(r), fill=fade(mix(SKIN, BLOOD, 0.55 + 0.35 * pulse), k))
    text(d, (x1 - 20, y0 + 20), "skin", 24, BG, "Bold", "rm", k=k)
    text(d, (x1 - 20, vy), "small blood vessels", 24, TXT, "Bold", "rm", k=k)
    return vy, r

def watch_back(d, cx, y, w, k=1.0, lit=True, col=LED_G):
    """Watch body seen from the side, sitting on the skin at y; LED on the left, photodiode on the right."""
    box(d, (cx - w // 2, y - 110, cx + w // 2, y - 10), PANEL, LINE, 24, 4, k)
    text(d, (cx, y - 70), "watch", 28, DIM, "Bold", "mm", k=k)
    lx, px = cx - w // 4, cx + w // 4
    d.rectangle([lx - 26, y - 24, lx + 26, y - 4], fill=fade(col if lit else DIM, k))
    d.rectangle([px - 30, y - 24, px + 30, y - 4], fill=fade((40, 50, 80), k), outline=fade(CYAN, k), width=3)
    return lx, px

def photon_path(d, a, b, depth, u, col, k=1.0, r=7):
    """A dot travelling from a down to depth and back up to b (u = 0..1)."""
    u = clamp(u)
    mx = (a[0] + b[0]) / 2
    if u < 0.5:
        v = u * 2; x = a[0] + (mx - a[0]) * v; y = a[1] + (depth - a[1]) * math.sin(v * math.pi / 2)
    else:
        v = (u - 0.5) * 2; x = mx + (b[0] - mx) * v; y = depth + (b[1] - depth) * (1 - math.cos(v * math.pi / 2))
    d.ellipse([x - r, y - r, x + r, y + r], fill=fade(col, k))

def heart(d, cx, cy, s, col, k=1.0):
    d.ellipse([cx - s, cy - s * 0.8, cx, cy + s * 0.2], fill=fade(col, k))
    d.ellipse([cx, cy - s * 0.8, cx + s, cy + s * 0.2], fill=fade(col, k))
    d.polygon([(cx - s * 0.97, cy - 0.1 * s), (cx + s * 0.97, cy - 0.1 * s), (cx, cy + s * 1.05)], fill=fade(col, k))

def axes(d, x0, y0, w, h, k=1.0, xl="time", yl=""):
    d.line([x0, y0, x0, y0 + h, x0 + w, y0 + h], fill=fade(LINE, k), width=3)
    if xl: text(d, (x0 + w, y0 + h + 66), xl, 24, DIM, "Medium", "rm", k=k)
    if yl: text(d, (x0 - 14, y0), yl, 24, DIM, "Medium", "rm", k=k)

# ---------------- chapter 0 ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "Your smartwatch has no electrodes on your heart. It reads your pulse with a tiny green light, by watching your blood.", t, dur)
    k = prog(t, 0.2, 0.7)
    beat = (t * 72 / 60) % 1.0
    heart(d, 420, 420, 110 * (1 + 0.08 * math.exp(-((beat - 0.1) / 0.08) ** 2)), RED, k)
    for g in range(4):
        rr = 60 + g * 40
        d.ellipse([1300 - rr, 440 - rr, 1300 + rr, 440 + rr], outline=fade(mix(BG, LED_G, 0.5 - g * 0.1), k), width=5)
    d.ellipse([1270, 410, 1330, 470], fill=fade(LED_G, k))
    if t > 1.6:
        kk = prog(t, 1.6, 2.1)
        ppg_trace(d, 260, 640, 1400, 120, t, 72, LED_G, kk, reveal=(t - 1.6) / 4.0)
    if t > 3.2:
        text(d, (1300, 260), f"{72} bpm", 56, AMBER, "Bold", "mm", mono=True, k=prog(t, 3.2, 3.7))

def s_cover(d, t, dur):
    chrome(d, "", "Here's what we'll cover", "We'll go step by step: the light, the pulse it sees, the electronics, finding the beats, the big problem of movement, and what else the light can tell us.", t, dur)
    items = [("1", "Light", "shining into your skin", LED_G), ("2", "The pulse", "what each heartbeat changes", RED),
             ("3", "Measuring", "from light to numbers", CYAN), ("4", "Finding beats", "from a wiggle to a number", AMBER),
             ("5", "Movement", "the hardest part", PURPLE), ("6", "Beyond", "oxygen, rhythm, and limits", BLUE)]
    for i, (n, a, b, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.45, 0.8 + i * 0.45)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 270 + row * 170
        box(d, (x, y, x + 720, y + 130), PANEL, c, 16, 3, kk)
        d.ellipse([x + 26, y + 30, x + 96, y + 100], fill=fade(c, kk))
        text(d, (x + 61, y + 65), n, 38, BG, "Bold", "mm", k=kk)
        text(d, (x + 130, y + 46), a, 40, TXT, "Bold", "lm", k=kk)
        text(d, (x + 130, y + 94), b, 28, DIM, "Medium", "lm", k=kk)

# ---------------- chapter 1: light ----------------
def s_scatter(d, t, dur):
    chrome(d, "STEP 1 · LIGHT", "Light goes in, some comes back", "Flip the watch over and you'll see small LEDs and a light sensor. The LED shines into your skin. Some light is absorbed, some scatters around and comes back out.", t, dur)
    k = prog(t, 0.2, 0.6)
    skin_section(d, 200, 470, 1720, 800, k)
    lx, px = watch_back(d, 960, 470, 760, k)
    for i in range(7):
        u = (t * 0.45 + i / 7) % 1.0
        if t < 1.0: break
        absorbed = i in (2, 5)
        if absorbed and u > 0.5: continue
        photon_path(d, (lx, 480), (px, 480), 640 + (i % 3) * 30, u, LED_G, k)
    kk = prog(t, 2.6, 3.1)
    text(d, (lx, 300), "LED", 34, LED_G, "Bold", "mm", k=kk)
    text(d, (px, 300), "photodiode", 34, CYAN, "Bold", "mm", k=kk)
    arrow(d, (lx, 320), (lx, 345), LED_G, 4, kk)
    arrow(d, (px, 320), (px, 345), CYAN, 4, kk)

def s_green(d, t, dur):
    chrome(d, "STEP 1 · LIGHT", "Why green?", "Blood strongly absorbs green light, so small changes in blood show up clearly. Green also stays near the surface, which suits the wrist. Many watches use green for heart rate.", t, dur)
    k = prog(t, 0.2, 0.6)
    cols = [("blue", BLUE, 0.85), ("green", LED_G, 0.9), ("red", RED, 0.25), ("infrared", IRED, 0.15)]
    x0, y0 = 300, 280
    text(d, (x0 - 20, y0 + 40), "how strongly blood absorbs it", 26, DIM, "Medium", "lm", k=k)
    for i, (n, c, v) in enumerate(cols):
        kk = prog(t, 0.6 + i * 0.4, 1.0 + i * 0.4)
        y = y0 + 110 + i * 100
        text(d, (x0 + 160, y), n, 34, c, "Bold", "rm", k=kk)
        d.rounded_rectangle([x0 + 190, y - 26, x0 + 190 + 640 * v * kk, y + 26], 10, fill=fade(c, kk))
    text(d, (x0 + 510, 720), "(rough comparison, not to scale)", 24, DIM, "Medium", "mm", k=prog(t, 2.2, 2.6))
    kk = prog(t, 3.0, 3.5)
    box(d, (1260, 330, 1700, 650), PANEL, LED_G, 16, 3, kk)
    text(d, (1480, 390), "green light", 36, LED_G, "Bold", "mm", k=kk)
    text(d, (1480, 470), "big change per beat", 28, TXT, "Medium", "mm", k=kk)
    text(d, (1480, 530), "shallow: near the surface", 28, TXT, "Medium", "mm", k=kk)
    text(d, (1480, 590), "common on the wrist", 28, TXT, "Medium", "mm", k=kk)

def s_modes(d, t, dur):
    chrome(d, "STEP 1 · LIGHT", "Through, or bounce back?", "A clip-on finger sensor shines light right through your fingertip. A watch can't do that through a wrist, so it uses reflection: the LED and the sensor sit side by side.", t, dur)
    k = prog(t, 0.2, 0.6)
    # transmission: finger
    kk = prog(t, 0.4, 0.9)
    d.rounded_rectangle([200, 400, 760, 560], 80, fill=fade(SKIN, kk))
    d.rectangle([420, 340, 520, 380], fill=fade(RED, kk))
    d.rectangle([420, 580, 520, 610], fill=fade((40, 50, 80), kk), outline=fade(CYAN, kk), width=3)
    for i in range(4):
        yy = 380 + ((t * 120 + i * 50) % 200)
        d.ellipse([463, yy - 7, 477, yy + 7], fill=fade(RED, kk))
    text(d, (480, 290), "THROUGH", 36, RED, "Bold", "mm", k=kk)
    text(d, (480, 680), "fingertip clip", 30, DIM, "Medium", "mm", k=kk)
    # reflection: wrist
    kk = prog(t, 2.0, 2.5)
    d.rectangle([1080, 480, 1720, 640], fill=fade(SKIN, kk))
    lx, px = watch_back(d, 1400, 480, 520, kk)
    for i in range(4):
        u = (t * 0.5 + i / 4) % 1.0
        photon_path(d, (lx, 490), (px, 490), 600, u, LED_G, kk)
    text(d, (1400, 290), "BOUNCE BACK", 36, LED_G, "Bold", "mm", k=kk)
    text(d, (1400, 680), "watch on the wrist", 30, DIM, "Medium", "mm", k=kk)

# ---------------- chapter 2: the pulse ----------------
def s_beat(d, t, dur):
    chrome(d, "STEP 2 · THE PULSE", "Each beat, a little more blood", "Every heartbeat pushes a wave of blood through your arteries. The tiny vessels under the watch swell slightly, then relax. More blood absorbs more light.", t, dur)
    k = prog(t, 0.2, 0.6)
    beat = (t * 60 / 60) % 1.0
    p = ppg_shape(beat) / 1.15
    heart(d, 260, 470, 80 * (1 + 0.1 * p), RED, k)
    arrow(d, (370, 470), (560, 470), RED, 6, k)
    vy, r = skin_section(d, 600, 330, 1720, 760, k, pulse=p, vy=560)
    m = int(5 - 3 * p)
    for i in range(5):
        if i < m:
            d.ellipse([1640 - i * 40 - 10, 300 - 10, 1640 - i * 40 + 10, 300 + 10], fill=fade(LED_G, k))
    text(d, (1460, 260), "light coming back", 26, LED_G, "Bold", "mm", k=k)
    text(d, (980, 260), "more blood = less light back", 30, AMBER, "Bold", "mm", k=prog(t, 2.6, 3.1))

def s_acdc(d, t, dur):
    chrome(d, "STEP 2 · THE PULSE", "A tiny ripple on a big signal", "Most of the light is absorbed the same way all the time, by skin, tissue and bone. The heartbeat adds only a small ripple, often around a percent or less of the total.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, y0, w, h = 300, 260, 1320, 500
    axes(d, x0, y0, w, h, k, "time", "light received")
    steady = y0 + h * 0.3
    kk = prog(t, 0.8, 1.3)
    d.rectangle([x0 + 3, steady, x0 + w, y0 + h - 2], fill=fade((26, 46, 52), kk))
    text(d, (x0 + w / 2, steady + 160), "steady part: skin, tissue, bone", 32, DIM, "Bold", "mm", k=kk)
    kk = prog(t, 2.0, 2.5)
    ppg_trace(d, x0 + 3, steady - 22, w - 6, 18, t, 70, LED_G, kk, inverted=True, width=4)
    if t > 3.2:
        kj = prog(t, 3.2, 3.7)
        box(d, (x0 + 760, y0 - 10, x0 + w, y0 + 70), PANEL, LED_G, 12, 3, kj)
        text(d, (x0 + 1040, y0 + 30), "pulsing part: tiny", 30, LED_G, "Bold", "mm", k=kj)
        arrow(d, (x0 + 900, y0 + 70), (x0 + 860, steady - 30), LED_G, 4, kj)

def s_wave(d, t, dur):
    chrome(d, "STEP 2 · THE PULSE", "Zoom in on the ripple", "Zoom in, flip it so more blood points up, and you get the pulse wave. A quick rise as the beat arrives, then a slower fall. One bump for every heartbeat.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, y0, w, h = 260, 280, 1400, 400
    axes(d, x0, y0, w, h, k, "time (s)", "blood volume")
    for s in range(6):
        xx = x0 + s * w / 5
        d.line([xx, y0 + h, xx, y0 + h + 12], fill=fade(LINE, k), width=3)
        text(d, (xx, y0 + h + 34), str(s), 24, DIM, "Medium", "mm", k=k)
    ppg_trace(d, x0, y0 + 20, w, h - 40, t, 72, LED_G, k, reveal=(t - 0.6) / 3.5, width=6)
    kk = prog(t, 3.4, 3.9)
    xb = x0 + ((1.18) * 60 / 72) / 5 * w
    text(d, (xb, y0 - 20), "beat arrives", 28, AMBER, "Bold", "mm", k=kk)
    text(d, (x0 + w - 10, y0 - 20), "(simplified shape, 72 bpm example)", 24, DIM, "Medium", "rm", k=kk)

# ---------------- chapter 3: measuring ----------------
def s_chain(d, t, dur):
    chrome(d, "STEP 3 · MEASURING", "From light to numbers", "The photodiode turns light into a tiny current. An amplifier turns that current into a voltage, and an analogue-to-digital converter turns the voltage into numbers.", t, dur)
    k = prog(t, 0.2, 0.6)
    stages = [("photodiode", "light → current", CYAN), ("amplifier", "current → voltage", PURPLE),
              ("ADC", "voltage → numbers", AMBER), ("processor", "finds the beats", GREEN)]
    for i, (a, b, c) in enumerate(stages):
        kk = prog(t, 0.4 + i * 0.7, 0.9 + i * 0.7)
        x = 140 + i * 430
        chip(d, x, 380, 330, 180, a, b, c, kk)
        if i < 3: arrow(d, (x + 340, 470), (x + 420, 470), DIM, 5, kk)
    kk = prog(t, 3.4, 3.9)
    text(d, (W // 2, 700), "... 512, 515, 521, 518, 509, 506, 511 ...", 40, AMBER, "Bold", "mm", mono=True, k=kk)
    text(d, (W // 2, 760), "(example readings)", 24, DIM, "Medium", "mm", k=kk)

def s_ambient(d, t, dur):
    chrome(d, "STEP 3 · MEASURING", "Blink, and subtract the room", "Room light and sunlight leak in too. So the LED is flashed on and off very quickly. With the LED off, the sensor measures only stray light, and that is subtracted.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, w = 260, 1400
    rows = [("LED", LED_G, 300), ("sensor", CYAN, 470), ("on − off", AMBER, 640)]
    for n, c, y in rows:
        text(d, (x0 - 20, y + 40), n, 28, c, "Bold", "rm", k=k)
    reveal = clamp((t - 0.6) / 4.0)
    per = w / 10
    led, sen, res = [], [], []
    for px in range(0, int(w * reveal), 2):
        on = (px % per) < per * 0.4
        led.append((x0 + px, 300 + (0 if on else 80)))
        amb = 18 * math.sin(px / w * 2 * math.pi * 1.3)
        sig = 40 + 6 * math.sin(px / w * 2 * math.pi * 4)
        sen.append((x0 + px, 470 + 60 - amb - (sig if on else 0)))
        res.append((x0 + px, 640 + 60 - sig))
    for pts, c in ((led, LED_G), (sen, CYAN), (res, AMBER)):
        if len(pts) > 1: d.line(pts, fill=fade(c, k), width=5)
    text(d, (x0 + w, 780), "(illustration: the flashes are far faster in a real watch)", 24, DIM, "Medium", "rm", k=prog(t, 3.0, 3.5))

def s_samples(d, t, dur):
    chrome(d, "STEP 3 · MEASURING", "Samples, many times a second", "The watch takes a reading many times every second, often tens to hundreds of times. That's plenty: a heart rarely beats more than about three times a second.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, y0, w, h = 260, 300, 1400, 380
    axes(d, x0, y0, w, h, k, "time", "")
    ppg_trace(d, x0, y0, w, h, t, 72, mix(BG, LED_G, 0.35), k, secs=2.5, width=3)
    n = int(clamp((t - 0.8) / 3.0) * 60)
    for i in range(n):
        s = i / 60 * 2.5
        v = ppg_shape(s * 72 / 60) / 1.15
        x, y = x0 + i / 60 * w, y0 + h - v * h
        d.line([x, y0 + h, x, y], fill=fade(LINE, k), width=2)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=fade(AMBER, k))
    text(d, (x0 + w, y0 - 10), "example: 25 samples per second", 28, AMBER, "Bold", "rm", k=prog(t, 2.6, 3.1))

# ---------------- chapter 4: finding beats ----------------
def s_filter(d, t, dur):
    chrome(d, "STEP 4 · FINDING BEATS", "Filter: keep the heartbeat band", "First, filter. Hearts beat roughly between half a beat and four beats per second. A band-pass filter keeps that band and removes slow drift and fast noise.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, w = 260, 1400
    text(d, (x0, 290), "raw", 30, DIM, "Bold", "lm", k=k)
    pts = []
    for px in range(0, w, 3):
        s = px / w * 5
        v = ppg_shape(s * 72 / 60) / 1.15 * 50 + 70 * math.sin(s * 0.9) + 10 * math.sin(px * 1.7) * math.sin(px * 0.21)
        pts.append((x0 + px, 420 - v))
    d.line(pts, fill=fade(DIM, k), width=4)
    kk = prog(t, 1.8, 2.3)
    box(d, (800, 500, 1120, 580), PANEL, AMBER, 14, 3, kk)
    text(d, (960, 540), "band-pass", 32, AMBER, "Bold", "mm", k=kk)
    arrow(d, (960, 470), (960, 496), AMBER, 4, kk)
    arrow(d, (960, 584), (960, 610), AMBER, 4, kk)
    kk = prog(t, 2.8, 3.3)
    ppg_trace(d, x0, 630, w, 110, t, 72, LED_G, kk, reveal=(t - 2.8) / 2.0)
    text(d, (x0, 620), "clean", 30, LED_G, "Bold", "lm", k=kk)
    text(d, (x0 + w, 290), "keeps about 0.5 to 4 beats per second", 26, AMBER, "Bold", "rm", k=prog(t, 2.0, 2.5))

def s_peaks(d, t, dur):
    chrome(d, "STEP 4 · FINDING BEATS", "Find the peaks, time the gaps", "Next, find each peak and measure the time between them. If peaks are 0.8 seconds apart, that's 60 divided by 0.8: 75 beats per minute.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, y0, w, h = 260, 300, 1400, 300
    secs = 4.0
    ppg_trace(d, x0, y0, w, h, t, 75, LED_G, k, secs=secs)
    per = 60 / 75
    pk = [(0.18 + i) * per for i in range(5) if (0.18 + i) * per < secs]
    for i, s in enumerate(pk):
        kk = prog(t, 1.0 + i * 0.4, 1.3 + i * 0.4)
        x = x0 + s / secs * w
        y = y0 + h - ppg_shape(0.18) / 1.15 * h
        d.ellipse([x - 12, y - 12, x + 12, y + 12], outline=fade(AMBER, kk), width=4)
        if i > 0:
            xp = x0 + pk[i - 1] / secs * w
            d.line([xp, y0 + h + 40, x, y0 + h + 40], fill=fade(AMBER, kk), width=3)
            text(d, ((xp + x) / 2, y0 + h + 70), "0.8 s", 28, AMBER, "Bold", "mm", mono=True, k=kk)
    kk = prog(t, 3.4, 3.9)
    text(d, (W // 2, 760), "60 ÷ 0.8 s = 75 beats per minute", 48, TXT, "Bold", "mm", mono=True, k=kk)

def s_freq(d, t, dur):
    chrome(d, "STEP 4 · FINDING BEATS", "Or look for the rhythm", "Another way: take several seconds of signal and ask which rhythm is strongest. That's a frequency analysis. A strong peak at 1.25 per second also means 75 beats per minute.", t, dur)
    k = prog(t, 0.2, 0.6)
    ppg_trace(d, 160, 330, 640, 200, t, 75, LED_G, k, secs=6)
    text(d, (480, 290), "several seconds of signal", 28, DIM, "Bold", "mm", k=k)
    kk = prog(t, 1.4, 1.9)
    arrow(d, (830, 430), (960, 430), DIM, 5, kk)
    x0, y0, w, h = 1020, 280, 700, 400
    axes(d, x0, y0, w, h, kk, "beats per second", "strength")
    for f in [0, 1, 2, 3, 4]:
        x = x0 + f / 4 * w
        text(d, (x, y0 + h + 30), str(f), 24, DIM, "Medium", "mm", k=kk)
    pts = []
    for px in range(0, w, 3):
        f = px / w * 4
        v = 0.95 * math.exp(-((f - 1.25) / 0.08) ** 2) + 0.35 * math.exp(-((f - 2.5) / 0.08) ** 2) + 0.04
        pts.append((x0 + px, y0 + h - v * h * prog(t, 2.0, 3.0)))
    d.line(pts, fill=fade(AMBER, kk), width=5)
    kj = prog(t, 3.0, 3.5)
    text(d, (x0 + 1.25 / 4 * w, y0 - 10), "1.25 /s = 75 bpm", 30, AMBER, "Bold", "lm", mono=True, k=kj)

# ---------------- chapter 5: movement ----------------
def s_motion(d, t, dur):
    chrome(d, "STEP 5 · MOVEMENT", "The hardest part: you move", "When you walk or run, the watch shifts on your wrist and blood sloshes in the tissue. That changes the light far more than your pulse does, and the beats get buried.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, w = 260, 1400
    text(d, (x0, 290), "sitting still", 30, LED_G, "Bold", "lm", k=k)
    ppg_trace(d, x0, 320, w, 120, t, 75, LED_G, k)
    kk = prog(t, 1.8, 2.3)
    text(d, (x0, 500), "running", 30, RED, "Bold", "lm", k=kk)
    ppg_trace(d, x0, 610, w, 50, t, 150, RED, kk, motion=0.9, mf=2.7, noise=0.25)
    text(d, (x0 + w, 500), "(illustration)", 24, DIM, "Medium", "rm", k=kk)

def s_accel(d, t, dur):
    chrome(d, "STEP 5 · MOVEMENT", "A second sensor: the accelerometer", "The watch also has an accelerometer that feels your arm swing. It knows the rhythm of your movement, so the software can ignore that rhythm and look for the one that's left.", t, dur)
    k = prog(t, 0.2, 0.6)
    chip(d, 200, 300, 360, 160, "light sensor", "pulse + movement", CYAN, k)
    chip(d, 200, 560, 360, 160, "accelerometer", "movement only", PURPLE, prog(t, 0.8, 1.3))
    kk = prog(t, 1.6, 2.1)
    for y in (380, 640):
        arrow(d, (580, y), (760, 510 + (y - 510) * 0.4), DIM, 5, kk)
    box(d, (780, 430, 1140, 590), PANEL, AMBER, 16, 3, kk)
    text(d, (960, 490), "compare", 36, AMBER, "Bold", "mm", k=kk)
    text(d, (960, 540), "and remove motion", 28, TXT, "Medium", "mm", k=kk)
    kj = prog(t, 2.8, 3.3)
    arrow(d, (1160, 510), (1260, 510), DIM, 5, kj)
    ppg_trace(d, 1280, 440, 440, 140, t, 150, LED_G, kj, secs=2.5)
    text(d, (1500, 640), "pulse, recovered", 30, LED_G, "Bold", "mm", k=kj)

def s_cadence(d, t, dur):
    chrome(d, "STEP 5 · MOVEMENT", "The cadence trap", "Here's a sneaky one. A runner's steps can land at almost the same rate as their heart beats. When the two rhythms overlap, the watch can mistake your steps for your pulse.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, y0, w, h = 300, 280, 1320, 400
    axes(d, x0, y0, w, h, k, "per minute", "strength")
    for v in (120, 150, 180, 210):
        x = x0 + (v - 100) / 130 * w
        text(d, (x, y0 + h + 30), str(v), 24, DIM, "Medium", "mm", k=k)
    sep = 40 * (1 - prog(t, 1.2, 4.0))
    hr, cad = 165 - sep / 2, 165 + sep / 2
    for f, c, n, yo in ((hr, RED, "heart", 0), (cad, PURPLE, "steps", 50)):
        pts = []
        for px in range(0, w, 3):
            ff = 100 + px / w * 130
            pts.append((x0 + px, y0 + h - 0.8 * h * math.exp(-((ff - f) / 5) ** 2)))
        d.line(pts, fill=fade(c, k), width=5)
        text(d, (x0 + (f - 100) / 130 * w, y0 - 10 + yo), n, 30, c, "Bold", "mm", k=k)
    text(d, (W // 2, 770), "(example: 165 per minute)", 26, DIM, "Medium", "mm", k=prog(t, 3.0, 3.5))

def s_fit(d, t, dur):
    chrome(d, "STEP 5 · MOVEMENT", "What else gets in the way", "Fit matters too. A loose strap lets light leak in. Cold hands mean less blood near the surface. Tattoo ink and darker skin absorb more light, so the signal can be weaker.", t, dur)
    items = [("Loose strap", "stray light, more movement", AMBER), ("Cold", "less blood near the surface", BLUE),
             ("Tattoo ink", "absorbs a lot of light", PURPLE), ("Darker skin", "more absorption, weaker signal", CYAN)]
    for i, (a, b, c) in enumerate(items):
        kk = prog(t, 0.4 + i * 0.6, 0.9 + i * 0.6)
        col, row = i % 2, i // 2
        x, y = 200 + col * 800, 290 + row * 200
        box(d, (x, y, x + 720, y + 160), PANEL, c, 16, 3, kk)
        text(d, (x + 40, y + 55), a, 42, c, "Bold", "lm", k=kk)
        text(d, (x + 40, y + 115), b, 30, TXT, "Medium", "lm", k=kk)
    text(d, (W // 2, 760), "Good designs compensate: brighter LEDs, more gain, a snug fit", 30, GREEN, "Bold", "mm", k=prog(t, 3.2, 3.7))

# ---------------- chapter 6: beyond ----------------
def s_oxygen(d, t, dur):
    chrome(d, "STEP 6 · BEYOND", "Red and infrared: blood oxygen", "Blood with and without oxygen absorbs red and infrared light differently. Compare the pulse at the two colours to estimate how much oxygen your blood carries.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, w = 300, 900
    for i, (n, c, amp) in enumerate([("red", RED, 0.55), ("infrared", IRED, 1.0)]):
        y = 300 + i * 220
        kk = prog(t, 0.5 + i * 0.6, 1.0 + i * 0.6)
        text(d, (x0 - 20, y + 60), n, 32, c, "Bold", "rm", k=kk)
        ppg_trace(d, x0, y + 60 - 60 * amp, w, 120 * amp, t, 72, c, kk, secs=3)
    kk = prog(t, 2.4, 2.9)
    box(d, (1300, 330, 1720, 650), PANEL, AMBER, 16, 3, kk)
    text(d, (1510, 400), "compare the", 32, TXT, "Bold", "mm", k=kk)
    text(d, (1510, 450), "two ripples", 32, TXT, "Bold", "mm", k=kk)
    text(d, (1510, 530), "→ oxygen estimate", 32, AMBER, "Bold", "mm", k=kk)
    text(d, (1510, 600), "(shapes illustrative)", 24, DIM, "Medium", "mm", k=kk)

def s_hrv(d, t, dur):
    chrome(d, "STEP 6 · BEYOND", "Not every gap is the same", "Look closely and the gaps between beats are never exactly equal. They speed up as you breathe in and slow as you breathe out. Watches track this as heart rate variability.", t, dur)
    k = prog(t, 0.2, 0.6)
    x0, y0, w = 220, 330, 1480
    gaps = [0.84, 0.80, 0.76, 0.74, 0.77, 0.82, 0.86, 0.85, 0.80, 0.76]
    x = x0
    xs = [x]
    for g in gaps: x += g * 180; xs.append(x)
    for i, xx in enumerate(xs):
        kk = prog(t, 0.4 + i * 0.25, 0.6 + i * 0.25)
        d.line([xx, y0, xx, y0 + 180], fill=fade(RED, kk), width=6)
        if i > 0:
            text(d, ((xs[i - 1] + xx) / 2, y0 + 230), f"{gaps[i - 1]:.2f}", 26, AMBER, "Bold", "mm", mono=True, k=kk)
    text(d, (x0, y0 - 40), "beats", 28, RED, "Bold", "lm", k=k)
    text(d, (W // 2, 660), "gaps between beats (seconds, example)", 30, DIM, "Medium", "mm", k=prog(t, 2.4, 2.9))
    text(d, (W // 2, 740), "heart rate variability", 46, AMBER, "Bold", "mm", k=prog(t, 3.2, 3.7))

def s_ecg(d, t, dur):
    chrome(d, "STEP 6 · BEYOND", "Light on the wrist vs a chest strap", "A chest strap works differently. Its electrodes pick up the heart's own electrical signal, so each beat is a sharp spike. During hard exercise, it's generally the more accurate option.", t, dur)
    cols = [("WRIST LIGHT", LED_G, ["sees the blood pulse", "comfortable, all day", "movement can confuse it", "a small delay after each beat"]),
            ("CHEST STRAP", CYAN, ["hears the heart's electricity", "sharp, clear beats", "better in hard exercise", "less comfortable all day"])]
    for i, (n, c, lines) in enumerate(cols):
        x = 200 + i * 800
        kk = prog(t, 0.4 + i * 1.4, 0.9 + i * 1.4)
        box(d, (x, 260, x + 720, 800), PANEL, c, 18, 3, kk)
        text(d, (x + 360, 320), n, 48, c, "Bold", "mm", k=kk)
        if i == 0:
            ppg_trace(d, x + 80, 370, 560, 80, t, 72, c, kk, secs=3, width=4)
        else:
            pts = []
            for px in range(0, 560, 2):
                u = (px / 560 * 3 * 72 / 60) % 1.0
                v = -1.0 * math.exp(-((u - 0.2) / 0.012) ** 2) - 0.25 * math.exp(-((u - 0.45) / 0.05) ** 2)
                pts.append((x + 80 + px, 430 + v * 60))
            d.line(pts, fill=fade(c, kk), width=4)
        for j, ln in enumerate(lines):
            text(d, (x + 60, 520 + j * 66), "•  " + ln, 32, TXT, "Medium", "lm", k=kk)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "From a green light to a number", "Light goes in and scatters back. Each beat adds blood, so less light returns. Electronics make numbers, software counts the beats, and motion sensing keeps it honest.", t, dur)
    stg = [("Light", LED_G), ("Pulse", RED), ("Measure", CYAN), ("Beats", AMBER), ("Movement", PURPLE), ("Beyond", BLUE)]
    x0, x1, y = 220, 1700, 420
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(stg):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.2:
        ppg_trace(d, 360, 560, 1200, 160, t, 72, LED_G, prog(t, 4.2, 4.7), secs=5)

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does a prosthetic hand", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "read muscle signals?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_cover", s_cover, 8),
          ("03_scatter", s_scatter, 8), ("04_green", s_green, 8), ("05_modes", s_modes, 8),
          ("06_beat", s_beat, 8), ("07_acdc", s_acdc, 8), ("08_wave", s_wave, 8),
          ("09_chain", s_chain, 8), ("10_ambient", s_ambient, 8), ("11_samples", s_samples, 8),
          ("12_filter", s_filter, 8), ("13_peaks", s_peaks, 8), ("14_freq", s_freq, 8),
          ("15_motion", s_motion, 8), ("16_accel", s_accel, 8), ("17_cadence", s_cadence, 8), ("18_fit", s_fit, 8),
          ("19_oxygen", s_oxygen, 8), ("20_hrv", s_hrv, 8), ("21_ecg", s_ecg, 8),
          ("22_recap", s_recap, 8), ("23_end", s_end, 6)]

NARRATION = {
 "01_hook": "Your smartwatch can tell you your heart rate, all day long. But nothing on it touches your heart, and there are no wires on your chest. Instead, it shines a tiny green light into your wrist, and watches your blood. Here's how that actually works.",
 "02_cover": "We'll take it step by step. First, the light, and what happens to it inside your skin. Then, what each heartbeat changes. Then the electronics that turn light into numbers, and the maths that finds the beats. Then the hardest part: movement. And finally, what else the light can tell us.",
 "03_scatter": "Step one: light. Flip a smartwatch over, and you'll usually see a few small LEDs, and one or more light sensors called photodiodes. The LED shines into your skin. Some of that light is absorbed. Some of it scatters around inside the tissue, and finds its way back out, where the photodiode catches it.",
 "04_green": "Why green? Blood absorbs green light strongly, much more than red or infrared. So a small change in the amount of blood makes a clear change in the light. Green light also doesn't travel very deep, so it mostly samples the tiny vessels near the surface. That's why many watches use green for heart rate.",
 "05_modes": "There are two ways to set this up. A clip-on finger sensor, like the ones in hospitals, shines light right through your fingertip, to a sensor on the other side. A wrist is far too thick for that. So a watch uses reflection instead. The LED and the photodiode sit side by side, and the sensor catches the light that bounces back.",
 "06_beat": "Step two: the pulse. Every time your heart beats, it pushes a wave of blood out through your arteries. When that wave reaches your wrist, the tiny vessels under the watch swell slightly, and then relax again. More blood means more light is absorbed, so a little less light comes back to the sensor.",
 "07_acdc": "Here's the catch. Most of the light is absorbed the same way all the time, by skin, tissue, bone and the blood that's always there. That gives a big, steady signal. The heartbeat only adds a small ripple on top, often around a percent or less of the total. The watch has to find that tiny ripple.",
 "08_wave": "Let's zoom in on the ripple, and flip it over, so that more blood points up. Now you can see the pulse wave. A quick rise as each beat arrives, then a slower fall as the vessels relax. There's one bump for every heartbeat. This signal has a name: a photoplethysmogram, or P P G for short.",
 "09_chain": "Step three: measuring. The photodiode turns light into a tiny electric current. More light, more current. An amplifier turns that current into a voltage big enough to measure. Then an analogue-to-digital converter, an A D C, like the one in episode eight, turns the voltage into a stream of numbers.",
 "10_ambient": "But the room has light too, and sunlight can be far brighter than the LED. So the LED isn't left on. It's flashed on and off, very quickly. While it's off, the sensor measures only the stray light. While it's on, it measures stray light plus the LED. Subtract one from the other, and the stray light cancels out.",
 "11_samples": "The watch does this many times every second. Often tens of times, sometimes hundreds. That's plenty, because even during hard exercise, a heart rarely beats more than about three times a second. To save battery, many watches also measure less often while you're resting.",
 "12_filter": "Step four: finding the beats. The raw numbers wander up and down slowly, as you breathe and shift, and they have fast jitter from noise. A human heart beats roughly between half a beat and four beats per second. So a band-pass filter keeps just that range, and throws away the slow drift and the fast noise.",
 "13_peaks": "Now the software looks for the peaks, one per heartbeat, and measures the time between them. Say the peaks are zero point eight seconds apart. There are sixty seconds in a minute, so sixty divided by zero point eight gives seventy five beats per minute. Average a few beats, and that's the number on your screen.",
 "14_freq": "There's another way to do it. Take several seconds of signal, and ask: which rhythm is strongest in here? That's called a frequency analysis. If the strongest rhythm repeats one and a quarter times per second, that's also seventy five beats per minute. Many watches combine methods like these.",
 "15_motion": "Step five: movement, the hardest part. When you're sitting still, the pulse wave is clear. But when you walk or run, the watch shifts on your wrist, light leaks in at the edges, and blood sloshes around in the tissue. Those changes can be much bigger than the pulse itself, and the beats get buried.",
 "16_accel": "So the watch uses a second sensor: an accelerometer, the same kind of motion sensor that counts your steps. It feels the swing of your arm, so it knows the rhythm of your movement. The software can then ignore that rhythm in the light signal, and look for the rhythm that's left: your pulse.",
 "17_cadence": "Here's a sneaky problem. A runner's feet can hit the ground about as often as their heart beats. Say a hundred and sixty five steps per minute, and a hundred and sixty five beats per minute. When the two rhythms line up, it's very hard to pull them apart, and a watch can briefly lock on to your steps instead of your heart.",
 "18_fit": "Accuracy also depends on fit, and on you. A loose strap lets stray light in, and lets the watch bounce around. Cold hands mean less blood near the surface, so the ripple shrinks. Tattoo ink, and darker skin, absorb more green light, so the signal can be weaker. Good designs compensate, with brighter LEDs, more amplification, and a snug fit.",
 "19_oxygen": "Step six: beyond heart rate. Some watches also have red and infrared LEDs. Blood that's carrying oxygen absorbs red and infrared light differently from blood that isn't. So by comparing the size of the pulse ripple at the two colours, the device can estimate how much oxygen your blood is carrying. That's the idea behind a pulse oximeter.",
 "20_hrv": "Look closely at the beats, and you'll notice the gaps between them are never exactly equal. Your heart speeds up a little as you breathe in, and slows down a little as you breathe out. Watches can track these small changes, and they call it heart rate variability.",
 "21_ecg": "Finally, how does this compare with a chest strap? A chest strap works differently. Its electrodes pick up the heart's own electrical signal, so each beat is a sharp, clear spike. The light on your wrist sees the blood pulse instead, a moment after each beat. During hard exercise, a chest strap is generally the more accurate option.",
 "22_recap": "Let's recap. Green light goes into your skin, and some scatters back. Each heartbeat adds a little blood, so a little less light returns. A photodiode, an amplifier and an A D C turn that into numbers. Filters and peak-finding count the beats. And an accelerometer helps keep movement from fooling it.",
 "23_end": "Next episode: how does a prosthetic hand read the signals from your muscles? Subscribe so you don't miss it.",
}
OUTPUT = "how_a_smartwatch_reads_heart_rate_ep13_narrated.mp4"

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep13/{name}.mp4", f"ep13/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep13", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    for j in range(0, len(SCENES), 9):
        s = Image.new("RGB", (W * 3, H * 3))
        for i, (_, fn, dur) in enumerate(SCENES[j:j + 9]):
            s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
        s.resize((2880, 1620)).save(f"ep13/sheet{j // 9 + 1}.jpg", quality=85)
