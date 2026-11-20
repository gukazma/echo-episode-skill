"""Stutter / 卡顿 scan of every spoken line as it sits in the film: TTS narration (v1/tts) + host segments (v1/seg).
flags: REP (extra/doubled syllables vs script), MISS, GAP (mid-line silence > 0.6 s beyond sentence punctuation), CUT (tighten splices)
-> prints film time mm:ss for each flagged line.  python stutterscan.py"""
import json, re, difflib, subprocess, sys
from pathlib import Path
import numpy as np
sys.argv = ["x", "none"]
import make_ep03 as m
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
ep = Path(".").resolve()
segs = [l.split("'")[1] for l in (ep / "v1" / "concat.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
pr = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
t = pr(segs[0]); start = {}
for s, p in zip(m.SHOTS, segs[1:]):
    start[s["id"]] = t; t += pr(p)
T = m.TIGHT  # what the render actually used (TIGHTEN=0 -> no host splices)
model = WhisperModel("medium", device="cuda", compute_type="float16")
clean = lambda x: re.sub(r"[^一-鿿0-9]", "", x)
mmss = lambda x: f"{int(x // 60)}:{x % 60:04.1f}"
nflag = 0
for i, s in enumerate(m.SHOTS, 1):
    if not s["line"] or s["who"] == "无" or s["pic"].startswith("fc:"):
        continue
    host = s["id"] in m.ACC
    src = Path(segs[i]) if host else m.voice(s)
    ws = [w for seg in model.transcribe(str(src), language="zh", vad_filter=False, word_timestamps=True, condition_on_previous_text=False, beam_size=5,
                                         initial_prompt="以下是普通话句子。")[0] for w in seg.words]
    heard = "".join(w.word for w in ws)
    A, B = lazy_pinyin(clean(m.say_text(s["line"]))), lazy_pinyin(clean(heard))
    ops = difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes()
    extra = [" ".join(B[c:d]) for o, a, b, c, d in ops if o == "insert"]
    miss = [" ".join(A[a:b]) for o, a, b, c, d in ops if o == "delete"]
    dup = [w2.word for w1, w2 in zip(ws, ws[1:]) if w1.word.strip() == w2.word.strip() and len(w1.word.strip()) == 1 and w1.word.strip() * 2 not in s["line"]]
    npunct = len(re.findall(r"[，。？！；：、…—]", s["line"].rstrip("，。？！…")))
    gaps = [round(w2.start - w1.end, 2) for w1, w2 in zip(ws, ws[1:]) if w2.start - w1.end > 0.6]
    flags = []
    if extra or dup: flags.append(f"REP{extra + dup}")
    if len(miss) > 0 and sum(len(x.split()) for x in miss) >= 2: flags.append(f"MISS{miss}")
    if len(gaps) > npunct or any(g > 1.2 for g in gaps): flags.append(f"GAP{gaps}")
    cuts = sum(len(T.get(k, [])) for k in m.ACC.get(s["id"], []))
    if cuts: flags.append(f"CUT{cuts}")
    if host and len(m.ACC[s["id"]]) > 1: flags.append("JOIN")
    if flags:
        nflag += 1
        print(f"{mmss(start[s['id']])} {s['id']} {'HOST' if host else 'VO  '} {s['who']} {' '.join(flags)} | {s['line'][:30]} || {heard[:40]}", flush=True)
print("SCAN_DONE flagged", nflag)
