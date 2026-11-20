"""EP05 studio shots (Seedance 2.0 mini, 15 s cap) → studio/plan_<name>.json  (python studio_plan.py <name> <shot ids...>)"""
import json, math, re, sys, subprocess
from pathlib import Path
sys.argv, args = ["x", "none"], sys.argv[1:]
import make_ep05 as m
name, ids = args[0], args[1:]
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖琥珀色吊灯主调加一点窗外的冷色夜光，浅景深，怀旧但干净精致。画面中不出现任何字幕、文字、水印、标志、商标。"
CHAR = {"老渡": "老渡（图1）：中国男性，约38岁，短寸头，鬓角微白，浅胡茬；简洁利落的黑色皮夹克，内搭黑色圆领T恤，深色牛仔裤，左手腕戴黄铜表壳机械表。性格沉稳、温厚、有书卷气。",
        "小柚": "小柚（图1）：中国女生，约23岁，齐肩的黑色短发，左侧别着柚子形小发夹，细边圆框眼镜；宽松的复古棒球夹克（奶白色衣身、墨绿色袖子，没有任何字母和徽章），里面是白色圆领T恤。不戴耳机。性格温柔可爱、文静，偶尔俏皮。"}
REF = {"老渡": ["look/lookclip_ld_t1_last.png", "look/plate_ld_s.jpg"], "小柚": ["look/lookclip_xy_t2_last.png", "look/plate_xy_s.jpg"]}  # Seedance-made look frames (Seedream stills with faces are refused)
SETD = {"老渡": "回声号这一期的演播室：1990年代初美国加州公路边一家通宵营业的老式美式餐馆，深红色皮革软包卡座，镀铬包边的米白色台面上有厚瓷白咖啡杯和一壶咖啡，头顶暖黄色吊灯，窗外是深夜湿漉漉的停车场和路灯。",
        "小柚": "回声号这一期的演播室：1990年代初美国加州公路边一家通宵营业的老式美式餐馆，深红色皮革软包卡座，挂着百叶帘的玻璃窗外是深夜的停车场和远处模糊的霓虹，桌上有厚瓷白咖啡杯和一壶咖啡，头顶暖黄色吊灯。"}
SEAT = {
 ("老渡", "side"): "【SCREEN DIRECTION】老渡坐在图2的卡座里，身体朝向画面右侧，视线看向画面右侧（看着坐在桌子对面的小柚）。背景固定是图2：" + SETD["老渡"],
 ("老渡", "cam"):  "【SCREEN DIRECTION】老渡坐在图2的卡座里，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["老渡"],
 ("小柚", "side"): "【SCREEN DIRECTION】小柚坐在图2的卡座里，身体朝向画面左侧，视线看向画面左侧（看着坐在桌子对面的老渡）。背景固定是图2：" + SETD["小柚"],
 ("小柚", "cam"):  "【SCREEN DIRECTION】小柚坐在图2的卡座里，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["小柚"],
}
POSTURE = {"老渡": "【POSTURE】坐姿放松但端正，背靠卡座靠背，双手自然放在桌面上，或一只手轻扶咖啡杯。",
           "小柚": "【POSTURE】小柚端正地坐在卡座上，腰背挺直，上半身高出桌面，人和座位比例正常，绝不陷进座位里，不缩成一团。"}
VOICE = {"老渡": "老渡的声音：低沉温厚的男中音，标准普通话，沉稳从容，有书卷气",
         "小柚": "小柚的声音：温柔甜美的年轻女声，标准普通话，轻柔自然，不夸张、不一惊一乍"}
