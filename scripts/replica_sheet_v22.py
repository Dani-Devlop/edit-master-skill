#!/usr/bin/env python3
"""R2d side-by-side sheet v22g: GRID layout (2 pair-columns x 5 rows) for stable
vision reading. [target | replica] at matched clock times. Blind critic input."""
import subprocess, os, sys
from PIL import Image, ImageDraw

TGT = "/home/z/my-project/upload/VID_20261121_000716_199.mp4"
ASSETS = "/home/z/my-project/p22work/assets"
REPL = "/tmp/ems-work/p22/replica_frames"
TAG = sys.argv[1] if len(sys.argv) > 1 else "r1"
REPL = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ems-work/p22/replica_frames"
OUT = f"{ASSETS}/replica_v22_sidebyside_{TAG}.jpg"
TIMES = [0.3, 1.0, 1.7, 2.4, 3.1, 3.8, 4.5, 5.2, 5.9, 6.6]
TGT_DUR = 6.893
REP_DUR = 12.0
# story-matched mapping: replica stretches target's 6.9s edit to 12s (inventory
# replica mapping) -> compare target t with replica t * REP_DUR/TGT_DUR
GRID_END = 8.9   # replica grid zone ends at M1_START-0.17; M1+endcard are
                  # our extension beats, not in the target -> compare grid-only
def rep_t(t):
    return min(GRID_END, t * GRID_END / TGT_DUR)
TW, TH = 380, 676

def grab(video, t, tag):
    p = f"{ASSETS}/tgt_{tag}_{int(t*100)}.png"
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", video,
                        "-frames:v", "1", "-vf", "scale=1080:1920", p], check=True)
    return Image.open(p).convert("RGB")

PW, PH = TW * 2 + 8, TH + 26
COLS, ROWS = 2, 5
G = 10
sheet = Image.new("RGB", (COLS * PW + (COLS + 1) * G, ROWS * PH + (ROWS + 1) * G), (18, 18, 20))
for i, t in enumerate(TIMES):
    tgt = grab(TGT, t, "a").resize((TW, TH))
    fi = min(359, int(rep_t(t) * 30))
    rep = Image.open(f"{REPL}/f_{fi:05d}.jpg").resize((TW, TH))
    pair = Image.new("RGB", (PW, PH), (12, 12, 12))
    pair.paste(tgt, (0, 26))
    pair.paste(rep, (TW + 8, 26))
    d = ImageDraw.Draw(pair)
    d.text((6, 5), f"t={t}s TARGET", fill=(240, 240, 240))
    d.text((TW + 14, 5), f"t={t}s REPLICA", fill=(240, 240, 240))
    c, r = i % COLS, i // COLS
    sheet.paste(pair, (G + c * (PW + G), G + r * (PH + G)))
sheet.save(OUT, quality=88)
print("sheet:", OUT, sheet.size)
