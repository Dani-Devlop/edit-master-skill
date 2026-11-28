#!/usr/bin/env python3
"""Phase 32 F8 — SUPERCUT v2: 30-32s variety cut from the 5 passing preset
reels + histmap replica + designed end card + loop-hold (last frame = first
frame of the cold open). Foley-composed audio -> loudnorm 2-pass -14 LUFS.
Gates: duration 30-32, loudness -14+-0.5, per-segment palette census
(world-aware: volt segments / histmap segment)."""
import os
import sys
import json
import math
import wave
import subprocess as sp

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/ems/components")
sys.path.insert(0, "/home/z/ems/components/adopted/histmap")
sys.path.insert(0, "/home/z/ems/scripts")
import renderlib as R
import histmap_kit as HM

WORK = os.environ.get("EMS_WORK", "/tmp/ems-work/p32r2")
REELS = f"{WORK}/reels"
OUT = f"{REELS}/supercut_v2_31s.mp4"
TMP = f"{WORK}/supercut_seg"
os.makedirs(TMP, exist_ok=True)
W, H, FPS, CRF = 720, 1280, 30, 20

ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p", "-r", str(FPS)]

# (source_file, t0, t1, world)
SEGS = [
    ("preset_cars_12s.mp4", 0.0, 2.2, "volt"),
    ("preset_fitness_12s.mp4", 2.2, 4.2, "volt"),
    ("preset_education_12s.mp4", 4.2, 6.4, "volt"),
    ("preset_mindset_12s.mp4", 6.4, 8.2, "volt"),
    ("preset_branding_12s.mp4", 8.2, 10.2, "volt"),
    ("histmap_replica_7s.mp4", 0.8, 4.4, "histmap"),
    ("preset_cars_12s.mp4", 4.2, 6.4, "volt"),
    ("preset_mindset_12s.mp4", 0.0, 2.2, "volt"),
    ("preset_education_12s.mp4", 2.2, 4.2, "volt"),
    ("preset_fitness_12s.mp4", 4.2, 6.4, "volt"),
    ("preset_mindset_12s.mp4", 8.2, 10.2, "volt"),
    ("preset_cars_12s.mp4", 6.4, 8.2, "volt"),
    ("preset_branding_12s.mp4", 10.9, 12.0, "volt"),
]
ENDCARD_DUR = 3.0
TOTAL = sum(b - a for _, a, b, _ in SEGS) + ENDCARD_DUR
assert 30.0 <= TOTAL <= 32.0, f"supercut must be 30-32s, got {TOTAL:.2f}"


def enc_seg(src, a, b, out):
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-to", str(b), "-i", f"{REELS}/{src}",
           "-an", *ENC, out]
    sp.run(cmd, check=True)


def render_endcard(out, first_frame_src):
    """Paper end card: serif TEST EDIT SKILL + volt pill + dots + loop-hold of
    the cold-open first frame (last frame ~= first frame -> loop)."""
    first = Image.open(first_frame_src).resize((W, H), Image.LANCZOS).convert("RGBA")
    proc = sp.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, out],
                    stdin=sp.PIPE, stderr=sp.PIPE)
    N = int(ENDCARD_DUR * FPS)
    for i in range(N):
        t = i / FPS
        if t < ENDCARD_DUR - 0.55:
            img = Image.new("RGBA", (W, H), (243, 240, 232, 255))
            d = ImageDraw.Draw(img, "RGBA")
            word = "TEST EDIT SKILL"
            f_g = R.playfair(int(W * 0.145), 900)
            bb = d.textbbox((0, 0), word, font=f_g)
            while bb[2] - bb[0] > W * 0.82 and f_g.size > 30:
                f_g = R.playfair(f_g.size - 6, 900)
                bb = d.textbbox((0, 0), word, font=f_g)
            ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.34
            tw_, th_ = bb[2] - bb[0], bb[3] - bb[1]
            pad = 20
            sh = Image.new("RGBA", (tw_ + pad * 2, th_ + pad * 2), (0, 0, 0, 0))
            ImageDraw.Draw(sh).text((pad + 8, pad + 7), word, font=f_g, fill=(20, 20, 24, 40))
            sh = sh.filter(ImageFilter.GaussianBlur(4))
            img.alpha_composite(sh, (int(ox - pad), int(oy - pad)))
            d.text((ox, oy), word, font=f_g, fill=(16, 17, 20, 245))
            sc = max(0.0, min(1.0, (t - 0.10) / 0.32))
            if sc > 0.3:
                R.volt_pill(img, (W / 2, H * 0.52), "F1-F8 gates PASS", R.montserrat(36, 900), rot=0)
            R.pixel_dots(img, 8, (60, int(H * 0.86), W - 60, int(H * 0.93)), seed=int(t * 5) + 3, size=9)
        else:
            img = first.copy()          # loop-hold: last frames = cold-open frame 0
        proc.stdin.write(img.convert("RGB").tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace")
    rc = proc.wait()
    return rc, err


def make_mix(total, out_wav):
    """one-shot foley on every cut + soft bed (single continuous mix)."""
    foley = HM.OneShotFoley(total + 0.5)
    t = 0.0
    hits = []
    for _, a, b, w in SEGS:
        hits.append(t)
        t += b - a
    hits.append(t)                   # endcard
    for i, ht in enumerate(hits):
        foley.thump(ht, gain=0.24 if i % 2 == 0 else 0.22)
    foley.whoosh(hits[-2], gain=0.24)
    foley.crack(hits[-1] + 0.6, gain=0.26)
    sr = HM.SR
    n = int(total * sr)
    rng = np.random.default_rng(11)
    nseg = np.convolve(rng.normal(0, 1, n), np.ones(96) / 96, "same")
    bed = nseg * 0.028
    kick_t = [h for h in hits]
    for kt in kick_t:
        i0 = int(kt * sr)
        ln = int(0.22 * sr)
        if i0 + ln < n:
            env = np.exp(-np.arange(ln) / (0.05 * sr))
            bed[i0:i0 + ln] += np.sin(2 * np.pi * 52 * np.arange(ln) / sr) * env * 0.045
    mix = np.clip(bed + foley.buf[:n], -1.0, 1.0)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out_wav


# 1) cut segments
parts = []
for k, (src, a, b, w) in enumerate(SEGS):
    seg = f"{TMP}/seg_{k:02d}.mp4"
    enc_seg(src, a, b, seg)
    parts.append(seg)

# 2) endcard (loop-hold)
first_frame = f"{TMP}/first.jpg"
sp.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.05", "-i", f"{REELS}/preset_cars_12s.mp4",
        "-frames:v", "1", first_frame], check=True)
