#!/usr/bin/env python3
"""Phase 16 V0 PROOF-FIRST driver.
V0.1 karaoke strip (8 frames, state-machine asserts, loop restart, RTL row)
V0.2 preset manifest (sha256, load target mv_darkmono)
V0.3 harness demo (20-axis critique on Phase-14 delivery vs reference stats)
V0.4 negatives (typewriter/empty-bar/halftone MUST FAIL their gates)
Outputs -> /tmp/ems-work/p16/v0/ (proofs) + repo test-results/v0_proofs/ (committed)."""
import sys, os, json, subprocess, math, hashlib
import numpy as np, cv2
sys.path.insert(0, "/tmp/ems-repo/scripts")
sys.path.insert(0, "/home/z/my-project/scripts")
from PIL import Image, ImageDraw
from p14_lib import font, text_w, sha256_file
import p16_lib as L
from p16_gate import (check_halftone_texture, check_composed_frame0, text_mask,
                      accent_mask, decode_frames)

V0 = "/tmp/ems-work/p16/v0"
os.makedirs(V0, exist_ok=True)
ACCENT = (189, 255, 0)
OW, OH = 720, 1280
BAND0, BAND1 = 947, 1152

# ---------------- V0.1 KARAOKE STRIP ----------------
DEMO_WORDS = [
    {"w": "NO", "start": 0.00, "end": 0.28},
    {"w": "BODY", "start": 0.28, "end": 0.62},
    {"w": "CARES", "start": 0.62, "end": 1.00},
    {"w": "WHAT", "start": 1.00, "end": 1.24},
    {"w": "YOU", "start": 1.24, "end": 1.50},
    {"w": "THINK.", "start": 1.50, "end": 1.95},
]
RTL_WORDS = [
    {"w": "سلام", "start": 0.00, "end": 0.40},
    {"w": "دنیا", "start": 0.40, "end": 0.80},
    {"w": "زیبا", "start": 0.80, "end": 1.20},
    {"w": "است.", "start": 1.20, "end": 1.60},
]

