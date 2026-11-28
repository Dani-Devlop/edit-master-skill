#!/usr/bin/env python3
"""Phase 32 F5 replica-test 2: execute two banked prompt recipes end-to-end.
Clip 1 = hook_volt_slam_confetti (3s). Clip 2 = trans_shrink_card_zoom (3s).
Mini-gates: volt-only chroma census on decoded frames + hook span <= 0.92W."""
import os
import sys
import json
import math
import subprocess as sp

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components"))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components", "adopted", "histmap"))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "scripts"))
import renderlib as R
import ig24kit as IG
IG.bind_renderlib(R)
import v22kit as K
import histmap_kit as HM

WORK = os.environ.get("EMS_WORK", "/tmp/ems-work/p32r2")
os.makedirs(WORK, exist_ok=True)
W, H, FPS = 1080, 1920, 30
VOLT = R.VOLT
INK = R.INK


def pipe_encode(frames_iter, out_path):
    proc = sp.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                     "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                     "-pix_fmt", "yuv420p", out_path], stdin=sp.PIPE, stderr=sp.PIPE)
    for fr in frames_iter:
        proc.stdin.write(fr.convert("RGB").tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace")
    rc = proc.wait()
    return rc, err


def gate_census(out_path, hook_word=None, world="volt"):
    """decode final; palette-world-aware chroma census + optional hook span.
    world='volt'    -> v26 family: volt H24-48 ONLY (B8 rule)
    world='histmap' -> F12 family: tan/crimson H0-48 + olive/teal H80-130 +
                       ember H165-180 (same windows as the F4 neon check).
    The preset renderer (F7) tags every preset with its color world and runs
    the matching census."""
    if world == "histmap":
        ok_hue = (((np.arange(180) >= 0) & (np.arange(180) <= 48)) |
                  ((np.arange(180) >= 80) & (np.arange(180) <= 130)) |
                  (np.arange(180) >= 165))
    else:
        ok_hue = (np.arange(180) >= 24) & (np.arange(180) <= 48)
    cap = cv2.VideoCapture(out_path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idx = [int(k * (n - 2) / 11.0) for k in range(12)]
    checked = bad_total = chroma_total = 0
    ratios = []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok:
            continue
        sm = cv2.resize(fr, (270, 480))
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
        ch = (hsv[..., 1] > 90) & (hsv[..., 2] > 60)
        vo = ch & ok_hue[hsv[..., 0]]
        bad_total += int((ch & ~vo).sum())
        chroma_total += int(ch.sum())
        checked += 1
        if hook_word:
            band = (ch & (hsv[..., 0] >= 24) & (hsv[..., 0] <= 48))[int(480 * 0.28):int(480 * 0.52), :]
            rows = np.where(band.sum(axis=1) >= max(6, int(0.12 * 270)))[0]
            if len(rows):
                seg = band[rows[0]:rows[-1] + 1]
                cols = np.where(seg.any(axis=0))[0]
                if len(cols):
                    ratios.append(round(float(cols[-1] - cols[0]) / 270.0, 3))
    cap.release()
    return {"world": world, "frames": checked, "offpalette_frac": round(bad_total / max(1, chroma_total), 5),
            "hook_ratios": ratios, "hook_ok": (not ratios) or max(ratios) <= 0.92}


def confetti_v(d, cx, cy, spread, t, rng_seed=7):
    """volt + white confetti (local copy of showcase confetti_v — importing the
    showcase module would pull the MV-dependent onset grid)"""
    rng = np.random.default_rng(rng_seed)
    colors = [VOLT + (235,), (240, 242, 246, 225)]
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        r = spread * rng.uniform(0.25, 1.0)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        s = rng.uniform(5, 12)
        rot = rng.uniform(0, math.pi)
        dxl, dyl = s * math.cos(rot), s * math.sin(rot)
        d.line([(x - dxl, y - dyl), (x + dxl, y + dyl)],
               fill=colors[i % 2], width=max(3, int(s * 0.4)))


# ---------------- recipe 1: hook_volt_slam_confetti ----------------
def clip1():
    out = f"{WORK}/prompt1_hook_slam_3s.mp4"
    plate = HM.relief_plate(night=True, seed=5).resize((W, H), Image.LANCZOS).convert("RGBA")

    def frames():
        for i in range(90):
            t = i / FPS
            img = plate.copy()
            d = ImageDraw.Draw(img, "RGBA")
            size_big = 210
            while R.montserrat(size_big, 900).getlength("WELCOME") > int(W * 0.66) and size_big > 70:
                size_big -= 8
            IG.slam_text(img, (W / 2, int(H * 0.385)), "WELCOME",
                         lambda s: R.montserrat(s, 900), t, 0.0,
                         per_letter=0.045, size=size_big, base=True, track=-2)
            tw = R.montserrat(size_big, 900).getlength("WELCOME")
            K.bracket_corners(d, (W / 2 - tw / 2 - 40, int(H * 0.30),
                                  W / 2 + tw / 2 + 40, int(H * 0.48)), color=INK, L=40, w=6)
            confetti_v(d, W / 2, int(H * 0.40), 230 * min(1.0, (t - 0) / 0.34 + 0.2), t)
            img, z, dx, dy = K.cam_apply(img, t, 0.0, punch=0.06, drift=12)
            img = IG.dust_scratch(img, t, p_dust=0.5)
            _d = ImageDraw.Draw(img, "RGBA")
            _d.rectangle([0, 0, 11, H], fill=(8, 8, 10, 255))
            _d.rectangle([W - 12, 0, W - 1, H], fill=(8, 8, 10, 255))
            yield img.convert("RGB")

    rc, err = pipe_encode(frames(), out)
    g = gate_census(out, hook_word="WELCOME", world="volt")
    return {"clip": out, "prompt": "hook_volt_slam_confetti", "world": "volt", "rc": rc, "err": err[:120], "gate": g}


# ---------------- recipe 2: trans_shrink_card_zoom ----------------
def clip2():
    out = f"{WORK}/prompt2_shrinkcard_3s.mp4"
    plate = HM.relief_plate(night=False, seed=21).resize((W, H), Image.LANCZOS).convert("RGBA")
    paper = Image.new("RGBA", (W, H), (243, 240, 232, 255))

    def scene_b(i, zoom):
        img = paper.copy()
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, int(H * 0.845), W, int(H * 0.845) + 6], fill=VOLT + (200,))
        R.pixel_dots(img, 9, (100, int(H * 0.20), W - 100, int(H * 0.27)), seed=i, size=10)
        f = R.montserrat(110, 900)
        txt = "ZOOM"
        bb = d.textbbox((0, 0), txt, font=f)
        d.text(((W - bb[2] + bb[0]) / 2, int(H * 0.44)), txt, font=f, fill=(16, 17, 20, 245))
        s = 1.0 + 0.9 * zoom
        nw, nh = int(W * s), int(H * s)
        return img.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2,
                                                          (nw - W) // 2 + W, (nh - H) // 2 + H))

    def frames():
        for i in range(90):
            t = i / FPS
            if t < 1.2:                       # scene A: histmap relief, slow pan
                img = HM.camera_crop(plate, t, 0.0, 1.2, (0, 0, 790, 1405), (60, 120, 790, 1405))
            elif t < 1.9:                     # shrink A into tilted volt card + B zooms through
                u = (t - 1.2) / 0.7
                u = max(0.0, min(1.0, u))
                card_s = 1.0 - 1.35 * u       # shrinks past frame edge
                b_img = scene_b(i, u)
                comp = b_img.copy()
                if card_s > 0.02:
                    cw, ch = int(W * card_s), int(H * card_s)
                    if cw > 4 and ch > 4:
                        card = plate.resize((cw, ch), Image.LANCZOS)
                        card = card.rotate(-6 * u, expand=False, resample=Image.BICUBIC)
                        bd = ImageDraw.Draw(card, "RGBA")
                        bd.rectangle([0, 0, cw - 1, ch - 1], outline=VOLT + (220,), width=6)
                        sh = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
                        ImageDraw.Draw(sh).rectangle([20, 26, 20 + cw, 26 + ch], fill=(0, 0, 0, 110))
                        sh = sh.filter(ImageFilter.GaussianBlur(12))
                        sh.alpha_composite(card, (20, 20))
                        comp.alpha_composite(sh, (int(W / 2 - sh.width / 2), int(H / 2 - sh.height / 2)))
                img = comp
            else:                             # scene B settles
                img = scene_b(i, 0.0)
            img = IG.dust_scratch(img, t, p_dust=0.4)
            yield img.convert("RGB")

    rc, err = pipe_encode(frames(), out)
    g = gate_census(out, world="histmap")
    return {"clip": out, "prompt": "trans_shrink_card_zoom", "world": "histmap", "rc": rc, "err": err[:120], "gate": g}


r1 = clip1()
r2 = clip2()
rep = {"bank": "components/prompt-bank/prompts.json", "replicas": [r1, r2]}
json.dump(rep, open(f"{WORK}/prompt_replica_report.json", "w"), indent=1)
json.dump(rep, open(os.path.join(os.path.dirname(_HERE), "test-results", "p32", "prompt_replica_report.json"), "w"), indent=1)
print(json.dumps(rep, indent=1))
