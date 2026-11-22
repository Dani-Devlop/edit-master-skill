#!/usr/bin/env python3
"""Phase 14.1 UNIFIED RENDERER — one code path for all videos (L0 preset-driven).
Usage: p14_render.py <work_dir> <preset.json> <raw> <out.mp4> [variant]
variant: 9x16 (default) | 1x1 | 4x5
Outputs: out.mp4 + render_log.json + contact_sheet.jpg (all inside work_dir TEMP).
"""
import cv2, numpy as np, json, os, sys, subprocess, math, random
sys.path.insert(0, "/home/z/my-project/scripts")
from PIL import Image, ImageDraw
from p14_lib import (font, draw_keyword_line, karaoke_state, draw_karaoke, grade_bw,
                     grade_color, grade_day_for_night, add_grain, add_vignette, invert_bite, whip_streak,
                     zoom_through_crop, scanlines, shake, subject_centroid, smooth_track,
                     matte_alpha, music_bed, write_wav, two_pass_loudnorm, sfx_whoosh,
                     sfx_glitch, sfx_splice, sfx_thump, synth_kick, SR, sha256_file,
                     text_w, group_phrases)

WORK, PRESET_PATH, RAW, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
VARIANT = sys.argv[5] if len(sys.argv) > 5 else "9x16"
random.seed(14); np.random.seed(14)
P = json.load(open(PRESET_PATH))
probe = json.load(open(f"{WORK}/probe.json"))
lett = json.load(open(f"{WORK}/letterbox.json"))
crop_rect = lett["crop_rect"]
census = json.load(open(f"{WORK}/census.json"))
whisper = json.load(open(f"{WORK}/whisper_words.json"))
beatmap = json.load(open(f"{WORK}/beatmap.json"))
srcq = json.load(open(f"{WORK}/source_quality.json"))

SRC_FPS = probe["fps"]; SRC_DUR = probe["duration_s"]
if VARIANT == "1x1": OW, OH = 720, 720
elif VARIANT == "4x5": OW, OH = 720, 900
else: OW, OH = 720, 1280
ACCENT = tuple(P["palette"]["accent_rgb"])
BAND0, BAND1 = int(OH * P["captions"]["band_frac"][0]), int(OH * P["captions"]["band_frac"][1])
ENDCARD_S = 2.4

# ---------- scenes ----------
metrics = census["metrics4fps"]
scene_bounds = census["cut_candidates_s"][:] or [0.0]
scene_defs = []  # (start, end, is_color)
prev = 0.0
for c in scene_bounds + [SRC_DUR]:
    seg = [m for m in metrics if prev <= m["t"] < c]
    cf = float(np.mean([m["color_frac"] for m in seg])) if seg else 0.0
    scene_defs.append({"start": round(prev, 3), "end": round(c, 3), "color": cf > 0.08})
    prev = c
if len(scene_defs) == 1 and SRC_DUR > 6:  # single-scene sources: split at thirds for variety
    t1, t2 = SRC_DUR / 3, SRC_DUR * 2 / 3
    scene_defs = [{"start": 0, "end": t1, "color": scene_defs[0]["color"]},
                  {"start": t1, "end": t2, "color": scene_defs[0]["color"]},
                  {"start": t2, "end": SRC_DUR, "color": scene_defs[0]["color"]}]
scene_defs = [s for s in scene_defs if s["end"] - s["start"] > 0.5] or \
             [{"start": 0, "end": SRC_DUR, "color": False}]

# ---------- captions plan ----------
words = whisper.get("words", [])
if words:
    cap_engine = "whisper-word-sync"
else:
    cap_engine = "beat-keyword"
kw = P["captions"].get("keywords", ["NOW", "WATCH", "REAL", "RAW", "GO"])

# ---------- beat planning ----------
target_len = min(P["beats"]["length_s"][1] - ENDCARD_S, SRC_DUR + 3.0)
n_beats = max(P["beats"]["count"][0], min(P["beats"]["count"][1], int(target_len / 3.0)))
grid = beatmap.get("strong_onsets") and [s["t"] for s in beatmap["strong_onsets"]] or \
       (beatmap.get("beats") or [])
