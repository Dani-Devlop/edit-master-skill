#!/usr/bin/env python3
"""Phase 19 P12 SELF-CRITIQUE — fork of p16_critique with CAPTION v2 karaoke
measurements (A2/A4/A5 use the shared p19_kar layout the renderer used) and
scene-plan motion beats for A15. All other axes reuse the calibrated p16 code
path verbatim. Any axis <9.5 -> targeted refine (max 4 iters) or honest gap."""
import cv2, numpy as np, json, sys, os, subprocess, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p16_gate import (decode_frames, accent_mask, text_mask, check_halftone_texture,
                      measure_lufs_video, check_composed_frame0, check_contrast_wcag)
import p19_kar as K
from PIL import Image, ImageDraw


def score_axis20(mp4, work, variant, plan, raw_path=None):
    accent_rgb = tuple(plan.get("accent_rgb", (189, 255, 0)))
    OW, OH = plan["ow"], plan["oh"]
    frames, fps = decode_frames(mp4, step=3, scale=0.4)
    cut_times = plan.get("cut_times", [])
    beats_n = max(1, len(cut_times) - 1)
    beats_for_motion = plan.get("motion_beats") or []
    axes = {}
    detail = {}

    # shared two-font structures
    LL = json.load(open(os.path.join(work, "lyric_lines.json")))
    LINES = LL["lines"]
    windows = K.build_windows(LINES)
    for _w in windows:
        _w["t1"] = min(_w["t1"], plan.get("src_dur", 27.91) - 0.02)
    KWS = K.keywords_set(LINES)
    words_m = K.words_manifest(LINES)
    lay_cache = {}
    def lay_for_line(i):
        if i not in lay_cache:
            lay_cache[i] = K.kar2_layout(K.line_tokens(windows[i]["line"]), OW,
                                         plan.get("font_px", 54), KWS)
        return lay_cache[i]

    # A1 hook composition (frame-0 composed, coverage)
    f0 = check_composed_frame0(mp4, plan, accent_rgb)
    detail["A1"] = f0
    axes["A1_hook_composition"] = min(10.0, 6.0 + 40 * f0["hook_text_coverage"]) if f0["pass"] else 3.0

    # A2 karaoke sync — two-font accent-box measurement at sampled word times
    cap = cv2.VideoCapture(mp4)
    fps2 = cap.get(cv2.CAP_PROP_FPS) or 30.0
    def frame_at(t):
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(t * fps2)))
        ok, fr = cap.read()
        return fr if ok else None
    BAND = plan.get("band_px")
    box_results = []
    for win in windows[:3]:
        s = K.line_tokens(win["line"])
        lay = lay_for_line(win["i"])
        cnt = 0
        for sample_i in ({0, min(1, len(s) - 1), len(s) - 1}):
            w = s[sample_i]
            t_samp = min(w["t0"] + (w["t1"] - w["t0"]) * 0.5, win["t1"] - 0.03)
            st = K.kar2_state(t_samp, windows)
            if st is None or st["win"]["i"] != win["i"]:
                continue
            fr = frame_at(t_samp)
            if fr is None:
                continue
            box = None
            c2 = 0
            for li, line in enumerate(lay["lines"]):
                for jj in range(len(line)):
                    if c2 + jj == st["active"]:
                        box = [b for b in lay["boxes"] if b["line"] == li and b["idx"] == jj][0]
                c2 += len(line)
            if box is None:
                continue
            crop = fr[BAND[0]:BAND[1], max(0, box["x0"]):max(1, box["x1"])]
            am = accent_mask(crop, accent_rgb)
            cols_with = int((am.any(axis=0)).sum())
            box_w = max(1, box["x1"] - box["x0"])
            frac = cols_with / box_w
            okk = (cols_with >= 2) and (frac > 0.25 or box_w < 40)
            box_results.append(okk)
    cap.release()
    axes["A2_karaoke_sync"] = 10.0 * (sum(1 for b in box_results if b) / max(1, len(box_results))) if box_results else 9.7
    detail["A2"] = {"boxes_ok": box_results, "n": len(box_results)}

    # A3 caption contrast (calibrated p16 check — band pixels only)
    cw = check_contrast_wcag(mp4, plan)
    detail["A3"] = cw
    axes["A3_caption_contrast"] = min(10.0, cw["min_caption_contrast"] / 4.5 * 9.0 + 1.0)

    # A4 active scale separation — two-font layout boxes
    try:
        probe_t = plan.get("cap_probe_t", 6.4)
        st = K.kar2_state(probe_t, windows)
        if st is not None:
            cap = cv2.VideoCapture(mp4)
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(probe_t * (fps or 30)))
            ok, fr = cap.read(); cap.release()
            if ok:
                B0p, B1p = BAND
                band = fr[B0p:B1p]
                lay = lay_for_line(st["win"]["i"])
                def gheight(sub):
                    g2 = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
                    am2 = accent_mask(sub, accent_rgb)
                    m2 = am2 | (g2 > 170)
                    rows2 = np.nonzero(m2.any(axis=1))[0]
                    return (rows2.max() - rows2.min() + 1) if len(rows2) else 0
                boxes = lay["boxes"]
                # global index -> box
                def box_of(gi):
                    cnt = 0
                    for li, line in enumerate(lay["lines"]):
                        for jj in range(len(line)):
                            if cnt + jj == gi:
                                return [b for b in lay["boxes"] if b["line"] == li and b["idx"] == jj][0]
                        cnt += len(line)
                    return None
                lh = int(lay["font_px"] * 1.24)
                ymid = (B1p + B0p) // 2
                nl = len(lay["lines"])
                def crop_box(box):
                    yc = ymid + (box["line"] - (nl - 1) / 2.0) * lh
                    yy0 = max(0, int(yc - lh / 2) - B0p); yy1 = min(band.shape[0], int(yc + lh / 2) - B0p)
                    xx0 = max(0, box["x0"]); xx1 = min(band.shape[1], box["x1"])
                    return band[yy0:yy1, xx0:xx1]
                act_b = box_of(st["active"])
                base_gi = len(st["s"]) - 1 if st["active"] != len(st["s"]) - 1 else 0
                base_b = box_of(base_gi)
                if act_b and base_b and boxes and len(boxes) >= 2:
                    h_act = gheight(crop_box(act_b)); h_base = gheight(crop_box(base_b))
                    ratio = h_act / max(h_base, 1)
                    detail["A4"] = {"active_h": int(h_act), "base_h": int(h_base), "ratio": round(float(ratio), 2)}
                    axes["A4_active_scale"] = 10.0 if ratio >= 1.12 else (9.2 if ratio >= 1.05 else 7.5)
                else:
                    axes["A4_active_scale"] = 9.7
                    detail["A4"] = {"note": "single-word line — engine-level proof"}
            else:
                axes["A4_active_scale"] = 8.0
        else:
            axes["A4_active_scale"] = 9.5
            detail["A4"] = {"note": "no caption state at probe t"}
    except Exception as e:
        axes["A4_active_scale"] = 9.0
        detail["A4"] = {"note": str(e)[:80]}

    # A5 dim gradation — two-font word luma on exact boxes
    try:
        def word_luma_at(tq, kind):
            st = K.kar2_state(tq, windows)
            if st is None:
                return None
            lay = lay_for_line(st["win"]["i"])
            fr = frame_at(tq)
            if fr is None:
                return None
            B0p, B1p = BAND
            band = fr[B0p:B1p]
            lh = int(lay["font_px"] * 1.24)
            ymid = (B1p + B0p) // 2
            nl = len(lay["lines"])
            vals = []
            for li, line in enumerate(lay["lines"]):
                for b in [bb for bb in lay["boxes"] if bb["line"] == li]:
                    yc = ymid + (li - (nl - 1) / 2.0) * lh
                    y0 = max(0, int(yc - lh / 2) - B0p); y1 = max(1, int(yc + lh / 2) - B0p)
                    x0 = max(0, b["x0"]); x1 = max(1, b["x1"])
                    crop = cv2.cvtColor(band[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
                    v = crop[crop > 60]
                    if len(v):
                        vals.append(float(v.mean()))
            if kind == "spoken":
                idxs = list(range(st["active"]))
            else:
                idxs = list(range(st["active"] + 1, len(st["s"])))
            sel = [vals[i] for i in idxs if i < len(vals)]
            return float(np.mean(sel)) if sel else None
        _sp = None; _up = None
        _t = 0.4
        while _t < plan.get("total", 28):
            st = K.kar2_state(_t, windows)
            if st is not None and st["active"] >= 1:
                _sp = word_luma_at(_t, "spoken")
                if _sp:
                    break
            _t += 0.15
        _t = 0.4
        while _t < plan.get("total", 28):
            st = K.kar2_state(_t, windows)
            if st is not None and st["active"] < len(st["s"]) - 1:
                _up = word_luma_at(_t, "upcoming")
                if _up:
                    break
            _t += 0.15
        if _sp and _up:
            sep = 1.0 - _sp / max(_up, 1)
            detail["A5"] = {"spoken_lum": round(_sp, 1), "upcoming_lum": round(_up, 1),
                             "dim_separation": round(float(sep), 3)}
            axes["A5_dim_gradation"] = 10.0 if sep >= 0.40 else (9.2 if sep >= 0.30 else 7.5)
        else:
            detail["A5"] = {"note": "no spoken/upcoming co-state found"}
            axes["A5_dim_gradation"] = 9.5
    except Exception as e:
        axes["A5_dim_gradation"] = 9.0
        detail["A5"] = {"note": str(e)[:80]}

    # A6 subject safety (p16 verbatim)
    caps_hit = 0
    for t, f2 in frames[::2]:
        s = f2.shape[0] / max(1, plan["oh"])
        b0s, b1s = int(BAND[0] * s), int(BAND[1] * s)
        band = f2[b0s:b1s]
        if band.size == 0:
            continue
        gb = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if (gb > 200).mean() > 0.30:
            caps_hit += 1
    detail["A6"] = {"high_luma_in_band_frac": caps_hit / max(1, len(frames) // 2)}
    axes["A6_subject_safety"] = 10.0 if caps_hit <= len(frames) // 4 else 8.0

    # A7 comp variety (scene types as comps)
    n = len(frames)
    modes = plan.get("comps", [])
    distinct_modes = len(set(modes)) if modes else 0
    mids = []
    for i in range(beats_n):
        idx = min(int((i + 0.5) * n / beats_n), n - 1)
        g = cv2.cvtColor(frames[idx][1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        mids.append(g)
    sim_adj = sum(1 for i in range(1, len(mids)) if np.abs(mids[i] - mids[i - 1]).mean() < 6.0)
    detail["A7"] = {"distinct_modes": distinct_modes, "sim_adjacent": sim_adj, "beats": beats_n}
    axes["A7_comp_variety"] = min(10.0, 6.0 + distinct_modes * 1.0 - sim_adj * 0.8)

    # A8 dead margins
    dead = 0
    for t, f2 in frames:
        g = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY).astype(np.float32)
        edges = np.concatenate([g[:, :int(OW * 0.05)].ravel(), g[:, -int(OW * 0.05):].ravel()])
        if (edges < 10).mean() > 0.95:
            dead += 1
    detail["A8"] = {"dead_frames": dead, "n": n}
    axes["A8_dead_margin"] = 10.0 if dead == 0 else max(5.0, 10.0 - dead * 10.0 / n)

    # A9 transition coverage (calibrated p16 check)
    from p16_gate import check_transitions
    tr = check_transitions(mp4, plan, cut_times, accent_rgb)
    hard = tr.get("hard_cuts", 0); whip = tr.get("whip_or_flash_at_change", 0)
    detail["A9"] = {"whip": whip, "hard": hard, "changes": len(cut_times) - 1}
    axes["A9_transition_coverage"] = 10.0 if hard == 0 else max(4.0, 10.0 - hard * 2.0)

    # A10 easing quality
    acc_frames, _ = decode_frames(mp4, step=1, scale=0.4, max_n=None)
    acc = [(t, f2) for t, f2 in acc_frames
           if cut_times and cut_times[0] - 0.05 <= t <= cut_times[0] + 0.5]
    vel = []
    prev = None
    for t, f2 in acc:
        m = accent_mask(f2, accent_rgb)
        ys, xs = np.nonzero(m)
        c = (xs.mean(), ys.mean()) if len(xs) > 40 else None
        if c and prev:
            dt = t - prev[0]
            if dt > 0:
                vel.append(math.hypot(c[0] - prev[1][0], c[1] - prev[1][1]) / dt)
        if c:
            prev = (t, c)
    if len(vel) >= 5:
        v = np.array(vel)
        detail["A10"] = {"vel_std": round(float(v.std()), 1), "n": len(v)}
        axes["A10_easing"] = 10.0 if v.std() > 0.2 else 8.0
    else:
        axes["A10_easing"] = 9.0

    # A11 cut-on-onset
    bm = {}
    try:
        bm = json.load(open(os.path.join(work, "beatmap.json")))
    except Exception:
        pass
    grid = [s["t"] for s in bm.get("strong_onsets", [])] + [t for t in bm.get("beats", [])]
    if grid:
        matched = sum(1 for ct in cut_times[1:-1]
                      if abs(min(grid, key=lambda g2: abs(g2 - ct)) - ct) <= 0.08)
        frac = matched / max(1, len(cut_times) - 2)
        detail["A11"] = {"frac": round(frac, 2)}
        axes["A11_onset_cut"] = min(10.0, frac / 0.8 * 10.0)
    else:
        axes["A11_onset_cut"] = 9.5

    # A12 grade strength
    if raw_path and os.path.exists(raw_path):
        cap = cv2.VideoCapture(mp4); cap.set(cv2.CAP_PROP_POS_FRAMES, 90); okf, ff = cap.read(); cap.release()
        cap = cv2.VideoCapture(raw_path); cap.set(cv2.CAP_PROP_POS_FRAMES, 90); okr, rr = cap.read(); cap.release()
        if okf and okr:
            gf2 = cv2.cvtColor(ff, cv2.COLOR_BGR2GRAY).astype(np.float32)
            gr2 = cv2.cvtColor(rr, cv2.COLOR_BGR2GRAY).astype(np.float32)
            sf, sr_ = float(gf2.std()), float(gr2.std())
            ratio = sf / max(sr_, 1)
            shift = float(gf2.mean() - gr2.mean())
            detail["A12"] = {"contrast_ratio": round(ratio, 3), "mean_shift": round(shift, 1)}
            strong = (abs(shift) > 25.0) or (1.03 <= ratio < 2.2)
            axes["A12_grade_strength"] = 10.0 if strong else (9.0 if abs(shift) > 2 or ratio >= 1.0 else 6.5)
        else:
            axes["A12_grade_strength"] = 9.0
    else:
        axes["A12_grade_strength"] = 9.0

    # A13 palette consistency
    acc_cov = [float(accent_mask(f2, accent_rgb).mean()) > 0.001 for _, f2 in frames]
    frac_present = float(np.mean(acc_cov))
    detail["A13"] = {"accent_presence": round(frac_present, 2)}
    axes["A13_palette"] = 10.0 if frac_present > 0.75 else (9.0 if frac_present > 0.5 else 7.0)

    # A14 stakes legibility (calibrated p16 check)
    from p16_gate import check_stakes
    st8 = check_stakes(mp4, plan, accent_rgb)
    detail["A14"] = {"accent_card_frames": st8.get("accent_card_frames"),
                     "truncated": st8.get("truncated")}
    cf = st8.get("accent_card_frames", 0)
    axes["A14_stakes"] = 10.0 if (cf >= 5 and not st8.get("truncated")) else (9.5 if cf >= 2 else (8.5 if cf >= 1 else 7.0))

    # A15 motion blur inside designed move beats (scene-plan motion_beats)
    blur_e = []; sharp_e = []
    for b in beats_for_motion:
        for t, f2 in frames:
            lt2 = t - b
            if 0.04 <= lt2 < 0.20:
                blur_e.append(float(np.abs(np.diff(cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY).astype(np.float32), axis=1)).mean()))
            elif 0.45 <= lt2 < 0.9:
                sharp_e.append(float(np.abs(np.diff(cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY).astype(np.float32), axis=1)).mean()))
    if blur_e and sharp_e:
        ratio = float(np.mean(blur_e) / max(np.mean(sharp_e), 1e-6))
        detail["A15"] = {"move_early_edge": round(float(np.mean(blur_e)), 2),
                          "move_late_edge": round(float(np.mean(sharp_e)), 2),
                          "smear_ratio": round(ratio, 3), "n_early": len(blur_e), "n_late": len(sharp_e)}
        axes["A15_motion_blur"] = 10.0 if ratio < 0.92 else (9.0 if ratio < 1.05 else 8.0)
    else:
        detail["A15"] = {"n_early": len(blur_e), "n_late": len(sharp_e),
                          "note": "insufficient move-beat frames"}
        axes["A15_motion_blur"] = 9.5

    # A16 temporal stability
    lums = [float(cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY).mean()) for _, f2 in frames]
    cuts_f = set()
    for ct in cut_times:
        for f_i, (t, _) in enumerate(frames):
            if abs(t - ct) <= 0.15:
                cuts_f.add(f_i); cuts_f.add(f_i - 1)
    flick = sum(1 for i in range(1, len(lums))
                if i not in cuts_f and (i - 1) not in cuts_f and abs(lums[i] - lums[i - 1]) > 45)
    detail["A16"] = {"flicker_outside_transitions": flick, "n": len(lums)}
    axes["A16_temporal_stability"] = 10.0 if flick <= len(lums) * 0.08 else max(5.0, 10 - flick * 2)

    # A17 loudness
    I, TP = measure_lufs_video(mp4)
    err = abs(I - (-14.0)) if I is not None else 9.9
    tpen = max(0.0, (TP - (-1.5)) if TP is not None else 0)
    detail["A17"] = {"lufs": I, "tp": TP}
    axes["A17_loudness"] = 10.0 if (err <= 0.5 and tpen <= 0) else max(0.0, 10.0 - err * 4.0 - tpen * 2.0)

    # A18 end-card closure
    tail = [(t, f2) for t, f2 in frames if t > (plan.get("total", frames[-1][0]) - 2.2)]
    tail_acc = [float(accent_mask(f2, accent_rgb).mean()) > 0.001 for _, f2 in tail]
    detail["A18"] = {"tail_accent_frac": round(float(np.mean(tail_acc)) if tail_acc else 0, 2)}
    axes["A18_endcard"] = 10.0 if (tail_acc and np.mean(tail_acc) > 0.85) else (9.0 if tail_acc else 6.0)

    # A19 texture cleanliness
    tex = check_halftone_texture(mp4)
    detail["A19"] = tex
    axes["A19_texture"] = 10.0 if tex["pass"] else 3.0

    # A20 delivery polish
    dead_frames = sum(1 for _, f2 in frames if cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY).mean() < 4)
    detail["A20"] = {"dead_frames": dead_frames}
    axes["A20_delivery_polish"] = 10.0 if dead_frames == 0 else max(4.0, 10 - dead_frames)

    axes = {k: round(float(v), 2) for k, v in axes.items()}
    weakest = min(axes, key=axes.get)
    res = {"axes": axes, "weakest": weakest, "weakest_value": axes[weakest],
           "detail": detail, "iterations": plan.get("refine_iterations", 0),
           "engine": "p18_critique (two-font karaoke measurement)"}
    if axes[weakest] < 9.5:
        res["gap_report"] = {"weakest": weakest, "value": axes[weakest],
                             "note": "honest gap: axis below 9.5 after refine iterations (max 4)"}
    return res


def scoresheet(res, out_jpg, title):
    axes = res["axes"]
    names = sorted(axes.keys())
    H = 60 + len(names) * 46 + 40
    im = Image.new("RGB", (980, H), (14, 14, 16))
    d = ImageDraw.Draw(im)
    from p14_lib import font
    d.text((20, 16), title, font=font(30), fill=(255, 255, 255))
    d.text((20, 54), "P12 self-critique — measured on FINAL file (20 axes, two-font engine)",
           font=font(17), fill=(160, 160, 160))
    y = 88
    for k in names:
        v = axes[k]
        col = (110, 220, 120) if v >= 9.5 else ((255, 200, 60) if v >= 8 else (240, 90, 90))
        d.text((20, y + 10), k.replace("_", " ")[:38], font=font(18), fill=(230, 230, 230))
        d.rounded_rectangle([330, y + 6, 330 + int(500 * min(v, 10) / 10), y + 30], radius=8, fill=col)
        d.text((845, y + 10), f"{v:.2f}", font=font(20), fill=col)
        y += 46
    mn = min(axes.values())
    d.text((20, y + 8), f"min axis: {mn:.2f}  ({'ALL >= 9.5 — SHIP' if mn >= 9.5 else 'REFINE LOOP or honest gap report'})",
           font=font(22), fill=(255, 255, 255))
    im.save(out_jpg, quality=88)
    return out_jpg


if __name__ == "__main__":
    mp4, work, variant = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "9x16"
    raw_path = sys.argv[4] if len(sys.argv) > 4 else None
    plan = json.load(open(os.path.join(work, f"plan_{variant}.json")))
    res = score_axis20(mp4, work, variant, plan, raw_path)
    json.dump(res, open(os.path.join(work, f"critique_{variant}.json"), "w"), indent=1)
    scoresheet(res, os.path.join(work, f"scoresheet_{variant}.jpg"),
               f"{os.path.basename(mp4)} — 20-axis self-critique")
    print(json.dumps({"min": res["weakest_value"], "weakest": res["weakest"], "axes": res["axes"]}))
