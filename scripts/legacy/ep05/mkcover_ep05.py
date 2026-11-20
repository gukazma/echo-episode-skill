"""cover 1920x1080: Jensen Huang on stage in the leather jacket (Computex 2024, 323 s, gold light) right, title left."""
import io, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
ep = Path(__file__).resolve().parent
def grab(key, t, vf):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(ep / "footage" / f"{key}.mp4"), "-frames:v", "1", "-vf", vf,
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(raw)).convert("RGB")
W, H = 1920, 1080
pic = grab("computex2024", 323, "crop=iw*0.62:ih:iw*0.36:0,scale=-2:1080:flags=lanczos")
pic = ImageEnhance.Sharpness(pic).enhance(1.4)
bg = Image.new("RGB", (W, H), (14, 11, 9))
bg.paste(pic, (W - pic.width, 0))
mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
x0 = W - pic.width
for x in range(W):
    a = 1 - min(1, max(0, (x - x0) / 360))  # dark on the left, fading into the picture
    dm.line([(x, 0), (x, H)], fill=int(255 * a))
bg = Image.composite(Image.new("RGB", (W, H), (14, 11, 9)), bg, mask.filter(ImageFilter.GaussianBlur(30)))
bg = Image.blend(bg, Image.new("RGB", (W, H), (70, 40, 20)), 0.10)
d = ImageDraw.Draw(bg)
F = "C:/Windows/Fonts/"
kai = ImageFont.truetype(F + "simkai.ttf", 150); sub = ImageFont.truetype(F + "msyhbd.ttc", 56); sub2 = ImageFont.truetype(F + "msyh.ttc", 40)
tag = ImageFont.truetype(F + "msyhbd.ttc", 34)
gold, cream = (236, 196, 120), (242, 232, 214)
def tx(x, y, s, f, fill):
    d.text((x + 5, y + 5), s, font=f, fill=(0, 0, 0)); d.text((x, y), s, font=f, fill=fill)
tx(90, 270, "离倒闭只有", kai, gold)
tx(90, 430, "三十天", kai, gold)
tx(112, 640, "黄仁勋", sub, cream)
tx(114, 730, "九岁扫厕所，十五岁洗碗，", sub2, (225, 214, 196))
tx(114, 790, "三十岁在餐馆卡座里开了一家公司", sub2, (225, 214, 196))
tx(120, 960, "回声号 · 第五期", tag, (200, 190, 170))
(ep / "cover").mkdir(exist_ok=True)
bg.save(ep / "cover" / "EP05_cover.jpg", quality=93)
print("COVER_OK")
