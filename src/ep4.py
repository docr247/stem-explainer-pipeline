import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
DESC = [("bLength", "18"), ("bcdUSB", "2.00"), ("bDeviceClass", "0x00"), ("bMaxPacketSize0", "64"),
        ("idVendor", "0x1A2B"), ("idProduct", "0x3C4D"), ("iProduct", "\"USB Keyboard\"")]

def plug(d, x, y, s=1.0, k=1.0, col=CYAN):
    d.rounded_rectangle([x, y, x + 120 * s, y + 70 * s], 10 * s, fill=fade(PANEL, k), outline=fade(col, k), width=max(2, int(4 * s)))
    d.rectangle([x + 120 * s, y + 14 * s, x + 200 * s, y + 56 * s], fill=fade((150, 160, 185), k))
    d.rectangle([x + 140 * s, y + 24 * s, x + 156 * s, y + 34 * s], fill=fade(BG, k))
    d.rectangle([x + 170 * s, y + 24 * s, x + 186 * s, y + 34 * s], fill=fade(BG, k))

def packet(d, x, y, label, col, w=220):
    d.rounded_rectangle([x - w / 2, y - 22, x + w / 2, y + 22], 10, fill=col)
    text(d, (x, y), label, 24, BG, "Bold", "mm", mono=True)

def wire_pair(d, k):
    chip(d, 140, 330, 360, 240, "Device", "just plugged in", CYAN, k, pins=False)
    chip(d, 1420, 330, 360, 240, "Host", "USB controller", PURPLE, k, pins=False)
    d.line([500, 420, 1420, 420], fill=fade(LINE, k), width=5)
    d.line([500, 480, 1420, 480], fill=fade(LINE, k), width=5)

def travel(d, t, a, b, y, label, col, to_host=True, w=260):
    if a < t < b:
        p = ease((t - a) / (b - a))
        x = (520 + w / 2 + p * (880 - w)) if to_host else (1400 - w / 2 - p * (880 - w))
        packet(d, x, y, label, col, w)

def s_hook(d, t, dur):
    chrome(d, "", "", "You plug something in. A second later, it just works. But at first, your computer had no idea what that thing was.", t, dur)
    x = 260 + 420 * ease(clamp((t - 0.6) / 1.4))
    plug(d, x, 380, 1.6, prog(t, 0.2, 0.6))
    k = prog(t, 0.2, 0.6)
    d.rounded_rectangle([1000, 330, 1520, 560], 18, fill=fade(PANEL, k), outline=fade(LINE, k), width=4)
    d.rectangle([1000, 395, 1040, 485], fill=fade(BG, k))
    if t > 2.2:
        text(d, (1260, 445), "???", 110, AMBER, "Bold", "mm", k=prog(t, 2.2, 2.7))

def s_detect(d, t, dur):
    chrome(d, "STEP 1 · DETECT", "A resistor says hello", "The device has a tiny pull-up resistor on one data line. When it's plugged in, that line's voltage rises, and the host knows something is attached, and even how fast it can talk.", t, dur)
    k = prog(t, 0.2, 0.7)
    wire_pair(d, k)
    text(d, (960, 395), "D+", 28, AMBER, "Bold", "mm", mono=True, k=k)
    text(d, (960, 510), "D−", 28, DIM, "Bold", "mm", mono=True, k=k)
    kk = prog(t, 1.0, 1.5)
    d.line([560, 420, 560, 350], fill=fade(AMBER, kk), width=4)
    for i in range(5):
        y = 350 - i * 12
        d.line([560, y, 575 if i % 2 == 0 else 545, y - 6], fill=fade(AMBER, kk), width=4)
    text(d, (600, 300), "1.5 kΩ pull-up", 26, AMBER, "Bold", "lm", k=kk)
    x0, w0 = 600, 760
    text(d, (x0 - 20, 700), "D+", 30, AMBER, "Bold", "rm", mono=True, k=prog(t, 1.6, 2.0))
    d.line([x0, 740, x0 + w0, 740], fill=fade(LINE, k), width=2)
    pts = []
    tt = clamp((t - 1.8) / 3.0) * w0
    for px in range(0, int(tt), 3):
        u = px / w0
        v = 0 if u < 0.35 else 1 - math.exp(-(u - 0.35) * 18)
        pts.append((x0 + px, 740 - v * 80))
    if len(pts) > 1: d.line(pts, fill=AMBER, width=5)
    if t > 5.2:
        text(d, (1420, 700), "D+ high → full speed", 30, GREEN, "Bold", "lm", k=prog(t, 5.2, 5.7))

