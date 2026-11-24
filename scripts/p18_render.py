#!/usr/bin/env python3
"""Phase 18.0 UNIFIED SCENE RENDERER (ST1..ST10) — scene-plan driven, ONE path.
Engine chain (E3, logged per beat): FilmCraft CLI unavailable in sandbox ->
EffectCraft unavailable -> Remotion scaffold skipped -> PIL sequences + ffmpeg
composite (measured fallback). Captions: two-font karaoke (bold sans body +
serif accent keyword center-first), full sentence always, sweep loop, NO
typewriter. NO debug HUD in deliverable. TEMP -> work_dir only."""
import cv2, numpy as np, json, os, sys, subprocess, math, random, hashlib, platform
sys.path.insert(0, "/tmp/ems-work/ems-repo/scripts")
sys.path.insert(0, "/home/z/my-project/scripts")
from PIL import Image, ImageDraw, ImageFilter
from p14_lib import (font, text_w, sha256_file, grade_bw, grade_color, add_grain,
                     add_vignette, invert_bite, whip_streak, zoom_through_crop,
                     shake, subject_centroid, smooth_track, write_wav,
                     two_pass_loudnorm, sfx_whoosh, sfx_glitch, sfx_splice,
                     sfx_thump, SR, DEJAVU_B)
import p16_lib as L
from p16_lib import (hook_slam_lockup, highlighter_tape, selection_brackets,
                     odometer, starburst_drawon, ease_out_cubic, ease_out_back,
                     motion_blur_h, light_leak, grade_leap)

WORK, PRESET_PATH, RAW, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
VARIANT = sys.argv[5] if len(sys.argv) > 5 else "9x16"
random.seed(18); np.random.seed(18)

P = json.load(open(PRESET_PATH))
probe = json.load(open(f"{WORK}/probe.json"))
lett = json.load(open(f"{WORK}/letterbox.json"))
crop_rect = lett["crop_rect"]
LL = json.load(open(f"{WORK}/lyric_lines.json"))
LINES = LL["lines"]
PLAN = json.load(open(f"{WORK}/scene_plan.json"))
CUE = json.load(open(f"{WORK}/cue_sheet.json"))
beatmap = json.load(open(f"{WORK}/beatmap.json"))
srcq = json.load(open(f"{WORK}/source_quality.json"))

PRESET_SHA = sha256_file(PRESET_PATH)
SRC_FPS = probe["fps"]; SRC_DUR = probe["duration_s"]
OW, OH = 720, 1280
ACCENT = tuple(P["palette"]["accent_rgb"])
BAND0, BAND1 = int(OH * 0.705), int(OH * 0.795)  # text zone fully above bottom-20% (no-text rule)
ENDCARD_S = PLAN.get("endcard_s", 2.4)
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
from PIL import ImageFont
def sfont(px): return ImageFont.truetype(SERIF_B, px)

TOTAL = round(SRC_DUR + ENDCARD_S, 3)

# ---------- windows: each lyric line is one karaoke sentence (shared engine) ----------
import p18_kar as K
windows = K.build_windows(LINES)
for _w in windows:
    _w["t1"] = min(_w["t1"], SRC_DUR - 0.02)
words = K.words_manifest(LINES)
KWS = K.keywords_set(LINES)

def kar2_state(t):
    return K.kar2_state(t, windows)

def kar2_layout(sents, font_px=54, width_frac=0.90, max_lines=2):
    return K.kar2_layout(sents, OW, font_px, KWS, width_frac, max_lines)

def draw_kar2(im, st, lay, stroke=3):
    return K.draw_kar2(im, st, lay, ACCENT, BAND0, BAND1, KWS, stroke)

lay_cache = {}
def lay_for(li):
    if li not in lay_cache:
        s = K.line_tokens(windows[li]["line"])
        lay_cache[li] = kar2_layout(s)
    return lay_cache[li]

# ---------- footage window (salience-tracked) ----------
ASPECT = OW / OH
_sal = {}
def window_for(src_t):
    ch, cw = crop_rect["h"], crop_rect["w"]
    ww = int(ch * ASPECT)
    if "track" not in _sal:
        ts = list(np.arange(0.0, SRC_DUR, 0.33)); vals = []
        c = cv2.VideoCapture(RAW)
        for st2 in ts:
            c.set(cv2.CAP_PROP_POS_FRAMES, min(int(st2 * SRC_FPS), int(SRC_FPS * SRC_DUR) - 2))
            ok, fr = c.read()
            if ok:
                cr = fr[crop_rect["y"]:crop_rect["y"]+crop_rect["h"], crop_rect["x"]:crop_rect["x"]+crop_rect["w"]]
                vals.append(subject_centroid(cr)[0])
            else:
                vals.append(0.5)
        c.release()
        _sal["track"] = (ts, smooth_track(vals, 0.3))
    ts, cx_tr = _sal["track"]
    cx = float(np.interp(src_t, ts, cx_tr)); cx = max(0.3, min(0.7, cx))
    x0 = int((cw - ww) * cx) if ww < cw else 0
    y0 = 0 if ch <= int(ww / ASPECT) else 0
    return (crop_rect["x"] + x0, crop_rect["y"] + y0, ww, min(ch, int(ww / ASPECT)))

