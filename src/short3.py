"""Tech 101, episode 3 Short (blueprint style): your keyboard never sends the letter A."""
import math, sys
import style
from style import clamp, prog, mix
from ep3 import keycap, report_row, glow, glow_dot, press_at

V = style.get("blueprint", vertical=True)
W, H, FPS = V.W, V.H, V.FPS
VOICE, SPEED, LANG = V.VOICE, V.SPEED, V.LANG
BG, PANEL, LINE, TXT, DIM = V.BG, V.PANEL, V.LINE, V.TXT, V.DIM
CY, AM, GR, RD, PU = V.ACCENT, V.HILITE, V.GOOD, V.BAD, V.EXTRA
CX = 500  # visual centre: content stays between x=70 and x=930


def s_hook(d, t, dur):
    V.headline(d, ["Your keyboard", "never sends", "the letter A"], t, TXT, 280, 80)
    k = prog(t, 0.5, 1.0)
    keycap(d, CX, 820, 320, "A", press_at(t, 1.6, 2.3), k)
    if t > 2.0:
        kk = prog(t, 2.0, 2.4)
        V.line(d, [(CX - 190, 640), (CX + 190, 1010)], RD, 12, kk)
    V.caption_v(d, "So what does it actually send?", t, 1330)


def s_matrix(d, t, dur):
    V.headline(d, ["It scans a", "grid of wires"], t, CY, 270, 80)
    k = prog(t, 0.2, 0.7)
    n, s = 5, 150
    x0, y0 = CX - 2 * s, 560
    col = int((t - 0.6) * 3) % n if t > 0.6 else -1
    hit = (2, 3)
    pressed = t > 1.6
    for c in range(n):
        x = x0 + c * s
        if c == col: glow(d, [(x, y0 - 60), (x, y0 + (n - 1) * s + 60)], AM, 7)
        else: V.line(d, [(x, y0 - 60), (x, y0 + (n - 1) * s + 60)], LINE, 5, k)
    for r in range(n):
        y = y0 + r * s
        lit = pressed and col == hit[1] and r == hit[0]
        if lit: glow(d, [(x0 - 60, y), (x0 + (n - 1) * s + 60, y)], GR, 7)
        else: V.line(d, [(x0 - 60, y), (x0 + (n - 1) * s + 60, y)], LINE, 5, k)
        for c in range(n):
            on = pressed and (r, c) == hit
            x = x0 + c * s
            V.box(d, (x - 26, y - 26, x + 26, y + 26), mix(BG, GR, 0.8) if on else PANEL, GR if on else LINE, 6, 3, k)
    V.caption_v(d, "Column by column, many times a second.", t, 1330)


def s_report(d, t, dur):
    V.headline(d, ["Then it sends", "a number"], t, AM, 270, 80)
    vals = ["00", "00", "04", "00", "00", "00", "00", "00"]
    for row in range(2):
        report_row(d, CX - 2 * 190 + 10, 520 + row * 220, vals[row * 4:row * 4 + 4], 1.0, t=t, t0=0.6 + row * 0.6, step=0.15,
                   bw=170, bh=170, gap=20, hot=(2,) if row == 0 else (), size=72)
    k = prog(t, 2.0, 2.5)
    V.text(d, (CX, 1000), "8-byte report", 40, DIM, "Medium", "mm", k=k)
    V.text(d, (CX, 1110), "usage 0x04", 64, AM, "Bold", "mm", mono=True, k=prog(t, 2.6, 3.1))
    V.text(d, (CX, 1190), "= the key in the A position", 38, TXT, "Medium", "mm", k=prog(t, 3.0, 3.5))
    V.caption_v(d, "Not a letter. Just a key position.", t, 1330)


def s_layout(d, t, dur):
    V.headline(d, ["Your computer", "picks the letter"], t, CY, 270, 80)
    k = prog(t, 0.3, 0.8)
    V.box(d, (CX - 210, 470, CX + 210, 580), mix(BG, AM, 0.2), AM, 18, 4, k)
    V.text(d, (CX, 525), "0x04", 64, AM, "Bold", "mm", mono=True, k=k)
    ka = prog(t, 1.0, 1.4)
    V.arrow(d, (CX - 90, 590), (CX - 220, 700), DIM, 6, ka)
    V.arrow(d, (CX + 90, 590), (CX + 220, 700), DIM, 6, ka)
    k2 = prog(t, 1.5, 2.0)
    keycap(d, CX - 230, 850, 220, "a", 1.0 if t > 1.5 else 0, k2, GR)
    V.text(d, (CX - 230, 1030), "US QWERTY", 42, GR, "Bold", "mm", k=k2)
    k3 = prog(t, 2.4, 2.9)
    keycap(d, CX + 230, 850, 220, "q", 1.0 if t > 2.4 else 0, k3, CY)
    V.text(d, (CX + 230, 1030), "French AZERTY", 42, CY, "Bold", "mm", k=k3)
    V.text(d, (CX, 1160), "same key, same code", 40, DIM, "Bold", "mm", k=prog(t, 3.2, 3.7))
    V.caption_v(d, "QWERTY makes a. AZERTY makes q.", t, 1330)


def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    V.text(d, (CX, 600), "From fingertip", 84, TXT, "Bold", "mm", k=k)
    V.text(d, (CX, 700), "to pixel", 84, TXT, "Bold", "mm", k=k)
    V.text(d, (CX, 800), "7 steps, explained", 44, CY, "Medium", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    V.box(d, (CX - 330, 900, CX + 330, 1030), CY, CY, 65, 1, k2)
    V.text(d, (CX, 965), "Watch the full video", 52, BG, "Bold", "mm", k=k2 if k2 > 0.5 else 0)
    V.arrow(d, (CX, 1220), (CX, 1080), CY, 8, prog(t, 1.4, 2.0))


SCENES = [("s1", s_hook, 6), ("s2", s_matrix, 7), ("s3", s_report, 7), ("s4", s_layout, 7), ("s5", s_cta, 5)]

NARRATION = {
 "s1": "Your keyboard never sends the letter a. Not even once. So what does it actually send?",
 "s2": "Under the keys is a grid of wires. A tiny chip scans it, column by column, many times a second, to find which crossing just closed.",
 "s3": "Then it sends a number. Hex, zero four. That doesn't mean a. It just means: the key in this position.",
 "s4": "Your computer picks the letter. On a US qwerty layout, that key is a. On French azerty, the exact same code types q.",
 "s5": "Every step, from fingertip to pixel, is in the full video.",
}
OUTPUT = "ep3_short_keyboard_never_sends_a_narrated.mp4"


def render(name, fn, dur): V.render_to("short3", name, fn, dur)


if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    V.preview("short3", SCENES)
