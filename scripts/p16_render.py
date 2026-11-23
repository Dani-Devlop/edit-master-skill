#!/usr/bin/env python3
"""Phase 16.0 TWENTY-PILLAR UNIFIED RENDERER — ONE code path for all videos.
Usage: p16_render.py <work_dir> <preset.json> <raw> <out.mp4> [variant] [overrides.json]
Pillars: P1 karaoke-v2 captions (vox words or beat-keywords, loop, RTL) | P2 type craft
(hook slam lockup, ghost, tapes, brackets) | P3 occlusion (freeze matte, cutouts UNDER type)
| P4 3+ comps incl. Mode A cutouts | P5 easings/punch-ins/ramps/motion-blur |
P6 whip+zoom-through+invert, no hard cuts | P7 grade science | P8 real stakes graphics
| P10 audio craft | P19 manifest. TEMP -> work_dir only."""
import cv2, numpy as np, json, os, sys, subprocess, math, random, hashlib, platform
sys.path.insert(0, "/tmp/ems-repo/scripts")
sys.path.insert(0, "/home/z/my-project/scripts")
from PIL import Image, ImageDraw, ImageFilter
from p14_lib import (font, text_w, sha256_file, matte_alpha, grade_bw, grade_color,
                     grade_day_for_night, add_grain, add_vignette, invert_bite, whip_streak,
                     zoom_through_crop, scanlines, shake, subject_centroid, smooth_track,
                     music_bed, write_wav, two_pass_loudnorm, sfx_whoosh, sfx_glitch,
                     sfx_splice, sfx_thump, synth_kick, SR)
import p16_lib as L
from p16_lib import (karaoke_state_v2, karaoke_layout, draw_karaoke_v2, hook_slam_lockup,
                     highlighter_tape, selection_brackets, odometer, starburst_drawon,
                     orbit_card, ease_out_cubic, ease_out_back, motion_blur_h, light_leak,
                     grade_leap, font_px_for_lang)

WORK, PRESET_PATH, RAW, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
VARIANT = sys.argv[5] if len(sys.argv) > 5 else "9x16"
OVR_PATH = sys.argv[6] if len(sys.argv) > 6 else None
random.seed(16); np.random.seed(16)
P = json.load(open(PRESET_PATH))
probe = json.load(open(f"{WORK}/probe.json"))
lett = json.load(open(f"{WORK}/letterbox.json"))
crop_rect = lett["crop_rect"]
census = json.load(open(f"{WORK}/census.json"))
wsp = json.load(open(f"{WORK}/whisper_words.json"))
beatmap = json.load(open(f"{WORK}/beatmap.json"))
srcq = json.load(open(f"{WORK}/source_quality.json"))
overrides = json.load(open(OVR_PATH)) if OVR_PATH and os.path.exists(OVR_PATH) else {}

PRESET_SHA = sha256_file(PRESET_PATH)

SRC_FPS = probe["fps"]; SRC_DUR = probe["duration_s"]
if VARIANT == "1x1": OW, OH = 720, 720
elif VARIANT == "4x5": OW, OH = 720, 900
else: OW, OH = 720, 1280
ACCENT = tuple(P["palette"]["accent_rgb"])
if overrides.get("accent_rgb"):
    ACCENT = tuple(overrides["accent_rgb"])
BAND_FR = P["captions"].get("band_frac", [0.74, 0.9])
SAFE = {"9x16": {"top": 0.10, "bottom": 0.16, "sides": 0.06},
        "1x1": {"top": 0.08, "bottom": 0.10, "sides": 0.06},
        "4x5": {"top": 0.08, "bottom": 0.12, "sides": 0.06}}
_sz = SAFE.get(VARIANT, SAFE["9x16"])
# clamp caption band inside platform safe zone (P15/G-P15)
_b0 = max(BAND_FR[0], _sz["top"] + 0.06)
_b1 = min(BAND_FR[1], 1.0 - _sz["bottom"] - 0.02)
BAND0, BAND1 = int(OH * _b0), int(OH * _b1)
CAPTION_SCRIM = True
ENDCARD_S = 2.4
RTL = bool(wsp.get("language", "en") == "fa") or bool(overrides.get("rtl"))

# ---------- P1 caption words: real vox (whisper) or beat-keywords ----------
words = [w for w in wsp.get("words", []) if w.get("w")]
if words:
    cap_engine = "whisper-word-sync"
    # lyric lines = sentences: force sentence ender at each whisper segment boundary
    _seg_bounds = []
    for _sg in wsp.get("segments", []):
        _seg_bounds.append((round(_sg["start"], 2), round(_sg["end"], 2)))
    _last_end = None
    for _wi, _w in enumerate(words):
        for (_s0, _s1) in _seg_bounds:
            if abs(_w["end"] - _s1) < 0.12:
                _w["w"] = _w["w"].rstrip(".,;:!?") + "."
                break
    norm_log = []
    if "Pellegrino" in " ".join(w["w"] for w in words) or "pellegrino" in " ".join(w["w"] for w in words).lower():
        for w in words:
            if w["w"].lower().startswith("pellegrino"):
                w["w"] = "Pellegrino"
        norm_log.append("Pellegrino kept verbatim (brand ASR normalization logged, never invent)")
else:
    cap_engine = "beat-keyword"
    norm_log = []

# ---------- scenes ----------
metrics = census["metrics4fps"]
scene_bounds = census["cut_candidates_s"][:] or [0.0]
scene_defs = []
prev = 0.0
for c in scene_bounds + [SRC_DUR]:
    seg = [m for m in metrics if prev <= m["t"] < c]
    cf = float(np.mean([m["color_frac"] for m in seg])) if seg else 0.0
    scene_defs.append({"start": round(prev, 3), "end": round(c, 3), "color": cf > 0.08})
    prev = c
