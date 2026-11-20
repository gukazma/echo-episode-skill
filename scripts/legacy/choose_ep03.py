"""EP03: per host shot pick the cleanest Seedance take (split shots: best take per part) by strict QC -> studio/accepted.json + choose.txt
python choose_ep03.py [plan=studio/plan_all.json]"""
import itertools, json, re, sys
from pathlib import Path
st = Path("studio")
plan = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else "studio/plan_all.json").read_text(encoding="utf-8"))
qc = json.loads((st / "qc.json").read_text(encoding="utf-8")); q2 = json.loads((st / "qc2.json").read_text(encoding="utf-8"))
REJECT = set(json.loads((st / "reject.json").read_text())) if (st / "reject.json").exists() else set()  # takes failed by eye (posture, seat, face)
def pen(k):
    if k in REJECT or k not in q2 or k not in qc: return 99
    f = " ".join(q2[k]["flags"]); p = 0.0
    if "REP" in f: p += 10 + 2 * len(q2[k]["extra"])
    if "SYL" in f: p += 3
    if "GAP" in f: p += 3
    mm = re.search(r"SLOW([\d.]+)", f)
    if mm: p += 6 * (float(mm.group(1)) - 1.45) + 2
    p += 8 * (1 - qc[k]["sim"]) + 2 * len(q2[k]["miss"])
    return round(p, 2)
parts = {}
for s in plan["shots"]: parts.setdefault(s["shot"], []).append(s["id"])
acc, rep, bad = {}, [], []
for sid, ps in parts.items():
    opts = [[p.stem for p in sorted((st / "clips").glob(f"{u}_t*.mp4"))] for u in ps]
    if not all(opts): rep.append(f"{sid}: no takes yet"); bad.append(sid); continue
    scored = sorted((sum(pen(k) for k in c), list(c)) for c in itertools.product(*opts))
    acc[sid] = scored[0][1]
    rep.append(f"{sid} -> {'+'.join(scored[0][1])} pen {scored[0][0]:.1f} | " + "  ".join(f"{'+'.join(c)}:{p:.1f}" for p, c in scored[1:4]))
    for k in scored[0][1]:
        if k in REJECT or q2.get(k, {}).get("flags") or qc.get(k, {}).get("sim", 0) < 0.9:
            rep.append(f"   flagged {k}: {q2.get(k, {}).get('flags')} sim {qc.get(k, {}).get('sim')} heard {q2.get(k, {}).get('heard', '')[:40]}"); bad.append(sid)
(st / "accepted.json").write_text(json.dumps(acc, indent=1)); (st / "choose.txt").write_text("\n".join(rep), encoding="utf-8")
print("\n".join(rep)); print("needs retake:", sorted(set(bad)))
