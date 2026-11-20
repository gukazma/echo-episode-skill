"""小柚 幸子头 mockups on the chosen look (xy_A)."""
import sys
from pathlib import Path
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.graphics.seedream_ark import SeedreamArkImage
NOTXT = "画面中没有任何可读的文字、字母、数字、标志、水印。"
BASE = ("以图1为准：同一个女生、同一套衣服（奶白粗棒针开衫+浅粉碎花小圆领连衣裙）、同一把扶手椅、同一个名曲喫茶背景，脸、细边圆框眼镜、年龄完全不变。"
        "只把发型换成七十年代日剧《血疑》里幸子的'幸子头'：")
JOBS = {
 "xy_A_hair1": BASE + "乌黑顺直的短发，发尾刚到下颌、整齐地向内微微卷，厚而齐的刘海盖到眉毛，头发有光泽，左侧仍别着一个柚子形小发夹。她面向镜头，开心地用一只手轻轻摸了摸自己的发尾，像在展示新发型，温柔地笑。中近景，16:9。" + NOTXT,
 "xy_A_hair2": BASE + "乌黑顺直的蘑菇形短发，发尾齐耳到下颌之间、向内收成圆弧，厚齐刘海到眉毛，左侧仍别着一个柚子形小发夹。她面向镜头，端正地坐着，眼睛弯弯地笑，有点小得意。中近景，16:9。" + NOTXT,
}
for key, prompt in JOBS.items():
    out = Path(f"{key}.png")
    if out.exists():
        print(key, "exists", flush=True); continue
    r = SeedreamArkImage().execute({"prompt": prompt, "size": "2560x1440", "reference_images": [str(Path("xy_A.png").resolve())], "output_path": str(out.resolve())})
    print(key, "ok" if r.success else "FAILED", r.data.get("estimated_cost_cny") if r.success else r.error, flush=True)
