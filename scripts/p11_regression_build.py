#!/usr/bin/env python3
"""Phase 11.1 REGRESSION: build 5 ANTI negative clips (the forbidden classes) and
prove the gate FAILS each; the positive case = travel_1 (16/16 PASS already shown).
Each clip: 540x960, 30fps, ~4s, 2 beats, minimal audio.
"""
import json, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/z/my-project"
RD = f"{ROOT}/p11work/regression"
os.makedirs(RD, exist_ok=True)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(sz):
    return ImageFont.truetype(FB, sz)

def base_canvas():
    img = np.zeros((960, 540, 3), np.uint8)
    img[:, :, :] = (240, 240, 244)
    return img

def write_clip(path, frames):
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", "540x960", "-r", "30", "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                             "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    for f in frames:
        proc.stdin.write(np.ascontiguousarray(f[:, :, :3]).tobytes())
    proc.stdin.close()
    proc.wait()

def add_sine(path, events):
    import soundfile as sf
    sr = 22050
    n = int(4.0 * sr)
    t = np.arange(n) / sr
    a = 0.2 * np.sin(2 * np.pi * 220 * t)
    for e in events:
        i0 = int(e * sr)
        a[i0:i0 + 1500] += 0.5 * np.exp(-np.arange(1500) / 300.0) * np.sin(2 * np.pi * 620 * np.arange(1500) / sr)
    a = np.tanh(1.6 * a) / np.tanh(1.6)
    sf.write(path, a.astype(np.float32), sr)

