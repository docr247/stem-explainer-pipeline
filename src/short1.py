"""Tech 101, episode 1 Short: what happens the instant you press power (chalk style, vertical)."""
import math, sys
import style
from style import clamp, prog, mix
from ep1 import (write, stroke, garrow, carrow, sketch, gcircle, tick, power_icon, dot, along, monitor, rail_v,
                 STAGES, C_PWR, C_RST, C_FW, C_DEV, C_BL, C_K)

V = style.get("chalk", vertical=True)
W, H, FPS = V.W, V.H, V.FPS
VOICE, SPEED, LANG = V.VOICE, V.SPEED, V.LANG


def s_hook(d, t, dur):
    V.headline(d, ["Your processor wakes", "up knowing just", "ONE address"], t, V.TXT, 270, 74)
    cx, cy, r = 540, 830, 160
    gcircle(d, (cx, cy), r, V.LINE, prog(t, 0.3, 1.0), 7, fill=V.PANEL)
    power_icon(d, cx, cy + 10, r * 0.48, mix(V.TXT, V.HILITE, prog(t, 1.2, 1.5)), prog(t, 0.5, 1.3), 12)
    if t > 1.3:
        for g in range(3):
            u = ((t - 1.3) * 0.6 + g / 3) % 1.0
            gcircle(d, (cx, cy), r + 20 + u * 110, mix(V.BG, V.HILITE, 0.8 * (1 - u)), 1.0, 5)
    write(d, (W // 2, 1150), "hex FFFF FFF0", 80, V.HILITE, t, 1.8, 2.8)
    V.caption_v(d, "What happens the instant you press power?", t, 1300)


def s_power(d, t, dur):
    V.headline(d, ["First: wait for", "steady power"], t, C_PWR, 270, 80)
    x0, y0, w, h = 150, 480, 780, 380
    stroke(d, [(x0, y0), (x0, y0 + h), (x0 + w, y0 + h)], V.LINE, prog(t, 0.3, 0.8), 4)
    vy = lambda v: y0 + h - v / 13.5 * h
    reveal = prog(t, 0.6, 2.4)
    for Vv, c, delay, name in ((12, C_PWR, 0.05, "12 V"), (5, V.ACCENT, 0.09, "5 V"), (3.3, V.EXTRA, 0.12, "3.3 V")):
        pts = [(x0 + px, vy(rail_v(Vv, px / w, delay))) for px in range(0, int(w * reveal), 5)]
        if len(pts) > 1: V.line(d, pts, c, 6)
        write(d, (x0 + w, vy(Vv) + (40 if Vv < 4 else -30)), name, 34, c, t, 1.0, anchor="rm")
    # power good step
    yb = 1060
    write(d, (x0, yb - 90), "Power Good", 40, V.GOOD, t, 2.4, anchor="lm")
    stroke(d, [(x0, yb), (x0 + 520, yb), (x0 + 520, yb - 60), (x0 + w, yb - 60)], V.GOOD, prog(t, 2.6, 3.6), 6)
    write(d, (x0, yb + 50), "goes high only when every rail is steady", 32, V.DIM, t, 3.4, w="Medium", anchor="lm")
    V.caption_v(d, "Rails settle, then Power Good goes high.", t, 1300)


def s_vector(d, t, dur):
    V.headline(d, ["Then: the first", "instruction"], t, C_RST, 270, 80)
    bx0, bx1, by0, by1 = 170, 300, 460, 1180
    sketch(d, (bx0, by0, bx1, by1), V.LINE, prog(t, 0.3, 0.9), r=6)
    kf = prog(t, 0.8, 1.3)
    if kf > 0: d.rectangle([bx0 + 5, by0 + 5, bx1 - 5, by0 + 110], fill=V.fade(mix(V.PANEL, C_FW, 0.45), kf))
    kr = prog(t, 1.0, 1.5)
    if kr > 0: d.rectangle([bx0 + 5, by1 - 280, bx1 - 5, by1 - 5], fill=V.fade(mix(V.PANEL, V.DIM, 0.25), kr))
    write(d, (bx0 + 65, by0 - 30), "4 GB", 34, V.DIM, t, 0.6)
    write(d, (bx0 + 65, by1 + 40), "0", 34, V.DIM, t, 0.6)
    write(d, (340, by0 + 80), "firmware chip", 34, C_FW, t, 1.2, anchor="lm")
    write(d, (340, by1 - 140), "RAM: not ready yet", 34, V.DIM, t, 1.4, w="Medium", anchor="lm")
    garrow(d, (900, by0 + 16), (bx1 + 10, by0 + 16), C_RST, prog(t, 1.8, 2.4), 7)
    write(d, (620, 700), "hex FFFF FFF0", 66, V.HILITE, t, 2.4, 3.2)
    write(d, (620, 780), "16 bytes below 4 GB", 36, V.TXT, t, 3.0, w="Medium")
    write(d, (620, 900), "the \"reset vector\"", 44, C_RST, t, 3.6)
    write(d, (620, 960), "(on x86 PCs)", 30, V.DIM, t, 4.0, w="Medium")
    V.caption_v(d, "The reset vector: a jump into the firmware.", t, 1300)


def s_relay(d, t, dur):
    V.headline(d, ["Then a relay", "of handoffs"], t, C_BL, 270, 80)
    steps = [("firmware: POST, RAM", C_FW), ("55 AA sector or EFI file", C_DEV), ("bootloader", C_BL), ("kernel", C_K)]
    for i, (n, c) in enumerate(steps):
        y = 470 + i * 190
        a = 0.4 + i * 0.7
        sketch(d, (150, y, 930, y + 120), c, prog(t, a, a + 0.5), fill=mix(V.PANEL, c, 0.12))
        write(d, (540, y + 60), n, 44, c, t, a + 0.2)
        if i < 3: garrow(d, (540, y + 126), (540, y + 182), V.TXT, prog(t, a + 0.5, a + 0.8), 5)
    if t > 0.8:
        u = clamp((t - 0.8) / 3.0)
        dot(d, (110, 530 + u * 570), 16, V.HILITE)
    kl = prog(t, 3.4, 4.0)
    write(d, (540, 1250), "...then the login screen", 44, V.GOOD, t, 3.6, 4.4)
    V.caption_v(d, "Each stage loads the next, then jumps.", t, 1330)


def s_cta(d, t, dur):
    for i, (_, c, _) in enumerate(STAGES):
        dot(d, (240 + i * 120, 420), 18, c, prog(t, 0.2 + i * 0.15, 0.5 + i * 0.15))
    stroke(d, [(240, 420), (840, 420)], V.DIM, prog(t, 0.2, 1.1), 3)
    write(d, (W // 2, 560), "Power button", 84, V.TXT, t, 0.2, 0.9)
    write(d, (W // 2, 670), "to login screen,", 84, V.TXT, t, 0.7, 1.4)
    write(d, (W // 2, 780), "step by step", 84, V.HILITE, t, 1.2, 1.9)
    k2 = prog(t, 1.6, 2.2)
    sketch(d, (170, 900, 910, 1040), V.ACCENT, k2, r=60, width=5, fill=mix(V.PANEL, V.ACCENT, 0.2))
    write(d, (W // 2, 970), "Watch the full video", 56, V.ACCENT, t, 2.0, 2.6)
    garrow(d, (W // 2, 1250), (W // 2, 1070), V.ACCENT, prog(t, 2.4, 3.0), 8)


SCENES = [("s1", s_hook, 6), ("s2", s_power, 7), ("s3", s_vector, 7), ("s4", s_relay, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Your processor wakes up knowing just one address. So what happens the instant you press power?",
 "s2": "First, it waits. The power supply's rails ramp up and settle. Only when they're all steady does a signal called Power Good go high, and the processor is let out of reset.",
 "s3": "Then it fetches its first instruction from a hard-wired address: on x eighty six, hex, F F F F, F F F zero. The firmware chip sits right there. It's the reset vector.",
 "s4": "From there, it's a relay. The firmware checks the hardware, finds a boot sector or a boot file, and runs the bootloader. That loads the kernel, and the kernel brings up your login screen.",
 "s5": "The whole journey, step by step, is in the full video.",
}
OUTPUT = "ep1_short_computer_boot_narrated.mp4"


def render(name, fn, dur): V.render_to("short1", name, fn, dur)

if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    print(V.preview("short1", SCENES))
