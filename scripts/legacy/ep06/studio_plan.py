"""EP06 studio shots (Seedance 2.0 fast 480p, 15 s cap) -> studio/plan_<name>.json  (python studio_plan.py <name> <shot ids...>)"""
import json, math, sys, subprocess
from pathlib import Path
sys.argv, args = ["x", "none"], sys.argv[1:]
import make_ep06 as m
name, ids = args[0], args[1:]
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，暖橙色黄昏光加室内钨丝灯，浅景深，温暖怀旧但干净精致。画面中不出现任何字幕、文字、数字、球衣号码、队徽、水印、标志、商标。"
CHAR = {"老渡": "老渡（图1）：中国男性，约38岁，短寸头，鬓角微白，浅胡茬；墨绿色粗针织开衫，内搭白色衬衫，深灰色长裤，左手腕戴黄铜表壳机械表。性格沉稳、温厚、有书卷气。",
        "小柚": "小柚（图1）：中国女生，约23岁，齐肩的黑色短发，左侧别着柚子形小发夹，细边圆框眼镜；正红色圆领粗针织毛衣，脖子上松松地围着一条红绿配色的针织围巾（没有任何文字和图案）。不戴耳机。性格温柔可爱、文静，偶尔俏皮。"}
REF = json.loads(Path("look/refs.json").read_text(encoding="utf-8"))  # {"老渡": [lookclip last frame, plate], "小柚": [...]} - Seedance-made frames (Seedream faces are refused)
SETD = {"老渡": "回声号这一期的演播室：葡萄牙里斯本老城一家傍晚的球迷小酒馆，墙面下半截是蓝白色手绘瓷砖，上半截是暖白色石灰墙，墙上挂着红绿配色的针织围巾，深色木桌木椅，桌上一杯咖啡和一小碟葡式蛋挞。",
        "小柚": "回声号这一期的演播室：葡萄牙里斯本老城一家傍晚的球迷小酒馆，身后是窗户，窗外是黄昏的石板坡道和模糊的黄色老电车，墙上挂着红绿配色的针织围巾，窗边小木桌上有咖啡和葡式蛋挞。"}
SEAT = {
 ("老渡", "side"): "【SCREEN DIRECTION】老渡坐在图2的木桌旁，身体朝向画面左侧，视线看向画面左侧（看着坐在桌子对面的小柚）。背景固定是图2：" + SETD["老渡"],
 ("老渡", "cam"):  "【SCREEN DIRECTION】老渡坐在图2的木桌旁，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["老渡"],
 ("小柚", "side"): "【SCREEN DIRECTION】小柚坐在图2的木椅上，身体朝向画面右侧，视线看向画面右侧（看着坐在桌子对面的老渡）。背景固定是图2：" + SETD["小柚"],
 ("小柚", "cam"):  "【SCREEN DIRECTION】小柚坐在图2的木椅上，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["小柚"],
}
POSTURE = {"老渡": "【POSTURE】坐姿放松但端正，双手自然放在桌面上，或一只手轻扶咖啡杯。",
           "小柚": "【POSTURE】小柚端正地坐在木椅上，腰背挺直，上半身高出桌面，人和椅子比例正常，绝不陷进椅子里，不缩成一团。"}
VOICE = {"老渡": "老渡的声音：低沉温厚的男中音，标准普通话，沉稳从容，有书卷气",
         "小柚": "小柚的声音：温柔甜美的年轻女声，标准普通话，轻柔自然，不夸张、不一惊一乍"}
