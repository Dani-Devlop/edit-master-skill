#!/usr/bin/env python3
"""Wavely renderlib — graphics-first composition primitives.
Ported grammar: remotion-captions-themes karaoke state machine (CV2),
reels-editor safe-area rules (top 300 / bottom 480 / sides 130 @1080x1920),
MotionCraft timing (spring/overshoot/stagger/title-holds). Engine log: python-pil/numpy/ffmpeg."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = "/home/z/my-project/download/edit-master-skill"
FONTS = f"{REPO}/assets/fonts"

VOLT = (216, 243, 74)
NAVY_A = (18, 32, 74)
NAVY_B = (8, 14, 40)
RED_A = (74, 13, 18)
RED_B = (28, 4, 7)
GREEN_A = (122, 160, 20)
GREEN_B = (52, 76, 10)
PAPER = (250, 250, 248)
INK = (20, 20, 22)


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def montserrat(size, weight=900):
    return font(f"{FONTS}/Montserrat.ttf", size, weight)


def playfair(size, weight=700):
    return font(f"{FONTS}/PlayfairDisplay.ttf", size, weight)


def playfair_italic(size, weight=700):
    return font(f"{FONTS}/PlayfairItalic.ttf", size, weight)


def mono(size, bold=False):
    return font(f"{FONTS}/SpaceMonoBold.ttf" if bold else f"{FONTS}/SpaceMono.ttf", size)


# ---------------- easing (MotionCraft: no linear) ----------------
def ease_out_back(t, s=1.70158 * 0.66):
    t = min(max(t, 0.0), 1.0)
    t1 = t - 1
    return 1 + (s + 1) * (t1 ** 3) + s * (t1 ** 2)


def ease_out_cubic(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def spring_scale(t, dur=0.32, overshoot=1.10):
    """entrance 120-400ms with overshoot 1.06-1.12 + settle"""
    if t <= 0:
        return 0.0
    if t >= dur:
        return 1.0
    x = t / dur
    return ease_out_back(x, 1.9 * (overshoot - 1.0) * 2.2)


# ---------------- designed canvases (AS2: design, never blur-bg) ----------------
def _grain(img, strength=6):
    w, h = img.size
    noise = (np.random.default_rng(7).standard_normal((h, w, 1)) * strength)
    arr = np.asarray(img).astype(np.int16) + noise.astype(np.int16)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _vignette(img, k=0.22):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    d = np.sqrt(((xx - cx) / (w * 0.62)) ** 2 + ((yy - cy) / (h * 0.62)) ** 2)
    mask = np.clip(1 - k * np.clip(d - 0.55, 0, 1.4), 0.55, 1.0)
    arr = np.asarray(img).astype(np.float32) * mask[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t)
    return Image.fromarray(np.tile(arr, (1, w, 1)).astype(np.uint8))


def _halftone(draw, w, h, color, alpha=26, step=26, region=None):
    """dots grid, denser toward one corner (designed, not empty dot-grid wall)"""
    rng = np.random.default_rng(11)
    y0, y1, x0, x1 = region or (0, h, 0, w)
    for y in range(y0, y1, step):
        for x in range(x0, x1, step):
            p = (y - y0) / max(1, y1 - y0)
            if rng.random() < 0.70:
                r = max(1, int(step * 0.13 * (0.4 + p)))
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))


def paper_white(w, h, seed=3):
    img = Image.new("RGBA", (w, h), PAPER + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    _halftone(d, w, h, (30, 30, 34), alpha=16, step=30, region=(int(h * 0.78), h, 0, w))
    d.rectangle([0, h - 4, w, h], fill=VOLT + (255,))
    return _grain(_vignette(img, 0.10), 5)


def navy_scene(w, h, ghost=None):
    img = _gradient(w, h, NAVY_A, NAVY_B).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    _halftone(d, w, h, (210, 220, 255), alpha=14, step=34, region=(0, int(h * 0.25), 0, w))
    if ghost:
        size = int(h * 0.13)
        f = playfair(size, 900)
        tw = d.textbbox((0, 0), ghost, font=f)[2]
        while tw > w - 160 and size > 40:
            size -= 10
            f = playfair(size, 900)
            tw = d.textbbox((0, 0), ghost, font=f)[2]
        d.text(((w - tw) / 2, h * 0.055), ghost, font=f, fill=(255, 255, 255, 13))
    return _grain(_vignette(img, 0.26), 6)


def red_scene(w, h, ghost=None):
    img = _gradient(w, h, RED_A, RED_B).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    _halftone(d, w, h, (255, 120, 110), alpha=12, step=36, region=(int(h * 0.7), h, 0, w))
    if ghost:
        size = int(h * 0.12)
        f = playfair(size, 900)
        tw = d.textbbox((0, 0), ghost, font=f)[2]
        while tw > w - 160 and size > 40:
            size -= 10
            f = playfair(size, 900)
            tw = d.textbbox((0, 0), ghost, font=f)[2]
        d.text(((w - tw) / 2, h * 0.07), ghost, font=f, fill=(255, 190, 180, 14))
    return _grain(_vignette(img, 0.30), 6)


def green_scene(w, h):
    img = _gradient(w, h, GREEN_A, GREEN_B).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    _halftone(d, w, h, (235, 255, 160), alpha=16, step=30, region=(0, h, 0, int(w * 0.3)))
    return _grain(_vignette(img, 0.24), 6)


def black_halftone(w, h, quote=None):
    img = Image.new("RGBA", (w, h), (8, 8, 10, 255))
    d = ImageDraw.Draw(img, "RGBA")
    _halftone(d, w, h, (70, 70, 78), alpha=18, step=26, region=(0, h, 0, w))
    if quote:
        f = playfair(int(h * 0.075), 700)
        tw = d.textbbox((0, 0), quote, font=f)[2]
        d.text(((w - tw) / 2, h * 0.30), quote, font=f, fill=(240, 240, 235, 40))
    return _grain(_vignette(img, 0.34), 6)


# ---------------- stickers (semantic, R3) ----------------
def volt_pill(base, center, text, fnt, rot=-8, pad=(26, 12), fill=VOLT, tc=INK):
    """rotated accent pill (Congrats-style marker stroke)"""
    tmp = Image.new("RGBA", (int(base.width * 0.9), int(base.height * 0.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = tw + pad[0] * 2, th + pad[1] * 2
    tmp = tmp.crop((0, 0, pw, ph))
    d = ImageDraw.Draw(tmp)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=max(4, ph // 4), fill=fill + (235,))
    d.text((pad[0] - bb[0], pad[1] - bb[1]), text, font=fnt, fill=tc + (255,))
    tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC)
    cx, cy = center
    base.alpha_composite(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)))
    return tmp.size


def pixel_word(base, pos, text, fnt, color=INK, chunk=3):
    """chunky pixel/bitmap display word (target grammar DIFF2): render small, upscale nearest"""
    d = ImageDraw.Draw(base)
    bb = d.textbbox((0, 0), text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tmp = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tmp)
    dt.text((2 - bb[0], 2 - bb[1]), text, font=fnt, fill=color + (255,))
    small = tmp.resize((max(1, (tw + 4) // chunk), max(1, (th + 4) // chunk)), Image.BILINEAR)
    big = small.resize(((tw + 4), (th + 4)), Image.NEAREST)
    base.alpha_composite(big, (int(pos[0] - tw / 2), int(pos[1] - th / 2)))
    return (tw, th)


def mini_panel(base, box, canvas_kind, draw_fn=None):
    """2x2 collage mini-panel (target grammar DIFF1): self-designed sub-canvas"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if canvas_kind == "paper":
        sub = R_paper(w, h)
    elif canvas_kind == "navy":
        sub = R_navy(w, h)
    elif canvas_kind == "red":
        sub = R_red(w, h)
    else:
        sub = R_green(w, h)
    if draw_fn:
        draw_fn(sub, w, h)
    base.alpha_composite(sub, (x0, y0))
    d = ImageDraw.Draw(base, "RGBA")
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=(255, 255, 255, 60), width=2)


