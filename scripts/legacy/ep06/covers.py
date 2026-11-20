"""Covers in 4 ratios for Bilibili / Douyin: 16:9 (1920x1080), 4:3 (1440x1080), 3:4 (1080x1440), 9:16 (1080x1920).
python covers.py cover.json   (json: src, t, focus_x [0-1 centre of the subject], title [2 lines], name, lines [2], tag, out_prefix)"""
import io, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
ep = Path.cwd()
cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(cfg["t"]), "-i", str(ep / cfg["src"]), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
frame = ImageEnhance.Sharpness(Image.open(io.BytesIO(raw)).convert("RGB")).enhance(1.3)
if cfg.get("pre_crop"):  # [x, y, w, h] fractions: drop channel logos / score bugs before any layout
    x, y, w, h = cfg["pre_crop"]; frame = frame.crop((int(x * frame.width), int(y * frame.height), int((x + w) * frame.width), int((y + h) * frame.height)))
F = "C:/Windows/Fonts/"
gold, cream, soft, bgc = (236, 196, 120), (242, 232, 214), (225, 214, 196), (14, 11, 9)

def crop_to(img, w, h, fx, fy=0.45):
    """scale to cover w x h, keep the subject (fx, fy) in frame"""
    s = max(w / img.width, h / img.height); im = img.resize((int(img.width * s + 0.5), int(img.height * s + 0.5)), Image.LANCZOS)
    x = min(max(0, int(fx * im.width - w / 2)), im.width - w); y = min(max(0, int(fy * im.height - h / 2)), im.height - h)
    return im.crop((x, y, x + w, y + h))

def text(d, x, y, s, f, fill):
    d.text((x + 5, y + 5), s, font=f, fill=(0, 0, 0)); d.text((x, y), s, font=f, fill=fill)

def side(W, H, pic_w, scale):  # picture right, title left, dark fade between
    bg = Image.new("RGB", (W, H), bgc); pic = crop_to(frame, pic_w, H, cfg["focus_x"], cfg.get("focus_y", 0.45)); x0 = W - pic_w
    bg.paste(pic, (x0, 0))
    mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
    for x in range(W): dm.line([(x, 0), (x, H)], fill=int(255 * (1 - min(1, max(0, (x - x0) / (pic_w * 0.35))))))
    bg = Image.composite(Image.new("RGB", (W, H), bgc), bg, mask.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(bg); k = scale
    kai = ImageFont.truetype(F + "simkai.ttf", int(150 * k)); nm = ImageFont.truetype(F + "msyhbd.ttc", int(56 * k)); ln = ImageFont.truetype(F + "msyh.ttc", int(40 * k)); tg = ImageFont.truetype(F + "msyhbd.ttc", int(34 * k))
    text(d, int(90 * k), int(H * 0.25), cfg["title"][0], kai, gold); text(d, int(90 * k), int(H * 0.25 + 160 * k), cfg["title"][1], kai, gold)
    text(d, int(112 * k), int(H * 0.59), cfg["name"], nm, cream)
    for i, l in enumerate(cfg["lines"]): text(d, int(114 * k), int(H * 0.675 + i * 60 * k), l, ln, soft)
    text(d, int(120 * k), int(H * 0.9), cfg["tag"], tg, (200, 190, 170))
    return bg

def tall(W, H, frac):  # picture top, title bottom
    pic_h = int(H * frac); bg = Image.new("RGB", (W, H), bgc); bg.paste(crop_to(frame, W, pic_h, cfg["focus_x"], cfg.get("focus_y", 0.45)), (0, 0))
    mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
    for y in range(H): dm.line([(0, y), (W, y)], fill=int(255 * min(1, max(0, (y - pic_h * 0.72) / (pic_h * 0.3)))))
    bg = Image.composite(Image.new("RGB", (W, H), bgc), bg, mask.filter(ImageFilter.GaussianBlur(25)))
    d = ImageDraw.Draw(bg); k = W / 1080
    kai = ImageFont.truetype(F + "simkai.ttf", int(140 * k)); nm = ImageFont.truetype(F + "msyhbd.ttc", int(58 * k)); ln = ImageFont.truetype(F + "msyh.ttc", int(42 * k)); tg = ImageFont.truetype(F + "msyhbd.ttc", int(34 * k))
    y = pic_h - int(60 * k)
    for t in cfg["title"]:
        tw = d.textlength(t, font=kai); text(d, int((W - tw) / 2), y, t, kai, gold); y += int(150 * k)
    tw = d.textlength(cfg["name"], font=nm); text(d, int((W - tw) / 2), y + int(20 * k), cfg["name"], nm, cream); y += int(110 * k)
    for l in cfg["lines"]:
        tw = d.textlength(l, font=ln); text(d, int((W - tw) / 2), y, l, ln, soft); y += int(60 * k)
    tw = d.textlength(cfg["tag"], font=tg); text(d, int((W - tw) / 2), max(y + int(30 * k), H - int(90 * k)), cfg["tag"], tg, (200, 190, 170))
    return bg

out = ep / "cover"; out.mkdir(exist_ok=True); p = cfg["out_prefix"]
side(1920, 1080, 1100, 1.0).save(out / f"{p}_16x9.jpg", quality=93)
side(1440, 1080, 700, 0.78).save(out / f"{p}_4x3.jpg", quality=93)
tall(1080, 1440, 0.52).save(out / f"{p}_3x4.jpg", quality=93)
tall(1080, 1920, 0.62).save(out / f"{p}_9x16.jpg", quality=93)
print("COVERS_OK", p)
