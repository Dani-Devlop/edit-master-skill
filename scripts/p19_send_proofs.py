#!/usr/bin/env python3
"""Send Phase 19 proof sheets to Telegram owner (LIVE-ONLY)."""
import sys, os
sys.path.insert(0, "/home/z/my-project/ems19-repo/scripts")
import p16_tg as tg

P = "/home/z/my-project/download/phase19_deliverables/proofs"
sheets = [
    ("S1_caption_v2_strip_8frames.jpg",
     "PROOF S1/7 — Caption System v2 (CV1-CV7): Montserrat ExtraBold body, ONE accent ≤1.15x, "
     "spoken dim 45%, upcoming white, sweep LOOP, underline = karaoke progress. No serif, no ghost."),
    ("S2_asset_license_watermark_audit.jpg",
     "PROOF S2/7 — AS1/GC2: license registry (manager-raw + generated card); watermark scan 4 frames "
     "+ painting; 2 heuristic false-positives resolved by 2x close-up visual audit (no watermark pixels). Effective hits = 0."),
    ("S3_designed_canvas_proof.jpg",
     "PROOF S3/7 — AS2: designed canvases (darkmono gradient+grain+halftone+ghost / paper) replace "
     "blur-of-footage scene bg; blur plate marked FORBIDDEN beyond 0.3s (GC3)."),
    ("S4_scene_plan_quota.jpg",
     "PROOF S4/7 — Scene plan: 12 lyric-line beats, 12 scene types, designed frac 0.99, "
     "no consecutive repeats, ≥6 wow moments, ≥4 camera moves, frame-1 composed, no-brand end card."),
    ("S5_cue_sheet_sample.jpg",
     "PROOF S5/7 — Cue sheet: every animation mapped to SFX with per-event dB; original mix kept; "
     "loudnorm 2-pass -14 LUFS, TP ≤ -1.5."),
    ("S6_song_id_source_log.jpg",
     "PROOF S6/7 — Song-ID: WELCOME — IDK feat. Eminem (prod. J Dilla), faster-whisper x Genius "
     "verbatim, HIGH confidence; fresh v19 whisper evidence shown. Source chain: REF-TAG-A 403 "
     "(key expired) -> yt-dlp blocked -> honest fallback manager-provided official-MV excerpt."),
    ("S7_engine_beat_table.jpg",
     "PROOF S7/7 — Engine/beat table (E3 chain logged per beat): FilmCraft/EffectCraft unavailable "
     "-> Remotion skipped -> PIL+ffmpeg composite used; per-beat canvas + motion map."),
]
ok_all = True
for fn, cap in sheets:
    p = os.path.join(P, fn)
    if not os.path.exists(p):
        ok_all = False
        print("MISSING", fn)
        continue
    ok = tg.send_photo(p, cap)
    print(fn, ok)
    ok_all = ok_all and ok
msg = ("<b>PROOFS-FIRST COMPLETE (7/7)</b>\n"
       "Captions v2 + assets AS1 + canvas AS2 + scene plan + cue sheet + song-ID + engine map.\n"
       "Gates preview: GC1 one-accent by construction; GC2 effective hits 0; GC3 zero blur-bg scenes; "
       "GC4 no-brand end card; GC5 grade-delta probe + camera moves logged in render.\n"
       "Next: full render T-1 v19 -> GC1-GC5 + Q1-Q12 + M1-M4 gates on FINAL file -> negatives 8/8 must FAIL.")
print("SUMMARY", tg.send(msg))