def R_paper(w, h):
    return paper_white(w, h)


def R_navy(w, h):
    return navy_scene(w, h)


def R_red(w, h):
    return red_scene(w, h)


def R_green(w, h):
    return green_scene(w, h)


def highlight_pill(base, box, fill=VOLT, alpha=210, radius=14):
    """volt highlighter BEHIND keyword (CV7: pill behind keyword only)"""
    d = ImageDraw.Draw(base, "RGBA")
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill + (alpha,))


def bracket_corners(base, box, color=INK, w=5, arm=34):
    d = ImageDraw.Draw(base, "RGBA")
    x0, y0, x1, y1 = box
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([cx, cy, cx + dx * arm, cy], fill=color + (255,), width=w)
        d.line([cx, cy, cx, cy + dy * arm], fill=color + (255,), width=w)


def pixel_dots(base, n, box, seed=5, color=VOLT, size=10):
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(base, "RGBA")
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = int(rng.uniform(x0, x1)); y = int(rng.uniform(y0, y1))
        s = int(rng.uniform(size * 0.5, size * 1.3))
        a = int(rng.uniform(120, 235))
        d.rectangle([x, y, x + s, y + s], fill=color + (a,))


def heart_glyph(base, center, size, color=(214, 40, 57), alpha=255):
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center; s = size
    d.ellipse([cx - s, cy - s * 0.9, cx, cy + s * 0.1], fill=color + (alpha,))
    d.ellipse([cx, cy - s * 0.9, cx + s, cy + s * 0.1], fill=color + (alpha,))
    d.polygon([(cx - s, cy - s * 0.25), (cx + s, cy - s * 0.25), (cx, cy + s)], fill=color + (alpha,))


