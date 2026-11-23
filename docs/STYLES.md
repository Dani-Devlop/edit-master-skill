# Category Style Sheets (Phase 5.0)

Per-niche look systems applied by the v3 renderer (G8). One sheet per
reference niche; Cars and Racing share the midnight/electric sheet, as
specified. Fonts are Google Fonts (variable TTFs), driven through PIL
weight axes. Every sheet also fixes: caption scrim strength, grade chain,
signature graphics kit, particle system and the AI insert-beat prompt.

## CARS / LUXURY (`cars`)

- Palette: accent `rgb(0, 229, 255)` / secondary `rgb(120, 190, 255)`, panel bg `rgb(10, 16, 34)` -> `rgb(3, 6, 14)`
- Body font: **Montserrat.ttf** w700 56px; Keyword: **JetBrainsMono-Italic.ttf** w700 62px (accent)
- Grade: `eq=contrast=1.10:saturation=1.05,curves=all='0/0.03 0.5/0.52 1/0.98',colorbalance=bs=0.10:rh=-0.02,vibrance=intensity=0.12`
- Caption scrim: 0.15 | particles: speed
- Signature kit: speed_lines, rpm_counter, gear_pill, whip_flash
- AI insert beat: "midnight blue luxury sports car headlight detail with electric cyan rim light, dark studio, photorealistic, vertical 9:16"

## RACING / MOTORSPORT (`racing`)

- Palette: accent `rgb(0, 229, 255)` / secondary `rgb(255, 120, 60)`, panel bg `rgb(10, 16, 34)` -> `rgb(3, 6, 14)`
- Body font: **Montserrat.ttf** w700 56px; Keyword: **JetBrainsMono-Italic.ttf** w700 62px (accent)
- Grade: `eq=contrast=1.12:saturation=1.08,curves=all='0/0.03 0.5/0.53 1/0.98',colorbalance=bs=0.08:rh=0.05,vibrance=intensity=0.14`
- Caption scrim: 0.15 | particles: speed
- Signature kit: speed_lines, rpm_counter, gear_pill, whip_flash
- AI insert beat: "race car cornering on night circuit with cyan light streaks and motion blur, photorealistic, vertical 9:16"

## BRANDING / CORPORATE (`branding`)

- Palette: accent `rgb(212, 175, 55)` / secondary `rgb(230, 230, 235)`, panel bg `rgb(18, 18, 20)` -> `rgb(6, 6, 8)`
- Body font: **Inter.ttf** w400 56px; Keyword: **PlayfairDisplay-Italic.ttf** w700 76px (accent)
- Grade: `eq=contrast=1.08:saturation=0.95,curves=all='0/0.03 0.5/0.52 1/0.98',colorbalance=bs=0.05:rm=0.03:rh=0.05,vibrance=intensity=0.08`
- Caption scrim: 0.18 | particles: dust
- Signature kit: lower_third, grid_lines, gold_counter, line_draw
- AI insert beat: "minimal corporate lobby interior with warm gold accent lighting and charcoal marble, photorealistic, vertical 9:16"

## TALKING HEAD (`talkinghead`)

- Palette: accent `rgb(232, 120, 80)` / secondary `rgb(255, 210, 180)`, panel bg `rgb(38, 26, 20)` -> `rgb(10, 7, 5)`
- Body font: **Poppins-Medium.ttf** w500 56px; Keyword: **Caveat.ttf** w700 84px (accent)
- Grade: `eq=contrast=1.05:saturation=1.02,curves=all='0/0.03 0.5/0.51 1/0.99',colorbalance=rm=0.03:rh=0.06,vibrance=intensity=0.10`
- Caption scrim: 0.15 | particles: dust
- Signature kit: speaker_pill, quote_payoff, word_sync
- AI insert beat: "podcast microphone on warm wooden desk in terracotta light, shallow depth of field, photorealistic, vertical 9:16"

## MOTIVATION / FITNESS (`fitness`)