if not grid and beatmap.get("silent"):
    bpm = beatmap["tempo_bpm"]; beat = 60.0 / bpm
    grid = [round(beat * i, 3) for i in range(int(SRC_DUR / beat) + 30)]

def nearest_onset(t, tol=0.12):
    if not grid: return t
    best = min(grid, key=lambda g: abs(g - t))
    return best if abs(best - t) <= tol else t

cut_times = [0.0]
step = target_len / n_beats
tcur = 0.0
for i in range(n_beats - 1):
    tcur += step
    tcur = min(tcur, SRC_DUR - 1.2)
    cut_times.append(nearest_onset(tcur))
cut_times.append(round(max(SRC_DUR, target_len) - ENDCARD_S, 3))
cut_times = sorted(set(cut_times))
# enforce max_beat
for i in range(1, len(cut_times)):
    if cut_times[i] - cut_times[i - 1] > P["beats"]["max_beat_s"]:
        cut_times[i] = cut_times[i - 1] + P["beats"]["max_beat_s"]
cut_times = sorted(set(round(c, 3) for c in cut_times))
n_beats = len(cut_times) - 1

# assign source windows per beat (rotate scenes, color-pop inserts for color scenes)
color_scenes = [s for s in scene_defs if s["color"]]
bw_scenes = [s for s in scene_defs if not s["color"]]
beats = []
for i in range(n_beats):
    s0, s1 = cut_times[i], cut_times[i + 1]
    dur = s1 - s0
    # pick source scene: prefer bw scenes for base, color scene for 1-2 insert beats
    if color_scenes and i in (n_beats - 2, n_beats - 3) and P["palette"].get("color_pop") not in (None, "n/a"):
        sc = color_scenes[(i - (n_beats - 2)) % len(color_scenes)]
    else:
        sc = bw_scenes[i % len(bw_scenes)] if bw_scenes else scene_defs[i % len(scene_defs)]
    slen = sc["end"] - sc["start"]
    src0 = sc["start"] + min(0.5, slen * 0.1) + (i * 0.7) % max(slen * 0.4, 0.5)
    src1 = min(sc["end"], src0 + min(dur, slen))
    if src1 - src0 < dur * 0.6:
        src0 = max(sc["start"], sc["end"] - dur)
        src1 = sc["end"]
    beats.append({"i": i, "start": round(s0, 3), "end": round(s1, 3),
                  "src": [round(src0, 3), round(src1, 3)], "scene": sc,
                  "color_pop": bool(sc["color"]) and P["palette"].get("color_pop") not in (None, "n/a")})

# elements per beat
hook_beats = [0]
for b in beats:
    b["elements"] = []
    if b["i"] == 0:
        b["elements"] += ["hook_lockup", "freeze_slam", "occlusion", "shake"]
    elif b["i"] == 1:
        b["elements"] += ["stutter_echo"] if cap_engine == "whisper-word-sync" else ["punch_in"]
    if b["i"] in (2, 5):
        b["elements"] += ["speed_ramp"]
    if b["i"] == 3:
        b["elements"] += ["card_cascade"]
    if b["i"] == 2:
        b["elements"] += ["scramble"]
    if b["i"] == n_beats - 1:
        b["elements"] += ["payoff"]
    if b["i"] == 1:  # techniques quota
        b["elements"] += ["zoom_through"]
    if b["i"] == 4 and n_beats >= 6:
        b["elements"] += ["invert_bite"]

# hook lockup text: REAL lyric line (never invented) — FULL first sentence
if cap_engine == "whisper-word-sync":
    first_seg = whisper.get("segments", [{}])[0]
    hook_text = (first_seg.get("text") or "").strip().upper() or " ".join(w["w"] for w in group_phrases(words)[0]).upper()
    stakes_words = ["die", "dies", "homicide", "paid", "money", "kill", "end", "never", "life"]
    score = {p: (3 if any(s in hook_text.lower() for s in stakes_words) else 1) for p in
             ["stakes", "curiosity", "emotion", "rhythm", "clarity"]}
