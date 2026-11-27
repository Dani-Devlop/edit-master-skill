#!/usr/bin/env python3
"""Independent blind critic x3 median protocol (measurement-integrity fix R6):
same frames, 3 fresh z-ai vision calls, NO claims/specs; aggregate = median
overall + per-axis mean of the two runs closest to median (trim noise).
Usage: critic_v22x3.py <sheet.jpg> <out.json>"""
import sys, json, subprocess, statistics

sheet, out = sys.argv[1], sys.argv[2]
import os
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "critic_v22.py")
runs = []
for k in range(3):
    tmp = f"/tmp/ems-work/p22/critic_x3_{k}.json"
    rc = subprocess.run([sys.executable, SCRIPT, sheet, tmp],
                        capture_output=True, text=True, timeout=280)
    try:
        d = json.load(open(tmp))
        if "overall" in d:
            runs.append(d)
    except Exception:
        pass

if not runs:
    json.dump({"error": "all critic calls failed"}, open(out, "w"), indent=1)
    print("CRITIC-X3 FAILED")
    sys.exit(1)

overs = [r["overall"] for r in runs]
med = statistics.median(overs)
# keep the two runs nearest the median for axis averaging
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
top_gaps = sorted(gaps, key=gaps.get, reverse=True)[:4]
res = {"runs_overall": overs, "median_overall": med, "axes_avg": axes_avg,
       "top_gaps": top_gaps, "n_valid_runs": len(runs)}
json.dump(res, open(out, "w"), indent=1)
print("CRITIC-X3 runs:", overs, "MEDIAN:", med)
