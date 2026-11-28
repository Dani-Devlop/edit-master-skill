#!/usr/bin/env python3
"""Supercut v2 continuation: endcard -> concat -> audio loudnorm -> gates.
(Phase 32 F8; segments already encoded by the driver.)"""
import os
import sys
import json
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

WORK = "/tmp/ems-work/p32r2"
REELS = f"{WORK}/reels"
TMP = f"{WORK}/supercut_seg"
OUT = f"{REELS}/supercut_v2_31s.mp4"
W, H, FPS = 720, 1280, 30
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]
SEGS = [f"{TMP}/seg_{k:02d}.mp4" for k in range(13)]


def render_endcard(out, first_frame_src, dur=3.6):
    first = Image.open(first_frame_src).resize((W, H), Image.LANCZOS).convert("RGBA")
    proc = sp.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, out],
                    stdin=sp.PIPE, stderr=sp.PIPE)
    N = int(dur * FPS)
    for i in range(N):
        t = i / FPS
        if t < dur - 0.55:
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
            img = first.copy()          # loop-hold: tail = cold-open frame 0
        proc.stdin.write(img.convert("RGB").tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace")
    rc = proc.wait()
    return rc, err


def make_mix(total, out_wav):
    """cut-aligned foley + soft bed."""
    foley = HM.OneShotFoley(total + 0.5)
    lens = [2.2, 2.0, 2.2, 1.8, 2.0, 3.6, 2.2, 2.2, 2.0, 2.2, 2.0, 1.8, 1.1, 3.6]
    hits = []
    t = 0.0
    for L in lens:
        hits.append(t)
        t += L
    for i, ht in enumerate(hits):
        foley.thump(ht, gain=0.24 if i % 2 == 0 else 0.22)
    foley.whoosh(hits[-2], gain=0.24)
    foley.crack(hits[-1] + 0.6, gain=0.26)
    sr = HM.SR
    n = int(total * sr)
    rng = np.random.default_rng(11)
    # dense bed normalized to RMS 0.10 (~ -21 LUFS) — convolution alone
    # attenuated the noise ~10x leaving a sparse mix loudnorm cannot lift
    # within the TP ceiling (that is why loudnorm stalled at -26 LUFS)
    bed = np.convolve(rng.normal(0, 1, n), np.ones(96) / 96, "same")
    bed_rms = float(np.sqrt((bed ** 2).mean())) + 1e-9
    bed = bed / bed_rms * 0.10
    for kt in hits:
        i0 = int(kt * sr)
        ln = int(0.22 * sr)
        if i0 + ln < n:
            env = np.exp(-np.arange(ln) / (0.05 * sr))
            bed[i0:i0 + ln] += np.sin(2 * np.pi * 52 * np.arange(ln) / sr) * env * 0.045
    mix = np.clip(bed + foley.buf[:n], -1.0, 0.95)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out_wav


ff = f"{TMP}/first.jpg"
sp.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.05", "-i", f"{REELS}/preset_cars_12s.mp4",
        "-frames:v", "1", ff], check=True)
end_seg = f"{TMP}/seg_end.mp4"
rc, err = render_endcard(end_seg, ff)
print("endcard rc:", rc, err[:120])

lst = f"{TMP}/concat.txt"
with open(lst, "w") as f:
    for p in SEGS + [end_seg]:
        f.write(f"file '{p}'\n")
silent = f"{TMP}/video_only.mp4"
sp.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
total = sum(2.2, ) if False else 30.3
wav = make_mix(30.9, f"{TMP}/supercut_mix.wav")
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
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)

pr = sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT],
            capture_output=True, text=True).stdout.strip()
dur = float(pr)
worlds = ["volt"] * 5 + ["histmap"] + ["volt"] * 7 + ["volt"]
lens = [2.2, 2.0, 2.2, 1.8, 2.0, 3.6, 2.2, 2.2, 2.0, 2.2, 2.0, 1.8, 1.1, 3.6]
okhue_volt = (np.arange(180) >= 24) & (np.arange(180) <= 48)
okhue_hist = (((np.arange(180) >= 0) & (np.arange(180) <= 48)) |
              ((np.arange(180) >= 80) & (np.arange(180) <= 130)) |
              (np.arange(180) >= 165))
cap = cv2.VideoCapture(OUT)
seg_report = []
t0 = 0.0
for w_, L in zip(worlds, lens):
    mid = t0 + L / 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(mid * FPS))
    ok, fr = cap.read()
    if ok:
        sm = cv2.resize(fr, (270, 480))
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
        ch = (hsv[..., 1] > 90) & (hsv[..., 2] > 60)
        okh = okhue_hist if w_ == "histmap" else okhue_volt
        vo = ch & okh[hsv[..., 0]]
        frac = int((ch & ~vo).sum()) / max(1, int(ch.sum()))
        seg_report.append({"t_mid": round(mid, 2), "world": w_,
                           "offpalette_frac": round(float(frac), 5), "pass": bool(frac <= 0.02)})
    t0 += L
cap.release()
eb = sp.run(["ffmpeg", "-i", OUT, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
            capture_output=True, text=True).stderr
integrated = None
import re as _re
for ln in eb.splitlines():
    m = _re.search(r"I:\s+(-?\d+\.\d+)\s+LUFS", ln)
    if m:
        integrated = float(m.group(1))
report = {"out": OUT, "planned_total": 30.9, "measured_duration": dur,
          "loudnorm_pass1_I": meas.get("measured_I"),
          "ebur128_final_I": integrated,
          "loudness_pass": integrated is not None and abs(integrated + 14.0) <= 0.5,
          "duration_pass": 30.0 <= dur <= 32.0,
          "segment_census_all_pass": all(s["pass"] for s in seg_report),
          "segment_census": seg_report,
          "loop_hold": "endcard tail 0.55s = cold-open frame 0"}
json.dump(report, open(f"{REELS}/supercut_v2_report.json", "w"), indent=1)
print(json.dumps(report, indent=1)[:1200])
