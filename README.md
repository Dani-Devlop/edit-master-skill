[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/Dani-Devlop/edit-master-skill)](https://github.com/Dani-Devlop/edit-master-skill/releases)
[![GitHub stars](https://img.shields.io/github/stars/Dani-Devlop/edit-master-skill?style=social)](https://github.com/Dani-Devlop/edit-master-skill)
[![GitHub forks](https://img.shields.io/github/forks/Dani-Devlop/edit-master-skill?style=social)](https://github.com/Dani-Devlop/edit-master-skill)
[![GitHub commits](https://img.shields.io/github/commit-activity/m/Dani-Devlop/edit-master-skill)](https://github.com/Dani-Devlop/edit-master-skill/commits)
[![Last commit](https://img.shields.io/github/last-commit/Dani-Devlop/edit-master-skill)](https://github.com/Dani-Devlop/edit-master-skill)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Dani-Devlop/edit-master-skill/pulls)

# Edit Master Skill

**Universal viral video editing skill for any AI agent** — Claude, ChatGPT,
Codex, Gemini CLI, Cursor, or a plain chat window. Short-form vertical AND
long-form horizontal. Free and open source, MIT licensed.

Give it raw footage or a raw idea and it runs the whole pipeline: a 10-question
onboarding, hook options from **21 long-form + 26 short-form formulas** scored
on a **5-property panel**, beat sheets, **edit decision lists**, a **humanizer
pass**, **caption linting**, **viral research by outlier multiple**,
**retention analysis**, and a QA gate that ends every run with the same
question: *ship it, or change it?*

Nothing publishes itself. The skill writes, you ship.

## What's inside

| File | What it is |
|------|------------|
| `SKILL.md` | The complete skill: onboarding, 47 hook formulas, scoring, beat sheets, EDL, humanizer, 12 editing principles, 5-phase workflow, caption linting, viral research, retention, tool integrations, QA checklist, testing protocol |
| `templates/voice.md` | Brand voice template — fill it in once, every phase reads it |
| `examples/` | Three worked examples: onboarding + edit plan, an EDL, a caption file |

## Install

**Claude Code / Codex / Cursor / Gemini CLI:**

```bash
git clone https://github.com/Dani-Devlop/edit-master-skill.git
cp -r edit-master-skill ~/.claude/skills/edit-master   # path varies by agent
```

**Any chatbot with no filesystem:** paste the entire `SKILL.md` at the top of
the chat. It runs as a mode — you keep the method, formulas, checklists and
linting rules without the file-based tooling.

**Then:** spend ten minutes on `templates/voice.md`, or send the agent three
of your own videos and say *"write my voice.md from these"*.

## Quick start

Paste one of these into your agent:

```
Edit this raw talking-head recording into a 30-second vertical reel in a
minimal style. Read my voice.md first. Five scored hooks, beat sheet, EDL,
burned captions, QA checklist.
```

```
Find what's working in my niche this month: 4 direct, 4 adjacent, 2 outsized
accounts, ranked by outlier multiple, with the hook formula each used.
```

## The 10 onboarding questions

1. Main platform? 2. Video type? 3. Target length? 4. Brand style? 5. Main
goal? 6. Available tools? 7. Budget per video? 8. Delivery speed? 9. Footage
source? 10. Brand assets?

(Full definitions in SKILL.md → User Onboarding Questions.)

## Features

- **Agent-agnostic** — one markdown file, no dependencies, no API keys
- **47 hook formulas** (21 long-form + 26 short-form), each with shape,
  example, on-screen version and failure mode
- **5-property hook scoring** — SPECIFICITY / ADDRESS / STAKES / CURIOSITY /
  BREVITY, verdict = 60% mean + 40% weakest property
- **Beat sheets** for both formats with timing rules (165 wpm default)
- **EDL structure** — dead air, filler, retakes with timecodes; markdown +
  JSON output
- **Humanizer pass** — invisible characters, typography, slop lexicon,
  structural tells, 5-check detection panel
- **Caption linting** — Job A/B, 125-visible-character rule, one ask,
  hashtag cap, search-term placement
- **Viral research** — outlier multiple ranking (views / account's own median)
- **Retention analysis** — hook leak / cliffs / slide, one fix per report
- **Tool integrations** — ffmpeg, Remotion, HyperFrames, Premiere, DaVinci,
  CapCut; transcripts via whisper
- **QA gate** — 16-point checklist before anything ships

## Credits

Synthesized and adapted with thanks to:

- **Joseph | Video Editing** — minimal talking-head / premium reel Claude editing workflows
- **Dan Kieft** — AI video editing course workflows
- **Grow with Alex** — Claude video editing fundamentals and hard rules
- **Softgirlnocode** — HyperFrames setup and prompts
- **Jason Cooperson** — AI video editing setup guide
- [Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (MIT) — 21 hook formulas, 5-property hook panel, EDL, retention and viral research concepts
- [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill) (MIT) — 26 hook formulas, beat sheets, humanizer, caption linting

Hook libraries and the scoring-panel concept are adapted from the two
MIT-licensed repositories above; the onboarding, workflow, editing principles
and checklists are original to this skill.

## Commit signing & verification

This repository follows a strict badge policy: every commit on `main`
shows **either** the blue **Verified** badge **or no signature badge at
all** — a yellow *Unverified* badge is never accepted.

The maintainer's ed25519 signing key is published at
[`GPG-PUBLIC-KEY.asc`](GPG-PUBLIC-KEY.asc). Registering it with the GitHub
account requires an API token with the `admin:gpg_key` scope; when that
scope is unavailable, commits are intentionally left unsigned (no badge)
rather than signed-but-unverified. If you maintain the account, you can
complete registration in **Settings → SSH and GPG keys → New GPG key**
(paste the contents of `GPG-PUBLIC-KEY.asc`); future commits can then be
verified by anyone with:

```bash
gpg --import GPG-PUBLIC-KEY.asc
git verify-commit <commit-sha>
```

## License

MIT — see [LICENSE](LICENSE). Use it, change it, ship it.
