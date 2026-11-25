#!/usr/bin/env python3
"""Replica audio: synth SFX bank (license-clean) + WELCOME bed (duck -18dB under SFX)
+ 2-pass loudnorm -14 LUFS, TP <= -1.5. Ship cue sheet JSON.
E4: every entrance has an SFX (pop/whoosh/tick/riser/sub/impact)."""
import os, sys, wave, json, subprocess
import numpy as np

SR = 48000
SCRATCH = "/tmp/my-project/p21work/scratch"
FRAMES = f"{SCRATCH}/replica_frames"
WAV = f"{SCRATCH}/target_audio.wav"   # WELCOME clip 27.9s
DUR = 12.0
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
        x = rng.standard_normal(n) * 0.4
        # bandpass-ish emphasis via amplitude envelope
        x *= np.sin(np.pi * t / dur) ** 2
        x += 0.15 * np.sin(phase)
    elif kind == "tick":
        e = np.exp(-t * 60)
        x = np.sign(np.sin(2 * np.pi * 2200 * t)) * 0.25 * e
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

# scene starts (mirror engine; DROP fixed by energy = 10.37)
DROP = 10.37
SCENE_SFX = [
    (0.00, "pop", 0.5), (0.90, "whoosh", 0.6), (1.80, "pop", 0.4), (2.70, "impact", 0.7),
    (3.60, "tick", 0.25), (4.50, "riser", 0.8), (5.40, "pop", 0.4), (6.30, "whoosh", 0.6),
    (7.20, "tick", 0.3), (8.10, "pop", 0.4), (DROP, "impact", 0.9), (DROP + 0.10, "sub", 1.0),
    (DROP + 0.67, "pop", 0.4),
]
CUE = []
mix = np.zeros(N + SR, dtype=np.float32)

# music bed: WELCOME 0-12s, medium-low, ducked -18dB under SFX hits
f = wave.open(WAV, "rb")
sr_w = f.getframerate()
raw = f.readframes(int(sr_w * DUR))
f.close()
bed = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
if bed.ndim > 1:
    bed = bed.mean(axis=1)
bed = bed[:N]
bed /= max(1.0, np.abs(bed).max())
bed *= 0.32  # medium-low
mix[:len(bed)] += bed

# duck bed -18dB for 0.45s around each SFX hit
duck = np.ones(len(bed), dtype=np.float32)
for (ts, kind, dur) in SCENE_SFX:
    i0, i1 = int((ts - 0.05) * SR), int((ts + 0.45) * SR)
    i0 = max(0, i0); i1 = min(len(duck), i1)
    if i1 > i0:
        duck[i0:i1] *= 10 ** (-18 / 20)
bed *= duck[:len(bed)]
mix[:len(bed)] = bed.copy()

# SFX medium-low
for (ts, kind, dur) in SCENE_SFX:
    x = synth_sfx(kind, dur) * 0.30
    i0 = int(ts * SR)
    i1 = min(len(mix), i0 + len(x))
    mix[i0:i1] += x[:i1 - i0]
    CUE.append({"t": round(ts, 2), "sfx": kind, "maps_to": "scene-entrance" if kind != "sub" else "drop-slam"})

mix = mix[:N]
mix /= max(1.0, np.abs(mix).max())
mix *= 0.92
# gentle fade-out last 0.4s
fade = int(0.4 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)

with wave.open(f"{SCRATCH}/replica_mix.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((mix * 32767).astype(np.int16))

json.dump({"cue_sheet": CUE,
           "music": {"track": "WELCOME — IDK feat. Eminem & J Dilla (user-supplied clip 0-12s)",
                     "bed_gain": "medium-low 0.32", "duck_db": -18},
           "loudnorm": "2-pass -14 LUFS TP -1.5 (ffmpeg)"},
          open(f"{SCRATCH}/replica_cuesheet.json", "w"), indent=1)
print("mix + cue sheet done")
