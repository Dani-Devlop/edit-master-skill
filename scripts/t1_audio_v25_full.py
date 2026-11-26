#!/usr/bin/env python3
"""T-1 v24 AUDIO — IG1 beat-locked sound design over WELCOME bed (27.9s).
Cues read from /tmp/ems-work/p24/t1_v24_plan.json (renderer truth):
  sub-drop at structural scenes | riser into m1/pop | tape-stop into loop point |
  silence dropout 0.15s before slams | stereo-panned whooshes at whip/ui_tap/
  zoomthrough | echo-throw hits on lyric keywords (dies/homicide/paid/lemonade) |
  vinyl crackle + tape hiss bed (B&W world) | kick reinforcement (low thump).
Mix -> duck -> 2-pass loudnorm -14 LUFS TP<=-1.5 -> mux with frames."""
import os, wave, json, math
import numpy as np

SR = 48000
DUR = 27.9
N = int(SR * DUR)
P24 = "/home/z/my-project/p25work"
WAV = "/home/z/my-project/p22work/assets/target_audio.wav"
PLAN = json.load(open(f"{P24}/t1_v25_plan.json"))
SC = {k: t for (t, k) in PLAN["scenes"]}
KICKS = PLAN["kicks"]

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

def add_at(mix, t, sig, gain=1.0, pan=0.0):
    """mix stereo sig into master at t; pan -1 (L) .. 1 (R)"""
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
    return np.stack([x * (1.0 - max(0.0, pan)) ** 0.5, x * (1.0 - max(0.0, -pan)) ** 0.5], axis=1)

def synth(kind, dur=0.5, rng_seed=None):
    n = int(SR * dur)
    t = np.arange(n) / SR
    rng = np.random.default_rng(rng_seed if rng_seed is not None else hash(kind) % (2 ** 32))
    if kind == "pop":
        x = (rng.standard_normal(n) * 0.25 + np.sin(2 * np.pi * 900 * t)) * np.exp(-t * 22)
    elif kind == "whoosh":  # bandpass-swept noise
        sweep = 300 + 2500 * (t / dur)
        phase = 2 * np.pi * np.cumsum(sweep) / SR
        x = rng.standard_normal(n) * 0.4 * (np.sin(np.pi * t / dur) ** 2) + 0.15 * np.sin(phase)
    elif kind == "tick":
        x = np.sign(np.sin(2 * np.pi * 2200 * t)) * 0.22 * np.exp(-t * 60)
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
    elif kind == "tapestop":  # pitch-down stall into loop point
        f = 420 * np.exp(-t * 6.5)
        phase = 2 * np.pi * np.cumsum(f) / SR
        x = np.sin(phase) * np.exp(-t * 3.2) * 0.7 + rng.standard_normal(n) * np.exp(-t * 4) * 0.2
    elif kind == "echobed":  # echo-throw keyword hit (noise burst + feedback echo)
        burst = rng.standard_normal(int(SR * 0.05)) * np.exp(-np.arange(int(SR * 0.05)) / SR * 60)
        x = np.zeros(n)
        for k in range(4):
            i = int(k * 0.11 * SR)
            g = 0.5 ** k
            if i + len(burst) < n:
                x[i:i + len(burst)] += burst * g
        x += 0.25 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 8)
    elif kind == "thump":
        x = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 14) * 0.5
    else:
        x = np.zeros(n)
    return x.astype(np.float32)

def crackle_bed(n, rng_seed=17):
    """vinyl crackle + tape hiss (B&W world bed, IG1)"""
    rng = np.random.default_rng(rng_seed)
    x = rng.standard_normal(n) * 0.012                      # tape hiss
    k = rng.random(n) < 0.0016                              # crackle impulses
    idx = np.where(k)[0]
    x[idx] += rng.standard_normal(len(idx)) * 0.16
    # lowpass the crackle slightly (surface noise feel)
    spec = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    spec[fr > 6000] *= 0.4
    return np.fft.irfft(spec, n).astype(np.float32)

def duck_envelope(cue_ts, n, depth=0.45, pre=0.03, post=0.30):
    """bed duck under SFX hits"""
    env = np.ones(n, dtype=np.float32)
    for t in cue_ts:
        i0 = max(0, int((t - pre) * SR))
        i1 = min(n, int((t + post) * SR))
        if i1 > i0:
            env[i0:i1] = np.minimum(env[i0:i1], depth)
    # smooth 20ms
    k = np.ones(int(0.02 * SR)) / int(0.02 * SR)
    return np.convolve(env, k, mode="same")

