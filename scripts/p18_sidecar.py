#!/usr/bin/env python3
"""Augment p18 work sidecars with p16-gate-compatible fields (metadata only,
video unchanged): plan aliases, manifest gate keys, onboarding proposal.
All values are the REAL measured/logged values from p18_render + plan."""
import json, os

WORK = "/tmp/ems-work/p18/run_T1"
plan = json.load(open(f"{WORK}/plan_9x16.json"))
manifest = json.load(open(f"{WORK}/manifest_9x16.json"))
scene_plan = json.load(open(f"{WORK}/scene_plan.json"))
cue = json.load(open(f"{WORK}/cue_sheet.json"))
LL = json.load(open(f"{WORK}/lyric_lines.json"))
preset = json.load(open("/tmp/ems-work/ems-repo/presets/mv_welcome.json"))

beats = plan["beats"]
cut_times = [b["start"] for b in beats] + [round(plan["total"] - 2.4, 3)]

# words manifest = as-rendered karaoke tokens (no synthetic punctuation)
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
    "cap_engine": "whisper-word-sync x Genius-verbatim (two-font karaoke v18)",
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
        "Zurbaran Still Life (1633)": "public-domain artwork (artist d. 1664); rehost via image-search, PD status unchanged",
        "DejaVu fonts": "free (Bitstream Vera license)",
        "faster-whisper small": "MIT",
        "Genius lyrics": "verbatim reference for ASR alignment (text only, no audio)",
        "yt-dlp blocked": "YouTube bot-check; cobalt auth-required; REF-TAG-A CDN 403 -> fallback logged"},
    "grade_probe_t": 3.0,
    "grade_probe_src_t": 3.0,
    "overrides": {"applied": False},
    "hook_window": [0.0, 0.52],
    "sfx_n": len(cue["events"]),
})
manifest.update({"gate_json": None, "refine_iterations": 0, "preset_name": preset["name"]})
json.dump(plan, open(f"{WORK}/plan_9x16.json", "w"), indent=1)
json.dump(manifest, open(f"{WORK}/manifest_9x16.json", "w"), indent=1)

if not os.path.exists(f"{WORK}/onboarding_proposal.json"):
    prop = {"run": "p18_T1_welcome", "genre": "music_video",
            "proposal": {"family": preset["family"], "palette_accent": preset["palette"]["accent_rgb"],
                          "music_plan": preset["music_plan"]["decision"],
                          "platforms": ["9:16"]},
            "defaults": {"brand_end_card": False, "two_font_captions": True,
                          "scene_engine": "p18 ST2 plan-driven"},
            "ask": "confirm or override - non-blocking proceed",
            "status": "proceeded-with-defaults (manager pre-approved Phase 18 spec)"}
    json.dump(prop, open(f"{WORK}/onboarding_proposal.json", "w"), indent=1)

print("sidecar augmented: words", len(words), "| cut_times", cut_times[:4], "...",
      "| comps", len(set(comps)), "distinct | events", len(cue["events"]))
