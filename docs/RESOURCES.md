# RESOURCES — Bank (L6, Phase 14.1)

Refreshed: 2026-11-22 06:47 UTC. Only royalty-free/CC/licensed sources. Log license per item.

## Stock video libraries (verified reachable, license-safe)
| Library | License | Access method | Notes |
|---|---|---|---|
| Mixkit | Mixkit Stock Video Free License (free commercial, no attribution) | HTML scrape of category pages -> assets.mixkit.co/videos/<id>/<id>-1080.mp4 | Server-rendered pages expose direct CDN mp4; category URLs /free-stock-video/<cat>/ |
| Pexels | Pexels License | blocked: Cloudflare challenge on datacenter IP | API key path available if key provided |
| Wikimedia Commons | CC0/CC-BY per file | API (action=query) | vertical coverage near-zero; good for horizontal |

## Blocked (logged honestly)
- YouTube via yt-dlp: bot-check "Sign in to confirm you're not a bot" on datacenter IP (no cookies/JS runtime). Retry with cookies if manager provides.
- Instagram: same network class block; not attempted beyond yt-dlp.

## Banked assets (Phase 14.1 run)
| ID | Genre | Res | Dur | Used as |
|---|---|---|---|---|
| Mixkit 52080 | fitness | 1080x1920 | 16.7s | T-2 |
| Mixkit 10428 | food | 1080x1920 | 15.0s | T-3 |
| Mixkit 4633 | cars/scenic | 1920x1080 | 22.1s | T-4 (day-for-night) |
| Mixkit 1548 | pets/dog | 1080x1920 | 14.8s | T-5 |

## SFX + music
- SFX synthesized in-run (whoosh/glitch/splice/thump) — no license exposure.
- Music beds synthesized in-run per genre (drive/bright/dark/bouncy @ genre BPM) — original works.

## Viral-edit technique references (public breakdowns, technique only)
- Karaoke word-sweep captions (TikTok/Reels norm), type-slam hook lockups, speed-ramp accents,
  splice-flash bites <=0.15s, freeze+slam on hook — grammar in docs/REFERENCES.md + docs/STYLES.md.
