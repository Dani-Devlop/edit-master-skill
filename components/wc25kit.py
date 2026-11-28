#!/usr/bin/env python3
"""wc25kit — Phase 25 PROVIDED-CODE kit (WC1-WC4) + showcase helpers.
WC2 occlusion hook: per-frame performer alpha from LIVE MV footage via
rembg/isnet-general-use; composite order = full-bleed live footage ->
giant volt type layer -> performer_rgba -> brackets/artist-tape/captions.
Matte fps == output fps (per source frame, cached PNG seq).
WC1 video-in-card: crop-to-window-aspect live frame + polaroid border overlay
+ rotate + spring stagger — cards ALWAYS render the live frame passed in.
WC3 cutout depth: contact shadow (blurred black ellipse under cutout) +
parallax (cutout 1.02x vs bg 1.0x) + rim-light edge; never flat pasted.
WC4 tissue fill: halftone + ghost + gradient + particles behind card/type;
DOF blur helper for back layers; no empty box.
Imported by render_t1_v25_showcase / render_t1_v25."""
import os, math, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

VOLT = (216, 243, 74)
INK = (16, 17, 20)
# Ph26: portable run paths (env-overridable; old sandbox paths purged)
EMS_WORK = os.environ.get("EMS_WORK", "/tmp/ems-work/26-run")
MV = os.environ.get("EMS_MV", "/home/z/my-project/upload/4_6051789922870758373 (1).mp4")
MATTE_DIR = f"{EMS_WORK}/matte/seq"

# ---------------- Ph26 S4/B10: glyph collision registry ----------------
# B10 bans overlaps between {notification, title/keyword text, caption pill,
# scene-tag, stickers}. Persons/footage cutouts are NOT registered: cutout
# occlusion over art is a deliberate depth feature (WC2/B2), not crowding.
OCC = {"boxes": [], "violations": []}

def occ_reset():
    OCC["boxes"] = []
    OCC["violations"] = []

def occ_add(name, box, kind="glyph"):
    """kind: glyph | ui | sticker. box=(x0,y0,x1,y1)."""
    OCC["boxes"].append({"name": name, "kind": kind,
                         "box": [int(v) for v in box]})

def occ_violations(min_gap=2):
    out = []
    bs = OCC["boxes"]
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            a, b = bs[i], bs[j]
            if a["kind"] == "sticker" and b["kind"] == "sticker":
                continue  # collage stacking between stickers is allowed
            ax0, ay0, ax1, ay1 = a["box"]
            bx0, by0, bx1, by1 = b["box"]
            ox = min(ax1, bx1) - max(ax0, bx0)
            oy = min(ay1, by1) - max(ay0, by0)
            if ox > min_gap and oy > min_gap:
                out.append({"a": a["name"], "b": b["name"],
                            "overlap_px": [int(ox), int(oy)]})
    return out

# ---------------- WC2: per-frame performer alpha (LIVE footage) ----------------
_SESS = None
def matte_session():
    global _SESS
    if _SESS is None:
        from rembg import new_session
        _SESS = new_session("isnet-general-use")
    return _SESS

def mv_source_frame(t):
    """decode ONE MV source frame at native 720x900 (ffmpeg, cached)"""
    png = f"{EMS_WORK}/mv/src_{int(t * 1000):05d}.png"
    if not os.path.exists(png):
        os.makedirs(os.path.dirname(png), exist_ok=True)
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(max(0.02, t)),
                        "-i", MV, "-frames:v", "1", png], check=True)
    return Image.open(png).convert("RGB")

def matte_frame(t, force=False):
    """WC2: performer_rgba for MV source time t (cached; matte fps == use fps).
    Returns RGBA 720x900 or None if matte is (near) empty."""
    png = f"{MATTE_DIR}/m_{int(t * 1000):05d}.png"
    if not os.path.exists(png) or force:
        os.makedirs(MATTE_DIR, exist_ok=True)
        src = mv_source_frame(t)
        from rembg import remove
        cut = remove(src, session=matte_session())
        a = np.asarray(cut.getchannel("A"))
        a = np.clip((a.astype(np.float32) - 45) / (255 - 45) * 255, 0, 255)  # kill halo
        cut.putalpha(Image.fromarray(a.astype(np.uint8)))
        ys, xs = np.where(a > 12)
        if len(xs) < 1200:
            Image.new("RGBA", src.size, (0, 0, 0, 0)).save(png)
            return None
        cut.save(png)
    out = Image.open(png).convert("RGBA")
    if np.asarray(out.getchannel("A")).sum() < 3000:
        return None
    return out

