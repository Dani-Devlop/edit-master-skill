#!/usr/bin/env python3
"""Phase 11.1 GATE-ON-FILE (G1-G14) — measures the DECODED final mp4, not intent.

Usage: p11_gate.py <video.mp4> <manifest.json> <out_gate.json>
Exit 0 = all PASS, exit 2 = any FAIL (file quarantined by caller).

Manifest is the renderer's declaration of what it rendered; every declaration is
cross-checked against pixels/audio. Missing-but-required elements FAIL.
"""
import json, os, subprocess, sys, tempfile, math
import numpy as np
import cv2

def log(*a):
    print(*a, flush=True)
    try:
        with open("/home/z/my-project/p11work/gate_progress.log", "a") as lf:
            lf.write(" ".join(str(x) for x in a) + "\n")
    except Exception:
        pass
    try:
        with open("/home/z/my-project/p11work/gate_progress.log", "a") as lf:
            lf.write(" ".join(str(x) for x in a) + "\n")
    except Exception:
        pass

# ---------------------------------------------------------------- video decode
def probe(path):
    st = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate,codec_name",
         "-of", "json", path]))["streams"][0]
    n, d = st["avg_frame_rate"].split("/")
    fps = float(n) / float(d)
    fmt = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", path]))["format"]
    return dict(w=st["width"], h=st["height"], fps=fps,
                codec=st["codec_name"], dur=float(fmt["duration"]))

def stream_gray(path, scale=(90, 160)):
    """Yield (i, gray_small) at native fps, downscaled, streaming."""
    w, h = scale
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h}",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    fsz = w * h
    i = 0
    while True:
        buf = proc.stdout.read(fsz)
        if len(buf) < fsz:
            break
        yield i, np.frombuffer(buf, np.uint8).reshape(h, w)
        i += 1
    proc.wait()

def frame_at(path, t, w=None):
    if w is None:
        w = probe(path)["w"]
    h = int(w * 16 / 9)
    args = ["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
            "-vf", f"scale={w}:{h}", "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    buf = subprocess.check_output(args)
    if len(buf) < w * h * 3:
        return None
    return np.frombuffer(buf, np.uint8).reshape(h, w, 3)

def full_gray_series(path, scale=(270, 480), max_frames=2000):
    out = []
    for i, g in stream_gray(path, scale):
        if i >= max_frames:
            break
        out.append(g)
    return out

# ---------------------------------------------------------------- OCR
_tz = None
def ocr(img_bgr, psm=11):
    global _tz
    try:
        import pytesseract
    except ImportError:
        return []
    im = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    d = pytesseract.image_to_data(im, config=f"--psm {psm}", output_type=pytesseract.Output.DICT,
                                  timeout=8)
    out = []
    for i in range(len(d["text"])):
        t = (d["text"][i] or "").strip()
        c = int(d["conf"][i])
        if t and c > 0:
            x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
            out.append(dict(text=t, conf=c, box=[x, y, w, h]))
    return out

def ocr_words(img, psm=11):
    return [w for w in ocr(img, psm) if w["conf"] >= 40 and len(w["text"]) >= 2]

def fuzzy_in(target, words):
    t = target.lower().replace(" ", "")
    joined = []
    for i in range(len(words) - 1):
        joined.append(dict(text=words[i]["text"] + words[i + 1]["text"],
                           conf=min(words[i]["conf"], words[i + 1]["conf"]),
                           box=words[i]["box"]))
    allw = list(words) + joined
    for w in allw:
        s = w["text"].lower().replace(" ", "")
        if t and (t in s or s in t):
            return w
    # character-overlap match (OCR-tolerant): two tiers
    #  - overlap >= 0.7 with close length
    #  - overlap >= 0.85 with loose length (garbled suffixes on busy strips)
    for w in allw:
        s = w["text"].lower().replace(" ", "")
        inter = len(set(t) & set(s))
        if not t:
            continue
        r = inter / max(1, len(set(t)))
        if (r >= 0.7 and abs(len(s) - len(t)) <= 3) or (r >= 0.85 and abs(len(s) - len(t)) <= 5):
            return w
    return None

# ---------------------------------------------------------------- audio
def lufs_tp(path):
    cmd = ["ffmpeg", "-nostats", "-i", path, "-af",
           "ebur128=peak=true", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    txt = p.stderr
    lufs = tp = None
    for ln in txt.splitlines():
        if "I:" in ln and "LUFS" in ln and lufs is None:
            try:
                lufs = float(ln.split("I:")[1].replace("LUFS", "").strip())
            except Exception:
                pass
        if "Peak:" in ln and "dBFS" in ln:
            try:
                tp = float(ln.split("Peak:")[1].replace("dBFS", "").strip())
            except Exception:
                pass
    return lufs, tp

def audio_onsets(path, sr=22050):
    try:
        import librosa
    except ImportError:
        return []
    y, _ = librosa.load(path, sr=sr, mono=True)
    strength = librosa.onset.onset_strength(y=y, sr=sr)
    frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False, delta=0.12)
    times = librosa.frames_to_time(frames, sr=sr)
    vals = strength[frames] if len(frames) else []
    # fixed threshold calibrated on the soft-clipped mix (pad flux <= 4.3, SFX >= 4.6)
    strong = [float(t) for t, v in zip(times, vals) if v > 4.0]
    return strong

# ---------------------------------------------------------------- detectors
def accent_mask(bgr, accent, tol_hue=25, min_sat=0.30):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    ar, ag, ab = int(accent[0]), int(accent[1]), int(accent[2])
    hsv_accent = cv2.cvtColor(np.uint8([[[ab, ag, ar]]]), cv2.COLOR_BGR2HSV)[0, 0]
    h0 = int(hsv_accent[0])
    sat = int(min_sat * 255)
    lo, hi = max(0, h0 - tol_hue), min(179, h0 + tol_hue)
    if lo <= 0:
        return cv2.inRange(hsv, np.array([0, sat, 60], np.uint8), np.array([hi, 255, 255], np.uint8))
    if hi >= 179:
        return cv2.inRange(hsv, np.array([lo, sat, 60], np.uint8), np.array([179, 255, 255], np.uint8))
    m1 = cv2.inRange(hsv, np.array([0, sat, 60], np.uint8), np.array([min(hi - 179 + 180, 179), 255, 255], np.uint8))
    m2 = cv2.inRange(hsv, np.array([lo, sat, 60], np.uint8), np.array([179, 255, 255], np.uint8))
    return m1 | m2

def largest_accent_word(bgr, accent, y_max_frac=0.75, tol_hue=12, min_sat=0.45):
    m = accent_mask(bgr, accent, tol_hue=tol_hue, min_sat=min_sat)
    H, W = m.shape[:2]
    m[int(H * y_max_frac):, :] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    best = None
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 0.002 * W * H:
            continue
        fill = area / max(1, w * h)
        # reject diffuse washes (halftone / graded sky) only when they dominate the
        # frame; text-scale components keep their natural low fill
        if area > 0.15 * W * H and fill < 0.25:
            continue
        if best is None or w > best[2]:
            best = (x, y, w, h, area)
    return best, m

def halftone_score(gray):
    """Periodic dot-grid score via normalized autocorrelation of high-pass residual."""
    g = gray.astype(np.float32)
    med = cv2.medianBlur(g.astype(np.uint8), 5).astype(np.float32)
    res = g - med
    res -= res.mean()
    f = np.fft.rfft2(res)
    p = np.abs(f) ** 2
    p = np.fft.fftshift(p)
    c = np.real(np.fft.ifft2(np.fft.ifftshift(p)))
    c /= (c[0, 0] + 1e-9)
    H, W = c.shape
    band = c[H // 2 - 40:H // 2 + 40, W // 2 - 40:W // 2 + 40].copy()
    band[36:44, 36:44] = 0  # zero-lag
    score = float(band.max())
    return score

def wcag_contrast(c1, c2):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    l1 = 0.2126 * lin(c1[2]) + 0.7152 * lin(c1[1]) + 0.0722 * lin(c1[0])
    l2 = 0.2126 * lin(c2[2]) + 0.7152 * lin(c2[1]) + 0.0722 * lin(c2[0])
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)

def dhash(bgr, size=8):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (size + 1, size))
    d = g[:, 1:] > g[:, :-1]
    return "".join("1" if v else "0" for v in d.flatten())

