#!/usr/bin/env python3
"""T-1 audio: WELCOME bed (full source clip 27.9s) + synth SFX cue-sheet per entrance/transition
+ duck -18dB + 2-pass loudnorm -14 LUFS TP -1.5 (via ffmpeg on final mux)."""
import os, wave, json
import numpy as np

SR = 48000
SCRATCH = "/tmp/my-project/p21work/scratch"
WAV = f"{SCRATCH}/target_audio.wav"
DUR = 27.9
N = int(SR * DUR)

def synth_sfx(kind, dur=0.5):
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(hash(kind) % (2**32))
    if kind == "pop":
        e = np.exp(-t * 22)
        x = (rng.standard_normal(n) * 0.25 + np.sin(2 * np.pi * 900 * t)) * e
    elif kind == "whoosh":
        sweep = 300 + 2500 * (t / dur)
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = rng.standard_normal(n) * 0.4 * (np.sin(np.pi * t / dur) ** 2) + 0.15 * np.sin(phase)
    elif kind == "tick":
        e = np.exp(-t * 60)
        x = np.sign(np.sin(2 * np.pi * 2200 * t)) * 0.22 * e
    elif kind == "riser":
        sweep = 120 + 1800 * (t / dur) ** 2
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = 0.5 * np.sin(phase) * (t / dur)
    elif kind == "sub":
        sweep = 80 * np.exp(-t * 3) + 28
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = 0.9 * np.sin(phase) * np.exp(-t * 5)
    elif kind == "impact":
        x = rng.standard_normal(n) * 0.5 * np.exp(-t * 18) + 0.7 * np.sin(2 * np.pi * 55 * t) * np.exp(-t * 7)
    else:
        x = np.zeros(n)
    return x.astype(np.float32)

SCENE_SFX = [
    (0.00, "pop", 0.5, "hook entrance"),
    (0.05, "riser", 1.2, "hook tension"),
    (3.30, "whoosh", 0.6, "whip transition"),
    (6.20, "tick", 0.3, "listicle reveal"),
    (9.00, "impact", 0.8, "counter slam"),
    (11.90, "whoosh", 0.7, "zoom-through"),
    (14.80, "pop", 0.4, "polaroid slide-in"),
    (17.60, "sub", 1.0, "invert bite drop"),
    (20.40, "tick", 0.3, "callout draw"),
    (23.20, "impact", 0.9, "M1 3D slam"),
    (23.30, "sub", 1.0, "M1 sub drop"),
    (25.60, "pop", 0.4, "end card settle"),
]
CUE = []
f = wave.open(WAV, "rb")
sr_w = f.getframerate()
raw = f.readframes(int(sr_w * (DUR + 0.5)))
f.close()
bed = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
if bed.ndim > 1:
    bed = bed.mean(axis=1)
# resample source (16k) to SR (48k)
n_src = len(bed)
bed = np.interp(np.linspace(0, n_src - 1, int(n_src * SR / sr_w)), np.arange(n_src), bed)
if len(bed) < N:
    bed = np.pad(bed, (0, N - len(bed)))
bed = bed[:N]
bed /= max(1.0, np.abs(bed).max())
bed *= 0.42  # the MV song IS the content: medium bed level
mix = bed.copy()
duck = np.ones(N, dtype=np.float32)
for (ts, kind, dur, why) in SCENE_SFX:
    i0, i1 = max(0, int((ts - 0.05) * SR)), min(N, int((ts + 0.45) * SR))
    duck[i0:i1] *= 10 ** (-18 / 20)
    x = synth_sfx(kind, dur) * 0.30
    j0 = int(ts * SR)
    j1 = min(N, j0 + len(x))
    seg = x[:j1 - j0]
    mix[j0:j1] += seg
    CUE.append({"t": round(ts, 2), "sfx": kind, "dur": dur, "maps_to": why})
mix *= duck
mix /= max(1.0, np.abs(mix).max())
mix *= 0.92
fade = int(0.5 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
with wave.open(f"{SCRATCH}/t1_mix.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((mix * 32767).astype(np.int16))
json.dump({"cue_sheet": CUE,
           "music": {"track": "WELCOME — IDK feat. Eminem & J Dilla",
                     "source": "user-supplied clip (27.91s), full-clip coverage window",
                     "bed_gain": "medium 0.42", "duck_db": -18},
           "loudnorm": "2-pass -14 LUFS TP -1.5 (ffmpeg)"},
          open(f"{SCRATCH}/t1_cuesheet.json", "w"), indent=1)
print("t1 mix + cue sheet done")
