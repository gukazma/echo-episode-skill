"""卡顿 scan of host segments as rendered: frozen picture runs (>= 5 frames ~no change) and silent holes > 0.8 s between words."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
sys.argv = ["x", "none"]
import make_episode as m
ep = Path(".").resolve()
segs = [l.split("'")[1] for l in (ep / "v1" / "concat.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
pr = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
t = pr(segs[0]); start = {}
for s, p in zip(m.SHOTS, segs[1:]): start[s["id"]] = t; t += pr(p)
mmss = lambda x: f"{int(x // 60)}:{x % 60:04.1f}"
for i, s in enumerate(m.SHOTS, 1):
    if s["id"] not in m.ACC: continue
    p = segs[i]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "scale=192:108,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 108, 192).astype(np.float32); d = np.abs(np.diff(f, axis=0)).mean((1, 2))
    fz, j = [], 0
    while j < len(d):
        if d[j] < 0.15:
            k = j
            while k < len(d) and d[k] < 0.15: k += 1
            if k - j >= 5: fz.append((round(j / 25, 2), k - j))
            j = k
        else: j += 1
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float); n = len(x) // 160; e = np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))
    sm = np.convolve(e, np.ones(5) / 5, "same"); on = np.where(sm > 0.1 * np.percentile(sm, 95))[0]
    holes = []
    if len(on): 
        q = np.diff(on); holes = [(round(on[a] / 100, 2), round(q[a] / 100, 2)) for a in np.where(q > 80)[0]]
    print(f"{mmss(start[s['id']])} {s['id']} {s['who']} dur={len(f)/25:.1f} ramp={m.RAMP_LOG.get(m.ACC[s['id']][0], '')} freeze={fz} holes={holes} | {s['line'][:30]}", flush=True)
print("FREEZE_DONE")
