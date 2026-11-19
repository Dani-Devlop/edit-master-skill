# Example 2 — Edit Decision List (EDL) for a 42s podcast clip

Source: 62-minute podcast, raw transcript from whisper. Target: vertical clip
for TikTok, energetic style. Dead-air floor 0.35s.

## Cuts

| id | tc_in | tc_out | action | visual | audio | on_screen | note |
|----|-------|--------|--------|--------|-------|-----------|------|
| C01 | 00:18:12.400 | 00:18:14.900 | KEEP | host mid-gesture, punch-in 108% | music bed in | NEVER PAY FULL PRICE | hook, formula #2 Negative Command |
| C02 | 00:18:14.900 | 00:18:16.100 | KEEP | host continues | music bed | | "Stop booking hotels direct." |
| C03 | 00:18:16.100 | 00:18:19.300 | KEEP | B-roll: booking site screen rec | SFX whoosh on cut | | "Here's the 3-step workaround." |
| C04 | 00:18:19.300 | 00:18:19.850 | CUT-FILLER | - | - | - | "um" cue only |
| C05 | 00:18:19.850 | 00:18:24.500 | KEEP | punch-in 104% | music bed | STEP 1 | step one explained |
| C06 | 00:18:24.500 | 00:18:27.100 | CUT-DEAD | - | - | - | 2.6s gap, trim from middle, keep breath |
| C07 | 00:18:27.100 | 00:18:31.000 | KEEP | screen rec follows cursor | music bed | STEP 2 | step two |
| C08 | 00:18:31.000 | 00:18:33.200 | CUT-RETAKE | - | - | - | sentence restarted; keep only second attempt |
| C09 | 00:18:33.200 | 00:18:37.800 | KEEP | B-roll: price comparison graphic animates | SFX ding | STEP 3 | step three |
| C10 | 00:18:37.800 | 00:18:40.500 | KEEP | host, wide | music swells | | payoff: "That's 40% off, every booking." |
| C11 | 00:18:40.500 | 00:18:42.000 | KEEP | host, punch-in | music ends on beat | COMMENT "TRAVEL" | ask + loop word echo |

## JSON (agent-readable)

```json
{"project": "podcast-travel-hack", "wpm": 168, "target_s": 30,
 "source_offset_s": 1092.4,
 "cuts": [
  {"id":"C01","tc_in":"00:18:12.400","tc_out":"00:18:14.900","action":"KEEP",
   "visual":"punch-in 108%","audio":"music bed in","on_screen":"NEVER PAY FULL PRICE",
   "note":"hook, formula #2 Negative Command"},
  {"id":"C06","tc_in":"00:18:24.500","tc_out":"00:18:27.100","action":"CUT-DEAD",
   "note":"2.6s gap, trim from middle, keep breath"}
 ],
 "speech_removed_pct": 21.0,
 "warning": "percentage is of SPEECH only; no silent demo in this span"}
```

## Checks before render

- beat changes every <= 4s: pass (max gap 4.5s is C05... flagged, split C05)
- captions inside 1080x1920 safe zone: pass
- hook inside 3s: pass (C01+C02 = 3.7s total speech, but first claim lands at 2.5s)
- loop: C11 "comment TRAVEL" echoes C01 "never pay full price" -> pass
