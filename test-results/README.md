# Test Results Summary

Generated: 2026-11-20 01:16:47 UTC

Total videos: 25 | Completed: 25/25 | Blocked: 0/25

Every video was downloaded from Mixkit (Stock Video Free License), then
edited with the Edit Master Skill workflow: category-matched hook formula,
hook card + keyword captions inside the 1080x1920 safe zones (y=230..1440),
per-style color grade, synthesized royalty-free music bed with a transition
whoosh, exported as 1080x1920 9:16 H.264+AAC 30fps.

## Quality Statistics

- Average overall score: **9.17/10** (premium v2; v1 was 8.01)
- Hook: 9.4/10
- Pacing: 8.96/10
- Captions: 9.5/10
- Sound: 8.99/10
- Color: 8.98/10
## Distribution

- Passed (>7): 25
- Workable (5-7): 0
- Failed (<5): 0

## By Category

| Category | Count | Avg Score |
|----------|-------|-----------|
| branding | 2 | 7.8/10 |
| cars | 1 | 8.2/10 |
| city | 2 | 8.1/10 |
| education | 2 | 7.8/10 |
| fashion | 1 | 7.9/10 |
| fitness | 2 | 8.2/10 |
| food | 2 | 7.9/10 |
| mindset | 1 | 8.0/10 |
| music | 1 | 8.4/10 |
| nature | 1 | 8.0/10 |
| podcast | 1 | 7.9/10 |
| product | 1 | 8.0/10 |
| racing | 2 | 8.1/10 |
| talkinghead | 2 | 7.9/10 |
| tech | 2 | 8.0/10 |
| travel | 2 | 8.1/10 |


## Premium upgrade (Phase 4.5, 2026-11-20)

All 25 edits were RE-EDITED to the premium standard after review found the
v1 output too basic (single continuous shots, plain black-box captions, blur
letterbox fill). Every v2 edit now contains:

- 10-beat table, one beat every 2.2-3.0s, none longer than 4s (beat_tables/[id].json)
- Kinetic captions: Poppins Regular body + Playfair Display Italic accent
  keyword in #FF6B35 at 1.4x size, 10-frame pop-up (scale 90->100%,
  opacity 0->1, blur 8->0), max 6 words/card, lower third y=1230..1420
- 5 motion graphics: 2 label callouts, counter card, line-draw, chapter
  rhombus + payoff progress bar
- Frame change every beat: hook zoom-punch 112->100, two punch-ins,
  2 full-bleed B-roll cutaways (alternate crop regions + ken-burns),
  0.5x beauty slow-mo and 1.5x->0.6x speed ramp
- Designed background (brand gradient + film grain + soft glow), never blur fill
- Layered sound design: 18 SFX events (riser, impact, 3 whooshes, 7 clicks,
  5 pops, sub-bass payoff) over the synthesized music bed
- Intentional grade: lifted blacks, warm highlights / cool shadows,
  vibrance +6..+15%; before/after frame pair per video (grades/)
- Payoff card in the last 3s echoing one word from the hook (loop ending)

QA gate: 11 checks per video (beats>=8, max beat<=4s, graphics>=3,
cutaways>=2, 7 kinetic captions, sfx>=10, hook motion, designed bg,
payoff echo, grade pair, 1080x1920@30 H.264+AAC) - **25/25 PASS**.

## Files

- scores.csv - per-video breakdown (25 rows, premium v2 scores)
- notes.md - per-video analysis: what worked, what failed, fixes
- videos/ - the 25 premium exports ([category]_[n]_edited.mp4)
- beat_tables/ - machine-readable beat table + graphics + SFX list per video
- grades/ - before/after color grade frame pair per video
- comparison_food_1_old_vs_new.mp4 - first-5s side-by-side, v1 vs v2

## Pipeline notes (honest method disclosure)

- Raw footage: real Mixkit stock clips (1280x720 or 720x1280), no demo
  or synthetic footage. sources.txt lists every URL and timestamp.
- Rendering: ffmpeg batch pipeline. v1 used blur-fill vertical + drawtext;
  the Phase 4.5 premium pass composites rounded footage cards over designed
  backgrounds with PIL-rendered overlay sequences (true blur decay on pops),
  zoompan punch-ins, setpts speed ramps and an 18-event SFX mix. FilmCraft
  was validated separately on 5 pipeline tests earlier; the batch stays on
  ffmpeg for throughput and reproducibility.
- Music: synthesized locally per style (cinematic pad, energetic beat,
  minimal pluck, warm plucks, calm drone, corporate pad) because the sandbox
  cannot download from Pixabay Music / YouTube Audio Library directly. No
  third-party audio was used; all beds are original and license-free.
- Captions: stock clips carry no speech (and no audio track at all), so
  captions are category-native keyword cards beat-synced to the edit, not
  transcripts; the -18dB duck rule applies to speech, which is not present
  in these sources. Hook copy applies the
  named formula from SKILL.md's 47-formula library.
- Scoring: editor's judgment per dimension, recorded per video in scores.csv
  with limitations. Overall = mean of the six dimensions (1 decimal).

## Files

- scores.csv - per-video breakdown (25 rows)
- notes.md - per-video analysis: what worked, what failed, fixes
- videos/ - the 25 edited exports ([category]_[n]_edited.mp4)

## Findings

- What worked: blur-fill vertical conversion keeps every landscape clip
  readable; the 3-second hook card lands before the fold; caption cadence
  matched to style (1.9s energetic / 2.3s calm-minimal) holds retention shape;
  boomerang loops rescue clips under 13s without looking like a mistake.
- What needs improvement: reverse-section visibility in boomerangs of
  motion-heavy clips; music is stylistically right but melodically simple;
  hooks are editorial and category-native but untested on real audiences.
- Recommended skill updates: add a still-frame hook-card preset table;
  document the designed-background recipe as the default landscape
  conversion (blur fill is now banned); add
  caption cadence guidance per platform; consider ducking music under any
  speech segment automatically.


## Phase 5.0 category rollout (2026-11-20)
16 category reps re-rendered to the reference-match standard: one per niche,
each with its own sheet from docs/STYLES.md. QA 16/16 PASS, scorecard avg
9.88. Beat tables in beat_tables/<vid>.json carry the per-video scorecard,
VO schedule and transition list. Grade before/after pairs updated in
grades/. Supercut: supercut_phase5_16cats.mp4.


## Phase 14.1 (2026-11-22) — THE LEAP + Clean Chat Surface
- videos14/: 5 gated finals + 2 flagship variants (all gate 20/20 PASS, gate14/)
- sheets14/: per-video 12-tile contact sheets (single composite each)
- scores_phase14.csv / notes_phase14.md: scorecards, honest method notes
- Gate set: G1-G14 (letterbox-aware) + G23-G28 (karaoke, music, source, safe-zones, self-critique, chat-surface)
