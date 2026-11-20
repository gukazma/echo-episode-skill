import json, subprocess, sys
import numpy as np
qc = json.load(open("studio/qc.json", encoding="utf-8"))
def rms(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float); n = len(x) // 160
    return np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))
for arg in sys.argv[1:]:
    k, s, t = arg.split(":"); s, t = float(s), float(t)
    e = rms(f"studio/clips/{k}.mp4"); q = qc[k]; a, b = q["speech"][0], q["speech"][1]
    peak = np.percentile(e[int(a * 100):int(b * 100)], 95)
    seg = e[int(s * 100):int(t * 100)] / peak
    print(k, s, t, "rel min/med/max", seg.min().round(3), np.median(seg).round(3), seg.max().round(3), "|", " ".join(f"{v:.2f}" for v in seg[::10]))
