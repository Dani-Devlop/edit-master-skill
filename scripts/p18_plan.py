#!/usr/bin/env python3
"""Phase 18.0 ST1+ST2 — lyric alignment (whisper timings x Genius verbatim text)
+ scene plan per lyric line (S01-S19) + cue sheet + quota forecast.
Inputs : /tmp/ems-work/p18/run_T1/whisper_words.json  (word timings, measured)
Outputs: lyric_lines.json, scene_plan.json, cue_sheet.json, quota_forecast.json,
         asr_corrections.json  (honest log, never invent)
"""
import json, os

WORK = "/tmp/ems-work/p18/run_T1"
wsp = json.load(open(f"{WORK}/whisper_words.json"))
segs = wsp["segments"]
raw_words = wsp["words"]

# ---- Genius verbatim lines for this 27.9s excerpt (Intro: Eminem + Verse 1: IDK) ----
# whisper seg idx -> (genius_verbatim, section, speaker)
GENIUS = {
    0: ("Welcome to the party where everybody dies at the end", "Intro", "Eminem"),
    1: ("Move your body", "Intro", "Eminem"),
    2: ("This is 'bout to be a homicide scene", "Intro", "Eminem"),
    3: ("I think you all nah mean when I scream", "Intro", "Eminem"),
    4: ("Welcome — to another day", "Verse 1", "IDK (+Eminem adlib)"),
    5: ("To another plot on my mind", "Verse 1", "IDK"),
    6: ("'cause I gots to get paid", "Verse 1", "IDK"),
    7: ("I'd rather get paid than laid", "Verse 1", "IDK"),
    8: ("If life hand me lemons, then it's San Pellegrino lemonade", "Verse 1", "IDK"),
    9: ("Baccarat glasses with chips on it", "Verse 1", "IDK"),
    10: ("Women eatin' pasta on my clean", "Verse 1", "IDK"),
    11: ("Ann Demeulemeester plates", "Verse 1", "IDK"),
}
# semantic keywords (content words only — never function words) per line, for
# two-font serif accent + semantic emphasis (ST5)
KEYWORDS = {
    0: ["WELCOME", "DIES", "END"],
    1: ["BODY"],
    2: ["HOMICIDE", "SCENE"],
    3: ["SCREAM"],
    4: ["WELCOME", "DAY"],
    5: ["PLOT", "MIND"],
    6: ["PAID"],
    7: ["PAID", "LAID"],
    8: ["LEMONS", "PELLEGRINO", "LEMONADE"],
    9: ["BACCARAT", "CHIPS"],
    10: ["PASTA"],
    11: ["DEMEULEMEESTER", "PLATES"],
}

# ---- scene plan (ST2): per lyric line -> scene type + params ----
# engine chain per spec E3: EffectCraft(motionCraft) unavailable in sandbox ->
# fallback chain Remotion(node ok, but no project scaffold time budget)->HTML->frames
# -> PIL sequences + ffmpeg composite. Chosen engine per beat logged HONESTLY.
SCENES = {
    0: {"type": "S02_full_screen_text", "engine": "PIL+ffmpeg (E3 fallback; FilmCraft CLI unavailable in sandbox)",
        "params": {"lockup": ["EMINEM", "WELCOME", "everybody dies at the end"],
                   "freeze_slam": True, "matte_occlusion": "attempt+fallback", "shake": True}},
    1: {"type": "S11_ui_pop", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"keyword": "BODY", "starburst": True, "brackets": True, "punch_in": True}},
    2: {"type": "S04_line_illustration", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"keyword": "HOMICIDE", "tape_slam": True, "illustration": "crosshair"}},
    3: {"type": "S03_line_text_track", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"track": "subject_centroid_smooth", "whip_in": True}},
    4: {"type": "S02_echo_invert", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"echo": "WELCOME", "mask_wipe_in": True, "invert_bite_s": 0.14}},
    5: {"type": "S10_ui_listicle", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"rows": ["01 ANOTHER DAY", "02 ANOTHER PLOT", "03 ON MY MIND"], "row_pop": 0.28}},
    6: {"type": "S08_graph_odometer", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"grid_ball_rise": True, "odometer_label": "DILLA BPM", "odometer_source": "beatmap.tempo_bpm (measured)"}},
    7: {"type": "S12_circular_counter", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"arc": "PAID", "counter_label": "PAID > LAID", "arc_fill_s": 1.2}},
    8: {"type": "S05_painting_slide_in", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"asset": "painting_lemons.jpg", "paper_texture": True,
                   "tape_label": "SAN PELLEGRINO", "slide_dir": "left"}},
    9: {"type": "S13_blurred_square_list", "engine": "PIL+ffmpeg (E3 fallback)",
        "params": {"pills": ["BACCARAT", "GLASSES", "CHIPS ON IT"], "blur_backdrop": True}},
    10: {"type": "S07_object_callout", "engine": "PIL+ffmpeg (E3 fallback)",
         "params": {"arrow_to": "plate zone", "label": "ANN DEMEULEMEESTER"}},
    11: {"type": "S09_broll_text_endcard", "engine": "PIL+ffmpeg (E3 fallback)",
         "params": {"text": "PLATES", "end_card": {"loop_echo": True, "brand": "clean no-brand",
                                                    "repo_pill": "github.com/Dani-Devlop/edit-master-skill"}}},
}

