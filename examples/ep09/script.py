"""回声号 EP09《封狼居胥》预览稿 v1（11-24）。
主线：女奴之子、私生子霍去病，替一个被匈奴欺负了七十年的王朝出头：17 岁八百骑封冠军侯，19 岁两定河西、单骑入营受降，21 岁封狼居胥，23 岁病逝。
史实见 research.md（《史记·卫将军骠骑列传》《汉书》；匈奴歌出《史记索隐》引《西河旧事》；酒泉为传说）。年龄用实岁。
写法：热血爽文弧线（憋屈→爆发→更大的爆发→巅峰→骤然陨落→余烬）；旁白自己讲故事，不写「X说：」转述链；诗句裸引不报作者。
"""
import json
from pathlib import Path

EMOTION = """
母题：那口气（白登/和亲/嫚书 → 七十年 → 漠北"吐了出来"）；家（私生子 → 认父 → "匈奴未灭，无以家为" → 小柚：一个没有家的人说他不要家）；
      祁连山（匈奴悲歌 → 冢象祁连山）；狼居胥（冷开场 → 高潮收回）；马（八百骑 → 马踏匈奴 → 桌上的马踏飞燕）；二十三岁（小柚也二十三岁）。
冷开场 漠北追两千里、登狼居胥祭天（巅峰悬念）→"四年前私生子/两年后死了"→片名
屈辱七十年（憋）→ 私生子（谷）→ 狂言"顾方略何如耳"（扬）→ 八百骑（第一爆，留白）→ 六天五国（第二爆）→ 祁连山孤军（第三爆）→ 匈奴悲歌（留白）
→ 受降驰入敌营（胆魄峰）→ 酒泉传说（喘息）→ 认父（柔）→ 封狼居胥（全片最高潮，留白，王维）→ 匈奴未灭无以家为（金句）→ 另一面（真实）
→ 二十三岁病逝（骤空，留白）→ 冢象祁连山、马踏匈奴 → 丝路/霍光/辛弃疾/高铁（余烬复燃）→ 结尾 王维全句 → 致敬卡
"""

BGM = {  # key: (file in bgm/, start s, volume[, {"fin": fade-in s, "hit": music time landing on the section's hit shot}])
    "zhangu": ("zhangu.wav", 0, 0.55),            # 《战鼓燃天》：冷开场
    "shimian": ("shimian_liu.wav", 0, 0.5),       # 琵琶《十面埋伏》刘德海：冷开场后半"四年前…"
    "title": ("dahan.wav", 0, 0.6),               # 《大汉雄风》：片名
    "hexi": ("hexi_yanni.wav", 0, 0.45),          # 雅尼《河西走廊之梦》：开场、祁连山、回声
    "xunsw": ("xun_suwu.wav", 0, 0.5),            # 埙《苏武牧羊》：屈辱七十年
    "xiao": ("xiao.wav", 0, 0.45),                # 洞箫：私生子
    "shimianf": ("shimian_fang.wav", 0, 0.55),    # 《十面埋伏》方锦龙琵琶+堂鼓：八百骑
    "naner": ("nanerzqiang.wav", 0, 0.55),        # 《男儿当自强》香港中乐团：六天五国
    "lanling": ("lanling.wav", 0, 0.55),          # 鼓乐《兰陵王入阵曲》：受降
    "yangguan": ("yangguan.wav", 0, 0.45),        # 古琴《阳关三叠》：认父
    "qinwang": ("qinwang.wav", 0, 0.55),          # 《秦王破阵乐》打击协奏：封狼居胥出征
    "choir": ("tiexue.wav", 0, 0.6),              # 《铁血赞歌》：封狼居胥高潮
    "hanwu": ("hanwu_bz.wav", 0, 0.5),            # 《最后的倾诉》伴奏（《汉武大帝》片头曲）：匈奴未灭
    "xiao2": ("xiao.wav", 120, 0.4),              # 洞箫（后段）：另一面
    "xun": ("xun_chuge.wav", 0, 0.55),            # 埙《楚歌》：二十三岁
    "jiangjun": ("jiangjun.wav", 0, 0.5),         # 《将军令》：结尾、片尾卡
    "none": (None, 0, 0),
}

