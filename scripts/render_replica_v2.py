#!/usr/bin/env python3
"""REPLICA v2 — STRICT STRUCTURAL CLONE of the target grammar (method swap after R2 stop-loss):
EVERY frame = full-bleed 2x2 designed-panel grid, black gutters, center serif badge,
people/photo cut-outs edge-touched in quadrants, pixel/mono display mix, thin volt highlights
BEHIND keywords, node-graph/app-icon sticker voice, stagger 40-80ms per quadrant.
Captions karaoke v2 = one layer among many (R0). M1 3D slam accent at the drop (R9).
End card exception: clean single canvas loop-echo + family pill (AS3/LB10)."""
import os, sys, math, wave, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/components")
import renderlib as R
from renderlib import VOLT, INK

W, H, FPS, DUR = 1080, 1920, 30, 12.0
N = int(FPS * DUR)
SCRATCH = "/tmp/my-project/p21work/scratch"
FRAMES = f"{SCRATCH}/replica_frames"
MV = "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
os.makedirs(FRAMES, exist_ok=True)

sys.path.insert(0, "/home/z/my-project/download/edit-master-skill/scripts")
from render_replica_12s import beat_grid, clean_cutout, paste_person, mv_frame, LYRICS

BEATS, ENERGY = beat_grid(f"{SCRATCH}/target_audio.wav", DUR + 0.5)
cand = [b for b in BEATS if 8.5 <= b <= 11.5]
DROP = max(cand, key=lambda b: ENERGY[int(b * 100)]) if cand else 10.37
print("DROP", DROP)

PERSON = clean_cutout("stair11_isnet")
BUILDING = clean_cutout("building25_isnet")
CAR = clean_cutout("car_isnet")

M1_SEQ = f"{SCRATCH}/m1_seq"
M1_FRAMES = 84

def paste_m1(img, t):
    f = int((t - DROP) * FPS)
    if f < 0 or f >= M1_FRAMES:
        return
    p = f"{M1_SEQ}/f_{f:04d}.png"
    if os.path.exists(p):
        img.alpha_composite(Image.open(p).convert("RGBA").resize((1080, 1920)))

# ---------------- quadrant variants ----------------
def q_person(img, box, t, ent, which="stair", label=None):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    hh = int(h * (0.60 + 0.06 * math.sin(t * 2.1)))
    paste_person(img, (x0 + w / 2, y0 + h * 0.46), hh, which,
                 rot=1.5 * math.sin(t * 0.9))
    if label:
        d = ImageDraw.Draw(img, "RGBA")
        f = R.mono(int(w * 0.055), bold=True)
        bb = d.textbbox((0, 0), label, font=f)
        d.text((x0 + w * 0.09, y0 + h * 0.80), label, font=f, fill=(30, 30, 34, 230))
        lw = bb[2] - bb[0]
        d.rounded_rectangle([x0 + w * 0.09 - 6, y0 + h * 0.80 + bb[3] + 6, x0 + w * 0.09 + lw + 6, y0 + h * 0.80 + bb[3] + 12], radius=3, fill=VOLT + (230,))