- Palette: accent `rgb(180, 255, 0)` / secondary `rgb(255, 255, 255)`, panel bg `rgb(10, 12, 8)` -> `rgb(2, 3, 2)`
- Body font: **Oswald.ttf** w600 62px; Keyword: **Montserrat-Italic.ttf** w800 70px (accent)
- Grade: `eq=contrast=1.18:saturation=1.10,curves=all='0/0.015 0.5/0.55 1/0.985',vibrance=intensity=0.15`
- Caption scrim: 0.20 | particles: none
- Signature kit: rep_counter, heartbeat, impact_flash
- AI insert beat: "athlete taping hands in dark gym with volt green rim light, high contrast, photorealistic, vertical 9:16"

## MINDSET / FOCUS (`mindset`)

- Palette: accent `rgb(230, 180, 110)` / secondary `rgb(210, 210, 205)`, panel bg `rgb(52, 52, 50)` -> `rgb(16, 16, 15)`
- Body font: **Lora.ttf** w400 54px; Keyword: **Lora-Italic.ttf** w500 72px (accent)
- Grade: `eq=contrast=0.97:saturation=0.85:brightness=0.015,curves=all='0/0.06 0.5/0.52 1/0.97',noise=alls=7:allf=t`
- Caption scrim: 0.10 | particles: pollen
- Signature kit: breathing_zoom, quote_payoff, soft_leak
- AI insert beat: "foggy forest at dawn with candle amber sunrise glow, heavy film grain, calm mood, photorealistic, vertical 9:16"

## EDUCATION (`education`)

- Palette: accent `rgb(28, 80, 160)` / secondary `rgb(240, 246, 255)`, panel bg `rgb(242, 246, 252)` -> `rgb(214, 226, 242)`
- Body font: **Lora.ttf** w500 54px; Keyword: **Lora-Italic.ttf** w700 72px (accent)
- Grade: `eq=brightness=0.02:contrast=1.04:saturation=0.98,curves=all='0/0.02 0.5/0.51 1/0.99',vibrance=intensity=0.06`
- Caption scrim: 0.32 | particles: none
- Signature kit: marker_kw, underline_draw, page_wipe, diagram_lines
- AI insert beat: "open notebook with handwritten blue-ink diagram and pen on white desk, soft daylight, photorealistic, vertical 9:16"

## CITY / URBAN (`city`)

- Palette: accent `rgb(255, 45, 170)` / secondary `rgb(0, 230, 200)`, panel bg `rgb(16, 6, 20)` -> `rgb(4, 2, 8)`
- Body font: **SpaceGrotesk.ttf** w600 58px; Keyword: **JetBrainsMono-Italic.ttf** w700 64px (accent)
- Grade: `eq=contrast=1.15:saturation=1.18,curves=all='0/0.02 0.5/0.54 1/0.99',colorbalance=bs=0.08:mg=0.05,vibrance=intensity=0.16`
- Caption scrim: 0.16 | particles: none
- Signature kit: rgb_split, strobe, neon_callout, waveform_bars
- AI insert beat: "neon night street with magenta and teal signs reflected on wet asphalt, photorealistic, vertical 9:16"

## NATURE (`nature`)

- Palette: accent `rgb(224, 196, 120)` / secondary `rgb(180, 220, 170)`, panel bg `rgb(14, 30, 20)` -> `rgb(4, 10, 7)`
- Body font: **Inter.ttf** w300 54px; Keyword: **Lora-Italic.ttf** w500 74px (accent)
- Grade: `eq=contrast=1.04:saturation=0.95,curves=all='0/0.04 0.5/0.51 1/0.985',colorbalance=gs=0.05:rh=0.03,vibrance=intensity=0.08`
- Caption scrim: 0.14 | particles: pollen
- Signature kit: pollen_particles, soft_leak, slow_parallax, sand_callout
- AI insert beat: "misty pine forest with floating golden pollen in soft light beams, deep green tones, photorealistic, vertical 9:16"

## FOOD / RESTAURANT (`food`)

- Palette: accent `rgb(255, 107, 53)` / secondary `rgb(255, 190, 120)`, panel bg `rgb(28, 15, 7)` -> `rgb(6, 3, 2)`
- Body font: **Poppins-Regular.ttf** w400 56px; Keyword: **PlayfairDisplay-Italic.ttf** w700 78px (accent)
- Grade: `eq=contrast=1.07:saturation=1.02,curves=all='0/0.035 0.5/0.52 1/0.99',colorbalance=bs=0.04:rh=0.09:gh=0.02,vibrance=intensity=0.12`
- Caption scrim: 0.18 | particles: dust
- Signature kit: label_callout, counter_card, line_draw
- AI insert beat: "overhead gourmet dish plating with warm orange rim light on dark wood, gentle steam, photorealistic, vertical 9:16"

