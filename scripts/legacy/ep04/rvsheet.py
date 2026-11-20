"""stack studio/review strips of accepted takes (with labels) -> qc/rv_<n>.jpg, 9 strips per sheet"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
st = Path("studio"); acc = json.loads((st / "accepted.json").read_text())
import sys
keys = sys.argv[1:] or [k for v in acc.values() for k in v]
f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 28)
for n in range(0, len(keys), 9):
    ims = [(k, Image.open(st / "review" / f"{k}.jpg")) for k in keys[n:n + 9] if (st / "review" / f"{k}.jpg").exists()]
    W = max(i.width for _, i in ims); H = sum(i.height + 4 for _, i in ims)
    sh = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(sh); y = 0
    for k, i in ims:
        sh.paste(i, (0, y)); d.text((6, y + 4), k, font=f, fill=(255, 230, 0)); y += i.height + 4
    sh.save(f"qc/rv{'x' if sys.argv[1:] else ''}_{n // 9}.jpg", quality=85)
print("RV_DONE")