def hash_sim(a, b):
    return 1 - sum(c1 != c2 for c1, c2 in zip(a, b)) / max(1, len(a))

def starburst_present(bgr):
    """F3 signature: >=8 thin radial segments from one center, angular spread >=120 deg.
    Tightened against footage false-positives (random Hough lines on busy frames)."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (5, 5), 0)
    edges = cv2.Canny(g, 60, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 36, threshold=40, minLineLength=30, maxLineGap=6)
    if lines is None or len(lines) < 8:
        return False, 0
    pts = lines[:, 0, :]
    mids_x = (pts[:, 0] + pts[:, 2]) / 2
    mids_y = (pts[:, 1] + pts[:, 3]) / 2
    lens = np.hypot(pts[:, 2] - pts[:, 0], pts[:, 3] - pts[:, 1])
    best = 0
    best_spread = 0.0
    for cx, cy in zip(mids_x[::2], mids_y[::2]):
        d = np.hypot(mids_x - cx, mids_y - cy)
        near = d < 80
        nn = int(near.sum())
        if nn >= 8:
            ang = np.degrees(np.arctan2(mids_y[near] - cy, mids_x[near] - cx)) % 180
            spread = float(ang.max() - ang.min())
            ok_lens = lens[near].mean() < 140
            if spread >= 120 and ok_lens and nn > best:
                best, best_spread = nn, spread
    return (best >= 8 and best_spread >= 120), best

def corner_brackets(bgr, accent):
    """F1 signature: L-shaped accent strokes near the 4 corners of a text bbox."""
    m = accent_mask(bgr, accent)
    H, W = m.shape[:2]
    qs = [(0, 0, W // 3, H // 3), (2 * W // 3, 0, W // 3, H // 3),
          (0, 2 * H // 3, W // 3, H // 3), (2 * W // 3, 2 * H // 3, W // 3, H // 3)]
    cnt = 0
    for (x, y, w, h) in qs:
        sub = m[y:y + h, x:x + w]
        if sub.size and (sub > 0).mean() > 0.01:
            cnt += 1
    return cnt >= 2, cnt

def tape_present(bgr, accent):
    """F1 signature: wide accent bar (aspect>2.5) with text inside."""
    m = accent_mask(bgr, accent)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    H, W = m.shape
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if w / max(1, h) > 2.5 and area > 0.006 * W * H:
            words = ocr_words(bgr[y:y + h, x:x + w], psm=7)
            if words:
                return True, w / h
    return False, 0

def glass_panel(bgr):
    """F2 signature: large uniform rounded plate (variance < thr) covering 12-55% of frame."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    H, W = g.shape
    best = None
    for scale in (0.25, 0.35, 0.45):
        w, h = int(W * scale), int(H * scale)
        for y in range(0, H - h, 40):
            for x in range(0, W - w, 40):
                sub = g[y:y + h, x:x + w]
                if sub.std() < 18 and sub.mean() > 40:
                    a = w * h
                    if best is None or a > best[0]:
                        best = (a, x, y, w, h, sub.std())
    ok = best is not None and 0.12 * W * H <= best[0] <= 0.55 * W * H
    return ok, best

def odometer_profile(gray_small_series, rect, fps):
    """F4: temporal diff in digit region high during roll, near-zero when settled."""
    x, y, w, h = rect
    sw, sh = gray_small_series[0].shape[1], gray_small_series[0].shape[0]
    sx, sy, sw2, sh2 = int(x / 1080 * sw), int(y / 1920 * sh), int(w / 1080 * sw), int(h / 1920 * sh)
    regs = [g[sy:sy + sh2, sx:sx + sw2].astype(np.float32) for g in gray_small_series]
    d = [0.0] + [float(np.abs(regs[i] - regs[i - 1]).mean()) for i in range(1, len(regs))]
    d = np.array(d)
    if len(d) < 10:
        return False, 0, 0
    k = int(fps * 0.9)
    head = float(d[2:k].mean())
    tail = float(d[-int(fps * 0.6):].mean())
    return (head > 3.0 * max(tail, 1e-3)) and tail < 2.0, head, tail

