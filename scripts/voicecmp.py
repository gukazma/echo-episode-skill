"""Every 10 ms where the voice track has sound, the finished film must have it too (film = gain x (voice + ducked music)).
Flags frames where the film is > 12 dB quieter than the voice -> dropouts anywhere in the film (hosts and narration)."""
import subprocess, sys
import numpy as np
SR = 48000
def env(f):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vn", "-af", "pan=mono|c0=c0", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    n = len(x) // 480; return 20 * np.log10(np.sqrt((x[:n * 480].reshape(n, 480).astype(np.float64) ** 2).mean(1)) + 1e-9)
v, f = env(sys.argv[1]), env(sys.argv[2]); n = min(len(v), len(f))
v, f = v[:n], f[:n]; on = v > -40
d = f[on] - v[on]; med = float(np.median(d))
bad = np.where(on & (f - v < med - 12))[0]
runs = []
for i in bad:
    if runs and i - runs[-1][1] <= 2: runs[-1][1] = i
    else: runs.append([i, i])
runs = [r for r in runs if r[1] - r[0] >= 2]
print("voiced frames", int(on.sum()), "median film-voice dB", round(med, 2), "dropouts", len(runs), [(f"{int(a / 100 // 60)}:{a / 100 % 60:04.1f}", (b - a + 1) * 10) for a, b in runs[:30]])
