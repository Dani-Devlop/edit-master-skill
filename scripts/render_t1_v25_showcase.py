#!/usr/bin/env python3
"""T-1 v25 SHOWCASE — 10.0s (hook 0-4s + one verse beat 4-10s), 1080x1920@30.
Phase 25: FZ3 scope — B1-B6 binary acceptance + numeric gates BEFORE full 30s.
  WC2 occlusion hook: full-bleed LIVE MV footage -> giant volt type ->
  per-frame performer alpha (rembg/isnet) -> brackets/artist-tape/captions
  WC1 video-in-card: live MV frames in bordered cards (crop-to-window-aspect),
  spring stagger — NEVER frozen
  WC3 cutout depth: contact shadow + 1.02x parallax + rim light (paste_person_v25)
  WC4 tissue fill: halftone+ghost+gradient+particles (counter/listicle bands)
  IG1 beat-lock: every scene start snapped to librosa onsets; kick pulse ±3%
  IG2 pseudo-UI: cursor tap -> next scene / comment bubble / payout notif
  IG3 seamless loop: last 0.45s = exact frame-0 composition (gate >= 0.9)
  IG4 kinetic slams: WELCOME + DIES per-letter stagger, squash/stretch, chroma
  IG5 idle micro-motion: monotone cam + wobble + ticker + odometer + particles
  IG6 selective color: volt-only accents; isolation micro-beat measured (counter)
  IG7 tight pacing: median interval <= 2.0s, max <= 2.5s (no hold > 2.5s)
  IG8 film texture: grade+grain+halation+dust+gate-weave+light-leak
  IG9 captions: draw_caption_pop karaoke pill, safe-zone; COVER = frame 0
  IG10 camera: punch-in, whip, dutch, zoom-punch, freeze+slam, speed ramp,
      shrink-card, match-cut (>= 6 moves)
TEMP /tmp/ems-work/p25. Engines: pil/numpy canvas+type, persp3d (M2/M3),
rembg-isnet (WC2 mattes), ffmpeg (assemble)."""
import os, sys, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{_SK}/components")
sys.path.insert(0, f"{_SK}/scripts")
import renderlib as R
from renderlib import VOLT, INK, listicle_bars, volt_pill
import ig24kit as IG
IG.bind_renderlib(R)
import v22kit as K
from v22kit import (W, H, FPS, canvas, cam_apply, sticker_hourglass, sticker_coin,
                    sticker_appicons, bracket_corners, scene_label, ghost_word,
                    ticker_strip)
import wc25kit as WC
WC.bind_renderlib(K)
K.load_persons()
# hybrid human-polish (B4 stop-loss round): brighten dark B&W cutouts so depth
# cues (shadow/rim/separation) read on dark footage — alpha preserved
for _nm in ("man", "stair", "rock22", "duo", "church", "agent"):
    WC.lift_person_v25(_nm)

# Ph26 S1/B7: DELIVERABLE frames — internal scene labels disabled (QC-logged)
K.LABELS_ENABLED = False
# Ph26 S3/B9: hook-type fit evidence (measured, logged to plan)
SHOW_HOOK_FIT = {}

P25 = os.environ.get("EMS_WORK", K.EMS_WORK)
FRAMES = f"{P25}/showcase_frames"
os.makedirs(FRAMES, exist_ok=True)
DUR = 10.0
N = int(FPS * DUR)

# ---------------- IG1 beat grid ----------------
ONSETS, LIB_BEATS, KICKS, TEMPO, OENG = IG.onset_grid(
    f"{K.ASSETS}/target_audio.wav", DUR + 0.6)
SNAP_LOG = []
def snap(t):
    st, d = IG.snap(t, ONSETS, 0.30)
    if st == t:
        b = min(ONSETS, key=lambda o: abs(o - t))
        st, d = round(b, 3), round(abs(b - t), 3)
    SNAP_LOG.append({"plan": round(float(t), 3), "snapped": st, "delta": d})
    return st

