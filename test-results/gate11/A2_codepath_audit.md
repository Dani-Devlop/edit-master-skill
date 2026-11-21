# A2 Code-Path Audit (Phase 11.1, 2026-11-21)

## Which function/script rendered the delivered travel_1.mp4?
- Delivered file: p8work/render8/travel_1/final_tg.mp4 (Telegram copy of final.mp4, sha256 c2305618b8c543b8...)
- Rendered by the Phase-8 ROLLOUT renderer (per-category script, family F3 world-pan path with
  scrim + type + cards per p8work/plans/travel_1.json).
- That renderer script is NOT PERSISTED: the sandbox session that produced render8/* lost it;
  the only local git commit (f499581, 2026-11-20 20:06) never contained p8work/ (untracked).
- Artifact signature of the lost renderer: plans/<vid>.json (10-beat plan) + sfx_events.json
  (53 events) + qa.json (23 intent-level checks) + loudnorm.json + contact_sheet.jpg.

## Diff vs benchmark renderer
- The Phase-8 Step 1-2 BENCHMARK renderer script is ALSO not persisted. Code-level diff impossible.
- Artifact-level diff (honest): benchmark QA schema = 22 checks incl. real rembg occlusion;
  rollout QA schema = 23 checks (added C1 matte-fps); rollout F1/F2 used mattes, F3 used a
  duotone scrim over footage with halftone (legacy QA checked "halftone present" = code
  presence, NOT pixels — the delivered file measures 0.00-0.16 halftone score, mostly absent).

## Renderer path count
- Historical (Phase 8): 2 category-render paths existed (benchmark renderer [lost],
  rollout renderer [lost]) + 1 supercut script (p8_supercut3.py, persists).
- Persisted TODAY before reset: p8_style16.py (style config only, no rendering),
  p8_supercut3.py (supercut concat only) => category-render code paths persisted: 0.
- Phase 11.1 target: ONE unified renderer (benchmark + rollout + supercut feed from the same
  path; category delta = style config only). Code-path count after Step U must equal 1.

## Which paths lacked the Phase 11.1 spec?
ALL historical paths lacked: Gate-on-file (they asserted intent-level QA), delivery lock
D1-D3, Mode-B texture ban enforcement, invert bite / zoom-through / caption-OCR / dead-frame
/ consecutive-comp checks, dBTP true-peak semantics (legacy reported -1.3 dBFS and called it
a pass), SFX-onset parity verification, occlusion pixel verification on delivered files.
