# 回声号制作管线（EP02 实际跑通的参数）

目录约定（每期 `D:\OpenMontage\output\echo_epNN`）：

```
script_vN.py / .json   剧本（生成 json）
voice_ids.json         {"laodu": "<老渡音色ID>", "xiaoyou": "<小柚音色ID>"}
drama/eps/eNN.mp4      影视原片（94 版三国 e01..e84）
footage/*.mp4          网络实拍
bgm/*.wav              音乐（各段已 loudnorm）
cover/EPNN_cover.jpg   封面
studio/plan_*.json     主持人镜头生产计划
studio/clips/<id>_t<n>.mp4/.json/_last.png   Seedance takes
studio/qc.json qc2.json accepted.json tighten.json tail.json
v3/{pic,tts,seg}/      渲染缓存；v3/concat.txt 最终拼接表
EPNN_标题_vK.mp4        成片
```

## 1. TTS（豆包克隆 2.0）

- POST `https://openspeech.bytedance.com/api/v3/tts/unidirectional`，headers `X-Api-Key`、`X-Api-Resource-Id: seed-icl-2.0`、`X-Api-Request-Id: uuid`。
- `req_params.additions = json.dumps({"model_type": 4, "context_texts": [语气描述]})` —— model_type 必须在 additions 字符串里。
- `speech_rate = 0`（不加速）。克隆音色比预置音色慢约 19%，用 tone 上下文提速提情绪，而不是 rate。
- 多音字：`SAY = {"乐毅": "岳毅", "张郃": "张合", "马谡": "马速", "费祎": "费衣", "刘禅": "刘善", "涿州": "卓州", "剽牛": "飘牛"}` 只替换送 TTS 的文本。
- 训练克隆：POST `/api/v3/tts/voice_clone` `{speaker_id, audio:{data,format:wav}, model_type:4}`（`vtrain.py`）；状态 `/api/v3/tts/get_voice`（2 = 完成）。
- 缓存键 = md5(speaker|resource|m4|rate|ctx|line) → `v3/tts/*.mp3`。

## 2. 主持人镜头（Seedance via `tools/video/seedance_ark.py`）

`studio_plan.py <name> <ids...>` → `studio/plan_<name>.json`：每条 `{id, who, angle(side|cam), duration, refs[], audio_refs[], prompt, line}` + `chains`。
- 定妆参考：老渡 `echo_ep01_final/img/c_laodu.png` + `s_bg_laodu.png`；小柚 `S06x_t3_last.png` + `studio/bg_xiaoyou_v1.png`。
- `SEAT[(who, angle)]` 写死座位/朝向/背景；`POSTURE` 防陷沙发；`VOICE` 写音色；`SHOT[id] = (angle, 表演, 运镜)`；`PRON` 多音字提示；`FORCE_SPLIT`。
- duration = `ceil(1.15·tts + 1)`，上限 MAXA 10.8 s 以上拆分。

`studio_produce.py <plan.json> [mini] [720p]`：链并行（最多 3 个 Ark 任务），链内每条把上一条 API last frame 追加为参考并插入 `【CONTINUITY】`。输入字典：
```python
{"prompt", "model_variant": "mini", "model": MODEL_IDS["mini"], "duration", "aspect_ratio": "16:9", "resolution": "720p",
 "generate_audio": True, "operation": "reference_to_video", "reference_image_paths", "return_last_frame": True,
 "reference_audio_paths", "output_path", "timeout_seconds": 1800, "poll_interval_seconds": 8}
```
（显式写 model，否则 `.env` 的 ARK_SEEDANCE_MODEL 会覆盖 variant；字典里别写 `#` 注释行。）

`studio_qc.py` → `qc.json`（speech 起止、speech_len、tts_len）；`qc2.py --accepted | <keys>` → `qc2.json`（REP/SYL/GAP/SLOW）。
`choose_orig.py`：每个 id 选最干净的 take（拆分句选同链一致的 a/b 组合）→ `accepted.json`。

## 3. 画面

`pic` 语法见 script-format.md。渲染（`make_v4.py`）：
- `d:EP:SEC`：94 版动态片段，`plan_windows` 给每个镜头分配不重叠的时间窗，`DRAMA_VF = crop=iw-40:ih*0.665:20:ih*0.135`（去台标+烧录字幕）。
- `f:FILE:SEC`：网络实拍，`cropdetect=limit=24:round=2:reset=0` 去黑边后再 `FOOT_INNER = crop=iw*0.90:ih*0.76:iw*0.05:ih*0.11`（去角标/字幕），个别源用 `FOOT_OVR` 覆盖。
- `clip:EP:A:B:orig|mute|<bgmkey>`：原片段，4:3 居中 + 模糊铺底；`orig` 保留原声，`<bgmkey>` 把音乐直接作为该段音频。
- `mont:KEY`：蒙太奇（`MONT` 表，pieces `[ep,a,b,now|flash]`，xfade 0.6，flash = 全屏 + 褪色暖调回忆感）。
- 高帧率源：`framerate=fps=25` 混帧，不要 vidstab。
- 字幕：`subs_for` 按标点切句、按字数分配时长；ASS 样式 `Microsoft YaHei 17, Outline 1.2, MarginV 26`。

## 4. 结尾卡 / 封面

- 卡片：`s["card"] = [行1, 行2, 行3]`，`s["hold"] = 18`；冻结帧 + drawtext 居中，窗口不被 clamp。
- 封面：`mkcover.py <ep> <sec> <out.jpg> <x0> [flip]`：从原片抓帧，右侧人物、左侧标题区暗化渐变 + 暖调 + 暗角，楷体/黑体金色标题。成片开头 2.5 s `000_cover.mkv` + 末尾 `-disposition:v:1 attached_pic`。

## 5. 混音

- 每段 BGM：`loudnorm=I=-20:TP=-3`，`volume` 按表，3 s qsin 淡入、3.5 s 淡出，段间重叠 1.5 s。
- 床：`amix ... volume=0.55`；纯原片无人声段（`:mute`）床 +8 dB（2 s 斜坡）。
- 人声轨：`aresample=48000:async=1:first_pts=0`（口型同步关键）。
- 闪避：`sidechaincompress=threshold=0.04:ratio=4:attack=30:release=700`；总线 `loudnorm=I=-16:TP=-1.5:LRA=11`。
- 片尾：`build_after_fit` 让最后一段（送别）倒推，片子结束时音乐自然收尾。

## 6. 渲染控制（环境变量）

- `OUT=EPNN_标题_vK.mp4` 输出名（每次新版本号）。
- `ONLY=__none__`：复用所有非主持人段（主持人段总是从 take 重建，便宜）；`ONLY=049,124` 只重渲这些。
- `RANGE=118-149` 只渲一段（样片检查）。
- `PREVIEW_TTS=1` 分镜样片：TTS 配音 + 生成画面。
- `TIGHTEN=0` 关闭停顿收紧。
- 渲染一次 ≈ 6–8 分钟（制作机，33 分钟成片）。