## TECH / CODING (`tech`)

- Palette: accent `rgb(0, 255, 130)` / secondary `rgb(180, 190, 200)`, panel bg `rgb(8, 12, 10)` -> `rgb(2, 4, 3)`
- Body font: **Inter.ttf** w400 54px; Keyword: **JetBrainsMono-Italic.ttf** w700 62px (accent)
- Grade: `eq=contrast=1.08:saturation=0.92,curves=all='0/0.03 0.5/0.52 1/0.98',colorbalance=bs=0.09:rh=0.02,vibrance=intensity=0.07`
- Caption scrim: 0.16 | particles: none
- Signature kit: terminal_typing, code_diff, phosphor_counter
- AI insert beat: "dark terminal screen close-up with green phosphor code text glow, photorealistic, vertical 9:16"

## TRAVEL (`travel`)

- Palette: accent `rgb(255, 170, 80)` / secondary `rgb(255, 236, 210)`, panel bg `rgb(60, 30, 24)` -> `rgb(14, 8, 6)`
- Body font: **Nunito.ttf** w600 56px; Keyword: **Caveat.ttf** w700 84px (accent)
- Grade: `eq=contrast=1.06:saturation=1.08,curves=all='0/0.035 0.5/0.52 1/0.99',colorbalance=rs=0.03:rh=0.10:gh=0.03,vibrance=intensity=0.13`
- Caption scrim: 0.16 | particles: dust
- Signature kit: stamp_pop, map_line_draw, passport_wipe, sunset_callout
- AI insert beat: "coastal road at sunset with warm orange sky and a vintage suitcase, photorealistic, vertical 9:16"

## FASHION (`fashion`)

- Palette: accent `rgb(255, 190, 205)` / secondary `rgb(240, 240, 245)`, panel bg `rgb(26, 18, 20)` -> `rgb(6, 4, 6)`
- Body font: **Inter.ttf** w400 52px; Keyword: **PlayfairDisplay.ttf** w600 78px (accent)
- Grade: `eq=contrast=1.06:saturation=0.85,curves=all='0/0.03 0.5/0.52 1/0.985',colorbalance=rm=0.03:bh=0.02,vibrance=intensity=0.06`
- Caption scrim: 0.16 | particles: dust
- Signature kit: frame_in_frame, shutter_wipe, minimal_callout
- AI insert beat: "elegant fashion detail with blush fabric folds on noir background, studio light, photorealistic, vertical 9:16"

## MUSIC (`music`)

- Palette: accent `rgb(170, 90, 255)` / secondary `rgb(255, 170, 60)`, panel bg `rgb(24, 10, 38)` -> `rgb(6, 3, 12)`
- Body font: **JetBrainsMono.ttf** w500 52px; Keyword: **PlayfairDisplay.ttf** w600 78px (accent)
- Grade: `eq=contrast=1.10:saturation=1.10,curves=all='0/0.03 0.5/0.53 1/0.99',colorbalance=bs=0.06:ms=0.04:rh=0.04,vibrance=intensity=0.12`
- Caption scrim: 0.15 | particles: none
- Signature kit: waveform_bars, beat_strobe, quote_payoff
- AI insert beat: "concert stage bathed in purple and amber lights with crowd silhouettes, photorealistic, vertical 9:16"

## PRODUCT DEMO (`product`)

- Palette: accent `rgb(40, 120, 255)` / secondary `rgb(245, 247, 250)`, panel bg `rgb(246, 248, 252)` -> `rgb(220, 228, 240)`
- Body font: **Poppins-Medium.ttf** w500 54px; Keyword: **Poppins-SemiBold.ttf** w700 66px (accent)
- Grade: `eq=contrast=1.05:brightness=0.015:saturation=1.02,curves=all='0/0.02 0.5/0.51 1/0.99',vibrance=intensity=0.08`
- Caption scrim: 0.30 | particles: none
- Signature kit: spec_table, check_draw, spin_kenburns, clean_callout
- AI insert beat: "smartphone product shot on clean white pedestal with cobalt blue accent light, studio photography, vertical 9:16"

