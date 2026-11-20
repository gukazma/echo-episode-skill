"""EP05 look via Seedance 2.0 mini: old approved face ref + new empty set plate + outfit/hair in text -> short silent clip; its last frame = new character ref.
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
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖琥珀色吊灯主调加一点窗外的冷色夜光，浅景深。画面中不出现任何字幕、文字、水印、标志、商标。"
SETD = "1990年代初美国加州公路边一家通宵营业的老式美式餐馆的卡座：深红色皮革软包卡座、镀铬包边的米白色台面，桌上两只厚瓷白咖啡杯和一壶咖啡，头顶一盏暖黄色吊灯，窗外是深夜湿漉漉的停车场和远处模糊的霓虹光斑。"
JOB = {
 "老渡": (["../echo_ep01_final/img/c_laodu.png", "look/plate_ld_s.jpg"],
        "【CHARACTER】图1里的这位男士（老渡）：脸、短寸头、鬓角微白、浅胡茬、年龄与图1完全一致。"
        "【WARDROBE】这一期他换了衣服：简洁利落的黑色皮夹克，内搭黑色圆领T恤，深色牛仔裤，左手腕戴黄铜表壳机械表。绝对不要穿图1里的橄榄绿夹克。"
        "【SCENE】他坐在图2这个卡座里，背景与图2一致：" + SETD +
        "【SHOT】中近景，固定机位，正面略偏。他面向镜头，坐得放松端正，双手轻放在桌面上，温和地微笑，轻轻点一下头，然后保持安静的微笑。不说话。"),
 "小柚": (["../echo_ep01_final/clips/S06x_t3_last.png", "look/plate_xy_s.jpg"],
        "【CHARACTER】图1里的这位女生（小柚）：脸、齐肩的黑色短发、细边圆框眼镜、年龄与图1完全一致，左侧别着柚子形小发夹。"
        "【WARDROBE】这一期她换了衣服：宽松的复古棒球夹克（奶白色衣身、墨绿色袖子，没有任何字母和徽章），里面是白色圆领T恤。不戴耳机。绝对不要穿图1里的橙色连帽卫衣。"
        "【SCENE】她坐在图2这个卡座里，背景与图2一致：" + SETD +
        "【POSTURE】她端正地坐在卡座上，腰背挺直，上半身高出桌面，人和座位比例正常，绝不陷进座位里。"
        "【SHOT】中近景，固定机位，正面略偏。她面向镜头，眼睛弯弯地温柔微笑，轻轻推了一下眼镜，然后双手放在桌上，保持安静的微笑。不说话。"),
}
def run(who, take):
    refs, desc = JOB[who]; tag = "ld" if who == "老渡" else "xy"
    out = lk / f"lookclip_{tag}_t{take}.mp4"
    inputs = {"prompt": STYLE + "\n" + desc + "\n【AUDIO】只有安静的室内环境声和远处偶尔驶过的汽车声，没有音乐，没有人说话。", "model_variant": "mini", "model": SeedanceArkVideo.MODEL_IDS["mini"],
              "duration": 5, "aspect_ratio": "16:9", "resolution": "720p", "generate_audio": False, "operation": "reference_to_video",
              "reference_image_paths": [str((ep / r).resolve()) for r in refs], "return_last_frame": True, "output_path": str(out),
              "timeout_seconds": 1800, "poll_interval_seconds": 8}
    r = SeedanceArkVideo().execute(inputs)
    if not r.success:
        print(tag, take, "FAIL", str(r.error)[:300], flush=True); return
    (lk / f"lookclip_{tag}_t{take}_last.png").write_bytes(requests.get(r.data["last_frame_url"], timeout=120).content)
    print(tag, take, "OK cost", r.cost_usd, flush=True)
with ThreadPoolExecutor(4) as pool:
    list(pool.map(lambda a: run(*a), [(w, int(t)) for w, t in (x.split(":") for x in sys.argv[1:])]))
print("LOOKCLIP_DONE", flush=True)