F = "中近景，固定机位"
SHOT = {  # id: (angle or None = from pic, 表演, 运镜)
 "008": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众打招呼，说到'小酒馆'时目光稍稍扫一下四周", F),
 "008b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势，随即转向画面左侧的小柚，像在讲一个远方的故事；念'陆止于此，海始于斯'时语气郑重、稍稍放缓；开口就说，开头不停顿", "近景（胸像），固定机位，比上一个镜头明显更近的景别"),
 "008c": (None, "紧接上一句说下去：开头是上一个镜头结尾的姿势（看着小柚），随即转回镜头，温和地微微一笑，语气温暖、笃定；开口就说，开头不停顿", F),
 "009": (None, "小柚面向镜头，眼睛弯弯地笑，先轻轻挥手打招呼，说到'红绿围巾'时用手轻轻提一下脖子上的围巾，带一点调皮", F),
 "010": (None, "小柚歪着头，好奇地轻声问，后半句语气慢慢低下来", F),
 "011": (None, "老渡看着小柚，语气温柔、怀念，说到'不一样'时轻轻摇一下头。注意：两句之间只停顿半秒左右，接着往下说，停顿时不发呆", F),
 "011b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（看着小柚），随即转向镜头，语气温柔而郑重，说到'还回去了'时声音轻下来；开口就说，开头不停顿", "近景（胸像），固定机位，比上一个镜头明显更近的景别"),
 "012": (None, "老渡面向镜头，语气沉稳、有分量，像在讲一个开场白。注意：两句之间只停顿半秒左右，接着往下说，停顿时不发呆", F),
 "012b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势，随即转向画面左侧的小柚，说到'离倒闭只有三十天'时带一点笑意，说到'奔跑了二十三年'时目光坚定；开口就说，开头不停顿。注意：'为同一面旗帜'里'同一面'三个字要清清楚楚说出来", "近景（胸像），固定机位，比上一个镜头明显更近的景别"),
 "017": (None, "小柚眼神有些湿润，声音很轻，语气温柔、有点心疼", "近景，固定机位"),
 "018": (None, "老渡看着小柚，语气温柔、低缓，像在念一句诗，说到'回到它开始的地方'时目光坚定", F),
 "023": (None, "小柚忍不住笑出来，语气轻快、俏皮", F),
 "026": (None, "小柚认真地想了想，好奇地问。注意：结尾是'擦球鞋的人吧'，'球鞋'两个字必须说出来，绝不能说成'擦鞋子'", F),
 "027": (None, "老渡点点头，语气温和，说到'留了一段话'时轻轻点一下桌面。注意：'这样一群人'只有一个'群'字，绝不能说成'一群群人'", F),
 "034": (None, "小柚轻轻吸一口气，声音很轻，带一点自嘲的心疼", "近景，固定机位"),
 "038": (None, "小柚身体微微前倾，认真地问，语气心疼", F),
 "039": (None, "老渡平静地看着小柚，语气沉稳，说到'一文不值'时加重语气，但不喊叫", F),
 "044": (None, "小柚眼睛亮了一下，语气温柔、带一点感慨", F),
 "045": (None, "老渡轻轻点头，语气沉稳，说到'整整一个国家的梦'时加重语气", F),
 "053": (None, "小柚声音很轻，语气心疼、惋惜。语速与音频1一致，不要拖慢，说完就停", "近景，固定机位"),
 "062": (None, "小柚低下眼睛又抬起来，声音很轻，语气心疼", "近景，固定机位"),
 "063": (None, "老渡望着桌上的咖啡杯，像朗诵一首诗那样，语气低缓、深情，说到'渐行渐远'时声音轻下来；头部保持稳定", F),
 "069": (None, "小柚皱了皱眉，语气心疼又不平", F),
 "070": (None, "老渡看着小柚，像朗诵一首诗那样，语气越来越坚定有力，说到'飞扬'时目光明亮，后半句平稳有力", F),
 "081": (None, "小柚眼神里带着惋惜，声音很轻。注意：开口直接说台词，开口前不叹气、不哼声、不发出任何声音", "近景，固定机位"),
 "083": (None, "老渡看着小柚，语气平静而郑重", F),
 "083b": (None, "紧接上一句、同一口气说下去：开头是上一个镜头结尾的姿势（看着小柚），随即转向镜头，像朗诵一首诗那样，越念越坚定、越有力量，说到'相信未来'时目光坚定；开口就说，开头不停顿", "近景（胸像），固定机位，比上一个镜头明显更近的景别"),
 "096": (None, "小柚眼神湿润，声音很轻很柔，像在描述一件很珍贵的事", "近景，固定机位"),
 "101": (None, "小柚屏住呼吸，紧张地小声问。注意：'葡萄牙'只说一遍，绝不重复", F),
 "112": (None, "老渡面向镜头，语气温柔而有力量，说到'两行泪之间，隔着十二年'时放缓、郑重", F),
 "113": (None, "小柚开心地笑，望了一眼窗外，语气温暖。注意：结尾是'是熄着的吧'，'着'只说一次，绝不说成'熄着着'", F),
 "121": (None, "小柚声音很轻，语气心疼", "近景，固定机位"),
 "128": (None, "老渡面向镜头，像朗诵一首诗那样，语气坚定有力、越来越激昂，但不喊叫，说到'怒斥'时目光灼灼", F),
 "132": (None, "小柚声音轻下来，语气惋惜", "近景，固定机位"),
 "137": (None, "小柚身体微微前倾，好奇地问，语气温柔", F),
 "141": (None, "小柚声音很轻，眼神湿润，语气温柔、心疼。注意：'晚一步'只有一个'晚'字，绝不说成'晚晚一步'", "近景，固定机位"),
 "143": (None, "小柚坐在原位忍不住笑出来，语气俏皮。注意：一镜到底，绝不切到特写，人物不离开座位、不凑近镜头", F),
 "144": (None, "老渡也笑了，语气温暖风趣，说到'一个拥抱'时语气温柔下来", F),
 "145": (None, "小柚坐在原位想了想，语气温柔、好奇。注意：一镜到底，绝不切到特写，人物不离开座位、不凑近镜头", F),
 "147": (None, "老渡面向镜头，语气温柔、怀念，念'仿佛永远分离，却又终身相依'时稍稍放缓，说到'落幕了'时声音轻下来", F),
 "151": (None, "小柚轻轻笑了一下，语气温柔、感慨", F),
 "153": (None, "小柚托着下巴，温柔地问", F),
 "154": (None, "老渡微微一笑，低头想了想，语气温柔", F),
 "163": (None, "小柚眼神湿润，声音很轻，语气温柔", "近景，固定机位"),
 "164": (None, "老渡面向镜头，语气温柔而郑重，说到'一直看着长大'时微微一笑", F),
 "169": (None, "老渡面向镜头，先轻声问出'值得吗'，稍停，然后语气温柔而坚定地说完", F),
 "170": (None, "老渡面向镜头，温和地微笑，举起咖啡杯轻轻示意，向观众告别。注意：'回声号'读 huí shēng hào，三个字咬字清楚；句与句之间只停顿半秒左右，举杯的动作在说话时完成，不在停顿里发呆", F),
}
PRON = {"渡叔": "dù shū", "C罗": "西罗", "7号": "七号", "泊在": "bó zài", "罗卡角": "luó kǎ jiǎo", "硬塞": "yìng sāi", "还在": "hái zài", "还回去": "huán huí qù",
        "落款": "luò kuǎn", "落笔": "luò bǐ", "倒是": "dào shì", "收拾": "shōu shi", "为这样": "wèi zhè yàng", "为国家队": "wèi guó jiā duì", "为同一面": "wèi tóng yí miàn",
        "咬着牙": "yǎo zhe yá", "熬过": "áo guò", "便一文不值": "biàn yì wén bù zhí", "菲戈": "fēi gē", "沉得多": "chén de duō", "只不过": "zhǐ bú guò",
        "背影": "bèi yǐng", "嘘": "xū", "踩进": "cǎi jìn", "当蜘蛛网": "dāng zhī zhū wǎng", "查封": "chá fēng", "铺平": "pū píng", "灰烬": "huī jìn",
        "两行泪": "liǎng háng lèi", "隔着": "gé zhe", "一盏灯": "yì zhǎn dēng", "熄着": "xī zhe", "还有希望": "hái yǒu xī wàng", "好多人": "hǎo duō rén",
        "好几天": "hǎo jǐ tiān", "众说纷纭": "zhòng shuō fēn yún", "给游子": "gěi yóu zǐ", "剑拔弩张": "jiàn bá nǔ zhāng", "只剩": "zhǐ shèng",
        "看着长大": "kàn zhe zhǎng dà", "渺小": "miǎo xiǎo", "叮当": "dīng dāng", "小卖部": "xiǎo mài bù", "眉毛": "méi mao"}
