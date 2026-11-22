#!/usr/bin/env python3
"""Rebuild audio mix for a generated-bed video (no re-render): bed+sfx from plan,
compressor+loudnorm chain, re-mux onto final video. Usage: p14_reaudio.py <work> <final.mp4> <bpm> <style> <energy>"""
import sys, json, subprocess, numpy as np
sys.path.insert(0, "/home/z/my-project/scripts")
from p14_lib import (music_bed, write_wav, sfx_whoosh, sfx_glitch, sfx_splice, sfx_thump, SR)

WORK, FINAL, BPM, STYLE, ENERGY = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], float(sys.argv[5])
plan = json.load(open(f"{WORK}/plan_9x16.json"))
TOTAL = plan["total"]
bed = music_bed(BPM, TOTAL, style=STYLE, energy=ENERGY)
sfx = np.zeros_like(bed)
for e in plan["events"]:
    i0 = int(e["t"] * SR)
    g = {"whoosh": sfx_whoosh, "glitch": sfx_glitch, "splice": sfx_splice,
         "thump": sfx_thump}[e["sfx"]](dur=0.35 if e["sfx"] == "thump" else 0.5)
    g = g / (np.abs(g).max() or 1) * 0.5
    i1 = min(len(bed), i0 + len(g))
    if i1 > i0:
        sfx[i0:i1] += np.stack([g[:i1 - i0], g[:i1 - i0]], axis=1)
mix = bed * 0.85 + sfx
write_wav(f"{WORK}/audio_mix_rebuilt.wav", mix)
subprocess.run(["ffmpeg", "-y", "-v", "error",
                "-i", f"{WORK}/audio_mix_rebuilt.wav",
                "-af", "acompressor=threshold=-12dB:ratio=4:attack=2:release=90,"
                       "loudnorm=I=-14:TP=-3.4:LRA=11,"
                       "alimiter=limit=0.7499:attack=1:release=80:level=false",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", f"{WORK}/ln_a.aac"], check=True)
def meas(p):
    r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", p, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[-1600:]
    import re
    I = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", tail)
    TP = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", tail)
    return (float(I.group(1)) if I else None, float(TP[-1]) if TP else None)
I, TP = meas(f"{WORK}/ln_a.aac")
gain = round(-14.0 - I, 2)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{WORK}/ln_a.aac", "-af", f"volume={gain}dB",
                "-c:a", "aac", "-b:a", "192k", f"{WORK}/ln_b.aac"], check=True)
I2, TP2 = meas(f"{WORK}/ln_b.aac")
if TP2 is not None and TP2 > -1.5:
    g2 = round((-1.9) - TP2, 2)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{WORK}/ln_b.aac", "-af", f"volume={g2}dB",
                    "-c:a", "aac", "-b:a", "192k", f"{WORK}/ln_c.aac"], check=True)
    I2, TP2 = meas(f"{WORK}/ln_c.aac")
    src = f"{WORK}/ln_c.aac"
else:
    src = f"{WORK}/ln_b.aac"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", FINAL, "-i", src, "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", FINAL + ".new.mp4"], check=True)
import os
os.replace(FINAL + ".new.mp4", FINAL)
log_p = f"{WORK}/render_log_9x16.json"
log = json.load(open(log_p))
log["loudnorm"] = {"integrated_lufs": I2, "true_peak_dbfs": TP2, "attempts": "rebuilt-bed chain"}
json.dump(log, open(log_p, "w"), indent=1)
print(f"{FINAL.split('/')[-1]}: I={I2} TP={TP2}")
