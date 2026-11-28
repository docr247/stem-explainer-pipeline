"""Thumbnail for Tech 101 ep 4 (chalk): writes thumbs/ep4_thumbnail.jpg (run from src/)."""
import os, math
from PIL import Image, ImageDraw
import style

S = style.get("chalk")
im, d = S.thumb_canvas()

# ---- subject (left): a big chalk plug, its cable, and a "?" with a speech bubble
def box(xy, col, w=7, r=20):
    pts = S._rr_points(xy, r)
    d.rounded_rectangle(xy, r, fill=S.PANEL)
    S.line(d, pts + [pts[0]], col, w)

# cable
S.line(d, [(40, 560), (120, 520), (180, 450), (230, 390)], S.DIM, 12)
# plug body + shell, angled up-right
box((150, 250, 360, 420), S.GOOD, 8, 26)
S.line(d, [(360, 290), (540, 290), (540, 380), (360, 380), (360, 290)], S.LINE, 7)
for x in (400, 460):
    d.rectangle([x, 312, x + 34, 330], fill=S.DIM)
# D+ / D- conversation arrows
S.arrow(d, (560, 470), (240, 470), S.ACCENT, 7)
S.arrow(d, (240, 540), (560, 540), S.HILITE, 7)
S.text(d, (400, 600), "D+  D−", 44, S.DIM, "Bold", "mm")
# speech bubble with the question
box((110, 40, 560, 200), S.HILITE, 7, 40)
S.line(d, [(250, 200), (230, 250), (300, 200)], S.HILITE, 7)
S.text(d, (335, 120), "who are you?", 62, S.HILITE, "Bold", "mm")

# ---- headline (right): 3 heavy lines, one highlighted word
x0 = 640
S.text(d, (x0, 150), "Your PC", 104, S.TXT, "Bold", "lm")
S.text(d, (x0, 285), "ASKS", 128, S.HILITE, "Bold", "lm")
S.text(d, (x0 + S.textlen(d, "ASKS ", 128, "Bold"), 292), "every", 96, S.TXT, "Bold", "lm")
S.text(d, (x0, 420), "device", 104, S.TXT, "Bold", "lm")
S.line(d, [(x0, 345), (x0 + S.textlen(d, "ASKS", 128, "Bold"), 349)], S.HILITE, 8)

# ---- one slightly tilted tag (kept away from the bottom-right corner)
tag = Image.new("RGBA", (460, 96), (0, 0, 0, 0))
td = ImageDraw.Draw(tag)
td.rounded_rectangle([4, 4, 456, 92], 22, fill=S.PANEL + (255,), outline=S.HILITE + (255,), width=6)
td.text((230, 50), "USB, step by step", font=S.font(40, "Bold"), fill=S.HILITE, anchor="mm")
tag = tag.rotate(5, expand=True, resample=Image.BICUBIC)
im.paste(tag, (640, 500), tag)

im = S.finish(im)
os.makedirs("thumbs", exist_ok=True)
im.save("thumbs/ep4_thumbnail.jpg", quality=92)
print("thumbs/ep4_thumbnail.jpg", os.path.getsize("thumbs/ep4_thumbnail.jpg"), "bytes")