SECTIONS, SHOTS = [], []
_bgm, _ctx = "none", ""
_NUM = [0]
_NEW = [False]
LD, XY, NO = "老渡", "小柚", "无"
ST_LD, ST_XY, ST_LDC, ST_XYC = "img:st_ld", "img:st_xy", "img:st_ld_cam", "img:st_xy_cam"
CTX = {  # TTS 语气：豆包 2.0 context_texts 用"请求式"
    "calm": "你可以用沉稳、温厚的语气，像讲一个老故事那样说吗？",
    "warm": "你可以用温暖、带着笑意的语气说吗？",
    "tender": "你可以用很温柔、很怀念的语气，轻轻地说吗？",
    "heavy": "你可以用特别沉痛、心碎的语气，声音发颤地说吗？",
    "tense": "你可以压低声音，用紧张、扣人心弦的语气说吗？",
    "rise": "你可以用越来越激昂、越来越有力量的语气说吗？",
    "joy": "你可以用特别激动、热泪盈眶、发自内心的喜悦语气说吗？",
    "poem": "你可以像朗诵一首诗那样，饱含深情、带着一点哽咽地念出来吗？",
    "poem_rise": "你可以像朗诵一首诗那样，一字一句，越念越坚定、越念越有力量吗？",
    "xy": "你可以用温柔、好奇的语气，轻轻地问吗？",
    "xy_sad": "你可以用很心疼、快要哭出来的语气，轻轻地说吗？",
    "xy_happy": "你可以用开心、忍不住笑出来的语气说吗？",
    "xy_tense": "你可以屏住呼吸，用很紧张、很担心的语气小声问吗？",
}
SLOW = {CTX["heavy"]: 0, CTX["poem"]: 0, CTX["poem_rise"]: 0, CTX["tender"]: 0, CTX["xy_sad"]: 0}  # 语速一律不动（EP06 用户），情绪句只多留画面


def sec(name, bgm, ctx="calm"):
    global _bgm, _ctx
    SECTIONS.append(name)
    if bgm != _bgm:
        _NEW[0] = True
    _bgm, _ctx = bgm, ctx


def bgm(key):
    global _bgm
    _bgm = key
    _NEW[0] = True


FOOT = {}  # 占位素材名 -> 实际 footage key（素材核对后填）


def F(key, t="auto"):
    return f"f:footage/{FOOT.get(key, key)}.mp4:{t}"


def O(key, a, b):
    return f"fc:footage/{FOOT.get(key, key)}.mp4:{a}:{b}"


def shot(who, line, pic, sub="", **kw):
    if not sub:
        _NUM[0] += 1
    ctx = kw.pop("ctx", None) or (CTX["xy"] if who == XY else CTX[_ctx])
    if ctx in SLOW and who != NO:
        kw.setdefault("rate", SLOW[ctx])
        kw.setdefault("maxpause", 0.9)
        kw.setdefault("pad", 1.2)
    if _NEW[0]:
        kw["newbed"] = True
        _NEW[0] = False
    SHOTS.append({"id": f"{_NUM[0]:03d}{sub}", "sec": SECTIONS[-1], "who": who, "line": line, "pic": pic, "bgm": _bgm, "ctx": ctx, **kw})


DUB = {}


def D(key, a, b):
    """外语原声 → 国语配音：原片画面 + 原声开头约 1 s 后压低垫底，配音演员读中文"""
    return f"fd:footage/{FOOT.get(key, key)}.mp4:{a}:{b}"


def dub(name, line, key, a, b, **kw):
    shot(DUB[name], line, D(key, a, b), **kw)


def breath(key, t, hold, amb=0.6, cap="", **kw):
    """留白：旁白停下，原片 key@t 带现场声放 hold 秒，音乐推上来（amb = 现场声音量，0 = 只听音乐）"""
    shot(NO, "", F(key, t), hold=hold, breath=amb, cap=cap, **kw)


