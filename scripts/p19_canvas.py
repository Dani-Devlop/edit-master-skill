#!/usr/bin/env python3
"""Phase 19 Canvas System (AS2/AS3).
AS2: scene backgrounds are DESIGNED (solid/gradient brand + paper/grain texture +
     halftone/ghost atoms) OR real full-screen footage. Blur-of-same-footage allowed
     ONLY <=0.3s as transition — never as whole scene bg.
AS3: feathered wipes (no dead plain area); end card NO-BRAND (loop echo + family
     pill only; branding only on manager command).
Deterministic (seeded). Logs bg_kind per beat for GC3."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MAX_BLUR_BG_S = 0.30   # AS2 ceiling


def _grain(arr, seed, amount=5.0):
    rng = np.random.RandomState(seed)
    return arr + rng.normal(0, amount, arr.shape)


def _halftone(im, accent, alpha=26, step=26, r=1.6, seed=3):
    """subtle halftone dot field (designed texture atom)."""
    d = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    rng = np.random.RandomState(seed)
    jx = int(rng.uniform(0, step)); jy = int(rng.uniform(0, step))
    for yy in range(jy, h, step):
        for xx in range(jx, w, step):
            rr = r * (0.8 + 0.4 * math.sin((xx + yy) / 90.0))
            d.ellipse([xx - rr, yy - rr, xx + rr, yy + rr],
                      fill=accent + (alpha,))
    return im


def _ghost_ring(im, cx, cy, rad, width=3, alpha=30):
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(255, 255, 255, alpha),
              width=width)
    return im


def designed_darkmono(ow, oh, accent, seed=7, kind="gradient"):
    """AS2 designed canvas: dark mono gradient + grain + halftone + ghost ring.
    Returns np.float32 frame (H,W,3)."""
    rng = np.random.RandomState(seed)
    top = np.array([10, 10, 12], np.float32)
    bot = np.array([24, 24, 28], np.float32) + rng.uniform(-3, 3, 3)
    g = np.linspace(0, 1, oh, dtype=np.float32)[:, None, None]
    arr = top[None, None, :] * (1 - g) + bot[None, None, :] * g
    arr = np.repeat(arr, ow, axis=1)
    arr = _grain(arr, seed, 4.0)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im = _halftone(im, accent, alpha=22, step=30, seed=seed + 1)
    im = _ghost_ring(im, int(ow * 0.5), int(oh * 0.34), int(ow * 0.46), 3, 26)
    im = _ghost_ring(im, int(ow * 0.5), int(oh * 0.34), int(ow * 0.30), 2, 18)
    return np.asarray(im).astype(np.float32)


def designed_paper(ow, oh, seed=11):
    """warm paper + fibers + grain (for painting/card scenes)."""
    rng = np.random.RandomState(seed)
    base = np.full((oh, ow, 3), 236.0, np.float32)
    base = _grain(base, seed, 9.0)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for _ in range(int(oh * ow / 5200)):
        x, y = rng.randint(0, ow), rng.randint(0, oh)
        d.point((x, y), fill=(212, 205, 192))
    return np.asarray(im).astype(np.float32)


def designed_for_scene(stype, ow, oh, accent, seed=7):
    """route: painting -> paper; graphs/counters/listicles -> darkmono."""
    if stype == "S05_painting_slide_in":
        return designed_paper(ow, oh, seed + 5)
    return designed_darkmono(ow, oh, accent, seed)


def feathered_wipe(frame_np, keep_np, frac, direction=1, feather=24):
    """AS3: wipe with feathered edge (no dead plain area). frac 0..1 revealed."""
    h, w = int(frame_np.shape[0]), int(frame_np.shape[1])
    edge = int(w * frac)
    if edge <= 0:
        return keep_np
    mask = np.zeros((h, w), np.float32)
    mask[:, :edge] = 1.0
    x0 = max(0, edge - feather)
    ramp = np.linspace(1.0, 0.0, max(2, edge - x0))[None, :]
    mask[:, x0:edge] = ramp
    return frame_np * mask[..., None] + keep_np * (1 - mask[..., None])


def endcard_family_pill(pil, family, accent, font_small):
    """AS3: NO-BRAND end card = loop echo + family pill only. No repo URL/brand."""
    d = ImageDraw.Draw(pil)
    wpx = font_small.getlength(family)
    W, H = pil.size
    x0 = (W - int(wpx)) // 2 - 14
    y0 = int(H * 0.56)
    d.rounded_rectangle([x0, y0, x0 + int(wpx) + 28, y0 + 42], radius=12,
                        fill=(12, 12, 12), outline=accent, width=2)
    d.text((W // 2, y0 + 21), family, font=font_small, fill=(255, 255, 255), anchor="mm")
    return pil