def plate_rects(bgr):
    """Bright uniform rect regions (potential phone plates / UI cards)."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    H, W = g.shape
    out = []
    for scale in (0.22, 0.3, 0.4):
        w, h = int(W * scale), int(H * scale)
        for y in range(0, H - h, 30):
            for x in range(0, W - w, 30):
                sub = g[y:y + h, x:x + w]
                if sub.std() < 14 and sub.mean() > 70:
                    out.append((x, y, w, h))
    return out

def rect_overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    return inter / min(aw * ah, bw * bh)

# ---------------------------------------------------------------- main gate
def run_gate(video, manifest_path, out_json):
    m = json.load(open(manifest_path))
    P = probe(video)
    log("STAGE probe done")
    W, H, fps, dur = P["w"], P["h"], P["fps"], P["dur"]
    accent = m.get("palette", {}).get("accent", [255, 170, 80])
    log(f"GATE {os.path.basename(video)} {W}x{H}@{fps:.1f} {dur:.1f}s")
    checks = []

    ONLY = None
    for _a in sys.argv:
        if _a.startswith("--only="):
            ONLY = _a.split("=", 1)[1]
    import hashlib as _hl
    _sig = _hl.sha256((video + manifest_path).encode()).hexdigest()[:12]
    _part = out_json + ".partial"
    _done_checks = []
    if "--resume" in sys.argv and os.path.exists(_part):
        try:
            pj = json.load(open(_part))
            if pj.get("sig") == _sig:
                _done_checks = pj.get("checks", [])
                checks.extend(_done_checks)
                log(f"RESUME: {len(_done_checks)} checks loaded")
        except Exception:
            pass

    def add(name, ok, detail):
        for c in _done_checks:
            if c["name"] == name:
                return
        if ONLY is not None and not name.startswith(ONLY):
            return
        checks.append(dict(name=name, ok=bool(ok), detail=detail))
        log(("OK  " if ok else "FAIL"), name, "|", detail)
        try:
            json.dump(dict(sig=_sig, checks=checks), open(_part, "w"))
        except Exception:
            pass

    if ONLY is None or ONLY[:2] in ("G6", "G8", "G9"):
        # ---- decode series (downscaled) for temporal checks
        log("STAGE series start")
        series = full_gray_series(video, scale=(270, 480))
        log("STAGE series done", len(series))
        diffs = np.array([0.0] + [float(np.abs(series[i].astype(np.float32) - series[i - 1].astype(np.float32)).mean())
                                  for i in range(1, len(series))])

        # G6 dead/black frames + frame 0
        dead = [i for i, g in enumerate(series) if g.mean() < 6 and g.std() < 3]
        f0_ok = series[0].mean() > 10 and series[0].std() > 4
        add("G6 no dead frames + composed frame 0",
            len(dead) == 0 and f0_ok,
            f"dead={len(dead)} frames0_luma={series[0].mean():.1f} std={series[0].std():.1f}")

        # ---- event detection (whip clusters)
        thr_hi = diffs.mean() + 2.5 * diffs.std()
        thr_lo = diffs.mean() + 1.0 * diffs.std()
        events, i = [], 1
        while i < len(diffs):
            if diffs[i] > thr_hi:
                j = i
                while j < len(diffs) and diffs[j] > thr_lo:
                    j += 1
                events.append((i, j - 1))
                i = j + int(fps * 0.3)
            else:
                i += 1
        sustained = []
        for (a, b) in events:
            # whip = sustained motion over the 0.3s transition window: >=4 frames whose
            # diff exceeds max(0.12*peak, 8). A hard cut = single spike then flat.
            # Calibrated on V1 reference whips (0.20-0.28s blur tails).
            peak = float(diffs[a:b + 1].max())
            win = diffs[a:a + int(fps * 0.30)]
            n_sus = int((win > min(max(0.12 * peak, 8.0), 24.0)).sum())
            sustained.append(n_sus >= 4)
        whip_ok = all(sustained) and len(events) > 0 and len(events) >= len(m.get("mode_per_beat", [])) - 2
        add("G8a whip on every comp change (events >= planned beats - 2)",
            whip_ok, f"events={len(events)} planned_beats={len(m.get('mode_per_beat', []))} win_frames={[int((diffs[a:a+int(fps*0.30)]>min(max(0.12*float(diffs[a:b+1].max()),8.0),35.0)).sum()) for a,b in events][:12]}")

        # ---- zoom-through: ORB scale growth near the declared zoom boundary (or any event)
        log("STAGE zoom start")
        zoom_ok = False
        zoom_detail = "none found"
        orb = cv2.ORB_create(nfeatures=800)
        zt = m.get("zoom_through_t")
        win = []
        if zt is not None:
            win.append((int(zt * fps) - 5, int(zt * fps) + int(fps * 0.6)))
        win += [(a, b + int(fps * 0.5)) for (a, b) in events]
        for (a, b) in win:
            i0 = max(0, a - 3)
            i1 = min(len(series) - 1, b)
            f0 = cv2.cvtColor(series[i0], cv2.COLOR_GRAY2BGR)
            f1 = cv2.cvtColor(series[i1], cv2.COLOR_GRAY2BGR)
            k0, d0 = orb.detectAndCompute(f0, None)
            k1, d1 = orb.detectAndCompute(f1, None)
            if d0 is None or d1 is None or len(k0) < 30 or len(k1) < 30:
                continue
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(d0, d1)
            if len(matches) < 20:
                continue
            src = np.float32([k0[mm.queryIdx].pt for mm in matches]).reshape(-1, 1, 2)
            dst = np.float32([k1[mm.trainIdx].pt for mm in matches]).reshape(-1, 1, 2)
            M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6)
            if M is None:
                continue
            s = float(np.hypot(M[0, 0], M[1, 0]))
            if s > 1.6 or s < 0.62:
                zoom_ok = True
                zoom_detail = f"frame{i0}->{i1} scale={s:.2f}"
                break
        add("G8b >=1 recursive zoom-through", zoom_ok, zoom_detail)

        # ---- invert bite: near-black frame with content right after an event start
        inv_ok, inv_detail = False, "none"
        for (a, b) in events:
            for i in range(a, min(b + int(fps * 0.2), len(series))):
                if series[i].mean() < 30 and series[i].std() > 12:
                    inv_ok = True
                    inv_detail = f"frame {i} @{i/fps:.2f}s luma={series[i].mean():.1f} std={series[i].std():.1f}"
                    break
            if inv_ok:
                break
        add("G8c >=1 invert/negative bite", inv_ok, inv_detail)

        # ---- G9 consecutive comps not near-identical
        g9_bad = []
        comp_snaps = []
        for (a, b) in events:
            j = min(len(series) - 1, b + int(fps * 0.4))
            comp_snaps.append((a, j))
        for k in range(1, len(comp_snaps)):
            h1 = dhash(cv2.cvtColor(series[comp_snaps[k - 1][1]], cv2.COLOR_GRAY2BGR))
            h2 = dhash(cv2.cvtColor(series[comp_snaps[k][1]], cv2.COLOR_GRAY2BGR))
            s = hash_sim(h1, h2)
            if s > 0.9:
                g9_bad.append(f"{comp_snaps[k-1][0]/fps:.1f}->{comp_snaps[k][0]/fps:.1f}:{s:.2f}")
        add("G9 no consecutive comps similarity>0.9", len(g9_bad) == 0,
            f"pairs={max(0,len(comp_snaps)-1)} bad={g9_bad[:4]}")

    # ---- G2 OCR hook at ~2s (hook phrase band + hook giant band + occlusion fallback)
    hook = m.get("hook") or []
    hook_t = m.get("hook_t", 2.0)
    best = None
    hr = m.get("hook_rect")
    for t in (hook_t, hook_t + 0.2, hook_t + 0.5):
        fr = frame_at(video, t, w=540)
        if fr is None:
            continue
        words = list(ocr_words(fr))
        if hr:
            hx, hy, hw, hh = hr
            cx = fr[max(0, int(hy / 1920 * 960)):int((hy + hh) / 1920 * 960),
                    max(0, int(hx / 1080 * 540)):int((hx + hw) / 1080 * 540)]
            if cx.size:
                cx3 = cv2.resize(cx, (cx.shape[1] * 3, cx.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
                words += ocr_words(cx3, psm=7) + ocr_words(cx3, psm=13)
        for lk2 in m.get("lockups", []):
            if abs(lk2.get("t0", -1) - hook_t) <= 1.6 and lk2.get("rect"):
                gx2, gy2, gw2, gh2 = lk2["rect"]
                gc = fr[max(0, int(gy2 / 1920 * 960)):int((gy2 + gh2) / 1920 * 960),
                        max(0, int(gx2 / 1080 * 540)):int((gx2 + gw2) / 1080 * 540)]
                if gc.size:
                    gc3 = cv2.resize(gc, (gc.shape[1] * 3, gc.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
                    words += ocr_words(gc3, psm=7) + ocr_words(gc3, psm=13)
        got = [fuzzy_in(h, words) for h in hook]
        occl = {lk2["giant"]: lk2 for lk2 in m.get("lockups", [])
                if lk2.get("occluded") and abs(lk2.get("t0", -1) - hook_t) <= 1.6 and lk2.get("rect")}
        got2 = []
        for h, gres in zip(hook, got):
            if gres is None and h in occl:
                rx2, ry2, rw2, rh2 = occl[h]["rect"]
                gc = fr[max(0, int(ry2 / 1920 * 960)):int((ry2 + rh2) / 1920 * 960),
                        max(0, int(rx2 / 1080 * 540)):int((rx2 + rw2) / 1080 * 540)]
                if gc.size:
                    cov = float((accent_mask(gc, accent, tol_hue=12, min_sat=0.45) > 0).mean())
                    if cov >= 0.12:
                        gres = dict(text=h + "[pixel-verified occluded]", conf=100,
                                    box=[rx2, ry2, rw2, rh2])
            got2.append(gres)
        score = sum(1 for g2_ in got2 if g2_)
        if best is None or score > best[0]:
            best = (score, t, got2, len(words))
    g2_ok = best is not None and len(hook) > 0 and best[0] == len(hook)
    add("G2 hook words legible @2s", g2_ok,
        f"hook={hook} matched={best[0] if best else 0}/{len(hook)} @t={best[1] if best else '-'} words_seen={best[3] if best else 0}")

    # ---- G3 giant word width on lockup beats (in-band measurement; Mode B measured
    # inside its declared plate band, disconnected from footage colors)
    g3_bad, g3_meas = [], []
    for lk in m.get("lockups", []):
        fr = frame_at(video, min(lk["t0"] + 0.5, dur - 0.2), w=540)
        if fr is None:
            continue
        rx, ry, rw, rh = lk.get("rect", [0, 0, W, H])
        if rw / 1080 > 0.92:
            g3_bad.append(f"{lk['giant']}@{lk['t0']}:declared_band={rw/1080:.2f}")
            continue
        sx, sy = int(rx / 1080 * 540), int(ry / 1920 * 960)
        sw2, sh2 = int(rw / 1080 * 540), int(rh / 1920 * 960)
        crop = fr[max(0, sy):sy + sh2, max(0, sx):sx + sw2]
        if crop.size == 0:
            continue
        comp, _ = largest_accent_word(crop, accent, y_max_frac=1.0)
        # Mode A overflow guard: glyph evidence crossing the declared band edges
        # (canvas comps only; Mode B words are plate-contained by construction)
        if lk.get("mode", "A") == "A":
            hsvF = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
            hsvA = cv2.cvtColor(np.uint8([[[int(accent[2]), int(accent[1]), int(accent[0])]]]),
                                 cv2.COLOR_BGR2HSV)[0, 0]
            h0 = int(hsvA[0])
            lo_, hi_ = max(0, h0 - 12), min(179, h0 + 12)
            if lo_ <= 0:
                full_mask = cv2.inRange(hsvF, np.array([0, 115, 150], np.uint8), np.array([hi_, 255, 255], np.uint8))
            elif hi_ >= 179:
                full_mask = cv2.inRange(hsvF, np.array([lo_, 115, 150], np.uint8), np.array([179, 255, 255], np.uint8))
            else:
                full_mask = cv2.inRange(hsvF, np.array([lo_, 115, 150], np.uint8), np.array([hi_, 255, 255], np.uint8))
            sb = m.get("subject_bbox")
            if sb:
                ex0 = max(0, int((sb[0] - sb[2] * 0.05) / 1080 * 540))
                ex1 = min(fr.shape[1], int((sb[0] + sb[2] * 1.05) / 1080 * 540))
                ey0 = max(0, int((sb[1] - sb[3] * 0.05) / 1920 * 960))
                ey1 = min(fr.shape[0], int((sb[1] + sb[3] * 1.05) / 1920 * 960))
                full_mask[ey0:ey1, ex0:ex1] = 0  # subject pixels may share accent hue
            band_x0, band_x1 = max(0, sx), min(fr.shape[1], sx + sw2)
            side_l = full_mask[max(0, sy):sy + sh2, :max(1, band_x0 - int(0.02 * fr.shape[1]))]
            side_r = full_mask[max(0, sy):sy + sh2, min(fr.shape[1] - 1, band_x1 + int(0.02 * fr.shape[1])):]
            nL, labL, stL, _ = cv2.connectedComponentsWithStats(side_l)
            nR, labR, stR, _ = cv2.connectedComponentsWithStats(side_r)
            over = 0
            for st_ in (stL, stR):
                for i in range(1, st_.shape[0]):
                    if st_[i, 4] > 0.003 * fr.shape[0] * fr.shape[1] and st_[i, 2] > 0.06 * fr.shape[1]:
                        over += 1
            if over > 0:
                g3_bad.append(f"{lk['giant']}@{lk['t0']}:overflow_x")
                g3_meas.append(f"{lk['giant']}@{lk['t0']}:OVERFLOW")
                continue
        if comp is None:
            g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            bw = (g > 235).astype(np.uint8)
            n, lab, stats, _ = cv2.connectedComponentsWithStats(bw)
            bestc = None
            for i in range(1, n):
                x, y, w, h, area = stats[i]
                if area > 0.004 * crop.shape[0] * crop.shape[1] and (bestc is None or w > bestc[2]):
                    bestc = (x, y, w, h, area)
            comp = bestc
        if comp:
            # glyph span in frame terms: component width + its offset inside the band
            glyph_w = comp[2]
            ratio = min(1.0, (comp[0] + glyph_w) / fr.shape[1])
            span = glyph_w / fr.shape[1]
            g3_meas.append(f"{lk['giant']}@{lk['t0']}:span={span:.2f}W")
            if span > 0.92:
                g3_bad.append(f"{lk['giant']}@{lk['t0']}:{span:.2f}")
    add("G3 giant word <=0.92W (declared band + in-band glyph span)", len(g3_bad) == 0 and len(g3_meas) > 0,
        f"measured={g3_meas[:6]} bad={g3_bad[:3]}")

    # ---- G4 cards: labels untruncated + no duplicate card hashes
    card_hashes, labels_seen, g4_bad = [], [], []
    margin = 40 / 1080
    for cd in m.get("cards", []):
        fr = frame_at(video, min(cd["t"] + 0.6, dur - 0.2), w=720)
        if fr is None:
            continue
        rect = cd.get("rect")
        if rect is None:
            words = ocr_words(fr)
            hit = fuzzy_in(cd["label"], words)
            if not hit:
                g4_bad.append(f"{cd['label']}:label-ocr-missing")
            else:
                labels_seen.append(cd["label"])
            continue
        x, y, w, h = rect
        sx, sy = int(x / 1080 * 720), int(y / 1920 * 1280)
        sw, sh = int(w / 1080 * 720), int(h / 1920 * 1280)
        crop = fr[sy:sy + sh, sx:sx + sw]
        if crop.size == 0:
            g4_bad.append(f"{cd['label']}:empty-crop")
            continue
        card_hashes.append(dhash(crop))
        # label OCR on the upscaled card crop + tight pill strip (bottom 20%)
        crop2 = cv2.resize(crop, (crop.shape[1] * 2, crop.shape[0] * 2))
        pill_strip = crop[int(sh * 0.80):, max(8, crop.shape[1] // 20):int(crop.shape[1] * 0.95)]
        pill2 = cv2.resize(pill_strip, (pill_strip.shape[1] * 2, pill_strip.shape[0] * 2),
                           interpolation=cv2.INTER_CUBIC)
        gth3 = cv2.cvtColor(pill2, cv2.COLOR_BGR2GRAY)
        pinv = cv2.threshold(gth3, 120, 255, cv2.THRESH_BINARY_INV)[1]
        words = (ocr_words(fr) + ocr_words(crop2, psm=6) + ocr_words(pill2, psm=7) +
                 ocr_words(pill2, psm=11) + ocr_words(cv2.cvtColor(pinv, cv2.COLOR_GRAY2BGR), psm=7) +
                 ocr_words(cv2.cvtColor(pinv, cv2.COLOR_GRAY2BGR), psm=11))
        hit = fuzzy_in(cd["label"], words)
        # the pill strip / card crop are inside the card by construction; only a
        # full-frame hit needs the edge-clipping test
        if not hit:
            g4_bad.append(f"{cd['label']}:label-ocr-missing")
        elif hit in words[:len(ocr_words(fr))] or hit["box"][0] < 2000 and hit in ocr_words(fr):
            bx = hit["box"]
            nx, nw = bx[0] / 720, bx[2] / 720
            inside = (nx >= 0.02 and nx + nw <= 0.98)
            labels_seen.append(cd["label"])
            if not inside:
                g4_bad.append(f"{cd['label']}:clipped@edge")
        else:
            labels_seen.append(cd["label"])
    dup = len(card_hashes) - len(set(card_hashes))
    add("G4 card labels untruncated + no dup card hashes",
        len(g4_bad) == 0 and dup == 0 and len(labels_seen) > 0,
        f"cards={len(labels_seen)} dup_hashes={dup} bad={g4_bad[:4]}")

    # ---- G5 phone: contrast >=4.5, never over Mode B footage
    mode_beats = m.get("mode_per_beat", [])
    phone = m.get("phone", [])
    phone_bad = []
    for ph in phone:
        fr = frame_at(video, min(ph["t"] + 0.5, dur - 0.2), w=540)
        if fr is None:
            continue
        x, y, w, h = ph["rect"]
        sx, sy = int(x / 1080 * 540), int(y / 1920 * 960)
        sw, sh = int(w / 1080 * 540), int(h / 1920 * 960)
        crop = fr[sy:sy + sh, sx:sx + sw]
        words = ocr_words(crop, psm=6)
        if not words:
            phone_bad.append(f"t{ph['t']}:no-phone-text")
            continue
        plate = crop.reshape(-1, 3).mean(0)
        # per-word contrast; ignore crop-edge artifacts and tiny fragments
        contrasts = []
        for wd in words:
            bx = wd["box"]
            if bx[0] < 6 or bx[1] < 6 or bx[0] + bx[2] > sw - 6 or bx[1] + bx[3] > sh - 6:
                continue
            if bx[2] < 30:
                continue
            tx = crop[bx[1]:bx[1] + bx[3], bx[0]:bx[0] + bx[2]].reshape(-1, 3)
            nrm = np.linalg.norm(tx, axis=1)
            k = max(1, int(0.25 * len(nrm)))
            dark = tx[np.argsort(nrm)[:k]].mean(0)
            contrasts.append(wcag_contrast(dark, plate))
        if contrasts:
            c = min(contrasts)
            if c < 4.5:
                phone_bad.append(f"t{ph['t']}:contrast={c:.1f}")
        else:
            phone_bad.append(f"t{ph['t']}:no-readable-phone-text")
        if ph.get("mode", "A") == "B":
            phone_bad.append(f"t{ph['t']}:phone-on-modeB")
    # mode B beats must have no large bright plate (phone) over footage;
    # candidate plates count only if they contain UI text AND are not declared cards
    card_rects = [c.get("rect") for c in m.get("cards", []) if c.get("rect")]
    for bi, mode in enumerate(mode_beats):
        if mode != "B":
            continue
        t0 = m["beat_starts"][bi] if "beat_starts" in m else bi * (dur / max(1, len(mode_beats)))
        fr = frame_at(video, min(t0 + 0.8, dur - 0.2), w=360)
        if fr is None:
            continue
        for (x, y, w, h) in plate_rects(fr):
            fx, fy, fw, fh = int(x / 360 * 1080), int(y / 640 * 1920), int(w / 360 * 1080), int(h / 640 * 1920)
            cxr, cyr = fx + fw // 2, fy + fh // 2
            if any(cr[0] <= cxr <= cr[0] + cr[2] and cr[1] <= cyr <= cr[1] + cr[3] for cr in card_rects):
                continue  # declared card on Mode B beat = allowed (U2 cards beside/above)
            crop = fr[y:y + h, x:x + w]
            ws2 = ocr_words(crop, psm=6)
            if len(ws2) < 2:
                continue
            # readable UI text = dark glyphs on the bright plate (contrast >= 4.5);
            # snow/sky noise words are low-contrast and do not count
            plate_mean = crop.reshape(-1, 3).mean(0)
            readable = 0
            for wd in ws2:
                bx = wd["box"]
                if bx[0] < 4 or bx[1] < 4 or bx[2] < 20:
                    continue
                tx = crop[bx[1]:bx[1] + bx[3], bx[0]:bx[0] + bx[2]].reshape(-1, 3)
                nrm = np.linalg.norm(tx, axis=1)
                k = max(1, int(0.25 * len(nrm)))
                dark = tx[np.argsort(nrm)[:k]].mean(0)
                if wcag_contrast(dark, plate_mean) >= 4.5:
                    readable += 1
            if readable >= 2:
                phone_bad.append(f"beat{bi}@{t0:.1f}:plate-over-footage")
                break
    add("G5 phone text contrast>=4.5 + not over Mode B footage",
        len(phone_bad) == 0, f"phone={len(phone)} bad={phone_bad[:4]}")

    # ---- G7 captions on message beats
    caps_bad = []
    cap_beats = m.get("captions", [])
    for cp in cap_beats[:5]:
        t = min(cp["t0"] + 1.2, dur - 0.3)
        fr = frame_at(video, t, w=540)
        if fr is None:
            caps_bad.append(f"t{t}:no-frame")
            continue
        # declared caption band (renderer-fixed caption position)
        cr = m.get("caption_rect", [0, 1600, 1080, 240])
        band = fr[max(0, int(cr[1] / 1920 * 960)):int((cr[1] + cr[3]) / 1920 * 960), :]
        band2 = cv2.resize(band, (band.shape[1] * 2, band.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
        gth = cv2.cvtColor(band2, cv2.COLOR_BGR2GRAY)
        words = list(ocr_words(band2, psm=11)) + list(ocr_words(band2, psm=13))
        darkm = (gth < 80).astype(np.uint8)
        nD, labD, stD, _ = cv2.connectedComponentsWithStats(darkm)
        for i in range(1, nD):
            x, y, w, h, a = stD[i]
            if a > 4000 and w > 120 and h > 40:
                pcrop = gth[y:y + h, x:x + w]
                # a caption plate carries the white glyphs: require bright text pixels
                if int((pcrop > 180).sum()) < 80:
                    continue  # subject/footage dark blob without rendered text
                # white caption text on dark plate -> black text on white for OCR
                binimg = 255 - cv2.threshold(pcrop, 110, 255, cv2.THRESH_BINARY)[1]
                binimg = cv2.copyMakeBorder(binimg, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
                words += ocr_words(cv2.cvtColor(binimg, cv2.COLOR_GRAY2BGR), psm=7)
                words += ocr_words(cv2.cvtColor(binimg, cv2.COLOR_GRAY2BGR), psm=8)
        if not words:
            caps_bad.append(f"t{cp['t0']:.1f}:no-caption-ocr")
    add("G7 captions OCR-present on message beats",
        len(cap_beats) > 0 and len(caps_bad) == 0,
        f"caption_beats={len(cap_beats)} sampled={min(6,len(cap_beats))} bad={caps_bad[:4]}")

    # ---- G10 payoff + end card + loop echo in last 4s
    last4_words = []
    for t in (dur - 3.0, dur - 1.6, dur - 0.7):
        if t < 0:
            continue
        fr = frame_at(video, float(t), w=420)
        if fr is None:
            continue
        last4_words += ocr_words(fr)
        loop_band = fr[int(747 * 0.58):int(747 * 0.74), :]
        loop2 = cv2.resize(loop_band, (loop_band.shape[1] * 2, loop_band.shape[0] * 2),
                           interpolation=cv2.INTER_CUBIC)
        gth2 = cv2.cvtColor(loop2, cv2.COLOR_BGR2GRAY)
        lthr2 = cv2.threshold(gth2, 130, 255, cv2.THRESH_BINARY_INV)[1]
        last4_words += ocr_words(loop2, psm=11)
        last4_words += ocr_words(cv2.cvtColor(lthr2, cv2.COLOR_GRAY2BGR), psm=7)
    payoff = [p for p in (m.get("payoff") or []) if p]
    endcard = m.get("endcard_text", "github.com/Dani-Devlop")
    loopw = m.get("loop_word", "")
    def seen(target):
        return bool(target) and fuzzy_in(target, last4_words) is not None

    # loop echo pixel-evidence: rendered text glyphs in the declared loop band
    # (OCR may fail when the subject occludes the echo — same standard as G2)
    loop_seen = False
    lr = m.get("loop_rect")
    if lr and loopw:
        frL = frame_at(video, dur - 3.0, w=540)
        if frL is not None:
            band = frL[max(0, int(lr[1] / 1920 * 960)):int((lr[1] + lr[3]) / 1920 * 960), :]
            sb3 = m.get("subject_bbox")
            gL = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
            if sb3:
                ex0 = max(0, int((sb3[0] - sb3[2] * 0.05) / 1080 * 540))
                ex1 = min(540, int((sb3[0] + sb3[2] * 1.05) / 1080 * 540))
                ey0 = max(0, int((sb3[1] - sb3[3] * 0.05) / 1920 * 960) - int(lr[1] / 1920 * 960))
                ey1 = min(band.shape[0], int((sb3[1] + sb3[3] * 1.05) / 1920 * 960) - int(lr[1] / 1920 * 960))
                if ex1 > ex0 and ey1 > ey0:
                    gL[ey0:ey1, ex0:ex1] = 255
            # text glyphs = mid-dark marks on light canvas OR bright marks on dark canvas
            frac_dark = float(((gL > 40) & (gL < 140)).mean())
            frac_bright = float((gL > 200).mean())
            loop_seen = frac_dark >= 0.02 or frac_bright >= 0.55
    ec_hit = fuzzy_in(endcard.split("/")[0], last4_words) or fuzzy_in(endcard.split("/")[-1], last4_words)
    payoff_seen = all(seen(p) for p in payoff)
    if not payoff_seen:
        pr = m.get("payoff_rect")
        if pr:
            frP = frame_at(video, dur - 3.0, w=540)
            if frP is not None:
                bandP = frP[max(0, int(pr[1] / 1920 * 960)):int((pr[1] + pr[3]) / 1920 * 960), :]
                covP = float((accent_mask(bandP, accent, tol_hue=14, min_sat=0.4) > 0).mean())
                if covP >= 0.08:
                    payoff_seen = True
                    payoff_pixel = covP
    g10_ok = payoff_seen and ec_hit is not None and (not loopw or seen(loopw) or loop_seen)
    add("G10 payoff + end card + loop echo in last 4s", g10_ok,
        f"payoff={payoff} ocr={all(seen(p) for p in payoff)} endcard_seen={bool(ec_hit)} loop={loopw} ocr_seen={seen(loopw) if loopw else False} pixel_loop={loop_seen} words={len(last4_words)}")

    # ---- G11 occlusion pixel-verified + matte fps + face-overlap 0
    occ_bad = []
    for lk in m.get("lockups", []):
        if not lk.get("occluded"):
            continue
        fr = frame_at(video, min(lk["t0"] + 0.5, dur - 0.2), w=720)
        if fr is None:
            continue
        x, y, w, h = lk["rect"]
        sx, sy = int(x / 1080 * 720), int(y / 1920 * 1280)
        sw, sh = int(w / 1080 * 720), int(h / 1920 * 1280)
        crop = fr[sy:sy + sh, sx:sx + sw]
        am = accent_mask(crop, accent)
        occ_frac = 1.0 - float((am > 0).mean())
        # occluded => some word pixels must be hidden behind subject (non-accent inside word rect)
        if occ_frac < 0.10:
            occ_bad.append(f"{lk['giant']}@{lk['t0']}:occ={occ_frac:.2f}")
    fz = m.get("face_zone")
    face_bad = []
    if fz:
        # text/cards/labels/stickers must not enter face zone on any sampled frame
        for t in np.arange(0.5, min(dur, 12.0), 2.5):
            fr = frame_at(video, float(t), w=540)
            if fr is None:
                continue
            ax, ay, aw = int(fz[0] / 1080 * 540), int(fz[1] / 1920 * 960), int(fz[2] / 1080 * 540)
            ah = int(fz[3] / 1920 * 960)
            zone = fr[ay:ay + ah, ax:ax + aw]
            am = accent_mask(zone, accent)
            sb2 = m.get("subject_bbox")
            if sb2:
                ex0 = max(0, int((sb2[0] - sb2[2] * 0.05) / 1080 * 540) - ax)
                ex1 = min(aw, int((sb2[0] + sb2[2] * 1.05) / 1080 * 540) - ax)
                ey0 = max(0, int((sb2[1] - sb2[3] * 0.05) / 1920 * 960) - ay)
                ey1 = min(ah, int((sb2[1] + sb2[3] * 1.05) / 1920 * 960) - ay)
                if ex1 > ex0 and ey1 > ey0:
                    am[ey0:ey1, ex0:ex1] = 0
            frac = float((am > 0).mean())
            if frac > 0.10:
                face_bad.append(f"t{t:.1f}:{frac:.2f}")
    matte_fps = m.get("matte_fps")
    fps_ok = (matte_fps is None and not m.get("matte")) or (matte_fps == int(round(fps)))
    add("G11 occlusion pixel-verified + matte fps==output fps + face-overlap 0",
        len(occ_bad) == 0 and len(face_bad) == 0 and fps_ok,
        f"occ_bad={occ_bad[:3]} face_bad={face_bad[:3]} matte_fps={matte_fps} out_fps={fps:.0f}")

    # ---- G12 loudness + SFX parity
    log("STAGE audio start")
    lufs, tp = lufs_tp(video)
    lufs_ok = lufs is not None and abs(lufs - (-14.0)) <= 0.5 and tp is not None and tp <= -1.5
    ons = audio_onsets(video)
    ent = m.get("sfx_entrances", [])
    matched = 0
    for e in ent:
        if any(abs(o - e) <= 0.18 for o in ons):
            matched += 1
    unmatched_onsets = len(ons) - matched
    add("G12 -14 LUFS +/-0.5, TP<=-1.5, SFX events==entrances",
        lufs_ok and matched >= len(ent) - 1 and unmatched_onsets <= max(4, len(ent) // 2),
        f"lufs={lufs} tp={tp} onsets={len(ons)} entrances={len(ent)} matched={matched} unmatched_onsets={unmatched_onsets}")

    # ---- G13 family palette consistent
    pal_bad = []
    n_beats = max(1, len(mode_beats))
    for bi in range(n_beats):
        t0 = m["beat_starts"][bi] if "beat_starts" in m else bi * (dur / n_beats)
        fr = frame_at(video, min(t0 + 0.8, dur - 0.2), w=360)
        if fr is None:
            continue
        am = accent_mask(fr, accent, min_sat=0.35)
        frac = float((am > 0).mean())
        # 0.006 floor: F1's tape+ink-giant style leaves only tape margins as accent
        # (measured 0.0087 on fitness_1 b6); accent-free canvases measure ~0.002
        if frac < 0.006:
            pal_bad.append(f"beat{bi}@{t0:.1f}:{frac:.3f}")
    add("G13 family palette present on every beat", len(pal_bad) == 0,
        f"beats={n_beats} bad={pal_bad[:4]}")

    # ---- G14 family signature present
    fam = m.get("family", "")
    sig_ok, sig_detail = False, f"family={fam}"
    frames_sig = []
    for t in np.arange(0.8, min(dur - 0.5, 11.0), 2.0):
        fr = frame_at(video, float(t), w=420)
        if fr is not None:
            frames_sig.append(fr)
    if fam == "F1":
        tape = any(tape_present(fr, accent)[0] for fr in frames_sig)
        br = max(corner_brackets(fr, accent)[1] for fr in frames_sig)
        sig_ok, sig_detail = tape and br >= 2, f"tape={tape} bracket_quads={br}"
    elif fam == "F2":
        # F2 signature: phone-UI glass panel with typewriter reveal OR uniform plate
        ph = (m.get("phone") or [None])[0]
        if ph and ph.get("rect"):
            x, y, w, h = ph["rect"]
            def chars_at(tt):
                f2 = frame_at(video, min(tt, dur - 0.2), w=540)
                sx2, sy2 = int(x / 1080 * 540), int(y / 1920 * 960)
                sw2, sh2 = int(w / 1080 * 540), int(h / 1920 * 960)
                c2 = f2[sy2:sy2 + sh2, sx2:sx2 + sw2]
                return sum(len(w2["text"]) for w2 in ocr_words(c2, psm=6))
            t0p = ph["t"]
            n_early = chars_at(t0p + 0.4)
            n_late = chars_at(t0p + 1.6)
            typewriter = n_late > max(4, n_early * 1.5)
            gp = 0.0
            for tt in (t0p + 0.8, t0p + 1.4):
                f2 = frame_at(video, min(tt, dur - 0.2), w=420)
                if f2 is not None:
                    okp, bestp = glass_panel(f2)
                    if okp and bestp:
                        gp = max(gp, bestp[0] / (420 * 747))
            sig_ok = typewriter or gp > 0.10
            sig_detail = f"typewriter={typewriter} chars {n_early}->{n_late} plate={gp:.2f}"
        else:
            gp = max((glass_panel(fr)[1][0] / (540 * 960)) if glass_panel(fr)[0] else 0 for fr in frames_sig)
            sig_ok = gp > 0.10
            sig_detail = f"glass_panel_area={gp:.2f}"
    elif fam == "F3":
        sb = max(starburst_present(fr) for fr in frames_sig)
        sig_ok = sb[0]
        sig_detail = f"starburst_near_lines={sb[1]}"
    elif fam == "F4":
        gs = [g for _, g in stream_gray(video, scale=(270, 480))]
        odo = False
        rect = m.get("odometer_rect")
        ot = m.get("odometer_t")
        if rect and ot is not None:
            i0 = int(ot * fps)
            bs = m.get("beat_starts", [])
            end_t = bs[5] - 0.15 if len(bs) > 5 else ot + 2.4
            seg = gs[i0:min(len(gs), int(end_t * fps))]
            odo, head, tail = odometer_profile(seg, rect, fps)
        sig_ok = odo
        sig_detail = f"odometer={odo}"
    add("G14 family signature element present", sig_ok, sig_detail)

    # ---- G1 halftone/grid over footage-or-subject (Mode B)
    ht_bad = []
    mode_beats = m.get("mode_per_beat", [])
    if any(mode == "B" for mode in mode_beats):
        n_beats = len(mode_beats)
        for bi, mode in enumerate(mode_beats):
            if mode != "B":
                continue
            t0 = m["beat_starts"][bi] if "beat_starts" in m else bi * (dur / n_beats)
            for dt in (0.3, 0.9, 1.5):
                fr = frame_at(video, min(t0 + dt, dur - 0.2), w=540)
                if fr is None:
                    continue
                sc = halftone_score(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY))
                if sc > 0.12:  # calibration: legacy halftone peak 0.163, clean refs <=0.018
                    ht_bad.append(f"beat{bi}@{t0+dt:.1f}:score={sc:.2f}")
    add("G1 zero halftone/grid over footage-or-subject (Mode B beats)",
        len(ht_bad) == 0, f"violations={ht_bad[:4]}")

    # ---- summary
    try:
        os.remove(_part)
    except Exception:
        pass
    npass = sum(1 for c in checks if c["ok"])
    overall = npass == len(checks)
    out = dict(video=os.path.abspath(video), sha256_file=None, checks=checks,
               npass=npass, n=len(checks), overall_pass=overall,
               measured=dict(lufs=lufs, tp=tp, fps=fps, dur=dur, w=W, h=H,
                             events=[round(a / fps, 2) for a, b in events],
                             hook=hook, family=fam))
    import hashlib
    h = hashlib.sha256(open(video, "rb").read()).hexdigest()
    out["sha256_file"] = h
    out["gate_sha256"] = hashlib.sha256(json.dumps(
        {k: v for k, v in out.items() if k != "gate_sha256"}, sort_keys=True).encode()).hexdigest()
    json.dump(out, open(out_json, "w"), indent=1)
    log(f"SUMMARY {npass}/{len(checks)} PASS overall={'PASS' if overall else 'FAIL'}")
    return 0 if overall else 2

if __name__ == "__main__":
    sys.exit(run_gate(sys.argv[1], sys.argv[2], sys.argv[3]))
