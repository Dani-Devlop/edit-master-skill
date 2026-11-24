#!/usr/bin/env python3
"""Phase 18 shared two-font karaoke engine (used by p18_render, p18_gate, p18_critique).
ST5: tight bold sans body + serif accent keyword center-first; full sentence always;
active=accent+1.2x; spoken dim 45%; upcoming white; sweep LOOP until sentence change.
NO typewriter/partial words. Deterministic boxes exported for gates."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ACCENT_DIM_F = 0.45
ACTIVE_SCALE = 1.2
DROP_TOKENS = ("-", "--", "\u2014")


def sfont(px):
    return ImageFont.truetype(SERIF_B, px)


def bfont(px):
    return ImageFont.truetype(SANS_B, px)


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


def kar2_state(t, windows):
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
            active = 0 if lt <= s[0]["t0"] else len(s) - 1
            for i2, w in enumerate(s):
                if w["t0"] - 0.03 <= lt < w["t1"] + 0.03:
                    active = i2
                    break
            return {"win": win, "s": s, "active": active,
                    "spoken": set(range(active)), "looped": looped}
    return None


def kar2_layout(sents, out_w, font_px=54, kws=frozenset(), width_frac=0.90, max_lines=2):
    """two-font deterministic layout; widths reserved at ACTIVE scale (1.2x)."""
    chosen = font_px
    gap = int(chosen * 0.30)
    probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))

    def wpx(word, px):
        f = sfont(int(px * 1.06)) if word.upper() in kws else bfont(px)
        return text_w2(word, f, probe) * ACTIVE_SCALE

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
    return {"lines": lines_i, "boxes": boxes, "font_px": chosen}


def draw_kar2(im, st, lay, accent, band0, band1, kws=frozenset(), stroke=3):
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
            kw = wordx.upper() in kws
            if is_act:
                fill = accent
            elif spoken:
                fill = (int(255 * ACCENT_DIM_F),) * 3
            else:
                fill = accent if kw else (255, 255, 255)
            if is_act:
                f2 = sfont(int(fp * 1.06 * ACTIVE_SCALE)) if kw else bfont(int(fp * ACTIVE_SCALE))
                gl = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dg = ImageDraw.Draw(gl)
                dg.text(((b["x0"] + b["x1"]) / 2, y), wordx, font=f2,
                        fill=accent + (150,), anchor="mm")
                gl = gl.filter(ImageFilter.GaussianBlur(7))
                im.paste(Image.alpha_composite(im.convert("RGBA"), gl).convert("RGB"), (0, 0))
                d = ImageDraw.Draw(im)
            else:
                f2 = sfont(int(fp * 1.06)) if kw else bfont(fp)
            d.text(((b["x0"] + b["x1"]) / 2, y), wordx, font=f2, fill=fill,
                   stroke_width=stroke, stroke_fill=(10, 10, 10), anchor="mm")
    return im
