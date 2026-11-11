# echo-episode-skill

《回声号》式双主持人历史/人物科普长视频的 Claude Code skill：老渡 + 小柚两位 AI 主持（Seedance），影视原片/实拍素材，克隆配音，古风 BGM，从选题、剧本、分镜样片、主持人镜头、结巴 QC 与停顿收紧、混音、封面到 B 站发布文案的全流程。

由两期实战沉淀：EP01《龙不会老》、EP02《一诺千年——真实的诸葛亮》。

## 安装

```bash
git clone https://github.com/gukazma/echo-episode-skill.git ~/.claude/skills/echo-episode
```
（或放进项目的 `.claude/skills/echo-episode/`）

## 内容

- `SKILL.md` — 流程、确认关口、硬规则、QC、出片前检查清单
- `references/` — 管线参数、剧本格式、用户反馈→规则、踩坑清单、发布模板
- `scripts/` — EP02 实际跑通的工具（渲染器、Seedance 链式生成、结巴 QC、停顿收紧、ASR 复核、封面、章节时间戳），见 `scripts/README.md`

密钥只从 `D:\OpenMontage\.env` 读取（`ARK_API_KEY`、`VOLC_TTS_APIKEY`），仓库中不含任何密钥；克隆音色 ID 放在每期目录的 `voice_ids.json`。