## PODCAST CLIP (`podcast`)

- Palette: accent `rgb(255, 190, 70)` / secondary `rgb(240, 240, 240)`, panel bg `rgb(20, 16, 12)` -> `rgb(5, 4, 3)`
- Body font: **Poppins-Bold.ttf** w700 66px; Keyword: **Caveat.ttf** w700 88px (accent)
- Grade: `eq=contrast=1.10:saturation=0.95,curves=all='0/0.03 0.5/0.52 1/0.98',colorbalance=bs=0.05:rh=0.04,vibrance=intensity=0.09`
- Caption scrim: 0.22 | particles: none
- Signature kit: big_word_sync, speaker_pill, quote_payoff
- AI insert beat: "condenser microphone in dark studio with a single warm amber accent light, photorealistic, vertical 9:16"

### Honest substitutions

- Fashion asks for Didot (commercial license): substituted with Playfair Display, the closest open high-contrast serif.
- Talking-head asks for a script accent: Caveat is used (open equivalent).
- City asks for 'glitch mono': JetBrains Mono Italic + ffmpeg `rgbashift` flashes implement the glitch vocabulary.
- Mindset 'no hard cuts': soft mask wipes only, breathing 4-6-8 zoom, heavy grain baked into the grade.

---

# Phase 8.0 Depth-Anchor Sheets (16 reps, depth-layered 3D-type system)

Per-category depth anchor, layout family, palette accent and signature graphic
for the R1-R12 motion system (SKILL.md "Depth-Layered 3D-Type Motion System").
Anchors were probe-driven (4 rembg frames per video) and are honest: F1/F2
categories carry real 30fps alpha mattes (occlusion pixel-verified in QA);
F3 categories use duotone-scrim depth with NO occlusion claim.

| # | video | category | family | depth anchor | palette accent | signature graphic |
|---|-------|----------|--------|--------------|----------------|-------------------|
| 1 | talkinghead_1 | Talking head | F1 talking-head stack | masked subject (u2net 30fps, edge-IoU 0.991) | terracotta #E87850 | speaker pill "SPEAKER TAKEOVER" + quote payoff |
| 2 | podcast_1 | Podcast clip | F1 talking-head stack | masked subject (u2net 30fps, 0.992) | amber #FFBE46 | "REC 00:26" pill + two-mic label |
| 3 | education_1 | Education | F1 talking-head stack | masked subject (u2net 30fps, 0.992) | ink blue #1C50A0 | "DAILY DRILL" pill + step labels |
| 4 | fitness_1 | Motivation / Fitness | F1 talking-head stack | masked subject - athlete (u2net 30fps, 0.978) | volt #B4FF00 | rep counter pill "REP COUNTER 8/12" |
| 5 | food_1 | Food / Restaurant | F2 hero object | masked object - dish (u2net 30fps, 0.990) | orange #FF6B35 | "READS $4,000" pill + order callout |
| 6 | product_2 | Product demo | F2 hero object | masked object - device (u2net 30fps, 0.987) | cobalt #2878FF | "SPEC SHEET V2" pill + check draw |
| 7 | branding_1 | Branding / Corporate | F2 hero object | masked object - signage (u2net 30fps, 0.980) | gold #D4AF37 | gold counter pill "GOLD COUNTER x12" |
| 8 | nature_1 | Nature | F3 world pan | world-pan scrim (matte FAIL on water: u2net 0.678 / isnet 0.773 - honest flip, C4 amendment) | sand #E0C478 | "TIDE TABLE +0.4M" mono label |
| 9 | cars_2 | Cars / Luxury | F3 world pan | world-pan scrim (probe fg 5.9%, unstable) | cyan #00E5FF | "GEAR PILL N-60" + speed stickers |
| 10 | racing_1 | Racing / Motorsport | F3 world pan | world-pan scrim (probe fg 0.1%) | cyan/orange | "RPM 12,400" mono pill + whip flash |
| 11 | city_1 | City / Urban | F3 world pan | world-pan scrim (probe IoU 0.005) | magenta #FF2DAA | "ROOFTOP 51F" pill + neon callout |
| 12 | fashion_1 | Fashion | F3 world pan | world-pan scrim (probe IoU 0.0) | blush #FFBECD | "LOOKBOOK 12" pill + frame-in-frame |
| 13 | mindset_1 | Mindset / Focus | F3 world pan | world-pan scrim (probe bw 0.16) | amber #E6B46E | "BREATH 4-4-6" pill + soft leak |
| 14 | music_1 | Music | F3 world pan | world-pan scrim (probe IoU 0.14) | purple #AA5AFF | "128 BPM LIVE" pill + waveform |
| 15 | tech_1 | Tech / Coding | F3 world pan | world-pan scrim (probe fg 0.2%, dark screens) | phosphor #00FF82 | "> ping 12ms" terminal label + UPLINK pill |
| 16 | travel_1 | Travel | F3 world pan | world-pan scrim (probe bw 0.17) | sunset #FFAA50 | "ROUTE 1 OPEN" pill + stamp pop |

