#!/usr/bin/env python3
"""Phase 24 delivery package: decoded-frame crop proofs (visual truth),
contact sheet, grid-designed cover, cue sheet + manifest with sha256 chain +
gate/preset/engine hashes. All from the DELIVERED master file.
Usage: p24_package.py"""
import os, json, hashlib, subprocess, shutil, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FINAL = "/home/z/my-project/download/phase24_deliverables/T1_welcome_v24_9x16.mp4"
OUT = "/home/z/my-project/download/phase24_deliverables"
REPO = "/home/z/my-project/download/edit-master-skill"
os.makedirs(OUT, exist_ok=True)

def sha256(p, n=64):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]

def grab(t, out, w=1080, h=1920):
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        return out
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", FINAL,
                    "-frames:v", "1", "-vf", f"scale={w}:{h}", out], check=True)
    return out

F = "/tmp/ems-work/p24/pkg"
os.makedirs(F, exist_ok=True)

# ---- 1. crop proofs (decoded from DELIVERED file) ----
claims = [
    (0.50, "IG4 hook slam + LF3 full-bleed + brackets + artist tape", (60, 160, 1020, 860)),
    (2.45, "IG2 cursor-tap beat + F2 shrink-card transition", (140, 380, 940, 1560)),
    (4.10, "LB2 ghost quote + F3 hourglass + dutch", (60, 480, 1020, 1500)),
    (6.70, "LF2 video-in-card live + IG2 comment bubble", (700, 40, 1080, 700)),
    (8.30, "IG10 zoom punch keyword + density band (F1)", (700, 100, 1080, 800)),
    (9.90, "M3 counter ring + IG2 notification banner", (60, 400, 1020, 1500)),
    (11.55,"F2 shrink-card zoom-through mid-transition", (60, 300, 1020, 1650)),
    (12.60,"LB5 real PD painting polaroid + highlighter pill", (120, 400, 960, 1500)),
    (14.20,"M2 floating polaroids parallax (live video in cards)", (60, 350, 1020, 1500)),
    (15.60,"LB6 polaroid cascade + connector + M5 world insert", (60, 350, 1020, 1550)),
    (17.05,"IG6 selective-color isolation (volt only)", (60, 400, 1020, 1500)),
    (18.60,"IG10 speed ramp 0.4x-1.6x + IG2 heart burst", (60, 350, 1020, 1550)),
    (21.10,"IG4 homicide slam + IG10 freeze+slam + caution tape", (60, 250, 1020, 1450)),
    (22.40,"M4 callout orbit", (60, 350, 1020, 1500)),
    (24.10,"M1 persp3d volt/chrome 3D type slam (integrated)", (60, 250, 1020, 1450)),
    (26.90,"LB10 loop echo end card (IG3) - no brand", (60, 400, 1020, 1600)),
]
rows = []
for t, claim, box in claims:
    full = f"{F}/proof_{int(t*10)}.png"
    grab(t, full)
    im = Image.open(full)
    rows.append((t, claim, im.crop(box), im.resize((270, 480))))

sheet = Image.new("RGB", (1080, len(rows) * 250 + 60), (12, 12, 12))
d = ImageDraw.Draw(sheet)
f_title = ImageFont.truetype(f"{REPO}/assets/fonts/Montserrat.ttf", 30)
f_small = ImageFont.truetype(f"{REPO}/assets/fonts/Montserrat.ttf", 22)
d.text((20, 12), "T-1 v24 VISUAL TRUTH — decoded-frame crop proofs (delivered file)", font=f_title, fill=(240, 240, 235))
y = 60
for (t, claim, crop, thumb) in rows:
    th = thumb.copy(); th.thumbnail((200, 230))
    sheet.paste(th, (20, y))
    ch = crop.copy(); ch.thumbnail((420, 230))
    sheet.paste(ch, (240, y))
    d.text((680, y + 20), f"t={t}s", font=f_small, fill=(216, 243, 74))
    for k in range(0, len(claim), 42):
        d.text((680, y + 54 + k * 5), claim[k:k + 42], font=f_small, fill=(230, 230, 226))
    y += 250
sheet.save(f"{OUT}/proof_crop_index_T1_v24.jpg", quality=86)
print("crop index done", flush=True)

# ---- 2. contact sheet (scene census) ----
picks = [5, 75, 100, 205, 250, 300, 350, 420, 470, 520, 560, 640, 700, 730, 790, 830]
tiles = []
for f_ in picks:
    full = f"{F}/cs_{f_}.png"
    grab(f_ / 30.0, full)
    tiles.append(Image.open(full).resize((260, 462)))
