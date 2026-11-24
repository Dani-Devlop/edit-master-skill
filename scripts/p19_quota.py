#!/usr/bin/env python3
"""Rebuild quota_forecast.json from lyric_lines.json (Phase 19 run-stage helper;
same formulas as p18_plan.py quota block). Usage: p19_quota.py <work_dir>"""
import json, sys, os

WORK = sys.argv[1]
LL = json.load(open(os.path.join(WORK, "lyric_lines.json")))
lines = LL["lines"]
SRC_DUR = max(l["t1"] for l in lines)

quota = {
    "designed_scene_frac": round(sum(
        (l["scene"]["type"] != "S01_aroll_captions") * (l["t1"] - l["t0"]) for l in lines)
        / SRC_DUR, 2),
    "n_scene_types": len({l["scene"]["type"] for l in lines}),
    "types": sorted({l["scene"]["type"] for l in lines}),
    "no_consecutive_same": all(lines[i]["scene"]["type"] != lines[i - 1]["scene"]["type"]
                               for i in range(1, len(lines))),
    "wow_moments": ["type-slam lockup", "starburst pop", "tape slam", "whip", "mask-wipe",
                    "invert bite", "odometer", "arc counter", "painting slide", "object callout"],
    "camera_moves": ["freeze shake", "punch-in", "subject track", "zoom-through",
                     "feathered mask wipe"],
    "frame1_composed": True,
    "end_card_no_brand": True,
}
json.dump(quota, open(os.path.join(WORK, "quota_forecast.json"), "w"), indent=1)
print("QUOTA:", json.dumps({k: quota[k] for k in ("designed_scene_frac", "n_scene_types",
                                                  "no_consecutive_same")}))
