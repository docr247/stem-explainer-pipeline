"""Tech 101, episode 4 Short: USB asks 'who are you?'  (chalk style, 1080x1920)"""
import math, sys
import style
from style import clamp, ease, prog
from ep4 import write, chalk, chalk_arrow, sketch_box, resistor, ground, joint, dots, icon, plug, badge, trace, A

V = style.get("chalk", vertical=True)
W, H, FPS = V.W, V.H, V.FPS
VOICE, SPEED, LANG = V.VOICE, V.SPEED, V.LANG
CX = 500          # centre of the safe area (x 70..930)
DP, DM, VB = V.HILITE, V.EXTRA, V.BAD


def s_hook(d, t, dur):
    V.headline(d, ["You plug it in.", "It has no idea", "what it is."], t, V.TXT, 270, 80)
    k = A(t, dur, 0.05, 0.15)
    sketch_box(d, (110, 620, 560, 1000), V.ACCENT, k, st=V)
    write(d, (335, 665), "computer", 38, V.ACCENT, k, "Bold", "mm", st=V)
    chalk(d, [(560, 780), (525, 780), (525, 850), (560, 850)], V.LINE, k, 4, V)
    pin = ease(clamp((t / dur - 0.1) / 0.2))
    px = 900 - 330 * pin
    icon(d, "keyboard", 760, 1130, 1.3, V.GOOD, k, V)
    chalk(d, [(px + 150, 815), (px + 200, 815), (880, 960), (840, 1070)], V.DIM, k, 5, V)
    plug(d, px, 815, 0.72, V.GOOD, k, -1, V)
    write(d, (335, 840), "?", 200, V.HILITE, A(t, dur, 0.35, 0.45), "Bold", "mm", st=V)
    V.caption_v(d, "So it has to ask.", t, 1330)


def s_resistor(d, t, dur):
    V.headline(d, ["A resistor", "says hello"], t, DP, 270, 88)
    k = A(t, dur, 0.04, 0.14)
    # D+ and D- lines, with the device's pull-up on D+
    chalk(d, [(110, 640), (900, 640)], VB, k, 5, V)
    write(d, (110, 605), "3.3 V (in the device)", 32, VB, k, "Bold", "lm", st=V)
    chalk(d, [(110, 800), (900, 800)], DP, k, 5, V)
    chalk(d, [(110, 900), (900, 900)], DM, k, 5, V)
    write(d, (110, 762), "D+", 38, DP, k, "Bold", "lm", st=V)
    write(d, (110, 862), "D−", 38, DM, k, "Bold", "lm", st=V)
    kr = A(t, dur, 0.12, 0.25)
    resistor(d, (600, 640), (600, 800), DP, kr, V)
    joint(d, 600, 800, DP, kr, V)
    V.text(d, (630, 720), "1.5 kΩ", 32, DP, "Bold", "lm", mono=True, k=kr)
    if t / dur > 0.3: dots(d, (600, 660), (600, 790), t, DP, 2, 0.9, 7, 1, V)
    # D+ voltage rising
    kg = A(t, dur, 0.28, 0.36)
    gx, gy, gw, gh = 130, 1000, 760, 200
    chalk(d, [(gx, gy), (gx, gy + gh), (gx + gw, gy + gh)], V.LINE, kg, 3, V)
    write(d, (gx + 14, gy + 4), "D+ voltage", 30, DP, kg, "Regular", "la", st=V)
    trace(d, gx, gy, gw, gh, lambda u: 0.05 if u < 0.35 else 0.05 + 0.75 * (1 - math.exp(-(u - 0.35) * 40)),
          A(t, dur, 0.3, 0.55), DP, 6, st=V)
    write(d, (gx + gw, gy + 50), "≈ 3 V", 40, DP, A(t, dur, 0.5, 0.58), "Bold", "ra", st=V)
    V.caption_v(d, "The device pulls D+ up. The host sees it rise.", t, 1330)


