import sys, math
sys.argv = ["x", "none"]
import make_ep03 as m
for s in m.SHOTS:
    if s["pic"].startswith("img:st_"):
        t = m.probe(m.tts_path(s))
        print(s["id"], s["who"], s["pic"][4:], f"{t:4.1f}", min(30, max(4, math.ceil(1.15 * t + 1))), s["sec"][:6], s["line"][:34])
