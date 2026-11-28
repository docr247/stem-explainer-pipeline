"""Thumbnail for episode 3 (blueprint): writes thumbs/ep3_thumbnail.jpg. Run from src/."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import style

S = style.get("blueprint")
W, H = 1280, 720
BLACK = style.INTER + "Inter-Black.otf"
MONO = style.MONO_B
TXT = (242, 245, 252)


def font(p, s): return ImageFont.truetype(p, s)


def tracked(d, xy, s, f, fill, track):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track


os.makedirs("thumbs", exist_ok=True)
im, d = S.thumb_canvas(W, H)

# cyan glow behind a big keycap
cx, cy, s = 320, 330, 300
glow = Image.new("RGB", (W, H), (0, 0, 0))
ImageDraw.Draw(glow).rounded_rectangle([cx - s / 2 - 70, cy - s / 2 - 70, cx + s / 2 + 70, cy + s / 2 + 70], 90, fill=(10, 90, 120))
glow = glow.filter(ImageFilter.GaussianBlur(60))
im = Image.fromarray(np.clip(np.asarray(im, dtype=int) + np.asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)

# signal trace leaving the key
pts = [(cx, cy + s / 2 + 30), (cx, 600), (560, 600)]
d.line(pts, fill=(30, 90, 110), width=22, joint="curve")
d.line(pts, fill=S.ACCENT, width=8, joint="curve")
d.ellipse([548, 588, 572, 612], fill=S.HILITE)

# keycap
d.rounded_rectangle([cx - s / 2, cy - s / 2 + 26, cx + s / 2, cy + s / 2 + 26], 40, fill=(6, 10, 20))
d.rounded_rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], 40, fill=S.PANEL, outline=S.ACCENT, width=10)
d.text((cx, cy), "A", font=font(BLACK, 190), fill=TXT, anchor="mm")
# strike-through: the letter is never sent
d.line([(cx - s / 2 - 10, cy + s / 2 + 10), (cx + s / 2 + 10, cy - s / 2 - 10)], fill=S.BAD, width=16)

# tilted amber tag
tag = Image.new("RGBA", (260, 84), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 256, 80], 14, fill=(26, 22, 8), outline=S.HILITE, width=5)
td.text((129, 42), "SENDS 04", font=font(MONO, 36), fill=S.HILITE, anchor="mm")
tag = tag.rotate(6, expand=True, resample=Image.BICUBIC)
im.paste(tag, (330, 115), tag)

# headline: one amber word
d = ImageDraw.Draw(im)
tracked(d, (640, 110), "YOUR KEYBOARD", font(BLACK, 66), TXT, -2)
tracked(d, (636, 190), "NEVER", font(BLACK, 150), S.HILITE, -5)
tracked(d, (640, 370), "SENDS LETTERS", font(BLACK, 66), TXT, -2)

im.save("thumbs/ep3_thumbnail.jpg", quality=92)
print("thumbs/ep3_thumbnail.jpg", os.path.getsize("thumbs/ep3_thumbnail.jpg"), "bytes")