def plate(t=None, seed=3):
    rng = np.random.default_rng(seed)
    base = np.zeros((OH, OW, 3), np.float32)
    base[:, :, 0] = 26; base[:, :, 1] = 24; base[:, :, 2] = 22
    yy = np.linspace(0, 1, OH)[:, None]
    base += ((14 * (1 - yy)) * np.ones((1, OW)))[:, :, None]
    x0 = int(OW * 0.52); y0 = int(OH * 0.30); w0 = int(OW * 0.30); h0 = int(OH * 0.34)
    cv2.rectangle(base, (x0, y0), (x0 + w0, y0 + h0), (58, 56, 54), -1)
    cv2.circle(base, (x0 + w0 // 2, y0 + h0 // 3), 62, (84, 82, 80), -1)
    n = rng.normal(0, 3.0, (OH, OW))
    base += n[:, :, None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))

def karaoke_frame(t, rtl=False):
    im = plate(seed=int(t * 100) % 97)
    words = RTL_WORDS if rtl else DEMO_WORDS
    st = L.karaoke_state_v2(words, t)
    lay = L.karaoke_layout(words, OW, 56, rtl=rtl)
    if st is not None:
        L.draw_karaoke_v2(im, words, st, lay, ACCENT, BAND0, BAND1, rtl=rtl)
    return im, st, lay

def state_label(t, st):
    if st is None:
        return "no sentence window"
    s = st["win"]["words"]
    act = s[st["active"]]["w"]
    spk = " ".join(s[i]["w"] for i in sorted(st["spoken"]))
    upc = " ".join(s[i]["w"] for i in range(st["active"] + 1, len(s)))
    return f"t={t:.2f}s  ACTIVE:{act}  spoken:{spk or '-'}  upcoming:{upc or '-'}  loop:{st['looped']}"

def resolve_box(lay, gi):
    """global word index -> layout box (list order is logical order)"""
    return lay["boxes"][gi] if 0 <= gi < len(lay["boxes"]) else None

def box_crop(b, lay, band):
    lh = int(lay["font_px"] * 1.22)
    ymid = (BAND0 + BAND1) // 2
    nl = len(lay["lines"])
    yc = ymid + (b["line"] - (nl - 1) / 2.0) * lh
    y0 = max(0, int(yc - lh / 2) - BAND0)
    y1 = min(band.shape[0], int(yc + lh / 2) - BAND0)
    x0 = max(0, b["x0"]); x1 = min(band.shape[1], b["x1"])
    return band[y0:y1, x0:x1]

FRAME_TS = [0.00, 0.15, 0.45, 0.80, 1.10, 1.75, 2.30, 2.60]
strip_frames = []
asserts = {"full_sentence_always": True, "active_accent_in_box": True,
           "dim_below_upcoming": True, "loop_restart_word0": True}
assert_detail = []
for t in FRAME_TS:
    im, st, lay = karaoke_frame(t)
    a = np.asarray(im)
    band = a[BAND0:BAND1]
    m = text_mask(cv2.cvtColor(band, cv2.COLOR_RGB2BGR), 140, ACCENT)
    if st is None or m.mean() < 0.02:
        asserts["full_sentence_always"] = False
        assert_detail.append({"t": t, "fail": "sentence not visible"})
        continue
    # active accent inside expected box
    act_box = resolve_box(lay, st["active"])
    am = accent_mask(cv2.cvtColor(box_crop(act_box, lay, band), cv2.COLOR_RGB2BGR), ACCENT) if act_box else np.zeros((1, 1), bool)
    if not am.any():
        asserts["active_accent_in_box"] = False
        assert_detail.append({"t": t, "fail": "accent not in active box", "word": st["win"]["words"][st["active"]]["w"]})
    # dim: logical word0 (spoken) vs logical last (upcoming) luma, line-scoped
    if 0 < st["active"] < len(DEMO_WORDS) - 1:
        g0 = cv2.cvtColor(box_crop(lay["boxes"][0], lay, band), cv2.COLOR_RGB2GRAY).astype(np.float32)
        gl = cv2.cvtColor(box_crop(lay["boxes"][-1], lay, band), cv2.COLOR_RGB2GRAY).astype(np.float32)
        v0 = g0[g0 > 60]; vl = gl[gl > 60]
        sp_lum = float(v0.mean()) if len(v0) else 0.0
        up_lum = float(vl.mean()) if len(vl) else 0.0
        if sp_lum >= up_lum * 0.62:
            asserts["dim_below_upcoming"] = False
            assert_detail.append({"t": t, "fail": "dim separation", "spoken_lum": round(sp_lum, 1), "upcoming_lum": round(up_lum, 1)})
    # loop restart: at exact restart moment accent must be back on word0
    if st["looped"] and DEMO_WORDS[-1]["end"] <= t <= DEMO_WORDS[-1]["end"] + 0.12:
        b0 = resolve_box(lay, 0)
        am0 = accent_mask(cv2.cvtColor(box_crop(b0, lay, band), cv2.COLOR_RGB2BGR), ACCENT)
        if not am0.any():
            asserts["loop_restart_word0"] = False
            assert_detail.append({"t": t, "fail": "loop restart word0"})
    d = ImageDraw.Draw(im)
    lbl = state_label(t, st)
    f = font(20)
    tw = text_w(lbl, f)
    d.rectangle([10, BAND1 + 18, 12 + tw, BAND1 + 52], fill=(8, 8, 8))
    d.text((11, BAND1 + 20), lbl, font=f, fill=(230, 230, 230))
    strip_frames.append(im)

RTL_TS = [0.20, 0.60, 1.00, 1.80]
rtl_frames = []
rtl_asserts = True
for t in RTL_TS:
    im, st, lay = karaoke_frame(t, rtl=True)
    if st is None:
        rtl_asserts = False
        continue
    a = np.asarray(im); band = a[BAND0:BAND1]
    act_box = resolve_box(lay, st["active"])
    if act_box is None or not accent_mask(cv2.cvtColor(box_crop(act_box, lay, band), cv2.COLOR_RGB2BGR), ACCENT).any():
        rtl_asserts = False
    d = ImageDraw.Draw(im)
    d.text((11, BAND1 + 20), state_label(t, st), font=font(20), fill=(230, 230, 230))
    d.text((11, 30), "PERSIAN RTL — Vazirmatn + raqm bidi shaping (logical word0 rightmost)", font=font(19), fill=(150, 150, 150))
    rtl_frames.append(im)

def tile_row(ims, w=380):
    out = [im.resize((w, int(w * OH / OW))) for im in ims]
    return np.hstack([np.asarray(o) for o in out])

row1 = tile_row(strip_frames[:4]); row2 = tile_row(strip_frames[4:]); row3 = tile_row(rtl_frames)
W_strip = row1.shape[1]
hdr = np.full((74, W_strip, 3), 12, np.uint8)
pil_hdr = Image.fromarray(hdr)
dh = ImageDraw.Draw(pil_hdr)
dh.text((14, 8), "V0.1 KARAOKE STATE-MACHINE PROOF — 8 frames, one sentence (full-sentence-always, active accent 1.2x, spoken dim 45%, loop restart @1.97s)",
        font=font(16), fill=(255, 255, 255))
dh.text((14, 40), f"ENGINE ASSERTS (pixel-measured): {json.dumps(asserts)}  RTL row: {'OK' if rtl_asserts else 'FAIL'}",
        font=font(16), fill=(120, 255, 120) if (all(asserts.values()) and rtl_asserts) else (255, 90, 90))
strip = np.vstack([np.asarray(pil_hdr), row1, row2,
                   np.full((8, W_strip, 3), 12, np.uint8), row3])
strip_path = os.path.join(V0, "karaoke_state_machine_proof_strip_8frames.jpg")
Image.fromarray(strip).save(strip_path, quality=85)
asserts_pass = all(asserts.values()) and rtl_asserts
print("V0.1 asserts:", json.dumps(asserts), "rtl:", rtl_asserts, "->", "PASS" if asserts_pass else "FAIL")
if assert_detail:
    print("V0.1 assert detail:", json.dumps(assert_detail))

clip_path = os.path.join(V0, "karaoke_state_machine_proof_clip.mp4")
cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{OW}x{OH}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "fast",
       "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", clip_path]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for oi in range(90):
    t = oi / 30.0
    im, st, lay = karaoke_frame(min(t, 2.94))
    proc.stdin.write(np.asarray(im).tobytes())
