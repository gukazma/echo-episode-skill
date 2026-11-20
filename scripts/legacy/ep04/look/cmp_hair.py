import subprocess
from PIL import Image, ImageDraw, ImageFont
subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1050", "-i", "../footage/akai_bl_ep29.mp4", "-frames:v", "1", "sachiko.png"])
f = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 36)
items = [("sachiko.png", "《血疑》里的幸子"), ("lookclip_xy_t5_last.png", "小柚 · 幸子头 候选A"), ("lookclip_xy_t6_last.png", "小柚 · 幸子头 候选B")]
W, H = 960, 540
sheet = Image.new("RGB", (W * 3 + 40, H + 70), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for i, (p, t) in enumerate(items):
    im = Image.open(p).convert("RGB"); im = im.resize((W, int(im.height * W / im.width)))
    if im.height > H: top = (im.height - H) // 2; im = im.crop((0, top, W, top + H))
    x = 10 + i * (W + 10); sheet.paste(im, (x, 10)); d.text((x + 10, H + 20), t, font=f, fill=(230, 190, 110))
sheet.save("xiaoyou_hair_compare.jpg", quality=90)
