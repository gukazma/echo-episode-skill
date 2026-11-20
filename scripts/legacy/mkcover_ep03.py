"""preview cover 1920x1080: Roh (2002 speech) left, Moon (2017 memorial) right, title centre."""
import io, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
ep = Path(__file__).resolve().parent
def grab(key, t, crop):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(ep / "footage" / f"{key}.mp4"), "-frames:v", "1", "-vf", crop,
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB")
W, H = 1920, 1080
roh = grab("bexco2002", 28, "crop=ih*0.70*0.89:ih*0.70:iw*0.36:ih*0.02,scale=960:1080")
moon = grab("memorial2017", 395, "crop=ih*0.62*0.89:ih*0.62:iw*0.30:ih*0.08,scale=960:1080")
bg = Image.new("RGB", (W, H), (10, 9, 8))
bg.paste(roh, (0, 0)); bg.paste(moon, (960, 0))
bg = ImageEnhance.Color(bg).enhance(0.8)
mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
for x in range(W):
    c = abs(x - W / 2) / (W / 2)
    dm.line([(x, 0), (x, H)], fill=int(235 * max(0, 1 - c * 2.2)))
bg = Image.composite(Image.new("RGB", (W, H), (12, 10, 8)), bg, mask.filter(ImageFilter.GaussianBlur(40)))
bg = Image.blend(bg, Image.new("RGB", (W, H), (60, 38, 12)), 0.10)
d = ImageDraw.Draw(bg)
F = "C:/Windows/Fonts/"
kai = ImageFont.truetype(F + "simkai.ttf", 150); sub = ImageFont.truetype(F + "msyhbd.ttc", 52); tag = ImageFont.truetype(F + "msyhbd.ttc", 36)
gold, cream = (236, 196, 120), (242, 232, 214)
def ct(y, s, f, fill):
    w = d.textlength(s, font=f); d.text(((W - w) / 2 + 5, y + 5), s, font=f, fill=(0, 0, 0)); d.text(((W - w) / 2, y), s, font=f, fill=fill)
ct(250, "愿为江水", kai, gold)
ct(430, "与君重逢", kai, gold)
ct(640, "文在寅与卢武铉", sub, cream)
ct(960, "回声号 · 第三期", tag, (200, 190, 170))
(ep / "cover").mkdir(exist_ok=True)
bg.save(ep / "cover" / "EP03_cover.jpg", quality=93)
print("COVER_OK")
