#!/usr/bin/env python3
"""12s GRAPHICS-FIRST REPLICA — target: eightsenses-style (user screen-recording).
Scene engine: beat-locked scene swaps, spring entrances, karaoke v2 captions,
M1 3D accent (pre-rendered alpha seq), synthesized SFX bank, WELCOME audio bed.
Engine log per beat: pil/numpy (canvas+type), bpy-alpha-seq (3D), ffmpeg (assemble/audio).
Output: 1080x1920@30fps master + frames dir (TEMP, purged after gate)."""
import os, sys, math, wave, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
import renderlib as R
from renderlib import VOLT, INK

W, H, FPS, DUR = 1080, 1920, 30, 12.0
N = int(FPS * DUR)
SCRATCH = "/tmp/my-project/p21work/scratch"
FRAMES = f"{SCRATCH}/replica_frames"
OUTDIR = f"{SCRATCH}/replica_out"
MV = "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

# ---------------- beat grid from audio energy (E3/pl5) ----------------
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
    # spectral-flux-ish: positive diff of log energy
    le = np.log(e + 1e-4)
    flux = np.clip(np.diff(le, prepend=le[0]), 0, None)
    beats = []
    last = -1.0
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

BEATS, ENERGY = beat_grid(f"{SCRATCH}/target_audio.wav", DUR + 0.5)
# strongest onset in 8.5-11.5s window = the drop for M1 slam
cand = [b for b in BEATS if 8.5 <= b <= 11.5]
DROP = max(cand, key=lambda b: ENERGY[int(b * 100)]) if cand else 10.0
print("BEATS:", [round(b, 2) for b in BEATS])
print("DROP:", round(DROP, 3))

def nearest_beat_after(t):
    for b in BEATS:
        if b >= t - 0.02:
            return b
    return t

# ---------------- scene plan (12 scenes, quota: 100% designed canvas) ----------------
# grammar: target inventory S01-S10 mapped to WELCOME lyrics (whisper ts)
SCENES = [
    # (start, canvas, kind, lyric_line, headline, sub)
    (0.00, "paper",   "hero",      ["Welcome", "to", "the"], ("the", "party"), "where everybody"),
    (0.90, "navy",    "card",      ["to", "the", "party"], ("where", "everybody"), "dies at the end"),
    (1.80, "paper",   "but",       ["where", "everybody"], ("dies", "at"), "the end"),
    (2.70, "red",     "icon",      ["dies", "at", "the"], ("end", "MOVE"), "your body"),
    (3.60, "black",   "listicle",  ["MOVE", "your", "body"], ("this", "is"), "the beat"),
    (4.50, "green",   "orb",       ["this", "is", "bot"], ("to", "beat"), "on homicide scene"),
    (5.40, "paper",   "matters",   ["on", "homicide", "scene"], ("show", "the"), "world the scene"),
    (6.30, "navy",    "lookup",    ["I", "think", "you"], ("walk", "NOT"), "me"),
    (7.20, "paper",   "constel",   ["walk", "NOT", "me"], ("what", "comes"), "next hits"),
    (8.10, "red",     "polaroid",  ["what", "comes", "next"], ("the", "SCENE"), "raw vs graded"),
    (float(DROP) - 0.35, "paper", "m1", None, ("WELCOME",), None),
    (float(DROP) + 0.55, "paper", "endcard", None, ("WELCOME", "to the party"), None),
]
SCENES = [(s, c, k, l, hd, sub) for (s, c, k, l, hd, sub) in SCENES]
ENGINE_LOG = []

# whisper word ts (±120ms) for karaoke v2 — hook from transcribe
LYRICS = [
    {"text": "Welcome", "start": 0.00, "end": 0.62},
    {"text": "to", "start": 0.62, "end": 0.82},
    {"text": "the", "start": 0.82, "end": 0.98},
    {"text": "party", "start": 0.98, "end": 1.48},
    {"text": "where", "start": 1.48, "end": 1.86},
    {"text": "everybody", "start": 1.86, "end": 2.62},
    {"text": "dies", "start": 2.62, "end": 2.96},
    {"text": "at", "start": 2.96, "end": 3.14},
    {"text": "the", "start": 3.14, "end": 3.30},
    {"text": "end", "start": 3.30, "end": 3.94},
    {"text": "MOVE", "start": 4.32, "end": 4.86},
    {"text": "your", "start": 4.86, "end": 5.10},
    {"text": "body", "start": 5.10, "end": 5.44},
    {"text": "homicide", "start": 6.30, "end": 7.10},
    {"text": "scene", "start": 7.10, "end": 7.60},
    {"text": "WALK", "start": 8.32, "end": 8.90},
    {"text": "not", "start": 8.90, "end": 9.10},
    {"text": "me", "start": 9.10, "end": 9.42},
    {"text": "WELCOME", "start": 9.42, "end": 10.30},
]