PLANNED = [(0.00, "hook_car"), (1.50, "hook_duo"), (2.80, "hook_duo2"),
           (4.00, "ui_tap"), (5.00, "listicle"), (7.00, "counter"),
           (8.60, "m2_live"), (9.55, "loop")]
SCENES = [(snap(s), k) for (s, k) in PLANNED]
ST = {k: t for (t, k) in SCENES}
IDX = {k: i for i, (t, k) in enumerate(SCENES)}
UI_TAP_T, LIST_T, COUNTER_T, M2_T, LOOP_T = (ST["ui_tap"], ST["listicle"],
                                             ST["counter"], ST["m2_live"], ST["loop"])
print(f"IG1 onsets[{OENG}] {len(ONSETS)} | kicks {len(KICKS)} | tempo {TEMPO}", flush=True)
print("SCENES:", SCENES, flush=True)

STICKER_MAP = {
    "party": "confetti burst (volt/white only) + app-icons",
    "everybody": "arrow + volt heart accents (m2)",
    "dies at the end": "hourglass (animated sand)",
    "paid": "coin cascade + payout notification (counter)",
    "raw cuts": "live-video polaroid cascade + connector (m2)",
}

# ---------------- lyric timing (whisper SEGS, verified p21/p22) ----------------
SEGS = [(0.00, 4.32, "Welcome to the party where everybody dies at the end"),
        (4.32, 5.44, "Move your body"),
        (5.44, 8.32, "this is about to beat on homicide scene"),
        (8.32, 10.00, "I think you walk not me we're not screened")]
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

# ---------------- F4 grade (B&W + volt drawn after) ----------------
def grade(img):
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
    lum = np.clip((lum - 0.5) * 1.16 + 0.5, 0, 1)
    lum = np.clip(lum ** 1.06, 0, 1)
    out = Image.fromarray((np.stack([lum] * 3, axis=-1) * 255).astype(np.uint8))
    out = R._grain(out, 7)
    out = R._vignette(out, 0.30)
    return out.convert("RGB")

def dutch(img, deg):
    if abs(deg) < 0.15:
        return img
    return img.rotate(deg, resample=Image.BICUBIC, fillcolor=(8, 8, 10, 255))

_CANVAS = {}
def canvas_cached(kind, ghost=None):
    key = (kind, ghost)
    if key not in _CANVAS:
        _CANVAS[key] = canvas(kind, ghost=ghost)
    return _CANVAS[key].copy()

def confetti_v(d, cx, cy, spread, t, rng_seed=7):
    """IG6-disciplined confetti: volt + white only (no off-world yellow)"""
    rng = np.random.default_rng(rng_seed)
    colors = [VOLT + (235,), (240, 242, 246, 225)]
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        r = spread * rng.uniform(0.25, 1.0)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        s = rng.uniform(5, 12)
        rot = rng.uniform(0, math.pi)
        dx, dy = s * math.cos(rot), s * math.sin(rot)
        d.line([(x - dx, y - dy), (x + dx, y + dy)],
               fill=colors[i % 2], width=max(3, int(s * 0.4)))

