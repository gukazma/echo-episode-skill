"""QC every Seedance take of plan_all: studio_qc (ASR sim, speech span) then qc2 (strict stutter)."""
import subprocess, sys
from pathlib import Path
py = sys.executable
subprocess.run([py, "studio_qc.py", "studio/plan_all.json"])
keys = sorted(p.stem for p in Path("studio/clips").glob("*_t*.mp4") if not p.stem.endswith("_last"))
subprocess.run([py, "qc2.py", *keys])
