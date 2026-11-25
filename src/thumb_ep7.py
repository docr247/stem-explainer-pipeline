from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
BG = (11, 16, 32); GRID = (24, 33, 61)
LED = (240, 80, 90); AMBER = (255, 184, 64); TXT = (242, 245, 252); GREY = (154, 166, 200)
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
gd.ellipse([175 - 60, 110 - 60, 475 + 60, 410 + 60], fill=(170, 50, 60))
glow = glow.filter(ImageFilter.GaussianBlur(70))
im = Image.fromarray(__import__("numpy").clip(__import__("numpy").asarray(im, dtype=int) + __import__("numpy").asarray(glow, dtype=int), 0, 255).astype("uint8"))
d = ImageDraw.Draw(im)
d.ellipse([155, 90, 495, 430], fill=(22, 30, 54), outline=(52, 66, 104), width=6)
d.ellipse([175, 110, 475, 410], fill=LED, outline=(255, 200, 205), width=8)

# IRQ line: flat, then a sharp pulse
d.line([(70, 600), (300, 600), (300, 520), (360, 520), (360, 600), (600, 600)], fill=AMBER, width=9)

# 50% tag (rotated)
tag = Image.new("RGBA", (180, 80), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([2, 2, 176, 76], 14, fill=(26, 22, 8), outline=AMBER, width=5)
td.text((89, 40), "IRQ!", font=font(MONO, 42), fill=AMBER, anchor="mm")
tag = tag.rotate(3, expand=True, resample=Image.BICUBIC)
im.paste(tag, (400, 430), tag)

# Headline
tracked(d, (650, 105), "YOUR CPU NEVER", font(F, 62), GREY, -2)
tracked(d, (646, 190), "CHECKS", font(F, 140), AMBER, -5)
tracked(d, (650, 350), "THIS BUTTON", font(F, 84), TXT, -2)

im.save("thumbs/ep7_thumbnail.jpg", quality=92)