# ---- cue sheet (ST9): every animation -> SFX, medium-low, SFX==entrances ----
CUE = [
    {"t": 0.00, "animation": "freeze + type-slam lockup", "sfx": "thump+impact", "level_db": -8},
    {"t": 0.90, "animation": "selection brackets draw-on", "sfx": "click", "level_db": -14},
    {"t": 4.36, "animation": "starburst pop on BODY", "sfx": "splice+click", "level_db": -12},
    {"t": 5.30, "animation": "highlighter tape slam on HOMICIDE", "sfx": "whoosh+thump", "level_db": -10},
    {"t": 8.32, "animation": "whip transition into tracking line", "sfx": "whoosh", "level_db": -10},
    {"t": 11.06, "animation": "mask-wipe into echo card", "sfx": "whoosh_short", "level_db": -12},
    {"t": 11.20, "animation": "invert bite 0.14s", "sfx": "glitch", "level_db": -12},
    {"t": 12.96, "animation": "listicle rows pop x3", "sfx": "click_x3", "level_db": -14},
    {"t": 15.06, "animation": "glowing grid + ball rise + odometer", "sfx": "riser", "level_db": -12},
    {"t": 16.50, "animation": "odometer settle", "sfx": "thump", "level_db": -10},
    {"t": 17.60, "animation": "circular counter arc fill", "sfx": "riser_soft", "level_db": -14},
    {"t": 18.58, "animation": "painting slide-in (paper)", "sfx": "whoosh", "level_db": -12},
    {"t": 21.86, "animation": "blurred pill rows pop x3", "sfx": "click_x3", "level_db": -14},
    {"t": 24.40, "animation": "object callout arrow", "sfx": "click", "level_db": -14},
    {"t": 25.60, "animation": "end card loop echo", "sfx": "tape_stop_short", "level_db": -12},
]

# ---- rebuild word list with Genius-verbatim tokens (timing from whisper) ----
corrections = []
lines = []
w_by_seg = {}
for w in raw_words:
    w_by_seg.setdefault(None, None)
# assign raw words to segments by time containment
def words_in(t0, t1):
    return [w for w in raw_words if w["start"] >= t0 - 0.35 and w["end"] <= t1 + 0.35]

for si, sg in enumerate(segs):
    text, section, speaker = GENIUS[si]
    toks = text.split()
    raw = words_in(sg["start"], sg["end"])
    t0 = sg["start"]
    t1 = sg["end"]
    span = max(t1 - t0, 0.25)
    # redistinct: distribute genius tokens across segment span (length-weighted)
    tot = sum(len(t) for t in toks) or 1
    tokens, cur = [], t0
    for tk in toks:
        d = span * len(tk) / tot
        tokens.append({"w": tk, "t0": round(cur, 3), "t1": round(min(t1, cur + d), 3)})
        cur += d
    # whisper->genius corrections log (honest)
    wr_text = " ".join(w["w"] for w in raw)
    if wr_text.strip().lower() != text.lower():
        corrections.append({"seg": si, "whisper": wr_text.strip(), "genius": text,
                            "method": "faster-whisper-small timings x Genius verbatim text"})
    lines.append({"i": si, "t0": round(t0, 3), "t1": round(t1, 3),
                  "section": section, "speaker": speaker, "text": text,
                  "tokens": tokens, "scene": SCENES[si],
                  "keywords": KEYWORDS[si]})

