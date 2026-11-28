"""Thumbnail for Tech 101 episode 1 (chalk style): writes thumbs/ep1_thumbnail.jpg (run from src/)."""
import math, os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import style
from style import mix

S = style.get("chalk")
os.makedirs("thumbs", exist_ok=True)
im, d = S.thumb_canvas()
W, H = im.size

# soft chalk-dust glow behind the button
glow = Image.new("RGB", (W, H), (0, 0, 0))
cx, cy, r = 330, 330, 175
ImageDraw.Draw(glow).ellipse([cx - r - 70, cy - r - 70, cx + r + 70, cy + r + 70], fill=(70, 64, 20))
glow = glow.filter(ImageFilter.GaussianBlur(60))
im = Image.fromarray(np.clip(np.asarray(im, int) + np.asarray(glow, int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)

# big power button, drawn in chalk
for g in range(3):
    S.circle(d, (cx, cy), r + 26 + g * 30, None, mix(S.BG, S.HILITE, 0.75 - g * 0.22), 6)
S.circle(d, (cx, cy), r, S.PANEL, S.LINE, 9)
a0, a1 = -90 + 38, 270 - 38
pts = [(cx + r * 0.5 * math.cos(math.radians(a0 + (a1 - a0) * i / 40)), cy + 10 + r * 0.5 * math.sin(math.radians(a0 + (a1 - a0) * i / 40)))
       for i in range(41)]
S.line(d, pts, S.HILITE, 16)
S.line(d, [(cx, cy + 10 - r * 0.62), (cx, cy + 10 - r * 0.1)], S.HILITE, 16)

# the six stops as a chalk trail under the button
xs = [70 + i * 104 for i in range(6)]
S.line(d, [(xs[0], 610), (xs[-1], 610)], S.DIM, 4)
cols = [S.HILITE, S.BAD, S.ACCENT, S.GOOD, S.EXTRA, S.BLUE]
for x, c in zip(xs, cols):
    S.circle(d, (x, 610), 17, c)

# headline on the right
x0 = 640
S.text(d, (x0, 50), "PRESS POWER.", 58, S.DIM, "Bold")
S.text(d, (x0, 130), "WHAT", 112, S.TXT, "Bold")
S.text(d, (x0, 250), "REALLY", 112, S.HILITE, "Bold")
S.text(d, (x0, 370), "HAPPENS?", 112, S.TXT, "Bold")
S.line(d, [(x0, 378), (x0 + S.textlen(d, "REALLY", 112, "Bold"), 382)], S.HILITE, 7)

# one slightly tilted tag
tag = Image.new("RGBA", (420, 96), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([4, 4, 416, 92], 22, fill=S.PANEL + (255,), outline=S.HILITE, width=5)
td.text((210, 48), "FFFF FFF0", font=S.font(48, "Bold"), fill=S.HILITE, anchor="mm")
tag = tag.rotate(5, expand=True, resample=Image.BICUBIC)
im.paste(tag, (650, 530), tag)

im = S.finish(im)
im.save("thumbs/ep1_thumbnail.jpg", quality=92)
print("thumbs/ep1_thumbnail.jpg", os.path.getsize("thumbs/ep1_thumbnail.jpg"))
