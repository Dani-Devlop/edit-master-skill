#!/usr/bin/env python3
"""Phase 32 F7 — GENERALIZED PRESET RENDERER.
Preset-driven FULL reels (not module strips) for matrix genres:
cars / fitness / education / branding / mindset.
Executes preset JSON ops through banked components; volt color world (B8/F1
discipline, F3 hook fit); energy-window reframe (claude-shorts face-track
spec, lightweight adaptation); foley-composed audio -> loudnorm 2-pass -14;
mini-gates: palette census + hook span + probe + loudness; QA keyframes."""
import os
import sys
import json
import math
import glob
import wave
import subprocess as sp

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components"))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "components", "adopted", "histmap"))
import renderlib as R
import ig24kit as IG
IG.bind_renderlib(R)
import v22kit as K
import wc25kit as WC
import histmap_kit as HM

WORK = os.environ.get("EMS_WORK", "/tmp/ems-work/p32r2")
REELS = f"{WORK}/reels"
PRESETS = os.path.join(os.path.dirname(_HERE), "presets", "p32")
os.makedirs(REELS, exist_ok=True)
os.makedirs(f"{REELS}/qa", exist_ok=True)

VOLT = R.VOLT
INK = R.INK


def confetti_v(d, cx, cy, spread, t, rng_seed=7):
    rng = np.random.default_rng(rng_seed)
    colors = [VOLT + (235,), (240, 242, 246, 225)]
    for i in range(16):
        a = rng.uniform(0, 2 * math.pi)
        r = spread * rng.uniform(0.25, 1.0)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        s = rng.uniform(5, 12)
        rot = rng.uniform(0, math.pi)
        d.line([(x - s * math.cos(rot), y - s * math.sin(rot)),
                (x + s * math.cos(rot), y + s * math.sin(rot))],
               fill=colors[i % 2], width=max(3, int(s * 0.4)))


