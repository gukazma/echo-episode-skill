---
name: echo-episode
description: 制作《回声号》式双主持人历史/人物科普长视频（老渡+小柚 AI 主持 + 影视原片/实拍素材 + 克隆配音 + 古风 BGM），从选题、剧本、分镜样片、Seedance 主持人镜头、素材剪辑、混音、封面到 B 站发布文案的全流程。当用户要做新一期回声号、AI 科普短剧、"老高与小茉"式对话节目、人物/历史纪录片式视频，或要修改这类成片（结巴/卡顿、口型、封面、BGM、结尾卡、发布标题标签）时使用。
---

# 回声号单集制作

两期实战沉淀：EP01《龙不会老》（马斯克/SpaceX，11:39→v4）与 EP02《一诺千年——真实的诸葛亮》（33:21，v11）。
本 skill 是**流程 + 硬规则 + 踩坑清单**；具体参数见 `references/`，可直接复用的工具在 `scripts/`。

## 0. 环境（一切都在用户的 Windows 制作机上）

- 连接：按你本机的远程说明（如 `~/REMOTE_PC.md`）ssh 到 Windows 制作机，对端是 cmd.exe。
- 工程：`D:\OpenMontage`（venv `.venv`，Python 3.11，ffmpeg 8，faster-whisper，pypinyin）。每期一个目录 `D:\OpenMontage\output\echo_epNN`，沙盒镜像 `~/hs/epNN`（改脚本在沙盒，`scp` 上去）。
- 密钥在 `D:\OpenMontage\.env`（`ARK_API_KEY`、`VOLC_TTS_APIKEY` 等）：**绝不 type/cat/echo 这个文件，不回显任何 key**。
- **制作机 是用户正在打字的电脑：绝不弹窗。** 所有任务写成 `run_xxx.cmd`，用 `powershell -NoProfile -ExecutionPolicy Bypass -File launch.ps1 run_xxx.cmd`（WMI 隐藏启动，见 `scripts/launch.ps1`）。只杀自己的进程：`taskkill /PID <pid> /T /F`。
- 中文文件名的文件操作用 Python，不用 cmd。cmd 文件开头加 `chcp 65001 >nul`，`set PYTHONIOENCODING=utf-8`。
- 等后台任务：轮询**本轮新写入**的完成标记；日志用 `>` 覆盖而非 `>>`，否则会读到上一轮的 DONE（EP02 踩过）。
- 新装外部代码/模型要先征得用户同意。

## 1. 硬规则（用户反馈沉淀，违反过就被打回）

内容
- 选题要**动人、励志**，不是干巴巴科普：要有情感弧线（低谷→坚持→兑现）和金句；每条史实都要核对（EP02 改过：班洪事件是 1934 年不是抗战时期；"帽子房"传说属傣族）。
- 冷开场（一个强场景）→ 开场自我介绍（老渡/小柚）→ 分段正文 → 高潮用原片 → 身后/后世影响 → 结尾对话 → 居中致敬卡。
- **不要采访、百家讲坛、后人讲话等现代原声插入**——用户嫌突兀，只要"旁白 + 镜头"。
- 时长不设上限（EP02 33 分钟可以），但不能拖沓。

画面
- **只有老渡/小柚是 AI 生成**（Seedance）。其他所有画面用影视原片（如 94 版《三国演义》）或网络实拍（景点航拍等）。
- **禁止静态图和 AI 示意图**：不能"截一帧 + 推拉"（zoompan 还会抖），必须是**动态原片片段**。
- 原片要裁掉台标和烧录字幕（`DRAMA_VF`、`cropdetect` + 内缩裁切）；片头字幕/演职员表镜头换掉。
- 小柚**不能陷进沙发**：坐姿提示词锁定 `【POSTURE】`，背景 plate 用比例正常的椅子。
- 连续的主持人镜头动作要连贯：用上一条的最后一帧做 continuity 参考；同机位不要越推越近。
- 一个镜头只有一个人说话（正反打）。

声音
- 老渡 = 沉稳、克制的力度；小柚 = 温柔可爱，不一惊一乍。激昂处要起来，但不过火。
- **不要用 speech_rate 加速**（发紧、不自然）；靠克隆 2.0 + 语气上下文 `context_texts` 得到节奏和情绪。
- 主持人镜头**用 Seedance 原片原声**。口型对齐方案（LatentSync 等）用户明确拒绝："机器出戏"。
- **结巴/卡顿零容忍**（重复字、句中长停顿、拖音）：严格 QC + 补拍 + 剪辑收紧停顿（见 §5）。
- 多音字逐句检查（TTS 用 `SAY` 替换表，Seedance 用 `【PRONUNCIATION】` 或改写台词）。

