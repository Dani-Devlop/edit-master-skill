#!/usr/bin/env python3
"""ig24kit — Phase 24 IG-native kit. Imported by render_replica_v24 / render_t1_v24.
IG1 beat-lock (librosa onsets+kicks, snap) | IG2 pseudo-UI (cursor tap, heart burst,
comment bubble, notification) | IG4 kinetic slams (per-letter stagger, squash/stretch,
chromatic split, outline+fill) | IG5 idle micro-motion helpers | IG6 selective color
(volt-hue isolation) | IG8 film texture (halation, dust, gate-weave, light-leak)
| IG10 camera helpers (speed ramp, dutch) | 3D: perspective-projection engine
(homography quads + layered extrusion) for M1-M5 moves — bpy is NOT available in
this session, engine honestly labelled "persp3d" with proof strips."""
import os, math, wave, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

VOLT = (216, 243, 74)
INK = (16, 17, 20)

# ---------------- IG1: beat-lock ----------------
def _lowpass(y, sr, cutoff=120):
    """FFT-mask low-pass (librosa lacks effects.low_pass)"""
    spec = np.fft.rfft(y)
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    spec[freqs > cutoff] = 0
    return np.fft.irfft(spec, len(y))

def onset_grid(wav_path, dur, sr_hint=48000):
    """librosa onsets + beats + low-band kicks (IG1). Falls back to energy flux."""
    try:
        import librosa
        y, sr = librosa.load(wav_path, sr=22050, mono=True, duration=dur)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr,
                                                  backtrack=False, units="frames")
        onsets = [round(float(f * 512 / sr), 3) for f in onset_frames]
        tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        beats = [round(float(f * 512 / sr), 3) for f in beat_frames]
        # kicks: low-band (<120Hz) energy onsets
        y_low = _lowpass(y, sr, 120)
        lo_env = librosa.onset.onset_strength(y=y_low, sr=sr)
        lo_frames = librosa.onset.onset_detect(onset_envelope=lo_env, sr=sr, backtrack=False)
        kicks = [round(float(f * 512 / sr), 3) for f in lo_frames]
        return onsets, beats, kicks, round(float(np.atleast_1d(tempo)[0]), 1), "librosa"
    except Exception as e:
        import traceback
        traceback.print_exc()
        # fallback: energy flux (v22 method)
        f = wave.open(wav_path, "rb")
        sr = f.getframerate()
        raw = f.readframes(int(sr * dur)); f.close()
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        if x.ndim > 1: x = x.mean(axis=1)
        hop = int(sr * 0.01)
        n = len(x) // hop
        e = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
        le = np.log(e + 1e-4)
        flux = np.clip(np.diff(le, prepend=le[0]), 0, None)
        onsets, beats, kicks = [], [], []
        for i in np.argsort(flux)[::-1]:
            t = i * 0.01
            if t < 0.15: continue
            if all(abs(t - o) > 0.42 for o in onsets):
                onsets.append(t)
            if len(onsets) >= 40: break
        onsets.sort(); beats = onsets[::2]
        return onsets, beats, onsets[:12], 0.0, "flux-fallback"

def snap(t, onsets, tol=0.06):
    """snap t to nearest onset within tol (IG1 gate: ±60ms)"""
    if not onsets:
        return t, None
    b = min(onsets, key=lambda o: abs(o - t))
    return (round(b, 3), round(abs(b - t), 3)) if abs(b - t) <= tol else (t, None)

def kick_pulse(t, kicks, amp=0.03, decay=7.0):
    """IG1: kick-synced scale pulse ±3% (returns multiplier 1.0..1+amp)"""
    p = 0.0
    for k in kicks:
        dt = t - k
        if 0 <= dt < 0.5:
            p = max(p, amp * math.exp(-decay * dt))
    return 1.0 + p

