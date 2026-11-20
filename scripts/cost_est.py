import sys, math
sys.argv = ["x", "none"]
import make_episode as m
host = [s for s in m.SHOTS if s["pic"].startswith("img:st_")]
secs, tts_total = 0, 0.0
by = {"老渡": 0, "小柚": 0}
for s in host:
    t = m.probe(m.tts_path(s)); tts_total += t
    secs += min(30, max(4, math.ceil(1.15 * t + 1))); by[s["who"]] += 1
print("host shots", len(host), by, "tts", round(tts_total, 1), "gen s/pass", secs)
for takes in (1.5, 2, 3):
    print(takes, [round(secs * takes * 21600 * p / 1e6) for p in (70, 77)])
