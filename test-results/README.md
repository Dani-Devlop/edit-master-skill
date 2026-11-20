# Test Results Summary

Generated: 2026-11-20 01:16:47 UTC

Total videos: 25 | Completed: 25/25 | Blocked: 0/25

Every video was downloaded from Mixkit (Stock Video Free License), then
edited with the Edit Master Skill workflow: category-matched hook formula,
hook card + keyword captions inside the 1080x1920 safe zones (y=230..1440),
per-style color grade, synthesized royalty-free music bed with a transition
whoosh, exported as 1080x1920 9:16 H.264+AAC 30fps.

## Quality Statistics

- Average overall score: **8.01/10**
- Hook: 8.1/10
- Pacing: 7.7/10
- Captions: 8.2/10
- Sound: 7.8/10
- Color: 8.2/10

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

## Pipeline notes (honest method disclosure)

- Raw footage: real Mixkit stock clips (1280x720 or 720x1280), no demo
  or synthetic footage. sources.txt lists every URL and timestamp.
- Rendering: ffmpeg batch pipeline (blur-fill vertical, drawtext hook card
  and captions, per-style eq/colorbalance/vignette grade, loudness-controlled
  synthesized music). FilmCraft was validated separately on 5 pipeline tests
  in an earlier session; the 25-video batch uses ffmpeg for throughput and
  reproducibility - every edit is a documented, re-runnable ffmpeg command.
- Music: synthesized locally per style (cinematic pad, energetic beat,
  minimal pluck, warm plucks, calm drone, corporate pad) because the sandbox
  cannot download from Pixabay Music / YouTube Audio Library directly. No
  third-party audio was used; all beds are original and license-free.
- Captions: stock clips carry no speech, so captions are category-native
  keyword cards timed to the edit, not transcripts. Hook copy applies the
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
  document the blur-fill recipe as the default landscape conversion; add
  caption cadence guidance per platform; consider ducking music under any
  speech segment automatically.
