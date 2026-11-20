from PIL import Image, ImageDraw, ImageFont
f = ImageFont.truetype(r"C:\Windows\Fonts\simhei.ttf", 40)
items = [("ld_A.png", "老渡 A：驼色灯芯绒西装 + 米白高领毛衣"), ("ld_B.png", "老渡 B：藏青粗花呢西装 + 浅灰蓝衬衫"),
         ("xy_A.png", "小柚 A：奶白粗针开衫 + 浅粉碎花连衣裙"), ("xy_B.png", "小柚 B：白色荷叶领衬衫 + 酒红毛衣背心")]
W, H = 1280, 720
sheet = Image.new("RGB", (W * 2 + 30, (H + 70) * 2 + 20), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, (p, t) in enumerate(items):
    im = Image.open(p).convert("RGB").resize((W, H))
    x, y = 10 + (i % 2) * (W + 10), 10 + (i // 2) * (H + 70)
    sheet.paste(im, (x, y)); d.text((x + 10, y + H + 12), t, font=f, fill=(230, 190, 110))
sheet.save("EP04_主持人造型预览.jpg", quality=90)
