#!/usr/bin/env python3
"""histmap_kit — ADOPTED from historical-map-animation skill (Phase 32 F4).
Physical 2.5D historical map animation grammar: relief-map plates, chroma
sprites, articulated stick-arms, physical props, S-curve camera, auto-fit
lower-thirds, sparse one-shot foley. ZERO neon route lines.

PROVENANCE (license-log, see README.md):
- Source: owner-supplied `historical-map-animation` skill.md attachment.
- EXACT copies (do NOT paraphrase / invent constants): smoothstep, smootherstep,
  spring_pop, parabolic_hop, extract_green_screen_sprite, draw_flame_cluster.
- Documented gotchas implemented as helpers: stick-arm angles -45..-68deg,
  auto-fit lower-third (34pt->28pt when tw>W-56), sparse one-shot foley
  (0.20-0.28 gain under 0dB narration), clean ffmpeg pipe shutdown
  (stdin.close + stderr.read + wait), mandatory keyframe QA (5-7 frames),
  alpha_composite discipline for ALL translucent effects.
- Extensions implemented in-kit (source NAMES these but ships no code):
  procedural relief plates (day/night), diorama deck, physical props
  (chain/planks/barrel/crate/reeds/watchtower/banner), peg-doll sprite factory.
"""
import math
import os
import subprocess as sp

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 720, 1280
OV_W, OV_H = 900, 1600
FPS = 30
SR = 44100

# ---- F12 family palette (exact, from skill Stage-3 prompts) ----
LAND_DAY = (181, 159, 120)      # #B59F78 warm parchment-tan terrain
SNOW = (244, 247, 250)          # #F4F7FA snow-capped peaks
WATER = (75, 114, 130)          # #4B7282 slate-teal rivers/oceans
LAND_NIGHT = (86, 76, 58)       # moonlit dark parchment
WATER_NIGHT = (28, 48, 62)      # deep navy-teal
INK = (42, 36, 23)              # dark ink coastline borders / outlines

_SERIF_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",   # skill spec
    "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
]
_SERIF_LOG = []


def serif_bi(size):
    """Classic bold italic serif map label font (skill: DejaVuSerif-BoldItalic,
    honest fallback chain logged)."""
    global _SERIF_LOG
    for p in _SERIF_CANDIDATES:
        if os.path.exists(p):
            if p not in _SERIF_LOG:
                _SERIF_LOG.append(p)
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/home/z/ems/assets/fonts/PlayfairItalic.ttf", size)


# ================= EXACT COPIES (skill.md Core Verified Engine Helpers) =================

def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def spring_pop(t: float, dur: float = 0.38) -> float:
    if t <= 0.0:
        return 0.0
    u = t / dur
    if u >= 1.0:
        return 1.0
    if u < 0.55:
        return 1.16 * smoothstep(u / 0.55)
    elif u < 0.82:
        return 1.16 - 0.20 * smoothstep((u - 0.55) / 0.27)
    return 0.96 + 0.04 * smoothstep((u - 0.82) / 0.18)


def parabolic_hop(t: float, t0: float, t1: float, p0: tuple, p1: tuple, hop_height: float = 48.0):
    if t <= t0:
        return p0[0], p0[1], 0.0, 0.0
    if t >= t1:
        return p1[0], p1[1], 0.0, 0.0
    u = smootherstep((t - t0) / max(1e-4, t1 - t0))
    x = p0[0] + (p1[0] - p0[0]) * u
    y_linear = p0[1] + (p1[1] - p0[1]) * u
    lift = math.sin(u * math.pi) * hop_height
    tilt = math.sin(u * math.pi * 2.0) * 8.5
    return x, y_linear - lift, lift, tilt


