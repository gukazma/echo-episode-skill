"""EP02 studio shots → studio/plan_<name>.json  (python studio_plan.py <name> <shot ids...>)"""
import json, math, re, sys, subprocess
from pathlib import Path
sys.argv, args = ["x", "none"], sys.argv[1:]
import make_v4 as m
name, ids = args[0], args[1:]
E1 = "../echo_ep01_final/"
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖琥珀色主调，浅景深。画面中不出现任何字幕、文字、水印、标志。"
CHAR = {"老渡": "老渡（图1）：中国男性，约38岁，短寸头，鬓角微白，浅胡茬；深橄榄绿飞行员夹克，内搭黑色圆领T恤，左手腕戴黄铜表壳机械表。性格沉稳、温厚。",
        "小柚": "小柚（图1）：中国女生，约23岁，齐肩短发，左侧别着柚子形发夹，细边圆框眼镜；宽松的橙色连帽卫衣，白色头戴式耳机挂在脖子上。性格温柔可爱、文静。"}
REF = {"老渡": [E1 + "img/c_laodu.png", E1 + "img/s_bg_laodu.png"], "小柚": [E1 + "clips/S06x_t3_last.png", "studio/bg_xiaoyou_v1.png"]}
SEAT = {
 ("老渡", "side"): "【SCREEN DIRECTION】老渡坐在演播室左边那把棕色皮质扶手椅上，身体朝向画面右侧，视线看向画面右侧（看着坐在对面的小柚）。背景固定是图2：背后是拱形黄铜边框的大舷窗，窗外是星空和地球，两侧胡桃木护墙板和壁灯。",
 ("老渡", "cam"):  "【SCREEN DIRECTION】老渡坐在演播室那把棕色皮质扶手椅上，面向镜头，看着镜头和观众说话。背景固定是图2：背后是拱形黄铜边框的大舷窗，窗外是星空和地球。",
 ("小柚", "side"): "【SCREEN DIRECTION】小柚坐在演播室右边那把棕色皮质扶手椅上（图2里那把椅子），身体朝向画面左侧，视线看向画面左侧（看着坐在对面的老渡）。背景固定是图2：黄铜仪表墙、圆形小舷窗和胡桃木书架，她左手边是小圆木边桌。",
 ("小柚", "cam"):  "【SCREEN DIRECTION】小柚坐在演播室那把棕色皮质扶手椅上（图2里那把椅子），面向镜头，看着镜头和观众说话。背景固定是图2：黄铜仪表墙、圆形小舷窗和胡桃木书架。",
}
POSTURE = {"老渡": "【POSTURE】坐姿放松但端正，背靠椅背，双手自然放在扶手或腿上。",
           "小柚": "【POSTURE】小柚端正地坐在坐垫上，腰背挺直，臀部坐实在坐垫上，扶手只到她的腰部，肩膀和整个上半身都高出扶手；人和椅子的比例正常，绝不陷进沙发里，不缩成一团。"}
VOICE = {"老渡": "老渡的声音：低沉温厚的男中音，标准普通话，沉稳从容",
         "小柚": "小柚的声音：温柔甜美的年轻女声，标准普通话，轻柔自然，不夸张、不一惊一乍"}
