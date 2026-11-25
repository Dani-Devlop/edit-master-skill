#!/usr/bin/env python3
"""R2d side-by-side contact sheet: [target frame | replica frame] at matched clock times."""
import subprocess, os
from PIL import Image, ImageDraw

TGT = "/home/z/my-project/upload/VID_20261121_000716_199.mp4"
REPL = "/tmp/my-project/p21work/scratch/replica_frames"
OUT = "/tmp/my-project/p21work/scratch/replica_sidebyside.jpg"
TIMES = [0.3, 1.0, 1.7, 2.4, 3.1, 3.8, 4.5, 5.2, 5.9, 6.6]
TW, TH = 300, 533

def grab(video, t):
    p = f"/tmp/my-project/p21work/scratch/tgt_{int(t*100)}.png"
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", video,
                        "-frames:v", "1", "-vf", "scale=1080:1920", p], check=True)
    return Image.open(p).convert("RGB")

tiles = []
for t in TIMES:
    tgt = grab(TGT, t).resize((TW, TH))
    fi = min(359, int(t * 30))
    rep = Image.open(f"{REPL}/r_{fi:05d}.jpg").resize((TW, TH))
    pair = Image.new("RGB", (TW * 2 + 8, TH + 26), (12, 12, 12))
    pair.paste(tgt, (0, 26))
    pair.paste(rep, (TW + 8, 26))
    d = ImageDraw.Draw(pair)
    d.text((6, 4), f"t={t}s TARGET", fill=(240, 240, 240))
    d.text((TW + 14, 4), f"t={t}s REPLICA", fill=(240, 240, 240))
    tiles.append(pair)

sheet = Image.new("RGB", (tiles[0].width, sum(t.height for t in tiles) + 4 * len(tiles)), (12, 12, 12))
y = 0
for tl in tiles:
    sheet.paste(tl, (0, y))
    y += tl.height + 4
sheet.save(OUT, quality=85)
print("side-by-side sheet", OUT, sheet.size)
