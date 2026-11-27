"""回声号 EP08《敲门的人》预览稿 v3（11-24：去掉"罗伯说/罗尼说"式转述）。

主线：1975-12-23 卡迪夫，一个拎着冻鸡的无家可归者敲开一对年轻夫妇的门，住了四十五年（罗尼·洛克伍德 × 罗伯、黛安·帕森斯）。
史实见 research.md（A/B 级；C 级不用）。诊断：BBC 说自闭症，书里说从未正式诊断 → 两种说法都交代。
写法规则（skill echo-episode §1）：冷开场悬念 → 自我介绍 + 回声号 + 接上一期 → 起伏（谷→峰）+ 伏笔回收（门、墙、儿歌、"我是不是做错了什么"、校门口）；
诗用外国现代诗，直接念不报作者；人名代替代词；主持人台词 ≤ 约 50 字（2.0 fast 单条 15 s 上限）。
"""
import json
from pathlib import Path

EMOTION = """
v2（11-24 用户：顶椅子那段没人味、流水账，通篇没感情、太平）→ 文案重写：每个事实给一层人心；母题前埋后收；留白前先铺垫。
母题：门（敲门→椅子顶门→钥匙→探头说晚安→救护车门→洛克伍德中心→"门给你留着"）；"挺好"；"我是不是做错了什么"（→"你什么都没做错"）；
      没人等的校门口（→垃圾站门口有人送）；主日学儿歌（→病床边）；"永远在一起"（→"你说对了"）。诗：里尔克《严重的时刻》首尾、泰戈尔×2、狄金森。
冷开场 雨夜敲门、冻鸡、里尔克"走向我"（悬）→ 病房儿歌（伏笔）→ 片名
主日学（俏皮→"散了场要回哪里去"）→ 那道墙（谷）→ 没人等的校门口（谷底，留白）
今晚住下吧（暖）→ "挺好"（心疼）→ 椅子：门两边都在害怕（人心）→ 再也没防过他（升）
钥匙：大衣、内裤（笑→心疼）→ "我不去"（怕）→ 回头一眼 → 钥匙（峰，留白）→ 第一个圣诞哭了（泪点，留白）
惊喜：被看见（暖）→ 小河马（笑）→ 被需要（升）→ 兄弟 + 泰戈尔
永远在一起：卫生间（紧）→ 他察觉了（谷）→ "我们会永远在一起，对吧？"（悬，留白）
碎了的人：赌瘾、黛安的坦白（真实）→ 光脚回家 → 泰戈尔"以痛吻我"
门开向别人（暖）→ "这是罗尼的家"
我爱你：四十年太晚（憾）→ 救护车（谷）→ "带我回去" → 病床边的儿歌（全片最深，留白）→ 里尔克"眼望着我" → "你什么都没做错"
你说对了（峰，留白蓝天）→ 四万英镑、给别人留下一扇门（升）→ 结尾 狄金森 → 结尾卡
"""

