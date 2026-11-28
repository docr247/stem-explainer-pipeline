"""Thumbnail for episode 5 (paper style): writes thumbs/ep5_thumbnail.jpg. Run from src/."""
import os
from PIL import Image, ImageDraw
import style
from ep5 import UC, SC, IC, levf, wave, mini_uart, mini_spi, mini_i2c

S = style.get("paper")
im, d = S.thumb_canvas()

# big subject on the left: a paper scope screen with the three signals
x0, y0, x1, y1 = 50, 70, 640, 640
S.box(d, (x0, y0, x1, y1), S.PANEL, S.LINE, 30, 6)
gc = style.mix(S.PANEL, S.LINE, 0.12)
for i in range(1, 8):
    x = x0 + (x1 - x0) * i / 8
    d.line([(x, y0 + 16), (x, y1 - 16)], fill=gc, width=2)
for j in range(1, 6):
    y = y0 + (y1 - y0) * j / 6
    d.line([(x0 + 16, y), (x1 - 16, y)], fill=gc, width=2)
rows = [("UART", UC, mini_uart, 175), ("SPI", SC, mini_spi, 355), ("I²C", IC, mini_i2c, 535)]
for n, c, fn, yc in rows:
    S.pill(d, (130, yc), n, 34, c)
    fn(d, 220, 615, yc, 26, c, 1.0, 1.0, width=8)

# headline on the right, one word highlighted
f = S.font(104, "Black")
d.text((690, 110), "HOW CHIPS", font=f, fill=S.TXT)
d.text((690, 230), "TALK", font=S.font(150, "Black"), fill=S.HILITE)
d.text((690, 395), "TO EACH OTHER", font=S.font(72, "Black"), fill=S.TXT)

# one slightly tilted tag
fs = S.font(44, "Bold")
s = "UART vs SPI vs I²C"
tw = int(d.textlength(s, font=fs)) + 56
tile = Image.new("RGBA", (tw + 30, 110), (0, 0, 0, 0))
td = ImageDraw.Draw(tile)
td.rounded_rectangle([12, 18, 12 + tw, 96], 22, fill=(90, 70, 50, 70))
td.rounded_rectangle([4, 8, 4 + tw, 86], 22, fill=S.EXTRA + (255,))
td.text((4 + tw / 2, 47), s, font=fs, fill=S.ON_ACCENT + (255,), anchor="mm")
tile = tile.rotate(4, expand=True, resample=Image.BICUBIC)
im.paste(tile, (700, 500), tile)

os.makedirs("thumbs", exist_ok=True)
im.save("thumbs/ep5_thumbnail.jpg", quality=92)
print("thumbs/ep5_thumbnail.jpg", os.path.getsize("thumbs/ep5_thumbnail.jpg"))
