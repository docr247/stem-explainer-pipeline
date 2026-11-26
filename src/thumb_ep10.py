import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1280, 720
BG = (11, 16, 32); GRID = (24, 33, 61)
CYAN = (64, 214, 255); AMBER = (255, 184, 64); TXT = (242, 245, 252); GREY = (154, 166, 200)
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

# glowing antenna with radiating rings
ax, ay = 200, 330
glow = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([ax - 60, ay - 200, ax + 380, ay + 200], fill=(20, 90, 120))
glow = glow.filter(ImageFilter.GaussianBlur(70))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
d.line([ax, ay - 150, ax, ay + 170], fill=(200, 210, 235), width=14)
d.ellipse([ax - 18, ay - 168, ax + 18, ay - 132], fill=CYAN)
for i, r in enumerate([80, 150, 220, 290, 360]):
    d.arc([ax - r, ay - 150 - r, ax + r, ay - 150 + r], -55, 55, fill=CYAN, width=10 - i)

# wave carrying bits
pts = []
for px in range(60, 600, 3):
    u = (px - 60) / 540
    bit = "1011"[min(3, int(u * 4))]
    a = 1.0 if bit == "1" else 0.35
    pts.append((px, 590 - 50 * a * math.sin(u * 2 * math.pi * 9)))
d.line(pts, fill=AMBER, width=8)

tag = Image.new("RGBA", (220, 80), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 216, 76], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((109, 40), "2.4 GHz", font=font(MONO, 40), fill=AMBER, anchor="mm")
tag = tag.rotate(4, expand=True, resample=Image.BICUBIC)
im.paste(tag, (360, 420), tag)

d = ImageDraw.Draw(im)
tracked(d, (650, 105), "HOW YOUR BITS", font(F, 62), GREY, -2)
tracked(d, (646, 190), "FLY", font(F, 160), AMBER, -5)
tracked(d, (650, 370), "THROUGH AIR", font(F, 84), TXT, -2)

im.save("thumbs/ep10_thumbnail.jpg", quality=92)