SHOT = {  # id: (angle or None = from pic, 表演, 运镜)
 "007": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众打招呼，说到'老餐馆'时目光稍稍扫一下窗外的停车场", "中近景，固定机位"),
 "008": (None, "小柚面向镜头，眼睛弯弯地笑，先轻轻挥手打招呼，说到'黑皮夹克'时笑着朝画面左侧（老渡的方向）瞥一眼，带一点调皮", "中近景，固定机位"),
 "009": (None, "老渡看着小柚，笑着承认，像被说中了，语气自然随意；说到'皮夹克'时右手轻轻拍一下自己的衣襟，头部保持稳定", "中近景，固定机位"),
 "010": (None, "小柚双手捧着咖啡杯，好奇地问，语气轻快、带着笑意", "中近景"),
 "011": (None, "老渡点点头，手指轻轻点了点桌面，语气温和，带一点怀旧", "中近景，固定机位"),
 "012": (None, "老渡望着窗外的夜色，若有所思，语气低缓、沉稳", "中近景，固定机位"),
 "012b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（刚把视线从窗外收回来），随即转向镜头，语气沉稳、有分量，说到'悬崖边'时目光坚定；开口就说，开头不停顿", "中近景，固定机位"),
 "016": (None, "小柚歪着头，认真地想，好奇地轻声问", "中近景，固定机位"),
 "017": (None, "老渡温和地笑了笑，语气缓慢而温厚，说到'心思全在里面'时轻轻点头", "中近景"),
 "024": (None, "小柚眼神有些湿润，声音很轻，语气温柔、有点心疼", "近景，固定机位"),
 "029": (None, "小柚缩了缩脖子，难以置信地轻声说，带一点自嘲的笑", "中近景，固定机位"),
 "030": (None, "老渡看着小柚，语气转暖，带着欣慰", "中近景，固定机位"),
 "030b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（看着小柚），随即转向镜头，说到'一百个俯卧撑'时轻轻笑一下；开口就说，开头不停顿", "中近景，固定机位"),
 "039": (None, "小柚掰着手指头数，说完惊讶地看着老渡", "中近景"),
 "040": (None, "老渡平静地看着小柚，语气沉稳，说到'攥得格外紧'时右手轻轻握拳", "中近景，固定机位"),
 "047": (None, "小柚忍不住笑出来，俏皮地说", "中近景，固定机位"),
 "048": (None, "老渡也笑了，看着小柚，语气温暖风趣，像在讲一件可爱的往事", "中近景，固定机位"),
 "048b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（看着小柚），随即转向镜头，带着笑意，像讲到一个可爱的小细节；开口就说，开头不停顿", "中近景，固定机位"),
 "057": (None, "小柚睁大眼睛，半信半疑地问。注意：台词是'他看这个年轻人顺眼'，'年轻人'和'顺眼'之间没有'是'字，绝不能加字", "中近景，固定机位"),
 "058": (None, "老渡笑着点点头，语气笃定、温和", "中近景，固定机位"),
 "069": (None, "小柚皱了皱眉，不解地问", "中近景，固定机位"),
 "070": (None, "老渡面向镜头，语气坚定有力，但不喊叫。注意：结尾是'他一说就是三十多年'，'就'字必须清楚说出来，绝不能漏", "中近景，固定机位"),
 "080": (None, "小柚身体微微前倾，认真地问", "中近景，固定机位"),
 "081": (None, "老渡轻轻摇头，语气沉稳，说到'没有松手'时加重语气", "中近景"),
 "092": (None, "小柚轻轻笑了一下，语气温柔，带一点感慨", "中近景，固定机位"),
 "100": (None, "小柚望着窗外想了想，轻声问", "中近景，固定机位"),
 "101": (None, "老渡面向镜头，语气温柔而郑重，说到'长成什么样子'时微微一笑", "中近景，固定机位"),
 "102": (None, "小柚托着下巴，认真地问", "中近景，固定机位"),
 "103": (None, "老渡微微一笑，卖个关子，语气从容", "中近景，固定机位"),
 "106": (None, "小柚恍然大悟地笑了，语气温柔", "中近景，固定机位"),
 "110": (None, "老渡看着小柚，语气沉稳、带着书卷气，引用古文时一字一顿但不拖沓", "中近景，固定机位"),
 "110b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（看着小柚），随即转向镜头，语气沉稳有力；开口就说，开头不停顿", "中近景，固定机位"),
 "116": (None, "老渡望着桌上的咖啡杯，语气低缓，像在回顾一段长路。注意：'九岁那台录音机'里的'那台'两个字必须清楚说出来，一个字都不能漏", "中近景，固定机位"),
 "116b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（还看着桌上的咖啡杯），随即抬起头面向镜头，语气坚定有力，但不喊叫；开口就说，开头不停顿。注意：'离倒闭只有三十天'里的'只有'两个字必须清楚说出来，绝不能说成'离倒闭有三十天'", "中近景，固定机位"),
 "117": (None, "老渡面向镜头，温和地微笑，举起咖啡杯轻轻示意，向观众告别", "中近景，固定机位"),
}
PRON = {"黄仁勋": "huáng rén xūn", "英伟达": "yīng wěi dá", "入交昭一郎": "rù jiāo zhāo yī láng", "渡叔": "dù shū", "卡座": "kǎ zuò",
        "行头": "xíng tou", "还不敢": "hái bù gǎn", "还在": "hái zài", "还跳了": "hái tiào le", "一聊聊": "yì liáo liáo", "攥得": "zuàn de",
        "落款": "luò kuǎn", "长成": "zhǎng chéng", "苦其心志": "kǔ qí xīn zhì", "劳其筋骨": "láo qí jīn gǔ", "大任": "dà rèn", "是人也": "shì rén yě",
        "钟头": "zhōng tóu", "砍了": "kǎn le", "CUDA": "库达", "倒闭": "dǎo bì", "卧推": "wò tuī", "俯卧撑": "fǔ wò chēng"}
REF_RATE = -15
PACE = {"老渡": "语速、节奏和停顿完全以音频1为准：语速从容，逗号处换一口气，句号处稍作停顿，一句一句、一个字一个字说清楚，吐字清晰饱满，像在灯下讲故事；节奏平稳舒缓，不抢拍、不连读、不含糊。说话时头部保持稳定，只有自然的表情和轻微的手势，不低头、不转头、不摇头。",
        "小柚": "语速与音频1一致，轻快自然，句与句之间只停顿半秒左右，绝不长时间停顿发呆。"}
