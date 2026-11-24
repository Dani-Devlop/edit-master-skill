#!/usr/bin/env python3
"""Generate a painterly still-life card (AS1 'generated' asset — no third-party
rights). Deterministic. Replaces the unreachable public-domain CDN download
(logged honestly in the asset registry)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

rng = np.random.RandomState(1633)
W, H = 1200, 960
im = Image.new("RGB", (W, H), (38, 30, 24))
d = ImageDraw.Draw(im, "RGBA")

# backdrop gradient (warm dark)
g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
bg = (np.array([44, 34, 26])[None, None, :] * (1 - g)
      + np.array([22, 16, 12])[None, None, :] * g)
bg = np.repeat(bg, W, axis=1)
im = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(im, "RGBA")

# table plane
d.rectangle([0, int(H * 0.68), W, H], fill=(58, 44, 32, 255))
d.line([(0, int(H * 0.68)), (W, int(H * 0.68))], fill=(80, 62, 44, 255), width=3)

# wicker basket (weave arcs)
cx, cy, bw, bh = W // 2, int(H * 0.70), 300, 130
for i in range(9):
    a = 255 - i * 12
    d.ellipse([cx - bw // 2 + i * 8, cy - bh // 2 + i * 6,
               cx + bw // 2 - i * 8, cy + bh // 2 - i * 3],
              outline=(124, 92, 58, a), width=5)
d.ellipse([cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + int(bh * 0.72)],
          fill=(96, 72, 46, 255))

# lemons (painterly ellipses + nub + highlight)
def lemon(x, y, rx, ry, tilt):
    lem = Image.new("RGBA", (rx * 3, ry * 3), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lem)
    dl.ellipse([rx // 2, ry, rx * 2 + rx // 2, ry * 3], fill=(226, 196, 60, 255))
    dl.ellipse([rx * 1.1, ry * 1.2, rx * 1.9, ry * 2.6], fill=(240, 216, 92, 180))
    dl.ellipse([rx * 1.55, ry * 0.95, rx * 1.85, ry * 1.25], fill=(196, 164, 40, 255))
    dl.ellipse([rx * 1.2, ry * 1.4, rx * 1.6, ry * 1.8], fill=(250, 236, 150, 200))
    lem = lem.rotate(tilt, expand=True, resample=Image.BICUBIC)
    return lem

for (lx, ly, rx, ry, tl) in [(cx - 90, cy - 40, 46, 30, 14), (cx + 40, cy - 55, 52, 34, -10),
                             (cx + 130, cy - 25, 40, 27, 22), (cx - 20, cy - 15, 58, 36, 4)]:
    card = lemon(lx, ly, rx, ry, tl)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.ellipse([lx - rx, ly - ry // 2, lx + rx * 2, ly + ry], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    im.paste(Image.alpha_composite(im.convert("RGBA"), sh).convert("RGB"), (0, 0))
    im.paste(card, (lx - rx, ly - ry * 2), card)
    d = ImageDraw.Draw(im, "RGBA")

# painterly texture: brush strokes + grain + vignette
for _ in range(900):
    x, y = rng.randint(0, W), rng.randint(0, H)
    l = rng.randint(6, 26)
    a = rng.randint(10, 34)
    dx, dy = rng.randn() * 6, rng.randn() * 2
    d.line([(x, y), (x + l, y + dy)], fill=(255, 255, 255, a if rng.rand() > .6 else 0), width=1)
arr = np.asarray(im).astype(np.float32)
arr += rng.normal(0, 5.5, arr.shape)
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
arr *= (1 - 0.32 * np.clip(r - 0.55, 0, 1))[..., None]
Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(
    "/tmp/ems-work/p19/run/assets/painting_lemons.jpg", quality=92)
print("generated still-life card saved (1200x960, deterministic seed 1633)")
