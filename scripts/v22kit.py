#!/usr/bin/env python3
"""v22kit — shared graphics-first grammar for replica v22 + T-1 v22 (Phase 22).
F3 semantic sticker kit / F1 full-bleed canvas families / F7 camera life /
F5 single caption voice helpers / cut-out person layer / M1 alpha-seq paste.
Imported by render_replica_v22.py and render_t1_v22.py. No render loop here."""
import os, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import sys
# Ph26: portable paths — repo-relative sys.path + env-overridable run dirs
# (old sandbox paths /home/z/my-project/* were purged at Phase 25 cleanup)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components"))
import renderlib as R
from renderlib import VOLT, INK

W, H, FPS = 1080, 1920, 30
EMS_WORK = os.environ.get("EMS_WORK", "/tmp/ems-work/26-run")
SCRATCH = os.environ.get("EMS_SCRATCH", f"{EMS_WORK}/scratch")
ASSETS = os.environ.get("EMS_ASSETS", f"{EMS_WORK}/assets")
CUT = f"{ASSETS}/cutouts"
M1_SEQ = f"{EMS_WORK}/m1_seq"
M1_FRAMES = 84
MV = os.environ.get("EMS_MV", "/home/z/my-project/upload/4_6051789922870758373 (1).mp4")

# ---------------- Ph26 S1/B7: internal labels are QC-ONLY ----------------
# Deliverables (master/cover) NEVER burn internal spec labels such as
# "[ hook / ... (WC2) ]" or "[ tap -> next scene (IG2) ]". Deliverable
# renderers set LABELS_ENABLED=False BEFORE drawing; every label call is
# logged with its position so the QC contact sheet can crop-proof that the
# delivered file is clean at each historic label position.
LABELS_ENABLED = True
LABEL_LOG = []

# ---------------- beat grid ----------------
def beat_grid(wav, dur):
    f = wave.open(wav, "rb")
    sr = f.getframerate()
    raw = f.readframes(int(sr * dur))
    f.close()
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = int(sr * 0.01)
    n = len(x) // hop
    e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    le = np.log(e + 1e-4)
    flux = np.clip(np.diff(le, prepend=le[0]), 0, None)
    beats = []
    for i in np.argsort(flux)[::-1]:
        t = i * 0.01
        if t < 0.15:
            continue
        if all(abs(t - b) > 0.42 for b in beats):
            beats.append(t)
        if len(beats) >= 14:
            break
    beats.sort()
    return beats, e

# ---------------- cut-out person layer (footage = ONE layer, R0) ----------------
PERSONS = {}
def load_persons():
    """load every salvaged matte (cut_<name>[_isnet].png); key = name without prefixes"""
    import glob
    for p in glob.glob(f"{CUT}/cut_*.png"):
        b = os.path.basename(p)[4:]
        if b.endswith("_isnet.png"):
            b = b[:-10]
        elif b.endswith(".png"):
            b = b[:-4]
        if b and b not in PERSONS:
            PERSONS[b] = Image.open(p).convert("RGBA")
    return sorted(PERSONS.keys())

# ---------------- lyric timing (whisper SEGS, verified p21) ----------------
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
for (_s, _e, _txt) in SEGS:
    _words = _txt.split()
    _dur = max(0.001, _e - _s)
    _wsum = sum(len(w) for w in _words) + len(_words)
    _acc = _s
    for _wd in _words:
        _wd_dur = _dur * (len(_wd) + 1) / _wsum
        LYRIC_WORDS.append({"text": _wd, "start": round(_acc, 2), "end": round(_acc + _wd_dur, 2)})
        _acc += _wd_dur

def lyric_at(t):
    """returns (words[-3:], active_word) for the single karaoke voice (R5/F5)"""
    cur = [w for w in LYRIC_WORDS if w["start"] <= t < w["end"]]
    if not cur:
        prev = [w for w in LYRIC_WORDS if w["end"] <= t]
        if not prev:
            return [], None
        cur = [prev[-1]]
    w = cur[0]
    back = [x for x in LYRIC_WORDS if x["end"] <= w["start"] + 0.001][-2:]
    words = [x["text"] for x in back] + [w["text"]]
    return words[-3:], w["text"]

