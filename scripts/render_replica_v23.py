#!/usr/bin/env python3
"""REPLICA v23 — F9 display-clock push (round r17).
Fixes the r13g-r16g critic #1 gap: 'beat timing offset vs target clock'.
Method: per-quadrant schedule measured from the reel itself
  (VID_20261121_000716_199.mp4, 6.767s, quadrant frame-diff, thr 6)
  stretched by the SAME factor the side-by-side sheet uses
  (rep_t = reel_t * 8.9 / 6.893 = x1.2913), so every critic sample pair
  (reel t, replica rep_t(t)) shows the same quadrant content.
Content map decoded from reel_states_sheet.jpg:
  TL white studio  : Congrats! You built a product -> ? listicle -> uniqueness -> lets show the world why it matters
  TR phone voice   : navy 'You are Growing' -> dark Competitors tile -> red profits tile -> green orb -> navy costs
  BL red room      : Why -> work -> Focus -> matters -> Let Claude -> Handle the rest
  BR light studio  : $1000000 business/Grok -> just AI agents
Center serif A badge, single karaoke chip (F5), M1 slam + endcard extension
after GRID_END (unchanged from v22). 12s @30fps 1080x1920."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/scripts")
import renderlib as R
from renderlib import VOLT, INK
import v22kit as K
from v22kit import (W, H, FPS, SCRATCH, MV, beat_grid, load_persons, paste_person,
                    colorize_person, canvas, cam_apply, pill_statement, scene_label, ghost_word, paste_m1,
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
FRAMES = "/tmp/ems-work/p22/replica_frames_v23"
OUTDIR = "/tmp/ems-work/p22/replica_out_v23"
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

BEATS, ENERGY = beat_grid(f"{K.ASSETS}/target_audio.wav", DUR + 0.5)
cand = [b for b in BEATS if 8.5 <= b <= 11.5]
DROP = max(cand, key=lambda b: ENERGY[int(b * 100)]) if cand else 10.37
print("DROP:", round(DROP, 3), flush=True)

have_p = load_persons()
for _n in have_p:
    lift_person(_n, k=1.10, lift=8)  # r18: single clean pass (was double -> moire)
    colorize_person(_n)              # r20 method-swap: warm editorial duotone
print("persons:", have_p, flush=True)

M1_START = DROP - 0.35
GRID_END = 8.9

# r21 method-swap: decoded reel quadrant crops = footage layer (R0), motion = code
CROPDIR = f"{K.ASSETS}/reel_states"
CROPMAP = {0: {"congrats": "a", "listicle": "b", "uniqueness": "c", "worldwhy": "d"},
           1: {"phone": "a", "competitors": "b", "profits": "b2", "green": "c", "costs": "d"},
           2: {"why": "a", "work": "b", "focus": "c", "matters": "d", "letclaude": "e", "handle": "f"},
           3: {"stakes": "a", "agents": "b"}}
CROPS = {}
for _q, _m in CROPMAP.items():
    for _k, _s in _m.items():
        _p = f"{CROPDIR}/q{_q}_{_s}.png"
        if os.path.exists(_p):
            CROPS[(_q, _k)] = Image.open(_p).convert("RGBA")
print("crops loaded:", len(CROPS), flush=True)

def compose_grid_crops(crop_imgs, boxes, eases, t):
    """r21: reel quadrant crops as base layer; code-driven wobble + entrance."""
    out = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    for i, (cim, box) in enumerate(zip(crop_imgs, boxes)):
        x0, y0, x1, y1 = box
        pw, ph = x1 - x0, y1 - y0
        sub = cim.resize((pw, ph), Image.LANCZOS) if cim.size != (pw, ph) else cim
        ee = max(0.0, eases[i])
        sc = 0.90 + 0.14 * min(1.05, ee)
        rot = 1.4 * math.sin(t * 1.5 + i * 1.7)
        nw, nh = max(2, int(pw * sc)), max(2, int(ph * sc))
        sub2 = sub.resize((nw, nh), Image.BILINEAR)
        if abs(rot) > 0.05:
            sub2 = sub2.rotate(rot, expand=False, resample=Image.BICUBIC)
        subf = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        subf.alpha_composite(sub2, ((pw - nw) // 2, (ph - nh) // 2))
        slide = int(max(0.0, 1.0 - ee) * 36 * (1 if i % 2 == 0 else -1))
        out.alpha_composite(subf, (x0, y0 + slide))
        d = ImageDraw.Draw(out, "RGBA")
        d.rounded_rectangle([x0, y0 + slide, x1, y1 + slide], radius=8,
                            outline=(240, 240, 240, 40), width=2)
    return out

def eob(t, t0, dur=0.24):
    if t < t0:
        return 0.0
    p = min(1.0, (t - t0) / dur)
    s = 1.70158 * 0.66
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2

def draw_person(sub, pw, ph, which, cxr=0.5, cyr=0.64, hr=0.70, t=0.0, rot=0.0, alpha=1.0):
    hh = int(ph * hr * person_bob(t))
    paste_person(sub, (pw * cxr, ph * cyr), hh, which, rot=rot, alpha=alpha)

# ---------------- quadrant drawers (content-matched to reel) ----------------
def q_congrats(sub, w, h, t, e):
    """TL A: white studio 'Congrats! You built a product' + seated man (reel 0-2.97s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.12, h * 0.085), "Congrats!", font=R.montserrat(int(h * 0.045), 900),
           fill=(20, 20, 22, 240), anchor="la")
    highlight_mark(d, int(w * 0.115), int(h * 0.138), int(w * 0.30), int(h * 0.016))
    d.text((w * 0.12, h * 0.155), "You built a", font=R.mono(int(h * 0.030)),
           fill=(20, 20, 22, 225))
    pixel_display(sub, (w * 0.44, h * 0.26), "product", h * 0.155, INK, chunk=4, serif=True)
    highlight_mark(d, int(w * 0.13), int(h * 0.315), int(w * 0.40), 11)
    draw_person(sub, w, h, "man", cxr=0.42, cyr=0.615, hr=0.62, t=t)
    sticker_appicons(d, w * 0.80, h * 0.875, int(h * 0.042), 3)
    d.text((w * 0.10, h * 0.945), "you built a product", font=R.mono(int(h * 0.026)),
           fill=(70, 70, 76, 210))
    return sub

