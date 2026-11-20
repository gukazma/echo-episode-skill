"""print TTS (tightened) durations of host + dub lines: python durs.py"""
import make_episode as m
for s in m.SHOTS:
    if s["line"] and s["who"] != "无" and (s["pic"].startswith(("img:st_", "fd:"))):
        p = m.tts_path(s)
        d = round(m.probe(m.tts_path(s)), 1) if p.exists() else -1
        extra = ""
        if s["pic"].startswith("fd:"):
            x = s["pic"].split(":"); extra = f" span {float(x[3]) - float(x[2]):.1f} tight {m.probe(m.voice(s)):.1f}"
        print(s["id"], s["who"], d, extra, s["line"][:30], flush=True)
