#!/usr/bin/env python3
"""T-1 v24 assemble: frames -> H.264 + audio mix -> 2-pass loudnorm (-14 LUFS,
TP<=-1.5) -> mux -> deliverable + sha256 + TG transcode.
Usage: t1_assemble_v24.py <frames_dir> <mix_wav> <out_final.mp4> <out_tg.mp4>"""
import sys, os, json, re, subprocess, hashlib

FRAMES = sys.argv[1]
MIX = sys.argv[2]
FINAL = sys.argv[3]
TG = sys.argv[4]
FPS = 30

os.makedirs(os.path.dirname(FINAL), exist_ok=True)

def sh(cmd, timeout=560):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        print("CMD-FAIL:", " ".join(cmd)[:200], file=sys.stderr)
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(1)
    return r

# 1) silent video from frames
sh(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", f"{FRAMES}/t_%05d.jpg",
    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
    "-an", "/tmp/ems-work/p24/t1_v24_silent.mp4"], timeout=580)
print("video pass done", flush=True)

# 2) loudnorm pass 1 (measure)
r = subprocess.run(["ffmpeg", "-i", MIX, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True, timeout=280)
tail = r.stderr[-2500:]
js = tail[tail.rfind("{"):tail.rfind("}") + 1]
m = json.loads(js)
meas = {k: m[k] for k in ("input_i", "input_tp", "input_lra", "input_thresh",
                          "output_i", "output_tp", "output_lra", "output_thresh")}
print("measure:", meas, flush=True)
af = ("loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={input_i}:measured_LRA={input_lra}:"
      "measured_TP={input_tp}:measured_thresh={input_thresh}:linear=true,"
      "alimiter=limit=0.84:level=false").format(**meas)
sh(["ffmpeg", "-y", "-v", "error", "-i", MIX, "-af", af,
    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "/tmp/ems-work/p24/t1_v24_audio.m4a"])

# 3) mux
sh(["ffmpeg", "-y", "-v", "error", "-i", "/tmp/ems-work/p24/t1_v24_silent.mp4",
    "-i", "/tmp/ems-work/p24/t1_v24_audio.m4a", "-c:v", "copy", "-c:a", "copy",
    "-movflags", "+faststart", FINAL])
print("final muxed", flush=True)

# 4) verify loudness on the FINAL file
r = subprocess.run(["ffmpeg", "-i", FINAL, "-af", "ebur128", "-f", "null", "-"],
                   capture_output=True, text=True, timeout=280)
tail = r.stderr[-3000:]
ilufs = re.findall(r"I:\s+(-?\d+\.\d+)\s+LUFS", tail)
tps = re.findall(r"Peak:\s+(-?\d+\.\d+)\s+dBFS", tail)
iluf = float(ilufs[-1]) if ilufs else None
tp = float(tps[-1]) if tps else None
print(f"FINAL LOUDNESS: I={iluf} LUFS  TP={tp} dBFS", flush=True)
ok = iluf is not None and abs(iluf + 14) <= 0.5 and tp is not None and tp <= -1.5
print("LOUDNESS-PASS" if ok else "LOUDNESS-FAIL", flush=True)

# 5) TG transcode (<= 45 MB, audio copy)
sh(["ffmpeg", "-y", "-v", "error", "-i", FINAL,
    "-c:v", "libx264", "-preset", "medium", "-b:v", "5000k", "-maxrate", "6000k",
    "-bufsize", "9000k", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", TG])
print("tg transcode done", flush=True)

# 6) sha256 manifest
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
man = {"final": {"path": FINAL, "sha256": sha256(FINAL), "bytes": os.path.getsize(FINAL),
                 "lufs": iluf, "tp": tp},
       "tg": {"path": TG, "sha256": sha256(TG), "bytes": os.path.getsize(TG)}}
json.dump(man, open("/tmp/ems-work/p24/t1_v24_manifest.json", "w"), indent=1)
print("MANIFEST:", json.dumps(man["final"]), flush=True)