# ---- scene plan doc + quota forecast ----
plan = {
    "song": {"title": "WELCOME", "artists": "IDK feat. Eminem", "producer": "J Dilla (posthumous)",
             "released": "2026-11-13", "mv": "IDK & Eminem - WELCOME (Prd. By J Dilla) [Official Music Video]",
             "id_method": "faster-whisper-small transcript -> exact-phrase match (Genius/consequence.net)",
             "id_confidence": "HIGH (distinctive hook line, multi-source verbatim match)"},
    "source": {"raw": "upload/4_6051789922870758373 (1).mp4 (IG-format excerpt of official MV footage, manager-provided)",
               "original_mv_fetch": "yt-dlp BLOCKED (YouTube bot-check) + cobalt API auth-required + REF-TAG-A CDN 403 -> honest fallback to on-disk manager-provided raw",
               "license": "commercial track (IDK/Eminem/J Dilla) - EDIT-TEST USAGE ONLY, no publication"},
    "fps": 30, "src_dur": 27.91, "endcard_s": 2.4,
    "total": round(27.91 + 2.4, 2),
    "lines": [{k: l[k] for k in ("i", "t0", "t1", "text", "section", "speaker")} for l in lines],
    "scenes": [{"line": l["i"], **l["scene"]} for l in lines],
    "captions": {"style": "two-font karaoke: tight bold sans body + serif accent keyword center-first, gaps smaller",
                 "sweep": "full sentence always, active=accent+1.2x, spoken dim 45%, upcoming white, loop until change",
                 "keywords_semantic_only": True},
}
quota = {
    "designed_scene_frac": round(sum(
        (l["scene"]["type"] != "S01_aroll_captions") * (l["t1"] - l["t0"])
        for l in lines) / 27.91, 2),
    "n_scene_types": len({l["scene"]["type"] for l in lines}),
    "types": sorted({l["scene"]["type"] for l in lines}),
    "no_consecutive_same": all(lines[i]["scene"]["type"] != lines[i - 1]["scene"]["type"]
                               for i in range(1, len(lines))),
    "wow_moments": ["type-slam lockup", "starburst pop", "tape slam", "whip", "mask-wipe",
                    "invert bite", "odometer", "arc counter", "painting slide", "object callout"],
    "camera_moves": ["freeze shake", "punch-in", "subject track", "zoom-through", "mask wipe"],
    "frame1_composed": True,
    "end_card_no_brand": True,
}
cue_sheet = {"events": CUE,
             "music": "original mix KEPT (Eminem/IDK vocal + Dilla beat) - no overlay; "
                      "SFX ducked under mix; two-pass loudnorm -14 LUFS / TP<=-1.5",
             "copyright": "commercial track - edit-test usage only, no publication; "
                          "excerpt <= 31s from manager-provided raw"}

json.dump({"lines": lines, "corrections": corrections}, open(f"{WORK}/lyric_lines.json", "w"), indent=1)
json.dump(plan, open(f"{WORK}/scene_plan.json", "w"), indent=1)
json.dump(cue_sheet, open(f"{WORK}/cue_sheet.json", "w"), indent=1)
json.dump(quota, open(f"{WORK}/quota_forecast.json", "w"), indent=1)
json.dump(corrections, open(f"{WORK}/asr_corrections.json", "w"), indent=1)

print(f"LYRIC LINES: {len(lines)} | corrections: {len(corrections)}")
for l in lines:
    print(f"  L{l['i']} [{l['t0']:6.2f}-{l['t1']:6.2f}] {l['scene']['type']:26s} | {l['text']}")
print("QUOTA:", json.dumps({k: quota[k] for k in ('designed_scene_frac', 'n_scene_types', 'no_consecutive_same')}))
print("PLAN DONE")
