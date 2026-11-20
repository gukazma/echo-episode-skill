"""EP04 look via Seedance: old approved face ref + new empty set plate + outfit/hair in text -> short silent clip; its last frame = new character ref.
python look/gen_lookclip.py  (2 takes per host)"""
import json, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.video.seedance_ark import SeedanceArkVideo
ep = Path(__file__).resolve().parent.parent; lk = ep / "look"
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖琥珀色钨丝灯主调，浅景深。画面中不出现任何字幕、文字、水印、标志。"
JOB = {
 "老渡": (["../echo_ep01_final/img/c_laodu.png", "look/plate_ld.png"],
        "【CHARACTER】图1里的这位男士（老渡）：脸、短寸头、鬓角微白、浅胡茬、年龄与图1完全一致。"
        "【WARDROBE】这一期他换了衣服：驼色灯芯绒西装外套，内搭米白色高领针织衫，深棕色西裤，左手腕戴黄铜表壳机械表。绝对不要穿图1里的橄榄绿夹克和黑T恤。"
        "【SCENE】他坐在图2这间1980年东京老式名曲喫茶里那把棕色皮质扶手椅上，背后是满墙黑胶唱片架和黄铜壁灯，左侧是挂着蕾丝窗帘的雨夜玻璃窗、木壳黑胶唱机和插着秋樱的小花瓶。背景与图2一致。"
        "【SHOT】中近景，固定机位，正面略偏。他面向镜头，背靠椅背坐得放松端正，双手自然放在扶手上，温和地微笑，轻轻点一下头，然后保持安静的微笑。不说话。"),
 "小柚": (["../echo_ep01_final/clips/S06x_t3_last.png", "look/plate_xy.png", "look/hairref_wig.png"],
        "【CHARACTER】图1里的这位女生（小柚）：脸、细边圆框眼镜、年龄与图1完全一致，左侧别着柚子形小发夹。"
        "【HAIR】发型严格照图3这顶假发的发型来（图3只是发型参考，模特头本身不要出现）：这一期她特意剪了1984年在中国红极一时的'幸子头'（日剧《血疑》里山口百惠饰演的幸子的发型），和她平时的直发完全不同：乌黑浓密的短发，齐耳，发尾在耳垂到下颌之间，层次感很强、蓬松饱满、头顶有自然的蓬度；发尾整体向内卷成圆润的弧度，两侧盖住耳朵；刘海是打薄的碎刘海，轻盈、微微分开、带一点弧度地搭在眉毛上，不是厚重的齐刘海；整体是七十年代日本少女那种柔软、微卷、有空气感的短发，绝不是顺直的波波头。"
        "【WARDROBE】这一期她换了衣服：奶白色粗棒针开衫，里面是浅粉色碎花小圆领连衣裙。不戴耳机。绝对不要穿图1里的橙色连帽卫衣。"
        "【SCENE】她坐在图2这间1980年东京老式名曲喫茶里那把比例正常的焦糖色皮质扶手椅上，背后是挂着蕾丝窗帘的雨夜玻璃窗和黑胶唱片架，身旁小圆木桌上有黑胶唱机和插着秋樱的小花瓶。背景与图2一致。"
        "【POSTURE】她端正地坐在坐垫上，腰背挺直，扶手只到她的腰部，上半身高出扶手，绝不陷进沙发里。"
        "【SHOT】中近景，固定机位，正面略偏。她面向镜头，眼睛弯弯地温柔微笑，用一只手轻轻碰了一下自己的发尾，然后双手放回腿上，保持安静的微笑。不说话。"),
}
def run(who, take):
    refs, desc = JOB[who]; tag = "ld" if who == "老渡" else "xy"
    out = lk / f"lookclip_{tag}_t{take}.mp4"
    inputs = {"prompt": STYLE + "\n" + desc + "\n【AUDIO】只有安静的室内环境声和窗外轻微的雨声，没有音乐，没有人说话。", "model_variant": "2.5", "model": SeedanceArkVideo.MODEL_IDS["2.5"],
              "duration": 5, "aspect_ratio": "16:9", "resolution": "720p", "generate_audio": False, "operation": "reference_to_video",
              "reference_image_paths": [str((ep / r).resolve()) for r in refs], "return_last_frame": True, "output_path": str(out),
              "timeout_seconds": 1800, "poll_interval_seconds": 8, "custom_price_cny_per_million_tokens": 77.0}
    r = SeedanceArkVideo().execute(inputs)
    if not r.success:
        print(tag, take, "FAIL", str(r.error)[:300], flush=True); return
    (lk / f"lookclip_{tag}_t{take}_last.png").write_bytes(requests.get(r.data["last_frame_url"], timeout=120).content)
    print(tag, take, "OK cost", r.cost_usd, flush=True)
with ThreadPoolExecutor(4) as pool:
    list(pool.map(lambda a: run(*a), [(w, int(t)) for w, t in (x.split(":") for x in sys.argv[1:])]))
print("LOOKCLIP_DONE", flush=True)
