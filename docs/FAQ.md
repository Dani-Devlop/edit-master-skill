# FAQ

Short answers to the questions that come up most. Terminology follows
SKILL.md exactly; deeper detail lives in `docs/WORKFLOWS.md`,
`docs/HOOKS.md` and `docs/TOOLS.md`.

## Does it work with my agent

Yes — Claude Code, ChatGPT, Codex, Gemini CLI, Cursor, and any chatbot
with no filesystem at all. With a filesystem, install the skill and point
the agent at `SKILL.md` (`docs/INSTALLATION.md` has per-agent paths).
Without one, paste the entire `SKILL.md` at the top of the chat; it runs
as a mode. You keep the method, formulas, checklists and linting rules,
and lose the file-based tooling.

## Can I use my own brand colors and voice

Yes, and you should. Question 10 of the onboarding captures colors, fonts
and logo; `templates/voice.md` carries the voice: who you talk to, how you
actually talk, words you never use, words you do use, what you will not
claim, and your format block. Every phase reads it. Ten minutes there is
worth more than any prompt you will ever write.

## What if I do not have footage

Answer question 9 with "Need AI generation". The skill uses image and
video generators for B-roll and cold opens only, keeps claimed results
real, and labels generated footage when it could mislead. The plan (shot
list keyed to the beats) works the same way as for recorded footage; only
the source changes.

## How do I score hooks without the Python helper

Score by hand on the same five properties — SPECIFICITY, ADDRESS, STAKES,
CURIOSITY, BREVITY, each 0-100 — and show the weakest one. The verdict is
still 60% the mean + 40% the weakest property, bands still STRONG >= 72,
WORKABLE >= 55, WEAK < 55. See the worked numeric example in
`docs/WORKFLOWS.md`.

## Is it free for commercial use

Yes. The repository is MIT licensed — use it, change it, ship it, charge
for what you make with it. Keep the license file with any redistribution,
and keep the credits for the two MIT upstream repositories if you remix
the hook libraries.

## Why do commits sometimes show no Verified badge

The repository follows a strict badge policy: every commit on `main` shows
either the blue **Verified** badge or no signature badge at all — a yellow
*Unverified* badge is never accepted. When the maintainer's API token
lacks the `admin:gpg_key` scope, commits are intentionally left unsigned
(no badge) rather than signed-but-unverified. No badge means unsigned by
policy, not suspicious.

## How do I verify GPG signatures manually

```bash
gpg --import GPG-PUBLIC-KEY.asc
git verify-commit <commit-sha>
```

`GPG-PUBLIC-KEY.asc` sits at the repository root. If verification fails
because the key is not registered with the GitHub account yet, that is
expected under the badge policy above — commits stay unsigned rather than
unverified.

## Does the skill publish videos for me

No. Nothing publishes itself. Every run ends in a copy-ready block and the
delivery receipt, then the question: ship it, or change it? The skill
writes and QAs; you ship.

## Short form or long form — which first

Short form. The 15-45 second working range gives you fast feedback loops
on hooks, pacing and captions, and a hook that survives two seconds is
the same discipline long-form needs at fifteen. Move to long-form (5-30
min) once your hooks hold; the long-form beat sheet, re-hooks and the
0:30 cliff rules then apply.

## What is an outlier multiple

Views divided by that account's own recent median — the only ranking the
viral research method trusts. Above 3x is a signal. Below 1.5x is that
account's normal day and teaches you nothing, no matter how big the
number looks. For channels, require at least 4 videos per channel or the
median means nothing. Raw views are not evidence.

## How long should a hook card stay on screen

Cards run at most 3 seconds each, and the hook card is up at frame 1 —
not after the title, not after the intro sting. Captions carry most cards
word-synced; the hook card is the one on-screen line that fires together
with the spoken hook inside the 2-second short-form window.

## Safe zones for captions on 1080x1920

On a 1080x1920 frame, nothing above y=230 or below y=1440, and keep the
right 230 pixels clear — the platform interface covers everything outside
that box. Never put the hook where the caption sits. Cards are at most 2
lines, about 42 characters per line, with contrast at least 4.5:1 against
the footage.

## Can I change the 10 onboarding questions

