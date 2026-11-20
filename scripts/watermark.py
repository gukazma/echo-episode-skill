"""回声号 signature watermark (bottom-right, every episode): "老渡 · 小柚" in Noto Serif SC SemiBold, thin gold rule with a
diamond, soft shadow, 72 % opacity. Same look as EP01. render_badge(out_png, W, H) -> full-frame RGBA PNG to overlay."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FALLBACK = r"C:\Windows\Fonts\simsun.ttc"


def _font(size):
    try:
        f = ImageFont.truetype(SERIF, size)
        f.set_variation_by_name(b"SemiBold")
        return f
    except Exception:
        return ImageFont.truetype(FALLBACK, size)


def render_badge(out_png, W=1920, H=1080, text="老渡 · 小柚", opacity=0.72):
    S = 3
    fz = _font(30 * S)
    tw = int(ImageDraw.Draw(Image.new("RGBA", (10, 10))).textlength(text, font=fz))
    bw, bh = tw + 60 * S, 64 * S
    b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    m = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(m).text((30 * S, 6 * S), text, font=fz, fill=255)
    sh = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(4 * S)).point(lambda v: v * 150 // 255))
    b.alpha_composite(sh, (0, 2 * S))
    d = ImageDraw.Draw(b)
    d.text((30 * S, 6 * S), text, font=fz, fill=(246, 238, 222, 255))
    y, cx = 50 * S, 30 * S + tw // 2
    d.line([(30 * S, y), (cx - 9 * S, y)], fill=(232, 163, 61, 230), width=S + 1)
    d.line([(cx + 9 * S, y), (30 * S + tw, y)], fill=(232, 163, 61, 230), width=S + 1)
    d.polygon([(cx, y - 4 * S), (cx + 4 * S, y), (cx, y + 4 * S), (cx - 4 * S, y)], fill=(240, 190, 100, 255))
    b = b.resize((bw // S, bh // S), Image.LANCZOS)
    b.putalpha(b.getchannel("A").point(lambda v: int(v * opacity)))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(b, (W - b.width - 30, H - b.height - 26))
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    im.save(out_png)
    return Path(out_png)