def scene_at(t):
    idx = 0
    for i, (s, *rest) in enumerate(SCENES):
        if t >= s:
            idx = i
    return idx

def entrance(t0, t, dur=0.32):
    return R.spring_scale(max(0.0, t - t0), dur)

def exit_scale(t0, t, t1):
    """exit 100-200ms before scene end"""
    dt = t1 - t
    if dt < 0.16:
        return max(0.72, 1.0 - (0.16 - dt) * 1.8)
    return 1.0

def ghost_stamp(img, text, f, alpha=24, pos="top"):
    d = ImageDraw.Draw(img, "RGBA")
    bb = d.textbbox((0, 0), text, font=f)
    tw = bb[2] - bb[0]
    y = img.height * 0.055 if pos == "top" else img.height * 0.86
    d.text(((img.width - tw) / 2, y), text, font=f, fill=(255, 255, 255, alpha))

# frame sources for polaroids/inserts
def mv_frame(t):
    png = f"{SCRATCH}/mvf_{int(t * 1000)}.png"
    if not os.path.exists(png):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", MV,
                        "-frames:v", "1", "-vf", "scale=720:900", png], check=True)
    return Image.open(png).convert("RGB")

def clean_cutout(name, thr=45):
    """alpha threshold + trim + feather (3D7: no halo/fringe)"""
    from PIL import ImageFilter
    im = Image.open(f"{SCRATCH}/cutouts/cut_{name}.png").convert("RGBA")
    a = np.array(im)
    al = a[..., 3].astype(np.uint8)
    al[al < thr] = 0
    a[..., 3] = al
    im2 = Image.fromarray(a)
    ys, xs = np.where(np.array(im2)[..., 3] > 10)
    if len(xs):
        im2 = im2.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return im2

PERSON = clean_cutout("stair11_isnet")
BUILDING = clean_cutout("building25_isnet")
CAR = clean_cutout("car_isnet")

def paste_person(img, center, height, which="stair", rot=0.0, shadow=True):
    src = {"stair": PERSON, "building": BUILDING, "car": CAR}[which]
    w = int(src.width * height / src.height)
    fg = src.resize((w, int(height)), Image.LANCZOS)
    if rot:
        fg = fg.rotate(rot, expand=True, resample=Image.BICUBIC)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        cx, cy = center
        ds.ellipse([cx - w * 0.42, cy + height * 0.42, cx + w * 0.42, cy + height * 0.52], fill=(0, 0, 0, 70))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        img.alpha_composite(sh)
    img.alpha_composite(fg, (int(center[0] - fg.width / 2), int(center[1] - fg.height / 2)))

# ---------------- M1 3D accent sequence (bpy alpha) ----------------
M1_SEQ = f"{SCRATCH}/m1_seq"
M1_START = None  # set after DROP known
M1_FRAMES = 84

def paste_m1(img, t):
    f = int((t - DROP) * FPS)
    if f < 0 or f >= M1_FRAMES:
        return
    p = f"{M1_SEQ}/f_{f:04d}.png"
    if not os.path.exists(p):
        return
    fg = Image.open(p).convert("RGBA").resize((1080, 1920))
    img.alpha_composite(fg)

# ---------------- per-frame compose ----------------
rng = np.random.default_rng(21)
CAP_Y = int(H * 0.885)  # single consistent lower-third (text bottom <= 1440 safe)

