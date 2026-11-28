# Phase 32 F6 — 15-repo adoption checklist (security-grade EVERY repo before code)

| repo | grade | adopted | denied/dropped | stop-loss |
|------|-------|---------|----------------|-----------|
| kajisho5/ffmpeg-skill | A | SKILL.md + workflow.md -> opsverify contract layer | .claude/, tests/, .github/, bin/ (119MB engine not needed) | 0 |
| howseen-ai/claude-motion-design | CAUTION | SKILL.md -> HTML+Playwright+ffmpeg fallback engine spec | 4 fetch scripts DENY-LISTED (mcp21_client/mixkit_sfx_search/render_template/svgl_logos) | 0 |
| iart-ai/motion-skills | A | PACK-INDEX (19 packs/56 skills) + verify trio | child pack repos not fetched (index = vocabulary) | 1 (child fetch) |
| artemnovitckii/claude-animation-skills | A- | 11 family specs (F5-F11) | kit/setup.sh + tts_elevenlabs.py denied | 0 |
| Barty-Bart/motion-graphics | B | 6 specs incl. word-timed B-roll + object-separation | skills/*/scripts/ denied (network) | 0 |
| AgriciDaniel/claude-shorts | A | SKILL + 4 references (moment selection, face-track 9:16) | remotion engine not adopted (stack policy) | 0 |
| kurbaitaev/ghost-editor | B | 7 styles + people-rules + reverse-engineer method (19-style claim DISCREPANCY logged) | scripts/ denied (network + Mac renderer) | 1 (style count) |
| viettranx/3dviz-pro-max | A- | 223 recipes + capture.py screen gate + SKILL.md | site/brand/evals out of scope | 0 |
| yt-dlp, openai/whisper, heygen-com/hyper-frames | SKIP | already in stack / not adopted | — | — |
| LPengYang/MotionClone | SKIP | GPU generative research | — | — |
| CloudAI-X/threejs-skills, mattypark/Motion-graphics-skill | REFERENCE-ONLY | cloned, not banked (three.js / gráficos specs duplicative of banked sets) | — | — |

License-log: ALL 8 adopted repos = MIT (verified LICENSE headers, see per-repo
SECURITY-GRADE.md). Zero network-capable file was banked. Ghost-editor
Mac-renderer path explicitly NOT adopted (F6). All sources: github.com public
clones (shallow, depth 1).
