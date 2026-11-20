"""EP07 studio shots (Seedance 2.0 fast 720p, 15 s cap; forked from EP06) -> studio/plan_<name>.json  (python studio_plan.py <name> <shot ids...>)"""
import json, math, sys, subprocess
from pathlib import Path
sys.argv, args = ["x", "none"], sys.argv[1:]
import make_episode as m
name, ids = args[0], args[1:]
STYLE = "电影级写实风格，16:9，数字电影机质感，轻微胶片颗粒，室内温暖的炉火光，窗外清冷的月光雪色，浅景深，安静温暖略带苍凉，画面干净精致。画面中不出现任何字幕、文字、数字、水印、标志、商标。"
CHAR = {"老渡": "老渡（图1）：中国男性，约38岁，短寸头，鬓角微白，浅胡茬；炭灰色粗针织高领毛衣，外面是深棕色灯芯绒夹克，深色长裤，左手腕戴黄铜表壳机械表。性格沉稳、温厚、有书卷气。",
        "小柚": "小柚（图1）：中国女生，约23岁，齐肩的黑色短发，左侧别着柚子形小发夹，细边圆框眼镜；奶白色粗麻花针织高领毛衣，肩上披着一条驼色格纹羊毛披肩（没有任何文字和图案）。不戴耳机。性格温柔可爱、文静，偶尔俏皮。"}
REF = json.loads(Path("look/refs.json").read_text(encoding="utf-8"))  # {"老渡": [lookclip last frame, plate], "小柚": [...]} - Seedance-made frames (Seedream faces are refused)
SETD = {"老渡": "回声号这一期的演播室：安第斯山脚下一间夜晚的木屋避难所，原木墙壁，石砌壁炉里炉火正旺，墙上挂着老式煤油马灯，粗木桌上铺着厚羊毛毯，桌上有冒热气的搪瓷杯、马黛茶葫芦杯。",
        "小柚": "回声号这一期的演播室：安第斯山脚下一间夜晚的木屋避难所，身后是大窗，窗外是月光下的雪山和飘雪，窗边小木桌上有冒热气的搪瓷杯和一台旧半导体收音机。"}
SEAT = {
 ("老渡", "side"): "【SCREEN DIRECTION】老渡坐在图2壁炉边的旧皮扶手木椅上，身体朝向画面左侧，视线看向画面左侧（看着坐在对面的小柚）。背景固定是图2：" + SETD["老渡"],
 ("老渡", "cam"):  "【SCREEN DIRECTION】老渡坐在图2壁炉边的旧皮扶手木椅上，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["老渡"],
 ("小柚", "side"): "【SCREEN DIRECTION】小柚坐在图2窗边的木椅上，身体朝向画面右侧，视线看向画面右侧（看着坐在对面的老渡）。背景固定是图2：" + SETD["小柚"],
 ("小柚", "cam"):  "【SCREEN DIRECTION】小柚坐在图2窗边的木椅上，面向镜头，看着镜头和观众说话。背景固定是图2：" + SETD["小柚"],
}
POSTURE = {"老渡": "【POSTURE】坐姿放松但端正，双手自然放在桌面上，或一只手轻扶搪瓷杯。",
           "小柚": "【POSTURE】小柚端正地坐在木椅上，腰背挺直，上半身高出桌面，人和椅子比例正常，绝不陷进椅子里，不缩成一团。"}
VOICE = {"老渡": "老渡的声音：低沉温厚的男中音，标准普通话，沉稳从容，有书卷气",
         "小柚": "小柚的声音：温柔甜美的年轻女声，标准普通话，轻柔自然，不夸张、不一惊一乍"}
