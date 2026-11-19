# Installation

Edit Master is a skill, not an app: one markdown file (`SKILL.md`) that any
AI agent can run as an operating procedure. Pick the install path for your
agent below, then spend ten minutes on `templates/voice.md`.

Repository:
https://github.com/Dani-Devlop/edit-master-skill

## What you need

- Any of: Claude Code, Codex, Cursor, Gemini CLI — or any chatbot with no
  filesystem at all.
- A Rust-free, dependency-free setup: the skill itself has none.
- Optional: `ffmpeg` on PATH if you want the agent to actually render, not
  just plan (see `docs/TOOLS.md`).

## Claude Code

```bash
git clone https://github.com/Dani-Devlop/edit-master-skill.git
cp -r edit-master-skill ~/.claude/skills/edit-master
```

Verify it loaded: run `/skills` inside Claude Code, or just ask the agent
"Do you have the edit-master skill? State its identity line." It should
answer from the Identity & Mission section of `SKILL.md`. Project-scoped
alternative: copy the folder to `.claude/skills/edit-master/` inside a
single project instead of `~/.claude/skills/`.

## Codex

Codex reads instructions from `AGENTS.md`. Point it at the skill folder as
a working set:

1. Clone the repo somewhere stable, for example `~/skills/edit-master`:

```bash
git clone https://github.com/Dani-Devlop/edit-master-skill.git ~/skills/edit-master
```

2. Add a pointer to your `AGENTS.md` (repo-level, or
   `~/.codex/AGENTS.md` for global):

```markdown
For any video editing, scripting, repurposing, research or QA request,
first read ~/skills/edit-master/SKILL.md and follow it exactly.
```

3. Run codex from your project; when a video task appears it reads
   `SKILL.md` first. Verify by asking it to state the 5-phase workflow.

## Cursor

Two options:

- **Rules file (recommended):** create `.cursor/rules/edit-master.mdc` in
  your project (or use Settings, Rules for AI) containing:

```markdown
---
description: Edit Master video editing skill
alwaysApply: false
---
When the user asks to edit, script, repurpose, research or QA a video,
read ~/.claude/skills/edit-master/SKILL.md (adjust the path to where you
cloned it) and follow it as the operating procedure.
```

- **@-mention in chat:** type `@SKILL.md` and ask the agent to run it as
  its operating procedure for the session.

## Gemini CLI

Gemini CLI reads context from `GEMINI.md`. Create a `GEMINI.md` in your
project root (or append to an existing one):

```markdown
## Video editing mode

When the user asks for video editing, scripting, repurposing, research or
QA work, read ~/.claude/skills/edit-master/SKILL.md and follow it as the
operating procedure. Load it as system instruction context if the request
is entirely video work.
```

Verify by asking the agent to state the 5-phase workflow and the hook
count (47: 21 long-form + 26 short-form).

## Chat-only mode (any chatbot, no filesystem)

Paste the **entire** `SKILL.md` at the top of the chat, then paste your
footage transcript or idea. It runs as a mode: you keep the method, the
formulas, the checklists and the linting rules, and you lose the file-based
tooling. Practical limits:

- The agent cannot read your video files, transcribe audio, or write
  files. You paste transcripts in and copy outputs back out.
- Timecodes must come from a transcript you paste. Never accept guessed
  timecodes (SKILL.md rule).
- One video per chat keeps the context clean; a fresh chat needs the
  SKILL.md and your voice summary pasted again.

## templates/voice.md — do this next

Every phase reads the brand voice file; a script in the wrong voice is
worse than no script.

1. Copy the template:
   `cp templates/voice.md ~/.claude/edit-master/voice.md` (any stable
   location works — tell the skill where it lives).
2. Fill in the sections, deleting the guidance lines as you go: who you
   talk to, how you actually talk, words you never use, words you do use,
   what you will not claim, and your format block.
3. No transcript to paste? Send the agent three of your own videos and say
   "write my voice.md from these" — the skill infers the voice, writes the
   file, and you confirm.

## Troubleshooting

### The agent does not pick up the skill

Each agent looks in exactly one place:

| Agent | Where it looks | Fix |
|-------|----------------|-----|
| Claude Code | `~/.claude/skills/edit-master/SKILL.md` | Re-run the `cp -r`; restart the session; check with `/skills` |
| Codex | `AGENTS.md` pointer, reachable from the working directory | Confirm the path in the pointer is absolute or correct relative to where codex runs |
| Cursor | `.cursor/rules/` rules file | Confirm the file extension is `.mdc` and the rule is enabled |
| Gemini CLI | `GEMINI.md` in the project root | Confirm the file is in the directory where you launched `gemini` |
| Chat-only | The pasted text at the top of the chat | Paste the whole SKILL.md again; it must be complete, not a summary |

Then test with: "read your skill and state the 5-phase workflow and the
hook count." If it cannot, the file is not where that agent looks.

### Chat-only mode limits

No filesystem means no transcription, no EDL files, no SRT writes. The
workaround is paste-in, copy-out, one video per chat. For full tooling,
install under an agent with file access.

### Updating

```bash
cd edit-master-skill
git pull
cp -r . ~/.claude/skills/edit-master   # or re-point your agent's rule
```

Chat-only users: re-paste `SKILL.md` from the latest `main` when it
changes.

### GPG-PUBLIC-KEY.asc and the badge policy

`GPG-PUBLIC-KEY.asc` at the repository root is the maintainer's public
signing key. This repository follows a strict badge policy: every commit on
`main` shows either the blue **Verified** badge or **no signature badge at
all** — a yellow *Unverified* badge is never accepted. Commits that carry
no badge are intentionally unsigned, not suspicious.

Verify a commit manually:

```bash
gpg --import GPG-PUBLIC-KEY.asc
git verify-commit <commit-sha>
```

### License and remix notes

The skill is MIT licensed (see [LICENSE](../LICENSE)). Fork it, rename it,
ship your own variant. Keep the license file, and if you remix the hook
libraries, keep the attribution to the two MIT upstream repositories listed
in the README Credits section.
