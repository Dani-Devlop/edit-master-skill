#!/usr/bin/env python3
"""v22 asset prep: polaroid sources (real MV frames + white border), MV stills.
Cutouts run separately (rembg) after pip install completes."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFilter

MV = os.environ.get("EMS_MV", "/tmp/ems-work/current/src.mp4")
SCRATCH = os.environ.get("EMS_SCRATCH", "/tmp/ems-work/current/scratch")
os.makedirs(SCRATCH, exist_ok=True)

# polaroid frames: 3 real MV moments (car roof @1.2, stairwell @1.35 shift, church @12.6)
WINDOWS = [(1.2, 0), (1.5, 1), (12.6, 2)]
for t, idx in WINDOWS:
    raw = f"{SCRATCH}/pola_raw_{idx}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", MV, "-frames:v", "1", raw], check=True)
    im = Image.open(raw).convert("RGB")
    # polaroid: photo inset on white card
    PW, PH = 460, 560
    card = Image.new("RGB", (PW, PH), (244, 242, 236))
    iw = PW - 48
    ih = int(im.height * iw / im.width)
    if ih > PH - 130:
        ih = PH - 130
        iw = int(im.width * ih / im.height)
    im2 = im.resize((iw, ih), Image.LANCZOS)
    card.paste(im2, (24, 24))
    d = ImageDraw.Draw(card)
    # grain + border shadow line
    import numpy as np
    arr = np.array(card).astype(np.int16)
    g = np.random.default_rng(idx).normal(0, 4, arr.shape[:2])[..., None].astype(np.int16)
    arr = np.clip(arr + g, 0, 255).astype(np.uint8)
    card = Image.fromarray(arr)
    card = card.convert("RGBA")
    # drop shadow
    sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([20 + 6, 20 + 8, 20 + card.width + 10, 20 + card.height + 12], fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(card, (20, 20))
    sh.save(f"{SCRATCH}/pola_{idx}.png")
    print("pola", idx, "ok", card.size)

print("prep done")