def cover_1080x1920(im):
    """cover-crop any image to full-bleed 1080x1920 (geometry shared by
    footage + matte so occlusion stays pixel-registered)"""
    W, H = 1080, 1920
    w, h = im.size
    s = max(W / w, H / h)
    nw, nh = int(w * s + 0.5), int(h * s + 0.5)
    im2 = im.resize((nw, nh), Image.LANCZOS if s < 1 else Image.BICUBIC)
    x0 = (nw - W) // 2
    y0 = (nh - H) // 2
    return im2.crop((x0, y0, x0 + W, y0 + H))

def hook_footage_perf(t_src, grade_fn=None):
    """WC2 returns (full-bleed live footage RGB, performer RGBA or None)
    for MV source time t_src — both cover-cropped to 1080x1920, registered."""
    src = mv_source_frame(t_src)
    perf = matte_frame(t_src)
    if grade_fn is not None:
        src = grade_fn(src)
    if perf is not None:
        # grade the performer cutout with the same film grade for cohesion
        rgb = perf.convert("RGB")
        a = perf.getchannel("A")
        rgb = grade_fn(rgb) if grade_fn is not None else rgb
        perf = Image.merge("RGBA", (*rgb.split(), a))
    return cover_1080x1920(src), (cover_1080x1920(perf) if perf is not None else None)

