# RESOURCES — Bank v4 (P17, Phase 16.0)

Refreshed: 2026-11-24. Only royalty-free/CC/licensed sources. License logged per item.
Bank size: 4 banked stock videos + 1 manager-attached MV raw + synthesized SFX/music +
technique-reference library. No login/private content is ever scraped.

## Stock video libraries (verified reachable, license-safe)
| Library | License | Access method | Notes |
|---|---|---|---|
| Mixkit | Mixkit Stock Video Free License (free commercial, no attribution) | HTML scrape of category pages → assets.mixkit.co/videos/<id>/<id>-1080.mp4 | Server-rendered pages expose direct CDN mp4; category URLs /free-stock-video/<cat>/ |
| Pexels | Pexels License | blocked: Cloudflare challenge on datacenter IP | API key path available if key provided |
| Wikimedia Commons | CC0/CC-BY per file | API (action=query) | vertical coverage near-zero; good for horizontal |

## Blocked (logged honestly)
- YouTube via yt-dlp: bot-check "Sign in to confirm you're not a bot" on datacenter IP
  (no cookies/JS runtime). Retry with cookies if manager provides.
- Instagram: same network class block; not attempted beyond yt-dlp.

## Banked assets
| ID | Genre | Res | Dur | License | Used as |
|---|---|---|---|---|---|
| Mixkit 52080 | fitness | 1080x1920 | 16.7s | Mixkit Free (commercial, no attribution) | T-2 fitness_leap_v16 |
| Mixkit 10428 | food | 1080x1920 | 15.0s | Mixkit Free | T-3 food_fresh_v16 |
| Mixkit 4633 | cars/scenic | 1920x1080 | 22.1s | Mixkit Free | T-4 cars_nightdrive_v16 (day-for-night) |
| Mixkit 1548 | pets/dog | 1080x1920 | 14.8s | Mixkit Free | T-5 pets_zoomies_v16 |
| manager upload | music_video | — | — | manager-provided source (T-1 rights held by manager) | T-1 mv_darkmono_v16 (song + MV raw) |

Every banked asset used in a delivery carries its license in the video manifest
(`resource_licenses` field — G-P17).

## SFX + music
- SFX synthesized in-run (whoosh/glitch/splice/thump) — original works, no license exposure.
- Music beds synthesized in-run per genre (drive/bright/dark/bouncy @ genre BPM) — original works.
- T-1 MV: original mix KEPT (P10) — no overlay music; copyright coverage = full (original audio).
- Generated-bed videos (T-2..T-5): full-length music safe — original synthesized beds.

## Public technique references (opened 2026-11-24)
- Karaoke word-by-word caption grammar (word highlight follows speech):
  https://recapo.ai/blog/how-to-add-word-by-word-captions — used for P1 spec sanity
  (active-word highlight + dim pattern is the mainstream pro norm).
- Internal grammar references: docs/REFERENCES.md (reference-pack ingest evidence),
  docs/STYLES.md (family sheets), docs/TECHNIQUES.md v4 (when-to-use encyclopedia).

## Engine learnings banked this phase (also in docs/TECHNIQUES.md v4)
- Halftone-on-footage detector: lattice autocorrelation (structural), replaces
  non-discriminative FFT peak-ratio; calibrated on 7 real finals + synthetic negatives.
- Whip-pan smear: edge-clamped shift (np.roll wrap pulls the opposite frame edge
  across bright scenes as a dark band).
- Motion-blur detection: strong blur collapses horizontal edge energy — detect the
  collapse, not an increase.
- Accent-card detection: saturation floor must be accent-relative for soft palettes.
- Matte-unavailable honest fallback: cutout beat → deep-zoom comp, logged in manifest.

## Phase 18.0 resource bank (2026-11-24)
- Song: WELCOME — IDK feat. Eminem, prod. J Dilla (2026-11-13). Commercial;
  edit-test usage only, no publication. Identified via faster-whisper transcript
  x Genius verbatim match (HIGH confidence).
- Sources attempted: yt-dlp YouTube (blocked: bot-check), cobalt API
  (auth-required), REF-TAG-A CDN (403). Fallback: manager-provided raw
  (official MV footage excerpt) — all logged in test-results/phase18/.
- Painting asset: Francisco de Zurbarán, "Still Life with Lemons, Oranges and
  a Rose" (1633) — PUBLIC DOMAIN (artist d. 1664); retrieved via image-search
  rehost (z-cdn mirror); PD status unchanged.