def extract_green_screen_sprite(img_path: str, out_png_path: str, target_max_dim: int = 420) -> Image.Image:
    bgr = cv2.imread(img_path)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, np.array([32, 65, 65]), np.array([90, 255, 255]))
    fg_mask = cv2.bitwise_not(green_mask)
    fg_mask[:8, :] = fg_mask[-8:, :] = fg_mask[:, :8] = fg_mask[:, -8:] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg_mask = cv2.erode(fg_mask, np.ones((3, 3), np.uint8), iterations=1)
    alpha = cv2.GaussianBlur(fg_mask, (3, 3), 0)

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    spill = np.maximum(0.0, g - np.maximum(r, b))
    rgb[:, :, 1] = g - spill * 0.80
    rgba = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])

    ys, xs = np.where(alpha > 20)
    if len(xs) > 0 and len(ys) > 0:
        h, w = fg_mask.shape
        rgba = rgba[max(0, int(ys.min()) - 4):min(h, int(ys.max()) + 5),
                    max(0, int(xs.min()) - 4):min(w, int(xs.max()) + 5)]

    pil_sp = Image.fromarray(rgba, mode="RGBA")
    if max(pil_sp.size) > target_max_dim:
        sc = target_max_dim / float(max(pil_sp.size))
        pil_sp = pil_sp.resize((max(8, int(pil_sp.size[0] * sc)), max(8, int(pil_sp.size[1] * sc))), Image.Resampling.LANCZOS)
    pil_sp.save(out_png_path)
    return pil_sp


def draw_flame_cluster(canvas_pil: Image.Image, cx: float, cy: float, t: float, intensity: float = 1.0, seed: int = 0):
    """Alpha-composited soft fire glow + animated tongues + rising embers (never overwrites canvas alpha)."""
    if intensity <= 0.02:
        return
    s = intensity
    pad = int(max(90, 115 * s))
    patch = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    pd = ImageDraw.Draw(patch, "RGBA")
    pc = pad
    for mult, alpha_v in [(1.0, 26), (0.72, 42), (0.45, 65)]:
        gr = int(76 * s * mult * (0.94 + 0.06 * math.sin(t * 13.0 + seed)))
        pd.ellipse([pc - gr, pc - gr, pc + gr, pc + gr], fill=(255, 110, 20, int(alpha_v * min(1.0, s))))
    for k in range(5):
        ph = t * (10.0 + k * 2.1) + seed * 1.7 + k * 1.3
        ox = (k - 2) * 14 * s + math.sin(ph) * 5 * s
        fh = (44 + (k % 3) * 18) * s * (0.85 + 0.22 * abs(math.sin(ph)))
        fw = (15 + (k % 2) * 5) * s
        pd.polygon([
            (pc + ox - fw, pc + 8 * s),
            (pc + ox - fw * 0.6, pc - fh * 0.45),
            (pc + ox + math.sin(ph * 1.3) * 7 * s, pc - fh),
            (pc + ox + fw * 0.6, pc - fh * 0.45),
            (pc + ox + fw, pc + 8 * s),
        ], fill=(242, 82, 18, int(225 * min(1.0, s))))
        pd.polygon([
            (pc + ox - fw * 0.48, pc + 5 * s),
            (pc + ox + math.sin(ph * 1.3) * 4 * s, pc - fh * 0.62),
            (pc + ox + fw * 0.48, pc + 5 * s),
        ], fill=(255, 226, 92, int(240 * min(1.0, s))))
    for e in range(5):
        ep = (t * 1.1 + seed * 0.23 + e * 0.21) % 1.0
        ex = pc + math.sin(ep * 6.0 + e * 2.0 + seed) * 28 * s - ep * 20 * s
        ey = pc - 18 * s - ep * (pad - 12)
        er = max(2, int((1.0 - ep) * 4.5 * s))
        pd.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 210, 85, int((1.0 - ep) * 230)))
    canvas_pil.alpha_composite(patch, (int(cx - pad), int(cy - pad)))


# ================= GOTCHA HELPERS (exact documented values) =================

def draw_stick_arm(d, shoulder, angle_deg, length, prop=None, hand_r=7):
    """Thin black stick-arm + white-gloved hand. GOTCHA: raised/cheering/shocked
    arm angles stay between -45deg and -68deg (cos>0, sin<0) so arms extend
    cleanly outward+upward and never cross the face."""
    angle_deg = max(-68.0, min(-45.0, float(angle_deg)))
    a = math.radians(angle_deg)
    sx, sy = shoulder
    ex, ey = sx + length * math.cos(a), sy + length * math.sin(a)
    d.line([(sx, sy), (ex, ey)], fill=(20, 16, 12, 255), width=5)
    d.ellipse([ex - hand_r, ey - hand_r, ex + hand_r, ey + hand_r],
              fill=(246, 244, 238, 255), outline=(20, 16, 12, 255), width=2)
    if prop is not None:
        prop(d, ex, ey, a)
    return (ex, ey)