SHOT = {  # id: (angle or None = from pic, 表演, 运镜)
 "009": ("cam", "老渡面向镜头，温和地微笑，轻轻点头向观众打招呼，说到'爱讲老故事'时嘴角上扬", "中近景，固定机位"),
 "010": ("cam", "小柚面向镜头，眼睛弯弯地笑，右手在胸前轻轻挥了一下打招呼，然后双手放回腿上，说话轻柔", "中近景，固定机位"),
 "011": ("side", "老渡微笑着，右手掌心向上轻轻向身后的舷窗方向一摊，像在介绍这艘船，语气沉稳而带着一点神秘", "中近景，极慢推近"),
 "012": ("side", "老渡身体微微前倾，语气放缓，像要揭晓一个秘密，说到'去见一个人'时停顿一下", "中近景"),
 "013": ("side", "小柚眼睛一亮，轻轻笑着歪了一下头，语气温柔、带一点小得意，像在猜谜", "中近景"),
 "014": ("side", "老渡笑着轻轻摇了摇头，竖起一根手指示意'先不急'，然后神情慢慢认真起来，语速放慢", "中近景，缓推"),
 "015": ("side", "小柚轻轻睁大眼睛，小声重复'四十七岁'，然后好奇地轻声问", "近景"),
 "016": ("side", "老渡看着小柚，平静而郑重地只说了两个字，说完轻轻点了一下头", "近景，固定机位"),
 "020": (None, "老渡双手交握放在腿上，带着一丝不解微微皱眉，说到'为什么？'时抬眼看向小柚，停顿一下", "中近景"),
 "023": (None, "小柚轻轻吸了口气，眼神柔和下来，低声感叹，有点心疼", "近景"),
 "027": (None, "小柚轻轻叹了口气，微微低头，然后抬眼看向老渡，语气轻柔，带一点不可思议", "近景"),
 "028": (None, "老渡轻轻摇头，说'他没有'时语气坚定，然后身体微微前倾，右手在身前轻轻比划，沉稳有力", "中近景，缓推"),
 "033": (None, "小柚有点动容，轻声感叹，眼睛里带着敬意", "近景"),
 "034": (None, "小柚歪着头，好奇地望着老渡，轻声发问，右手食指轻轻点了点下巴", "中近景"),
 "036": (None, "老渡沉稳地讲述，先用左手、再用右手在身前比出'一边''一边'，语气越来越有力，说到最后语气坚定", "中近景，缓推"),
 "039": (None, "小柚眼睛一亮，轻声说出答案，带着一点小得意的微笑", "近景"),
 "046": (None, "小柚轻轻抿了抿嘴，眼神里带着心疼，低声说", "近景"),
 "052": (None, "小柚好奇地微微前倾，轻声确认，带一点兴奋", "中近景"),
 "055": (None, "老渡坐直身体，眼神发亮，语气振奋而沉稳，右手轻轻握拳放在扶手上", "中近景，缓推"),
 "060": (None, "小柚抬起右手示意'等等'，眼睛慢慢睁大，越说越兴奋，但声音依然温柔", "中近景"),
 "061": (None, "老渡郑重地点头说'对'，目光望向远处，语气越来越激昂但克制", "中近景，缓推"),
 "065": (None, "小柚神情黯然，轻声重复，声音有点发颤", "近景，固定机位"),
 "066": (None, "老渡神情凝重，目光低垂，缓缓地说，语气沉重", "中近景，固定机位"),
 "070": (None, "小柚眼神一黯，像突然明白了什么，轻声说，难过地垂下眼睛", "近景"),
 "076": (None, "小柚愣了一下，眼眶微红，轻声问，声音很小", "近景"),
 "082": (None, "小柚眼神湿润，轻轻叹息，声音轻柔而心疼", "近景，固定机位"),
 "083": (None, "老渡沉默片刻后缓缓开口，语气低沉克制，说到'只能靠他了'之前停顿，轻轻吸一口气", "中近景，极慢推近"),
 "086": (None, "小柚重新打起精神，好奇地轻声问，带一点期待", "中近景"),
 "093": (None, "老渡娓娓道来，语气平和而有感情，说到最后带着敬意，微微点头", "中近景"),
 "098": (None, "小柚不解地歪了歪头，轻声说，带一点疑惑", "中近景"),
 "099": (None, "老渡平静而有分量地回答，语气沉稳，说到'对自己，也一样'时轻轻点头", "中近景"),
 "110": (None, "小柚眼含泪光，声音轻轻发颤，慢慢地说", "近景，固定机位"),
 "121": (None, "老渡神情由沉重转为郑重，语气沉稳，说到'真正开始流传'时微微抬眼", "中近景"),
 "123": (None, "小柚轻轻笑了一下，带着感慨和佩服，轻声说", "近景"),
 "128": (None, "老渡身体微微前倾，看着小柚，语气沉稳有力，带着自豪", "中近景，缓推"),
 "129": (None, "小柚认真地点点头，眼神坚定而温柔，轻声说", "近景"),
 "137": (None, "小柚面向镜头，带着小骄傲的笑容坐直身子，像学生背书一样认真地背诵，温柔可爱", "中近景"),
 "138": (None, "老渡缓缓点头，目光深远，语气深沉而有力，带着感慨", "中近景，极慢推近"),
 "139": (None, "小柚望着老渡，轻声问，带着疑惑和一点担心", "中近景"),
 "140": (None, "老渡沉默一下，轻轻吸了口气，语气平静而沉重", "近景"),
 "141": (None, "小柚轻声追问，眼神真诚", "近景"),
 "142": (None, "老渡看着小柚，平静而温和地说，说完轻轻点头", "近景，固定机位"),
 "145": (None, "老渡平静地娓娓道来，语气诚恳，像在讲一位老朋友", "中近景"),
 "146": (None, "老渡语气逐渐有力，慷慨而克制，眼神坚定，说到'二十七年''十一年'时加重语气", "中近景，缓推"),
 "147": (None, "小柚面向镜头，温柔而认真地轻声说，眼神关切，像在安慰观众", "中近景，固定机位"),
 "148": (None, "老渡面向镜头，沉稳有力地说，眼神坚定而温暖，最后露出一个淡淡的微笑", "中近景，极慢推近"),
}
PRON = {"背过": "bèi guò", "还寄": "hái jì", "还在": "hái zài", "还是": "hái shì", "差一点": "chà yì diǎn", "差点": "chà diǎn", "为了": "wèi le",
        "为什么": "wèi shén me", "答应": "dā ying", "宁愿": "nìng yuàn", "扛了": "káng le", "累倒": "lèi dǎo", "强大": "qiáng dà", "只能": "zhǐ néng",
        "不只是": "bù zhǐ shì", "中道崩殂": "zhōng dào bēng cú", "翻了身": "fān le shēn", "都会": "dōu huì", "都有": "dōu yǒu", "都给": "dōu gěi",
        "全都": "quán dōu", "睡得": "shuì de", "撑得": "chēng de", "得更": "de gèng", "看着": "kàn zhe", "跟着": "gēn zhe", "觉得": "jué de",
        "一事无成": "yí shì wú chéng", "寄人篱下": "jì rén lí xià", "罚": "fá", "处": "chǔ", "重": "zhòng"}
