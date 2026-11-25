#!/usr/bin/env python3
"""r21 method-swap: extract per-quadrant state crops from the reel at full res.
Each quadrant state = one PNG in p22work/assets/reel_states/. These crops are
the FOOTAGE LAYER of the replica (R0: footage is one layer); all timing,
entrances, gutters, badge, karaoke chip, camera and grain stay code-driven."""
import subprocess, os
REEL = "/home/z/my-project/upload/VID_20261121_000716_199.mp4"
OUT = "/home/z/my-project/p22work/assets/reel_states"
os.makedirs(OUT, exist_ok=True)
# quadrant boxes in full-res 720x1280 (from thumb geometry x2.667, minus gutter)
Q = {
    0: (6, 4, 350, 626),      # TL
    1: (370, 4, 714, 626),    # TR
    2: (6, 654, 350, 1276),   # BL
    3: (370, 654, 714, 1276), # BR
}
# state -> reel-clock grab time (span midpoint + settle)
GRAB = {
    0: {"a": 1.5, "b": 3.7, "c": 4.55, "d": 5.9},                 # TL
    1: {"a": 1.0, "b": 2.5, "b2": 3.2, "c": 4.4, "d": 6.3},       # TR
    2: {"a": 1.2, "b": 2.9, "c": 3.9, "d": 4.65, "e": 5.3, "f": 6.2},  # BL
    3: {"a": 2.0, "b": 4.6},                                      # BR
}
for q, states in GRAB.items():
    x0, y0, x1, y1 = Q[q]
    for key, t in states.items():
        p = f"{OUT}/q{q}_{key}.png"
        vf = f"crop={x1-x0}:{y1-y0}:{x0}:{y0},scale=520:936"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", REEL,
                        "-frames:v", "1", "-vf", vf, p], check=True)
        print("wrote", p)
print("DONE")
