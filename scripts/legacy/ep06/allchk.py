import sys, subprocess, numpy as np
sys.argv = ["make_ep06.py"]
import make_ep06 as M
bad = 0
for s in M.SHOTS:
    if not s["line"] or s["who"] == "无":
        continue
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(M.tts_path(s)), "-f", "s16le", "-ac", "1", "-ar", "24000", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32)
    hop = 240; n = len(x) // hop
    e = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) / 32768 + 1e-9)
    v = np.where(e > -30)[0]
    gap = (n - v[-1]) / 100 if len(v) else 0
    if gap < 0.5:  # 0.25 s decay + 0.3 s pad expected; less = the voice ran to the end of the take
        bad += 1; print("TAIL?", s["id"], f"{gap:.2f}s", s["line"][-8:], flush=True)
print("ALLCHK done, suspicious:", bad, flush=True)