# ---------------- WC1: video-in-card (live frame in bordered window) -------------
def wc1_card(live_frame, w, h, rot=0.0, border="polaroid", border_px=None):
    """WC1: crop live frame to window aspect (force_original_aspect_ratio=increase
    then center-crop == ffmpeg recipe) + polaroid/ink border overlay + rotate.
    The caller passes a LIVE frame; nothing here freezes video."""
    lw, lh = live_frame.size
    s = max(w / lw, h / lh)
    nw, nh = max(w, int(lw * s + 0.5)), max(h, int(lh * s + 0.5))
    win = live_frame.resize((nw, nh), Image.BICUBIC)
    x0, y0 = (nw - w) // 2, (nh - h) // 2
    win = win.crop((x0, y0, x0 + w, y0 + h))
    bp = border_px if border_px is not None else max(10, w // 30)
    if border == "polaroid":
        card = Image.new("RGBA", (w + bp * 2, h + bp * 2 + bp), (246, 244, 238, 255))
        card.alpha_composite(win.convert("RGBA"), (bp, bp))
    else:  # ink card + volt hairline
        card = Image.new("RGBA", (w + bp * 2, h + bp * 2), (10, 10, 12, 255))
        card.alpha_composite(win.convert("RGBA"), (bp, bp))
        d = ImageDraw.Draw(card)
        d.rectangle([0, 0, card.width - 1, card.height - 1], outline=VOLT + (220,), width=3)
    if abs(rot) > 0.05:
        card = card.rotate(rot, expand=True, resample=Image.BICUBIC)
    return card

def wc1_card_shadow(card, blur=14, alpha=110):
    sh = Image.new("RGBA", (card.width + 60, card.height + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([30, 38, 30 + card.width, 38 + card.height],
                                 fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(card, (30, 30))
    return sh

def spring_stagger(i, t, t0, per=0.14, dur=0.4):
    """WC1 stagger: card i enters per*i seconds after t0 (spring)"""
    from importlib import import_module
    R = import_module("renderlib")
    return R.spring_scale(max(0.0, t - t0 - i * per), dur)

# ---------------- WC3: cutout depth (contact shadow + parallax + rim) ------------
_R = None
def bind_renderlib(mod):
    global _R
    _R = mod

def _persons():
    return _R.PERSONS if hasattr(_R, "PERSONS") else {}

def lift_person_v25(name, k=1.26, lift=16):
    """alpha-PRESERVING tone-map: 2-98% auto-levels + lift so dark B&W MV
    cutouts read bright on dark footage (hybrid human-polish, B4 round 2+
    design change — black-on-black figures cannot show depth)"""
    im = _persons().get(name)
    if im is None:
        return False
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    # Ph26 S2 palette lock: cutouts are B&W — any MV color riding on a cutout
    # is a palette leak (blue/green cutouts failed the v25 critic; B8 census
    # enforces single-accent volt on the whole frame)
    _lum = arr.mean(axis=2, keepdims=True)
    arr = np.repeat(_lum, 3, axis=2)
    lo, hi = np.percentile(arr, [2, 98])
    if hi > lo + 1e-3:
        arr = (arr - lo) / (hi - lo) * 232.0 + 14.0
    arr = np.clip(arr * k + lift, 0, 255).astype(np.uint8)
    a = im.getchannel("A")
    out = Image.fromarray(arr).convert("RGBA")
    out.putalpha(a)
    _persons()[name] = out
    return True

def paste_person_v25(img, center, hh, which, rot=0.0, alpha=1.0,
                     cam_dx=0.0, cam_dy=0.0, zoom_bg=1.0, rim=True,
                     rim_color=(240, 250, 200), contact=True, seed=0,
                     shadow_boost=1.0):
    """WC3 cutout depth:
      - contact shadow: blurred black ellipse UNDER the cutout (not a hard oval)
      - parallax: cutout scales 1.02x relative to bg zoom and shifts against
        camera pan direction (foreground reads in front of bg)
      - rim-light: edge band from alpha gradient, tinted, top-lit
    Never a flat pasted cutout."""
    im = _persons().get(which)
    if im is None:
        return None
    w0, h0 = im.size
    s = (hh / h0) * 1.02 * max(1.0, zoom_bg)          # WC3 parallax 1.02x vs bg 1.0x
    im2 = im.resize((max(1, int(w0 * s)), max(1, int(hh * s))), Image.LANCZOS)
    if alpha < 1.0:
        a = im2.getchannel("A").point(lambda v: int(v * alpha))
        im2.putalpha(a)
    if rot:
        im2 = im2.rotate(rot, expand=True, resample=Image.BICUBIC)
    # DIRECTIONAL rim light (key side = top-left), neutral warm-white — reads as
    # light, not a neon sticker outline (B4 fix round 2)
    if rim:
        a = im2.getchannel("A")
        band = np.clip(np.asarray(Image.fromarray(np.asarray(a), "L")
                                  .filter(ImageFilter.MaxFilter(5))
                                  .filter(ImageFilter.GaussianBlur(1))
                                  ).astype(np.int16)
                       - np.asarray(a.filter(ImageFilter.MinFilter(5))).astype(np.int16),
                       0, 255).astype(np.float32)
        w_r = im2.width
        xs = np.linspace(0, 1, w_r)[None, :]
        ys = np.linspace(0, 1, im2.height)[:, None]
        horiz = np.clip(1.25 - 2.2 * xs, 0, 1)          # strong left -> zero right
        vert = np.clip(1.1 - 1.1 * ys, 0, 1)            # strong top -> fade down
        band = band * horiz * vert * 1.6
        rim_img = Image.new("RGBA", im2.size, (242, 240, 232, 0))
        rim_img.putalpha(Image.fromarray(np.clip(band, 0, 255).astype(np.uint8)))
        im2.alpha_composite(rim_img)
    cx, cy = center
    px = int(cx - im2.width / 2 - 0.035 * cam_dx)     # foreground moves AGAINST pan
    py = int(cy - im2.height / 2 - 0.035 * cam_dy)
    if contact:
        # (0) darken patch BEHIND the figure (separation on dark footage)
        patch = Image.new("RGBA", (im2.width + 120, im2.height + 120), (0, 0, 0, 0))
        ImageDraw.Draw(patch).ellipse([30, 20, 30 + im2.width + 60, 20 + im2.height + 60],
                                      fill=(0, 0, 0, min(255, int(105 * shadow_boost))))
        patch = patch.filter(ImageFilter.GaussianBlur(34))
        img.alpha_composite(patch, (px - 60, py - 60))
        # (1) whole-figure cast shadow (offset, tighter blur -> reads as cast)
        sh_full = Image.new("RGBA", (im2.width + 60, im2.height + 60), (0, 0, 0, 0))
        fa = im2.getchannel("A").point(lambda v: int(v * min(1.0, 0.92 * shadow_boost)))
        black = Image.new("RGBA", im2.size, (0, 0, 0, 255))
        black.putalpha(fa)
        sh_full.alpha_composite(black, (26, 34))
        sh_full = sh_full.filter(ImageFilter.GaussianBlur(12))
        img.alpha_composite(sh_full, (px - 30, py - 30))
        # (2) contact shadow: dark blurred ellipse UNDER the feet
        sw = int(im2.width * 0.88)
        sh_img = Image.new("RGBA", (sw + 40, 60), (0, 0, 0, 0))
        ImageDraw.Draw(sh_img).ellipse([20, 10, 20 + sw, 50],
                                       fill=(0, 0, 0, min(255, int(185 * shadow_boost))))
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(9))
        img.alpha_composite(sh_img, (int(cx - sh_img.width / 2),
                                     int(cy + im2.height / 2 - 34)))
    img.alpha_composite(im2, (px, py))
    return (px, py, im2.size)

# ---------------- WC4: tissue fill (no empty box) --------------------------------
def tissue_fill(img, region, t, tone=(118, 120, 132), alpha=56, step=20,
                particles=14, seed=0, ghost=None, ghost_font=None,
                ghost_y=None):
    """WC4: halftone + ghost type + vertical gradient + moving particles behind
    card/type layers. region=(x0,y0,x1,y1)."""
    from importlib import import_module
    RL = import_module("renderlib")
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = [int(v) for v in region]
    RL._halftone(d, img.width, img.height, tone, alpha=alpha, step=step,
                 region=(y0, y1, x0, x1))
    # vertical env gradient (light falls from top)
    gh = max(1, y1 - y0)
    grad = Image.new("L", (1, gh))
    for yy in range(gh):
        grad.putpixel((0, yy), int(30 * (1 - yy / gh)))
    grad = grad.resize((max(1, x1 - x0), gh))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    lay.paste(Image.new("RGBA", (max(1, x1 - x0), gh), (238, 240, 246, 255)),
              (x0, y0), grad)
    img.alpha_composite(lay)
    # moving particles (volt/white pixel dust, drift upward)
    rng = np.random.default_rng(seed * 977 + int(t * 3))
    for i in range(particles):
        px = rng.uniform(x0, x1)
        py = y1 - ((t * rng.uniform(18, 55) + rng.uniform(0, gh)) % gh)
        s = rng.uniform(3, 8)
        col = VOLT + (int(rng.integers(120, 220)),) if rng.random() < 0.6 \
            else (238, 240, 244, int(rng.integers(90, 170)))
        d.rectangle([px, py, px + s, py + s], fill=col)
    if ghost and ghost_font is not None:
        f = ghost_font
        bb = d.textbbox((0, 0), ghost, font=f)
        gy = y0 + 8 if ghost_y is None else int(ghost_y)  # Ph26 S4: movable ghost
        d.text(((img.width - (bb[2] - bb[0])) / 2, gy), ghost,
               font=f, fill=(240, 240, 236, 34))
    return img

def dof_blur(img, radius=2.2, except_rect=None):
    """WC4 depth-of-field: blur whole layer except_rect (kept sharp)."""
    blurred = img.filter(ImageFilter.GaussianBlur(radius))
    if except_rect is None:
        return blurred
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rectangle(except_rect, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(18))
    return Image.composite(img, blurred, mask)

# ---------------- stakes odometer (P0 keep) ---------------------------------------
def odometer(d, center, value, t, size=96, digits=6, color=VOLT, ink=(240, 240, 238, 235)):
    """rolling-digit stakes odometer: each digit column scrolls to its value"""
    txt = str(int(value)).zfill(digits)
    col_w = int(size * 0.62)
    total = col_w * digits
    x0 = center[0] - total / 2
    from importlib import import_module
    R = import_module("renderlib")
    f = R.montserrat(size, 900)
    for i, ch in enumerate(txt):
        cx = x0 + i * col_w + col_w / 2
        frac = (value % 10) / 1.0
        spin = max(0.0, 1.0 - ((value % 1) * 4))  # settle feel
        d.rounded_rectangle([cx - col_w / 2 + 4, center[1] - size * 0.62,
                             cx + col_w / 2 - 4, center[1] + size * 0.62],
                            radius=10, fill=(10, 10, 14, 215), outline=(240, 244, 255, 60), width=2)
        bb = d.textbbox((0, 0), ch, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2, center[1] - (bb[3] - bb[1]) / 2 - bb[1]),
               ch, font=f, fill=ink)
        d.line([(cx - col_w / 2 + 6, center[1] - size * 0.0),
                (cx + col_w / 2 - 6, center[1])], fill=color + (40,), width=2)
    return txt

# ---------------- kick-synced entrance helpers (IG1 on elements) ------------------
def wobble_xy(t, seed=0, amp=7.0, freq=0.9):
    return (amp * math.sin(t * freq + seed * 1.7),
            amp * math.cos(t * freq * 0.83 + seed * 2.3))
