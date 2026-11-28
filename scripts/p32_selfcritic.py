#!/usr/bin/env python3
"""Phase 32 F9 — IG-MATCH (honest protocol):
- IG reference frames (4-quadrant P2 / Raw-Edited P3 / Hera P1) are NOT
  reachable: absent from repo since ingest (docs/REFERENCES.md marks PENDING)
  and yt-dlp remains bot-blocked (26.04). Owner asked again in the report.
- Delivered INSTEAD (nothing fabricated): (a) self-critic x3 — z-ai vision,
  3 fresh calls, rubric-only prompt over a supercut contact sheet, no target
  claims; (b) grammar-conformance notes vs docs/REFERENCES.md documented
  motion grammars A (single-column lockups) / B (4-quadrant collage).
  match% vs actual IG refs stays PENDING."""
import os
import sys
import json
import subprocess
import statistics

import cv2
import numpy as np
from PIL import Image

WORK = "/tmp/ems-work/p32r2"
REELS = f"{WORK}/reels"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "test-results", "p32", "selfcritic_supercut_x3.json")

SRC = f"{REELS}/supercut_v2_31s.mp4"
SHEET = f"{WORK}/supercut_contact_sheet.jpg"

# 1) contact sheet 12 frames
cap = cv2.VideoCapture(SRC)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frames = []
for i in [int(k * (n - 1) / 11.0) for k in range(12)]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ok, fr = cap.read()
    if ok:
        frames.append(Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((240, 427)))
cap.release()
cols, rows = 6, 2
sheet_img = Image.new("RGB", (cols * 246 + 6, rows * 433 + 6), (24, 24, 26))
for k, im in enumerate(frames):
    sheet_img.paste(im, (6 + (k % cols) * 246, 6 + (k // cols) * 433))
sheet_img.save(SHEET, quality=88)
print("sheet:", SHEET, len(frames), "frames")

PROMPT = """You are an independent motion-design critic. You see a contact sheet of 12 frames
from a short-form edit reel (9:16). NO target/reference is provided — score the reel ABSOLUTELY
on these axes, 0-10 each:
1. structural_grammar: scene structure variety (hook / footage / card / listicle / end card), clean composition
2. people_subjects: subjects/footage read clearly (graded, framed, not mushy)
3. typography_register: display type scale hierarchy, stroke/fit discipline, no clipped glyphs
4. sticker_vocabulary: semantic volt accents (scribble/arrows/pills/listicle bars), not random decoration
5. color_story: disciplined single-accent palette (B&W + volt), no off-world chroma
6. density_overlap: density without voids, no glyph collisions
7. motion_feel: entrance states/camera life readable in stills
8. overall_impression: would this pass as a polished creator reel?
Return STRICT JSON only:
{"axes_avg": {"structural_grammar": x, "people_subjects": x, "typography_register": x,
  "sticker_vocabulary": x, "color_story": x, "density_overlap": x, "motion_feel": x,
  "overall_impression": x}, "overall": 0-10, "top_gaps": ["g1", "g2", "g3"]}"""

def parse_cli(raw):
    """z-ai CLI prints banner + JSON envelope; model output = choices[0].message.content."""
    try:
        s, e = raw.find("{"), raw.rfind("}")
        if s < 0 or e <= s:
            return None
        env = json.loads(raw[s:e + 1])
        content = env["choices"][0]["message"]["content"]
    except Exception:
        content = raw
    for opener, closer in (("```json", "```"), ("```", "```")):
        if opener in content:
            return content.split(opener)[1].split(closer)[0].strip()
    a, b = content.find("{"), content.rfind("}")
    return content[a:b + 1].strip() if (a >= 0 and b > a) else None


runs = []
for k in range(3):
    r = subprocess.run(["z-ai", "vision", "-i", SHEET, "-p", PROMPT],
                       capture_output=True, text=True, timeout=280)
    js = parse_cli(r.stdout)
    try:
        d = json.loads(js)
        if "overall" in d:
            runs.append(d)
            print(f"run{k}: overall {d['overall']}")
    except Exception as e:
        print(f"run{k} parse fail:", str(e)[:80], (js or "")[:120])

if not runs:
    json.dump({"error": "all critic calls failed"}, open(OUT, "w"), indent=1)
    print("SELF-CRITIC FAILED")
    sys.exit(1)

overs = [r["overall"] for r in runs]
med = statistics.median(overs)
ranked = sorted(runs, key=lambda r: abs(r["overall"] - med))[:2]
axes = {}
for r in ranked:
    for k, v in (r.get("axes_avg") or {}).items():
        axes.setdefault(k, []).append(v)
axes_avg = {k: round(sum(v) / len(v), 2) for k, v in axes.items()}
gaps = {}
for r in ranked:
    for g in (r.get("top_gaps") or []):
        gaps[g] = gaps.get(g, 0) + 1
res = {
    "protocol": "self-critic x3 rubric-only (NO IG target refs reachable — match% stays PENDING)",
    "refs_status": {"P1_Hera": "absent", "P2_4quadrant": "absent", "P3_raw_edited": "absent",
                    "yt_dlp": "bot-blocked since 26.04", "owner": "asked again in Ph32 report"},
    "sheet": SHEET,
    "runs_overall": overs, "median_overall": med, "axes_avg": axes_avg,
    "top_gaps": sorted(gaps, key=gaps.get, reverse=True)[:4],
    "grammar_conformance": {
        "vs_A_single_column_lockups": "our reels use single-column full-frame footage + lockups (REFERENCES.md grammar A) on hook/footage/endcard ops",
        "vs_B_4quadrant_collage": "4-quadrant collage is a v26-master-scene grammar; preset reels use video-in-card as the collage-family stand-in (1 card per scene) — documented, not silent"},
}
json.dump(res, open(OUT, "w"), indent=1)
print("SELF-CRITIC-X3 runs:", overs, "MEDIAN:", med)
