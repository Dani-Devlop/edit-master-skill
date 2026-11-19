# Test Protocol — the 25-Video Matrix

SKILL.md's Testing Protocol defines the matrix abstractly: 25 videos
spanning the six brand styles and all budget tiers, scored 1-10 per video
on six criteria, honest reporting throughout. This document is this
repository's concrete realization of that protocol: 16 categories, 25
videos, matching the sources in `sources.txt` and `raw_videos/`
(with `raw_videos/manifest.json` recording metadata per file).

## The matrix (16 categories, 25 videos)

| # | Category | Videos | Raw sources (raw_videos/) |
|---|----------|--------|---------------------------|
| 1 | Cars / Luxury | 2 | cars_1.mp4, cars_2.mp4 |
| 2 | Racing / Motorsport | 2 | racing_1.mp4, racing_2.mp4 |
| 3 | Branding / Corporate | 2 | branding_1.mp4, branding_2.mp4 |
| 4 | Talking Head / Interview | 2 | talkinghead_1.mp4, talkinghead_2.mp4 |
| 5 | Motivation / Fitness | 2 | fitness_1.mp4, fitness_2.mp4 |
| 6 | Mindset / Focus | 1 | mindset_1.mp4 |
| 7 | Education / Learning | 2 | education_1.mp4, education_2.mp4 |
| 8 | City / Urban | 2 | city_1.mp4, city_2.mp4 |
| 9 | Nature / Landscape | 1 | nature_1.mp4 |
| 10 | Food / Restaurant | 2 | food_1.mp4, food_2.mp4 |
| 11 | Tech / Coding | 2 | tech_1.mp4, tech_2.mp4 |
| 12 | Travel / Destination | 2 | travel_1.mp4, travel_2.mp4 |
| 13 | Fashion / Style | 1 | fashion_1.mp4 |
| 14 | Music / Performance | 1 | music_1.mp4 |
| 15 | Product Demo | 2 | product_1.mp4, product_2.mp4 |
| 16 | Podcast Clip | 1 | podcast_1.mp4 |
| — | **Total** | **25** | |

Format per category: b-roll-driven categories (cars, racing, city,
nature, travel, food, fashion, music, product) run short-form vertical
edits; Talking Head / Interview and Podcast Clip exercise the long-form
beat sheet on a horizontal master first, then the vertical repurpose.
Together the run spans all six brand styles (minimal, cinematic,
energetic, corporate, playful, luxury) and the budget tiers.

## Scoring

Score each video 1-10 on six dimensions. **Overall is the average of the
six.** Per SKILL.md, a video with any dimension at 3 or lower is a FAIL
regardless of the mean.

| Dimension | What it measures |
|-----------|------------------|
| hook effectiveness | the first 2 seconds: motion, on-screen card, spoken hook |
| pacing | frame-change rhythm; beats inside the pacing budget |
| caption quality | word-sync accuracy + safe zones + readability |
| sound design | music fit, SFX on changes, VO intelligibility |
| color grading | consistency across cuts, skin tones, brand look |
| overall polish | the whole edit as a viewer experiences it |

`test-results/scores.csv` schema (header + one row per video):

```
video_id,category,hook_effectiveness,pacing,caption_quality,sound_design,color_grading,overall_polish,overall,verdict,notes
```

Example rows (arithmetic checked):

```
cars_1,Cars / Luxury,8,7,9,7,8,8,7.83,PASS,loop word lands; grade matched across cuts
food_2,Food / Restaurant,5,3,7,6,6,5,5.33,FAIL,pacing flagged: static shots over the budget in beats 3-5
```

## The honest reporting rule

- **Never fabricate an edited video.** If a renderer or MCP tool was
  unavailable, say so and report which tests ran and which are blocked.
  A fabricated render is worse than a missing one.
- **A blocked test names the real reason.** "Renderer unavailable",
  "source download failed", "no usable transcript" — the actual cause,
  not a vague status. Record the verdict as BLOCKED in `scores.csv`.
- **Retry alternative sources up to 3 attempts.** A dead or unusable
  source gets up to three replacement attempts from `sources.txt` or a
  re-sourced URL before the test is declared blocked.

## Required artifacts

| Artifact | Location | Content |
|----------|----------|---------|
| Source list | `sources.txt` | one line per source video: URL, category, download date |
| Raw sources | `raw_videos/` | the 25 source files + `manifest.json` |
| Scores | `test-results/scores.csv` | the schema above, header + 25 rows |
| Notes | `test-results/notes.md` | per video: what worked, what did not, the one fix to try next |
| Renders | `test-results/videos/` | the edited output per video, `<video_id>.mp4`, at the export spec |

## How to run

1. Read `sources.txt` and `raw_videos/manifest.json` to confirm the 25
   sources and their categories.
2. For each video, run the skill end to end: onboarding (one shared
   `voice.md` for the run, or per-category), hooks scored on the
   5-property panel, beat sheet, EDL from a real transcript, humanizer,
   caption lint.
3. Render to the export spec into `test-results/videos/`.
4. Score all six dimensions; write one `scores.csv` row per video; write
   the notes entry (what worked, what did not, the one fix to try next).
5. Blocked? Name the real reason, retry up to 3 alternative sources, then
   record BLOCKED. Never fabricate.
6. Summarize in `test-results/notes.md`: runs, passes, fails, blocks, and
   the single biggest pattern across the matrix.

## How to add a new category

1. Pick a category the six brand styles can all express; avoid categories
   that only work in one style.
2. Add a row to the matrix table with its count, and keep the total at 25
   — rebalance an existing category if needed and say so in the change.
3. Add the sources to `sources.txt` and entries to
   `raw_videos/manifest.json`, following the existing naming scheme.
4. Note which hook formulas fit the category (see `docs/HOOKS.md`) so the
   pairing is documented for the next run.
5. Keep the `scores.csv` schema unchanged; the header is load-bearing.

## Export spec

1080x1920, H.264 (`yuv420p`, CRF about 23), AAC 192 kbps, 30 fps,
`+faststart` — identical to the delivery export spec in `docs/TOOLS.md`.
All categories render vertical at this spec; Talking Head / Interview and
Podcast Clip keep a horizontal master for the long-form pass before the
vertical repurpose.