MAXA = 10.8
FORCE_SPLIT = {"010": 2, "137": 2}  # failed twice as one clip  # Seedance max 15 s clip / 15 s audio ref; longer lines are split into chained parts
def pr(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True); return float(r.stdout.strip() or 0)
def split_line(line, n):
    parts = [x for x in re.split(r"(?<=[。？！])", line) if x.strip()]
    if len(parts) < n: parts = [x for x in re.split(r"(?<=[，。？！；])", line) if x.strip()]
    best = None
    for cut in __import__("itertools").combinations(range(1, len(parts)), n - 1):
        segs = ["".join(parts[i:j]) for i, j in zip((0,) + cut, cut + (len(parts),))]
        sc_ = max(len(x) for x in segs)
        if best is None or sc_ < best[0]: best = (sc_, segs)
    return best[1]
units = []  # (sid, part id, line, tts path, tts dur)
for sid in ids:
    s = next(x for x in m.SHOTS if x["id"] == sid); m.tts(s); td = pr(m.tts_path(s))
    if td <= MAXA and sid not in FORCE_SPLIT:
        units.append((s, sid, s["line"], m.tts_path(s), td)); continue
    n = max(math.ceil(td / MAXA), FORCE_SPLIT.get(sid, 1))
    for k, seg in enumerate(split_line(s["line"], n)):
        ps = {**s, "line": seg}; m.tts(ps); units.append((s, f"{sid}{'abc'[k]}", seg, m.tts_path(ps), pr(m.tts_path(ps))))
