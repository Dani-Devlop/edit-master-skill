#!/usr/bin/env python3
"""T-1 v25 SHOWCASE AUDIO — IG1 beat-locked sound design over WELCOME bed (10s).
Cues read from /tmp/ems-work/p25/showcase_plan.json (renderer truth):
  sub-drop at ui_tap (structural point) | riser into counter | tape-stop into
  loop point | silence dropout 0.15s before DIES slam | stereo-panned whooshes
  at ui_tap + m2 entries | echo-throw hits on lyric keywords (dies/paid) |
  vinyl crackle + tape hiss bed (B&W world) | kick reinforcement (low thump).
Mix -> duck bed under cues -> write mix wav (2-pass loudnorm happens in
t1_assemble_v24.py)."""
import os, wave, json, math
import numpy as np

SR = 48000
DUR = 10.0
N = int(SR * DUR)
P25 = "/home/z/my-project/p25work"
WAV = "/home/z/my-project/p22work/assets/target_audio.wav"
PLAN = json.load(open(f"{P25}/showcase_plan.json"))
SC = {k: t for (t, k) in PLAN["scenes"]}
KICKS = PLAN["kicks"]
UI_TAP_T = SC["ui_tap"]; LIST_T = SC["listicle"]; COUNTER_T = SC["counter"]
M2_T = SC["m2_live"]; LOOP_T = SC["loop"]; DIES_T = SC["hook_duo"]

def read_wav(path):
    f = wave.open(path, "rb")
    sr = f.getframerate()
    ch = f.getnchannels()
    raw = f.readframes(f.getnframes())
    f.close()
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        x = x.reshape(-1, 2)
    else:
        x = np.stack([x, x], axis=1)
    return sr, x

sr_bed, bed = read_wav(WAV)
nb = min(N, len(bed))
mix = np.zeros((N, 2), dtype=np.float64)
mix[:nb] += bed[:nb] * 0.92

def add_at(mix, t, sig, gain=1.0, pan=0.0):
    i0 = int(t * SR)
    if i0 >= N or t < 0:
        return
    n = min(len(sig), N - i0)
    gl = gain * (1.0 - max(0.0, pan)) ** 0.5
    gr = gain * (1.0 - max(0.0, -pan)) ** 0.5
    if sig.ndim > 1:
        mix[i0:i0 + n, 0] += sig[:n, 0] * gl
        mix[i0:i0 + n, 1] += sig[:n, 1] * gr
    else:
        mix[i0:i0 + n, 0] += sig[:n] * gl
        mix[i0:i0 + n, 1] += sig[:n] * gr

def stereo(x, pan=0.0):
    return np.stack([x * (1.0 - max(0.0, pan)) ** 0.5,
                     x * (1.0 - max(0.0, -pan)) ** 0.5], axis=1)

def synth(kind, dur=0.5, rng_seed=None):
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(rng_seed if rng_seed is not None else hash(kind) % (2 ** 32))
    if kind == "whoosh":
        sweep = 300 + 2500 * (t / dur)
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = rng.standard_normal(n) * 0.4 * (np.sin(np.pi * t / dur) ** 2) + 0.15 * np.sin(phase)
    elif kind == "riser":
        sweep = 120 + 1800 * (t / dur) ** 2
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = 0.5 * np.sin(phase) * (t / dur) + 0.2 * rng.standard_normal(n) * (t / dur) ** 2
    elif kind == "sub":
        sweep = 80 * np.exp(-t * 3) + 28
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = 0.9 * np.sin(phase) * np.exp(-t * 5)
    elif kind == "impact":
        x = rng.standard_normal(n) * 0.5 * np.exp(-t * 18) + 0.7 * np.sin(2 * np.pi * 55 * t) * np.exp(-t * 7)
    elif kind == "tapestop":
        f = 420 * np.exp(-t * 6.5)
        phase = 2 * np.pi * np.cumsum(f) / SR
        x = np.sin(phase) * np.exp(-t * 3.2) * 0.7 + rng.standard_normal(n) * np.exp(-t * 4) * 0.2
    elif kind == "echobed":
        burst = rng.standard_normal(int(SR * 0.05)) * np.exp(-np.arange(int(SR * 0.05)) / SR * 60)
        x = np.zeros(n)
        echo_taps = [0.0, 0.12, 0.24, 0.38]
        for ei, et in enumerate(echo_taps):
            i0 = int(et * SR)
            g = 0.5 * (0.55 ** ei)
            if i0 < n:
                x[i0:i0 + len(burst)] += burst[:n - i0] * g
        x *= 0.8
    elif kind == "crackle":
        x = (rng.random(n) < 0.0007).astype(np.float64) * rng.uniform(-1, 1, n) * 0.5
        x += rng.standard_normal(n) * 0.006          # tape hiss bed
    else:  # tick/pop
        x = (rng.standard_normal(n) * 0.25 + np.sin(2 * np.pi * 900 * t)) * np.exp(-t * 22)
    return x