# ---------------- IG4: kinetic slams ----------------
def slam_text(img, center, word, font_fn, t, t0, per_letter=0.05, size=150,
              color=VOLT + (245,), stroke=(240, 240, 238, 235), chroma=True, base=False,
              track=0):
    """per-letter stagger slam: each letter enters 30-60ms late with squash/stretch
    1.08/0.94 on impact + chromatic split 2-3px + outline+fill double layer.
    base=True: ALWAYS draw the full word (composed frame-0 / loop-freeze safety);
    impact FX (squash/chroma) applies per-letter during its 0.22s window."""
    d = ImageDraw.Draw(img, "RGBA")
    dt = max(0.0, t - t0)
    total_w = 0
    widths, f = [], font_fn(size)
    for ch in word:
        bb = d.textbbox((0, 0), ch, font=f)
        wch = bb[2] - bb[0]
        widths.append(wch); total_w += wch
    x = center[0] - total_w / 2
    cy = center[1]
    letters_drawn = 0
    for i, ch in enumerate(word):
        lt = dt - i * per_letter          # letter-local time
        fx = (lt >= 0) and (lt < 0.22)    # impact FX window
        if not fx and not base:
            if lt < 0:
                break
        letters_drawn += 1
        bb = d.textbbox((0, 0), ch, font=f)
        wch, hch = bb[2] - bb[0], bb[3] - bb[1]
        # squash/stretch: overshoot 1.08 -> dip 0.94 -> settle 1.0 (first 0.22s)
        sc = 1.0
        pop = 0.0
        if fx:
            pop = max(0.0, 1.0 - lt / 0.09)
            if lt < 0.10:
                sc = 0.94 + 0.14 * (lt / 0.10)
            else:
                ph = (lt - 0.10) / 0.12
                sc = 1.08 - 0.14 * ph * (1 - ph * 0.5)
            sc = min(1.08, max(0.94, sc))
        # chromatic split 2-3px during impact
        off = int(3 * pop) if chroma else 0
        # F3 (Ph32): natural advance ONLY — the old `lx = x + sum(widths[:i])`
        # double-accumulated position (x already advanced) rendering the word
        # ~1.5x wider than the S3 fit loop measured (plan 690px vs actual 1014px
        # ink span on decoded frames) -> edge-cropped hook. track (px) tightens.
        lx = x
        f2 = f
        if abs(sc - 1.0) > 0.004:
            sz = max(8, int(size * sc))
            f2 = font_fn(sz)
            bb2 = d.textbbox((0, 0), ch, font=f2)
            wch, hch = bb2[2] - bb2[0], bb2[3] - bb2[1]
        ox, oy = int(lx - wch / 2), int(cy - hch / 2)
        if off:
            # Ph26 S2/B8 palette lock: chroma split stays (IG4 feature) but the
            # split colors are volt/white — red+blue variants were off-palette
            d.text((ox - off, oy), ch, font=f2, fill=(216, 243, 74, int(170 * pop)),
                   stroke_width=2, stroke_fill=(216, 243, 74, int(140 * pop)))
            d.text((ox + off, oy), ch, font=f2, fill=(246, 246, 242, int(170 * pop)),
                   stroke_width=2, stroke_fill=(246, 246, 242, int(140 * pop)))
        d.text((ox, oy), ch, font=f2, fill=color, stroke_width=max(2, size // 60),
               stroke_fill=stroke)
        x += widths[i] + track
    return letters_drawn

# ---------------- IG2: pseudo-UI ----------------
def cursor_tap(img, x, y, t, t0, dur=0.55, scale=1.0):
    """animated cursor moves in -> press (squash) -> ripple rings -> settle.
    Returns True during beat (for 'tap triggers next scene' grammar)."""
    d = ImageDraw.Draw(img, "RGBA")
    p = (t - t0) / dur
    if p < 0 or p > 1.6:
        return False
    # cursor slides in from offset, presses at p~0.5
    slide = max(0.0, min(1.0, p / 0.45))
    press = max(0.0, min(1.0, (p - 0.45) / 0.18)) if p > 0.45 else 0.0
    cx = x + (1 - slide) * 140
    cy = y + (1 - slide) * 110
    s = 34 * scale * (1 - 0.16 * math.sin(press * math.pi))
    # arrow cursor polygon (white + ink outline)
    pts = [(cx, cy), (cx, cy + s * 1.45), (cx + s * 0.34, cy + s * 1.06),
           (cx + s * 0.62, cy + s * 1.72), (cx + s * 0.86, cy + s * 1.58),
           (cx + s * 0.58, cy + s * 0.94), (cx + s * 1.02, cy + s * 0.92)]
    d.polygon(pts, fill=(246, 246, 248, 240), outline=(16, 17, 20, 245))
    # ripple rings after press
    for r_i in range(2):
        rp = p - 0.55 - r_i * 0.16
        if 0 < rp < 0.5:
            rr = 14 + 66 * rp
            a = int(200 * (1 - rp / 0.5))
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=VOLT + (a,), width=4)
    return True

