#!/usr/bin/env python3
"""Vosk word-level ASR fallback for T-1 real vox (whisper HF 429-blocked).
Outputs whisper_words.json-compatible structure. Honest method logged."""
import json, subprocess, wave, sys, os

RAW = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/upload/4_6051789922870758373 (1).mp4"
WORK = sys.argv[2] if len(sys.argv) > 2 else "/tmp/ems-work/p14run1/work/t1_mv"
MODELDIR = "/tmp/ems-work/p14run1/work/t1_mv/vosk-model-small-en-us-0.15"

wav = os.path.join(WORK, "vox_16k.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", RAW, "-ar", "16000", "-ac", "1", "-vn", wav], check=True)

from vosk import Model, KaldiRecognizer
model = Model(MODELDIR)
wf = wave.open(wav, "rb")
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)
words, segs = [], []
while True:
    data = wf.readframes(8000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        r = json.loads(rec.Result())
        if r.get("result"):
            for wd in r["result"]:
                words.append({"w": wd["word"], "start": round(wd["start"], 3),
                              "end": round(wd["end"], 3), "prob": round(wd.get("conf", 0.8), 3)})
            segs.append({"start": round(r["result"][0]["start"], 3),
                         "end": round(r["result"][-1]["end"], 3),
                         "text": " ".join(w["word"] for w in r["result"])})
fin = json.loads(rec.FinalResult())
if fin.get("result"):
    for wd in fin["result"]:
        words.append({"w": wd["word"], "start": round(wd["start"], 3),
                      "end": round(wd["end"], 3), "prob": round(wd.get("conf", 0.8), 3)})
    segs.append({"start": round(fin["result"][0]["start"], 3),
                 "end": round(fin["result"][-1]["end"], 3),
                 "text": " ".join(w["word"] for w in fin["result"])})
wf.close()

out = {"language": "en", "engine": "vosk-model-small-en-us-0.15 (fallback: faster-whisper blocked by HF HTTP 429)",
       "duration": round(len(words) and max(w["end"] for w in words) or 0, 3),
       "segments": segs, "words": words}
json.dump(out, open(os.path.join(WORK, "whisper_words.json"), "w"), indent=1)
print(f"VOSK: words={len(words)} segs={len(segs)}")
for s in segs:
    print(f"  [{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