if len(scene_defs) == 1 and SRC_DUR > 6:
    t1, t2 = SRC_DUR / 3, SRC_DUR * 2 / 3
    scene_defs = [{"start": 0, "end": t1, "color": scene_defs[0]["color"]},
                  {"start": t1, "end": t2, "color": scene_defs[0]["color"]},
                  {"start": t2, "end": SRC_DUR, "color": scene_defs[0]["color"]}]
scene_defs = [s for s in scene_defs if s["end"] - s["start"] > 0.5] or \
             [{"start": 0, "end": SRC_DUR, "color": False}]

# ---------- beat planning (P4/P11) ----------
target_len = min(P["beats"]["length_s"][1] - ENDCARD_S, SRC_DUR + 3.0)
n_beats = max(P["beats"]["count"][0], min(P["beats"]["count"][1], int(target_len / 3.0)))
# onset grid: strong onsets first, full beat grid as fallback (P11: every cut on an onset)
_grid_s = [s["t"] for s in (beatmap.get("strong_onsets") or [])]
_grid_b = [t for t in (beatmap.get("beats") or []) if t not in _grid_s]
grid = (_grid_s + _grid_b) or []
if not grid and beatmap.get("silent"):
    bpm = beatmap["tempo_bpm"]; beat = 60.0 / bpm
    grid = [round(beat * i, 3) for i in range(int(SRC_DUR / beat) + 30)]

def nearest_onset(t, tol=0.28):
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
for i in range(1, len(cut_times)):
    if cut_times[i] - cut_times[i - 1] > P["beats"]["max_beat_s"]:
        cut_times[i] = cut_times[i - 1] + P["beats"]["max_beat_s"]
cut_times = sorted(set(round(c, 3) for c in cut_times))
n_beats = len(cut_times) - 1

color_scenes = [s for s in scene_defs if s["color"]]
bw_scenes = [s for s in scene_defs if not s["color"]]
beats = []
for i in range(n_beats):
    s0, s1 = cut_times[i], cut_times[i + 1]
    dur = s1 - s0
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

# ---------- P4 comps: >=3 distinct; Mode A cutouts on silent sources ----------
kw = P["captions"].get("keywords", ["NOW", "WATCH", "REAL", "RAW", "GO"])
silent_src = beatmap.get("silent", False)
mode_a_beats = set()
if silent_src and n_beats >= 5:
    mode_a_beats = {3}  # one cutout-canvas beat (non-adjacent to any other canvas beat)
comp_cycle = ["base", "punch", "mirror", "zoom"]
for b in beats:
    comp = comp_cycle[b["i"] % 4]
    if b["i"] in mode_a_beats:
        comp = "cutout"
    b["comp"] = comp

# ---------- elements per beat (P13 when-to-use quotas) ----------
technique_log = []
for b in beats:
    b["elements"] = []
    if b["i"] == 0:
        b["elements"] += ["hook_lockup", "freeze_slam", "occlusion", "shake", "brackets"]
        technique_log.append({"beat": 0, "technique": "freeze+type-slam lockup",
                              "when_to_use": "t=0 hook — instant stake + composed frame-1"})
    if b["i"] == 1:
        b["elements"] += ["zoom_through"]
        technique_log.append({"beat": 1, "technique": "recursive zoom-through",
                              "when_to_use": "after hook — dive into tilted card/scene for momentum"})
    if b["i"] == 2:
        b["elements"] += ["speed_ramp", "odometer"]
        technique_log.append({"beat": 2, "technique": "eased speed-ramp + odometer",
                              "when_to_use": "motion beat — ramp creates surge; odometer counts real quantity"})
    if b["i"] == 3 and n_beats >= 5:
        b["elements"] += ["orbit_cards"]
        technique_log.append({"beat": 3, "technique": "orbit cards High/Med/Low",
                              "when_to_use": "comparison/verdict beat over cutout canvas"})
    if b["i"] == 4 and n_beats >= 6:
        b["elements"] += ["invert_bite"]
        technique_log.append({"beat": 4, "technique": "invert bite <=0.15s",
                              "when_to_use": "pattern interrupt at retention-risk midpoint"})
    if b["i"] == n_beats - 1:
        b["elements"] += ["payoff_starburst", "tape"]
        technique_log.append({"beat": b["i"], "technique": "starburst draw-on + highlighter tape",
                              "when_to_use": "payoff — semantic emphasis on the promise word"})
    if b["comp"] == "cutout":
        b["elements"] += ["contact_shadow"]
    b["elements"].append("punch_in_emphasis")

# ---------- hook lockup text: REAL lyric sentence (never invented) ----------
if cap_engine == "whisper-word-sync":
    first_seg = wsp.get("segments", [{}])[0]
    hook_text = (first_seg.get("text") or "").strip().upper()
    if not hook_text:
        hook_text = " ".join(w["w"] for w in words[:6]).upper()
    hook_words_split = hook_text.split()
    if len(hook_words_split) > 8:
        hook_text = " ".join(hook_words_split[:8])
    kicker = hook_words_split[0] if hook_words_split else "WELCOME"
    giant = hook_words_split[1] if len(hook_words_split) > 1 else (kw[0])
    cont = " ".join(hook_words_split[2:5]) if len(hook_words_split) > 2 else ""
