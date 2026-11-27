# CONTEXT — edit-master-skill (Phase 26 boot, rebuilt from repo)

Owner: Dani (GitHub **Dani-Devlop**) · Branch: main only · Tokens silent · MIT.

## MISSION
Build a GENERAL, FREE, MIT, open-source **universal viral video-editing skill**
that ANY AI agent (Claude/ChatGPT/Codex/Cursor/Gemini/plain chat) can load to
produce premium IG/YT-native edits. Repo is source of truth:
https://github.com/Dani-Devlop/edit-master-skill

## GOALS
(a) save time + premium quality + money (post/client-ready reels);
(b) free & open on GitHub; (c) outputs that LOOK/FEEL like top IG/YT edits —
playful, interactive, motion-rich, enjoyable even when topic is irrelevant;
(d) FULL AUTOMATION: agent detects song/genre/source, proposes style, asks
only when truly blocked; (e) user PC is WEAK, user is NOT an editor — all
heavy compute in agent sandbox; user receives final MP4 + reports (Telegram
owner 2040835005, bot mystationZworkbot, LIVE-only, NO scheduler);
(f) HONESTY: measured frame evidence, blind independent critic, no fake
passes, stop-loss 2 rounds then hybrid/executor-swap/user-decision.

## TOOLSTACK (honest fallback log per engine)
- NLE/MOTION: FilmCraft + EffectCraft (ArtCraft), Blender HEADLESS + blender-cli
  / Blender MCP, Remotion (+captions-themes, reels-editor, ads,
  claude-remotion-skill, MotionCraft), HyperFrames, ffmpeg.
- ANALYSIS: whisper/faster-whisper, librosa/aubio, rembg/isnet + mediapipe,
  chromaprint/fpcalc + AcoustID/AudD, yt-dlp, PIL/numpy.
- ASSETS (license-logged, no watermarked stock): Google Fonts (Montserrat/
  Inter/Poppins/Playfair/Vazirmatn/JetBrains Mono/Space Mono/Archivo Black),
  Pexels/Pixabay/Mixkit/Coverr, Pixabay Music/YT Audio Library/Freesound,
  OpenMoji/Twemoji, Wikimedia/Met/Rijksmuseum (PD), PolyHaven/ambientCG.
- ACTUAL PIPELINE (proven): pure Python PIL/numpy + ffmpeg + librosa +
  rembg/isnet; persp3d homography for M1-M5 (honest substitute when bpy
  unavailable); no Blender/Remotion required.

## REFERENCE BANK (replica protocol)
YT: g9xoKm5DEeU, 7g9Qm1e00zU, sGt1ACELN4k, z6zkeILNHL8, AgUATWAOaKY,
pwGeWRlrU10, 03BNd8ygnq8. IG: DgIBQu2IRM1, DfhJhfCj2su, DgCHM4NMgrv,
DfuYIefNp_l, Dfj6Q5CDzhZ, DfnCiOkRGOH, DexJ-qWiWdY. Frame sets: 4-quadrant
families, Raw/Edited lockups, Hera depth. IG reference creators credited in
README (@eightsenses.media, @keevinnlc, @nikhilmotion.vlc, @sambee9991).

## ACCEPTANCE (Phase 26 reframe, S7)
PASS-to-post = **binary B1-B10 ALL YES** + IG-native match >=70% (blind
independent critic). Absolute aesthetic 8.5 = STRETCH, not blocker; if
stretch unmet after 1 round -> USER decision (post-as-is OR hybrid
human-polish). Never fake, never endless rounds.
- B1 living footage >=60% · B2 hook occlusion · B3 video-in-card ·
  B4 cutout depth · B5 semantic stickers · B6 tissue fill ·
  B7 no internal labels · B8 single-accent volt · B9 hook legible <=0.92W ·
  B10 no glyph overlap.
- Frozen gate ledger (26 IDs: G1-G8, LF1-LF8, IG1-IG10, WC1-WC4) IMMUTABLE;
  loudness -14±0.5 LUFS TP<=-1.5; face-safe; end clean; single caption voice;
  delivery lock (gate json measured on final decoded file, sha-equal).

## OPS / HYGIENE
Telegram owner 2040835005, LIVE-only inline reports every ~30 min (step
boundaries, NO scheduler/cron). task.md first, 20-block progress bar in
reports. Hygiene: TEMP in /tmp/ems-work/<run>/ deleted after output;
KEEP-LIST; chat surface clean (no edit-*/TEMP). Badge policy is an INTERNAL
agent rule (Verified-or-none, NEVER Unverified, 0 Unverified audits) — kept
ONLY in agent prompt/config + internal note in docs/OPS.md; public README
does NOT mention GPG/signing/scopes. Commit signing: token has no
admin:gpg_key scope -> intentional unsigned fallback. Only Dani-Devlop, only main.

## WHAT WE DID (phase history, reconstructed from 31 commits)
- Ph1-7 skill creation+publish: hooks/scoring/EDL/humanizer/caption-lint/
  retention/viral-research; MIT; 7 YouTube + 2 Jakeschincariol sources.
- Ph8-12 enforcement: unified renderer, gate-on-file, delivery lock,
  regression negatives, karaoke v2, hygiene, chat-clean, no-schedule.
- Ph13-16 leap: PRO presets, style-DNA, encyclopedia, self-critique,
  20-pillar proof-first V0.
- Ph17-19 scene-engine + adopted repos + graphics-first + replica protocol;
  Ph18 FULL AUTOMATION song-ID (WELCOME — IDK ft. Eminem, prod. J Dilla);
  Ph19 adopted pro pipelines (reels-editor/captions-themes/remotion-ads/
  claude-remotion-skill).
- Ph20 visual truth: crop proofs from delivered file, blind critic, clean sha,
  placeholder/watermark ban. Ph21 graphics-first + Blender headless attempt.
- Ph22 balance/semantic stickers/color-world. Ph23 living footage +
  video-in-card + density. Ph24 IG-native: beat-lock, pseudo-UI, seamless
  loop, kinetic slams, idle motion, selective color, tight pacing, film
  texture. Ph25 frozen gate ledger + binary B1-B6 + WC1-WC4 provided code +
  10s showcase-first + stop-loss (commit 348423f).

## CURRENT STATE AT PH26 BOOT
- In-repo gate truth: test-results/g25_full_gates.json (25/26 PASS, LF6
  replica-live open). Last in-repo master sha16: v24 9042d6886bdd6eff.
  v25 deliverables + sha 881320f85d3fd166 were external-only (purged).
- Blind critic v25: 7.3 median (< 8.5 stretch bar) — honest NO-PASS.
- KNOWN FLAWS carried into Ph26: internal spec labels burned into master;
  palette leaks (blue invert / green leaves / color cutouts); hook "W E L C"
  edge-cropped; glyph crowding (notification over "stakes"); light-phase
  (12-17.4s) sparse; cutout shadow weak on white.
- Ph26 fixes implemented in code (this phase): S1 labels QC-only +
  LABEL_LOG; S2 B&W cutouts + graded WC1 sources + B8 census; S3 hook fit
  0.84W pre-camera + B9 measurement; S4 collisions repositioned + census B10;
  S5 HERO cutouts >=45%H + density census; S6 shadow_boost; gates B7-B10
  appended (frozen ledger untouched). Render/gates/delivery run the moment
  the raw MV clip is re-supplied (source ladder logged in task.md 26.04).
