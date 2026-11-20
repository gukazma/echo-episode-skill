"""download footage/bgm listed in a list file: lines 'key id [start-end]' (bgm_* -> bgm_src audio) -> footage/<key>.mp4
11-13 user: save proxy traffic -> <=720p, optional section download (e.g. 1800-1900 seconds), NO_PROXY for domestic hosts."""
import os, subprocess, sys
DOMESTIC = ",.volces.com,.volcengine.com,.bytedance.com,.bytedanceapi.com,.byteimg.com,.bilibili.com,.bilivideo.com,.hdslb.com,.qq.com,.aliyuncs.com,.baidu.com"
for _k in ("NO_PROXY", "no_proxy"):
    os.environ[_k] = (os.environ.get(_k, "") + DOMESTIC).lstrip(",")
from pathlib import Path
ep = Path(__file__).resolve().parent
lst = Path(sys.argv[1]).read_text(encoding="utf-8")
for line in lst.splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split(); k, vid = parts[0], " ".join(p for p in parts[1:] if not (p[:1].isdigit() and "-" in p and p.replace('-', '').replace('.', '').isdigit()))
    sect = next((p for p in parts[1:] if p[:1].isdigit() and "-" in p and p.replace('-', '').replace('.', '').isdigit()), None)
    audio = k.startswith("bgm_")
    sub = "bgm_src" if audio else "footage"
    (ep / sub).mkdir(exist_ok=True)
    out = ep / sub / (f"{k}.m4a" if audio else f"{k}.mp4")
    if out.exists():
        print(k, "exists", flush=True); continue
    fmt = ["-f", "ba[ext=m4a]/ba"] if audio else ["-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/b", "--merge-output-format", "mp4"]
    url = vid if vid.startswith("ytsearch") else f"https://www.youtube.com/watch?v={vid}"
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "--no-playlist", *fmt, *(["--download-sections", "*" + sect] if sect else []), "-o", str(out), url], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(k, vid, "ok" if out.exists() else f"FAIL {r.returncode} {r.stderr[-300:]}", flush=True)
print("DL_DONE", flush=True)
