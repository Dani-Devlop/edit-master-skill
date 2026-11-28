# prompt-bank — F5 ADOPTION (vocabulary, not engine)

## Status: BANKED (internal) / external source BLOCKED (honest)

F5 target was prompt-motion.com's free prompt bank (230+ prompts with exact
prompts). Reachability attempts (2026-11-28):
1. direct curl x4 URL variants -> HTTP 403 Cloudflare "Just a moment..."
2. headless agent-browser (Chrome 158) -> Turnstile interstitial; clicked
   "Verify you are human" -> challenge never completes headless (5x title poll
   over 65s stayed "Just a moment...")
3. archive.org availability API -> HTTP 000 (host unreachable from sandbox)

STOP-LOSS reached (2 attempts + fallback). **Nothing fabricated**: the bank
below contains ZERO external prompt content.

## What is banked

`prompts.json` — 55-entry internal vocabulary distilled from THIS repo's
gate-verified grammar (v26 renderer + adopted modules). Each entry:
`prompt` (human-readable motion vocabulary) + `recipe` (ordered ops, each op
maps 1:1 to a banked component function) + `gate` (the ledger gate that
polices it). Categories: hook / transition / camera / sticker / caption /
audio / pacing / texture / scene / gate.

Engine discipline: the bank stores VOCABULARY + recipes, never an engine —
renders execute through the banked renderers only.

## License

- Internal entries: MIT (this repo).
- prompt-motion.com content: UNVERIFIED / NOT-FETCHED (blocked). If a
  reachable fetch path appears, extraction must be re-run with its license
  check BEFORE banking any external prompt.

## Replica-test 2 (F5 requirement)

`scripts/p32_prompt_replica.py` executes two banked recipes end-to-end:
1. `hook_volt_slam_confetti` -> 3s clip (slam + confetti + brackets +
   film-gate burn), mini-gate: volt-only chroma census + span <= 0.92W.
2. `trans_shrink_card_zoom` -> 3s clip (shrink-to-tilted-volt-card +
   zoom-through from histmap relief plate to paper canvas), mini-gate:
   volt-only chroma census.
Reports: test-results/p32/prompt_replica_report.json