P = CTX["poem"]
PR = CTX["poem_rise"]
H = CTX["heavy"]
T = CTX["tender"]
W = CTX["warm"]

RISE = CTX["rise"]
TENSE = CTX["tense"]
JOY = CTX["joy"]
XYS, XYH, XYT = CTX["xy_sad"], CTX["xy_happy"], CTX["xy_tense"]
XYR = "你可以用激动、热血沸腾、眼睛发亮的语气说吗？"

# ================================================================== 冷开场
sec("冷开场 · 狼居胥", "zhangu", "tense")
shot(LD, "公元前119年，漠北。戈壁上的风，从两千里外，一路追着一支骑兵吹过来。", F("steppe_human", 5.0))
shot(LD, "五万匹战马，跑过了没有水的大漠，跑到了匈奴人以为汉朝人一辈子也到不了的地方。", F("steppe_human", 30.0), ctx=RISE)
shot(LD, "队伍的最前面，是一个二十一岁的年轻人。", F("hexi_hqb", 60.0), ctx=TENSE, pad=1.2)
shot(LD, "他勒住马，抬起头，望着眼前那座山。匈奴人管它叫：狼居胥。", F("hexi_film", 20.0), ctx=TENSE)
shot(LD, "他登上山顶，点起祭天的火。火光照着他的脸，也照着身后那面汉家的旗。七十年了，这面旗，从来没有在这里升起过。", F("hexi_film", 70.0), ctx=RISE, pad=1.5)
shot(LD, "黄沙百战穿金甲，不破楼兰终不还。", F("hexi_hqb", 0.0), ctx=PR, pad=1.8)
bgm("shimian")
shot(LD, "四年前，他还只是长安城里，一个没有父亲认的私生子。", F("changan_ruins", 180.0), ctx=T, pad=1.2)
shot(LD, "两年后，他就死了。", F("hexi_mobei", 280.0), ctx=H, pad=1.8)
shot(LD, "他的名字，叫霍去病。", F("hw_800", 65.0), ctx=RISE, pad=1.2)
bgm("title")
shot(NO, "", F("hexi_film", 120.0), card=["封狼居胥"], hold=7.0, hit=True)

# ================================================================== 开场
sec("开场", "hexi", "warm")
shot(LD, "大家好，我是老渡。今夜的回声号，在河西走廊一间土坯客栈里。炉火正旺，窗外是祁连山的雪。", ST_LDC)
shot(XY, "大家好，我是小柚！渡叔，刚才那一幕我鸡皮疙瘩都起来了。二十一岁，就站在了那座山顶上？", ST_XYC, ctx=XYR)
shot(LD, "二十一岁。而且，那还不是他第一次，让整个天下吃惊。", ST_LD, ctx=RISE)
shot(LD, "这里是回声号。历史上每一个惊心动魄的瞬间，都会留下回声。有的回声，是一阵马蹄声。", ST_LDC, sub="b")
shot(LD, "上一期，我们守着一扇门，讲了四十五年；今夜，我们讲一个只活了二十三年的人。", ST_LDC, sub="c", ctx=T)
shot(XY, "二十三年……那他这一辈子，得跑得多快啊。", ST_XY, ctx=XYS)
shot(LD, "快得像一支箭。可要看懂这支箭为什么射出去，得先说说一口气。一口汉朝咽了七十年的气。", ST_LD, ctx=TENSE)

