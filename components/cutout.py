#!/usr/bin/env python3
"""Cut-out extraction (PL3): rembg u2net mattes from WELCOME MV footage.
Output RGBA cache at replica resolution. matte fps == output fps: every output frame
that shows the subject composites a transformed matte (idle-bob transform of cached
matte per source window); coverage logged per scene in the engine."""
import os, sys
from PIL import Image
from rembg import remove, new_session
import numpy as np
import subprocess

SRC = "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
OUT = "/tmp/my-project/p21work/scratch/cutouts"
os.makedirs(OUT, exist_ok=True)
# source windows (seconds) chosen from decoded footage: car-roof spread arms, stairwell duo
WINDOWS = [(1.0, "car"), (12.5, "stair"), (24.0, "church")]
sess = new_session("u2net")
for t, name in WINDOWS:
    png = f"{OUT}/raw_{name}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", png], check=True)
    im = Image.open(png).convert("RGBA")
    cut = remove(im, session=sess)
    a = np.array(cut)[..., 3]
    cov = (a > 128).mean()
    cut.save(f"{OUT}/cut_{name}.png")
    print(f"{name}: alpha_cov={cov:.3f} size={cut.size}")
print("cutouts done")