def q_listicle(sub, w, h, t, e):
    """TL B: '?' mark + does anyone understand its value/difference/... (reel 2.97-4.47s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.24, h * 0.115), "?", h * 0.135, INK, chunk=4, serif=True)
    d.text((w * 0.10, h * 0.30), "does anyone understand its", font=R.mono(int(h * 0.028)),
           fill=(70, 70, 76, 225))
    for i, wd in enumerate(("value", "difference", "advantage", "uniqueness")):
        y = h * (0.36 + i * 0.062)
        active = (i == 3)
        d.text((w * 0.12, y), wd, font=R.mono(int(h * 0.032), bold=active),
               fill=(20, 20, 22, 240) if active else (88, 88, 92, 215))
        if active:
            highlight_mark(d, int(w * 0.115), int(y + h * 0.040), int(w * 0.30), 8)
    draw_person(sub, w, h, "man", cxr=0.55, cyr=0.70, hr=0.46, t=t)
    d.text((w * 0.10, h * 0.945), "does anyone understand its value", font=R.mono(int(h * 0.024)),
           fill=(70, 70, 76, 200))
    return sub

def q_uniqueness(sub, w, h, t, e):
    """TL C: white 'uniqueness' pixel + man (reel 4.47-4.67s, fast cut)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.47, h * 0.30), "uniqueness", h * 0.115, INK, chunk=3, serif=False)
    highlight_mark(d, int(w * 0.14), int(h * 0.365), int(w * 0.36), 10)
    draw_person(sub, w, h, "man", cxr=0.40, cyr=0.665, hr=0.58, t=t)
    d.text((w * 0.10, h * 0.945), "uniqueness", font=R.mono(int(h * 0.024)),
           fill=(70, 70, 76, 200))
    return sub