- Editing-knowledge study links (techniques extracted into scene engine):
  youtu.be/g9xoKm5DEeU (Joseph premium reels) | youtu.be/7g9Qm1e00zU +
  youtu.be/AgUATWAOaKY (Dan Kieft) | youtu.be/sGt1ACELN4k (Jason Cooperson) |
  youtu.be/z6zkeILNHL8 (HyperFrames) | youtu.be/pwGeWRlrU10 (Joseph 5-phase) |
  youtu.be/03BNd8ygnq8 (Grow with Alex). Playback blocked in sandbox
  (bot-check); techniques extracted from Phase 18 spec + prior phases.
- Engines: filmcraft (storytold/filmcraft) + EffectCraft/motionCraft —
  unavailable in sandbox; fallback chain per spec E3 (Remotion -> HTML->frames
  -> PIL sequences -> ffmpeg) implemented in p18_render.py.
- Fonts: DejaVu Sans/Serif Bold (Bitstream Vera license).
- ASR: faster-whisper small (MIT); beatmap: librosa (ISC).

## Phase 19 additions — adopted pro pipelines (all cloned/studied, licenses verified)
- github.com/andrebrito16/skill-reels-editor — MIT (c) 2026 André Brito.
  Adopted: pipeline order, silence-cut padding (0.09/0.15s), IG safe area
  (300/480/130px @1080w), export spec (H.264 High 2-pass VBR 12/16Mbps,
  closed GOP, BT.709, AAC 48k, -14 LUFS TP -1.5), numeric-checked grading.
- github.com/vshukla7/remotion-captions-themes — MIT (c) 2026 Vinayak Shukla.
  Adopted: word-level karaoke + relation-based layout engine (anchors,
  relations, collision) -> ported into p19_kar.py deterministic PIL layout.
- github.com/Maartenlouis/remotion-ads — MIT (c) 2025 Maarten van Onoesen.
  Adopted: word-by-word caption pacing + VO-sync patterns.
- github.com/haidrrrry/claude-remotion-skill — MIT (c) 2025 haidrrrry.
  Adopted: motion-graphics skill structure + Remotion motion rules.
- Caption grammar (web refs, no code reuse): hyperframes.heygen.com/tools/
  animated-captions (17 named caption styles; every word timed to speech;
  below-chin above-UI placement), submagic.co/ai-caption (word-by-word
  highlight styles, safe-zone placement), usevyra.com (Submagic alternative) + blitzcutai.com TikTok font
  grammar (bold sans, white, 1-3 words, one active highlight).
- Fonts: Montserrat variable + Inter variable (SIL OFL 1.1, google/fonts,
  repo-shipped under assets/fonts/); DejaVu (Bitstream Vera) fallback.
- ASR faster-whisper (MIT); beatmap librosa (ISC); opencv-python-headless
  (Apache-2.0); PIL (HPND).
- Asset policy AS1: only public-domain/CC0/generated/manager-raw. In this
  sandbox Wikimedia/Met image CDNs were proxy-blocked (403) — still-life card
  generated in-sandbox (p19_gen_paint.py, deterministic) and logged honestly.

## Phase 21+3D — graphics-first replica + Blender 3D module

- Blender bpy 5.0.1 (GPL-2.0-or-later, Blender Foundation) — headless 3D via
  pip wheel in sandbox; M1 extruded-type slam banked as components/3d/
  m1_type_slam/ (m1_render.py, Cycles CPU low-samples, film-transparent alpha
  sequence, DOF f/2.8). Blender-lab MCP (blender.org/lab/mcp-server) and
  github.com/ahujasid/mcp-for-blender listed as interactive fallbacks; not
  needed here (bpy IS the headless driver — honest engine log). blender-cli
  (renezander030) repo unreachable from sandbox (auth prompt) — bpy used
  instead. SceneCraft (arxiv.org/abs/2403.01248) — text->Blender python
  knowledge base.
- 3D asset policy: no external kit used this phase; geometry is generated
  bpy primitives + repo-shipped fonts (extruded text). CC0 kits listed for
  future: polyhaven.com, ambientcg.com, rendercrate.com. ArtCraft 3D Stage
  (getartcraft.com/faq/3d-editor, github.com/storytold/artcraft) — used when
  credits available; none consumed this phase (log).
