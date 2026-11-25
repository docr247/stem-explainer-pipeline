from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
BG = (11, 16, 32); GRID = (24, 33, 61)
LED = (90, 230, 140); AMBER = (255, 184, 64); TXT = (242, 245, 252); GREY = (154, 166, 200)
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

# LED glow
glow = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([175 - 60, 110 - 60, 475 + 60, 410 + 60], fill=(60, 170, 100))
glow = glow.filter(ImageFilter.GaussianBlur(70))
im = Image.fromarray(__import__("numpy").clip(__import__("numpy").asarray(im, dtype=int) + __import__("numpy").asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
d.ellipse([175, 110, 475, 410], fill=LED, outline=(217, 255, 230), width=8)

# PWM wave + average line
pts = [(70, 600)]
x = 70
for i in range(5):
    pts += [(x, 520), (x + 55, 520), (x + 55, 600), (x + 110, 600)]
    x += 110
pts += [(x, 520)] if False else []
d.line(pts, fill=AMBER, width=9, joint="curve")
for xx in range(70, 580, 24): d.line([xx, 560, min(xx + 14, 580), 560], fill=LED, width=4)

# 50% tag (rotated)
tag = Image.new("RGBA", (180, 80), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 176, 76], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((89, 40), "50%", font=font(MONO, 42), fill=AMBER, anchor="mm")
tag = tag.rotate(3, expand=True, resample=Image.BICUBIC)
im.paste(tag, (400, 430), tag)

# Headline
tracked(d, (650, 105), "THIS LED IS", font(F, 70), GREY, -2)
tracked(d, (646, 190), "BLINKING", font(F, 132), AMBER, -5)
tracked(d, (650, 345), "1000× A SECOND", font(F, 66), TXT, -2)

im.save("thumbs/ep6_thumbnail.jpg", quality=92)