PACE = {"老渡": "语速、节奏和停顿完全以音频1为准：语速从容自然，逗号处换一口气，句号处稍作停顿，一个字一个字说清楚，吐字清晰饱满；不抢拍、不连读、不含糊，也不拖腔。说话时头部保持稳定，只有自然的表情和轻微的手势，不低头、不转头、不摇头。",
        "小柚": "语速与音频1一致，轻快自然，句与句之间只停顿半秒左右，绝不长时间停顿发呆。"}
LD_TIGHT = {"011", "012", "170"}  # 11-18: these 老渡 takes kept 1.3-1.7 s sentence pauses (user: 卡顿) -> ref pauses capped at 0.85 s (not 0.6: EP05 烫嘴)
MAXA = 12.5  # Seedance 2.0: clips <= 15 s and audio refs 2-15 s; longer lines are split in the script (sub="b")
def pr(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True); return float(r.stdout.strip() or 0)
TOO_LONG, units = [], []
for sid in ids:
    s = next(x for x in m.SHOTS if x["id"] == sid); m.tts(s)
    ref = (m.voice({**s, "maxpause": 0.85}) if sid in LD_TIGHT else m.tts_path(s)) if s["who"] == "老渡" else m.voice(s)  # 老渡: untightened TTS at normal speed (EP05 '烫嘴' came from tightened refs); 小柚: tightened
    td = pr(ref)
    if td > MAXA: TOO_LONG.append(f'{sid} {s["who"]} {td:.1f}s {s["line"]}'); continue
    units.append((s, sid, s["line"], ref, td))
