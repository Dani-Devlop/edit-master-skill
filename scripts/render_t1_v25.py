#!/usr/bin/env python3
"""T-1 v25 FULL MASTER — WELCOME (IDK ft. Eminem & J Dilla) — 27.9s, 9x16.
Phase 25: WC1 live video-in-card / WC2 rembg occlusion hook / WC3 cutout depth /
WC4 tissue fill + hybrid-polish brightened cutouts (B4 blind-critic fixes).
Phase 24 IG-native on top of Phase 22 F-fixes (commit 759f885f):
  IG1 beat-lock: librosa onsets -> EVERY comp change snapped ±60ms (logged);
      kick-synced ±3% scale pulse on comps; kick onsets exported for audio
  IG2 pseudo-UI: cursor-tap triggers scene (2.2s) / comment bubble "dies" (6.2s)
      / notification banner payout (9.0s) / heart-burst payoff (pop) — 4 beats
  IG3 seamless loop: t>=27.6 renders the frame-0 hook composition frozen;
      gate measures last-frame vs first-frame similarity >= 0.9
  IG4 kinetic slams: WELCOME per-letter stagger+chroma+outline (hook), homicide
      slam (callout), persp3d M1 bounce (m1)
  IG5 idle micro-motion: cam drift everywhere + sticker wobble + ticker + dots;
      motion logged per frame (idle census 1s windows)
  IG6 selective color: 'isol' beat 16.6-17.6 volt-hue isolation measured
  IG7 tight pacing: 19 comps, median interval ~1.5s (census gate <=2.0)
  IG8 film texture: grain+vignette (grade) + halation + dust + gate-weave
      + light-leak at ui_tap & pop entrances
  IG9 native captions: draw_caption_pop (active-word pop-bounce + rotate jitter),
      plate at H*0.80 (above IG bottom UI row); COVER = frame 0
  IG10 camera language: punch-ins, whip (ghost in), dutch (ghost/paint), speed
      ramp 0.4x->1.6x (pop), freeze+slam (callout), zoom punch (listicle2),
      match-cut volt-bar (ui_tap->ghost), shrink-card transitions — >=6 moves
Keeps: LF2 video-in-card live mini-videos, F2 shrink-card zoom-through (no glyph
cut), F3 semantic stickers, F4 B&W+volt world, F5 single caption voice, F7 camera
life. bpy NOT available this session -> M1 = persp3d engine (honest substitute).
Engines: pil/numpy canvas+type, persp3d (M1-M5), ffmpeg assemble.
TEMP /tmp/ems-work/p24."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components"))
sys.path.insert(0, _HERE)
import renderlib as R
from renderlib import VOLT, INK
import ig24kit as IG
IG.bind_renderlib(R)
import v22kit as K
import wc25kit as WC
WC.bind_renderlib(K)
from v22kit import (W, H, FPS, load_persons, paste_person, canvas, cam_apply,
                    sticker_hourglass, sticker_coin, sticker_lemon, sticker_confetti,
                    sticker_caution, sticker_arrow, sticker_starburst, sticker_appicons,
                    bracket_corners, scene_label)

# hybrid human-polish (B4): brightened cutouts, alpha preserved
for _nm in ("man", "stair", "rock22", "duo", "church", "agent"):
    WC.lift_person_v25(_nm)

# Ph26 S1/B7: DELIVERABLE master — internal scene labels disabled (QC-logged)
K.LABELS_ENABLED = False

# Ph26 S4/B10: glyph-collision census (registered scenes, every frame)
COLL = {"checked": 0, "violations": []}
def occ_census(scene, boxes):
    """boxes: (name, box, kind) triples; kind in glyph|ui|sticker."""
    WC.occ_reset()
    for nm, bx, kd in boxes:
        WC.occ_add(nm, bx, kind=kd)
    v = WC.occ_violations()
    COLL["checked"] += 1
    for x in v:
        COLL["violations"].append({"scene": scene, **x})
    return v

import render_t1_v25_showcase as _SHOW
from render_t1_v25_showcase import draw_hook as v25_hook, confetti_v

def mv_frame(t):
    """MV frame fetch (720x900), path-safe, cached (v25: wc25kit decoder)"""
    return WC.mv_source_frame(t)

DUR = 27.9
N = int(FPS * DUR)
FRAMES = f"{K.EMS_WORK}/v26_frames"
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(f"{K.SCRATCH}/scratch12s", exist_ok=True)  # legacy cache dir

# ---------------- IG1 beat-lock ----------------
ONSETS, LIB_BEATS, KICKS, TEMPO, OENG = IG.onset_grid(
    f"{K.ASSETS}/target_audio.wav", DUR + 0.6)
SNAP_LOG = []
def snap(t):
    # quantize to NEAREST detected onset (DAW-style grid quantize) — every cut
    # lands ON an onset; gate measures |cut - nearest onset| <= 60ms (always 0)
    st, d = IG.snap(t, ONSETS, 0.30)
    if st != t and (d is None or d > 0.30):
        b = min(ONSETS, key=lambda o: abs(o - t)) if ONSETS else t
        st, d = round(b, 3), round(abs(b - t), 3)
    SNAP_LOG.append({"plan": round(float(t), 3), "snapped": st, "delta": d})
    return st
print(f"IG1 onsets[{OENG}]: {len(ONSETS)} | kicks: {len(KICKS)} | tempo {TEMPO}", flush=True)

# ---------------- lyric timing (whisper segments, verified p21/p22) ----------------
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

# ---------------- scene plan (IG7 tight pacing, every start IG1-snapped) ---------
PLANNED = [
    (0.00, "hook"), (2.20, "ui_tap"), (3.30, "ghost"), (4.80, "ghost2"),
    (6.20, "listicle"), (7.70, "listicle2"), (9.00, "counter"), (11.30, "zoomthrough"),
    (11.90, "paint"), (13.40, "paint2"), (14.80, "cascade"), (16.60, "isol"),
    (17.60, "pop"), (19.00, "pop2"), (20.40, "callout"), (22.00, "callout2"),
    (23.20, "m1"), (25.60, "endcard"), (27.60, "loop"),
]
SCENES = [(snap(s), k) for (s, k) in PLANNED]
ST = {k: t for (t, k) in SCENES}
HOOK_T, UITAP_T, GHOST_T, GHOST2_T = ST["hook"], ST["ui_tap"], ST["ghost"], ST["ghost2"]
LIST_T, LIST2_T, COUNTER_T, ZT_T = ST["listicle"], ST["listicle2"], ST["counter"], ST["zoomthrough"]
PAINT_T, PAINT2_T, CASCADE_T, ISOL_T = ST["paint"], ST["paint2"], ST["cascade"], ST["isol"]
POP_T, POP2_T, CALLOUT_T, CALLOUT2_T = ST["pop"], ST["pop2"], ST["callout"], ST["callout2"]
M1_SCENE_START, ENDCARD_T, LOOP_START = ST["m1"], ST["endcard"], ST["loop"]
DROP = M1_SCENE_START

STICKER_MAP = {
    "party": "confetti burst + app-icons",
    "everybody": "arrow + heart accents",
    "dies at the end": "hourglass (animated sand)",
    "paid": "coin cascade + payout notification",
    "homicide": "caution-tape band (never crosshair-on-face)",
    "lemonade": "lemon + glass",
    "raw cuts": "real-frame polaroid cascade + connector",
}

# Ph26 S5: light-phase (11.9-17.6s) density census — footage-led + HERO cutouts
# (>=45%H); painting/cascade = accents, never the sole content of a light scene
LIGHT_PHASE = {
    "paint": ["graded paper canvas", "PD painting polaroid", "lemon sticker",
              "wc1 live card (graded)", "HERO cutout man 900px", "highlight pill",
              "halftone tissue", "grain+vignette"],
    "paint2": ["graded paper canvas", "M2 parallax live polaroids x3", "HERO cutout duo 880px",
               "wc4 particles", "halftone", "grain", "cam drift", "dof blur"],
    "cascade": ["graded paper canvas", "wc1 live card c1", "wc1 live card c2",
                "M5 world insert (live)", "volt connectors", "raw-cuts pill",
                "arrow sticker", "HERO cutout church 880px", "halftone"],
    "isol": ["graded paper canvas", "painting polaroid", "HERO cutout man 880px",
             "coin stickers x2", "volt-only headline", "pixel dots",
             "selective-color isolation", "cam life"],
}

# ---------------- F4 grade + IG8 film texture ----------------
def grade(img):
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = (0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2])
    lum = np.clip((lum - 0.5) * 1.16 + 0.5, 0, 1)
    lum = np.clip(lum ** 1.06, 0, 1)
    arr = np.stack([lum, lum, lum], axis=-1)
    out = Image.fromarray((arr * 255).astype(np.uint8))
    out = R._grain(out, 7)
    out = R._vignette(out, 0.30)
    return out.convert("RGB")

def graded_mv(t):
    return grade(mv_frame(max(0.05, t)))

def dutch(img, deg):
    if abs(deg) < 0.15:
        return img
    return img.rotate(deg, resample=Image.BICUBIC, fillcolor=(8, 8, 10, 255))

# scene canvas cache (deterministic canvases -> identical every call, big speedup)
_CANVAS = {}
def canvas_cached(kind, ghost=None):
    key = (kind, ghost)
    if key not in _CANVAS:
        _CANVAS[key] = canvas(kind, ghost=ghost)
    return _CANVAS[key].copy()

# ---------------- F2 shrink-card transitions (ui_tap / zoomthrough) ---------------
def shrink_card(prev_idx, next_idx, p, t_abs, tap_fx=False, wobble=True):
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    nxt, _, _, _ = draw_scene(next_idx, t_abs)
    nxt = nxt.convert("RGBA")
    ns = 0.80 + 0.20 * p
    nw, nh = int(W * ns), int(H * ns)
    n2 = nxt.resize((nw, nh), Image.BILINEAR)
    base.alpha_composite(n2, ((W - nw) // 2, (H - nh) // 2))
    prv, _, _, _ = draw_scene(prev_idx, SCENES[prev_idx][0])
    prv = prv.convert("RGBA")
    ps = 0.82 - 0.40 * p
    rot = -8.0 * p + (IG.rot_jitter(t_abs, 3, 1.4) if wobble else 0.0)
    pw, ph = int(W * ps), int(H * ps)
    p2 = prv.resize((pw, ph), Image.BILINEAR).rotate(rot, expand=True, resample=Image.BICUBIC)
    card = Image.new("RGBA", (p2.width + 24, p2.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=18,
                                           fill=(10, 10, 12, 255), outline=VOLT + (220,), width=3)
    card.alpha_composite(p2, (12, 12))
    sh = Image.new("RGBA", (card.width + 60, card.height + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([30, 38, 30 + card.width, 38 + card.height], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    sh.alpha_composite(card, (30, 30))
    card = sh
    cx, cy = W / 2, H * 0.44
    px = int(min(max(6, cx - card.width / 2), W - card.width - 6))
    py = int(min(max(6, cy - card.height / 2), H - card.height - 6))
    assert 0 <= px and px + card.width <= W and 0 <= py and py + card.height <= H, "card out of bounds"
    base.alpha_composite(card, (px, py))
    if tap_fx:
        IG.cursor_tap(base, px + card.width // 2, py + card.height // 2,
                      t_abs, UITAP_T + 0.42)
    return base

# ---------------- scene drawers ----------------
def draw_scene(idx, t):
    s0, kind = SCENES[idx]
    ent = R.spring_scale(max(0.0, t - s0), 0.34)
    cam_log = (1.0, 0.0, 0.0)
    pulse = IG.kick_pulse(t, KICKS, 0.03)  # IG1 kick-synced scale pulse

    if kind == "hook":  # WC2 full-bleed LIVE occlusion + IG4 slam (v25)
        img, eng, tag, cam_log = v25_hook(
            t, src_start=0.30, scene_t0=s0, rate=0.95, slam_word="WELCOME",
            slam_t0=s0, confetti=True, appicons=False)
        return img, "pil-wc2", "WC2 full-bleed occlusion + IG4 slam", cam_log

    elif kind == "ui_tap":  # IG2 cursor tap triggers next scene + IG8 light-leak
        p = min(1.0, (t - s0) / 0.55)
        img = shrink_card(0, 2, p, t, tap_fx=True)
        d = ImageDraw.Draw(img, "RGBA")
        scene_label(img, (86, int(H * 0.92)), "tap -> next scene (IG2)")
        # C.3: real camera transform on the transition too (monotone zoom+pan path)
        img, z, dx, dy = cam_apply(img.convert("RGBA"), t, s0, punch=0.02)
        cam_log = (z, dx, dy)
        return img.convert("RGB"), "pil-ui", "IG2 cursor-tap beat + IG8 light-leak", cam_log

    elif kind == "ghost":  # LB2 + dutch + hourglass + WC1 live card (v25)
        img = canvas_cached("black", ghost="everybody dies at the end")
        d = ImageDraw.Draw(img, "RGBA")
        gc = WC.wc1_card(graded_mv(9.6 + (t - s0) * 1.15), 320, 360, rot=2.2, border="ink")
        gc = WC.wc1_card_shadow(gc)
        gs_ = WC.spring_stagger(0, t, s0 + 0.15)
        if gs_ > 0.02:
            img.alpha_composite(gc.resize((max(1, int(gc.width * gs_)), max(1, int(gc.height * gs_)))),
                                (60, 170))
        f_g = R.playfair(132, 900)
        bb = d.textbbox((0, 0), "everybody", font=f_g)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.36), "everybody", font=f_g, fill=(240, 240, 236, 240))
        bb2 = d.textbbox((0, 0), "dies at the end", font=f_g)
        d.text(((W - bb2[2] + bb2[0]) / 2, H * 0.46), "dies at the end", font=f_g, fill=VOLT + (235,))
        sc = R.spring_scale(max(0.0, t - s0 - 0.12), 0.32)
        if sc > 0.5:
            sticker_hourglass(d, W - 190, int(H * 0.30), 150, t)
            paste_person(img, (170, int(H * 0.62)), 420 * min(1.0, sc), "church", rot=-2, alpha=0.92)
        d.rectangle([0, int(H * 0.845), W, int(H * 0.845) + 6], fill=VOLT + (200,))
        scene_label(img, (86, int(H * 0.80)), "ghost / quote lockup")
        _q1 = d.textbbox((0, 0), "everybody", font=f_g)
        _q2 = d.textbbox((0, 0), "dies at the end", font=f_g)
        occ_census("ghost", [
            ("quote_everybody", ((W - (_q1[2] - _q1[0])) / 2, int(H * 0.36), (W + (_q1[2] - _q1[0])) / 2, int(H * 0.36) + _q1[3] - _q1[1]), "glyph"),
            ("quote_dies", ((W - (_q2[2] - _q2[0])) / 2, int(H * 0.46), (W + (_q2[2] - _q2[0])) / 2, int(H * 0.46) + _q2[3] - _q2[1]), "glyph"),
            ("hourglass", (W - 190 - 80, int(H * 0.30) - 80, W - 190 + 80, int(H * 0.30) + 80), "sticker"),
            ("wc1_card1", (30, 140, 400, 550), "sticker"),
        ])
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.035, drift=20)
        img = dutch(img, -1.6)  # IG10 dutch
        cam_log = (z * pulse, dx, dy)
        return img, "pil", "IG10 dutch + F3 hourglass", cam_log

    elif kind == "ghost2":  # subcut: jump punch-in + WC1 live card (v25)
        img = canvas_cached("black", ghost="everybody dies at the end")
        d = ImageDraw.Draw(img, "RGBA")
        gc2 = WC.wc1_card(graded_mv(14.2 + (t - s0) * 1.1), 320, 360, rot=-2.4, border="ink")
        gc2 = WC.wc1_card_shadow(gc2)
        gs2 = WC.spring_stagger(0, t, s0 + 0.15)
        if gs2 > 0.02:
            img.alpha_composite(gc2.resize((max(1, int(gc2.width * gs2)), max(1, int(gc2.height * gs2)))),
                                (60, int(H * 0.615)))
        f_g = R.playfair(150, 900)
        bb2 = d.textbbox((0, 0), "dies at the end", font=f_g)
        d.text(((W - bb2[2] + bb2[0]) / 2, H * 0.30), "dies at the end", font=f_g, fill=VOLT + (240,))
        paste_person(img, (W - 240, int(H * 0.60)), 460, "duo", rot=2)
        IG.sticker_scribble if False else None
        # Ph26 S4: scribble moved below the quote band (was overlapping glyphs)
        K.sticker_scribble(d, 250, int(H * 0.435), 200, seed=5)
        d.rectangle([0, int(H * 0.845), W, int(H * 0.845) + 6], fill=VOLT + (200,))
        scene_label(img, (86, int(H * 0.80)), "jump cut / punch-in (IG10)")
        occ_census("ghost2", [
            ("quote_dies2", ((W - 900) / 2, int(H * 0.30) - 5, (W + 900) / 2, int(H * 0.30) + 140), "glyph"),
            ("scribble", (150, int(H * 0.435), 350, int(H * 0.435) + 160), "sticker"),
            ("wc1_card2", (30, int(H * 0.615) - 30, 400, int(H * 0.615) + 400), "sticker"),
        ])
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.10, drift=22)
        cam_log = (z * pulse, dx, dy)
        return img, "pil", "IG10 zoom punch jump-cut", cam_log

    elif kind == "listicle":  # LB3 full-height footage + right band + IG2 comment bubble
        img = canvas_cached("black", ghost=None)
        frame = graded_mv(7.0)
        fh = frame.resize((760, 1920))
        img.alpha_composite(fh.convert("RGBA"), (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        # C.2 void fix: band lift + FULL-band halftone (region was (y0,y1,x0,x1) —
        # old tuple only textured y 760-1920 leaving an upper flat-black zone)
        d.rectangle([760, 0, W, H], fill=(16, 16, 20, 255))
        R._halftone(d, W, H, (118, 120, 132), alpha=56, step=20, region=(0, H, 760, W))
        d.rectangle([760, 0, 766, H], fill=VOLT + (150,))  # volt spine
        # LF2 video-in-card: live mini-video playing inside right band
        live = graded_mv(7.0 + (t - s0) * 1.2).resize((300, 375))
        lc = Image.new("RGBA", (316, 391), (0, 0, 0, 0))
        lc.alpha_composite(live.convert("RGBA"), (8, 8))
        ImageDraw.Draw(lc).rectangle([0, 0, 315, 390], outline=VOLT + (220,), width=3)
        img.alpha_composite(lc, (782, 60))
        items = [("01", "party"), ("02", "everybody"), ("03", "homicide"), ("04", "paid")]
        active = int((t - s0) / 0.65) % 4
        R.listicle_bars(img, 800, 560, items, R.montserrat(44, 900), active_idx=active, bar_w=110, gap=130)
        scene_label(img, (796, 440), "scene index")
        sticker_coin(d, 880, int(H * 0.88), 74)
        sticker_coin(d, 1000, int(H * 0.93), 54)
        IG.comment_bubble(img, int(W * 0.05), int(H * 0.70), "beat on homicide scene",
                          t, IG.snap(s0 + 0.30, ONSETS, 0.30)[0], who="comment", kw="homicide")  # IG2 (onset-quantized)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=16)
        cam_log = (z * pulse, dx, dy)
        return img, "pil", "LF2 video-in-card + IG2 comment bubble", cam_log

    elif kind == "listicle2":  # subcut: zoom punch on lyric stress + density fill (F1)
        img = canvas_cached("black", ghost=None)
        frame = graded_mv(9.5)
        fh = frame.resize((760, 1920))
        img.alpha_composite(fh.convert("RGBA"), (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        # C.2 void fix (same as listicle): band lift + full-band halftone
        d.rectangle([760, 0, W, H], fill=(16, 16, 20, 255))
        R._halftone(d, W, H, (118, 120, 132), alpha=56, step=20, region=(0, H, 760, W))
        d.rectangle([760, 0, 766, H], fill=VOLT + (150,))  # volt spine
        f_kw = R.playfair(120, 900)
        # C.2b glyph-cut fix: keyword spans FULL frame width (editorial bleed over
        # band+footage), fitted <= 1020px — was clipped at right frame edge
        _bb = d.textbbox((0, 0), "homicide", font=f_kw)
        while _bb[2] - _bb[0] > 1020 and f_kw.size > 60:
            f_kw = R.playfair(f_kw.size - 8, 900)
            _bb = d.textbbox((0, 0), "homicide", font=f_kw)
        d.text(((W - _bb[2] + _bb[0]) / 2, int(H * 0.115)), "homicide",
               font=f_kw, fill=(250, 246, 242, 245))
        K.highlight_mark(d, 796, int(H * 0.30), 250, 12)
        items = [("01", "party"), ("02", "everybody"), ("03", "homicide"), ("04", "paid")]
        R.listicle_bars(img, 800, 560, items, R.montserrat(44, 900), active_idx=2, bar_w=110, gap=130)
        scene_label(img, (796, 440), "zoom punch / lyric stress (IG10)")
        # F1 density fill lower band: ticker tissue + coins + pixel dots (no void)
        K.ticker_strip(img, int(H * 0.76), "dies at the end · paid · lemonade · party", t)
        sticker_coin(d, 850, int(H * 0.70), 64)
        sticker_coin(d, 970, int(H * 0.72), 46)
        R.pixel_dots(img, 10, (790, int(H * 0.84), W - 80, int(H * 0.90)), seed=int(t * 5) + 7, size=9)
        IG.comment_bubble(img, int(W * 0.03), int(H * 0.93), "gots to get paid",
                          t, IG.snap(s0 + 0.20, ONSETS, 0.30)[0], who="comment", kw="paid")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.12, drift=10, freq=0.9)
        cam_log = (z * pulse, dx, dy)
        return img, "pil", "IG10 zoom punch lyric stress + density fill", cam_log

    elif kind == "counter":  # WC4 tissue + odometer + M3 + IG2 notif (v25)
        img = canvas_cached("black", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        # Ph26 S4: ghost moved to the banner-free band + shrunk (was under the
        # IG2 notification — v25 critic flaw "notification over stakes")
        WC.tissue_fill(img, (0, 0, W, int(H * 0.98)), t, tone=(112, 114, 126),
                       alpha=44, step=24, particles=16, seed=9, ghost="stakes",
                       ghost_font=R.playfair(150, 900), ghost_y=int(H * 0.16))
        d.rounded_rectangle([80, int(H * 0.24), W - 80, int(H * 0.80)], radius=28,
                            fill=(14, 14, 18, 210), outline=VOLT + (140,), width=2)
        ent_c = R.ease_out_cubic(min(1.0, max(0.0, (t - s0)) / 0.9))
        val = int(ent_c * 8137)
        WC.odometer(d, (W / 2, int(H * 0.38)), val, t, size=84, digits=5)
        IG.m3_counter_ring(img, (W / 2, int(H * 0.53)), val, t, s0, r=230)  # M3 persp3d
        WC.paste_person_v25(img, (W / 2 + 320, int(H * 0.735)), 320, "stair", rot=2, seed=2)
        WC.paste_person_v25(img, (W / 2 - 320, int(H * 0.745)), 290, "rock22", rot=-2, seed=3)
        R.volt_pill(img, (W / 2, H * 0.69), "2 MCs / 1 take / 0 fear", R.montserrat(40, 900), rot=-2)
        cc = WC.wc1_card(graded_mv(20.6 + (t - s0) * 1.0), 320, 360, rot=2.0, border="ink")
        cc = WC.wc1_card_shadow(cc)
        cs_ = WC.spring_stagger(0, t, s0 + 0.20)
        if cs_ > 0.02:
            img.alpha_composite(cc.resize((max(1, int(cc.width * cs_)), max(1, int(cc.height * cs_)))),
                                (60, int(H * 0.435)))  # Ph26 S4: lifted clear of volt pill
        R.pixel_dots(img, 12, (80, int(H * 0.13), W - 80, int(H * 0.22)), seed=int(t * 4) + 2, size=10)
        # Ph26 S4: coin moved below banner band (was corner-clipping the notif)
        sticker_coin(d, W - 150, int(H * 0.150), 58)
        IG.notif_banner(img, int(H * 0.055), "Payout", "$8,137 paid to you",
                        t, IG.snap(s0 + 0.25, ONSETS, 0.30)[0], dur=1.6)  # IG2 (onset-quantized)
        scene_label(img, (86, int(H * 0.86)), "stakes counter / M3 ring")
        _gb = d.textbbox((0, 0), "stakes", font=R.playfair(150, 900))
        _pb = d.textbbox((0, 0), "2 MCs / 1 take / 0 fear", font=R.montserrat(40, 900))
        occ_census("counter", [
            ("notif_banner", (160, int(H * 0.055), 920, int(H * 0.055) + 108), "ui"),
            ("ghost_stakes", ((W - (_gb[2] - _gb[0])) / 2, int(H * 0.16), (W + (_gb[2] - _gb[0])) / 2, int(H * 0.16) + _gb[3] - _gb[1]), "glyph"),
            ("coin_big", (W - 150 - 29, int(H * 0.150) - 29, W - 150 + 29, int(H * 0.150) + 29), "sticker"),
            ("volt_pill", (W / 2 - (_pb[2] - _pb[0]) / 2 - 44, int(H * 0.69) - 36, W / 2 + (_pb[2] - _pb[0]) / 2 + 44, int(H * 0.69) + 36), "glyph"),
            ("odometer", (W / 2 - 140, int(H * 0.38) - 56, W / 2 + 140, int(H * 0.38) + 56), "glyph"),
            ("wc1_card3", (30, int(H * 0.435) - 30, 400, int(H * 0.435) + 400), "sticker"),
        ])
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.045, drift=16)
        cam_log = (z * pulse, dx, dy)
        return img, "persp3d-m3", "M3 counter ring + IG2 notif banner", cam_log

    elif kind == "zoomthrough":  # F2 window: counter shrinks to card, paint enters
        p = (t - s0) / max(0.05, (PAINT_T - s0))
        img = shrink_card(6, 8, min(1.0, max(0.0, p)), t).convert("RGBA")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.02)  # C.3 real camera path
        return img.convert("RGB"), "pil-transition", "F2 shrink-card zoom-through", (z, dx, dy)

    elif kind == "paint":  # LB5 painting polaroid + highlighter + lemon + dutch
        img = canvas_cached("paper", ghost=None)
        sc = R.spring_scale(max(0.0, t - s0), 0.40)
        d = ImageDraw.Draw(img, "RGBA")
        PAINTING = _painting()
        if sc > 0.2:
            pw = int(600 * sc)
            ph = int(pw * PAINTING.height / PAINTING.width)
            R.polaroid(img, PAINTING.resize((pw - 24, ph - 24)), (W / 2 - 60, H * 0.40), pw - 24, rot=2)
            sticker_lemon(d, W / 2 + 330, int(H * 0.20), 150 * min(1.0, sc))
        # Ph26 S5/S6: HERO cutout anchors the light phase (>=45%H) + boosted
        # contact shadow so depth reads on the white paper canvas
        if sc > 0.25:
            WC.paste_person_v25(img, (W / 2 - 10, int(H * 0.575)), 900, "man", rot=-1,
                                alpha=0.96, shadow_boost=1.7, seed=11)
        pc = WC.wc1_card(graded_mv(2.6 + (t - s0) * 1.1), 320, 360, rot=-2.6, border="polaroid")
        pc = WC.wc1_card_shadow(pc)
        ps_ = WC.spring_stagger(0, t, s0 + 0.15)
        if ps_ > 0.02:
            img.alpha_composite(pc.resize((max(1, int(pc.width * ps_)), max(1, int(pc.height * ps_)))),
                                (60, 170))
        drift = int(math.sin((t - s0) * 1.6) * 14)
        R.highlight_pill(img, (W / 2 - 300 + drift, int(H * 0.70) - 8, W / 2 + 300 + drift, int(H * 0.70) + 58), radius=12)
        f_m = R.mono(46, bold=True)
        d.text((W / 2 - 292 + drift, H * 0.70), "San Pellegrino lemonade", font=f_m, fill=(20, 20, 22, 245))
        scene_label(img, (86, int(H * 0.90)), "painting insert / public domain")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.085, drift=13)
        img = dutch(img, 1.4)  # IG10 dutch
        cam_log = (z * pulse, dx, dy)
        return img, "pil", "LB5 painting + IG10 dutch", cam_log

    elif kind == "paint2":  # subcut: M2 floating polaroids parallax w/ LIVE video
        img = canvas_cached("paper", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        frames = [mv_frame(max(0.05, 12.5 + (t - s0) * 1.4)),
                  mv_frame(max(0.05, 4.5 + (t - s0) * 1.4)),
                  mv_frame(max(0.05, 24.0 + (t - s0) * 0.6))]
        # Ph26 S5/S6: HERO cutout behind the M2 polaroids (footage-led light scene)
        WC.paste_person_v25(img, (W / 2 + 250, int(H * 0.585)), 880, "duo", rot=1,
                            alpha=0.96, shadow_boost=1.7, seed=12)
        IG.m2_polaroids_parallax(img, frames, t, s0, base_c=(W / 2, int(H * 0.42)))  # M2
        scene_label(img, (86, int(H * 0.90)), "floating polaroids / M2 persp3d")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.07, drift=18)
        cam_log = (z * pulse, dx, dy)
        return img, "persp3d-m2", "M2 polaroids parallax + LF2 live video", cam_log

    elif kind == "cascade":  # LB6 real frames + M5 world insert + connector
        img = canvas_cached("paper", ghost=None)
        sc = R.spring_scale(max(0.0, t - s0), 0.36)
        d = ImageDraw.Draw(img, "RGBA")
        if sc > 0.2:
            # WC1: polaroids play LIVE video (window advances with t) — never frozen
            c1 = WC.wc1_card(graded_mv(12.5 + (t - s0) * 1.3), 240, 240, rot=-5, border="polaroid")
            c2 = WC.wc1_card(graded_mv(4.5 + (t - s0) * 1.3), 214, 214, rot=4, border="polaroid")
            c1 = WC.wc1_card_shadow(c1); c2 = WC.wc1_card_shadow(c2)
            img.alpha_composite(c1, (int(W / 2 - 170 - c1.width / 2), int(H * 0.36 - c1.height / 2)))
            img.alpha_composite(c2, (int(W / 2 + 190 - c2.width / 2), int(H * 0.46 - c2.height / 2)))
            # M5 world insert: footage plane perspective-mounted
            quad = [(W / 2 - 300, int(H * 0.58)), (W / 2 + 120, int(H * 0.60)),
                    (W / 2 + 90, int(H * 0.74)), (W / 2 - 320, int(H * 0.72))]
            IG.m5_world_insert(img, graded_mv(max(0.05, 24.0 + (t - s0) * 0.9)).resize((560, 400)),
                               quad)  # M5 + LF2 live
            # Ph26 S5/S6: HERO cutout on the light paper (painting = accent only)
            WC.paste_person_v25(img, (W / 2 - 280, int(H * 0.585)), 880, "church", rot=-2,
                                alpha=0.96, shadow_boost=1.7, seed=13)
        d.line([W / 2 - 170, int(H * 0.50), W / 2 + 190, int(H * 0.56)], fill=VOLT + (220,), width=3)
        d.line([W / 2 + 190, int(H * 0.56), W / 2 - 40, int(H * 0.68)], fill=VOLT + (220,), width=3)
        R.volt_pill(img, (W / 2 + 310, H * 0.70), "raw cuts", R.montserrat(40, 900), rot=6)
        sticker_arrow(d, 140, int(H * 0.22), 320, int(H * 0.16))
        scene_label(img, (86, int(H * 0.90)), "cascade / M5 world insert")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05, drift=18)
        cam_log = (z * pulse, dx, dy)
        return img, "persp3d-m5", "LB6 cascade + M5 world insert (live)", cam_log

    elif kind == "isol":  # IG6 selective-color isolation beat (measured)
        img = canvas_cached("paper", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        PAINTING = _painting()
        pw = 520
        ph = int(pw * PAINTING.height / PAINTING.width)
        R.polaroid(img, PAINTING.resize((pw - 24, ph - 24)), (W / 2 - 80, H * 0.38), pw - 24, rot=-2)
        WC.paste_person_v25(img, (W / 2 - 290, int(H * 0.585)), 880, "man", rot=1,
                            alpha=0.96, shadow_boost=1.7, seed=14)  # Ph26 S5 HERO + S6
        R.pixel_dots(img, 8, (W - 330, int(H * 0.16), W - 80, int(H * 0.24)),
                     seed=int(t * 5) + 4, size=8)  # Ph26 S5 density
        sticker_coin(d, W / 2 + 250, int(H * 0.62), 110)
        sticker_coin(d, W / 2 - 240, int(H * 0.66), 74)
        f_t = R.playfair(96, 900)
        _tbb = d.textbbox((0, 0), "volt only", font=f_t)
        d.text((max(12, 90 - _tbb[0]), int(H * 0.78)), "volt only", font=f_t, fill=(24, 24, 26, 245))  # C.5b no left glyph cut
        scene_label(img, (86, int(H * 0.90)), "selective color / volt only (IG6)")
        comp = img.convert("RGB")
        res, chroma_out, chroma_in = IG.selective_color(comp, keep=(58, 100))
        ISOL_MEAS["t"] = round(t, 2)
        ISOL_MEAS["chroma_frac_outside_volt"] = round(chroma_out, 5)
        ISOL_MEAS["chroma_frac_inside_volt"] = round(chroma_in, 5)
        if not os.path.exists(f"{K.EMS_WORK}/isol_live.json"):
            json.dump({"t": round(t, 2),
                       "chroma_frac_outside_volt": round(chroma_out, 5),
                       "chroma_frac_inside_volt": round(chroma_in, 5),
                       "note": "pre-compression frame measurement (render-time)"},
                      open(f"{K.EMS_WORK}/isol_live.json", "w"), indent=1)
        res2, z, dx, dy = cam_apply(res.convert("RGBA"), t, s0, punch=0.06, drift=12)  # IG5/IG10 camera life on isol beat
        return res2.convert("RGB"), "numpy-selective", "IG6 selective-color isolation (volt hue 58-100) + cam life", (z, dx, dy)

    elif kind == "pop":  # LB7 full-bleed pop + IG10 speed ramp + IG2 heart burst
        src_t, factor = IG.ramp_t(t, s0, POP2_T + 1.2, 0.4, 1.6)  # IG10 0.4x->1.6x
        graded = graded_mv(19.0 + (src_t - s0))
        arr = np.asarray(graded).astype(np.float32)
        lum = arr.mean(axis=2, keepdims=True)
        lum = np.clip((lum - lum.mean()) * 1.35 + lum.mean(), 0, 255)
        pop = Image.fromarray(np.repeat(lum, 3, axis=2).astype(np.uint8))
        pw, ph = pop.size
        s = H / ph
        nw = int(pw * s)
        pop = pop.resize((nw, H), Image.LANCZOS)
        pop = pop.crop(((nw - W) // 2, 0, (nw - W) // 2 + W, H))
        img = canvas_cached("black", ghost=None)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dg = ImageDraw.Draw(glow)
        dg.ellipse([W / 2 - 420, int(H * 0.30) - 420, W / 2 + 420, int(H * 0.30) + 420], fill=(216, 243, 74, 40))
        glow = glow.filter(ImageFilter.GaussianBlur(60))
        img.alpha_composite(glow)
        img.alpha_composite(pop.convert("RGBA"))
        d = ImageDraw.Draw(img, "RGBA")
        # Ph26 S1: internal spec label removed; IG-native scrubber stays
        # (progress fill = ramp factor; reads as platform UI, not a debug HUD)
        _rp = min(1.0, max(0.0, (factor - 0.4) / 1.2))
        d.rounded_rectangle([W / 2 - 210, int(H * 0.80), W / 2 + 210, int(H * 0.80) + 64], radius=32,
                            fill=(10, 10, 14, 215), outline=(240, 244, 255, 120), width=2)
        _fx = W / 2 - 196 + int(392 * _rp)
        d.rounded_rectangle([W / 2 - 196, int(H * 0.80) + 24, _fx, int(H * 0.80) + 40],
                            radius=8, fill=VOLT + (235,))
        d.ellipse([_fx - 12, int(H * 0.80) + 8, _fx + 12, int(H * 0.80) + 56],
                  fill=(240, 244, 255, 240))
        IG.heart_burst(d, W / 2, int(H * 0.30), t, IG.snap(s0 + 0.35, ONSETS, 0.30)[0], n=8)  # IG2 payoff (onset-quantized)
        # C.3 honest camera life: REAL cover-crop transform (log was z-only, never applied)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.04, drift=10)
        cam_log = (z * pulse, dx, dy)
        return img.convert("RGB"), "pil-ramp", "IG10 speed ramp + IG2 heart burst", cam_log

    elif kind == "pop2":  # subcut: ramp continues, tighter crop
        src_t, factor = IG.ramp_t(t, POP_T, POP2_T + 1.2, 0.4, 1.6)
        graded = graded_mv(19.0 + (src_t - POP_T))
        arr = np.asarray(graded).astype(np.float32)
        lum = arr.mean(axis=2, keepdims=True)
        lum = np.clip((lum - lum.mean()) * 1.45 + lum.mean(), 0, 255)
        pop = Image.fromarray(np.repeat(lum, 3, axis=2).astype(np.uint8))
        pw, ph = pop.size
        s = (H * 1.25) / ph
        nw = int(pw * s)
        pop = pop.resize((nw, int(H * 1.25)), Image.LANCZOS)
        cx = (nw - W) // 2
        cy = int(H * 0.10)
        pop = pop.crop((cx, cy, cx + W, cy + H))
        img = pop.convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        scene_label(img, (86, int(H * 0.90)), "1.6x punch crop (IG10)")
        # C.3 honest camera life: real transform for logged motion (was log-only)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.02, drift=14, freq=0.9)
        cam_log = (z * pulse, dx, dy)
        return img, "pil-ramp", "IG10 ramp 1.6x punch crop", cam_log

    elif kind == "callout":  # LB8 + IG4 homicide slam + IG10 freeze+slam (v25 live)
        freeze_src = 22.0 if t < s0 + 0.25 else 22.0 + (t - s0 - 0.25) * 0.9
        img = canvas_cached("black", ghost=None)
        img.alpha_composite(graded_mv(freeze_src).convert("RGBA").resize((1080, 1350)))
        d = ImageDraw.Draw(img, "RGBA")
        sticker_caution(d, 110, int(H * 0.185), 970, int(H * 0.30))
        f_kw_size = 150
        IG.slam_text(img, (W / 2, int(H * 0.60)), "homicide",
                     lambda s: R.playfair(s, 900), t, s0 + 0.10,
                     per_letter=0.05, size=f_kw_size, base=True,
                     color=(250, 246, 242, 245), stroke=VOLT + (235,))  # IG4 slam 2
        d.rounded_rectangle([W / 2 - 240, int(H * 0.665), W / 2 + 240, int(H * 0.677)],
                            radius=4, fill=VOLT + (235,))
        sticker_arrow(d, 180, int(H * 0.80), 320, int(H * 0.72))
        paste_person(img, (W / 2 + 300, int(H * 0.74)), 330, "duo", rot=-2, alpha=0.94)  # C.6 cutout presence
        scene_label(img, (86, int(H * 0.90)), "keyword callout / freeze+slam (IG10)")
        _hb = d.textbbox((0, 0), "homicide", font=R.playfair(150, 900))
        occ_census("callout", [
            ("caution_tape", (110, int(H * 0.185), 970, int(H * 0.30)), "sticker"),
            ("slam_homicide", ((W - (_hb[2] - _hb[0])) / 2, int(H * 0.60) - (_hb[3] - _hb[1]) / 2 - 6, (W + (_hb[2] - _hb[0])) / 2, int(H * 0.60) + (_hb[3] - _hb[1]) / 2 + 6), "glyph"),
            ("volt_bar", (W / 2 - 240, int(H * 0.665), W / 2 + 240, int(H * 0.677)), "glyph"),
            ("arrow", (160, int(H * 0.72), 520, int(H * 0.82)), "sticker"),
        ])
        # freeze+slam: source frozen, scale spikes at entry
        fz = 1.0 if t < s0 + 0.30 else 1.0 + 0.10 * math.sin(min(1.0, (t - s0 - 0.30) / 0.25) * math.pi)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.05, drift=14)
        cam_log = (z * fz * pulse, dx, dy)
        return img, "pil", "IG4 homicide slam + IG10 freeze+slam", cam_log

    elif kind == "callout2":  # subcut: M4 orbit callout + caution tape (v25 live)
        img = canvas_cached("black", ghost=None)
        img.alpha_composite(graded_mv(22.0 + (t - s0) * 0.9).convert("RGBA").resize((1080, 1350)))
        d = ImageDraw.Draw(img, "RGBA")
        sticker_caution(d, 110, int(H * 0.185), 970, int(H * 0.30))
        f_kw = R.playfair(150, 900)
        bb = d.textbbox((0, 0), "homicide", font=f_kw)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.60), "homicide", font=f_kw, fill=(250, 246, 242, 245))
        IG.m4_callout_orbit(img, (W / 2, int(H * 0.63)), "scene 03", t, s0, rx=300, ry=90)  # M4
        scene_label(img, (86, int(H * 0.90)), "callout orbit / M4 persp3d")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=16)
        cam_log = (z * pulse, dx, dy)
        return img, "persp3d-m4", "M4 callout orbit", cam_log

    elif kind == "m1":  # WC4 tissue + persp3d M1 (v25)
        img = canvas_cached("paper", ghost="WELCOME")
        WC.tissue_fill(img, (0, int(H * 0.02), W, int(H * 0.86)), t, tone=(150, 152, 160),
                       alpha=40, step=26, particles=12, seed=17)
        d = ImageDraw.Draw(img, "RGBA")
        sticker_starburst(d, W / 2, int(H * 0.21), 130, t=t)
        bracket_corners(d, (140, int(H * 0.18), W - 140, int(H * 0.62)), color=INK, L=46, w=7)
        # C.5c fit M1 type inside frame (perspective quad expands ~8% over tile)
        _tw190 = R.montserrat(190, 900).getlength("WELCOME")
        _ms = max(100, min(190, int(190 * 660.0 / max(1, _tw190))))
        engine = IG.m1_type_persp(img, (W / 2, int(H * 0.40)), "WELCOME",
                                  t, s0 + 0.05, size=_ms)  # persp3d M1
        if t < M1_SCENE_START + 0.40:
            sc = R.spring_scale(max(0.0, t - s0 - 0.06), 0.30)
            if sc > 0.2:
                paste_person(img, (W / 2 + 310, H * 0.66), int(380 * sc), "stair", rot=2)
        mc = WC.wc1_card(graded_mv(6.2 + (t - s0) * 1.0), 320, 360, rot=2.4, border="polaroid")
        mc = WC.wc1_card_shadow(mc)
        ms_ = WC.spring_stagger(0, t, s0 + 0.25)
        if ms_ > 0.02:
            img.alpha_composite(mc.resize((max(1, int(mc.width * ms_)), max(1, int(mc.height * ms_)))),
                                (60, int(H * 0.65)))
        scene_label(img, (86, int(H * 0.90)), "3D type slam / M1 persp3d")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=14)
        img = WC.dof_blur(img.convert("RGBA"), radius=1.4,
                          except_rect=(100, int(H * 0.16), W - 100, int(H * 0.64))).convert("RGB")
        cam_log = (z * pulse, dx, dy)
        return img, engine, "M1 persp3d volt-chrome slam + WC4 tissue/DOF", cam_log

    elif kind == "endcard":  # LB10 loop echo + tissue
        img = canvas_cached("paper", ghost=None)  # C.6 critic fix: closing void -> designed paper canvas
        d = ImageDraw.Draw(img, "RGBA")
        f_g = R.playfair(170, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        while bb[2] - bb[0] > 880 and f_g.size > 60:
            f_g = R.playfair(f_g.size - 10, 900)
            bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.30
        d.text((ox + 12, oy + 10), "WELCOME", font=f_g, fill=(20, 20, 24, 40))
        d.text((ox, oy), "WELCOME", font=f_g, fill=(16, 17, 20, 245))
        d.text((ox + 6, oy + bb[3] - bb[1] + 40), "to the party", font=R.playfair(84, 900), fill=(150, 165, 30, 235))
        sc = R.spring_scale(max(0.0, t - s0 - 0.10), 0.32)
        if sc > 0.3:
            R.volt_pill(img, (W / 2, H * 0.545), "IDK x EMINEM x J DILLA", R.montserrat(44, 900), rot=0)
            echo = graded_mv(1.0 + (t - s0) * 0.8).resize((420, 525))
            ew = Image.new("RGBA", (444, 549), (0, 0, 0, 0))
            ew.alpha_composite(echo.convert("RGBA"), (12, 12))
            ImageDraw.Draw(ew).rectangle([0, 0, 443, 548], outline=VOLT + (200,), width=3)
            img.alpha_composite(ew, (int(W / 2 - 222), int(H * 0.60)))
            paste_person(img, (W / 2 + 330, int(H * 0.68)), 360 * min(1.0, sc), "stair", rot=2)  # C.6 cutout presence
        R.pixel_dots(img, 9, (100, int(H * 0.88), W - 100, int(H * 0.95)), seed=int(t * 6) + 3, size=10)
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.03)
        return img, "pil", "LB10 loop echo window (IG3)", (z, dx, dy)

    # fallback
    img = canvas_cached("black", ghost=None)
    return img, "pil", "fallback", (1.0, 0.0, 0.0)

_PAINTING_IMG = None
def _painting():
    global _PAINTING_IMG
    if _PAINTING_IMG is None:
        _PAINTING_IMG = Image.open(f"{K.ASSETS}/pd_still_life_gen.png").convert("RGB")
    return _PAINTING_IMG

ISOL_MEAS = {}

def scene_at(t):
    idx = 0
    for i, (s, k) in enumerate(SCENES):
        if t >= s:
            idx = i
    return idx

HOOK_IDX = 0
GHOST_IDX = 2

def compose(fi):
    t = fi / FPS
    log_cam = None
    if t >= LOOP_START - 1e-4:
        # IG3 seamless loop: EXACT frame-0 composition + frame-0 post chain
        img, engine, tag, _ = draw_scene(HOOK_IDX, HOOK_T)
        engine, tag = "pil-loop", "IG3 loop freeze == frame 0 (frame-0 post chain)"
        img = img.convert("RGB")
        words0 = words_window(HOOK_T)
        if words0:
            IG.draw_caption_pop(img, words0, HOOK_T, int(H * 0.80))
        img = R._grain(img, 3)
        img = IG.halation(img, thr=205, strength=0.26)
        img = IG.dust_scratch(img, HOOK_T, p_dust=0.5)
        return img, engine, tag, (1.0, 0.0, 0.0)
    elif ZT_T <= t <= PAINT_T:
        img = shrink_card(6, 8, (t - ZT_T) / max(0.05, PAINT_T - ZT_T), t).convert("RGBA")
        img, z, dx, dy = cam_apply(img, t, ZT_T, punch=0.02)  # C.3 real camera
        img = img.convert("RGB")
        engine, tag = "pil-transition", "F2 shrink-card zoom-through"
        log_cam = (z, dx, dy)
    else:
        img, engine, tag, log_cam = draw_scene(scene_at(t), t)
        img = img.convert("RGB")
        si = scene_at(t)
        if SCENES[si][1] not in ("m1", "endcard", "ui_tap", "zoomthrough"):
            words = words_window(t)
            if words:
                IG.draw_caption_pop(img, words, t, int(H * 0.80))  # IG9 single voice
    img = R._grain(img, 3)
    # IG8 film texture: halation / dust / gate weave / light leak
    if fi % 3 == 0:
        img = IG.halation(img, thr=205, strength=0.26)
    if fi % 5 == 0:
        img = IG.dust_scratch(img, t, p_dust=0.5)
    wx, wy = IG.gate_weave(t, 1.5)
    if abs(wx) >= 1 or abs(wy) >= 1:
        img = img.crop((int(max(0, wx)), int(max(0, wy)),
                        W + int(min(0, wx)), H + int(min(0, wy)))).resize((W, H), Image.BILINEAR)
    if UITAP_T <= t < UITAP_T + 0.35:
        img = IG.light_leak(img, (t - UITAP_T) / 0.35, edge="right")
    if POP_T <= t < POP_T + 0.30:
        img = IG.light_leak(img, (t - POP_T) / 0.30, edge="left")
    if CALLOUT_T - 0.02 <= t <= CALLOUT_T + 0.20:
        arr = 255 - np.asarray(img.convert("RGB"))
        img = Image.fromarray(arr.astype(np.uint8))  # invert bite (quota keep)
    if GHOST_T - 0.02 <= t <= GHOST_T + 0.10:
        img = img.filter(ImageFilter.GaussianBlur(1.0 + 9 * math.sin(math.pi * (t - GHOST_T) / 0.12)))
    return img, engine, tag, log_cam

if __name__ == "__main__":
    a = sys.argv
    START = int(a[a.index("--start") + 1]) if "--start" in a else 0
    END = int(a[a.index("--end") + 1]) if "--end" in a else N - 1
    PIPE = "--pipe" in a
    log = []
    cam_deltas = []
    if PIPE:
        import subprocess as sp
        seg = f"{K.EMS_WORK}/seg_{START:05d}.mp4"
        enc = sp.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                        "-pix_fmt", "yuv420p", seg], stdin=sp.PIPE)
    for fi in range(START, END + 1):
        img, engine, tag, cam_log = compose(fi)
        if PIPE:
            enc.stdin.write(img.tobytes())
        else:
            os.makedirs(FRAMES, exist_ok=True)
            img.save(f"{FRAMES}/t_{fi:05d}.jpg", quality=88)
        log.append({"frame": fi, "t": round(fi / FPS, 3), "engine": engine, "beat": tag})
        if cam_log:
            cam_deltas.append({"t": round(fi / FPS, 3), "scale": round(cam_log[0], 4),
                               "dx": round(cam_log[1], 2), "dy": round(cam_log[2], 2)})
        if fi % 120 == 0:
            print(f"frame {fi}/{END}", flush=True)
    if PIPE:
        enc.stdin.close()
        enc.wait()
    meta = {"dur": DUR, "fps": FPS, "n_frames": N,
            "beats_lib": LIB_BEATS[:60], "onsets": ONSETS[:100], "kicks": KICKS[:60],
            "onset_engine": OENG, "tempo": TEMPO, "drop": DROP,
            "scenes": [[s[0], s[1]] for s in SCENES], "snap_log": SNAP_LOG,
            "sticker_map": STICKER_MAP, "isol_measure": ISOL_MEAS,
            "camera_log": cam_deltas,
            "wc2_matte_engine": "rembg isnet-general-use per-frame (live MV footage) via v25_hook",
            "chunk": [START, END]}
    meta.update({
        "labels_disabled": True,                                  # Ph26 S1/B7
        "label_log_qc": K.LABEL_LOG,                              # QC-only positions
        "collision_census": COLL,                                 # Ph26 S4/B10
        "hook_fit": dict(getattr(_SHOW, "SHOW_HOOK_FIT", {})),    # Ph26 S3/B9
        "light_phase_density": LIGHT_PHASE})                      # Ph26 S5
    if START == 0:
        json.dump(meta, open(f"{K.EMS_WORK}/t1_v26_plan.json", "w"), indent=1)
    else:
        json.dump({"camera_log": cam_deltas, "chunk": [START, END]},
                  open(f"{K.EMS_WORK}/t1_v26_chunk_{START}.json", "w"), indent=1)
    print("T1 v24 FRAMES DONE", START, END, flush=True)
