import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BG = (11, 16, 32)
PANEL = (22, 30, 54)
LINE = (52, 66, 104)
TXT = (230, 236, 250)
DIM = (130, 144, 180)
CYAN = (64, 214, 255)
AMBER = (255, 184, 64)
GREEN = (90, 230, 140)
RED = (255, 96, 96)

F = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_fc = {}
def font(size, w="SemiBold", mono=False):
    k = (size, w, mono)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(MONO if mono else F + f"Inter-{w}.otf", size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def prog(t, a, b): return ease((t - a) / (b - a))
def mix(c1, c2, k): return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))
def fade(c, k): return mix(BG, c, clamp(k))

def text(d, xy, s, size=40, col=TXT, w="SemiBold", anchor="la", mono=False, k=1.0):
    d.text(xy, s, font=font(size, w, mono), fill=fade(col, k), anchor=anchor)

def box(d, xy, col=PANEL, outline=LINE, r=18, width=3, k=1.0):
    d.rounded_rectangle(xy, r, fill=fade(col, k), outline=fade(outline, k), width=width)

def chrome(d, step, title, caption, t, dur):
    k = prog(t, 0, 0.6)
    if step:
        text(d, (120, 90), step, 30, CYAN, "Bold", k=k)
    text(d, (120, 130), title, 64, TXT, "Bold", k=k)
    if caption:
        n = int(len(caption) * clamp((t - 0.3) / 2.2))
        lines = wrap(caption[:n] if n < len(caption) else caption, 64)
        y = H - 70 - 52 * len(wrap(caption, 64))
        for ln in lines:
            text(d, (W // 2, y), ln, 40, TXT, "Medium", "ma"); y += 52

def wrap(s, n):
    out, cur = [], ""
    for wd in s.split():
        if len(cur) + len(wd) + 1 > n: out.append(cur); cur = wd
        else: cur = (cur + " " + wd).strip()
    if cur: out.append(cur)
    return out

def arrow(d, a, b, col, width=5, k=1.0):
    d.line([a, b], fill=fade(col, k), width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    p = [b, (b[0] - 22 * math.cos(ang - .45), b[1] - 22 * math.sin(ang - .45)),
         (b[0] - 22 * math.cos(ang + .45), b[1] - 22 * math.sin(ang + .45))]
    d.polygon(p, fill=fade(col, k))

def chip(d, x, y, w, h, label, sub=None, col=CYAN, k=1.0, pins=True):
    if pins:
        for i in range(6):
            px = x + 30 + i * (w - 60) / 5
            d.rectangle([px - 6, y - 16, px + 6, y], fill=fade(DIM, k))
            d.rectangle([px - 6, y + h, px + 6, y + h + 16], fill=fade(DIM, k))
    box(d, (x, y, x + w, y + h), PANEL, col, 14, 4, k)
    text(d, (x + w / 2, y + h / 2 - (18 if sub else 0)), label, 40, TXT, "Bold", "mm", k=k)
    if sub: text(d, (x + w / 2, y + h / 2 + 28), sub, 26, DIM, "Medium", "mm", k=k)

# ---------------- scenes ----------------
def s_hook(d, t, dur):
    chrome(d, "", "", "You press this button. A few seconds later, you're looking at a login screen. What happened in between?", t, dur)
    cx, cy = W // 2, 420
    press = 1 - 0.08 * math.sin(math.pi * clamp((t - 1.4) / 0.35))
    on = t > 1.6
    r = int(150 * press)
    col = CYAN if on else DIM
    if on:
        for g in range(6):
            rr = r + 20 + g * 14
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=mix(BG, CYAN, 0.25 - g * 0.04), width=4)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PANEL, outline=col, width=8)
    d.arc([cx - 60, cy - 55, cx + 60, cy + 65], 300, 240, fill=col, width=12)
    d.line([cx, cy - 75, cx, cy + 5], fill=col, width=12)
    if on:
        el = max(0.0, (t - 1.6) * 0.55)
        text(d, (cx, 660), f"t = {el:0.3f} s", 46, AMBER, mono=True, anchor="mm", k=prog(t, 1.6, 2.2))

def scope(d, x0, y0, w, h, t, start, name, col, level, settle):
    text(d, (x0 - 20, y0 + h / 2), name, 30, col, "Bold", "rm", mono=True)
    d.line([x0, y0 + h, x0 + w, y0 + h], fill=LINE, width=2)
    pts = []
    tt = clamp((t - 1.0) / 8.0) * w
    for px in range(0, int(tt), 4):
        st = px / w * 8.0
        if st < start: v = 0
        else:
            u = st - start
            v = level * (1 - math.exp(-u * 3)) + (0.15 * math.exp(-u * 2.5) * math.sin(u * 30) if settle else 0)
        pts.append((x0 + px, y0 + h - v * h))
    if len(pts) > 1: d.line(pts, fill=col, width=5)

def s_power(d, t, dur):
    chrome(d, "STEP 1 · POWER", "Rails up, then Power Good", "First the power supply ramps up its voltage rails. Only when they are stable does it raise Power Good, and the CPU is finally let out of reset.", t, dur)
    x0, w, h = 420, 1300, 80
    scope(d, x0, 270, w, h, t, 0.3, "+12V", AMBER, 1.0, True)
    scope(d, x0, 390, w, h, t, 0.5, "+5V", CYAN, 1.0, True)
    scope(d, x0, 510, w, h, t, 0.7, "+3.3V", GREEN, 1.0, True)
    scope(d, x0, 630, w, h, t, 3.6, "PWR_OK", TXT, 1.0, False)
    scope(d, x0, 750, w, h, t, 5.6, "RESET#", RED, 1.0, False)
    if t > 7.6:
        k = prog(t, 7.6, 8.2)
        xs = x0 + 5.6 / 8 * w
        d.line([xs, 225, xs, 840], fill=fade(RED, k * 0.6), width=2)
        text(d, (xs - 16, 790), "CPU released from reset", 30, RED, "Bold", "rm", k=k)

def s_vector(d, t, dur):
    chrome(d, "STEP 2 · RESET VECTOR", "The first instruction", "The CPU wakes up knowing exactly one thing: the hard-wired address of its first instruction. This is the reset vector.", t, dur)
    chip(d, 260, 330, 380, 260, "CPU", "just out of reset", CYAN, prog(t, 0.2, 0.8))
    chip(d, 1280, 330, 380, 260, "SPI Flash", "firmware ROM", AMBER, prog(t, 0.5, 1.1))
    k = prog(t, 1.0, 1.6)
    d.line([640, 430, 1280, 430], fill=fade(LINE, k), width=6)
    d.line([640, 500, 1280, 500], fill=fade(LINE, k), width=6)
    text(d, (960, 405), "address", 26, DIM, "Medium", "mb", k=k)
    text(d, (960, 530), "data", 26, DIM, "Medium", "ma", k=k)
    s = "PC = 0xFFFFFFF0"
    n = int(len(s) * clamp((t - 1.5) / 1.2))
    text(d, (450, 680), s[:n], 48, CYAN, mono=True, anchor="mm")
    if 3.0 < t < 5.0:
        p = ease((t - 3.0) / 1.6); x = 640 + p * 640
        d.ellipse([x - 14, 416, x + 14, 444], fill=CYAN)
        text(d, (x, 380), "0xFFFFFFF0", 28, CYAN, mono=True, anchor="mm")
    if 5.0 < t < 7.2:
        p = ease((t - 5.0) / 1.6); x = 1280 - p * 640
        d.ellipse([x - 14, 486, x + 14, 514], fill=AMBER)
        text(d, (x, 560), "JMP → firmware", 28, AMBER, mono=True, anchor="mm")
    if t > 7.4:
        k = prog(t, 7.4, 8.0)
        box(d, (560, 740, 1360, 830), PANEL, LINE, 14, 2, k)
        text(d, (960, 785), "ARM microcontroller: reads the vector table at 0x00000000", 30, DIM, "Medium", "mm", k=k)

def s_post(d, t, dur):
    chrome(d, "STEP 3 · FIRMWARE", "BIOS / UEFI runs POST", "That jump lands in the firmware, BIOS or UEFI, which runs the Power-On Self-Test and trains your RAM.", t, dur)
    items = ["CPU & microcode", "RAM training", "Chipset & PCIe", "Graphics", "USB & keyboard", "Storage"]
    for i, it in enumerate(items):
        st = 0.8 + i * 1.2
        k = prog(t, st, st + 0.4)
        if k <= 0: continue
        y = 280 + i * 92
        box(d, (360, y, 1560, y + 72), PANEL, LINE, 12, 2, k)
        text(d, (400, y + 36), it, 36, TXT, "Medium", "lm", k=k)
        done = prog(t, st + 0.6, st + 1.0)
        if i == 1:
            bw = 520 * prog(t, st + 0.1, st + 1.0)
            d.rounded_rectangle([960, y + 26, 960 + 520, y + 46], 8, fill=fade(LINE, k))
            if bw > 4: d.rounded_rectangle([960, y + 26, 960 + bw, y + 46], 8, fill=AMBER)
        if done > 0:
            cx, cy = 1510, y + 36
            d.line([(cx - 18, cy), (cx - 5, cy + 14), (cx + 20, cy - 14)], fill=fade(GREEN, done), width=7)

def s_bootdev(d, t, dur):
    chrome(d, "STEP 4 · FIND SOMETHING BOOTABLE", "Magic bytes: 55 AA", "Next it hunts for something bootable. Legacy BIOS checks the first sector for the magic bytes 55 AA. UEFI looks for a bootloader file instead.", t, dur)
    devs = [("USB stick", False), ("NVMe SSD", True), ("Network", False)]
    for i, (nm, ok) in enumerate(devs):
        y = 300 + i * 130
        k = prog(t, 0.3 + i * 0.3, 0.8 + i * 0.3)
        scan = 1.2 + i * 0.9
        col = LINE
        if t > scan and i < 2: col = GREEN if ok else RED
        box(d, (160, y, 560, y + 100), PANEL, col, 14, 4, k)
        text(d, (360, y + 50), nm, 36, TXT, "Bold", "mm", k=k)
        if t > scan + 0.4 and i != 1 and i < 1:
            text(d, (580, y + 50), "nothing", 26, RED, "Medium", "lm")
    if t > 2.4:
        k = prog(t, 2.4, 3.0)
        arrow(d, (580, 480), (700, 480), GREEN, 5, k)
        text(d, (1260, 270), "Sector 0  ·  512 bytes", 32, DIM, "Medium", "mm", k=k)
        cols, rows, cw, ch = 32, 16, 30, 22
        x0, y0 = 760, 320
        fill = clamp((t - 2.8) / 2.5)
        tot = cols * rows
        for j in range(int(tot * fill)):
            r, c = divmod(j, cols)
            last = j >= tot - 2
            colr = AMBER if last else (CYAN if j < 440 else DIM)
            a = 1.0 if last else 0.35
            d.rectangle([x0 + c * cw, y0 + r * ch, x0 + c * cw + cw - 6, y0 + r * ch + ch - 6], fill=mix(BG, colr, a))
        if t > 5.4:
            k2 = prog(t, 5.4, 6.0)
            text(d, (x0 + cols * cw - 50, y0 + rows * ch + 40), "55 AA", 44, AMBER, mono=True, anchor="mm", k=k2)
            text(d, (x0, y0 + rows * ch + 40), "boot code", 28, CYAN, "Medium", "lm", k=k2)
        if t > 7.5:
            k3 = prog(t, 7.5, 8.1)
            text(d, (x0, y0 + rows * ch + 100), "UEFI:  \\EFI\\BOOT\\BOOTX64.EFI", 30, GREEN, mono=True, k=k3)

def s_loader(d, t, dur):
    chrome(d, "STEP 5 · BOOTLOADER", "Copy the OS into RAM", "The bootloader, such as GRUB or Windows Boot Manager, copies the operating system kernel into RAM and hands over control.", t, dur)
    chip(d, 200, 360, 360, 220, "SSD", "kernel image", GREEN, prog(t, 0.2, 0.8), pins=False)
    k = prog(t, 0.4, 1.0)
    box(d, (900, 300, 1720, 640), PANEL, CYAN, 14, 4, k)
    text(d, (1310, 270), "RAM", 34, CYAN, "Bold", "mm", k=k)
    nb = 40
    f = clamp((t - 1.4) / 4.5)
    for j in range(int(nb * f)):
        r, c = divmod(j, 10)
        x, y = 930 + c * 78, 330 + r * 76
        col = AMBER if j < 28 else GREEN
        d.rounded_rectangle([x, y, x + 66, y + 62], 8, fill=mix(BG, col, 0.75))
    if 1.4 < t < 6.0:
        p = (t * 1.8) % 1
        x = 580 + p * 300
        d.rounded_rectangle([x - 18, 450, x + 18, 486], 6, fill=AMBER)
    arrow(d, (580, 520), (880, 520), DIM, 4, k)
    if t > 6.2:
        k2 = prog(t, 6.2, 6.8)
        text(d, (1000, 700), "kernel", 30, AMBER, "Bold", k=k2)
        text(d, (1200, 700), "initramfs", 30, GREEN, "Bold", k=k2)
        text(d, (960, 780), "jump to kernel entry point  →", 36, TXT, "Bold", "mm", k=prog(t, 7.0, 7.6))

def s_kernel(d, t, dur):
    chrome(d, "STEP 6 · KERNEL", "The OS takes over", "The kernel takes control of the hardware, loads drivers, mounts your file system, and starts the very first process.", t, dur)
    box(d, (260, 260, 1660, 800), (6, 10, 20), LINE, 14, 3, prog(t, 0.1, 0.6))
    log = ["[    0.000000] Linux version 6.x booting",
           "[    0.012441] Memory: 16 GB available",
           "[    0.214077] PCI: enumerating devices",
           "[    0.402930] usb 1-1: new device found",
           "[    0.611352] nvme0: 1 TB SSD detected",
           "[    0.902118] i915: graphics driver loaded",
           "[    1.301775] EXT4-fs: mounted root filesystem",
           "[    1.623540] Run /sbin/init as PID 1"]
    n = clamp((t - 0.8) / 6.5) * len(log)
    for i in range(int(n)):
        col = GREEN if i == len(log) - 1 else (190, 200, 220)
        text(d, (300, 300 + i * 58), log[i], 32, col, mono=True)
    if int(n) < len(log) and int(t * 3) % 2 == 0:
        d.rectangle([300, 300 + int(n) * 58, 318, 336 + int(n) * 58], fill=TXT)

def s_recap(d, t, dur):
    chrome(d, "RECAP", "Six handoffs", "Power, reset, firmware, bootloader, kernel, login. Six handoffs, all in a few seconds.", t, dur)
    stages = [("Power", AMBER), ("Reset", RED), ("Firmware", CYAN), ("Bootloader", GREEN), ("Kernel", (180, 140, 255)), ("Login", TXT)]
    x0, x1, y = 220, 1700, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.0), y], fill=LINE, width=6)
    for i, (nm, col) in enumerate(stages):
        st = 0.5 + i * 0.6
        k = prog(t, st, st + 0.4)
        if k <= 0: continue
        x = x0 + i * (x1 - x0) / 5
        rr = 22
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fade(col, k))
        text(d, (x, y - 60), nm, 36, col, "Bold", "mm", k=k)
        if i < 5: text(d, (x + (x1 - x0) / 10, y + 50), "hand off", 22, DIM, "Medium", "mm", k=k)
    if t > 4.6:
        k = prog(t, 4.6, 5.4)
        box(d, (710, 590, 1210, 820), PANEL, CYAN, 18, 4, k)
        d.ellipse([925, 615, 995, 685], outline=fade(DIM, k), width=5)
        text(d, (960, 720), "Welcome", 40, TXT, "Bold", "mm", k=k)
        box(d, (800, 760, 1120, 800), (34, 44, 76), LINE, 10, 2, k)

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does a microcontroller", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "actually run your code?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_power", s_power, 12), ("03_vector", s_vector, 12),
          ("04_post", s_post, 11), ("05_bootdev", s_bootdev, 12), ("06_loader", s_loader, 11),
          ("07_kernel", s_kernel, 11), ("08_recap", s_recap, 10), ("09_end", s_end, 6)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    fn(d, t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    if a < 1: im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)
    return im

def render(name, fn, dur):
    out, tmp = f"out/{name}.mp4", f"out/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    if sys.argv[1:] and sys.argv[1] == "preview":
        for name, fn, dur in SCENES:
            frame(fn, dur * 0.8, dur).save(f"out/prev_{name}.jpg", quality=85)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor() as ex:
            list(ex.map(render, *zip(*SCENES)))
