#!/usr/bin/env python3
"""Phase 14 shared library: drawing, karaoke engine, effects, matte, audio synth."""
import numpy as np, subprocess, json, os, math, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DEJAVU_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def font(size, bold=True):
    return ImageFont.truetype(DEJAVU_B if bold else DEJAVU, size)

# ---------------- text ----------------
def draw_text_stroke(draw, xy, text, fnt, fill, stroke=3, stroke_fill=(0, 0, 0), anchor="la"):
    draw.text(xy, text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)

def text_w(text, fnt):
    im = Image.new("RGB", (4, 4)); d = ImageDraw.Draw(im)
    return d.textlength(text, font=fnt)

def fit_font(draw_target_w, text, start_px, min_px=24, bold=True):
    px = start_px
    while px > min_px and text_w(text, font(px, bold)) > draw_target_w:
        px -= 2
    return font(px, bold), px

# ---------------- karaoke engine (K1-K4) ----------------
def group_phrases(words, lo=2, hi=6):
    """group word dicts into phrase groups of 2..6 (respect punctuation end)."""
    groups, cur = [], []
    for w in words:
        cur.append(w)
        ender = w["w"].rstrip().endswith((",", ".", "!", "?", ";"))
        if len(cur) >= hi or (ender and len(cur) >= lo):
            groups.append(cur); cur = []
    if cur:
        if len(cur) < lo and groups:
            groups[-1].extend(cur)
        else:
            groups.append(cur)
    return groups

def karaoke_state(words, t, phrase_words_lo=2, phrase_words_hi=6):
    """returns (phrase_words, active_idx, spoken_idxs) for time t. Sweep loops per K2:
    during gaps longer than 1.2s after a phrase, the phrase sweep restarts (loop)."""
    groups = group_phrases(words, phrase_words_lo, phrase_words_hi)
    for g in groups:
        if t < g[0]["start"] - 0.05:
            continue
        if t <= g[-1]["end"] + 1.2:
            # active = word whose [start,end) contains t; loop restart inside phrase window
            span = g[-1]["end"] - g[0]["start"]
            lt = t
            if t > g[-1]["end"] and span > 0.4:  # tail loop: restart sweep until sentence changes
                lt = g[0]["start"] + ((t - g[-1]["end"]) % max(span, 0.4))
            active = None
            for i, w in enumerate(g):
                if w["start"] <= lt < w["end"] + 0.02:
                    active = i
                    break
            if active is None:
                active = 0 if lt <= g[0]["start"] else len(g) - 1
            return g, active, set(range(0, active))
    return None, None, set()

def draw_karaoke(im, phrase, active, spoken, band_y0, band_y1, accent, out_w,
                 font_px=56, stroke=3, active_scale=1.2, dim_frac=0.55, rtl=False):
    """One line: spoken words dimmed, active = accent + scale, upcoming full-white."""
    d = ImageDraw.Draw(im)
    f = font(font_px)
    sp = " ".join(w["w"] for w in phrase)
    target_w = out_w * 0.88
    while text_w(sp, f) > target_w and font_px > 26:
        font_px -= 2
        f = font(font_px)
    f_act = font(int(font_px * active_scale))
    widths = []
    for i, w in enumerate(phrase):
        widths.append(text_w(w["w"], f_act if i == active else f))
    gap = int(font_px * 0.30)
    total = sum(widths) + gap * (len(phrase) - 1)
    x = (out_w - total) // 2
    ymid = (band_y0 + band_y1) // 2
    for i, w in enumerate(phrase):
        if i == active:
            fnt, fill, y = f_act, accent, ymid
            anchor = "lm"
        else:
            fnt, fill, y = f, ((int(255 * dim_frac),) * 3 if i in spoken else (255, 255, 255)), ymid
            anchor = "lm"
        d.text((x, y), w["w"], font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(10, 10, 10), anchor=anchor)
        x += widths[i] + gap

