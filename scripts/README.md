# scripts（EP07 版整套工具）

所有脚本放在每期目录（如 `D:\OpenMontage\output\echo_ep08\`）里运行，读同目录的 `script.json`；Windows 渲染机上的 Python 3.11 venv（ffmpeg 8、faster-whisper、pypinyin、numpy、Pillow、python-dotenv、requests）。密钥只从 `<OPENMONTAGE>\.env` 读（`ARK_API_KEY`、`VOLC_TTS_APIKEY`），克隆音色 ID 放每期目录的 `voice_ids.json`（不进仓库）。渲染机上一律隐藏启动：`powershell -NoProfile -ExecutionPolicy Bypass -File launch.ps1 run_xxx.cmd`（`.cmd` 含中文必须 CRLF）。

| 阶段 | 脚本 | 用途 |
|---|---|---|
| 剧本 | `../examples/ep07/script.py` | 剧本 DSL（`shot/F/O/A/dub/breath/bgm/sec`）→ `script.json`；复制到新一期改写 |
| 素材 | `dl.py` `caps.py` `sheets.py` `strip.py` | 按清单下载片段（≤720p）/ 抓 YouTube 字幕 / 每个素材出联系表 / 指定区间的密集帧条 |
| 配乐 | `prep_bgm.py` | m4a → wav |
| 渲染 | `make_episode.py tts\|wins\|video` | TTS（克隆 2.0 + 请求式语气）、素材窗口规划（不重复同一秒）、原声 `fc:`/`fa:`、国语配音 `fd:`、主持人镜头（停顿快放 + 25/24 conform）、留白、numpy 人声轨 + 固定增益混音、字幕、水印、封面首帧。`ONLY=id,id` 只重渲指定镜头；`OUT=文件名` |
| 主持人 | `studio_plan.py <name> <ids>` → `studio_produce.py studio\plan_<name>.json fast 720p` | Seedance 提示词（本期布景/服装/表演/读音表在文件开头"EDIT PER EPISODE"块里改）、链式生成（上一条末帧接续） |
| 语音 QC | `qcall.py`（= `studio_qc` + `qc2` + `strict_check` + `takecheck` + `choose`） | 相似度/语速、结巴、逐字拼音、分块重听 + 帧差（镜头内跳切）→ 每镜选最干净的 take → `studio/accepted.json`，打印 needs retake |
| 成片检查 | `voicecmp.py v1\voice.wav 成片.mp4`、`freezescan.py`、`audiocheck.py 成片.mp4`、`deepscan.py host`、`shotsheet.py 成片.mp4`、`segtest.py` | 断音 / 冻结与长停顿 / 爆音削波与音画延迟 / 主持人逐块重听 / 每镜一帧联系表 / 渲染参数回归 |
| 辅助 | `durs.py` `holescan.py` `takestrip.py` `specat.py` `reuse_check.py` `cost_est.py` | 台词时长、停顿、take 帧条、分阶段频谱、素材重复检查、费用估算 |
| 发布 | `chap.py script.json v1/concat.txt`、`covers2.py covers_cfg/epNN.json`、`watermark.py` | 章节时间戳、四比例封面、"老渡 · 小柚"水印 |
| 交付 | `delivery/lanview_server.py` + `run.vbs` | 局域网视频页（手机 Safari，按 项目→作品→版本，HTTP Range 边下边播）；`--list` 打印分类 |

`legacy/` 保留 EP02–EP06 的旧版工具（make_v4、make_ep03、stutterscan、tighten、verify_orig、ep04–ep06 目录等），SKILL.md 历史条目里提到的脚本都在这里。

交付前的硬指标：voicecmp dropouts = 0；audiocheck lag = 0 ms；freezescan 无冻结、停顿 ≤ ~1.2 s；deepscan 无真实漏字/重复；整片 -16 LUFS、峰值 ≤ -1 dBFS（`astats`）；四个比例封面放在成片旁边。
