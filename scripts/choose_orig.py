"""Back to Seedance's own picture+voice: per host shot pick the cleanest take (or chain-consistent take set) by strict QC.
-> studio/accepted.json (old one kept as accepted_lipsync.json) + report studio/choose_orig.txt"""
import json, re, shutil
from pathlib import Path
st = Path("studio")
qc = json.loads((st / "qc.json").read_text(encoding="utf-8")); q2 = json.loads((st / "qc2.json").read_text(encoding="utf-8"))
acc = json.loads((st / "accepted_lipsync.json").read_text()) if (st / "accepted_lipsync.json").exists() else json.loads((st / "accepted.json").read_text())
def pen(k):
    if k not in q2 or k not in qc: return 99
    f = " ".join(q2[k]["flags"]); p = 0.0
    if "REP" in f: p += 10 + 2 * len(q2[k]["extra"])
    if "SYL" in f: p += 3
    if "GAP" in f: p += 3
    mm = re.search(r"SLOW([\d.]+)", f)
    if mm: p += 6 * (float(mm.group(1)) - 1.45) + 2
    p += 8 * (1 - qc[k]["sim"]) + 2 * len(q2[k]["miss"])
    return round(p, 2)
COMBOS = {  # chain-consistent take sets for split shots
    "010": [["010_t1"], ["010_t2"], ["010a_t1", "010b_t1"], ["010a_t2", "010b_t2"], ["010a_t2", "010b_t3"]],
    "036": [["036a_t1", "036b_t1"], ["036a_t1", "036b_t2"], ["036a_t2", "036b_t3"], ["036a_t3", "036b_t4"]],
    "083": [["083a_t1", "083b_t1"]],
    "093": [["093a_t1", "093b_t1"], ["093a_t1", "093b_t2"], ["093a_t2", "093b_t3"]],
    "137": [["137_t1"], ["137_t2"], ["137a_t1", "137b_t1"], ["137a_t1", "137b_t2"]],
}
PAIR = [  # 145 + 146 together (146a was generated from the chosen 145b's last frame)
    (["145a_t1", "145b_t1"], ["146a_t1", "146b_t1"]), (["145a_t2", "145b_t2"], ["146a_t2", "146b_t2"]),
    (["145a_t3", "145b_t3"], ["146a_t3", "146b_t3"]), (["145a_t3", "145b_t3"], ["146a_t4", "146b_t4"]),
    (["145a_t3", "145b_t3"], ["146a_t4", "146b_t5"]), (["145a_t3", "145b_t4"], ["146a_t5", "146b_t6"]), (["145a_t3", "145b_t5"], ["146a_t6", "146b_t7"])]
new, rep = {}, []
for sid in acc:
    if sid in ("145", "146"): continue
    cands = COMBOS.get(sid) or [[p.stem] for p in sorted((st / "clips").glob(f"{sid}_t*.mp4"))]
    scored = sorted((sum(pen(k) for k in c), c) for c in cands if all((st / "clips" / f"{k}.mp4").exists() for k in c))
    best = scored[0]; new[sid] = best[1]
    rep.append(f"{sid} -> {'+'.join(best[1])} pen {best[0]:.1f} | " + "  ".join(f"{'+'.join(c)}:{p:.1f}" for p, c in scored[:4]))
ps = sorted((sum(pen(k) for k in a + b), a, b) for a, b in PAIR)
new["145"], new["146"] = ps[0][1], ps[0][2]
rep.append(f"145/146 -> {'+'.join(ps[0][1])} / {'+'.join(ps[0][2])} pen {ps[0][0]:.1f}")
for sid, ks in new.items():
    for k in ks:
        if k in q2 and q2[k]["flags"]: rep.append(f"   still flagged {k}: {q2[k]['flags']} heard {q2[k]['heard'][:30]}")
if not (st / "accepted_lipsync.json").exists(): shutil.copy(st / "accepted.json", st / "accepted_lipsync.json")
(st / "accepted.json").write_text(json.dumps(new, indent=1)); (st / "choose_orig.txt").write_text("\n".join(rep), encoding="utf-8")
clean = sum(1 for ks in new.values() if all(k in q2 and not q2[k]["flags"] for k in ks))
print("\n".join(rep)); print("fully clean shots:", clean, "/", len(new))