def heart_burst(d, cx, cy, t, t0, n=7, spread=120, color=VOLT + (235,)):
    """hearts pop outward with gravity arc (payoff beat). F1 (Ph32): volt ONLY —
    the red-pink 240,78,90 default was an off-palette leak (B8 targeted census)"""
    dt = t - t0
    if dt < 0 or dt > 0.9:
        return 0
    rng = np.random.default_rng(21)
    cnt = 0
    for i in range(n):
        a = rng.uniform(-2.6, -0.5)
        v = rng.uniform(180, 320)
        x = cx + v * math.cos(a) * dt
        y = cy + v * math.sin(a) * dt + 240 * dt * dt
        s = int(26 + 10 * math.sin(i * 2.1)) * max(0.0, 1.0 - dt / 0.9)
        if s < 4: continue
        r = s // 2
        d.ellipse([x - r, y - int(r * 0.9), x, y + int(r * 0.1)], fill=color)
        d.ellipse([x, y - int(r * 0.9), x + r, y + int(r * 0.1)], fill=color)
        d.polygon([(x - r, y - int(r * 0.18)), (x + r, y - int(r * 0.18)), (x, y + r)], fill=color)
        cnt += 1
    return cnt

def comment_bubble(img, x, y, text, t, t0, who="you", kw=None):
    """comment chip pops (overshoot) with lyric keyword accent"""
    dt = t - t0
    if dt < 0 or dt > 2.2:
        return
    d = ImageDraw.Draw(img, "RGBA")
    pop = 1.0 + 0.12 * math.sin(min(1.0, dt / 0.30) * math.pi) if dt < 0.30 else 1.0
    f = R_mono(30, bold=True)
    tw = d.textbbox((0, 0), text, font=f)[2]
    w = tw + 46
    h = 62
    x0, y0 = int(x), int(y - h * pop / 2)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + int(h * pop)], radius=30,
                        fill=(14, 14, 18, 225), outline=(240, 244, 255, 110), width=2)
    d.text((x0 + 22, y0 + 12), who + ":", font=R_mono(26), fill=(150, 152, 160, 220))
    if kw and kw in text:
        i = text.index(kw)
        pre, post = text[:i], text[i + len(kw):]
        fx = x0 + 22 + d.textbbox((0, 0), who + ":  " + pre, font=f)[2]
        if pre.strip():
            d.text((x0 + 22 + d.textbbox((0, 0), who + ":  ", font=f)[2], y0 + 16), pre,
                   font=f, fill=(238, 238, 240, 235))
        d.rounded_rectangle([fx - 8, y0 + 14, fx + d.textbbox((0, 0), kw, font=f)[2] + 10, y0 + h - 12],
                            radius=10, fill=VOLT + (235,))
        d.text((fx, y0 + 16), kw, font=f, fill=(18, 18, 20, 255))
        d.text((fx + d.textbbox((0, 0), kw, font=f)[2] + 16, y0 + 16), post, font=f, fill=(238, 238, 240, 235))
    else:
        d.text((x0 + 22 + d.textbbox((0, 0), who + ":  ", font=f)[2], y0 + 16), text, font=f,
               fill=(238, 238, 240, 235))

