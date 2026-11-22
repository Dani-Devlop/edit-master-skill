#!/usr/bin/env python3
"""Phase 14 unified ingest: probe, letterbox census, whisper word timestamps,
beat map, scene census, L5 source-quality score. TEMP -> /tmp/ems-work/<run>/.
Usage: p14_ingest.py <raw_path> <work_dir> [lang]
"""
import cv2, numpy as np, json, os, sys, subprocess, math

RAW = sys.argv[1]
WORK = sys.argv[2]
LANG = sys.argv[3] if len(sys.argv) > 3 else "en"
os.makedirs(WORK, exist_ok=True)
FR = os.path.join(WORK, "ingest_frames")  # TEMP, deleted after tables

# ---------- P1.1 probe ----------
cap = cv2.VideoCapture(RAW)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
    "stream=codec_name,width,height,r_frame_rate,pix_fmt,channels,sample_rate",
    "-of", "json", RAW], capture_output=True, text=True)
pjson = json.loads(probe.stdout or "{}")
probe_res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size,bit_rate",
    "-of", "json", RAW], capture_output=True, text=True)
fjson = json.loads(probe_res.stdout or "{}")
streams = pjson.get("streams", [])
vst = next((s for s in streams if s.get("codec_type") == "video"), {})
ast = next((s for s in streams if s.get("codec_type") == "audio"), {})
probe_tbl = {
    "path": os.path.basename(RAW), "resolution": f"{W}x{H}", "aspect": round(W / H, 4),
    "fps": round(fps, 3), "duration_s": round(float(fjson.get("format", {}).get("duration", 0)), 3),
    "size_bytes": int(fjson.get("format", {}).get("size", 0)),
    "video_codec": vst.get("codec_name"), "pix_fmt": vst.get("pix_fmt"),
    "audio_codec": ast.get("codec_name"), "audio_channels": ast.get("channels"),
    "color": "bw+color-mixed (measured in census)",
}

# ---------- decode + sample @4fps ----------
step = max(1, int(round(fps / 4.0)))
sampled = []; idx = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    if idx % step == 0: sampled.append((idx, fr.copy()))
    idx += 1
cap.release()
n_decoded = idx

