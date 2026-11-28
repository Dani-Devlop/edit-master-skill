# BANKING — verified module bank (Phase 31 re-bank)

## RE-BANKED THIS SESSION (evidence = v26 gate ledgers + hardening suite)
| module | file | verification |
|--------|------|--------------|
| WC1 video-in-card (live, never frozen) | components/wc25kit.py | LF2 PASS (v26) |
| WC2 hook occlusion (per-frame isnet mattes) | components/wc25kit.py | LF3/B2 PASS (v26) |
| WC3 cutout depth (contact shadow+parallax+rim, shadow_boost) | components/wc25kit.py | B4 PASS (v26) |
| WC4 tissue fill | components/wc25kit.py | B6/G1 PASS (v26) |
| IG1-IG10 beat-lock/pseudo-UI/loop/slams/idle/color/pacing/texture/captions/camera | components/ig24kit.py | all PASS (v26) |
| persp3d M1-M5 | components/ + render_t1_v25.py | G6/LF5 PASS (v26) |
| B1-B10 binary gates + frozen ledger w/ seek-fallback decode | scripts/gates_t1_v25.py | 29 PASS + negatives FAIL |
| cutout pipeline (isnet-general-use, multi-window QA) | scripts/cutout_v22.py + gen_assets_v31 | 6/6 subjects banked |
| palette-locked chroma split (volt/white) | components/ig24kit.py | B8 0.0 (v26) |
| film-gate edge burn (kills yuv420 edge chroma) | render_t1_v25_showcase.py | B9 clearance PASS |

## LOST WITH PURGE (Ph27 adoption banks — honest status)
motion-skills full spec bank, ghost 19 style pack, 3dviz recipe pack, word-timed
B-roll bank, face-track reframe bank, opsverify + vt_screen_check scripts: the
Ph27 adopted banks were lost with the Ph28 sandbox purge (28.02) and the replica
references are unreachable this session (yt-dlp bot-block + IG authwall). The
re-bank above is the PROVEN, gate-verified core. Re-adoption of the lost banks
requires the reference clips (or owner-supplied mirrors) — queued, no silent
substitution.

## PHASE 32 BANK (F4-F6 adoption wave — replica-tested before banking)
| module | file | verification |
|--------|------|--------------|
| histmap adopted kit (spring_pop/parabolic_hop/smootherstep/extract_green_screen_sprite/draw_flame_cluster EXACT copies + stick-arm clamp -45..-68 + lower-third 34->28 fit + OneShotFoley 0.20-0.28 + FFmpegPipe clean shutdown + KeyframeQA 5-7 + relief plates + physical props, ZERO neon route lines) | components/adopted/histmap/histmap_kit.py | replica-test 7s scene PASS: 6 QA frames clean, 0 route lines (70px AA residual), foley in band, probe 720x1280@30 h264+aac (test-results/p32/histmap_replica_report.json) |
| F6 15-repo wave: 8 repos security-graded A/CAUTION/B and banked into components/adopted/<repo>/ (ffmpeg-skill contract -> opsverify; claude-motion-design fallback-engine spec w/ 4 fetch scripts DENY-LISTED; motion-skills pack index + verify trio; claude-animation-skills 11 families F5-F11; motion-graphics 6 specs incl. word-timed B-roll + object-separation; claude-shorts moment selection + face-track 9:16; ghost-editor 7 styles + people-rules + reverse-engineer method, scripts/ denied, 19-vs-7 discrepancy logged; 3dviz-pro-max 223 recipes + capture.py screen gate) + ghost styles ported to presets/ghost-styles/ | components/adopted/ADOPTION-LOG.md + per-repo SECURITY-GRADE.md | grades: ALL MIT verified; ZERO network-capable file banked |
