"""python strip.py footage/<key>.mp4 <from_s> <to_s> <n_frames> sheets/<out>.jpg -> timestamped contact strip (6 per row)"""
import io, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
src, a, b, n, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
ts = [a + (b - a) * i / (n - 1) for i in range(n)]; tiles = []
for t in ts:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", "scale=320:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    im = Image.open(io.BytesIO(raw)).convert("RGB"); ImageDraw.Draw(im).text((4, 4), f"{t:.1f}", fill=(255, 255, 0), font=ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 22)); tiles.append(im)
c = 6; w, h = tiles[0].size; s = Image.new("RGB", (w * c, h * ((len(tiles) + c - 1) // c)))
for i, im in enumerate(tiles): s.paste(im, ((i % c) * w, (i // c) * h))
s.save(out, quality=85)
