"""specat.py out.png file:t0 [file:t0 ...] -> stacked 1.2 s spectrograms + waveform envelope (to compare stages at the same moment)"""
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
SR = 48000; rows = []
for spec in sys.argv[2:]:
    p, t0 = spec.rsplit(":", 1); t0 = float(t0)
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t0 - 0.6):.3f}", "-t", "1.2", "-i", p, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    win, hop = 1024, 96
    fr = [np.abs(np.fft.rfft(x[i:i + win] * np.hanning(win)))[:256] for i in range(0, len(x) - win, hop)]
    S = 20 * np.log10(np.array(fr).T + 1e-6); S = np.clip((S + 20) / 90, 0, 1)[::-1]
    im = Image.fromarray((S * 255).astype(np.uint8)).resize((900, 200)).convert("RGB")
    wv = Image.new("RGB", (900, 80)); d = ImageDraw.Draw(wv); n = len(x)
    for c in range(900):
        seg = x[c * n // 900:(c + 1) * n // 900]
        if len(seg): a = float(np.abs(seg).max()); d.line([(c, 40 - a * 40), (c, 40 + a * 40)], fill=(255, 80, 80) if a > 0.98 else (120, 220, 120))
    ImageDraw.Draw(im).text((4, 2), spec[-40:], fill=(255, 255, 0))
    rows += [im, wv]
out = Image.new("RGB", (900, sum(r.height for r in rows))); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(sys.argv[1]); print("SPEC_OK")