def s_who(d, t, dur):
    V.headline(d, ["\"Who are", "you?\""], t, V.ACCENT, 270, 92)
    k = A(t, dur, 0.04, 0.12)
    sketch_box(d, (110, 480, 470, 640), V.ACCENT, k, st=V)
    write(d, (290, 560), "HOST", 44, V.ACCENT, k, "Bold", "mm", st=V)
    sketch_box(d, (560, 480, 920, 640), V.GOOD, k, st=V)
    write(d, (700, 560), "device", 40, V.GOOD, k, "Bold", "mm", st=V)
    badge(d, (850, 560), "0", V.HILITE, k, 40, 40, V)
    ka = A(t, dur, 0.15, 0.3)
    chalk(d, [(290, 650), (290, 760), (740, 760), (740, 700)], V.ACCENT, ka, 5, V)
    if ka > 0.95: chalk_arrow(d, (740, 710), (740, 655), V.ACCENT, 1, 5, V)
    write(d, (500, 720), "GET_DESCRIPTOR", 34, V.ACCENT, ka, "Bold", "mm", st=V)
    kc = A(t, dur, 0.35, 0.45)
    sketch_box(d, (110, 830, 920, 1210), V.HILITE, kc, st=V)
    write(d, (CX, 880), "device descriptor: 18 bytes", 36, V.HILITE, kc, "Bold", "mm", st=V)
    for i, (a, b) in enumerate((("vendor ID", "0x1234"), ("product ID", "0x5678"))):
        kk = A(t, dur, 0.45 + i * 0.1, 0.55 + i * 0.1)
        y = 970 + i * 100
        write(d, (160, y), a, 44, V.TXT, kk, "Bold", "lm", st=V)
        write(d, (870, y), b, 50, V.HILITE, kk, "Bold", "rm", mono=True, st=V)
    V.pill(d, (CX, 1170), "example values", 26, V.DIM, A(t, dur, 0.6, 0.66))
    V.caption_v(d, "At address 0, it answers with a name tag.", t, 1330)


def s_class(d, t, dur):
    V.headline(d, ["The class code", "picks the driver"], t, V.GOOD, 270, 80)
    rows = [("03", "HID", "keyboard, mouse", "keyboard", V.ACCENT), ("08", "storage", "flash drive", "drive", V.HILITE),
            ("01", "audio", "headset", "headset", V.EXTRA)]
    for i, (code, nm, ex, ic, c) in enumerate(rows):
        kk = A(t, dur, 0.06 + i * 0.12, 0.16 + i * 0.12)
        y = 470 + i * 220
        sketch_box(d, (110, y, 920, y + 190), c, kk, st=V)
        V.text(d, (150, y + 60), "hex", 30, V.DIM, "Regular", "lm", k=kk)
        write(d, (150, y + 125), code, 70, c, kk, "Bold", "lm", mono=True, st=V)
        write(d, (330, y + 65), nm, 50, V.TXT, (kk - 0.2) / 0.8, "Bold", "lm", st=V)
        write(d, (330, y + 130), ex, 36, V.DIM, (kk - 0.4) / 0.6, "Regular", "lm", st=V)
        icon(d, ic, 800, y + 95 + 4 * math.sin(t * 3 + i), 0.8, c, kk, V)
    write(d, (CX, 1190), "no install needed", 52, V.GOOD, A(t, dur, 0.55, 0.65), "Bold", "mm", st=V)
    V.caption_v(d, "A class driver loads, and it just works.", t, 1330)


def s_cta(d, t, dur):
    k = A(t, dur, 0.04, 0.2)
    write(d, (CX, 560), "The whole USB", 80, V.TXT, k, "Bold", "mm", st=V)
    write(d, (CX, 660), "conversation,", 80, V.TXT, A(t, dur, 0.1, 0.26), "Bold", "mm", st=V)
    write(d, (CX, 760), "step by step", 80, V.HILITE, A(t, dur, 0.18, 0.34), "Bold", "mm", st=V)
    k2 = A(t, dur, 0.3, 0.45)
    sketch_box(d, (150, 900, 850, 1030), V.ACCENT, k2, 60, 5, st=V)
    write(d, (CX, 965), "Watch the full video", 52, V.ACCENT, (k2 - 0.3) / 0.7, "Bold", "mm", st=V)
    bob = 12 * math.sin(t * 4)
    chalk_arrow(d, (CX, 1220 + bob), (CX, 1060 + bob), V.ACCENT, A(t, dur, 0.45, 0.6), 8, V)


SCENES = [("s1", s_hook, 6), ("s2", s_resistor, 8), ("s3", s_who, 9), ("s4", s_class, 9), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "The moment you plug something into U S B, your computer has no idea what it is. So it has to ask.",
 "s2": "First, a resistor says hello. The device pulls one data line up, and the host sees the voltage rise.",
 "s3": "After a reset, the device answers at address zero. The host asks: who are you? Back comes a name tag: a vendor I D, and a product I D.",
 "s4": "It also gives a class code. Hex, zero three means keyboard or mouse. Hex, zero eight means storage. A class driver loads, and it just works.",
 "s5": "The whole conversation, step by step, is in the full video.",
}
OUTPUT = "ep4_short_usb_who_are_you_narrated.mp4"


def render(name, fn, dur): V.render_to("short4", name, fn, dur)


if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    print(V.preview("short4", SCENES))