def q_pixel_word(img, box, t, ent, word, light=False, highlight=None):
    """chunky display word + THIN volt highlight BEHIND a keyword (not standalone pill)"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    col = (245, 245, 248) if light else (24, 24, 28)
    size = int(h * 0.16)
    dd = ImageDraw.Draw(img, "RGBA")
    while dd.textbbox((0, 0), word, font=R.montserrat(size, 900))[2] > w * 0.80 and size > 40:
        size -= 8
    d = ImageDraw.Draw(img, "RGBA")
    if highlight:
        f_h = R.montserrat(size, 900)
        bb = d.textbbox((0, 0), highlight, font=f_h)
        hx = x0 + w * 0.09
        hy = y0 + h * 0.62
        d.rounded_rectangle([hx - 8, hy + bb[1] - 4, hx + (bb[2] - bb[0]) + 8, hy + bb[3] + 6], radius=6, fill=VOLT + (200,))
        R.pixel_word(img, (x0 + w / 2, y0 + h * 0.34), word, R.montserrat(size, 900), color=col, chunk=3)
        d.text((hx, hy), highlight, font=f_h, fill=col + (255,))
    else:
        R.pixel_word(img, (x0 + w / 2, y0 + h * 0.40), word, R.montserrat(size, 900), color=col, chunk=3)
    f_m = R.mono(int(w * 0.05))
    d.text((x0 + w * 0.09, y0 + h * 0.82), "everybody dies at the end"[:24], font=f_m, fill=((230, 230, 240, 190) if light else (60, 60, 66, 200)))


def q_constellation(img, box, t, ent, light=False):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    R.constellation(img, (x0 + w / 2, y0 + h / 2), 9, int(min(w, h) * 0.30), R.ease_out_cubic(ent / 0.3),
                    color=(235, 235, 240) if light else (26, 26, 30))


def q_orb(img, box, t, ent):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    R.orb_glow(img, (x0 + w / 2, y0 + h / 2), int(min(w, h) * 0.24), t - int(t * 2) * 0.5 + t * 0)
    d = ImageDraw.Draw(img, "RGBA")
    f = R.mono(int(w * 0.055), bold=True)
    d.text((x0 + w * 0.09, y0 + h * 0.82), "the beat drops", font=f, fill=(250, 255, 220, 235))


def q_iconrow(img, box, t, ent, light=False):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d = ImageDraw.Draw(img, "RGBA")
    n = 4
    for i in range(n):
        cx = x0 + w * (0.20 + 0.20 * i)
        cy = y0 + h * 0.40
        R.app_icon(img, (cx, cy), int(w * 0.075), glyph=["✦", "→", "♪", "A"][i],
                   fill=(20, 20, 24) if (i % 2 == 0) != light else VOLT, alpha=235,
                   glyph_color=(245, 245, 240) if (i % 2 == 0) != light else (20, 20, 24))
    f = R.mono(int(w * 0.052), bold=True)
    d.text((x0 + w * 0.09, y0 + h * 0.60), "just AI agents", font=f, fill=(240, 240, 246, 235) if light else (30, 30, 34, 230))


def q_photo(img, box, t, ent, which="building", ts=24.0):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    src = BUILDING if which == "building" else CAR
    hh = int(h * (0.52 + 0.02 * math.sin(t * 1.7)))
    ww = int(src.width * hh / src.height)
    fg = src.resize((ww, hh), Image.LANCZOS).rotate(2.0 * math.sin(t * 0.7), expand=True, resample=Image.BICUBIC)
    img.alpha_composite(fg, (int(x0 + w / 2 - fg.width / 2), int(y0 + h * 0.44 - fg.height / 2)))
    d = ImageDraw.Draw(img, "RGBA")
    f = R.mono(int(w * 0.05))
    d.text((x0 + w * 0.09, y0 + h * 0.80), "raw — 12.5s", font=f, fill=(250, 170, 160, 235))


def q_annotation(img, box, t, ent, lines, hi_word=None, light=False):
    """mono stack; ONE word gets thin volt highlight BEHIND it"""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d = ImageDraw.Draw(img, "RGBA")
    f = R.montserrat(int(w * 0.085), 900)
    y = y0 + h * 0.28
    reveal = min(len(lines), int(ent / 0.14) + 1)
    for i, ln in enumerate(lines[:reveal]):
        if hi_word and hi_word in ln and i == reveal - 1:
            pre, post = ln.split(hi_word, 1)
            x = x0 + w * 0.09
            for part, hl in ((pre, False), (hi_word, True), (post, False)):
                bb = d.textbbox((0, 0), part, font=f)
                if hl:
                    d.rounded_rectangle([x - 6, y + bb[1] - 2, x + (bb[2] - bb[0]) + 6, y + bb[3] + 4], radius=6, fill=VOLT + (205,))
                d.text((x, y), part, font=f, fill=(20, 20, 24, 255) if not light else (18, 18, 22, 255))
                x += bb[2] - bb[0]
        else:
            d.text((x0 + w * 0.09, y), ln, font=f, fill=(45, 45, 50, 235) if not light else (235, 235, 242, 235))
        y += int(h * 0.115)


def q_glasscard(img, box, t, ent, title="You are Growing"):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d = ImageDraw.Draw(img, "RGBA")
    cw, ch = w * 0.78, h * 0.42
    cx, cy = x0 + w / 2, y0 + h * 0.42
    d.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2], radius=int(cw * 0.10), fill=(200, 212, 245, 70), outline=(240, 244, 255, 90), width=2)
    f = R.montserrat(int(w * 0.075), 900)
    bb = d.textbbox((0, 0), title, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2, cy - ch / 2 + int(ch * 0.16)), title, font=f, fill=(232, 238, 252, 245))
    prog = min(1.0, ent / 0.9)
    d.rounded_rectangle([cx - cw * 0.30, cy + ch * 0.22, cx + cw * 0.02, cy + ch * 0.34], radius=20, fill=(90, 110, 190, 255))
    kx = cx - cw * 0.30 + int(prog * cw * 0.32)
    d.ellipse([kx - 14, cy + ch * 0.22 - 6, kx + 14, cy + ch * 0.34 + 6], fill=VOLT + (255,))


def q_counter(img, box, t, ent, value, label, prefix="$", light=False):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if light:
        d3 = ImageDraw.Draw(img, "RGBA")
        txt = f"{prefix}{value:,}"
        f_big = R.montserrat(int(w * 0.11), 900)
        bb = d3.textbbox((0, 0), txt, font=f_big)
        d3.text((x0 + w / 2 - (bb[2] - bb[0]) / 2, y0 + h * 0.40 - bb[1]), txt, font=f_big, fill=(250, 244, 240, 255))
        f_small = R.mono(int(w * 0.05))
        bb2 = d3.textbbox((0, 0), label, font=f_small)
        d3.text((x0 + w / 2 - (bb2[2] - bb2[0]) / 2, y0 + h * 0.58), label, font=f_small, fill=(255, 190, 180, 240))
        d3.rounded_rectangle([x0 + w / 2 - 130, y0 + h * 0.66, x0 + w / 2 + 130, y0 + h * 0.674], radius=4, fill=VOLT + (235,))
    else:
        R.counter_odometer(img, (x0 + w / 2, y0 + h * 0.44), value, label, R.montserrat(int(w * 0.11), 900), R.mono(int(w * 0.05)), prefix=prefix)


def q_phone(img, box, t, ent):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    sc = R.spring_scale(ent, 0.36)
    R.phone_card(img, (x0 + w / 2, y0 + h * 0.42), int(w * 0.72 * sc), int(h * 0.56 * sc))
    f_g = R.montserrat(int(w * 0.085 * max(0.5, sc)), 900)
    d2 = ImageDraw.Draw(img, "RGBA")
    bb = d2.textbbox((0, 0), "GROWING", font=f_g)
    d2.text((x0 + w / 2 - (bb[2] - bb[0]) / 2, y0 + h * 0.30), "GROWING", font=f_g, fill=(235, 240, 255, 255))

# ---------------- grid assembly ----------------
GUT = 8
def grid_box(qi):
    cw = (W - GUT) // 2
    ch = (H - GUT) // 2
    x0 = 0 if qi % 2 == 0 else cw + GUT
    y0 = 0 if qi < 2 else ch + GUT
    return (x0, y0, x0 + cw, y0 + ch)

CANVASES = {}
def canvas_for(kind):
    if kind not in CANVASES:
        if kind == "paper":
            CANVASES[kind] = R.paper_white(W // 2, H // 2)
        elif kind == "navy":
            CANVASES[kind] = R.navy_scene(W // 2, H // 2)
        elif kind == "red":
            CANVASES[kind] = R.red_scene(W // 2, H // 2)
        elif kind == "green":
            CANVASES[kind] = R.green_scene(W // 2, H // 2)
        else:
            CANVASES[kind] = R.black_halftone(W // 2, H // 2)
    return CANVASES[kind]

# per-beat: (t0, canvas_kinds[q1..q4], variants[q1..q4], badge_letter)
# variants: ("person","stair") / ("pixel",word,light,highlight) / ("constel",light) / ("orb",)
#           ("icons",light) / ("photo","building"|"car",ts) / ("annot",[lines],hi,light)
#           ("glass",title) / ("counter",val0,label) / ("phone",)
SCENES_V2 = [
    (0.00, ["paper", "navy", "paper", "paper"],
     [("annot", ["you built a", "WELCOME", "here"], "WELCOME", False),
      ("glass",), ("person", "stair"), ("pixel", "product", False, None)], "A"),
    (1.00, ["navy", "paper", "paper", "green"],
     [("phone",), ("annot", ["you are", "GROWING"], "GROWING", False),
      ("person", "stair"), ("orb",)], "W"),
    (2.00, ["paper", "red", "black", "paper"],
     [("pixel", "But", False, "party"), ("person", "stair"), ("constel", False), ("icons", False)], "E"),
    (2.90, ["red", "paper", "navy", "black"],
     [("counter", 1000000, "on the line"), ("annot", ["does anyone get", "it", "value difference"], "value", False),
      ("pixel", "why", True, None), ("photo", "building", 24.0)], "L"),
    (3.90, ["black", "paper", "paper", "navy"],
     [("annot", ["everybody", "dies at", "the end"], "dies", False), ("constel", False),
      ("person", "stair"), ("counter", 14, "beats counted")], "C"),
    (4.90, ["green", "navy", "paper", "paper"],
     [("orb",), ("icons", True), ("pixel", "beat", False, "drop"), ("photo", "car", 1.0)], "O"),
    (5.90, ["paper", "black", "navy", "red"],
     [("annot", ["lets show the", "world why it", "matters"], "why it", False), ("constel", False),
      ("person", "stair"), ("counter", 48000, "frames rendered")], "M"),
    (6.90, ["navy", "paper", "red", "paper"],
     [("pixel", "WALK", True, None), ("annot", ["I think you", "walk NOT me"], "NOT", False),
      ("person", "stair"), ("glass",)], "E"),
    (7.90, ["paper", "green", "paper", "navy"],
     [("constel", False), ("orb",), ("annot", ["what comes", "next hits"], "next", False), ("icons", True)], "W"),
    (8.80, ["red", "paper", "black", "paper"],
     [("photo", "car", 1.0), ("annot", ["the scene", "raw vs graded"], "raw", False),
      ("pixel", "homicide", False, None), ("person", "stair")], "L"),
]

CAP_WINDOWS = [(0, 3), (3, 6), (6, 9), (9, 12)]  # lyric thirds -> karaoke line rotation
CAP_LINES = [LYRICS[0:4], LYRICS[4:9], LYRICS[9:15], LYRICS[15:19]]

def compose(fi):
    t = fi / FPS
    idx = 0
    for i, sc in enumerate(SCENES_V2):
        if t >= sc[0]:
            idx = i
    s0, kinds, variants, letter = SCENES_V2[idx]
    t1 = SCENES_V2[idx + 1][0] if idx + 1 < len(SCENES_V2) else (DROP - 0.35)
    img = Image.new("RGBA", (W, H), (5, 5, 6, 255))

    if t >= DROP - 0.35 and t < DROP + 0.55:
        # M1 window: single designed paper canvas + 3D slam + caption
        img.alpha_composite(R.paper_white(W, H))
        paste_m1(img, t)
        if t < DROP:
            sc = R.spring_scale(max(0.0, t - (DROP - 0.35)), 0.30)
            if sc > 0.01:
                paste_person(img, (W / 2 + 320, H * 0.70), int(360 * sc), "stair", rot=2)
        d = ImageDraw.Draw(img, "RGBA")
        f = R.mono(40)
        d.text((W / 2 - 150, H * 0.13), "extruded 3D type", font=f, fill=(60, 60, 66, 235))
        R.draw_caption_line(img, CAP_LINES[-1], t, int(H * 0.885))
        return img.convert("RGB")

    if t >= DROP + 0.55:
        # clean end card (LB10/AS3): loop echo + family pill, NO brand
        img.alpha_composite(R.paper_white(W, H))
        d = ImageDraw.Draw(img, "RGBA")
        f_g = R.playfair(150, 900)
        bb = d.textbbox((0, 0), "WELCOME", font=f_g)
        ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.36
        d.text((ox + 12, oy + 10), "WELCOME", font=f_g, fill=(180, 180, 186, 30))
        d.text((ox, oy), "WELCOME", font=f_g, fill=(20, 20, 22, 255))
        sc = R.spring_scale(max(0.0, t - (DROP + 0.55) - 0.10), 0.34)
        if sc > 0.01:
            R.volt_pill(img, (W / 2, H * 0.54), "to the party", R.montserrat(52, 900), rot=0)
        R.pixel_dots(img, 9, (100, int(H * 0.64), W - 100, int(H * 0.80)), seed=int(t * 6) + 3, size=10)
        R.draw_caption_line(img, CAP_LINES[-1], t, int(H * 0.885))
        return img.convert("RGB")

    # ---- 2x2 grid ----
    ent = t - s0
    for qi in range(4):
        x0, y0, x1, y1 = grid_box(qi)
        kind = kinds[qi]
        sub = canvas_for(kind)
        # quadrant entrance stagger 40-80ms + micro zoom
        q_ent = max(0.0, ent - qi * 0.06)
        sc = 0.74 + 0.26 * R.spring_scale(q_ent, 0.30)  # floor: frame-1 composed, pop-in to 1.0
        if sc <= 0.01:
            continue
        v = variants[qi]
        kind_v = v[0]
        tmp = sub.copy()
        # quadrant content
        if kind_v == "person":
            q_person(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, which=v[1], label="on beat" if qi == 2 else None)
        elif kind_v == "pixel":
            q_pixel_word(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, v[1], light=v[2], highlight=v[3] if len(v) > 3 else None)
        elif kind_v == "constel":
            q_constellation(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, light=(kind == "navy" or kind == "black"))
        elif kind_v == "orb":
            q_orb(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent)
        elif kind_v == "icons":
            q_iconrow(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, light=(kind == "navy"))
        elif kind_v == "photo":
            q_photo(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, which=v[1])
        elif kind_v == "annot":
            q_annotation(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, v[1], hi_word=v[2] if len(v) > 2 else None, light=(kind == "navy" or kind == "black" or kind == "red"))
        elif kind_v == "glass":
            q_glasscard(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent)
        elif kind_v == "counter":
            val0 = v[1]
            val = val0 + int(q_ent * 90)
            q_counter(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent, val, v[2],
                      prefix="" if ("beats" in str(v[2]) or "frames" in str(v[2])) else "$",
                      light=(kind in ("red", "black")))
        elif kind_v == "phone":
            q_phone(tmp, (0, 0, x1 - x0, y1 - y0), t + qi, q_ent)
        # scale-in quadrant
        if sc < 1.0:
            qcw, qch = x1 - x0, y1 - y0
            sw, sh = max(1, int(qcw * sc)), max(1, int(qch * sc))
            small = tmp.resize((sw, sh))
            tmp = Image.new("RGBA", (qcw, qch), (5, 5, 6, 255))
            tmp.alpha_composite(small, ((qcw - sw) // 2, (qch - sh) // 2))
        img.alpha_composite(tmp, (x0, y0))

    # gutter + center badge (straddles seams)
    d = ImageDraw.Draw(img, "RGBA")
    cw, ch = (W - GUT) // 2, (H - GUT) // 2
    d.rectangle([cw, 0, cw + GUT, H], fill=(5, 5, 6, 255))
    d.rectangle([0, ch, W, ch + GUT], fill=(5, 5, 6, 255))
    bx, by = W // 2, H // 2
    d.ellipse([bx - 52, by - 52, bx + 52, by + 52], fill=VOLT + (255,))
    f_b = R.playfair(64, 900)
    bb = d.textbbox((0, 0), letter, font=f_b)
    d.text((bx - (bb[2] - bb[0]) / 2 - bb[0], by - (bb[3] - bb[1]) / 2 - bb[1]), letter, font=f_b, fill=(20, 20, 22, 255))

    # captions karaoke v2 (one layer among many)
    ci = min(3, int(t // 3))
    R.draw_caption_line(img, CAP_LINES[ci], t, int(H * 0.885))
    return img.convert("RGB")

if __name__ == "__main__":
    a = sys.argv
    START = int(a[a.index("--start") + 1]) if "--start" in a else 0
    END = int(a[a.index("--end") + 1]) if "--end" in a else N - 1
    for fi in range(START, END + 1):
        compose(fi).save(f"{FRAMES}/r_{fi:05d}.jpg", quality=90)
        if fi % 60 == 0:
            print(f"frame {fi}/{END}", flush=True)
    print("V2 FRAMES DONE", START, END)
