"""QC every new Seedance take: studio_qc (ASR sim, speech span) -> qc2 (stutter) -> strict_check (word-level pinyin, zero tolerance) -> choose.
Only takes not yet in qc2.json / strict.json are processed (CPU ASR, low priority)."""
import json, subprocess, sys
from pathlib import Path
py = sys.executable; st = Path("studio")
subprocess.run([py, "studio_qc.py", "studio/plan_all.json"])
keys = sorted(p.stem for p in (st / "clips").glob("*_t*.mp4") if p.with_suffix(".json").exists())
done2 = json.loads((st / "qc2.json").read_text(encoding="utf-8")) if (st / "qc2.json").exists() else {}
done3 = json.loads((st / "strict.json").read_text(encoding="utf-8")) if (st / "strict.json").exists() else {}
new2 = [k for k in keys if k not in done2]; new3 = [k for k in keys if k not in done3]
if new2: subprocess.run([py, "qc2.py", *new2])
if new3: subprocess.run([py, "strict_check.py", *new3])
subprocess.run([py, "choose_ep06.py", "studio/plan_all.json"])
print("QCALL_DONE", flush=True)
