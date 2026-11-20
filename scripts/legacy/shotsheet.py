"""one frame per shot (mid-segment) from the final film -> shotsheet_<n>.jpg (8x5 tiles, label = shot id + time)"""
import json, subprocess, sys
from pathlib import Path
ep = Path(__file__).resolve().parent
film = ep / sys.argv[1]
SH = json.loads((ep / "script_ep03.json").read_text(encoding="utf-8"))["shots"]
segs = [l.split("'")[1] for l in (ep / "v1" / "concat.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
def pr(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
t = pr(segs[0]); marks = []
for s, p in zip(SH, segs[1:]):
    d = pr(p); marks.append((s["id"], t + d / 2)); t += d
(ep / "qc").mkdir(exist_ok=True)
for b in range(0, len(marks), 40):
    chunk = marks[b:b + 40]; ins = []; fl = []
    for j, (sid, tm) in enumerate(chunk):
        ins += ["-ss", f"{tm:.1f}", "-i", str(film)]
        fl.append(f"[{j}:v]scale=320:180,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{sid} {int(tm//60)}m{int(tm%60):02d}':fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6:x=4:y=4[p{j}]")
    n = len(chunk)
    lay = "|".join(f"{(j % 8) * 320}_{(j // 8) * 180}" for j in range(n))
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl) + ";" + "".join(f"[p{j}]" for j in range(n)) + f"xstack=inputs={n}:layout={lay}:fill=black",
                    "-frames:v", "1", "-q:v", "4", str(ep / "qc" / f"shotsheet_{b // 40}.jpg")], check=True)
print("SHEETS", (len(marks) + 39) // 40)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(film), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
print([l for l in r.splitlines() if "I:" in l][-1])
