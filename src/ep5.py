import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
UART_C, SPI_C, I2C_C = AMBER, CYAN, GREEN

def bits_wave(d, x0, y0, w, h, bits, col, k, reveal=1.0, labels=None, lab_col=DIM):
    n = len(bits); bw = w / n
    pts = []
    m = int(n * reveal + 0.999)
    for i, b in enumerate(bits[:m]):
        y = y0 if b else y0 + h
        pts += [(x0 + i * bw, y), (x0 + (i + 1) * bw, y)]
        if labels:
            text(d, (x0 + i * bw + bw / 2, y0 + h + 34), labels[i], 24, lab_col, "Bold", "mm", mono=True, k=k)
    if len(pts) > 1: d.line(pts, fill=fade(col, k), width=6)

def s_hook(d, t, dur):
    chrome(d, "", "", "Your microcontroller is surrounded by other chips: sensors, displays, memory. They all talk through just a few wires, in one of three languages.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 780, 380, 360, 220, "MCU", "", PURPLE, k)
    parts = [("Sensor", 220, 300, I2C_C, "I2C"), ("Display", 220, 620, SPI_C, "SPI"), ("GPS module", 1440, 460, UART_C, "UART")]
    for i, (n, x, y, c, proto) in enumerate(parts):
        kk = prog(t, 0.8 + i * 0.6, 1.3 + i * 0.6)
        box(d, (x, y, x + 300, y + 120), PANEL, c, 14, 4, kk)
        text(d, (x + 150, y + 60), n, 34, TXT, "Bold", "mm", k=kk)
        if x < 780:
            d.line([x + 300, y + 60, 780, 490], fill=fade(c, kk), width=5)
            text(d, ((x + 300 + 780) / 2, (y + 60 + 490) / 2 - 30), proto, 30, c, "Bold", "mm", k=prog(t, 3.0, 3.5))
        else:
            d.line([1140, 490, x, y + 60], fill=fade(c, kk), width=5)
            text(d, ((1140 + x) / 2, 450), proto, 30, c, "Bold", "mm", k=prog(t, 3.0, 3.5))

def s_uart_wires(d, t, dur):
    chrome(d, "1 · UART", "Two wires, no clock", "UART is the simplest. Two wires, crossed over: my transmit goes to your receive. There's no clock wire at all, so both sides must agree on the speed in advance, like 115,200 bits per second.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 200, 360, 340, 240, "MCU", "", PURPLE, k, pins=False)
    chip(d, 1380, 360, 340, 240, "GPS", "module", UART_C, k, pins=False)
    kk = prog(t, 1.0, 1.6)
    d.line([540, 420, 1380, 540], fill=fade(UART_C, kk), width=6)
    d.line([540, 540, 1380, 420], fill=fade(UART_C, kk), width=6)
    text(d, (570, 400), "TX", 28, UART_C, "Bold", "lm", mono=True, k=kk)
    text(d, (570, 565), "RX", 28, UART_C, "Bold", "lm", mono=True, k=kk)
    text(d, (1350, 400), "TX", 28, UART_C, "Bold", "rm", mono=True, k=kk)
    text(d, (1350, 565), "RX", 28, UART_C, "Bold", "rm", mono=True, k=kk)
    if t > 3.0:
        kk = prog(t, 3.0, 3.5)
        box(d, (640, 680, 1280, 780), mix(BG, UART_C, 0.18), UART_C, 14, 3, kk)
        text(d, (960, 730), "both agree: 115200 baud", 36, UART_C, "Bold", "mm", mono=True, k=kk)

def s_uart_frame(d, t, dur):
    chrome(d, "1 · UART FRAME", "Sending the letter A", "To send the letter A, the line drops low for a start bit, then sends eight data bits, least significant bit first, then goes high again for a stop bit.", t, dur)
    k = prog(t, 0.2, 0.6)
    text(d, (W // 2, 290), "'A' = 0x41 = 0100 0001", 44, TXT, "Bold", "mm", mono=True, k=k)
    bits = [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1]
    labels = ["idle", "S", "1", "0", "0", "0", "0", "0", "1", "0", "P", "idle"]
    bits_wave(d, 260, 420, 1400, 160, bits, UART_C, k, clamp((t - 1.0) / 4.5), labels)
    if t > 6.0:
        kk = prog(t, 6.0, 6.5)
        text(d, (260 + 1400 / 12 * 1.5, 700), "start", 28, RED, "Bold", "mm", k=kk)
        text(d, (260 + 1400 / 12 * 6, 700), "8 data bits, LSB first", 28, UART_C, "Bold", "mm", k=kk)
        text(d, (260 + 1400 / 12 * 10.5, 700), "stop", 28, GREEN, "Bold", "mm", k=kk)

def s_spi_wires(d, t, dur):
    chrome(d, "2 · SPI", "Fast, with its own clock", "SPI adds a clock wire, so the controller sets the pace. Data goes out on one wire and comes back on another at the same time. And every chip gets its own chip-select line.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 160, 330, 340, 380, "MCU", "controller", PURPLE, k, pins=False)
    chip(d, 1400, 280, 340, 180, "Display", "", SPI_C, k, pins=False)
    chip(d, 1400, 560, 340, 180, "SD card", "", SPI_C, k, pins=False)
    names = ["SCLK", "MOSI", "MISO"]
    for i, n in enumerate(names):
        kk = prog(t, 0.8 + i * 0.4, 1.2 + i * 0.4)
        y = 400 + i * 70
        d.line([500, y, 1200, y], fill=fade(SPI_C, kk), width=5)
        d.line([1200, y, 1200, 330 + i * 30], fill=fade(SPI_C, kk), width=3)
        d.line([1200, 330 + i * 30, 1400, 330 + i * 30], fill=fade(SPI_C, kk), width=3)
        d.line([1200, y, 1200, 610 + i * 30], fill=fade(SPI_C, kk), width=3)
        d.line([1200, 610 + i * 30, 1400, 610 + i * 30], fill=fade(SPI_C, kk), width=3)
        text(d, (520, y - 24), n, 26, SPI_C, "Bold", "lm", mono=True, k=kk)
    kk = prog(t, 2.6, 3.2)
    d.line([500, 640, 1100, 640, 1100, 430, 1400, 430], fill=fade(AMBER, kk), width=4)
    d.line([500, 690, 1150, 690, 1150, 710, 1400, 710], fill=fade(RED, kk), width=4)
    text(d, (520, 616), "CS1", 26, AMBER, "Bold", "lm", mono=True, k=kk)
    text(d, (520, 666), "CS2", 26, RED, "Bold", "lm", mono=True, k=kk)

def s_spi_wave(d, t, dur):
    chrome(d, "2 · SPI TIMING", "One bit per clock tick", "Pull chip-select low, and the clock starts ticking. On every tick, one bit goes out, and one bit comes back. At tens of megahertz, that's why displays and SD cards love SPI.", t, dur)
    k = prog(t, 0.2, 0.6)
    rv = clamp((t - 0.8) / 5.0)
    rows = [("CS", RED, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
            ("SCLK", SPI_C, [0, 0] + [1, 0] * 8),
            ("MOSI", AMBER, [0, 0] + sum([[b, b] for b in [1, 0, 1, 1, 0, 0, 1, 0]], [])),
            ("MISO", GREEN, [0, 0] + sum([[b, b] for b in [0, 1, 1, 0, 1, 0, 0, 1]], []))]
    for i, (n, c, bits) in enumerate(rows):
        y = 280 + i * 140
        text(d, (300, y + 40), n, 32, c, "Bold", "rm", mono=True, k=k)
        bits_wave(d, 340, y, 1360, 80, bits, c, k, rv)
    if t > 6.2:
        text(d, (W // 2, 860 - 40), "full duplex: out and in at the same time", 30, DIM, "Medium", "mm", k=prog(t, 6.2, 6.7))

def s_i2c_bus(d, t, dur):
    chrome(d, "3 · I2C", "Two wires, many chips", "I2C uses just two wires, shared by every chip on the bus: data and clock, each held high by a pull-up resistor. Every chip has its own address, so dozens can share the same two wires.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 140, 380, 300, 200, "MCU", "controller", PURPLE, k, pins=False)
    d.line([440, 440, 1780, 440], fill=fade(I2C_C, k), width=6)
    d.line([440, 520, 1780, 520], fill=fade(I2C_C, k), width=6)
    text(d, (470, 410), "SDA", 26, I2C_C, "Bold", "lm", mono=True, k=k)
    text(d, (470, 550), "SCL", 26, I2C_C, "Bold", "lm", mono=True, k=k)
    kk = prog(t, 0.8, 1.3)
    for x in (560, 640):
        d.line([x, 440 if x == 560 else 520, x, 300], fill=fade(AMBER, kk), width=4)
        d.rectangle([x - 10, 330, x + 10, 380], outline=fade(AMBER, kk), width=3)
    text(d, (600, 280), "pull-ups → 3.3 V", 24, AMBER, "Bold", "mm", k=kk)
    devs = [("OLED", "0x3C"), ("IMU", "0x68"), ("Temp sensor", "0x76")]
    for i, (n, a) in enumerate(devs):
        kk = prog(t, 1.6 + i * 0.6, 2.0 + i * 0.6)
        x = 860 + i * 320
        d.line([x + 120, 440, x + 120, 620], fill=fade(I2C_C, kk), width=3)
        d.line([x + 160, 520, x + 160, 620], fill=fade(I2C_C, kk), width=3)
        box(d, (x, 620, x + 280, 760), PANEL, I2C_C, 14, 3, kk)
        text(d, (x + 140, 665), n, 32, TXT, "Bold", "mm", k=kk)
        text(d, (x + 140, 715), a, 32, AMBER, "Bold", "mm", mono=True, k=kk)

def s_i2c_frame(d, t, dur):
    chrome(d, "3 · I2C TRANSACTION", "Calling a chip by name", "A transaction starts with a start condition, then the address of the chip you want, plus a read or write bit. Only that chip answers with an acknowledge. Then the data flows, and a stop condition ends it.", t, dur)
    parts = [("START", RED, 150), ("ADDR 0x68", AMBER, 300), ("W", PURPLE, 90), ("ACK", GREEN, 120),
             ("DATA", I2C_C, 260), ("ACK", GREEN, 120), ("STOP", RED, 150)]
    x = 960 - sum(p[2] + 16 for p in parts) / 2
    for i, (n, c, w) in enumerate(parts):
        kk = prog(t, 0.6 + i * 0.6, 1.0 + i * 0.6)
        box(d, (x, 380, x + w, 490), mix(BG, c, 0.22), c, 12, 4, kk)
        text(d, (x + w / 2, 435), n, 30, c, "Bold", "mm", mono=True, k=kk)
        x += w + 16
    if t > 5.2:
        kk = prog(t, 5.2, 5.7)
        text(d, (W // 2, 620), "writing to the IMU at 0x68, while every other chip stays quiet", 32, DIM, "Medium", "mm", k=kk)

def s_compare(d, t, dur):
    chrome(d, "SIDE BY SIDE", "Which one wins?", "None of them wins. UART for simple point-to-point links. SPI when you need speed. I2C when you want lots of chips on just two wires.", t, dur)
    hdr = ["", "UART", "SPI", "I2C"]
    rows = [("Wires", "2", "4 + 1 per chip", "2"), ("Clock", "none", "yes", "yes"),
            ("Devices", "2", "1 + many", "many (addressed)"), ("Speed", "~115 kbps typ.", "10s of MHz", "100 k–1 MHz"),
            ("Best for", "GPS, debug", "displays, SD", "sensors")]
    cols = [180, 560, 960, 1360]
    cw = [360, 380, 380, 380]
    k = prog(t, 0.2, 0.6)
    for j, h in enumerate(hdr[1:], 1):
        c = [UART_C, SPI_C, I2C_C][j - 1]
        text(d, (cols[j] + cw[j] / 2, 280), h, 44, c, "Bold", "mm", k=k)
    for i, r in enumerate(rows):
        kk = prog(t, 0.8 + i * 0.5, 1.2 + i * 0.5)
        y = 330 + i * 90
        d.line([180, y, 1740, y], fill=fade(LINE, kk), width=2)
        text(d, (cols[0] + 10, y + 45), r[0], 32, DIM, "Bold", "lm", k=kk)
        for j in range(1, 4):
            text(d, (cols[j] + cw[j] / 2, y + 45), r[j], 32, TXT, "Medium", "mm", k=kk)

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does PWM", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "dim an LED?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 9), ("02_uart", s_uart_wires, 11), ("03_uart_frame", s_uart_frame, 10),
          ("04_spi", s_spi_wires, 11), ("05_spi_wave", s_spi_wave, 10), ("06_i2c", s_i2c_bus, 11),
          ("07_i2c_frame", s_i2c_frame, 10), ("08_compare", s_compare, 11), ("09_end", s_end, 6)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep5/{name}.mp4", f"ep5/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep5", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    s = Image.new("RGB", (W * 3, H * 3))
    for i, (_, fn, dur) in enumerate(SCENES):
        s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
    s.resize((2880, 1620)).save("ep5/sheet.jpg", quality=85)