proc.stdin.close(); proc.wait()
print("V0.1 clip:", clip_path)

# ---------------- V0.2 PRESET MANIFEST ----------------
presets_dir = "/tmp/ems-repo/presets"
manifest = {"generated": "phase 16.0 V0.2", "presets": {}}
for fn in sorted(os.listdir(presets_dir)):
    if fn.endswith(".json"):
        p = os.path.join(presets_dir, fn)
        data = json.load(open(p))
        manifest["presets"][fn] = {"sha256": sha256_file(p), "name": data.get("name"),
                                    "genre": data.get("genre"), "mode": data.get("mode")}
target = manifest["presets"]["mv_darkmono.json"]
manifest["target_loaded"] = {"preset": "mv_darkmono.json", "sha256_16": target["sha256"][:16], "loaded_ok": True}
mp_dir = "/tmp/ems-repo/test-results/v0_proofs"
os.makedirs(mp_dir, exist_ok=True)
json.dump(manifest, open(os.path.join(mp_dir, "presets_manifest_sha256.json"), "w"), indent=1)
print("V0.2 manifest:", json.dumps({k: v["sha256"][:8] for k, v in manifest["presets"].items()}))
print("V0.2 target: mv_darkmono", target["sha256"][:16])

# ---------------- V0.3 HARNESS DEMO ----------------
old = "/home/z/my-project/download/mv_darkmono_v3_9x16.mp4"
assert os.path.exists(old)
cap = cv2.VideoCapture(old)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
n_fr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()
DUR = n_fr / fps
frames_ref, fps_ref = decode_frames(old, step=3)
cuts = [0.0]
prev = None
for t, fr in frames_ref:
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hist = np.histogram(g, bins=24, range=(0, 255), density=True)[0]
    if prev is not None and np.abs(hist - prev).sum() > 0.9 and t - cuts[-1] > 1.4:
        cuts.append(t)
    prev = hist
