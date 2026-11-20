"""Per-frame motion (mean abs diff of consecutive grey frames, whole + centre) + RMS for a clip window; prints 0.1 s rows."""
import subprocess, sys
import numpy as np
f, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W, H = 320, 180
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", f, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(float)
pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
n, d = pr.split("/"); fps = float(n) / float(d)
au = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", f, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
x = np.frombuffer(au, np.int16).astype(float)
print("fps", fps, "frames", len(fr))
dif = np.abs(np.diff(fr, axis=0)).mean((1, 2))
for i, v in enumerate(dif):
    t = a + (i + 1) / fps
    s = int((i + 1) / fps * 16000); r = np.sqrt((x[s:s + 1600] ** 2).mean()) if s < len(x) else 0
    print(f"{t:6.2f} diff {v:6.3f} {'#' * int(min(60, v * 20))}  rms {int(r):5d}")
