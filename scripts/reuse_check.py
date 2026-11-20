"""which footage windows overlap / wrap (= visible repeats) in the current plan"""
import sys, collections
sys.argv = ["x", "none"]
import make_episode as m
m.plan_windows()
by = collections.defaultdict(list)
for sid, (src, a, d) in m.WIN.items():
    by[src.stem].append((a, a + d, sid))
rows = []
for k, ws in by.items():
    ws.sort()
    rep = 0.0
    for i in range(len(ws)):
        for j in range(i):
            rep += max(0.0, min(ws[i][1], ws[j][1]) - max(ws[i][0], ws[j][0]))
    lo, hi = m.USE.get(k, (0, 0))
    rows.append((rep, k, len(ws), round(sum(b - a for a, b, _ in ws), 1), (lo, hi), [s for *_, s in ws]))
for r in sorted(rows, reverse=True):
    if r[0] > 0.5 or r[2] >= 4:
        print(f"{r[1]:20s} shots={r[2]:2d} used={r[3]:6.1f}s range={r[4]} REPEAT={r[0]:.1f}s ids={r[5]}")
