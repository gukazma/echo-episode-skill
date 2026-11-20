import os, sys, subprocess
import numpy as np
ids = sys.argv[1:]; sys.argv = ["x", "none"]
import make_episode as m
def runs(p, fps=25):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", "scale=192:108,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 108, 192).astype(np.float32); d = np.abs(np.diff(f, axis=0)).mean((1, 2))
    out, j = [], 0
    while j < len(d):
        if d[j] < 0.15:
            q = j
            while q < len(d) and d[q] < 0.15: q += 1
            if q - j >= 3: out.append((round(j / fps, 2), q - j))
            j = q
        else: j += 1
    return len(f), out
for sid in ids:
    i, s = next((i, s) for i, s in enumerate(m.SHOTS, 1) if s["id"] == sid)
    for ramp, conf in (("0", "0"), ("0", "1"), ("1", "1")):
        os.environ["RAMP"], os.environ["CONFORM"] = ramp, conf
        p, d = m.studio_segment(i, s)
        n, r = runs(p)
        print(sid, m.ACC[sid], f"RAMP={ramp} CONFORM={conf}", f"dur {d:.2f} frames {n}", "stalls", r, flush=True)
