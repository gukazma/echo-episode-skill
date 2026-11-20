"""EP04 host look mockups (Seedream): set plates, then each host in the new outfit on the new set. python gen_look.py"""
import sys
from pathlib import Path
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.graphics.seedream_ark import SeedreamArkImage

NOTXT = "画面中没有任何可读的文字、字母、数字、标志、水印。"
SET = ("回声号这一期的演播室布置成1980年东京的一间老式'名曲喫茶'（听唱片的咖啡馆）：深色胡桃木护墙板，满墙黑胶唱片架，"
       "黄铜台灯和磨砂玻璃吊灯发出暖黄的钨丝灯光，蕾丝窗帘，玻璃窗外是雨夜的东京街灯和模糊的霓虹光斑，"
       "角落一只老式立式白色话筒架，桌上一台木壳黑胶唱机，小花瓶里插着粉白的大波斯菊（秋樱）。"
       "电影级写实摄影，16:9，暖琥珀色主调，浅景深，轻微胶片颗粒，昭和怀旧但干净精致，不脏乱。")
JOBS = [
 ("plate_ld", SET + "画面右侧三分之一是一把棕色皮质单人扶手椅，椅子空着，朝向画面右前方；背后是黑胶唱片墙和黄铜壁灯。画面中没有任何人物。" + NOTXT, []),
 ("plate_xy", SET + "画面右侧三分之一是一把比例正常的焦糖色皮质单人扶手椅，椅子空着；背后是挂着蕾丝窗帘的雨夜玻璃窗，窗边小圆木桌上放着黑胶唱机和插着秋樱的小花瓶。画面中没有任何人物。" + NOTXT, []),
 ("ld_A", "以图1这位男士为准，保持他的脸、发型、胡茬、年龄完全不变。他坐在图2这把扶手椅上，背景就是图2的名曲喫茶。"
          "服装换成：驼色灯芯绒西装外套，内搭米白色高领针织衫，深棕色西裤，左手腕戴黄铜表壳机械表。面向镜头温和微笑，中近景，16:9。" + NOTXT, ["c_laodu.png", "plate_ld.png"]),
 ("ld_B", "以图1这位男士为准，保持他的脸、发型、胡茬、年龄完全不变。他坐在图2这把扶手椅上，背景就是图2的名曲喫茶。"
          "服装换成：深藏青色粗花呢西装外套，内搭浅灰蓝衬衫、不打领带，最上面一颗扣子解开，左手腕戴黄铜表壳机械表。面向镜头温和微笑，中近景，16:9。" + NOTXT, ["c_laodu.png", "plate_ld.png"]),
 ("xy_A", "以图1这位女生为准，保持她的脸、齐肩短发、柚子形发夹、细边圆框眼镜、年龄完全不变。她端正地坐在图2这把扶手椅上，人和椅子比例正常，上半身高出扶手，背景就是图2的名曲喫茶。"
          "服装换成：七十年代风格的奶白色粗棒针开衫，里面是小圆领的浅粉色碎花连衣裙。不戴耳机。面向镜头温柔地笑，中近景，16:9。" + NOTXT, ["c_xy_last.png", "plate_xy.png"]),
 ("xy_B", "以图1这位女生为准，保持她的脸、齐肩短发、柚子形发夹、细边圆框眼镜、年龄完全不变。她端正地坐在图2这把扶手椅上，人和椅子比例正常，上半身高出扶手，背景就是图2的名曲喫茶。"
          "服装换成：白色荷叶领衬衫，外面一件酒红色针织背心，领口系一条细细的米色丝带。不戴耳机。面向镜头温柔地笑，中近景，16:9。" + NOTXT, ["c_xy_last.png", "plate_xy.png"]),
]
for key, prompt, refs in JOBS:
    out = Path(f"{key}.png")
    if out.exists():
        print(key, "exists", flush=True); continue
    r = SeedreamArkImage().execute({"prompt": prompt, "size": "2560x1440", "reference_images": [str(Path(x).resolve()) for x in refs], "output_path": str(out.resolve())})
    print(key, "ok" if r.success else "FAILED", r.data.get("estimated_cost_cny") if r.success else r.error, flush=True)
print("LOOK_DONE", flush=True)
