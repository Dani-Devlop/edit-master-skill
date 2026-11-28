# SECURITY GRADE: CAUTION (adopted with DENY-LIST per F6)
Repo: howseen-ai/claude-motion-design, MIT (c) 2026 Howseen AI (Raphael Aubry).
Manual review 2026-11-28: fetch-capable scripts identified — DENY-LISTED, NOT
banked, must never run inside this sandbox:
1. skill/motion-design/scripts/mcp21_client.py   (remote MCP client)
2. skill/motion-design/scripts/mixkit_sfx_search.py (network SFX search)
3. skill/motion-design/scripts/render_template.py  (network hit)
4. skill/motion-design/scripts/svgl_logos.py       (remote SVG fetch)
Banked: SKILL.md spec ONLY. Role: HTML+Playwright+ffmpeg FALLBACK ENGINE
concept (render slides/motion via HTML -> Playwright frames -> ffmpeg mux) —
adapted, not executed as upstream code.
