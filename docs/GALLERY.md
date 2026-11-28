# GALLERY — delivered renders, scores, evidence (Phase 31)

All artifacts measured on DELIVERED files (delivery lock). Repo copies in `test-results/p31/`.

## T-1 v26 FULL MASTER — WELCOME (IDK ft. Eminem & J Dilla)
- File: `T1_welcome_v26_9x16.mp4` · 27.9s · 1080x1920@30 · sha256 `7a2deb83e2a3488e...c42006240`
- Cover: `cover_v26.jpg` · Contact sheet: `contact_sheet_v26.jpg` (12 decoded moments)
- **FULL GATES: 29 PASS / 1 honest** — B1-B10 ALL YES; B8 off-palette 0.0;
  B9 hook 0.889-0.896W with 20px clearance; B10 census 700 frames / 0 overlaps;
  IG1 onset-lock PASS; IG3 loop-sim 0.918; G8 loudness -14 LUFS TP<=-1.5.
- Blind critic x3 (frames-only): showcase median **7.7** (v25 was 7.3; 8.5 = stretch).
- LF6 replica-live: vs raw source MV median 3.5 (edit grammar deliberately diverges
  from bare footage); match% vs IG reference reels PENDING (yt-dlp bot-block since 26.04).
- Sound design: cues (sub/riser/whoosh/tape-stop/impacts/echobed/crackle) + kick
  reinforcement, 2-pass loudnorm — cue sheet `t1_v24_cuesheet.json`.
- Telegram LIVE: msgs 783-787, caption "Test Edit Skill".

## v26 SHOWCASE (10s protocol)
- Gates: 28 PASS / B10+LF6 stage-pending; sheet `showcase_sheet.jpg`.

## Q4 MODULE MATRIX (5 genres x banked modules)
| # | genre | living % | off-palette | verdict |
|---|-------|----------|-------------|---------|
| 1 | cars | 91.1 | 0.0 | PASS |
| 2 | fitness | 87.2 | 0.0 | PASS |
| 3 | education | 93.3 | 0.0 | PASS |
| 4 | branding | 95.9 | 0.0 | PASS |
| 5 | mindset | 67.5 | 0.0002 | PASS |
- Sheet: `matrix_sheet.jpg`; scores `matrix_scores.json`; probes 4s, 720x1280.
- Full preset-driven reels queued (renderer generalization).

## HARDENING (regression negatives — all MUST FAIL, all DO)
Palette leak -> B8 FAIL (0.78) | cropped hook -> B9 FAIL (0.97W, 0px) |
burned labels -> B7 FAIL | dead frames -> G1 FAIL | glyph overlap -> B10 FAIL.
Evidence: `hardening_negatives.json`.

## PLATFORM MASTERS
Reels/Shorts/TikTok = 9:16 native (sha-equal master) · Telegram 720x1280 ·
LinkedIn 1:1 + 4:5 blur-pad (caption band safe) · loudness carried from master.

---

# PHASE 32-R2 deliveries (2026-11-28)

All artifacts measured on DELIVERED files. Repo copies in `test-results/p32/`.

## F4 histmap replica (adopted module demo)
- `histmap_replica_7s.mp4` · 7.0s · 720x1280@30 · h264+aac — Telegram msg 796
- EXACT helper adoption (spring_pop/parabolic_hop/smootherstep/extract_green_screen_sprite/
  draw_flame_cluster) + gotcha helpers; relief plate #B59F78/#F4F7FA/#4B7282; ZERO neon
  route lines (0 violation px; 70px AA blend residual logged); foley 14 accents @0.20-0.28;
  QA 6 keyframes (histmap_replica_sheet.jpg)

## F5 prompt-bank replicas
- `prompt1_hook_slam_3s.mp4` — volt world, off-palette 0.0, hook 0.70<=0.92 (F3 advance fix visible)
- `prompt2_shrinkcard_3s.mp4` — histmap world, off-palette 0.0

## F7 preset reels (generalized preset renderer, msgs 805-809)
| reel | dur | census off-palette | hook span (decoded) | verdict |
|------|-----|--------------------|--------------------|---------|
| preset_cars_12s | 12.0s | 0.0 | 0.60 | PASS |
| preset_fitness_12s | 12.0s | 6e-05 | 0.637 | PASS |
| preset_education_12s | 12.0s | 0.0 | 0.633 | PASS |
| preset_branding_12s | 12.0s | 6e-05 | 0.622 | PASS |
| preset_mindset_12s | 12.0s | 0.0 | 0.611 | PASS |
All: 720x1280@30, B&W-graded footage (S2), foley-composed audio -> loudnorm, QA 6
keyframes each, no internal labels. Captons: "Test Edit Skill — preset <genre>".

## F8 supercut v2 (msg 811)
- `supercut_v2_31s.mp4` · measured 30.5s · loudness **-14.2 LUFS** (ebur128 on final)
- 13 variety segments (5 preset reels + histmap) + designed end card + loop-hold
  (tail = cold-open frame 0); per-segment world-aware census ALL PASS
- Loudness fix documented: sparse foley mix cannot reach -14 within TP; dense bed
  RMS-normalized to ~-21 LUFS before loudnorm (supercut_v2_report.json)

## F9 self-critic x3 (rubric-only, honest)
- Supercut sheet 12 frames: median **6.2** (runs 6.3/6.2/5.5) — NO IG target refs
  reachable (P1/P2/P3 absent since ingest; yt-dlp bot-blocked since 26.04) → match%
  stays PENDING; nothing fabricated. selfcritic_supercut_x3.json
