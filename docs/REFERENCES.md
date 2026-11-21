# REFERENCES — Phase 11.1 Reference Pack Ingest (Step 0)

Ingested 2026-11-21. Sampling: VIDEO-1 @ 4 fps end-to-end (112 frames), VIDEO-2 @ 8 fps
end-to-end (54 frames), plus a full 30 fps metric pass (per-frame luma / inter-frame
absdiff / RGB means, `refwork/metrics30.json`). Key moments verified at full resolution
(`refwork/keyframes_strip.jpg`). Evidence labels: **[VID t]** = video-evidenced with
timestamp; **[SPEC]** = spec-derived (no source evidence available).

## 0. Sources

| ID | File | Dur | Res | FPS | Status |
| --- | --- | --- | --- | --- | --- |
| VIDEO-1 (V1) | `4_5914418752572623746.mp4` | 28.07 s | 720x1280 | 30 | INGESTED |
| VIDEO-2 (V2) | `VID_20261121_000716_199.mp4` | 6.77 s | 720x1280 | 30 | INGESTED |
| P1 (Hera agency frames) | — | — | — | — | PENDING (absent; proceed per R3) |
| P3 (Raw/Edited composition frames) | — | — | — | — | PENDING (absent; proceed per R3) |
| ANTI (failed-output frames) | — | — | — | — | PENDING as images; the five ANTI failure classes are enumerated in the task and are enforced as gate negatives G1–G14 |
| P2 (4-quadrant photos) | — | not needed | — | — | V2 present, so P2 fallback unused |

Both V1 and V2 are 30 fps — every whip/blur/invert timestamp below is frame-accurate.

---

## 1. VIDEO-1 — Motion Grammar A (Raw/Edited reel, single-column scene/lockup)

### 1.1 Structure (7 Raw -> Edited cycles)

| Seg | Raw in | Edited in | Content | Edited lockup |
| --- | --- | --- | --- | --- |
| A | 0.00 | 1.75 | white studio, blue chair | "Make better **Scripts**" + cards + "with this fomula" |
| B | 4.25 | 6.00 | night outdoor, fitness | tape "**BOMB**" + "looking for an" |
| C | 8.00 | 10.00 | white studio, armchair | "Nobody cares what you **sell**" -> card comp |
| C2 | — | 12.50 | card comp: "they care what it fixes" + "?" card + "Adults" pill | photo-card hero |
| D | 14.9 | 15.00 | white studio, chair | "This one tip / Will change your / **Life**" -> tilted cards "**mistake**" |
| E | 16.0 | 18.0 | gym, leg press | "Let's go For **LEG** *Day*" |
| F | 20.0 | 22.00 | gray studio, stool | "You can't miss these insane **GYMS** *in California*" |
| G | 24.0 | 26.00 | purple gym | "3 ways to lose fat *Faster*" + numbered tabs |

### 1.2 Technique table [VID]

| # | Technique | Timestamps | Measured values |
| --- | --- | --- | --- |
| A1 | Raw -> Edited whip-blur + grade jump | 1.75–2.0, 4.23, 6.00, 7.97, 9.90–10.03, 16.03, 19.97 | whip length 0.20–0.28 s (motion-blurred subject visible 1.80→1.90); grade jump = desaturated flat -> saturated + rim light in 1 frame; pill swaps Raw/Edited in same move |
| A2 | Mixed-scale sentence lockup | 2.0–4.0, 10.0–11.5, 26.0–27.75 | small sans words + ONE giant accent word ("Scripts" ~62%H red serif; "sell" ~35%H; "GYMS" ~28%H yellow); giant word <= 0.92W, always fully legible |
| A3 | Giant word vs subject | 2.25–4.0 (Scripts above head), 11.0 (sell across lap, head clear), 22.25–23.75 (GYMS behind torso) | subject head NEVER covered; word may pass behind torso [VID] |
| A4 | Pixel-glitch blocks with lockup entrance | 2.25, 6.25 | 2–6 squares, brand accent color, stepped timing, ~0.3 s life |
| A5 | Glow bloom on giant word | 2.50, 22.50 | red/yellow bloom radius ~0.5 em, peaks ~0.2 s after word lands |
| A6 | Tilted photo-card cascade + pill labels | 3.00–3.75, 12.50–14.25, 15.25–15.75 | 2–4 cards, rounded corners, white inner border + accent outer border, spring back-out overshoot entrance, pill name tags ("Adults", "Aslani", "??") |
| A7 | Highlighter tape italic subline | 6.25–7.0 ("looking for an"), 26.25 ("3 ways") | tape bar behind italic script, slight -2 deg tilt |
| A8 | Numbered file-tab cascade | 26.0–27.5 | tabs 1/2/3 with small captions, staggered drop-in ~0.12 s apart, above head |
| A9 | Doodles | 2.75 (brackets around Scripts), 6.5–7.75 ("?" x2), 15.5 ("x", sparkles), 15.5 ("Life" underline bracket) | hexagon/circle brackets, x-marks, sparkle crosses, scribble underline; <=3 per comp, anchored to type |
| A10 | Recursive zoom-through | 11.75–12.25 | outgoing comp ("sell" + card) scales up through camera ~0.5 s into next comp [VID zt1/zt2] |
| A11 | INVERT / negative bite | 14.67–14.80 | full-frame black with inverted white lockup echo, 1–3 frames (~0.10–0.13 s), lands between comps [VID inv1] |
| A12 | Lower-third caption on message beat | 16.0–17.75 ("I think I unlocked Lumetri Ultra Pro Max") | white caption w/ plate on RAW segment; word-sync [SPEC] |
| A13 | Card whip-in with directional blur | 14.77–14.83, 15.0 | diagonal streak blur, card lands with overshoot |
| A14 | Subject scale reframe | 10.0 | subject shrinks ~40% in 0.25 s to make room for lockup |