def density_pass(img, t, s0, kind):
    """R3 richness: push every frame to 10-14 elements; no dead zones."""
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(int(t * 5) + 7)
    # drifting pixel dot clusters (re-seeded each 0.2s -> visible motion)
    dx = int(rng.uniform(-14, 14)); dy = int(rng.uniform(-10, 10))
    R.pixel_dots(img, 7, (70 + dx, 150 + dy, W - 70 + dx, 330 + dy), seed=int(t * 5) + 7, size=9)
    R.pixel_dots(img, 6, (90 + dy, int(H * 0.60) + dx, W - 90 + dy, int(H * 0.72) + dx), seed=int(t * 5) + 31, size=8)
    # icon row (3 squircle chips) top-left
    for i in range(3):
        R.app_icon(img, (110 + i * 96, 210), 34, glyph=["✦", "→", "♪"][i],
                   fill=(20, 20, 24) if i % 2 == 0 else VOLT, alpha=235,
                   glyph_color=(245, 245, 240) if i % 2 == 0 else (20, 20, 24))
    # starburst corner (slow spin)
    rot = (t - s0) * 0.8
    dark_bg = kind in ("card", "lookup", "icon", "listicle")
    col = (214, 40, 57)
    R.starburst(img, (W - 130, int(H * 0.30)), 52 + int(4 * math.sin(t * 2.2)), rot, col)
    # mono label chip bottom-left
    chip = ["no script", "one take", "on beat", "raw cut", "dropsoon"][int(t * 2) % 5]
    f_c = R.mono(34, bold=True)
    bb = d.textbbox((0, 0), chip, font=f_c)
    cw = bb[2] - bb[0]
    d.rounded_rectangle([96, int(H * 0.565) - 26, 96 + cw + 36, int(H * 0.565) + 34], radius=12, fill=(16, 16, 18, 200))
    d.text((114, int(H * 0.565) - 22), chip, font=f_c, fill=VOLT + (255,))
    # volt connector line + node
    d.line([96, int(H * 0.565) + 48, 96 + cw + 36, int(H * 0.565) + 48], fill=VOLT + (190,), width=3)
    d.rectangle([96 + cw + 36 - 4, int(H * 0.565) + 44, 96 + cw + 36 + 4, int(H * 0.565) + 52], fill=VOLT + (255,))
    # heart accent
    R.heart_glyph(img, (W - 170, int(H * 0.52)), 26)


