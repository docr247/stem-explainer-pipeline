"""Tech 101, episode 5 Short: three chip languages (UART, SPI, I2C). Style: paper, vertical."""
import math, sys
import style
from style import clamp, prog, pop, grow, mix
from ep5 import (UC, SC, IC, C_CLK, C_MOSI, C_MISO, C_CS, wave, scope, stamp, levf, mini_uart, mini_spi, mini_i2c,
                 uart_scope_frame, spi_lev, kin, drop, popk)

V = style.get("paper", vertical=True)
W, H, FPS = V.W, V.H, V.FPS
VOICE, SPEED, LANG = V.VOICE, V.SPEED, V.LANG
CX = 500                                   # centre of the safe area (x 70..930)

def tl(t, dur): return t * 8.0 / max(dur, 1e-6)

def s_hook(d, t, dur):
    V.headline(d, ["Chips talk in", "3 languages"], t, V.TXT, 300, 92)
    T = tl(t, dur)
    V.chip(d, CX - 170, 540 + drop(T, 0.5), 340, 160, "MCU", None, V.HILITE, kin(T, 0.5))
    for i, (n, c, fn) in enumerate((("UART", UC, mini_uart), ("SPI", SC, mini_spi), ("I²C", IC, mini_i2c))):
        a = 1.4 + i * 0.9
        k = kin(T, a, 0.35)
        y = 860 + i * 150 + drop(T, a, 40)
        V.box(d, (80, y - 62, 920, y + 62), V.PANEL, None, 24, 0, k)
        V.pill(d, (200, y), n, 40, c, k)
        fn(d, 340, 890, y, 18, c, k, prog(T, a + 0.3, a + 1.8) if T < 6 else 1.0, st=V, width=5)
    V.caption_v(d, "Here's how each one looks on a scope.", t, 1330)

def s_uart(d, t, dur):
    V.headline(d, ["UART:", "no clock at all"], t, UC, 280, 92)
    T = tl(t, dur)
    xy = (70, 520, 930, 880)
    scope(d, xy, kin(T, 0.3), (8, 3), st=V, tag="")
    uart_scope_frame(d, T, t, xy, 650, 800, prog(T, 0.8, 5.0), kin(T, 0.5), st=V, lsize=20, vsize=24)
    stamp(d, (CX, 970), "115 200 baud (example)", UC, 40, -4, kin(T, 5.2), popk(T, 5.2), st=V)
    V.text(d, (CX, 1090), "both sides agree the speed first", 38, V.TXT, "SemiBold", "mm", k=kin(T, 5.8))
    V.caption_v(d, "Start bit, 8 data bits, stop bit. Done.", t, 1330)

def s_spi(d, t, dur):
    V.headline(d, ["SPI: a clock", "and a tap"], t, SC, 280, 92)
    T = tl(t, dur)
    scope(d, (70, 480, 930, 1200), kin(T, 0.3), (6, 4), st=V, tag="")
    U, b0, cs, clk, mosi, miso, mb, ib = spi_lev()
    rows = [("CS", cs, C_CS, 600), ("SCLK", clk, C_CLK, 740), ("MOSI", mosi, C_MOSI, 880), ("MISO", miso, C_MISO, 1020)]
    rv = prog(T, 1.0, 5.5)
    for i, (n, lev, c, yc) in enumerate(rows):
        k = kin(T, 0.5 + i * 0.2)
        V.text(d, (100, yc - 58), n, 30, c, "Bold", "lm", k=k)
        if n == "MISO":
            wave(d, lev, 100, 900, yc + 40, yc - 30, c, k, rv, 6, u0=1.0 / U, u1=9.6 / U, st=V)
        else:
            wave(d, lev, 100, 900, yc + 40, yc - 30, c, k, rv, 6, st=V)
    V.text(d, (CX, 1160), "1 bit out + 1 bit back per tick", 34, V.TXT, "Bold", "mm", k=kin(T, 5.8))
    V.caption_v(d, "Fast, and a select wire for every chip.", t, 1330)

