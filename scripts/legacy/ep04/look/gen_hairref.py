"""幸子头 hairstyle reference without a face (so Ark accepts it as a Seedance reference)."""
import sys
from pathlib import Path
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.graphics.seedream_ark import SeedreamArkImage
HAIR = ("七十年代日剧《血疑》里幸子的'幸子头'：乌黑浓密有光泽的短发，齐耳，发尾在耳垂到下颌之间；层次感很强，头顶蓬松饱满；"
        "发尾整体向内卷成圆润的弧度，两侧盖住耳朵；刘海是打薄的碎刘海，轻盈、从中间微微分开、带一点弧度地搭在眉毛上。整体柔软、微卷、有空气感，像1970年代日本少女的发型，不是顺直的波波头。")
JOBS = {
 "hairref_wig": "美发沙龙的产品摄影：一顶真发假发戴在一个光滑的纯白色无五官泡沫模特头上（模特头没有眼睛、鼻子、嘴巴，只是光滑的白色头型），四分之三侧前方视角，"
                "柔和的影棚光，浅灰色纯色背景。假发的发型是" + HAIR + "画面中没有任何人、人脸、文字、标志、水印。",
 "hairref_back": "一位年轻女生的后脑勺和侧后方特写，看不到脸，只看到头发和一点点脖子与奶白色开衫的领口，温暖的钨丝灯光，背景是虚化的黑胶唱片架。发型是" + HAIR + "画面中看不到脸，没有任何文字、标志、水印。",
}
for k, prompt in JOBS.items():
    out = Path(f"{k}.png")
    r = SeedreamArkImage().execute({"prompt": prompt, "size": "2048x2048", "reference_images": [], "output_path": str(out.resolve())})
    print(k, "ok" if r.success else "FAILED", r.data.get("estimated_cost_cny") if r.success else r.error, flush=True)