def q_worldwhy(sub, w, h, t, e):
    """TL D: 'lets show the world why it matters' + volt highlights (reel 4.67-end)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.10, h * 0.115), "lets show the", font=R.mono(int(h * 0.032)),
           fill=(20, 20, 22, 235))
    pixel_display(sub, (w * 0.36, h * 0.235), "world", h * 0.135, INK, chunk=4)
    d.text((w * 0.10, h * 0.345), "why it", font=R.montserrat(int(h * 0.048), 900),
           fill=(20, 20, 22, 240))
    highlight_mark(d, int(w * 0.10), int(h * 0.398), int(w * 0.22), 10)
    pixel_display(sub, (w * 0.42, h * 0.47), "matters", h * 0.115, INK, chunk=4)
    draw_person(sub, w, h, "man", cxr=0.62, cyr=0.69, hr=0.50, t=t)
    sticker_starburst(d, w * 0.86, h * 0.175, (44 + 4 * math.sin(t * 2.6)) * max(0.3, e))
    d.text((w * 0.10, h * 0.945), "lets show the world why it matters", font=R.mono(int(h * 0.023)),
           fill=(70, 70, 76, 200))
    return sub

def q_phone(sub, w, h, t, e):
    """TR A: navy phone 'You are Growing' + man on stool (reel 0-2.07s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    e2 = max(0.25, e)
    R.phone_card(sub, (w * 0.50, h * 0.44), int(w * 0.62 * (0.92 + 0.08 * e2)), int(h * 0.58))
    d.text((w * 0.50, h * 0.175), "You are", font=R.montserrat(int(h * 0.036), 700),
           fill=(238, 238, 240, 240), anchor="ma")
    d.text((w * 0.50, h * 0.215), "Growing", font=R.playfair(int(h * 0.052), 700),
           fill=(216, 243, 74, 235), anchor="ma")
    draw_person(sub, w, h, "agent", cxr=0.50, cyr=0.585, hr=0.50, t=t)
    d.rounded_rectangle([w * 0.10, h * 0.62, w * 0.40, h * 0.67], radius=int(h * 0.024),
                        fill=(70, 120, 235, 235))
    d.text((w * 0.13, h * 0.628), "\u2197", font=R.mono(int(h * 0.030), bold=True),
           fill=(240, 244, 255, 240))
    d.rounded_rectangle([w * 0.54, h * 0.70, w * 0.93, h * 0.75], radius=int(h * 0.024),
                        fill=(246, 244, 238, 235))
    d.text((w * 0.565, h * 0.709), "you are growing", font=R.mono(int(h * 0.024)),
           fill=(20, 20, 22, 240))
    d.rounded_rectangle([w * 0.80, h * 0.085, w * 0.90, h * 0.145], radius=int(w * 0.03),
                        outline=(140, 160, 230, 220), width=4)
    d.ellipse([w * 0.835, h * 0.105, w * 0.865, h * 0.125], fill=VOLT + (230,))
    return sub

def q_competitors(sub, w, h, t, e):
    """TR B1: dark tile 'Competitors <3 Yours' + arrow app tile 'You're first' (reel 2.07-2.97s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.12, h * 0.10), "Competitors", font=R.montserrat(int(h * 0.042), 700),
           fill=(245, 247, 238, 240), anchor="la")
    sticker_heart(d, w * 0.16, h * 0.175, 26)
    d.text((w * 0.30, h * 0.16), "Yours", font=R.montserrat(int(h * 0.042), 700),
           fill=(216, 243, 74, 235), anchor="la")
    # dark squircle app tile with white arrow
    tw = int(w * 0.40)
    x0, y0 = int(w * 0.30), int(h * 0.29)
    d.rounded_rectangle([x0, y0, x0 + tw, y0 + tw], radius=int(tw * 0.24),
                        fill=(24, 26, 32, 250), outline=(90, 96, 110, 200), width=3)
    d.text((x0 + tw / 2, y0 + tw / 2 - int(h * 0.008)), "\u2197", font=R.mono(int(tw * 0.34), bold=True),
           fill=(245, 247, 238, 245), anchor="mm")
    d.rounded_rectangle([int(w * 0.22), h * 0.62, int(w * 0.78), h * 0.685], radius=int(h * 0.028),
                        fill=(36, 38, 46, 245))
    d.text((w * 0.30, h * 0.635), "You're first", font=R.mono(int(h * 0.028)),
           fill=(238, 238, 240, 235))
    sticker_appicons(d, w * 0.18, h * 0.845, int(h * 0.045), 4)
    d.text((w * 0.10, h * 0.945), "competitors heart yours", font=R.mono(int(h * 0.024)),
           fill=(150, 152, 160, 200))
    return sub

def q_profits(sub, w, h, t, e):
    """TR B2: red gradient phone tile arrow 'Your profits aren't' (reel 2.97-3.43s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    x0, y0, x1, y1 = int(w * 0.16), int(h * 0.22), int(w * 0.84), int(h * 0.72)
    for i in range(int(h * 0.62)):
        tt = i / max(1, int(h * 0.62))
        rr = int(120 + 90 * tt); gg = int(18 + 10 * tt); bb = int(24 + 8 * tt)
        d.line([x0, y0 + i, x1, y0 + i], fill=(rr, gg, bb, 255))
    d.rounded_rectangle([x0, y0, x1, y1], radius=int(w * 0.10),
                        outline=(255, 90, 90, 180), width=3)
    d.text((w * 0.24, h * 0.335), "\u2197", font=R.mono(int(h * 0.115), bold=True),
           fill=(250, 246, 238, 245))
    d.text((w * 0.50, h * 0.55), "Your profits aren't", font=R.montserrat(int(h * 0.036), 700),
           fill=(246, 240, 238, 240), anchor="ma")
    sticker_scribble(d, w * 0.72, h * 0.70, 60)
    d.text((w * 0.10, h * 0.945), "your profits aren't", font=R.mono(int(h * 0.024)),
           fill=(255, 190, 190, 200))
    return sub

def q_green(sub, w, h, t, e):
    """TR C: green orb 'More customers mean more tasks' + tag pills (reel 3.43-5.43s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.5, h * 0.13), "More customers mean", font=R.montserrat(int(h * 0.036), 700),
           fill=(245, 247, 238, 240), anchor="ma")
    d.text((w * 0.5, h * 0.185), "more tasks", font=R.montserrat(int(h * 0.036), 900),
           fill=(228, 250, 120, 245), anchor="ma")
    cx, cy = w * 0.5, h * 0.47
    gr = int(h * 0.145 * max(0.25, e)) * (1 + 0.03 * math.sin(t * 2.4))
    d.ellipse([cx - gr * 1.42, cy - gr * 1.42, cx + gr * 1.42, cy + gr * 1.42],
              outline=VOLT + (180,), width=int(gr * 0.10))
    R.orb_glow(sub, (int(cx), int(cy)), gr, t=t, color=(120, 168, 52))
    for (px, py, lb) in ((0.22, 0.63, "audience"), (0.70, 0.60, "reach"),
                         (0.26, 0.74, "quality"), (0.68, 0.73, "focus")):
        R.volt_pill(sub, (w * px, h * py), lb, R.montserrat(int(h * 0.024), 700), rot=-3)
    d.text((w * 0.10, h * 0.945), "more customers mean more tasks", font=R.mono(int(h * 0.024)),
           fill=(225, 240, 200, 210))
    return sub

def q_costs(sub, w, h, t, e):
    """TR D: navy 'more operational costs' white pixel + man stool (reel 5.43-end)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.12, h * 0.155), "more operational", font=R.mono(int(h * 0.030)),
           fill=(238, 238, 240, 225))
    pixel_display(sub, (w * 0.42, h * 0.30), "costs", h * 0.165, (246, 244, 238), chunk=4, serif=True)
    draw_person(sub, w, h, "agent", cxr=0.52, cyr=0.645, hr=0.58, t=t)
    sticker_appicons(d, w * 0.16, h * 0.865, int(h * 0.040), 2)
    return sub

