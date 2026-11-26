import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
BG = (11, 16, 32); GRID = (24, 33, 61)
CYAN = (64, 214, 255); AMBER = (255, 184, 64); TXT = (242, 245, 252); GREY = (154, 166, 200)
PURPLE = (180, 140, 255)
F = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def font(p, s): return ImageFont.truetype(p, s)

def tracked(d, xy, s, f, fill, track):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track

os.makedirs("thumbs", exist_ok=True)
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)
for x in range(0, W, 40): d.line([x, 0, x, H], fill=GRID, width=1)
for y in range(0, H, 40): d.line([0, y, W, y], fill=GRID, width=1)

# touch grid on the left, with a glowing touch blob
x0, y0, gw, gh, nr, nc = 70, 120, 520, 480, 7, 7
fr, fc = 3.2, 3.6
glow = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
for r in range(nr):
    y = y0 + (r + 0.5) * gh / nr
    gd.line([x0, y, x0 + gw, y], fill=(10, 70, 90), width=26)
for c in range(nc):
    x = x0 + (c + 0.5) * gw / nc
    gd.line([x, y0, x, y0 + gh], fill=(55, 40, 90), width=26)
bx, by = x0 + (fc + 0.5) * gw / nc, y0 + (fr + 0.5) * gh / nr
gd.ellipse([bx - 120, by - 120, bx + 120, by + 120], fill=(170, 110, 30))
glow = glow.filter(ImageFilter.GaussianBlur(26))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
for r in range(nr):
    y = y0 + (r + 0.5) * gh / nr
    d.line([x0, y, x0 + gw, y], fill=CYAN, width=7)
for c in range(nc):
    x = x0 + (c + 0.5) * gw / nc
    d.line([x, y0, x, y0 + gh], fill=PURPLE, width=7)
d.ellipse([bx - 62, by - 62, bx + 62, by + 62], outline=AMBER, width=10)
d.ellipse([bx - 30, by - 30, bx + 30, by + 30], fill=AMBER)

# tilted tag
tag = Image.new("RGBA", (240, 84), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 236, 80], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((119, 42), "TOUCH", font=font(MONO, 44), fill=AMBER, anchor="mm")
tag = tag.rotate(4, expand=True, resample=Image.BICUBIC)
im.paste(tag, (400, 40), tag)

# headline
d = ImageDraw.Draw(im)
tracked(d, (660, 130), "WHY YOUR PHONE", font(F, 62), GREY, -2)
tracked(d, (654, 210), "IGNORES", font(F, 118), AMBER, -4)
tracked(d, (660, 360), "A PEN", font(F, 104), TXT, -3)

im.save("thumbs/ep9_thumbnail.jpg", quality=92)
print(os.path.getsize("thumbs/ep9_thumbnail.jpg"))