Layout rules per family:
- **F1 talking-head stack**: giant type (2-line slam) behind the speaker's
  head; cards below face rect; stickers on side thirds; phone typing beat;
  payoff loops the hook footage (REWIND type over the b0 window).
- **F2 hero object**: salient object (dish/device/signage) occludes the giant
  type; cards flank lower third; object top-30% zone is the protected area.
- **F3 world pan**: NO matte claim. Giant type under duotone scrim gradient +
  vignette, upper 55%; cards / stickers / labels / phone confined to the
  lower safe band (y >= 1080 of 1920) so any in-frame face stays clear; depth
  QA = scrim separation + type legibility (honest naming in QA gate).

Shared rhythm (all families): b0 type slam + glitch -> b1 type -> b2 type +
zoom-through exit -> b3 card cascade + connector -> b4 phone typing ->
b5 AI surreal insert + pill + impact -> b6 cards + connector -> b7 signature
type -> b8 echo phone (hook words retype) -> b9 payoff (loop the hook).
Every beat ends with a graphics-only whip blur (subject/object stays sharp).

---

# STYLES v2 — Phase 11.1 family system (VIDEO-2 reference wins)

16 categories map onto four VIDEO-2 families (all Mode A canvas compositions unless the
category's footage has no matte-able subject — then message beats run Mode B footage-first
per the Mode rules). Category identity = copy + cards + insert world + signature motion;
palette/type = family system.

| Category | Family | Canvas | Accent | Signature graphics |
| --- | --- | --- | --- | --- |
| talkinghead_1 | F1 | white 245,246,242 | neon-yellow 190,245,40 | tape + corner brackets + scramble-decode |
| podcast_1 | F1 | white | neon-yellow | tape + brackets + scramble |
| education_1 | F1 | white | neon-yellow | tape + brackets + scramble + vertical word-stack |
| fitness_1 | F1 | white | neon-yellow | tape + brackets + v-stack + pixel blocks |
| food_1 | F2 | navy 14,28,62 | blue 88,148,255 | glass phone panel + typewriter + orbit task cards |
| product_2 | F2 | navy | blue | glass panel + typewriter + orbit cards |
| tech_1 | F2 | navy | blue | glass panel + typewriter + orbit cards |
| branding_1 | F2 | navy | blue | glass panel + typewriter + orbit cards |
| racing_1 | F3 | maroon 46,10,20 | red-pink 255,92,110 | pixel-mono type + starburst draw-on + pixel particles |
| cars_2 | F3 | maroon | red-pink | pixel-mono + starburst + particles |
| city_1 | F3 | maroon | red-pink | pixel-mono + starburst + particles |
| music_1 | F3 | maroon | red-pink | pixel-mono + starburst + particles |
| fashion_1 | F4 | light-gray 238,238,241 | pink 250,112,142 | odometer + blob mascots + icon rows |
| mindset_1 | F4 | light-gray | pink | odometer + mascots + icon rows |
| travel_1 | F4 | light-gray (insert backdrops on canvas beats) | pink | odometer + mascots + icon rows |
| nature_1 | F4 | light-gray | pink | odometer + mascots + icon rows |

Superseded: the Phase-5.0 per-category palettes and the Phase-8 F1/F2/F3 matte-vs-scrim
depth families (the 6 footage-first scrim renders measured in the A3 audit are invalid).


---

## v3 — Style-DNA additions (Phase 14.1, 2026-11-22 06:47 UTC)