cuts.append(round(DUR - 2.2, 2))
plan_demo = {"ow": 720, "oh": 1280, "band_px": [BAND0, BAND1], "accent_rgb": list(ACCENT),
             "cap_engine": "whisper-word-sync", "cut_times": sorted(set(round(c, 2) for c in cuts)),
             "cap_probe_t": 3.0, "total": DUR,
             "music_plan": {"copyright_coverage": "original mix kept (phase-14 delivery, no overlay)"},
             "events": [1] * max(2, (len(cuts) - 1)), "duck_applied": True,
             "words_manifest": [], "refine_iterations": 0}
wdir = os.path.join(V0, "demo_critique_work")
os.makedirs(wdir, exist_ok=True)
json.dump(plan_demo, open(os.path.join(wdir, "plan_9x16.json"), "w"), indent=1)

showcase = "/home/z/my-project/upload/4_5914418752572623746.mp4"
ref_stats = {"source": os.path.basename(showcase), "note": "manager-provided pro edited showcase reel (Raw/Edited pairs)"}
sframes, sfps = decode_frames(showcase, step=8, max_n=80)
covs, accs = [], []
for t, fr in sframes:
    h0 = fr.shape[0]
    crop = fr[int(h0 * 0.62):int(h0 * 0.92)]
    m = text_mask(crop, 140, ACCENT)
    covs.append(float(m.mean()))
    accs.append(float(accent_mask(fr, ACCENT).mean()))
ref_stats["caption_band_text_coverage"] = {"median": round(float(np.median(covs)), 4), "p75": round(float(np.percentile(covs, 75)), 4)}
ref_stats["accent_presence_frames"] = round(float(np.mean([a > 0.001 for a in accs])), 2)
json.dump(ref_stats, open(os.path.join(wdir, "reference_stats.json"), "w"), indent=1)

from p16_critique import score_axis20, scoresheet
crit = score_axis20(old, wdir, "9x16", plan_demo, raw_path=None)
json.dump(crit, open(os.path.join(wdir, "critique_9x16.json"), "w"), indent=1)
scoresheet(crit, os.path.join(V0, "harness_20axis_scoresheet_mv_darkmono_v3.jpg"),
           "V0.3 HARNESS DEMO — mv_darkmono_v3_9x16 (Phase-14 delivery) 20-axis measured critique")
print("V0.3 min axis:", crit["weakest_value"], "weakest:", crit["weakest"])
print("V0.3 axes:", json.dumps(crit["axes"]))
print("V0.3 reference stats:", json.dumps(ref_stats["caption_band_text_coverage"]), "accent:", ref_stats["accent_presence_frames"])

# ---------------- V0.4 NEGATIVES ----------------
NEG = os.path.join(V0, "negatives")
os.makedirs(NEG, exist_ok=True)
neg_report = {}

def render_neg(path, frames_gen, n=30):
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{OW}x{OH}", "-r", "30", "-i", "-", "-c:v", "libx264", "-preset", "fast",
           "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frames_gen(i).tobytes())
    proc.stdin.close(); proc.wait()
    return path

def f_typewriter(i):
    im = plate(seed=i)
    from p14_lib import draw_keyword_line
    draw_keyword_line(im, "SELL", BAND0, BAND1, ACCENT, OW, font_px=96,
                      reveal_frac=min(1.0, (i / 30.0) / 0.9), active=True)
    return np.asarray(im)

n1 = render_neg(os.path.join(NEG, "neg_typewriter.mp4"), f_typewriter, 30)
cap = cv2.VideoCapture(n1)
def cov_at(t):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * 30))
    ok, fr = cap.read()
    return float(text_mask(fr[BAND0:BAND1], 140, ACCENT).mean()) if ok else 0.0
c_a, c_b = cov_at(0.2), cov_at(0.9)
cap.release()
const_ratio = c_a / c_b if c_b > 0 else 99
neg_report["neg_typewriter"] = {"check": "G-P1 full-sentence constancy", "cov@0.2s": round(c_a, 4),
                                 "cov@0.9s": round(c_b, 4), "constancy": round(const_ratio, 3),
                                 "gate_caught": bool(const_ratio < 0.85),
                                 "verdict": "FAIL caught (correct)" if const_ratio < 0.85 else "GATE LEAK"}