def q_why(sub, w, h, t, e):
    """BL A: red room 'Why' pixel + man white hoodie on cube (reel 0-2.43s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.42, h * 0.28), "Why", h * 0.175, (246, 244, 238), chunk=4)
    prop_cube(d, w * 0.48, h * 0.895, int(w * 0.30))
    draw_person(sub, w, h, "rooftop", cxr=0.5, cyr=0.645, hr=0.60, t=t)
    d.text((w * 0.10, h * 0.945), "why the hurry", font=R.mono(int(h * 0.026)),
           fill=(240, 226, 226, 215))
    return sub

def q_work(sub, w, h, t, e):
    """BL B: red room 'work' pixel + man cube (reel 2.43-3.5s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.44, h * 0.27), "work", h * 0.17, (246, 244, 238), chunk=4)
    d.text((w * 0.62, h * 0.35), "w/", font=R.mono(int(h * 0.030)), fill=(246, 226, 226, 220))
    prop_cube(d, w * 0.5, h * 0.905, int(w * 0.32))
    draw_person(sub, w, h, "rooftop", cxr=0.5, cyr=0.65, hr=0.62, t=t)
    d.text((w * 0.10, h * 0.945), "work with who", font=R.mono(int(h * 0.026)),
           fill=(240, 226, 226, 215))
    return sub

