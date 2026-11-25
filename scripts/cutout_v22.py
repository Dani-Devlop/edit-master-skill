#!/usr/bin/env python3
"""Cut-out extraction v22.2: multi-window + contrast-boosted rembg u2net + QA gate.
Dark B&W MV frames defeated plain u2net (salvaged mattes = dark full frames).
For each subject: try several source windows, pick best alpha coverage 0.06-0.55
+ sane bbox aspect; pre-boost contrast before rembg; feather edges (3D7 no halo)."""
import os, subprocess
from PIL import Image, ImageOps, ImageFilter
import numpy as np
from rembg import remove, new_session

SRC = "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
OUT = "/home/z/my-project/p22work/assets/cutouts"
os.makedirs(OUT, exist_ok=True)

SUBJECTS = {
    "car": [1.0, 1.3, 2.0, 0.6],
    "stair": [3.5, 12.5, 13.5, 14.5],
    "church": [24.0, 24.8, 25.5, 23.4],
    "duo": [8.0, 9.0, 6.5],
}
sess = new_session("u2net")

def score(alpha):
    cov = (alpha > 128).mean()
    ys, xs = np.where(alpha > 128)
    if len(xs) < 1000:
        return cov, 9.9, None
    bw, bh = xs.max() - xs.min(), ys.max() - ys.min()
    ar = bh / max(1, bw)
    return cov, ar, (xs.min(), ys.min(), xs.max(), ys.max())

for name, windows in SUBJECTS.items():
    best = None
    for t in windows:
        png = f"{OUT}/tmp_{name}_{int(t*10)}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", SRC,
                        "-frames:v", "1", "-vf", "eq=contrast=1.45:brightness=0.10", png], check=True)
        im = Image.open(png).convert("RGBA")
        cut = remove(im, session=sess)
        a = np.array(cut)[..., 3]
        cov, ar, bbox = score(a)
        # QA gate: person-ish coverage + tall-ish bbox
        ok = 0.05 <= cov <= 0.55 and (ar is None or 0.7 <= ar <= 6.0)
        print(f"{name} t={t}: cov={cov:.3f} ar={ar if ar else 0:.2f} ok={ok}")
        if ok:
            s = (cov if cov > 0.10 else 0.0) - abs(ar - 2.2) * 0.02
            if best is None or s > best[0]:
                best = (s, cut, t, cov)
        os.remove(png)
    if best:
        cut = best[1]
        arr = np.array(cut)
        al = arr[..., 3].astype(np.uint8)
        al[al < 45] = 0  # thr (3D7 fringe removal)
        arr[..., 3] = al
        im2 = Image.fromarray(arr)
        ys, xs = np.where(arr[..., 3] > 10)
        im2 = im2.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        # brightness lift: bright-clothed target look
        rgb = np.asarray(im2.convert("RGB")).astype(np.float32)
        rgb = np.clip(rgb * 1.32 + 18, 0, 255).astype(np.uint8)
        im2 = Image.fromarray(rgb).convert("RGBA")
        a2 = np.array(im2)
        a2[..., 3] = np.array(Image.fromarray(a2[..., 3]).filter(ImageFilter.GaussianBlur(1)))
        im2 = Image.fromarray(a2)
        im2.save(f"{OUT}/cut_{name}.png")
        print(f"PICK {name}: t={best[2]} cov={best[3]:.3f} -> cut_{name}.png {im2.size}")
    else:
        print(f"NO PASS for {name}: keep salvaged matte if any")
print("cutouts v22.2 done")
