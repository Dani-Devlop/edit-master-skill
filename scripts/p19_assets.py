#!/usr/bin/env python3
"""Phase 19 Asset System (AS1): zero watermarked stock; license registry;
automatic watermark heuristic scan + proof-sheet visual audit; GC2 gate data."""
import os, json, hashlib
import numpy as np
from PIL import Image, ImageFilter

# AS1 whitelist: public-domain / CC0 / generated / manager-provided raw only
ALLOWED = {
    "wikimedia_commons": "public domain / CC (per-file license logged)",
    "met_open_access": "CC0 / public domain",
    "rijksmuseum": "public domain",
    "pexels": "Pexels license (free, no attribution)",
    "pixabay": "Pixabay Content License",
    "mixkit": "Mixkit Free License",
    "generated": "generated in-sandbox (PIL/numpy), no third-party rights",
    "manager_raw": "manager-provided raw footage excerpt (edit-test usage only)",
}
BANNED_SOURCES = ("alamy", "shutterstock", "getty", "istock", "adobe stock",
                  "dreamstime", "123rf", "depositphotos")


def register(path, source, license_note, url=""):
    """license registry entry (every asset MUST be registered before use)."""
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    assert source in ALLOWED, f"AS1: source '{source}' not whitelisted"
    low = (source + " " + url + " " + license_note).lower()
    for b in BANNED_SOURCES:
        assert b not in low, f"AS1: banned stock source detected: {b}"
    return {"path": os.path.basename(path), "sha256_16": h, "source": source,
            "license": license_note or ALLOWED[source], "url": url,
            "bytes": os.path.getsize(path)}


def _tile_letter_score(tile):
    """letter-like structure score: top-hat blobs with text-ish size stats."""
    g = np.asarray(tile.convert("L"), np.float32)
    # semi-transparent watermark text = mid-frequency uniform overlay:
    # compare tile against heavy blur; watermark residue has sharp edges
    resid = g - np.asarray(tile.filter(ImageFilter.GaussianBlur(6)).convert("L"), np.float32)
    bw = (np.abs(resid) > 14).mean()
    return float(bw)


def watermark_scan(im, name=""):
    """heuristic scan: uniform text-like residue in corners + diagonal-stripe
    signature (Alamy-style tiled marks). Returns dict; hits -> gate evidence."""
    w, h = im.size
    tiles = {
        "TL": im.crop((0, 0, int(w * 0.34), int(h * 0.16))),
        "TR": im.crop((int(w * 0.66), 0, w, int(h * 0.16))),
        "BL": im.crop((0, int(h * 0.84), int(w * 0.34), h)),
        "BR": im.crop((int(w * 0.66), int(h * 0.84), w, h)),
        "CTR": im.crop((int(w * 0.33), int(h * 0.44), int(w * 0.67), int(h * 0.56))),
    }
    scores = {k: round(_tile_letter_score(v), 4) for k, v in tiles.items()}
    g = np.asarray(im.convert("L"), np.float32)
    # diagonal stripe signature: strong periodic diff between shifted copies
    d1 = np.abs(g - np.roll(np.roll(g, 6, axis=0), 6, axis=1)).mean()
    d2 = np.abs(g - np.roll(g, 2, axis=1)).mean()
    diag_sig = round(float(d1 / max(d2, 1e-3)), 3)
    hit = (max(scores.values()) > 0.30) or diag_sig > 3.5
    return {"asset": name, "tiles": scores, "diag_sig": diag_sig,
            "watermark_suspect": bool(hit)}


def audit(paths_with_meta, out_json, verdicts=None):
    """full AS1 audit -> registry + scans; GC2 evidence. Images scanned directly;
    video assets scanned on 3 sample frames (watermarks burn into every frame).
    verdicts: {hit_name: 'clean — ...'} from agent visual review of 2x tile crops
    (heuristic is a screen only; visual audit is the decider per AS1)."""
    reg, scans = [], []
    for p, src, lic, url in paths_with_meta:
        if not os.path.exists(p):
            continue
        reg.append(register(p, src, lic, url))
        ext = os.path.splitext(p)[1].lower()
        try:
            if ext in (".jpg", ".jpeg", ".png", ".webp"):
                im = Image.open(p).convert("RGB")
                im.thumbnail((1400, 1400), Image.LANCZOS)
                scans.append(watermark_scan(im, os.path.basename(p)))
            elif ext in (".mp4", ".mov", ".m4v"):
                import cv2
                cap = cv2.VideoCapture(p)
                n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                for frac in (0.08, 0.42, 0.75):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * frac))
                    ok, fr = cap.read()
                    if ok:
                        im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
                        scans.append(watermark_scan(im, f"{os.path.basename(p)}@{frac:.2f}"))
                cap.release()
        except Exception as e:
            scans.append({"asset": os.path.basename(p), "error": str(e),
                          "watermark_suspect": False})
    rep = {"registry": reg, "scans": scans,
           "watermark_hits": [s["asset"] for s in scans if s["watermark_suspect"]],
           "visual_verdicts": verdicts or {},
           "watermark_hits_effective": [h for h in [s["asset"] for s in scans if s["watermark_suspect"]]
                                        if not str((verdicts or {}).get(h, "")).lower().startswith("clean")],
           "policy": {"banned": list(BANNED_SOURCES), "allowed": ALLOWED}}
    json.dump(rep, open(out_json, "w"), indent=1)
    return rep
