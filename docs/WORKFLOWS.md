# Workflows — the 5-Phase Pipeline, Deep Dive

Edit Master always works in the same order: onboard (if not onboarded) ->
research -> hooks -> beat sheet / EDL -> render plan -> QA gate. This page
expands each of the five phases from SKILL.md: purpose, inputs, outputs, a
decision tree, one example output snippet, and the failure modes with
fixes. Reference sections at the bottom cover the onboarding questions,
the scoring math, the timing rules, the EDL structure and the QA gate.

---

## Phase 1 — ONBOARD

**Purpose.** Learn who is being edited for before any creative work: a
script in the wrong voice is worse than no script. Record the answers once
in `voice.md` and reuse them every session.

**Inputs.** The user's request; any existing `voice.md`; three or more of
the user's own videos if the file does not exist.

**Outputs.** Filled `voice.md`; one true specific for the video ("what
happened, to whom, and what did it cost or return").

**Decision tree:**

```
voice.md exists?
|-- yes --> read it; confirm at most three stale facts; go to Phase 2
`-- no  --> user has 3+ of their own videos?
            |-- yes --> infer the voice from those, write voice.md,
            |           have the user confirm
            `-- no  --> ask the 10 questions in ONE batched message
                        idea thin? --> one batched follow-up: what
                        happened, to whom, what did it cost or return
```

**Example output snippet** (batched onboarding message):

```
Before I touch anything: 10 questions, answer any you like.
1. Main platform?  2. Video type?  3. Target length?
4. Brand style?    5. Main goal?   6. Available tools?
7. Budget per video?  8. Delivery speed?
9. Footage source?    10. Brand assets?
And the one thing that matters most: what happened, to whom, and what did
it cost or return? One specific true thing is all a video needs.
```

**Failure modes and fixes:**

- *Asking the questions one at a time.* Fix: batch all 10 into one message;
  a slow onboarding is how creators disengage.
- *Accepting "make it go viral" as a brief.* Fix: the batched follow-up —
  one specific true thing, or no script. Never pad a thin idea.
- *Skipping voice.md because "I know the vibe".* Fix: infer it from three
  videos or refuse script work; the humanizer cannot rescue the wrong
  voice.

---

## Phase 2 — RESEARCH

**Purpose.** Find what is actually working before opining about it. Raw
views are not evidence; the outlier multiple is.

**Inputs.** The niche; the user's own Saved collection (the fastest
relevant corpus that exists); public listings only.

**Outputs.** A swipe file (refresh monthly, not daily — formulas last a
season); top five items with multiples and formulas; the ONE structural
thing they share; the harder line — which of those the user could actually
make this week, in their voice, with what they have.

**Decision tree:**

```
User wants "what's working"?
|-- yes --> build/refresh the swipe file (monthly, not daily)
|           |-- account mix: 4 direct + 4 adjacent + 2-4 outsized
|           |   (collect within ~10x of the user's own size)
|           |-- rank on outlier multiple = views / account's own median
|           |-- channels: >= 4 videos each, or the median means nothing
|           `-- capture per item: handle, followers, median, views,
|               hook verbatim, first on-screen card, formula, length,
|               structural pattern of cuts
|-- no  --> check what the user's own audience already rewarded
`-- never: scraping, logging into accounts, background loops
```

**Example output snippet** (swipe-file row, capture fields):

```
handle: @atelierforms        followers: 3,900
median (last 12): 8,400      this video: 96,000     multiple: 11.4x  SIGNAL
hook verbatim: "Nobody tells you that your first 30 reels are supposed
to flop."
first card: YOUR FIRST 30 WILL FLOP       formula: #3 Nobody Tells You
length: 24s   cuts: hard cut every ~2.2s, text card at every cut
```

**Failure modes and fixes:**

- *Ranking by raw views.* Fix: rank on the outlier multiple — above 3x is a
  signal, below 1.5x is that account's normal day and teaches nothing.
- *Scraping.* Fix: read, do not scrape — public listings only, human speed,
  no crawlers, no scraping services, never log into anyone's account.
- *Copy-paste a video because it worked.* Fix: copy the formula, never the
  video — the hook shape, the structure, the length, the pattern of cuts.
  Attribute every row.

---

