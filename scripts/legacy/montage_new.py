import subprocess, sys
from pathlib import Path
keys = sys.argv[1:]
ins, fl = [], []
for j, k in enumerate(keys):
    ins += ["-i", f"sheets/{k}.jpg"]
    fl.append(f"[{j}:v]scale=960:-2,pad=960:420:0:0,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{k}':fontsize=30:fontcolor=red:box=1:boxcolor=white@0.8:x=6:y=390[p{j}]")
n = len(keys)
lay = "|".join(f"{(j % 2) * 960}_{(j // 2) * 420}" for j in range(n))
subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl) + ";" + "".join(f"[p{j}]" for j in range(n)) + f"xstack=inputs={n}:layout={lay}:fill=black", "-frames:v", "1", "-q:v", "5", "qc/new_sheets.jpg"], check=True)
print("MONTAGE_OK")
