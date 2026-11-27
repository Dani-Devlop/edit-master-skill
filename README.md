# 🎬 Edit Master Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/Dani-Devlop/edit-master-skill)](https://github.com/Dani-Devlop/edit-master-skill/releases)
[![Stars](https://img.shields.io/github/stars/Dani-Devlop/edit-master-skill?style=social)](https://github.com/Dani-Devlop/edit-master-skill)
[![Forks](https://img.shields.io/github/forks/Dani-Devlop/edit-master-skill?style=social)](https://github.com/Dani-Devlop/edit-master-skill/fork)
[![Last commit](https://img.shields.io/github/last-commit/Dani-Devlop/edit-master-skill)](https://github.com/Dani-Devlop/edit-master-skill/commits/main)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**One markdown skill + a component library that turns ANY AI agent into a
premium short-form video editor.** Graphics-first, Instagram/YouTube-native,
beat-locked, 3D-capable — and honest about its own quality.

Works with Claude · ChatGPT · Codex · Cursor · Gemini CLI · plain chat.
Free & open source (MIT). Your weak laptop is fine: heavy rendering happens
in the agent's sandbox/cloud; you receive the finished MP4.

---

## ✨ What it does

Give it raw footage (or let it find the source itself) and it runs the whole
pipeline: transcript & tight cuts → scene plan → designed graphics scenes →
karaoke captions → camera language → grade → 3D accents → cue-sheet sound
design → platform masters + cover. The edit itself is the entertainment:
playful, interactive, motion-rich — enjoyable even when the topic isn't.

## 🚀 Features

- **Graphics-first scene engine** — 19 scene types (full-screen text, line+
  text, painting, illustrations, graphs, B-roll+text, UI listicles, counters,
  before/after, polaroid cascades, insert worlds, 3D type slams…)
- **Karaoke captions v2** — bold sans, single active-word highlight, spoken
  dim, looping sweep, word-timestamp sync, RTL/Persian support
- **IG-native feel** — onset-locked cuts, pseudo-UI interaction (tap/swipe/
  comment/notification/heart), seamless loop, kinetic slams, idle micro-
  motion, selective color, tight pacing, film texture
- **Living footage** — full-bleed performance beats + video-in-card
  polaroids (never a frozen slideshow)
- **3D accents** — Blender headless / ArtCraft 3D Stage; extruded type,
  floating cards, counter rings, callout orbits, world inserts
- **Honest quality gates** — binary human-visible checklist + independent
  blind critic + frame-crop proofs; no self-reported fake scores
- **Full automation** — song-ID (fingerprint + lyrics), source fetch, style
  proposal; asks only when truly blocked
- **Multi-platform masters** — Reels / Shorts / TikTok / Telegram / LinkedIn
  (+1:1, 4:5), per-platform safe-zones & loudness

## ⚡ Quick start

    git clone https://github.com/Dani-Devlop/edit-master-skill.git
    # load SKILL.md into your agent (see Install below), then say:
    # "Edit this raw clip into a 30s IG-native reel in your best style."

No filesystem? Paste SKILL.md at the top of any chat — it runs as a mode.

## 🧩 Install per agent

- **Claude Code / Codex / Cursor / Gemini CLI:** copy SKILL.md (+ components/,
  presets/) into your skills directory, or point the agent at the repo path.
- **Any chatbot:** paste SKILL.md; keep the method, formulas and checklists.
- **MCP/agent platforms:** expose the render engines (below) as tools;
  SKILL.md is the brain, the renderer is pluggable.

## 🛠 Toolstack

| Layer | Tools |
|---|---|
| NLE / motion | FilmCraft, EffectCraft, ArtCraft Studio 3D Stage, Remotion (+captions-themes, reels-editor, ads, motion-craft), HyperFrames |
| 3D | Blender headless + blender-cli / Blender MCP |
| Analysis | whisper/faster-whisper, librosa/aubio, rembg/isnet+mediapipe, chromaprint/AcoustID/AudD, yt-dlp |
| Composite / master | ffmpeg, PIL/numpy |
| Assets | Google Fonts, Pexels/Pixabay/Mixkit/Coverr, Pixabay Music/YT Audio Library/Freesound, OpenMoji/Twemoji, Wikimedia/Met/Rijksmuseum (PD art), PolyHaven/ambientCG/RenderCrate |

## 🎯 Quality & honesty

Pass-to-post = **10 binary human-visible checks** (living footage, hook
occlusion, video-in-card, cutout depth, semantic stickers, tissue fill, no
internal labels, single-accent palette, legible hook, no glyph overlap)
**+ ≥70% IG-native match** scored by an independent blind critic on decoded
frames. Every claim ships a frame-crop proof. Stop-loss after 2 rounds →
hybrid human polish or executor swap. Numbers are never invented.

## 📊 Results

See `test-results/` for masters, covers, contact sheets, gate ledgers,
cue sheets and sha256 manifests.

## 🙏 Credits

**Reference tutorials (studied frame-by-frame):**
Joseph | Video Editing (premium reels, minimal talking-head, 5-phase),
Dan Kieft (AI editing course), Grow with Alex (5 basics + beat table),
Softgirlnocode (HyperFrames), Jason Cooperson (setup guide).

**Concept repos (MIT):** Jakeschincariol/youtube-agent-skill (21 hooks,
scoring, EDL, retention), Jakeschincariol/instagram-agent-skill (26 hooks,
beats, humanizer, caption lint).

**Adopted pipelines (MIT):** andrebrito16/skill-reels-editor,
vshukla7/remotion-captions-themes, Maartenlouis/remotion-ads,
haidrrrry/claude-remotion-skill, MotionCraft skill.

**Engines:** ArtCraft (FilmCraft/EffectCraft/Studio), Blender + blender-cli +
Blender MCP, Remotion, HyperFrames (HeyGen), ffmpeg.

**IG reference creators:** @eightsenses.media, @keevinnlc,
@nikhilmotion.vlc, @sambee9991.

**Assets/fonts/audio:** Google Fonts, Pexels/Pixabay/Mixkit/Coverr,
Pixabay Music / YouTube Audio Library / Freesound, OpenMoji/Twemoji,
Wikimedia Commons / Met Open Access / Rijksmuseum, PolyHaven/ambientCG/
RenderCrate. All license-logged in docs/RESOURCES.md.

## 🤝 Contributing

Issues + PRs welcome (see CONTRIBUTING.md). New scene types, sticker
species, language packs and platform presets are especially wanted.

## 🗺 Roadmap

More 3D moves banked · color-source pipeline · more genre presets ·
bilingual subtitle packs · public example gallery.

## 📄 License

MIT — use it, change it, ship it. See LICENSE.

---

If this saves you an editor's fee, ⭐ the repo so more creators find it.
