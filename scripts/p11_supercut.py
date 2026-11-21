#!/usr/bin/env python3
"""Phase 11.1 SUPERCUT v4 (fast build): ffmpeg segment extraction + flash bridges +
end card + concat + two-pass loudnorm. Sources: only PASS-gated finals (D2)."""
import json, subprocess, os, sys
import numpy as np

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/p11work/render11/supercut_v4"
os.makedirs(OUT, exist_ok=True)
SEG = 1.70
vids = ["travel_1","cars_2","food_1","tech_1","podcast_1","education_1","fitness_1",
        "talkinghead_1","product_2","branding_1","racing_1","city_1","fashion_1",
        "mindset_1","music_1","nature_1"]

for v in vids:
    d = json.load(open(f"{ROOT}/p11work/render11/{v}/gate.json"))
    assert d["overall_pass"], f"{v} not gated PASS"
print("all sources gated PASS (D2)", flush=True)

# 1) per-video segment (video only)
for i, v in enumerate(vids):
    src = f"{ROOT}/p11work/render11/{v}/final.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.35", "-i", src, "-t", str(SEG),
                    "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                    "-vf", "scale=1080:1920", f"{OUT}/seg_{i:02d}.mp4"], check=True)
print("segments ok", flush=True)

# 2) flash bridge (0.1s, 3 frames)
import cv2
base = np.full((1920, 1080, 3), (30, 30, 34), np.uint8)
proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                         "-s", "1080x1920", "-r", "30", "-i", "-",
                         "-c:v", "libx264", "-preset", "fast", "-crf", "19", f"{OUT}/bridge.mp4"],
                        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for k, mult in enumerate((3.5, 1.8, 0.5)):
    f = np.clip(base.astype(np.float32) * mult, 0, 255).astype(np.uint8)
    proc.stdin.write(np.ascontiguousarray(f))
proc.stdin.close(); proc.wait()
print("bridge ok", flush=True)

# 3) end card 2.8s (alternating for subtle flicker)
from PIL import Image, ImageDraw, ImageFont
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(sz): return ImageFont.truetype(FB, sz)
end = Image.new("RGB", (1080, 1920), (238, 238, 241))
d = ImageDraw.Draw(end)
for li, line in enumerate(["EDIT MASTER SKILL", "Test Edit Skill",
                           "github.com/Dani-Devlop/edit-master-skill"]):
    fnt = font(76 if li < 2 else 54)
    bb = d.textbbox((0, 0), line, font=fnt)
    d.text(((1080 - (bb[2] - bb[0])) // 2, 600 + li * 190), line, font=fnt,
           fill=(24, 24, 26) if li < 2 else (120, 40, 60))
d.rounded_rectangle([60, 60, 1020, 1860], radius=40, outline=(250, 112, 142), width=22)
d.text((340, 1420), "loop: PAVE IT", font=font(64), fill=(24, 24, 26))
endA = np.array(end)
endB = np.clip(endA.astype(np.float32) * 0.92, 0, 255).astype(np.uint8)
proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                         "-s", "1080x1920", "-r", "30", "-i", "-",
                         "-c:v", "libx264", "-preset", "fast", "-crf", "19", f"{OUT}/endcard.mp4"],
                        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
for k in range(84):
    f = endA if k % 2 == 0 else endB
    proc.stdin.write(np.ascontiguousarray(f))
proc.stdin.close(); proc.wait()
print("endcard ok", flush=True)

# 4) concat video
lines = []
for i in range(16):
    lines.append(f"file 'seg_{i:02d}.mp4'")
    if i < 15:
        lines.append("file 'bridge.mp4'")
lines.append("file 'endcard.mp4'")
open(f"{OUT}/concat.txt", "w").write("\n".join(lines))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                "-i", f"{OUT}/concat.txt", "-c:v", "libx264", "-preset", "fast",
                "-crf", "19", f"{OUT}/sc_video.mp4"], check=True, cwd=OUT)
print("video concat ok", flush=True)

# 5) audio: per-seg source audio + silent bridges + endcard tone
import soundfile as sf
sr = 48000
sf.write(f"{OUT}/bridge_silent.wav", np.zeros(int(0.1 * sr), np.float32), sr)
t = np.arange(int(2.8 * sr)) / sr
sf.write(f"{OUT}/endcard.wav",
         (0.15 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), sr)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/bridge_silent.wav", "-c:a", "aac",
                "-b:a", "160k", f"{OUT}/bridge_silent.aac"], check=True, cwd=OUT)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/endcard.wav", "-c:a", "aac",
                "-b:a", "160k", f"{OUT}/endcard.aac"], check=True, cwd=OUT)
alines = []
for i, v in enumerate(vids):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.35", "-t", str(SEG), "-i",
                    f"{ROOT}/p11work/render11/{v}/final.mp4", "-vn", "-c:a", "aac",
                    "-b:a", "160k", f"{OUT}/a_{i:02d}.aac"], check=True)
    alines.append(f"file 'a_{i:02d}.aac'")
    if i < 15:
        alines.append("file 'bridge_silent.aac'")
alines.append("file 'endcard.aac'")
open(f"{OUT}/alist.txt", "w").write("\n".join(alines))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/alist.txt",
                "-c:a", "aac", "-b:a", "192k", f"{OUT}/sc_audio.aac"], check=True, cwd=OUT)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/sc_video.mp4", "-i", f"{OUT}/sc_audio.aac",
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
                "-movflags", "+faststart", f"{OUT}/supercut_v4_raw.mp4"], check=True, cwd=OUT)
print("mux ok", flush=True)

# 6) two-pass loudnorm -> final
r = subprocess.run(["ffmpeg", "-nostats", "-i", f"{OUT}/supercut_v4_raw.mp4",
                    "-af", "loudnorm=I=-14:TP=-1.7:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
m = None
for cand in r.stderr.split("{"):
    if '"input_i"' in cand or '"measured_I"' in cand:
        try:
            m = json.loads("{" + cand.split("}")[0] + "}")
            break
        except Exception:
            pass
assert m, "loudnorm measure failed"
g = lambda a, b: m.get(a, m.get(b))
af = ("loudnorm=I=-14:TP=-1.7:LRA=11:"
      f"measured_I={g('measured_I','input_i')}:measured_LRA={g('measured_LRA','input_lra')}:"
      f"measured_TP={g('measured_TP','input_tp')}:measured_thresh={g('measured_thresh','input_thresh')}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/supercut_v4_raw.mp4", "-af", af,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                f"{OUT}/supercut_v4.mp4"], check=True)
print("SUPERCUT v4 DONE", flush=True)
