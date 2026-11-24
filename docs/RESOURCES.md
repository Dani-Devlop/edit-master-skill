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
