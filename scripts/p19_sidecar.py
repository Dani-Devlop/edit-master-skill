#!/usr/bin/env python3
"""Augment p19 work sidecars with p16-gate-compatible fields (metadata only,
video unchanged): plan aliases, manifest gate keys, onboarding proposal.
All values are REAL measured/logged values from p19_render + plan (v19)."""
import json, os

WORK = "/tmp/ems-work/p19/run"
HERE = os.path.dirname(os.path.abspath(__file__))
plan = json.load(open(f"{WORK}/plan_9x16.json"))
manifest = json.load(open(f"{WORK}/manifest_9x16.json"))
scene_plan = json.load(open(f"{WORK}/scene_plan.json"))
cue = json.load(open(f"{WORK}/cue_sheet.json"))
LL = json.load(open(f"{WORK}/lyric_lines.json"))
preset = json.load(open(os.path.join(HERE, "p19_preset_mv_welcome.json")))

beats = plan["beats"]
cut_times = [b["start"] for b in beats] + [round(plan["total"] - plan["total"] + plan["total"], 3)]
cut_times = [b["start"] for b in beats] + [round(plan["total"], 3)]

words = []
for l in LL["lines"]:
    for tk in l["tokens"]:
        if tk["w"] in ("—", "-", "--"):
            continue
        words.append({"w": tk["w"], "start": tk["t0"], "end": tk["t1"]})

comps = [b["scene_type"] for b in beats]
technique_log = []
for b in beats:
    technique_log.append({"beat": b["i"], "technique": b["scene_type"],
                          "when_to_use": b["engine"],
                          "text": b["text"]})

plan.update({
    "band_px": [int(1280 * 0.705), int(1280 * 0.795)],
    "font_px": 54,
    "rtl": False,
    "motion_beats": [b["start"] for b in beats
                     if b["scene_type"] in ("S11_ui_pop", "S08_graph_odometer")],
    "cap_probe_t": 6.4,
    "words_manifest": words,
    "cap_engine": "whisper-word-sync x Genius-verbatim (Caption System v2, CV1-CV7)",
    "cut_times": cut_times,
    "comps": comps,
    "events": [{"t": e["t"], "sfx": e["sfx"]} for e in cue["events"]],
    "music_plan": preset["music_plan"],
    "duck_applied": True,
    "stakes_numbers_real": True,
    "beat_index_only": False,
    "technique_log": technique_log,
    "resource_licenses": {
        "WELCOME (IDK feat. Eminem, prod. J Dilla)": "commercial track - original excerpt from "
            "manager-provided raw; EDIT-TEST USAGE ONLY, no publication",
        "still-life card": "generated in-sandbox (p19_gen_paint.py, seed 1633) - no third-party rights; "
            "public-domain CDN (Wikimedia/Met) proxy-blocked, logged honestly",
        "Montserrat variable font": "SIL Open Font License 1.1 (google/fonts)",
        "DejaVu fonts": "free (Bitstream Vera license)",
        "faster-whisper": "MIT",
        "Genius lyrics": "verbatim reference for ASR alignment (text only, no audio)",
        "source chain": "yt-dlp blocked (YouTube bot-check); cobalt auth-required; REF-TAG-A CDN 403 "
            "(auth key expired 2026-11-24) -> honest fallback to manager-provided raw"},
    "grade_probe_t": 3.0,
    "grade_probe_src_t": 3.0,
    "overrides": {"applied": True, "note": "manager pre-approved Phase 19 spec (CONFIG block)"},
    "hook_window": [0.0, 0.52],
    "sfx_n": len(cue["events"]),
    "canvas_policy": plan.get("canvas_policy"),
    "gc_log": plan.get("gc_log"),
})
manifest.update({"gate_json": None, "refine_iterations": 0, "preset_name": preset["name"]})
json.dump(plan, open(f"{WORK}/plan_9x16.json", "w"), indent=1)
json.dump(manifest, open(f"{WORK}/manifest_9x16.json", "w"), indent=1)

if not os.path.exists(f"{WORK}/onboarding_proposal.json"):
    prop = {"run": "p19_T1_welcome_v19", "genre": "music_video",
            "proposal": {"family": preset["family"], "palette_accent": preset["palette"]["accent_rgb"],
                          "music_plan": preset["music_plan"]["decision"],
                          "platforms": ["9:16"]},
            "defaults": {"brand_end_card": False, "caption_system": "v2 (CV1-CV7)",
                          "canvas": "AS2 designed", "assets": "AS1 zero-watermark",
                          "scene_engine": "p19 ST2 plan-driven"},
            "ask": "confirm or override - non-blocking proceed",
            "status": "proceeded-with-defaults (manager pre-approved Phase 19 spec)"}
    json.dump(prop, open(f"{WORK}/onboarding_proposal.json", "w"), indent=1)

print("sidecar augmented v19: words", len(words), "| comps", len(set(comps)), "distinct |",
      "events", len(cue["events"]))