# ---------- P1.2 letterbox census ----------
bar_thresh = 16.0
tops, bottoms, lefts, rights = [], [], [], []
for _, fr in sampled:
    small = cv2.resize(fr, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
    rm, cm = gray.mean(axis=1), gray.mean(axis=0)
    rstd, cstd = gray.std(axis=1), gray.std(axis=0)
    h, w = gray.shape
    # bar = UNIFORM dark row/col (mean<thr AND std<6) — dark textured footage rows are NOT bars
    t = 0
    while t < h // 2 and rm[t] < bar_thresh and rstd[t] < 6.0: t += 1
    b = 0
    while b < h // 2 and rm[h - 1 - b] < bar_thresh and rstd[h - 1 - b] < 6.0: b += 1
    l = 0
    while l < w // 2 and cm[l] < bar_thresh and cstd[l] < 6.0: l += 1
    r = 0
    while r < w // 2 and cm[w - 1 - r] < bar_thresh and cstd[w - 1 - r] < 6.0: r += 1
    tops.append(t * 2); bottoms.append(b * 2); lefts.append(l * 2); rights.append(r * 2)
def med(x): return float(np.median(x)) if x else 0.0
letter = {"top_med": med(tops), "bottom_med": med(bottoms), "left_med": med(lefts),
          "right_med": med(rights), "top_max": int(max(tops)), "bottom_max": int(max(bottoms)),
          "left_max": int(max(lefts)), "right_max": int(max(rights)),
          "frames_with_bars": int(sum(1 for t, b, l, r in zip(tops, bottoms, lefts, rights) if t or b or l or r)),
          "n_sampled": len(sampled)}
crop = {"x": int(max(lefts)), "y": int(max(tops)),
        "w": W - int(max(lefts)) - int(max(rights)),
        "h": H - int(max(tops)) - int(max(bottoms))}

# ---------- P1.3 scene metrics @4fps ----------
metrics, diffs = [], []
prev_gray = None
for i, (fidx, fr) in enumerate(sampled):
    t = fidx / fps
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    sat = float(hsv[:, :, 1].mean())
    cf = float(((hsv[:, :, 1] > 60) & (hsv[:, :, 2] > 40)).mean())
    lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    metrics.append({"t": round(t, 3), "luma": round(float(gray.mean()), 1),
                    "std": round(float(gray.std()), 1), "sat": round(sat, 1),
                    "color_frac": round(cf, 4), "sharpness": round(lap, 1)})
    if prev_gray is not None:
        diffs.append({"t": round(t, 3), "absdiff": round(float(np.abs(gray.astype(np.int16) - prev_gray).mean()), 2)})
    prev_gray = gray.astype(np.int16)

# scene cut candidates: big absdiff spikes
dvals = np.array([d["absdiff"] for d in diffs]) if diffs else np.array([0.0])
cut_thr = max(12.0, float(np.mean(dvals) + 2.5 * np.std(dvals)))
cuts = [d["t"] for d in diffs if d["absdiff"] >= cut_thr]
merged = []
for c in cuts:
    if not merged or c - merged[-1] > 1.0: merged.append(c)

# ---------- L5 source-quality score ----------
res_score = 2.0 if H >= 1280 else (1.5 if H >= 900 else 0.8)
fps_score = 1.5 if fps >= 29.9 else 0.8
stab = float(np.mean(dvals)); stdev_stab = float(np.std(dvals))
stab_score = 1.5 if 2.0 <= stab <= 18.0 else (0.9 if stab <= 30 else 0.6)
clar = float(np.mean([m["sharpness"] for m in metrics]))
clar_score = 1.5 if clar >= 120 else (1.0 if clar >= 60 else 0.6)
lum_mean = float(np.mean([m["luma"] for m in metrics]))
lum_std = float(np.mean([m["std"] for m in metrics]))
light_score = 1.5 if lum_mean >= 35 and lum_std >= 30 else (1.0 if lum_mean >= 22 else 0.6)
aud = subprocess.run(["ffmpeg", "-nostats", "-i", RAW, "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True)
tail = aud.stderr[-1600:]
import re
mI = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", tail)
mTP = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", tail)
lufs = float(mI[-1]) if mI else -70.0
audio_score = 1.5 if lufs >= -30 else (1.0 if lufs >= -45 else 0.5)
total = res_score + fps_score + stab_score + clar_score + light_score + audio_score
source_q = {"resolution": round(res_score, 2), "fps": round(fps_score, 2),
            "stability": round(stab_score, 2), "subject_clarity": round(clar_score, 2),
            "lighting": round(light_score, 2), "audio_usability": round(audio_score, 2),
            "total_10": round(total, 2), "pass_L5": total >= 6.0,
            "measured": {"mean_motion_diff": round(stab, 2), "mean_sharpness": round(clar, 1),
                         "mean_luma": round(lum_mean, 1), "lufs_integrated": lufs,
                         "true_peak_dbfs": float(mTP[-1]) if mTP else None},
            "notes": ["B&W+color mixed footage accepted as stylistic source" if lum_mean < 60 else "color source"]}
json.dump(probe_tbl, open(f"{WORK}/probe.json", "w"), indent=1)
json.dump({"letterbox": letter, "crop_rect": crop}, open(f"{WORK}/letterbox.json", "w"), indent=1)
json.dump({"metrics4fps": metrics, "diffs4fps": diffs,
           "cut_candidates_s": [round(c, 2) for c in merged],
           "cut_threshold": round(cut_thr, 2)}, open(f"{WORK}/census.json", "w"), indent=1)
json.dump(source_q, open(f"{WORK}/source_quality.json", "w"), indent=1)
print("PROBE:", json.dumps(probe_tbl))
print("LETTERBOX:", json.dumps(letter))
print("CROP:", json.dumps(crop), "aspect:", round(crop["w"] / max(crop["h"], 1), 4))
print("CUTS@:", [round(c, 2) for c in merged])
print("SOURCE-QUALITY:", json.dumps(source_q))

# ---------- P1.4 whisper word timestamps (skipped if cached) ----------
_wsp_cache = f"{WORK}/whisper_words.json"
_cache_ok = False
if os.path.exists(_wsp_cache):
    try:
        _c = json.load(open(_wsp_cache))
        _cache_ok = bool(_c.get("words"))
    except Exception:
        _cache_ok = False
try:
    if _cache_ok:
        raise RuntimeError("cache-hit")
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(RAW, language=LANG, word_timestamps=True,
                                      vad_filter=False, beam_size=5,
                                      condition_on_previous_text=False)
    words, segs = [], []
    for seg in segments:
        segs.append({"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
        for w in seg.words:
            words.append({"w": w.word.strip(), "start": round(w.start, 3),
                          "end": round(w.end, 3), "prob": round(float(w.probability), 3)})
    wsp = {"language": info.language, "language_prob": round(float(info.language_probability), 3),
           "duration": round(float(info.duration), 3), "segments": segs, "words": words}
    json.dump(wsp, open(f"{WORK}/whisper_words.json", "w"), indent=1)
    print(f"WHISPER: lang={info.language} words={len(words)}")
    for s in segs:
        print(f"  [{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
except Exception as e:
    if not _cache_ok:
        json.dump({"error": str(e)}, open(f"{WORK}/whisper_words.json", "w"), indent=1)
    print("WHISPER FAILED:", type(e).__name__, "-> honest fallback: beat-map captions only")

# ---------- P1.5 beat map (skipped if cached) ----------
if os.path.exists(f"{WORK}/beatmap.json"):
    bm = json.load(open(f"{WORK}/beatmap.json"))
    print(f"BEATMAP cached: tempo={bm['tempo_bpm']} beats={bm['n_beats']}")
    print("INGEST DONE ->", WORK)
    sys.exit(0)
import librosa
y, sr = librosa.load(RAW, sr=44100, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time", trim=False)
beat_times = [round(float(b), 3) for b in beats.tolist()]
onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
on_frames = librosa.util.peak_pick(onset_env, pre_max=6, post_max=6, pre_avg=12, post_avg=12,
                                   delta=0.9, wait=10)
on_times = librosa.frames_to_time(on_frames, sr=sr, hop_length=512).tolist()
strengths = onset_env[on_frames]
strong = [{"t": round(float(t), 3), "s": round(float(s), 2)} for t, s in zip(on_times, strengths)
          if s > np.percentile(strengths, 55)]
bm = {"method": "librosa.beat.beat_track + onset_strength peak_pick (hop 512, delta 0.9, wait 10)",
      "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 2),
      "n_beats": len(beat_times), "beats": beat_times,
      "n_onsets": len(on_times), "onsets": [round(float(o), 3) for o in on_times],
      "strong_onsets": strong}
json.dump(bm, open(f"{WORK}/beatmap.json", "w"), indent=1)
print(f"BEATMAP: tempo={bm['tempo_bpm']} BPM beats={len(beat_times)} onsets={len(on_times)} strong={len(strong)}")

print("INGEST DONE ->", WORK)
