"""print TTS duration of every host (img:st_*) line -> cost estimate for Seedance 2.0 fast 720p"""
import sys, math, subprocess
sys.argv = ["x", "none"]
import make_episode as m
def pr(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True); return float(r.stdout.strip() or 0)
tot = 0
for s in m.SHOTS:
    if not s["pic"].startswith("img:st_"): continue
    ref = m.tts_path(s) if s["who"] == "老渡" else m.voice(s)
    td = pr(ref); d = max(4, min(15, math.ceil(td * (1.12 if s["who"] == "老渡" else 1.08) + (1.0 if s["who"] == "老渡" else 0.8))))
    tot += d
    print(s["id"], s["who"], f"{td:.1f}", d, "LONG" if td > 12.5 else "", len(s["line"]))
print("TOTAL", tot, "s/take; list 0.80/s:", round(tot * 0.8), "CNY per take-round")
