import io, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
keys, out = sys.argv[2:], sys.argv[1]; rows = []
pr = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
fnt = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 20)
for k in keys:
    p = f"studio/clips/{k}.mp4"; d = pr(p); tiles = []
    for i in range(10):
        t = d * (i + 0.5) / 10
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-vf", "scale=240:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        im = Image.open(io.BytesIO(raw)).convert("RGB"); ImageDraw.Draw(im).text((4, 2), f"{k} {t:.1f}" if i == 0 else f"{t:.1f}", fill=(255, 255, 0), font=fnt); tiles.append(im)
    w, h = tiles[0].size; r = Image.new("RGB", (w * 10, h))
    for i, im in enumerate(tiles): r.paste(im, (i * w, 0))
    rows.append(r)
s = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows: s.paste(r, (0, y)); y += r.height
s.save(out, quality=85); print("STRIP_OK")