def s_reset(d, t, dur):
    chrome(d, "STEP 2 · RESET", "Everyone starts at address 0", "The host resets the device by pulling both data lines low. After a reset, every new device answers at the same default address: zero.", t, dur)
    k = prog(t, 0.2, 0.7)
    wire_pair(d, k)
    low = 1.2 < t < 3.2
    if low:
        d.line([500, 420, 1420, 420], fill=RED, width=7)
        d.line([500, 480, 1420, 480], fill=RED, width=7)
        text(d, (960, 360), "RESET: D+ and D− held low", 32, RED, "Bold", "mm", mono=True)
    if t > 3.4:
        kk = prog(t, 3.4, 4.0)
        box(d, (200, 620, 440, 720), mix(BG, AMBER, 0.25), AMBER, 14, 4, kk)
        text(d, (320, 670), "addr 0", 40, AMBER, "Bold", "mm", mono=True, k=kk)
        text(d, (960, 670), "the only device allowed to answer at 0", 32, DIM, "Medium", "mm", k=prog(t, 4.2, 4.8))

def s_describe(d, t, dur):
    chrome(d, "STEP 3 · WHO ARE YOU?", "The device descriptor", "The host asks: who are you? The device answers with its device descriptor, 18 bytes that say which company made it, which product it is, and how big its packets can be.", t, dur)
    k = prog(t, 0.2, 0.6)
    chip(d, 100, 300, 300, 200, "Device", "addr 0", CYAN, k, pins=False)
    chip(d, 100, 560, 300, 200, "Host", "", PURPLE, k, pins=False)
    if 0.8 < t < 2.4:
        p = ease((t - 0.8) / 1.4)
        packet(d, 250, 540 - p * 20, "GET_DESCRIPTOR", PURPLE, 300)
    for i, (f, v) in enumerate(DESC):
        st = 2.4 + i * 0.45
        kk = prog(t, st, st + 0.35)
        if kk <= 0: continue
        y = 270 + i * 72
        hot = f in ("idVendor", "idProduct")
        box(d, (560, y, 1720, y + 60), mix(BG, AMBER, 0.18) if hot else PANEL, AMBER if hot else LINE, 10, 3 if hot else 2, kk)
        text(d, (590, y + 30), f, 32, CYAN, "Bold", "lm", mono=True, k=kk)
        text(d, (1690, y + 30), v, 32, AMBER if hot else TXT, "Bold", "rm", mono=True, k=kk)
    if t > 6.0:
        text(d, (1140, 800), "Vendor ID + Product ID = this exact model (example values)", 26, DIM, "Medium", "mm", k=prog(t, 6.0, 6.5))

def s_address(d, t, dur):
    chrome(d, "STEP 4 · SET_ADDRESS", "A unique number", "Next, the host gives the device its own address, a number from 1 to 127. Address zero is now free for the next device you plug in.", t, dur)
    k = prog(t, 0.2, 0.7)
    wire_pair(d, k)
    travel(d, t, 1.0, 2.6, 420, "SET_ADDRESS(7)", PURPLE, to_host=False, w=300)
    a = "0" if t < 2.8 else "7"
    col = AMBER if t < 2.8 else GREEN
    box(d, (200, 620, 440, 720), mix(BG, col, 0.25), col, 14, 4, k)
    text(d, (320, 670), f"addr {a}", 40, col, "Bold", "mm", mono=True, k=k)
    if t > 3.4:
        kk = prog(t, 3.4, 4.0)
        for i in range(8):
            x = 620 + i * 130
            used = i in (1, 2, 4, 7)
            box(d, (x, 640, x + 110, 710), mix(BG, GREEN, 0.3) if used else PANEL, GREEN if i == 7 else LINE, 10, 2, kk)
            text(d, (x + 55, 675), str(i), 32, TXT, "Bold", "mm", mono=True, k=kk)
        text(d, (1660, 675), "… 127", 32, DIM, "Bold", "lm", mono=True, k=kk)