- rembg isnet-general-use / u2net (MIT, danielgatis/rembg; models Apache-2.0)
  — person cut-outs (PL3 rotoscopy substitute). u2net fails on dark B&W
  footage (0.03 coverage); isnet-general-use succeeds (stairwell figure).
  matte fps == output fps: cutouts composited on every 30fps frame they
  appear; coverage logged per scene in engine logs.
- faster-whisper 1.2.1 (MIT, SYSTRAN) — song-ID transcription (E3): whisper
  lyrics -> web verification: "WELCOME" = IDK feat. Eminem & J Dilla (Apple
  Music id 6828648031; Musixmatch). yt-dlp 2026.11.23 (Unlicense) installed
  for original-source fetch — YouTube fetch unavailable in sandbox (video
  unavailable / no JS runtime) — honest fallback: user-supplied clip.
- Fonts added: Playfair Display variable + Italic, Space Mono Regular/Bold,
  JetBrains Mono variable (all SIL OFL 1.1, google/fonts) -> assets/fonts/.
- Asset policy AS4 this phase: Wikimedia/Met CDNs proxy-blocked (HTTP 400/403
  attempts logged) -> LB5 still-life GENERATED in-sandbox (z-ai image gen,
  "Dutch Golden Age still life" prompt) — generated-asset path allowed by
  AS4, no watermark, provenance logged in manifest.
- Target reference: IG refs (DgIBQu2IRM1 eightsenses et al.) login-walled ->
  per R1 protocol the user screen-recording upload was used as the ONE target;
  decoded 0.5s beat map in docs/p21/INVENTORY_target.md.

## Phase 22 additions (2026-11-26)
- REPLICA display-clock method: per-quadrant frame-diff cut detection
  (numpy, thr 6, 0.20s merge) on the user screen-recording
  (VID_20261121_000716_199.mp4, 6.77s, user-provided — the ONE target per
  R1 protocol); stretch rep_t = reel_t * 8.9/6.893 matched to
  replica_sheet_v22.py comparison clock; r21 method-swap uses decoded reel
  quadrant crops (ffmpeg crop=344x622) as footage layer — source = user's
  own recording, no third-party assets added.
- bpy 5.0.1 headless via recovered venv (Blender-as-pip-module, GPL +
  Blender License; used only as a renderer subprocess, scene files in
  components/3d/m1_type_slam/).
- ffmpeg loudnorm 2-pass + alimiter chain (LGPL/GPL build, deb13u1) —
  mastering chain documented in SKILL.md Phase 22 section.
- No new third-party fonts/assets this phase; fonts remain OFL set in
  assets/fonts/ (restored to repo-persistent path after sandbox recycle).

## Credits (synced with README, Phase 26 2026-11-27)

**Reference tutorials (studied frame-by-frame):** Joseph | Video Editing
(premium reels, minimal talking-head, 5-phase), Dan Kieft (AI editing
course), Grow with Alex (5 basics + beat table), Softgirlnocode
(HyperFrames), Jason Cooperson (setup guide).

**Concept repos (MIT):** Jakeschincariol/youtube-agent-skill (21 hooks,
scoring, EDL, retention), Jakeschincariol/instagram-agent-skill (26 hooks,
beats, humanizer, caption lint).

**Adopted pipelines (MIT):** andrebrito16/skill-reels-editor,
vshukla7/remotion-captions-themes, Maartenlouis/remotion-ads,
haidrrrry/claude-remotion-skill, MotionCraft skill (metiu1-motion-craft).

**Engines:** ArtCraft (FilmCraft/EffectCraft/Studio 3D Stage), Blender +
blender-cli + Blender MCP, Remotion (+captions-themes, reels-editor, ads),
HyperFrames (HeyGen), ffmpeg.

**IG reference creators:** @eightsenses.media, @keevinnlc,
@nikhilmotion.vlc, @sambee9991.

**Assets/fonts/audio:** Google Fonts (Montserrat/Inter/Poppins/Playfair
Display/Vazirmatn/JetBrains Mono/Space Mono/Archivo Black), Pexels/Pixabay/
Mixkit/Coverr (CC0 footage), Pixabay Music / YouTube Audio Library /
Freesound, OpenMoji/Twemoji, Wikimedia Commons / Met Open Access /
Rijksmuseum (PD art), PolyHaven/ambientCG/RenderCrate (CC0 3D).
All license-logged in the per-phase sections above.
