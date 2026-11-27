from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, math

W, H = 1280, 720
BG = (11, 16, 32); GRID = (24, 33, 61)
RED = (255, 96, 96); AMBER = (255, 184, 64); TXT = (242, 245, 252); GREY = (154, 166, 200)
CYAN = (64, 214, 255); PANEL = (22, 30, 54); LINE = (52, 66, 104)
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

# glowing stepper motor, end-on, with toothed rotor
cx, cy, r = 320, 330, 190
glow = Image.new("RGB", (W, H), (0, 0, 0))
ImageDraw.Draw(glow).ellipse([cx - r - 60, cy - r - 60, cx + r + 60, cy + r + 60], fill=(20, 90, 130))
glow = glow.filter(ImageFilter.GaussianBlur(70))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], 40, fill=(60, 66, 90), outline=(200, 210, 235), width=8)
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = cx + sx * (r - 38), cy + sy * (r - 38)
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=BG)
rr = 120
d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=PANEL, outline=(200, 210, 235), width=5)
for i in range(50):
    a = i * 2 * math.pi / 50
    d.line([cx + (rr - 4) * math.cos(a), cy + (rr - 4) * math.sin(a), cx + (rr - 22) * math.cos(a), cy + (rr - 22) * math.sin(a)], fill=(200, 210, 235), width=5)
d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(200, 210, 235))
d.line([cx, cy, cx + 90 * math.cos(-1.1), cy + 90 * math.sin(-1.1)], fill=AMBER, width=10)

# pulse train below
pts = [(60, 640)]
for i in range(9):
    x = 70 + i * 56
    pts += [(x, 640), (x, 600), (x + 26, 600), (x + 26, 640)]
d.line(pts, fill=AMBER, width=6)

tag = Image.new("RGBA", (300, 80), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 296, 76], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((149, 40), "NO SENSOR", font=font(MONO, 38), fill=AMBER, anchor="mm")
tag = tag.rotate(-4, expand=True, resample=Image.BICUBIC)
im.paste(tag, (360, 470), tag)

d = ImageDraw.Draw(im)
tracked(d, (650, 105), "IT DOESN'T SEE.", font(F, 62), GREY, -2)
tracked(d, (646, 190), "IT COUNTS", font(F, 118), AMBER, -5)
tracked(d, (650, 340), "HOW 3D PRINTERS", font(F, 56), TXT, -2)
tracked(d, (650, 410), "KNOW WHERE THEY ARE", font(F, 46), TXT, -2)

im.save("thumbs/ep12_thumbnail.jpg", quality=92)