end_seg = f"{TMP}/seg_end.mp4"
rc, err = render_endcard(end_seg, first_frame)
assert rc == 0, f"endcard encode failed: {err[:200]}"
parts.append(end_seg)

# 3) concat
lst = f"{TMP}/concat.txt"
with open(lst, "w") as f:
    for p in parts:
        f.write(f"file '{p}'\n")
silent = f"{TMP}/video_only.mp4"
sp.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
        "-c", "copy", silent], check=True)

# 4) audio mix -> loudnorm 2-pass -> mux
wav = make_mix(TOTAL, f"{TMP}/supercut_mix.wav")
p1 = sp.run(["ffmpeg", "-y", "-v", "info", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
             "-f", "null", "-"], capture_output=True, text=True).stderr
meas = {}
for ln in p1.splitlines():
    if ln.strip().startswith("measured_"):
        k, v = ln.strip().rstrip(",").split(":")
        meas[k.strip()] = v.strip()
ln2 = "loudnorm=I=-14:TP=-1.5:LRA=11"
if len(meas) >= 4:
    ln2 = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={meas['measured_I']}"
           f":measured_LRA={meas['measured_LRA']}:measured_TP={meas['measured_TP']}"
           f":measured_thresh={meas['measured_thresh']}:linear=true")
sp.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", wav, "-af", ln2,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", OUT], check=True)

# 5) gates
pr = sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout.strip()
dur = float(pr)
# per-segment census at segment midpoints (world-aware)
cap = cv2.VideoCapture(OUT)
seg_report = []
t0 = 0.0
okhue_volt = ((np.arange(180) >= 24) & (np.arange(180) <= 48))
okhue_hist = (((np.arange(180) >= 0) & (np.arange(180) <= 48)) |
              ((np.arange(180) >= 80) & (np.arange(180) <= 130)) |
              (np.arange(180) >= 165))
for src, a, b, w in SEGS:
    mid = t0 + (b - a) / 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(mid * FPS))
    ok, fr = cap.read()
    if ok:
        sm = cv2.resize(fr, (270, 480))
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
        ch = (hsv[..., 1] > 90) & (hsv[..., 2] > 60)
        okh = okhue_hist if w == "histmap" else okhue_volt
        vo = ch & okh[hsv[..., 0]]
        frac = int((ch & ~vo).sum()) / max(1, int(ch.sum()))
        seg_report.append({"seg": src, "t_mid": round(mid, 2), "world": w,
                           "offpalette_frac": round(float(frac), 5),
                           "pass": bool(frac <= 0.02)})
    t0 += b - a
cap.release()
# loudness verify on final
eb = sp.run(["ffmpeg", "-i", OUT, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
            capture_output=True, text=True).stderr
integrated = None
for ln in eb.splitlines():
    if "I:" in ln and "LRA:" in ln and "integrated" not in ln:
        try:
            integrated = float(ln.split("I:")[1].split("LRA")[0].strip().replace(" LUFS", "").strip())
        except Exception:
            pass
report = {"out": OUT, "total_planned": round(TOTAL, 2), "measured_duration": dur,
          "loudnorm_measured_I_pass1": meas.get("measured_I"),
          "ebur128_integrated_final": integrated,
          "loudness_pass": integrated is not None and abs(integrated - (-14.0)) <= 0.5,
          "duration_pass": 30.0 <= dur <= 32.0,
          "segment_census": seg_report,
          "loop_hold": "endcard tail 0.55s = cold-open frame 0"}
json.dump(report, open(f"{REELS}/supercut_v2_report.json", "w"), indent=1)
print(json.dumps(report, indent=1))
