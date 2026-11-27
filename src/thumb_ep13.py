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

# glowing green LED shining into a wrist, with a pulse trace
cx, cy, r = 320, 300, 120
glow = Image.new("RGB", (W, H), (0, 0, 0))
ImageDraw.Draw(glow).ellipse([cx - r - 90, cy - r - 90, cx + r + 90, cy + r + 90], fill=(20, 120, 50))
glow = glow.filter(ImageFilter.GaussianBlur(70))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
G = (70, 235, 120)
for g in range(4):
    rr = r + 20 + g * 34
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=tuple(int(c * (0.7 - g * 0.15)) for c in G), width=6)
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=G)
d.ellipse([cx - 60, cy - 70, cx - 10, cy - 30], fill=(190, 255, 210))
# pulse trace
def shape(u):
    u = u % 1.0; s = 0.07 if u < 0.18 else 0.15
    return math.exp(-((u - 0.18) / s) ** 2) + 0.25 * math.exp(-((u - 0.5) / 0.1) ** 2)
pts = [(50 + px, 640 - 110 * shape(px / 150)) for px in range(0, 520, 2)]
d.line(pts, fill=G, width=7)

tag = Image.new("RGBA", (300, 80), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 296, 76], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((149, 40), "GREEN LED", font=font(MONO, 38), fill=AMBER, anchor="mm")
tag = tag.rotate(-4, expand=True, resample=Image.BICUBIC)
im.paste(tag, (340, 405), tag)

d = ImageDraw.Draw(im)
tracked(d, (650, 105), "NO WIRES.", font(F, 62), GREY, -2)
tracked(d, (646, 190), "JUST LIGHT", font(F, 110), AMBER, -5)
tracked(d, (650, 340), "HOW YOUR WATCH", font(F, 58), TXT, -2)
tracked(d, (650, 410), "READS YOUR PULSE", font(F, 54), TXT, -2)

im.save("thumbs/ep13_thumbnail.jpg", quality=92)
