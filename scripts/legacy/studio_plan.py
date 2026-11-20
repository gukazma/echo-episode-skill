"""EP03 studio shots (Seedance 2.5) → studio/plan_<name>.json  (python studio_plan.py <name> <shot ids...>)"""
import json, math, re, sys, subprocess
from pathlib import Path
sys.argv, args = ["x", "none"], sys.argv[1:]
import make_ep03 as m
name, ids = args[0], args[1:]
E1 = "../echo_ep01_final/"
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖琥珀色主调，浅景深。画面中不出现任何字幕、文字、水印、标志。"
CHAR = {"老渡": "老渡（图1）：中国男性，约38岁，短寸头，鬓角微白，浅胡茬；深橄榄绿飞行员夹克，内搭黑色圆领T恤，左手腕戴黄铜表壳机械表。性格沉稳、温厚。",
        "小柚": "小柚（图1）：中国女生，约23岁，齐肩短发，左侧别着柚子形发夹，细边圆框眼镜；宽松的橙色连帽卫衣，白色头戴式耳机挂在脖子上。性格温柔可爱、文静。"}
REF = {"老渡": [E1 + "img/c_laodu.png", E1 + "img/s_bg_laodu.png"], "小柚": [E1 + "clips/S06x_t3_last.png", "../echo_ep02/studio/bg_xiaoyou_v1.png"]}
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
 "009": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众打招呼，说到'爱讲老故事'时嘴角微微上扬", "中近景，固定机位"),
 "010": (None, "小柚面向镜头，眼睛弯弯地笑，右手在胸前轻轻挥了一下打招呼，然后双手放回腿上，说话轻柔", "中近景，固定机位"),
 "011": (None, "老渡微笑着，右手掌心向上轻轻向身后的舷窗方向一摊，像在介绍这艘船，语气沉稳而带着一点神秘", "中近景，极慢推近"),
 "013": (None, "小柚眼睛一亮，轻轻笑着，语气温柔、带一点小得意，像在猜谜，说到最后微微歪头向老渡确认", "中近景"),
 "067": (None, "小柚吃惊地轻轻睁大眼睛，小声重复，带着不敢相信和心疼", "近景，固定机位"),
 "141": (None, "小柚眼神湿润，轻轻叹了口气，声音轻柔而心疼，说完微微低下头", "近景，固定机位"),
 "146": (None, "小柚若有所思，轻声重复这句话，眼神温柔而郑重", "近景，固定机位"),
 "192": (None, "老渡神情凝重，双手交握放在腿上，语气沉稳而有分量，说到'注定是逆风'时轻轻点头", "中近景"),
 "208": (None, "老渡身体微微前倾，看着小柚，语气越来越坚定，说到'让法律自己说话'时加重语气，但不喊叫", "中近景，缓推"),
 "216": (None, "小柚望着老渡，轻声问，带着期待和一点担心", "近景"),
 "220": (None, "小柚眼含泪光，慢慢地说，声音温柔，带着敬意", "近景，固定机位"),
 "221": ("side", "小柚望着老渡，好奇地轻声问，右手食指轻轻点了点下巴", "中近景"),
 "224": (None, "小柚面向镜头，眼神湿润，语气温柔而惋惜，说到'好像并没有好好对待他们'时声音轻轻发颤", "中近景，固定机位"),
 "225": (None, "老渡沉默片刻后缓缓开口，语气低沉克制，强忍着悲伤，说完轻轻闭了一下眼睛", "中近景，极慢推近"),
 "226": (None, "老渡面向镜头，语气沉稳坚定，眼神温暖，说到'普通人这一边'时轻轻点头", "中近景，极慢推近"),
 "227": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众告别", "中近景，固定机位"),
}
PRON = {"文在寅": "wén zài yín", "卢武铉": "lú wǔ xuàn", "李明博": "lǐ míng bó", "重逢": "chóng féng", "曝光": "bào guāng", "见不得光": "jiàn bù dé guāng", "循着": "xún zhe", "一辈子": "yí bèi zi", "渡叔": "dù shū", "给了": "gěi le", "颗": "kē", "背过": "bèi guò", "还寄": "hái jì", "还在": "hái zài", "还是": "hái shì", "差一点": "chà yì diǎn", "差点": "chà diǎn", "为了": "wèi le",
        "为什么": "wèi shén me", "答应": "dā ying", "宁愿": "nìng yuàn", "扛了": "káng le", "累倒": "lèi dǎo", "强大": "qiáng dà", "只能": "zhǐ néng",
        "不只是": "bù zhǐ shì", "中道崩殂": "zhōng dào bēng cú", "翻了身": "fān le shēn", "都会": "dōu huì", "都有": "dōu yǒu", "都给": "dōu gěi",
        "全都": "quán dōu", "睡得": "shuì de", "撑得": "chēng de", "得更": "de gèng", "看着": "kàn zhe", "跟着": "gēn zhe", "觉得": "jué de",
        "一事无成": "yí shì wú chéng", "寄人篱下": "jì rén lí xià", "罚": "fá", "处": "chǔ", "重": "zhòng"}
