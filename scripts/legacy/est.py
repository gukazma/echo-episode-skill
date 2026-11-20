import json, subprocess, collections, sys
sys.argv = ["x", "none"]
import make_v4 as m
def pr(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],capture_output=True,text=True)
    return float(r.stdout.strip() or 0)
d = collections.OrderedDict(); t = 0
for s in m.SHOTS:
    p = s["pic"]
    if p.startswith("mont:"):
        M = m.MONT[p[5:]]; x = sum(b - a for _, a, b, _ in M["pieces"]) - M["xfade"] * (len(M["pieces"]) - 1)
    elif p.startswith("clip:"):
        e, a, b = p.split(":")[1:4]; x = float(b) - float(a)
    elif s["line"] and s["who"] != "无":
        x = pr(m.tts_path(s)) + 0.25 + s.get("pad", 0.45)
    else:
        x = 6.0 if s["line"] else 3.5
    d.setdefault(s["sec"], [0, t]); d[s["sec"]][0] += x; t += x
for k, (x, st) in d.items(): print(f"{st/60:5.1f}m {x:6.1f}s {k}")
print("total", round(t, 1), f"{int(t//60)}:{t%60:04.1f}")
