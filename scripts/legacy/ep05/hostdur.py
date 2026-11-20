import math, make_ep05 as m
tot = 0; n15 = []
rows = []
for s in m.SHOTS:
    if s["pic"].startswith("img:st_"):
        d = m.probe(m.voice(s)); g = math.ceil(1.08 * d + 0.8); tot += g
        rows.append((s["id"], s["who"], round(d, 1), g))
        if g > 15: n15.append(s["id"])
for r in rows: print(*r)
print("HOSTS", len(rows), "gen_seconds", tot, "over15", n15)
