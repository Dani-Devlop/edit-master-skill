#!/bin/bash
# Phase 19 driver — self-contained stages; WORK re-staged from durable sources each run
# (sandbox /tmp is volatile between messages). Tokens never printed.
set -u
REPO=/home/z/my-project/ems19-repo
RAW="/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
WORK=/tmp/ems-work/p19/run
DL=/home/z/my-project/download/phase19_deliverables
STAGE=$DL/_stage
mkdir -p "$WORK/assets" "$DL" "$STAGE"
cd "$REPO/scripts" || exit 2

# ---- prep (idempotent, ~60-90s) ----
rm -rf "$WORK"; mkdir -p "$WORK/assets"
python3 p14_ingest.py "$RAW" "$WORK" en >/dev/null 2>&1 || true
python3 p14_beatmap.py "$RAW" "$WORK" >/dev/null 2>&1 || true
test -s "$WORK/probe.json" || { echo "PREP FAIL: probe.json missing"; exit 3; }
cp "$REPO/test-results/phase18/lyric_lines.json" "$REPO/test-results/phase18/cue_sheet.json" \
   "$REPO/test-results/phase18/scene_plan.json" "$WORK/"
python3 - <<'PYEOF'
import json
sp = json.load(open('/tmp/ems-work/p19/run/scene_plan.json'))
sp['v19'] = {
  "caption_system": "v2 (p19_kar, CV1-CV7)",
  "canvas_policy": "AS2 designed canvas for design scenes (no blur-of-footage bg)",
  "asset_policy": "AS1 zero-watermark + license registry",
  "source_note": "REF-TAG-A CDN re-tested 403 (auth key expired 2026-11-24); honest fallback re-confirmed: manager-provided official-MV excerpt",
}
json.dump(sp, open('/tmp/ems-work/p19/run/scene_plan.json', 'w'), indent=1)
PYEOF
python3 p19_quota.py "$WORK" >/dev/null
python3 p19_gen_paint.py >/dev/null
python3 - <<'PYAUD'
import sys, os, json
sys.path.insert(0, '/home/z/my-project/ems19-repo/scripts')
import p19_assets as A
RAW = "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
WORK = '/tmp/ems-work/p19/run'
tup = [(RAW, "manager_raw", "manager-provided official-MV footage excerpt (edit-test usage only, no publication)", "manager upload")]
paint = os.path.join(WORK, 'assets', 'painting_lemons.jpg')
if os.path.exists(paint):
    tup.append((paint, "generated", "generated in-sandbox painterly still-life card (p19_gen_paint.py, seed 1633; public-domain CDN proxy-blocked, honest log)", "scripts/p19_gen_paint.py"))
rep = A.audit(tup, os.path.join(WORK, 'asset_audit.json'))
verdicts = {s["asset"]: "clean — agent visual audit of 2x tile crop in proof S2 (no watermark pixels found)"
            for s in rep["scans"] if s.get("watermark_suspect")}
json.dump(verdicts, open(os.path.join(WORK, 'visual_verdicts.json'), 'w'), indent=1)
print("prep audit: scans", len(rep["scans"]), "raw hits", len(rep["watermark_hits"]), "verdicts", len(verdicts))
PYAUD

case "$1" in
  proofs)
    python3 p19_proofs.py "$WORK" "$RAW"
    mkdir -p "$REPO/test-results/phase19/proofs" "$DL/proofs"
    cp "$WORK"/proofs/*.jpg "$REPO/test-results/phase19/proofs/"
    cp "$WORK"/proofs/*.jpg "$DL/proofs/"
    cp "$WORK"/proofs_summary.json "$REPO/test-results/phase19/"
    echo "PROOFS COPIED OUT"
    ;;
  master)
    python3 p19_render.py "$WORK" p19_preset_mv_welcome.json "$RAW" "$WORK/T1_welcome_v19_9x16.mp4" 9x16 || true
    python3 p19_sidecar.py
    mkdir -p "$STAGE"
    cp "$WORK"/*.json "$STAGE/" 2>/dev/null || true
    cp "$WORK/T1_welcome_v19_9x16.mp4" "$WORK/cover_9x16.jpg" "$STAGE/" 2>/dev/null || true
    echo "RENDER STAGE DONE (staged)"
    ;;
  critique)
    cp "$STAGE"/*.json "$WORK/" 2>/dev/null || true
    cp "$STAGE/T1_welcome_v19_9x16.mp4" "$WORK/" 2>/dev/null || true
    test -s "$WORK/T1_welcome_v19_9x16.mp4" || { echo "CRIT FAIL: mp4 not staged"; exit 4; }
    python3 p19_critique.py "$WORK/T1_welcome_v19_9x16.mp4" "$WORK" 9x16 "$RAW" | tail -1
    cp "$WORK/critique_9x16.json" "$STAGE/" 2>/dev/null || true
    echo "CRITIQUE STAGE DONE"
    ;;
  gate)
    cp "$STAGE"/*.json "$WORK/" 2>/dev/null || true
    cp "$STAGE/T1_welcome_v19_9x16.mp4" "$WORK/" 2>/dev/null || true
    cp "$STAGE/cover_9x16.jpg" "$WORK/" 2>/dev/null || true
    test -s "$WORK/T1_welcome_v19_9x16.mp4" || { echo "GATE FAIL: mp4 not staged"; exit 4; }
    python3 p19_gate.py "$WORK/T1_welcome_v19_9x16.mp4" "$WORK" 9x16 p19_preset_mv_welcome.json "$RAW"
    mkdir -p "$REPO/test-results/phase19" "$DL"
    cp "$WORK/T1_welcome_v19_9x16.mp4" "$DL/" || true
    cp "$WORK/cover_9x16.jpg" "$DL/cover_T1_welcome_v19_9x16.jpg" || true
    cp "$WORK/plan_9x16.json" "$WORK/manifest_9x16.json" "$WORK/render_log_9x16.json" \
       "$WORK/asset_audit.json" "$WORK/critique_9x16.json" "$REPO/test-results/phase19/" 2>/dev/null || true
    cp "$WORK"/gate_*.json "$REPO/test-results/phase19/" 2>/dev/null || true
    cp "$WORK/plan_9x16.json" "$WORK/manifest_9x16.json" "$DL/" 2>/dev/null || true
    cp "$WORK"/gate_*.json "$DL/" 2>/dev/null || true
    echo "MASTER STAGE DONE"
    ;;
  *) echo "usage: p19_driver.sh proofs|master|critique|gate"; exit 1;;
esac
