#!/usr/bin/env python3
"""Beat map for sources with/without audio. Uses ffmpeg->wav decode (no audioread).
Silent source => honest 'generated bed' plan. Usage: p14_beatmap.py <raw> <work> [bpm_for_generated]
"""
import subprocess, json, sys, os, re

RAW, WORK = sys.argv[1], sys.argv[2]
GEN_BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
wav = os.path.join(WORK, "audio_44k.wav")

# does the file have an audio stream?
p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                    "stream=codec_name,duration", "-of", "json", RAW], capture_output=True, text=True)
astreams = json.loads(p.stdout or "{}").get("streams", [])
if not astreams:
    json.dump({"method": "no-audio-source", "silent": True, "tempo_bpm": GEN_BPM,
               "n_beats": 0, "beats": [], "n_onsets": 0, "onsets": [], "strong_onsets": [],
               "note": "source has NO audio stream; edit will use generated royalty-free bed at "
                       f"{GEN_BPM} BPM; cuts align to generated bed grid (M2 decision logged)"},
              open(f"{WORK}/beatmap.json", "w"), indent=1)
    print("BEATMAP: NO AUDIO SOURCE -> generated bed plan @", GEN_BPM, "BPM")
    sys.exit(0)

subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", RAW, "-ar", "44100", "-ac", "1", "-vn", wav], check=True)
import numpy as np, librosa
y, sr = librosa.load(wav, sr=44100, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time", trim=False)
beat_times = [round(float(b), 3) for b in beats.tolist()]
onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
on_frames = librosa.util.peak_pick(onset_env, pre_max=6, post_max=6, pre_avg=12, post_avg=12,
                                   delta=0.9, wait=10)
on_times = librosa.frames_to_time(on_frames, sr=sr, hop_length=512).tolist()
strengths = onset_env[on_frames]
strong = [{"t": round(float(t), 3), "s": round(float(s), 2)} for t, s in zip(on_times, strengths)
          if s > np.percentile(strengths, 55)]
bm = {"method": "librosa.beat.beat_track + onset_strength peak_pick (ffmpeg->wav decode)",
      "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 2),
      "n_beats": len(beat_times), "beats": beat_times,
      "n_onsets": len(on_times), "onsets": [round(float(o), 3) for o in on_times],
      "strong_onsets": strong, "silent": False}
json.dump(bm, open(f"{WORK}/beatmap.json", "w"), indent=1)
print(f"BEATMAP: tempo={bm['tempo_bpm']} beats={len(beat_times)} onsets={len(on_times)} strong={len(strong)}")