Yes — they are a starting point, not scripture. Keep the three properties
that make them work: asked in one batched message, answered once into
`voice.md`, and always including the follow-up that pulls out one
specific true thing (what happened, to whom, what did it cost or return).
If you change them, update SKILL.md, `docs/WORKFLOWS.md` and the CI
structure assumptions in the same change.

## How does the humanizer pass work

Automatic fixes first: invisible characters (zero-width spaces, joiners,
BOMs), typography (em dash to comma, curly quotes to straight), and the
slop lexicon (delve, leverage, robust, seamless, game-changer and the
platform block). Structural tells — "not just X, it's Y", rule-of-three
triads, hashtag walls — are flagged, never auto-rewritten, because
rewriting shape needs judgement. Then the 5-check panel: BURSTINESS,
SPECIFICITY, SLOP DENSITY, FINGERPRINT, VOICE, each 0-100. Verdict =
60% mean + 40% weakest check; PASS = overall 70+ with no check below 55.
Two rounds is normal; five means the draft was written by formula and the
fix is a different draft. Never claim any text is undetectable.

## What caption rules are enforced

Declare the job first: Job A (the video already hooked them — the caption
is the ask, the context and the search words, not a second hook) or Job B
(the caption is the content — line one is the hook). Then the lint:
line 1 carries the roughly 125 characters visible before the "... more"
cut; never a greeting, hashtag, or emoji as the first character; short
paragraphs with one line of white space; one ask; up to five specific
hashtags on their own line or none; no link in the caption; keyword asks
people can actually type; no slop words or invisible characters.

## What about music licensing

Use music you can legally use, and record the source in `voice.md`
(genre, energy, library link, anything off-limits). One of the common
mistakes is chasing a trending audio the user cannot use — the skill
checks rights before the sound design gate, not after the upload.

## Does it replace an editor

No. It plans and QAs like a professional editor — research before
opinions, scored hooks, edit decision lists instead of vibes — and then a
human (or a renderer the human directs) applies the plan. For NLE work,
the skill hands over the EDL, beat sheet, caption file and shot list; the
editor keeps the taste and the final call.

## How do I run the 25-video test matrix

Follow `tests/README.md`: 25 videos across 16 categories, rendered to the
export spec (1080x1920, H.264 + AAC, 30 fps), scored 1-10 on six
dimensions with the overall as the average, honest reporting throughout —
never fabricate an edited video, name the real reason for any blocked
test, and retry alternative sources up to 3 attempts.

## Can I extend the hook library

Yes. A new formula needs four things before it counts: a shape, a written
example, an on-screen version (six words or fewer for short-form), and a
failure mode. Update the count text everywhere it appears (47 total =
21 long-form + 26 short-form), add the entry to `docs/HOOKS.md`, and see
CONTRIBUTING.md for the process.

## What render settings for TikTok, Reels and Shorts

1080x1920, H.264 High profile with `yuv420p`, CRF about 23, 30 fps, AAC
at 192 kbps, `+faststart`. The full command is in `docs/TOOLS.md`, and
the same spec is the export requirement of the test matrix.

## Why 165 wpm

Most people land between 150 and 200 words per minute, so the skill plans
at 165 until you have timed yourself — a safe middle that keeps beat
timings honest. That is 2.75 words per second: a 30-second script is
about 82 spoken words. Long-form runtime estimates use words / 150 =
minutes instead.

## What is the difference between EDL markdown and JSON

Same cuts, two audiences. The markdown table is for humans — every row
shows id, timecodes, action (KEEP / CUT-DEAD / CUT-FILLER / CUT-RETAKE /
BROLL / SPEED), visual, audio, on-screen text and the note saying why.
The JSON is for agents and render bridges — the same cuts as structured
`cuts` and `dead_air` arrays that a script can apply without parsing
prose. Both are produced from a real transcript; neither is hand-invented.

## How do I repurpose one long video into Shorts

A Short is a moment that survives without the video around it: it opens
on a complete thought, has a turn, and ends on a line. Pick moments that
way from the long video, then write a NEW first line for each Short and
score it — do not just clip the best moment.

## How do I contribute

Read CONTRIBUTING.md. Bugs go through the bug report template, feature
ideas start in GitHub Discussions, pull requests follow fork -> branch ->
PR -> review with Conventional Commits, and any SKILL.md edit keeps the
counts in sync: 47 hook formulas (21 + 26), 5 phases, 12 editing
principles, 16 QA points, 10 onboarding questions.