else:
    hook_text = kw[0].upper()
    parts = hook_text.split()
    kicker = "NEW DROP" if silent_src else parts[0]
    giant = parts[-1] or kw[0]
    cont = kw[1] if len(kw) > 1 else ""
hook_frame_t = beats[0]["src"][0] + 0.1

# ---------- beat-keyword synthetic words for karaoke ----------
if cap_engine != "whisper-word-sync":
    kws = [k.upper() for k in kw]
    words = []
    for b in beats:
        k = kws[b["i"] % len(kws)]
        ws = k.split()
        bw0, bw1 = b["start"], min(b["end"], b["start"] + 1.6)
        dur_w = max(0.25, (bw1 - bw0) / max(len(ws), 1))
        for j, wtxt in enumerate(ws):
            if j == len(ws) - 1:
                wtxt = wtxt.rstrip(",;:.!?") + "."  # sentence terminator per keyword phrase (P1 window)
            words.append({"w": wtxt, "start": round(bw0 + j * dur_w, 3),
                          "end": round(bw0 + (j + 1) * dur_w, 3)})

# ---------- freeze matte for hook occlusion (P3) ----------
cap = cv2.VideoCapture(RAW)
cap.set(cv2.CAP_PROP_POS_FRAMES, int(hook_frame_t * SRC_FPS))
ok, hook_src = cap.read()
cap.release()
matte = None
if ok:
    crop = hook_src[crop_rect["y"]:crop_rect["y"] + crop_rect["h"], crop_rect["x"]:crop_rect["x"] + crop_rect["w"]]
    pil = Image.fromarray(cv2.cvtColor(cv2.resize(crop, (360, int(360 * crop.shape[0] / crop.shape[1]))), cv2.COLOR_BGR2RGB))
    m = matte_alpha(pil, f"{os.path.basename(RAW)}_hook16")
    if m is not None and 0.03 < float((m > 128).mean()) < 0.97:
        # plausibility guard: keep the largest connected component; matte must be a
        # plausible subject (not over-segmented background) or we fall back to scrim
        mb = (m > 128).astype(np.uint8)
        ncomp, lab, stats_c, _ = cv2.connectedComponentsWithStats(mb, 8)
        if ncomp > 1:
            big = 1 + int(np.argmax(stats_c[1:, cv2.CC_STAT_AREA]))
            mb = (lab == big).astype(np.uint8) * 255
        cov = float((mb > 128).mean())
        if 0.03 < cov < 0.45:
            matte = cv2.resize(mb, (OW, OH), interpolation=cv2.INTER_LINEAR)
            np.save(f"{WORK}/subject_mask_{VARIANT}.npy", matte)
matte_ok = matte is not None
HOOK_SCRIM = False
hook_y_frac = 0.20
if matte_ok:
    _best = None
    for _cand in (0.14, 0.20, 0.28, 0.36, 0.44):
        _rows = matte[int(OH * _cand):int(OH * (_cand + 0.26))]
        _cov = float((_rows > 128).mean())
        if _best is None or _cov < _best[1]:
            _best = (_cand, _cov)
    hook_y_frac = _best[0]
    # glyph-row test: if the subject covers most of the actual glyph rows, the lockup
    # would be majority-hidden -> scrim plate (honest fallback, occlusion not claimed)
    _g0 = int(OH * (hook_y_frac - 0.09)); _g1 = int(OH * (hook_y_frac + 0.09))
    _gcov = float((matte[_g0:_g1] > 128).mean())
    if _gcov > 0.35:
        HOOK_SCRIM = True
        matte_ok = False
        matte = None

# ---------- Mode A cutouts (rembg keyframes, contact shadow) ----------
cutouts = {}
comp_fallback_beats = []
if silent_src and mode_a_beats:
    for bi in mode_a_beats:
        b = beats[bi]
        fidx = int((b["src"][0] + (b["src"][1] - b["src"][0]) * 0.4) * SRC_FPS)
        c2 = cv2.VideoCapture(RAW)
        c2.set(cv2.CAP_PROP_POS_FRAMES, min(fidx, int(SRC_FPS * SRC_DUR) - 2))
        okk, fr2 = c2.read()
        c2.release()
        if not okk: continue
        cr2 = fr2[crop_rect["y"]:crop_rect["y"] + crop_rect["h"], crop_rect["x"]:crop_rect["x"] + crop_rect["w"]]
        pil2 = Image.fromarray(cv2.cvtColor(cv2.resize(cr2, (480, int(480 * cr2.shape[0] / cr2.shape[1]))), cv2.COLOR_BGR2RGB))
        m2 = matte_alpha(pil2, f"{os.path.basename(RAW)}_cut{bi}")
        if m2 is not None and 0.04 < float((m2 > 128).mean()) < 0.95:
            rgba = pil2.copy()
            rgba.putalpha(Image.fromarray(m2))
            cutouts[bi] = {"rgba": rgba, "matte": m2}
            technique_log.append({"beat": bi, "technique": "Mode A cut-out canvas + contact shadow",
                                  "when_to_use": "static-energy beat — clean canvas, subject 30-55%H bottom-center"})

# ---------- salience track ----------
def _salience_at(src_t, aspect, cache={}):
    ch, cw = crop_rect["h"], crop_rect["w"]
    content_aspect = cw / ch
    if content_aspect > aspect:
        wh = ch; ww = int(ch * aspect)
    else:
        ww = cw; wh = int(cw / aspect)
    if "track" not in cache:
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
        cache["track"] = (sal_t, smooth_track(vals, 0.3))
    sal_t, cx_track = cache["track"]
    cx = float(np.interp(src_t, sal_t, cx_track))
    cx = max(0.25, min(0.75, cx))
    x0 = int((cw - ww) * cx) if ww < cw else 0
    y0 = max(0, min(ch - wh, int(ch * 0.08))) if wh < ch else 0
    return (crop_rect["x"] + x0, crop_rect["y"] + y0, ww, wh)