- **MV DARK MONO (F3 variant)**: B&W lifted-blacks base + volt accent (189,255,0); color-pop
  inserts keep source color; grain/scanline bites <=0.15s; karaoke volt active word.
- **Fitness energy (F1 Mode B)**: source color + neon-yellow (190,245,40); mirrored odd beats.
- **Food fresh (F4 Mode B)**: pink (250,112,142); odometer ingredient pills.
- **Cars night drive (F2 Mode B)**: glass-blue (88,148,255) + day-for-night grade when footage is daytime.
- **Pets playful (F4 variant)**: sunny-orange (255,176,46); paw stickers, odometer counters.
- Caption grammar: 76px+stroke equivalent (56-64px @720w), band 0.72-0.90H, underline chrome,
  beat pill + progress bar = family chrome (G13 guarantee >=0.006 accent fraction).
# STYLES v4 — Phase 16.0 LEAP family addendum

Appended 2026-11-24 to the Phase 5.0 category sheets above. These five LEAP family
sheets are the preset bank (presets/*.json, sha256-logged in every gate json).
The renderer loads one preset per run (G-P13); onboarding may override platform /
palette / end-card / bilingual / TTS / genre / length (P18).

## F3 — DARK MONO (music_video, `mv_darkmono.json`)

- Reference: gritty B&W rap MV, volt accent on grade + type only
- Palette: B&W base `bw` + accent `rgb(189,255,0)` volt; color-pop: keep source color
  on color inserts only
- Grade: high-contrast B&W curve, crushed-black floor, grain 4.2 matched to source,
  vignette 0.20, halation on highlights
- Captions: whisper-word-sync karaoke (volt accent active 1.2x), band 0.74–0.90,
  font 56px, stroke 3
- Signature kit: freeze+slam hook with occlusion, ghost echo, selection brackets,
  invert bite ≤0.15s, glitch bites, whip edge-clamp
- Modes: 9:16 primary + 1:1 + 4:5

## F4 — LIGHT GRAY + PINK (food, `food_fresh.json`)

- Palette: light-gray canvas + accent `rgb(250,112,142)` pink (soft family — G-P8
  card scan uses accent-relative saturation floor)
- Grade: bright airy curve, warm highlights, gentle contrast 1.06–1.10
- Captions: beat-keyword lines (no vox), pink underline accents, band 0.76+
- Signature kit: odometer (BPM/real quantities), starburst payoff, highlighter tape,
  light-leak on Mode A entrance, speed-ramp on pour/sizzle
- Modes: 9:16 primary

## ENERGY (fitness, `fitness_energy.json`)

- Palette: dark slate + electric accent, high-energy cuts
- Grade: contrast 1.12, saturation 1.08, sweat-highlight bloom
- Captions: beat-keyword (no vox), punch-in on every emphasis word
- Signature kit: rep odometer from motion cycles, orbit cards High/Med/Low,
  speed-ramp 0.4x/1.6x on movement peaks, whip between comps
- Modes: 9:16 primary

## NIGHT DRIVE (cars, `cars_nightdrive.json`)

- Palette: midnight panel + electric accent
- Grade: day-for-night on daytime source, cyan rim-light cast, halation on
  headlight highlights, scanline bites ≤0.15s
- Captions: beat-keyword, mono-italic accent words
- Signature kit: speed lines, gear pill, glitch entrance, whip edge-clamp
- Modes: 9:16 primary (16:9 source letterbox-aware)

## PLAYFUL (pets, `pets_playful.json`)

- Palette: warm cream + amber accent (hue-adjacent fur protected — card scan
  excludes desaturated fur by strict-hue + fill-ratio)
- Grade: bright, saturated 1.10, warm bias
- Captions: beat-keyword, bouncy ease-out-back entrances
- Signature kit: zoomies speed-ramp, polaroid cascade with real different frames,
  odometer treats, starburst payoff
- Modes: 9:16 primary

## P7 color-science chain (all families)

curves/LUT → skin-tone protection → halation/bloom on highlights → grain matched
to source (σ4.2 default) → subtle vignette 0.20 → per-family palette consistency
check (accent present in >60% of sampled frames, G-P7). GRADE JUMP vs raw is
measured per video with a before/after pair in the scoresheet.
