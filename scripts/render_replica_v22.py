#!/usr/bin/env python3
"""REPLICA v22.3 — F9 display-register push.
Decoded target register (from tgt_a_30/450 frames + r1-r7 blind-critic notes):
  2x2 editorial grid, EXACTLY 2 light + 2 dark panels per state; dark quadrants
  rotate (navy phone card / red room / green orb / black constellation);
  light = white paper or light-gray studio; chunky PIXEL-SERIF display words
  (R.pixel_word), LARGE bright cut-out people w/ cube/chair props, sparse volt
  accents, serif 'A' badge at grid center, single karaoke voice on black tissue
  band (F5), M1 3D slam on the drop (F6), per-beat camera life (F7).
Captions: lyric-synced, ONE volt active-accent pill (R5). 12s @30fps 1080x1920."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/scripts")
import renderlib as R
from renderlib import VOLT, INK
import v22kit as K
from v22kit import (W, H, FPS, SCRATCH, MV, beat_grid, load_persons, paste_person,
                    canvas, cam_apply, pill_statement, scene_label, ghost_word, paste_m1,
                    m1_available, sticker_hourglass, sticker_coin, sticker_lemon,
                    sticker_confetti, sticker_caution, sticker_heart,
                    sticker_arrow, sticker_starburst, sticker_constellation, bracket_corners, sticker_appicons,
                    sticker_scribble, sticker_badge_A, sticker_playchip, phone_chip,
                    floating_pill, big_numerals, panel_paper, panel_navy, panel_red,
                    panel_black, person_bob, grid_layout, compose_grid, lyric_at,
                    fit_font, display_word, lift_person, ticker_strip,
                    panel_gray, pixel_display, prop_cube, prop_chair, appicons_row,
                    sticker_blob, highlight_mark, sticker_constellation2)

DUR = 12.0
N = int(FPS * DUR)
FRAMES = "/tmp/ems-work/p22/replica_frames"
OUTDIR = "/tmp/ems-work/p22/replica_out"
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

BEATS, ENERGY = beat_grid(f"{K.ASSETS}/target_audio.wav", DUR + 0.5)
cand = [b for b in BEATS if 8.5 <= b <= 11.5]
DROP = max(cand, key=lambda b: ENERGY[int(b * 100)]) if cand else 10.37
print("BEATS:", [round(b, 2) for b in BEATS])
print("DROP:", round(DROP, 3), flush=True)

have_p = load_persons()
for _n in have_p:
    lift_person(_n, k=1.12, lift=10)  # second pass after auto-levels: bright studio key
print("persons:", have_p, flush=True)

M1_START = DROP - 0.35

def eob(t, t0, dur=0.24):
    """ease-out-back entrance 0..1 (R4)"""
    if t < t0:
        return 0.0
    p = min(1.0, (t - t0) / dur)
    s = 1.70158 * 0.66
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2

def draw_person(sub, pw, ph, which, cxr=0.5, cyr=0.64, hr=0.70, t=0.0, rot=0.0, alpha=1.0):
    hh = int(ph * hr * person_bob(t))
    paste_person(sub, (pw * cxr, ph * cyr), hh, which, rot=rot, alpha=alpha)

# ---------------- panel drawers (target register: sparse + big pixel word + big person) ----------------
def p_welcome(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.40, h * 0.26), WORD_SLOT["word"][:9], h * 0.18, INK, chunk=4, serif=False)
    highlight_mark(d, int(w * 0.14), int(h * 0.335), int(w * 0.36), 11)
    floating_pill(sub, (w * 0.72, h * 0.115), "to the party", int(h * 0.036), rot=-7)
    draw_person(sub, w, h, "man", cxr=0.50, cyr=0.62, hr=0.70, t=t)
    sticker_appicons(d, w * 0.24, h * 0.90, int(h * 0.045), 3)
    d.text((w * 0.10, h * 0.925), "everybody is here tonight", font=R.mono(int(h * 0.028)),
           fill=(20, 20, 22, 225))
    return sub

def p_phone(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    e2 = max(0.25, e)
    R.phone_card(sub, (w * 0.50, h * 0.46), int(w * 0.66 * (0.92 + 0.08 * e2)), int(h * 0.62))
    d.text((w * 0.30, h * 0.155), "You", font=R.playfair(int(h * 0.075), 700),
           fill=(238, 238, 240, 240))
    draw_person(sub, w, h, "agent", cxr=0.50, cyr=0.56, hr=0.52, t=t)
    # cyan UI chip w/ arrow + white chip (target phone voice)
    d.rounded_rectangle([w * 0.10, h * 0.58, w * 0.42, h * 0.63], radius=int(h * 0.024),
                        fill=(70, 120, 235, 235))
    d.text((w * 0.13, h * 0.588), "\u2197", font=R.mono(int(h * 0.03), bold=True),
           fill=(240, 244, 255, 240))
    d.rounded_rectangle([w * 0.52, h * 0.685, w * 0.92, h * 0.735], radius=int(h * 0.024),
                        fill=(246, 244, 238, 235))
    d.text((w * 0.545, h * 0.694), "welcome to the party", font=R.mono(int(h * 0.026)),
           fill=(20, 20, 22, 240))
    # squircle icon top-right (volt dot)
    d.rounded_rectangle([w * 0.80, h * 0.085, w * 0.90, h * 0.145], radius=int(w * 0.03),
                        outline=(140, 160, 230, 220), width=4)
    d.ellipse([w * 0.835, h * 0.105, w * 0.865, h * 0.125], fill=VOLT + (230,))
    return sub

def p_why(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.52, h * 0.335), "Why", h * 0.20, (246, 244, 238), chunk=4)
    prop_cube(d, w * 0.5, h * 0.905, int(w * 0.30))
    draw_person(sub, w, h, "rooftop", cxr=0.5, cyr=0.645, hr=0.62, t=t)
    sticker_blob(d, w * 0.15, h * 0.82, 46 * max(0.3, e))
    sticker_starburst(d, w * 0.86, h * 0.83, (44 + 4 * math.sin(t * 2.6)) * max(0.3, e))
    d.text((w * 0.10, h * 0.945), "that should take minutes?", font=R.mono(int(h * 0.028)),
           fill=(246, 244, 238, 225))
    return sub

def p_stakes(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.52, h * 0.20), "$1008", h * 0.175, (214, 40, 57), chunk=4, serif=False)
    d.text((w * 0.64, h * 0.252), "bus", font=R.mono(int(h * 0.032)), fill=(20, 20, 22, 235))
    d.text((w * 0.10, h * 0.30), "stakes on the table", font=R.mono(int(h * 0.028)),
           fill=(20, 20, 22, 235))
    prop_chair(d, w * 0.5, h * 0.90, int(w * 0.34))
    draw_person(sub, w, h, "man", cxr=0.5, cyr=0.645, hr=0.68, t=t)
    for (sx, sy, ss) in ((0.87, 0.19, 0.040), (0.91, 0.29, 0.034)):
        d.rounded_rectangle([w * (sx - ss / 2), h * (sy - ss), w * (sx + ss / 2), h * sy],
                            radius=int(w * 0.02), outline=(214, 40, 57, 220), width=4)
    sticker_blob(d, w * 0.13, h * 0.17, 36 * max(0.3, e))
    sticker_coin(d, w * 0.82, h * 0.855, (54 + 5 * math.sin(t * 3)) * max(0.3, e))
    return sub

def p_dies(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.48, h * 0.28), WORD_SLOT["word"][:9], h * 0.17, INK, chunk=4)
    sticker_hourglass(d, w * 0.82, h * 0.155, (86 + 6 * math.sin(t * 2)) * max(0.3, e), t,
                      color=(20, 20, 22, 235))
    draw_person(sub, w, h, "car", cxr=0.48, cyr=0.66, hr=0.66, t=t)
    d.text((w * 0.10, h * 0.93), "where everybody goes", font=R.mono(int(h * 0.030)),
           fill=(20, 20, 22, 225))
    highlight_mark(d, int(w * 0.10), int(h * 0.45), 30, 10)
    return sub

def p_homicide(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    sticker_caution(d, int(w * 0.16), int(h * 0.10), int(w * 0.84), int(h * 0.15))
    pixel_display(sub, (w * 0.5, h * 0.325), "homicide", h * 0.155, (246, 244, 238), chunk=4)
    draw_person(sub, w, h, "car", cxr=0.5, cyr=0.635, hr=0.66, t=t)
    d.text((w * 0.08, h * 0.945), "about to beat / homicide scene", font=R.mono(int(h * 0.024)),
           fill=(238, 238, 240, 225))
    return sub

def p_lemon(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.5, h * 0.275), WORD_SLOT["word"][:9], h * 0.17, INK, chunk=4)
    sticker_lemon(d, w * 0.80, h * 0.135, (92 + 6 * math.sin(t * 2.3)) * max(0.3, e))
    sticker_scribble(d, w * 0.80, h * 0.155, 100)
    draw_person(sub, w, h, "duo", cxr=0.46, cyr=0.655, hr=0.66, t=t)
    floating_pill(sub, (w * 0.28, h * 0.40), "san pellegrino", int(h * 0.036), rot=-5)
    d.text((w * 0.10, h * 0.935), "if life hand me lemons", font=R.mono(int(h * 0.030)),
           fill=(20, 20, 22, 225))
    return sub

def p_agents(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    sticker_blob(d, w * 0.14, h * 0.115, 40 * max(0.3, e))
    d.text((w * 0.42, h * 0.145), "just", font=R.mono(int(h * 0.036), bold=True),
           fill=(20, 20, 22, 235))
    d.text((w * 0.50, h * 0.175), "AI agents", font=R.montserrat(int(h * 0.062), 900),
           fill=(20, 20, 22, 245))
    d.ellipse([w * 0.80, h * 0.225, w * 0.818, h * 0.240], fill=(214, 40, 57, 245))
    appicons_row(d, w * 0.5, h * 0.315, int(w * 0.048), 6)
    prop_chair(d, w * 0.5, h * 0.905, int(w * 0.32))
    draw_person(sub, w, h, "agent", cxr=0.5, cyr=0.665, hr=0.64, t=t)
    return sub

def p_whisper(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.5, h * 0.30), "walk not me", h * 0.14, (238, 238, 240), chunk=4,
                  serif=False)
    sticker_constellation2(d, w * 0.5, h * 0.615, (200 + 12 * math.sin(t * 1.7)) * max(0.25, e),
                           seed=8)
    sticker_heart(d, w * 0.84, h * 0.135, 44 + 3 * math.sin(t * 2.2))
    sticker_arrow(d, int(w * 0.12), int(h * 0.80), int(w * 0.30), int(h * 0.72))
    d.text((w * 0.10, h * 0.915), "i think you walk not me", font=R.mono(int(h * 0.026)),
           fill=(238, 238, 240, 210))
    return sub

def p_matters(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.5, h * 0.30), WORD_SLOT["word"][:9], h * 0.185, INK, chunk=4)
    R.volt_pill(sub, (w * 0.40, h * 0.435), "why its", R.montserrat(int(h * 0.036), 900),
                rot=-4, pad=(12, 6))
    draw_person(sub, w, h, "car", cxr=0.55, cyr=0.66, hr=0.64, t=t)
    sticker_scribble(d, w * 0.78, h * 0.87, 78)
    return sub

def p_green(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.5, h * 0.16), "More customers mean", font=R.montserrat(int(h * 0.038), 700),
           fill=(245, 247, 238, 240), anchor="ma")
    R.playfair_italic and d.text((w * 0.5, h * 0.215), "more tasks",
                                 font=R.playfair_italic(int(h * 0.048), 700),
                                 fill=VOLT + (250,), anchor="ma")
    cx, cy = w * 0.5, h * 0.47
    gr = int(h * 0.155 * max(0.25, e)) * (1 + 0.03 * math.sin(t * 2.4))
    d.ellipse([cx - gr * 1.42, cy - gr * 1.42, cx + gr * 1.42, cy + gr * 1.42],
              outline=VOLT + (180,), width=int(gr * 0.10))
    R.orb_glow(sub, (int(cx), int(cy)), gr, t=t, color=(120, 168, 52))
    d.text((w * 0.10, h * 0.925), "more customers mean more tasks", font=R.mono(int(h * 0.026)),
           fill=(240, 244, 236, 215))
    return sub

def p_value(sub, w, h, t, e):
    """listicle register (target TL t=4.5s): mono list + pixel word + volt bullet"""
    d = ImageDraw.Draw(sub, "RGBA")
    f_l = R.mono(int(h * 0.030))
    d.text((w * 0.10, h * 0.115), "value", font=f_l, fill=(88, 88, 92, 235))
    d.text((w * 0.10, h * 0.155), "difference", font=f_l, fill=(88, 88, 92, 235))
    d.text((w * 0.10, h * 0.195), "advantage", font=f_l, fill=(88, 88, 92, 235))
    d.text((w * 0.075, h * 0.255), "\u25b6", font=R.mono(int(h * 0.030), bold=True), fill=VOLT + (240,))
    pixel_display(sub, (w * 0.44, h * 0.335), "uniqueness", h * 0.145, INK, chunk=3)
    draw_person(sub, w, h, "man", cxr=0.50, cyr=0.66, hr=0.64, t=t)
    d.text((w * 0.10, h * 0.935), "that makes it different", font=R.mono(int(h * 0.028)),
           fill=(20, 20, 22, 225))
    return sub

def p_world(sub, w, h, t, e):
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.10, h * 0.145), "lets show the", font=R.mono(int(h * 0.034)),
           fill=(20, 20, 22, 235))
    pixel_display(sub, (w * 0.44, h * 0.30), "world", h * 0.185, INK, chunk=4)
    sticker_starburst(d, w * 0.84, h * 0.15, (66 + 5 * math.sin(t * 2.2)) * max(0.3, e))
    draw_person(sub, w, h, "rooftop", cxr=0.48, cyr=0.655, hr=0.64, t=t)
    highlight_mark(d, int(w * 0.10), int(h * 0.40), 34, 10)
    return sub

def p_costs(sub, w, h, t, e):
    """outline serif on navy (target 6.0-6.5s: 'costs' outline white)"""
    d = ImageDraw.Draw(sub, "RGBA")
    f = R.playfair(int(h * 0.17), 700)
    d.text((w * 0.12, h * 0.24), "costs", font=f, fill=(20, 26, 60, 0),
           stroke_width=3, stroke_fill=(238, 238, 240, 235))
    d.text((w * 0.12, h * 0.40), "more operational", font=R.mono(int(h * 0.030)),
           fill=(238, 238, 240, 225))
    draw_person(sub, w, h, "agent", cxr=0.5, cyr=0.66, hr=0.62, t=t)
    return sub

PANELS = {
    "welcome": p_welcome, "phone": p_phone, "why": p_why, "stakes": p_stakes,
    "dies": p_dies, "homicide": p_homicide, "lemon": p_lemon, "agents": p_agents,
    "whisper": p_whisper, "matters": p_matters, "green": p_green,
    "value": p_value, "world": p_world, "costs": p_costs,
}

KINDS = {
    "welcome": "paper", "dies": "paper", "lemon": "paper", "matters": "paper",
    "phone": "navy", "why": "red", "homicide": "red", "whisper": "black",
    "stakes": "gray", "agents": "gray", "green": "green", "value": "paper",
    "world": "paper", "costs": "navy",
}

# ---------------- scene plan: 2 light + 2 dark per grid state; dark quadrants rotate ----------------
# order = [TL, TR, BL, BR]; L=paper/gray, D=navy/red/black/green
STATES = [
    (0.00, ["welcome", "phone", "why", "stakes"], "grid"),        # composed frame-1 (gate)
    (0.51, ["welcome", "phone", "why", "stakes"], "grid"),        # L D D L (tgt_a_30) ≈beat
    (1.36, ["value", "green", "whisper", "agents"], "grid"),      # L D D L (tgt_a_450)
    (2.21, ["dies", "costs", "homicide", "world"], "grid"),       # L D D L
    (3.06, ["matters", "phone", "whisper", "stakes"], "grid"),    # L D D L (≈beat 3.18)
    (3.91, ["lemon", "green", "why", "agents"], "grid"),          # L D D L rotated (≈beat 3.88)
    (4.76, ["value", "costs", "homicide", "world"], "grid"),      # L D D L
    (5.61, ["welcome", "phone", "whisper", "agents"], "grid"),    # L D D L (≈beat 5.71)
    (6.46, ["matters", "green", "why", "lemon"], "grid"),         # L D D L
    (7.31, ["dies", "costs", "world", "stakes"], "grid"),         # L D D L
    (8.16, ["lemon", "green", "whisper", "agents"], "grid"),      # L D D L (≈beat 8.61)
    (float(M1_START), [float(M1_START), None, None, None], "m1"),
    (float(M1_START) + 1.05, None, "endcard"),
]

def state_at(t):
    idx = 0
    for i, s in enumerate(STATES):
        if t >= s[0] - 1e-6:
            idx = i
    return idx

BOXES = grid_layout()

# ---------------- v22.9 lyric-dynamic word slots ----------------
LYR_SEG = [
    (0.00, "welcome"), (1.36, "value"), (2.21, "the end"), (3.06, "matters"),
    (3.91, "lemonade"), (4.76, "value"), (5.61, "welcome"), (6.46, "matters"),
    (7.31, "the end"), (8.16, "lemonade"),
]
WORD_SLOT = {"word": "welcome"}

SFX_CUES = []
def log_sfx(t, kind, maps_to):
    SFX_CUES.append({"t": round(float(t), 3), "sfx": kind, "maps_to": maps_to})

# ---------------- render ----------------
engine_log = []
for frame in range(N):
    t = frame / FPS
    si = state_at(t)
    s0 = STATES[si][0]
    mode = STATES[si][2]

    if mode == "grid":
        keys = STATES[si][1]
        for _ls, _lw in LYR_SEG:
            if t >= _ls - 1e-6:
                WORD_SLOT["word"] = _lw
        eases = [eob(t, float(s0) + j * 0.05, 0.26) for j in range(4)]
        panels = []
        for k in keys:
            fn = (lambda kk: (lambda sub, w, h: PANELS[kk](sub, w, h, t, eases[keys.index(kk)])))(k)
            panels.append((KINDS[k], fn))
        img = compose_grid(panels, BOXES, eases, t)
        sticker_badge_A(ImageDraw.Draw(img, "RGBA"), int((BOXES[0][2] + BOXES[1][0]) / 2),
                        int((BOXES[0][3] + BOXES[2][1]) / 2), int(126 * max(0.25, eases[0])))
        # compact karaoke chip on center cross (single voice F5; no full-width band)
        words, active = lyric_at(t)
        if words:
            chip = Image.new("RGBA", (W, 118), (0, 0, 0, 0))
            pill_statement(chip, 16, words, active, size=40)
            img.alpha_composite(chip, (0, int(H * 0.908) - 4))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, int(H * 0.908), W, int(H * 0.908) + 4], fill=VOLT + (170,))
        img, z, dx, dy = cam_apply(img, t, float(s0), punch=0.05, drift=11)
        bs = 1.0 + 0.010 * math.sin(t * 2.8)
        zw, zh = int(W / bs), int(H / bs)
        img = img.crop(((W - zw) // 2, (H - zh) // 2, (W - zw) // 2 + zw, (H - zh) // 2 + zh)) \
                  .resize((W, H), Image.BILINEAR)
        if frame <= int(float(s0) * FPS) + 1:
            log_sfx(float(s0), "pop" if si % 2 else "tick", f"grid state {si}")
        engine = "pil/numpy"
        tag = f"grid state {si} {keys}"
    elif mode == "m1":
        img = canvas("paper", ghost="WELCOME")
        d = ImageDraw.Draw(img, "RGBA")
        sticker_starburst(d, W / 2, int(H * 0.20), 130, t=t)
        bracket_corners(d, 140, int(H * 0.16), W - 140, int(H * 0.64), color=INK, L=46, w=7)
        ok = paste_m1(img, t, float(s0))
        engine = "bpy-alpha-seq" if ok else "pil-fallback"
        scene_label(img, (86, int(H * 0.92)), "3D type slam / M1")
        img, z, dx, dy = cam_apply(img, t, float(s0), punch=0.05)
        log_sfx(float(s0), "impact", "M1 3D slam")
        tag = "m1 slam"
    else:  # endcard (LB10 exception)
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
        engine = "pil/numpy"
        tag = "endcard"
        log_sfx(float(s0), "sub", "end card settle")

    arr = np.array(img.convert("RGB")).astype(np.int16)
    g = np.random.default_rng(frame % 7).normal(0, 4, arr.shape[:2])[..., None].astype(np.int16)
    img = Image.fromarray(np.clip(arr + g, 0, 255).astype(np.uint8))
    img.save(f"{FRAMES}/f_{frame:05d}.jpg", quality=90)
    engine_log.append({"frame": frame, "t": round(t, 3), "engine": engine, "beat": tag})
    if frame % 90 == 0:
        print(f"frame {frame}/{N}", flush=True)

json.dump({"beats": [round(float(b), 3) for b in BEATS], "drop": float(DROP),
           "cues": SFX_CUES, "states": [[float(s[0]), s[2]] for s in STATES],
           "engine_log_head": engine_log[:4]},
          open(f"{OUTDIR}/replica_v22_beats.json", "w"), indent=1)
print("REPLICA v22.3 FRAMES DONE:", N, "cues:", len(SFX_CUES), flush=True)