MAXA = 12.5  # Seedance 2.0: clips <= 15 s and audio refs 2-15 s; longer lines were split in the script (never a/b-stitch one line)
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
TOO_LONG = []
units = []  # (sid, part id, line, tts path, tts dur)
for sid in ids:
    s = next(x for x in m.SHOTS if x["id"] == sid); m.tts(s)
    if s["who"] == "老渡":  # 11-13 user: 老渡 sounded '烫嘴' -> reference = untightened TTS at ~85% speed (guides: slower reference gives the lip-sync room)
        ps = {**s, "rate": REF_RATE}; m.tts(ps); ref = m.tts_path(ps)
    else:
        ref = m.voice(s)
    td = pr(ref)  # audio ref = pause-tightened TTS: Seedance copies (and stretches) the reference pauses
    if td <= MAXA and sid not in FORCE_SPLIT:
        units.append((s, sid, s["line"], ref, td)); continue
    TOO_LONG.append(f'{sid} {s["who"]} {td:.1f}s {s["line"]}'); continue
    n = max(math.ceil(td / MAXA), FORCE_SPLIT.get(sid, 1))
    for k, seg in enumerate(split_line(s["line"], n)):
        ps = {**s, "line": seg}; m.tts(ps); units.append((s, f"{sid}{'abc'[k]}", seg, m.voice(ps), pr(m.voice(ps))))
if TOO_LONG:
    print('TOO LONG (> %.1f s):' % MAXA); print('\n'.join(TOO_LONG)); raise SystemExit(1)
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
    p = ["【GLOBAL STYLE】" + STYLE, "【SCENE】回声号演播室（本期布置成1990年代初加州公路边的通宵美式餐馆卡座）。", "【CHARACTERS】" + CHAR[who] + " 画面中只有这一个人物，另一位角色不出画。",
         SEAT[(who, ang)] + "绝不换座位，绝不换背景。", POSTURE[who],
         "【PROPS】" + ("老渡手里不拿任何东西，左手腕上始终戴着黄铜机械表。" if who == "老渡" else "小柚手里不拿任何东西，左侧始终别着柚子形发夹。"),
         "【LIGHTING】头顶暖黄色吊灯从上方偏侧照下，窗外是深夜停车场的冷色路灯和模糊霓虹，人物脸上有柔和的轮廓光。",
         f"【SHOT】{cam}。表演：{perf}。表情和动作自然、有分寸，不夸张。",
         f"【DIALOGUE】{who}说话的语音内容就是音频1，口型与音频1逐字同步。{VOICE[who]}。台词（一字不改）：“{line}”{whole}。"
         "台词只说一遍：一字不多、一字不少，不重复、不卡顿、不结巴；说完最后一个字就闭上嘴，不再说任何话，只保持表情和轻微动作直到镜头结束。" + PACE[who]]
    if pron: p.append("【PRONUNCIATION】多音字读音：" + "，".join(pron) + "。")
    p += [f"【AUDIO REFERENCE】音频1就是这句台词的完整配音：{who}的口型严格对齐音频1逐字说出，声音、语速、停顿、语气与音频1完全一致，就是同一段声音。",
          "【POSITIVE LOCKS】服装、发型、眼镜、发夹、手表与图1完全一致；座位、朝向和背景与图2完全一致。画面上绝对不出现字幕、台词文字或任何文字。",
          "【AUDIO】只有这一句对白和安静的室内环境声。不要背景音乐，不要其他人说话。"]
    shots.append({"id": uid, "shot": sid, "who": who, "angle": ang, "line": line, "duration": max(4, min(15, math.ceil(td * (1.12 if who == "老渡" else 1.08) + (1.0 if who == "老渡" else 0.8)))), "tts_dur": round(td, 2),
                  "refs": REF[who], "audio_refs": [str(tts)], "prompt": "\n".join(p)})
    k = (who, ang); prev = lastkey.get(k)
    base = next((i for i, c in enumerate(chains) if c[-1] == sid[:-1]), None) if sid.endswith("b") else None
    if base is not None: chains[base].append(uid)  # 11-13 user "两段的衔接要做好": the 2nd half of a split line is generated right after the 1st, from its last frame (pose/light continuity)
    elif prev is not None and int(sid[:3]) - int(prev[0][:3]) <= 4: chains[prev[1]].append(uid)
    else: chains.append([uid])
    lastkey[k] = (sid, next(i for i, c in enumerate(chains) if c[-1] == uid))
plan = {"shots": shots, "chains": chains}
Path("studio").mkdir(exist_ok=True)
Path(f"studio/plan_{name}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(s["duration"] for s in shots)
print(len(shots), "clips", tot, "s ≈", round(tot * 21600 * 23 / 1e6), "CNY (2.0 mini 720p)")
for c in chains: print(" chain", c)
for s in shots:
    if s["id"] != s["shot"] or s["tts_dur"] > 12: print(" ", s["id"], s["tts_dur"], s["line"])
