"""Stack studio/review/<take>.jpg strips (10 per sheet) -> qc/rev_N.jpg, with the take name drawn on each strip."""
import subprocess, sys
from pathlib import Path
keys = sys.argv[1:]
Path("qc").mkdir(exist_ok=True)
FONT = "C\\:/Windows/Fonts/msyh.ttc"
for n in range(0, len(keys), 10):
    ks = keys[n:n + 10]; ins = []
    for k in ks: ins += ["-i", f"studio/review/{k}.jpg"]
    fc = ";".join(f"[{i}:v]scale=1920:-2,drawtext=fontfile='{FONT}':text='{k}':fontsize=40:fontcolor=yellow:box=1:boxcolor=black@0.6:x=10:y=10[s{i}]" for i, k in enumerate(ks))
    fc += ";" + "".join(f"[s{i}]" for i in range(len(ks))) + f"vstack=inputs={len(ks)}[o]" if len(ks) > 1 else fc.replace("[s0]", "[o]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fc, "-map", "[o]", "-q:v", "4", f"qc/rev_{n // 10}.jpg"], check=True)
    print("sheet", n // 10, ks, flush=True)
