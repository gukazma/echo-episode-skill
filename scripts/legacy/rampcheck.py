"""For each host segment: per-frame motion p95/max over the whole segment vs the original take's talking p95; ASR text; A/V duration."""
import subprocess, sys, json
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cuda", compute_type="float16")
def mot(f):
    vr = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", "scale=160:90,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(vr, np.uint8).reshape(-1, 90, 160).astype(float)
    return np.abs(np.diff(fr, axis=0)).mean((1, 2))
for pair in sys.argv[1:]:
    seg, take = pair.split("=")
    a, b = mot(seg), mot(f"studio/clips/{take}.mp4")
    txt = "".join(s.text for s in m.transcribe(seg, language="zh", beam_size=5, initial_prompt="以下是普通话句子。")[0])
    top = np.argsort(a)[-2:][::-1]
    print(f"{take}: seg p95 {np.percentile(a,95):.2f} max {a.max():.2f} @ {[round((i+1)/25,2) for i in top]} | take p95 {np.percentile(b,95):.2f} max {b.max():.2f} | {txt}", flush=True)