cs = Image.new("RGB", (260 * 4 + 40, 462 * 4 + 40), (10, 10, 10))
for i, tl in enumerate(tiles):
    cs.paste(tl, ((i % 4) * 260 + 8, (i // 4) * 462 + 8))
cs.save(f"{OUT}/contact_sheet_T1_v24.jpg", quality=85)
print("contact sheet done", flush=True)

# ---- 3. cover = first frame designed for grid (IG9) ----
grab(0.0, f"{F}/cover_raw.png")
c = Image.open(f"{F}/cover_raw.png")
c.save(f"{OUT}/cover_T1_v24.jpg", quality=90)
print("cover done", flush=True)

# ---- 4. manifest + hashes ----
gates = json.load(open(f"{REPO}/test-results/g24_gates.json"))
plan = json.load(open("/tmp/ems-work/p24/t1_v24_plan.json"))
cues = json.load(open("/tmp/ems-work/p24/t1_v24_cuesheet.json"))
replica = json.load(open("/home/z/my-project/p22work/assets/critic_v24_r24b2.json"))
preset_sha = sha256(f"{REPO}/presets/mv_darkmono.json", 16)
manifest = {
    "master": os.path.basename(FINAL),
    "sha256_16": sha256(FINAL, 16),
    "sha256": sha256(FINAL),
    "bytes": os.path.getsize(FINAL),
    "duration_s": 27.9, "resolution": "1080x1920@30",
    "song": "WELCOME — IDK feat. Eminem & J Dilla (verified p19/p21)",
    "audio": {"lufs_i": gates["G8_loudness"]["integrated_lufs"],
              "tp_dbfs": gates["G8_loudness"]["true_peak_dbfs"],
              "sfx_cues": len(cues["cues"]), "crackle_bed": True,
              "dropout_before_slams": True, "kick_reinforced": cues["kick_reinforced"]},
    "gates": {"pass": sum(1 for v in gates.values() if isinstance(v, dict) and v.get("pass")),
              "total": len(gates), "file": "test-results/g24_gates.json",
              "gates_sha16": sha256(f"{REPO}/test-results/g24_gates.json", 16)},
    "ig1_onset_lock_pct": gates["IG9_onset_lock"]["pct"],
    "ig3_loop_sim": gates["IG10_loop_sim"]["first_last_corr"],
    "ig7_interval_median_s": gates["IG11_pacing"]["median_s"],
    "ig2_ui_beats": gates["IG17_ui_beats"]["count"],
    "ig10_camera_moves": gates["IG16_camera_moves"]["distinct_moves"],
    "sticker_map": plan["sticker_map"],
    "preset_sha16": preset_sha,
    "engine_sha16": {p: sha256(f"{REPO}/scripts/{p}", 16) for p in
                     ("render_t1_v24.py", "t1_audio_v24.py", "gates_t1_v24.py")},
    "component_sha16": {p: sha256(f"{REPO}/components/{p}", 16) for p in
                        ("ig24kit.py", "renderlib.py")},
    "replica_verdict": {"rounds": 1, "runs": replica["runs_overall"],
                        "median": replica["median_overall"], "bar": 8.5,
                        "method": "r21 register (decoded-quadrant R0) + IG additions"},
    "engines": "pil/numpy canvas+type, persp3d M1-M5 (bpy unavailable this session, honest substitute), librosa onsets, ffmpeg assemble/2-pass loudnorm",
    "deliverables": ["T1_welcome_v24_9x16.mp4", "T1_welcome_v24_9x16_tg.mp4",
                     "cover_T1_v24.jpg", "contact_sheet_T1_v24.jpg",
                     "proof_crop_index_T1_v24.jpg", "cue_sheet_T1_v24.json",
                     "manifest_T1_v24.json"],
}
json.dump(manifest, open(f"{OUT}/manifest_T1_v24.json", "w"), indent=1)
shutil.copy("/tmp/ems-work/p24/t1_v24_cuesheet.json", f"{OUT}/cue_sheet_T1_v24.json")
print("MANIFEST master sha16:", manifest["sha256_16"])
for f_ in sorted(os.listdir(OUT)):
    print("  ", f_, os.path.getsize(f"{OUT}/{f_}") // 1024, "KB")
print("PACKAGE DONE")
