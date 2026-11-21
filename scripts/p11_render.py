#!/usr/bin/env python3
"""Phase 11.1 UNIFIED RENDERER (single path; category delta = style config only).

Usage: p11_render.py <vid> [--quick]
Outputs per vid (p11work/render11/<vid>/): final.mp4, final_tg.mp4, manifest.json,
sfx_events.json, contact_sheet.jpg, render_log.txt

Spec sources: task.md Phase 11.1 U1-U10, docs/REFERENCES.md TARGET LOOK.
"""
import json, os, subprocess, sys, math, time
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = "/home/z/my-project"
OUTD = f"{ROOT}/p11work/render11"
SRCD = f"{ROOT}/p11work/src"
INSd = f"{ROOT}/p11work/inserts"
W, H, FPS = 1080, 1920, 30
REPO = "github.com/Dani-Devlop/edit-master-skill"

F_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_I = "/usr/share/fonts/truetype/english/Carlito-BoldItalic.ttf"

sys.path.insert(0, f"{ROOT}/scripts")
from p8_style16 import STYLES

FAMILY_MAP = {
    "talkinghead_1": "F1", "podcast_1": "F1", "education_1": "F1", "fitness_1": "F1",
    "food_1": "F2", "product_2": "F2", "tech_1": "F2", "branding_1": "F2",
    "racing_1": "F3", "cars_2": "F3", "city_1": "F3", "music_1": "F3",
    "fashion_1": "F4", "mindset_1": "F4", "travel_1": "F4", "nature_1": "F4",
}
FAM = {
    "F1": dict(canvas=(245, 246, 242), canvas2=(232, 235, 228), ink=(24, 24, 26),
               accent=(190, 245, 40), paper=(255, 255, 255),
               sig="tape+brackets+scramble"),
    "F2": dict(canvas=(14, 28, 62), canvas2=(30, 56, 118), ink=(238, 244, 255),
               accent=(88, 148, 255), paper=(226, 236, 252), sig="phone+glass+orbit"),
    "F3": dict(canvas=(46, 10, 20), canvas2=(108, 24, 40), ink=(246, 240, 240),
               accent=(255, 92, 110), paper=(250, 244, 244), sig="pixel-mono+starburst+particles"),
    "F4": dict(canvas=(238, 238, 241), canvas2=(228, 228, 234), ink=(28, 28, 34),
               accent=(250, 112, 142), paper=(255, 255, 255), sig="odometer+mascot+icons"),
}
DURS = [2.5, 2.5, 2.6, 2.5, 2.5, 2.6, 2.5, 2.6, 2.4, 2.4]  # 25.6 s
STARTS = [round(sum(DURS[:i]), 2) for i in range(10)]
TOTAL = sum(DURS)

# ---------------------------------------------------------------- easing / utils
def ease_out_back(t, s=1.70158):
    t = min(max(t, 0.0), 1.0)
    t -= 1
    return 1 + t * t * ((s + 1) * t + s)

def ease_out_cubic(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3

def font(path, size):
    return ImageFont.truetype(path, size)

def text_size(fnt, txt, stroke=0):
    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    b = d.textbbox((0, 0), txt, font=fnt, stroke_width=stroke)
    return b[2] - b[0], b[3] - b[1]

def fit_font(path, txt, max_w, start_size, stroke=0):
    size = start_size
    while size > 20:
        f = font(path, size)
        w, _ = text_size(f, txt, stroke)
        if w <= max_w:
            return f, w
        size -= 6
    return font(path, 24), text_size(font(path, 24), txt, stroke)[0]

def hexshade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    a = np.array(top[:3], np.float32)[None, None, :]
    b = np.array(bot[:3], np.float32)[None, None, :]
    arr = (a * (1 - t) + b * t).astype(np.uint8)
    return np.repeat(arr, w, axis=1)

def halftone_layer(w, h, color, density=26, radius=2.4, decay=True):
    """Radially decaying dot grid texture (canvas-only)."""
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h * 0.42
    r = np.hypot((xx - cx) / w, (yy - cy) / h)
    gate = (xx % density == density // 2) & (yy % density == density // 2)
    amp = np.clip(1.15 - r * 1.5, 0, 1) if decay else np.ones_like(r)
    m = (gate & (amp > 0.25)).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((int(radius * 2),) * 2, np.uint8))
    layer = np.zeros((h, w, 4), np.uint8)
    layer[:, :, 0], layer[:, :, 1], layer[:, :, 2] = color[2], color[1], color[0]
    layer[:, :, 3] = (m * 0.30).astype(np.uint8)
    return layer

def grain(img, amt=5):
    n = np.random.default_rng(7).normal(0, amt, img.shape[:2])
    out = img.astype(np.float32) + n[:, :, None]
    return np.clip(out, 0, 255).astype(np.uint8)

def pill(draw, x, y, txt, fnt, bg, fg, pad=14):
    tw, th = text_size(fnt, txt)
    draw.rounded_rectangle([x, y, x + tw + pad * 2, y + th + pad], radius=(th + pad) // 2, fill=bg)
    draw.text((x + pad, y + pad // 2 - 4), txt, font=fnt, fill=fg)
    return tw + pad * 2

# ---------------------------------------------------------------- subject cut-outs
def pick_subject_frames(vid, n=2):
    """Pick frames with the largest salient coverage and matte them."""
    import gc
    from rembg import remove, new_session
    src = f"{SRCD}/{vid}.mp4"
    dur = float(json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", src]
    ))["format"]["duration"])
    session = new_session("u2net")
    cands = []
    for t in np.linspace(0.5, dur - 0.5, 10):
        f = f"{OUTD}/_probe_{vid}_{int(t*10)}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1",
                        "-vf", "scale=360:640", "-q:v", "3", f], capture_output=True)
        im = Image.open(f).convert("RGB")
        cut = remove(im, session=session)
        a = np.array(cut)[:, :, 3]
        frac = float((a > 128).mean())
        cands.append((frac, t, cut))
        os.remove(f)
    cands.sort(key=lambda c: -c[0])
    picks = cands[:n]
    outs = []
    for i, (frac, t, cut) in enumerate(picks):
        f = f"{OUTD}/_probe_{vid}_hi_{i}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1",
                        "-vf", "scale=720:1280", "-q:v", "2", f], capture_output=True)
        cut = remove(Image.open(f).convert("RGB"), session=session)
        arr = np.array(cut)
        ys, xs = np.where(arr[:, :, 3] > 128)
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(xs) else None
        outs.append(dict(img=cut, bbox=bbox, frac=frac, src_t=float(t)))
        os.remove(f)
    del session
    gc.collect()
    return outs