音乐
- BGM 必须古风/与题材相符（EP02：古琴《卧龙吟》、《赤壁》配乐、古筝《渔舟唱晚》、《送别》、例外《说了再见》钢琴）；不要 Interstellar/Time 这类不搭的。
- 结尾**不能在 BGM 中途结束**：至少让《送别》完整收尾（`build_after_fit` 把最后一段音乐倒推对齐片尾）。
- 版权：用户要求音乐/影视素材不考虑版权；但**不要自己抄写受版权保护的歌词全文**，让用户提供。

成片
- **封面 = 视频首帧 = 内嵌缩略图**（2.5 s 封面段 + `attached_pic`）。封面要好看：EP02 用户否了"哭丧脸"，要年轻、好看的全身像（白衣羽扇）。
- 致敬/结尾卡：**居中**，停留足够久（≥13 s，EP02 用 18 s），不要放在字幕位置。
- 交付直接给 制作机 上的文件路径（新版本号，不覆盖旧版）；不要 commit。

预算
- 用户会说预算（EP02 900 元）；超支前要估算。用户说过"花钱吧不用先问我"后可直接补拍，但仍报实际花费。
- Seedance mini 720p ≈ 0.5 元/秒（工具返回的 cost 字段是 USD，×7.2）。EP02 主持人 46 镜头 ≈ 437 元含重拍，总 ≈ 860 元。

## 2. 流程与确认关口

每个 ⛳ 是**必须等用户确认**的关口；不要提前开始后面的阶段（连构建/改文件都不要）。

1. **选题 + 大纲** ⛳：一句话主题（EP02："一诺千年"——守一句承诺二十七年），情感节拍表，核心史实及出处。
2. **剧本** ⛳：`script_vN.py` → `script_vN.json`（格式见 `references/script-format.md`）。每句台词：说话人、画面来源、语气 tone、段落 BGM。同时出 `分镜表.md`。
3. **声音样音** ⛳：克隆音色（老渡 `<老渡音色ID>`、小柚 `<小柚音色ID>`，`voice_ids.json`），挑几句代表性台词给用户听。
4. **分镜样片** ⛳：`PREVIEW_TTS=1` 渲染（TTS 配音 + 已有画面），先看新内容是否合适——**花大钱前必须先过这一关**。
5. **主持人镜头生产**：`studio_plan.py` → `studio_produce.py`（链式、last-frame 连贯）→ `qc2.py` 严格 QC → 补拍 → `choose_orig.py` 选条 → `studio/accepted.json`。
6. **素材**：94 版剧集 `drama/eps/eNN.mp4`；网络实拍下到 `footage/`（下载在沙盒/代理做，再 scp）。每个镜头用 `d:EP:SEC` / `f:FILE:SEC` 指向**动态片段**。
7. **成片渲染**：`tighten.py`（收紧停顿/去重复字）→ `make_v4.py video`（`OUT=...`）→ `tverify.py` + 出片前检查（§6）。
8. **交付** ⛳：给路径、时长、改了什么、仍有的瑕疵（诚实列出）。
9. **发布文案**：标题 3 选 1、简介（含章节时间戳 `chap.py`、素材与音乐来源、AI 生成声明）、标签（见 `references/publish.md`）。

## 3. 主持人镜头（Seedance）要点

- 模型：Seedance mini，720p，`reference_to_video`，参考图 = 角色定妆照 + 背景 plate (+ 上一条最后一帧)，`generate_audio=True`，参考音频 ≈5 s 声音样本保持音色。
- 时长：`ceil(1.15 × TTS时长 + 1)`；台词 > 10.8 s 拆成 a/b 两段（`FORCE_SPLIT`），同一链里连续生成。片长给多了 Seedance 会**重复说词来填时间**。
- 提示词块：`【STYLE】【CHARACTER】【SCREEN DIRECTION】【POSTURE】【PERFORMANCE】【SHOT】【LINE】【VOICE】【PRONUNCIATION】【LIGHTING】(+【CONTINUITY】)`，并写"台词只说一遍，一字不差，说完就闭嘴"。
- 链条 4–5 跳后会漂（眼镜变色等）→ 从 plate 重新起链。链式会越推越近 → continuity 里写"景别按 SHOT 重新构图"，把"缓推"换"固定机位"。
- Ark 会拦含人脸参考图生成的 Seedream 图（InputImageSensitiveContentDetected）；plate 用无人背景图。美国国旗特写会触发版权拦截。
- 补拍时只重拍 QC 有问题的；每条拍 2–3 个 take，按 QC 选最干净的。

