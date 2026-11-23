#!/usr/bin/env python3
"""Phase 16.0 library — TWENTY-PILLAR engine additions on top of p14_lib.
P1 karaoke state-machine v2 (full-sentence, loop, RTL) | P2 type craft |
P3 occlusion | P5 motion | P6 transitions | P7 grade science | P8 stakes.
All drawing measured-friendly (deterministic boxes exported for gates)."""
import numpy as np, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from p14_lib import font, text_w, DEJAVU_B, DEJAVU

VAZIR_B = "/tmp/ems-work/p16/assets/Vazirmatn-Bold.ttf"
VAZIR_R = "/tmp/ems-work/p16/assets/Vazirmatn-Regular.ttf"
ACCENT_DIM_F = 0.45          # P1 spoken dim ~45%
ACTIVE_SCALE = 1.2           # P1 active scale

def font_px_for_lang(px, rtl=False):
    path = VAZIR_B if rtl else DEJAVU_B
    if rtl and not os.path.exists(path):
        path = DEJAVU_B
    return ImageFont.truetype(path, px)

# ---------------- P1: karaoke state machine v2 ----------------
def sentences_from_words(words, max_gap=1.2):
    """Split into sentences on punctuation or gap > max_gap. Returns list of word-lists."""
    sents, cur = [], []
    for w in words:
        if cur and (w["start"] - cur[-1]["end"] > max_gap):
            sents.append(cur); cur = []
        cur.append(w)
        if w["w"].rstrip().endswith((".", "!", "?")):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    return sents

def sentence_windows(sents, preroll=0.35, max_gap_hold=2.5):
    """Each sentence visible from t0-preroll until next sentence start (minus 0.05);
    sweep loops inside that window. Gaps > max_gap_hold -> visibility gap (None)."""
    wins = []
    for i, s in enumerate(sents):
        t0 = s[0]["start"] - preroll
        t_end_last = s[-1]["end"]
        if i + 1 < len(sents):
            t_next = sents[i + 1][0]["start"] - 0.05
            t1 = t_next if (t_next - t_end_last) <= max_gap_hold else t_end_last + max_gap_hold
        else:
            t1 = t_end_last + 1.0
        wins.append({"i": i, "t0": max(0.0, t0), "t1": t1, "words": s})
    return wins

def line_width(words, f, font_px, active_scale=ACTIVE_SCALE):
    """Widths reserved at ACTIVE scale (1.2x) so a scaled active word never
    overlaps neighbours; boxes stay stable across the sweep."""
    gap = int(font_px * 0.30)
    return int(sum(text_w(w["w"], f) * active_scale for w in words) + gap * (len(words) - 1))

def karaoke_layout(sent_words, out_w, font_px=56, rtl=False, lo=2, hi=6, max_lines=2, width_frac=0.88):
    """Deterministic layout: wrap into <=2 lines of lo..hi words, fit width.
    Returns dict with lines (word idx lists), boxes (x0,x1) per word, font_px."""
    chosen = font_px
    f = font_px_for_lang(chosen, rtl)
    lines = None
    while chosen > 24:
        f = font_px_for_lang(chosen, rtl)
        lines, cur = [], []
        for w in sent_words:
            cand = cur + [w]
            lw = line_width(cand, f, chosen)
            if len(cur) >= hi or (lw > out_w * width_frac and cur):
                lines.append(cur); cur = [w]
            else:
                cur = cand
        if cur:
            lines.append(cur)
        ok = (len(lines) <= max_lines) and all(len(l) <= hi for l in lines) \
            and all((len(l) >= lo) or (len(sent_words) < 2 * lo) or (chosen <= 30) for l in lines)
        if ok and len(lines) <= max_lines:
            break
        chosen -= 2
    f = font_px_for_lang(chosen, rtl)
    boxes = []
    for li, line in enumerate(lines):
        total = line_width(line, f, chosen)
        gap = int(chosen * 0.30)
        x = int((out_w - total) / 2)
        for wi, w in enumerate(line):
            wpx = text_w(w["w"], f) * ACTIVE_SCALE
            boxes.append({"line": li, "idx": wi, "x0": int(x), "x1": int(x + wpx),
                          "word": w["w"]})
            x += wpx + gap
    if rtl:
        # bidi: logical word 0 must appear RIGHTMOST for RTL readers
        for b in boxes:
            b["x0"], b["x1"] = out_w - b["x1"], out_w - b["x0"]
    return {"lines": lines, "boxes": boxes, "font_px": chosen, "rtl": rtl}