CUE_LOG = []
def cue(kind, t, dur=0.5, gain=0.5, pan=0.0, seed=None):
    x = synth(kind, dur=dur, rng_seed=seed)
    add_at(mix, t, stereo(x, pan), gain=gain)
    CUE_LOG.append({"kind": kind, "t": round(float(t), 3), "dur": dur,
                    "gain": gain, "pan": pan})

# ---- IG1 silence dropout 0.15s BEFORE the DIES slam ----
d0 = int((DIES_T - 0.15) * SR)
d1 = int(DIES_T * SR)
if d0 > 0:
    env = np.linspace(0, 1, d1 - d0)[:, None] ** 2
    mix[d0:d1] *= env
    CUE_LOG.append({"kind": "dropout0.15s", "t": round(DIES_T - 0.15, 3), "dur": 0.15,
                    "gain": 0.0, "pan": 0.0})
# second dropout before loop tape-stop
d0b = int((LOOP_T - 0.12) * SR)
d1b = int(LOOP_T * SR)
if d0b > 0:
    envb = np.linspace(1, 0, d1b - d0b)[:, None]
    mix[d0b:d1b] *= envb
    CUE_LOG.append({"kind": "fadeout-into-tapestop", "t": round(LOOP_T - 0.12, 3),
                    "dur": 0.12, "gain": 0.0, "pan": 0.0})

# ---- cues (all snapped to renderer scene times / onsets) ----
cue("impact", DIES_T, 0.4, 0.55, 0.0)                       # slam impact (post-dropout)
cue("sub", UI_TAP_T, 0.6, 0.7, 0.0)                         # structural sub-drop
cue("whoosh", UI_TAP_T - 0.10, 0.45, 0.4, -0.6)             # stereo pan L
cue("whoosh", M2_T - 0.10, 0.45, 0.4, 0.6)                  # stereo pan R
cue("riser", COUNTER_T - 0.8, 0.8, 0.42, 0.0)               # riser into counter
cue("impact", COUNTER_T, 0.4, 0.5, 0.0)
cue("echobed", DIES_T + 0.05, 0.6, 0.5, 0.25)               # echo-throw 'dies'
cue("echobed", LIST_T + 0.55, 0.6, 0.45, -0.25)             # echo-throw 'paid'
cue("tapestop", LOOP_T, 0.55, 0.6, 0.0)                     # tape-stop into loop
cue("pop", SC["hook_car"] + 0.02, 0.25, 0.35, 0.0)          # entry pop
cue("tick", UI_TAP_T + 0.42, 0.2, 0.4, 0.3)                 # cursor press tick
# kick reinforcement (low thump under detected kicks)
for k in KICKS:
    if k < DUR - 0.2:
        cue("sub", k, 0.18, 0.16, 0.0)
# vinyl crackle + tape hiss bed across the B&W world
cue("crackle", 0.0, DUR, 0.30, 0.0, seed=11)

# ---- gentle ducking of bed under cues (already implicit); soft clip guard ----
mix = np.clip(mix, -1.2, 1.2)

out = f"{P25}/showcase_mix.wav"
ww = wave.open(out, "wb")
ww.setnchannels(2)
ww.setsampwidth(2)
ww.setframerate(SR)
ww.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
ww.close()
json.dump({"cues": CUE_LOG, "sr": SR, "dur": DUR,
           "bed": "target_audio.wav (WELCOME, IDK ft. Eminem & J Dilla)"},
          open(f"{P25}/showcase_audio_cues.json", "w"), indent=1)
print("MIX DONE", out, "cues:", len(CUE_LOG), flush=True)
