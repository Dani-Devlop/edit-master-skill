#!/usr/bin/env python3
"""Phase 11.1 Step 0 ingest probe.
- Sample VIDEO1 (4fps) and VIDEO2 (8fps) end-to-end.
- 30fps per-frame metrics: luma, inter-frame absdiff, channel means (invert detection).
- Build montage sheets for visual technique tables.
Outputs -> /home/z/my-project/refwork/
"""
import os, subprocess, json
import numpy as np
from PIL import Image

ROOT = "/home/z/my-project/refwork"
UP = "/home/z/my-project/upload"

VIDEOS = {
    "VIDEO1": (f"{UP}/4_5914418752572623746.mp4", 4.0),   # white-bg Raw/Edited reel, 28.07s
    "VIDEO2": (f"{UP}/VID_20261121_000716_199.mp4", 8.0), # 4-quadrant families reel, 6.77s
}

os.makedirs(ROOT, exist_ok=True)

# 1) frame extraction
for name, (path, fps) in VIDEOS.items():
    d = f"{ROOT}/{name}"
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.startswith("f_"):
            os.remove(os.path.join(d, f))
    subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps}",
                    "-q:v", "2", f"{d}/f_%04d.jpg"], check=True)
    n = len([f for f in os.listdir(d) if f.startswith("f_")])
    print(name, "frames", n, "at", fps, "fps", flush=True)

# 2) 30fps metrics via rawvideo pipe
def metrics(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,nb_frames,avg_frame_rate",
           "-of", "json", path]
    st = json.loads(subprocess.check_output(cmd))["streams"][0]
    W, H, fpsn = st["width"], st["height"], st["avg_frame_rate"]
    num, den = map(int, fpsn.split("/"))
    fps = num / den
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=180:320",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    SW, SH = 180, 320
    fsz = SW * SH * 3
    fps_out = []
    prev = None
    i = 0
    while True:
        buf = proc.stdout.read(fsz)
        if len(buf) < fsz:
            break
        fr = np.frombuffer(buf, dtype=np.uint8).reshape(SH, SW, 3).astype(np.float32)
        luma = float((0.2126*fr[:,:,0] + 0.7152*fr[:,:,1] + 0.0722*fr[:,:,2]).mean())
        r, g, b = float(fr[:,:,0].mean()), float(fr[:,:,1].mean()), float(fr[:,:,2].mean())
        diff = 0.0 if prev is None else float(np.abs(fr - prev).mean())
        fps_out.append(dict(i=i, t=round(i/fps, 3), luma=round(luma,1), diff=round(diff,1),
                            r=round(r,1), g=round(g,1), b=round(b,1)))
        prev = fr
        i += 1
    proc.wait()
    return dict(w=W, h=H, fps=round(fps,3), n=i, frames=fps_out)

report = {}
for name, (path, _) in VIDEOS.items():
    report[name] = metrics(path)
    m = report[name]
    fr = m["frames"]
    # event candidates
    diffs = np.array([f["diff"] for f in fr])
    thr = diffs.mean() + 2.5 * diffs.std()
    spikes = [(f["t"], f["diff"]) for f, d in zip(fr, diffs) if d >= thr]
    # invert candidates: large luma drop+rebound within 0.5s (negative bite)
    lumas = np.array([f["luma"] for f in fr])
    invs = []
    for i in range(1, len(lumas)):
        if lumas[i] < lumas[i-1] - 35 and i+3 < len(lumas) and lumas[min(i+3,len(lumas)-1)] > lumas[i] + 25:
            invs.append(round(i / m["fps"], 3))
    report[name]["whip_candidates"] = [f"{t:.2f}s diff={d:.0f}" for t, d in spikes[:40]]
    report[name]["invert_candidates_s"] = invs[:12]
    print(name, "spikes:", len(spikes), "invert cand:", invs[:12], flush=True)

json.dump(report, open(f"{ROOT}/metrics30.json", "w"), indent=1)

# 3) montages
def montage(src_dir, cols, thumb_w, out, per_sheet):
    files = sorted(f for f in os.listdir(src_dir) if f.startswith("f_"))
    tw, th = thumb_w, int(thumb_w * 16 / 9)
    sheets = [files[i:i+per_sheet] for i in range(0, len(files), per_sheet)]
    for si, chunk in enumerate(sheets, 1):
        rows = (len(chunk) + cols - 1) // cols
        pad = 6
        W = cols * (tw + pad) + pad
        H = rows * (th + pad) + pad
        sheet = Image.new("RGB", (W, H), (24, 24, 24))
        for k, fn in enumerate(chunk):
            im = Image.open(f"{src_dir}/{fn}").resize((tw, th))
            x = pad + (k % cols) * (tw + pad)
            y = pad + (k // cols) * (th + pad)
            sheet.paste(im, (x, y))
            # timestamp label
            idx = int(fn[2:6])
            t = (idx - 1) * (1/ (4.0 if "VIDEO1" in src_dir else 8.0))
            from PIL import ImageDraw
            d = ImageDraw.Draw(sheet)
            d.text((x+4, y+4), f"{idx-1} @{t:.2f}s", fill=(255, 255, 0))
        sheet.save(f"{ROOT}/{out}_{si}.jpg", quality=82)
        print("sheet", f"{out}_{si}.jpg", sheet.size, flush=True)

montage(f"{ROOT}/VIDEO1", 7, 190, "sheet_V1", 28)
montage(f"{ROOT}/VIDEO2", 6, 190, "sheet_V2", 18)
print("DONE", flush=True)