## 4. QC 指标（`qc2.py`，whisper medium，无 initial_prompt，word timestamps）

- **REP**：识别文本拼音对比台词，多出来的字（重复）。
- **SYL**：声学音节数 > 字数×1.12+1（拖音/重复）。
- **GAP**：句中停顿 > 0.55 s 且多于标点数。
- **SLOW**：语音时长 > 1.45 × TTS 时长。
- 单个重复音节常是拖音（可接受），多字重复才是真结巴。
- 不要给 whisper `initial_prompt`：会吞掉开头匹配的词，误判"漏说"。

## 5. 卡顿收紧（成片前必做）

Seedance 原声常在句中停 1–2.7 s、偶尔重复字。`scripts/tighten.py`：
- 声学静音段（RMS < 7% 峰值）> 0.75 s → 缩短到 0.4 s（保留 0.2 s 头）。
- 相邻相同单字（的的/操操/在在）且台词里没有该叠字 → 删第一个（注意"罚他，他才"这种合法叠字，她/他归一化）。
- **保护词尾**：词尾 0.3 s 内有可闻声（> max(3% 峰值, 3×底噪)）不剪——"对自己也一样"里轻声的"也"曾被误剪。
- 输出 `studio/tighten.json`（剪切区间）+ `studio/tail.json`（真实最后一个字的结束，防止末尾"了"被裁）。
- `make_v4.studio_segment` 按区间 trim+concat，音频 12 ms 微淡入淡出；take 到片尾就把尾部淡出缩到 0.06 s。
- 之后跑 `tverify.py`：对每个改过的主持人镜头做 ASR，与台词按拼音比对 miss/extra/gaps；繁体字、阿拉伯数字、原片本身的误读算误报，逐条核实。

## 6. 出片前检查清单

- [ ] `v3/concat.txt` 里主持人镜头来源正确（**模式切换后必查**：EP02 v9 因 `ONLY=` 复用了旧口型段落而交错版本）。
- [ ] 无 `ai:` / `img:v_` / 静态图镜头（`make_v4` 会拒绝渲染）。
- [ ] 主持人镜头声画同步（段音频 = 视频长度：`apad` + `-t`；混音 `aresample=48000:async=1:first_pts=0`）。
- [ ] 响度：整片 -16 LUFS，各段 -19~-21 dB 平均；纯音乐段不发闷。
- [ ] 封面首帧 + attached_pic；结尾卡居中且停留；BGM 自然收尾。
- [ ] 卡顿收紧 + tverify 通过；剩余瑕疵列给用户。
- [ ] 章节时间戳用 `chap.py` 从实际 concat 计算（每次重渲都会变）。

## 7. 常见坑（详见 `references/pitfalls.md`）

- 输入字典里的 `#` 注释吞掉了 duration/aspect/resolution 键 → 永远 5 s。
- `loudnorm` 输出 192 kHz → 之后一定 `aresample=48000` 再 concat。
- 长段静音原片 + 床底音乐会被混没 → 把音乐直接放进该段自身音频。
- 帧率 60/30→25 丢帧会"抖" → `framerate=fps=25` 混帧；不要用 vidstab。
- 封面用 loop 图像输入 concat 会卡死 → 封面做成普通首段。
- py3.11 f-string 里不能写反斜杠。
- 脚本别叫 `select.py`（遮蔽标准库）。
- Wikimedia/部分站点对 制作机 返回 429/403 → 沙盒下载再 scp。
- 克隆 2.0 必须把 `model_type:4` 放进 `additions` JSON 字符串里，否则静默退回 1.0。

## 参考

- `references/pipeline.md` — 各环节命令、参数、ffmpeg 滤镜、混音参数。
- `references/script-format.md` — 剧本/镜头 JSON 格式与 `pic` 语法。
- `references/feedback-log.md` — 两期用户反馈原话 → 规则（为什么这样做）。
- `references/publish.md` — B 站标题/简介/标签模板与 AI 声明。
- `scripts/README.md` — 每个脚本的用途和调用方式（来自 EP02 实际跑通的版本，路径/ID 需按新一期调整）。
