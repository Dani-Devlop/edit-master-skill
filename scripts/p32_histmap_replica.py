#!/usr/bin/env python3
"""Phase 32 F4 replica-test: ONE histmap scene exercising every adopted helper.
7.0s 720x1280@30. Plate day-relief -> S-curve camera -> spring_pop title ->
peg-doll chroma sprite -> stick-arm pointer -> parabolic_hop crossing ->
plank bridge -> props -> flame cluster -> lower-third -> one-shot foley ->
keyframe QA -> ffmpeg pipe (clean shutdown)."""
import os
import sys
import math
import json
import wave

import numpy as np
from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components", "adopted", "histmap"))
import histmap_kit as HM

WORK = os.environ.get("EMS_WORK", "/tmp/ems-work/p32r2")
QA_DIR = f"{WORK}/histmap_qa"
OUT = f"{WORK}/histmap_replica_7s.mp4"
os.makedirs(QA_DIR, exist_ok=True)

DUR = 7.0
N = int(DUR * HM.FPS)

# 1) green-screen sprite factory -> EXACT extractor (HSV mask + spill suppression)
gs_png = f"{WORK}/pegdoll_gs.png"
HM.peg_doll_sprite(gs_png)
sprite = HM.extract_green_screen_sprite(gs_png, f"{WORK}/pegdoll_rgba.png", target_max_dim=300)

# 2) day relief plate (F12) — 900x1600 overscan
plate = HM.relief_plate(night=False, seed=11)

# 3) foley plan (sparse one-shots, gain band 0.20-0.28)
foley = HM.OneShotFoley(DUR)
foley.thump(0.10, 0.24)          # title slam
foley.thump(0.90, 0.22)          # sprite pop-in
foley.whoosh(1.45, 0.24)         # hop launch
foley.thump(2.10, 0.24)          # hop landing
for k in range(7):               # plank locks (sequential)
    foley.knock(2.55 + k * 0.22, 0.22)
foley.thump(4.20, 0.24)          # props settle
foley.crack(4.75, 0.26)          # campfire one-shot
foley.thump(5.30, 0.24)          # lower-third

# 4) render loop
pipe = HM.FFmpegPipe(OUT, crf=20)
qa = HM.KeyframeQA(n=6)
spring_title = HM.spring_pop
hop = (HM.parabolic_hop(2.10, 1.50, 2.10, (180, 690), (360, 700), hop_height=64.0))

for i in range(N):
    t = i / HM.FPS
    # S-curve camera glide across the plate (900x1600 -> 720x1280 window)
    a = (0, 0, 790, 1405)
    b = (110, 195, 790, 1405)
    img = HM.camera_crop(plate, t, 0.0, 6.2, a, b)

    d = ImageDraw.Draw(img, "RGBA")

    # title (spring_pop scale 0->1.16->0.96->1.0)
    sc = spring_title(t, 0.38)
    if sc > 0.02:
        f = HM.serif_bi(int(52 * sc))
        txt = "THE RIVER CROSSING"
        bb = d.textbbox((0, 0), txt, font=f)
        tx, ty = (HM.W - bb[2] + bb[0]) / 2, int(HM.H * 0.14)
        shp = Image.new("RGBA", (bb[2] - bb[0] + 12, bb[3] - bb[1] + 12), (0, 0, 0, 0))
        ImageDraw.Draw(shp).text((6 - bb[0], 6 - bb[1]), txt, font=f, fill=(INKSH := (20, 16, 10, 200)))
        shp = shp.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(3))
        img.alpha_composite(shp, (int(tx - 6), ty - 6 + 4))
        d.text((tx, ty), txt, font=f, fill=(246, 242, 230, 245))

    # peg-doll courier: spring pop-in -> stick-arm pointer -> parabolic hop
    pop = HM.spring_pop(t - 0.90, 0.38)
    hop_x, hop_y, hop_lift, hop_tilt = HM.parabolic_hop(t, 1.50, 2.10, (170, 700), (368, 712), hop_height=64.0)
    if t < 1.50:
        px, py = 170, 700
    else:
        px, py = hop_x, hop_y
    if pop > 0.02:
        sp_h = int(sprite.height * 0.55 * pop)
        sp_w = int(sprite.width * 0.55 * pop)
        spr = sprite.resize((max(1, sp_w), max(1, sp_h)), Image.LANCZOS)
        if abs(hop_tilt) > 0.3:
            spr = spr.rotate(hop_tilt, expand=True, resample=Image.BICUBIC)
        # contact shadow (F2 discipline: patch + alpha_composite)
        shpatch = Image.new("RGBA", (spr.width + 24, 26), (0, 0, 0, 0))
        ImageDraw.Draw(shpatch).ellipse([8, 6, 8 + spr.width, 20], fill=(0, 0, 0, 80))
        img.alpha_composite(shpatch.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(5)),
                            (int(px - spr.width / 2 - 12), int(py + sp_h / 2 - 16)))
        img.alpha_composite(spr, (int(px - spr.width / 2), int(py - spr.height / 2)))
        # articulated stick-arm with pointer prop (-58deg, inside -45..-68 band)
        d2 = ImageDraw.Draw(img, "RGBA")
        shoulder = (px + int(sp_w * 0.28), py - int(sp_h * 0.10))
        if t < 1.50:
            HM.draw_stick_arm(d2, shoulder, -58.0, int(sp_h * 0.42))
        else:
            HM.draw_stick_arm(d2, shoulder, -50.0, int(sp_h * 0.42))

    # timber plank bridge locks sequentially across the river band
    prog = max(0.0, min(1.0, (t - 2.45) / 1.55))
    HM.draw_timber_plank_bridge(d, 150, int(HM.H * 0.545), 620, prog, planks=7)

    # far-bank props settle at 4.2s (barrel + crate + reeds + watchtower banner)
    pset = HM.spring_pop(t - 4.20, 0.38)
    if pset > 0.02:
        d3 = ImageDraw.Draw(img, "RGBA")
        s3 = pset
        HM.draw_3d_wooden_barrel(d3, int(HM.W * 0.68), int(HM.H * 0.70) + int(18 * (1 - s3)), int(110 * s3))
        HM.draw_3d_cargo_crate(d3, int(HM.W * 0.46), int(HM.H * 0.665) + int(14 * (1 - s3)), int(96 * s3))
        HM.draw_reed_bundle(d3, int(HM.W * 0.24), int(HM.H * 0.60), int(64 * s3))
        HM.draw_watchtower_banner(d3, int(HM.W * 0.84), int(HM.H * 0.46), int(150 * s3), t)

    # campfire: alpha-composited flame cluster (exact adopted helper)
    if t >= 4.7:
        HM.draw_flame_cluster(img, int(HM.W * 0.68), int(HM.H * 0.685),
                              t, intensity=min(1.0, (t - 4.7) / 0.6), seed=3)

    # iron chain locks across the gorge after 5.8s (tangible, not a route line)
    if t >= 5.8:
        HM.draw_iron_chain(ImageDraw.Draw(img, "RGBA"), 640, int(HM.H * 0.52),
                           HM.W - 30, int(HM.H * 0.56), links=9)

    # auto-fit lower-third (34pt -> 28pt when tw > W-56)
    if t >= 5.20:
        HM.draw_lower_third(img, "Chapter One — The Crossing")

    qa.maybe_save(i, N, img, QA_DIR)
    pipe.write(img.convert("RGB").tobytes())

