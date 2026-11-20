"""Mid-line pauses of Seedance takes (70 ms median RMS < 12 % of speech peak, runs > 0.5 s between first and last speech)."""
import json, subprocess, sys
import numpy as np
qc = json.load(open("studio/qc.json", encoding="utf-8"))
for k in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"studio/clips/{k}.mp4", "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float); n = len(x) // 160
    e = np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))
    a, b = qc[k]["speech"]; peak = np.percentile(e[int(a * 100):int(b * 100)], 95)
    sm = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(e, 3, mode="edge"), 7), axis=1)
    loud = np.where(sm >= 0.12 * peak)[0]; q = sm < 0.12 * peak
    runs, j = [], loud[0]
    while j < loud[-1]:
        if q[j]:
            r = j
            while r < loud[-1] and q[r]: r += 1
            if r - j > 50: runs.append((round(j / 100, 2), round((r - j) / 100, 2)))
            j = r
        else: j += 1
    print(k, "speech", round((loud[-1] - loud[0]) / 100, 2), "pauses", runs, "max", max([p for _, p in runs], default=0))
