"""EP06 look via Seedance 2.0 mini: old approved face ref + new empty set plate + outfit in text -> 5 s silent clip; its last frame = this episode's character ref.
(Seedream stills with faces - ld_A/xy_A - are refused by Seedance as 'real person'.)  python look/gen_lookclip.py 老渡:1 小柚:1 ..."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.video.seedance_ark import SeedanceArkVideo
ep = Path(__file__).resolve().parent.parent; lk = ep / "look"
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖橙色黄昏光加室内钨丝灯，浅景深，温暖怀旧但干净精致。画面中不出现任何字幕、文字、数字、球衣号码、队徽、水印、标志、商标。"
SETD = ("葡萄牙里斯本老城一家傍晚的球迷小酒馆：墙面下半截是蓝白色手绘瓷砖，上半截是暖白色石灰墙，墙上挂着红绿配色的针织围巾，深色木桌木椅，"
        "桌上一杯咖啡和一小碟葡式蛋挞，窗外是黄昏的石板坡道和模糊的黄色老电车。")
JOB = {
 "老渡": (["look/c_laodu_s.jpg", "look/plate_ld_s.jpg"],
        "【CHARACTER】图1里的这位男士（老渡）：脸、发型、鬓角、浅胡茬、年龄与图1完全一致。"
        "【WARDROBE】这一期他换了衣服：墨绿色粗针织开衫，内搭白色衬衫，深灰色长裤，左手腕戴黄铜表壳机械表。绝对不要穿图1里的衣服。"
        "【SCENE】他坐在图2这张木桌旁的木椅上，背景与图2一致：" + SETD +
        "【SHOT】中近景，固定机位，正面略偏。他面向镜头，坐得放松端正，双手轻放在桌面上，温和地微笑，轻轻点一下头，然后保持安静的微笑。不说话。"),
 "小柚": (["look/c_xy_last_s.jpg", "look/plate_xy_s.jpg"],
        "【CHARACTER】图1里的这位女生（小柚）：脸、齐肩的黑色短发、细边圆框眼镜、年龄与图1完全一致，左侧别着柚子形小发夹。"
        "【WARDROBE】这一期她换了衣服：正红色的圆领粗针织毛衣，脖子上松松地围着一条红绿配色的针织围巾（没有任何文字和图案）。不戴耳机。绝对不要穿图1里的衣服。"
        "【SCENE】她坐在图2这把木椅上，背景与图2一致：" + SETD +
        "【POSTURE】她端正地坐在木椅上，腰背挺直，上半身高出桌面，人和椅子比例正常，绝不陷进椅子里。"
        "【SHOT】中近景，固定机位，正面略偏。她面向镜头，眼睛弯弯地温柔微笑，轻轻推了一下眼镜，然后双手放在桌上，保持安静的微笑。不说话。"),
}
def run(who, take):
    refs, desc = JOB[who]; tag = "ld" if who == "老渡" else "xy"
    out = lk / f"lookclip_{tag}_t{take}.mp4"
    inputs = {"prompt": STYLE + "\n" + desc + "\n【AUDIO】只有安静的室内环境声和远处电车的叮当声，没有音乐，没有人说话。", "model_variant": "mini", "model": SeedanceArkVideo.MODEL_IDS["mini"],
              "duration": 5, "aspect_ratio": "16:9", "resolution": "720p", "generate_audio": False, "operation": "reference_to_video",
              "reference_image_paths": [str((ep / r).resolve()) for r in refs], "return_last_frame": True, "output_path": str(out),
              "timeout_seconds": 1800, "poll_interval_seconds": 8}
    r = SeedanceArkVideo().execute(inputs)
    if not r.success:
        print(tag, take, "FAIL", str(r.error)[:300], flush=True); return
    (lk / f"lookclip_{tag}_t{take}_last.png").write_bytes(requests.get(r.data["last_frame_url"], timeout=120).content)
    print(tag, take, "OK cost", r.cost_usd, flush=True)
with ThreadPoolExecutor(2) as pool:
    list(pool.map(lambda a: run(*a), [(w, int(t)) for w, t in (x.split(":") for x in sys.argv[1:])]))
print("LOOKCLIP_DONE", flush=True)