rc, err = pipe.close()   # GOTCHA: stdin.close + stderr.read + wait (never communicate)
print("pipe rc:", rc, "stderr:", err[:200])

# 5) audio: quiet bed + foley mix under 0dB (narration absent in replica test)
bed = (np.sin(2 * np.pi * 58 * np.arange(int(DUR * HM.SR)) / HM.SR) * 0.012).astype(np.float32)
mix = foley.mix_under(bed)
pcm = (mix * 32767).astype(np.int16)
with wave.open(f"{WORK}/histmap_foley.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(HM.SR)
    wf.writeframes(pcm.tobytes())

# mux audio + faststart
import subprocess as sp
sp.run(["ffmpeg", "-y", "-v", "error", "-i", OUT, "-i", f"{WORK}/histmap_foley.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        f"{WORK}/histmap_replica_final.mp4"], check=True)
sp.replace = None
os.replace(f"{WORK}/histmap_replica_final.mp4", OUT)

# 6) verification: ffprobe + neon-route-line absence + QA count
import subprocess
pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_name",
                     "-of", "default=noprint_wrappers=1", OUT], capture_output=True, text=True).stdout

# neon-route-line check: saturated saturated-blue/green/pink line strokes crossing
# the map (histmap hard rule) — scan QA frames for chroma outside histmap palette
viol = 0
for p in qa.saved:
    fr = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
    hsv = __import__("cv2").cvtColor(fr[..., ::-1].astype(np.uint8), __import__("cv2").COLOR_RGB2HSV)
    chroma = (hsv[..., 1] > 110) & (hsv[..., 2] > 70)
    off = chroma & ~(((hsv[..., 0] >= 10) & (hsv[..., 0] <= 30)) |   # parchment/tan family
                     ((hsv[..., 0] >= 95) & (hsv[..., 0] <= 125)) |  # slate-teal family
                     ((hsv[..., 0] >= 170)))                          # ember/red family
    viol += int(off.sum())
report = {
    "out": OUT, "ffprobe": pr.strip().splitlines(),
    "qa_frames": len(qa.saved),
    "qa_files": [os.path.basename(p) for p in qa.saved],
    "neon_route_line_violation_px": viol,
    "serif_font_used": HM._SERIF_LOG,
    "foley_accents": len(foley.used),
    "foley_gain_band": "0.20-0.28",
}
json.dump(report, open(f"{WORK}/histmap_replica_report.json", "w"), indent=1)
print(json.dumps(report, indent=1))