def karaoke_state_v2(words, t, preroll=0.35):
    """State at t: sentence idx, active word idx, spoken set, loop flag.
    Sweep loops inside sentence window until sentence change."""
    sents = sentences_from_words(words)
    wins = sentence_windows(sents, preroll=preroll)
    for win in wins:
        if win["t0"] <= t < win["t1"]:
            s = win["words"]
            t_start, t_end_last = s[0]["start"], s[-1]["end"]
            lt = t
            looped = False
            if t < t_start:
                lt = t_start
            elif t > t_end_last and t_end_last > t_start:
                span = max(t_end_last - t_start, 0.4)
                lt = t_start + ((t - t_end_last) % span)   # LOOP restart
                looped = True
            active = 0 if lt <= s[0]["start"] else len(s) - 1
            for i, w in enumerate(s):
                if w["start"] - 0.03 <= lt < w["end"] + 0.03:
                    active = i; break
            spoken = set(range(0, active))
            return {"sent_i": win["i"], "active": active, "spoken": spoken,
                    "looped": looped, "win": win, "lt": lt}
    return None

def draw_karaoke_v2(im, words, state, layout, accent, band_y0, band_y1,
                    stroke=3, glow=True, rtl=False, boxes_out=None):
    """Full sentence always: per-line centered. active=accent+1.2x+glow,
    spoken=dim45%, upcoming=white. NO partial reveal — every word drawn complete."""
    d = ImageDraw.Draw(im)
    s = state["win"]["words"]
    f = font_px_for_lang(layout["font_px"], rtl)
    f_act = font_px_for_lang(int(layout["font_px"] * ACTIVE_SCALE), rtl)
    ymid = (band_y0 + band_y1) // 2
    lh = int(layout["font_px"] * 1.22)
    line_count = len(layout["lines"])
    for li, line in enumerate(layout["lines"]):
        lbox = [b for b in layout["boxes"] if b["line"] == li]
        y = ymid + (li - (line_count - 1) / 2.0) * lh
        for b in lbox:
            gi = 0
            cnt = 0
            for lj, l2 in enumerate(layout["lines"]):
                if lj == li:
                    gi = cnt + b["idx"]; break
                cnt += len(l2)
            is_act = (gi == state["active"])
            spoken = gi in state["spoken"]
            w = s[gi]
            fill = accent if is_act else ((int(255 * ACCENT_DIM_F),) * 3 if spoken else (255, 255, 255))
            fnt = f_act if is_act else f
            if is_act and glow:
                gl = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dg = ImageDraw.Draw(gl)
                dg.text(((b["x0"] + b["x1"]) / 2, y), w["w"], font=fnt,
                        fill=accent + (160,), anchor="mm")
                gl = gl.filter(ImageFilter.GaussianBlur(6))
                im.paste(Image.alpha_composite(im.convert("RGBA"), gl).convert("RGB"), (0, 0))
                d = ImageDraw.Draw(im)
            d.text(((b["x0"] + b["x1"]) / 2, y), w["w"], font=fnt, fill=fill,
                   stroke_width=stroke, stroke_fill=(10, 10, 10), anchor="mm")
            if boxes_out is not None:
                boxes_out.append({"x0": b["x0"], "x1": b["x1"], "line": li, "gi": gi,
                                  "active": is_act, "spoken": spoken,
                                  "y0": int(y - lh / 2), "y1": int(y + lh / 2), "word": w["w"]})
    return im