Whip spikes measured at 30 fps: 4.23, 6.00, 7.97, 9.90, 10.03, 12.30, 14.67–14.80, 16.03,
19.97 (diff 62–209 gray-levels). **No hard cuts**: every comp change carries blur.

---

## 2. VIDEO-2 — Motion Grammar B (4-quadrant families reel)

Four quadrants run SIMULTANEOUSLY, center Aslani "A" badge at the cross. Each quadrant is
a clean monochrome canvas (Mode A) with a small seated cut-out subject.

### 2.1 Per-family evidence [VID]

| Family | Palette | Evidence timestamps | Signature moves |
| --- | --- | --- | --- |
| F1 white + neon-yellow | white canvas, neon-yellow accent, black ink | 0.00–0.60 scramble; 0.25/0.375 tape; 2.0–4.9 "But" + "Competitor's/Yours" pills; 5.0–6.0 app-tile | scramble-decode mono headline (letters random -> resolve), highlighter tape, yellow corner brackets, vertical word-stacks, ghost bleed type, pixel selection brackets, app-icon tile with red arrow |
| F2 blue | navy scene-canvas, glass blue panel | 0.25–0.50 "You" -> "You are" panel reveal; 0.40 whip-blur; 5.3–6.5 "matters/costs" stacks | phone-UI architecture behind seated subject (glass panel + pills + tiles), screen-content swap, orbiting glass task cards, whip-blur between comps, tape "VERY UP" |
| F3 maroon | deep maroon/red gradient, white pixel-mono | 0.0–1.5 "Why" + corner brackets + ghost bleed; 1.6–3.5 "work"; 5.5–6.2 starburst | pixel-mono type, corner brackets, em-dash pixel marks, node starburst draw-on (staggered lines 5.55 -> 6.00), floating pixel particles (white/red squares), b/w stripe footer |
| F4 light-gray + pink | light gray canvas, pink accents | 0.25–1.12 odometer "$1" -> "$10" -> "$1,000" -> "$1,000,000"; 4.9–5.4 blob + "AI agents" icon row; 5.9 starburst icon | odometer rolling counter, blob mascots with eyes + scribble rings, color-variant icon rows, pink rounded-square particles, "Let Claude" card |

### 2.2 Family motion numbers (measured)

| Move | Value | Evidence |
| --- | --- | --- |
| Scramble resolve | <= 0.60 s full decode (0.00 scrambled -> 0.60 "product" legible); per-char stagger left->right [SPEC] | V2 0.0–0.6 |
| Odometer settle | roll ~0.9 s, final value legible >= 0.6 s (legible 1.12 -> 1.75+) | V2 0.25–1.75 |
| Orbit drift | slow (~0.3–0.6 px/frame at 720p); no fast orbit [SPEC for exact px] | V2 0.5–4.9 |
| Starburst draw-on | staggered: lines appear over ~0.45 s (5.55 partial -> 6.00 full) | V2 5.55/5.70 |
| Mascot pop | overshoot scale-in, ~0.3 s [SPEC for curve] | V2 4.9–5.4 |
| Family whips | F2 whip-blur 0.40–0.50 s window (blurred re-entry); F1 tile flip 5.0–6.0; quadrant-local, not global | V2 0.4, 5.0–6.0 |
| Phone-UI text reveal | typewriter inside glass panel ("You" @0.25 -> "You are" @0.375) | V2 0.25–0.375 |
| Ghost bleed type | 1–2 offset semi-transparent echoes behind "Why", <=4% offsets | V2 0.5–1.5 |

