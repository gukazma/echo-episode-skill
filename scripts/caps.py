"""YouTube captions (manual or auto) for interview/archive sources -> footage/caps/<key>.<lang>.vtt (no GPU ASR on 114)."""
import subprocess, sys
from pathlib import Path
ep = Path(__file__).resolve().parent; out = ep / "footage" / "caps"; out.mkdir(parents=True, exist_ok=True)
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    p = line.split()
    if len(p) < 2 or line.startswith("#"): continue
    k, vid = p[0], p[1]
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "--skip-download", "--write-subs", "--write-auto-subs",
                        "--sub-langs", __import__("os").environ.get("SUBL", "en,es,en-orig,es-orig"), "--sub-format", "vtt", "-o", str(out / k), f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    got = sorted(x.name for x in out.glob(f"{k}.*.vtt"))
    print(k, got or ("NONE " + r.stderr[-200:]), flush=True)
    __import__("time").sleep(20)
print("CAPS_DONE")