def duck_avatar(base, center, size):
    """simple duck sticker (openmoji-inspired shape, drawn)"""
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center; s = size
    d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=(255, 214, 66, 255))
    d.ellipse([cx - s * 0.85, cy - s * 1.1, cx + s * 0.85, cy + s * 0.35], fill=(255, 226, 96, 255))
    d.ellipse([cx - s * 0.45, cy - s * 0.75, cx - s * 0.2, cy - s * 0.5], fill=(30, 30, 34, 255))
    d.polygon([(cx + s * 0.6, cy - s * 0.5), (cx + s * 1.25, cy - s * 0.28), (cx + s * 0.6, cy - s * 0.15)], fill=(240, 138, 30, 255))


def app_icon(base, center, size, fill=(16, 16, 20), alpha=235, glyph="→", glyph_color=(240, 240, 240)):
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center; s = size
    d.rounded_rectangle([cx - s, cy - s, cx + s, cy + s], radius=int(s * 0.32), fill=fill + (alpha,))
    f = montserrat(int(s * 1.1), 800)
    bb = d.textbbox((0, 0), glyph, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), glyph, font=f, fill=glyph_color + (255,))


def red_arrow_icon(base, center, size):
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center; s = size
    d.line([cx - s * 0.7, cy - s * 0.7, cx + s * 0.5, cy + s * 0.5], fill=(214, 40, 57, 255), width=int(s * 0.28))
    d.polygon([(cx + s * 0.75, cy + s * 0.1), (cx + s * 0.75, cy + s * 0.75), (cx + s * 0.1, cy + s * 0.75)], fill=(214, 40, 57, 255))


