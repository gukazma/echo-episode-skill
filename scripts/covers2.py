"""Series covers in 4 ratios (16:9 1920x1080, 4:3 1440x1080, 3:4 1080x1440, 9:16 1080x1920), EP06 look.
python covers2.py epNN.json
json: out_dir, out_prefix, frames:[{src, t, vf?, flip?, fx, fy}] (1 frame, or 2 tiled side by side),
      title:[1-2 lines], name, lines:[0-2], tag"""
import io, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
F = "C:/Windows/Fonts/"
gold, cream, soft, bgc = (236, 196, 120), (242, 232, 214), (225, 214, 196), (14, 11, 9)

def grab(fr):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(fr["t"]), "-i", fr["src"], "-frames:v", "1"]
    if fr.get("vf"): cmd += ["-vf", fr["vf"]]
    raw = subprocess.run(cmd + ["-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    im = ImageEnhance.Sharpness(Image.open(io.BytesIO(raw)).convert("RGB")).enhance(1.3)
    if fr.get("flip"): im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if fr.get("kill_purple"):  # footage sparkle overlays: purple/magenta -> neutral, skin/warm tones untouched
        import numpy as np
        hsv = np.array(im.convert("HSV")).astype(np.int32); h, sat = hsv[..., 0], hsv[..., 1]
        m = (h > 170) & (h < 245) & (sat > 50)  # PIL hue 0-255: ~240-345 deg
        hsv[..., 1] = np.where(m, sat // 8, sat); im = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
    return im
frames = [(grab(f), f.get("fx", 0.5), f.get("fy", 0.45)) for f in cfg["frames"]]

def crop_to(img, w, h, fx, fy):
    s = max(w / img.width, h / img.height); im = img.resize((int(img.width * s + 0.5), int(img.height * s + 0.5)), Image.LANCZOS)
    x = min(max(0, int(fx * im.width - w / 2)), im.width - w); y = min(max(0, int(fy * im.height - h / 2)), im.height - h)
    return im.crop((x, y, x + w, y + h))

def picture(w, h):  # one frame, or frames tiled left->right with a soft seam
    if len(frames) == 1: return crop_to(frames[0][0], w, h, frames[0][1], frames[0][2])
    n = len(frames); tw = w // n; out = Image.new("RGB", (w, h), bgc)
    for i, (im, fx, fy) in enumerate(frames):
        tile = crop_to(im, tw + (w - tw * n if i == n - 1 else 0), h, fx, fy)
        if i == 0: out.paste(tile, (0, 0)); continue
        m = Image.new("L", tile.size, 255); dm = ImageDraw.Draw(m)
        for x in range(60): dm.line([(x, 0), (x, h)], fill=int(255 * x / 60))
        out.paste(tile, (i * tw, 0), m)
    return out

def text(d, x, y, s, f, fill):
    d.text((x + 5, y + 5), s, font=f, fill=(0, 0, 0)); d.text((x, y), s, font=f, fill=fill)

def fonts(k, tsize):
    return (ImageFont.truetype(F + "simkai.ttf", int(tsize * k)), ImageFont.truetype(F + "msyhbd.ttc", int(56 * k)),
            ImageFont.truetype(F + "msyh.ttc", int(40 * k)), ImageFont.truetype(F + "msyhbd.ttc", int(34 * k)))

def side(W, H, pic_w, k):  # picture right, title left
    bg = Image.new("RGB", (W, H), bgc); x0 = W - pic_w; bg.paste(picture(pic_w, H), (x0, 0))
    mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
    for x in range(W): dm.line([(x, 0), (x, H)], fill=int(255 * (1 - min(1, max(0, (x - x0) / (pic_w * cfg.get('fade', 0.35)))))))
    bg = Image.composite(Image.new("RGB", (W, H), bgc), bg, mask.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(bg); tl = cfg["title"]
    ts = min(150, int((W - pic_w * 0.75 - 120 * k) / k / max(len(t) for t in tl)))  # keep the title inside the dark panel
    kai, nm, ln, tg = fonts(k, ts)
    y = H * 0.25 + (80 * k if len(tl) == 1 else 0)
    for i, t in enumerate(tl): text(d, int(90 * k), int(y + i * 160 * k), t, kai, gold)
    text(d, int(112 * k), int(H * 0.59), cfg["name"], nm, cream)
    for i, l in enumerate(cfg.get("lines", [])): text(d, int(114 * k), int(H * 0.675 + i * 60 * k), l, ln, soft)
    text(d, int(120 * k), int(H * 0.9), cfg["tag"], tg, (200, 190, 170))
    return bg

def tall(W, H, frac):  # picture top, title bottom
    pic_h = int(H * frac); bg = Image.new("RGB", (W, H), bgc); bg.paste(picture(W, pic_h), (0, 0))
    mask = Image.new("L", (W, H), 0); dm = ImageDraw.Draw(mask)
    for y in range(H): dm.line([(0, y), (W, y)], fill=int(255 * min(1, max(0, (y - pic_h * 0.72) / (pic_h * 0.3)))))
    bg = Image.composite(Image.new("RGB", (W, H), bgc), bg, mask.filter(ImageFilter.GaussianBlur(25)))
    d = ImageDraw.Draw(bg); k = W / 1080; tl = cfg["title"]
    kai, nm, ln, tg = fonts(k, min(140, int(960 / max(len(t) for t in tl))))
    nm = ImageFont.truetype(F + "msyhbd.ttc", int(58 * k)); ln = ImageFont.truetype(F + "msyh.ttc", int(42 * k))
    y = pic_h - int(60 * k)
    for t in tl:
        tw = d.textlength(t, font=kai); text(d, int((W - tw) / 2), y, t, kai, gold); y += int(150 * k)
    tw = d.textlength(cfg["name"], font=nm); text(d, int((W - tw) / 2), y + int(20 * k), cfg["name"], nm, cream); y += int(110 * k)
    for l in cfg.get("lines", []):
        tw = d.textlength(l, font=ln); text(d, int((W - tw) / 2), y, l, ln, soft); y += int(60 * k)
    tw = d.textlength(cfg["tag"], font=tg); text(d, int((W - tw) / 2), max(y + int(30 * k), H - int(90 * k)), cfg["tag"], tg, (200, 190, 170))
    return bg

out = Path(cfg["out_dir"]); out.mkdir(parents=True, exist_ok=True); p = cfg["out_prefix"]
side(1920, 1080, 1100, 1.0).save(out / f"{p}_16x9.jpg", quality=93)
side(1440, 1080, 700, 0.78).save(out / f"{p}_4x3.jpg", quality=93)
tall(1080, 1440, 0.52).save(out / f"{p}_3x4.jpg", quality=93)
tall(1080, 1920, 0.62).save(out / f"{p}_9x16.jpg", quality=93)
print("COVERS_OK", p)