---

## 3. Unified TARGET LOOK (what every render must satisfy)

1. **Canvas modes.** Mode A: clean monochrome canvas; cut-out subject 30–55%H,
   bottom-center, contact shadow; canvas textures (halftone / ghost echo / light leak /
   grain) on CANVAS ONLY. Mode B: real scene — NO halftone / pixel-grid / ghost overlay
   on footage AT ALL; only grade + rim glow, lockup behind head, cards/doodles beside or
   above, lower-third captions. Families F1–F4 are Mode A by definition. (Delta vs
   Phase-8 rollout: 6 categories were rendered footage-first with scrim + halftone —
   now invalid; see test-results/failure log.)
2. **Lockup.** Mixed-scale sentence: small sans words + ONE giant accent word
   (Archivo-Black-class weight, italic or upright) fully legible <= 0.92W; bleed echo
   <= 4%/side, echo-only. Giant word may pass behind subject torso; never covers face.
3. **Cards.** Rounded, white inner border + accent outer border, pill name label,
   untruncated, >= 40 px on-frame margin, max 4 per beat, no duplicate hashes; content
   differs from master shot (detail / insert / b-roll frame).
4. **Phone UI.** Only over insert world or Mode A canvas — never over Mode B footage;
   bold >= 60 px text on plate >= 0.85 alpha or clean area, contrast >= 4.5:1.
5. **Captions.** Word-sync lower-third, 76 px+ with stroke or plate, on every message beat.
6. **Transitions.** Whip-blur (+scale punch + whoosh) on EVERY comp change (0.20–0.28 s);
   >= 1 recursive zoom-through (~0.5 s); >= 1 invert bite (1–3 frames, inverted echo);
   no hard cuts; frame 1 composed; payoff + end card + loop; no two consecutive comps
   with frame-hash similarity > 0.9.
7. **Stickers/doodles.** Semantic, <= 2 stickers + <= 3 doodles per beat, anchored to type.
8. **Family signatures (U10).** F1 tape + corner brackets + scramble; F2 phone glass +
   orbit cards + typewriter reveal; F3 pixel-mono + starburst draw-on + particles;
   F4 odometer + mascot row + icon row.
9. **Audio.** Whoosh at every whip (V2 audio peaks 1.6/1.95/2.1/3.15/3.35 s [VID];
   per-move SFX parity), music bed, VO ducks music; loudnorm two-pass -14 LUFS / TP <= -1.5 dBTP.
10. **Scramble/odometer/starburst/mascot motion constants** = Section 2.2 values.

## 4. R2 delta log (reference wins over prior spec)

| # | Conflict | Resolution |
| --- | --- | --- |
| D1 | Phase-8 rollout rendered 6 categories footage-first with halftone scrim (legacy QA even checked "halftone present" as a PASS) | REFERENCE WINS: halftone/ghost/grid on canvas only (Mode A); Mode B footage never gets textures; legacy QA rule inverted |
| D2 | Old family system F1/F2/F3 (matte vs scrim anchor) | Replaced by V2 families F1–F4 (all Mode A canvas); old F3 world-pan look retired |
| D3 | No odometer/scramble/starburst/mascot grammar existed | Added from V2 with measured constants |
| D4 | Phone UI allowed over footage in old renders | Now insert-world/canvas only |
| D5 | Whip only on some comp changes | Whip-blur required on EVERY comp change + zoom-through + invert bite present |
| D6 | Giant type sometimes rendered OVER subject (fake occlusion bug, Phase-8 Step-2 lesson) | Type composited under subject matte; face overlap = 0 |

## 5. Pending items

- P1/P3/ANTI photo sets: PENDING (R3). When they arrive: re-ingest, patch
  composition measurements (card anatomy px, giant-word %W, subject %H) and append
  here. Family motion stays video-evidenced from V2.
- Audio whoosh per-transition mapping for V1: music bed is continuous (RMS flat,
  mean 0.223); whoosh positions are therefore taken from visual whip timestamps.
