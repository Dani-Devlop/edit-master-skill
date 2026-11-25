#!/usr/bin/env python3
"""Independent blind critic v22 — z-ai vision, fresh call, ONLY frames + neutral rubric.
The critic call receives NO claims, NO specs, NO prior scores (R6 honesty rule).
Usage: critic_v22.py <sheet.jpg> <out.json>"""
import sys, json, subprocess, os

sheet = sys.argv[1]
out = sys.argv[2]
PROMPT = """You are an independent motion-design critic. You see a contact sheet: each row shows
LEFT = TARGET frame (a reference reel), RIGHT = REPLICA frame (a clone attempt) at the same clock time.
Score the REPLICA's motion-language fidelity to the TARGET on these axes, 0-10 each:
1. panel_grid: same structural grammar (2x2 editorial collage, panel types, gutters) vs flat/sparse
2. people_cutouts: masked cut-out people present and placed like target
3. typography_register: giant serif/sans display words + mono whispers, correct scale hierarchy
4. sticker_vocabulary: pills/arrows/coins/scribbles/badges/app-icons used like target (semantic, not random)
5. color_story: canvas palette families and accent usage match (white/black/red+accent, not off-world)
6. density_overlap: element density and overlapping/bleed feel (no large empty zones, no placeholder bars)
7. motion_feel: from frame evidence (entrance states, tilt, scale bounces readable in stills)
8. overall_impression: would a viewer say "same editor made both"?
Return STRICT JSON only:
{"rows": [{"t": 0.3, "panel_grid": 0-10, "people_cutouts": 0-10, "typography_register": 0-10,
  "sticker_vocabulary": 0-10, "color_story": 0-10, "density_overlap": 0-10,
  "motion_feel": 0-10, "overall_impression": 0-10, "note": "<=25 words"}],
 "axes_avg": {"panel_grid": x, "...": x}, "overall": 0-10,
 "top_gaps": ["gap1", "gap2", "gap3"]}"""

r = subprocess.run(["z-ai", "vision", "-i", sheet, "-p", PROMPT],
                   capture_output=True, text=True, timeout=240)
raw = r.stdout
# extract JSON block
js = None
for opener, closer in (("```json", "```"), ("```", "```")):
    if opener in raw:
        block = raw.split(opener)[1].split(closer)[0]
        js = block.strip()
        break
if js is None:
    s, e = raw.find("{"), raw.rfind("}")
    if s >= 0 and e > s:
        js = raw[s:e + 1]
# unescape escaped-JSON responses
if js and "\\" in js and js.lstrip().startswith('"') is False and '\n' not in js.replace('\\n',''):
    try:
        unesc = js.encode().decode('unicode_escape')
        if unesc.strip().startswith("{"):
            js = unesc
    except Exception:
        pass
if js and not js.lstrip().startswith("{"):
    s, e = js.find("{"), js.rfind("}")
    if s >= 0 and e > s:
        js = js[s:e + 1]
if js is None:
    open(out, "w").write(json.dumps({"error": raw[:2000], "stderr": r.stderr[:500]}, indent=1))
    print("CRITIC RAW (no json) saved; tail:", raw[-400:])
    sys.exit(1)
try:
    parsed = json.loads(js)
    # unwrap z-ai choices envelope -> parse inner content JSON
    if isinstance(parsed, dict) and "choices" in parsed:
        inner = parsed["choices"][0]["message"]["content"]
        s2, e2 = inner.find("{"), inner.rfind("}")
        if s2 >= 0 and e2 > s2:
            parsed = json.loads(inner[s2:e2 + 1])
except Exception as ex:
    parsed = {"error": str(ex), "raw": js[:2000]}
open(out, "w").write(json.dumps(parsed, indent=1))
ov = parsed.get("overall")
print("CRITIC OVERALL:", ov)
for g in parsed.get("top_gaps", [])[:4]:
    print("GAP:", g)
