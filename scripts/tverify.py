"""Verify tightened host segments: ASR of each final segment vs script line (missing / extra syllables, remaining gaps)."""
import json, re, difflib
from pathlib import Path
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
SH = json.loads(Path("script_v4.json").read_text(encoding="utf-8"))["shots"]
T = json.loads(Path("studio/tighten.json").read_text(encoding="utf-8"))
ACC = json.loads(Path("studio/accepted.json").read_text(encoding="utf-8"))
m = WhisperModel("medium", device="cuda", compute_type="float16")
clean = lambda t: re.sub(r"[^一-鿿0-9]", "", t)
for i, s in enumerate(SH, 1):
    if s["id"] not in ACC: continue
    takes = ACC[s["id"]]
    if not any(k in T for k in takes): continue
    p = Path("v3/seg") / (f"{i:03d}.mkv" if len(takes) > 1 else f"{i:03d}_s0.mkv")
    ws = [w for seg in m.transcribe(str(p), language="zh", vad_filter=False, word_timestamps=True, condition_on_previous_text=False, beam_size=5)[0] for w in seg.words]
    heard = "".join(w.word for w in ws)
    A, B = lazy_pinyin(clean(s["line"])), lazy_pinyin(clean(heard))
    ops = difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes()
    miss = [" ".join(A[a:b]) for o, a, b, c, d in ops if o in ("delete", "replace")]
    extra = [" ".join(B[c:d]) for o, a, b, c, d in ops if o in ("insert", "replace")]
    gaps = [round(w2.start - w1.end, 2) for w1, w2 in zip(ws, ws[1:]) if w2.start - w1.end > 0.6]
    print(f"{s['id']} {'OK ' if not miss and not extra else 'CHK'} miss={miss} extra={extra} gaps={gaps} | {heard}", flush=True)
print("VERIFY_DONE")