## Phase 3 — HOOK + SCRIPT

**Purpose.** Score hooks before anyone wastes a take, then write a script
in the creator's actual voice with something on screen at every beat.

**Inputs.** The one true specific from Phase 1; `voice.md`; the swipe file
if Phase 2 ran.

**Outputs.** Three hook options (short-form) or five (long-form), scored on
the 5-property panel, top two shown with scores and the winning formula
name; a script in plain spoken language with every beat marked ON SCREEN.

**Decision tree:**

```
Short-form or long-form?
|-- short-form (Reels/TikTok/Shorts)
|           |-- hook = first 2 seconds; spoken + on-screen written
|           |   separately; on-screen six words or fewer
|           `-- write 3 formulas that genuinely fit (never 3 rewrites
|               of one)
|-- long-form (YouTube)
|           |-- hook = first 15 seconds; confirm the title, open a
|           |   question, prove the payoff exists
|           `-- write 5 formulas
`-- score all on the 5-property panel (verdict = 60% mean + 40% weakest)
    |-- top hook under 50? --> no hook yet; back to the idea
    `-- keep the top two, show both --> script it, humanize it
```

**Example output snippet** (scored panel row):

```
#5 Time Collapse  "Proposals used to take me five hours. Twenty minutes
now."  |  on screen: 5 HOURS -> 20 MIN
S 88  A 71  St 58  C 64  B 100  |  mean 76.2, weakest STAKES 58
verdict = 0.6 x 76.2 + 0.4 x 58 = 73.0 -> 73 STRONG (weakest: STAKES)
```

**Failure modes and fixes:**

- *Three rewrites of one formula.* Fix: three genuinely different
  formulas; a panel of near-identical hooks is one hook wearing wigs.
- *Averaging the panel so the dead property hides.* Fix: the verdict is 40%
  the weakest property precisely because a hook with one dead property
  leaks at that property.
- *A hook that would work for anyone else in the niche.* Fix: it is not
  your hook; put the thing only the creator can say in it.

---

## Phase 4 — EDIT PLAN

**Purpose.** Turn script + footage into cuts someone (or some agent) can
apply: timed beats, an EDL with real timecodes, captions that pass lint.

