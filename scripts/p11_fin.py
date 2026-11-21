#!/usr/bin/env python3
"""Phase 11.1 finishing stage (resumable): loudnorm 2-pass -> final.mp4, TG encode,
contact sheet, cleanup. Safe to re-run; skips completed steps."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

ROOT = "/home/z/my-project"
OUTD = f"{ROOT}/p11work/render11"
FPS = 30

def fin(vid):
    od = f"{OUTD}/{vid}"
    vo, wav = f"{od}/video_only.mp4", f"{od}/audio.wav"
    final, tg = f"{od}/final.mp4", f"{od}/final_tg.mp4"
    if not os.path.exists(vo) or not os.path.exists(wav):
        print("fin: missing video_only/audio", flush=True)
        return 3
    if not os.path.exists(final) or os.path.getsize(final) < 100000:
        # pass 1: measure
        r = subprocess.run(["ffmpeg", "-nostats", "-i", vo, "-i", wav, "-map", "0:v", "-map", "1:a",
                            "-c:v", "copy", "-c:a", "aac",
                            "-af", "acompressor=threshold=-16dB:ratio=3:attack=15:release=200,loudnorm=I=-14:TP=-1.7:LRA=11:print_format=json",
                            "-f", "null", "-"],
                           capture_output=True, text=True)
        import re
        m = None
        for cand in re.findall(r"\{[^{}]*\}", r.stderr, flags=re.S):
            if "measured_I" in cand or "input_i" in cand:
                try:
                    m = json.loads(cand)
                    break
                except Exception:
                    pass
        if not m:
            print("fin: loudnorm measure failed", r.stderr[-300:], flush=True)
            return 2
        g = lambda k1, k2: m.get(k1, m.get(k2))
        af = ("loudnorm=I=-14:TP=-1.7:LRA=11:"
              f"measured_I={g('measured_I','input_i')}:measured_LRA={g('measured_LRA','input_lra')}:"
              f"measured_TP={g('measured_TP','input_tp')}:measured_thresh={g('measured_thresh','input_thresh')}:"
              "print_format=summary")
        af2 = "acompressor=threshold=-16dB:ratio=3:attack=15:release=200," + af
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vo, "-i", wav, "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-af", af2, "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", final], check=True)
        print("fin: final.mp4 done", flush=True)
    if not os.path.exists(tg) or os.path.getsize(tg) < 100000:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-c:v", "libx264", "-preset", "fast",
                        "-crf", "31", "-vf", "scale=720:1280", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", tg],
                       check=True)
        print("fin: final_tg.mp4 done", os.path.getsize(tg), flush=True)
    sheet_path = f"{od}/contact_sheet.jpg"
    if not os.path.exists(sheet_path):
        sheet = Image.new("RGB", (5 * 216, 4 * 384), (18, 18, 18))
        for k, t in enumerate([0.5, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 21.5,
                               23.0, 24.0, 25.0, 25.4, 12.5, 17.5, 9.0, 19.0]):
            r = subprocess.run(["ffmpeg", "-v", "error", "-i", final, "-ss", str(t), "-frames:v", "1",
                                "-vf", "scale=216:384", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               capture_output=True)
            if len(r.stdout) >= 216 * 384 * 3:
                fr = np.frombuffer(r.stdout[:216 * 384 * 3], np.uint8).reshape(384, 216, 3)
                sheet.paste(Image.fromarray(fr), ((k % 5) * 216, (k // 5) * 384))
        sheet.save(sheet_path, quality=80)
        print("fin: contact sheet done", flush=True)
    for f in (vo, wav):
        if os.path.exists(f):
            os.remove(f)
    print("fin: OK", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(fin(sys.argv[1]))