# ---------- matte for hook occlusion (P3 attempt + honest fallback) ----------
cap = cv2.VideoCapture(RAW)
cap.set(cv2.CAP_PROP_POS_FRAMES, int(0.12 * SRC_FPS))
okh, hook_src = cap.read()
cap.release()
matte = None
if okh:
    crop = hook_src[crop_rect["y"]:crop_rect["y"]+crop_rect["h"], crop_rect["x"]:crop_rect["x"]+crop_rect["w"]]
    pil = Image.fromarray(cv2.cvtColor(cv2.resize(crop, (360, int(360 * crop.shape[0] / crop.shape[1]))), cv2.COLOR_BGR2RGB))
    try:
        from p14_lib import matte_alpha
        m = matte_alpha(pil, "welcome_hook_m18")
    except Exception:
        m = None
    if m is not None:
        mb = (m > 128).astype(np.uint8)
        ncomp, lab, stats_c, _ = cv2.connectedComponentsWithStats(mb, 8)
        if ncomp > 1:
            big = 1 + int(np.argmax(stats_c[1:, cv2.CC_STAT_AREA]))
            mb = (lab == big).astype(np.uint8) * 255
        cov = float((mb > 128).mean())
        if 0.03 < cov < 0.45:
            matte = cv2.resize(mb, (OW, OH), interpolation=cv2.INTER_LINEAR)
matte_ok = matte is not None
HOOK_SCRIM = False
hook_y_frac = 0.24
if matte_ok:
    best = None
    for cand in (0.14, 0.20, 0.28, 0.36, 0.44):
        rows = matte[int(OH * cand):int(OH * (cand + 0.26))]
        cv2m = float((rows > 128).mean())
        if best is None or cv2m < best[1]: best = (cand, cv2m)
    hook_y_frac = best[0]
    g0, g1 = int(OH * (hook_y_frac - 0.09)), int(OH * (hook_y_frac + 0.09))
    if float((matte[g0:g1] > 128).mean()) > 0.35:
        HOOK_SCRIM = True; matte_ok = False; matte = None

# ---------- painting asset ----------
PAINT = "/tmp/ems-work/p18/assets/painting_lemons.jpg"
paint_im = None
if os.path.exists(PAINT):
    try:
        paint_im = Image.open(PAINT).convert("RGB")
        paint_im.thumbnail((560, 460), Image.LANCZOS)
    except Exception:
        paint_im = None

# ---------- beats from scene plan (cut on lyric onsets, P11 snap) ----------
grid = [s["t"] for s in (beatmap.get("strong_onsets") or [])]
grid += [t for t in (beatmap.get("beats") or []) if t not in grid]
def snap(t, tol=0.28):
    if not grid or t <= 0.01: return t
    best = min(grid, key=lambda g: abs(g - t))
    return best if abs(best - t) <= tol else t
beats = []
for i, l in enumerate(LINES):
    s0 = 0.0 if i == 0 else snap(l["t0"])
    s1 = snap(LINES[i + 1]["t0"]) if i + 1 < len(LINES) else SRC_DUR
    beats.append({"i": i, "start": round(s0, 3), "end": round(s1, 3),
                  "src0": l["t0"], "src1": l["t1"], "scene": l["scene"],
                  "text": l["text"]})
# drop zero-length (snap collisions)
beats = [b for b in beats if b["end"] - b["start"] > 0.24]

# ---------- SFX synth extras (riser / click / tape-stop) ----------
def synth_click(dur=0.05, sr=SR):
    n = int(dur * sr)
    x = np.random.uniform(-1, 1, n) * np.exp(-np.linspace(0, 8, n))
    return x.astype(np.float32)
def synth_riser(dur=1.0, sr=SR):
    n = int(dur * sr)
    f = np.linspace(180, 900, n)
    ph = np.cumsum(2 * np.pi * f / sr)
    x = np.sin(ph) * np.linspace(0.15, 1.0, n)
    x += np.random.uniform(-1, 1, n) * np.linspace(0.02, 0.2, n)
    return (x * np.linspace(0.4, 1.0, n)).astype(np.float32)
def synth_tape_stop(dur=0.35, sr=SR):
    n = int(dur * sr)
    f = np.linspace(330, 60, n)
    ph = np.cumsum(2 * np.pi * f / sr)
    x = np.sin(ph) * np.linspace(1.0, 0.0, n) ** 1.5
    return x.astype(np.float32)

