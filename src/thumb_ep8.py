import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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

os.makedirs("thumbs", exist_ok=True)
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)
for x in range(0, W, 40): d.line([x, 0, x, H], fill=GRID, width=1)
for y in range(0, H, 40): d.line([0, y, W, y], fill=GRID, width=1)

# smooth wave on the left that turns into a staircase
x0, x1, yc, amp = 70, 600, 330, 170
def v(u): return math.sin(2 * math.pi * (u * 1.1 + 0.05))
wave = [(x0 + (x1 - x0) * i / 300, yc - amp * v(i / 300)) for i in range(301)]
steps = []
n = 16
for i in range(n):
    ua, ub = i / n, (i + 1) / n
    q = round(v((ua + ub) / 2) * 4) / 4
    y = yc - amp * q
    steps += [(x0 + (x1 - x0) * ua, y), (x0 + (x1 - x0) * ub, y)]

glow = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.line(wave, fill=(150, 100, 30), width=40)
gd.line(steps, fill=(20, 110, 140), width=40)
glow = glow.filter(ImageFilter.GaussianBlur(28))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
d.line(wave, fill=AMBER, width=10)
d.line(steps, fill=CYAN, width=10)

# bits under the wave
d.text((80, 560), "1010 1010 1010", font=font(MONO, 54), fill=CYAN)

# tilted tag
tag = Image.new("RGBA", (200, 84), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 196, 80], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((99, 42), "ADC", font=font(MONO, 46), fill=AMBER, anchor="mm")
tag = tag.rotate(4, expand=True, resample=Image.BICUBIC)
im.paste(tag, (430, 60), tag)

# headline
d = ImageDraw.Draw(im)
tracked(d, (660, 110), "YOUR CHIP MAKES", font(F, 60), GREY, -2)
tracked(d, (654, 185), "12 GUESSES", font(F, 104), AMBER, -4)
tracked(d, (660, 320), "TO READ ONE", font(F, 74), TXT, -2)
tracked(d, (660, 410), "VOLTAGE", font(F, 74), TXT, -2)

im.save("thumbs/ep8_thumbnail.jpg", quality=92)