def _compose(fi):
    t = fi / FPS
    idx = scene_at(t)
    s0, canvas, kind, lyric, headline, sub = SCENES[idx]
    t1 = SCENES[idx + 1][0] if idx + 1 < len(SCENES) else DUR
    ent = entrance(s0, t)
    ex = exit_scale(s0, t, t1)
    beat_bounce = 1.0
    # camera: scale bounce on entrance + punch on beats (R4/R5)
    for b in BEATS:
        if abs(t - b) < 0.10:
            beat_bounce = 1.03
    zoom = (1.0 + 0.06 * ent) * beat_bounce * ex

    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    if canvas == "paper":
        img.alpha_composite(R.paper_white(W, H))
    elif canvas == "navy":
        img.alpha_composite(R.navy_scene(W, H, ghost="WELCOME" if kind == "card" else None))
    elif canvas == "red":
        img.alpha_composite(R.red_scene(W, H, ghost="the party" if kind == "icon" else None))
    elif canvas == "green":
        img.alpha_composite(R.green_scene(W, H))
    elif canvas == "black":
        img.alpha_composite(R.black_halftone(W, H, quote="everybody dies at the end"))

    d = ImageDraw.Draw(img, "RGBA")

    # ---- scene kind composition ----
    if kind == "hero":
        # polaroid insert (real frame) instead of fake cutout; rotated volt pill + serif lockup
        fr = mv_frame(1.0)
        sc = R.spring_scale(max(0.0, t - s0 - 0.06), 0.36)
        if sc > 0.01:
            drift = math.sin((t - s0) * 2 * math.pi * 0.9) * 6
            paste_person(img, (W / 2 - 120, H * 0.34 + drift), int(460 * sc), "stair", rot=2)
            R.polaroid(img, fr, (W / 2 + 300, H * 0.44), int(280 * sc), rot=-6)
        R.volt_pill(img, (W / 2 + 250, H * 0.155), "FRESH", R.montserrat(46, 900), rot=-9)
        f_m = R.mono(38); f_s = R.playfair(150, 900)
        d.text((W / 2 - 300, H * 0.545), "you pressed", font=f_m, fill=(40, 40, 44, 235))
        bb = d.textbbox((0, 0), "WELCOME", font=f_s)
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.585), "WELCOME", font=f_s, fill=(20, 20, 22, 255))
        R.pixel_dots(img, 10, (60, H * 0.76, W - 60, H * 0.82), seed=5, size=12)
        R.bracket_corners(img, (W / 2 - 320, int(H * 0.575), W / 2 + 320, int(H * 0.71)))
        ENGINE_LOG.append((fi, "pil", "hero:polaroid+volt-pill+serif"))
    elif kind == "card":
        sc = entrance(s0, t, 0.40)
        if sc > 0.01:
            card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            R.phone_card(card, (W / 2, H * 0.44), 760, 1000)
            f_g = R.montserrat(84, 900)
            bb = ImageDraw.Draw(card).textbbox((0, 0), "GROWING", font=f_g)
            ImageDraw.Draw(card).text(((W - bb[2] + bb[0]) / 2, H * 0.30), "GROWING", font=f_g, fill=(235, 240, 255, 255))
            bob = math.sin((t - s0) * 2 * math.pi * 1.2) * 8
            R.duck_avatar(card, (W / 2 + 240, H * 0.26 + bob), 52)
            dy = int((1 - sc) * 260)
            card = card.transform(card.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy), resample=Image.BICUBIC)
            card.putalpha(card.getchannel("A").point(lambda a: int(a * min(1, sc * 1.6))))
            img.alpha_composite(card)
            # in-scene sub-motion: toggle knob slides (no static holds)
            prog = min(1.0, (t - s0) / (t1 - s0))
            kx = W / 2 - 0.28 * W + int(prog * (0.30 * W))
            d.ellipse([kx - 16, int(H * 0.44 + 300) - 16, kx + 16, int(H * 0.44 + 300) + 16], fill=VOLT + (255,))
        ENGINE_LOG.append((fi, "pil", "navy-phone-card-slide+toggle"))
    elif kind == "but":
        f_big = R.playfair(220, 900)
        bb = d.textbbox((0, 0), "But", font=f_big)
        d.text(((W - bb[2] + bb[0]) / 2 - 240, H * 0.175), "But", font=f_big, fill=(26, 26, 30, 255))
        sc = R.spring_scale(max(0.0, t - s0 - 0.08), 0.30)
        if sc > 0.01:
            R.heart_glyph(img, (W / 2 - 210, int(H * 0.44)), int(46 * sc))
        paste_person(img, (W / 2 + 290, H * 0.40), 480, "stair", rot=3)
        f_m = R.mono(40, bold=True)
        d.text((W / 2 - 240, H * 0.50), "everybody dies", font=f_m, fill=(30, 30, 34, 230))
        R.bracket_corners(img, (W / 2 - 240, int(H * 0.49), W / 2 + 200, int(H * 0.60)))
        R.draw_caption_line(img, LYRICS[5:9], t, CAP_Y)
        ENGINE_LOG.append((fi, "pil", "but-split+person"))
        return img
    elif kind == "icon":
        # 2x2 collage (target grammar: multi-panel + center badge)
        gap = 10
        m = 90
        cw, ch = (W - 2 * m - gap) // 2, int((H * 0.62 - gap) // 2)
        boxes = [(m, int(H * 0.16), m + cw, int(H * 0.16) + ch),
                 (m + cw + gap, int(H * 0.16), W - m, int(H * 0.16) + ch),
                 (m, int(H * 0.16) + ch + gap, m + cw, int(H * 0.16) + 2 * ch + gap),
                 (m + cw + gap, int(H * 0.16) + ch + gap, W - m, int(H * 0.16) + 2 * ch + gap)]
        sc = R.spring_scale(max(0.0, t - s0 - 0.05), 0.34)

        def p1(sub, w, h):
            ImageDraw.Draw(sub).text((w * 0.12, h * 0.12), "move", font=R.mono(int(w * 0.11)), fill=(30, 30, 34, 235))
            ImageDraw.Draw(sub).text((w * 0.12, h * 0.34), "your body", font=R.mono(int(w * 0.11)), fill=(30, 30, 34, 150))

        def p2(sub, w, h):
            dd = ImageDraw.Draw(sub, "RGBA")
            R.duck_avatar(sub, (int(w * 0.72), int(h * 0.30)), int(w * 0.10))
            dd.rounded_rectangle([w * 0.1, h * 0.62, w * 0.9, h * 0.74], radius=16, fill=(240, 240, 245, 60))

        def p3(sub, w, h):
            R.red_arrow_icon(sub, (int(w * 0.5), int(h * 0.5)), int(w * 0.16))

        def p4(sub, w, h):
            dd = ImageDraw.Draw(sub, "RGBA")
            R.heart_glyph(sub, (int(w * 0.5), int(h * 0.46)), int(w * 0.11))
            dd.text((w * 0.16, h * 0.74), "on beat", font=R.mono(int(w * 0.10)), fill=(120, 120, 126, 220))

        if sc > 0.01:
            for box, ck, fn in zip(boxes, ["paper", "navy", "red", "paper"], [p1, p2, p3, p4]):
                s = min(1.0, sc * 1.15)
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                bw, bh = int((box[2] - box[0]) * s), int((box[3] - box[1]) * s)
                tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                R.mini_panel(tmp, box, ck, fn)
                panel = tmp.crop(box).resize((bw, bh)) if s < 1.0 else tmp.crop(box)
                img.alpha_composite(panel, (int(cx - bw / 2), int(cy - bh / 2)))
            # center serif badge at seam (target signature)
            bx, by = W // 2, int(H * 0.16) + ch + gap // 2
            d.ellipse([bx - 46, by - 46, bx + 46, by + 46], fill=VOLT + (255,))
            d.text((bx - 20, by - 34), "A", font=R.playfair(58, 900), fill=(20, 20, 22, 255))
        ENGINE_LOG.append((fi, "pil", "red-2x2-collage+badge"))
        return img
    elif kind == "listicle":
        f_l = R.montserrat(88, 900)
        items = [("01", "the party"), ("02", "everybody"), ("03", "dies at"), ("04", "the end")]
        active = int((t - s0) / 0.22)
        R.listicle_bars(img, 200, int(H * 0.34), items, f_l, active_idx=active, bar_w=520, gap=110)
        ENGINE_LOG.append((fi, "pil", "listicle-bars"))
        return img
    elif kind == "orb":
        R.orb_glow(img, (W / 2 - 180, H * 0.40), 170, t - s0)
        R.pixel_dots(img, 14, (80, H * 0.12, W - 80, H * 0.85), seed=8, size=10)
        bob = math.sin((t - s0) * 2 * math.pi * 1.0) * 10
        R.duck_avatar(img, (W / 2 + 330, int(H * 0.30 + bob)), 44)
        paste_person(img, (W / 2 + 280, H * 0.56), 420, "stair", rot=-3)
        val = 200 + int((t - s0) * 90)
        R.counter_odometer(img, (W / 2 + 250, H * 0.74), val, "beats counted", R.montserrat(84, 900), R.mono(34))
        f_m = R.mono(46, bold=True)
        txt = "the beat drops here"
        bb = d.textbbox((0, 0), txt, font=f_m)
        d.rounded_rectangle([(W - bb[2] + bb[0]) / 2 - 20 - 200, H * 0.84 - 12, (W - bb[2] + bb[0]) / 2 + bb[2] - bb[0] + 20 - 200, H * 0.84 + 46], radius=14, fill=(16, 16, 18, 160))
        d.text(((W - bb[2] + bb[0]) / 2 - 200, H * 0.84), txt, font=f_m, fill=(245, 255, 210, 240))
        ENGINE_LOG.append((fi, "pil", "green-orb+counter+person"))
        return img
    elif kind == "matters":
        gap = 10
        m = 80
        top = int(H * 0.14)
        ch = int((H * 0.66 - gap) // 2)
        cw = (W - 2 * m - gap) // 2
        boxes = [(m, top, m + cw, top + ch), (m + cw + gap, top, W - m, top + ch),
                 (m, top + ch + gap, m + cw, top + 2 * ch + gap), (m + cw + gap, top + ch + gap, W - m, top + 2 * ch + gap)]

        def q1(sub, w, h):
            R.pixel_word(sub, (w / 2, h / 2), "dies", R.montserrat(int(h * 0.42), 900), chunk=3)
            ImageDraw.Draw(sub).text((w * 0.10, h * 0.80), "AT THE END", font=R.playfair(int(h * 0.16), 900), fill=(18, 18, 20, 235))

        def q2(sub, w, h):
            dd = ImageDraw.Draw(sub, "RGBA")
            dd.text((w * 0.10, h * 0.10), "the party", font=R.mono(int(h * 0.10)), fill=(40, 40, 44, 220))
            R.orb_glow(sub, (w / 2, h * 0.55), int(h * 0.26), t - s0)

        def q3(sub, w, h):
            paste_person(sub, (w * 0.5, h * 0.52), int(h * 0.78), "stair", rot=-2)

        def q4(sub, w, h):
            dd = ImageDraw.Draw(sub, "RGBA")
            R.heart_glyph(sub, (int(w * 0.5), int(h * 0.42)), int(w * 0.10))
            dd.text((w * 0.14, h * 0.72), "on beat", font=R.mono(int(h * 0.10)), fill=(110, 110, 116, 230))

        sc2 = R.spring_scale(max(0.0, t - s0 - 0.05), 0.34)
        if sc2 > 0.01:
            for box, ck, fn in zip(boxes, ["paper", "paper", "navy", "red"], [q1, q2, q3, q4]):
                tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                R.mini_panel(tmp, box, ck, fn)
                img.alpha_composite(tmp.crop(box))
            bx, by = W // 2, top + ch + gap // 2
            d.ellipse([bx - 40, by - 40, bx + 40, by + 40], fill=VOLT + (255,))
            d.text((bx - 17, by - 29), "A", font=R.playfair(50, 900), fill=(20, 20, 22, 255))
        ENGINE_LOG.append((fi, "pil", "matters-2x2-collage+person"))
        return img
    elif kind == "lookup":
        R.pixel_word(img, (W / 2, H * 0.26), "WALK", R.montserrat(150, 900), color=(245, 245, 248), chunk=4)
        # volt pill BEHIND keyword NOT ME + outline style
        f_g = R.playfair(118, 900)
        bb2 = d.textbbox((0, 0), "NOT ME", font=f_g)
        w2 = bb2[2] - bb2[0]
        x0 = (W - w2) / 2; y0 = H * 0.375
        d.rounded_rectangle([x0 - 44, y0 + bb2[1] - 26, x0 + w2 + 44, y0 + bb2[3] + 30], radius=18, fill=VOLT + (235,))
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            d.text((x0 + ox, y0 + oy), "NOT ME", font=f_g, fill=(235, 235, 245, 200))
        paste_person(img, (W / 2 + 280, H * 0.62), 430, "stair", rot=-2)
        R.draw_caption_line(img, LYRICS[13:15], t, CAP_Y)
        ENGINE_LOG.append((fi, "pil", "navy-pixel-word+pill+person"))
        return img
    elif kind == "constel":
        prog = R.ease_out_cubic((t - s0) / 0.30)
        R.constellation(img, (W / 2, H * 0.42), 9, 260, prog)
        paste_person(img, (W / 2 + 330, H * 0.62), 400, "stair", rot=2)
        f_m = R.mono(42, bold=True)
        txt = "what comes next"
        bb = d.textbbox((0, 0), txt, font=f_m)
        d.rounded_rectangle([(W - bb[2] + bb[0]) / 2 - 22, H * 0.70 - 14, (W - bb[2] + bb[0]) / 2 + bb[2] - bb[0] + 22, H * 0.70 + 44], radius=12, fill=(16, 16, 18, 190))
        d.text(((W - bb[2] + bb[0]) / 2, H * 0.70), txt, font=f_m, fill=(245, 245, 240, 245))
        ENGINE_LOG.append((fi, "pil", "constellation-draw"))
        return img
    elif kind == "polaroid":
        fr = mv_frame(12.5)
        sc = R.spring_scale(max(0.0, t - s0 - 0.06), 0.36)
        if sc > 0.01:
            R.polaroid(img, fr, (W / 2, H * 0.42), int(500 * sc), rot=3)
            fr2 = mv_frame(24.0)
            R.polaroid(img, fr2, (W / 2 - 60, H * 0.55), int(300 * sc), rot=-7)
        R.bracket_corners(img, (170, int(H * 0.60), W - 170, int(H * 0.80)))
        f_m = R.mono(40, bold=True)
        d.text((210, int(H * 0.805)), "raw — stairwell 12.5s", font=f_m, fill=(255, 170, 160, 235))
        ENGINE_LOG.append((fi, "pil", "polaroid-cascade"))
        return img
    elif kind == "m1":
        paste_m1(img, t)
        R.pixel_dots(img, 8, (100, int(H * 0.14), W - 100, int(H * 0.30)), seed=17, size=10)
        f_m = R.mono(40)
        d.text((W / 2 - 150, H * 0.16), "extruded 3D type", font=f_m, fill=(60, 60, 66, 235))
        fr = mv_frame(1.0)
        sc = R.spring_scale(max(0.0, t - s0 - 0.06), 0.36)
        if sc > 0.01 and t < DROP:
            R.polaroid(img, fr, (W / 2 + 300, H * 0.66), int(260 * sc), rot=6)
        ENGINE_LOG.append((fi, "bpy-alpha-seq", "M1-type-slam"))
        return img
    elif kind == "endcard":
        # LB10 clean end card: loop echo ghost + family pill; NO brand/URL; underline removed
        f_g = R.playfair(150, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.38
        d.text((ox + 14, oy + 12), "WELCOME", font=f_g, fill=(180, 180, 186, 30))  # ghost echo same baseline
        d.text((ox, oy), "WELCOME", font=f_g, fill=(20, 20, 22, 255))
        sc = R.spring_scale(max(0.0, t - s0 - 0.12), 0.34)
        if sc > 0.01:
            R.volt_pill(img, (W / 2, H * 0.55), "to the party", R.montserrat(52, 900), rot=0)
            paste_person(img, (W / 2 + 330, H * 0.72), 330, "stair", rot=2)
        R.pixel_dots(img, 8, (100, int(H * 0.62), W - 100, int(H * 0.80)), seed=13, size=10)
        ENGINE_LOG.append((fi, "pil", "endcard-loop-echo"))
        return img

    # shared caption for scenes without dedicated caption draw
    if lyric:
        # single consistent lower-third y (CAP_Y)
        if kind == "hero":
            R.draw_caption_line(img, LYRICS[0:3], t, CAP_Y)
        elif kind == "card":
            R.draw_caption_line(img, LYRICS[3:6], t, CAP_Y)
        ENGINE_LOG.append((fi, "pil", f"karaoke:{kind}"))

    return img

def compose(fi):
    img = _compose(fi)
    t = fi / FPS
    idx = scene_at(t)
    s0, canvas, kind, lyric, headline, sub = SCENES[idx]
    if kind not in ("m1", "endcard"):
        density_pass(img, t, s0, kind)
    # camera zoom (designed bounce)
    t1 = SCENES[idx + 1][0] if idx + 1 < len(SCENES) else DUR
    ent = entrance(s0, t)
    ex = exit_scale(s0, t, t1)
    beat_bounce = 1.0
    for b in BEATS:
        if abs(t - b) < 0.10:
            beat_bounce = 1.03
    zoom = (1.0 + 0.06 * ent) * beat_bounce * ex
    if abs(zoom - 1.0) > 0.002:
        zw, zh = int(W * zoom), int(H * zoom)
        big = img.resize((zw, zh), Image.BILINEAR)
        img = big.crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    return img


# ---------------- render loop ----------------
if __name__ == "__main__":
    a = sys.argv
    START = int(a[a.index("--start") + 1]) if "--start" in a else 0
    END = int(a[a.index("--end") + 1]) if "--end" in a else N - 1
    for fi in range(START, END + 1):
        img = compose(fi).convert("RGB")
        img.save(f"{FRAMES}/r_{fi:05d}.jpg", quality=90)
        if fi % 60 == 0:
            print(f"frame {fi}/{END}", flush=True)
    json.dump({"beats": BEATS, "drop": DROP, "scenes": [(s[0], s[1], s[2]) for s in SCENES]},
              open(f"{SCRATCH}/replica_beats.json", "w"), indent=1)
    print("FRAMES DONE", START, END)
