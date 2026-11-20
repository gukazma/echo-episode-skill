"""contact sheets per footage file -> sheets/<key>.jpg (n frames with timestamps; long files get more frames, split in pages of 20)
python sheets.py [key ...]"""
import subprocess, sys
from pathlib import Path
ep = Path(__file__).resolve().parent
(ep / "sheets").mkdir(exist_ok=True)


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


keys = sys.argv[1:] or [f.stem for f in sorted((ep / "footage").glob("*.mp4"))]
for k in keys:
    f = ep / "footage" / f"{k}.mp4"
    if not f.exists():
        continue
    d = probe(f)
    if d <= 0:
        continue
    n = 20 if d < 600 else 40 if d < 3600 else 60
    step = d / (n + 1)
    ts = [step * (j + 1) for j in range(n)]
    for page in range(0, n, 20):
        o = ep / "sheets" / f"{k}_{page // 20}.jpg"
        if o.exists():
            continue
        tt = ts[page:page + 20]
        ins = []
        for t in tt:
            ins += ["-ss", f"{t:.1f}", "-i", str(f)]
        lab = ";".join(f"[{j}:v]scale=384:216:force_original_aspect_ratio=decrease,pad=384:216:(ow-iw)/2:(oh-ih)/2,setsar=1,"
                       f"drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{t:.0f}s':fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.6:x=4:y=4[p{j}]" for j, t in enumerate(tt))
        lay = "|".join(f"{(j % 5) * 384}_{(j // 5) * 216}" for j in range(len(tt)))
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", lab + ";" + "".join(f"[p{j}]" for j in range(len(tt))) + f"xstack=inputs={len(tt)}:layout={lay}",
                            "-frames:v", "1", "-q:v", "5", str(o)], capture_output=True, text=True)
        print("sheet", o.name, round(d), "ERR " + r.stderr[-200:] if r.returncode else "", flush=True)
print("SHEETS_DONE", flush=True)
