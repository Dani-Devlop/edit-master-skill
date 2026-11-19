# Changelog

All notable changes to this project are documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet. Changes land here before the next tag.

## [1.0.0] - 2026-11-19

First release: the complete skill, templates, worked examples, test
protocol, community files, CI and release automation.

### Added

- 47 hook formulas — 21 long-form (hook = first 15 seconds) + 26 short-form
  (hook = first 2 seconds, spoken line and on-screen line written
  separately), adapted from the two MIT-licensed upstream repositories.
- 5-property hook scoring panel: SPECIFICITY / ADDRESS / STAKES / CURIOSITY
  / BREVITY, each 0-100; verdict = 60% mean + 40% weakest property; bands
  STRONG >= 72, WORKABLE >= 55, WEAK < 55.
- Beat sheets for short-form (15-45s working range) and long-form (5-30
  min), with timing rules at a 165 wpm planning default.
- Edit decision lists (EDL) in markdown and JSON: KEEP / CUT-DEAD /
  CUT-FILLER / CUT-RETAKE / BROLL / SPEED actions with timecodes from a
  real transcript, never guessed.
- Humanizer pass: automatic fixes (invisible characters, typography, slop
  lexicon), flag-not-rewrite structural tells, and the 5-check detection
  panel (BURSTINESS, SPECIFICITY, SLOP DENSITY, FINGERPRINT, VOICE);
  PASS = overall 70+ with no check below 55.
- Caption linting: Job A / Job B, the 125-visible-character rule for line
  one, one ask per caption, up to five hashtags, no links in captions.
- Viral research by outlier multiple (views divided by the account's own
  recent median), 4 direct + 4 adjacent + 2-4 outsized account mix.
- Retention analysis: hook leak, cliffs, slide — one fix per report.
- The 12 editing principles.
- The 5-phase workflow: Onboard, Research, Hook+Script, Edit Plan,
  Render+QA.
- The 16-point QA gate.
- Tool integrations: ffmpeg, Remotion, HyperFrames, FilmCraft, Premiere,
  DaVinci Resolve, CapCut, with transcription via whisper.
- Brand voice template (templates/voice.md) and the 10-question onboarding.
- Three worked examples (examples/).
- CI (markdown lint, link check, structure anchors, required files) and a
  tag-driven release workflow.
- Community files: contributing guide, security policy, code of conduct,
  installation and workflow guides, the complete hook library reference,
  tool integration guide, FAQ, worked examples and the 25-video test
  protocol.

### Credits

Synthesized and adapted with thanks to:

- Joseph | Video Editing — minimal talking-head and premium reel Claude
  editing workflows
- Dan Kieft — AI video editing course workflows
- Grow with Alex — Claude video editing fundamentals and hard rules
- Softgirlnocode — HyperFrames setup and prompts
- Jason Cooperson — AI video editing setup guide
- Jakeschincariol/youtube-agent-skill (MIT) — 21 hook formulas, the
  5-property panel concept, EDL, retention and viral research
- Jakeschincariol/instagram-agent-skill (MIT) — 26 hook formulas, beat
  sheets, humanizer, caption linting

### License

- MIT — see [LICENSE](LICENSE).