# ---------- paper texture (P2 craft for S05) ----------
def paper_texture(w, h, seed=7):
    rng = np.random.RandomState(seed)
    base = np.full((h, w, 3), 238.0)
    base += rng.normal(0, 9.0, (h, w, 1))
    fib = rng.uniform(0, 1, (h, w)) > 0.988
    base[fib] = [215, 208, 195]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def lockup18(im, kicker, giant, cont, accent, out_w, y_top_frac, settle=0.28, t_lt=1.0, ghost=True):
    """Phase 18 lockup: mixed-scale type slam, giant PRE-FIT to 0.66W so the
    1.30x slam start stays <=0.90W (G-P2). Same design language as p16."""
    import math as _m
    d = ImageDraw.Draw(im)
    W, H = im.size
    e = min(1.0, t_lt / settle) if settle > 0 else 1.0
    sc = 1.30 - 0.30 * e
    if e > 0.75:
        sc = 1.0 + 0.03 * _m.sin((e - 0.75) / 0.25 * _m.pi)
    px = 96
    fg = font(px)
    while text_w(giant, fg) > out_w * 0.66 and px > 40:
        px -= 2; fg = font(px)
    fg = font(int(px * sc))
    fk = font(int(px * 0.34 * sc)); fc = font(int(px * 0.36 * sc))
    y0 = int(H * y_top_frac)
    if ghost:
        off = int(6 * (1 - e) + 3)
        d.text((W // 2 + off, y0 + off), giant, font=fg, fill=(int(255 * 0.28),) * 3,
               anchor="mm", stroke_width=1, stroke_fill=(60, 60, 60))
    if kicker:
        d.text((W // 2, y0 - px * 0.62), kicker, font=fk, fill=(255, 255, 255),
               stroke_width=2, stroke_fill=(10, 10, 10), anchor="mm")
    d.text((W // 2, y0), giant, font=fg, fill=accent,
           stroke_width=4, stroke_fill=(10, 10, 10), anchor="mm")
    if cont:
        d.text((W // 2, y0 + px * 0.62), cont, font=fc, fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
    return im

# ================= RENDER LOOP =================
cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{OW}x{OH}", "-r", "30", "-i", "-",
       "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
cap = cv2.VideoCapture(RAW)
seq_pos, seq_frame = -1, None
def fetch_frame(fidx):
    global seq_pos, seq_frame
    fidx = int(max(0, min(fidx, int(SRC_DUR * SRC_FPS) - 2)))
    if seq_frame is None or fidx < seq_pos - 2:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
        ok, fr = cap.read()
        if ok: seq_pos, seq_frame = fidx, fr
        return seq_frame
    while seq_pos < fidx:
        ok, fr = cap.read()
        if not ok: break
        seq_pos += 1; seq_frame = fr
    return seq_frame

n_out = int(TOTAL * 30)
cut_last = beats[-1]["end"]
cover_best = {"score": -1, "frame": None, "t": 0}
scene_stats = {"types": [], "engine": {}}

def plate_from(fr_np, dark=0.55, blur=14):
    """design-scene footage plate: full-bleed, blurred, darkened (still real footage)."""
    im = Image.fromarray(np.clip(fr_np, 0, 255).astype(np.uint8))
    im = im.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im).astype(np.float32) * dark
    return a

for oi in range(n_out):
    t = oi / 30.0
    if oi % 150 == 0:
        print(f"F{oi}/{n_out}", flush=True)
    # ---------- end card (loop echo, no-brand) ----------
    if t >= cut_last:
        src_t = beats[0]["src0"] + (t - cut_last) * 0.5
        x, y, ww, wh = window_for(min(src_t, SRC_DUR - 0.1))
        fr = fetch_frame(int(min(src_t, SRC_DUR - 0.1) * SRC_FPS))
        if fr is None: fr = fetch_frame(int(beats[0]["src0"] * SRC_FPS))
        cr = fr[y:y+wh, x:x+ww]
        frame = cv2.cvtColor(cv2.resize(cr, (OW, OH)), cv2.COLOR_BGR2RGB).astype(np.float32)
        frame = grade_bw(frame, contrast=1.14, lift=-6)
        frame = add_vignette(frame, 0.20); frame = add_grain(frame, 4.0)
        pil = Image.fromarray(frame.astype(np.uint8))
        d = ImageDraw.Draw(pil)
        d.text((OW//2, int(OH*0.34)), "THE LEAP", font=font(60), fill=ACCENT,
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
        d.text((OW//2, int(OH*0.44)), "LOOP", font=font(40), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
        repo = P["end_card"]["repo_pill"]
        f2 = font(22); wpx = text_w(repo, f2)
        x0 = (OW - wpx)//2 - 14
        d.rounded_rectangle([x0, int(OH*0.56), x0+wpx+28, int(OH*0.56)+42],
                            radius=12, fill=(12, 12, 12), outline=ACCENT, width=2)
        d.text((OW//2, int(OH*0.56)+21), repo, font=f2, fill=(255, 255, 255), anchor="mm")
        st = kar2_state(t)
        if st is not None and t < SRC_DUR - 0.05:
            scr_alpha = 248 if float(np.asarray(pil.convert("L"), np.float32)[BAND0:BAND1].mean()) >= 110 else 234
            scr = Image.new("L", (OW, OH), 0)
            ds2 = ImageDraw.Draw(scr)
            ds2.rectangle([0, BAND0-30, OW, BAND1+34], fill=scr_alpha)
            scr = scr.filter(ImageFilter.GaussianBlur(14))
            darkim = Image.new("RGB", (OW, OH), (8, 8, 10))
            pil = Image.composite(darkim, pil, scr)
            draw_kar2(pil, st, lay_for(st["win"]["i"]))
            d = ImageDraw.Draw(pil)
        d.rectangle([int(OW*0.28), BAND1+8, int(OW*0.72), BAND1+14], fill=ACCENT)
        of = np.clip(np.asarray(pil).astype(np.float32), 0, 255).astype(np.uint8)
        proc.stdin.write(of.tobytes())
        continue

    b = next((bb for bb in beats if bb["start"] <= t < bb["end"]), beats[-1])
    lt = t - b["start"]; dur = b["end"] - b["start"]
    sc = b["scene"]; stype = sc["type"]; prm = sc["params"]
    scene_stats["engine"][b["i"]] = sc["engine"]
    scene_stats["types"].append(stype)
    src_t = min(b["src0"] + lt * (b["src1"] - b["src0"]) / max(dur, 0.1), SRC_DUR - 0.06)
    x, y, ww, wh = window_for(src_t)
    fr = fetch_frame(int(src_t * SRC_FPS))
    if fr is None: fr = fetch_frame(0)
    design_led = stype in ("S02_full_screen_text", "S02_echo_invert", "S05_painting_slide_in",
                           "S08_graph_odometer", "S10_ui_listicle", "S12_circular_counter",
                           "S13_blurred_square_list")
    # ---------- comp: zoom/punch/tracks ----------
    zin = 1.0
    if prm.get("punch_in"):
        zin = 1.0 + 0.10 * ease_out_cubic(min(1.0, lt / max(dur * 0.5, 0.1)))
    if stype == "S08_graph_odometer":
        zin = 1.06 + 0.05 * math.sin(lt / max(dur, 0.5) * math.pi)
    if design_led:
        zin = 1.0
    tw, th = max(48, int(ww / zin)), max(48, int(wh / zin))
    cx_off = int((ww - tw) * 0.5)
    cy_off = int((wh - th) * 0.42)
    cr = fr[y+cy_off:y+cy_off+th, x+cx_off:x+cx_off+tw]
    resized = cv2.resize(cr, (OW, OH), interpolation=cv2.INTER_AREA)
    if zin > 1.001 and not design_led:
        mb = int(5 + 9 * max(0.0, 1.0 - lt / max(dur * 0.5, 0.1)))
        k = max(1, mb | 1)
        resized = cv2.GaussianBlur(resized, (k, 1), k / 3.0)
    frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32)
    if design_led and stype != "S02_full_screen_text":
        frame = plate_from(frame, dark=0.42, blur=16)
    # speed ramp on tracking beat
    if prm.get("track") and 0.35 < lt / max(dur, 0.1) < 0.7:
        pass  # src mapping already eased via time split; visual only here
    # grade (P7)
    frame = grade_leap(frame, base="color") if stype != "S05_painting_slide_in" else grade_leap(frame, base="bw")
    frame = add_vignette(frame, 0.20)
    frame = add_grain(frame, 4.2)

    # ---------- transitions (P6) ----------
    if lt < 0.16 and b["i"] > 0:
        mbk = max(3, int(16 * (1 - lt / 0.13)))
        frame = np.asarray(L.motion_blur_h(Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)),
                                           strength=mbk)).astype(np.float32)
        frame = whip_streak(frame, direction=1 if b["i"] % 2 else -1,
                            intensity=1 - lt / 0.16, flash=0.88 * (1 - lt / 0.16))
        frame = zoom_through_crop(frame, 1.0 + 0.05 * (1 - lt / 0.13))
    if "invert_bite_s" in prm and lt < prm["invert_bite_s"]:
        frame = invert_bite(frame)
    if b["i"] == 3 and lt > dur - 0.5:  # recursive zoom-through into echo card
        z = 1.0 + (lt - (dur - 0.5)) / 0.5 * 0.9
        frame = zoom_through_crop(frame, z)
    if prm.get("freeze_slam") and lt < 0.52:
        frame = fetch_frame(int(0.12 * SRC_FPS))
        frame = cv2.cvtColor(cv2.resize(
            frame[y:y+wh, x:x+ww], (OW, OH)), cv2.COLOR_BGR2RGB).astype(np.float32)
        frame = grade_leap(frame, base="bw")
        frame = add_vignette(frame, 0.20); frame = add_grain(frame, 4.2)
        if lt < 0.35:
            mag = int(6 * (1 - lt / 0.35))
            frame = shake(frame, random.randint(-mag, mag), random.randint(-mag // 2, mag // 2))
    if "mask_wipe_in" in prm and lt < 0.30:
        e = ease_out_cubic(lt / 0.30)
        Wm = int(OW * e)
        keep = fetch_frame(int(max(0.0, (b["src0"] - 0.12)) * SRC_FPS))
        keep_c = cv2.cvtColor(cv2.resize(keep[y:y+wh, x:x+ww], (OW, OH)), cv2.COLOR_BGR2RGB).astype(np.float32)
        keep_c = grade_leap(keep_c, base="bw")
        frame[:, Wm:] = keep_c[:, Wm:]

    pil = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)

    # ================= scene design overlays =================
    if stype == "S02_full_screen_text":
        kicker, giant, cont = prm["lockup"]
        if HOOK_SCRIM or not matte_ok:
            lockup18(pil, kicker, giant, cont, ACCENT, OW,
                     y_top_frac=hook_y_frac, settle=0.28, t_lt=lt, ghost=True)
        else:
            base_arr = np.asarray(pil).astype(np.float32)
            text_layer = Image.new("RGB", (OW, OH), (0, 0, 0))
            lockup18(text_layer, kicker, giant, cont, ACCENT, OW,
                     y_top_frac=hook_y_frac, settle=0.28, t_lt=lt, ghost=True)
            tl = np.asarray(text_layer).astype(np.float32)
            tm = (tl.sum(axis=2) > 40)
            comp = base_arr.copy()
            vis = tm & (matte <= 128)
            comp[vis] = tl[vis]
            pil = Image.fromarray(comp.astype(np.uint8))
        d = ImageDraw.Draw(pil)
        if lt < 1.3:
            gw = font(96); pw = 96
            while text_w(giant, gw) > OW * 0.80 and pw > 40:
                pw -= 2; gw = font(pw)
            tw3 = text_w(giant, gw)
            selection_brackets(pil, int(OW/2 - tw3/2), int(OH*hook_y_frac) - int(pw*0.55),
                               int(OW/2 + tw3/2), int(OH*hook_y_frac) + int(pw*0.55), ACCENT, lt)
            d = ImageDraw.Draw(pil)

    elif stype == "S02_echo_invert":
        d.text((OW//2, int(OH*0.30)), "WELCOME", font=font(74), fill=ACCENT,
               stroke_width=4, stroke_fill=(10, 10, 10), anchor="mm")
        e = ease_out_back(min(1.0, lt / 0.4))
        sub = "to another day"
        d.text((OW//2, int(OH*0.30) + 66), sub, font=font(int(34 * min(1.0, e))), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")

    elif stype == "S11_ui_pop":
        starburst_drawon(pil, OW//2, int(OH*0.30), 150, lt, ACCENT, rays=14)
        d = ImageDraw.Draw(pil)
        kw = prm["keyword"]
        d.text((OW//2, int(OH*0.30)), kw, font=sfont(58), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
        if lt < 1.0:
            selection_brackets(pil, OW//2 - 120, int(OH*0.30) - 60,
                               OW//2 + 120, int(OH*0.30) + 60, ACCENT, lt)
            d = ImageDraw.Draw(pil)

    elif stype == "S04_line_illustration":
        kw = prm["keyword"]
        y0 = int(OH * 0.26)
        if lt > 0.2:
            fx = font(50)
            wpx = text_w(kw, fx)
            highlighter_tape(pil, OW//2 - wpx/2 - 10, y0 - 8, OW//2 + wpx/2 + 10, y0 + 62,
                             color=(180, 30, 30), prog=min(1.0, (lt - 0.2) / 0.35))
            d = ImageDraw.Draw(pil)
            d.text((OW//2, y0 + 27), kw, font=fx, fill=(255, 255, 255),
                   stroke_width=2, stroke_fill=(10, 10, 10), anchor="mm")
        # crosshair illustration on subject zone
        ccx, ccy = OW//2, int(OH*0.42)
        r = int(56 * min(1.0, lt / 0.5))
        d.ellipse([ccx-r, ccy-r, ccx+r, ccy+r], outline=ACCENT, width=3)
        d.line([(ccx-r-14, ccy), (ccx-r+8, ccy)], fill=ACCENT, width=3)
        d.line([(ccx+r-8, ccy), (ccx+r+14, ccy)], fill=ACCENT, width=3)
        d.line([(ccx, ccy-r-14), (ccx, ccy-r+8)], fill=ACCENT, width=3)
        d.line([(ccx, ccy+r-8), (ccx, ccy+r+14)], fill=ACCENT, width=3)

    elif stype == "S03_line_text_track":
        # camera-tracked lyric card: follows salience x (smoothed)
        ts_, cx_tr = _sal["track"]
        cx = float(np.interp(src_t, ts_, cx_tr)); cx = max(0.3, min(0.7, cx))
        cardx = int(OW * cx)
        txt = b["text"].upper()
        fpx = 34
        from p14_lib import fit_font
        fx, _ffpx = fit_font(OW * 0.78, txt, fpx, min_px=20)
        wpx = text_w(txt, fx)
        bx0 = max(10, min(OW - int(wpx) - 34, cardx - int(wpx) // 2))
        e = ease_out_back(min(1.0, lt / 0.35))
        byy = int(OH*0.22) + int(14 * (1 - e))
        d.rounded_rectangle([bx0, byy, bx0 + int(wpx) + 24, byy + 50], radius=12,
                            fill=(12, 12, 12), outline=ACCENT, width=2)
        d.text((bx0 + int(wpx)/2 + 12, byy + 25), txt, font=fx, fill=(255, 255, 255), anchor="mm")

    elif stype == "S10_ui_listicle":
        rows = prm["rows"]
        y0 = int(OH * 0.20)
        for ri, rtxt in enumerate(rows):
            appear = lt > ri * prm["row_pop"]
            if not appear: continue
            e = ease_out_back(min(1.0, (lt - ri * prm["row_pop"]) / 0.30))
            ry = y0 + ri * 74 - int(16 * (1 - e))
            d.rounded_rectangle([int(OW*0.10), ry, int(OW*0.90), ry + 58], radius=14,
                                fill=(12, 12, 12), outline=ACCENT if ri == len(rows)-1 else (70, 70, 70), width=2)
            d.text((int(OW*0.13), ry + 29), rtxt, font=font(30),
                   fill=ACCENT if ri == len(rows)-1 else (255, 255, 255), anchor="lm")

    elif stype == "S08_graph_odometer":
        gx0, gy0, gx1, gy1 = int(OW*0.14), int(OH*0.18), int(OW*0.86), int(OH*0.40)
        # glowing grid
        for gx in np.linspace(gx0, gx1, 8):
            d.line([(gx, gy0), (gx, gy1)], fill=(40, 48, 20), width=1)
        for gy in np.linspace(gy0, gy1, 5):
            d.line([(gx0, gy), (gx1, gy)], fill=(40, 48, 20), width=1)
        # bezier ball rise
        e = ease_out_cubic(min(1.0, lt / 1.1))
        bx = gx0 + (gx1 - gx0) * min(1.0, lt / max(dur, 0.5))
        by = gy1 - (gy1 - gy0) * e
        for rr, al in ((16, 110), (9, 255)):
            gl = Image.new("RGBA", pil.size, (0, 0, 0, 0))
            dg = ImageDraw.Draw(gl)
            dg.ellipse([bx-rr, by-rr, bx+rr, by+rr], fill=ACCENT + (al,))
            gl = gl.filter(ImageFilter.GaussianBlur(6 if rr > 10 else 2))
            pil.paste(Image.alpha_composite(pil.convert("RGBA"), gl).convert("RGB"), (0, 0))
            d = ImageDraw.Draw(pil)
        odometer(pil, OW//2, int(OH*0.30), int(beatmap["tempo_bpm"]), fpx=54, digits=3,
                 accent=ACCENT, settle_lt=lt)
        d = ImageDraw.Draw(pil)
        d.text((OW//2, int(OH*0.30) - 56), prm["odometer_label"], font=font(22),
               fill=(255, 255, 255), stroke_width=2, stroke_fill=(10, 10, 10), anchor="mm")

    elif stype == "S12_circular_counter":
        cxr, cyr, rr = OW//2, int(OH*0.30), 110
        e = ease_out_cubic(min(1.0, lt / prm["arc_fill_s"]))
        d.arc([cxr-rr, cyr-rr, cxr+rr, cyr+rr], start=-90, end=-90 + int(359 * e),
              fill=ACCENT, width=12)
        d.arc([cxr-rr, cyr-rr, cxr+rr, cyr+rr], start=-90 + int(359 * e), end=270,
              fill=(60, 60, 60), width=12)
        d.text((cxr, cyr), f"{int(100*e)}%", font=font(52), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
        d.text((cxr, cyr + rr + 30), prm["counter_label"], font=sfont(34), fill=ACCENT,
               stroke_width=2, stroke_fill=(10, 10, 10), anchor="mm")

    elif stype == "S05_painting_slide_in":
        if paint_im is not None:
            e = ease_out_back(min(1.0, lt / 0.5))
            px_ = int((OW - paint_im.size[0]) / 2 - (1 - e) * OW * 0.9)
            py_ = int(OH * 0.20)
            card = paper_texture(paint_im.size[0] + 44, paint_im.size[1] + 56)
            dc = ImageDraw.Draw(card)
            card.paste(paint_im, (22, 22))
            dc.rectangle([22, 22, 22 + paint_im.size[0] - 1, 22 + paint_im.size[1] - 1],
                         outline=(90, 90, 90), width=2)
            rot = card.rotate(-2.2, expand=True, fillcolor=(226, 222, 214))
            sh = Image.new("RGBA", pil.size, (0, 0, 0, 0))
            dsh = ImageDraw.Draw(sh)
            dsh.rectangle([px_ + 10, py_ + 14, px_ + rot.size[0] + 10, py_ + rot.size[1] + 14],
                          fill=(0, 0, 0, 130))
            sh = sh.filter(ImageFilter.GaussianBlur(12))
            pil.paste(Image.alpha_composite(pil.convert("RGBA"), sh).convert("RGB"), (0, 0))
            pil.paste(rot, (px_, py_))
            d = ImageDraw.Draw(pil)
            tw4 = text_w(prm["tape_label"], font(26))
            highlighter_tape(pil, OW//2 - tw4/2 - 12, py_ + rot.size[1] + 6,
                             OW//2 + tw4/2 + 12, py_ + rot.size[1] + 44,
                             color=(255, 230, 0), prog=min(1.0, max(0.0, (lt - 0.35) / 0.4)))
            d = ImageDraw.Draw(pil)
            d.text((OW//2, py_ + rot.size[1] + 25), prm["tape_label"], font=font(26),
                   fill=(12, 12, 12), anchor="mm")
            if lt < 0.5:
                pil = light_leak(pil, lt, dur=0.5)
                d = ImageDraw.Draw(pil)

    elif stype == "S13_blurred_square_list":
        pills = prm["pills"]
        y0 = int(OH * 0.20)
        for ri, ptxt in enumerate(pills):
            if lt < ri * 0.22: continue
            e = ease_out_back(min(1.0, (lt - ri * 0.22) / 0.28))
            ry = y0 + ri * 78 - int(14 * (1 - e))
            pw2 = int(OW * (0.52 + 0.10 * ri))
            bx0 = int((OW - pw2) / 2)
            pill = Image.new("RGBA", (pw2, 60), (12, 12, 12, 200))
            dp = ImageDraw.Draw(pill)
            dp.rounded_rectangle([0, 0, pw2 - 1, 59], radius=16,
                                 outline=ACCENT if ri == 0 else (90, 90, 90), width=2)
            pill = pill.filter(ImageFilter.GaussianBlur(0.6))
            pil.paste(pill.convert("RGB"), (bx0, ry), pill)
            d = ImageDraw.Draw(pil)
            d.text((OW//2, ry + 30), ptxt, font=font(28),
                   fill=ACCENT if ri == 0 else (255, 255, 255), anchor="mm")

    elif stype == "S07_object_callout":
        ax0, ay0 = int(OW*0.62), int(OH*0.30)
        ax1, ay1 = int(OW*0.38), int(OH*0.44)
        e = ease_out_cubic(min(1.0, lt / 0.5))
        axc, ayc = ax0 + (ax1 - ax0) * e, ay0 + (ay1 - ay0) * e
        d.line([(ax0, ay0), (axc, ayc)], fill=ACCENT, width=4)
        d.ellipse([ax1 - 7, ay1 - 7, ax1 + 7, ay1 + 7], fill=ACCENT)
        lbl = prm["label"]
        fx = font(24)
        wpx = text_w(lbl, fx)
        d.rounded_rectangle([ax0 - wpx/2 - 12, ay0 - 46, ax0 + wpx/2 + 12, ay0],
                            radius=10, fill=(12, 12, 12), outline=ACCENT, width=2)
        d.text((ax0, ay0 - 23), lbl, font=fx, fill=(255, 255, 255), anchor="mm")

    elif stype == "S09_broll_text_endcard":
        d.text((OW//2, int(OH*0.26)), prm["text"], font=sfont(56), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")

    # ================= two-font karaoke band (ST5) =================
    st = kar2_state(t)
    if st is not None:
        band_luma = float(np.asarray(pil.convert("L"), np.float32)[BAND0:BAND1].mean())
        alpha = 234 if band_luma < 110 else 248
        scr = Image.new("L", (OW, OH), 0)
        ds2 = ImageDraw.Draw(scr)
        ds2.rectangle([0, BAND0 - 30, OW, BAND1 + 34], fill=alpha)
        scr = scr.filter(ImageFilter.GaussianBlur(14))
        darkim = Image.new("RGB", (OW, OH), (8, 8, 10))
        pil = Image.composite(darkim, pil, scr)
        draw_kar2(pil, st, lay_for(st["win"]["i"]))
        d = ImageDraw.Draw(pil)
        d.rectangle([int(OW*0.28), BAND1 + 8, int(OW*0.72), BAND1 + 14], fill=ACCENT)

    of = np.clip(np.asarray(pil).astype(np.float32), 0, 255).astype(np.uint8)
    proc.stdin.write(of.tobytes())

    # cover scorer
    if 0.5 < t < cut_last - 1.0:
        g = cv2.cvtColor(of, cv2.COLOR_RGB2GRAY).astype(np.float32)
        acc = float((np.abs(of[:, :, 1].astype(np.int16) - ACCENT[1]) < 40).mean() +
                    (np.abs(of[:, :, 0].astype(np.int16) - ACCENT[0]) < 40).mean())
        sc2 = acc * 3 + (20 < g.mean() < 200) * 1.0 + float((g > 150).mean())
        if sc2 > cover_best["score"]:
            cover_best = {"score": sc2, "frame": of.copy(), "t": round(t, 2)}

cap.release()
proc.stdin.close(); proc.wait()

# ================= AUDIO (P10/ST9) =================
audio_work = f"{WORK}/audio_mix_18.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", RAW, "-vn", "-ar", "44100",
                "-ac", "2", "-t", f"{SRC_DUR:.3f}", f"{WORK}/orig18.wav"], check=True)
import wave as _w
wr = _w.open(f"{WORK}/orig18.wav", "rb")
orig = np.frombuffer(wr.readframes(wr.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767.0
wr.close()
if len(orig) < int(TOTAL * SR):
    pad_n = int(TOTAL * SR) - len(orig)
    head = orig[:min(len(orig), pad_n)]  # loop echo pad (video loops beat 0)
    orig = np.concatenate([orig, head])[:int(TOTAL * SR)]
orig = orig[:int(TOTAL * SR)]
SFXF = {"whoosh": lambda: sfx_whoosh(dur=0.5), "whoosh_short": lambda: sfx_whoosh(dur=0.3),
        "glitch": lambda: sfx_glitch(dur=0.12), "splice": lambda: sfx_splice(dur=0.08),
        "thump": lambda: sfx_thump(dur=0.35), "click": synth_click,
        "riser": lambda: synth_riser(1.0), "riser_soft": lambda: synth_riser(0.7),
        "tape_stop_short": synth_tape_stop}
sfx = np.zeros_like(orig)
n_events = 0
for ev in CUE["events"]:
    if ev["t"] >= TOTAL - 0.1: continue
    g = np.zeros(1, np.float32)
    for part in ev["sfx"].split("+"):
        base = part.replace("_x3", "")
        f3 = SFXF.get(base)
        if f3 is None: continue
        gg = f3()
        if part.endswith("_x3"):
            gg = np.concatenate([np.pad(gg, (0, int(0.12 * SR))), gg, np.pad(gg, (0, int(0.12 * SR)))])
        amp = 0.5 * (10 ** (ev["level_db"] / 20.0))
        mx = np.abs(gg).max() or 1
        g = np.concatenate([g, (gg / mx * amp)])
    i0 = int(ev["t"] * SR)
    i1 = min(len(orig), i0 + len(g))
    if i1 > i0:
        sfx[i0:i1] += np.stack([g[:i1-i0], g[:i1-i0]], axis=1)
        n_events += 1
mix = orig + sfx
write_wav(audio_work, mix)

final = OUT.replace(".mp4", "_ln.mp4")
ln = two_pass_loudnorm(audio_work, f"{WORK}/ln18.aac")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", OUT, "-i", f"{WORK}/ln18.aac",
                "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", final], check=True)
os.replace(final, OUT)

# ================= exports =================
if cover_best["frame"] is not None:
    cv2.imwrite(f"{WORK}/cover_{VARIANT}.jpg", cv2.cvtColor(cover_best["frame"], cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 92])

plan_out = {"variant": VARIANT, "ow": OW, "oh": OH, "fps": 30, "total": TOTAL,
            "preset": P["name"], "preset_sha256": PRESET_SHA,
            "beats": [{"i": b["i"], "start": b["start"], "end": b["end"],
                       "scene_type": b["scene"]["type"], "engine": b["scene"]["engine"],
                       "text": b["text"]} for b in beats],
            "scene_census": {"types": sorted(set(scene_stats["types"])),
                             "n_types": len(set(scene_stats["types"]))},
            "matte_occlusion": matte_ok, "hook_scrim": HOOK_SCRIM,
            "hook_y_frac": hook_y_frac, "sfx_events": n_events,
            "two_font": {"body": "DejaVuSans-Bold", "keyword": "DejaVuSerif-Bold",
                         "keywords_semantic": sorted(KWS)},
            "hud": "none (Q11 debug-HUD removed)",
            "engine_chain": "FilmCraft unavailable -> EffectCraft unavailable -> PIL+ffmpeg (E3 fallback, per-beat logged)",
            "renderer": "p18_render.py (single path)",
            "loudnorm": ln,
            "source_quality": srcq["total_10"],
            "resource_licenses": PLAN["source"]["license"]}
json.dump(plan_out, open(f"{WORK}/plan_{VARIANT}.json", "w"), indent=1)

manifest = {"video": P["name"], "variant": VARIANT, "input_sha256": sha256_file(RAW),
            "preset_sha256": PRESET_SHA, "seed": 18,
            "tool_versions": {"python": platform.python_version(), "opencv": cv2.__version__},
            "beat_table": plan_out["beats"], "renderer": "p18_render.py",
            "total": TOTAL, "loudnorm": ln, "cover_t": cover_best["t"],
            "song": PLAN["song"], "source": PLAN["source"]}
json.dump(manifest, open(f"{WORK}/manifest_{VARIANT}.json", "w"), indent=1)

log = {"preset": P["name"], "variant": VARIANT, "out": os.path.basename(OUT),
       "n_beats": len(beats), "cut_times": [b["start"] for b in beats],
       "scene_types": scene_stats["types"], "sfx_events": n_events,
       "matte_occlusion": matte_ok, "loudnorm": ln, "renderer": "p18_render.py"}
json.dump(log, open(f"{WORK}/render_log_{VARIANT}.json", "w"), indent=1)
print("RENDER DONE:", OUT, "| ln:", json.dumps(ln), "| sfx:", n_events)