# ---------------- P2: type craft ----------------
def hook_slam_lockup(im, kicker, giant, cont, accent, out_w, y_top_frac=0.20,
                     settle=0.28, t_lt=1.0, ghost=True, tape=None):
    """Mixed-scale lockup: kicker + GIANT accent + continuation. Type-slam settle
    (1.35 -> 1.0 overshoot). Ghost echo. Fully composed at t=0 (no reveal)."""
    d = ImageDraw.Draw(im)
    W, H = im.size
    e = min(1.0, t_lt / settle) if settle > 0 else 1.0
    sc = 1.35 - 0.35 * e
    if e > 0.75:
        sc = 1.0 + 0.035 * math.sin((e - 0.75) / 0.25 * math.pi)
    px = 96
    fg = font(px)
    while text_w(giant, fg) > out_w * 0.80 and px > 40:
        px -= 2; fg = font(px)
    fg = font(int(px * sc))
    fk = font(int(px * 0.34 * sc)); fc = font(int(px * 0.36 * sc))
    y0 = int(H * y_top_frac)
    if ghost:
        off = int(6 * (1 - e) + 3)
        d.text((W // 2 + off, y0 + off), giant, font=fg, fill=(int(255 * 0.28),) * 3,
               anchor="mm", stroke_width=1, stroke_fill=(60, 60, 60))
    if tape:
        tw = text_w(giant, fg)
        d.rectangle([W // 2 - tw / 2 - 12, y0 - px * 0.52, W // 2 + tw / 2 + 12, y0 + px * 0.52],
                    fill=tape)
    if kicker:
        d.text((W // 2, y0 - px * 0.62), kicker, font=fk, fill=(255, 255, 255),
               stroke_width=2, stroke_fill=(10, 10, 10), anchor="mm")
    d.text((W // 2, y0), giant, font=fg, fill=accent,
           stroke_width=4, stroke_fill=(10, 10, 10), anchor="mm")
    if cont:
        d.text((W // 2, y0 + px * 0.62), cont, font=fc, fill=(255, 255, 255),
               stroke_width=3, stroke_fill=(10, 10, 10), anchor="mm")
    return im

def ghost_echo_word(im, xy, word, fpx, accent, lt, anchor="mm"):
    d = ImageDraw.Draw(im)
    f = font(fpx)
    fade = max(0.0, 1.0 - lt * 2.2)
    if fade > 0.05:
        v = int(255 * 0.30 * fade)
        d.text((xy[0] - 8 * (1 - fade) - 4, xy[1]), word, font=f, fill=(v, v, v), anchor=anchor)
    d.text(xy, word, font=f, fill=accent, anchor=anchor)
    return im

def highlighter_tape(im, x0, y0, x1, y1, color=(255, 230, 0), prog=1.0):
    d = ImageDraw.Draw(im)
    w = (x1 - x0) * min(1.0, prog)
    d.rectangle([x0, y0, x0 + w, y1], fill=color)
    return im

def selection_brackets(im, x0, y0, x1, y1, accent, lt):
    d = ImageDraw.Draw(im)
    L = int(min(x1 - x0, y1 - y0) * 0.28)
    g = int(6 * (1 - min(1.0, lt * 3)))
    x0, y0, x1, y1 = x0 - g, y0 - g, x1 + g, y1 + g
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=accent, width=5)
        d.line([(cx, cy), (cx, cy + sy * L)], fill=accent, width=5)
    return im

# ---------------- P5 motion / P6 transitions ----------------
def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t

def motion_blur_h(im, strength=8):
    a = np.asarray(im).astype(np.float32)
    from scipy.ndimage import uniform_filter1d
    out = np.stack([uniform_filter1d(a[:, :, c], max(1, strength), axis=1) for c in range(3)], axis=2)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def light_leak(im, lt, dur=0.4, color=(255, 170, 90), strength=0.35):
    if lt > dur: return im
    f = 1 - lt / dur
    W, H = im.size
    grad = Image.new("L", (W, H), 0)
    dg = ImageDraw.Draw(grad)
    for i in range(H):
        v = int(255 * f * max(0.0, 1.0 - abs(i / H - 0.35) * 2.2))
        dg.line([(0, i), (W, i)], fill=v)
    leak = Image.new("RGB", (W, H), color)
    im.paste(Image.blend(im, leak, strength * f), (0, 0), grad)
    return im

def halftone_overlay(im, cell=8):
    """Halftone dots — ONLY for negative regression clips (texture gate must fail it)."""
    a = np.asarray(im.convert("L")).astype(np.float32) / 255.0
    h, w = a.shape
    step = max(3, cell // 2)
    out = im.copy()
    d = ImageDraw.Draw(out)
    ys, xs = np.mgrid[0:h:step, 0:w:step]
    for y, x in zip(ys.ravel(), xs.ravel()):
        r = max(0.4, (1.0 - a[y, x]) * step * 0.62)
        if r > 0.5:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(12, 12, 12))
    return out

def odometer(im, cx, cy, value, fpx=64, digits=3, accent=(189, 255, 0), settle_lt=0.0):
    d = ImageDraw.Draw(im)
    f = font(fpx)
    tnorm = min(1.0, settle_lt / 0.6)
    shown = int(value * ease_out_cubic(tnorm))
    s = str(shown).rjust(digits, "0")
    d.rounded_rectangle([cx - fpx * 1.6, cy - fpx * 0.8, cx + fpx * 1.6, cy + fpx * 0.8],
                        radius=10, fill=(12, 12, 12), outline=accent, width=2)
    d.text((cx, cy), s, font=f, fill=accent, anchor="mm")
    return im

def starburst_drawon(im, cx, cy, r_out, lt, accent, rays=12):
    d = ImageDraw.Draw(im)
    r_in = int(r_out * 0.42)
    prog = min(1.0, lt / 0.5)
    n = max(1, int(rays * ease_out_cubic(prog)))
    for i in range(n):
        ang = i / rays * 2 * math.pi
        d.line([(cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)),
                (cx + r_out * math.cos(ang), cy + r_out * math.sin(ang))],
               fill=accent, width=4)
    return im

def orbit_card(im, center, angle_deg, w, h, label, sub, accent):
    d = ImageDraw.Draw(im)
    cx, cy = center
    rad = math.radians(angle_deg)
    x = cx + int(w * 0.9 * math.cos(rad))
    y = cy + int(h * 0.22 * math.sin(rad))
    card = Image.new("RGBA", (int(w), int(h)), (12, 12, 12, 235))
    dc = ImageDraw.Draw(card)
    dc.rounded_rectangle([0, 0, w - 1, h - 1], radius=12, outline=accent, width=3)
    f1 = font(int(h * 0.30)); f2 = font(int(h * 0.20))
    dc.text((w // 2, int(h * 0.38)), label, font=f1, fill=accent, anchor="mm")
    dc.text((w // 2, int(h * 0.70)), sub, font=f2, fill=(255, 255, 255), anchor="mm")
    im.paste(card, (int(x - w / 2), int(y - h / 2)), card)
    return im

# ---------------- P7 grade science ----------------
def halation_bloom(img_np, strength=0.22, thresh=200):
    a = img_np / 255.0
    m = (a.mean(axis=2) > thresh / 255.0).astype(np.float32)
    from scipy.ndimage import gaussian_filter
    b = gaussian_filter(m, 9.0)
    out = a + (b[:, :, None] * np.array([1.0, 0.86, 0.62])[None, None, :] * strength)
    return np.clip(out * 255.0, 0, 255)

def skin_tone_protect(img_np, shift=0.85):
    a = img_np / 255.0
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    skin = (r > 0.55) & (r > g * 1.15) & (g > b * 1.05) & (b < r * 0.95)
    a[skin] = a[skin] * shift + a[skin] * (1 - shift) * 0.4
    return np.clip(a * 255.0, 0, 255)

def grade_leap(img_np, base="bw"):
    """P7 pipeline: lift floor, S-curve, halation, skin protect."""
    g = img_np.mean(axis=2, keepdims=True)
    g = (g - 128) * 1.16 + 130
    s = 1 / (1 + np.exp(-(g - 118) / 46.0))
    g = g * 0.75 + s * 255 * 0.25
    g = np.clip(g, 0, 255)
    g = 8 + (g / 255.0) * (255 - 8)
    if base == "bw":
        out = np.repeat(g, 3, axis=2)
    else:
        chroma = img_np - img_np.mean(axis=2, keepdims=True)
        out = np.clip(g + chroma * 1.12, 0, 255)
    out = halation_bloom(out)
    out = skin_tone_protect(out)
    return out