def dropout_envelope(drops, n):
    """silence dropout 0.15s before slams (IG1)"""
    env = np.ones(n, dtype=np.float32)
    for t in drops:
        i0 = max(0, int((t - 0.15) * SR))
        i1 = min(n, int(t * SR))
        if i1 > i0:
            env[i0:i1] *= np.linspace(1.0, 0.02, i1 - i0)
    return env

def main():
    sr, bed = read_wav(WAV)
    assert sr == SR
    if len(bed) < N:
        bed = np.vstack([bed, np.zeros((N - len(bed), 2), dtype=np.float32)])
    bed = bed[:N]

    mix = bed.copy()

    # IG1 vinyl crackle + tape hiss bed
    mix += stereo(crackle_bed(N), 0.0) * 0.9

    cues = []
    # structural sub-drops
    for k in ("counter", "pop", "m1"):
        add_at(mix, SC[k], stereo(synth("sub", 0.9), 0.0), 0.55)
        cues.append((SC[k], "sub", f"structural {k}"))
    # risers into pop + m1
    for k, back in (("pop", 0.5), ("m1", 0.5)):
        add_at(mix, SC[k] - back, stereo(synth("riser", back), 0.0), 0.42)
        cues.append((round(SC[k] - back, 2), "riser", f"into {k}"))
    # tape-stop into loop point (IG3)
    add_at(mix, SC["loop"] - 0.30, stereo(synth("tapestop", 0.55), 0.0), 0.60)
    cues.append((round(SC["loop"] - 0.30, 2), "tapestop", "into seamless loop"))
    # stereo-panned whooshes (IG10/IG2 moments)
    add_at(mix, SC["ui_tap"], stereo(synth("whoosh", 0.45), 0.7), 0.5)
    cues.append((SC["ui_tap"], "whoosh R->L", "ui_tap cursor"))
    add_at(mix, SC["ghost"], stereo(synth("whoosh", 0.40), -0.7), 0.5)
    cues.append((SC["ghost"], "whoosh L->R", "whip into ghost"))
    add_at(mix, SC["zoomthrough"], stereo(synth("whoosh", 0.45), -0.6), 0.5)
    cues.append((SC["zoomthrough"], "whoosh L->R", "F2 zoom-through"))
    # slam impacts + 0.15s silence dropouts before them
    slams = [SC["callout"] + 0.10, SC["m1"] + 0.05, SC["pop"] + 0.35]
    for t in slams:
        add_at(mix, t, stereo(synth("impact", 0.6), 0.0), 0.72)
        cues.append((round(t, 2), "impact", "slam"))
    # IG2 UI beats
    add_at(mix, SC["ui_tap"] + 0.42, stereo(synth("pop", 0.30), 0.3), 0.5)
    cues.append((round(SC["ui_tap"] + 0.42, 2), "pop", "cursor tap"))
    add_at(mix, SC["counter"] + 0.25, stereo(synth("tick", 0.25), -0.2), 0.35)
    cues.append((round(SC["counter"] + 0.25, 2), "tick", "notification banner"))
    add_at(mix, SC["pop"] + 0.35, stereo(synth("pop", 0.3), 0.25), 0.4)
    cues.append((round(SC["pop"] + 0.35, 2), "pop", "heart burst"))
    # echo-throw on lyric keywords (IG1)
    kw_times = {"dies": 2.90, "homicide": 6.55, "paid": 15.60, "lemonade": 21.20}
    for kw, t in kw_times.items():
        add_at(mix, t, stereo(synth("echobed", 0.55), 0.25), 0.42)
        cues.append((t, "echobed", f"lyric keyword: {kw}"))
    # kick reinforcement (IG1: kick-synced pulse audible)
    for kt in KICKS:
        if kt < DUR - 0.2:
            add_at(mix, kt, stereo(synth("thump", 0.28), 0.0), 0.22)

    # envelopes: dropout before slams + duck under cues
    mix *= dropout_envelope(slams, N)[:, None]
    mix *= duck_envelope([c[0] for c in cues], N)[:, None]

    # soft clip guard
    mix = np.tanh(mix * 1.1) / 1.1

    out = np.clip(mix * 32767 * 0.85, -32767, 32767).astype(np.int16)
    wf = wave.open(f"{P24}/t1_v24_mix.wav", "wb")
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(out.tobytes())
    wf.close()
    json.dump({"cues": [{"t": c[0], "sfx": c[1], "maps_to": c[2]} for c in cues],
               "dropouts_before_slams": slams, "kick_reinforced": len(KICKS),
               "crackle": True, "dur": DUR},
              open(f"{P24}/t1_v24_cuesheet.json", "w"), indent=1)
    print("MIX DONE:", len(cues), "cues |", len(KICKS), "kicks reinforced")

if __name__ == "__main__":
    main()
