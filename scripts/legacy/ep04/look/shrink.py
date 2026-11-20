import sys
from PIL import Image
for p in sys.argv[1:]:
    im = Image.open(p).convert("RGB"); im.thumbnail((900, 900)); im.save(p.rsplit(".",1)[0] + "_s.jpg", quality=85)