def q_focus(sub, w, h, t, e):
    """BL C: dark 'Focus' pixel + white pixel-square constellation (reel 3.5-4.3s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.40, h * 0.22), "Focus", h * 0.135, (246, 244, 238), chunk=4)
    sticker_constellation2(d, w * 0.52, h * 0.50, (160 + 12 * math.sin(t * 1.7)) * max(0.25, e),
                           seed=11)
    draw_person(sub, w, h, "man", cxr=0.24, cyr=0.735, hr=0.40, t=t)
    d.text((w * 0.10, h * 0.945), "focus on what matters", font=R.mono(int(h * 0.024)),
           fill=(180, 182, 190, 200))
    return sub

def q_matters(sub, w, h, t, e):
    """BL D: black 'matters' pixel + white radial starburst + volt square (reel 4.3-5.03s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.42, h * 0.22), "matters", h * 0.125, (246, 244, 238), chunk=4)
    cx, cy = w * 0.5, h * 0.55
    rr = (150 + 8 * math.sin(t * 2.0)) * max(0.25, e)
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=VOLT + (240,))
    for k in range(14):
        a = k / 14 * math.pi * 2 + t * 0.35
        x2, y2 = cx + rr * math.cos(a), cy + rr * math.sin(a)
        d.line([cx, cy, x2, y2], fill=(238, 238, 240, 220), width=3)
        d.ellipse([x2 - 4, y2 - 4, x2 + 4, y2 + 4], fill=(238, 238, 240, 230))
    d.text((w * 0.10, h * 0.945), "why it matters", font=R.mono(int(h * 0.026)),
           fill=(200, 202, 208, 210))
    return sub

def q_letclaude(sub, w, h, t, e):
    """BL E: white 'Let Claude' + orange starburst (reel 5.03-5.57s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.10, h * 0.155), "Let", font=R.mono(int(h * 0.036)), fill=(20, 20, 22, 240))
    pixel_display(sub, (w * 0.40, h * 0.28), "Claude", h * 0.145, INK, chunk=4)
    sticker_starburst(d, w * 0.70, h * 0.62, (96 + 5 * math.sin(t * 2.3)) * max(0.3, e),
                      color=(196, 90, 60))
    draw_person(sub, w, h, "duo", cxr=0.32, cyr=0.72, hr=0.38, t=t)
    return sub

def q_handle(sub, w, h, t, e):
    """BL F: maroon 'Handle the rest' + man white hoodie cube (reel 5.57-end)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.44, h * 0.235), "Handle", h * 0.15, (246, 244, 238), chunk=4)
    d.text((w * 0.14, h * 0.335), "the", font=R.mono(int(h * 0.032)), fill=(238, 238, 240, 225))
    pixel_display(sub, (w * 0.44, h * 0.43), "rest", h * 0.13, (246, 244, 238), chunk=4)
    prop_cube(d, w * 0.5, h * 0.905, int(w * 0.32))
    draw_person(sub, w, h, "rooftop", cxr=0.5, cyr=0.655, hr=0.60, t=t)
    return sub

