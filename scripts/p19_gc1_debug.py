#!/usr/bin/env python3
"""Diagnostic: which frames trigger GC1 multi-accent, and what is the 2nd run?"""
import cv2, json, sys, os
import numpy as np
sys.path.insert(0, "/home/z/my-project/ems19-repo/scripts")
from p16_gate import decode_frames, accent_mask
import p19_kar as K

mp4 = sys.argv[1]
work = sys.argv[2]
plan = json.load(open(os.path.join(work, "plan_9x16.json")))
accent_rgb = tuple(plan.get("accent_rgb", (189, 255, 0)))
OW, OH = plan["ow"], plan["oh"]
BAND = plan.get("band_px", [int(OH * 0.705), int(OH * 0.795)])
LL = json.load(open(os.path.join(work, "lyric_lines.json")))
windows = K.build_windows(LL["lines"])
for _w in windows:
    _w["t1"] = min(_w["t1"], plan.get("src_dur", 27.91) - 0.02)

def runs_of(fr):
    band = fr[BAND[0]:BAND[1]]
    am = accent_mask(band, accent_rgb)
    cols = am.any(axis=0)
    spans, x = [], 0
    while x < len(cols):
        if cols[x]:
            x2 = x
            while x2 < len(cols) and cols[x2]: x2 += 1
            spans.append([x, x2]); x = x2
        else:
            x += 1
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] <= 6: merged[-1][1] = s[1]
        else: merged.append(list(s))
    out = []
    for m in merged:
        w2 = m[1] - m[0]
        if w2 < 22: continue
        colseg = am[:, m[0]:m[1]]
        vf = float(colseg.any(axis=1).mean())
        out.append({"x0": m[0], "x1": m[1], "w": w2, "vfill": round(vf, 2)})
    return out, am

frames, _ = decode_frames(mp4, step=7, max_n=30, scale=1.0)
tiles = []
for t, fr in frames:
    st = K.kar2_state(t, windows)
    if st is None: continue
    rs, am = runs_of(fr)
    if len(rs) > 1:
        band_img = fr[BAND[0]:BAND[1]].copy()
        for r in rs:
            cv2.rectangle(band_img, (r["x0"], 0), (r["x1"], band_img.shape[0] - 1), (255, 60, 60), 2)
            cv2.putText(band_img, f'w{r["w"]} vf{r["vfill"]}', (r["x0"] + 2, 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 120, 120), 1)
        tiles.append((t, band_img, rs))

print("violations:", len(tiles))
for t, _, rs in tiles:
    print(f"  t={t:.2f}: {rs}")
sheet_h = 140 * max(1, len(tiles))
sheet = Image.new("RGB", (760, sheet_h + 40), (16, 16, 18)) if False else None
from PIL import Image, ImageDraw
sheet = Image.new("RGB", (760, sheet_h + 40), (16, 16, 18))
d = ImageDraw.Draw(sheet)
d.text((10, 8), "GC1 diagnostic: accent runs per violating frame (red boxes)", font=None)
y = 36
for t, bimg, rs in tiles:
    small = cv2.resize(bimg, (720, 112))
    sheet.paste(Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB)), (20, y))
    d.text((20, y + 112), f"t={t:.2f}s runs={rs}", fill=(255, 200, 120))
    y += 140
sheet.save(os.path.join(work, "gc1_diagnostic.jpg"), quality=90)
print("saved", os.path.join(work, "gc1_diagnostic.jpg"))