def notif_banner(img, y, title, body, t, t0, dur=1.8):
    """iOS-style notification slides down + typing dots -> text (IG2 beat)"""
    dt = t - t0
    if dt < 0 or dt > dur:
        return
    d = ImageDraw.Draw(img, "RGBA")
    slide = min(1.0, dt / 0.35)
    ease = 1 - (1 - slide) ** 3
    w = 760
    x0 = (img.width - w) // 2
    y0 = int(-120 + (y + 120) * ease)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 108], radius=26, fill=(20, 20, 24, 235),
                        outline=(240, 244, 255, 70), width=2)
    d.ellipse([x0 + 22, y0 + 22, x0 + 62, y0 + 62], fill=VOLT + (240,))
    d.text((x0 + 78, y0 + 18), title, font=R_mono(30, bold=True), fill=(244, 244, 246, 245))
    typing = dt < 0.9
    if typing:
        for i in range(3):
            a = int(120 + 100 * math.sin(t * 6 - i * 0.9))
            d.ellipse([x0 + 80 + i * 26, y0 + 66, x0 + 96 + i * 26, y0 + 82], fill=(200, 202, 210, a))
    else:
        d.text((x0 + 80, y0 + 60), body, font=R_mono(28), fill=(210, 214, 222, 235))

# lazy font accessors (avoid import cycle: renderlib imported by caller)
_R = None
def bind_renderlib(mod):
    global _R
    _R = mod
def R_mont(sz, weight=900):
    return _R.montserrat(sz, weight)
def R_mono(sz, bold=False):
    return _R.mono(sz, bold=bold) if bold else _R.mono(sz)
def R_playfair(sz, weight=900):
    return _R.playfair(sz, weight)

# ---------------- IG6: selective color ----------------
def selective_color(img, keep=(58, 100), boost_inside=1.25):
    """B&W world isolation beat: everything -> luma, volt hue window stays chromatic.
    Returns (image, chroma_frac_out, chroma_frac_in)."""
    hsv = np.asarray(img.convert("HSV")).astype(np.float32)
    hue = hsv[..., 0] * 360 / 255.0
    sat = hsv[..., 1] / 255.0
    val = hsv[..., 2] / 255.0
    lum = val
    mask = (hue >= keep[0]) & (hue <= keep[1]) & (sat > 0.18)
    out = np.stack([lum, lum, lum], axis=-1) * 255.0  # C.5 fix: luma 0..1 -> 0..255
    sat_in = np.clip(sat * boost_inside, 0, 1)[..., None]
    color = _hue_to_rgb(hue / 360.0, sat_in[..., 0], lum)
    out = np.where(mask[..., None], color, out)
    res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    # measure on the OUTPUT image (post-filter truth): residual chroma outside
    # the volt window must be ~0; volt-window chroma stays high
    oh = np.asarray(res.convert("HSV")).astype(np.float32)
    ohue = oh[..., 0] * 360 / 255.0
    osat = oh[..., 1] / 255.0
    omask = (ohue >= keep[0]) & (ohue <= keep[1])
    chroma_out = float((osat > 0.22)[~omask].mean()) if (~omask).any() else 0.0
    chroma_in = float((osat > 0.22)[omask].mean()) if omask.any() else 0.0
    return res, chroma_out, chroma_in

def _hue_to_rgb(h, s, v):
    i = np.floor(h * 6)
    f = h * 6 - i
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    i = i.astype(int) % 6
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1) * 255.0