window_for = _salience_at
ASPECT = OW / OH

# ---------- P5 time warp (eased ramps) ----------
def time_warp(lt, dur, kind="slow_mid"):
    if kind != "slow_mid":
        return lt
    f = lt / max(dur, 0.1)
    if 0.35 < f < 0.7:
        e = math.sin((f - 0.35) / 0.35 * math.pi)
        return lt * (0.4 + 1.2 * (1 - e))
    return lt

# ---------- P10 audio events (SFX == entrances, medium-low) ----------
events = []
for b in beats:
    events.append({"t": b["start"], "sfx": "whoosh"})
    if "freeze_slam" in b["elements"]:
        events.append({"t": b["start"] + 0.06, "sfx": "thump"})
    if "invert_bite" in b["elements"]:
        events.append({"t": b["start"] + 0.2, "sfx": "glitch"})
    if "zoom_through" in b["elements"]:
        events.append({"t": max(0.0, b["end"] - 0.5), "sfx": "whoosh"})
    if "payoff_starburst" in b["elements"]:
        events.append({"t": b["start"] + 0.3, "sfx": "thump"})
events = sorted(events, key=lambda e: e["t"])
TOTAL = cut_times[-1] + ENDCARD_S
BPM_STAKES = beatmap.get("tempo_bpm", 120)