for _k in ("重逢",):  # 重逢 is chóng, not the generic 重 zhòng
    PRON.pop("重", None)
MAXA = 25.0  # Seedance 2.5 takes up to 30 s clips / audio refs: keep a line in one clip (a split mid-line shows as a jump cut)
FORCE_SPLIT = {}  # 2.5: never split a line (the seam between two clips is heard as a stutter - user 11-11)
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
    s = next(x for x in m.SHOTS if x["id"] == sid); m.tts(s); td = pr(m.voice(s))  # audio ref = pause-tightened TTS: Seedance copies (and stretches) the reference pauses
    if td <= MAXA and sid not in FORCE_SPLIT:
        units.append((s, sid, s["line"], m.voice(s), td)); continue
    n = max(math.ceil(td / MAXA), FORCE_SPLIT.get(sid, 1))
    for k, seg in enumerate(split_line(s["line"], n)):
        ps = {**s, "line": seg}; m.tts(ps); units.append((s, f"{sid}{'abc'[k]}", seg, m.voice(ps), pr(m.voice(ps))))
shots, chains, lastkey = [], [], {}
for s, uid, line, tts, td in units:
    sid, who = s["id"], s["who"]; ang0, perf, cam = SHOT[sid]
    ang = ang0 or ("cam" if s["pic"].endswith("_cam") else "side")
    if td < 2.3:  # Ark wants reference audio of 2-30 s: pad short lines with trailing silence
        pad = Path("studio") / f"aref_{uid}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tts), "-af", "apad=pad_dur=1.5", "-ar", "24000", str(pad)])
        tts = pad.resolve()
    pron = [f"{k}（{v}）" for k, v in PRON.items() if k in line and not any(k != k2 and k in k2 and k2 in line for k2 in PRON)]
    whole = f"（这是整句台词“{s['line']}”中的一段，只说这一段）" if line != s["line"] else ""
    p = ["【GLOBAL STYLE】" + STYLE, "【SCENE】回声号演播室。", "【CHARACTERS】" + CHAR[who] + " 画面中只有这一个人物，另一位角色不出画。",
         SEAT[(who, ang)] + "绝不换座位，绝不换背景。", POSTURE[who],
         "【PROPS】" + ("老渡手里不拿任何东西，左手腕上始终戴着黄铜机械表。" if who == "老渡" else "小柚手里不拿任何东西。"),
         "【LIGHTING】温暖的琥珀色主光从画面上方偏左照下，人物脸上有柔和的轮廓光。",
         f"【SHOT】{cam}。表演：{perf}。表情和动作自然、有分寸，不夸张。",
         f"【DIALOGUE】{who}开口说话，口型与台词逐字同步。{VOICE[who]}。台词（一字不改）：“{line}”{whole}。"
         "台词只说一遍：一字不多、一字不少，不重复、不卡顿、不结巴；说完最后一个字就闭上嘴，不再说任何话，只保持表情和轻微动作直到镜头结束。语速与音频1一致，紧凑自然，句与句之间只停顿半秒左右，绝不长时间停顿发呆。"]
    if pron: p.append("【PRONUNCIATION】多音字读音：" + "，".join(pron) + "。")
    p += [f"【AUDIO REFERENCE】音频1就是这句台词的完整配音：{who}的口型严格对齐音频1逐字说出，声音、语速、停顿、语气与音频1完全一致，就是同一段声音。",
          "【POSITIVE LOCKS】服装、发型、眼镜、耳机、手表与图1完全一致；座位、朝向和背景与图2完全一致。画面上绝对不出现字幕、台词文字或任何文字（224_t1 曾自带字幕）。",
          "【AUDIO】只有这一句对白和安静的室内环境声。不要背景音乐，不要其他人说话。"]
    shots.append({"id": uid, "shot": sid, "who": who, "angle": ang, "line": line, "duration": max(4, min(30, math.ceil(td * 1.08 + 0.8))), "tts_dur": round(td, 2),
                  "refs": REF[who], "audio_refs": [str(tts)], "prompt": "\n".join(p)})
    k = (who, ang); prev = lastkey.get(k)
    if prev is not None and int(sid) - int(prev[0]) <= 4: chains[prev[1]].append(uid)
    else: chains.append([uid])
    lastkey[k] = (sid, next(i for i, c in enumerate(chains) if c[-1] == uid))
plan = {"shots": shots, "chains": chains}
Path("studio").mkdir(exist_ok=True)
Path(f"studio/plan_{name}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(s["duration"] for s in shots)
print(len(shots), "clips", tot, "s ≈", round(tot * 21600 * 75 / 1e6), "CNY (2.5 720p)")
for c in chains: print(" chain", c)
for s in shots:
    if s["id"] != s["shot"] or s["tts_dur"] > 12: print(" ", s["id"], s["tts_dur"], s["line"])
