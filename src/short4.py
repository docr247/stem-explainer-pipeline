import os, subprocess, sys
from PIL import Image, ImageDraw
from render import (clamp, ease, prog, mix, fade, text, box, arrow, chip,
                    BG, PANEL, LINE, TXT, DIM, CYAN, AMBER, GREEN)
from short import headline, caption, W, H, FPS
from ep4 import plug, packet, PURPLE

def s_hook(d, t, dur):
    headline(d, ["Your PC has", "NO idea what you", "just plugged in."], t, y=300, size=70)
    x = 120 + 300 * ease(clamp((t - 0.6) / 1.2))
    plug(d, x, 760, 1.6, prog(t, 0.3, 0.7))
    if t > 2.0:
        text(d, (540, 1060), "???", 120, AMBER, "Bold", "mm", k=prog(t, 2.0, 2.5))
    caption(d, "So it has to ask.", t, 1250)

def s_ask(d, t, dur):
    headline(d, ["So it asks:", "who are you?"], t, CYAN, 260, 74)
    k = prog(t, 0.2, 0.6)
    chip(d, 290, 460, 500, 160, "Host", "", PURPLE, k, pins=False)
    chip(d, 290, 900, 500, 160, "Device", "address 0", CYAN, k, pins=False)
    d.line([540, 620, 540, 900], fill=fade(LINE, k), width=6)
    if 0.8 < t < 2.6:
        packet(d, 540, 640 + ease((t - 0.8) / 1.6) * 230, "GET_DESCRIPTOR", PURPLE, 330)
    if 3.0 < t < 4.8:
        packet(d, 540, 880 - ease((t - 3.0) / 1.6) * 230, "18 bytes", AMBER, 220)
    caption(d, "Every new device starts at address zero.", t, 1250)

def s_tag(d, t, dur):
    headline(d, ["It answers with", "a name tag"], t, AMBER, 260, 70)
    rows = [("idVendor", "0x1A2B", "who made it"), ("idProduct", "0x3C4D", "which model"), ("class", "0x03", "what it is")]
    for i, (f, v, m) in enumerate(rows):
        kk = prog(t, 0.6 + i * 0.6, 1.0 + i * 0.6)
        y = 460 + i * 220
        box(d, (110, y, 970, y + 180), PANEL, AMBER if i < 2 else CYAN, 16, 4, kk)
        text(d, (150, y + 60), f, 46, CYAN, "Bold", "lm", mono=True, k=kk)
        text(d, (930, y + 60), v, 52, AMBER, "Bold", "rm", mono=True, k=kk)
        text(d, (150, y + 130), m, 36, DIM, "Medium", "lm", k=kk)
    caption(d, "Example values. Every model has its own pair.", t, 1250)

def s_class(d, t, dur):
    headline(d, ["The class code", "picks the driver"], t, CYAN, 260, 70)
    rows = [("0x03", "Keyboard / mouse", CYAN), ("0x08", "Flash drive", AMBER), ("0x01", "Headset", PURPLE)]
    for i, (c, n, col) in enumerate(rows):
        kk = prog(t, 0.6 + i * 0.5, 1.0 + i * 0.5)
        y = 460 + i * 170
        hot = i == 0 and t > 2.8
        box(d, (110, y, 970, y + 140), mix(BG, col, 0.25) if hot else PANEL, col, 16, 5 if hot else 3, kk)
        text(d, (150, y + 70), c, 56, col, "Bold", "lm", mono=True, k=kk)
        text(d, (400, y + 70), n, 44, TXT, "Bold", "lm", k=kk)
    if t > 3.4:
        kk = prog(t, 3.4, 3.9)
        box(d, (230, 1000, 850, 1110), (245, 247, 252), LINE, 16, 3, kk)
        text(d, (540, 1055), "Device is ready", 44, (20, 24, 40), "Bold", "mm", k=kk)
    caption(d, "Load the driver, and it just works.", t, 1250)

def s_cta(d, t, dur):
    k = prog(t, 0.2, 0.8)
    text(d, (W // 2, 640), "The whole", 84, TXT, "Bold", "mm", k=k)
    text(d, (W // 2, 740), "USB handshake", 84, TXT, "Bold", "mm", k=k)
    k2 = prog(t, 0.9, 1.5)
    box(d, (190, 880, 890, 1010), CYAN, CYAN, 65, 1, k2)
    if k2 > 0.5: text(d, (W // 2, 945), "Watch the full video", 52, BG, "Bold", "mm")
    arrow(d, (W // 2, 1180), (W // 2, 1060), CYAN, 8, prog(t, 1.4, 2.0))

SCENES = [("s1", s_hook, 6), ("s2", s_ask, 7), ("s3", s_tag, 8), ("s4", s_class, 8), ("s5", s_cta, 5)]

def frame(fn, t, dur):
    im = Image.new("RGB", (W, H), BG)
    fn(ImageDraw.Draw(im), t, dur)
    a = min(clamp(t / 0.25), clamp((dur - t) / 0.25))
    return im if a >= 1 else Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, a)

def render(name, fn, dur):
    out, tmp = f"short4/{name}.mp4", f"short4/{name}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                          "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(round(dur * FPS))):
        p.stdin.write(frame(fn, i / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

os.makedirs("short4", exist_ok=True)
if __name__ == "__main__" and sys.argv[1:] == ["preview"]:
    sheet = Image.new("RGB", (W * 5, H))
    for i, (_, fn, dur) in enumerate(SCENES): sheet.paste(frame(fn, dur * 0.85, dur), (i * W, 0))
    sheet.resize((W * 5 // 3, H // 3)).save("short4/sheet.jpg", quality=85)
