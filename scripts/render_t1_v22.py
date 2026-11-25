#!/usr/bin/env python3
"""T-1 v22 FULL MASTER — WELCOME (IDK ft. Eminem & J Dilla) — 27.9s.
Phase 22 F-fixes over p21:
  F1  canvas-fill/no-void: every designed scene = full-bleed rich canvas + tissue bands
  F2  zoom-through = shrink previous comp into tilted card while next enters big (no glyph cut)
  F3  semantic sticker map (hourglass/coin/lemon/confetti/caution-tape) — NO crosshair-on-face
  F4  B&W+volt color world committed: grade() is neutral B&W (no pink/sepia lift, no warm halation)
  F5  single caption voice (karaoke pill); mono lines become semantic scene labels (no duplicates)
  F6  M1 volt-emissive 3D on rich canvas (no beige box); camera push + DOF via bpy re-render
  F7  camera life: cam_apply punch+drift per scene; no static card >2s
  F8  loudness target -14.0 LUFS +-0.5, TP <= -1.5 (re-mastered downstream in t1_audio_v22)
Engines: pil/numpy canvas+type, bpy-alpha-seq (M1), ffmpeg assemble. TEMP /tmp/ems-work/p22."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/scripts")
import renderlib as R
from renderlib import VOLT, INK
import v22kit as K
from v22kit import (W, H, FPS, SCRATCH, beat_grid, load_persons, paste_person, canvas,
                    cam_apply, pill_statement, scene_label, ghost_word, paste_m1, m1_available,
                    sticker_hourglass, sticker_coin, sticker_lemon, sticker_confetti,
                    sticker_caution, sticker_heart, sticker_appicons, sticker_arrow,
                    sticker_starburst, sticker_constellation, bracket_corners)

from render_replica_12s import mv_frame  # MV frame fetch helper (path-safe)

W2, H2 = W, H
DUR = 27.9
N = int(FPS * DUR)
FRAMES = "/tmp/ems-work/p22/t1_frames"
os.makedirs(FRAMES, exist_ok=True)

BEATS, ENERGY = beat_grid(f"{K.ASSETS}/target_audio.wav", DUR + 0.6)
cand = [b for b in BEATS if 9.0 <= b <= 11.0]
DROP = max(cand, key=lambda b: ENERGY[int(b * 100)]) if cand else 10.37

load_persons()
PAINTING = Image.open(f"{K.ASSETS}/pd_still_life_gen.png").convert("RGB")
M1_SCENE_START = 23.20

# ---------------- F4: neutral B&W grade (no pink/sepia) ----------------
def grade(img):
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = (0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2])
    # neutral B&W: filmic S-curve, deeper blacks, protected highlights
    lum = np.clip((lum - 0.5) * 1.16 + 0.5, 0, 1)
    lum = np.clip(lum ** 1.06, 0, 1)
    arr = np.stack([lum, lum, lum], axis=-1)
    out = Image.fromarray((arr * 255).astype(np.uint8))
    out = R._grain(out, 7)
    out = R._vignette(out, 0.30)
    return out.convert("RGB")

def graded_mv(t):
    return grade(mv_frame(t))

# ---------------- lyric timing (whisper segments, same as p21 — verified) ----------------
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
    (0.00, "hook"),
    (3.30, "ghost"),
    (6.20, "listicle"),
    (9.00, "counter"),
    (11.90, "paint"),
    (14.80, "cascade"),
    (17.60, "pop"),
    (20.40, "callout"),
    (23.20, "m1"),
    (25.60, "endcard"),
]
STICKER_MAP = {
    "party": "confetti burst + app-icons",
    "everybody": "arrow + heart accents",
    "dies at the end": "hourglass (animated sand)",
    "paid": "coin cascade",
    "homicide": "caution-tape band (never crosshair-on-face)",
    "lemonade": "lemon + glass",
    "raw cuts": "real-frame polaroid cascade + connector",
}

def scene_at(t):
    idx = 0
    for i, (s, k) in enumerate(SCENES):
        if t >= s:
            idx = i
    return idx

def draw_scene(idx, t):
    """returns (img, engine, tag, cam_log)"""
    s0, kind = SCENES[idx]
    ent = R.spring_scale(max(0.0, t - s0), 0.34)

    if kind == "hook":  # LB1 + confetti (F3) + full-bleed tissue (F1)
        img = canvas("black", ghost=None)
        img.alpha_composite(graded_mv(1.0).convert("RGBA").resize((1080, 1350)))
        d = ImageDraw.Draw(img, "RGBA")
        size_big = 210
        while R.montserrat(size_big, 900).getlength("WELCOME") > 900 and size_big > 90:
            size_big -= 8
        f_big = R.montserrat(size_big, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_big)
        tw = bb[2] - bb[0]
        d.text(((W - tw) / 2 - 20, H * 0.125), "WELCOME", font=f_big, fill=VOLT + (235,))
        paste_person(img, (W / 2, H * 0.41), 700, "stair", rot=0)
        bracket_corners(d, (W / 2 - tw / 2 - 40, int(H * 0.13), W / 2 + tw / 2 + 40, int(H * 0.36)), color=INK, L=40, w=6)
        R.volt_pill(img, (W / 2, H * 0.065), "IDK x EMINEM x J DILLA", R.montserrat(44, 900), rot=-3)
        sticker_confetti(d, W / 2, int(H * 0.185), 230 * ent, t)
        sticker_appicons(d, W / 2 - 300, int(H * 0.82), 64, 3)
        scene_label(img, (86, int(H * 0.79)), "hook / the party starts here")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05, drift=20)
        return img, "pil", "LB1 hook: volt-behind-head+brackets+pill+confetti", (z, dx, dy)

    elif kind == "ghost":  # LB2 + hourglass sticker (F3) + ticker tissue (F1)
        img = canvas("black", ghost="everybody dies at the end")
        d = ImageDraw.Draw(img, "RGBA")
        f_g = R.playfair(132, 900)
        bb = d.textbbox((0, 0), "everybody", font=f_g)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.36), "everybody", font=f_g, fill=(240, 240, 236, 240))
        bb2 = d.textbbox((0, 0), "dies at the end", font=f_g)
        d.text(((W - bb2[2] + bb2[0]) / 2, H * 0.46), "dies at the end", font=f_g, fill=VOLT + (235,))
        sc = R.spring_scale(max(0.0, t - s0 - 0.12), 0.32)
        if sc > 0.5:
            sticker_hourglass(d, W - 190, int(H * 0.30), 150, t)
            paste_person(img, (170, int(H * 0.62)), 420 * min(1.0, sc), "church", rot=-2, alpha=0.92)
        # designed tissue band: lyric ticker strip (not void)
        d.rectangle([0, int(H * 0.845), W, int(H * 0.845) + 6], fill=VOLT + (200,))
        scene_label(img, (86, int(H * 0.80)), "ghost / quote lockup")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.035, drift=20)
        return img, "pil", "LB2 black halftone+ghost quote+hourglass+ticker", (z, dx, dy)

    elif kind == "listicle":  # LB3 full-height footage + right band (F1)
        img = canvas("black", ghost=None)
        frame = graded_mv(7.0)
        fh = frame.resize((760, 1920))
        img.alpha_composite(fh.convert("RGBA"), (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([760, 0, W, H], fill=(10, 10, 13, 255))
        R._halftone(d, W, H, (118, 120, 132), alpha=48, step=24, region=(0, H, 760, W))
        items = [("01", "party"), ("02", "everybody"), ("03", "homicide"), ("04", "paid")]
        active = int((t - s0) / 0.65) % 4
        R.listicle_bars(img, 800, 560, items, R.montserrat(44, 900), active_idx=active, bar_w=110, gap=130)
        scene_label(img, (796, 440), "scene index")
        sticker_coin(d, 880, int(H * 0.88), 74)
        sticker_coin(d, 1000, int(H * 0.93), 54)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=16)
        return img, "pil", "LB3 listicle over full-height graded footage+coins", (z, dx, dy)

    elif kind == "counter":  # LB4 + coin stickers (F3)
        img = canvas("navy", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle([80, int(H * 0.24), W - 80, int(H * 0.80)], radius=28,
                            fill=(12, 20, 46, 200), outline=(240, 244, 255, 60), width=2)
        val = 1000000 + int(ent * 8137)
        f4 = R.montserrat(104, 900)
        txt4 = f"${val:,}"
        bb4 = d.textbbox((0, 0), txt4, font=f4)
        d.text((W / 2 - (bb4[2] - bb4[0]) / 2, H * 0.28 - bb4[1]), txt4, font=f4, fill=(250, 246, 242, 255))
        f4s = R.mono(38)
        bb4s = d.textbbox((0, 0), "stakes on the table", font=f4s)
        d.text((W / 2 - (bb4s[2] - bb4s[0]) / 2, H * 0.40), "stakes on the table", font=f4s, fill=(216, 243, 74, 245))
        for (cx, v4, lab) in ((W / 2 - 260, 2, "MCs"), (W / 2, 1, "take"), (W / 2 + 260, 0, "fear")):
            f4b = R.montserrat(96, 900)
            bb4b = d.textbbox((0, 0), str(v4), font=f4b)
            d.text((cx - (bb4b[2] - bb4b[0]) / 2, H * 0.48 - bb4b[1]), str(v4), font=f4b, fill=(216, 243, 74, 250))
            f4c = R.mono(40, bold=True)
            bb4c = d.textbbox((0, 0), lab, font=f4c)
            d.text((cx - (bb4c[2] - bb4c[0]) / 2, H * 0.575), lab, font=f4c, fill=(240, 240, 244, 245))
        R.volt_pill(img, (W / 2, H * 0.67), "2 MCs / 1 take / 0 fear", R.montserrat(40, 900), rot=-2)
        R.pixel_dots(img, 12, (80, int(H * 0.13), W - 80, int(H * 0.22)), seed=int(t * 4) + 2, size=10)
        sticker_coin(d, W - 160, int(H * 0.115), 64)
        scene_label(img, (86, int(H * 0.86)), "stakes counter")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.045, drift=16)
        return img, "pil", "LB4 counter grid+real stakes+coins", (z, dx, dy)

    elif kind == "paint":  # LB5 + lemon sticker (F3)
        img = canvas("paper", ghost=None)
        sc = R.spring_scale(max(0.0, t - s0), 0.40)
        d = ImageDraw.Draw(img, "RGBA")
        if sc > 0.2:
            pw = int(600 * sc)
            ph = int(pw * PAINTING.height / PAINTING.width)
            R.polaroid(img, PAINTING.resize((pw - 24, ph - 24)), (W / 2 - 60, H * 0.40), pw - 24, rot=2)
            sticker_lemon(d, W / 2 + 330, int(H * 0.20), 150 * min(1.0, sc))
        drift = int(math.sin((t - s0) * 1.6) * 14)
        R.highlight_pill(img, (W / 2 - 300 + drift, int(H * 0.70) - 8, W / 2 + 300 + drift, int(H * 0.70) + 58), radius=12)
        f_m = R.mono(46, bold=True)
        d.text((W / 2 - 292 + drift, H * 0.70), "San Pellegrino lemonade", font=f_m, fill=(20, 20, 22, 245))
        scene_label(img, (86, int(H * 0.90)), "painting insert / public domain")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.085, drift=13)
        return img, "pil", "LB5 painting polaroid+highlighter+lemon", (z, dx, dy)

    elif kind == "cascade":  # LB6 real frames + connector (P0 keep)
        img = canvas("paper", ghost=None)
        fr1 = mv_frame(12.5); fr2 = mv_frame(4.5); fr3 = mv_frame(24.0)
        for i, fr in enumerate((fr1, fr2, fr3)):
            arr = np.asarray(fr.convert("RGB")).astype(np.float32)
            lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
            fr = Image.fromarray(np.stack([lum] * 3, -1).astype(np.uint8))  # B&W world (F4)
        sc = R.spring_scale(max(0.0, t - s0), 0.36)
        d = ImageDraw.Draw(img, "RGBA")
        if sc > 0.2:
            R.polaroid(img, fr1, (W / 2 - 170, H * 0.36), int(300 * sc), rot=-5)
            R.polaroid(img, fr2, (W / 2 + 190, H * 0.46), int(260 * sc), rot=4)
            R.polaroid(img, fr3, (W / 2 - 40, H * 0.60), int(220 * sc), rot=-2)
        d.line([W / 2 - 170, int(H * 0.50), W / 2 + 190, int(H * 0.56)], fill=VOLT + (220,), width=3)
        d.line([W / 2 + 190, int(H * 0.56), W / 2 - 40, int(H * 0.68)], fill=VOLT + (220,), width=3)
        R.volt_pill(img, (W / 2 + 310, H * 0.70), "raw cuts", R.montserrat(40, 900), rot=6)
        sticker_arrow(d, 140, int(H * 0.22), 260, int(H * 0.16))
        scene_label(img, (86, int(H * 0.90)), "cascade / raw frames")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05, drift=18)
        return img, "pil", "LB6 polaroid cascade+connector+arrow", (z, dx, dy)

    elif kind == "pop":  # LB7 register in B&W+volt world (F4); F1: full-bleed footage card (Mode B)
        graded = graded_mv(19.0)
        arr = np.asarray(graded).astype(np.float32)
        lum = arr.mean(axis=2, keepdims=True)
        lum = np.clip((lum - lum.mean()) * 1.35 + lum.mean(), 0, 255)  # local-contrast pop (measurable delta)
        pop = Image.fromarray(np.repeat(lum, 3, axis=2).astype(np.uint8))
        # full-bleed cover 1080x1920 (F1 Mode B: full-bleed footage = compositionally full)
        pw, ph = pop.size
        s = H / ph
        nw = int(pw * s)
        pop = pop.resize((nw, H), Image.LANCZOS)
        pop = pop.crop(((nw - W) // 2, 0, (nw - W) // 2 + W, H))
        img = canvas("black", ghost=None)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dg = ImageDraw.Draw(glow)
        dg.ellipse([W / 2 - 420, int(H * 0.30) - 420, W / 2 + 420, int(H * 0.30) + 420], fill=(216, 243, 74, 40))
        glow = glow.filter(ImageFilter.GaussianBlur(60))
        img.alpha_composite(glow)
        img.alpha_composite(pop.convert("RGBA"))
        d = ImageDraw.Draw(img, "RGBA")
        # F5: phone-UI pill = semantic scene label, NOT duplicate of caption words
        d.rounded_rectangle([W / 2 - 210, int(H * 0.80), W / 2 + 210, int(H * 0.80) + 64], radius=32,
                            fill=(10, 10, 14, 215), outline=(240, 244, 255, 120), width=2)
        f_u = R.mono(36, bold=True)
        d.text((W / 2 - 160, int(H * 0.80) + 14), "[ local-contrast pop ]", font=f_u, fill=(240, 244, 255, 240))
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05, drift=18)
        return img, "pil", "LB7 B&W local-contrast pop full-bleed+volt glow+scene label", (z, dx, dy)

    elif kind == "callout":  # LB8 + caution tape (F3), NO crosshair constellation on face
        img = canvas("black", ghost=None)
        img.alpha_composite(graded_mv(22.0).convert("RGBA").resize((1080, 1350)))
        d = ImageDraw.Draw(img, "RGBA")
        sticker_caution(d, 110, int(H * 0.185), 970, int(H * 0.30))
        f_kw = R.playfair(150, 900)
        bb = d.textbbox((0, 0), "homicide", font=f_kw)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.60), "homicide", font=f_kw, fill=(250, 246, 242, 245))
        d.rounded_rectangle([W / 2 - bb[2] / 2 - 14, H * 0.60 + bb[3] + 8, W / 2 + bb[2] / 2 + 14, H * 0.60 + bb[3] + 20],
                            radius=4, fill=VOLT + (235,))
        sticker_arrow(d, 180, int(H * 0.80), 320, int(H * 0.72))
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05, drift=18)
        return img, "pil", "LB8 keyword callout+caution tape (no crosshair)", (z, dx, dy)

    elif kind == "m1":  # F6: rich canvas + volt-emissive M1 (no beige box)
        img = canvas("paper", ghost="WELCOME")
        d = ImageDraw.Draw(img, "RGBA")
        sticker_starburst(d, W / 2, int(H * 0.21), 130, t=t)
        bracket_corners(d, (140, int(H * 0.18), W - 140, int(H * 0.62)), color=INK, L=46, w=7)
        ok = paste_m1(img, t, M1_SCENE_START)
        engine = "bpy-alpha-seq" if ok else "pil-fallback"
        if t < M1_SCENE_START + 0.40:
            sc = R.spring_scale(max(0.0, t - s0 - 0.06), 0.30)
            if sc > 0.2:
                paste_person(img, (W / 2 + 310, H * 0.66), int(380 * sc), "stair", rot=2)
        scene_label(img, (86, int(H * 0.90)), "3D type slam / M1")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=14)
        return img, engine, "M1 volt-emissive 3D slam on rich canvas", (z, dx, dy)

    elif kind == "endcard":  # LB10: loop echo + tissue band (F1); clean black base, NO tissue
        img = canvas("cleanblack", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        f_g = R.playfair(170, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        while bb[2] - bb[0] > 880 and f_g.size > 60:
            f_g = R.playfair(f_g.size - 10, 900)
            bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.30
        d.text((ox + 12, oy + 10), "WELCOME", font=f_g, fill=(190, 190, 196, 34))
        d.text((ox, oy), "WELCOME", font=f_g, fill=(240, 240, 238, 245))
        d.text((ox + 6, oy + bb[3] - bb[1] + 40), "to the party", font=R.playfair(84, 900), fill=(216, 243, 74, 220))
        sc = R.spring_scale(max(0.0, t - s0 - 0.10), 0.32)
        if sc > 0.3:
            R.volt_pill(img, (W / 2, H * 0.545), "IDK x EMINEM x J DILLA", R.montserrat(44, 900), rot=0)
            # loop-echo: small live footage window (designed, not void)
            echo = graded_mv(1.0).resize((420, 525))
            ew = Image.new("RGBA", (444, 549), (0, 0, 0, 0))
            ew.alpha_composite(echo.convert("RGBA"), (12, 12))
            ImageDraw.Draw(ew).rectangle([0, 0, 443, 548], outline=VOLT + (200,), width=3)
            img.alpha_composite(ew, (int(W / 2 - 222), int(H * 0.60)))
        R.pixel_dots(img, 9, (100, int(H * 0.88), W - 100, int(H * 0.95)), seed=int(t * 6) + 3, size=10)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.03)
        return img, "pil", "LB10 end card loop-echo window, no brand", (z, dx, dy)

# ---------------- F2: zoom-through = shrink-card transition ----------------
ZT = (11.30, 11.90)  # window: counter shrinks into tilted card, paint enters big
INV = (17.60, 17.85)
WHIP = (3.30, 3.42)

def transition_frame(t):
    """F2 composite: prev comp shrinks into tilted card (fully inside frame, no glyph cut),
    next comp enters big underneath."""
    prev_idx = scene_at(t - 0.01)
    next_idx = scene_at(t + 0.01)
    p = (t - ZT[0]) / (ZT[1] - ZT[0])
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    nxt, _, _, _ = draw_scene(next_idx, t)  # new comp enters big (scale 0.80->1.0)
    ns = 0.80 + 0.20 * p
    nw, nh = int(W * ns), int(H * ns)
    n2 = nxt.resize((nw, nh), Image.BILINEAR)
    base.alpha_composite(n2, ((W - nw) // 2, (H - nh) // 2))
    prv, _, _, _ = draw_scene(prev_idx, ZT[0])  # frozen prev comp
    ps = 0.82 - 0.40 * p         # shrink to card (p=0 fits with frame margins)
    rot = -8.0 * p               # tilt
    pw, ph = int(W * ps), int(H * ps)
    p2 = prv.resize((pw, ph), Image.BILINEAR).rotate(rot, expand=True, resample=Image.BICUBIC)
    # card frame + shadow
    card = Image.new("RGBA", (p2.width + 24, p2.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=18,
                                           fill=(10, 10, 12, 255), outline=VOLT + (220,), width=3)
    card.alpha_composite(p2, (12, 12))
    sh = Image.new("RGBA", (card.width + 60, card.height + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([30, 38, 30 + card.width, 38 + card.height], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    sh.alpha_composite(card, (30, 30))
    card = sh
    # fully inside frame (F2 gate: no glyph cut at edges)
    cx, cy = W / 2, H * 0.44
    px = int(min(max(6, cx - card.width / 2), W - card.width - 6))
    py = int(min(max(6, cy - card.height / 2), H - card.height - 6))
    assert 0 <= px and px + card.width <= W and 0 <= py and py + card.height <= H, "card out of bounds"
    base.alpha_composite(card, (px, py))
    return base

def compose(fi):
    t = fi / FPS
    log_cam = None
    if ZT[0] <= t <= ZT[1]:
        img = transition_frame(t).convert("RGB")
        img = R._grain(img, 3)
        engine, tag = "pil-transition", "F2 shrink-card zoom-through"
    else:
        img, engine, tag, log_cam = draw_scene(scene_at(t), t)
        img = img.convert("RGB")
        # captions: single voice karaoke (F5) — everywhere except endcard/m1 cleanliness
        if scene_at(t) not in (8, 9):
            words = words_window(t)
            if words:
                R.draw_caption_line(img, words, t, int(H * 0.885))
        img = R._grain(img, 3)
    if INV[0] <= t <= INV[1]:
        arr = 255 - np.asarray(img.convert("RGB"))
        img = Image.fromarray(arr.astype(np.uint8))
    if WHIP[0] <= t <= WHIP[1]:
        img = img.filter(ImageFilter.GaussianBlur(1.0 + 10 * math.sin(math.pi * (t - WHIP[0]) / (WHIP[1] - WHIP[0]))))
    return img, engine, tag, log_cam

if __name__ == "__main__":
    a = sys.argv
    START = int(a[a.index("--start") + 1]) if "--start" in a else 0
    END = int(a[a.index("--end") + 1]) if "--end" in a else N - 1
    log = []
    cam_deltas = []
    for fi in range(START, END + 1):
        img, engine, tag, cam_log = compose(fi)
        img.save(f"{FRAMES}/t_{fi:05d}.jpg", quality=90)
        log.append({"frame": fi, "engine": engine, "beat": tag})
        if cam_log:
            cam_deltas.append({"t": round(fi / FPS, 3), "scale": round(cam_log[0], 4),
                               "dx": round(cam_log[1], 2), "dy": round(cam_log[2], 2)})
        if fi % 120 == 0:
            print(f"frame {fi}/{END}", flush=True)
    json.dump({"beats": BEATS, "drop": DROP, "engine_log": log,
               "scenes": [(s[0], s[1]) for s in SCENES],
               "sticker_map": STICKER_MAP, "camera_log": cam_deltas,
               "m1_available": m1_available()},
              open(f"{SCRATCH}/t1_v22_engine_log_{START}_{END}.json", "w"), indent=1)
    print("T1 v22 FRAMES DONE", START, END)