# ================================================================== 一 屈辱七十年
sec("第一段 · 七十年的那口气", "xunsw", "heavy")
shot(LD, "公元前200年，冬天。汉朝的开国皇帝刘邦，亲自带兵北上，迎击匈奴。", F("hw_heqin", 280.0))
shot(LD, "他追得太急，一头扎进了匈奴的圈套。四十万匈奴骑兵，把他围在白登山上，整整七天七夜。", F("hw52", 1100.0), ctx=TENSE)
shot(LD, "天寒地冻，十个士兵里，有两三个冻掉了手指。最后，靠着偷偷给单于的阏氏送去厚礼，皇帝才捡回一条命。", F("hw_heqin", 0.0))
shot(LD, "从那以后，汉朝不敢再打了。一年又一年，把公主送到草原上去和亲，把丝绸、粮食、美酒，一车一车往北送。", F("hw_heqin", 20.0), pad=1.2)
shot(LD, "匈奴的单于，甚至写信给守寡的吕后，言语轻佻，极尽羞辱。满朝文武气得要拔剑，最后送回去的，却是一封低声下气的回信。", F("hw_heqin", 180.0), ctx=H)
shot(XY, "这也太憋屈了……", ST_XY, ctx=XYS)
shot(LD, "一憋，就是七十年。边关的百姓，最怕秋天。秋高马肥，就是匈奴南下的季节。", ST_LD, ctx=H)
shot(LD, "七十年里，汉朝一直在等。等粮仓攒满，等战马养肥，等一个敢打的皇帝。", F("shandan_xh", 0.0), ctx=TENSE)
shot(LD, "这个皇帝，终于来了。公元前133年，二十三岁的汉武帝刘彻下了决心：这口气，不咽了。", F("hw_800c", 0.0), ctx=RISE)
shot(LD, "可是，要打仗，得有能打的人。", F("hw54", 970.0), ctx=TENSE, pad=1.2)

# ================================================================== 二 私生子
sec("第二段 · 私生子", "xiao", "tender")
shot(LD, "平阳公主的府里，有一个女奴，叫卫少儿。她和一个来府里当差的小吏好上了，生下一个男孩。", ST_LD)
shot(LD, "那个小吏后来回了老家，另娶了妻子，再也没有回头看过这个孩子。", F("hexi_hqb", 140.0), ctx=H, pad=1.2)
shot(LD, "这个男孩，就是霍去病。一出生，他就是私生子；一出生，他就是奴仆的儿子。", F("hw_800b", 10.0), ctx=H)
shot(XY, "那他……这辈子不就被定死了吗？", ST_XY, ctx=XYS)
shot(LD, "本来是。可他有一个舅舅，叫卫青，原本是府里给人牵马的骑奴；他还有一个姨母，叫卫子夫，原本是府里的歌女。", ST_LD, ctx=T)
shot(LD, "后来的事，像是老天突然翻了一页。卫子夫被汉武帝看中，做了皇后；骑奴卫青，当上了将军，在龙城打出了汉朝对匈奴的第一场胜仗。", F("hw_800", 40.0), ctx=RISE)
shot(LD, "霍去病，就在这样一个忽然显赫起来的家里长大。他话不多，骑马射箭，却比谁都狠。", F("hw_yanzhi", 96.0))
shot(LD, "汉武帝很喜欢这个少年，想亲自教他孙子、吴起的兵法。少年却摇了摇头：打仗，看的是临阵怎么谋划，用不着去学古人的兵法。", F("hw_800c", 48.0), ctx=W)
shot(XY, "哇，他好狂啊！", ST_XYC, ctx=XYH)
shot(LD, "狂。可他很快就会让所有人知道，他有狂的资格。", ST_LDC, ctx=RISE, pad=1.2)

# ================================================================== 三 八百骑
sec("第三段 · 八百骑", "shimianf", "tense")
shot(LD, "公元前123年，春天。大将军卫青带着十几万大军，从定襄出塞，北击匈奴。", F("hw52", 820.0))
shot(LD, "军中有一个刚满十七岁的剽姚校尉。这是他第一次上战场。", F("hw_800b", 0.0), ctx=TENSE)
shot(LD, "大军还在一步一步往前推，他却挑了八百个最快、最狠的骑兵，离开大军，一头扎进了茫茫大漠。", F("hw_800", 10.0), ctx=TENSE)
shot(XY, "八百个人？就敢自己走？", ST_XY, ctx=XYT)
shot(LD, "不光敢走，还一口气走出了几百里。他要找的，是匈奴人的营地。", ST_LD, ctx=TENSE)
shot(LD, "他找到了。趁着匈奴人还没回过神来，八百骑兵像一把刀，直直插了进去。", F("hw_800b", 35.0), ctx=RISE)
shot(LD, "斩杀、俘虏匈奴两千零二十八人。单于祖父一辈的籍若侯，当场被斩；单于的叔父罗姑比，被活捉了回来。", F("hw52", 1350.0), ctx=RISE)
shot(LD, "汉武帝大喜，专门为他造了一个封号：冠军侯。意思是，勇冠三军。", F("hw_800", 72.0), ctx=JOY)
shot(LD, "那一年，他十七岁。别人的十七岁在读书，他的十七岁，在八百匹战马的最前面。", F("hw_800b", 50.0), ctx=RISE, pad=1.5)
breath("hexi_hqb", 20.0, 6.0, amb=0.5)

