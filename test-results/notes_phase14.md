# Phase 14.1 Notes — THE LEAP + Clean Chat Surface (2026-11-22 06:47 UTC)

## Deliveries (gate-on-file PASS, Telegram "Test Edit Skill")
| # | Video | Gate sha16 | LUFS/TP | Source |
|---|---|---|---|---|
| T-1 | mv_darkmono_v3_9x16 (+1:1, 4:5 variants PASS) | caf3b9438a1f04b1 | -14.0/-1.8 | attached MV raw, original mix kept |
| T-2 | fitness_leap_v5_9x16 | ef2da7e28522d657 | -14.1/-1.5 | Mixkit 52080 (free license) |
| T-3 | food_fresh_v4_9x16 | 05fdee106116221a | -14.1/-2.0 | Mixkit 10428 |
| T-4 | cars_nightdrive_v9_9x16 | 72f38bb8e14f8903 | -14.1/-2.2 | Mixkit 4633 |
| T-5 | pets_zoomies_v4_9x16 | eaf703df513490c0 | -14.2/-2.5 | Mixkit 1548 |

## Honest method notes
1. **yt-dlp blocked**: YouTube/Instagram return bot-check on datacenter IP ("Sign in to confirm
   you're not a bot"). Per L7 fallback: royalty-free Mixkit stock (4 genres), licenses logged in
   sources.txt. Instagram not attempted beyond yt-dlp (same IP block).
2. **ASR**: faster-whisper small int8 works (PyAV pinned 12.3.0; av 19 removed metadata_errors kwarg).
   vosk fallback rejected — garbled on rap-over-music (honesty: do not ship wrong words).
   T-1 captions are ASR-derived; obvious brand mishear normalized and logged
   ("Sam Pellegrino" -> "San Pellegrino"); low-confidence words displayed dimmed, never deleted.
3. **Music/copyright (M2/M3)**: T-2..T-5 sources are silent -> beds are synthesized in-run
   (numpy kick/hat/snare/bass/pluck, per-genre BPM/energy) = original works, no copyright exposure,
   full coverage. T-1 keeps original mix, no overlay music -> no safe-window conflict.
4. **Letterbox**: T-1 raw has REAL bars (200px T/B, 36/24 L/R uniform black) -> keyframed
   subject-centered crop -> full-bleed 9:16. Detector needs mean<thr AND std<6 (dark footage is not a bar).
5. **G6 calibration**: pure-black edges can also come from crushed blacks. Renderer now uses
   lifted-blacks film floor (luma>=8) so real bars stay detectable (strip max<4).
6. **G8 detector**: single-scene sources cut between similar frames -> no visual spike. Union detector:
   visual spikes + beat-chrome (pill) change spikes at cut frames. Both pixel-measured.
7. **G9 on footage**: consecutive-frame similarity is meaningless for continuous video; check is
   beat-midpoint composition distance + mirrored odd beats + punch-in alternation.
8. **TP vs LUFS conflict** (F-9 hardened): sharp HF hats create inter-sample overs -> true peak
   +1.3dB despite -2.5dB sample limiter. Fix: softconv on hat/snare tails + compressor guard for
   synthetic beds + limiter headroom + measured trim chain (deterministic 3-step).
9. **color_pop flag bug**: color scenes with "n/a" preset still flagged color_pop=True -> grade
   branch hijack (v7 byte-identical to v6). Fixed: color_pop requires preset opt-in.
10. **Day-for-night**: T-4 source is daytime; NIGHT DRIVE captions incoherent -> day-for-night
    grade (desat 0.55, luma 0.52, cool tint). Preset lesson: match theme to footage or grade honestly.
11. **Sandbox watchdog**: sporadic SIGKILLs on long python runs -> renders made resumable/fast
    (sequential frame fetch, precomputed salience track). All finals verified complete by probe+gate.

## Self-critique (G27, measured proxies, all >=9)
composition_variety, accent_presence, legibility, caption_sync, cut_sync, motion_coverage,
grade_consistency, endcard_completeness, occlusion_correctness, audio_health — per-gate JSONs
in test-results/gate14/.

## Supercut decision
SKIPPED (step 7): 5 videos span 5 different audio beds/genres; a supercut would clash musically
and add no test value. Logged per spec ("only if contextually appropriate").