F = "中近景，固定机位"
C = "近景（胸像），固定机位"
SHOT = {  # id: (angle or None = from pic, 表演, 运镜)
 "009": (None, "老渡面向镜头，温和地微笑，轻轻点头向观众打招呼，说到'木屋'时目光稍稍扫一下四周的炉火", F),
 "010": (None, "小柚面向镜头，先温柔地笑着打招呼，说到'刚才山顶上那个人'时笑容收住，身体微微前倾，语气变得紧张、急切", F),
 "011": (None, "老渡看着小柚，轻轻抬手示意她别急，语气沉稳，说到'星期五的下午'时声音放低，像要讲一个很长的故事", F),
 "011b": (None, "老渡面向镜头，语气郑重、有分量，像节目的开场白", F),
 "011c": (None, "紧接上一句说下去：开头是上一个镜头结尾的姿势，语气温和而郑重，说到'七十二天'时稍稍放缓；开口就说，开头不停顿", C),
 "012": (None, "小柚歪着头看着窗边桌上的旧收音机，带一点调皮地问，说到'沙沙声'时轻轻笑了一下", F),
 "013": (None, "老渡看着小柚，语气从温和慢慢沉下来，说到'两条消息'时目光变得深沉", F),
 "013b": (None, "紧接上一句说下去：开头是上一个镜头结尾的姿势（看着小柚），身体微微前倾，压低声音，语气郑重，说完卖个关子似的停住、看着小柚；开口就说，开头不停顿", C),
 "019": (None, "小柚轻轻皱了一下眉，半开玩笑地说，语气轻快", F),
 "020": (None, "老渡看着小柚，语气温和、怀念，像在描述一幅明亮的画面，嘴角带一点笑", F),
 "032": (None, "小柚眼神湿润，声音很轻，语气心疼，说到'二十二岁'时声音有些发颤", C),
 "033": (None, "老渡看着小柚，语气温柔而坚定，说到'亲口告诉爸爸'时一字一句", F),
 "033b": (None, "紧接上一句说下去：开头是上一个镜头结尾的姿势，语气低沉、郑重，像揭开一个伏笔；开口就说，开头不停顿", C),
 "036": (None, "小柚抱着一点期望，认真地问，语气温柔", F),
 "037": (None, "老渡看着小柚，语气平静，说到'等一个好消息'时声音轻下来，带一点不忍", F),
 "042": (None, "小柚犹豫了一下，小声地、小心翼翼地问", C),
 "043": (None, "老渡点点头，语气平静而沉重，说到'全世界'时稍稍加重", F),
 "051": (None, "小柚忍不住笑了一下，语气轻快、带点佩服", F),
 "052": (None, "老渡看着小柚，笑容慢慢收住，语气温柔里带着一点不忍", F),
 "057": (None, "小柚的笑容僵住，眼神湿润，声音很轻很轻，说完就停", C),
 "060": (None, "小柚声音很轻，语气温柔、心疼，说到'二十五岁生日'时眼神湿润", F),
 "061": (None, "老渡看着小柚，语气温柔，说到'一群兄弟'时声音轻下来，眼神温暖", F),
 "070": (None, "小柚声音很轻，语气温柔、感慨", F),
 "071": (None, "老渡面向镜头，语气低沉、坚决，说到'一个一个地走'时一字一句", C),
 "083": (None, "小柚屏住呼吸，紧张地小声问", C),
 "084": (None, "老渡看着小柚，语气沉稳，一字一句，像在丈量那段路", F),
 "084b": (None, "紧接上一句说下去：开头是上一个镜头结尾的姿势，语气越来越明亮、越来越有希望，说到'野花'时嘴角浮起笑意；开口就说，开头不停顿", F),
 "089": (None, "小柚屏住呼吸，紧张地小声问", C),
 "090": (None, "老渡看着小柚，压低声音，语气紧张而克制，说到'一句话'时放缓", F),
 "096": (None, "小柚眼睛一亮，开心地说，语气激动但不喊叫", F),
 "097": (None, "老渡看着小柚，眼里有光，语气越说越激动，说到'可以回家了'时声音温柔下来，带着笑", F),
 "105": (None, "小柚眼泪在眼眶里打转，声音很轻，说完就停", C),
 "106": (None, "老渡面向镜头，语气温柔而郑重，说到'七十二天'时放缓", F),
 "107": (None, "小柚想起了什么，认真地问", F),
 "122": (None, "小柚望着窗外的雪山，转回头来认真地问，语气温柔", F),
 "123": (None, "老渡沉默了一下才开口，语气温柔，说到'一个父亲在等他'时声音轻下来", F),
 "123b": (None, "紧接上一句说下去：转向镜头，语气温柔而坚定，说到'白等'时一字一句；开口就说，开头不停顿", C),
 "124": (None, "小柚面向镜头，有点不好意思地笑了一下，语气温柔、认真", F),
 "125": (None, "老渡面向镜头，语气低缓、深情，像朗诵一首诗，说到'都还活着'时声音轻下来", F),
 "125b": (None, "紧接上一句说下去：开头是上一个镜头结尾的姿势，像朗诵一首诗那样，语气温柔而坚定；开口就说，开头不停顿", C),
 "126": (None, "老渡面向镜头，温和地微笑，端起搪瓷杯轻轻示意，向观众告别。举杯的动作在说话时完成，不在停顿里发呆", F),
}
PRON = {"渡叔": "dù shū", "努马": "nǔ mǎ", "拧了": "nǐng le", "得先": "děi xiān", "得活着": "děi huó zhe", "还是回头": "hái shì huí tóu", "还在": "hái zài",
        "犹豫": "yóu yù", "舷窗": "xián chuāng", "一个一个地": "yí gè yí gè de", "只隔着": "zhǐ gé zhe", "熬不下去": "áo bù xià qù", "苔藓": "tái xiǎn",
        "蹄印": "tí yìn", "空罐头": "kōng guàn tou", "绝境盟约": "jué jìng méng yuē", "好会给人打气": "hǎo huì gěi rén dǎ qì", "一封信": "yì fēng xìn",
        "炉火还暖着": "lú huǒ hái nuǎn zhe", "狂野": "kuáng yě", "给山上": "gěi shān shàng", "要了他们的命": "yào le tā men de mìng", "翻涌": "fān yǒng",
        "卡内萨": "kǎ nèi sà", "帕拉多": "pà lā duō", "尼科里奇": "ní kē lǐ qí", "回声号": "huí shēng hào", "喊": "hǎn", "沙沙声": "shā shā shēng", "离活下去": "lí huó xià qù", "白等": "bái děng"}
