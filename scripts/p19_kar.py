#!/usr/bin/env python3
"""Phase 19 Caption System v2 (CV1-CV7) — IG-native, replaces p18_kar two-font style.
CV1 body = tight BOLD SANS (Montserrat ExtraBold), white, normal tracking (0.14em),
    natural spacing, never justified; 1-3 words/line OR tight sentence <=2 lines.
CV2 ONE active word accent (accent color, <=1.15x); spoken dim ~45%; upcoming white;
    sweep LOOPS until sentence change; word-ts tolerance +/-120ms. Never multi-accent.
CV3 no serif body (serif/script only as occasional lockup emphasis — not used in v19).
CV4 no ghost double-text / glow echo on captions (registered echo <=12% only in lockups).
CV5 relation-style layout: lines centered as a block, no free-floating words.
CV6 emphasis lands on content words via sweep timing (never to/the/and/a).
CV7 underline = karaoke progress only, removed when sentence window ends.
Deterministic boxes exported for GC1 gates. NO typewriter."""
import math
from PIL import Image, ImageDraw
import p19_fonts as F

ACTIVE_SCALE = 1.15          # CV2 ceiling
ACCENT_DIM_F = 0.45          # CV2 spoken dim
TRACK_EM = 0.14              # CV1 normal tracking
WORD_TOL = 0.12              # CV2 +/-120ms
DROP_TOKENS = ("-", "--", "\u2014")


def sfont(px):
    return F.sans_bold(px)


def bfont(px):
    return F.sans_bold(px)


def text_w2(word, fnt, draw=None):
    if draw is None:
        draw = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    return draw.textlength(word, font=fnt)


def build_windows(lines):
    """one lyric line = one karaoke sentence window (loop inside)."""
    wins = []
    for i, l in enumerate(lines):
        t0 = max(0.0, l["t0"] - 0.30)
        t1 = (lines[i + 1]["t0"] - 0.05) if i + 1 < len(lines) else l["t1"] + 1.0
        wins.append({"i": i, "t0": t0, "t1": t1, "line": l})
    return wins


def line_tokens(line):
    return [tk for tk in line["tokens"] if tk["w"] not in DROP_TOKENS]


def words_manifest(lines):
    out = []
    for l in lines:
        for tk in line_tokens(l):
            out.append({"w": tk["w"], "start": tk["t0"], "end": tk["t1"]})
    return out


def keywords_set(lines):
    kws = set()
    for l in lines:
        kws |= {k.upper() for k in l.get("keywords", [])}
    return kws


STOPWORDS = {"to", "the", "and", "a", "an", "of", "in", "on", "at", "is",
             "it", "my", "i", "we", "you", "they", "that", "this", "so"}


def kar2_state(t, windows):
    """state at t; returns None outside every window (=> no captions, no underline)."""
    for win in windows:
        if win["t0"] <= t < win["t1"]:
            s = line_tokens(win["line"])
            if not s:
                continue
            t_start, t_end = s[0]["t0"], s[-1]["t1"]
            lt = t
            looped = False
            if lt < t_start:
                lt = t_start
            elif lt > t_end and t_end > t_start:
                span = max(t_end - t_start, 0.4)
                lt = t_start + ((lt - t_end) % span)
                looped = True
            # nearest-interval handover (speech-following): exact containment wins,
            # otherwise the word whose [t0,t1] is closest to lt (absorbs <=120ms skew
            # symmetrically; no premature handover on rapid syllables)
            active = 0
            best_d = 1e9
            for i2, w in enumerate(s):
                if w["t0"] - 1e-6 <= lt <= w["t1"] + 1e-6:
                    active = i2
                    best_d = 0.0
                    break
                d = (w["t0"] - lt) if lt < w["t0"] else (lt - w["t1"])
                if d < best_d:
                    best_d = d
                    active = i2
            span_p = max(t_end - t_start, 0.4)
            prog = max(0.0, min(1.0, (lt - t_start) / span_p))
            word_is_content = s[active]["w"].lower().strip(".,!?\"'") not in STOPWORDS
            return {"win": win, "s": s, "active": active,
                    "spoken": set(range(active)), "looped": looped,
                    "prog": prog, "active_content": word_is_content}
    return None


def kar2_layout(sents, out_w, font_px=54, kws=frozenset(), width_frac=0.90, max_lines=2):
    """v2 layout: ONE sans family; widths reserved at ACTIVE scale (1.15x);
    natural tracking; centered block (relation-style anchor: center-first)."""
    chosen = font_px
    gap = int(chosen * TRACK_EM)
    probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))

    def wpx(word, px):
        return text_w2(word, bfont(px), probe) * ACTIVE_SCALE

    lines_i, cur = [], []
    for w in sents:
        wordx = w["w"] if isinstance(w, dict) else w
        cand = cur + [wordx]
        lw = int(sum(wpx(x, chosen) for x in cand) + gap * (len(cand) - 1))
        if lw > out_w * width_frac and cur:
            lines_i.append(cur)
            cur = [wordx]
        else:
            cur = cand
    if cur:
        lines_i.append(cur)
    if len(lines_i) > max_lines and chosen > 26:
        return kar2_layout(sents, out_w, chosen - 4, kws, width_frac, max_lines)
    boxes = []
    for li, line in enumerate(lines_i):
        total = int(sum(wpx(x, chosen) for x in line) + gap * (len(line) - 1))
        x = int((out_w - total) / 2)
        for wi, wordx in enumerate(line):
            wp = int(wpx(wordx, chosen))
            boxes.append({"line": li, "idx": wi, "x0": int(x), "x1": int(x + wp),
                          "word": wordx})
            x += wp + gap
    return {"lines": lines_i, "boxes": boxes, "font_px": chosen,
            "track_em": TRACK_EM}


def draw_kar2(im, st, lay, accent, band0, band1, kws=frozenset(), stroke=3):
    """v2 draw: white upcoming, 45% dim spoken, ONE accent active (+1.15x),
    dark stroke, no glow/ghost, karaoke progress underline below band."""
    d = ImageDraw.Draw(im)
    fp = lay["font_px"]
    lh = int(fp * 1.24)
    ymid = (band0 + band1) // 2
    nl = len(lay["lines"])
    for li, line in enumerate(lay["lines"]):
        y = ymid + (li - (nl - 1) / 2.0) * lh
        for b in [x for x in lay["boxes"] if x["line"] == li]:
            gi = b["idx"] + sum(len(lay["lines"][k]) for k in range(li))
            is_act = gi == st["active"]
            spoken = gi in st["spoken"]
            wordx = b["word"]
            if is_act:
                fill = accent
            elif spoken:
                v = int(255 * ACCENT_DIM_F)
                fill = (v, v, v)
            else:
                fill = (255, 255, 255)
            f2 = bfont(int(fp * ACTIVE_SCALE)) if is_act else bfont(fp)
            d.text(((b["x0"] + b["x1"]) / 2, y), wordx, font=f2, fill=fill,
                   stroke_width=stroke, stroke_fill=(10, 10, 10), anchor="mm")
    # CV7: underline = karaoke progress only (accent), below band; gone when no state
    act_box = lay["boxes"][min(st["active"], len(lay["boxes"]) - 1)]
    li = act_box["line"]
    lb = [x for x in lay["boxes"] if x["line"] == li]
    span0, span1 = lb[0]["x0"], lb[-1]["x1"]
    uw = max(int(fp * 2), int((span1 - span0) * max(0.12, st["prog"])))
    ux0 = (im.size[0] - uw) // 2
    d.rectangle([ux0, band1 + 8, ux0 + uw, band1 + 13], fill=accent)
    return im
