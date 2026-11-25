import os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED)
from short import headline, caption, W, H, FPS
from ep5 import bits_wave, PURPLE, UART_C, SPI_C, I2C_C

def s_hook(d, t, dur):
    headline(d, ["Chips talk in", "3 languages"], t, TXT, 300, 84)
    k = prog(t, 0.3, 0.8)
    chip(d, 340, 560, 400, 220, "MCU", "", PURPLE, k)
    for i, (n, c) in enumerate([("UART", UART_C), ("SPI", SPI_C), ("I2C", I2C_C)]):
        kk = prog(t, 1.0 + i * 0.5, 1.4 + i * 0.5)
        y = 900 + i * 110
        box(d, (290, y, 790, y + 90), mix(BG, c, 0.2), c, 16, 4, kk)
        text(d, (540, y + 45), n, 52, c, "Bold", "mm", k=kk)
    caption(d, "Here's each one, fast.", t, 1300)

def s_uart(d, t, dur):
    headline(d, ["UART: no clock,", "just agree on speed"], t, UART_C, 260, 64)
    k = prog(t, 0.2, 0.6)
    chip(d, 90, 470, 300, 170, "MCU", "", PURPLE, k, pins=False)
    chip(d, 690, 470, 300, 170, "GPS", "", UART_C, k, pins=False)
    d.line([390, 510, 690, 600], fill=fade(UART_C, k), width=6)
    d.line([390, 600, 690, 510], fill=fade(UART_C, k), width=6)
    bits_wave(d, 120, 760, 840, 110, [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1], UART_C, k, clamp((t - 1.0) / 3.0))
    text(d, (540, 1000), "115200 baud", 56, UART_C, "Bold", "mm", mono=True, k=prog(t, 3.0, 3.5))
    caption(d, "Two wires. Perfect for GPS and debug.", t, 1250)

def s_spi(d, t, dur):
    headline(d, ["SPI: fast, but a", "wire for every chip"], t, SPI_C, 260, 64)
    k = prog(t, 0.2, 0.6)
    rv = clamp((t - 0.8) / 3.5)
    rows = [("SCLK", SPI_C, [0] + [1, 0] * 8), ("MOSI", AMBER, [0] + sum([[b, b] for b in [1, 0, 1, 1, 0, 0, 1, 0]], [])),
            ("MISO", GREEN, [0] + sum([[b, b] for b in [0, 1, 1, 0, 1, 0, 0, 1]], []))]
    for i, (n, c, bits) in enumerate(rows):
        y = 480 + i * 180
        text(d, (90, y - 30), n, 34, c, "Bold", "lm", mono=True, k=k)
        bits_wave(d, 90, y, 900, 90, bits, c, k, rv)
    text(d, (540, 1060), "10s of MHz", 60, SPI_C, "Bold", "mm", mono=True, k=prog(t, 3.6, 4.1))
    caption(d, "Displays and SD cards love it.", t, 1250)

def s_i2c(d, t, dur):
    headline(d, ["I2C: two wires,", "many chips"], t, I2C_C, 260, 70)
    k = prog(t, 0.2, 0.6)
    d.line([180, 460, 180, 1100], fill=fade(I2C_C, k), width=7)
    d.line([250, 460, 250, 1100], fill=fade(I2C_C, k), width=7)
    text(d, (180, 440), "SDA", 28, I2C_C, "Bold", "mb", mono=True, k=k)
    text(d, (250, 440), "SCL", 28, I2C_C, "Bold", "mb", mono=True, k=k)
    devs = [("OLED", "0x3C"), ("IMU", "0x68"), ("Temp", "0x76")]
    for i, (n, a) in enumerate(devs):
        kk = prog(t, 0.8 + i * 0.6, 1.2 + i * 0.6)
        y = 520 + i * 200
        hot = i == 1 and t > 3.2
        d.line([180, y + 60, 520, y + 60], fill=fade(I2C_C, kk), width=3)
        d.line([250, y + 90, 520, y + 90], fill=fade(I2C_C, kk), width=3)
        box(d, (520, y, 960, y + 150), mix(BG, AMBER, 0.25) if hot else PANEL, AMBER if hot else I2C_C, 16, 5 if hot else 3, kk)
        text(d, (560, y + 75), n, 46, TXT, "Bold", "lm", k=kk)
        text(d, (920, y + 75), a, 46, AMBER, "Bold", "rm", mono=True, k=kk)
    caption(d, "Call a chip by its address. Only it answers.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "Which one", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "should you use?", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_uart, 8), ("s3", s_spi, 8), ("s4", s_i2c, 8), ("s5", s_cta, 5)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short5/{name}.mp4", f"short5/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short5", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short5/sheet.jpg", quality=85)
