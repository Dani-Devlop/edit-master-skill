#!/usr/bin/env python3
"""T-1 FULL MASTER — WELCOME (IDK ft. Eminem & J Dilla) — 27.9s (source-limited; source clip 27.91s).
Lookbook LB1-LB10 + captions karaoke v2 + camera moves + grade + M1 3D accent + cue-sheet SFX.
Engines per beat logged: python-pil/numpy (canvas+type), bpy-alpha-seq (3D), ffmpeg (grade/assemble/audio).
Footage = one layer (R0); designed canvases elsewhere; blur-bg banned (AS2)."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/scripts")
import renderlib as R
from renderlib import VOLT, INK
from render_replica_12s import beat_grid, clean_cutout, paste_person, mv_frame

W, H, FPS = 1080, 1920, 30
DUR = 27.9
N = int(FPS * DUR)
SCRATCH = "/tmp/my-project/p21work/scratch"
FRAMES = f"{SCRATCH}/t1_frames"
MV = "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
os.makedirs(FRAMES, exist_ok=True)

BEATS, ENERGY = beat_grid(f"{SCRATCH}/target_audio.wav", DUR + 0.6)
cand = [b for b in BEATS if 9.0 <= b <= 11.0]
DROP = max(cand, key=lambda b: ENERGY[int(b * 100)]) if cand else 10.37

PERSON = clean_cutout("stair11_isnet")
BUILDING = clean_cutout("building25_isnet")
CAR = clean_cutout("car_isnet")
PAINTING = Image.open(f"{SCRATCH}/pd_still_life_gen.png").convert("RGB")

# ---------------- grade (PL2: S-Log3-style curve + halation + grain + vignette) ----------------
def grade(img):
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    # S-curve
    arr = np.clip((arr - 0.5) * 1.18 + 0.5 + 0.02 * np.sin((arr - 0.5) * math.pi), 0, 1)
    # skin protect: keep R slightly lifted in midtones
    r = arr[..., 0]
    arr[..., 0] = np.clip(r * 1.03 + 0.01, 0, 1)
    # halation: red-channel glow
    glow = Image.fromarray((arr * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))
    ga = np.asarray(glow).astype(np.float32) / 255.0
    arr = np.clip(arr + (ga[..., 0:1] * 0.16), 0, 1)
    out = Image.fromarray((arr * 255).astype(np.uint8))
    # grain + vignette
    out = R._grain(out, 7)
    out = R._vignette(out, 0.30)
    return out.convert("RGB")

def graded_mv(t):
    raw = mv_frame(t)
    return grade(raw)

M1_SEQ = f"{SCRATCH}/m1_seq"
M1_FRAMES = 84
M1_SCENE_START = 23.20
def paste_m1(img, t):
    f = int((t - M1_SCENE_START) * FPS)
    if 0 <= f < M1_FRAMES:
        p = f"{M1_SEQ}/f_{f:04d}.png"
        if os.path.exists(p):
            img.alpha_composite(Image.open(p).convert("RGBA").resize((1080, 1920)))

# ---------------- lyric word timing (whisper segments -> per-word interpolated ts, clamped ±120ms) ----------------
SEGS = [
    (0.00, 4.32, "Welcome to the party where everybody dies at the end"),
    (4.32, 5.44, "Move your body"),
    (5.44, 8.32, "this is about to beat on homicide scene"),
    (8.32, 11.12, "I think you walk not me we're not screened"),
    (11.12, 13.12, "Welcome to another day"),
    (13.12, 16.48, "to another plot on my mind because I gots to get paid"),
    (16.48, 18.56, "I'd rather get paid than laid"),
    (18.56, 20.56, "If life hand me lemons then it's San"),
    (20.56, 22.24, "Pellegrino lemonade"),
    (22.24, 24.32, "Baccarat rock glasses with chips on it"),
    (24.32, 26.16, "women need a pasta on my clean"),
    (26.16, 27.90, "and familia needs to place"),
]
LYRIC_WORDS = []
for (s, e, txt) in SEGS:
    words = txt.split()
    dur = max(0.001, e - s)
    # weighted by length
    wsum = sum(len(wd) for wd in words) + len(words)
    acc = s
    for wd in words:
        wd_dur = dur * (len(wd) + 1) / wsum
        LYRIC_WORDS.append({"text": wd, "start": round(acc, 2), "end": round(acc + wd_dur, 2)})
        acc += wd_dur

def words_window(t, back=3.0):
    return [w for w in LYRIC_WORDS if w["start"] <= t < w["end"] + back][-3:]

# ---------------- scene table ----------------
SCENES = [
    (0.00, "hook"),     # LB1
    (3.30, "ghost"),    # LB2
    (6.20, "listicle"), # LB3
    (9.00, "counter"),  # LB4 (+ out-of-screen zoom exit)
    (11.90, "paint"),   # LB5
    (14.80, "cascade"), # LB6
    (17.60, "pop"),     # LB7 color-pop teal-orange
    (20.40, "callout"), # LB8
    (23.20, "m1"),      # 3D slam (M1)
    (25.60, "endcard"), # LB10
]

def scene_at(t):
    idx = 0
    for i, (s, k) in enumerate(SCENES):
        if t >= s:
            idx = i
    return idx

def entrance(t0, t, dur=0.34):
    return R.spring_scale(max(0.0, t - t0), dur)

def draw_scene(img, t, fi):
    idx = scene_at(t)
    s0, kind = SCENES[idx]
    t1 = SCENES[idx + 1][0] if idx + 1 < len(SCENES) else DUR
    ent = entrance(s0, t)
    d = ImageDraw.Draw(img, "RGBA")

    if kind == "hook":
        img.alpha_composite(graded_mv(1.0).convert("RGBA").resize((1080, 1350)))
        # giant volt word BEHIND head: paste cutout subject OVER the volt word
        size_big = 210
        while R.montserrat(size_big, 900).getlength("WELCOME") > 900 and size_big > 90:
            size_big -= 8
        f_big = R.montserrat(size_big, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_big)
        tw = bb[2] - bb[0]
        d.text(((W - tw) / 2 - 20, H * 0.125), "WELCOME", font=f_big, fill=VOLT + (235,))
        paste_person(img, (W / 2, H * 0.41), 700, "stair", rot=0)
        R.bracket_corners(img, (W / 2 - tw / 2 - 40, int(H * 0.13), W / 2 + tw / 2 + 40, int(H * 0.36)), color=INK, w=6, arm=40)
        R.volt_pill(img, (W / 2, H * 0.065), "IDK x EMINEM x J DILLA", R.montserrat(44, 900), rot=-3)
        sc = R.spring_scale(ent, 0.34)
        if sc > 0.5:
            f_m = R.mono(40, bold=True)
            d.text((W / 2 - 170, H * 0.78), "the party starts here", font=f_m, fill=(250, 250, 246, 235))
        return "pil", "LB1 hook: volt-behind-head+brackets+pill"
    elif kind == "ghost":
        img.alpha_composite(R.black_halftone(W, H, quote="everybody dies at the end"))
        f_g = R.playfair(132, 900)
        bb = d.textbbox((0, 0), "everybody", font=f_g)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.40), "everybody", font=f_g, fill=(240, 240, 236, 240))
        bb2 = d.textbbox((0, 0), "dies at the end", font=f_g)
        d.text(((W - bb2[2] + bb2[0]) / 2, H * 0.50), "dies at the end", font=f_g, fill=VOLT + (235,))
        sc = R.spring_scale(max(0.0, t - s0 - 0.12), 0.32)
        if sc > 0.5:
            R.duck_avatar(img, (W - 170, int(H * 0.30)), 46)
        return "pil", "LB2 black halftone+ghost quote"
    elif kind == "listicle":
        img.alpha_composite(graded_mv(7.0).convert("RGBA").resize((760, 950)).crop((0, 0, 760, 950)))
        # designed band on right third instead of blur-pad
        band = R.black_halftone(320, 1920)
        img.alpha_composite(band, (760, 0))
        d2 = ImageDraw.Draw(img, "RGBA")
        f_l = R.montserrat(64, 900)
        items = [("01", "party"), ("02", "everybody"), ("03", "homicide"), ("04", "paid")]
        active = int((t - s0) / 0.65) % 4
        R.listicle_bars(img, 800, 640, items, R.montserrat(44, 900), active_idx=active, bar_w=110, gap=130)
        f_m = R.mono(34, bold=True)
        d2.text((800, 500), "scene index", font=f_m, fill=VOLT + (240,))
        return "pil", "LB3 listicle over graded footage"
    elif kind == "counter":
        img.alpha_composite(R.navy_scene(W, H, ghost=None))
        # panel cards so counters never float unresolved
        d2 = ImageDraw.Draw(img, "RGBA")
        d2.rounded_rectangle([80, int(H * 0.26), W - 80, int(H * 0.80)], radius=28, fill=(12, 20, 46, 200), outline=(240, 244, 255, 60), width=2)
        dd4 = ImageDraw.Draw(img, "RGBA")
        val = 1000000 + int(ent * 8137)
        f4 = R.montserrat(104, 900)
        txt4 = f"${val:,}"
        bb4 = dd4.textbbox((0, 0), txt4, font=f4)
        dd4.text((W / 2 - (bb4[2] - bb4[0]) / 2, H * 0.30 - bb4[1]), txt4, font=f4, fill=(250, 246, 242, 255))
        f4s = R.mono(38)
        bb4s = dd4.textbbox((0, 0), "stakes on the table", font=f4s)
        dd4.text((W / 2 - (bb4s[2] - bb4s[0]) / 2, H * 0.42), "stakes on the table", font=f4s, fill=(255, 190, 180, 245))
        for (cx, v4, lab) in ((W / 2 - 260, 2, "MCs"), (W / 2, 1, "take"), (W / 2 + 260, 0, "fear")):
            f4b = R.montserrat(96, 900)
            bb4b = dd4.textbbox((0, 0), str(v4), font=f4b)
            dd4.text((cx - (bb4b[2] - bb4b[0]) / 2, H * 0.50 - bb4b[1]), str(v4), font=f4b, fill=(216, 243, 74, 250))
            f4c = R.mono(40, bold=True)
            bb4c = dd4.textbbox((0, 0), lab, font=f4c)
            dd4.text((cx - (bb4c[2] - bb4c[0]) / 2, H * 0.585), lab, font=f4c, fill=(240, 240, 244, 245))
        R.volt_pill(img, (W / 2, H * 0.68), "2 MCs / 1 take / 0 fear", R.montserrat(40, 900), rot=-2)
        R.pixel_dots(img, 12, (80, int(H * 0.14), W - 80, int(H * 0.24)), seed=int(t * 4) + 2, size=10)
        return "pil", "LB4 counter grid+real stakes"
    elif kind == "paint":
        img.alpha_composite(R.paper_white(W, H))
        sc = R.spring_scale(ent, 0.40)
        if sc > 0.2:
            pw = int(620 * sc)
            ph = int(pw * PAINTING.height / PAINTING.width)
            R.polaroid(img, PAINTING.resize((pw - 24, ph - 24)), (W / 2, H * 0.40), pw - 24, rot=2)
        drift = int(math.sin((t - s0) * 1.6) * 14)
        R.highlight_pill(img, (W / 2 - 300 + drift, int(H * 0.70) - 8, W / 2 + 300 + drift, int(H * 0.70) + 58), radius=12)
        f_m = R.mono(46, bold=True)
        d.text((W / 2 - 292 + drift, H * 0.70), "San Pellegrino lemonade", font=f_m, fill=(20, 20, 22, 245))
        return "pil", "LB5 painting polaroid+highlighter label"
    elif kind == "cascade":
        img.alpha_composite(R.paper_white(W, H))
        fr1 = mv_frame(12.5); fr2 = mv_frame(4.5); fr3 = mv_frame(24.0)
        sc = R.spring_scale(ent, 0.36)
        if sc > 0.2:
            R.polaroid(img, fr1, (W / 2 - 170, H * 0.36), int(300 * sc), rot=-5)
            R.polaroid(img, fr2, (W / 2 + 190, H * 0.46), int(260 * sc), rot=4)
            R.polaroid(img, fr3, (W / 2 - 40, H * 0.60), int(220 * sc), rot=-2)
        d2 = ImageDraw.Draw(img, "RGBA")
        d2.line([W / 2 - 170, int(H * 0.50), W / 2 + 190, int(H * 0.56)], fill=VOLT + (220,), width=3)
        d2.line([W / 2 + 190, int(H * 0.56), W / 2 - 40, int(H * 0.68)], fill=VOLT + (220,), width=3)
        R.volt_pill(img, (W / 2 + 310, H * 0.70), "raw cuts", R.montserrat(40, 900), rot=6)
        return "pil", "LB6 polaroid cascade+connector"
    elif kind == "pop":
        graded = graded_mv(19.0)
        arr = np.asarray(graded).astype(np.float32)
        # teal-orange grade
        arr[..., 0] = np.clip(arr[..., 0] * 1.10 + 8, 0, 255)
        arr[..., 2] = np.clip(arr[..., 2] * 1.06 + 4, 0, 255)
        pop = Image.fromarray(arr.astype(np.uint8)).resize((1080, 1350))
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dg = ImageDraw.Draw(glow)
        dg.ellipse([W / 2 - 420, H * 0.30 - 420, W / 2 + 420, H * 0.30 + 420], fill=(255, 160, 80, 60))
        glow = glow.filter(ImageFilter.GaussianBlur(60))
        img.alpha_composite(glow)
        img.alpha_composite(pop.convert("RGBA"))
        # phone-UI pill ONLY here (LB7 rule)
        d2 = ImageDraw.Draw(img, "RGBA")
        d2.rounded_rectangle([W / 2 - 190, int(H * 0.78), W / 2 + 190, int(H * 0.78) + 64], radius=32, fill=(16, 18, 28, 210), outline=(240, 244, 255, 120), width=2)
        f_u = R.mono(36, bold=True)
        d2.text((W / 2 - 132, int(H * 0.78) + 14), "san pellegrino", font=f_u, fill=(240, 244, 255, 240))
        return "pil", "LB7 color-pop insert+rim glow+phoneUI"
    elif kind == "callout":
        img.alpha_composite(graded_mv(22.0).convert("RGBA").resize((1080, 1350)))
        prog = R.ease_out_cubic(ent / 0.30)
        R.constellation(img, (W / 2, int(H * 0.42)), 7, 220, prog, color=(240, 240, 245))
        f_kw = R.playfair(150, 900)
        bb = d.textbbox((0, 0), "homicide", font=f_kw)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.60), "homicide", font=f_kw, fill=(250, 246, 242, 245))
        d.rounded_rectangle([W / 2 - bb[2] / 2 - 14, H * 0.60 + bb[3] + 8, W / 2 + bb[2] / 2 + 14, H * 0.60 + bb[3] + 20], radius=4, fill=VOLT + (235,))
        return "pil", "LB8 line+dot+keyword callout"
    elif kind == "m1":
        img.alpha_composite(R.paper_white(W, H))
        paste_m1(img, t)
        if t < M1_SCENE_START + 0.40:
            sc = R.spring_scale(max(0.0, t - s0 - 0.06), 0.30)
            if sc > 0.2:
                paste_person(img, (W / 2 + 310, H * 0.66), int(380 * sc), "stair", rot=2)
        return "bpy-alpha-seq", "M1 3D type slam accent"
    elif kind == "endcard":
        img.alpha_composite(R.black_halftone(W, H))
        f_g = R.playfair(170, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        while bb[2] - bb[0] > 880:
            f_g = R.playfair(170 - 10 * (1 if bb[2] - bb[0] > 880 else 0), 900)
            break
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.355
        d.text((ox + 12, oy + 10), "WELCOME", font=f_g, fill=(190, 190, 196, 34))
        d.text((ox, oy), "WELCOME", font=f_g, fill=(240, 240, 238, 245))
        d.text((ox + 6, oy + bb[3] - bb[1] + 40), "to the party", font=R.playfair(84, 900), fill=(216, 243, 74, 220))
        sc = R.spring_scale(max(0.0, t - s0 - 0.10), 0.32)
        if sc > 0.3:
            R.volt_pill(img, (W / 2, H * 0.60), "IDK x EMINEM x J DILLA", R.montserrat(44, 900), rot=0)
        R.pixel_dots(img, 9, (100, int(H * 0.64), W - 100, int(H * 0.80)), seed=int(t * 6) + 3, size=10)
        return "pil", "LB10 clean end card loop-echo, no brand"

# ---------------- transitions (PL6): whip / zoom-through / invert ----------------
ZT = (9.00, 11.90)   # zoom-through window between counter and paint
INV = (17.60, 17.85)  # invert bite at pop start
WHIP = (3.30, 3.42)

def transition_mod(fi, img):
    t = fi / FPS
    # recursive zoom-through: counter canvas scales up + re-enters itself
    if ZT[0] + 0.6 < t < ZT[1]:
        p = (t - (ZT[0] + 0.6)) / (ZT[1] - (ZT[0] + 0.6))
        z = 1.0 + p * 2.2
        zw, zh = int(W * z), int(H * z)
        big = img.resize((zw, zh), Image.BILINEAR)
        img = big.crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    elif ZT[0] <= t <= ZT[0] + 0.6:
        p = (t - ZT[0]) / 0.6
        z = 1.0 + p * 0.5
        zw, zh = int(W * z), int(H * z)
        big = img.resize((zw, zh), Image.BILINEAR)
        img = big.crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    # invert bite
    if INV[0] <= t <= INV[1]:
        arr = 255 - np.asarray(img.convert("RGB"))
        img = Image.fromarray(arr.astype(np.uint8))
    # whip blur
    if WHIP[0] <= t <= WHIP[1]:
        img = img.filter(ImageFilter.GaussianBlur(1.0 + 10 * math.sin(math.pi * (t - WHIP[0]) / (WHIP[1] - WHIP[0]))))
    return img

def compose(fi):
    t = fi / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    engine, tag = draw_scene(img, t, fi)
    if scene_at(t) not in (9,):  # captions everywhere except end card cleanliness? keep captions on endcard too (lyric ends) but cleaner: keep
        pass
    words = words_window(t)
    if words and scene_at(t) != 9:
        R.draw_caption_line(img, words, t, int(H * 0.885))
    img = transition_mod(fi, img).convert("RGB")
    # grain per frame for cohesion
    img = R._grain(img, 3)
    return img, engine, tag

if __name__ == "__main__":
    a = sys.argv
    START = int(a[a.index("--start") + 1]) if "--start" in a else 0
    END = int(a[a.index("--end") + 1]) if "--end" in a else N - 1
    log = []
    for fi in range(START, END + 1):
        img, engine, tag = compose(fi)
        img.save(f"{FRAMES}/t_{fi:05d}.jpg", quality=90)
        log.append({"frame": fi, "engine": engine, "beat": tag})
        if fi % 90 == 0:
            print(f"frame {fi}/{END}", flush=True)
    if START == 0:
        json.dump({"beats": BEATS, "drop": DROP, "engine_log": log, "scenes": [(s[0], s[1]) for s in SCENES]},
                  open(f"{SCRATCH}/t1_engine_log.json", "w"), indent=1)
    print("T1 FRAMES DONE", START, END)