def draw_lower_third(img, text, cy=None):
    """Auto-fit lower-third: measure with textbbox, step down 34pt -> 28pt
    whenever tw > W - 56 (captions never clip at screen edges). Crisp drop
    shadow via alpha_composite patch (F2 discipline)."""
    cy = int(H * 0.885) if cy is None else int(cy)
    size = 34
    while True:
        f = serif_bi(size)
        probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        bb = probe.textbbox((0, 0), text, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        if tw <= W - 56 or size <= 24:
            break
        size -= 2
    pad = 14
    patch = Image.new("RGBA", (tw + pad * 2 + 4, th + pad * 2 + 4), (0, 0, 0, 0))
    pd = ImageDraw.Draw(patch)
    pd.text((pad + 3 - bb[0], pad + 3 - bb[1]), text, font=f, fill=(INK + (210,)))
    patch = patch.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(patch, (int((W - tw) / 2 - pad + 3), cy - pad + 3))
    lab = Image.new("RGBA", (tw + pad * 2 + 4, th + pad * 2 + 4), (0, 0, 0, 0))
    ImageDraw.Draw(lab).text((pad - bb[0], pad - bb[1]), text, font=f,
                             fill=(246, 242, 230, 245))
    img.alpha_composite(lab, (int((W - tw) / 2 - pad), cy - pad))
    return {"font_size": size, "text_w": int(tw), "bar": W - 56}


class OneShotFoley:
    """Sparse one-shot foley: unique brief accents mixed gently under 0dB
    narration. GOTCHA: gain 0.20-0.28 per accent; NEVER loop ambient SFX."""

    def __init__(self, dur_s, sr=SR):
        self.sr = sr
        self.buf = np.zeros(int(dur_s * sr), dtype=np.float32)
        self.used = set()

    def _place(self, kind, t, gain):
        assert 0.20 - 1e-9 <= gain <= 0.28 + 1e-9, "foley gain must stay 0.20-0.28"
        key = (kind, round(t, 2))
        if key in self.used:                      # sparse + unique
            return
        self.used.add(key)
        sr, i0 = self.sr, int(t * self.sr)
        n = int(0.35 * sr)
        tt = np.linspace(0, 0.35, n, endpoint=False)
        rng = np.random.default_rng(int(t * 1000) + hash(kind) % 997)
        if kind == "thump":
            env = np.exp(-tt * 26)
            sig = np.sin(2 * np.pi * (72 - 30 * tt / 0.35) * tt) * env
        elif kind == "knock":
            env = np.exp(-tt * 60)
            sig = (rng.normal(0, 0.4) * env +
                   np.sin(2 * np.pi * 210 * tt) * np.exp(-tt * 90))
        elif kind == "crack":
            env = np.exp(-tt * 14) * (rng.random(n) > 0.86)
            sig = rng.normal(0, 1, n) * env
        else:                                     # whoosh
            env = np.sin(np.pi * np.clip(tt / 0.35, 0, 1)) ** 2
            sig = np.convolve(rng.normal(0, 1, n), np.ones(24) / 24, "same") * env
        seg = (sig / max(1e-6, np.abs(sig).max())).astype(np.float32) * gain
        i1 = min(len(self.buf), i0 + n)
        self.buf[i0:i1] += seg[:i1 - i0]

    def thump(self, t, gain=0.24): self._place("thump", t, gain)
    def knock(self, t, gain=0.22): self._place("knock", t, gain)
    def crack(self, t, gain=0.26): self._place("crack", t, gain)
    def whoosh(self, t, gain=0.24): self._place("whoosh", t, gain)

    def mix_under(self, narration_0db):
        """narration stays at 0dB; foley rides gently underneath."""
        out = np.asarray(narration_0db, dtype=np.float32)
        n = min(len(out), len(self.buf))
        out[:n] += self.buf[:n]
        return np.clip(out, -1.0, 1.0)


class FFmpegPipe:
    """30fps RGB24 -> libx264 pipe. GOTCHA (py3.11+): clean shutdown is
    stdin.close() + stderr.read() + wait() — NEVER communicate()."""

    def __init__(self, out_path, w=W, h=H, fps=FPS, crf=20):
        self.proc = sp.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
             "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
             "-pix_fmt", "yuv420p", out_path], stdin=sp.PIPE, stderr=sp.PIPE)

    def write(self, frame_rgb_bytes):
        self.proc.stdin.write(frame_rgb_bytes)

    def close(self):
        self.proc.stdin.close()
        err = self.proc.stderr.read().decode(errors="replace")
        rc = self.proc.wait()
        return rc, err