def draw_keyword_line(im, text, band_y0, band_y1, accent, out_w, font_px=58, stroke=3,
                      reveal_frac=1.0, active=True):
    d = ImageDraw.Draw(im)
    f = font(font_px)
    while text_w(text, f) > out_w * 0.88 and font_px > 26:
        font_px -= 2
        f = font(font_px)
    if reveal_frac < 1.0:
        n = max(1, int(len(text) * reveal_frac))
        text = text[:n]
    fill = accent if active else (255, 255, 255)
    d.text((out_w // 2, (band_y0 + band_y1) // 2), text, font=f, fill=fill,
           stroke_width=stroke, stroke_fill=(10, 10, 10), anchor="mm")

# ---------------- effects ----------------
def grade_bw(img_np, contrast=1.18, lift=-8, floor=8.0):
    g = img_np.mean(axis=2, keepdims=True)
    g = (g - 128) * contrast + 128 + lift
    g = np.clip(g, 0, 255)
    # lifted-blacks film floor: never crush to pure 0 (letterbox-bar lookalike prevention)
    g = floor + (g / 255.0) * (255 - floor)
    return np.repeat(g, 3, axis=2)

def grade_color(img_np, sat=1.12, contrast=1.06):
    im = Image.fromarray(img_np.astype(np.uint8))
    from PIL import ImageEnhance
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    return np.asarray(im).astype(np.float32)

def grade_day_for_night(img_np):
    """day-for-night: desaturate + darken + cool tint + crush (pro technique, honest grammar)."""
    g = img_np.mean(axis=2, keepdims=True)
    g = g * 0.52
    b = g * 1.12 + 6
    r = g * 0.82
    out = np.concatenate([r, g, b], axis=2)
    from PIL import Image as _I, ImageEnhance as _E
    im = _I.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    im = _E.Color(im).enhance(0.55)
    return np.asarray(im).astype(np.float32)

def add_grain(img_np, amount=6.0):
    n = np.random.default_rng(int(img_np.sum()) % 9999).normal(0, amount, img_np.shape[:2])
    return np.clip(img_np + n[:, :, None], 0, 255)

def add_vignette(img_np, strength=0.35):
    h, w = img_np.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / math.sqrt(2)
    m = 1 - strength * np.clip(r, 0, 1) ** 2
    return img_np * m[:, :, None]

def invert_bite(img_np):
    return 255 - img_np

def whip_streak(img_np, direction=1, intensity=1.0, flash=0.0):
    """horizontal streak blur + flicker flash (F-5: ensure >=12 luma delta)."""
    im = Image.fromarray(img_np.astype(np.uint8))
    k = int(9 + 18 * intensity)
    im = im.filter(ImageFilter.BoxBlur(3))
    arr = np.asarray(im).astype(np.float32)
    shifted = np.roll(arr, direction * k, axis=1)
    out = 0.55 * arr + 0.45 * shifted
    if flash > 0:
        out = out + 55 * flash
    return np.clip(out, 0, 255)

def zoom_through_crop(img_np, z, blur=True):
    h, w = img_np.shape[:2]
    cw, ch = int(w / z), int(h / z)
    x0 = (w - cw) // 2; y0 = (h - ch) // 2
    c = img_np[y0:y0 + ch, x0:x0 + cw]
    im = Image.fromarray(c.astype(np.uint8)).resize((w, h), Image.BILINEAR)
    if blur and z > 1.3:
        im = im.filter(ImageFilter.GaussianBlur((z - 1.3) * 3))
    return np.asarray(im).astype(np.float32)

def scanlines(img_np, alpha=0.18):
    h, w = img_np.shape[:2]
    m = np.ones((h, 1), np.float32)
    m[::3] = 1 - alpha
    return img_np * m[:, :, None]

def shake(img_np, dx, dy):
    return np.roll(np.roll(img_np, dy, axis=0), dx, axis=1)

# ---------------- salience / subject window ----------------
def subject_centroid(img_np):
    g = img_np.mean(axis=2)
    thr = np.percentile(g, 78)
    fg = (g > thr).astype(np.uint8)
    ys, xs = np.nonzero(fg)
    if len(xs) < 50:
        return 0.5, 0.5, 0.0
    return float(xs.mean()) / img_np.shape[1], float(ys.mean()) / img_np.shape[0], float(fg.mean())

def smooth_track(vals, a=0.25):
    out = []
    prev = None
    for v in vals:
        prev = v if prev is None else a * v + (1 - a) * prev
        out.append(prev)
    return out

# ---------------- matte (rembg, single-frame, freeze-window honest) ----------------
_MATTE_CACHE = {}
def matte_alpha(pil_img, key):
    if key in _MATTE_CACHE:
        return _MATTE_CACHE[key]
    try:
        from rembg import remove, new_session
        sess = _MATTE_CACHE.get("session") or new_session("u2net")
        _MATTE_CACHE["session"] = sess
        out = remove(pil_img, session=sess)
        a = np.asarray(out)[:, :, 3]
    except Exception:
        a = None
    _MATTE_CACHE[key] = a
    return a

# ---------------- audio ----------------
SR = 44100
def _env(n, a=0.01, d=0.15, sr=SR):
    t = np.arange(n) / sr
    e = np.minimum(t / max(a, 1e-3), 1) * np.exp(-np.maximum(t - a, 0) / d)
    return e

def synth_kick(dur=0.30, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    f = 120 * np.exp(-t * 18) + 42
    x = np.sin(2 * np.pi * np.cumsum(f) / sr) * _env(len(t), 0.002, 0.12)
    return x

def synth_hat(dur=0.06, sr=SR):
    n = np.random.default_rng(7).normal(0, 1, int(dur * sr))
    hp = np.diff(n, prepend=0)
    x = hp * _env(len(hp), 0.001, 0.02) * 0.5
    # tame inter-sample overs: soften HF edge (true-peak friendly)
    x = np.convolve(x, np.ones(3) / 3, mode="same")
    return x

def synth_snare(dur=0.18, sr=SR):
    n = np.random.default_rng(11).normal(0, 1, int(dur * sr))
    tone = np.sin(2 * np.pi * 190 * np.arange(int(dur * sr)) / sr)
    x = (0.55 * n + 0.45 * tone) * _env(len(n), 0.002, 0.09)
    return np.convolve(x, np.ones(3) / 3, mode="same")

def synth_bass(freq, dur, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    x = np.sign(np.sin(2 * np.pi * freq * t)) * 0.35 + np.sin(2 * np.pi * freq * t) * 0.65
    return x * _env(len(t), 0.01, dur * 0.7)

def synth_pluck(freq, dur, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    x = (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2 * t) + 0.2 * np.sin(2 * np.pi * freq * 3 * t))
    return x * _env(len(t), 0.004, dur * 0.5)

def sfx_whoosh(dur=0.5, sr=SR):
    n = np.random.default_rng(3).normal(0, 1, int(dur * sr))
    t = np.arange(len(n)) / sr
    sweep = np.sin(2 * np.pi * (300 + 2200 * t / dur) * t)
    x = (0.6 * n + 0.4 * sweep) * np.hanning(len(n)) ** 1.5
    return x * 0.9

def sfx_glitch(dur=0.12, sr=SR):
    n = np.random.default_rng(5).normal(0, 1, int(dur * sr))
    q = np.sign(n) * (np.abs(n) > 0.3)
    return q * np.hanning(len(q)) * 0.8

def sfx_splice(dur=0.08, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    x = np.sin(2 * np.pi * 900 * t) * np.exp(-t * 60)
    n = np.random.default_rng(9).normal(0, 1, len(t)) * np.exp(-t * 90)
    return (x + n) * 0.8

def sfx_thump(dur=0.35, sr=SR):
    t = np.arange(int(dur * sr)) / sr
    f = 90 * np.exp(-t * 14) + 34
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * _env(len(t), 0.002, 0.18)

def music_bed(bpm, dur_s, style="drive", energy=0.7, sr=SR):
    """Original self-generated royalty-free bed. Returns float32 stereo."""
    beat = 60.0 / bpm
    n_total = int(dur_s * sr)
    L = np.zeros(n_total, np.float32); R = np.zeros(n_total, np.float32)
    n_bars = int(dur_s / (beat * 4)) + 1
    roots = [55.0, 65.4, 73.4, 61.7]  # A1 C2 D2 B1-ish
    rng = np.random.default_rng(42)
    for b in range(n_bars):
        t0 = b * beat * 4
        root = roots[b % len(roots)]
        for i in range(4):
            tt = t0 + i * beat
            if tt >= dur_s: break
            idx = int(tt * sr)
            if i in (0, 2) or (style == "drive" and energy > 0.6 and i == 3):
                k = synth_kick(); e = min(len(k), n_total - idx)
                L[idx:idx + e] += k[:e] * 0.9; R[idx:idx + e] += k[:e] * 0.9
            h = synth_hat(); e = min(len(h), n_total - int((tt + beat / 2) * sr))
            hi = int((tt + beat / 2) * sr)
            if hi < n_total:
                L[hi:hi + e] += h[:e] * 0.35; R[hi:hi + e] += h[:e] * 0.55
            if i == 1:
                s = synth_snare(); e = min(len(s), n_total - idx)
                L[idx:idx + e] += s[:e] * 0.5; R[idx:idx + e] += s[:e] * 0.5
            bl = synth_bass(root if i % 2 == 0 else root * 1.5, beat * 0.9)
            e = min(len(bl), n_total - idx)
            L[idx:idx + e] += bl[:e] * 0.4; R[idx:idx + e] += bl[:e] * 0.4
            if style == "bright" or style == "bouncy":
                f2 = root * 4 * (1.5 if i == 3 else 1.0)
                p = synth_pluck(f2, beat * 0.5); e = min(len(p), n_total - idx)
                L[idx:idx + e] += p[:e] * 0.30; R[idx:idx + e] += p[:e] * 0.22
            if style == "dark":
                if i == 0:
                    p = synth_pluck(root * 2, beat * 1.6); e = min(len(p), n_total - idx)
                    L[idx:idx + e] += p[:e] * 0.22; R[idx:idx + e] += p[:e] * 0.26
    mix = np.stack([L, R], axis=1)
    peak = np.abs(mix).max() or 1.0
    return (mix / peak * 0.72 * (0.5 + 0.5 * energy)).astype(np.float32)

def write_wav(path, stereo_f32, sr=SR):
    import wave
    x = np.asarray(stereo_f32, np.float32)
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(data.tobytes())

def _measure_ebur(path):
    p = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path,
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    tail = p.stderr[-1600:]
    I = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", tail)
    TP = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", tail)
    return (float(I.group(1)) if I else None, float(TP[-1]) if TP else None)

def two_pass_loudnorm(in_wav_or_mp4, out_path, target_i=-14.0, tp=-1.5, lra=11.0, crest_guard=False):
    """Deterministic iterative loudnorm (F-9 lesson hardened):
    A) [crest_guard] compressor to reduce crest on synthetic percussive beds
       + dynamic loudnorm with conservative TP margin + -2.5dB limiter (AAC overshoot)
    B) volume trim to exact target LUFS
    C) TP safety trim if still hot. Every step measured (honest numbers reported)."""
    import os as _os
    cur = in_wav_or_mp4
    tmp = out_path + ".iter.aac"
    lim_db = -2.5
    ln_tp = -3.4
    pre = "acompressor=threshold=-12dB:ratio=4:attack=2:release=90," if crest_guard else ""
    af = (f"{pre}loudnorm=I={target_i}:TP={ln_tp}:LRA={lra},"
          f"alimiter=limit={10 ** (lim_db / 20):.4f}:attack=1:release=80:level=false")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", cur, "-af", af,
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", tmp], check=True)
    I, TPm = _measure_ebur(tmp)
    attempts = 1
    tmp2 = out_path + ".iter2.aac"
    if I is not None and abs(I - target_i) > 0.3:
        gain = round(target_i - I, 2)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", f"volume={gain}dB",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", tmp2], check=True)
        _os.replace(tmp2, tmp)
        I, TPm = _measure_ebur(tmp)
        attempts += 1
    if TPm is not None and TPm > tp:
        gain = round((tp - 0.4) - TPm, 2)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", f"volume={gain}dB",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", tmp2], check=True)
        _os.replace(tmp2, tmp)
        I, TPm = _measure_ebur(tmp)
        attempts += 1
    _os.replace(tmp, out_path)
    return {"integrated_lufs": I, "true_peak_dbfs": TPm, "attempts": attempts}

import re
def duck_sfx_under(sfx_mix, music, duck_db=-6.0):
    g = 10 ** (duck_db / 20)
    return sfx_mix * g + music

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
