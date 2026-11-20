"""Whole-film scan for inserted digital-silence holes (30-400 ms of near-zero samples with sound on both sides) and sample jumps."""
import subprocess, sys
import numpy as np
SR = 48000
for f in sys.argv[1:]:
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vn", "-af", "pan=mono|c0=c0", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    hop = 48; n = len(x) // hop; pk = np.abs(x[:n * hop]).reshape(n, hop).max(1)  # 1 ms peaks
    z = pk < 10 ** (float(__import__("os").environ.get("HOLE_DB", "-75")) / 20); holes = []; i = 0
    while i < n:
        if z[i]:
            j = i
            while j < n and z[j]: j += 1
            if 30 <= j - i <= 400 and pk[max(0, i - 20):i].max(initial=0) > 0.01 and pk[j:j + 20].max(initial=0) > 0.01:
                holes.append((round(i / 1000, 2), j - i))
            i = j
        else: i += 1
    print(f, "holes", len(holes), [(f"{int(t // 60)}:{t % 60:04.1f}", ms) for t, ms in holes[:40]], flush=True)