def s_class(d, t, dur):
    chrome(d, "STEP 5 · CONFIGURATION", "What kind of thing are you?", "Then it reads the configuration: the device's interfaces, its endpoints, and its class code. Class 3 means human interface device, like a keyboard or mouse. Class 8 means storage, like a flash drive.", t, dur)
    rows = [("0x03", "HID", "keyboard, mouse, gamepad", CYAN), ("0x08", "Mass Storage", "flash drive, external SSD", AMBER),
            ("0x01", "Audio", "headset, microphone", PURPLE), ("0x0E", "Video", "webcam", GREEN)]
    for i, (c, n, ex, col) in enumerate(rows):
        st = 0.6 + i * 0.7
        kk = prog(t, st, st + 0.4)
        if kk <= 0: continue
        y = 290 + i * 120
        hot = i == 0 and t > 4.0
        box(d, (240, y, 1680, y + 96), mix(BG, col, 0.22) if hot else PANEL, col, 14, 5 if hot else 3, kk)
        text(d, (290, y + 48), c, 44, col, "Bold", "lm", mono=True, k=kk)
        text(d, (500, y + 48), n, 40, TXT, "Bold", "lm", k=kk)
        text(d, (1640, y + 48), ex, 30, DIM, "Medium", "rm", k=kk)

def s_driver(d, t, dur):
    chrome(d, "STEP 6 · DRIVER", "Match, load, ready", "Finally, the operating system matches the vendor and product ID, or the class code, to a driver. It loads it, sends SET_CONFIGURATION, and your device is ready. Ding.", t, dur)
    steps = [("VID:PID or class", AMBER), ("Find driver", CYAN), ("SET_CONFIGURATION", PURPLE), ("Ready", GREEN)]
    for i, (s, c) in enumerate(steps):
        kk = prog(t, 0.4 + i * 0.7, 0.8 + i * 0.7)
        x = 120 + i * 430
        box(d, (x, 330, x + 380, 440), PANEL, c, 14, 4, kk)
        text(d, (x + 190, 385), s, 32, TXT, "Bold", "mm", mono=(i == 2), k=kk)
        if i < 3: arrow(d, (x + 384, 385), (x + 426, 385), DIM, 4, kk)
    if t > 3.6:
        kk = prog(t, 3.6, 4.2)
        box(d, (640, 560, 1280, 700), (245, 247, 252), LINE, 16, 3, kk)
        text(d, (960, 610), "USB Keyboard", 36, (20, 24, 40), "Bold", "mm", k=kk)
        text(d, (960, 655), "Device is ready to use", 28, (60, 70, 100), "Medium", "mm", k=kk)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "The USB handshake", "Detect, reset, describe, address, configure, and load a driver. A whole conversation, in a fraction of a second.", t, dur)
    st = [("Detect", AMBER), ("Reset", RED), ("Describe", CYAN), ("Address", GREEN), ("Configure", PURPLE), ("Driver", TXT)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(st):
        s = 0.5 + i * 0.6; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.4:
        plug(d, 860, 620, 1.0, prog(t, 4.4, 5.0), GREEN)

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "I2C vs SPI vs UART:", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "how chips talk", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_detect", s_detect, 11), ("03_reset", s_reset, 10),
          ("04_describe", s_describe, 11), ("05_address", s_address, 10), ("06_class", s_class, 11),
          ("07_driver", s_driver, 11), ("08_recap", s_recap, 9), ("09_end", s_end, 6)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep4/{name}.mp4", f"ep4/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep4", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    s = Image.new("RGB", (W * 3, H * 3))
    for i, (_, fn, dur) in enumerate(SCENES):
        s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
    s.resize((2880, 1620)).save("ep4/sheet.jpg", quality=85)