# ================================================================== 四 六天五国
sec("第四段 · 六天，五个部落", "naner", "tense")
shot(LD, "河西走廊，夹在祁连山和北山之间，一条一千多公里长的狭长通道。谁握住它，谁就握住了通往西域的大门。", F("qilian_grass", 30.0))
shot(LD, "那时候，它在匈奴手里。", F("qilian_grass", 60.0), ctx=TENSE, pad=1.0)
shot(LD, "出身仕汉羽林郎，初随骠骑战渔阳。", F("hw_hexi2", 65.0), ctx=PR, pad=1.5)
shot(LD, "公元前121年，春天。十九岁的骠骑将军霍去病，带着一万骑兵，从陇西出发。", F("hw_hexi2", 30.0), ctx=RISE)
shot(LD, "六天。他转战了匈奴五个部落。打完一个，转身就走；不停，不歇，不回头。", F("hw_hexi2", 5.0), ctx=RISE)
shot(LD, "匈奴人还没弄清楚来的是谁，他已经翻过了焉支山，又往前冲了一千多里。", F("hw_hexi2", 90.0), ctx=RISE)
shot(LD, "斩折兰王，斩卢胡王，活捉浑邪王的儿子。连匈奴人祭天用的金人，都被他运回了长安。", F("hw_yanzhi", 200.0), ctx=RISE)
shot(XY, "六天五个部落……这是在打仗，还是在赶路啊？", ST_XYC, ctx=XYH)
shot(LD, "对他来说，打仗就是赶路。快，就是他最大的兵法。", ST_LDC, ctx=RISE)

# ================================================================== 五 祁连山
sec("第五段 · 祁连山", "hexi", "tense")
shot(LD, "同一年夏天，他又出发了。这一次，他要直插河西的腹地。", F("hexi_hqb", 80.0))
shot(LD, "约好一起进军的另一路大军，在大漠里迷了路，没能赶到。", F("gobi_devil", 0.0), ctx=TENSE)
shot(LD, "换了别人，也许就退了。他没有。他带着自己的骑兵，渡过黄河，越过贺兰山，穿过居延泽，从匈奴人的背后，一头扎到了祁连山下。", F("hexi_hqb", 100.0), ctx=RISE)
shot(LD, "斩首三万二百级。匈奴的王子、相国、将军，被俘了一百多人。", F("hw_jiawei", 15.0), ctx=RISE)
shot(LD, "丢了河西的匈奴人，一边往北撤，一边唱起了一首悲歌。", F("hw_fenglang", 50.0), ctx=H, pad=1.2)
shot(LD, "失我祁连山，使我六畜不蕃息；失我焉支山，使我妇女无颜色。", F("hexi_film", 220.0), ctx=P, pad=2.0)
breath("qilian_grass", 100.0, 7.0, amb=0.3)
shot(XY, "渡叔，一年之内，他就把河西拿下来了？", ST_XY, ctx=XYR)
shot(LD, "还差最后一步。而这一步，比打仗还要凶险。", ST_LD, ctx=TENSE)

