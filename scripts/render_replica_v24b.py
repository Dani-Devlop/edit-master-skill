#!/usr/bin/env python3
"""REPLICA v24b — Phase 24 round-2: r21 WINNING METHOD (documented task.md 22.11)
decoded reel quadrant crops = footage layer R0 (live re-decode per frame at the
1.2913 story-stretch), all timing/entrance/badge/karaoke/camera CODE-DRIVEN, plus
IG additions: IG1 onset-snapped states + kick-synced ±3% pulse, IG2 cursor-tap
beat, IG4 persp3d M1 slam (bpy unavailable — honest substitute), IG5 entrance
wobble idle motion. No film-texture overlays here (replica = register fidelity).
12s @30fps 1080x1920. TEMP /tmp/ems-work/p22/replica_frames_b."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/scripts")
import renderlib as R
from renderlib import VOLT, INK
import ig24kit as IG
IG.bind_renderlib(R)
import v22kit as K
from v22kit import (W, H, FPS, load_persons, paste_person, canvas, cam_apply,
                    sticker_confetti, sticker_starburst, bracket_corners,
                    scene_label, pill_statement, lyric_at, grid_layout,
                    sticker_badge_A)

TGT = "/home/z/my-project/upload/VID_20261121_000716_199.mp4"
DUR = 12.0
N = int(FPS * DUR)
FRAMES = "/tmp/ems-work/p22/replica_frames_b"
OUTDIR = "/tmp/ems-work/p24"
os.makedirs(FRAMES, exist_ok=True)

ONSETS, LIB_BEATS, KICKS, TEMPO, OENG = IG.onset_grid(f"{K.ASSETS}/target_audio.wav", DUR + 0.5)
SNAP_LOG = []
def snap_state(t):
    st, d = IG.snap(t, ONSETS, 0.06)
    SNAP_LOG.append({"plan": round(float(t), 3), "snapped": st, "delta": d})
    return st
DROP = snap_state(9.42)
M1_START = snap_state(DROP - 0.35)
print(f"onsets[{OENG}]: {len(ONSETS)} | kicks {len(KICKS)} | DROP {DROP}", flush=True)

STATES = [
    (0.00, "grid"), (0.51, "grid"), (1.36, "grid"), (2.21, "grid"),
    (3.06, "grid"), (3.91, "grid"), (4.76, "grid"), (5.61, "grid"),
    (6.46, "grid"), (7.31, "grid"), (8.16, "grid"),
    (M1_START, "m1"), (snap_state(M1_START + 1.05), "endcard"),
]
STATES = [(0.0 if i == 0 else snap_state(t), k) for i, (t, k) in enumerate(STATES)]

def state_at(t):
    idx = 0
    for i, s in enumerate(STATES):
        if t >= s[0] - 1e-6:
            idx = i
    return idx

BOXES = grid_layout()
TGT_DUR = 6.893
GRID_END = 8.9
STRETCH = GRID_END / TGT_DUR      # 1.2913 story stretch (r17 measured)

_QUAD = {}
def target_quads(t_tgt):
    """decode target frame -> 4 quadrant crops (R0 footage layer, live)"""
    key = round(min(max(0.02, t_tgt), 6.70), 2)   # clamp: target ends 6.893s
    if key in _QUAD:
        return _QUAD[key]
    png = f"{FRAMES}/../tgt_dec_{key}.png"
    if not os.path.exists(png):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(max(0.02, key)),
                        "-i", TGT, "-frames:v", "1", "-vf", "scale=1080:1920", png],
                       check=True)
    img = Image.open(png).convert("RGB")
    mq_x, mq_y = img.width // 2, img.height // 2
    quads = [img.crop((0, 0, mq_x, mq_y)), img.crop((mq_x, 0, img.width, mq_y)),
             img.crop((0, mq_y, mq_x, img.height)), img.crop((mq_x, mq_y, img.width, img.height))]
    if len(_QUAD) > 140:
        _QUAD.clear()
    _QUAD[key] = quads
    return quads

def eob(t, t0, dur=0.24):
    if t < t0:
        return 0.0
    p = min(1.0, (t - t0) / dur)
    s = 1.70158 * 0.66
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2

SFX_CUES = []
def log_sfx(t, kind, maps_to):
    SFX_CUES.append({"t": round(float(t), 3), "sfx": kind, "maps_to": maps_to})

engine_log = []
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("--start", type=int, default=0)
_ap.add_argument("--end", type=int, default=N - 1)
_args = _ap.parse_args()
F0, F1 = _args.start, min(_args.end, N - 1)

for frame in range(F0, F1 + 1):
    t = frame / FPS
    si = state_at(t)
    s0, mode = STATES[si]

    if mode == "grid":
        quads = target_quads(t / STRETCH)   # R0 live footage layer (r21 method)
        img = Image.new("RGBA", (W, H), (5, 5, 7, 255))
        eases = [eob(t, float(s0) + j * 0.05, 0.26) for j in range(4)]
        for i, (box, quad) in enumerate(zip(BOXES, quads)):
            x0, y0, x1, y1 = box
            pw, ph = x1 - x0, y1 - y0
            sub = quad.resize((pw, ph), Image.LANCZOS).convert("RGBA")
            ee = max(0.0, eases[i])
            sc = 0.90 + 0.14 * min(1.05, ee)
            rot = 1.4 * math.sin(t * 1.5 + i * 1.7)   # IG5 idle wobble
            if sc < 0.999 or abs(rot) > 0.05:
                nw, nh = max(2, int(pw * sc)), max(2, int(ph * sc))
                sub2 = sub.resize((nw, nh), Image.BILINEAR)
                if abs(rot) > 0.05:
                    sub2 = sub2.rotate(rot, expand=False, resample=Image.BICUBIC)
                sub = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
                sub.alpha_composite(sub2, ((pw - nw) // 2, (ph - nh) // 2))
            slide = int(max(0.0, 1.0 - ee) * 36 * (1 if i % 2 == 0 else -1))
            img.alpha_composite(sub, (x0, y0 + slide))
            d = ImageDraw.Draw(img, "RGBA")
            d.rounded_rectangle([x0, y0 + slide, x1, y1 + slide], radius=8,
                                outline=(240, 240, 240, 40), width=2)
        sticker_badge_A(ImageDraw.Draw(img, "RGBA"),
                        int((BOXES[0][2] + BOXES[1][0]) / 2),
                        int((BOXES[0][3] + BOXES[2][1]) / 2),
                        int(126 * max(0.25, eases[0])))
        words, active = lyric_at(t)
        if words:
            chip = Image.new("RGBA", (W, 118), (0, 0, 0, 0))
            pill_statement(chip, 16, words, active, size=40)
            img.alpha_composite(chip, (0, int(H * 0.908) - 4))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, int(H * 0.908), W, int(H * 0.908) + 4], fill=VOLT + (170,))
        # IG2 cursor-tap beat at each state entrance (tap triggers next grid)
        if si >= 1 and 0.0 <= (t - float(s0)) <= 0.50:
            IG.cursor_tap(img, int(W * 0.72), int(H * 0.50), t, float(s0), dur=0.5)
        img, z, dx, dy = cam_apply(img, t, float(s0), punch=0.05, drift=11)
        bs = (1.0 + 0.010 * math.sin(t * 2.8)) * IG.kick_pulse(t, KICKS, 0.03)  # IG1
        zw, zh = int(W / bs), int(H / bs)
        img = img.crop(((W - zw) // 2, (H - zh) // 2, (W - zw) // 2 + zw, (H - zh) // 2 + zh)) \
                  .resize((W, H), Image.BILINEAR)
        if frame <= int(float(s0) * FPS) + 1:
            log_sfx(float(s0), "pop" if si % 2 else "tick", f"grid state {si}")
        engine, tag = "pil+r0-footage", f"grid state {si} (r21 method)"
    elif mode == "m1":
        img = canvas("paper", ghost="WELCOME")
        d = ImageDraw.Draw(img, "RGBA")
        sticker_starburst(d, W / 2, int(H * 0.20), 130, t=t)
        bracket_corners(d, 140, int(H * 0.16), W - 140, int(H * 0.64), color=INK, L=46, w=7)
        _tw190 = R.montserrat(190, 900).getlength("WELCOME")
        _ms = max(100, min(190, int(190 * 660.0 / max(1, _tw190))))
        engine = IG.m1_type_persp(img, (W / 2, int(H * 0.40)), "WELCOME",
                                  t, float(s0) + 0.05, size=_ms)   # IG4 persp3d
        IG.heart_burst(d, W / 2, int(H * 0.58), t, float(s0) + 0.18, n=6)
        scene_label(img, (86, int(H * 0.92)), "3D type slam / persp3d M1")
        img, z, dx, dy = cam_apply(img, t, float(s0), punch=0.05)
        log_sfx(float(s0), "impact", "M1 3D slam")
        tag = "m1 slam"
    else:  # endcard
        img = canvas("black", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        e1 = eob(t, float(s0), 0.34)
        f_g = R.playfair(int(150 + 60 * min(1, e1)), 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.32), "WELCOME", font=f_g, fill=(240, 240, 238, 245))
        d.text(((W - bb[2] + bb[0]) / 2 + 6, H * 0.32 + (bb[3] - bb[1]) + 36), "to the party",
               font=R.playfair(76, 900), fill=(216, 243, 74, 220))
        R.volt_pill(img, (W / 2, H * 0.60), "IDK x EMINEM x J DILLA", R.montserrat(40, 900), rot=0)
        sticker_confetti(d, W / 2, int(H * 0.20), 180 * e1, t)
        words, active = lyric_at(t)
        if words:
            pill_statement(img, int(H * 0.958) - 52, words, active, size=42)
        img, z, dx, dy = cam_apply(img, t, float(s0), punch=0.03)
        engine, tag = "pil/numpy", "endcard"
        log_sfx(float(s0), "sub", "end card settle")

    arr = np.array(img.convert("RGB")).astype(np.int16)
    g = np.random.default_rng(frame % 7).normal(0, 4, arr.shape[:2])[..., None].astype(np.int16)
    img = Image.fromarray(np.clip(arr + g, 0, 255).astype(np.uint8))
    img.save(f"{FRAMES}/f_{frame:05d}.jpg", quality=90)
    engine_log.append({"frame": frame, "t": round(t, 3), "engine": engine, "beat": tag,
                       "z": round(z, 4), "dx": round(dx, 2), "dy": round(dy, 2)})
    if frame % 90 == 0:
        print(f"frame {frame}/{N}", flush=True)

json.dump({"beats": [round(float(b), 3) for b in LIB_BEATS], "drop": float(DROP),
           "cues": SFX_CUES, "states": [[float(s[0]), s[1]] for s in STATES],
           "onset_engine": OENG, "snap_log": SNAP_LOG, "chunk": [F0, F1],
           "method": "r21: decoded reel quadrant crops = R0 footage layer, code-driven overlays",
           "engine_log_head": engine_log[:4]},
          open(f"{OUTDIR}/replica_v24b_beats_{F0}_{F1}.json", "w"), indent=1)
print("REPLICA v24b FRAMES DONE:", F0, F1, "cues:", len(SFX_CUES), flush=True)
