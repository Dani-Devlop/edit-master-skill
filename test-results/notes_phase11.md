# Per-Video Test Notes — Phase 11.1 (gated re-render)

Generated 2026-11-21 | 16 categories | single renderer path (scripts/p11_render.py)
| gate-on-file measured on every decoded final.mp4 | ALL 16 gate 16/16 PASS

Gate methodology: docs are in SKILL.md §11.1.4; calibration documented in code.
Measured on EVERY file: LUFS -14.5 / TP -1.5 dBTP (two-pass loudnorm + density chain),
whip on 9/9 comp changes, >=1 zoom-through, >=1 invert bite, no halftone on Mode B
footage, captions OCR-verified in the declared caption band, SFX-onset parity 18/18,
family signature pixel-verified, matte fps 30 (subject videos), face-overlap 0.

Scores from the legacy intent-QA era are INVALID (see gate11/A3 + A4). The only valid
score is the gate PASS line + measured values per file (scores_phase11.csv).

Gate artifacts: test-results/gate11/gate_<vid>.json (file sha256 + gate sha256).
Delivery: Telegram sendVideo with caption carrying the PASS line + hashes (D3).
Supercut v4: 16 gated highlights + flash bridges + end card + loop; SC gate 6/6 PASS
(32.2s, -14.5 LUFS, TP -3.6 dBTP); sources asserted gated in the build (D2).

Auto-mode decisions (honest log): categories whose source footage had no matte-able
subject (measured salient coverage < 0.15) ran message beats Mode B footage-first:
travel_1, nature_1 (subject_ok False per render_log). All other categories used the
Mode A canvas + cut-out subject composition.

Iteration notes per video are in gate11/ render logs; the failure log table
(SKILL.md §11.1.7) documents every defect class hit during the rollout and its fix.