class KeyframeQA:
    """Mandatory keyframe QA: save 5-7 representative frames during render."""

    def __init__(self, n=6):
        self.n = n
        self.saved = []

    def maybe_save(self, i, total, img, outdir):
        os.makedirs(outdir, exist_ok=True)
        targets = {int(round(k / max(1, self.n - 1) * (total - 1))) for k in np.linspace(0, self.n - 1, min(max(5, self.n), 7))}
        if i in targets:
            p = os.path.join(outdir, f"qa_f{i:04d}.jpg")
            img.convert("RGB").save(p, quality=90)
            self.saved.append(p)
            return p
        return None


# ================= F12 FAMILY: relief plates, diorama, physical props =================

def _fbm(shape, octaves=5, seed=7):
    rng = np.random.default_rng(seed)
    acc = np.zeros(shape, dtype=np.float32)
    amp, freq = 1.0, 4
    for _ in range(octaves):
        small = rng.random((max(2, int(shape[0] / freq)), max(2, int(shape[1] / freq)))).astype(np.float32)
        img = Image.fromarray((small * 255).astype(np.uint8)).resize(
            (shape[1], shape[0]), Image.BICUBIC)
        acc += np.asarray(img, dtype=np.float32) / 255.0 * amp
        amp *= 0.55
        freq *= 2
    return acc / acc.max()


def relief_plate(night=False, seed=7, w=OV_W, h=OV_H):
    """Clean 3D shaded topographic relief map plate — day (#B59F78/#F4F7FA/
    #4B7282) or moonlit night. STRICTLY empty: no characters/ships/labels/UI."""
    land = LAND_NIGHT if night else LAND_DAY
    water = WATER_NIGHT if night else WATER
    hmap = _fbm((h, w), octaves=6, seed=seed)
    hmap = cv2.GaussianBlur(hmap, (31, 31), 0)
    sea = 0.38
    gy, gx = np.gradient(hmap)
    shade = np.clip(-(gx * 0.7 + gy * 0.7) * 14.0, -28, 28)
    img = np.zeros((h, w, 3), dtype=np.float32)
    land_m = hmap >= sea
    snow_m = land_m & (hmap > sea + 0.34)
    img[:] = np.array(water, dtype=np.float32)
    img[land_m] = np.array(land, dtype=np.float32)
    img[snow_m] = np.array(SNOW if not night else (196, 206, 220), dtype=np.float32)
    # territory tint: subtle flat translucent dark-slate over north
    tint = img.copy()
    tint[: int(h * 0.30)] = tint[: int(h * 0.30)] * 0.88 + np.array([10, 16, 22]) * 0.12
    img = tint
    img += shade[..., None] * (0.4 if night else 1.0)
    if night:
        img *= 0.62
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(out, "RGBA")
    # ink coastline border
    edge = (hmap > sea).astype(np.uint8) * 255
    edge = cv2.Canny(edge, 80, 160)
    ys, xs = np.where(edge > 0)
    for x, y in zip(xs[::17], ys[::17]):
        d.point((int(x), int(y)), fill=INK + (160,))
    return out