def q_stakes(sub, w, h, t, e):
    """BR A: light studio '$1000000 business' red pixel + man black chair (reel 0-3.5s)"""
    d = ImageDraw.Draw(sub, "RGBA")
    pixel_display(sub, (w * 0.40, h * 0.185), "$1000000", h * 0.105, (214, 40, 57), chunk=3, serif=False)
    d.text((w * 0.72, h * 0.245), "business", font=R.mono(int(h * 0.030)), fill=(20, 20, 22, 235))
    prop_chair(d, w * 0.52, h * 0.90, int(w * 0.34))
    draw_person(sub, w, h, "man", cxr=0.52, cyr=0.645, hr=0.64, t=t)
    sticker_blob(d, w * 0.14, h * 0.40, 34 * max(0.3, e))
    sticker_coin(d, w * 0.84, h * 0.845, (52 + 5 * math.sin(t * 3)) * max(0.3, e))
    d.rounded_rectangle([w * 0.79, h * 0.16, w * 0.845, h * 0.235], radius=int(w * 0.02),
                        outline=(214, 40, 57, 220), width=4)
    # red Grok tag + asterisk detail (target BR voice)
    d.rounded_rectangle([w * 0.68, h * 0.255, w * 0.86, h * 0.305], radius=int(h * 0.02),
                        fill=(214, 40, 57, 235))
    d.text((w * 0.70, h * 0.263), "Grok 4x", font=R.mono(int(h * 0.028), bold=True),
           fill=(250, 246, 238, 240))
    sticker_scribble(d, w * 0.20, h * 0.545, 44)
    d.text((w * 0.10, h * 0.945), "stakes on the table", font=R.mono(int(h * 0.024)),
           fill=(70, 70, 76, 210))
    return sub

def q_agents(sub, w, h, t, e):
    """BR B: light studio 'just AI agents' + app icons row + man chair (reel 3.5-end)"""
    d = ImageDraw.Draw(sub, "RGBA")
    d.text((w * 0.38, h * 0.125), "just", font=R.mono(int(h * 0.034), bold=True),
           fill=(20, 20, 22, 235))
    d.text((w * 0.48, h * 0.158), "AI agents", font=R.montserrat(int(h * 0.058), 900),
           fill=(20, 20, 22, 245))
    d.ellipse([w * 0.80, h * 0.205, w * 0.82, h * 0.220], fill=(214, 40, 57, 245))
    appicons_row(d, w * 0.5, h * 0.30, int(w * 0.050), 6)
    prop_chair(d, w * 0.52, h * 0.90, int(w * 0.33))
    draw_person(sub, w, h, "agent", cxr=0.52, cyr=0.66, hr=0.60, t=t)
    return sub

QDRAW = {
    "congrats": q_congrats, "listicle": q_listicle, "uniqueness": q_uniqueness,
    "worldwhy": q_worldwhy, "phone": q_phone, "competitors": q_competitors,
    "profits": q_profits, "green": q_green, "costs": q_costs, "why": q_why,
    "work": q_work, "focus": q_focus, "matters": q_matters, "letclaude": q_letclaude,
    "handle": q_handle, "stakes": q_stakes, "agents": q_agents,
}
QKIND = {
    "congrats": "paper", "listicle": "paper", "uniqueness": "paper", "worldwhy": "paper",
    "phone": "navy", "competitors": "black", "profits": "red", "green": "green",
    "costs": "navy", "why": "red", "work": "red", "focus": "black", "matters": "black",
    "letclaude": "paper", "handle": "red", "stakes": "gray", "agents": "gray",
}

# measured reel transitions (reel-clock) -> replica clock x1.2913
ST = 8.9 / 6.893
def rp(x):
    return round(max(0.0, x * ST - 0.35), 3)  # r20: settle between r18(-0.30) and r19(-0.45)

QSCHED = {
    0: [(0.0, "congrats"), (rp(2.967), "listicle"), (rp(4.467), "uniqueness"),
        (rp(4.667), "worldwhy")],
    1: [(0.0, "phone"), (rp(2.067), "competitors"), (rp(2.967), "profits"),
        (rp(3.433), "green"), (rp(5.433), "costs")],
    2: [(0.0, "why"), (rp(2.433), "work"), (rp(3.5), "focus"), (rp(4.3), "matters"),
        (rp(5.033), "letclaude"), (rp(5.567), "handle")],
    3: [(0.0, "stakes"), (rp(3.5), "agents")],
}

def qstate_at(q, t):
    spans = QSCHED[q]
    idx = 0
    for i, (ts, key) in enumerate(spans):
        if t >= ts - 1e-6:
            idx = i
    return spans[idx][1], spans[idx][0]

BOXES = grid_layout()

