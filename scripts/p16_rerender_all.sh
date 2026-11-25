#!/bin/bash
# Phase 16.0 full re-render + re-critique + re-gate with fixed engine
# (whip edge-clamp, texture lattice detector, loudness harness, stakes accent-relative)
W=/home/z/my-project/p16_work
P=/tmp/ems-repo/presets
S=/home/z/my-project/p16_staging
SCR=/home/z/my-project/scripts
MVRAW="/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
MODE=$1  # render | gate

render_one() { # dir preset raw out variant
  local d=$1 pre=$2 raw=$3 out=$4 var=$5
  cd "$d" || return 1
  echo "[RENDER] $out [$var] start $(date +%H:%M:%S)"
  rm -f "./$out"
  timeout 580 python3 $SCR/p16_render.py "$d" $P/$pre.json "$raw" "./$out" "$var" 2>&1 | grep -E "RENDER DONE|Error|error" | head -2
  echo "[RENDER] $out done $(date +%H:%M:%S)"
}

gate_one() { # dir preset raw out variant
  local d=$1 pre=$2 raw=$3 out=$4 var=$5
  cd "$d" || return 1
  echo "[GATE] $out [$var] critique $(date +%H:%M:%S)"
  timeout 400 python3 $SCR/p16_critique.py "./$out" "$d" "$var" "$raw" 2>/dev/null | tail -1 | head -c 220; echo
  timeout 500 python3 $SCR/p16_gate.py "./$out" "$d" "$var" $P/$pre.json "$raw" 2>/dev/null | tail -1
  cp "./critique_$var.json" $S/ 2>/dev/null
  cp "./scoresheet_$var.jpg" $S/ 2>/dev/null
  cp ./gate_*.json $S/ 2>/dev/null
  cp "./cover_$var.jpg" $S/ 2>/dev/null
  cp "./plan_$var.json" $S/ 2>/dev/null
  cp "./manifest_$var.json" $S/ 2>/dev/null
  cp "./$out" $S/ 2>/dev/null
  echo "[GATE] $out done $(date +%H:%M:%S)"
}

if [ "$MODE" = "render" ]; then
  render_one $W/runs/T_food_v16    food_fresh      $W/raws/food_raw.mp4    food_fresh_v16_9x16.mp4    9x16
  render_one $W/runs/T_cars_v16    cars_nightdrive $W/raws/cars_raw.mp4    cars_nightdrive_v16_9x16.mp4 9x16
  render_one $W/runs/T_pets_v16    pets_playful    $W/raws/pets_raw.mp4    pets_zoomies_v16_9x16.mp4  9x16
  render_one $W/runs/T_fitness_v16 fitness_energy  $W/raws/fitness_raw.mp4 fitness_leap_v16_9x16.mp4  9x16
  render_one $W/runs/T1_mv_darkmono_v16 mv_darkmono "$MVRAW" mv_darkmono_v16_9x16.mp4 9x16
  render_one $W/runs/T1_mv_darkmono_v16 mv_darkmono "$MVRAW" mv_darkmono_v16_4x5.mp4 4x5
  render_one $W/runs/T1_mv_darkmono_v16 mv_darkmono "$MVRAW" mv_darkmono_v16_1x1.mp4 1x1
  echo "RENDER ALL DONE"
fi
if [ "$MODE" = "gate" ]; then
  gate_one $W/runs/T_food_v16    food_fresh      $W/raws/food_raw.mp4    food_fresh_v16_9x16.mp4    9x16
  gate_one $W/runs/T_cars_v16    cars_nightdrive $W/raws/cars_raw.mp4    cars_nightdrive_v16_9x16.mp4 9x16
  gate_one $W/runs/T_pets_v16    pets_playful    $W/raws/pets_raw.mp4    pets_zoomies_v16_9x16.mp4  9x16
  gate_one $W/runs/T_fitness_v16 fitness_energy  $W/raws/fitness_raw.mp4 fitness_leap_v16_9x16.mp4  9x16
  gate_one $W/runs/T1_mv_darkmono_v16 mv_darkmono "$MVRAW" mv_darkmono_v16_9x16.mp4 9x16
  gate_one $W/runs/T1_mv_darkmono_v16 mv_darkmono "$MVRAW" mv_darkmono_v16_4x5.mp4 4x5
  gate_one $W/runs/T1_mv_darkmono_v16 mv_darkmono "$MVRAW" mv_darkmono_v16_1x1.mp4 1x1
  echo "GATE ALL DONE"
fi