PACE = {"老渡": "语速、节奏和停顿完全以音频1为准：语速从容自然，逗号处换一口气，句号处稍作停顿，一个字一个字说清楚，吐字清晰饱满；不抢拍、不连读、不含糊，也不拖腔。句与句之间只停顿半秒左右，停顿时不发呆。说话时头部保持稳定，只有自然的表情和轻微的手势，不低头、不转头、不摇头。",
        "小柚": "语速与音频1一致，轻快自然，句与句之间只停顿半秒左右，绝不长时间停顿发呆。"}
LD_TIGHT = set()  # 11-18: these 老渡 takes kept 1.3-1.7 s sentence pauses (user: 卡顿) -> ref pauses capped at 0.85 s (not 0.6: EP05 烫嘴)
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
    p = ["【GLOBAL STYLE】" + STYLE, "【SCENE】回声号演播室（本期布置成安第斯山脚下一间夜晚的木屋避难所）。", "【CHARACTERS】" + CHAR[who] + " 画面中只有这一个人物，另一位角色不出画。",
         SEAT[(who, ang)] + "绝不换座位，绝不换背景。", POSTURE[who],
         "【PROPS】" + ("老渡手里不拿任何东西（告别时可以端起搪瓷杯），左手腕上始终戴着黄铜机械表。" if who == "老渡" else "小柚手里不拿任何东西，左侧始终别着柚子形发夹，驼色格纹披肩始终披在肩上。"),
         "【LIGHTING】壁炉的暖橙色火光从侧面照在脸上，轻轻跳动；窗外是清冷的蓝色月光雪色，形成冷暖对比；煤油马灯补光，人物脸上有柔和的轮廓光。",
         f"【SHOT】{cam}。整条视频是同一个连续镜头（一镜到底）：中途绝不切镜头、不跳剪、不突然推近或换景别，人物始终坐在原位。表演：{perf}。表情和动作自然、有分寸，不夸张。",
         f"【DIALOGUE】{who}说话的语音内容就是音频1，口型与音频1逐字同步。{VOICE[who]}。台词（一字不改）：“{line}”。"
         "台词只说一遍：一字不多、一字不少，不重复、不卡顿、不结巴；最后一个字要完整说完；说完最后一个字就闭上嘴，不再说任何话，只保持表情和轻微动作直到镜头结束。" + PACE[who]]
    if pron: p.append("【PRONUNCIATION】读音：" + "，".join(pron) + "。")
    p += [f"【AUDIO REFERENCE】音频1就是这句台词的完整配音：{who}的口型严格对齐音频1逐字说出，声音、语速、停顿、语气与音频1完全一致，就是同一段声音。",
          "【POSITIVE LOCKS】服装、发型、眼镜、发夹、披肩、手表与图1完全一致；座位、朝向和背景与图2完全一致。画面上绝对不出现字幕、台词文字或任何文字。",
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
print(len(shots), "clips", tot, "s ≈", round(tot * 0.80), "CNY list /", round(tot * 0.48), "CNY at 60% (2.0 fast 720p)")
for c in chains: print(" chain", c)