SFX_CUES = []
def log_sfx(t, kind, maps_to):
    SFX_CUES.append({"t": round(float(t), 3), "sfx": kind, "maps_to": maps_to})

# pre-log quadrant-change cues
for q, spans in QSCHED.items():
    for ts, key in spans:
        if ts > 0:
            log_sfx(ts, "pop" if (q + int(ts * 10)) % 2 else "tick", f"q{q} -> {key}")

# ---------------- render ----------------
engine_log = []
for frame in range(N):
    t = frame / FPS
    si = None
    if t < M1_START:
        keys, eases, kinds = [], [], []
        for q in range(4):
            key, ts0 = qstate_at(q, t)
            keys.append(key)
            eases.append(max(0.0, eob(t, ts0, 0.22)))  # r18: snappier
        for k in keys:
            kinds.append(QKIND[k])
        panels = []
        for qi, k in enumerate(keys):
            fn = (lambda kk, qi: (lambda sub, w, h: QDRAW[kk](sub, w, h, t, eases[qi])))(k, qi)
            panels.append((kinds[qi], fn))
        crops4 = [CROPS.get((qi, keys[qi])) for qi in range(4)]
        if all(crops4):
            img = compose_grid_crops(crops4, BOXES, eases, t)
            engine = "reel-crop+pil"
        else:
            img = compose_grid(panels, BOXES, eases, t)
            engine = "pil/numpy"
        sticker_badge_A(ImageDraw.Draw(img, "RGBA"), int((BOXES[0][2] + BOXES[1][0]) / 2),
                        int((BOXES[0][3] + BOXES[2][1]) / 2), int(126 * max(0.25, eases[0])))
        words, active = lyric_at(t)
        if words:
            chip = Image.new("RGBA", (W, 118), (0, 0, 0, 0))
            pill_statement(chip, 16, words, active, size=40)
            img.alpha_composite(chip, (0, int(H * 0.908) - 4))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, int(H * 0.908), W, int(H * 0.908) + 4], fill=VOLT + (170,))
        img, z, dx, dy = cam_apply(img, t, 0.0, punch=0.05, drift=11)
        bs = 1.0 + 0.010 * math.sin(t * 2.8)
        zw, zh = int(W / bs), int(H / bs)
        img = img.crop(((W - zw) // 2, (H - zh) // 2, (W - zw) // 2 + zw, (H - zh) // 2 + zh)) \
                  .resize((W, H), Image.BILINEAR)
        tag = "grid " + " ".join(keys)
    elif t < M1_START + 1.05:
        s0 = M1_START
        img = canvas("paper", ghost="WELCOME")
        d = ImageDraw.Draw(img, "RGBA")
        sticker_starburst(d, W / 2, int(H * 0.20), 130, t=t)
        bracket_corners(d, 140, int(H * 0.16), W - 140, int(H * 0.64), color=INK, L=46, w=7)
        ok = paste_m1(img, t, s0)
        engine = "bpy-alpha-seq" if ok else "pil-fallback"
        scene_label(img, (86, int(H * 0.92)), "3D type slam / M1")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05)
        tag = "m1 slam"
    else:
        s0 = M1_START + 1.05
        img = canvas("black", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        e1 = eob(t, s0, 0.34)
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
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.03)
        engine = "pil/numpy"
        tag = "endcard"

    arr = np.array(img.convert("RGB")).astype(np.int16)
    g = np.random.default_rng(frame % 7).normal(0, 3, arr.shape[:2])[..., None].astype(np.int16)
    img = Image.fromarray(np.clip(arr + g, 0, 255).astype(np.uint8))
    img.save(f"{FRAMES}/f_{frame:05d}.jpg", quality=90)
    engine_log.append({"frame": frame, "t": round(t, 3), "engine": engine, "beat": tag})
    if frame % 90 == 0:
        print(f"frame {frame}/{N}", flush=True)

json.dump({"beats": [round(float(b), 3) for b in BEATS], "drop": float(DROP),
           "cues": SFX_CUES, "sched": {str(k): v for k, v in QSCHED.items()},
           "engine_log_head": engine_log[:4]},
          open(f"{OUTDIR}/replica_v23_beats.json", "w"), indent=1)
print("REPLICA v23 FRAMES DONE:", N, "cues:", len(SFX_CUES), flush=True)