def orb_glow(base, center, r, t=0.0, color=(150, 210, 60)):
    """breathing AI-brain orb: halo + core, breathe 1.03"""
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    cx, cy = center
    breathe = 1.0 + 0.10 * math.sin(t * 2 * math.pi * 1.6)
    R = r * breathe
    for i, (rr, aa) in enumerate([(R * 1.9, 40), (R * 1.45, 70), (R * 1.15, 110), (R, 200)]):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=color + (aa,))
    core = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(core)
    rng = np.random.default_rng(4)
    for _ in range(220):
        ang = rng.uniform(0, 2 * math.pi)
        rad = R * math.sqrt(rng.uniform(0, 1)) * 0.92
        x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
        s = rng.uniform(2, 7)
        dc.ellipse([x - s, y - s, x + s, y + s], fill=(220, 255, 140, int(rng.uniform(60, 190))))
    glow = Image.alpha_composite(glow, core)
    base.alpha_composite(glow)


def constellation(base, center, spokes=9, reach=200, progress=1.0, color=(235, 235, 240)):
    d = ImageDraw.Draw(base, "RGBA")
    # contrast-safe: light color invisible on paper -> pick ink automatically
    px = base.convert("RGB").getpixel((max(4, int(center[0] - reach)), int(center[1])))
    if sum(px[:3]) > 560:
        color = (26, 26, 30)
    cx, cy = center
    rng = np.random.default_rng(9)
    pts = []
    for i in range(spokes):
        ang = 2 * math.pi * i / spokes + rng.uniform(-0.12, 0.12)
        rr = reach * rng.uniform(0.62, 1.0)
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    n_vis = max(1, int(spokes * progress))
    for i, (x, y) in enumerate(pts[:n_vis]):
        d.line([cx, cy, x, y], fill=color + (225,), width=4)
        d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=color + (255,))
    d.rectangle([cx - 10, cy - 10, cx + 10, cy + 10], fill=VOLT + (255,))


def starburst(base, center, size, rot=0.0, color=(214, 40, 57)):
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center
    pts = []
    for i in range(16):
        ang = rot + 2 * math.pi * i / 16
        rr = size if i % 2 == 0 else size * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=color + (255,))


def polaroid(base, frame_img, center, w, rot=-4, shadow=True):
    """polaroid cascade element holding a REAL frame"""
    iw, ih = frame_img.size
    ph = int(w * 1.22)
    card = Image.new("RGBA", (w + 24, ph + 44), (252, 252, 250, 255))
    fr = frame_img.resize((w, ph))
    card.paste(fr, (12, 12))
    if shadow:
        sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        ds.rounded_rectangle([26, 26, card.width + 14, card.height + 14], radius=6, fill=(0, 0, 0, 90))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        base.alpha_composite(sh, (int(center[0] - card.width / 2 - 20), int(center[1] - card.height / 2 - 20)))
    card = card.rotate(rot, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(card, (int(center[0] - card.width / 2), int(center[1] - card.height / 2)))


def phone_card(base, center, w, h, fill=(16, 28, 70), border=(240, 240, 245, 60)):
    """phone-shaped navy card (target S02)"""
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=int(w * 0.16), fill=fill + (250,))
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=int(w * 0.16), outline=border, width=3)
    d.rounded_rectangle([cx - w * 0.16, cy - h / 2 + 10, cx + w * 0.16, cy - h / 2 + 22], radius=6, fill=(230, 230, 240, 120))
    # toggle pill UI
    d.rounded_rectangle([cx - w * 0.30, cy + h * 0.30, cx + w * 0.02, cy + h * 0.38], radius=24, fill=(90, 110, 190, 255))
    d.ellipse([cx + w * 0.02 - 18, cy + h * 0.30 - 4, cx + w * 0.02 + 18, cy + h * 0.38 + 4], fill=VOLT + (255,))


