"""Chapter timestamps for the publish description.
python chap.py [script.json] [concat.txt]   (default: script_ep04.json v1/concat.txt; first concat entry = cover)"""
import json, subprocess, sys
js = sys.argv[1] if len(sys.argv) > 1 else "script_ep04.json"
cc = sys.argv[2] if len(sys.argv) > 2 else "v1/concat.txt"
SH = json.load(open(js, encoding="utf-8"))["shots"]
segs = [l.split("'")[1] for l in open(cc, encoding="utf-8") if l.strip()]
def pr(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
t = pr(segs[0]); cur = None
for s, p in zip(SH, segs[1:]):
    if s["sec"] != cur: print(f"{int(t//60):02d}:{int(t%60):02d} {s['sec']}"); cur = s["sec"]
    t += pr(p)
print("total", round(t, 1))