if TOO_LONG:
    print("TOO LONG (> %.1f s):" % MAXA); print("\n".join(TOO_LONG)); raise SystemExit(1)
shots, chains, lastkey = [], [], {}
for s, uid, line, tts, td in units:
    sid, who = s["id"], s["who"]; ang0, perf, cam = SHOT[sid]
    ang = ang0 or ("cam" if s["pic"].endswith("_cam") else "side")
    if td < 2.3:  # Ark wants reference audio of >= 2 s: pad short lines with trailing silence
        pad = Path("studio") / f"aref_{uid}.wav"; pad.parent.mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tts), "-af", "apad=pad_dur=1.5", "-ar", "24000", str(pad)])
        tts = pad.resolve()
    pron = [f"{k}（{v}）" for k, v in PRON.items() if k in line and not any(k != k2 and k in k2 and k2 in line for k2 in PRON)]
    p = ["【GLOBAL STYLE】" + STYLE, "【SCENE】回声号演播室（本期布置成葡萄牙里斯本老城傍晚的球迷小酒馆）。", "【CHARACTERS】" + CHAR[who] + " 画面中只有这一个人物，另一位角色不出画。",
         SEAT[(who, ang)] + "绝不换座位，绝不换背景。", POSTURE[who],
         "【PROPS】" + ("老渡手里不拿任何东西，左手腕上始终戴着黄铜机械表。" if who == "老渡" else "小柚手里不拿任何东西，左侧始终别着柚子形发夹，围巾始终围在脖子上。"),
         "【LIGHTING】窗外暖橙色的黄昏光从侧面照进来，室内钨丝壁灯补光，人物脸上有柔和的轮廓光。",
         f"【SHOT】{cam}。整条视频是同一个连续镜头（一镜到底）：中途绝不切镜头、不跳剪、不突然推近或换景别，人物始终坐在原位。表演：{perf}。表情和动作自然、有分寸，不夸张。",
         f"【DIALOGUE】{who}说话的语音内容就是音频1，口型与音频1逐字同步。{VOICE[who]}。台词（一字不改）：“{line}”。"
         "台词只说一遍：一字不多、一字不少，不重复、不卡顿、不结巴；最后一个字要完整说完；说完最后一个字就闭上嘴，不再说任何话，只保持表情和轻微动作直到镜头结束。" + PACE[who]]
    if pron: p.append("【PRONUNCIATION】读音：" + "，".join(pron) + "。")
    p += [f"【AUDIO REFERENCE】音频1就是这句台词的完整配音：{who}的口型严格对齐音频1逐字说出，声音、语速、停顿、语气与音频1完全一致，就是同一段声音。",
          "【POSITIVE LOCKS】服装、发型、眼镜、发夹、围巾、手表与图1完全一致；座位、朝向和背景与图2完全一致。画面上绝对不出现字幕、台词文字或任何文字。",
          "【AUDIO】只有这一句对白和安静的室内环境声。不要背景音乐，不要其他人说话。"]
    shots.append({"id": uid, "shot": sid, "who": who, "angle": ang, "line": line,
                  "duration": max(4, min(15, math.ceil(td * (1.12 if who == "老渡" else 1.08) + (1.0 if who == "老渡" else 0.8)))), "tts_dur": round(td, 2),
                  "refs": REF[who], "audio_refs": [str(Path(tts).resolve())], "prompt": "\n".join(p)})
    k = (who, ang); prev = lastkey.get(k)
    base = next((i for i, c in enumerate(chains) if c[-1][:3] == sid[:3]), None) if sid[-1] in "bc" else None
    if base is not None: chains[base].append(uid)  # 2nd half of a split line: generated right after the 1st, from its last frame
    elif prev is not None and chains[prev[1]][-1] == prev[0] and int(sid[:3]) - int(prev[0][:3]) <= 4: chains[prev[1]].append(uid)  # only continue a chain from the same angle
    else: chains.append([uid])
    lastkey[k] = (sid, next(i for i, c in enumerate(chains) if c[-1] == uid))
plan = {"shots": shots, "chains": chains}
Path("studio").mkdir(exist_ok=True)
Path(f"studio/plan_{name}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(s["duration"] for s in shots)
print(len(shots), "clips", tot, "s ≈", round(tot * 0.37), "CNY (2.0 fast 480p)")
for c in chains: print(" chain", c)