# ---------------- WC2 hook layers ----------------
def draw_hook(t, src_start, scene_t0, rate=1.0, slam_word="WELCOME", slam_t0=None,
              sub_line=None, hourglass=False, appicons=False, confetti=True,
              ghost_outline=None):
    s0 = scene_t0
    src_t = max(0.04, src_start + (t - s0) * rate)
    footage, perf = WC.hook_footage_perf(src_t, grade)
    img = Image.new("RGBA", (W, H), (8, 8, 10, 255))
    img.alpha_composite(footage.convert("RGBA"))
    d = ImageDraw.Draw(img, "RGBA")
    pulse = IG.kick_pulse(t, KICKS, 0.03)
    # ---- giant volt type layer (BEHIND performer head) ----
    if slam_word == "WELCOME":
        # type overlaps the performer head band (~H*0.47 in the car shot) so the
        # alpha occlusion is VISIBLE: head/chest covers the bottom of the type
        # Ph26 S3/B9: hook word FULLY legible <= 0.92W INCLUDING the camera
        # envelope (punch-in crop + dutch + gate-weave eat up to ~7% per side);
        # 0.84W pre-camera leaves measured clearance. Fit logged for B9.
        size_big = 210
        while R.montserrat(size_big, 900).getlength("WELCOME") > int(W * 0.84) and size_big > 90:
            size_big -= 8
        IG.slam_text(img, (W / 2, int(H * 0.40)), "WELCOME",
                     lambda s: R.montserrat(s, 900), t,
                     slam_t0 if slam_t0 is not None else s0,
                     per_letter=0.045, size=size_big, base=True)
        tw = R.montserrat(size_big, 900).getlength("WELCOME")
        SHOW_HOOK_FIT.update({"word": "WELCOME", "type_width_px": int(tw),
                              "ratio_plan": round(float(tw) / W, 3), "bar_max": 0.92,
                              "note": "pre-camera plan width; B9 measures decoded frames"})
        bracket_corners(d, (W / 2 - tw / 2 - 40, int(H * 0.31),
                            W / 2 + tw / 2 + 40, int(H * 0.50)), color=INK, L=40, w=6)
        volt_pill(img, (W / 2, H * 0.265), "IDK x EMINEM x J DILLA",
                  R.montserrat(44, 900), rot=-3)
        if confetti:
            confetti_v(d, W / 2, int(H * 0.40), 230 * min(1.0, (t - s0) / 0.34 + 0.2), t)
    else:
        # DIES slam: fit <=1020px so the word reads WIDER than the duo bodies —
        # the heads occlude the middle, letters stay readable on both sides
        size_big = 240
        while R.montserrat(size_big, 900).getlength("DIES") > int(W * 0.84) and size_big > 90:
            size_big -= 8
        IG.slam_text(img, (W / 2, int(H * 0.42)), "DIES",
                     lambda s: R.montserrat(s, 900), t,
                     slam_t0 if slam_t0 is not None else t,
                     per_letter=0.05, size=size_big, base=True,
                     stroke=(10, 10, 12, 235))
        f2 = R.playfair(92, 900)
        bb = d.textbbox((0, 0), "at the end", font=f2)
        d.text(((W - bb[2] + bb[0]) / 2, int(H * 0.52)), "at the end",
               font=f2, fill=(246, 246, 242, 240))
        if ghost_outline:
            # P0 ghost type: fit inside frame (NO glyph cut — G7 discipline)
            f_g = R.playfair(200, 700)
            while d.textbbox((0, 0), ghost_outline, font=f_g)[2] > 1030 and f_g.size > 60:
                f_g = R.playfair(f_g.size - 10, 700)
            bb = d.textbbox((0, 0), ghost_outline, font=f_g)
            d.text(((W - bb[2] + bb[0]) / 2, 130), ghost_outline,
                   font=f_g, fill=(255, 255, 255, 36))
    # ---- WC2 performer alpha ON TOP of type (occlusion: head covers type) ----
    if perf is not None:
        img.alpha_composite(perf)
    if hourglass:
        sticker_hourglass(d, W - 170, int(H * 0.655), 150, t)
    if appicons:
        sticker_appicons(d, W / 2, int(H * 0.875), 52, 3)
    scene_label(img, (86, int(H * 0.685)), "hook / full-bleed live occlusion (WC2)")
    img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=18)
    img = dutch(img, 1.2 * max(0.0, 1 - (t - s0) / 0.4))
    return img.convert("RGB"), "pil-wc2", "WC2 full-bleed occlusion + IG4 slam", (z * pulse, dx, dy)

