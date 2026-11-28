# ghost-styles (F6 port of kurbaitaev/ghost-editor styles, MIT)

7 style presets (cinematic/clean/editorial/kinetic/launch/meme/pop) + upstream
people-rules.json — ported verbatim as DATA. Upstream scripts/ (incl. the
Mac-only renderer + network fetch scripts) NOT adopted — see
components/adopted/ghost-editor/SECURITY-GRADE.md. Reverse-engineer method
(HOW-IT-WORKS.md/PLAYBOOK.md) feeds our replica protocol: replicate a style by
measuring reference frames -> fit preset parameters -> render through OUR
gate-verified renderer -> blind critic x3.
DISCREPANCY: infographic claims 19 styles; upstream ships 7 (logged honestly).
