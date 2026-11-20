"""Re-transcribe every original-sound span used in the script with whisper medium (large-v3 not installed) -> qc/orig_verify.txt"""
import json, sys
from pathlib import Path
from faster_whisper import WhisperModel
ep = Path(__file__).resolve().parent
S = json.loads((ep / "script_ep04.json").read_text(encoding="utf-8"))["shots"]
m = WhisperModel("medium", device="cuda", compute_type="float16")
out = []
for s in S:
    if not s["pic"].startswith(("fc:", "fa:")) or not s["line"]:
        continue
    x = s["pic"].split(":"); f, a, b = x[1], float(x[2]), float(x[3])
    lang = "zh" if "akai_bl" in f or "akai_zh" in f else "ja"
    segs, _ = m.transcribe(str(ep / f), language=lang, beam_size=5, vad_filter=False, clip_timestamps=[a, b])
    heard = " ".join(z.text.strip() for z in segs if z.start < b and z.end > a)
    out.append(f"{s['id']} {f.split('/')[-1]} {a}-{b}\n  SUB : {s['line']}\n  HEARD: {heard}\n")
(ep / "qc" / "orig_verify.txt").write_text("\n".join(out), encoding="utf-8")
print("VERIFY_DONE")