def listicle_bars(base, x, y0, items, fnt, active_idx=-1, bar_w=340, gap=64):
    """LB3 listicle: rhombus numbers + bars + active volt"""
    d = ImageDraw.Draw(base, "RGBA")
    y = y0
    for i, (num, word) in enumerate(items):
        act = i == active_idx
        col = VOLT if act else (70, 70, 76)
        d.polygon([(x, y - 16), (x + 16, y), (x, y + 16), (x - 16, y)], fill=col + (255,))
        f_num = mono(30, bold=True)
        d.text((x - 10 - d.textbbox((0, 0), num, font=f_num)[2] / 2 + 8, y - 19), num, font=f_num, fill=(20, 20, 24, 255))
        d.text((x + 34, y - 21), word, font=fnt, fill=(240, 240, 238, 255) if act else (150, 150, 156, 255))
        bw = int(bar_w * (0.55 + 0.45 * (i + 1) / len(items)))
        d.rounded_rectangle([x + 34, y + 12, x + 34 + bw, y + 20], radius=4, fill=col + (200,) if act else (70, 70, 76, 120))
        y += gap
    return y


def counter_odometer(base, center, value, label, f_big, f_small, prefix="$"):
    """LB4 counter with real stakes"""
    d = ImageDraw.Draw(base, "RGBA")
    cx, cy = center
    txt = f"{prefix}{value:,}"
    bb = d.textbbox((0, 0), txt, font=f_big)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f_big, fill=(20, 20, 24, 255))
    bb2 = d.textbbox((0, 0), label, font=f_small)
    d.text((cx - (bb2[2] - bb2[0]) / 2 - bb2[0], cy + 58), label, font=f_small, fill=(110, 110, 116, 255))


# ---------------- captions karaoke v2 (CV1/CV2 port of captions-themes) ----------------
SAFE = {"top": 300, "bottom": 480, "side": 130}  # reels-editor safe area @1080x1920


def draw_caption_line(base, words, t, center_y):
    """lower-third karaoke with dark plate (CV1: compact bold sans, white, normal tracking).
    Text ends at y<=1440 (safe area). Auto-fit: shrink font until line <= 800px; 1-3 words/line."""
    size = 64
    while True:
        f_up = montserrat(size, 900)
        f_ac = montserrat(int(size * 1.12), 900)
        d = ImageDraw.Draw(base, "RGBA")
        widths = []
        for wd in words:
            bb = d.textbbox((0, 0), wd["text"], font=f_up)
            widths.append(bb[2] - bb[0])
        gap = 16
        total = sum(widths) + gap * (len(words) - 1)
        if total <= 800 or size <= 40:
            break
        size -= 6
    line_start = words[0]["start"]; line_end = words[-1]["end"]
    span = max(0.001, line_end - line_start)
    tt = t if t <= line_end else line_start + ((t - line_start) % span)
    x = (base.width - total) / 2
    y_c = center_y
    x0 = x - 30; x1 = x + total + 30
    d.rounded_rectangle([x0, y_c - 78, x1, y_c + 34], radius=22, fill=(8, 8, 10, 168))
    for i, wd in enumerate(words):
        active = (wd["start"] - line_start <= tt - line_start < wd["end"] - line_start)
        spoken = tt - line_start >= wd["end"] - line_start
        if active:
            bb = d.textbbox((0, 0), wd["text"], font=f_ac)
            w_a = bb[2] - bb[0]
            ty = y_c - bb[3] / 2 - 20
            # pill spans the FULL glyph bbox + pad (no overhang), then word on top
            d.rounded_rectangle([x - 10, ty + bb[1] - 10, x + w_a + 10, ty + bb[3] + 12], radius=14, fill=VOLT + (235,))
            d.text((x, ty), wd["text"], font=f_ac, fill=(16, 16, 18, 255))
            x += w_a + gap
        else:
            col = (255, 255, 255, int(255 * 0.45)) if spoken else (255, 255, 255, 255)
            bb = d.textbbox((0, 0), wd["text"], font=f_up)
            d.text((x, y_c - bb[3] / 2 - 20), wd["text"], font=f_up, fill=col)
            x += widths[i] + gap
