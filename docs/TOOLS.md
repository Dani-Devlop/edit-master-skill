# Tool Integrations

Edit Master is renderer-agnostic: markdown in, plan out, any tool renders.
The skill writes beat sheets, EDLs, caption files and shot lists; whatever
the agent can actually run produces the pixels. Every integration below is
a starting point, not gospel — read the tool's current docs before relying
on a command.

What the skill hands to a renderer:

- beat sheet (markdown, timed at the creator's wpm)
- EDL (markdown table for humans, JSON for agents — same cuts)
- captions (SRT, word-synced, from a real transcript)
- shot list (markdown) and the hook card text (six words or fewer)

---

## ffmpeg (always available, zero budget)

### Center crop a 16:9 master to 9:16

```bash
ffmpeg -i master.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" vertical.mp4
```

`crop=ih*9/16:ih` keeps the full height and takes a width of nine
sixteenths of it (the filter centers the crop by default), then
`scale=1080:1920` lands the delivery frame. Only safe when the subject
sits mid-frame in the master — check a still first, because the QA gate
item "aspect + safe zones correct" applies to the crop, not just the
export.

### Blurred-fill vertical (keep the whole frame, no lost sides)

```bash
ffmpeg -i master.mp4 -filter_complex \
"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];\
[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];\
[bg][fg]overlay=(W-w)/2:(H-h)/2" \
-c:v libx264 -crf 23 -preset medium -c:a aac -b:a 192k vertical_fill.mp4
```

The background layer scales the master to cover 1080x1920 and blurs it;
the foreground scales to fit and is centered on top. Nothing important is
cropped away, and the blurred plate stays behind the caption block.

### Hook card with drawtext

```bash
ffmpeg -i cut.mp4 -vf \
"drawtext=text='5 HOURS -> 20 MIN':fontfile=Inter-Bold.ttf:fontsize=96:\
fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=24:\
x=(w-text_w)/2:y=1180:enable='between(t,0,3)'" \
hook_card.mp4
```

- `enable='between(t,0,3)'` holds the card for the first three seconds —
  the short-form hook window.
- `box=1` with `boxcolor=black@0.6` and `boxborderw=24` draws the backing
  plate so the card stays readable over moving footage.
- `y=1180` puts the card inside the safe zone (on a 1080x1920 frame
  nothing above y=230 or below y=1440); `x=(w-text_w)/2` centers it and
  keeps the right 230 pixels clear.

### Burn in word-synced captions (SRT)

```bash
ffmpeg -i cut.mp4 \
-vf "subtitles=captions.srt:force_style='FontName=Inter,FontSize=16,Bold=1,MarginV=60'" \
captioned.mp4
```

The `subtitles` filter burns the SRT into the picture; `force_style`
overrides libass styling — `FontName`, `Bold`, and `MarginV` lifting the
block off the bottom edge so it stays inside the safe zone. Note that
`FontSize` here is libass script size, not pixels; tune it on a still
frame. The SRT itself must be word-synced from a real transcript, cards
of two lines and about 42 characters maximum, never covering the
speaker's mouth.

### Mix music under the voice, with loudness targets

```bash
ffmpeg -i cut.mp4 -i music.mp3 -filter_complex \
"[1:a]volume=0.35[m];\
[0:a][m]sidechaincompress=threshold=0.05:ratio=6:attack=25:release=350[duck];\
[0:a][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k mixed.mp4
```

- `sidechaincompress` dips the music while the voice speaks; the voice
  channel itself is never ducked (the skill's rule: VO ducked under
  nothing).
- `volume=0.5` is about -6 dB — the skill's ducking increment. Start near
  it and set by ear so the VO stays intelligible over music peaks.
- `loudnorm=I=-14:TP=-1.5:LRA=11` lands the master at -14 LUFS with a
  -1.5 dBTP true peak — the target behind the receipt line "music -14
  LUFS mix".
- `amix ... normalize=0` stops the mixer from re-scaling both inputs.

For a static bed with no sidechain, replace the sidechain chain with
`[1:a]volume=0.25[m];[0:a][m]amix=inputs=2:duration=first:normalize=0, loudnorm=...`.

### Fade the loop point (short-form)

```bash
ffmpeg -i body.mp4 -vf "fade=t=in:st=0:d=0.2,fade=t=out:st=27.8:d=0.2" loop.mp4
```

A 0.2 second fade in and out; the out point matches the loop target from
the beat sheet so the last line hands cleanly back to the first.

### Delivery export spec

```bash
ffmpeg -i final.mov -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 23 \
-preset medium -r 30 -vf scale=1080:1920 \
-c:a aac -b:a 192k -ar 48000 -movflags +faststart delivery.mp4
```

The spec the QA gate checks under "aspect + safe zones correct for target
platform": 1080x1920, H.264 High profile, `yuv420p` for player
compatibility, CRF about 23 as the quality/size balance, 30 fps, AAC at
192 kbps, and `+faststart` so playback starts before the download
finishes. TikTok, Reels and Shorts all accept this profile unchanged.

---

## Remotion (React-rendered motion graphics)

What it is: a renderer where every frame is a React component. Text,
charts and animations are code, so an edit becomes parameterized and
repeatable — change the JSON, re-render.

Install and agent use (per SKILL.md):

```bash
npx skills add remotion-dev/skills
```

The agent builds a small Remotion project, feeds it the EDL, caption
cues and hook card text as data, and renders the mp4. Best for the
"Claude builds the entire edit" style of minimal talking-head reels:
kinetic text, programmatic captions, charts, line animations — the
graphic-heavy work that is tedious by hand and trivial in code.

When to reach for it: the edit is graphics-driven and you expect to
re-render variants (different numbers, localized cards, A/B hook cards).
When to skip it: one-off b-roll-heavy cuts — ffmpeg is faster than a
build pipeline there.

---

## HyperFrames (HeyGen; agent-driven video)

What it is: HTML/CSS-driven frames rendered to video. Frames are styled
with the same primitives as a web page, so captions and hook cards are
just positioned divs — safe zones become CSS bounds. Setup concept per
Softgirlnocode: the agent composes frames, previews, renders.

Install and agent workflow (per SKILL.md):

```bash
npx skills add heygen-com/hyperframes
npx hyperframes preview
npx hyperframes render --output video.mp4
```

Works from the Studio app or from coding agents. Prompt pattern (SKILL.md):
the goal, who it is for, two to four specifics, and the exact words in
quotes — the quoted words become the on-screen text verbatim.

When to reach for it: agent-driven renders where the whole edit is
composed as styled frames — hook cards, step cards, kinetic captions.

---

## FilmCraft / ArtCraft

FilmCraft (from the ArtCraft team) is an open-source video editor built
agent-first. Its core invariant is "everything is a command": every
operation in the UI has a command id with typed JSON parameters, and UI,
CLI, the control channel and MCP all dispatch by that id. Every widget
registers an automation id and UI state is serializable, so an agent can
read and set anything a human can touch.

Install and launch (needs a Rust toolchain; clone the FilmCraft
repository and build, then):

```bash
cargo run -p filmcraft -- --control 9876
```

`--control 9876` opens the desktop app with the control channel on port
9876; the repo's `docs/control-protocol.md` defines the wire protocol, and
the command catalog (every command's id, label, shortcut and JSON
parameters) is the API surface an agent scripts against.

### JSONL-style scripting

Each scripted step is one command: an id plus a JSON parameter object, in
the catalog's schema. A cut-and-export pass for this skill's pipeline
looks like:

```json
{"id":"file.newSequence","params":{"name":"reel-30s","width":1080,"height":1920,"fps":30}}
{"id":"file.import","params":{"paths":["raw/talkinghead_1.mp4"]}}
{"id":"timeline.place","params":{"item":"talkinghead_1","track":"V1","seconds":0.0}}
{"id":"sequence.transcribe","params":{"track":"mix","language":"en"}}
{"id":"clip.speedDuration","params":{"clips":["talkinghead_1"],"speed":105,"maintainPitch":true}}
{"id":"file.exportMedia","params":{"path":"out/reel.mp4","format":"h264","width":1080,"height":1920,"fps":30,"crf":23,"loudnessLufs":-14,"captionSidecar":"srt"}}
{"id":"file.exportEdl","params":{"path":"edl/reel.edl"}}
```

Commands from the catalog that map directly onto this skill's outputs:

- `file.import`, `file.newSequence` — project setup at delivery geometry
- `timeline.place`, `timeline.move` — place clips; move plans carry each
  clip identity once
- `clip.speedDuration` — SPEED rows from the EDL (speed percent, pitch
  maintained)
- `sequence.addEdit` — razor cuts at tick-accurate positions
- `sequence.transcribe` — a real transcript from the mix (language
  `en|auto`), which is what the EDL's timecode rule demands
- `file.exportMedia` — delivery render: `format: h264`, `crf`, explicit
  `width`/`height`/`fps`, `loudnessLufs: -14`, `burnCaptions`, and a
  `captionSidecar` of `srt` or `vtt`
- `file.exportEdl`, `file.exportFcpxml`, `file.exportOtio`,
  `file.exportAaf` — interchange out to other NLEs

House rules an agent must respect when driving FilmCraft: it never
crashes on bad input (errors come back as actionable failures, not
panics), every input-derived number is hostile, assets need licenses and
attribution, no Adobe artwork anywhere, `main` changes through pull
requests, and an agent reports only what it actually ran.

---

## NLE bridges (Premiere, DaVinci Resolve, CapCut)

The pattern everywhere: the skill writes the plan, the bridge applies it,
the human reviews the timeline. The skill outputs the EDL, beat sheet,
caption file and shot list; the NLE does the pixels; nothing publishes
itself.

- **Premiere Pro MCP.** Premiere exposes an MCP bridge that makes its
  tools callable by coding agents. Agent flow: translate the EDL JSON
  into tool calls (import media, build the sequence, place cuts, add
  caption tracks), then hand the timeline to the human for review and
  export. Timecodes come from the transcript, never guessed.
- **DaVinci Resolve (MCP over its scripting API).** Same pattern: a
  bridge wraps Resolve's scripting interface, the agent drives the
  timeline and the grade, and the human checks skin-tone matching and the
  brand look (editing principle 11: grade for consistency, not for
  beauty).
- **CapCut drafts.** Some skills generate CapCut draft projects directly;
  the creator opens the draft and tweaks by hand. The natural fit when
  the creator edits on a phone or wants final say on captions.

---

## Transcription

Timecodes always come from a real transcript. Never guess at timings.

**whisper (local CLI, free):**

```bash
whisper raw.mp4 --model medium --output_format srt --output_dir transcripts/
```

Good enough for EDLs and caption drafts; verify proper nouns and numbers
against the audio before they reach a card.

**faster-whisper (local, same models, faster and lighter):**

```python
from faster_whisper import WhisperModel

model = WhisperModel("medium")
segments, info = model.transcribe("raw.mp4", word_timestamps=True)
for segment in segments:
    print(f"{segment.start:.3f} {segment.end:.3f} {segment.text}")
```

`word_timestamps=True` gives the per-word timing that burned,
word-synced captions need.

**ElevenLabs Scribe (hosted):** the option when there is no local GPU.
Send the audio to the hosted transcription API and take back timestamped
text; check the current API docs for limits and pricing. Same rule
applies — real timecodes only.

**Fallback (per SKILL.md):** the platform's own caption track on an
unlisted upload.

---

## Picking a renderer

| Situation | Reach for |
|-----------|-----------|
| Zero budget, CLI only | ffmpeg |
| Graphics-heavy, parameterized, repeatable | Remotion |
| HTML/CSS frames, agent-driven end to end | HyperFrames |
| Full NLE quality, grading, interchange | FilmCraft, or Premiere / DaVinci via a bridge |
| Phone-first, human tweaks | CapCut drafts |

The skill itself is tool-agnostic: markdown in, plan out, any tool
renders. If a renderer is unavailable, say so and hand back the plan —
a blocked render is honest; a fabricated render is not.