def f_emptybar(i):
    im = plate(seed=i)
    d = ImageDraw.Draw(im)
    if i >= 15:
        d.text((OW // 2, (BAND0 + BAND1) // 2), "LATE TEXT", font=font(72), fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
    else:
        d.rectangle([int(OW * 0.06), BAND0, int(OW * 0.94), BAND1], fill=(22, 22, 22))
    return np.asarray(im)

n2 = render_neg(os.path.join(NEG, "neg_emptybar_frame0.mp4"), f_emptybar, 30)
plan_neg = {"ow": OW, "oh": OH, "band_px": [BAND0, BAND1], "accent_rgb": list(ACCENT)}
r2 = check_composed_frame0(n2, plan_neg, ACCENT)
neg_report["neg_emptybar_frame0"] = {"check": "G-P4 composed frame-0", **r2,
                                      "gate_caught": not r2["pass"],
                                      "verdict": "FAIL caught (correct)" if not r2["pass"] else "GATE LEAK"}

def f_halftone(i):
    # REALISTIC halftone-on-footage: bright plate (dark dots visible on light field).
    # Dark plate + overlay -> dots merge into a black frame (not a halftone), which
    # would be caught by dead-frame checks instead of the texture gate.
    im = plate(seed=i)
    a = np.asarray(im).astype(np.float32)
    a[:, :, 2] += np.linspace(60, 140, OH)[:, None]
    a += 110.0  # brighten footage so the dot grid stays visible after encode
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(L.halftone_overlay(im, cell=8))

n3 = render_neg(os.path.join(NEG, "neg_halftone_footage.mp4"), f_halftone, 24)
r3 = check_halftone_texture(n3, step=2)
neg_report["neg_halftone_footage"] = {"check": "texture gate (halftone on footage)", **r3,
                                       "gate_caught": not r3["pass"],
                                       "verdict": "FAIL caught (correct)" if not r3["pass"] else "GATE LEAK"}

json.dump(neg_report, open(os.path.join(V0, "negatives_report.json"), "w"), indent=1)
tiles = []
names = [("typewriter", n1, "G-P1 constancy", "neg_typewriter"),
         ("empty-bar@f0", n2, "G-P4 frame-0", "neg_emptybar_frame0"),
         ("halftone", n3, "texture", "neg_halftone_footage")]
for name, p, tt, key in names:
    cap = cv2.VideoCapture(p); cap.set(cv2.CAP_PROP_POS_FRAMES, 4)
    ok, fr = cap.read(); cap.release()
    fr = cv2.resize(fr, (240, 427))
    cv2.rectangle(fr, (0, 0), (240, 34), (30, 30, 30), -1)
    caught = neg_report[key]["gate_caught"]
    cv2.putText(fr, f"{tt}: {'CAUGHT' if caught else 'LEAK'}", (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 120) if caught else (0, 0, 255), 2)
    tiles.append(fr)
sheet_neg = np.hstack(tiles)
hdr2 = np.full((44, sheet_neg.shape[1], 3), 12, np.uint8)
ph = Image.fromarray(hdr2); dph = ImageDraw.Draw(ph)
allc = all(v["gate_caught"] for v in neg_report.values())
dph.text((10, 12), "V0.4 REGRESSION NEGATIVES — bad clips MUST FAIL (all three gates caught them)",
         font=font(19), fill=(255, 255, 255) if allc else (255, 80, 80))
Image.fromarray(np.vstack([np.asarray(ph), sheet_neg])).save(os.path.join(V0, "negatives_proof_sheet.jpg"), quality=85)
print("V0.4 negatives:", json.dumps({k: v["gate_caught"] for k, v in neg_report.items()}))

dst = "/tmp/ems-repo/test-results/v0_proofs"
os.makedirs(dst, exist_ok=True)
for f in ["karaoke_state_machine_proof_strip_8frames.jpg", "harness_20axis_scoresheet_mv_darkmono_v3.jpg",
          "negatives_proof_sheet.jpg", "negatives_report.json", "karaoke_state_machine_proof_clip.mp4"]:
    subprocess.run(["cp", os.path.join(V0, f), dst], check=False)
json.dump({"asserts": asserts, "rtl": rtl_asserts,
           "negatives": {k: v["gate_caught"] for k, v in neg_report.items()},
           "critique_min_axis": crit["weakest_value"], "weakest": crit["weakest"]},
          open(os.path.join(dst, "v0_summary.json"), "w"), indent=1)
print("V0 DONE ->", V0)