def mux(video, wav, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart", out], check=True)

def text(img, txt, size, xy, fill=(30, 30, 34)):
    im = Image.fromarray(img.copy())
    d = ImageDraw.Draw(im)
    d.text(xy, txt, font=font(size), fill=fill)
    return np.array(im)

# --------------------------------------------------------------- negatives
def neg_halftone():
    """ANTI-1: halftone dot grid ON footage beat (Mode B)."""
    frames = []
    road = base_canvas()
    for y in range(960):
        for x in range(540):
            if (x % 24 == 12 and y % 24 == 12):
                road[y, x] = (250, 120, 80)
    # simulate footage variance (Mode B)
    road = cv2.resize(cv2.resize(road, (54, 96), interpolation=cv2.INTER_LINEAR), (540, 960),
                      interpolation=cv2.INTER_LINEAR)
    for i in range(120):
        frames.append(road.copy())
    write_clip(f"{RD}/neg1.mp4", frames)
    man = dict(vid="neg1", family="F1", fps=30, mode_per_beat=["B"], beat_starts=[0.0],
               hook=["HOOK"], hook_t=1.0, hook_rect=None,
               lockups=[], cards=[], captions=[dict(t0=0.0)], phone=[],
               payoff=["RUN"], endcard_text="github.com/Dani-Devlop", loop_word="HOOK",
               signature=dict(family="F1"), palette=dict(accent=[250, 120, 80]),
               sfx_entrances=[0.5], matte=False, matte_fps=None, total=4.0)
    json.dump(man, open(f"{RD}/neg1.json", "w"))
    add_sine(f"{RD}/neg1.wav", [0.5])
    mux(f"{RD}/neg1.mp4", f"{RD}/neg1.wav", f"{RD}/neg1_final.mp4")

def neg_bleed():
    """ANTI-2: unreadable full-bleed giant word (>0.92W) + clipped edges."""
    frames = []
    for i in range(120):
        img = base_canvas()
        img = text(img, "SWEEPING VICTORY", 120, (-160, 300), (250, 112, 142))
        frames.append(img)
    write_clip(f"{RD}/neg2.mp4", frames)
    man = dict(vid="neg2", family="F4", fps=30, mode_per_beat=["A"], beat_starts=[0.0],
               hook=["VICTORY"], hook_t=1.0, hook_rect=[40, 260, 460, 120],
               lockups=[dict(t0=0.0, giant="SWEEPING VICTORY", rect=[0, 600, 540, 300], occluded=False)],
               cards=[], captions=[dict(t0=0.0)], phone=[],
               payoff=["RUN"], endcard_text="github.com/Dani-Devlop", loop_word="VICTORY",
               signature=dict(family="F4"), palette=dict(accent=[250, 112, 142]),
               sfx_entrances=[0.5], matte=False, matte_fps=None, total=4.0)
    json.dump(man, open(f"{RD}/neg2.json", "w"))
    add_sine(f"{RD}/neg2.wav", [0.5])
    mux(f"{RD}/neg2.mp4", f"{RD}/neg2.wav", f"{RD}/neg2_final.mp4")

def neg_dupcards():
    """ANTI-3: two identical cards (same hash) in one beat."""
    frames = []
    card = np.full((300, 220, 3), (255, 255, 255), np.uint8)
    cv2.rectangle(card, (0, 0), (219, 299), (250, 112, 142), 8)
    cv2.putText(card, "clip", (60, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (30, 30, 34), 3)
    for i in range(120):
        img = base_canvas()
        img[300:600, 30:250] = card
        img[300:600, 290:510] = card
        frames.append(img)
    write_clip(f"{RD}/neg3.mp4", frames)
    man = dict(vid="neg3", family="F1", fps=30, mode_per_beat=["A"], beat_starts=[0.0],
               hook=["HOOK"], hook_t=1.0, hook_rect=None,
               lockups=[],
               cards=[dict(t=0.0, label="clip", rect=[30, 300, 220, 300]),
                      dict(t=0.0, label="clip", rect=[290, 300, 220, 300])],
               captions=[dict(t0=0.0)], phone=[],
               payoff=["RUN"], endcard_text="github.com/Dani-Devlop", loop_word="HOOK",
               signature=dict(family="F1"), palette=dict(accent=[250, 112, 142]),
               sfx_entrances=[0.5], matte=False, matte_fps=None, total=4.0)
    json.dump(man, open(f"{RD}/neg3.json", "w"))
    add_sine(f"{RD}/neg3.wav", [0.5])
    mux(f"{RD}/neg3.mp4", f"{RD}/neg3.wav", f"{RD}/neg3_final.mp4")

def neg_phone_contrast():
    """ANTI-4: low-contrast phone text (gray on white)."""
    frames = []
    for i in range(120):
        img = base_canvas()
        img = text(img, "BOOST 4X", 34, (90, 300), (170, 170, 175))
        frames.append(img)
    write_clip(f"{RD}/neg4.mp4", frames)
    man = dict(vid="neg4", family="F2", fps=30, mode_per_beat=["A"], beat_starts=[0.0],
               hook=["BOOST"], hook_t=1.0, hook_rect=None,
               lockups=[], cards=[],
               captions=[dict(t0=0.0)],
               phone=[dict(t=0.0, rect=[60, 260, 420, 220], mode="A")],
               payoff=["RUN"], endcard_text="github.com/Dani-Devlop", loop_word="BOOST",
               signature=dict(family="F2"), palette=dict(accent=[88, 148, 255]),
               sfx_entrances=[0.5], matte=False, matte_fps=None, total=4.0)
    json.dump(man, open(f"{RD}/neg4.json", "w"))
    add_sine(f"{RD}/neg4.wav", [0.5])
    mux(f"{RD}/neg4.mp4", f"{RD}/neg4.wav", f"{RD}/neg4_final.mp4")

def neg_deadframe():
    """ANTI-5: dead/black frame 0 (empty canvas start)."""
    frames = []
    for i in range(120):
        if i < 20:
            frames.append(np.zeros((960, 540, 3), np.uint8))
        else:
            img = base_canvas()
            img = text(img, "HOOK NOW", 90, (60, 380), (250, 112, 142))
            frames.append(img)
    write_clip(f"{RD}/neg5.mp4", frames)
    man = dict(vid="neg5", family="F1", fps=30, mode_per_beat=["A"], beat_starts=[0.0],
               hook=["HOOK NOW"], hook_t=1.0, hook_rect=None,
               lockups=[dict(t0=0.0, giant="HOOK NOW", rect=[40, 300, 460, 200], occluded=False)],
               cards=[], captions=[dict(t0=0.67)], phone=[],
               payoff=["RUN"], endcard_text="github.com/Dani-Devlop", loop_word="HOOK",
               signature=dict(family="F1"), palette=dict(accent=[250, 112, 142]),
               sfx_entrances=[0.8], matte=False, matte_fps=None, total=4.0)
    json.dump(man, open(f"{RD}/neg5.json", "w"))
    add_sine(f"{RD}/neg5.wav", [0.8])
    mux(f"{RD}/neg5.mp4", f"{RD}/neg5.wav", f"{RD}/neg5_final.mp4")

if __name__ == "__main__":
    neg_halftone(); print("neg1 built")
    neg_bleed(); print("neg2 built")
    neg_dupcards(); print("neg3 built")
    neg_phone_contrast(); print("neg4 built")
    neg_deadframe(); print("neg5 built")
    print("ALL BUILT")