# ---------------- IG8: film texture ----------------
def halation(img, thr=205, strength=0.42, blur=9):
    """bright-area bloom (film halation) — computed at half-res then upscaled
    (bloom is low-frequency; 4x faster than full-res numpy+blur)"""
    w, h = img.size
    small = img.convert("RGB").resize((max(1, w // 2), max(1, h // 2)))
    arr = np.asarray(small).astype(np.float32)
    lum = arr.mean(axis=2)
    hi = np.clip((lum - thr) / (255 - thr), 0, 1)[..., None] * arr
    hi_img = Image.fromarray(np.clip(hi, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(3, blur // 2)))
    hi_arr = np.asarray(hi_img).astype(np.float32) * strength
    out = 255 - (255 - arr) * (255 - hi_arr) / 255  # screen blend
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)

def dust_scratch(img, t, seed=None, p_dust=0.55, scratch=False):
    """occasional dust specks + rare vertical scratch (IG8)"""
    rng = np.random.default_rng(int((t * 7 + 3) * 13) % (2 ** 32) if seed is None else seed)
    if rng.random() > p_dust and not scratch:
        return img
    # F2 (Ph32): dust via alpha_composite patch — never translucent ink directly
    # on the RGBA canvas (draw overwrites alpha; blending keeps dust subtle)
    _dpatch = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
    d = ImageDraw.Draw(_dpatch)
    for _ in range(rng.integers(2, 7)):
        x, y = rng.uniform(0, img.width), rng.uniform(0, img.height)
        s = rng.uniform(1.5, 4.5)
        d.ellipse([x, y, x + s, y + s], fill=(235, 235, 232, rng.integers(60, 130)))
    if scratch or rng.random() < 0.10:
        x = rng.uniform(0, img.width)
        d.line([(x, 0), (x + rng.uniform(-6, 6), img.height)], fill=(240, 240, 238, 42), width=1)
    img.alpha_composite(_dpatch)
    return img

def light_leak(img, p, edge="right"):
    """film-burn / light-leak wash at transition (IG8), p in 0..1"""
    if p <= 0 or p > 1:
        return img
    w, h = img.size
    grad = Image.new("L", (w, h), 0)
    dg = ImageDraw.Draw(grad)
    amp = math.sin(p * math.pi)
    for i in range(10):
        x0 = w if edge == "right" else 0
        span = int(w * 0.55 * amp)
        dg.ellipse([x0 - span // 2 - i * 30, int(h * (0.2 + 0.08 * i)) - span // 3,
                    x0 + span // 2 - i * 30, int(h * (0.2 + 0.08 * i)) + span // 3],
                   fill=int(90 * amp))
    grad = grad.filter(ImageFilter.GaussianBlur(70))
    leak = Image.new("RGB", (w, h), (255, 236, 170))
    out = Image.composite(leak, img.convert("RGB"), grad.point(lambda v: min(255, int(v * 1.6))))
    return out

def gate_weave(t, amp=1.5):
    """<=2px projector weave jitter (IG8)"""
    dx = amp * (math.sin(t * 23.7) * 0.6 + math.sin(t * 41.3) * 0.4)
    dy = amp * (math.cos(t * 29.1) * 0.6 + math.sin(t * 37.7) * 0.4)
    return dx, dy

# ---------------- IG10: camera ----------------
def ramp_t(t, t0, t1, x0=0.4, x1=1.6):
    """eased speed ramp 0.4x -> 1.6x across window; returns remapped source time"""
    p = min(1.0, max(0.0, (t - t0) / max(1e-3, t1 - t0)))
    e = p * p * (3 - 2 * p)  # smoothstep
    return t0 + (t1 - t0) * e, x0 + (x1 - x0) * e

# ---------------- IG5: idle micro-motion ----------------
def float_wobble(t, seed=0, amp=7.0, freq=0.9):
    return (amp * math.sin(t * freq + seed * 1.7),
            amp * math.cos(t * freq * 0.83 + seed * 2.3))

def rot_jitter(t, seed=0, amp=1.6):
    return amp * math.sin(t * 1.35 + seed * 2.1)

# ---------------- 3D: perspective-projection engine (M1-M5) ----------------
def find_coeffs(dst, src):
    """Homography mapping OUTPUT coords -> INPUT coords (PIL transform
    convention: x_in = (a x + b y + c)/(g x + h y + 1)). Solves G(dst_i)=src_i.
    Phase 24-C fix: the old solve was direction-inverted (src->dst), which made
    quad_warp sample outside the source — M1/M2/M5 rendered empty/distorted."""
    A, B = [], []
    for (dx, dy), (sx, sy) in zip(dst, src):
        A.append([dx, dy, 1, 0, 0, 0, -dx * sx, -dy * sx]); B.append(sx)
        A.append([0, 0, 0, dx, dy, 1, -dx * sy, -dy * sy]); B.append(sy)
    h = np.linalg.lstsq(np.array(A, dtype=np.float64), np.array(B, dtype=np.float64), rcond=None)[0]
    return tuple(h)

def quad_warp(img, dst_quad, out_w, out_h):
    """warp img so its corners land on dst_quad (in out_size canvas coords)"""
    w, h = img.size
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    coeffs = find_coeffs(dst_quad, src)
    return img.convert("RGBA").transform((out_w, out_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)

def m1_type_persp(img, center, word, t, t0, size=170, depth=26, color=VOLT):
    """M1 3D volt-emissive/chrome type via layered extrusion + perspective lean.
    bpy unavailable this session -> persp3d engine (honest substitute).
    Each frame: perspective quad lean (rotateX feel) + depth slices shaded by
    env gradient (chrome band) + volt emissive face + contact shadow."""
    d = ImageDraw.Draw(img, "RGBA")
    ent = min(1.0, max(0.0, (t - t0) / 0.42))
    bounce = 1 + 0.10 * math.sin(min(1.0, ent) * math.pi) if ent < 1 else 1.0
    lean = -14 + 6 * math.sin(t * 0.8)          # deg pseudo-3D yaw
    tilt = 10 - 3 * math.sin(t * 0.66)          # rotateX feel
    sz = int(size * bounce)
    f = _R.montserrat(sz, 900)
    bb = d.textbbox((0, 0), word, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 140
    tile = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    cx = pad - bb[0]; cy = pad - bb[1]
    # depth slices: dark chrome back -> emissive volt front
    for i in range(depth, 0, -1):
        sh = 0.30 + 0.62 * (1 - i / depth)      # env shading toward front
        col = (int(30 + 40 * sh), int(34 + 44 * sh), int(40 + 50 * sh), 235)
        off = int(i * 1.15 * math.sin(math.radians(lean)))
        td.text((cx + off, cy - int(i * 0.9 * math.sin(math.radians(tilt)))),
                word, font=f, fill=col)
    # chrome spec band across face
    band_y = cy + int(th * (0.28 + 0.10 * math.sin(t * 1.7)))
    td.text((cx, cy), word, font=f, fill=(226, 228, 234, 245))
    td.rectangle([cx - 8, band_y, cx + tw + 8, band_y + int(th * 0.16)], fill=(255, 255, 255, 60))
    # volt emissive face (soft, additive feel)
    td.text((cx, cy), word, font=f, fill=color + (215,))
    # contact shadow
    sh_img = Image.new("RGBA", (tile.width + 80, tile.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh_img).rectangle([40, tile.height + 20, 40 + tile.width, tile.height + 56],
                                     fill=(0, 0, 0, 120))
    sh_img = sh_img.filter(ImageFilter.GaussianBlur(18))
    # perspective: lean the tile onto canvas via quad
    W2, H2 = img.size
    cw, ch = tile.size
    k = math.sin(math.radians(abs(lean))) * 0.10
    dst = [(int(center[0] - cw * (0.5 + k)), int(center[1] - ch * 0.5)),
           (int(center[0] + cw * (0.5 - k)), int(center[1] - ch * 0.5 - ch * 0.03)),
           (int(center[0] + cw * (0.5 + k)), int(center[1] + ch * 0.5)),
           (int(center[0] - cw * (0.5 - k)), int(center[1] + ch * 0.5 + ch * 0.03))]
    warped = quad_warp(tile, dst, W2, H2)
    img.alpha_composite(sh_img, (int(center[0] - sh_img.width / 2),
                                 int(center[1] + ch * 0.5 - 30)))
    img.alpha_composite(warped)  # type over its shadow
    return "persp3d-m1"

def m2_polaroids_parallax(img, frames, t, t0, base_c, spread=260, depth_gain=0.18):
    """M2: floating polaroids with TRUE perspective parallax (3 cards, z-depth lean).
    frames: list of PIL RGB images (live video frames allowed = video-in-card)."""
    out = img
    for i, fr in enumerate(frames):
        z = i / max(1, len(frames) - 1)          # 0 back -> 1 front
        s = 1.0 + z * 0.45
        ww = int(300 * s)
        ph_x = base_c[0] + (i - 1) * spread * (1 + 0.06 * math.sin(t * 0.9 + i))
        ph_y = base_c[1] + (i - 1) * 90 * (1 + 0.05 * math.cos(t * 1.1 + i))
        tilt = -6 + i * 5 + rot_jitter(t, i, 1.2)
        ent = min(1.0, max(0.0, (t - t0 - i * 0.14) / 0.4))
        if ent <= 0:
            continue
        card = Image.new("RGBA", (ww + 24, int(ww * 1.25) + 24), (246, 244, 238, 255))
        card.alpha_composite(fr.convert("RGBA").resize((ww, int(ww * 0.98))), (12, 12))
        lean = tilt * 0.4
        rad = math.radians(lean)
        dxq = int(card.height * 0.06 * math.sin(rad))
        quad = [(ph_x - ww / 2 * s, ph_y - card.height / 2 + dxq),
                (ph_x + ww / 2 * s, ph_y - card.height / 2 - dxq),
                (ph_x + ww / 2 * s + int(18 * z), ph_y + card.height / 2 - dxq * 0.4),
                (ph_x - ww / 2 * s - int(18 * z), ph_y + card.height / 2 + dxq * 0.4)]
        warped = quad_warp(card.rotate(tilt, expand=True, resample=Image.BICUBIC), quad,
                           img.width, img.height)
        out.alpha_composite(Image.fromarray(
            np.clip(np.asarray(warped).astype(np.float32) * (0.7 + 0.3 * ent), 0, 255).astype(np.uint8)))
    return out

def m3_counter_ring(img, center, val, t, t0, r=210, color=VOLT):
    """M3: 3D counter ring — perspective ellipse + rotating ticks + odometer."""
    d = ImageDraw.Draw(img, "RGBA")
    ent = min(1.0, max(0.0, (t - t0) / 0.5))
    squash = 0.42 + 0.1 * math.sin(t * 0.9)      # rotateX perspective squash
    rr = r * ent
    # ring depth: back arc darker
    d.ellipse([center[0] - rr, center[1] - rr * squash - 10,
               center[0] + rr, center[1] + rr * squash - 10], outline=(40, 42, 48, 200), width=10)
    d.ellipse([center[0] - rr, center[1] - rr * squash,
               center[0] + rr, center[1] + rr * squash], outline=color + (240,), width=12)
    for i in range(24):
        a = t * 1.4 + i * math.pi / 12
        x1 = center[0] + rr * math.cos(a)
        y1 = center[1] + rr * squash * math.sin(a)
        x2 = center[0] + (rr - 26) * math.cos(a)
        y2 = center[1] + (rr - 26) * squash * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=color + ((150 if i % 2 else 235),), width=4)
    f = _R.montserrat(120, 900)
    txt = f"${val:,}"
    bb = d.textbbox((0, 0), txt, font=f)
    d.text((center[0] - (bb[2] - bb[0]) / 2, center[1] - (bb[3] - bb[1]) / 2 - 8), txt,
           font=f, fill=(250, 246, 242, 245))
    return "persp3d-m3"

def m4_callout_orbit(img, target_xy, label, t, t0, rx=300, ry=120, color=VOLT):
    """M4: object callout orbit — chip orbits the keyword on an ellipse (perspective)."""
    d = ImageDraw.Draw(img, "RGBA")
    a = t * 1.25
    ox = target_xy[0] + rx * math.cos(a)
    oy = target_xy[1] + ry * math.sin(a)
    front = math.sin(a) > 0
    f = _R.mono(32, bold=True)
    tw = d.textbbox((0, 0), label, font=f)[2]
    d.line([(target_xy[0], target_xy[1]), (ox, oy)], fill=color + (200,), width=3)
    d.rounded_rectangle([ox - tw / 2 - 16, oy - 24, ox + tw / 2 + 16, oy + 24], radius=24,
                        fill=(12, 12, 16, 235) if front else (12, 12, 16, 150),
                        outline=color + ((235 if front else 120),), width=3)
    d.text((ox - tw / 2, oy - 18), label, font=f, fill=color + (245,))
    return "persp3d-m4"

def m5_world_insert(img, frame, quad, shadow=True):
    """M5: world insert — footage plane perspective-mounted into scene (poster/screen)."""
    warped = quad_warp(frame, quad, img.width, img.height)
    if shadow:
        sh = Image.new("RGBA", (img.width, img.height), (0, 0, 0, 0))
        ImageDraw.Draw(sh).polygon([(x + 14, y + 18) for x, y in quad], fill=(0, 0, 0, 110))
        sh = sh.filter(ImageFilter.GaussianBlur(16))
        img.alpha_composite(sh)
    img.alpha_composite(warped)
    d = ImageDraw.Draw(img, "RGBA")
    d.line(list(map(tuple, quad)) + [tuple(quad[0])], fill=VOLT + (200,), width=3)
    return "persp3d-m5"


def draw_caption_pop(img, words, t, center_y, size=64):
    """IG9 native caption voice (single voice, karaoke pill) with active-word
    pop-bounce (scale 1.0->1.12 decay 0.16s) + rotate jitter ±0.8 deg at handover.
    Safe-zone: plate must sit ABOVE the IG bottom UI row (caller passes center_y
    <= H*0.80). Layout math mirrors renderlib.draw_caption_line."""
    d = ImageDraw.Draw(img, "RGBA")
    f_up = _R.montserrat(size, 900)
    f_ac = _R.montserrat(int(size * 1.12), 900)
    widths = []
    for wd in words:
        bb = d.textbbox((0, 0), wd["text"], font=f_up)
        widths.append(bb[2] - bb[0])
    gap = 16
    total = sum(widths) + gap * (len(words) - 1)
    line_start = words[0]["start"]; line_end = words[-1]["end"]
    span = max(0.001, line_end - line_start)
    tt = t if t <= line_end else line_start + ((t - line_start) % span)
    x = (img.width - total) / 2
    y_c = center_y
    _pill_box = (x - 30, y_c - 78, x + total + 30, y_c + 34)
    d.rounded_rectangle(_pill_box, radius=22, fill=(8, 8, 10, 170))
    for i, wd in enumerate(words):
        active = (wd["start"] - line_start <= tt - line_start < wd["end"] - line_start)
        spoken = tt - line_start >= wd["end"] - line_start
        if active:
            pop = max(0.0, 1.0 - (tt - wd["start"]) / 0.16)   # 1 -> 0 after handover
            sc = 1.0 + 0.12 * pop
            rot = 0.8 * pop * (1 if i % 2 else -1)
            bb = d.textbbox((0, 0), wd["text"], font=f_ac)
            w_a, h_a = bb[2] - bb[0], bb[3] - bb[1]
            # render active word tile (volt pill + ink text), then bounce-transform
            tile = Image.new("RGBA", (w_a + 30, h_a + 30), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            td.rounded_rectangle([8, 8 + bb[1], w_a + 22, 8 + bb[3] + 10], radius=14,
                                 fill=VOLT + (240,))
            td.text((15, 8), wd["text"], font=f_ac, fill=(16, 16, 18, 255))
            if abs(rot) > 0.05:
                tile = tile.rotate(rot, expand=True, resample=Image.BICUBIC)
            if abs(sc - 1.0) > 0.005:
                tile = tile.resize((int(tile.width * sc), int(tile.height * sc)), Image.BICUBIC)
            img.paste(tile, (int(x - 15 + w_a * (1 - sc) / 2),
                             int(y_c - 8 - tile.height / 2 + 10)), tile)
            x += w_a + gap
        else:
            col = (255, 255, 255, int(255 * 0.45)) if spoken else (255, 255, 255, 255)
            bb = d.textbbox((0, 0), wd["text"], font=f_up)
            d.text((x, y_c - bb[3] / 2 - 20), wd["text"], font=f_up, fill=col)
            x += widths[i] + gap
    return _pill_box