def camera_crop(plate, t, t0, t1, a, b, roll=0.0):
    """Smootherstep S-curve virtual camera: 900x1600 plate -> 720x1280 window
    gliding from rect a to rect b (optional deck-pitch roll)."""
    u = smootherstep(max(0.0, min(1.0, (t - t0) / max(1e-4, t1 - t0))))
    x0 = int(a[0] + (b[0] - a[0]) * u)
    y0 = int(a[1] + (b[1] - a[1]) * u)
    w0 = int(a[2] + (b[2] - a[2]) * u)
    h0 = int(a[3] + (b[3] - a[3]) * u)
    win = plate.crop((x0, y0, x0 + w0, y0 + h0)).resize((W, H), Image.LANCZOS)
    if abs(roll) > 0.05:
        win = win.rotate(roll, resample=Image.BICUBIC, fillcolor=tuple(int(c) for c in LAND_DAY))
    return win.convert("RGBA")


# ---- physical props (2.5D, tangible; never abstract neon lines) ----

def draw_iron_chain(d, x0, y0, x1, y1, links=9):
    """Sequentially locking iron chain links (dark iron + highlight arc)."""
    for i in range(links):
        u = i / max(1, links - 1)
        cx, cy = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + 3 * math.sin(i * 1.7)
        rw, rh = 11, 16
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], outline=(52, 50, 54, 255), width=5)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], outline=(92, 92, 100, 210), width=2)
        d.arc([cx - rw, cy - rh, cx + rw, cy + rh], 200, 250, fill=(140, 142, 150, 190), width=2)


def draw_timber_plank_bridge(d, x0, y, x1, progress, planks=7):
    """Timber plank bridge; planks lock sequentially (progress 0..1)."""
    n_done = max(0, min(planks, int(progress * planks + 0.001)))
    for i in range(n_done):
        u = i / max(1, planks - 1)
        px = x0 + (x1 - x0) * u
        w = (x1 - x0) / planks * 0.86
        yoff = 6 * math.sin(i * 0.9)
        d.polygon([(px - w / 2, y + yoff), (px + w / 2, y + yoff - 2),
                   (px + w / 2 - 4, y + yoff + 14), (px - w / 2 + 4, y + yoff + 14)],
                  fill=(122, 88, 52, 255), outline=(60, 42, 24, 255), width=2)
        d.line([(px - w / 2 + 3, y + yoff + 6), (px + w / 2 - 3, y + yoff + 5)],
               fill=(84, 60, 34, 180), width=2)


def draw_3d_wooden_barrel(d, cx, base_y, s):
    """3D wooden barrel (staves + iron hoops)."""
    w, h = s * 0.78, s
    d.ellipse([cx - w / 2, base_y - h * 0.30, cx + w / 2, base_y], fill=(96, 66, 38, 255),
              outline=(50, 34, 18, 255), width=3)
    d.rounded_rectangle([cx - w / 2, base_y - h, cx + w / 2, base_y - h * 0.14],
                        radius=int(w * 0.28), fill=(128, 90, 50, 255),
                        outline=(50, 34, 18, 255), width=3)
    for yy, hw in ((base_y - h * 0.82, w * 0.46), (base_y - h * 0.44, w * 0.525)):
        d.rounded_rectangle([cx - hw, yy, cx + hw, yy + 7], radius=3, fill=(58, 58, 64, 255))
    d.line([(cx - w * 0.28, base_y - h + 8), (cx - w * 0.30, base_y - h * 0.16)],
           fill=(86, 60, 34, 200), width=3)
    d.line([(cx + w * 0.28, base_y - h + 8), (cx + w * 0.30, base_y - h * 0.16)],
           fill=(86, 60, 34, 200), width=3)


def draw_3d_cargo_crate(d, cx, base_y, s, rot=0.0):
    """Isometric cargo crate (front + top + side faces, slats)."""
    w = s
    h = s * 0.82
    dpt = s * 0.34
    pts_f = [(cx - w / 2, base_y - h), (cx + w / 2, base_y - h),
             (cx + w / 2, base_y), (cx - w / 2, base_y)]
    pts_t = [(cx - w / 2, base_y - h), (cx - w / 2 + dpt, base_y - h - dpt * 0.7),
             (cx + w / 2 + dpt, base_y - h - dpt * 0.7), (cx + w / 2, base_y - h)]
    pts_s = [(cx + w / 2, base_y - h), (cx + w / 2 + dpt, base_y - h - dpt * 0.7),
             (cx + w / 2 + dpt, base_y - dpt * 0.7), (cx + w / 2, base_y)]
    d.polygon(pts_s, fill=(104, 74, 42, 255), outline=(46, 32, 18, 255))
    d.polygon(pts_t, fill=(140, 102, 58, 255), outline=(46, 32, 18, 255))
    d.polygon(pts_f, fill=(122, 88, 50, 255), outline=(46, 32, 18, 255), width=3)
    for yy in (base_y - h * 0.33, base_y - h * 0.66):
        d.line([(cx - w / 2 + 4, yy), (cx + w / 2 - 4, yy)], fill=(88, 62, 34, 220), width=3)


