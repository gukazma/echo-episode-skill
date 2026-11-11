# scripts —— EP02 实际跑通的工具（参考实现）

全部在 制作机 的期目录下运行（`D:\OpenMontage\output\echo_epNN`），解释器 `D:\OpenMontage\.venv\Scripts\python.exe`，通过 `run_xxx.cmd` + `launch.ps1` 隐藏启动。
新一期：复制到新目录，改片名/输出名、`script_vN.py`、`studio_plan.py` 里的 SHOT 表与参考图路径；密钥只从 `.env` 读取。

| 脚本 | 作用 | 用法 |
|---|---|---|
| `launch.ps1` | WMI 隐藏启动同目录下的 .cmd，返回 PID | `powershell -NoProfile -ExecutionPolicy Bypass -File launch.ps1 run_x.cmd` |
| `script_v4.py` | EP02 剧本示例（BGM 表、sec/shot/ins、MONT、PIC 覆盖、致敬卡） | `python script_v4.py` → `script_v4.json` |
| `make_v4.py` | 主渲染器：TTS、各类画面段、主持人段（含停顿收紧）、字幕、BGM 床 + 闪避混音、封面首帧 + attached_pic | `python make_v4.py tts\|video\|all`；环境变量 OUT / ONLY / RANGE / PREVIEW_TTS / TIGHTEN |
| `est.py` | 渲染前按 TTS 估算各段与总时长 | `python est.py` |
| `vtrain.py` | 豆包克隆音色训练（model_type 4） | 改 JOBS 后运行 |
| `studio_plan.py` | 主持人镜头计划：角色/座位/坐姿/音色/表演/运镜/多音字提示，时长与拆句 | `python studio_plan.py <name> <ids...>` → `studio/plan_<name>.json` |
| `studio_produce.py` | Seedance 链式生成（last-frame 连贯，最多 3 并发） | `python studio_produce.py studio/plan_x.json mini 720p` |
| `studio_qc.py` | 基础 QC：语音起止、时长、拼音相似 | → `studio/qc.json` |
| `qc2.py` | 严格结巴 QC：REP/SYL/GAP/SLOW | `python qc2.py --accepted` 或 `<take keys>` |
| `choose_orig.py` | 每个镜头选最干净的 take（拆句选同链组合） | → `studio/accepted.json` |
| `tighten.py` | 停顿收紧 + 重复字删除（声学静音 + 词尾保护） | → `studio/tighten.json`、`tail.json` |
| `tverify.py` | 成片后对改过的主持人段做 ASR 复核 | 看 `CHK` 行逐条核实 |
| `mkcover.py` | 从原片抓帧做 1920×1080 封面（标题区、暖调、暗角） | `python mkcover.py <ep> <sec> <out.jpg> <x0> [flip]` |
| `chap.py` | 从 `v3/concat.txt` 计算章节时间戳（发布简介用） | `python chap.py` |
| `peek.py` | 抽帧拼联系表，快速看画面 | |

典型一轮（成片）：
```
chcp 65001 >nul
cd /d D:\OpenMontage\output\echo_epNN
set PYTHONIOENCODING=utf-8
D:\OpenMontage\.venv\Scripts\python.exe tighten.py > studio\tighten.log 2>&1
set ONLY=__none__
set OUT=EPNN_片名_vK.mp4
D:\OpenMontage\.venv\Scripts\python.exe make_v4.py video > studio\vK.log 2>&1
D:\OpenMontage\.venv\Scripts\python.exe tverify.py > studio\tverify.log 2>&1
echo ALL_DONE >> studio\tverify.log
```