BGM = {  # key: (file in bgm/, start s, volume[, {"fin": fade-in s, "hit": music time landing on the section's hit shot}])
    "silent": ("silentnight_piano.wav", 0, 0.45),     # 《Silent Night》钢琴：冷开场、我爱你
    "jlm": ("jesuslovesme.wav", 0, 0.5),               # 《Jesus Loves Me》八音盒：黛安在病床边唱的那首
    "suo_choir": ("suogan_choir.wav", 0, 0.55, {"hit": 60}),  # 《Suo Gân》合唱（太阳帝国）：片名、你说对了
    "arlanymor": ("arlanymor.wav", 0, 0.45),           # 威尔士民歌《Ar Lan y Môr》吉他：开场前厅
    "sunbeam": ("sunbeam.wav", 0, 0.4),                # 《Jesus Wants Me for a Sunbeam》：主日学
    "anyname": ("anyothername.wav", 0, 0.5),           # Thomas Newman《Any Other Name》：那道墙
    "airpiano": ("walkingair_piano.wav", 0, 0.5),      # 《Walking in the Air》钢琴：今晚住下吧
    "mattina": ("unamattina.wav", 0, 0.45),            # Einaudi《Una Mattina》：钥匙
    "airorch": ("walkingair_orch.wav", 0, 0.5),        # 《Walking in the Air》管弦：第一个圣诞
    "comptine": ("comptine.wav", 0, 0.4),              # Tiersen《Comptine d'un autre été》：罗尼的仪式
    "nuvole": ("nuvole.wav", 0, 0.45),                 # Einaudi《Nuvole Bianche》：抱婴儿、被需要
    "myfanwy": ("myfanwy_cello.wav", 0, 0.5),          # 《Myfanwy》大提琴：一个卫生间
    "lawrence": ("lawrence.wav", 8, 0.5),              # 坂本龙一《Merry Christmas Mr. Lawrence》：永远在一起
    "suogan": ("suogan.wav", 0, 0.45),                 # 《Suo Gân》器乐：碎了的人
    "calon": ("calonlan_piano.wav", 0, 0.45),          # 《Calon Lân》钢琴：门开向别人
    "calonharp": ("calonlan_harp.wav", 0, 0.5),        # 《Calon Lân》竖琴：结尾、片尾卡
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


DUB = {"罗伯": "配·罗伯", "黛安": "配·黛安"}


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
ROB = "你可以用一位七十多岁的英国老先生温和、真诚、带着回忆的语气说吗？"
ROB_T = "你可以用一位七十多岁的英国老先生很轻、很温柔、带着哽咽的语气说吗？"
DIANE = "你可以用一位七十多岁的英国老太太温柔、慈祥、带着哽咽的语气，轻轻地说吗？"

# ================================================================== 冷开场
sec("冷开场 · 敲门", "silent", "tense")
shot(LD, "1975年12月23日，威尔士，卡迪夫。冬夜的雨，下得又细又密。", F("cdf_rain", 30.0))
shot(LD, "一条联排小街上，家家户户的窗子都亮着。离圣诞节还有两天，每一扇窗子后面，都是一个正在等着过节的家。", F("risca70", 10.0), ctx=T)
shot(LD, "这时候，罗伯·帕森斯家的门，被敲响了。", F("door_knocker_man", 2.0), ctx=CTX["tense"], pad=1.2)
shot(LD, "罗伯本来想装作没听见。犹豫了一会儿，他还是起身，去开了门。", F("door_knock_wood", 1.0), ctx=CTX["tense"])
shot(LD, "门外，黑暗里站着一个男人。胡子拉碴，衣衫褴褛。一只手拎着黑色塑料袋，那是他在这世上的全部家当；另一只手里，攥着一只冻得发硬的鸡。", F("homeless_c4", 0.5), ctx=T)
shot(LD, "此刻有谁在世上某处走，无缘无故在世上走，走向我。", F("cdf_rain", 200.0), ctx=P, pad=1.8)
shot(LD, "罗伯认出了他。二十年前，主日学里那个总被大家捉弄的男孩，罗尼·洛克伍德。", F("rob_cff", 15.0), ctx=T)
dub("罗伯", "请进。只有两个字。这些年，我常常想起它们。就是这两个字，改变了我们所有人的一生。", "davina", 511.0, 526.0, ctx=ROB)
shot(LD, "那天晚上，没有人知道，这扇门一开，就是四十五年。", F("door_open", 0.0), ctx=T, pad=1.5)
bgm("jlm")
shot(LD, "四十五年后，2020年，疫情笼罩着整个世界。一间昏暗的病房里，一位老太太躺在病床边，把头轻轻靠在一个老人的枕头旁，唱起了一首儿歌。", F("covid_front", 80.0), ctx=H, pad=1.5)
shot(LD, "那首歌，他们小时候，都唱过。", F("cardiff59", 1240.0), ctx=T, pad=2.0)
bgm("suo_choir")
shot(NO, "", F("cdf_drone", 20.0), card=["敲门的人"], hold=7.0, hit=True)

# ================================================================== 开场
sec("开场", "arlanymor", "warm")
shot(LD, "大家好，我是老渡。今夜的回声号，在卡迪夫一栋老房子的前厅里。茶刚沏好，窗外下着雨。", ST_LDC)
shot(XY, "大家好，我是小柚。渡叔，我刚才一直在想：那天晚上要是换成我，我会不会去开那扇门？", ST_XYC, ctx=CTX["xy"])
shot(LD, "我也想过。说实话，我不确定。", ST_LD, ctx=T)
shot(LD, "这里是回声号。历史上每一个惊心动魄的瞬间，都会留下回声。有时候，那回声，只是一声敲门。", ST_LDC, sub="b")
shot(LD, "上一期，我们在雪山上走了七十二天；今夜，我们守着一扇门，讲四十五年。", ST_LDC, sub="c")
shot(XY, "你身后那扇绿色的门，是特意布置的吧？", ST_XY)
shot(LD, "特意的。不过开门之前，得先认识一下门外这个人。他的故事，要从一个没有人等的孩子说起。", ST_LD, ctx=T)

# ================================================================== 第一段
sec("第一段 · 主日学", "sunbeam", "warm")
shot(LD, "五十年代的卡迪夫，礼拜天的早晨。街角那座小教堂里，一群孩子挤在长凳上，听老师讲故事，唱儿歌。罗伯在里面，黛安也在。", F("cardiff59", 1200.0))
shot(LD, "有一天，威廉姆斯小姐叮嘱孩子们：下礼拜，会来一个新同学。他住在福利院，没有家。你们要对他好一点。", F("cardiff59", 1250.0), ctx=T)
shot(LD, "新同学来的第一天，就把威廉姆斯小姐的手提包藏了起来，又一把夹住了罗伯的好朋友特伦斯的脖子。", F("nottinghill70", 30.0), ctx=W)
shot(XY, "他是想让大家注意到他吧。", ST_XY, ctx=T)
shot(LD, "也许是。他跑不快，一逗就急，孩子们都爱逗他。可没有人知道，礼拜天散了场，这个男孩要回到哪里去。", ST_LD, ctx=T)

# ================================================================== 第二段
sec("第二段 · 那道墙", "anyname", "heavy")
shot(XY, "渡叔，他的家人呢？", ST_XY, ctx=CTX["xy_sad"])
shot(LD, "没有人说得清。八岁那年，他被送进了福利院。档案上，只有冷冰冰的一句话：处于道德危险之中。", F("barnardo_kent", 720.0))
shot(LD, "大人们哄他：去度个短假，很快就回来。", F("barnardo_kent", 300.0), ctx=T, pad=1.5)
shot(LD, "那个很快，再也没有来。到那儿还不到一天，大孩子们给新来的人搞入会仪式。一个八岁的孩子，被人从一道墙上推了下去。", F("orphanage_ldn", 5.0))
shot(LD, "六个星期的病床，两次手术。那道墙，从此长进了他的膝盖：他一辈子弯不了膝盖，站不了太久。很多年后，他还会在梦里喊：他们又逼我去走那道墙了。", F("orphanage40", 30.0), ctx=H, pad=1.5)
shot(LD, "十一岁，他被送到两百英里外的一所寄宿学校。官方报告里，那是一所给低能男孩上的学校。罗尼自己，管那儿叫：笨蛋学校。", F("barnardo_kent", 540.0), ctx=H)
shot(LD, "那所学校，九十年代初关了门。后来，看护人员的性侵丑闻一桩桩曝光，三个人进了监狱。那几年，一个孩子在那里经历过什么，再也没有人能说清了。", F("barnardo_kent", 600.0), ctx=H, pad=1.5)
shot(LD, "十六岁，他像一件没人认领的行李，被扔回了卡迪夫的街头。", F("cardiff59", 1600.0), ctx=H, pad=1.2)
shot(LD, "从那以后，他打零工，睡在哪儿算哪儿。没有人问他冷不冷，也没有人，等他回家。", F("homeless_itv", 280.0), ctx=H, pad=1.5)
shot(LD, "罗尼可能在自闭症谱系上，这是几十年后才有人看明白的事。可在他长大的那个年代，像他这样的孩子，只有一个名字：不一样。", F("risca70", 40.0), ctx=T, pad=1.2)
shot(XY, "渡叔……他小时候，有没有人送他去过一次学校？", ST_XYC, ctx=CTX["xy_sad"])
shot(LD, "一次也没有。每个孩子，都需要校门口有个人在等。可罗尼的校门口，从来都是空的。", ST_LDC, ctx=H, pad=1.5)
breath("risca70", 60.0, 6.0, amb=0.3)

# ================================================================== 第三段
sec("第三段 · 今晚住下吧", "airpiano", "tender")
shot(LD, "所以，1975年的那个冬夜，快三十岁的罗尼，又站到了一扇门外。前一天晚上，他敲开另一户教会人家的门，那家人没有留他，只给了他一个地址：去找帕森斯夫妇吧。", F("cdf_rain", 120.0), ctx=T)
shot(LD, "门一开，罗尼就从罗伯身边挤了进去，穿过小小的走廊，一头钻进厨房，把那只冻鸡塞进正在做饭的黛安手里：给你的。", F("rob_cff", 24.0), ctx=W)
shot(XY, "他是把自己唯一的东西，当成了见面礼呀。", ST_XY, ctx=T)
shot(LD, "黛安看看罗伯，看看罗尼，又看看手里那只鸡。然后，她转过身，把那只鸡下了锅。", ST_LD, ctx=W)
shot(LD, "饭快吃完的时候，黛安把罗伯拉进另一个房间，压低了声音：今天是圣诞节啊，他没有地方去。我去收拾客房，你去问问他，今晚愿不愿意住下。", F("xmas70_party", 4.0), ctx=T)
shot(LD, "罗伯走回客厅。罗尼正盯着电视里的《加冕街》，一眼都舍不得挪开。罗尼，今晚就住我们这儿，好吗？", F("tvset70", 4.0), ctx=T)
shot(LD, "他的眼睛没离开屏幕，只应了一声：挺好。", F("corrie75", 11.5), ctx=T, pad=1.5)
shot(LD, "挺好。这是他一辈子挂在嘴边的两个字。一个从小被推来推去的人，早就学会了，不去要求什么。", ST_LD, ctx=T, pad=1.2)
shot(LD, "那天夜里关了灯，黑暗里，黛安的声音很轻：要是他……做点什么呢？我们几乎不认识他。", F("terrace70_cobbled", 30.0), ctx=CTX["tense"])
shot(LD, "罗伯只好爬起来，下楼搬了一把餐椅，轻轻顶在了卧室门后。", F("door_open", 2.0), ctx=T, pad=1.2)
shot(XY, "其实……换了谁，都会害怕吧。", ST_XYC, ctx=T)
shot(LD, "是啊。门这边的人在害怕。门那边的人，也许也在害怕。", ST_LD, ctx=T)
shot(LD, "一个习惯了被送走的人，躺在陌生人家的床上，也许也在想：明天早上，他们会不会让我走。", ST_LD, ctx=H, sub="b", pad=1.5)
shot(LD, "那把椅子，没顶多久。后来的四十五年，这个家的门，再也没有防过罗尼。", ST_LDC, ctx=T, pad=1.5)

# ================================================================== 第四段
sec("第四段 · 钥匙", "mattina", "warm")
shot(LD, "过完圣诞，夫妻俩才发现，罗尼被困在一个圈里：没有地址，开不了银行账户；没有账户，找不到工作；没有工作，就永远租不到一个地址。", F("cardiff77", 64.0))
shot(LD, "这个圈，困了他十几年。现在，他有了一个地址。他找到了人生第一份正式工作：收垃圾。", F("dustmen70_bbc", 10.0), ctx=W)
shot(LD, "上班前一天，夫妻俩带他去买衣服，像一对送孩子第一天上学的年轻父母：挑了大衣，又挑这挑那，一样一样地往篮子里放。", F("cardiff77", 32.0), ctx=W)
shot(LD, "排队结账的时候，黛安凑到罗伯耳边：他……有内裤吗？一问，罗尼答得坦坦荡荡：我不穿。", F("xmas70_presents", 5.0), ctx=W)
shot(XY, "三十岁了，连一条内裤都没有……", ST_XY, ctx=CTX["xy_sad"])
shot(LD, "黛安又气又心疼，把两个男人一起轰去了内衣柜台。", ST_LD, ctx=W)
shot(LD, "第二天一早，新衣服都穿好了，罗尼却站在门口不动了：我不去了。他害怕。", F("binmen76_bbc", 0.5), ctx=T, pad=1.2)
shot(LD, "黛安没有劝，也没有催，只轻轻一句：罗尼，你要是不去，我会难过的。罗尼想了很久：好吧，我去。", F("binmen76_bbc", 200.0), ctx=T)
shot(LD, "罗伯开车把他送到垃圾站门口。罗尼下了车，一步一步往院子里走。院子里站着一群正在说笑的工人。走到一半，他回过头，看了罗伯一眼。", F("dustmen70_bbc", 200.0), ctx=T, pad=1.2)
shot(LD, "接下来的那一刻，罗伯记了一辈子。", F("davina", 940.0), ctx=T, pad=1.0)
dub("罗伯", "我追了上去：罗尼！罗尼！他转过身来。我把家里的钥匙放进他手里：这是你的，罗尼。那是他这辈子的第一把钥匙。我就是要当着那些人的面给他。开车去律所的路上，我一直在流泪。", "davina", 955.0, 981.0, ctx=ROB)
breath("rob_cff", 36.8, 5.0, amb=0.2)
shot(LD, "三十岁这一年，那个第一天上学时没有人送的孩子，终于，有人送到了门口。", ST_LDC, ctx=H, pad=2.0)
shot(LD, "这一干，就是二十九年。他每天准时出门，按月交税，挺直了腰杆。一个流浪了十几年的人，有了尊严。", F("binday89_swansea", 80.0), ctx=CTX["rise"], pad=1.2)
bgm("airorch")
shot(LD, "那年圣诞节，黛安急急忙忙，给罗尼包了几份小礼物。", F("xmas50_home", 20.0), ctx=T)
shot(LD, "罗尼坐在圣诞饭桌前，一个一个地拆。拆着拆着，他哭了。", F("xmas50_home", 60.0), ctx=H, pad=1.5)
shot(LD, "快三十年了。这是他第一次，在一个家里过圣诞节。", F("bbc_ronnie", 18.0), ctx=H, pad=2.0)
breath("xmasdinner76", 1318.0, 6.0, amb=0.3)

# ================================================================== 第五段
sec("第五段 · 惊喜", "comptine", "warm")
shot(XY, "渡叔，那罗尼在这个家里，是个什么样的人？", ST_XY)
shot(LD, "话很少。问他什么，都是挺好。他最常问的，是另一句：我是不是做错事了？", ST_LD, ctx=T)
shot(LD, "住进来的第二天，他神秘兮兮地把罗伯拉进厨房：我给你准备了一个惊喜。然后打开洗碗机：里面的碗盘，全都拿出来放好了。", F("family80_lpool", 30.0), ctx=W)
shot(LD, "罗伯随口一句：哦，你把洗碗机清空了。罗尼的脸，一下子就沉了下来。他要的不是一句谢谢，是有人假装吃一惊，是有人，看见他。", ST_LD, ctx=T)
shot(LD, "从那以后，这个惊喜，他们演了四十五年。礼拜一刚收过的碗，礼拜三，还得再吃一惊。", F("family80_lpool", 200.0), ctx=W, pad=1.2)
shot(XY, "一个演了四十五年的惊喜……好像比什么礼物都珍贵。", ST_XYC, ctx=T)
bgm("nuvole")
shot(LD, "几年后，女儿凯蒂出生了。抱她回家那天，黛安问罗尼：想抱抱她吗？罗尼往后缩了缩：我觉得，这不是个好主意。", F("maternity70b", 1.0), ctx=W)
shot(LD, "罗伯这才意识到：这个三十多岁的男人，这辈子，从来没有抱过一个婴儿。", F("firststeps78", 20.0), ctx=T, pad=1.2)
shot(LD, "黛安让他坐下，张开胳膊。罗尼张开双臂，张得那么开，像是要接住一头小河马。", F("firststeps78", 100.0), ctx=W)
shot(LD, "黛安笑着把他的胳膊往里拢了拢，把凯蒂放进他怀里。该还回去的时候，罗尼舍不得撒手。嘴里还小声嘀咕着：我挺会带孩子的。", F("firststeps78", 170.0), ctx=T, pad=1.2)
shot(LD, "儿子劳埃德出生以后，黛安病倒了，一病就是六年；罗伯在律所忙得没日没夜。冲奶瓶，哄孩子，做豆子吐司，都落在了罗尼身上。", F("baby80_matthew", 136.0), ctx=W)
shot(LD, "这个一辈子被人安排、被人送走的人，第一次，被一个家需要着。", F("family80_lpool", 160.0), ctx=CTX["rise"], pad=1.5)
dub("罗伯", "他刚来的时候，是个房客。后来，成了朋友。再后来，成了我从来没有过的兄弟。我们俩爱着同一个人，她病了，我们一起陪她熬过来。", "davina", 1382.0, 1392.0, ctx=ROB)
shot(LD, "我们曾经梦见，我们是陌生人。醒来，才发现，我们原是相亲相爱的。", ST_LDC, ctx=P, pad=1.8)

# ================================================================== 第六段
sec("第六段 · 永远在一起", "myfanwy", "tender")
shot(XY, "那这个家，就这样一直过下去了吗？", ST_XY)
shot(LD, "差一点，就没有。凯蒂十一岁那年，孩子们大了，家里只有一个卫生间，越来越挤。", ST_LD, ctx=CTX["tense"])
shot(LD, "黛安提议：要不，在附近给罗尼租个小公寓吧。罗伯点了头。可真要开口的时候，黛安先摇了头：我做不到。", F("terrace70_cobbled", 60.0), ctx=T)
shot(LD, "可罗尼，好像已经察觉到了什么。一个从小被推来推去的孩子，对要被送走这件事，有一种天生的灵敏。", F("risca70", 220.0), ctx=H, pad=1.5)
bgm("lawrence")
shot(LD, "过了两天的一个晚上，罗尼敲了敲他们的房门。那天晚上的每一句话，罗伯都记得。", F("cdf_night", 75.0), ctx=T, pad=1.0)
dub("罗伯", "他站在门口：我能跟你们俩聊几句吗？他进来坐下，开口第一句就是：我没做坏事吧？没有啊，罗尼，怎么了？他沉默了一会儿：我们三个，是好朋友，对吧？我们会永远在一起，对吧？", "davina", 1072.0, 1091.0, ctx=ROB)
shot(LD, "这个问题，在空气里悬了很久，很久。", F("davina", 1092.0), ctx=T, pad=2.0)
shot(LD, "最后，黛安冲罗伯，轻轻点了点头。罗伯看着罗尼：是的，罗尼。我们会永远在一起。", F("bbc_ronnie", 63.0), ctx=T, pad=2.0)
breath("family80_lpool", 230.0, 6.0, amb=0.0)
shot(XY, "……他们做到了吗？", ST_XYC, ctx=CTX["xy_sad"])
shot(LD, "这个答案，我们留到最后。", ST_LDC, ctx=T)

# ================================================================== 第七段
sec("第七段 · 碎了的人", "suogan", "calm")
shot(XY, "听到这儿，我觉得罗尼像个天使。", ST_XY, ctx=T)
shot(LD, "可他不是天使。他是一个碎过的人。", ST_LD, ctx=CTX["calm"])  # 11-24: TTS with ctx=T tripped Ark InputAudioSensitiveContentDetected twice -> new take
shot(LD, "他在酒吧里玩老虎机，一玩就停不下来。这个家，陪他跟赌瘾斗了二十年。他撒谎，又撒得那么笨，一戳就破。", F("pub60_xmas", 10.0))
shot(LD, "这些年，黛安从不把罗尼说成圣人。", F("cg_ronnie", 330.0), ctx=T, sub="b")
dub("黛安", "说实话，有时候，我真希望他不在。这是大实话，一点都不掺假。", "cg_ronnie", 345.0, 351.0, ctx=DIANE)
shot(LD, "那几年，她一个人带着刚出生的孩子，丈夫天天加班到很晚。罗尼每天进门，会把一份《南威尔士回声报》直直地戳到她脸上。她终于忍不住：罗尼，我又不是狗。你把报纸放到我手里，好吗？", F("cardiff77", 72.0), ctx=W)
shot(XY, "可她还是留下了他。原来爱一个人，也包括忍受他。", ST_XYC, ctx=T)
shot(LD, "也是这个罗尼，有一天光着脚回了家。他把自己的新鞋，送给了街上一个流浪汉。他觉得，那个人比他更需要。", F("homeless_c4", 120.0), ctx=T, pad=1.2)
shot(LD, "他很美好。可他，也碎得很厉害。", ST_LDC, ctx=T)
shot(LD, "世界以痛吻我，要我报之以歌。", F("cdf_rain", 300.0), ctx=P, pad=2.0)

# ================================================================== 第八段
sec("第八段 · 门开向别人", "calon", "warm")
shot(LD, "1988年，罗伯辞去了律师的工作，和黛安一起，创办了一家帮助普通家庭的慈善机构。他开始满世界演讲，坐上了协和式飞机。", F("rob_vhs97", 300.0))
shot(LD, "一个在云端，一个在垃圾站。可罗伯慢慢发现，他们俩心里的那些挣扎，其实很像。", F("concorde03", 15.0), ctx=T)
shot(LD, "罗尼成了教会的椅子总管。每个礼拜天，他把椅子一把一把摆好；到了晚上，再去流浪者中心帮忙。", F("chairs_tl", 0.5), ctx=W)
shot(LD, "节礼日的慈善足球赛，他张罗了二十五年。隔壁老太太的垃圾桶，每个星期四，他都替她推出去。", F("charity_ninian", 200.0), ctx=W)
shot(LD, "新搬来的邻居悄悄问罗伯：每天下午四点，一辆垃圾车停在你家门口，下来一个清洁工，径直走进你家。那是谁？", F("binday89_swansea", 600.0), ctx=W)
shot(LD, "罗伯回答得再平常不过：那是罗尼。这是他的家。", ST_LDC, ctx=T, pad=1.5)
shot(XY, "他自己，是被一扇门救的。后来，他就一直替别人开门。", ST_XYC, ctx=T)

# ================================================================== 第九段
sec("第九段 · 我爱你", "silent", "tender")
shot(LD, "日子就这样过了几十年。直到有一天，罗伯读到一本书。作者也是在福利院长大的，书里有这样一句：大人们总说，我喜欢和孩子们一起工作。可从来没有人说过，他们爱我。", F("reynolds", 775.0), ctx=T)
shot(LD, "罗伯合上书，愣了很久：我好像，从来没有对罗尼说过我爱你。也许他这辈子，都没有听过这三个字。", ST_LD, ctx=T, pad=1.2)
shot(LD, "他多希望，这件事发生在四十年前。可它来得太晚了，离罗尼去世，只剩大概两年。", F("reynolds", 785.0), ctx=H, pad=1.5)
shot(LD, "每天晚上，罗尼睡前都会把头探进门来：晚安。从那天起，门里多了一句回答：我爱你，罗尼。门外，传来一声含含糊糊的咕哝。", F("door_open", 5.0), ctx=T, pad=1.5)
shot(XY, "黛安呢？她说了吗？", ST_XY, ctx=T)
shot(LD, "黛安给了罗尼很多很多的爱。可这三个字，她始终说不出口，她怕他误会。", ST_LD, ctx=T)
shot(LD, "2020年，疫情最重的时候。一天，罗伯在楼下书房，接到了罗尼的电话。", F("lockdown_cdf", 32.0), ctx=CTX["tense"])
dub("罗伯", "电话那头只有一句：我摔倒了，起不来了。是中风。因为疫情，我们不能跟着上救护车。车门关上之前，他看起来那么迷茫。我朝他喊：我爱你，罗尼！隔着车门，他也喊：我爱你。", "davina", 1747.0, 1768.0, ctx=ROB_T)
shot(LD, "罗尼从来没有登记过残疾，医院不给探视。一家人，只能在家里等。", F("covid_front", 20.0), ctx=H, pad=1.5)
shot(LD, "后来，罗伯终于见到了他一面。罗尼抬起头看着他，只有三个字：带我回去。", F("covid_front", 40.0), ctx=H, pad=2.0)
bgm("jlm")
shot(LD, "最后那天，医院让他们过去。一间昏暗的小病房，管子都撤了，只剩一根氧气管。他们坐在黑暗里，看着床单，一起，一伏。", F("covid_front", 160.0), ctx=H, pad=1.5)
shot(LD, "罗伯抱着罗尼，泣不成声：我爱你，罗尼。这时候，黛安从椅子上站了起来。", F("cdf_night", 30.0), ctx=H, pad=1.5)
dub("黛安", "我就躺到他身边，把头靠在他的枕头上，开始唱：耶稣爱我。我只是想让他知道，有人陪着他，一直到最后。他不是一个人。", "cg_ronnie", 290.0, 310.0, ctx=DIANE)
shot(LD, "那是将近七十年前，主日学的老师教他们唱的歌。黛安唱了一遍，又一遍，又一遍。", F("cardiff59", 1240.0), ctx=H, pad=2.0, again=True)
breath("cdf_rain", 500.0, 8.0, amb=0.0)
shot(LD, "此刻有谁在世上某处死，无缘无故在世上死，眼望着我。", F("cdf_rain", 450.0), ctx=P, pad=2.0)
shot(LD, "罗尼走了，七十五岁。他走的时候知道，自己是被爱着的。", F("cdf_rain", 560.0), ctx=H, pad=2.0)
shot(LD, "罗尼这辈子最常问的那句话：我是不是做错了什么？到最后，终于有了答案：没有，罗尼。你什么都没做错。", ST_LDC, ctx=H, pad=2.0)

# ================================================================== 第十段
sec("第十段 · 你说对了", "suo_choir", "tender")
shot(XY, "渡叔，那个问题……他们做到了吗？", ST_XYC, ctx=CTX["xy_sad"])
shot(LD, "罗尼的葬礼，在那年九月。那一天的很多事，罗伯都记不清了，只记得一件。", F("cdf_drone2", 95.0), ctx=T, pad=1.0)
dub("罗伯", "葬礼结束后，我和黛安在外面站了一会儿。九月的天，蓝得出奇。黛安忽然问我：还记得那么多年前，罗尼问我们的那句话吗？我们会永远在一起，对吧？还记得你是怎么回答的吗？我当然记得：我们会永远在一起。她看着我：你说对了。", "davina", 1834.0, 1856.0, ctx=ROB_T)
breath("cdf_drone", 40.0, 8.0, amb=0.0)
shot(LD, "罗尼走后，隔壁那位老太太送来一束花。家人打开他的遗嘱：一个收了二十九年垃圾的人，给慈善机构留下了大约四万英镑。", F("glenwood_meal", 4.0), ctx=T)
shot(LD, "那时候，他们的教会正在盖一座社区关怀中心，屋顶还差一笔钱。差的那个数，和罗尼留下的那笔钱，几乎分毫不差。", F("cdf_drone2", 30.0), ctx=CTX["rise"])
shot(LD, "这座中心，后来用他的名字命名：洛克伍德中心。一个当年无处可去的人，最后，给别人留下了一扇门。", F("cdf_drone", 80.0), ctx=CTX["rise"], pad=1.5)
shot(LD, "2024年，罗伯把这四十五年写成了一本书，书名就叫《敲门》。书里有一句：罗尼·洛克伍德，是给我们所有人的一份礼物。", F("rob_vhs97", 400.0), ctx=T)

# ================================================================== 结尾
sec("结尾", "calonharp", "tender")
shot(XY, "渡叔，今晚要是真有人敲我们这扇门……你会开吗？", ST_XY)
shot(LD, "我还是不确定。罗伯和黛安当年，其实也不确定。他们只是在那个晚上，多煮了一个人的饭。", ST_LD, ctx=T)
shot(LD, "可四十五年后，罗伯有了他的答案：如果早知道后来的一切，我们还是会去开那扇门。还是那句话：今晚住下吧。", ST_LDC, ctx=T, sub="b")
shot(XY, "在凯蒂心里，罗尼不是什么舅舅，也不是什么房客。他就是罗尼呀，家里的一个人。", ST_XYC, ctx=CTX["xy_sad"])
shot(LD, "如果我能让一颗心免于破碎，我就不虚此生。如果我能让一只昏厥的知更鸟，重新回到它的巢里，我就不虚此生。", ST_LDC, ctx=P, pad=1.5)
shot(LD, "感谢收看回声号。雨停了，茶还热着。门，我们一直给你留着。下期再见。", ST_LDC, ctx=W)
shot(NO, "", F("cdf_drone", 140.0), card=["“Stay with us tonight, Ronnie.”", "罗尼，今晚住下吧。", "—— 黛安·帕森斯，1975年12月23日", "他住了四十五年。献给每一扇在寒夜里打开的门。"], hold=15.0)

VO = {  # 正片 11-24: cost cap 300 元 -> long story lines become 老渡 voice-over on footage (text unchanged, id unchanged); 070/125/135b also exceed the 15 s clip cap
 "022": F("terrace70_lpool", 20.0),     # 他跑不快，一逗就急……散了场要回到哪里去
 "039": F("xmasdinner76", 1000.0),      # 黛安看看罗伯……把那只鸡下了锅
 "043": F("risca70", 300.0),          # 挺好……不去要求什么（罗尼扶手椅照）
 "047b": F("cdf_night", 95.0),          # 一个习惯了被送走的人……会不会让我走
 "061": F("binmen76_bbc", 480.0),       # 三十岁这一年……有人送到了门口
 "070": F("family80_lpool", 90.0),      # 洗碗机：是有人，看见他
 "080": F("xmas70_super8", 60.0),          # 泰戈尔：我们曾经梦见我们是陌生人（罗伯+婴儿+罗尼圣诞照）
 "082": F("terrace70_cobbled", 90.0),   # 凯蒂十一岁那年，一个卫生间
 "109": F("reynolds", 690.0),           # 罗伯合上书，愣了很久
 "125": F("cdf_drone", 160.0),         # 你什么都没做错（罗尼扶手椅照）
 "135b": F("rob_cff", 42.0),            # 罗伯有了他的答案：今晚住下吧
 "137": F("cdf_xmas", 380.0),          # 狄金森
 "093": F("cdf_rain", 380.0),            # 碎过的人 - Ark refused this line's audio ref 4x (InputAudioSensitiveContentDetected)
}
for _s in SHOTS:
    if _s["id"] in VO:
        _s["pic"] = VO[_s["id"]]


if __name__ == "__main__":
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps({"sections": SECTIONS, "shots": SHOTS, "bgm": BGM}, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(s["line"]) for s in SHOTS if not s.get("todo"))
    hosts = [s["id"] for s in SHOTS if s["pic"].startswith("img:st_")]
    dubs = [s["id"] for s in SHOTS if s["pic"].startswith("fd:")]
    todo = [s["id"] for s in SHOTS if s.get("todo")]
    print(len(SHOTS), "shots,", n, "chars ≈", round(n / 4.3 / 60, 1), "min narration;", len(hosts), "host shots", hosts, "TODO", todo, "dubs", dubs)
