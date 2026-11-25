import math, os, subprocess, sys
from PIL import Image, ImageDraw
from render import (font, clamp, ease, prog, mix, fade, text, box, arrow, chip, chrome,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN, RED, W, H, FPS)

PURPLE = (180, 140, 255)
REPORT = ["00", "00", "04", "00", "00", "00", "00", "00"]
REPORT_LBL = ["mods", "rsvd", "key 1", "key 2", "key 3", "key 4", "key 5", "key 6"]

def keycap(d, cx, cy, s, label, pressed, k=1.0, col=CYAN):
    dy = 10 if pressed else 0
    d.rounded_rectangle([cx - s // 2, cy - s // 2 + 14, cx + s // 2, cy + s // 2 + 14], 22, fill=fade((8, 12, 24), k))
    d.rounded_rectangle([cx - s // 2, cy - s // 2 + dy, cx + s // 2, cy + s // 2 + dy], 22,
                        fill=fade(PANEL, k), outline=fade(col if pressed else LINE, k), width=6)
    text(d, (cx, cy + dy), label, int(s * 0.45), TXT, "Bold", "mm", k=k)

def s_hook(d, t, dur):
    chrome(d, "", "", "You press a key, and a letter appears, in a few milliseconds. But your keyboard never actually sends the letter.", t, dur)
    pressed = 1.4 < t < 1.9
    keycap(d, 560, 420, 240, "A", pressed, prog(t, 0.2, 0.7))
    k = prog(t, 0.6, 1.1)
    box(d, (900, 330, 1520, 510), (245, 247, 252), LINE, 14, 3, k)
    if t > 1.7:
        text(d, (950, 420), "a", 80, (20, 24, 40), "Medium", "lm")
    if int(t * 2) % 2 == 0 and k > 0.5:
        x = 1000 if t > 1.7 else 950
        d.rectangle([x, 380, x + 5, 460], fill=(20, 24, 40))

def s_matrix(d, t, dur):
    chrome(d, "STEP 1 · THE KEY MATRIX", "A grid of wires", "Under the keys is a grid of wires, in rows and columns. The keyboard's microcontroller scans it, driving one column at a time and reading the rows, hundreds of times a second.", t, dur)
    k = prog(t, 0.2, 0.8)
    rows, cols = 4, 6
    x0, y0, sx, sy = 520, 300, 150, 120
    col = int(t * 4) % cols if t > 1.0 else -1
    hit = (1, 2)  # row, column of the pressed key
    pressed = t > 4.0
    for c in range(cols):
        x = x0 + c * sx
        active = c == col
        d.line([x, y0 - 40, x, y0 + (rows - 1) * sy + 40], fill=fade(AMBER if active else LINE, k), width=6 if active else 4)
        text(d, (x, y0 - 70), f"C{c}", 26, AMBER if active else DIM, "Bold", "mm", k=k)
    for r in range(rows):
        y = y0 + r * sy
        lit = pressed and col == hit[1] and r == hit[0]
        d.line([x0 - 40, y, x0 + (cols - 1) * sx + 40, y], fill=fade(GREEN if lit else LINE, k), width=6 if lit else 4)
        text(d, (x0 - 80, y), f"R{r}", 26, GREEN if lit else DIM, "Bold", "mm", k=k)
        for c in range(cols):
            x = x0 + c * sx
            on = pressed and (r, c) == hit
            d.rectangle([x - 18, y - 18, x + 18, y + 18], fill=fade(mix(BG, GREEN, 0.9) if on else PANEL, k),
                        outline=fade(GREEN if on else LINE, k), width=3)
    chip(d, 120, 380, 250, 170, "MCU", "scanning", CYAN, k)
    if pressed and col == hit[1]:
        text(d, (W // 2, 820), "R1 reads LOW while C2 is driven → key at (R1, C2)", 32, GREEN, "Bold", "mm", mono=True)

def s_debounce(d, t, dur):
    chrome(d, "STEP 2 · DEBOUNCE", "One press, not five", "Metal contacts bounce, flickering on and off for a few milliseconds. The firmware debounces the signal, so one press counts as exactly one press.", t, dur)
    k = prog(t, 0.2, 0.7)
    x0, w = 360, 1300
    for (y, name, col, clean) in [(300, "raw switch", RED, False), (560, "debounced", GREEN, True)]:
        text(d, (x0 - 30, y + 60), name, 30, col, "Bold", "rm", k=k)
        d.line([x0, y + 120, x0 + w, y + 120], fill=fade(LINE, k), width=2)
        pts, tt = [], clamp((t - (0.8 if not clean else 3.2)) / 3.0) * w
        bounce = [(0.20, 0.22), (0.24, 0.255), (0.27, 0.28), (0.295, 0.30)]
        for px in range(0, int(tt), 2):
            u = px / w
            if clean: hi = u > 0.36
            else: hi = u > 0.20 and not any(a < u < b for a, b in bounce)
            pts.append((x0 + px, y + (10 if hi else 120)))
        if len(pts) > 1: d.line(pts, fill=col, width=5)
    if t > 2.6:
        kk = prog(t, 2.6, 3.1)
        xa, xb = x0 + 0.20 * w, x0 + 0.30 * w
        d.rectangle([xa, 280, xb, 440], outline=fade(AMBER, kk), width=3)
        text(d, ((xa + xb) / 2, 470), "bounce ≈ 1–5 ms", 28, AMBER, "Bold", "mm", k=kk)

def s_report(d, t, dur):
    chrome(d, "STEP 3 · THE HID REPORT", "Not a letter, a number", "The keyboard doesn't send the letter A. It sends a code that means 'the key in this position', usage 4, packed into an 8-byte HID report.", t, dur)
    keycap(d, 300, 430, 180, "A", False, prog(t, 0.2, 0.7), CYAN)
    k = prog(t, 0.8, 1.3)
    arrow(d, (420, 440), (540, 440), DIM, 5, k)
    text(d, (480, 400), "usage", 24, DIM, "Medium", "mm", k=k)
    text(d, (480, 500), "0x04", 34, AMBER, mono=True, anchor="mm", k=k)
    for i, (b, lbl) in enumerate(zip(REPORT, REPORT_LBL)):
        st = 1.6 + i * 0.25
        kk = prog(t, st, st + 0.3)
        x = 580 + i * 150
        hot = i == 2
        box(d, (x, 370, x + 130, 500), mix(BG, AMBER, 0.25) if hot else PANEL, AMBER if hot else LINE, 12, 4 if hot else 2, kk)
        text(d, (x + 65, 435), b, 48, AMBER if hot else TXT, mono=True, anchor="mm", k=kk)
        text(d, (x + 65, 530), lbl, 24, DIM, "Medium", "mm", k=kk)
    text(d, (1180, 320), "8-byte boot keyboard report", 30, DIM, "Medium", "mm", k=prog(t, 1.6, 2.1))
    if t > 5.5:
        kk = prog(t, 5.5, 6.1)
        text(d, (W // 2, 660), "Hold Shift → byte 0 becomes 0x02", 34, CYAN, "Bold", "mm", mono=True, k=kk)

def s_poll(d, t, dur):
    chrome(d, "STEP 4 · USB POLLING", "The host asks", "A USB keyboard can't interrupt the computer. Instead, the host polls it, every few milliseconds: anything new? The keyboard answers with its report.", t, dur)
    k = prog(t, 0.2, 0.7)
    chip(d, 180, 360, 360, 220, "Keyboard", "USB device", CYAN, k, pins=False)
    chip(d, 1380, 360, 360, 220, "PC", "USB host", PURPLE, k, pins=False)
    d.line([540, 440, 1380, 440], fill=fade(LINE, k), width=5)
    d.line([540, 500, 1380, 500], fill=fade(LINE, k), width=5)
    cyc = 2.0
    if t > 1.0:
        n = int((t - 1.0) / cyc); p = ((t - 1.0) % cyc) / cyc
        has_data = n >= 2
        if p < 0.45:
            x = 1380 - ease(p / 0.45) * 840
            d.rounded_rectangle([x - 46, 422, x + 46, 458], 8, fill=PURPLE)
            text(d, (x, 440), "IN?", 24, BG, "Bold", "mm")
        elif p > 0.5:
            x = 540 + ease((p - 0.5) / 0.45) * 840
            col = AMBER if has_data else DIM
            d.rounded_rectangle([x - 70, 482, x + 70, 518], 8, fill=col)
            text(d, (x, 500), "00 00 04…" if has_data else "NAK", 22, BG, "Bold", "mm", mono=True)
        text(d, (W // 2, 640), f"poll #{n + 1}", 34, DIM, "Bold", "mm", mono=True)
    text(d, (W // 2, 720), "typically every 1–10 ms", 30, DIM, "Medium", "mm", k=prog(t, 1.5, 2.0))

def s_driver(d, t, dur):
    chrome(d, "STEP 5 · INTERRUPT + DRIVER", "Your layout decides", "The USB controller drops the report into memory and interrupts the CPU. The driver applies your keyboard layout. The same code 4 is 'a' on QWERTY, but 'q' on a French AZERTY keyboard.", t, dur)
    k = prog(t, 0.2, 0.7)
    steps = [("USB controller", PURPLE), ("RAM buffer", AMBER), ("IRQ → CPU", RED), ("HID driver", CYAN)]
    for i, (s, c) in enumerate(steps):
        kk = prog(t, 0.3 + i * 0.5, 0.7 + i * 0.5)
        x = 140 + i * 420
        box(d, (x, 280, x + 360, 380), PANEL, c, 14, 4, kk)
        text(d, (x + 180, 330), s, 34, TXT, "Bold", "mm", k=kk)
        if i < 3: arrow(d, (x + 364, 330), (x + 416, 330), DIM, 4, kk)
    if t > 3.0:
        kk = prog(t, 3.0, 3.6)
        text(d, (960, 480), "usage 0x04", 48, AMBER, mono=True, anchor="mm", k=kk)
        arrow(d, (860, 520), (640, 600), DIM, 4, kk)
        arrow(d, (1060, 520), (1280, 600), DIM, 4, kk)
        k2 = prog(t, 4.0, 4.6)
        keycap(d, 560, 690, 130, "a", False, k2, GREEN)
        text(d, (560, 800), "US · QWERTY", 28, GREEN, "Bold", "mm", k=k2)
        keycap(d, 1360, 690, 130, "q", False, k2, CYAN)
        text(d, (1360, 800), "FR · AZERTY", 28, CYAN, "Bold", "mm", k=k2)

def s_screen(d, t, dur):
    chrome(d, "STEP 6 · TO THE SCREEN", "Event, glyph, pixels", "The OS sends a key event to whichever window has focus. The app adds the letter, the font engine draws its glyph, and on the next screen refresh, there it is.", t, dur)
    steps = [("Event queue", PURPLE), ("Focused app", CYAN), ("Font engine", AMBER), ("GPU frame", GREEN)]
    for i, (s, c) in enumerate(steps):
        kk = prog(t, 0.3 + i * 0.6, 0.7 + i * 0.6)
        x = 140 + i * 420
        box(d, (x, 300, x + 360, 400), PANEL, c, 14, 4, kk)
        text(d, (x + 180, 350), s, 34, TXT, "Bold", "mm", k=kk)
        if i < 3: arrow(d, (x + 364, 350), (x + 416, 350), DIM, 4, kk)
    if t > 3.0:
        kk = prog(t, 3.0, 3.6)
        gx, gy, px = 760, 470, 28
        A = ["..##..", ".#..#.", "#....#", "######", "#....#", "#....#", "#....#"]
        n = int(clamp((t - 3.0) / 2.5) * 42)
        for j in range(min(n, 42)):
            r, c = divmod(j, 6)
            on = A[r][c] == "#"
            d.rectangle([gx + c * px * 2.4, gy + r * px * 1.1, gx + c * px * 2.4 + px * 2.2, gy + r * px * 1.1 + px],
                        fill=fade(GREEN if on else (24, 32, 56), kk))
        text(d, (1260, 560), "60 Hz → a new frame every 16.7 ms", 30, DIM, "Medium", "lm", k=prog(t, 5.6, 6.2))

def s_recap(d, t, dur):
    chrome(d, "RECAP", "From fingertip to pixel", "Scan, debounce, report, poll, interrupt, layout, and draw. All of it, in the time it takes to blink.", t, dur)
    st = [("Scan", AMBER), ("Debounce", RED), ("Report", AMBER), ("Poll", PURPLE), ("IRQ", RED), ("Layout", CYAN), ("Draw", GREEN)]
    x0, x1, y = 200, 1720, 470
    d.line([x0, y, x0 + (x1 - x0) * prog(t, 0.3, 4.2), y], fill=LINE, width=6)
    for i, (nm, c) in enumerate(st):
        s = 0.5 + i * 0.55; kk = prog(t, s, s + 0.4)
        if kk <= 0: continue
        x = x0 + i * (x1 - x0) / 6
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=fade(c, kk))
        text(d, (x, y - 60), nm, 34, c, "Bold", "mm", k=kk)
    if t > 4.6:
        keycap(d, W // 2, 660, 150, "A", 4.8 < t < 5.2, prog(t, 4.6, 5.2))

def s_end(d, t, dur):
    k = prog(t, 0.2, 0.9)
    text(d, (W // 2, 400), "NEXT EPISODE", 34, CYAN, "Bold", "mm", k=k)
    text(d, (W // 2, 500), "How does USB know", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 590), "what you plugged in?", 76, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "Subscribe so you don't miss it", 36, DIM, "Medium", "mm", k=prog(t, 1.2, 1.9))

SCENES = [("01_hook", s_hook, 8), ("02_matrix", s_matrix, 11), ("03_debounce", s_debounce, 10),
          ("04_report", s_report, 10), ("05_poll", s_poll, 11), ("06_driver", s_driver, 12),
          ("07_screen", s_screen, 11), ("08_recap", s_recap, 9), ("09_end", s_end, 6)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.35), clamp((dur - t) / 0.35))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"ep3/{name}.mp4", f"ep3/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("ep3", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    s = Image.new("RGB", (W * 3, H * 3))
    for i, (_, fn, dur) in enumerate(SCENES):
        s.paste(frame(fn, dur * 0.85, dur), ((i % 3) * W, (i // 3) * H))
    s.resize((2880, 1620)).save("ep3/sheet.jpg", quality=85)
