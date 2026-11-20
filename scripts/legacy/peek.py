"""peek.py <src(ep number or path)> <t0> <t1> <step> <out.jpg>  -> grid of frames with timestamps"""
import subprocess, sys
from PIL import Image, ImageDraw
src, t0, t1, st, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
path = f"drama/eps/e{int(src):02d}.mp4" if src.isdigit() else src
ims, t = [], t0
while t <= t1:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(raw) == 320 * 180 * 3:
        im = Image.frombytes("RGB", (320, 180), raw); d = ImageDraw.Draw(im); d.rectangle([0, 0, 58, 16], fill=(0, 0, 0)); d.text((3, 2), f"{t:.0f}", fill=(255, 255, 0)); ims.append(im)
    t += st
cols = 8; R = (len(ims) + cols - 1) // cols
g = Image.new("RGB", (320 * cols, 180 * R))
for k, im in enumerate(ims): g.paste(im, ((k % cols) * 320, (k // cols) * 180))
g.save(out, quality=70); print(out, len(ims))