**Inputs.** The approved script; the raw footage; a real transcript
(whisper or the platform's own caption track) whenever footage exists.

**Outputs.** Beat sheet (timings at the creator's wpm, every flag fixed);
EDL in markdown + JSON; caption file (SRT) linted Job A or Job B;
humanizer PASS on script and caption.

**Decision tree:**

```
Footage exists?
|-- yes --> transcript --> build the EDL from it
|           |-- CUT-DEAD: gaps over the floor (default 0.35s), trimmed
|           |   from the middle, breath kept both sides
|           |-- CUT-FILLER: "um", "so yeah", "basically"
|           |-- CUT-RETAKE: restarted sentences, keep the good take
|           |-- BROLL slots: what is ON SCREEN at each beat
|           `-- report the cut percentage of SPEECH, and warn when a long
|               silent demo makes that number misleading
|-- no  --> shot list keyed to the beats (AI generation covers B-roll and
|           cold opens only; label generated footage that could mislead)
`-- either way --> beat sheet flags: hook past 3s? beat over 4s? run of
    beats with nothing concrete? no loop? --> fix every flag, then
    humanizer pass, then caption lint (Job A or B)
```

**Example output snippet** (short-form beat sheet head):

```
0:00-0:02   HOOK     the claim. Spoken line and on-screen line written
                     separately. Motion in the first frame, not a static face.
0:02-0:07   STAKE    why this matters to the person watching. One line.
0:07-...    BODY     one idea per beat, and the frame changes every beat.
```

**Failure modes and fixes:**

- *Guessed timecodes.* Fix: transcript or nothing — a guessed cut is a
  double cut nobody can apply.
- *Cutting flush against speech.* Fix: trim silences so both sides keep a
  breath; a tightened take that sounds gasping reads as an error.
- *Captions outside the safe zones.* Fix: on a 1080x1920 frame nothing
  above y=230 or below y=1440, right 230 px clear; re-position before
  render, not after.

---

## Phase 5 — RENDER + QA

**Purpose.** Produce the deliverable through whatever tool the agent can
actually run, then run the 16-point QA gate gate by gate before anything
is called done.

**Inputs.** The EDL, caption file, music, and a renderer (ffmpeg,
Remotion, HyperFrames, FilmCraft, or an NLE by hand — see
`docs/TOOLS.md`).

**Outputs.** The render at delivery spec; the completed QA checklist; the
copy-ready block and delivery receipt ending in "ship it, or change it?".

**Decision tree:**

```
Pick the renderer by what can actually run:
|-- zero budget, CLI only      --> ffmpeg
|-- graphics-heavy, repeatable --> Remotion
|-- HTML/CSS frames            --> HyperFrames
|-- full NLE quality/grade     --> FilmCraft, or Premiere/DaVinci via a
|                                  bridge, CapCut for phone-first edits
`-- render --> run the QA gate, gate by gate
    |-- any FAIL --> not shipped; fix and re-run the gate
    `-- all pass --> copy-ready block + delivery receipt
                     --> "ship it, or change it?" (nothing publishes itself)
```

**Example output snippet** (delivery receipt):

```
EDIT READY
hook:       #10 If This, Then Watch, scored 76 STRONG (weakest: CURIOSITY 70)
length:     30.0s across 11 beats at 165 wpm
on-screen:  11 cards, all inside safe zones
humanizer:  3 artefacts stripped, human score 78 PASS
caption:    Job A, 53/125 visible chars, one ask, 3 hashtags
edl:        11 cuts, 3.45s of source removed, breath kept
audio:      music -14 LUFS mix, SFX on 4 beats
render:     1080x1920 30fps, fade out at 30.0s

Ship it, or change it?
```

**Failure modes and fixes:**

- *Shipping with one FAIL because the mean looks fine.* Fix: any FAIL = not
  shipped; the gate is a gate, not a scorecard.
- *Publishing for the user.* Fix: the skill never publishes anything; it
  hands back a copy-ready block and asks the question.
- *Chasing a trending audio the user cannot use.* Fix: check rights before
  the sound design gate; record the music source in `voice.md`.

---

## Reference: the 10 onboarding questions

Asked in one batched message before any creative work; answers recorded in
`voice.md` and reused every session.

1. **Main platform?** Instagram / YouTube / TikTok / LinkedIn / Other
2. **Video type?** Talking head / Podcast / Educational / Entertainment /
   Vlog / Product
3. **Target length?** Under 60s / 1-3 min / 5-10 min / 10min+
4. **Brand style?** Minimal / Cinematic / Energetic / Corporate / Playful /
   Luxury
5. **Main goal?** Save time / Increase quality / Make money / Grow
   audience / Client work
6. **Available tools?** Claude / ChatGPT / Higgsfield / Premiere / DaVinci
   / After Effects / CapCut
7. **Budget per video?** Free / Under $5 / Under $25 / Under $50 /
   Unlimited
8. **Delivery speed?** 1 hour / Same day / 1-2 days / No rush
9. **Footage source?** Already recorded / Need AI generation / Mix
10. **Brand assets?** Colors / Fonts / Logo / Voice.md / None

## Reference: 5-property scoring math

Five properties, 0-100 each: SPECIFICITY (numbers, names, dates; penalty
for vague words), ADDRESS ("you", ideally in the first six words), STAKES
(what it costs the viewer to keep going the current way), CURIOSITY (an
open gap; penalty if the sentence answers itself), BREVITY (9-24 words is
the band a spoken hook lands in inside 10 seconds).

**The verdict is 60% the mean + 40% the weakest property** — because a
hook with four strong properties and one dead one leaks at the dead one,
and averaging hides that.

Worked example:

```
SPECIFICITY 84   ADDRESS 70   STAKES 58   CURIOSITY 72   BREVITY 100

mean    = (84 + 70 + 58 + 72 + 100) / 5 = 384 / 5 = 76.8
weakest = STAKES at 58
verdict = 0.6 x 76.8 + 0.4 x 58 = 46.08 + 23.2 = 69.28 -> 69 = WORKABLE
```

A naive read of the mean (76.8) says healthy. The verdict says WORKABLE:
STAKES 58 is the leak. The fix for a low STAKES score is to name the cost —
losing, wasting, quitting, failing — and re-score before shooting.

Bands: **STRONG >= 72, WORKABLE >= 55, WEAK < 55**. Short-form scoring adds
the on-screen hook (six words or fewer, inside the safe zone, up at frame
1) and requires overall >= 70 with no property below 55 for STRONG. If the
top hook scores under 50, there is no hook yet; no amount of editing fixes
that. Honest limits apply: the panels separate deliberately bad hooks from
real ones well, and separate a creator's own hits from their own misses
barely at all.

## Reference: beat sheet timing rules

- Plan at **165 wpm** until the creator has timed themselves; most people
  land 150-200. 165 wpm = 2.75 words per second, so a 30-second script is
  about 82 spoken words.
- Long-form runtime estimate: words / 150 = minutes of spoken video.
- Short-form flags to fix before render: a hook past 3 seconds, any beat
  over 4 seconds, a run of beats with nothing concrete, and no loop.
- Short-form structure: HOOK 0:00-0:02, STAKE 0:02-0:07, BODY 0:07 onward
  (one idea per beat, frame changes every beat), PAYOFF in the last 3s,
  LOOP on the last line echoing one word from the hook. Under 7 seconds
  nothing but loop counts inflate; 15-45 seconds is the honest working
  range.
- Long-form structure: HOOK 0:00-0:15, TURN 0:15-0:45 (no channel intro,
  no "before we get started" — that is the 0:30 cliff), BODY beats each
  marked with what is ON SCREEN, RE-HOOK every ~60-90s, PAYOFF delivered
  explicitly, CLOSE with one ask. Not three.

## Reference: EDL structure

An EDL turns a transcript + footage into cuts someone can apply. Produced
as markdown (human) and JSON (agent), always with timecodes from a real
transcript — never guessed.

| field | meaning |
|-------|---------|
| id | beat/clip id, e.g. B03 |
| tc_in / tc_out | source timecodes (HH:MM:SS.mmm) |
| action | KEEP / CUT-DEAD / CUT-FILLER / CUT-RETAKE / BROLL / SPEED |
| duration | tc_out - tc_in |
| visual | what is on screen (shot, zoom, graphic, text card) |
| audio | VO / music / SFX note |
| on_screen | caption card or overlay text, six words max |
| note | why (for CUT rows: what it was) |

JSON shape:

```json
{"project": "...", "wpm": 165, "target_s": 30,
 "cuts": [{"id":"B01","tc_in":"00:00:00.000","tc_out":"00:00:02.400",
           "action":"KEEP","visual":"mid-action cold open","audio":"music in",
           "on_screen":"5 HOURS -> 20 MIN","note":"hook, formula #5"}],
 "dead_air": [{"tc_in":"00:00:41.200","tc_out":"00:00:43.900",
               "note":"gap 2.7s, trim from middle, keep breath both sides"}]}
```

Report language for transcript passes: **DEAD** (gap over the floor —
default 0.35s — trimmed from the middle), **FILLER** (cues that are nothing
but "um", "so yeah", "basically"), **REPEAT** (a sentence restarted,
compared against the last cue that was actually speech). State the cut
percentage of SPEECH and warn that a long silent demo makes that number
misleading against total runtime.

## Reference: the 16-point QA gate

Run every edit through all gates before delivery. Any FAIL = not shipped.

1. Hook: motion + on-screen text at frame 1; spoken hook inside the window
2. Hook scored on the 5-property panel; weakest property named
3. Promise delivered before the halfway mark; payoff shown then explained
4. One idea; one ask; no second CTA
5. Frame changes every beat; no static shot over the pacing budget
6. Dead air, filler and retakes cut; breath kept on both sides of cuts
7. Captions burned in, word-synced, inside safe zones, readable contrast
8. On-screen cards six words or fewer; hook card at frame 1
9. Sound: music matches claimed energy; SFX on changes; VO intelligible
10. Color consistent across cuts; skin tones matched; brand look applied
11. Numbers on screen match numbers spoken; nothing invented
12. Humanizer PASS (overall 70+, no check below 55) on script + caption
13. Caption lint clean (Job A/B declared, one ask, <= 5 hashtags, no link)
14. Loop: last line sets up the first line (short-form)
15. Aspect + safe zones correct for target platform
16. Delivery receipt printed; "ship it, or change it?" asked
