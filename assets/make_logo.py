"""Crop the Sinai Seeds logo out of a screenshot of Ali Fayed's Facebook post and
write a transparent-background PNG.

Source screenshot: 589x1280, phone UI around the post, pure-black background.
The logo itself is a 363x402 lockup (three leaves over a white sign plate) whose
bottom edge is cut off by the post crop, so the plate is extended by a few pixels
and its bottom corners rounded to match the top ones.

Usage: python3 make_logo.py SOURCE.jpg OUT.png
Needs: pillow, numpy
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
PLATE_EXTEND = 12      # px of white added under "ALI FAYED"
PLATE_RADIUS = 12      # bottom corner radius, matches the sign's top corners

src = Image.open(SRC).convert('RGB')
a = np.asarray(src).astype(np.int16)

# 1. lockup bounding box (the post background is pure black)
m = a.max(axis=2)
ys, xs = np.nonzero(m[420:870, :] > 24)
y0, y1, x0, x1 = ys.min() + 420, ys.max() + 420, xs.min(), xs.max()
crop = a[y0:y1 + 1, x0:x1 + 1]
h, w = crop.shape[:2]
mc = crop.max(axis=2)
mn = crop.min(axis=2)

# 2. white sign plate: the widest near-white band, holes filled so the dark
#    lettering inside stays fully opaque
white = ((mn > 170) & (mc > 200)).astype(np.uint8)
plate_top = np.nonzero(white.sum(axis=1) > 0.5 * w)[0].min()
band = np.zeros_like(white)
band[plate_top:] = white[plate_top:]
band = np.asarray(Image.fromarray((band * 255).astype(np.uint8))
                  .filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)))
ff = Image.fromarray(band).copy()
ImageDraw.floodfill(ff, (0, 0), 128)
plate = np.asarray(ff) != 128
# the crop is exactly as wide as the plate, so its outermost pixel columns are the
# plate's dark JPEG edge; clear them so the erosion below can work from the border
plate[:, :2] = False
plate[:, -2:] = False
# erode 2px so the plate's outer edge falls back to the luminance ramp instead of
# keeping the dark JPEG edge pixels fully opaque
plate_core = Image.fromarray((plate * 255).astype(np.uint8))
plate_core = plate_core.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MinFilter(3))
plate_a = np.asarray(plate_core.filter(ImageFilter.GaussianBlur(0.5))).astype(np.float32) / 255.0

# 3. leaves and edges: alpha ramp from luminance against black
ramp = np.clip((mc.astype(np.float32) - 10.0) / 70.0, 0, 1)
alpha = np.maximum(ramp, plate_a)

# 4. defringe: JPEG edges are blended with black, so pull edge colours in from
#    the nearest opaque pixel instead of leaving a dark rim
rgb = crop.astype(np.float32)
known = alpha >= 0.999

def shift(arr, dy, dx):
    out = np.zeros_like(arr)
    out[max(dy, 0):arr.shape[0] + min(dy, 0), max(dx, 0):arr.shape[1] + min(dx, 0)] = \
        arr[max(-dy, 0):arr.shape[0] + min(-dy, 0), max(-dx, 0):arr.shape[1] + min(-dx, 0)]
    return out

for _ in range(12):
    if known.all():
        break
    acc = np.zeros_like(rgb)
    cnt = np.zeros(alpha.shape, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                k = shift(known.astype(np.float32), dy, dx)
                acc += shift(rgb, dy, dx) * k[..., None]
                cnt += k
    newly = (~known) & (cnt > 0)
    if not newly.any():
        break
    rgb[newly] = acc[newly] / cnt[newly][:, None]
    known = known | newly

# 5. extend the cut-off plate and round its bottom corners
H = h + PLATE_EXTEND
canvas = np.zeros((H, w, 4), np.uint8)
canvas[:h, :, :3] = rgb
canvas[:h, :, 3] = (alpha * 255)
canvas[h:, :, :3] = 255
canvas[h:, :, 3] = 255
# the source's last rows are a half-covered grey edge row: make the seam white
for y in range(max(0, h - 6), h):
    canvas[y, plate[y], :3] = 255

S = 4  # supersample the corner mask
mask = Image.new('L', (w * S, H * S), 0)
d = ImageDraw.Draw(mask)
d.rounded_rectangle([0, 0, w * S - 1, H * S - 1], radius=PLATE_RADIUS * S, fill=255)
mask = np.asarray(mask.resize((w, H), Image.LANCZOS)).astype(np.float32) / 255.0

bottom = np.zeros((H, w), bool)
bottom[plate_top:] = True
canvas[..., 3] = np.where(bottom, (canvas[..., 3] * mask).round(), canvas[..., 3])

res = Image.fromarray(canvas, 'RGBA').crop(Image.fromarray(canvas, 'RGBA').getbbox())
res.save(OUT, optimize=True)
print('wrote', OUT, res.size)
