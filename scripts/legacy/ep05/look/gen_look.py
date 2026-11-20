"""EP05 host look mockups (Seedream): set plates, then each host in the new outfit on the new set. python gen_look.py"""
import sys
from pathlib import Path
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.graphics.seedream_ark import SeedreamArkImage

NOTXT = "画面中没有任何可读的文字、字母、数字、标志、商标、水印。"
SET = ("回声号这一期的演播室布置成1990年代初美国加州公路边一家通宵营业的老式美式餐馆（diner）的卡座：深红色皮革软包卡座、镀铬包边的米白色台面，"
       "桌上两只厚瓷白咖啡杯和一壶咖啡，一张铺开的纸餐巾上用铅笔画满了方块和连线的芯片草图（只有线条，没有任何文字），旁边一支铅笔；"
       "头顶一盏暖黄色吊灯，窗外是深夜的停车场、湿漉漉的柏油路和远处模糊的霓虹光斑与路灯，"
       "电影级写实摄影，16:9，暖琥珀色主调加一点窗外的冷色夜光，浅景深，轻微胶片颗粒，怀旧但干净精致，不脏乱。")
JOBS = [
 ("plate_ld", SET + "镜头从卡座一侧拍过去：画面右侧三分之一是一侧空着的深红色卡座座位，座位朝向画面右前方；背后是卡座高靠背和墙上的暖黄壁灯。画面中没有任何人物。" + NOTXT, []),
 ("plate_xy", SET + "镜头从卡座另一侧拍过去：画面右侧三分之一是另一侧空着的深红色卡座座位，座位高度正常、坐垫结实；背后是挂着百叶帘的玻璃窗和窗外深夜的停车场霓虹。画面中没有任何人物。" + NOTXT, []),
 ("ld_A", "以图1这位男士为准，保持他的脸、发型、胡茬、年龄完全不变。他坐在图2这个卡座里，背景就是图2的美式餐馆。"
          "服装换成：简洁利落的黑色皮夹克，内搭黑色圆领T恤，深色牛仔裤，左手腕戴黄铜表壳机械表。双手轻放在桌上，面向镜头温和微笑，中近景，16:9。" + NOTXT, ["c_laodu.png", "plate_ld.png"]),
 ("ld_B", "以图1这位男士为准，保持他的脸、发型、胡茬、年龄完全不变。他坐在图2这个卡座里，背景就是图2的美式餐馆。"
          "服装换成：深靛蓝色水洗牛仔衬衫外套，内搭白色圆领T恤，袖子随意挽到小臂，左手腕戴黄铜表壳机械表。双手轻放在桌上，面向镜头温和微笑，中近景，16:9。" + NOTXT, ["c_laodu.png", "plate_ld.png"]),
 ("xy_A", "以图1这位女生为准，保持她的脸、齐肩短发、柚子形发夹、细边圆框眼镜、年龄完全不变。她端正地坐在图2这个卡座里，人和座位比例正常，上半身高出桌面，背景就是图2的美式餐馆。"
          "服装换成：宽松的复古棒球夹克（奶白色衣身、墨绿色袖子，没有任何字母和徽章），里面是白色圆领T恤。不戴耳机。面向镜头温柔地笑，中近景，16:9。" + NOTXT, ["c_xy_last.png", "plate_xy.png"]),
 ("xy_B", "以图1这位女生为准，保持她的脸、齐肩短发、柚子形发夹、细边圆框眼镜、年龄完全不变。她端正地坐在图2这个卡座里，人和座位比例正常，上半身高出桌面，背景就是图2的美式餐馆。"
          "服装换成：柚子黄色的短款针织开衫，里面是浅蓝色牛仔衬衫，领口扣到第二颗。不戴耳机。面向镜头温柔地笑，中近景，16:9。" + NOTXT, ["c_xy_last.png", "plate_xy.png"]),
]
for key, prompt, refs in JOBS:
    out = Path(f"{key}.png")
    if out.exists():
        print(key, "exists", flush=True); continue
    r = SeedreamArkImage().execute({"prompt": prompt, "size": "2560x1440", "reference_images": [str(Path(x).resolve()) for x in refs], "output_path": str(out.resolve())})
    print(key, "ok" if r.success else "FAILED", r.data.get("estimated_cost_cny") if r.success else r.error, flush=True)
print("LOOK_DONE", flush=True)