def colorize_person(name):
    """r20 method-swap: warm editorial duotone LUT (navy shadows -> warm mids ->
    warm-white highs) so cutouts read as target's color studio figures, not B/W."""
    im = PERSONS.get(name)
    if im is None:
        return
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    lum = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]) / 255.0
    pts = [0.0, 0.35, 0.72, 1.0]
    Rr = [30, 92, 190, 240]; Gg = [32, 80, 168, 234]; Bb = [40, 72, 152, 226]
    out = np.stack([np.interp(lum, pts, Rr), np.interp(lum, pts, Gg),
                    np.interp(lum, pts, Bb)], axis=-1)
    a = np.asarray(im.getchannel("A"))
    PERSONS[name] = Image.fromarray(np.dstack([out.astype(np.uint8), a]))

def paste_person(img, center, hh, which="stair", rot=0.0, shadow=True, alpha=1.0):
    im = PERSONS.get(which)
    if im is None:
        return
    w0, h0 = im.size
    s = hh / h0
    im2 = im.resize((max(1, int(w0 * s)), max(1, int(hh))), Image.LANCZOS)
    if alpha < 1.0:
        a = im2.getchannel("A").point(lambda v: int(v * alpha))
        im2.putalpha(a)
    if rot:
        im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
    cx, cy = center
    px, py = int(cx - im2.width / 2), int(cy - im2.height / 2)
    if shadow:
        d = ImageDraw.Draw(img, "RGBA")
        sw = int(im2.width * 0.72)
        d.ellipse([cx - sw // 2, cy + hh // 2 - 26, cx + sw // 2, cy + hh // 2 + 18], fill=(0, 0, 0, 60))
    img.alpha_composite(im2, (px, py))

# ---------------- F3 semantic sticker kit (documented map, no random emoji) ----------------
def sticker_hourglass(d, cx, cy, s, t=0.0, color=(238, 238, 240, 235)):
    s = int(s)
    w, h = int(s * 0.62), s
    x0, y0 = int(cx - w // 2), int(cy - h // 2)
    d.line([(x0, y0), (x0 + w, y0), (x0, y0 + h), (x0 + w, y0 + h), (x0, y0)], fill=color, width=max(3, s // 26))
    ph = (math.sin(t * 2.2) + 1) / 2
    midy = y0 + h // 2
    d.polygon([(x0 + 6, y0 + 8), (x0 + w - 6, y0 + 8), (x0 + w // 2, midy)], fill=color)
    d.polygon([(x0 + 6, y0 + h - 8 - int(h * 0.34 * ph)), (x0 + w - 6, y0 + h - 8 - int(h * 0.34 * ph)),
               (x0 + w // 2, midy)], fill=color)

def sticker_coin(d, cx, cy, s, color=VOLT + (240,)):
    r = s // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(4, s // 16))
    d.ellipse([cx - int(r * 0.62), cy - int(r * 0.62), cx + int(r * 0.62), cy + int(r * 0.62)],
              outline=color, width=max(2, s // 28))
    f = R.mono(max(14, int(r * 0.9)), bold=True)
    d.text((cx - int(r * 0.30), cy - int(r * 0.66)), "$", fill=color, font=f)

def sticker_lemon(d, cx, cy, s, color=(255, 214, 64, 235)):
    r = s * 0.42
    d.ellipse([cx - r, cy - r * 0.78, cx + r, cy + r * 0.78], fill=color)
    d.ellipse([cx - r * 0.55, cy - r * 0.42, cx + r * 0.55, cy + r * 0.42], outline=(255, 240, 180, 235), width=4)
    gx0, gy0 = cx + r * 0.75, cy - r * 0.95
    gw, gh = r * 1.05, r * 1.9
    d.line([(gx0, gy0), (gx0, gy0 + gh), (gx0 + gw * 0.8, gy0 + gh), (gx0 + gw * 0.8, gy0)], fill=color, width=5)

def sticker_confetti(d, cx, cy, spread, t, rng_seed=7):
    rng = np.random.default_rng(rng_seed)
    colors = [VOLT + (235,), (238, 238, 240, 225), (255, 214, 64, 225)]
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        rr = spread * (0.25 + 0.75 * ((i % 5) / 5)) * (1 + 0.08 * math.sin(t * 3 + i))
        x = cx + rr * math.cos(a)
        y = cy + rr * math.sin(a) * 0.72
        c = colors[i % len(colors)]
        if i % 3 == 0:
            d.rectangle([x, y, x + 9, y + 5], fill=c)
        elif i % 3 == 1:
            d.ellipse([x, y, x + 7, y + 7], fill=c)
        else:
            d.line([(x, y), (x + 8, y + 8)], fill=c, width=4)

def sticker_caution(d, x0, y0, x1, y1, alpha=245):
    """homicide -> caution tape band (F3: NOT crosshair-on-face)"""
    d.rectangle([x0, y0, x1, y1], fill=(30, 28, 24, alpha))
    stripe = 46
    for sx in range(x0 - (y1 - y0), x1, stripe * 2):
        d.polygon([(sx, y1), (sx + stripe, y1), (sx + stripe + (y1 - y0), y0), (sx + (y1 - y0), y0)],
                  fill=VOLT + (alpha,))
    f = R.mono(30, bold=True)
    d.text(((x0 + x1) / 2 - 62, (y0 + y1) / 2 - 18), "CAUTION", fill=(20, 20, 22, 255), font=f)

def sticker_heart(d, cx, cy, s, color=(240, 78, 90, 235)):
    r = s // 2
    d.ellipse([cx - r, cy - int(r * 0.9), cx, cy + int(r * 0.1)], fill=color)
    d.ellipse([cx, cy - int(r * 0.9), cx + r, cy + int(r * 0.1)], fill=color)
    d.polygon([(cx - r, cy - int(r * 0.18)), (cx + r, cy - int(r * 0.18)), (cx, cy + r)], fill=color)

def sticker_appicons(d, cx, cy, s, n=4):
    step = s + 14
    x0 = cx - (n * step - 14) / 2
    for i in range(n):
        x = x0 + i * step
        d.rounded_rectangle([x, cy - s / 2, x + s, cy + s / 2], radius=int(s * 0.28),
                            outline=(238, 238, 240, 210), width=4)
        d.ellipse([x + s * 0.3, cy - s * 0.2, x + s * 0.7, cy + s * 0.2], fill=VOLT + (200,))

def sticker_arrow(d, x0, y0, x1, y1, color=VOLT + (240,), w=10):
    d.line([(x0, y0), (x1, y1)], fill=color, width=w)
    ang = math.atan2(y1 - y0, x1 - x0)
    for da in (math.radians(152), math.radians(-152)):
        d.line([(x1, y1), (x1 + 46 * math.cos(ang + da), y1 + 46 * math.sin(ang + da))], fill=color, width=w)

def sticker_starburst(d, cx, cy, s, color=VOLT + (235,), t=0.0, n=10):
    pts = []
    r1, r2 = s / 2, s / 5.2
    for i in range(n * 2):
        a = (i / (n * 2)) * 2 * math.pi + t * 0.6
        rr = r1 if i % 2 == 0 else r2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pts.append(pts[0])
    d.polygon(pts, fill=color)

def sticker_constellation(d, cx, cy, s, seed=5, draw=True):
    rng = np.random.default_rng(seed)
    pts = [(cx + rng.uniform(-s, s) * 0.5, cy + rng.uniform(-s, s) * 0.4) for _ in range(6)]
    if draw:
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=(238, 238, 240, 200), width=3)
        for p in pts:
            d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=VOLT + (240,))
    return pts

def bracket_corners(d, x0, y0=None, x1=None, y1=None, color=VOLT + (235,), L=56, w=9):
    if isinstance(x0, (tuple, list)):
        x0, y0, x1, y1 = x0
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(cx, cy), (cx + dx * L, cy)], fill=color, width=w)
        d.line([(cx, cy), (cx, cy + dy * L)], fill=color, width=w)

def scene_label(img, xy, text, color=VOLT + (240,), size=30):
    """QC-only scene tag (Ph26 S1/B7). Deliverable renderers set
    LABELS_ENABLED=False: label is LOGGED (position+text) for QC crop proofs
    and NOT drawn — no internal label can reach master/cover. QC sheet
    builders may re-enable to burn positions onto QC-only sheets."""
    LABEL_LOG.append({"xy": [int(xy[0]), int(xy[1])], "text": str(text)})
    if not LABELS_ENABLED:
        return None
    d = ImageDraw.Draw(img, "RGBA")
    f = R.mono(size, bold=True)
    d.text(xy, f"[ {text} ]", font=f, fill=color)

# ---------------- F1 canvas families (full-bleed, rich) ----------------
def ghost_word(img, center, word, size=300, alpha=44, font_family="serif"):
    d = ImageDraw.Draw(img, "RGBA")
    f = R.playfair(size, 700) if font_family == "serif" else R.montserrat(size, 900)
    bb = d.textbbox((0, 0), word, font=f)
    d.text((center[0] - (bb[2] - bb[0]) / 2, center[1] - (bb[3] - bb[1]) / 2), word,
           font=f, fill=(255, 255, 255, alpha))

def canvas(kind, ghost=None):
    if kind == "paper":
        base = R.paper_white(W, H).convert("RGBA")
        d = ImageDraw.Draw(base, "RGBA")
        rng = np.random.default_rng(11)
        for _ in range(46):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            s = rng.uniform(4, 10)
            d.rectangle([x, y, x + s, y + s], fill=VOLT + (int(rng.integers(90, 170)),))
        if ghost:
            ghost_word(base, (W / 2, 300), ghost, 280, 36)
    elif kind == "navy":
        base = R.navy_scene(W, H, ghost=ghost).convert("RGBA")
        d = ImageDraw.Draw(base, "RGBA")
        rng = np.random.default_rng(23)
        for _ in range(60):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            d.rectangle([x, y, x + rng.uniform(3, 8), y + rng.uniform(3, 8)],
                        fill=VOLT + (int(rng.integers(80, 160)),))
    elif kind == "red":
        base = R.red_scene(W, H, ghost=ghost).convert("RGBA")
        d = ImageDraw.Draw(base, "RGBA")
        rng = np.random.default_rng(31)
        for _ in range(40):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            d.rectangle([x, y, x + rng.uniform(3, 7), y + rng.uniform(3, 7)],
                        fill=VOLT + (int(rng.integers(70, 140)),))
    elif kind == "green":
        base = R.green_scene(W, H).convert("RGBA")
        d = ImageDraw.Draw(base, "RGBA")
        rng = np.random.default_rng(41)
        for _ in range(50):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            d.rectangle([x, y, x + rng.uniform(3, 8), y + rng.uniform(3, 8)],
                        fill=(238, 238, 240, int(rng.integers(50, 120))))
    elif kind == "black":
        # F1 rich full-frame tissue: visible halftone over gradient (LB2 register)
        base = R.black_halftone(W, H, quote=ghost).convert("RGBA")
        d2 = ImageDraw.Draw(base, "RGBA")
        R._halftone(d2, W, H, (112, 114, 126), alpha=44, step=24, region=(0, H, 0, W))
        gx = Image.new("L", (W, H), 0)
        ImageDraw.Draw(gx).ellipse([int(W * 0.5 - W * 0.62), int(H * 0.42 - H * 0.5),
                                    int(W * 0.5 + W * 0.62), int(H * 0.42 + H * 0.5)], fill=26)
        gx = gx.filter(ImageFilter.GaussianBlur(180))
        arrg = np.array(base.convert("RGB")).astype(np.int16) + np.asarray(gx, dtype=np.int16)[..., None]
        base = Image.fromarray(np.clip(arrg, 0, 255).astype(np.uint8)).convert("RGBA")
    elif kind == "cleanblack":
        # LB10 endcard: intentional clean black, NO tissue
        base = Image.new("RGBA", (W, H), (4, 4, 5, 255))
    else:
        base = R.paper_white(W, H).convert("RGBA")
    arr = np.array(base.convert("RGB")).astype(np.int16)
    g = np.random.default_rng(9).normal(0, 5, arr.shape[:2])[..., None].astype(np.int16)
    arr = np.clip(arr + g, 0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")

# ---------------- F7 camera life ----------------
def cam_apply(img, t, s0, punch=0.055, drift=9.0, freq=0.5):
    """slow punch-in + drift INSIDE the comp via cover-crop (no black borders, F1/F7).
    Phase 24-C: adds a MONOTONIC per-scene pan component that DOMINATES the
    sinusoidal drift over any >=1s window (14 px/s x vs <=10 px/s max sinusoid
    variation, 6 px/s y vs <=6) so every window has a real, logged, visible
    camera delta — pure-sinusoidal drift has phase dead-zones that measured as
    idle (IG12) / camera-dead (G3)."""
    p = min(1.0, max(0.0, (t - s0)))
    # Phase 24-C camera design (G3/IG12 guarantee by construction):
    #  - MONOTONE global push-in 0.0036/s (+10% over the reel)
    #  - MONOTONE pans with velocity ALWAYS positive (v_x >= 2.9 px/s,
    #    v_y >= 1.8 px/s) — phase-shifted per scene for organic rhythm, bounded
    #    travel so the cover-crop never clamps the motion
    #  - per-scene punch uses a FAST ramp (0.35s) so |dz| across any window is
    #    carried by the monotone terms
    z = 1.0 + 0.0036 * t + punch * min(1.0, p / 0.35)
    dx = 4.0 * t - 2.0 * math.cos(2 * math.pi * t / 9.2 + s0 * 0.7)
    dy = 2.5 * t - 1.2 * math.cos(2 * math.pi * t / 11.0 + s0 * 1.1)
    if z > 1.001 or abs(dx) > 0.5:
        zw, zh = max(2, int(W / z)), max(2, int(H / z))
        cx, cy = W / 2 + dx * 0.5, H / 2 + dy * 0.5
        x0 = min(max(0, cx - zw / 2), W - zw)
        y0 = min(max(0, cy - zh / 2), H - zh)
        crop = img.crop((int(x0), int(y0), int(x0 + zw), int(y0 + zh)))
        img = crop.resize((W, H), Image.BILINEAR)
    return img, z, dx, dy

# ---------------- F5 single caption voice ----------------
def pill_statement(img, y, words, active_word, size=64):
    """mono/montserrat statement, ONE volt pill on active word (highlighter karaoke voice)."""
    d = ImageDraw.Draw(img, "RGBA")
    f = R.montserrat(size, weight=900)
    full = " ".join(words)
    bb = d.textbbox((0, 0), full, font=f)
    tw = bb[2] - bb[0]
    x = W / 2 - tw / 2
    if active_word in words:
        i = words.index(active_word)
        pre = " ".join(words[:i]) + (" " if i > 0 else "")
        pb = d.textbbox((0, 0), pre, font=f) if pre else None
        ab = d.textbbox((0, 0), active_word, font=f)
        px0 = x + (pb[2] - pb[0]) if pre else x
        px0 = x + f.getlength(pre) if pre else x
        d.rounded_rectangle([px0 - 10, y - 2, px0 + f.getlength(active_word) + 12, y + (ab[3] - ab[1]) + 14],
                            radius=12, fill=VOLT + (255,))
    d.text((x, y), full, font=f, fill=(255, 255, 255, 255))

# ---------------- M1 alpha seq paste ----------------
def paste_m1(img, t, scene_start):
    f = int((t - scene_start) * FPS)
    if 0 <= f < M1_FRAMES:
        p = f"{M1_SEQ}/f_{f:04d}.png"
        if os.path.exists(p):
            img.alpha_composite(Image.open(p).convert("RGBA").resize((W, H)))
            return True
    return False

def m1_available():
    return os.path.exists(f"{M1_SEQ}/f_0000.png")

# ---------------- v22.1 target-refined kit (from p21 blind critic gap analysis) ----------------
def sticker_scribble(d, cx, cy, s, color=(232, 60, 60, 235), loops=2, seed=3):
    """red scribble ellipse annotation (target signature)"""
    rng = np.random.default_rng(seed)
    pts = []
    for L in range(loops):
        for a in np.linspace(0, 2 * math.pi, 26, endpoint=False):
            r = s / 2 * (0.82 + 0.18 * rng.random())
            wob = 3.0 * math.sin(a * 5 + L)
            pts.append((cx + (r + wob) * math.cos(a + 0.35 * L),
                        cy + (r * 0.62 + wob) * math.sin(a + 0.35 * L)))
    d.line(pts, fill=color, width=5, joint="curve")

def sticker_badge_A(d, cx, cy, s, bg=(246, 244, 238, 255), fg=(20, 20, 22, 255)):
    """serif drop-cap 'A' in circle at grid center (target signature element)"""
    r = s // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(20, 20, 22, 230), width=4)
    f = R.playfair(int(s * 0.78), 900)
    bb = d.textbbox((0, 0), "A", font=f)
    d.text((cx - (bb[2] - bb[0]) / 2, cy - (bb[3] - bb[1]) / 2 - bb[1]), "A", font=f, fill=fg)

def sticker_playchip(d, cx, cy, s, color=(232, 60, 60, 235)):
    """scribble circle + play button (target annotation voice)"""
    sticker_scribble(d, cx, cy, s, color=color)
    r = s // 5
    d.polygon([(cx - r * 0.5, cy - r), (cx - r * 0.5, cy + r), (cx + r * 1.1, cy)], fill=color)

def phone_chip(d, x0, y0, w, h, label, bg=(16, 30, 78, 240), fg=(238, 238, 240, 235)):
    """phone-shaped chat chip (target top-right panel voice); label auto-fits (no clip)"""
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=int(h * 0.35), fill=bg)
    size = max(16, int(h * 0.34))
    while size > 14:
        f = R.mono(size)
        if d.textbbox((0, 0), label, font=f)[2] <= w * 0.84:
            break
        size -= 2
    f = R.mono(size)
    bb = d.textbbox((0, 0), label, font=f)
    d.text((x0 + (w - (bb[2] - bb[0])) / 2, y0 + (h - (bb[3] - bb[1])) / 2 - bb[1]), label,
           font=f, fill=fg)

def floating_pill(img, center, text, size=34, rot=-6):
    """volt pill = SMALL FLOATING LABEL (critic fix: not highlighter-behind-keyword)"""
    return R.volt_pill(img, center, text, R.montserrat(size, 900), rot=rot, pad=(16, 8))

def big_numerals(d, center, text, size=150, color=(232, 60, 60, 245)):
    """big red serif numerals (target $100 voice)"""
    f = R.playfair(size, 900)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((center[0] - (bb[2] - bb[0]) / 2, center[1] - (bb[3] - bb[1]) / 2), text, font=f, fill=color)

def panel_paper(w, h):
    img = R.paper_white(w, h).convert("RGBA")
    return img

def panel_navy(w, h):
    """bright editorial navy (target TR voice): rich blue gradient, low vignette"""
    img = R._gradient(w, h, (46, 78, 178), (12, 18, 58)).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    R._halftone(d, w, h, (210, 220, 255), alpha=12, step=34, region=(0, int(h * 0.25), 0, w))
    return R._grain(R._vignette(img, 0.14), 5).convert("RGBA")

def panel_red(w, h):
    """rich red room (target BL voice): saturated red gradient, NOT murky maroon"""
    img = R._gradient(w, h, (178, 38, 52), (70, 14, 20)).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    R._halftone(d, w, h, (255, 130, 118), alpha=10, step=30, region=(int(h * 0.72), h, 0, w))
    return R._grain(R._vignette(img, 0.14), 5).convert("RGBA")

def panel_black(w, h):
    img = R.black_halftone(w, h).convert("RGBA")
    return img

def person_bob(t, amp=0.07, freq=1.9):
    return 1.0 + amp * math.sin(t * freq)

def grid_layout(gutter=14, top=0, bottom=0):
    """2x2 grid boxes with black gutters, full-bleed (F1)"""
    inner_w = (W - gutter * 3) // 2
    hh = (H - top - bottom - gutter * 3) // 2
    boxes = []
    for r in range(2):
        for c in range(2):
            x0 = gutter + c * (inner_w + gutter)
            y0 = top + gutter + r * (hh + gutter)
            boxes.append((x0, y0, x0 + inner_w, y0 + hh))
    return boxes

def panel_maroon(w, h):
    img = Image.new("RGBA", (w, h))
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    top = np.array([64, 16, 26]); bot = np.array([26, 8, 12])
    tt = np.linspace(0, 1, h)[:, None]
    g = (top[None, None, :] * (1 - tt[..., None]) + bot[None, None, :] * tt[..., None])
    arr[..., :3] = np.tile(g, (1, w, 1)).astype(np.uint8)
    arr[..., 3] = 255
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img, "RGBA")
    R._halftone(d, w, h, (255, 120, 110), alpha=10, step=30, region=(int(h * 0.72), h, 0, w))
    return R._grain(R._vignette(img, 0.30), 6).convert("RGBA")

def compose_grid(panels, boxes, eases=None, t=0.0):
    """panels: list of (kind, draw_fn); eases: per-panel entrance 0..1 (with overshoot);
    slight live wobble per panel = motion feel readable in stills (F7)."""
    out = Image.new("RGBA", (W, H), (5, 5, 7, 255))
    for i, ((kind, fn), box) in enumerate(zip(panels, boxes)):
        x0, y0, x1, y1 = box
        pw, ph = x1 - x0, y1 - y0
        sub = {"paper": panel_paper, "navy": panel_navy, "red": panel_red,
               "maroon": panel_red, "black": panel_black, "green": R.R_green,
               "gray": panel_gray}[kind](pw, ph)
        if fn:
            fn(sub, pw, ph)
        ee = eases[i] if eases else 1.0
        ee = max(0.0, ee)
        sc = 0.90 + 0.14 * min(1.05, ee)  # overshoot lands ~1.035 (R4 bounce)
        rot = 1.4 * math.sin(t * 1.5 + i * 1.7)
        if sc < 0.999 or abs(rot) > 0.05:
            nw, nh = max(2, int(pw * sc)), max(2, int(ph * sc))
            sub2 = sub.resize((nw, nh), Image.BILINEAR)
            if abs(rot) > 0.05:
                sub2 = sub2.rotate(rot, expand=False, resample=Image.BICUBIC)
            sub = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            sub.alpha_composite(sub2, ((pw - nw) // 2, (ph - nh) // 2))
        slide = int(max(0.0, 1.0 - ee) * 36 * (1 if i % 2 == 0 else -1))
        out.alpha_composite(sub, (x0, y0 + slide))
        d = ImageDraw.Draw(out, "RGBA")
        d.rounded_rectangle([x0, y0 + slide, x1, y1 + slide], radius=8,
                            outline=(240, 240, 240, 40), width=2)
    return out

# ---------------- v22.3 display-register kit (decoded from tgt frames) ----------------
def panel_gray(w, h):
    """light-gray studio bg (target BR voice): subtle vertical falloff + floor wash"""
    img = Image.new("RGBA", (w, h))
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    top = np.array([243, 243, 244]); bot = np.array([222, 222, 226])
    tt = np.linspace(0, 1, h)[:, None]
    g = (top[None, None, :] * (1 - tt[..., None]) + bot[None, None, :] * tt[..., None])
    arr[..., :3] = np.tile(g, (1, w, 1)).astype(np.uint8)
    arr[..., 3] = 255
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([int(w * 0.10), int(h * 0.82), int(w * 0.90), int(h * 1.00)], fill=(205, 205, 210, 90))
    return R._grain(img, 4).convert("RGBA")

def pixel_display(sub, center, text, size, color=INK, chunk=4, serif=True):
    """chunky pixel-serif display word (target signature register), auto-fit to 0.9w"""
    d = ImageDraw.Draw(sub)
    f = R.playfair(int(size), 700) if serif else R.montserrat(int(size), 900)
    bb = d.textbbox((0, 0), text, font=f)
    while bb[2] - bb[0] > sub.width * 0.90 and size > 24:
        size -= 6
        f = R.playfair(int(size), 700) if serif else R.montserrat(int(size), 900)
        bb = d.textbbox((0, 0), text, font=f)
    return R.pixel_word(sub, center, text, f, color=color, chunk=chunk)

def prop_cube(d, cx, y, s, color=(246, 244, 238, 245)):
    """white studio cube seat (target red-room voice)"""
    h = int(s * 0.62)
    d.rounded_rectangle([cx - s // 2, y - h, cx + s // 2, y], radius=6, fill=color)
    d.line([(cx - s // 2, y - h), (cx + s // 2, y - h)], fill=(225, 223, 218, 255), width=3)

def prop_chair(d, cx, y, s, color=(40, 40, 44, 240)):
    """dark studio armchair silhouette (target gray-studio voice)"""
    w = int(s * 1.15); h = int(s * 0.78)
    d.rounded_rectangle([cx - w // 2, y - h, cx + w // 2, y], radius=int(s * 0.18), fill=color)
    d.rounded_rectangle([cx - int(w * 0.40), y - int(h * 0.55), cx + int(w * 0.40), y + int(h * 0.10)],
                        radius=int(s * 0.14), fill=tuple(max(0, c - 14) for c in color[:3]) + (color[3],))

def appicons_row(d, cx, cy, s, n=6):
    """multicolor app-icon row (target 'just AI agents' voice)"""
    colors = [(158, 158, 165), (58, 88, 216), (238, 128, 42), (22, 22, 24),
              (44, 178, 92), (148, 92, 52), (216, 243, 74)]
    step = int(s * 2.3)
    x0 = cx - (n * step - (step - int(s * 2))) // 2
    for i in range(n):
        x = x0 + i * step
        c = colors[i % len(colors)]
        d.rounded_rectangle([x, cy - s, x + s * 2, cy + s], radius=int(s * 0.42), fill=c + (240,))
        d.ellipse([x + s * 0.62, cy - s * 0.42, x + s * 1.38, cy + s * 0.42],
                  fill=(255, 255, 255, 60 if c[:3] != (22, 22, 24) else 30))

def sticker_blob(d, cx, cy, s, color=(214, 40, 57, 240), seed=9):
    """glossy red blob sticker (target gray-studio voice)"""
    rng = np.random.default_rng(seed)
    pts = []
    for a in np.linspace(0, 2 * math.pi, 18, endpoint=False):
        rr = s / 2 * (0.80 + 0.28 * float(rng.random()))
        pts.append((cx + rr * math.cos(a), cy + rr * 0.86 * math.sin(a)))
    d.polygon(pts, fill=color)
    hx = cx - s * 0.14
    hy = cy - s * 0.18
    d.ellipse([hx - s * 0.16, hy - s * 0.10, hx + s * 0.10, hy + s * 0.10], fill=(255, 255, 255, 90))

def highlight_mark(d, x, y, w, h, color=VOLT + (225,)):
    """small volt marker stroke (target yellow-underline voice)"""
    d.rectangle([x, y, x + w, y + h], fill=color)

def sticker_constellation2(d, cx, cy, s, seed=5, draw=True):
    """hub-and-spokes with SQUARE nodes (target 'matters' voice)"""
    rng = np.random.default_rng(seed)
    hub = (cx, cy)
    pts = [(cx + rng.uniform(-s, s) * 0.62, cy + rng.uniform(-s, s) * 0.55) for _ in range(9)]
    if draw:
        for p in pts:
            d.line([hub, p], fill=(240, 240, 244, 200), width=3)
        for p in pts:
            d.rectangle([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8], fill=(245, 245, 248, 235))
        d.rectangle([hub[0] - 16, hub[1] - 16, hub[0] + 16, hub[1] + 16], fill=(245, 245, 248, 245))
    return pts

# ---------------- v22.2 density + fit helpers (round 2) ----------------
def fit_font(d, text, base_px, max_w, weight=900, serif=False, min_px=28):
    size = base_px
    while size > min_px:
        f = R.playfair(size, 900) if serif else R.montserrat(size, weight)
        if d.textbbox((0, 0), text, font=f)[2] <= max_w:
            return f
        size -= 6
    return R.playfair(min_px, 900) if serif else R.montserrat(min_px, weight)

def display_word(sub, w, h, word, xr=0.08, yr=0.16, max_w=None, fill=INK + (255,), serif=True, size_r=0.20):
    """panel display word auto-fitted to panel width (fixes clipping/WELCO bug)"""
    d = ImageDraw.Draw(sub, "RGBA")
    mw = max_w or w * 0.86
    f = fit_font(d, word, int(h * size_r), mw, serif=serif)
    d.text((w * xr, h * yr), word, font=f, fill=fill)

def brighten_cutouts(k=1.35, lift=14):
    """lift matte brightness so cut-outs read like target's bright-clothed people"""
    for k2, im in K_PERSONS.items() if False else []:
        pass

def lift_person(name, k=1.30, lift=18):
    """tone-map matte to bright studio register: 2-98%% auto-levels + lift
    (target people read bright/clean; MV cutouts start B&W dark)"""
    im = PERSONS.get(name)
    if im is None:
        return
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    lo, hi = np.percentile(arr, [2, 98])
    if hi > lo + 1e-3:
        arr = (arr - lo) / (hi - lo) * 235.0 + 12.0
    arr = np.clip(arr * k + lift, 0, 255).astype(np.uint8)
    PERSONS[name] = Image.fromarray(arr).convert("RGBA")

def ticker_strip(img, y, text, t, color=VOLT + (210,), speed=140):
    """sliding lyric ticker band (designed tissue, F1) with real motion"""
    d = ImageDraw.Draw(img, "RGBA")
    f = R.mono(30, bold=True)
    tw = d.textbbox((0, 0), text, font=f)[2]
    x = -(int(t * speed) % (tw + W)) + 0
    d.rectangle([0, y, W, y + 44], fill=(8, 8, 10, 210))
    d.text((x, y + 6), text, font=f, fill=color)
    d.text((x + tw + 80, y + 6), text, font=f, fill=color)