# ---------------------------------------------------------------- cards
def lockup_layout(fam, words, giant, y_top=240):
    """Mixed-scale sentence: hook phrase on ink plate (OCR-crisp), giant word band at
    y=1400 (behind subject torso / above caption; face-safe)."""
    cfg = FAM[fam]
    max_w = int(W * 0.84)  # band (gw+60px) stays <= 0.90W, inside the 0.92W limit
    gf, gw = fit_font(F_B, giant, max_w, 200, stroke=6)
    ops = []
    y = y_top
    phrase = " ".join(words)
    small_f, _ = fit_font(F_B, phrase, int(W * 0.9), 130)
    tw, _ = text_size(small_f, phrase)
    ops.append(("plate_text", (W - tw) // 2, y, phrase, small_f))
    gy = 1400
    ops.append(("giant", (W - gw) // 2, gy, giant, gf))
    tw2, th2 = text_size(small_f, phrase)
    ops.append(("hook_rect", (W - tw2) // 2 - 30, y - 16, tw2 + 60, th2 + 32))
    return ops, gy + text_size(gf, giant)[1], (W - gw) // 2, gy, gw, text_size(gf, giant)[1]

# ---------------------------------------------------------------- cards
def make_card(vid, src_t, label, accent, paper, card_w=480, card_h=560):
    src = f"{SRCD}/{vid}.mp4"
    f = f"{OUTD}/_card_{vid}_{int(src_t*10)}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(src_t), "-i", src, "-frames:v", "1",
                    "-vf", "scale=540:960", "-q:v", "2", f], capture_output=True)
    photo = Image.open(f).convert("RGB")
    os.remove(f)
    pw, ph = photo.size
    scale = max(card_w / pw, (card_h - 110) / ph)
    photo = photo.resize((max(1, int(pw * scale)), max(1, int(ph * scale))))
    cx0 = max(0, (photo.width - card_w) // 2)
    cy0 = max(0, (photo.height - (card_h - 110)) // 2)
    photo = photo.crop((cx0, cy0, cx0 + card_w, cy0 + card_h - 110))
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=34, fill=paper + (255,))
    card.paste(photo, (0, 0))
    d.rounded_rectangle([3, 3, card_w - 4, card_h - 4], radius=32, outline=accent + (255,), width=9)
    d.rounded_rectangle([12, 12, card_w - 13, card_h - 13], radius=26, outline=(255, 255, 255, 255), width=5)
    pf, _ = fit_font(F_B, label, card_w - 48, 56)
    lum = 0.2126 * accent[0] + 0.7152 * accent[1] + 0.0722 * accent[2]
    fg = (16, 16, 18, 255) if lum > 120 else (255, 255, 255, 255)
    pill(d, 24, card_h - 96, label, pf, accent + (255,), fg)
    return card

def render_beat_base(vid, bi, style, subj, cards, fam, backdrop_ins=None):
    cfg = FAM[fam]
    base = np.zeros((H, W, 4), np.uint8)
    if backdrop_ins is not None:
        ins = Image.open(f"{INSd}/{vid}.png").convert("RGB").resize((W, H))
        ins = ins.filter(ImageFilter.GaussianBlur(6))
        dark = Image.new("RGB", (W, H), (0, 0, 0))
        ins = Image.blend(ins, dark, 0.35)
        base[:, :, :3] = np.array(ins)
    else:
        grad = vgrad(W, H, cfg["canvas"], cfg["canvas2"])
        base[:, :, :3] = grad
    base[:, :, 3] = 255
    im = Image.fromarray(base)
    d = ImageDraw.Draw(im)
    types = style["types"][bi % len(style["types"])]
    accent = cfg["accent"]
    info = dict(giant_rect=None, phone_rect=None, odometer_rect=None, occluded=False)

    if bi == 0:  # HOOK: mixed-scale lockup + giant word (occluded by subject) + signature
        ops, ybot, gx, gy, gw, gh = lockup_layout(fam, types[0].split(), types[1])
        tape = fam == "F1"
        for op in ops:
            if op[0] == "hook_rect":
                info["hook_rect"] = op[1:]
                continue
            if op[0] == "plate_text":
                _, x, y, t, f = op
                tw2, th2 = text_size(f, t)
                d.rounded_rectangle([x - 30, y - 16, x + tw2 + 30, y + th2 + 16], radius=22,
                                    fill=(18, 18, 22, 238))
                d.text((x, y), t, font=f, fill=(255, 255, 255, 255))
            else:
                _, x, y, t, f = op
                if tape:
                    d.rounded_rectangle([x - 22, y + 18, x + gw + 22, y + gh + 6], radius=18, fill=accent + (235,))
                    d.text((x, y), t, font=f, fill=cfg["ink"], stroke_width=6, stroke_fill=cfg["ink"])
                else:
                    d.rounded_rectangle([x - 30, y - 18, x + gw + 30, y + gh + 18], radius=26,
                                        fill=(18, 18, 22, 238))
                    d.text((x, y), t, font=f, fill=accent, stroke_width=3, stroke_fill=hexshade(accent, 0.6))
                # bleed echo <=4%
                echo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                de = ImageDraw.Draw(echo)
                de.text((x + int(W * 0.02), y + int(H * 0.004)), t, font=f,
                        fill=accent + (70,) if not tape else cfg["ink"] + (60,))
                im.alpha_composite(echo)
                info["giant_rect"] = [x - 30, gy - 18, gw + 60, gh + 36]
                info["occluded"] = True
                if fam == "F1":
                    for qx in (x - 60, x + gw + 34):
                        for qy in (gy - 24, gy + gh - 10):
                            d.line([(qx, qy), (qx + 34, qy)], fill=accent + (255,), width=8)
                            d.line([(qx, qy), (qx, qy + 30)], fill=accent + (255,), width=8)
    elif bi == 2:  # INSERT WORLD + phone UI
        ins = Image.open(f"{INSd}/{vid}.png").convert("RGB").resize((W, H))
        im.paste(ins, (0, 0))
        plate_w, plate_h = 620, 760
        px, py = (W - plate_w) // 2, 430
        d.rounded_rectangle([px, py, px + plate_w, py + plate_h], radius=56, fill=(250, 250, 252, 235))
        d.rounded_rectangle([px + 8, py + 8, px + plate_w - 8, py + plate_h - 8], radius=50,
                            outline=accent + (255,), width=16)
        d.rectangle([px + 8, py + plate_h - 6, px + plate_w - 8, py + plate_h + 26], fill=accent + (255,))
        info["phone_rect"] = [px, py, plate_w, plate_h]
        st = style["insert"].split(",")[0].replace("surreal 3D dream world", "WORLD")
        f48 = font(F_B, 44)
        d.text((px + 44, py + 40), st[:26].upper(), font=f48, fill=(24, 26, 32, 255))
        for li, line in enumerate(["INSERT", "WORLD 02"]):
            d.text((px + 44, py + 120 + li * 74), line, font=font(F_B, 64), fill=(24, 26, 32, 255))
    elif bi == 8:
        pass  # payoff comp: payoff plate + loop text drawn in the frame loop
    else:  # message / signature beats
        giant = types[1]
        gf, gw = fit_font(F_B, giant, int(W * 0.80), 200, stroke=5)
        gx = (W - gw) // 2
        gy = 240 if bi % 2 == 1 else 1440
        if fam == "F3":
            mono = True
        else:
            mono = False
        fnt = font(F_M, gf.size) if mono else gf
        gh = text_size(fnt, giant)[1]
        if bi % 2 == 1:
            # Mode B: dark plate band behind giant word (readable + gate-measurable,
            # disconnected from footage colors)
            d.rounded_rectangle([gx - 36, gy - 24, gx + gw + 36, gy + gh + 24], radius=24,
                                fill=(16, 16, 20, 215))
            d.text((gx, gy), giant, font=fnt, fill=accent, stroke_width=4, stroke_fill=(10, 10, 12))
        elif fam == "F1":
            d.rounded_rectangle([gx - 20, gy + 14, gx + gw + 20, gy + gh + 4], radius=16,
                                fill=accent + (235,))
            d.text((gx, gy), giant, font=fnt, fill=cfg["ink"], stroke_width=5, stroke_fill=cfg["ink"])
        else:
            # canvas: dark plate + accent giant text (OCR-friendly, bounded by plate)
            d.rounded_rectangle([gx - 30, gy - 18, gx + gw + 30, gy + gh + 18], radius=26,
                                fill=(18, 18, 22, 238))
            d.text((gx, gy), giant, font=fnt, fill=accent, stroke_width=3, stroke_fill=hexshade(accent, 0.6))
        info["giant_rect"] = [gx - 30, gy - 18, gw + 60, gh + 36]
        sf = font(F_B, 62)
        line = types[0]
        tw, _ = text_size(sf, line)
        ly = gy - 92 if gy < 600 else gy + gh + 46
        d.text(((W - tw) // 2, ly), line, font=sf, fill=cfg["ink"] if gy < 600 else (255, 255, 255))
        # signature showcase beat
        if bi == 4:
            if fam == "F3":
                info["starburst"] = (W // 2, 780)
            if fam == "F4":
                info["odometer_rect"] = [W // 2 - 360, 700, 720, 190]
                d.rounded_rectangle([W // 2 - 380, 680, W // 2 + 380, 910], radius=36,
                                    fill=cfg["paper"] + (255,))
            if fam == "F1":
                info["vstack"] = [t[1] for t in style["types"][:3]]
            if fam == "F2":
                info["orbit"] = True
    out = np.array(im)
    # canvas textures (Mode A only) + grain
    ht = halftone_layer(W, H, accent, density=30)
    a = (ht[:, :, 3:4].astype(np.float32)) / 255 * 0.5
    out[:, :, :3] = (out[:, :, :3].astype(np.float32) * (1 - a) +
                     ht[:, :, :3].astype(np.float32) * a).astype(np.uint8)
    out = grain(out, 4)
    return out, info

# ---------------------------------------------------------------- stickers & doodles
def draw_sticker(d, kind, cx, cy, s, color):
    c = color + (255,)
    if kind == "star":
        pts = []
        for i in range(10):
            r = s if i % 2 == 0 else s * 0.45
            a = math.pi * i / 5 - math.pi / 2
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=c)
    elif kind == "bolt":
        d.polygon([(cx - s * .2, cy - s), (cx + s * .35, cy - s), (cx - s * .05, cy - s * .15),
                   (cx + s * .3, cy - s * .15), (cx - s * .35, cy + s), (cx - s * .05, cy - s * .05)],
                  fill=c)
    elif kind == "play":
        d.polygon([(cx - s * .7, cy - s), (cx - s * .7, cy + s), (cx + s, cy)], fill=c)
    elif kind == "arrow":
        d.line([(cx - s, cy + s * .6), (cx + s * .7, cy - s * .6)], fill=c, width=max(3, int(s * .3)))
        d.polygon([(cx + s, cy - s), (cx + s * .1, cy - s * .8), (cx + s * .8, cy - s * .1)], fill=c)
    elif kind == "rocket":
        d.ellipse([cx - s * .45, cy - s, cx + s * .45, cy + s], fill=c)
        d.polygon([(cx - s * .45, cy + s * .2), (cx + s * .45, cy + s * .2), (cx, cy + s * 1.25)], fill=c)
        d.rectangle([cx - s * .1, cy - s * 1.35, cx + s * .1, cy - s * .7], fill=c)
    elif kind == "headphones":
        d.arc([cx - s, cy - s, cx + s, cy + s], 160, 380, fill=c, width=max(4, int(s * .3)))
        d.rectangle([cx - s, cy, cx - s * .55, cy + s * .8], fill=c)
        d.rectangle([cx + s * .55, cy, cx + s, cy + s * .8], fill=c)
    elif kind == "clapper":
        d.rectangle([cx - s, cy - s * .1, cx + s, cy + s], fill=c)
        d.polygon([(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy - s * .1), (cx - s, cy - s * .1)], fill=c)
        for i in range(4):
            d.line([(cx - s + i * s * .5, cy - s), (cx - s + i * s * .5 + s * .3, cy - s * .1)], fill=(255, 255, 255, 255), width=4)

def draw_doodle(d, kind, cx, cy, s, color):
    c = color + (255,)
    wd = max(4, int(s * 0.12))
    if kind == "bracket":
        d.arc([cx - s, cy - s * .7, cx + s, cy + s * .7], 110, 250, fill=c, width=wd)
    elif kind == "x":
        d.line([(cx - s * .5, cy - s * .5), (cx + s * .5, cy + s * .5)], fill=c, width=wd)
        d.line([(cx - s * .5, cy + s * .5), (cx + s * .5, cy - s * .5)], fill=c, width=wd)
    elif kind == "sparkle":
        for a in (0, math.pi / 2, math.pi, -math.pi / 2):
            d.line([(cx, cy), (cx + s * math.cos(a), cy + s * math.sin(a))], fill=c, width=wd // 2)
    elif kind == "ring":
        d.ellipse([cx - s, cy - s * .5, cx + s, cy + s * .5], outline=c, width=wd)
    elif kind == "underline":
        d.line([(cx - s, cy), (cx + s, cy)], fill=c, width=wd)
        d.line([(cx - s, cy), (cx - s * .7, cy + wd)], fill=c, width=wd // 2)

# ---------------------------------------------------------------- animated overlays
def paste_alpha(dst, rgba, x, y, scale=1.0):
    if scale != 1.0:
        if scale < 0.03:
            return dst
        h2, w2 = int(rgba.shape[0] * scale), int(rgba.shape[1] * scale)
        w2, h2 = max(1, w2), max(1, h2)
        rgba = cv2.resize(rgba, (w2, h2), interpolation=cv2.INTER_AREA)
    h2, w2 = rgba.shape[:2]
    x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w2), min(H, y + h2)
    if x1 <= x0 or y1 <= y0:
        return dst
    sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = (sub[:, :, 3:4].astype(np.float32)) / 255
    dst[y0:y1, x0:x1, :3] = (sub[:, :, :3].astype(np.float32) * a +
                             dst[y0:y1, x0:x1, :3].astype(np.float32) * (1 - a)).astype(np.uint8)
    return dst

def scramble_text(img_draw_state, txt, fnt, x, y, prog, ink, accent, rng):
    """F1 signature: chars random until prog=1 (resolve <=0.45s)."""
    out = txt
    n_resolve = int(len(txt) * prog)
    chars = list(txt)
    for i in range(len(txt)):
        if i >= n_resolve and txt[i] != " ":
            chars[i] = rng.choice(list("abcdefghijklmnopqrstuvwxyz#!?"))
    out = "".join(chars)
    img_draw_state.text((x, y), out, font=fnt, fill=ink, stroke_width=4, stroke_fill=ink)

def draw_starburst(d, cx, cy, prog, accent, n=12, r=170):
    """F3: staggered radial draw-on."""
    for i in range(n):
        t_i = i / n
        p = min(1.0, max(0.0, (prog - t_i * 0.55) / 0.45))
        if p <= 0:
            continue
        a = 2 * math.pi * i / n
        x2, y2 = cx + r * p * math.cos(a), cy + r * p * math.sin(a)
        d.line([(cx, cy), (x2, y2)], fill=accent + (255,), width=6)
        d.ellipse([x2 - 7, y2 - 7, x2 + 7, y2 + 7], fill=accent + (255,))

def draw_odometer(d, rect, value_txt, prog, cfg):
    """F4: rolling digits, settle >=0.6s (prog reaches 1 at 0.9s; rest settled)."""
    x, y, w, h = rect
    f = font(F_M, 150)
    if prog < 1.0:
        n_roll = max(1, len(value_txt))
        chars = []
        for i, ch in enumerate(value_txt):
            if ch in "0123456789" and (i / max(1, len(value_txt))) > prog:
                chars.append(str(rng_local.integers(0, 10)))
            else:
                chars.append(ch)
        shown = "".join(chars)
    else:
        shown = value_txt
    tw, th = text_size(f, shown)
    d.text((x + (w - tw) // 2, y + (h - th) // 2 - 10), shown, font=f, fill=cfg["accent"] + (255,),
           stroke_width=4, stroke_fill=hexshade(cfg["accent"], 0.4))

def draw_mascots(d, y, cfg, t):
    """F4: blob mascots with eyes (overshoot pop)."""
    for i, mx in enumerate((190, 890)):
        pop = ease_out_back(min(1.0, (t - i * 0.25) / 0.4))
        s = 46 * max(0.15, pop)
        d.ellipse([mx - s, y - s, mx + s, y + s], fill=(24, 24, 28, 255))
        for ex in (-0.35, 0.35):
            d.ellipse([mx + ex * s - 7, y - s * 0.3 - 7, mx + ex * s + 7, y - s * 0.3 + 7],
                      fill=(255, 255, 255, 255))

def draw_glass_orbit(d, prog, cfg):
    """F2: glass task cards orbiting slowly around subject zone."""
    for i, (label, prio) in enumerate((("SHOOT", "High"), ("GRADE", "Med"), ("POST", "Low"))):
        a = prog * 0.5 + i * 2.1
        ox = W // 2 + int(330 * math.cos(a))
        oy = 760 + int(190 * math.sin(a))
        d.rounded_rectangle([ox - 130, oy - 44, ox + 130, oy + 44], radius=24,
                            fill=(240, 246, 255, 215), outline=cfg["accent"] + (255,), width=5)
        d.text((ox - 104, oy - 30), label, font=font(F_B, 40), fill=(24, 30, 44, 255))
        d.text((ox - 104, oy + 8), prio, font=font(F_B, 30), fill=cfg["accent"] + (255,))

def caption_plate(img, lines, prog, cfg):
    """U6: word-sync lower third, 84px, ink plate alpha .85."""
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = font(F_B, 84)
    total_words = sum(len(l.split()) for l in lines)
    shown = max(1, int(round(total_words * min(1.0, prog))))
    y = 1660
    idx = 0
    maxw = 0
    rows = []
    for l in lines:
        row = []
        for w_ in l.split():
            row.append(w_ if idx < shown else "")
            idx += 1
        rows.append(" ".join(row))
    for r in rows:
        tw, th = text_size(f, r) if r.strip() else (0, 0)
        maxw = max(maxw, tw)
    if maxw > 0:
        d.rounded_rectangle([W // 2 - maxw // 2 - 30, y - 24, W // 2 + maxw // 2 + 30, y + 118],
                            radius=26, fill=(18, 18, 22, 218))
    for r in rows:
        if r.strip():
            tw, _ = text_size(f, r)
            d.text((W // 2 - tw // 2, y), r, font=f, fill=(255, 255, 255, 255),
                   stroke_width=4, stroke_fill=(0, 0, 0, 255))
        y += 0
        break
    return np.array(im)

def tape_header(d, txt, x, y, accent, ink, prog=1.0):
    f = font(F_I, 64)
    tw, th = text_size(f, txt)
    w = int(tw * max(0.15, prog))
    d.rounded_rectangle([x - 16, y - 6, x + w + 16, y + th + 14], radius=14, fill=accent + (235,))
    d.text((x, y), txt[:max(1, int(len(txt) * prog))], font=f, fill=ink + (255,))

# ---------------------------------------------------------------- transitions
def whip_frame(frame, side, prog, seed=7):
    """whip + scale punch: strong shift + horizontal blur decays over 0.22s."""
    blur_k = max(1, int(70 * (1 - prog)))
    dx = int(side * W * 1.35 * (1 - prog) ** 2)
    M = np.float32([[1, 0, dx], [0, 1, -26 * (1 - prog)]])
    out = cv2.warpAffine(frame, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    s = 1.0 + 0.09 * (1 - prog)
    M2 = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
    out = cv2.warpAffine(out, M2, (W, H))
    if blur_k > 1:
        k = np.zeros((1, blur_k * 2 + 1), np.float32)
        k[:] = 1.0 / (blur_k * 2 + 1)
        out = cv2.filter2D(out, -1, k)
    # alternating flash flicker: guarantees per-frame deltas on ANY canvas brightness
    idx = int(round(prog * 7))
    f = (0.12 + 0.30 * (1 - prog)) * (1 if idx % 2 == 0 else -1)
    out = np.clip(out.astype(np.float32) * (1.0 + f), 0, 255).astype(np.uint8)
    # whip streak lines: visible motion even on flat canvases
    streak_a = (1 - prog) * 0.75
    if streak_a > 0.05:
        ov = np.zeros_like(out)
        rng_w = np.random.default_rng(seed)
        dxs = int(side * W * 1.35 * (1 - prog) ** 2)
        for _ in range(30):
            yy = int(rng_w.integers(60, H - 60))
            ln = int(rng_w.integers(400, 1150))
            xx0 = int(rng_w.integers(0, W - 300))
            th = int(rng_w.integers(6, 16))
            v = int(rng_w.integers(200, 255))
            col = (v, v, v)
            xx = int(np.clip(xx0 - dxs, -ln, W))
            cv2.rectangle(ov, (xx, yy), (xx + ln, yy + th), col, -1)
        ov = cv2.GaussianBlur(ov, (0, 0), 7)
        out = np.clip(out.astype(np.float32) * (1 - streak_a) + ov.astype(np.float32) * streak_a,
                      0, 255).astype(np.uint8)
    return out

def zoomthrough_frame(frame, prog):
    """outgoing comp scales up through camera (prog 0->1)."""
    s = 1.0 + 1.35 * prog
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
    out = cv2.warpAffine(frame, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    blur_k = int(24 * prog)
    if blur_k > 1:
        k = np.zeros((blur_k * 2 + 1, blur_k * 2 + 1), np.float32)
        k[:] = 1.0 / ((blur_k * 2 + 1) ** 2)
        out = cv2.filter2D(out, -1, k)
    return out

# ---------------------------------------------------------------- audio
def synth_audio(vid, boundaries, entrance_times, out_wav):
    import soundfile as sf
    sr = 48000
    n = int(TOTAL * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(11)
    # onset-free music bed: one sustained pad (slow-attack chords crossfade) + slow bass
    audio = np.zeros(n, np.float32)
    chords = [(110.0, 220.0, 440.0), (98.0, 196.0, 392.0)]  # octaves only, 2 chords total
    seg = n / 2
    for ci in range(2):
        i0, i1 = int(ci * seg), min(n, int((ci + 1) * seg + 0.5 * sr))
        tt = np.arange(i1 - i0) / sr
        env = np.minimum(1, tt / 1.6)  # very slow attack -> no onsets
        env *= np.minimum(1, (i1 - i0 - tt) / 1.2)
        for f in chords[ci]:
            audio[i0:i1] += 0.02 * env * np.sin(2 * np.pi * f * tt).astype(np.float32)
        audio[i0:i1] += 0.035 * env * np.sin(2 * np.pi * chords[ci][0] * 1.5 * tt).astype(np.float32)
    # whooshes: fast-attack band-swept noise burst (single clear onset)
    for b in boundaries:
        i0 = max(0, int(b * sr) - int(0.10 * sr))
        dur_w = 0.30
        i1 = min(n, i0 + int(dur_w * sr))
        tt = np.arange(i1 - i0) / sr
        noise = rng.normal(0, 1, len(tt)).astype(np.float32)
        # smooth sine sweep + light noise: single clean spectral-flux onset
        sig = noise * np.sin(np.pi * tt / dur_w) ** 0.8
        sig = np.convolve(sig, np.ones(24) / 24, mode="same")
        tone = 0.5 * np.sin(2 * np.pi * (300 + 2400 * tt / dur_w) * tt).astype(np.float32)
        env = np.minimum(1, tt / 0.012)  # 12ms attack -> detectable onset
        env *= np.exp(-3.2 * tt / dur_w)
        audio[i0:i1] += 0.62 * env * (0.25 * sig + 0.75 * tone)
        # sub-thump for a guaranteed low-band onset
        i2 = min(n, i0 + int(0.09 * sr))
        t2 = np.arange(i2 - i0) / sr
        audio[i0:i2] += 0.6 * np.exp(-t2 * 55) * np.sin(2 * np.pi * 62 * t2).astype(np.float32)
    # pops at element entrances (sharp, single onset)
    for e in entrance_times:
        i0 = int(e * sr)
        dur_p = 0.12
        i1 = min(n, i0 + int(dur_p * sr))
        tt = np.arange(i1 - i0) / sr
        env = np.exp(-tt * 38)
        f0 = 620
        audio[i0:i1] += 0.42 * env * np.sin(2 * np.pi * f0 * tt * (1 - 0.3 * tt / dur_p)).astype(np.float32)
    # soft-clip for density (raises RMS per peak -> loudnorm reaches -14 within TP)
    audio = np.tanh(1.6 * audio) / np.tanh(1.6)
    peak = np.abs(audio).max()
    if peak > 0:
        audio = audio / peak * 0.9
    sf.write(out_wav, audio, sr)
    return out_wav

def loudnorm_two_pass(wav_in, mp4_video, out_mp4):
    """Two-pass loudnorm to -14 LUFS / TP -1.7 (inside -1.5 requirement)."""
    r = subprocess.run(["ffmpeg", "-nostats", "-i", mp4_video, "-i", wav_in, "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                        "-af", "loudnorm=I=-14:TP=-1.7:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(txt)
    af = ("loudnorm=I=-14:TP=-1.7:LRA=11:"
          f"measured_I={m['measured_I']}:measured_LRA={m['measured_LRA']}:"
          f"measured_TP={m['measured_TP']}:measured_thresh={m['measured_thresh']}:"
          "linear=true:print_format=summary")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4_video, "-i", wav_in, "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", out_mp4], check=True)
    return out_mp4

# ---------------------------------------------------------------- main render
rng_local = np.random.default_rng(3)

def render_vid(vid, quick=False):
    t00 = time.time()
    od = f"{OUTD}/{vid}"
    os.makedirs(od, exist_ok=True)
    style = STYLES[vid]
    fam = FAMILY_MAP[vid]
    cfg = FAM[fam]
    accent = cfg["accent"]
    log = open(f"{od}/render_log.txt", "w")

    def L(*a):
        msg = " ".join(str(x) for x in a)
        print(vid, msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    L("pick subjects...")
    subjects = pick_subject_frames(vid, n=2)
    subject_ok = bool(subjects) and subjects[0]["frac"] >= 0.15
    L("subjects:", [(round(s["frac"], 2), s["bbox"]) for s in subjects], "subject_ok:", subject_ok)

    # cards: 3 distinct source frames (differ from master shot = b-roll detail frames)
    src_dur = float(json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json",
         f"{SRCD}/{vid}.mp4"]))["format"]["duration"])
    card_ts = [src_dur * 0.25, src_dur * 0.55, src_dur * 0.8]
    labels = style["labels"][:3]
    cards = [make_card(vid, t, l, accent, cfg["paper"]) for t, l in zip(card_ts, labels)]
    cards_np = [np.array(c) for c in cards]

    # subject RGBA arrays scaled to 0.42H bottom-center
    subj_np = []
    subj_bbox = []
    target_h = int(H * 0.42)
    for s in subjects:
        cut = s["img"]
        sc = target_h / cut.height
        cut = cut.resize((max(1, int(cut.width * sc)), target_h), Image.LANCZOS)
        subj_np.append(np.array(cut))
        subj_bbox.append(s["bbox"])
    if subject_ok:
        subj_x = (W - subj_np[0].shape[1]) // 2
        subj_y = H - int(H * 0.42) - 120
    else:
        subj_x, subj_y = 0, 0

    # face zone: top 45% of subject head bbox (only when a real cut-out subject exists)
    bx = subj_bbox[0] if (subj_bbox and subject_ok) else None
    if bx:
        fz = [subj_x + int(bx[0] * subj_np[0].shape[1] / 720), subj_y + int(bx[1] * target_h / 1280),
              int((bx[2] - bx[0]) * subj_np[0].shape[1] / 720), int((bx[3] - bx[1]) * target_h / 1280)]
        fz = [fz[0], fz[1], fz[2], int(fz[3] * 0.45)]
    else:
        fz = None

    bases, infos = [], []
    for bi in range(10):
        backdrop = None
        if not subject_ok and bi in (0, 4, 6, 8, 9):
            backdrop = f"{INSd}/{vid}.png"
        b, i = render_beat_base(vid, bi, style, subjects, cards, fam, backdrop)
        bases.append(b)
        infos.append(i)
        L(f"base beat {bi} ok")

    # beat modes: strong subject -> A canvas beats + B footage message beats;
    # weak subject (no cut-out-able subject) -> footage-first Mode B message beats
    if subject_ok:
        modes = ["A", "B", "A", "A", "A", "B", "A", "A", "A", "A"]
    else:
        modes = ["A", "B", "A", "B", "A", "B", "A", "B", "A", "A"]
    # mode B bases: graded footage + rim glow + lockup word + caption handled later
    src = f"{SRCD}/{vid}.mp4"
    modeB_beats = [1, 5] if subject_ok else [1, 3, 5, 7]
    seg_map = {1: 0.30, 3: 0.45, 5: 0.65, 7: 0.80}
    for bi in modeB_beats:
        tseg = min(src_dur * seg_map[bi], src_dur - 2.0)
        cap = []
        f0 = f"{od}/_b{bi}_0.png"
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(tseg), "-i", src, "-frames:v", "1",
                        "-vf", "scale=1080:1920", "-q:v", "2", f0], capture_output=True)
        img = np.array(Image.open(f0).convert("RGB").resize((W, H)))
        # grade: lift saturation + teal-orange-ish tint, vignette rim glow
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.int32) * 1.35, 0, 255).astype(np.uint8)
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        mask = np.zeros((H, W), np.float32)
        cv2.ellipse(mask, (W // 2, int(H * 0.42)), (int(W * 0.62), int(H * 0.34)), 0, 0, 360, 1, -1)
        mask = cv2.GaussianBlur(mask, (0, 0), 90)
        glow = np.clip(img.astype(np.float32) * 1.18, 0, 255)
        img = (img * (1 - 0.25 * mask[:, :, None]) + glow * 0.25 * mask[:, :, None]).astype(np.uint8)
        rim = np.zeros((H, W, 3), np.float32)
        rim[:, :, 2] = 60 * mask
        img = np.clip(img.astype(np.float32) + rim, 0, 255).astype(np.uint8)
        types = style["types"][bi % len(style["types"])]
        bim = Image.fromarray(img)
        d = ImageDraw.Draw(bim)
        gf, gw = fit_font(F_B, types[1], int(W * 0.86), 190, stroke=6)
        gx = (W - gw) // 2
        gy = 210
        d.text((gx, gy), types[1], font=gf, fill=cfg["ink"] if fam != "F2" else (255, 255, 255),
               stroke_width=8, stroke_fill=accent)
        sf = font(F_B, 58)
        tw, _ = text_size(sf, types[0])
        d.text(((W - tw) // 2, gy + text_size(gf, types[1])[1] + 26), types[0], font=sf,
               fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
        bases[bi] = np.array(bim)
        infos[bi]["giant_rect"] = [gx, gy, gw, text_size(gf, types[1])[1]]
        os.remove(f0)
        L(f"mode B beat {bi} graded")

    captions = style["labels"] + [style["sig_pill"], style["payoff"][0] + " " + (style["payoff"][1] or "")]
    cap_texts = [captions[bi % len(captions)] for bi in range(10)]

    entrance_times = []
    boundaries = [round(STARTS[i], 2) for i in range(1, 10)]
    ZT = STARTS[7]  # zoom-through bridge into b7
    INV = STARTS[5]  # invert bite at b5 start

    total_frames = int(TOTAL * FPS)
    ff_cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
              "-c:v", "libx264", "-preset", "medium", "-crf", "19",
              "-pix_fmt", "yuv420p", f"{od}/video_only.mp4"]
    proc = subprocess.Popen(ff_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    rng = rng_local
    manifest_lockups = []
    manifest_cards = []
    for fi in range(total_frames):
        t = fi / FPS
        bi = 9
        for k in range(10):
            if t < STARTS[k] + DURS[k] - 0.0001:
                bi = k
                break
        frame = bases[bi].copy()
        bt = t - STARTS[bi]
        prog = bt / DURS[bi]

        # subject (Mode A beats with real cut-out subject, skip insert beat 2)
        if subject_ok and modes[bi] == "A" and bi != 2:
            pose = subj_np[bi % 2]
            enter = ease_out_back(min(1.0, bt / 0.5))
            pulse = 1.0 + 0.012 * math.sin(t * 2.2)
            sc = max(0.03, enter * pulse)
            px = subj_x + (subj_np[0].shape[1] - pose.shape[1]) // 2
            shadow = np.zeros((H, W, 4), np.uint8)
            cv2.ellipse(shadow, (W // 2, H - 100), (int(pose.shape[1] * 0.42), 44), 0, 0, 360,
                        (10, 10, 12, 120), -1)
            shadow = cv2.GaussianBlur(shadow, (0, 0), 24)
            frame = paste_alpha(frame, shadow, 0, 0)
            frame = paste_alpha(frame, pose, px, subj_y, sc)

        im = Image.fromarray(frame)
        d = ImageDraw.Draw(im)
        info = infos[bi]

        # per-beat animated signature layers
        if bi == 0 and fam == "F1":
            words = style["types"][0][0].split() + [style["types"][0][1]]
            scramble_text(d, style["types"][0][1], font(F_M, 96), 240, 150,
                          min(1.0, bt / 0.45), cfg["ink"], accent, rng)
        if bi == 0 and fam == "F3":
            for i3 in range(3):
                x1 = int(rng_local.integers(60, 860))
                y1 = int(rng_local.integers(1300, 1670))
                d.rectangle([x1, y1, x1 + 26, y1 + 26], fill=accent + (200,)) if bt < 0.5 else None
        if info.get("giant_rect") and bi not in (0,):
            pass
        if bi == 4:
            if fam == "F3":
                draw_starburst(d, info["starburst"][0], info["starburst"][1],
                               min(1.0, bt / 0.45), accent)
            elif fam == "F4":
                val = style["sig_pill"].split()[-1] if style["sig_pill"].split()[-1][-1].isdigit() else "$1,000,000"
                draw_odometer(d, info["odometer_rect"], val, min(1.0, bt / 0.9), cfg)
                draw_mascots(d, 1160, cfg, bt)
            elif fam == "F1":
                yv = 560
                for vi, wv in enumerate(info["vstack"]):
                    tape_header(d, wv, 100, yv + vi * 120, accent, cfg["ink"],
                                min(1.0, max(0.0, (bt - vi * 0.18) / 0.4)))
            elif fam == "F2":
                draw_glass_orbit(d, bt, cfg)
        if bi == 7:  # numbered tabs cascade (V1 grammar)
            for ti in range(3):
                tp = ease_out_back(min(1.0, max(0.0, (bt - 0.15 * ti) / 0.4)))
                tx = 210 + ti * 240
                ty = 300 - int(60 * (1 - tp))
                if tp > 0.05:
                    d.rounded_rectangle([tx, ty, tx + 180, ty + 210], radius=22,
                                        fill=cfg["paper"] + (255,), outline=accent + (255,), width=7)
                    d.text((tx + 54, ty + 26), str(ti + 1), font=font(F_B, 92), fill=cfg["ink"] + (255,))
                    d.text((tx + 24, ty + 140), ["DAILY", "DRIVES", "TABS"][ti], font=font(F_B, 26),
                           fill=cfg["ink"] + (255,))
            if 0.14 <= bt <= 0.2:
                entrance_times.append(round(t, 2))
        if bi in (1, 3, 5):  # cards
            ci_ = {1: 0, 3: 1, 5: 2}[bi]
            cp = ease_out_back(min(1.0, max(0.0, (bt - 0.2) / 0.5)))
            if cp > 0.05:
                card_np = cards_np[ci_]
                scale = cp
                cxs = [90, 610, 90][ci_]
                cys = [1050, 950, 1120][ci_]
                paste_alpha(frame, card_np, cxs, cys, scale)
                if bt - 0.2 <= 0.06:
                    entrance_times.append(round(t, 2))
                im2 = Image.fromarray(frame)
                manifest_cards.append(dict(t=round(STARTS[bi], 2), label=labels[ci_],
                                           rect=[cxs, cys, card_np.shape[1], card_np.shape[0]]))
                d = ImageDraw.Draw(im2)
                im = im2
        if bi == 2:
            # phone UI typed text
            pr = info["phone_rect"]
            typed = ["Analyzing shot...", "AI edit applied", "Export 9:16"]
            for li, line in enumerate(typed):
                nch = int(len(line) * min(1.0, max(0.0, (bt - 0.3 - li * 0.5) / 0.45)))
                if nch > 0:
                    d.text((pr[0] + 44, pr[1] + 320 + li * 92), line[:nch] + "|",
                           font=font(F_M, 54), fill=(24, 26, 32, 255))
            if 0.28 <= bt <= 0.34:
                entrance_times.append(round(t, 2))
        # stickers + doodles (<=2 stickers, <=3 doodles per beat)
        if bi in (0, 3, 4, 8):
            stl = style["stickers"][:2]
            draw_sticker(d, stl[0], 950, 420, 60, accent)
            if len(stl) > 1:
                draw_sticker(d, stl[1], 130, 1520, 54, accent)
            for dk, (dx, dy) in zip(("sparkle", "ring"), ((806, 620), (240, 700))):
                draw_doodle(d, dk, dx, dy, 40, accent)
        if bi == 8:  # payoff + loop echo
            pf1, pf2 = style["payoff"]
            f = font(F_B, 170)
            tw1, th1 = text_size(f, pf1)
            d.rounded_rectangle([W // 2 - tw1 // 2 - 44, 690, W // 2 + tw1 // 2 + 44, 950],
                                radius=34, fill=(16, 16, 20, 240))
            d.text((W // 2 - tw1 // 2, 716), pf1, font=f, fill=accent + (255,))
            if pf2:
                tw2, _ = text_size(f, pf2)
                d.text((W // 2 - tw2 // 2, 970), pf2, font=f, fill=(255, 255, 255, 255))
            ef = font(F_B, 96)
            loopw = style["types"][0][1]
            tw3, _ = text_size(ef, loopw)
            d.text((W // 2 - tw3 // 2, 1240), "loop: " + loopw, font=ef, fill=cfg["ink"] + (255,))
            if 0.05 <= bt <= 0.12:
                entrance_times.append(round(t, 2))
        if bi == 9:  # end card (full canvas, URL fitted)
            d.rectangle([0, 0, W, H], fill=hexshade(cfg["canvas"], 0.94) + (255,))
            d.rounded_rectangle([10, 10, W - 10, H - 10], radius=40, outline=accent + (255,), width=26)
            ef = font(F_B, 64)
            for li, line in enumerate(["EDIT MASTER SKILL", "Test Edit Skill"]):
                tw, _ = text_size(ef, line)
                d.text((W // 2 - tw // 2, 560 + li * 150), line, font=ef, fill=cfg["ink"] + (255,))
            uf, uw = fit_font(F_B, REPO, int(W * 0.9), 58)
            d.text((W // 2 - uw // 2, 900), REPO, font=uf, fill=hexshade(accent, 0.75) + (255,))
            lum = 0.2126 * accent[0] + 0.7152 * accent[1] + 0.0722 * accent[2]
            pfg = (16, 16, 18, 255) if lum > 120 else (255, 255, 255, 255)
            pill(d, W // 2 - 190, 1160, style["sig_pill"], font(F_B, 48), accent + (255,), pfg)
        frame = np.array(im)

        # captions (word-reveal) on message beats
        if bi in (0, 1, 3, 5, 7):
            frame = caption_plate(frame, [cap_texts[bi]], max(0.0, (bt - 0.15) / 1.1), cfg)

        # whip transition in first 0.22s of each beat (except frame 0 of video)
        if bt < 0.22 and bi > 0:
            frame = whip_frame(frame, 1 if bi % 2 else -1, bt / 0.22, seed=100 + bi)
        # zoom-through at end of b6 (last 0.4s of beat 6)
        if bi == 6 and DURS[6] - bt < 0.4:
            zp = (bt - (DURS[6] - 0.4)) / 0.4
            frame = zoomthrough_frame(frame, zp)
        # invert bite: first 2 frames of b5 — black frame with inverted lockup-band echo
        if bi == 5 and bt < 2 / FPS:
            bite = np.zeros_like(frame[:, :, :3])
            gr = infos[5].get("giant_rect")
            if gr:
                gx2, gy2, gw2, gh2 = gr
                band = frame[max(0, gy2):gy2 + gh2, max(0, gx2):gx2 + gw2, :3]
                if band.size:
                    inv = 255 - cv2.cvtColor(band, cv2.COLOR_RGB2GRAY)
                    inv3 = np.repeat(inv[:, :, None], 3, axis=2)
                    bh, bw3 = inv3.shape[:2]
                    scale = min(0.86 * W / bw3, 0.4 * H / bh, 1.0)
                    nh, nw4 = max(1, int(bh * scale)), max(1, int(bw3 * scale))
                    invr = cv2.resize(inv3, (nw4, nh), interpolation=cv2.INTER_AREA)
                    oy2, ox2 = (H - nh) // 2, (W - nw4) // 2
                    bite[oy2:oy2 + nh, ox2:ox2 + nw4] = invr
            frame = bite

        rgb = np.ascontiguousarray(frame[:, :, :3])
        proc.stdin.write(rgb.tobytes())
        if fi % 150 == 0:
            L(f"frame {fi}/{total_frames}")
    proc.stdin.close()
    proc.wait()

    # dedupe card manifest entries
    seen = set()
    mc = []
    for c in manifest_cards:
        k = (c["t"], c["label"])
        if k not in seen:
            seen.add(k)
            mc.append(c)
    manifest_cards = mc

    L("encode audio...")
    ent = sorted(set(entrance_times))
    wav = f"{od}/audio.wav"
    synth_audio(vid, boundaries, ent, wav)

    # manifest + events saved BEFORE heavy finishing (finishing is resumable via fin11.py)
    hook = list(style["types"][0])
    hook_rect = infos[0].get("hook_rect")
    lockups = []
    for bi in range(10):
        gr = infos[bi].get("giant_rect")
        if gr:
            lockups.append(dict(t0=STARTS[bi], giant=style["types"][bi % 4][1],
                                rect=gr, occluded=bool(subject_ok and bi == 0 and infos[bi].get("occluded", False)),
                                mode=modes[bi]))
    man = dict(
        vid=vid, family=fam, origin="p11_render.py unified", fps=FPS,
        mode_per_beat=modes, beat_starts=STARTS,
        hook=hook, hook_t=1.2, hook_rect=hook_rect,
        lockups=lockups, cards=mc,
        captions=[dict(t0=STARTS[bi]) for bi in (0, 1, 3, 5, 7)],
        phone=[dict(t=STARTS[2], rect=infos[2]["phone_rect"], mode="A")] if infos[2].get("phone_rect") else [],
        payoff=list(style["payoff"]), endcard_text=REPO, loop_word=style["types"][0][1],
        signature=dict(family=fam), palette=dict(accent=list(accent)),
        sfx_entrances=ent, matte=subject_ok, matte_fps=(FPS if subject_ok else None),
        zoom_through_t=STARTS[7], odometer_t=STARTS[4], loop_rect=[0, 1180, 1080, 200], payoff_rect=[0, 680, 1080, 280], caption_rect=[0, 1600, 1080, 240],
        face_zone=fz, odometer_rect=infos[4].get("odometer_rect"),
        subject_bbox=([subj_x, subj_y, subj_np[0].shape[1], target_h] if subject_ok else None),
        total=TOTAL,
    )
    json.dump(man, open(f"{od}/manifest.json", "w"), indent=1)
    json.dump([[e, "pop.wav", 0.4] for e in ent] + [[b, "whoosh.wav", 0.5] for b in boundaries],
              open(f"{od}/sfx_events.json", "w"), indent=1)
    # gate parity list = ALL sfx events (entrance pops + whooshes)
    man["sfx_entrances"] = sorted(set(ent) | set(boundaries))
    json.dump(man, open(f"{od}/manifest.json", "w"), indent=1)
    L("manifest saved; finishing via fin11")
    r = subprocess.run(["python3", f"{ROOT}/scripts/p11_fin.py", vid])
    if r.returncode != 0:
        L(f"fin11 rc={r.returncode} (rerun scripts/p11_fin.py {vid} to resume)")
    L(f"DONE in {time.time()-t00:.0f}s")
    log.close()

if __name__ == "__main__":
    vid = sys.argv[1]
    quick = "--quick" in sys.argv
    render_vid(vid, quick)
