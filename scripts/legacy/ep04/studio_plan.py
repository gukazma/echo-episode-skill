"""EP04 studio shots (Seedance 2.5) → studio/plan_<name>.json  (python studio_plan.py <name> <shot ids...>)"""
import json, math, re, sys, subprocess
from pathlib import Path
sys.argv, args = ["x", "none"], sys.argv[1:]
import make_ep04 as m
name, ids = args[0], args[1:]
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖琥珀色钨丝灯主调，浅景深，昭和怀旧但干净精致。画面中不出现任何字幕、文字、水印、标志。"
CHAR = {"老渡": "老渡（图1）：中国男性，约38岁，短寸头，鬓角微白，浅胡茬；驼色灯芯绒西装外套，内搭米白色高领针织衫，深棕色西裤，左手腕戴黄铜表壳机械表。性格沉稳、温厚、有书卷气。",
        "小柚": "小柚（图1）：中国女生，约23岁，乌黑浓密的'幸子头'短发（齐耳到下颌，层次多、头顶蓬松，发尾向内收成圆弧盖住耳朵，打薄的碎刘海从中间微微分开），左侧别着柚子形小发夹，细边圆框眼镜；奶白色粗棒针开衫，里面是浅粉色碎花小圆领连衣裙。不戴耳机。性格温柔可爱、文静，偶尔俏皮。"}
REF = {"老渡": ["look/lookclip_ld_t1_last.png", "look/plate_ld.jpg"], "小柚": ["look/lookclip_xy_t5_last.png", "look/plate_xy.jpg"]}  # Seedream stills are refused as real persons; Seedance-made frames pass (11-12 user chose 小柚 A)
SETD = {"老渡": "回声号这一期的演播室：1980年东京的老式名曲喫茶，背后是满墙黑胶唱片架和黄铜壁灯，左侧是挂着蕾丝窗帘的雨夜玻璃窗、木壳黑胶唱机和插着秋樱的小花瓶。",
        "小柚": "回声号这一期的演播室：1980年东京的老式名曲喫茶，背后是挂着蕾丝窗帘的雨夜玻璃窗、黑胶唱片架、白色老式立式话筒架，她身旁小圆木桌上有黑胶唱机和插着秋樱的小花瓶。"}
SEAT = {
 ("老渡", "side"): "【SCREEN DIRECTION】老渡坐在图2那把棕色皮质扶手椅上，身体朝向画面右侧，视线看向画面右侧（看着坐在对面的小柚）。背景固定是图2：" + SETD["老渡"],
 ("老渡", "cam"):  "【SCREEN DIRECTION】老渡坐在图2那把棕色皮质扶手椅上，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["老渡"],
 ("小柚", "side"): "【SCREEN DIRECTION】小柚坐在图2那把焦糖色皮质扶手椅上，身体朝向画面左侧，视线看向画面左侧（看着坐在对面的老渡）。背景固定是图2：" + SETD["小柚"],
 ("小柚", "cam"):  "【SCREEN DIRECTION】小柚坐在图2那把焦糖色皮质扶手椅上，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["小柚"],
}
POSTURE = {"老渡": "【POSTURE】坐姿放松但端正，背靠椅背，双手自然放在扶手或腿上。",
           "小柚": "【POSTURE】小柚端正地坐在坐垫上，腰背挺直，臀部坐实在坐垫上，扶手只到她的腰部，肩膀和整个上半身都高出扶手；人和椅子的比例正常，绝不陷进沙发里，不缩成一团。"}
VOICE = {"老渡": "老渡的声音：低沉温厚的男中音，标准普通话，沉稳从容，有书卷气",
         "小柚": "小柚的声音：温柔甜美的年轻女声，标准普通话，轻柔自然，不夸张、不一惊一乍"}
