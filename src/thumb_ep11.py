from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1280, 720
BG = (11, 16, 32); GRID = (24, 33, 61)
RED = (255, 96, 96); AMBER = (255, 184, 64); TXT = (242, 245, 252); GREY = (154, 166, 200)
PANEL = (22, 30, 54); LINE = (52, 66, 104)
F = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def font(p, s): return ImageFont.truetype(p, s)

def tracked(d, xy, s, f, fill, track):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track

import os; os.makedirs("thumbs", exist_ok=True)
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)
for x in range(0, W, 40): d.line([x, 0, x, H], fill=GRID, width=1)
for y in range(0, H, 40): d.line([0, y, W, y], fill=GRID, width=1)

# glowing brake disc
cx, cy, r = 320, 330, 190
glow = Image.new("RGB", (W, H), (0, 0, 0))
ImageDraw.Draw(glow).ellipse([cx - r - 60, cy - r - 60, cx + r + 60, cy + r + 60], fill=(150, 40, 40))
glow = glow.filter(ImageFilter.GaussianBlur(70))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 66, 90), outline=(200, 210, 235), width=8)
d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=PANEL, outline=(200, 210, 235), width=6)
import math
for i in range(5):
    a = i * 2 * math.pi / 5
    x, y = cx + 40 * math.cos(a), cy + 40 * math.sin(a)
    d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(200, 210, 235))
for i in range(18):
    a = i * 2 * math.pi / 18
    x, y = cx + 130 * math.cos(a), cy + 130 * math.sin(a)
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=BG)
d.rounded_rectangle([cx + 110, cy - 170, cx + 200, cy + 10], 20, fill=RED)

# timeline: a red task cutting in
d.rectangle([60, 600, 300, 640], fill=(64, 214, 255))
d.rectangle([300, 600, 440, 640], fill=RED)
d.rectangle([440, 600, 600, 640], fill=(64, 214, 255))

tag = Image.new("RGBA", (220, 80), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 216, 76], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((109, 40), "RTOS", font=font(MONO, 44), fill=AMBER, anchor="mm")
tag = tag.rotate(-4, expand=True, resample=Image.BICUBIC)
im.paste(tag, (420, 470), tag)

d = ImageDraw.Draw(im)
tracked(d, (650, 105), "YOUR BRAKES", font(F, 66), GREY, -2)
tracked(d, (646, 190), "CAN'T", font(F, 150), AMBER, -5)
tracked(d, (650, 360), "WAIT THEIR TURN", font(F, 64), TXT, -2)

im.save("thumbs/ep11_thumbnail.jpg", quality=92)
