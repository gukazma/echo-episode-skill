# 剧本格式（script_vN.py → script_vN.json）

```python
BGM = {key: (文件名 | None, 起始秒 ss, 音量)}
sec(段落名, bgm_key)                # 开一个段落，后续镜头用这个 BGM
shot(who, line, pic)               # who: 老渡 / 小柚 / 无；id 自动 001,002,...
ins(who, line, pic)                # 在上一镜头后插入，id = 基id + n<k>，不重编号（studio take 按 id 绑定）
MONT = {key: {"music":..., "xfade":0.6, "pieces":[[ep, a, b, "now"|"flash"], ...]}}
PIC = {id: 新pic}                   # 统一覆盖，替换静态图/AI 图为动态素材
TONE / pad                          # 每句语气（TTS context_texts）与句尾留白
```

json：`{"shots": [{id, sec, who, line, pic, bgm, tone?, pad?, card?, hold?}], "bgm": {...}, "montages": {...}}`

## pic 语法

| 写法 | 含义 |
|---|---|
| `img:st_ld` / `st_xy` / `st_ld_cam` / `st_xy_cam` | 主持人镜头（必须在 accepted.json 有 take，否则拒绝渲染） |
| `d:EP:SEC` | 94 版第 EP 集第 SEC 秒附近的**动态片段**（时长 = 台词） |
| `f:FILE:SEC` | `footage/FILE.mp4` 第 SEC 秒附近的实拍片段 |
| `clip:EP:A:B:orig\|mute\|<bgm>` | 原片 A–B 秒，保留原声 / 静音 / 用某段音乐当声音 |
| `mont:KEY` | 蒙太奇 |
| `ai:描述` / `img:v_*` | **禁止**（用户不要 AI 图和静态图） |

## 写作规则

- 每个主持人镜头一句话、一个人；台词 ≤ ~10 s（更长会拆两条 take）。
- 叙述镜头（画外音 + 素材）由老渡/小柚 TTS 配音；小柚负责提问、共情，老渡讲述。
- 数字、年份、人名逐一核对；多音字写进 SAY / PRON；避免易误读词（EP01：收购→收盖、濒临→冰临）。
- 自我介绍：老渡"爱翻旧书、爱讲老故事"，小柚"替大家问问题"；"回声号"：每个惊心动魄的瞬间都会留下回声。
- 结尾：小柚问一个朴素的问题（"蜀国那么小，魏国那么大，他真的觉得能赢吗？"），老渡收束到主题，再接致敬卡。