def draw_reed_bundle(d, cx, base_y, s, n=6):
    """Bundled reeds leaning at the bank."""
    for i in range(n):
        a = math.radians(-14 + i * 5.2)
        x1 = cx + (i - n / 2) * s * 0.16
        x2 = x1 + math.sin(a) * s * 0.9
        y2 = base_y - math.cos(a) * s
        d.line([(x1, base_y), (x2, y2)], fill=(96, 112, 60, 255), width=4)
        d.ellipse([x2 - 3, y2 - 7, x2 + 3, y2 + 1], fill=(150, 130, 70, 255))


def draw_watchtower_banner(d, cx, base_y, s, t):
    """Wooden watchtower + fluttering camp banner."""
    d.line([(cx - s * 0.22, base_y), (cx, base_y - s)], fill=(70, 50, 30, 255), width=5)
    d.line([(cx + s * 0.22, base_y), (cx, base_y - s)], fill=(70, 50, 30, 255), width=5)
    d.line([(cx - s * 0.30, base_y - s * 0.45), (cx + s * 0.30, base_y - s * 0.55)],
           fill=(70, 50, 30, 255), width=4)
    d.polygon([(cx - s * 0.16, base_y - s * 0.9), (cx + s * 0.16, base_y - s * 0.9),
               (cx + s * 0.10, base_y - s * 1.12), (cx - s * 0.10, base_y - s * 1.12)],
              fill=(96, 68, 40, 255), outline=(46, 32, 18, 255), width=2)
    fh = s * 0.30
    fw = s * 0.34 * (1 + 0.12 * math.sin(t * 5.0))
    d.polygon([(cx, base_y - s * 1.10), (cx + fw, base_y - s * 1.10 + 4),
               (cx + fw * 0.9, base_y - s * 1.10 + fh),
               (cx + fw * 0.5, base_y - s * 1.10 + fh * 0.75),
               (cx, base_y - s * 1.10 + fh)], fill=(150, 44, 38, 235),
              outline=(60, 20, 16, 255), width=2)


def peg_doll_sprite(out_png, body=(140, 44, 40), size=420):
    """Procedural chibi peg-doll on pure #00FF00 (replica-test stand-in for the
    AI-generated chroma plates; extracted via extract_green_screen_sprite)."""
    s = size
    img = Image.new("RGB", (s, s), (0, 255, 0))
    d = ImageDraw.Draw(img)
    cx = s // 2
    base = int(s * 0.86)
    bw = int(s * 0.34)
    d.ellipse([cx - bw, base - int(s * 0.10), cx + bw, base + int(s * 0.10)],
              fill=(60, 30, 20))
    d.polygon([(cx - bw * 0.62, base), (cx + bw * 0.62, base),
               (cx + bw * 0.40, base - int(s * 0.46)),
               (cx - bw * 0.40, base - int(s * 0.46))], fill=body)
    hr = int(s * 0.22)
    hy = base - int(s * 0.56)
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=(244, 224, 198))
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], outline=(40, 30, 24), width=4)
    d.ellipse([cx - int(hr * 0.38), hy - int(hr * 0.12), cx - int(hr * 0.16), hy + int(hr * 0.10)], fill=(24, 20, 18))
    d.ellipse([cx + int(hr * 0.16), hy - int(hr * 0.12), cx + int(hr * 0.38), hy + int(hr * 0.10)], fill=(24, 20, 18))
    d.arc([cx - int(hr * 0.30), hy + int(hr * 0.10), cx + int(hr * 0.30), hy + int(hr * 0.52)],
          20, 160, fill=(60, 40, 36), width=4)
    img.save(out_png)
    return out_png
