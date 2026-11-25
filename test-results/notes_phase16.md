# Phase 16.0 — THE TWENTY-PILLAR LEAP — test notes

Executed 2026-11-23/24. V0 proof-first protocol green before any full render.


## V0 proofs (all PASS)
- V0.1 karaoke state machine: 8-frame strip, asserts full_sentence_always /
  active_accent_in_box / dim_below_upcoming / loop_restart_word0 all true; Persian
  RTL row correct (Vazirmatn, raqm bidi, logical word 0 rightmost).
- V0.2 preset manifest: 5 presets sha256-logged (presets_manifest_sha256.json);
  target mv_darkmono loaded.
- V0.3 harness demo: 20-axis MEASURED critique of the Phase-14 mv_darkmono_v3
  delivery — honest weaknesses exposed (A19_texture 3.0: the fixed lattice detector
  proves halftone-on-footage at score 0.213 that the old FFT engine shipped;
  A3_caption_contrast 5.18 vs reference band coverage median 0.78).
- V0.4 regression negatives 3/3 CAUGHT: typewriter -> G-P1 constancy FAIL;
  empty-bar@frame0 -> G-P4 composed-frame FAIL; halftone-on-footage -> texture
  gate FAIL (engine fix: lattice-autocorr detector, calibrated: clean plate 0.001,
  real finals <= 0.021, halftone neg >= 0.42, threshold 0.08).

## Engine fixes driven by V0/P12 (measured; documented in docs/TECHNIQUES.md v4)
1. Texture gate: FFT peak-ratio was non-discriminative (finals 11-27 vs neg 22.9)
   -> structural lattice autocorrelation.
2. whip_streak v2: edge-clamped smear (np.roll wrapped the vignette-darkened frame
   edge across bright scenes as a dark band).
3. G-P6 blur: strong smear COLLAPSES horizontal edge energy -> detect the collapse
   (post < 0.45 x pre); the old criterion was unsatisfiable.
4. G-P8 strict saturation floor now accent-relative (soft pink family S=141 was
   invisible to the absolute 150 floor).
5. Preset bank: 4 presets carried a copy-pasted name field -> fixed (hashes refreshed).
6. cutout->deep-zoom honest fallback when matte unavailable (logged in manifest),
   fixing an adjacent-comp luma collision (beats 3->4 dist 5.7 -> A7 9.2 -> 10.0).

## Per-delivery results (7 masters, all G-P1..G-P20 PASS, all 20 axes >= 9.5)

| video | variant | min axis | weakest | gate sha (16) | refine iters |
|---|---|---|---|---|---|
| food_fresh | 9x16 | 9.5 | A11_onset_cut | ec50d221d52958cc | 0 |
| cars_nightdrive | 9x16 | 9.5 | A11_onset_cut | 62d8e00b52f38c00 | 0 |
| pets_playful | 9x16 | 9.5 | A11_onset_cut | b3e4787cb32a888e | 0 |
| fitness_energy | 9x16 | 9.5 | A11_onset_cut | 99c29abb54a8b60e | 0 |
| mv_darkmono_9x16 | 9x16 | 9.7 | A2_karaoke_sync | 9c54f01743514b00 | 0 |
| mv_darkmono_4x5 | 4x5 | 9.7 | A2_karaoke_sync | b1720e6b0c24db98 | 0 |
| mv_darkmono_1x1 | 1x1 | 9.7 | A2_karaoke_sync | 447420d5aa3d0858 | 0 |

## Loudness (P10, measured per master)
food -14.2/-3.2 | cars -14.1/-2.9 | pets -14.1/-3.0 | fitness -14.1/-3.3 |
mv 9x16 -14.0/-3.0 | mv 4x5 -14.0/-3.0 | mv 1x1 -14.0/-3.0 (LUFS dB / TP dBFS;
spec -14 +/-0.5, TP <= -1.5 — all compliant).

## Source quality (P14)
All 5 raws scored >= 6/10 (per-video source_quality.json + render logs). T-4
daytime cars source day-for-night graded; food matte unavailable -> honest
cutout->zoom fallback (no bad-edit-bad-source).

## Music / copyright coverage (P10)
T-1: original mix KEPT, no overlay (coverage full, original audio). T-2..T-5:
original synthesized beds @ genre BPM (fully license-safe). SFX synthesized.
SFX events == entrances; sidechain duck under vox/music; silence-dropout before slams.

## Multi-platform mastering (P15)
T-1 mastered 9:16 + 4:5 + 1:1 (per-variant safe zones verified, G-P15). Covers
exported per video. H.264 + AAC, bt709.

## Delivery locks (P20)
Every gate_<sha>.json sha256 equals the FINAL mp4 sha256 AND overall PASS for
all 7 masters. Regression negatives re-run with the fixed engine: 3/3 FAIL
correctly.

## Resource bank (P17)
docs/RESOURCES.md v4: 4 Mixkit assets + manager-attached MV raw, licenses logged;
SFX/music synthesized; karaoke-caption public reference opened and logged;
yt-dlp/Instagram blocks documented honestly with fallback used.

