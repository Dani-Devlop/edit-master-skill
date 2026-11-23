# TECHNIQUE ENCYCLOPEDIA v4 — with WHEN-to-use rules (Phase 16.0, L0.3/P13)

Updated 2026-11-24. Every technique lists: what it is, when to use, when to avoid,
which gate measures it. The renderer (scripts/p16_render.py) implements every entry;
presets/*.json choose per genre/beat. "when_to_use" strings are logged into each
video manifest (G-P13) — technique choice must respect this table.

## Caption & type techniques

| Technique | What | Use when | Avoid when | Gate |
|---|---|---|---|---|
| karaoke-v2 word sweep | full sentence always visible; active word accent +1.2x + glow; spoken dim ~45%; upcoming white; sweep loops within the sentence until sentence change; index from whisper word timestamps (real vox) or beat map (no vox), ±120ms | any real-vox edit (MV/UGC/talking head); 2–6 words per line, ≤2 lines | no-vox sources (use beat-keyword line instead); typewriter/partial/single-letter states — NEVER | G-P1 |
| Persian RTL karaoke | same state machine, Vazirmatn/Kalameh, raqm bidi shaping, logical word 0 rightmost | Persian/Farsi/Arabic vox | forcing LTR order on RTL words | G-P1 (RTL row) |
| ghost echo outline | offset outline copy of hook word, 1–2 echo steps, low alpha | hook lockup, payoff word | long sentences; busy footage | G-P2 |
| mixed-scale lockup | small bold kicker + GIANT accent word + condensed/script continuation in one sentence block | every hook (t=0..2s) | equal-size lines (amateur flat type) | G-P2 lockup ≤0.92W |
| highlighter tape | accent rounded-rect swipe behind 1–2 semantic words | SEMANTIC emphasis only (a promise, a price, a verdict) | decorating random words | G-P2 |
| selection brackets | 4 corner brackets around one word/subject | odd-beat structure signature, verdict word | on every beat (noise) | G-P2/G-P13 |
| scramble-decode | glyphs cycle then lock to the real word | reveal hook word, countdown | long sentences (>6 words) | G-P2 |
| variable-weight animation | font weight axis animates with emphasis | kinetic hierarchy on hook words | fonts without variable axes | G-P2 |
| numbered tabs | small numbered chip per section/step | multi-step recipes, tutorials | single-beat videos | G-P8 |
| karaoke loop restart | after sentence's last word, accent returns to word 0 if window continues | sentence windows longer than spoken content | restarting mid-sentence | G-P1 |

## Motion & transition techniques

| Technique | What | Use when | Avoid when | Gate |
|---|---|---|---|---|
| whip-blur + scale-punch + whoosh | edge-clamped directional smear + screen-blend flash + zoom 1.05 + whoosh at EVERY comp change | every composition change | within same comp; multi-second blur | G-P6 |
| recursive zoom-through | previous comp dives into a tilted card/scene, 1 per video | after hook — scene pinch for momentum | every beat (nausea) | G-P6/G-P4 |
| invert/negative bite | full-frame negative ≤0.15s | B&W/gritty grammar, pattern interrupt at retention-risk midpoint | colorful warm genres >2 bites | G-P6 |
| feathered mask-wipe | soft matte wipe between scenes | family-fitting scene changes (food/fitness) | hard geometry on soft genres | G-P6 |
| light-leak | warm gradient wash ≤0.3s | Mode A canvas entrance, fitness/food families | on footage as texture (G-P16 texture gate fails it) | G-P6/G-P16 |
| glitch/scanline bite | RGB-split + scanlines ≤0.15s | tech/cars entrances, beat hits | full-length overlays | G-P16 |
| freeze + type-slam | freeze frame + giant lockup + shake decay | hook beat t=0, lyric stakes word, payoff | calm moments; >1 per 8 beats | G-P5/G-P2 |
| eased speed-ramp 0.4x/1.6x | bezier time remap on motion peaks | running, reps, zoomies, pours | static shots; linear ramps (hard cut feel) | G-P5 |
| punch-in 100→110% | scale push on every emphasis word | emphasis beats, variety on single-scene | during ramps (double motion) | G-P5 |
| motion-blur on fast moves | horizontal smear proportional to velocity | fast pans/whips only | slow moves (mush) | G-P5/G-P15 |
| drop-sync | first slam lands on the music drop ±80ms | music-driven edits | speech-led edits | G-P11 |
| match-cut | shape/motion continuity across cut | scene changes with shared geometry | forced matches | G-P11 |

## Depth & composition

| Technique | What | Use when | Avoid when | Gate |
|---|---|---|---|---|
| occlusion (freeze matte) | giant type UNDER subject matte, pixel-verified | subject + giant type on hook | moving subject during type (matte lies) | G-P3 |
| Mode A cut-out canvas | subject 30–55%H bottom-center on clean canvas | silent sources with clean subject | busy/moving subjects | G-P4 |
| Mode B graded in-scene | type over graded footage | vox sources, documentary feel | unprotected subject faces | G-P4 |
| contact shadow | soft ellipse shadow under cut-outs | every Mode A canvas | floating cut-outs | G-P3 |
| 2.5D parallax | fg/bg split speeds on stills | still inserts, polaroid cascades | moving footage | G-P3 |
| headroom discipline | no dead margins, no face crops | all comps | center-everything flatness | G-P4 |

## Stakes graphics (real numbers only)

| Technique | What | Use when | Avoid when | Gate |
|---|---|---|---|---|
| odometer counter | accent outlined counter, settle ≥0.6s | numeric hype (BPM, reps, price, time) from REAL measured quantities | MV grit; invented numbers | G-P8 |
| orbit cards High/Med/Low | 3 tilted cards orbiting subject | comparison/verdict beat over cutout canvas | every video (fatigue) | G-P8 |
| starburst draw-on | rays draw on behind payoff word | payoff beat, semantic emphasis | hook (keep clean) | G-P8 |
| polaroid cascade | tilted photo cards, REAL different content, views/name/verified pills | mid-video proof beats | same image repeated (fake) | G-P8 |
| progress chrome | real BPM/energy pill + progress bar | all videos (not beat-index-only) | meaningless index counters | G-P8 |

## Texture & grade

| Technique | What | Use when | Avoid when | Gate |
|---|---|---|---|---|
| halftone overlay | dot-lattice texture | NEVER on footage — canvas/insert plates only (lattice-autocorr gate fails halftone-on-footage at delivery codec) | on footage | G-P16 texture |
| film grain + vignette | source-matched grain 4.2, vignette 0.20 | all Mode B footage | clean digital look on gritty sources | G-P7 |
| day-for-night | darken + cool grade | daytime footage, night themes | faces need clarity (use scrim) | G-P7 |
| color-pop insert | B&W grade + single accent hue kept | B&W sources needing accent | colorful sources | G-P7 |
| skin-tone protection | hue preserve on skin mask | any human subject | forgetting during LUT push | G-P7 |

## Engine notes (Phase 16.0 fixes, measured)

- whip_streak v2: edge-CLAMPED horizontal shift — np.roll wrapped the opposite
  (vignette-darkened) frame edge into view as a dark band on bright scenes.
- texture gate v2: halftone = lattice autocorrelation ≥0.08 (halftone neg 0.42,
  real finals ≤0.02). The old FFT peak-ratio was non-discriminative on
  texture-heavy footage (finals 11–27 vs neg 22.9).
- G-P6 blur = smear collapse (post edge energy < 0.45 × pre) — strong blur
  collapses gradients; the old "edges above pre+6" criterion was unsatisfiable.
- G-P8 strict saturation floor is accent-relative (soft pink family S≈141 was
  excluded by the absolute 150 floor).
- cutout→zoom fallback: when no reliable matte exists, Mode-A beats degrade to a
  deep-zoom comp (logged as comp_fallback_beats in the render log) instead of
  producing adjacent-comp luma collisions.
