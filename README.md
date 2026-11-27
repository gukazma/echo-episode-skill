# echo-episode-skill

《回声号》式双主持人历史/人物故事长视频的 Claude Code skill：老渡 + 小柚两位 AI 主持（Seedance 生成、自带原声），影视原片/纪录片/新闻实拍素材，克隆配音旁白，按情绪曲线配乐，从选题、查证、剧本、分镜样片、主持人镜头生产与逐字语音 QC、停顿处理、混音、封面、局域网交付到 B 站发布文案的全流程。

由九期实战沉淀（EP01 马斯克 / EP02 诸葛亮 / EP03 文在寅与卢武铉 / EP04 山口百惠与三浦友和 / EP05 黄仁勋 / EP06 C罗 / EP07 1972 安第斯空难 / EP08 罗尼·洛克伍德 / EP09 霍去病），每条规则都来自一次被打回的版本，原话与原因见 `references/feedback-log.md`。

## 安装

```bash
git clone https://github.com/gukazma/echo-episode-skill.git ~/.claude/skills/echo-episode
```
（或放进项目的 `.claude/skills/echo-episode/`）

## 内容

- `SKILL.md` — 流程与确认关口、内容/画面/声音硬规则、Seedance 主持人要点、卡顿根因与处理、出片前检查清单
- `references/` — 管线参数、剧本格式、用户反馈 → 规则、踩坑清单、发布模板
- `scripts/` — EP07 版整套工具（渲染器、Seedance 链式生产、四道语音 QC、成片检查、封面、章节、局域网交付页），见 `scripts/README.md`
- `examples/ep07/` — 一期完整剧本与史实核查

## 依赖与配置

- Windows 渲染机：Python 3.11 venv、ffmpeg 8、faster-whisper（CPU int8 即可）、pypinyin、numpy、Pillow；OpenMontage 风格的工具目录（`tools/video/seedance_ark.py` 等，路径用环境变量 `OPENMONTAGE` 指定，默认 `D:\OpenMontage`）。
- 火山引擎方舟（Seedance / Seedream）与豆包语音（克隆 2.0）账号；密钥只放 `<OPENMONTAGE>\.env`，仓库中不含任何密钥、内网地址或音色 ID。
- 素材与配乐版权自行负责；成片含 AI 生成内容，发布时请勾选平台的 AI 声明。