# ================================================================== 六 受降
sec("第六段 · 驰入敌营", "lanling", "tense")
shot(LD, "那年秋天，被打怕了的浑邪王派人来投降。他杀了不肯降的休屠王，带着四万多部众，朝汉朝走来。", F("hw_fenglang", 42.0))
shot(LD, "汉武帝怕有诈，派霍去病带兵去接。", F("hw_800b", 115.0), ctx=TENSE)
shot(LD, "两军隔着黄河相望。就在这时候，匈奴的营地里，乱了。很多人一看见汉军，就后悔了，掉转马头就要跑。", F("hw_yanzhi", 152.0), ctx=TENSE)
shot(LD, "四万多人一旦哗变，这一年打下来的一切，都可能前功尽弃。", F("huanghe_air", 20.0), ctx=TENSE, pad=1.2)
shot(XY, "那……他怎么办？", ST_XYC, ctx=XYT)
shot(LD, "他带着亲兵，冲进了匈奴的大营。", ST_LDC, ctx=TENSE, pad=1.0)
shot(LD, "他直接冲到浑邪王的面前。下令：想逃的，斩。", F("hexi_hqb", 380.0), ctx=RISE)
shot(LD, "八千人，当场被斩。整座匈奴大营，一下子就安静了。", F("hw_jiawei", 112.0), ctx=RISE, pad=1.5)
shot(LD, "四万多匈奴人，号称十万，全部渡过黄河，归降汉朝。十九岁，他一身铁甲走进敌营，压住了十万人的局面。", F("huanghe_air", 100.0), ctx=JOY)
shot(LD, "河西走廊，从此回到了汉朝的手里。后来，这里有了四个郡：武威、张掖、酒泉、敦煌。", F("hexi_mobei", 500.0), ctx=RISE)
shot(XY, "酒泉！这个名字我知道！", ST_XY, ctx=XYH)
shot(LD, "传说，汉武帝赐了一坛御酒犒赏他。酒少人多，他就把酒倒进泉水里，和将士们一起喝。那眼泉，从此就叫酒泉。", ST_LD, ctx=W)
shot(LD, "不过，那只是传说。真正写进史书的，是另一件事。", ST_LDC, sub="b", ctx=T)

# ================================================================== 七 认父
sec("第七段 · 认父", "yangguan", "tender")
shot(LD, "有一次出征，大军路过河东平阳。那是他出生的地方。", F("qilian_autumn", 12.0))
shot(LD, "当年那个转身离开的小吏，霍仲孺，还住在那里。", F("hexi_hqb", 160.0), ctx=T, pad=1.2)
shot(LD, "霍去病派人把他请来。这个从来没被父亲认过的私生子，一见面，就跪了下去：去病以前不知道，自己是您的骨肉。", F("hw_800b", 62.0), ctx=T, pad=1.5)
shot(LD, "白发的霍仲孺慌忙伏在地上，连连叩头：我这把老骨头能托付给将军，这是老天的恩典啊。", F("hw_800c", 14.0), ctx=H, pad=1.5)
shot(XY, "他……原谅他爸爸了吗？", ST_XYC, ctx=XYS)
shot(LD, "史书没写原不原谅。只写了，他给父亲买了田地、宅子和奴婢。回长安的时候，还带走了一个十几岁的少年，他同父异母的弟弟，霍光。", ST_LDC, ctx=T)
shot(LD, "这个弟弟，后来会成为汉朝最有权势的人之一。不过，那是后话了。", ST_LD, ctx=T)

