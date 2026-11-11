# 踩坑清单（两期实际遇到）

## 运维 / 远程
- 制作机 默认 shell 是 cmd：串联用 `&`；`for` 循环经 ssh 容易坏 → 写 Python 驱动脚本。
- GBK 输出乱码：`chcp 65001`、`PYTHONIOENCODING=utf-8`；读 json 显式 `encoding="utf-8"`。
- 隐藏启动：`launch.ps1`（Win32_Process Create）+ 完整路径；绝不 schtasks /it、不开可见窗口。
- 等待循环别信旧日志：日志用 `>` 覆盖、完成标记每轮新写；先确认进程（`tasklist | findstr ffmpeg python`）。
- Wikimedia 429 / Pixabay 403 / incompetech 不通 → 沙盒（有代理）下载再 scp。
- 脚本名别用 `select.py`；py3.11 f-string 内不能有反斜杠。

## Seedance / Ark
- 输入 dict 里的 `#` 注释吞键 → 总是 5 s。
- `.env` 的 `ARK_SEEDANCE_MODEL` 会覆盖 variant → 显式传 model。
- 首帧模式要 `aspect_ratio` adaptive；seedance_ark.py 设置参考音频时 `duration` 变量被遮蔽（本地已修，上游 bug）。
- 片长 > 台词需要 → 重复说词填时间；时长 `ceil(1.15·tts+1)` + "说完就闭嘴"，干净率 ~50% → ~85%。
- Seedance 读音偏差：塞尔南→"林"、诸葛亮偶尔"朱可亮"；用 PRON 提示、改写，或多拍几条挑。
- 链式 4–5 跳后漂移、越推越近；从 plate 重新起链。
- 含人脸参考的 Seedream 图被拦；国旗特写被拦。
- 工具返回的 cost 是 USD。

## 口型 / 同步
- LatentSync 会保留底片原有嘴动，底片需是静音 plate；3/4 侧脸弱；用户嫌机器感 → 不用。
- 声画漂移（到 −3 s）：段音频 `apad` + `-t` 对齐视频；混音 `aresample=48000:async=1:first_pts=0`；用 probe 的实际段长排时间线。
- `ONLY=` 复用旧段会把旧方案（口型段）混进成片 → 主持人段永远重建；切换方案后把旧段移走并检查 concat.txt。

## 音频
- loudnorm 输出 192 kHz → 后接 `aresample=48000`。
- 静音原片 + 床底音乐被混没 → 音乐放进该段自身音轨。
- 停顿收紧阈值过松会剪掉轻声字（"也"）；过严（词尾保护覆盖所有词）会让重复字剪切失效 → 重复字剪切不受保护约束，保护只对"确有声音"的词尾生效。
- take 恰好在最后一个字结束（"呀"）时 0.2 s 淡出会吞字 → 淡出缩到 0.06 s。
- whisper 用 initial_prompt 会丢开头；whisper 会把停顿算进拉长的词里（"的人[2.10-3.64]"）→ 停顿检测用声学能量，不只靠词时间戳。

## 画面
- zoompan 推拉静态图会抖（且用户不要静态图）。
- 60/30 fps → 25 fps 丢帧显得抖 → framerate 混帧；vidstab 让运动镜头更糟。
- 网络视频的台标/烧录字幕：cropdetect + 内缩；片头演职员表镜头要换掉。
- 封面用 `-loop 1` 图像输入参与 concat 会卡死 → 做成普通 2.5 s 首段。
- 结尾卡窗口不能被时间窗 clamp，否则从错误帧开始。
