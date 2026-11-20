"""EP06 truncation scan: ASR every narrated segment exactly as it sits in the film (v1/seg via concat.txt),
compare with the script by pinyin; flag END (last syllable(s) not heard), MISS (syllables dropped mid-line), REP.
CPU only (114 is the user's PC): faster-whisper medium int8, 4 threads, run at low priority."""
import json, re, difflib, subprocess, sys
from pathlib import Path
sys.argv = ["make_ep06.py"]
import make_ep06 as M
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
work = M.work
segs = [l.split("'")[1] for l in (work / "concat.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
pr = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
ZH = "零一二三四五六七八九"
def norm(x):
    x = re.sub(r"\d", lambda m: ZH[int(m.group())], x)
    return re.sub(r"[^一-鿿]", "", x)
t, nflag, rows = pr(segs[0]), 0, []
import os
ids = set(os.environ.get("IDS", "").split())
for s, p in zip(M.SHOTS, segs[1:]):
    t0 = t; t += pr(p)
    if not s["line"] or s["who"] == "无" or (ids and s["id"] not in ids):
        continue
    wav = work / "scan" / f"{s['id']}.wav"; wav.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    ws = [w for seg in model.transcribe(str(wav), language="zh", vad_filter=False, word_timestamps=True, condition_on_previous_text=False,
                                         beam_size=5)[0] for w in seg.words]
    heard = "".join(w.word for w in ws)
    A, B = lazy_pinyin(norm(M.say_text(s["line"]))), lazy_pinyin(norm(heard))
    ops = difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes()
    miss = [(a, " ".join(A[a:b])) for o, a, b, c, d in ops if o in ("delete", "replace")]
    extra = [" ".join(B[c:d]) for o, a, b, c, d in ops if o == "insert"]
    flags = []
    if miss and miss[-1][0] >= len(A) - 2: flags.append(f"END[{miss[-1][1]}]")
    if [m for m in miss if m[0] < len(A) - 2]: flags.append(f"MISS{[m[1] for m in miss if m[0] < len(A) - 2]}")
    if extra: flags.append(f"REP{extra}")
    last = ws[-1].end if ws else 0
    row = f"{int(t0 // 60)}:{t0 % 60:04.1f} {s['id']} {s['who']} {' '.join(flags) or 'ok'} | ...{s['line']} || {heard} | lastword_end {last:.2f}/{pr(p):.2f}"
    print(row, flush=True)
    nflag += bool(flags)
print("SCAN_DONE flagged", nflag, flush=True)