else:
    hook_text = kw[0].upper()
    score = {p: 2 for p in ["stakes", "curiosity", "emotion", "rhythm", "clarity"]}
hook_frame_t = beats[0]["src"][0] + 0.1

# card source frames (from OTHER scenes)
card_scenes = [s for s in scene_defs if s is not beats[0]["scene"]]
card_frames = []
cap = cv2.VideoCapture(RAW)
for k, sc in enumerate(card_scenes[:3]):
    fidx = int((sc["start"] + (sc["end"] - sc["start"]) * 0.5) * SRC_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
    ok, fr = cap.read()
    if ok:
        h0, w0 = fr.shape[:2]
        x, y, w, h = crop_rect["x"], crop_rect["y"], crop_rect["w"], crop_rect["h"]
        card_frames.append(fr[y:y + h, x:x + w].copy())
cap.release()

# freeze-frame matte for occlusion (single frame -> static subject during freeze, honest)
cap = cv2.VideoCapture(RAW)
cap.set(cv2.CAP_PROP_POS_FRAMES, int(hook_frame_t * SRC_FPS))
ok, hook_src = cap.read()
cap.release()
matte = None
if ok:
    crop = hook_src[crop_rect["y"]:crop_rect["y"] + crop_rect["h"], crop_rect["x"]:crop_rect["x"] + crop_rect["w"]]
    pil = Image.fromarray(cv2.cvtColor(cv2.resize(crop, (360, int(360 * crop.shape[0] / crop.shape[1]))), cv2.COLOR_BGR2RGB))
    m = matte_alpha(pil, f"{os.path.basename(RAW)}_hook")
    if m is not None and 0.03 < float((m > 128).mean()) < 0.97:
        matte = cv2.resize(m, (OW, OH), interpolation=cv2.INTER_LINEAR)

# salience track for subject-centered window — PRECOMPUTED once (no per-frame decodes)
def _salience_at(src_t, aspect, cache={}):
    """content window in crop_rect coords filling aspect, centered on smoothed subject track."""
    ch, cw = crop_rect["h"], crop_rect["w"]
    content_aspect = cw / ch
    if content_aspect > aspect:      # content wider -> window narrower
        wh = ch; ww = int(ch * aspect)
    else:
        ww = cw; wh = int(cw / aspect)
    key = "track"
    if key not in cache:
        sal_t = list(np.arange(0.0, SRC_DUR, 0.33))
        vals = []
        c = cv2.VideoCapture(RAW)
        for st in sal_t:
            c.set(cv2.CAP_PROP_POS_FRAMES, min(int(st * SRC_FPS), int(SRC_FPS * SRC_DUR) - 2))
            ok, fr = c.read()
            if ok:
                cr = fr[crop_rect["y"]:crop_rect["y"] + crop_rect["h"], crop_rect["x"]:crop_rect["x"] + crop_rect["w"]]
                vals.append(subject_centroid(cr)[0])
            else:
                vals.append(0.5)
        c.release()
        cache[key] = (sal_t, smooth_track(vals, 0.3))
    sal_t, cx_track = cache[key]
    cx = float(np.interp(src_t, sal_t, cx_track))
    cx = max(0.25, min(0.75, cx))
    x0 = int((cw - ww) * cx) if ww < cw else 0
    y0 = max(0, min(ch - wh, int(ch * 0.08))) if wh < ch else 0
    return (crop_rect["x"] + x0, crop_rect["y"] + y0, ww, wh)
window_for = _salience_at
ASPECT = OW / OH

# time warp for speed ramps (eased)
def time_warp(lt, dur, ramp_dirs, base_rate=1.0):
    """returns source-local time for output-local time lt."""
    if not ramp_dirs:
        return lt * base_rate
    # eased slow ramp in middle 40-70% of beat
    f = lt / max(dur, 0.1)
    rate = base_rate
    if 0.35 < f < 0.7:
        e = math.sin((f - 0.35) / 0.35 * math.pi)
        rate = base_rate * (0.4 + 1.2 * (1 - e)) if ramp_dirs == "slow_mid" else base_rate * (0.6 + 1.2 * e)
    return lt * rate

# ---------- audio events (SFX == entrances) ----------
events = []
for b in beats:
    events.append({"t": b["start"], "sfx": "whoosh"})
    if "freeze_slam" in b["elements"]:
        events.append({"t": b["start"] + 0.06, "sfx": "thump"})
    if "card_cascade" in b["elements"]:
        events.append({"t": b["start"] + 0.35, "sfx": "splice"})
    if "invert_bite" in b["elements"]:
        events.append({"t": b["start"] + 0.2, "sfx": "glitch"})
    if "zoom_through" in b["elements"]:
        events.append({"t": b["end"] - 0.5, "sfx": "whoosh"})
events = sorted(events, key=lambda e: e["t"])
TOTAL = cut_times[-1] + ENDCARD_S

# ---------- karaoke phrase index by time ----------
def caption_state(t):
    if cap_engine == "whisper-word-sync":
        return karaoke_state(words, t, P["captions"]["phrase_words"][0], P["captions"]["phrase_words"][1])
    # beat-keyword: keywords rotate per beat; reveal synced to beat
    for b in beats:
        if b["start"] <= t < b["end"]:
            idx = b["i"] % len(kw)
            f = (t - b["start"]) / max(b["end"] - b["start"], 0.4)
            return ("kw", kw[idx].upper(), min(1.0, f * 3.0), b["i"] == 0)
    return None

print("PLAN:", json.dumps({
    "variant": VARIANT, "ow": OW, "oh": OH, "n_beats": n_beats,
    "cut_times": cut_times, "total": round(TOTAL, 2), "cap_engine": cap_engine,
    "hook_text": hook_text, "hook_score": score, "scenes": scene_defs,
    "events": len(events), "matte": bool(matte is not None), "accent_rgb": list(ACCENT)}))
json.dump({"beats": beats, "cut_times": cut_times, "hook_text": hook_text,
           "hook_score": score, "events": events, "total": TOTAL,
           "cap_engine": cap_engine, "variant": VARIANT, "scenes": scene_defs,
           "accent_rgb": list(ACCENT)},
          open(f"{WORK}/plan_{VARIANT}.json", "w"), indent=1)

# ---------- render ----------
cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{OW}x{OH}", "-r", "30", "-i", "-",
       "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
cap = cv2.VideoCapture(RAW)
n_out = int(TOTAL * 30)
grain_bite_frames = set()

for b in beats:
    for k in range(4):
        grain_bite_frames.add(int(b["start"] * 30) + k)

prev_scene = None
seq_pos = -1        # current sequential decode position (frame idx)
seq_frame = None    # last decoded frame
def fetch_frame(fidx):
    """sequential-read fetch: seek only when moving backward; hold last frame on stall."""
    global seq_pos, seq_frame
    fidx = int(max(0, min(fidx, int(SRC_DUR * SRC_FPS) - 2)))
    if seq_frame is None or fidx < seq_pos - 2:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
        ok, fr = cap.read()
        if ok:
            seq_pos, seq_frame = fidx, fr
        return seq_frame
    while seq_pos < fidx:
        ok, fr = cap.read()
        if not ok:
            break
        seq_pos += 1
        seq_frame = fr
    return seq_frame

for oi in range(n_out):
    t = oi / 30.0
    # end card segment: loop echo + payoff
    if t >= cut_times[-1]:
        src_t = beats[0]["src"][0] + (t - cut_times[-1]) * 0.5  # loop echo 0.5x of first beat
        x, y, ww, wh = window_for(src_t, ASPECT)
        fr = fetch_frame(int(src_t * SRC_FPS))
        if fr is None:
            fr = fetch_frame(int(beats[0]["src"][0] * SRC_FPS))
        cr = fr[y:y + wh, x:x + ww]
        frame = cv2.cvtColor(cv2.resize(cr, (OW, OH)), cv2.COLOR_BGR2RGB).astype(np.float32)
        frame = add_grain(frame, 4.0)
        if (t - cut_times[-1]) > -1.0:  # payoff + repo pill persist through whole end card
            pil = Image.fromarray(frame.astype(np.uint8))
            from PIL import ImageDraw
            d = ImageDraw.Draw(pil)
            import sys as _s; _s.path.insert(0, "/home/z/my-project/scripts")
            from p14_lib import font as _font, text_w as _tw
            f1 = _font(40)
            d.text((OW // 2, int(OH * 0.42)), "THE LEAP", font=_font(64), fill=ACCENT,
                   stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
            d.text((OW // 2, int(OH * 0.54)), "LOOP", font=_font(44), fill=(255, 255, 255),
                   stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
            repo = "github.com/Dani-Devlop/edit-master-skill"
            f2 = _font(26)
            wpx = _tw(repo, f2)
            pad = 14
            x0 = (OW - wpx) // 2 - pad
            d.rounded_rectangle([x0, int(OH * 0.70), x0 + wpx + 2 * pad, int(OH * 0.70) + 46],
                                radius=12, fill=(12, 12, 12), outline=ACCENT, width=2)
            d.text((OW // 2, int(OH * 0.70) + 23), repo, font=f2, fill=(255, 255, 255), anchor="mm")
            frame = np.asarray(pil).astype(np.float32)
        proc.stdin.write(frame[:, :, :3].astype(np.uint8).tobytes())
        continue

    # find beat
    b = next((bb for bb in beats if bb["start"] <= t < bb["end"]), beats[-1])
    lt = t - b["start"]; dur = b["end"] - b["start"]
    if "speed_ramp" in b["elements"]:
        src_lt = time_warp(lt, dur, "slow_mid")
    else:
        src_lt = lt
    src_t = b["src"][0] + src_lt
    src_t = max(0.0, min(SRC_DUR - 0.05, src_t))
    if "freeze_slam" in b["elements"] and lt < 0.45:
        src_t = hook_frame_t  # freeze for slam
    fidx = int(src_t * SRC_FPS)
    fr = fetch_frame(fidx)
    if fr is None:
        fr = fetch_frame(0)
    x, y, ww, wh = window_for(src_t, ASPECT)
    # per-beat punch-in + alternating bias + luma look-shift (composition variety, G9)
    zin = 1.0 + 0.16 * (b["i"] % 2)
    tw, th = max(48, int(ww / zin)), max(48, int(wh / zin))
    bias = 0.16 if (b["i"] % 4) < 2 else -0.16
    x = x + int((ww - tw) * min(1.0, max(0.0, 0.5 + bias)))
    y = y + int((wh - th) * 0.45)
    ww, wh = tw, th
    cr = fr[y:y + wh, x:x + ww]
    frame = cv2.cvtColor(cv2.resize(cr, (OW, OH), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB).astype(np.float32)
    if b["i"] % 2 == 1:
        frame = frame * 0.92  # alternate look-shift (composition variety)
        frame = frame[:, ::-1].copy()  # mirrored composition on odd beats (G9 variety)

    # grade
    if b.get("color_pop"):
        frame = grade_color(frame)
    elif P.get("grade", {}).get("day_for_night"):
        frame = grade_day_for_night(frame)
    else:
        frame = grade_bw(frame, contrast=1.18, lift=-6) if P["palette"]["base"] == "bw" else grade_color(frame, 1.05)
    frame = add_vignette(frame, 0.22)

    # effects
    if oi in grain_bite_frames:
        frame = add_grain(frame, 7.0)
        frame = scanlines(frame, 0.15)
    if "invert_bite" in b["elements"] and lt < 0.14:
        frame = invert_bite(frame)
    if "zoom_through" in b["elements"] and lt > dur - 0.5:
        z = 1.0 + (lt - (dur - 0.5)) / 0.5 * 0.9
        frame = zoom_through_crop(frame, z)
    if lt < 0.13 and b["i"] > 0:  # whip between beats (comp change)
        frame = whip_streak(frame, direction=1 if b["i"] % 2 else -1, intensity=1 - lt / 0.13,
                            flash=0.6 * (1 - lt / 0.13))
    if "shake" in b["elements"] and lt < 0.35:
        mag = int(6 * (1 - lt / 0.35))
        frame = shake(frame, random.randint(-mag, mag), random.randint(-mag // 2, mag // 2))

    pil = Image.fromarray(frame.astype(np.uint8))
    from PIL import ImageDraw
    d = ImageDraw.Draw(pil)

    # persistent family chrome: accent beat pill + progress bar + caption underline (G13)
    fchk = font(26)
    plbl = f"{b['i']+1:02d}/{n_beats:02d}"
    d.rounded_rectangle([14, 14, 14 + text_w(plbl, fchk) + 22, 58], radius=10, fill=ACCENT)
    d.text((26, 36), plbl, font=fchk, fill=(10, 10, 10), anchor="lm")
    prog = t / TOTAL
    d.rectangle([0, 0, int(OW * prog), 8], fill=ACCENT)

    # hook lockup with occlusion (matte under text) / scramble — 2-line slam
    if b["i"] == 0 and "hook_lockup" in b["elements"]:
        prog = min(1.0, lt / 0.6)
        fhook = font(64 if cap_engine != "whisper-word-sync" else 52)
        maxw = OW * P["type"]["max_width_frac"]
        words_h = hook_text.split()
        lines_full, cur = [], ""
        for wd in words_h:
            cand = (cur + " " + wd).strip()
            if text_w(cand, fhook) > maxw and cur:
                lines_full.append(cur); cur = wd
            else:
                cur = cand
        if cur:
            lines_full.append(cur)
        n_chars = sum(len(l) for l in lines_full)
        rem = int(n_chars * prog)
        shown_lines = []
        for l in lines_full:
            take = max(0, min(len(l), rem)); rem -= take
            shown_lines.append(l[:take])
        lh = int(fhook.size * 1.12)
        ty = int(OH * 0.24)
        plate_y0, plate_y1 = ty - lh, ty + lh * (len(lines_full) - 1) + int(lh * 0.7)
        d.rectangle([int(OW * 0.03), plate_y0, int(OW * 0.97), plate_y1], fill=(8, 8, 8))
        if matte is not None:
            m3 = (matte[:, :, None] / 255.0)
            base_arr = np.asarray(pil).astype(np.float32)
            text_layer = Image.new("RGB", (OW, OH), (0, 0, 0))
            tl = ImageDraw.Draw(text_layer)
            for li, sl in enumerate(shown_lines):
                tl.text((OW // 2, ty + li * lh), sl, font=fhook, fill=ACCENT, stroke_width=3,
                        stroke_fill=(0, 0, 0), anchor="mm")
            tl_arr = np.asarray(text_layer).astype(np.float32)
            txt_mask = (tl_arr.sum(axis=2) > 40)
            # TRUE occlusion: text UNDER subject — text visible only outside subject alpha;
            # inside subject silhouette the subject pixel stays (comp = base footage)
            comp = base_arr.copy()
            vis = txt_mask & (matte <= 128)
            comp[vis] = tl_arr[vis]
            pil = Image.fromarray(comp.astype(np.uint8))
            d = ImageDraw.Draw(pil)
        else:
            for li, sl in enumerate(shown_lines):
                d.text((OW // 2, ty + li * lh), sl, font=fhook, fill=ACCENT, stroke_width=3,
                       stroke_fill=(0, 0, 0), anchor="mm")

    # cards (from OTHER scenes) tilted cascade
    if "card_cascade" in b["elements"] and card_frames:
        prog = min(1.0, max(0.0, (lt - 0.15) / 0.45))
        for k, cfr in enumerate(card_frames[:2]):
            cw2 = int(OW * 0.30)
            ch2 = int(cw2 * cfr.shape[0] / cfr.shape[1])
            cim = Image.fromarray(cv2.cvtColor(cfr, cv2.COLOR_BGR2RGB)).resize((cw2, ch2))
            rot = (-12 + k * 24)
            cim = cim.rotate(rot, expand=True, fillcolor=(10, 10, 10))
            ease = 1 - (1 - prog) ** 3
            px = int(OW * (0.08 + k * 0.52))
            py = int(OH * (0.16 + 0.02 * k)) + int((1 - ease) * 80)
            mask = Image.new("L", cim.size, int(255 * min(1.0, prog * 1.4)))
            pil.paste(cim, (px, py), mask)
            d = ImageDraw.Draw(pil)
        # pill label
        from p14_lib import font as _f2, text_w as _t2
        lbl = f"SCENE {b['i']+1:02d}"
        f3 = _f2(24)
        wpx = _t2(lbl, f3)
        d.rounded_rectangle([int(OW * 0.06), int(OH * 0.14), int(OW * 0.06) + wpx + 22, int(OH * 0.14) + 38],
                            radius=10, fill=ACCENT)
        d.text((int(OW * 0.06) + 11, int(OH * 0.14) + 19), lbl, font=f3, fill=(10, 10, 10), anchor="lm")

    # captions
    st = caption_state(t)
    if st:
        if cap_engine == "whisper-word-sync" and st[0] is not None:
            phrase, active, spoken = st
            draw_karaoke(pil, phrase, active, spoken, BAND0, BAND1, ACCENT, OW,
                         font_px=P["captions"]["font_px"], stroke=P["captions"]["stroke_px"],
                         active_scale=P["captions"]["active_scale"], dim_frac=P["captions"]["dim_frac"])
        elif st[0] == "kw":
            _, text, reveal, is_hook = st
            draw_keyword_line(pil, text, BAND0, BAND1, ACCENT, OW,
                              font_px=P["captions"]["font_px"], stroke=P["captions"]["stroke_px"],
                              reveal_frac=reveal, active=is_hook)
    # accent caption underline (family chrome, keeps accent present on caption beats)
    d = ImageDraw.Draw(pil)
    d.rectangle([int(OW * 0.28), BAND1 + 8, int(OW * 0.72), BAND1 + 14], fill=ACCENT)
    # corner brackets on odd beats (F3 grammar node brackets — composition signature)
    if b["i"] % 2 == 1:
        L, wd, off = 34, 4, 18
        for (cx, cy, sx, sy) in [(off, off, 1, 1), (OW - off, off, -1, 1),
                                 (off, OH - off, 1, -1), (OW - off, OH - off, -1, -1)]:
            d.line([(cx, cy), (cx + sx * L, cy)], fill=ACCENT, width=wd)
            d.line([(cx, cy), (cx, cy + sy * L)], fill=ACCENT, width=wd)
    frame = np.asarray(pil).astype(np.float32)
    proc.stdin.write(frame[:, :, :3].astype(np.uint8).tobytes())

cap.release()
proc.stdin.close(); proc.wait()

# ---------- audio ----------
silent_src = beatmap.get("silent", False)
audio_work = f"{WORK}/audio_mix_{VARIANT}.wav"
if silent_src or not words:
    bpm = beatmap.get("tempo_bpm", 120)
    style = P["music_plan"].get("style") or {"fitness": "drive", "food": "bright",
            "cars": "dark", "pets": "bouncy"}.get(P["genre"], "drive")
    bed = music_bed(bpm, TOTAL, style=style, energy=P["music_plan"].get("energy", 0.7))
    sfx = np.zeros_like(bed)
    for e in events:
        i0 = int(e["t"] * SR)
        g = {"whoosh": sfx_whoosh, "glitch": sfx_glitch, "splice": sfx_splice,
             "thump": sfx_thump}[e["sfx"]](dur=0.35 if e["sfx"] == "thump" else 0.5)
        g = g / (np.abs(g).max() or 1) * 0.5
        i1 = min(len(bed), i0 + len(g))
        if i1 > i0:
            sfx[i0:i1] += np.stack([g[:i1 - i0], g[:i1 - i0]], axis=1)
    # duck SFX under bed, and duck bed during "hook slam" windows
    mix = bed * 0.85 + sfx
    write_wav(audio_work, mix)
else:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", RAW, "-vn", "-ar", "44100",
                    "-ac", "2", "-t", f"{TOTAL:.3f}", f"{WORK}/orig_audio.wav"], check=True)
    import wave as _w
    wr = _w.open(f"{WORK}/orig_audio.wav", "rb")
    orig = np.frombuffer(wr.readframes(wr.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767.0
    wr.close()
    if len(orig) < int(TOTAL * SR):
        orig = np.pad(orig, ((0, int(TOTAL * SR) - len(orig)), (0, 0)))
    orig = orig[:int(TOTAL * SR)]
    sfx = np.zeros((int(TOTAL * SR), 2), np.float32)
    for e in events:
        i0 = int(e["t"] * SR)
        g = {"whoosh": sfx_whoosh, "glitch": sfx_glitch, "splice": sfx_splice,
             "thump": sfx_thump}[e["sfx"]](dur=0.35 if e["sfx"] == "thump" else 0.5)
        g = g / (np.abs(g).max() or 1) * 0.4
        i1 = min(len(orig), i0 + len(g))
        if i1 > i0:
            sfx[i0:i1, 0] += g[:i1 - i0]; sfx[i0:i1, 1] += g[:i1 - i0]
    g_duck = 10 ** (P["audio"]["sfx_duck_db"] / 20)
    mix = orig + sfx * g_duck
    write_wav(audio_work, mix)

# ---------- mux + loudnorm ----------
video_only = OUT
final = OUT.replace(".mp4", "_ln.mp4")
ln = two_pass_loudnorm(audio_work, f"{WORK}/ln_audio.aac", crest_guard=(silent_src or not words))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video_only, "-i", f"{WORK}/ln_audio.aac",
                "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", final], check=True)
os.replace(final, OUT)

# render log
log = {"preset": P["name"], "variant": VARIANT, "out": os.path.basename(OUT),
       "ow": OW, "oh": OH, "fps": 30, "duration": round(TOTAL, 3),
       "n_beats": n_beats, "cut_times": cut_times, "hook_text": hook_text,
       "hook_score": score, "cap_engine": cap_engine, "events": events,
       "matte_occlusion": matte is not None,
       "matte_note": "freeze-frame static matte (subject frozen during slam) — fps-consistent, honest"
                     if matte is not None else "matte failed -> scrim plate fallback (honest, no occlusion claim)",
       "loudnorm": ln, "source_quality": srcq["total_10"],
       "music_plan": P["music_plan"], "code_path": "p14_render.py (single path)"}
json.dump(log, open(f"{WORK}/render_log_{VARIANT}.json", "w"), indent=1)

# contact sheet (TEMP, 12 tiles)
cap = cv2.VideoCapture(OUT)
tiles = []
for tt in np.linspace(0.2, TOTAL - 0.3, 12):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(tt * 30))
    ok, fr = cap.read()
    if ok:
        fr = cv2.resize(fr, (220, int(220 * OH / OW)))
        cv2.putText(fr, f"{tt:.1f}s", (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2)
        tiles.append(fr)
cap.release()
rows = [np.hstack(tiles[i * 6:(i + 1) * 6]) for i in range(2)]
hmax = max(r.shape[0] for r in rows)
rows = [cv2.copyMakeBorder(r, 0, hmax - r.shape[0], 0, 0, cv2.BORDER_CONSTANT) for r in rows]
cv2.imwrite(f"{WORK}/contact_{VARIANT}.jpg", np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
print("RENDER DONE:", OUT, "ln:", ln)