def s_i2c(d, t, dur):
    V.headline(d, ["I²C: a roll call", "on two wires"], t, IC, 280, 84)
    T = tl(t, dur)
    k = kin(T, 0.4)
    ysda, yscl = 620, 680
    V.line(d, [(80, ysda), (920, ysda)], IC, 7, k)
    V.line(d, [(80, yscl), (920, yscl)], mix(IC, V.TXT, 0.45), 7, k)
    V.text(d, (80, ysda - 32), "SDA", 30, IC, "Bold", "lm", k=k)
    V.text(d, (80, yscl + 36), "SCL", 30, mix(IC, V.TXT, 0.45), "Bold", "lm", k=k)
    devs = [("0x48", 185), ("0x50", 395), ("0x68", 605), ("0x3C", 815)]
    ci = 1
    for i, (ad, cx) in enumerate(devs):
        a = 0.8 + i * 0.4
        kk = kin(T, a)
        lit = T > 3.4 and i == ci
        for xx, yy in ((cx - 30, ysda), (cx + 30, yscl)):
            V.line(d, [(xx, yy), (xx, 790)], IC, 4, kk)
            V.circle(d, (xx, yy), 8, IC, None, k=kk, shadow=False)
        V.chip(d, cx - 95, 790 + drop(T, a), 190, 120, ad, None, IC if lit else V.LINE, kk, pins=False)
    if T > 2.4:
        V.pill(d, (CX, 510 + drop(T, 2.4, 30)), "calling 0x50...", 38, V.HILITE, kin(T, 2.4, 0.3))
    if T > 3.4:
        stamp(d, (395, 990), "here! (ACK)", V.GOOD, 38, -6, 1.0, popk(T, 3.4), st=V)
    mini_i2c(d, 110, 890, 1160, 22, IC, kin(T, 4.4), prog(T, 4.4, 6.4), st=V, width=5)
    V.caption_v(d, "Only the chip that's called answers.", t, 1330)

def s_cta(d, t, dur):
    T = tl(t, dur)
    V.headline(d, ["UART vs SPI vs I²C", "Which one when?"], t, V.TXT, 560, 76)
    k2 = kin(T, 1.2, 0.5)
    p = popk(T, 1.2)
    if p > 0.02:
        V.box(d, (CX - 330 * p, 900 - 70 * p, CX + 330 * p, 900 + 70 * p), V.HILITE, None, 70, 0, min(1, p * 1.5))
        V.text(d, (CX, 900), "Watch the full video", 54, V.ON_ACCENT, "Bold", "mm", k=kin(T, 1.6, 0.3))
    V.arrow(d, (CX, 1160), (CX, 1000), V.HILITE, 10, kin(T, 2.0))
    for i, c in enumerate((UC, SC, IC)):
        V.circle(d, (CX - 120 + i * 120, 760), 22 * max(0.01, popk(T, 0.8 + i * 0.2)), c, None, k=k2)

SCENES = [("s1", s_hook, 6), ("s2", s_uart, 8), ("s3", s_spi, 8), ("s4", s_i2c, 8), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Chips on a circuit board talk to each other in three languages. Here's what each one looks like on an oscilloscope.",
 "s2": "You-art has no clock wire. Both sides agree a speed in advance. Then it's a start bit, eight data bits, and a stop bit. Done.",
 "s3": "S P I has a clock, and a chip select wire for every chip. On each tick, one bit goes out, and one bit comes back. Fast!",
 "s4": "I squared C shares just two wires between many chips. The controller calls an address, like a roll call, and only that chip answers.",
 "s5": "So which one should you use, and when? Watch the full video.",
}
OUTPUT = "ep5_short_three_chip_languages_narrated.mp4"

def render(name, fn, dur): V.render_to("short5", name, fn, dur)

if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    V.preview("short5", SCENES)