SHOT = {  # id: (angle or None = from pic, 表演, 运镜)
 "007": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众打招呼，说到'老咖啡馆'时目光稍稍扫一下身边的唱片墙", "中近景，固定机位"),
 "008": (None, "小柚面向镜头，眼睛弯弯地笑，先轻轻挥手打招呼，说到'像不像幸子'时侧过头、用一只手轻轻碰了碰自己的发尾，带一点小得意", "中近景，固定机位"),
 "009": (None, "老渡看着小柚，端详了一下她的发型，笑着点点头，语气自然随意，像聊天时随口接话，开口就说，开头不停顿", "中近景"),
 "010": (None, "小柚开心地说起妈妈，语气轻快、带着笑意，说到'看一集哭一集'时忍不住笑出来", "中近景"),
 "011": (None, "老渡温和地微笑，右手掌心向上轻轻向身边的唱片墙一摊，像在介绍这个地方，语气沉稳、带一点神秘", "中近景，固定机位"),
 "017": (None, "小柚若有所思，轻声猜测，语气温柔，说完微微歪头看着老渡", "近景，固定机位"),
 "018": (None, "老渡看着小柚，轻轻点头，先肯定她，再缓缓说下去，语气温厚", "中近景"),
 "022": (None, "小柚忍不住笑，带点调侃地看着老渡，说到'可别这样'时用手指轻轻点了一下老渡的方向", "中近景"),
 "024": (None, "小柚面向镜头，像个小侦探一样一本正经地总结，说到'对得上'时俏皮地点一下头", "中近景，固定机位"),
 "037": (None, "小柚睁大眼睛，带着笑意轻声感叹，有点害羞", "近景"),
 "043": (None, "小柚面向镜头，嘴角上扬，语气温柔又带点羡慕", "中近景，固定机位"),
 "046": (None, "小柚有点不好意思地笑着讲自己的小事，说到'在吗'时缩了一下肩膀，自嘲地笑", "中近景"),
 "068": (None, "小柚面向镜头，笑着摸了摸自己的发尾，语气轻快", "中近景，固定机位"),
 "072": (None, "小柚抬起一只手轻轻示意'等一下'，带着疑惑认真地问", "中近景"),
 "073": (None, "老渡轻轻摇头，语气平稳而肯定，说到'自己拿的主意'时稍稍加重语气", "中近景"),
 "075": (None, "小柚面向镜头，若有所思地轻声说，语气温柔，带一点感慨", "近景，固定机位"),
 "084": (None, "小柚笑着打趣，眉毛一挑，语气轻快", "中近景"),
 "088": (None, "小柚面向镜头，忍不住笑，轻轻摇头", "中近景，固定机位"),
 "100": (None, "小柚望着老渡，轻声问，带着关切", "近景，固定机位"),
 "101": (None, "老渡轻轻点头，先低声应一句，再带一点卖关子的神情说下去", "中近景"),
 "103": (None, "小柚面向镜头，笑着摇摇头，带着感动和一点意外", "近景，固定机位"),
 "107": (None, "小柚笑着感叹，语气轻快，轻轻摇头", "中近景"),
 "113": (None, "小柚神情认真，语气轻柔而郑重，带着敬佩", "近景，固定机位"),
 "123": (None, "小柚面向镜头，半开玩笑地表示怀疑，眯了一下眼睛", "中近景，固定机位"),
 "126": (None, "老渡笑着摇头，语气温和，说到'合得来'时轻轻点头", "中近景"),
 "128": (None, "小柚学着说那句吐槽，说完自己先笑了出来", "中近景"),
 "137": (None, "小柚好奇地轻声问，眼睛亮亮的，带着笑", "中近景"),
 "139": (None, "小柚面向镜头，认真地问，语气温柔而郑重", "近景，固定机位"),
 "140": (None, "老渡面向镜头，语气沉稳，说到'谢谢你'那几句时放轻、放慢，带着温度", "中近景，极慢推近"),
 "141": (None, "小柚眼神温柔，轻声说，嘴角带着笑意", "近景，固定机位"),
 "142": (None, "老渡缓缓吟出诗句，语气沉静有韵味，说到'一句约定'时看向小柚", "中近景"),
 "143": (None, "老渡面向镜头，语气沉稳、温暖而有力量，说到'没有落空'时轻轻点头", "中近景，极慢推近"),
 "149": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众告别", "中近景，固定机位"),
}
PRON = {"山口百惠": "shān kǒu bǎi huì", "三浦友和": "sān pǔ yǒu hé", "幸子": "xìng zǐ", "渡叔": "dù shū", "血疑": "xuè yí", "相性": "xiāng xìng",
        "祐太朗": "yòu tài lǎng", "一辈子": "yí bèi zi", "那会儿": "nà huìr", "拿的主意": "ná de zhǔ yi", "调": "diào", "还真": "hái zhēn",
        "还以为": "hái yǐ wéi", "朝": "cháo", "契阔": "qì kuò", "死生契阔": "sǐ shēng qì kuò", "死生": "sǐ shēng", "说": "shuō", "成说": "chéng shuō", "偕老": "xié lǎo", "得多": "de duō",
        "得见": "de jiàn", "得真": "de zhēn", "觉得": "jué de", "看着": "kàn zhe", "背": "bēi", "落空": "luò kōng", "没变": "méi biàn", "长": "zhǎng"}
for _k in ("说", "调", "朝", "背", "长"):  # only multi-char hints; single chars mis-fire
    PRON.pop(_k, None)
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
    p = ["【GLOBAL STYLE】" + STYLE, "【SCENE】回声号演播室（本期布置成1980年东京的名曲喫茶）。", "【CHARACTERS】" + CHAR[who] + " 画面中只有这一个人物，另一位角色不出画。",
         SEAT[(who, ang)] + "绝不换座位，绝不换背景。", POSTURE[who],
         "【PROPS】" + ("老渡手里不拿任何东西，左手腕上始终戴着黄铜机械表。" if who == "老渡" else "小柚手里不拿任何东西，左侧始终别着柚子形发夹。"),
         "【LIGHTING】温暖的钨丝灯和黄铜台灯光从画面上方偏侧照下，窗外是雨夜东京的模糊霓虹，人物脸上有柔和的轮廓光。",
         f"【SHOT】{cam}。表演：{perf}。表情和动作自然、有分寸，不夸张。",
         f"【DIALOGUE】{who}开口说话，口型与台词逐字同步。{VOICE[who]}。台词（一字不改）：“{line}”{whole}。"
         "台词只说一遍：一字不多、一字不少，不重复、不卡顿、不结巴；说完最后一个字就闭上嘴，不再说任何话，只保持表情和轻微动作直到镜头结束。语速与音频1一致，紧凑自然，句与句之间只停顿半秒左右，绝不长时间停顿发呆。"]
    if pron: p.append("【PRONUNCIATION】多音字读音：" + "，".join(pron) + "。")
    p += [f"【AUDIO REFERENCE】音频1就是这句台词的完整配音：{who}的口型严格对齐音频1逐字说出，声音、语速、停顿、语气与音频1完全一致，就是同一段声音。",
          "【POSITIVE LOCKS】服装、发型、眼镜、发夹、手表与图1完全一致；座位、朝向和背景与图2完全一致。画面上绝对不出现字幕、台词文字或任何文字（224_t1 曾自带字幕）。",
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
