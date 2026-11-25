#!/usr/bin/env python3
"""M1 test strip: composite slam frames over a white canvas, 4x2 tile proof."""
import os
from PIL import Image

SEQ = "/tmp/my-project/p21work/scratch/m1_seq"
OUT = "/tmp/my-project/p21work/scratch/m1_test_strip.jpg"
PICK = [0, 6, 9, 12, 24, 48, 72, 83]
W, H = 540, 960

tiles = []
for f in PICK:
    p = os.path.join(SEQ, f"f_{f:04d}.png")
    fg = Image.open(p).convert("RGBA").resize((W, H))
    # white designed canvas: subtle paper grain + volt bottom band hint
    bg = Image.new("RGBA", (W, H), (250, 250, 248, 255))
    px = bg.load()
    for y in range(H):
        for x in range(0, W, 3):
            pass  # plain white for alpha proof clarity
    comp = Image.alpha_composite(bg, fg)
    tiles.append(comp.convert("RGB"))

sheet = Image.new("RGB", (W * 4 + 6 * 5, H * 2 + 6 * 3), (18, 18, 18))
for i, t in enumerate(tiles):
    x = (i % 4) * (W + 6) + 6
    y = (i // 4) * (H + 6) + 6
    sheet.paste(t, (x, y))
sheet.save(OUT, quality=88)
print("strip saved", OUT, sheet.size)

# alpha cleanliness audit: fringe/halo check on edges of opaque regions
import numpy as np
fg = Image.open(os.path.join(SEQ, "f_0060.png")).convert("RGBA")
a = np.array(fg)
alpha = a[..., 3]
solid = alpha > 200
edge = (alpha > 10) & (alpha <= 200)
print(f"opaque_px={solid.sum()} edge_px={edge.sum()} edge_ratio={edge.sum()/max(1,solid.sum()):.4f}")
rgb_edge = a[edge][:, :3].astype(float)
rgb_solid = a[solid][:, :3].astype(float)
print(f"edge_mean_rgb={rgb_edge.mean(axis=0).round(1)} solid_mean_rgb={rgb_solid.mean(axis=0).round(1)}")
