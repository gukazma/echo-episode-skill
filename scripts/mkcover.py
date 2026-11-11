"""mkcover.py <ep> <sec> <out.jpg> : 1920x1080 cover - 94版 诸葛亮 on the right, title block on the left"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
e, t, out = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f"drama/eps/e{e:02d}.mp4", "-frames:v", "1",
                      "-vf", "crop=iw-40:ih*0.665:20:ih*0.135,scale=-2:1080:flags=lanczos", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
import io
src = Image.open(io.BytesIO(raw)).convert("RGB")
if len(sys.argv) > 5 and sys.argv[5] == "flip": src = src.transpose(Image.FLIP_LEFT_RIGHT)
src = ImageEnhance.Contrast(ImageEnhance.Color(src).enhance(0.85)).enhance(1.08)
W, H = 1920, 1080
bg = Image.new("RGB", (W, H), (12, 10, 8))
x0 = int(sys.argv[4]) if len(sys.argv) > 4 else 520
bg.paste(src, (x0, 0))
# left fade to dark + warm grade + vignette
grad = Image.new("L", (W, H)); gd = ImageDraw.Draw(grad)
for x in range(W):
    a = 255 if x < x0 + 260 else max(0, int(255 * (1 - (x - x0 - 260) / 560)))
    gd.line([(x, 0), (x, H)], fill=a)
dark = Image.new("RGB", (W, H), (14, 11, 8))
bg = Image.composite(dark, bg, grad.filter(ImageFilter.GaussianBlur(40)))
warm = Image.new("RGB", (W, H), (60, 36, 10)); bg = Image.blend(bg, warm, 0.12)
vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-300, -250, W + 300, H + 250], fill=255)
bg = Image.composite(bg, Image.new("RGB", (W, H), (0, 0, 0)), vig.filter(ImageFilter.GaussianBlur(160)))
d = ImageDraw.Draw(bg)
F = "C:/Windows/Fonts/"
kai, hei, yh = F + "simkai.ttf", F + "simhei.ttf", F + "msyhbd.ttc"
gold, cream = (232, 190, 110), (240, 230, 210)
def text(xy, s, font, fill, sh=6, **kw):
    d.text((xy[0] + sh, xy[1] + sh), s, font=font, fill=(0, 0, 0), **kw); d.text(xy, s, font=font, fill=fill, **kw)
text((120, 96), "回声号 · 第 2 期", ImageFont.truetype(yh, 44), (200, 170, 120), sh=3)
d.line([(124, 168), (520, 168)], fill=(160, 120, 60), width=3)
text((104, 250), "一诺千年", ImageFont.truetype(kai, 230), gold, sh=8, stroke_width=3, stroke_fill=(70, 40, 10))
text((128, 540), "真实的诸葛亮", ImageFont.truetype(hei, 92), cream, sh=5)
text((132, 690), "他没有借过东风，也没有唱过空城计", ImageFont.truetype(yh, 44), (205, 195, 180), sh=3)
text((132, 752), "他只是守住了一句承诺 —— 二十七年", ImageFont.truetype(yh, 44), (205, 195, 180), sh=3)
bg.save(out, quality=94); print(out, src.size)
