#!/usr/bin/env python3
"""T-1 v24 master blind critic x3 — z-ai vision on the contact sheet, absolute
rubric (no target/replioca comparison; the reel IS the artifact). Fresh calls,
no claims/specs leakage (R6 honesty rule). Same JSON schema as critic_v22.py so
critic_v22x3.py aggregates it unchanged."""
import sys, json, subprocess

sheet = sys.argv[1]
out = sys.argv[2]
PROMPT = """You are an independent motion-design critic scoring a vertical music-video reel.
You see a contact sheet of 16 frames sampled across the reel (1080x1920, 27.9s).
Score the REEL on these axes, 0-10 each, from frame evidence only:
1. panel_grid: composition/density — full-frame designed canvases, editorial layering, no large flat-black void zones
2. people_cutouts: masked cut-out people integrated with footage (hooks, occlusion, placement)
3. typography_register: giant display words vs mono whispers, correct scale hierarchy, no clipped glyphs
4. sticker_vocabulary: semantic stickers (hourglass/coins/caution-tape/lemon/confetti/arrows) used purposefully, not random emoji
5. color_story: disciplined B&W world + single volt accent; no off-world color drift
6. density_overlap: elements overlap/bleed with gutters; frames feel full (designed tissue, not placeholder)
7. motion_feel: from stills — entrance states, kick pulses, parallax, tilts, speed-ramp labels readable
8. overall_impression: would a viewer rate this IG-native, editorial, premium?
Return STRICT JSON only:
{"rows": [{"t": <frame index>, "panel_grid": 0-10, "people_cutouts": 0-10, "typography_register": 0-10,
  "sticker_vocabulary": 0-10, "color_story": 0-10, "density_overlap": 0-10,
  "motion_feel": 0-10, "overall_impression": 0-10, "note": "<=25 words"}],
 "axes_avg": {"panel_grid": x, "...": x}, "overall": 0-10,
 "top_gaps": ["gap1", "gap2", "gap3"]}"""

r = subprocess.run(["z-ai", "vision", "-i", sheet, "-p", PROMPT],
                   capture_output=True, text=True, timeout=240)
raw = r.stdout
# z-ai CLI wraps the answer in an SDK envelope: {"choices":[{"message":{"content":"```json ...```"}}]}
js = None
try:
    env = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    content = env["choices"][0]["message"]["content"]
    if "```json" in content:
        js = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        js = content.split("```")[1].split("```")[0].strip()
    else:
        js = content.strip()
except Exception:
    pass
if js is None:
    s, e = raw.find("{"), raw.rfind("}")
    if s >= 0 and e > s:
        js = raw[s:e + 1]
if js and not js.lstrip().startswith("{"):
    s, e = js.find("{"), js.rfind("}")
    js = js[s:e + 1] if e > s else None
try:
    d = json.loads(js)
    d["critic_input"] = "contact_sheet_T1_v24.jpg (16 decoded frames, absolute rubric)"
    json.dump(d, open(out, "w"), indent=1)
    print("CRITIC overall:", d.get("overall"))
except Exception as e:
    json.dump({"error": str(e), "raw": raw[:800]}, open(out, "w"), indent=1)
    print("CRITIC FAILED:", e)