# ---------------- ui_tap: shrink-card zoom-through + cursor (IG2) ----------------
def shrink_card(prev_idx, next_idx, p, t_abs, tap_fx=False):
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    nxt, _, _, _ = draw_scene(next_idx, t_abs)
    nxt = nxt.convert("RGBA")
    ns = 0.80 + 0.20 * p
    nw, nh = int(W * ns), int(H * ns)
    base.alpha_composite(nxt.resize((nw, nh), Image.BILINEAR), ((W - nw) // 2, (H - nh) // 2))
    prv, _, _, _ = draw_scene(prev_idx, SCENES[prev_idx][0])
    prv = prv.convert("RGBA")
    ps = 0.82 - 0.40 * p
    rot = -8.0 * p + IG.rot_jitter(t_abs, 3, 1.4)
    pw, ph = int(W * ps), int(H * ps)
    p2 = prv.resize((pw, ph), Image.BILINEAR).rotate(rot, expand=True, resample=Image.BICUBIC)
    card = Image.new("RGBA", (p2.width + 24, p2.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=18,
                                           fill=(10, 10, 12, 255), outline=VOLT + (220,), width=3)
    card.alpha_composite(p2, (12, 12))
    card = WC.wc1_card_shadow(card, blur=14, alpha=110)
    cx, cy = W / 2, H * 0.44
    px = int(min(max(6, cx - card.width / 2), W - card.width - 6))
    py = int(min(max(6, cy - card.height / 2), H - card.height - 6))
    assert 0 <= px and px + card.width <= W and 0 <= py and py + card.height <= H, "card out of bounds"
    base.alpha_composite(card, (px, py))
    # match-cut seed: volt bar on the card bottom edge (continues as listicle spine)
    d = ImageDraw.Draw(base, "RGBA")
    d.rectangle([px + 12, py + card.height - 26, px + card.width - 12, py + card.height - 20],
                fill=VOLT + (200,))
    if tap_fx:
        IG.cursor_tap(base, px + card.width // 2, py + card.height // 2, t_abs, UI_TAP_T + 0.42)
    return base

# ---------------- scene drawers ----------------
def draw_scene(idx, t):
    s0, kind = SCENES[idx]
    ent = R.spring_scale(max(0.0, t - s0), 0.34)
    pulse = IG.kick_pulse(t, KICKS, 0.03)

    if kind == "hook_car":
        return draw_hook(t, src_start=0.30, scene_t0=s0, rate=0.95, slam_word="WELCOME",
                         slam_t0=s0, confetti=True, appicons=False)

    elif kind == "hook_duo":
        return draw_hook(t, src_start=1.55, scene_t0=s0, rate=1.0, slam_word="DIES",
                         slam_t0=s0, hourglass=True, ghost_outline="everybody dies at the end")

    elif kind == "hook_duo2":  # jump punch-in + ghost outline (IG10 zoom punch)
        img, eng, tag, cam = draw_hook(t, src_start=1.55, scene_t0=s0, rate=1.0,
                                       slam_word="DIES",
                                       slam_t0=ST["hook_duo"], hourglass=True,
                                       ghost_outline="everybody dies at the end")
        img2, z, dx, dy = cam_apply(img.convert("RGBA"), t, s0, punch=0.16, drift=14, freq=0.9)
        scene_label(img2, (86, int(H * 0.72)), "jump cut / zoom punch (IG10)")
        return img2.convert("RGB"), "pil-wc2", "IG10 zoom punch jump-cut", (z * pulse, dx, dy)

    elif kind == "ui_tap":
        p = min(1.0, (t - s0) / 0.55)
        img = shrink_card(IDX["hook_duo2"], IDX["listicle"], p, t, tap_fx=True)
        scene_label(img, (86, int(H * 0.92)), "tap -> next scene (IG2)")
        img, z, dx, dy = cam_apply(img.convert("RGBA"), t, s0, punch=0.02)
        return img.convert("RGB"), "pil-ui", "IG2 cursor-tap + shrink-card zoom-through", (z, dx, dy)

    elif kind == "listicle":  # LF2 + WC1 live cards + WC4 band tissue + IG2 comment
        img = Image.new("RGBA", (W, H), (8, 8, 10, 255))
        ft = WC.mv_source_frame(7.2 + (t - s0) * 1.2)
        left = WC.cover_1080x1920(grade(ft)).crop((0, 0, 760, 1920))
        img.alpha_composite(left.convert("RGBA"), (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([760, 0, W, H], fill=(16, 16, 20, 255))
        WC.tissue_fill(img, (764, 0, W, H), t, tone=(118, 120, 132), alpha=56,
                       step=20, particles=10, seed=4, ghost="raw cuts",
                       ghost_font=R.playfair(150, 900))
        d.rectangle([760, 0, 766, H], fill=VOLT + (150,))  # volt spine (match-cut target)
        # B4 executor-swap (stop-loss): the man cutout on DARK live footage
        # cannot show depth cues honestly (3 blind reads = flat) — removed.
        # Cutouts appear only where depth reads (counter halftone + m2 paper).
        # WC1 video-in-card x2 (LIVE, staggered, bordered, rotated)
        c1 = WC.wc1_card(WC.mv_source_frame(12.5 + (t - s0) * 1.4), 260, 260, rot=2.4,
                         border="polaroid")
        c2 = WC.wc1_card(WC.mv_source_frame(24.0 + (t - s0) * 0.9), 236, 276, rot=-3.0,
                         border="ink")
        s1 = WC.spring_stagger(0, t, s0 + 0.10)
        s2 = WC.spring_stagger(1, t, s0 + 0.10)
        if s1 > 0.02:
            sh1 = WC.wc1_card_shadow(c1)
            img.alpha_composite(sh1.resize((max(1, int(sh1.width * s1)), max(1, int(sh1.height * s1)))),
                                (772, int(H * 0.060) + int((1 - s1) * 90)))
        if s2 > 0.02:
            sh2 = WC.wc1_card_shadow(c2)
            img.alpha_composite(sh2.resize((max(1, int(sh2.width * s2)), max(1, int(sh2.height * s2)))),
                                (790, int(H * 0.565) + int((1 - s2) * 90)))
        items = [("01", "party"), ("02", "everybody"), ("03", "homicide"), ("04", "paid")]
        active = int((t - s0) / 0.65) % 4
        listicle_bars(img, 800, 560, items, R.montserrat(44, 900), active_idx=active,
                      bar_w=110, gap=130)
        scene_label(img, (796, 440), "scene index / live cards (WC1)")
        sticker_coin(d, 880, int(H * 0.885), 74)
        sticker_coin(d, 1000, int(H * 0.93), 54)
        ticker_strip(img, int(H * 0.965), "dies at the end · paid · lemonade · party", t)
        IG.comment_bubble(img, int(W * 0.05), int(H * 0.575), "beat on homicide scene",
                          t, IG.snap(s0 + 0.30, ONSETS, 0.30)[0], who="comment", kw="homicide")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.06, drift=16)
        return img.convert("RGB"), "pil-wc1", "WC1 live video-in-card + WC3 depth + WC4 tissue + IG2 comment", (z * pulse, dx, dy)

    elif kind == "counter":  # WC4 full tissue + M3 ring + odometer + notif (IG2 b3)
        img = canvas_cached("black", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        WC.tissue_fill(img, (0, 0, W, int(H * 0.98)), t, tone=(112, 114, 126),
                       alpha=44, step=24, particles=16, seed=9, ghost="stakes",
                       ghost_font=R.playfair(210, 900))
        card = Image.new("RGBA", (W - 160, int(H * 0.56)), (14, 14, 18, 215))
        cmask = Image.new("L", card.size, 0)
        ImageDraw.Draw(cmask).rounded_rectangle([0, 0, card.width, card.height], radius=28, fill=255)
        img.paste(card, (80, int(H * 0.24)), cmask)
        ImageDraw.Draw(img, "RGBA").rounded_rectangle([80, int(H * 0.24), W - 80, int(H * 0.80)],
                                                      radius=28, outline=VOLT + (140,), width=2)
        ent_c = R.ease_out_cubic(min(1.0, max(0.0, (t - s0)) / 0.9))
        val = int(ent_c * 8137)
        WC.odometer(d, (W / 2, int(H * 0.40)), val, t, size=88, digits=5)
        IG.m3_counter_ring(img, (W / 2, int(H * 0.60)), val, t, s0, r=230)
        volt_pill(img, (W / 2, H * 0.69), "2 MCs / 1 take / 0 fear", R.montserrat(40, 900), rot=-2)
        sticker_coin(d, W - 160, int(H * 0.115), 64)
        sticker_coin(d, 130, int(H * 0.15), 50)
        # WC3 cutout depth presence (counter scene)
        WC.paste_person_v25(img, (W / 2 + 330, int(H * 0.72)), 330, "stair", rot=2,
                            cam_dx=0.0, cam_dy=0.0, seed=2)
        WC.paste_person_v25(img, (W / 2 - 320, int(H * 0.73)), 300, "rock22", rot=-2,
                            cam_dx=0.0, cam_dy=0.0, seed=3)
        IG.notif_banner(img, int(H * 0.055), "Payout", "$8,137 paid to you",
                        t, IG.snap(s0 + 0.25, ONSETS, 0.30)[0], dur=1.6)
        scene_label(img, (86, int(H * 0.86)), "stakes counter / odometer (WC4)")
        fz = 1.0 if t < s0 + 0.30 else 1.0 + 0.10 * math.sin(min(1.0, (t - s0 - 0.30) / 0.25) * math.pi)
        img2, z, dx, dy = cam_apply(img.convert("RGBA"), t, s0, punch=0.045, drift=16)
        # WC4 DOF: edges soft, ring window sharp
        img2 = WC.dof_blur(img2, radius=1.6, except_rect=(60, int(H * 0.22), W - 60, int(H * 0.82)))
        # IG6 isolation micro-beat (measured, persisted render-time)
        if s0 + 1.0 <= t <= s0 + 1.35:
            comp = img2.convert("RGB")
            res, chroma_out, chroma_in = IG.selective_color(comp, keep=(58, 100))
            ISOL_MEAS["t"] = round(t, 2)
            ISOL_MEAS["chroma_frac_outside_volt"] = round(chroma_out, 5)
            ISOL_MEAS["chroma_frac_inside_volt"] = round(chroma_in, 5)
            img2 = res.convert("RGBA")
            if not os.path.exists(f"{P25}/isol_live.json"):
                json.dump({"t": round(t, 2),
                           "chroma_frac_outside_volt": round(chroma_out, 5),
                           "chroma_frac_inside_volt": round(chroma_in, 5),
                           "note": "pre-compression frame measurement (render-time)"},
                          open(f"{P25}/isol_live.json", "w"), indent=1)
        return img2.convert("RGB"), "persp3d-m3", "WC4 tissue + odometer + M3 ring + IG2 notif", (z * fz * pulse, dx, dy)

    elif kind == "m2_live":  # WC1 floating polaroids LIVE + speed ramp + volt accents
        img = canvas_cached("paper", ghost=None)
        d = ImageDraw.Draw(img, "RGBA")
        rt, factor = IG.ramp_t(t, s0, min(LOOP_T, s0 + 0.95), 0.4, 1.6)
        wins = [12.5 + (rt - s0) * 1.6, 4.5 + (rt - s0) * 1.6, 24.0 + (rt - s0) * 0.7]
        base_c = (W / 2, int(H * 0.42))
        for i, win in enumerate(wins):
            z = i / (len(wins) - 1)
            s_sz = 1.0 + z * 0.34
            cw = int(290 * s_sz)
            card = WC.wc1_card(WC.mv_source_frame(win), cw, cw, rot=-6 + i * 5 + IG.rot_jitter(t, i, 1.2),
                               border="polaroid")
            card = WC.wc1_card_shadow(card, blur=12, alpha=100)
            ent_i = WC.spring_stagger(i, t, s0, per=0.14)
            if ent_i <= 0.02:
                continue
            ph_x = base_c[0] + (i - 1) * 270 * (1 + 0.06 * math.sin(t * 0.9 + i))
            ph_y = base_c[1] + (i - 1) * 105 * (1 + 0.05 * math.cos(t * 1.1 + i))
            card_s = card.resize((max(1, int(card.width * ent_i)), max(1, int(card.height * ent_i))))
            lean = (-6 + i * 5) * 0.4
            rad = math.radians(lean)
            dxq = int(card_s.height * 0.05 * math.sin(rad))
            quad = [(ph_x - card_s.width / 2, ph_y - card_s.height / 2 + dxq),
                    (ph_x + card_s.width / 2, ph_y - card_s.height / 2 - dxq),
                    (ph_x + card_s.width / 2 + int(16 * z), ph_y + card_s.height / 2 - dxq * 0.4),
                    (ph_x - card_s.width / 2 - int(16 * z), ph_y + card_s.height / 2 + dxq * 0.4)]
            warped = IG.quad_warp(card_s, quad, W, H)
            img.alpha_composite(Image.fromarray(
                np.clip(np.asarray(warped).astype(np.float32) * min(1.0, 0.55 + 0.45 * ent_i),
                        0, 255).astype(np.uint8)))
        d.line([(150, int(H * 0.20)), (int(W * 0.5) + 120, int(H * 0.30))], fill=VOLT + (220,), width=8)
        f_m = R.montserrat(40, 900)
        d.text((int(W * 0.58), int(H * 0.295)), "raw cuts", font=f_m, fill=VOLT + (245,))
        hb = 30 + 6 * math.sin(t * 3.1)
        d.polygon([(int(W * 0.16), int(H * 0.60) - hb), (int(W * 0.16) + hb * 1.1, int(H * 0.60) - hb * 1.6),
                   (int(W * 0.16) + hb * 2.2, int(H * 0.60) - hb)], fill=VOLT + (235,))
        d.polygon([(int(W * 0.16), int(H * 0.60) - int(hb * 0.7)),
                   (int(W * 0.16) + hb * 2.2, int(H * 0.60) - int(hb * 0.7)),
                   (int(W * 0.16) + hb * 1.1, int(H * 0.60) + hb)], fill=VOLT + (235,))
        # WC3 cutout depth presence (m2 scene)
        WC.paste_person_v25(img, (W - 230, int(H * 0.775)), 380, "duo", rot=2,
                            cam_dx=0.0, cam_dy=0.0, seed=4)
        scene_label(img, (86, int(H * 0.90)), "floating polaroids / live video (WC1+M2)")
        img, z, dx, dy = cam_apply(img, t, s0, punch=0.07, drift=18)
        return img.convert("RGB"), "persp3d-m2", "WC1 live polaroids + IG10 speed ramp", (z * pulse, dx, dy)

    # fallback
    return canvas_cached("black"), "pil", "fallback", (1.0, 0.0, 0.0)

ISOL_MEAS = {}

def scene_at(t):
    idx = 0
    for i, (s, k) in enumerate(SCENES):
        if t >= s:
            idx = i
    return idx

def compose(fi):
    t = fi / FPS
    cam = None
    if t >= LOOP_T - 1e-4:
        # IG3 seamless loop: EXACT frame-0 composition + frame-0 post chain
        # (captions + grain->halation->dust in frame-0 order, frame-0 seeds;
        # no fi-dependent variance, no weave shift (frame-0 weave = 0,0))
        img, engine, tag, _ = draw_scene(IDX["hook_car"], SCENES[0][0])
        engine, tag = "pil-loop", "IG3 loop freeze == frame 0 (frame-0 post chain)"
        img = img.convert("RGB")
        words0 = words_window(SCENES[0][0])
        if words0:
            IG.draw_caption_pop(img, words0, SCENES[0][0], int(H * 0.80))
        img = R._grain(img, 3)                                   # frame-0 order
        img = IG.halation(img, thr=205, strength=0.26)           # frame0: fi%3==0
        img = IG.dust_scratch(img, 0.0, p_dust=0.5)              # frame0: fi%5==0
        return img, engine, tag, (1.0, 0.0, 0.0)
    else:
        img, engine, tag, cam = draw_scene(scene_at(t), t)
        img = img.convert("RGB")
        si = scene_at(t)
        if SCENES[si][1] not in ("ui_tap",):
            words = words_window(t)
            if words:
                IG.draw_caption_pop(img, words, t, int(H * 0.80))
    img = R._grain(img, 3)
    if fi % 3 == 0:
        img = IG.halation(img, thr=205, strength=0.26)
    if fi % 5 == 0:
        img = IG.dust_scratch(img, t, p_dust=0.5)
    wx, wy = IG.gate_weave(t, 1.5)
    if abs(wx) >= 1 or abs(wy) >= 1:
        img = img.crop((int(max(0, wx)), int(max(0, wy)),
                        W + int(min(0, wx)), H + int(min(0, wy)))).resize((W, H), Image.BILINEAR)
    if UI_TAP_T <= t < UI_TAP_T + 0.35:
        img = IG.light_leak(img, (t - UI_TAP_T) / 0.35, edge="right")
    if M2_T <= t < M2_T + 0.30:
        img = IG.light_leak(img, (t - M2_T) / 0.30, edge="left")
    if ST["hook_duo"] - 0.02 <= t <= ST["hook_duo"] + 0.10:
        img = img.filter(ImageFilter.GaussianBlur(1.0 + 9 * math.sin(math.pi * (t - ST["hook_duo"]) / 0.12)))
    if LIST_T - 0.02 <= t <= LIST_T + 0.10:
        img = img.filter(ImageFilter.GaussianBlur(1.0 + 8 * math.sin(math.pi * (t - LIST_T) / 0.12)))
    return img, engine, tag, cam

if __name__ == "__main__":
    a = sys.argv
    START = int(a[a.index("--start") + 1]) if "--start" in a else 0
    END = int(a[a.index("--end") + 1]) if "--end" in a else N - 1
    log = []
    cam_deltas = []
    for fi in range(START, END + 1):
        img, engine, tag, cam_log = compose(fi)
        img.save(f"{FRAMES}/t_{fi:05d}.jpg", quality=88)
        log.append({"frame": fi, "t": round(fi / FPS, 3), "engine": engine, "beat": tag})
        if cam_log:
            cam_deltas.append({"t": round(fi / FPS, 3), "scale": round(cam_log[0], 4),
                               "dx": round(cam_log[1], 2), "dy": round(cam_log[2], 2)})
        if fi % 60 == 0:
            print(f"frame {fi}/{END}", flush=True)
    meta = {"kind": "showcase", "dur": DUR, "fps": FPS, "n_frames": N,
            "beats_lib": LIB_BEATS[:40], "onsets": ONSETS[:80], "kicks": KICKS[:40],
            "onset_engine": OENG, "tempo": TEMPO,
            "scenes": [[s[0], s[1]] for s in SCENES], "snap_log": SNAP_LOG,
            "sticker_map": STICKER_MAP, "isol_measure": ISOL_MEAS,
            "camera_log": cam_deltas, "lyric_words": LYRIC_WORDS,
            "wc2_matte_engine": "rembg isnet-general-use per-frame (live MV footage)",
            "chunk": [START, END]}
    meta.update({"labels_disabled": True, "label_log_qc": K.LABEL_LOG,
                 "hook_fit": dict(SHOW_HOOK_FIT)})
    if START == 0:
        json.dump(meta, open(f"{P25}/showcase_plan.json", "w"), indent=1)
    else:
        json.dump({"camera_log": cam_deltas, "chunk": [START, END]},
                  open(f"{P25}/showcase_chunk_{START}.json", "w"), indent=1)
    print("SHOWCASE FRAMES DONE", START, END, flush=True)