class ClipSource:
    """Decodes a Mixkit clip; 9:16 energy-window reframe (lightweight
    face-track adaptation): per-shot crop x follows motion energy."""

    def __init__(self, path, out_w=720, out_h=1280):
        self.cap = cv2.VideoCapture(path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.out_w, self.out_h = out_w, out_h
        ok, f0 = self.cap.read()
        self.src_h, self.src_w = f0.shape[:2]
        self.crop_w = int(self.src_h * out_w / out_h)
        self.grade_bw = True  # S2/B8: volt-world footage graded B&W
        self.energy_x = None
        self.cache = {}

    def _read(self, idx):
        idx = max(0, min(self.n - 1, int(idx)))
        if idx in self.cache:
            return self.cache[idx]
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = self.cap.read()
        if not ok:
            fr = np.zeros((self.src_h, self.src_w, 3), np.uint8)
        if len(self.cache) > 90:
            self.cache.clear()
        self.cache[idx] = fr
        return fr

    def energy_track(self, sample_every=5):
        """frame-diff energy per column -> smoothed crop-center candidates."""
        gs_prev = None
        acc = None
        for i in range(0, self.n, sample_every):
            fr = self._read(i)
            gs = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if gs_prev is not None:
                diff = np.abs(gs - gs_prev).mean(axis=0)
                acc = diff if acc is None else acc + diff
            gs_prev = gs
        if acc is None:
            acc = np.ones(self.src_w, dtype=np.float32)
        acc = cv2.GaussianBlur(acc.reshape(1, -1), (1, 61), 0).ravel()
        x_max = self.src_w - self.crop_w
        if acc.max() > 0:
            center = int(np.clip(np.argmax(acc), self.crop_w // 2, self.src_w - self.crop_w // 2))
        else:
            center = self.src_w // 2
        self.energy_x = min(x_max, max(0, center - self.crop_w // 2))
        return self.energy_x

    def frame(self, t, drift=0.0):
        fr = self._read(t * self.fps)
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        x0 = int(min(max(0, self.energy_x + drift), self.src_w - self.crop_w))
        crop = rgb[:, x0:x0 + self.crop_w]
        img = Image.fromarray(crop).resize((self.out_w, self.out_h), Image.LANCZOS)
        if self.grade_bw:
            # S2/B8 discipline (v26): volt-world footage is B&W graded — raw
            # footage chroma (foliage greens / car reds) would blow the census
            arr = np.asarray(img.convert("RGB")).astype(np.float32).mean(axis=2)
            lo, hi = np.percentile(arr, [2, 98])
            if hi > lo + 1e-3:
                arr = (arr - lo) / (hi - lo) * 225.0 + 12.0
            arr = np.clip(arr, 0, 255)
            img = Image.fromarray(np.repeat(arr[..., None], 3, axis=2).astype(np.uint8))
        return img.convert("RGBA")


def cam_pulse(img, t, s0, punch=0.05, drift=10.0):
    """resolution-parameterized punch+drift cover-crop (v22kit.cam_apply is
    pinned to 1080x1920 constants; preset renderer runs 720x1280)."""
    W, H = img.size
    p = min(1.0, max(0.0, t - s0))
    z = 1.0 + 0.0036 * t + punch * min(1.0, p / 0.35)
    dx = 4.0 * t - 2.0 * math.cos(2 * math.pi * t / 9.2 + s0 * 0.7)
    dy = 2.0 * t - 1.0 * math.cos(2 * math.pi * t / 11.0 + s0 * 1.1)
    zw, zh = max(2, int(W / z)), max(2, int(H / z))
    cx, cy = W / 2 + (dx + drift * 0.4) * 0.5, H / 2 + dy * 0.5
    x0 = min(max(0, cx - zw / 2), W - zw)
    y0 = min(max(0, cy - zh / 2), H - zh)
    return img.crop((int(x0), int(y0), int(x0) + zw, int(y0) + zh)).resize((W, H), Image.BILINEAR)


def film_gate_burn(img):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, 11, H], fill=(8, 8, 10, 255))
    d.rectangle([W - 12, 0, W - 1, H], fill=(8, 8, 10, 255))
    return img


def make_audio(preset, out_wav):
    """foley composition + soft bed -> one mix (loudnorm applied at mux)."""
    dur = preset["dur"]
    foley = HM.OneShotFoley(dur + 0.5)
    for hit in preset["audio"]["foley"]:
        getattr(foley, hit["kind"])(hit["t"], gain=hit.get("gain", 0.24))
    sr = HM.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    bed_gain = preset["audio"].get("bed_gain", 0.05)
    rng = np.random.default_rng(7)
    bed = np.zeros(n, dtype=np.float32)
    kick_t = [h["t"] for h in preset["audio"]["foley"] if h["kind"] == "thump"]
    for kt in kick_t:
        i0 = int(kt * sr)
        ln = int(0.22 * sr)
        if i0 + ln < n:
            env = np.exp(-np.arange(ln) / (0.05 * sr))
            bed[i0:i0 + ln] += np.sin(2 * np.pi * 52 * np.arange(ln) / sr) * env * 0.5
    nseg = np.convolve(rng.normal(0, 1, n), np.ones(96) / 96, "same")
    mix = bed * bed_gain * 2 + nseg * bed_gain * 0.35 + foley.buf[:n]
    mix = np.clip(mix, -1.0, 1.0)
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav


def render_preset(preset_path):
    preset = json.load(open(preset_path))
    genre = preset["genre"]
    W, H = preset["res"]
    FPS = preset["fps"]
    DUR = preset["dur"]
    N = int(DUR * FPS)
    out = f"{REELS}/preset_{genre}_{int(DUR)}s.mp4"

    clip = ClipSource(preset["clip"]["path"], W, H)
    clip.energy_track()
    clip_dur = clip.n / clip.fps

    def src_t(spec, t):
        s = spec.get("src_t", 0.0)
        d = s + (t - spec["t"])
        if preset["clip"].get("loop_short", True) and d >= clip_dur - 0.05:
            d = s + ((t - spec["t"]) % max(1.0, clip_dur - s - 0.2))
        return max(0.0, d)

    scenes = sorted(preset["beats"], key=lambda b: b["t"])

    def active_spec(t):
        cur = scenes[0]
        for sp_ in scenes:
            if t >= sp_["t"]:
                cur = sp_
        return cur

    card_state = {}

    def compose(i):
        t = i / FPS
        spec = active_spec(t)
        op = spec["op"]
        img = None
        if op == "hook_slam":
            img = clip.frame(src_t(spec, t), drift=8 * math.sin(t * 1.3))
            d = ImageDraw.Draw(img, "RGBA")
            word = preset["hook"]["word"]
            size_big = 190
            while R.montserrat(size_big, 900).getlength(word) > int(W * preset["hook"].get("fit_w", 0.66)) and size_big > 60:
                size_big -= 6
            IG.slam_text(img, (W / 2, int(H * 0.385)), word,
                         lambda s: R.montserrat(s, 900), t, spec["t"],
                         per_letter=0.045, size=size_big, base=True, track=-2)
            tw = R.montserrat(size_big, 900).getlength(word)
            K.bracket_corners(d, (W / 2 - tw / 2 - 32, int(H * 0.30),
                                  W / 2 + tw / 2 + 32, int(H * 0.48)), color=INK, L=30, w=5)
            sub = preset["hook"].get("sub")
            if sub:
                fs = R.montserrat(46, 900)
                bb = d.textbbox((0, 0), sub, font=fs)
                d.text(((W - bb[2] + bb[0]) / 2, int(H * 0.52)), sub,
                       font=fs, fill=(246, 246, 242, 235))
            confetti_v(d, W / 2, int(H * 0.40), 180 * min(1.0, (t - spec["t"]) / 0.34 + 0.2), t)
            img = film_gate_burn(img)
        elif op == "footage":
            img = clip.frame(src_t(spec, t))
            if spec.get("sticker") == "scribble":
                d = ImageDraw.Draw(img, "RGBA")
                K.sticker_scribble(d, int(W * 0.24), int(H * 0.30), 150, seed=5)
            elif spec.get("sticker") == "arrow":
                d = ImageDraw.Draw(img, "RGBA")
                K.sticker_arrow(d, int(W * 0.12), int(H * 0.28), int(W * 0.38), int(H * 0.42))
            elif spec.get("sticker") == "starburst":
                d = ImageDraw.Draw(img, "RGBA")
                K.sticker_starburst(d, int(W * 0.78), int(H * 0.26), 130, t=t)
            elif spec.get("sticker") == "coin":
                d = ImageDraw.Draw(img, "RGBA")
                K.sticker_coin(d, int(W * 0.80), int(H * 0.28), 96)
            if spec.get("invert_bite") and t < spec["t"] + 0.20:
                arr = 255 - np.asarray(img.convert("RGB"))
                img = Image.fromarray(arr).convert("RGBA")
        elif op == "video_in_card":
            img = clip.frame(src_t(spec, t))
            inner_w = int(W * spec.get("card_w", 0.62))
            src_f = clip.frame(src_t(spec, t) + 0.0)
            ratio = inner_w / src_f.width
            inner = src_f.resize((inner_w, int(src_f.height * ratio)), Image.LANCZOS)
            tilt = spec.get("tilt", -4)
            card = WC.wc1_card(inner, inner.width, inner.height, rot=tilt, border="ink")
            card = WC.wc1_card_shadow(card, blur=14, alpha=110)
            if "card_pos" not in card_state:
                card_state["card_pos"] = (int(W * spec.get("cx", 0.5) - card.width / 2),
                                          int(H * spec.get("cy", 0.44) - card.height / 2))
            img = cam_pulse(img, t, spec["t"], punch=0.04, drift=8)
            img.alpha_composite(card, card_state["card_pos"])
            d2 = ImageDraw.Draw(img, "RGBA")
            d2.rectangle([0, int(H * 0.845), W, int(H * 0.845) + 5], fill=VOLT + (200,))
        elif op == "listicle":
            img = clip.frame(src_t(spec, t))
            arr = np.asarray(img.convert("RGB")).astype(np.float32).mean(axis=2)
            img = Image.fromarray(np.repeat(arr[..., None], 3, axis=2).astype(np.uint8)).convert("RGBA")
            WCpatch = Image.new("RGBA", (W, H), (0, 0, 0, 40))
            img.alpha_composite(WCpatch)
            d = ImageDraw.Draw(img, "RGBA")
            items = preset["listicle"]["items"]
            fnt = R.montserrat(44, 900)
            R.listicle_bars(img, int(W * 0.10), int(H * 0.36), [(f"{k+1:02d}", v) for k, v in enumerate(items)],
                            fnt, active_idx=min(len(items) - 1, int((t - spec["t"]) / 0.55)), bar_w=int(W * 0.55), gap=88)
            val = int(min(1.0, (t - spec["t"]) / (spec["dur"] - 0.4)) * preset["listicle"].get("value", 8137))
            f2 = R.montserrat(64, 900)
            d.text((int(W * 0.10), int(H * 0.24)), f"{val:,}", font=f2, fill=VOLT + (240,))
        elif op == "shrink_card":
            zt = (t - spec["t"]) / max(0.1, spec["dur"])
            zt = min(1.0, max(0.0, zt))
            bg = clip.frame(src_t(spec, t) + zt * 0.8)
            zoom = 1.0 + 0.9 * zt
            nw, nh = int(W * zoom), int(H * zoom)
            img = bg.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2,
                                                            (nw - W) // 2 + W, (nh - H) // 2 + H))
            card_s = 1.0 - 1.35 * zt
            if card_s > 0.02:
                cw, ch = int(W * card_s), int(H * card_s)
                if cw > 4 and ch > 4:
                    inner = clip.frame(spec["t"]).resize((cw, ch), Image.LANCZOS)
                    card = inner.rotate(spec.get("tilt", -6) * zt, expand=False, resample=Image.BICUBIC)
                    bd = ImageDraw.Draw(card, "RGBA")
                    bd.rectangle([0, 0, cw - 1, ch - 1], outline=VOLT + (220,), width=6)
                    sh = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
                    ImageDraw.Draw(sh).rectangle([20, 26, 20 + cw, 26 + ch], fill=(0, 0, 0, 110))
                    sh = sh.filter(ImageFilter.GaussianBlur(12))
                    sh.alpha_composite(card, (20, 20))
                    img.alpha_composite(sh, (int(W / 2 - sh.width / 2), int(H / 2 - sh.height / 2)))
        elif op == "endcard":
            img = Image.new("RGBA", (W, H), (243, 240, 232, 255))
            d = ImageDraw.Draw(img, "RGBA")
            word = preset["endcard"]["word"]
            f_g = R.playfair(int(W * 0.20), 900)
            bb = d.textbbox((0, 0), word, font=f_g)
            while bb[2] - bb[0] > W * 0.80 and f_g.size > 40:
                f_g = R.playfair(f_g.size - 8, 900)
                bb = d.textbbox((0, 0), word, font=f_g)
            ox, oy = (W - bb[2] + bb[0]) / 2, H * 0.30
            tw_, th_ = bb[2] - bb[0], bb[3] - bb[1]
            shpad = 22
            sh = Image.new("RGBA", (tw_ + shpad * 2, th_ + shpad * 2), (0, 0, 0, 0))
            ImageDraw.Draw(sh).text((shpad + 9, shpad + 8), word, font=f_g, fill=(20, 20, 24, 40))
            sh = sh.filter(ImageFilter.GaussianBlur(4))
            img.alpha_composite(sh, (int(ox - shpad), int(oy - shpad)))
            d.text((ox, oy), word, font=f_g, fill=(16, 17, 20, 245))
            sc = R.spring_scale(max(0.0, t - spec["t"] - 0.10), 0.32)
            if sc > 0.3:
                R.volt_pill(img, (W / 2, H * 0.545), preset["endcard"]["pill"], R.montserrat(38, 900), rot=0)
                echo = clip.frame(src_t(spec, t) * 0.3 + 1.0).resize((int(W * 0.34), int(W * 0.425)))
                ew = Image.new("RGBA", (echo.width + 24, echo.height + 24), (0, 0, 0, 0))
                ew.alpha_composite(echo.convert("RGBA"), (12, 12))
                ImageDraw.Draw(ew).rectangle([0, 0, ew.width - 1, ew.height - 1], outline=VOLT + (200,), width=3)
                img.alpha_composite(ew, (int(W / 2 - ew.width / 2), int(H * 0.60)))
            R.pixel_dots(img, 8, (60, int(H * 0.88), W - 60, int(H * 0.95)), seed=int(t * 5) + 3, size=9)
            img = cam_pulse(img, t, spec["t"], punch=0.03, drift=6)
        else:
            img = clip.frame(src_t(spec, t))
        # texture stack (F2 discipline inside helpers)
        img = img.convert("RGBA")
        if i % 3 == 0:
            img = IG.halation(img, thr=205, strength=0.24).convert("RGBA")
        if i % 5 == 0:
            img = IG.dust_scratch(img, t, p_dust=0.45)
        cap_text = preset.get("caption", {}).get("text")
        if cap_text and spec.get("caption", True) and op not in ("hook_slam", "endcard"):
            d = ImageDraw.Draw(img, "RGBA")
            fnt = R.montserrat(40, 900)
            bb = d.textbbox((0, 0), cap_text, font=fnt)
            pad = 14
            cx0 = (W - (bb[2] - bb[0])) / 2 - pad
            plate = Image.new("RGBA", (int(bb[2] - bb[0]) + pad * 2, (bb[3] - bb[1]) + pad * 2), (10, 10, 14, 215))
            pd = ImageDraw.Draw(plate)
            pd.rounded_rectangle([0, 0, plate.width - 1, plate.height - 1], radius=18, fill=(10, 10, 14, 215))
            pd.text((pad - bb[0], pad - bb[1]), cap_text, font=fnt, fill=(246, 246, 242, 240))
            img.alpha_composite(plate, (int(cx0), int(H * 0.78)))
        return img.convert("RGB")

    qa_idx = {int(round(k / 5.0 * (N - 1))) for k in range(6)}
    proc = sp.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                     "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                     "-pix_fmt", "yuv420p", out], stdin=sp.PIPE, stderr=sp.PIPE)
    for i in range(N):
        fr = compose(i)
        if i in qa_idx:
            fr.save(f"{REELS}/qa/{genre}_f{i:04d}.jpg", quality=88)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace")
    rc = proc.wait()

    # audio: foley composition -> loudnorm 2-pass -> mux
    wav = make_audio(preset, f"{REELS}/preset_{genre}_mix.wav")
    p1 = sp.run(["ffmpeg", "-y", "-v", "info", "-i", wav, "-af",
                 "loudnorm=I=-14:TP=-1.5:LRA=11", "-f", "null", "-"],
                capture_output=True, text=True).stderr
    meas = {}
    for ln in p1.splitlines():
        if "measured_I" in ln or "measured_LRA" in ln or "measured_TP" in ln or "measured_thresh" in ln:
            k, v = ln.strip().rstrip(",").split(":")
            meas[k.strip()] = v.strip()
    ln2 = "loudnorm=I=-14:TP=-1.5:LRA=11"
    if len(meas) >= 4:
        ln2 = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={meas.get('measured_I','')}"
               f":measured_LRA={meas.get('measured_LRA','')}:measured_TP={meas.get('measured_TP','')}"
               f":measured_thresh={meas.get('measured_thresh','')}:linear=true")
    muxed = out.replace(".mp4", "_aud.mp4")
    sp.run(["ffmpeg", "-y", "-v", "error", "-i", out, "-i", wav, "-af", ln2,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", muxed], check=True)
    os.replace(muxed, out)

    return {"genre": genre, "out": out, "rc": rc, "err": err[:120],
            "clip_dur": round(clip_dur, 2), "loudnorm_measured_I": meas.get("measured_I")}


def gate_reel(rep):
    out = rep["out"]
    pr = sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,codec_type",
                 "-of", "json", out], capture_output=True, text=True).stdout
    meta = json.loads(pr)
    cap = cv2.VideoCapture(out)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    okhue = ((np.arange(180) >= 24) & (np.arange(180) <= 48))
    bad = chroma = frames = 0
    ratios = []
    for i in [int(k * (n - 2) / 11.0) for k in range(12)]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok:
            continue
        sm = cv2.resize(fr, (270, 480))
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
        ch = (hsv[..., 1] > 90) & (hsv[..., 2] > 60)
        vo = ch & okhue[hsv[..., 0]]
        bad += int((ch & ~vo).sum())
        chroma += int(ch.sum())
        frames += 1
        band = vo[int(480 * 0.28):int(480 * 0.52), :]
        rows = np.where(band.sum(axis=1) >= max(6, int(0.12 * 270)))[0]
        if len(rows):
            seg = band[rows[0]:rows[-1] + 1]
            cols = np.where(seg.any(axis=0))[0]
            if len(cols):
                ratios.append(round(float(cols[-1] - cols[0]) / 270.0, 3))
    cap.release()
    frac = round(bad / max(1, chroma), 5)
    rep["gate"] = {"frames": frames, "offpalette_frac": frac,
                   "census_pass": frac <= 0.02,
                   "hook_ratios": ratios, "hook_pass": (not ratios) or max(ratios) <= 0.92,
                   "probe": meta}
    return rep


if __name__ == "__main__":
    args = sys.argv[1:]
    only = args[0] if args else None
    results = []
    for pp in sorted(glob.glob(f"{PRESETS}/*.json")):
        g = os.path.basename(pp).replace(".json", "")
        if only and g != only:
            continue
        rep = render_preset(pp)
        rep = gate_reel(rep)
        results.append(rep)
        print(json.dumps(rep, indent=1)[:600])
        print(f"[heartbeat] {g}: rc={rep['rc']} census={rep['gate']['census_pass']} hook={rep['gate']['hook_pass']}")
    json.dump(results, open(f"{REELS}/preset_reels_report.json", "w"), indent=1)
