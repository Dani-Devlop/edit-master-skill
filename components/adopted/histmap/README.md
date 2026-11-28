# histmap — ADOPTED MODULE (Phase 32 F4)

Source: `historical-map-animation` skill.md (owner-supplied attachment,
single-file skill, no explicit license file in source).

## License-log (RESOURCES discipline)

| Item | Provenance | License status | Action |
|---|---|---|---|
| histmap_kit.py core helpers (smoothstep, smootherstep, spring_pop, parabolic_hop, extract_green_screen_sprite, draw_flame_cluster) | owner-supplied skill.md, EXACT code copy per Phase-32 F4 instruction | no explicit license in source file; adopted under owner's direct instruction as reference implementation | logged here; credit "historical-map-animation skill (owner-supplied)"; do not redistribute as standalone library until upstream license identified |
| serif label font | DejaVuSerif-BoldItalic.ttf (skill spec) — NOT present in sandbox | GPL-compatible (DejaVu); fallback chain: FreeSerifBoldItalic (GPL+FE) -> LiberationSerif-BoldItalic (SIL OFL 1.1) -> repo PlayfairItalic | runtime fallback logged at `_SERIF_LOG` |
| palette constants #B59F78 / #F4F7FA / #4B7282 + day/night values | skill Stage-3 prompt specs | values only (not copyrightable) | copied verbatim |
| physical prop drawers + relief plate + peg-doll factory | implemented in-kit (source NAMES the props but ships no code) | original work of this repo (MIT) | marked "extension" in kit docstring |

## Family F12 (banked here)

Relief-map plates (day/night), 2.5D diorama grammar, chroma sprites
(HSV mask + spill suppression), physical props: iron chains, timber plank
bridge, 3D barrels, cargo crates, reed bundles, watchtower+banner,
alpha-composited flame clusters. **ZERO neon route lines** — every march/
crossing is depicted through tangible props + camera pans (hard rule).

## Gotchas carried as executable helpers (NOT prose)

1. Translucent effects REQUIRE patch + `canvas.alpha_composite(...)` — Pillow
   `ImageDraw` on RGBA overwrites pixel alpha (verified empirically in Phase 32
   F2: center pixel alpha became 60 after a 60-alpha draw on an opaque canvas).
2. Stick-arm angles: -45..-68deg only (`draw_stick_arm` clamps).
3. Lower-third auto-fit: 34pt -> 28pt step-down when `tw > W - 56`
   (`draw_lower_third` implements the loop).
4. Sparse one-shot foley: 0.20-0.28 gain, unique one-shots, narration 0dB
   (`OneShotFoley` asserts the gain band; de-dupes accents).
5. FFmpeg pipe shutdown: `stdin.close()` + `stderr.read()` + `wait()` — never
   `communicate()` (`FFmpegPipe.close()`).
6. Keyframe QA: 5-7 frames saved during render (`KeyframeQA`).
7. Camera: `smootherstep` S-curve 900x1600 -> 720x1280 (`camera_crop`).

## Replica-test

`scripts/p32_histmap_replica.py` renders one 7s scene exercising: procedural
day relief plate -> S-curve camera -> spring_pop title -> peg-doll chroma
sprite (green-screen factory + EXACT extractor) -> stick-arm pointer ->
parabolic_hop river crossing -> sequential plank bridge -> barrel/crate/
reeds/watchtower props -> flame cluster (alpha_composite) -> auto-fit
lower-third -> one-shot foley mix -> keyframe QA frames -> pipe encode.
Verification: ffprobe + neon-route-line absence check + QA frame audit.