shots, chains, lastkey = [], [], {}
for s, uid, line, tts, td in units:
    sid, who = s["id"], s["who"]; ang0, perf, cam = SHOT[sid]
    ang = ang0 or ("cam" if s["pic"].endswith("_cam") else "side")
    if td < 2.3:  # Ark wants reference audio of 2-30 s: pad short lines with trailing silence
        pad = Path("studio") / f"aref_{uid}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tts), "-af", "apad=pad_dur=1.5", "-ar", "24000", str(pad)])
        tts = pad.resolve()
    pron = [f"{k}（{v}）" for k, v in PRON.items() if k in line]
    whole = f"（这是整句台词“{s['line']}”中的一段，只说这一段）" if line != s["line"] else ""
    p = ["【GLOBAL STYLE】" + STYLE, "【SCENE】回声号演播室。", "【CHARACTERS】" + CHAR[who] + " 画面中只有这一个人物，另一位角色不出画。",
         SEAT[(who, ang)] + "绝不换座位，绝不换背景。", POSTURE[who],
         "【PROPS】" + ("老渡手里不拿任何东西，左手腕上始终戴着黄铜机械表。" if who == "老渡" else "小柚手里不拿任何东西。"),
         "【LIGHTING】温暖的琥珀色主光从画面上方偏左照下，人物脸上有柔和的轮廓光。",
         f"【SHOT】{cam}。表演：{perf}。表情和动作自然、有分寸，不夸张。",
         f"【DIALOGUE】{who}开口说话，口型与台词逐字同步。{VOICE[who]}。台词（一字不改）：“{line}”{whole}。"
         "台词只说一遍：一字不多、一字不少，不重复、不卡顿、不结巴；说完最后一个字就闭上嘴，不再说任何话，只保持表情和轻微动作直到镜头结束。"]
    if pron: p.append("【PRONUNCIATION】多音字读音：" + "，".join(pron) + "。")
    p += [f"【AUDIO REFERENCE】音频1就是这句台词的完整配音：{who}的口型严格对齐音频1逐字说出，声音、语速、停顿、语气与音频1完全一致，就是同一段声音。",
          "【POSITIVE LOCKS】服装、发型、眼镜、耳机、手表与图1完全一致；座位、朝向和背景与图2完全一致。",
          "【AUDIO】只有这一句对白和安静的室内环境声。不要背景音乐，不要其他人说话。"]
    shots.append({"id": uid, "shot": sid, "who": who, "angle": ang, "line": line, "duration": max(4, min(15, math.ceil(td * 1.15 + 1))), "tts_dur": round(td, 2),
                  "refs": REF[who], "audio_refs": [str(tts)], "prompt": "\n".join(p)})
    k = (who, ang); prev = lastkey.get(k)
    if prev is not None and int(sid) - int(prev[0]) <= 4: chains[prev[1]].append(uid)
    else: chains.append([uid])
    lastkey[k] = (sid, next(i for i, c in enumerate(chains) if c[-1] == uid))
plan = {"shots": shots, "chains": chains}
Path("studio").mkdir(exist_ok=True)
Path(f"studio/plan_{name}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(s["duration"] for s in shots)
print(len(shots), "clips", tot, "s ≈", round(tot * 0.5, 1), "CNY (mini 720p)")
for c in chains: print(" chain", c)
for s in shots:
    if s["id"] != s["shot"] or s["tts_dur"] > 12: print(" ", s["id"], s["tts_dur"], s["line"])