# ================================================================== 八 封狼居胥
sec("第八段 · 封狼居胥", "qinwang", "tense")
shot(LD, "公元前119年，汉朝要和匈奴，做一个了断。", F("hw52", 930.0), ctx=TENSE)
shot(LD, "十万骑兵，几十万步兵和运粮的民夫，兵分两路：大将军卫青一路，骠骑将军霍去病一路，各带五万骑兵，穿越大漠，去找单于决战。", F("hw52", 1050.0), ctx=RISE)
shot(LD, "霍去病带走了全军最精锐的骑兵，从代郡出发，扎进了大漠。", F("hexi_mobei", 240.0), ctx=RISE)
bgm("choir")
shot(LD, "这一次，他走得比任何时候都远。一千里，一千五百里，两千里。", F("herd_drone1", 0.0), ctx=RISE)
shot(LD, "斩比车耆，擒屯头王、韩王，俘虏匈奴的将军、相国、当户、都尉八十三人。匈奴左贤王的大军，被打得溃不成军，一路向北逃。", F("hw52", 1200.0), ctx=RISE)
shot(XY, "还追？都两千里了！", ST_XYC, ctx=XYR)
shot(LD, "还追。一直追到一座山前。", ST_LDC, ctx=RISE, pad=1.0)
shot(LD, "那座山，叫狼居胥山。", F("hexi_film", 140.0), ctx=RISE, pad=1.2)
shot(LD, "二十一岁的霍去病登上山顶，在狼居胥山祭天，在姑衍山祭地。然后他继续向北，一直走到了瀚海的岸边。", F("hexi_film", 90.0), ctx=JOY)
shot(LD, "斩首七万四百四十三级。同一场战役里，他的舅舅卫青，在另一头击溃了单于的主力。", F("hw_fenglang", 25.0), ctx=RISE)
shot(LD, "从这一天起，匈奴远遁，大漠以南，再也没有匈奴的王庭。", F("herd_drone2", 0.0), ctx=RISE)
shot(LD, "汉朝咽了七十年的那口气，在这一天，被一个二十一岁的年轻人，吐了出来。", F("hw_fenglang", 55.0), ctx=JOY, pad=2.0)
breath("hqb_trailer", 20.0, 8.0, amb=0.4)
shot(LD, "孰知不向边庭苦，纵死犹闻侠骨香。", F("hqb_trailer", 280.0), ctx=PR, pad=2.0)
shot(XY, "渡叔，我现在终于明白，为什么封狼居胥，会成了一个将军一辈子的梦想。", ST_XY, ctx=XYR)

# ================================================================== 九 匈奴未灭
sec("第九段 · 匈奴未灭", "hanwu", "calm")
shot(LD, "凯旋之后，汉武帝要在长安给他修一座豪华的府第，让他亲自去看看。", F("hw_fenglang", 100.0))
shot(LD, "霍去病没有去。他只回了一句话。", F("hw_jiawei", 0.0), ctx=TENSE, pad=1.2)
shot(LD, "匈奴未灭，无以家为也。匈奴还没有消灭，我要家做什么？", ST_LDC, ctx=PR, pad=1.8)
shot(XY, "一个从小没有家的人，最后说，他不要家。", ST_XYC, ctx=XYS)
shot(LD, "他找回了父亲，却不要一座宅子。也许在他心里，家从来不是一座房子，是身后那片再也不会被欺负的土地。", ST_LD, ctx=T, pad=1.5)

# ================================================================== 十 另一面
sec("第十段 · 另一面", "xiao2", "calm")
shot(XY, "他这么厉害，是不是……一个完美的人？", ST_XY)
shot(LD, "不是。司马迁写他的时候，也没有替他遮掩。", ST_LD, ctx=T)
shot(LD, "他少年显贵，不太体恤士兵。出征时皇帝送来几十车美食，回来时吃不完就扔了，可有的士兵还在挨饿；塞外缺粮，士兵饿得站不起来，他还在营里画出场地，踢球。", F("hw_yanzhi", 0.0))
shot(LD, "他还在甘泉宫的一次围猎中，射杀了老将李广的儿子李敢。汉武帝替他遮掩，对外只说，李敢是被鹿撞死的。", F("hw_ligan", 0.0), ctx=H, pad=1.2)
shot(LD, "他不是一个完人。可在那个时代，他是汉朝手里，最锋利的一把刀。", F("hw_jiawei", 90.0), ctx=RISE, pad=1.5)

