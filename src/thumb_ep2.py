"""Thumbnail for Tech 101 ep 2 (paper style): writes thumbs/ep2_thumbnail.jpg"""
import os
from PIL import Image, ImageDraw
import style
from style import mix

S = style.get("paper")
im, d = S.thumb_canvas()
BG, PANEL, LINE, TXT, ONA = S.BG, S.PANEL, S.LINE, S.TXT, S.ON_ACCENT
ACC, HIL, GOOD = S.ACCENT, S.HILITE, S.GOOD

# --- big subject on the left: a chip driving a glowing LED, with binary above
cx0, cy0, cx1, cy1 = 60, 250, 330, 520
for i in range(5):
    px = cx0 + 45 + i * 45
    d.rectangle([px - 9, cy0 - 24, px + 9, cy0], fill=LINE)
    d.rectangle([px - 9, cy1, px + 9, cy1 + 24], fill=LINE)
for i in range(4):
    py = cy0 + 50 + i * 57
    d.rectangle([cx0 - 24, py - 9, cx0, py + 9], fill=LINE)
    d.rectangle([cx1, py - 9, cx1 + 24, py + 9], fill=LINE)
S.box(d, (cx0, cy0, cx1, cy1), ACC, None, 26, 0)
d.ellipse([cx0 + 20, cy0 + 20, cx0 + 42, cy0 + 42], fill=mix(ACC, LINE, 0.35))
d.text(((cx0 + cx1) / 2, (cy0 + cy1) / 2 - 25), "0x4051", font=S.font(58, "Bold", mono=True), fill=ONA, anchor="mm")
d.text(((cx0 + cx1) / 2, (cy0 + cy1) / 2 + 45), "MCU", font=S.font(50, "Black"), fill=ONA, anchor="mm")
d.text((60, 130), "0100 0000", font=S.font(40, "Bold", mono=True), fill=mix(BG, LINE, 0.45))
d.text((60, 180), "0101 0001", font=S.font(40, "Bold", mono=True), fill=mix(BG, LINE, 0.45))
lx, ly, r = 495, 300, 56
for g in range(5):
    rr = r + 14 + g * 15
    d.ellipse([lx - rr, ly - rr, lx + rr, ly + rr], outline=mix(BG, GOOD, 0.55 - g * 0.1), width=11)
lit = mix(GOOD, (255, 255, 236), 0.3)
d.line([(lx - 20, ly + 60), (lx - 20, 478), (cx1 + 24, 478)], fill=LINE, width=8)
d.line([(lx + 20, ly + 60), (lx + 20, 560)], fill=LINE, width=8)
for i, hw in enumerate((30, 20, 10)):
    d.line([(lx + 20 - hw, 560 + i * 12), (lx + 20 + hw, 560 + i * 12)], fill=LINE, width=7)
d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=lit)
d.rectangle([lx - r, ly, lx + r, ly + 45], fill=lit)
d.rounded_rectangle([lx - r - 10, ly + 42, lx + r + 10, ly + 62], 6, fill=mix(lit, LINE, 0.2))
d.ellipse([lx - 34, ly - 40, lx - 8, ly - 12], fill=mix(lit, (255, 255, 255), 0.6))

# --- headline on the right (one word in HILITE)
f = S.font(92, "Black")
x = 690
d.text((x, 150), "HOW YOUR", font=f, fill=TXT)
d.text((x, 260), "CODE BECOMES", font=S.font(76, "Black"), fill=TXT)
d.text((x, 360), "LIGHT", font=S.font(132, "Black"), fill=HIL)

# --- one tilted tag
tag = Image.new("RGBA", (360, 96), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([4, 4, 352, 88], 40, fill=S.BAD)
td.text((178, 46), "INSIDE THE CHIP", font=S.font(38, "Black"), fill=ONA, anchor="mm")
tag = tag.rotate(5, expand=True, resample=Image.BICUBIC)
im.paste(tag, (700, 540), tag)

os.makedirs("thumbs", exist_ok=True)
im.convert("RGB").save("thumbs/ep2_thumbnail.jpg", quality=92)
print("thumbs/ep2_thumbnail.jpg", os.path.getsize("thumbs/ep2_thumbnail.jpg"))