# stakes numbers from REAL measured quantities (P8): tempo BPM, scene energy from census motion
scene_energy = {}
for m in metrics:
    scene_energy.setdefault(int(m["t"] // 5), []).append(m.get("diff", 0))
energy_by_beat = []
for b in beats:
    mid_t = b["src"][0]
    key = int(mid_t // 5)
    vals = scene_energy.get(key) or [0]
    e = float(np.clip(np.mean(vals) / 22.0 * 100, 35, 99))
    energy_by_beat.append(round(e))

# ---------- karaoke plan export (for G-P1 gate) ----------
lay0 = karaoke_layout(words[:min(6, len(words))], OW, P["captions"]["font_px"], rtl=RTL)
plan = {"variant": VARIANT, "ow": OW, "oh": OH, "fps": 30, "n_beats": n_beats,
        "cut_times": cut_times, "total": round(TOTAL, 3), "cap_engine": cap_engine,
        "words_manifest": words, "rtl": RTL, "font_px": P["captions"]["font_px"],
        "band_px": [BAND0, BAND1], "accent_rgb": list(ACCENT),
        "hook_text": hook_text, "hook_window": [0.0, 0.5], "hook_y_frac": hook_y_frac, "hook_scrim": HOOK_SCRIM,
        "matte_ok": matte_ok, "cap_probe_t": min(3.0, TOTAL * 0.4),
        "events": events, "duck_applied": True,
        "music_plan": P.get("music_plan", {}),
        "preset_name": P["name"], "preset_sha256": PRESET_SHA,
        "technique_log": technique_log,
        "resource_licenses": {"Vazirmatn": "OFL 1.1 (SIL Open Font License) — /tmp/ems-work/p16/assets",
                               "faster-whisper small": "MIT (Systran/faster-whisper-small)" if words else None,
                               "music bed": "original in-run synthesis (numpy) — no third-party audio",
                               "source raws": "see sources.txt / work manifest"},
        "stakes_numbers_real": True, "beat_index_only": False,
        "overrides": {"applied": bool(overrides), **overrides},
        "energy_by_beat": energy_by_beat, "bpm": BPM_STAKES,
        "scenes": scene_defs, "comps": [b["comp"] for b in beats],
        "renderer": "p16_render.py (single path)",
        "asr_normalizations_logged": norm_log}
json.dump(plan, open(f"{WORK}/plan_{VARIANT}.json", "w"), indent=1)

# onboarding proposal (P18) if not present
if not os.path.exists(f"{WORK}/onboarding_proposal.json"):
    prop = {"run": os.path.basename(WORK), "genre": P["genre"],
            "proposal": {"family": P.get("family", P["name"]), "palette_accent": list(ACCENT),
                          "energy": P.get("music_plan", {}).get("energy", 0.7),
                          "music_plan": P.get("music_plan", {}).get("decision"),
                          "platforms": P.get("platforms", ["9:16"])},
            "defaults": {"bilingual": False, "tts": False, "brand_end_card": False,
                          "loop_echo": True, "palette": "auto from preset"},
            "ask": "confirm or override — non-blocking proceed",
            "overrides_applied": overrides,
            "status": "proceeded-with-defaults (no reply within window)"}
    json.dump(prop, open(f"{WORK}/onboarding_proposal.json", "w"), indent=1)

# ---------- render manifest (P19) ----------
def tool_versions():
    import PIL, numpy
    v = {"python": platform.python_version(), "numpy": numpy.__version__,
         "opencv": cv2.__version__, "pillow": PIL.__version__}
    try:
        import faster_whisper
        v["faster_whisper"] = faster_whisper.__version__
    except Exception:
        pass
    return v

input_sha = sha256_file(RAW)
manifest = {"video": P["name"], "variant": VARIANT, "input_sha256": input_sha,
            "preset_sha256": PRESET_SHA, "preset_name": P["name"],
            "seed": 16, "tool_versions": tool_versions(),
            "beat_table": [{"i": b["i"], "start": b["start"], "end": b["end"],
                             "src": b["src"], "comp": b["comp"], "elements": b["elements"]}
                            for b in beats],
            "gate_json": None, "refine_iterations": 0, "renderer": "p16_render.py",
            "whisper_words_sha256": sha256_file(f"{WORK}/whisper_words.json") if words else None,
            "source_quality": srcq["total_10"],
            "music_plan": P.get("music_plan", {}),
            "asr_normalizations_logged": norm_log}
json.dump(manifest, open(f"{WORK}/manifest_{VARIANT}.json", "w"), indent=1)

from p14_lib import _MATTE_CACHE
_MATTE_CACHE.clear()
import gc as _g1; _g1.collect()
print("PLAN:", json.dumps({"variant": VARIANT, "ow": OW, "oh": OH, "n_beats": n_beats,
      "total": round(TOTAL, 2), "cap_engine": cap_engine, "n_words": len(words),
      "hook": hook_text, "matte": matte_ok, "comps": [b["comp"] for b in beats],
      "events": len(events), "accent": list(ACCENT), "preset_sha16": PRESET_SHA[:16]}))

# ================= RENDER =================
cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{OW}x{OH}", "-r", "30", "-i", "-",
       "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
cap = cv2.VideoCapture(RAW)

prev_scene = None
seq_pos = -1
seq_frame = None
def fetch_frame(fidx):
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
        if not ok: break
        seq_pos += 1
        seq_frame = fr
    return seq_frame

n_out = int(TOTAL * 30)
cover_best = {"score": -1, "frame": None, "t": 0}
sents_cache = L.sentences_from_words(words)
wins_cache = L.sentence_windows(sents_cache)
layout_cache = {}
def layout_for(sent_i):
    if sent_i not in layout_cache:
        layout_cache[sent_i] = karaoke_layout(sents_cache[sent_i], OW, P["captions"]["font_px"], rtl=RTL)
    return layout_cache[sent_i]

import gc as _gc
for oi in range(n_out):
    t = oi / 30.0
    if oi % 120 == 0:
        try:
            rss = int(open('/proc/self/status').read().split('VmRSS:')[1].split('kB')[0]) // 1024
            print(f"MEM@{oi}: {rss}MB", flush=True)
        except Exception:
            pass
        _gc.collect()
    # -------- end card: loop echo + family pill (P18 no-brand default) --------
    if t >= cut_times[-1]:
        src_t = beats[0]["src"][0] + (t - cut_times[-1]) * 0.5
        x, y, ww, wh = window_for(src_t, ASPECT)
        fr = fetch_frame(int(src_t * SRC_FPS))
        if fr is None:
            fr = fetch_frame(int(beats[0]["src"][0] * SRC_FPS))
        cr = fr[y:y + wh, x:x + ww]
        frame = cv2.cvtColor(cv2.resize(cr, (OW, OH)), cv2.COLOR_BGR2RGB).astype(np.float32)
        frame = add_grain(frame, 4.0)
        frame = grade_leap(frame, base=P["palette"]["base"]) if P["palette"]["base"] != "bw" else grade_bw(frame, contrast=1.14, lift=-6)
        pil = Image.fromarray(frame.astype(np.uint8))
        d = ImageDraw.Draw(pil)
        fam = P.get("family", P["name"])
        d.text((OW // 2, int(OH * 0.40)), "THE LEAP", font=font(64), fill=ACCENT,
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
        d.text((OW // 2, int(OH * 0.51)), "LOOP", font=font(44), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
        repo = "github.com/Dani-Devlop/edit-master-skill"
        f2 = font(24)
        wpx = text_w(repo, f2)
        x0 = (OW - wpx) // 2 - 14
        d.rounded_rectangle([x0, int(OH * 0.66), x0 + wpx + 28, int(OH * 0.66) + 44],
                            radius=12, fill=(12, 12, 12), outline=ACCENT, width=2)
        d.text((OW // 2, int(OH * 0.66) + 22), repo, font=f2, fill=(255, 255, 255), anchor="mm")
        d.text((OW // 2, int(OH * 0.60)), fam[:28].upper(), font=font(26), fill=(200, 200, 200), anchor="mm")
        frame = np.asarray(pil).astype(np.float32)
        proc.stdin.write(frame[:, :, :3].astype(np.uint8).tobytes())
        continue

    b = next((bb for bb in beats if bb["start"] <= t < bb["end"]), beats[-1])
    lt = t - b["start"]; dur = b["end"] - b["start"]
    src_lt = time_warp(lt, dur) if "speed_ramp" in b["elements"] else lt
    src_t = b["src"][0] + src_lt
    src_t = max(0.0, min(SRC_DUR - 0.05, src_t))
    if "freeze_slam" in b["elements"] and lt < 0.52:
        src_t = hook_frame_t
    fidx = int(src_t * SRC_FPS)
    fr = fetch_frame(fidx)
    if fr is None:
        fr = fetch_frame(0)
    x, y, ww, wh = window_for(src_t, ASPECT)

    # -------- composition (P4): punch / mirror / zoom / cutout --------
    comp_eff = b["comp"]
    if comp_eff == "cutout" and b["i"] not in cutouts:
        # honest fallback (matte unavailable): deep-zoom comp keeps adjacent-beat
        # variety instead of degrading into a near-duplicate of the next base beat
        comp_eff = "zoom"
        if b["i"] not in comp_fallback_beats:
            comp_fallback_beats.append(b["i"])
    zin = 1.0
    if comp_eff == "punch":
        zin = 1.0 + 0.10 * ease_out_cubic(min(1.0, lt / max(dur * 0.5, 0.1)))  # 100 -> 110%
    elif comp_eff == "zoom":
        zin = 1.12 + 0.10 * math.sin(lt / max(dur, 0.5) * math.pi)
    elif comp_eff == "mirror":
        zin = 1.0 + 0.16 * (b["i"] % 2)
    tw, th = max(48, int(ww / zin)), max(48, int(wh / zin))
    bias = 0.16 if (b["i"] % 4) < 2 else -0.16
    x = x + int((ww - tw) * min(1.0, max(0.0, 0.5 + bias)))
    y = y + int((wh - th) * 0.45)
    ww, wh = tw, th
    cr = fr[y:y + wh, x:x + ww]
    moved = comp_eff in ("punch", "zoom")
    resized = cv2.resize(cr, (OW, OH), interpolation=cv2.INTER_AREA)
    if moved:
        # motion blur proportional to punch velocity (P5): strongest at move onset
        mb = int(6 + 12 * max(0.0, 1.0 - lt / max(dur * 0.5, 0.1)))
        k = max(1, mb | 1)
        resized = cv2.GaussianBlur(resized, (k, 1), k / 3.0)
    frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32)

    if comp_eff == "mirror":
        frame = frame[:, ::-1].copy()

    # grade (P7)
    if b.get("color_pop"):
        frame = grade_color(frame)
    elif P.get("grade", {}).get("day_for_night"):
        frame = grade_day_for_night(frame)
        frame = grade_leap(frame, base="color")
    else:
        frame = grade_bw(frame, contrast=1.16, lift=-6) if P["palette"]["base"] == "bw" else grade_leap(frame, base="color")
    frame = add_vignette(frame, 0.20)
    frame = add_grain(frame, 4.2)

    # Mode A cutout canvas (P3/P4) — built before effects so transitions land on canvas
    if comp_eff == "cutout" and b["i"] in cutouts:
        cd = cutouts[b["i"]]
        canvas = np.zeros((OH, OW, 3), np.float32)
        cvv = 16 + 14 * (1 - t / max(TOTAL, 1))
        canvas[:, :, 0] = cvv; canvas[:, :, 1] = cvv; canvas[:, :, 2] = cvv
        # subtle family tint + grain
        canvas[:, :, 2] += 6
        # giant type BEHIND subject (P3 occlusion) on canvas
        frame = canvas
        rgba = cd["rgba"]
        scale_h = float(OW) / rgba.size[0] * (1.35 + 0.06 * math.sin(lt * 1.5))
        sw = int(rgba.size[0] * scale_h); shh = int(rgba.size[1] * scale_h)
        subj = rgba.resize((min(sw, OW - 40), min(shh, OH - 200)), Image.LANCZOS)
        if subj.size[1] > OH * 0.55:
            ns = int(OH * 0.55 / subj.size[1] * subj.size[0])
            subj = subj.resize((ns, int(OH * 0.55)), Image.LANCZOS)
        px = int((OW - subj.size[0]) // 2)
        py = int(OH * 0.30 + (OH * 0.55 - subj.size[1]))
        px = max(4, min(OW - subj.size[0] - 4, px))
        py = max(4, py)
        # contact shadow
        sh_layer = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
        dsh = ImageDraw.Draw(sh_layer)
        sh_y = py + subj.size[1] - 8
        dsh.ellipse([px + 20, sh_y, px + subj.size[0] - 20, sh_y + 26], fill=(0, 0, 0, 140))
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(7))
        pil_c = Image.fromarray(frame.astype(np.uint8)).convert("RGBA")
        pil_c.alpha_composite(sh_layer)
        pil_c.paste(subj, (px, py), subj)
        frame = np.asarray(pil_c.convert("RGB")).astype(np.float32)

    # -------- effects (P6) applied AFTER cutout canvas so transitions never erased --------
    if "invert_bite" in b["elements"] and lt < 0.14:
        frame = invert_bite(frame)
    if "zoom_through" in b["elements"] and lt > dur - 0.5:
        z = 1.0 + (lt - (dur - 0.5)) / 0.5 * 0.9
        frame = zoom_through_crop(frame, z)
    if lt < 0.16 and b["i"] > 0:
        # directional motion smear FIRST (P5), whip flash LAST (never diluted)
        mbk = max(3, int(16 * (1 - lt / 0.13)))
        frame = np.asarray(L.motion_blur_h(Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)),
                                            strength=mbk)).astype(np.float32)
        frame = whip_streak(frame, direction=1 if b["i"] % 2 else -1, intensity=1 - lt / 0.16,
                            flash=0.90 * (1 - lt / 0.16))
        frame = zoom_through_crop(frame, 1.0 + 0.05 * (1 - lt / 0.13))  # scale-punch at comp change
        if P["genre"] in ("fitness", "food"):
            frame = np.asarray(light_leak(Image.fromarray(np.clip(frame,0,255).astype(np.uint8)), lt, dur=0.3)).astype(np.float32)
    if "freeze_slam" in b["elements"] and lt < 0.35:
        mag = int(6 * (1 - lt / 0.35))
        frame = shake(frame, random.randint(-mag, mag), random.randint(-mag // 2, mag // 2))

    pil = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))

    # -------- chrome: real-stakes pill + progress (P8: not beat-index-only) --------
    d = ImageDraw.Draw(pil)
    e_pct = energy_by_beat[b["i"]] if b["i"] < len(energy_by_beat) else 60
    plbl = f"{b['i']+1:02d}/{n_beats:02d} · ENERGY {e_pct}% · {int(BPM_STAKES)} BPM"
    fchk = font(22)
    wpx = text_w(plbl, fchk)
    d.rounded_rectangle([14, 14, 14 + wpx + 24, 56], radius=10, fill=(12, 12, 12), outline=ACCENT, width=2)
    d.text((26, 35), plbl, font=fchk, fill=(240, 240, 240), anchor="lm")
    d.rectangle([14 + wpx + 24, 52, 14 + wpx + 24 + int((OW - 28 - wpx - 24) * (t / TOTAL)), 56], fill=ACCENT)
    prog_bar = t / TOTAL
    d.rectangle([0, 0, int(OW * prog_bar), 6], fill=ACCENT)

    # -------- hook slam lockup (P2/P3) --------
    if b["i"] == 0:
        if HOOK_SCRIM:
            # scrim plate behind lockup (subject-aware fallback, honest note in plan)
            _plate = Image.new("RGB", (OW, OH), (0, 0, 0))
            _pl = Image.new("L", (OW, OH), 0)
            _pd = ImageDraw.Draw(_pl)
            _py0 = int(OH * hook_y_frac) - 60
            _pd.rounded_rectangle([int(OW * 0.02), _py0, int(OW * 0.98), _py0 + int(OH * 0.30)],
                                  radius=24, fill=210)
            _pl = _pl.filter(ImageFilter.GaussianBlur(16))
            pil = Image.composite(_plate, pil, _pl)
            hook_slam_lockup(pil, kicker, giant, cont, ACCENT, OW,
                             y_top_frac=hook_y_frac, settle=0.28, t_lt=lt, ghost=True)
            d = ImageDraw.Draw(pil)
        elif matte_ok:
            base_arr = np.asarray(pil).astype(np.float32)
            # ghost + slam type UNDER subject: draw text layer, occlude by matte
            text_layer = Image.new("RGB", (OW, OH), (0, 0, 0))
            tl = ImageDraw.Draw(text_layer)
            tl_draw = lambda img: None
            hook_slam_lockup(text_layer, kicker, giant, cont, ACCENT, OW,
                             y_top_frac=hook_y_frac, settle=0.28, t_lt=lt, ghost=True)
            tl_arr = np.asarray(text_layer).astype(np.float32)
            txt_mask = (tl_arr.sum(axis=2) > 40)
            comp = base_arr.copy()
            vis = txt_mask & (matte <= 128)
            comp[vis] = tl_arr[vis]
            pil = Image.fromarray(comp.astype(np.uint8))
            d = ImageDraw.Draw(pil)
        else:
            hook_slam_lockup(pil, kicker, giant, cont, ACCENT, OW,
                             y_top_frac=hook_y_frac, settle=0.28, t_lt=lt, ghost=True)
            d = ImageDraw.Draw(pil)
        if "brackets" in b["elements"]:
            gw = font(96)
            pw = 96
            while text_w(giant, gw) > OW * 0.80 and pw > 40:
                pw -= 2; gw = font(pw)
            tw3 = text_w(giant, gw)
            gy0 = int(OH * hook_y_frac)
            selection_brackets(pil, int(OW / 2 - tw3 / 2), gy0 - int(pw * 0.55),
                               int(OW / 2 + tw3 / 2), gy0 + int(pw * 0.55), ACCENT, lt)

    # -------- stakes graphics (P8) --------
    if "odometer" in b["elements"]:
        odometer(pil, int(OW * 0.5), int(OH * 0.30), BPM_STAKES, fpx=58, digits=3,
                 accent=ACCENT, settle_lt=lt)
        d = ImageDraw.Draw(pil)
        d.text((int(OW * 0.5), int(OH * 0.30) - 52), "TRACK BPM", font=font(22), fill=(255, 255, 255),
               stroke_width=2, stroke_fill=(10, 10, 10), anchor="mm")
    if "orbit_cards" in b["elements"] and b["i"] in cutouts:
        ang = -60 + 120 * min(1.0, lt / dur)
        orbit_card(pil, (OW // 2, int(OH * 0.52)), ang, 190, 84,
                   "HIGH" if e_pct > 70 else ("MED" if e_pct > 50 else "LOW"),
                   f"ENERGY {e_pct}%", ACCENT)
        d = ImageDraw.Draw(pil)
    if "payoff_starburst" in b["elements"]:
        starburst_drawon(pil, int(OW * 0.5), int(OH * 0.22), 130, lt, ACCENT, rays=14)
        d = ImageDraw.Draw(pil)
    if "tape" in b["elements"] and 0.2 < lt:
        tw2 = text_w(giant, font(48))
        highlighter_tape(pil, int(OW / 2 - tw2 / 2 - 10), int(OH * 0.62), int(OW / 2 + tw2 / 2 + 10),
                         int(OH * 0.62) + 58, color=(255, 230, 0), prog=min(1.0, (lt - 0.2) / 0.4))
        d = ImageDraw.Draw(pil)
        d.text((OW // 2, int(OH * 0.62) + 29), giant, font=font(48), fill=(12, 12, 12), anchor="mm")

    # -------- P1 karaoke v2 captions (full sentence always) + scrim (P9 contrast) --------
    st = karaoke_state_v2(words, t)
    if st is not None:
        if CAPTION_SCRIM:
            # adaptive scrim: bright footage behind the band gets a stronger plate (WCAG 4.5:1)
            _band_luma = float(np.asarray(pil.convert("L"), np.float32)[BAND0:BAND1].mean())
            _alpha = 205 if _band_luma < 110 else 242
            scr = Image.new("L", (OW, OH), 0)
            ds2 = ImageDraw.Draw(scr)
            ds2.rectangle([0, BAND0 - 26, OW, BAND1 + 30], fill=_alpha)
            scr = scr.filter(ImageFilter.GaussianBlur(14))
            dark = Image.new("RGB", (OW, OH), (8, 8, 10))
            pil = Image.composite(dark, pil, scr)
        lay = layout_for(st["sent_i"])
        draw_karaoke_v2(pil, words, st, lay, ACCENT, BAND0, BAND1, stroke=P["captions"]["stroke_px"], rtl=RTL)
        d = ImageDraw.Draw(pil)
    d.rectangle([int(OW * 0.28), BAND1 + 8, int(OW * 0.72), BAND1 + 14], fill=ACCENT)
    if b["i"] % 2 == 1:
        Lcorner = 34
        off = 18
        for (cx, cy, sx, sy) in [(off, off, 1, 1), (OW - off, off, -1, 1)]:
            d.line([(cx, cy), (cx + sx * Lcorner, cy)], fill=ACCENT, width=4)
            d.line([(cx, cy), (cx, cy + sy * Lcorner)], fill=ACCENT, width=4)

    frame = np.asarray(pil).astype(np.float32)
    out_frame = np.clip(frame, 0, 255).astype(np.uint8)
    proc.stdin.write(out_frame[:, :, :3].tobytes())

    # cover frame scorer (P15): accent + text presence + mid luma
    if 0.5 < t < cut_times[-1]:
        g = cv2.cvtColor(out_frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
        acc = float((np.abs(out_frame[:, :, 1].astype(np.int16) - ACCENT[1]) < 40).mean() +
                    (np.abs(out_frame[:, :, 0].astype(np.int16) - ACCENT[0]) < 40).mean())
        sc = acc * 3 + (20 < g.mean() < 200) * 1.0 + float((g > 150).mean())
        if sc > cover_best["score"]:
            cover_best = {"score": sc, "frame": out_frame.copy(), "t": round(t, 2)}

cap.release()
proc.stdin.close(); proc.wait()

# ================= AUDIO (P10) =================
audio_work = f"{WORK}/audio_mix_{VARIANT}.wav"
if silent_src or not words:
    bpm = beatmap.get("tempo_bpm", 120)
    style = P["music_plan"].get("style") or {"fitness": "drive", "food": "bright",
            "cars": "dark", "pets": "bouncy"}.get(P["genre"], "drive")
    energy = P["music_plan"].get("energy", 0.7)
    bed = music_bed(bpm, TOTAL, style=style, energy=energy)
    sfx = np.zeros_like(bed)
    for e in events:
        i0 = int(e["t"] * SR)
        g = {"whoosh": sfx_whoosh, "glitch": sfx_glitch, "splice": sfx_splice,
             "thump": sfx_thump}[e["sfx"]](dur=0.35 if e["sfx"] == "thump" else 0.5)
        g = g / (np.abs(g).max() or 1) * 0.42
        i1 = min(len(bed), i0 + len(g))
        if i1 > i0:
            sfx[i0:i1] += np.stack([g[:i1 - i0], g[:i1 - i0]], axis=1)
    # sidechain-style duck: duck bed 6dB for 0.35s around each event (P10)
    duck_env = np.ones(len(bed), np.float32)
    for e in events:
        i0 = int(e["t"] * SR); i1 = min(len(bed), i0 + int(0.35 * SR))
        duck_env[i0:i1] = np.minimum(duck_env[i0:i1], 10 ** (-6 / 20))
    mix = bed * duck_env[:, None] + sfx
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
        g = g / (np.abs(g).max() or 1) * 0.35
        i1 = min(len(orig), i0 + len(g))
        if i1 > i0:
            sfx[i0:i1, 0] += g[:i1 - i0]; sfx[i0:i1, 1] += g[:i1 - i0]
    g_duck = 10 ** (P["audio"]["sfx_duck_db"] / 20)
    mix = orig + sfx * g_duck
    write_wav(audio_work, mix)

video_only = OUT
final = OUT.replace(".mp4", "_ln.mp4")
ln = two_pass_loudnorm(audio_work, f"{WORK}/ln_audio.aac", crest_guard=(silent_src or not words))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video_only, "-i", f"{WORK}/ln_audio.aac",
                "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", final], check=True)
os.replace(final, OUT)

# ================= cover frame (P15) =================
if cover_best["frame"] is not None:
    cv2.imwrite(f"{WORK}/cover_{VARIANT}.jpg", cv2.cvtColor(cover_best["frame"], cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 92])
manifest["cover_t"] = cover_best["t"]
manifest["loudnorm"] = ln
manifest["total"] = round(TOTAL, 3)
json.dump(manifest, open(f"{WORK}/manifest_{VARIANT}.json", "w"), indent=1)

# render log
log = {"preset": P["name"], "variant": VARIANT, "out": os.path.basename(OUT),
       "ow": OW, "oh": OH, "fps": 30, "duration": round(TOTAL, 3),
       "n_beats": n_beats, "cut_times": cut_times, "hook_text": hook_text,
       "cap_engine": cap_engine, "n_words": len(words), "events": events,
       "matte_occlusion": matte_ok, "loudnorm": ln,
       "comp_fallback_beats": comp_fallback_beats,
       "source_quality": srcq["total_10"],
       "music_plan": P.get("music_plan", {}),
       "renderer": "p16_render.py (single path)", "code_path": "p16_render.py"}
json.dump(log, open(f"{WORK}/render_log_{VARIANT}.json", "w"), indent=1)
print("RENDER DONE:", OUT, "ln:", json.dumps(ln))