# ================================================================== 十一 陨落
sec("第十一段 · 二十三岁", "xun", "heavy")
shot(LD, "漠北之战后两年，公元前117年。", F("hexi_film", 100.0), ctx=H, pad=1.2)
shot(LD, "霍去病突然病逝。史书里没有写他得了什么病，只有短短一行字。", F("hw54", 1225.0), ctx=H, pad=1.5)
shot(LD, "那一年，他二十三岁。", F("hw54", 1245.0), ctx=H, pad=2.0)
shot(LD, "汉武帝悲痛万分。他调来身穿黑色铠甲的属国骑兵，从长安城，一路列阵到茂陵，为他送葬。", F("hqb_trailer", 240.0), ctx=H, pad=1.5)
shot(LD, "他下令，把霍去病的坟墓，修成祁连山的样子。", F("maoling_walk", 480.0), ctx=H, pad=1.5)
shot(LD, "那座他从匈奴手里夺回来的山，最后，成了他长眠的地方。", F("hexi_film", 130.0), ctx=H, pad=1.8)
shot(LD, "墓前立着一座石雕：一匹战马昂首挺立，马蹄下踩着一个仰面挣扎的匈奴人。人们叫它，马踏匈奴。", F("mata_xiongnu", 0.0), ctx=RISE, pad=1.5)
breath("maoling_walk", 420.0, 7.0, amb=0.2)
shot(XY, "渡叔，我今年也二十三岁。我还在想，毕业以后要去哪儿。", ST_XYC, ctx=XYS)
shot(LD, "他用二十三年，跑完了别人的一辈子。", ST_LDC, ctx=H, pad=1.8)

# ================================================================== 十二 回声
sec("第十二段 · 回声", "hexi", "calm")
shot(LD, "霍去病走了。可他打通的那条路，再也没有断过。", F("qilian_grass", 130.0), ctx=RISE)
shot(LD, "河西四郡建了起来。一支又一支驼队从长安出发，穿过河西走廊，走向西域，走向更远的地方。后来，人们叫这条路：丝绸之路。", F("jiayuguan_cctv", 300.0), ctx=RISE)
shot(LD, "那个被他带到长安的弟弟霍光，后来辅佐了两代皇帝，执掌汉朝朝政将近二十年。", F("hw54", 1040.0), ctx=T)
shot(LD, "而封狼居胥这四个字，成了中国武将心里最高的荣誉。往后两千年，无数将军做梦都想去那座山上看一看。", F("shandan_air", 0.0), ctx=RISE)
shot(LD, "一千三百年后，南宋的辛弃疾登上京口北固亭，望着北方，写下：元嘉草草，封狼居胥，赢得仓皇北顾。", F("yumen_air2", 5.0), ctx=T)
shot(LD, "那是一个再也封不了狼居胥的时代，在远远地，怀念他。", F("gobi_devil", 90.0), ctx=H, pad=1.5)
shot(LD, "今天，坐高铁穿过河西走廊，窗外就是祁连山。两千一百多年前，一个少年的马蹄声，就是从那里，一路响到了今天。", F("jiayuguan_cctv", 160.0), ctx=RISE, pad=1.5)

# ================================================================== 结尾
sec("结尾", "jiangjun", "warm")
shot(XY, "渡叔，如果只用一句话说霍去病，你会怎么说？", ST_XY)
shot(LD, "他是那个替一个王朝，把头抬起来的少年。", ST_LD, ctx=RISE)
shot(XY, "那我会说：他的二十三年，比很多人的一百年都长。", ST_XYC, ctx=XYR)
shot(LD, "出身仕汉羽林郎，初随骠骑战渔阳。孰知不向边庭苦，纵死犹闻侠骨香。", ST_LDC, ctx=PR, pad=1.5)
shot(LD, "感谢收看回声号。炉火还旺着，祁连山的雪还没化。下期再见。", ST_LDC, ctx=W)
shot(NO, "", F("hexi_film", 255.0), card=["匈奴未灭，无以家为也。", "—— 霍去病（前140—前117）", "献给每一段少年时的热血。"], hold=15.0)

VO = {}
for _s in SHOTS:
    if _s["id"] in VO:
        _s["pic"] = VO[_s["id"]]


if __name__ == "__main__":
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps({"sections": SECTIONS, "shots": SHOTS, "bgm": BGM}, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(s["line"]) for s in SHOTS if not s.get("todo"))
    hosts = [s["id"] for s in SHOTS if s["pic"].startswith("img:st_")]
    ph = sorted({s["pic"].split("/")[1].split(".")[0] for s in SHOTS if "ph_" in s["pic"]})
    print(len(SHOTS), "shots,", n, "chars ≈", round(n / 4.3 / 60, 1), "min narration;", len(hosts), "host shots;", len(ph), "placeholder pics")
