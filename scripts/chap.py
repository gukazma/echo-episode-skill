import json, subprocess
sc = json.load(open("script_v4.json", encoding="utf-8")); SH = sc["shots"]
segs = [l.split("'")[1] for l in open("v3/concat.txt", encoding="utf-8") if l.strip()]
def pr(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
t = pr(segs[0]); cur = None
for s, p in zip(SH, segs[1:]):
    if s["sec"] != cur: print(f"{int(t//60):02d}:{int(t%60):02d} {s['sec']} | {s['line'][:30]}"); cur = s["sec"]
    t += pr(p)
print("total", round(t, 1))
