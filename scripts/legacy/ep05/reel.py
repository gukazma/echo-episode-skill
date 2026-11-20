"""Review reel of the accepted raw Seedance host takes (no trim / no ramp), each labelled: No. + shot id + speaker + line -> EP05_主持人原片审片.mp4"""
import json, subprocess
from pathlib import Path
ep = Path(__file__).resolve().parent
acc = json.loads((ep / "studio" / "accepted.json").read_text(encoding="utf-8"))
import sys
ONLY = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
shots = [s for s in json.loads((ep / "script_ep05.json").read_text(encoding="utf-8"))["shots"] if s["id"] in acc and (not ONLY or s["id"] in ONLY)]
wd = ep / "studio" / "reel"; wd.mkdir(exist_ok=True)
FONT = "C\\:/Windows/Fonts/msyh.ttc"
parts = []
for n, s in enumerate(shots, 1):
    for key in acc[s["id"]]:
        src = ep / "studio" / "clips" / f"{key}.mp4"
        t1 = wd / f"t1_{n}.txt"; t1.write_text(f"No.{n}   镜头 {s['id']}   {s['who']}   ({key})", encoding="utf-8")
        line = s["line"]; wrapped = "\n".join(line[i:i + 30] for i in range(0, len(line), 30))
        t2 = wd / f"t2_{n}.txt"; t2.write_text(wrapped, encoding="utf-8")
        f1, f2 = t1.as_posix().replace(":", "\\:"), t2.as_posix().replace(":", "\\:")
        out = wd / f"{n:03d}.mkv"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex",
                        f"[0:v]fps=25,scale=1280:720:flags=lanczos,setsar=1,"
                        f"drawtext=fontfile='{FONT}':textfile='{f1}':fontsize=34:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=10:x=24:y=20,"
                        f"drawtext=fontfile='{FONT}':textfile='{f2}':fontsize=28:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8:x=24:y=h-th-30:line_spacing=8,format=yuv420p[v];"
                        "[0:a]aresample=48000,aformat=channel_layouts=stereo[a]",
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "pcm_s16le", str(out)], check=True)
        parts.append(out)
lst = wd / "list.txt"; lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts), encoding="utf-8")
final = ep / (sys.argv[2] if len(sys.argv) > 2 else "EP05_主持人原片审片.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(final)], check=True)
print("REEL", len(parts), "clips", final.name, flush=True)
