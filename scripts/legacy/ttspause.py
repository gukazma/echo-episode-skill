import sys, subprocess, numpy as np
sys.argv = ["x", "none"]
import make_ep03 as m
for sid in ["011", "224", "192", "208", "225"]:
    s = next(x for x in m.SHOTS if x["id"] == sid)
    for p in (m.tts_path(s), m.voice(s)):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", "24000", "-f", "s16le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32); hop = 240; n = len(x) // hop
        db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) / 32768 + 1e-9)
        db = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(db, 4, mode="edge"), 9), axis=1)
        loud = np.where(db > -32)[0]; runs = []; j = loud[0]
        while j < loud[-1]:
            if db[j] <= -32:
                r = j
                while r < loud[-1] and db[r] <= -32: r += 1
                if r - j > 40: runs.append(round((r - j) / 100, 2))
                j = r
            else: j += 1
        print(sid, p.name[:8], round(m.probe(p), 2), runs)
