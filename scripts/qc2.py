"""Strict stutter QC: python qc2.py <take keys...> | --accepted   -> qc2.json + table
flags: REP (ASR repeats/extra text), SYL (acoustic syllable count > chars*1.12+1), GAP (mid-phrase pause >0.55 s), SLOW (speech > 1.45x TTS)"""
import json, re, subprocess, sys, difflib
from pathlib import Path
import numpy as np
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
st = Path("studio"); qc = json.loads((st / "qc.json").read_text(encoding="utf-8"))
SC = {s["id"]: s for s in json.loads(Path("script_v4.json").read_text(encoding="utf-8"))["shots"]}
plans = {}
for f in sorted(st.glob("plan_*.json"), key=lambda f: f.stat().st_mtime):
    for s in json.loads(f.read_text(encoding="utf-8"))["shots"]:
        s.setdefault("line", SC.get(s["id"], {}).get("line", "")); s.setdefault("who", SC.get(s["id"], {}).get("who", "")); plans[s["id"]] = s
keys = [t for v in json.loads((st / "accepted.json").read_text()).values() for t in v] if "--accepted" in sys.argv else []
keys += [a for a in sys.argv[1:] if not a.startswith("--")]
m = WhisperModel("medium", device="cuda", compute_type="float16")
def pcm(p, a, b):
    raw = subprocess.run(["ffmpeg","-v","error","-ss",f"{a:.2f}","-to",f"{b:.2f}","-i",str(p),"-vn","-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(float)
def syllables(x):
    hop = 160; n = len(x) // hop
    e = np.sqrt((x[:n*hop].reshape(n, hop)**2).mean(1)); e = np.convolve(e, np.ones(5)/5, "same")
    th = max(e.max() * 0.12, 250); pk = 0; last = -99
    for i in range(1, n - 1):
        if e[i] > th and e[i] >= e[i-1] and e[i] > e[i+1] and i - last >= 9:  # >= 90 ms apart
            # require a dip of 25% between peaks
            if last < 0 or e[last:i].min() < 0.75 * min(e[last], e[i]): pk += 1; last = i
    return pk
out = {}
for k in keys:
    sid = k.split("_t")[0]; p = st / "clips" / f"{k}.mp4"; q = qc.get(k); line = plans[sid]["line"]
    if not p.exists() or not q: continue
    a, b = max(0, q["speech"][0] - 0.2), q["speech"][1] + 0.2
    words = [w for s in m.transcribe(str(p), language="zh", vad_filter=False, word_timestamps=True, condition_on_previous_text=False, beam_size=5)[0] for w in s.words]
    heard = "".join(w.word for w in words)
    clean = lambda t: re.sub(r"[^\u4e00-\u9fff0-9]", "", t)
    A, B = lazy_pinyin(clean(line)), lazy_pinyin(clean(heard))
    extra = [" ".join(B[j1:j2]) for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes() if op in ("insert", "replace") and j2 > j1]
    miss = [" ".join(A[i1:i2]) for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes() if op in ("delete", "replace") and i2 > i1]
    nchar = len(clean(line)); syl = syllables(pcm(p, a, b))
    gaps = []
    punct_after = set(i for i, c in enumerate(re.sub(r"[^\u4e00-\u9fff0-9，。！？；：、…]", "", line)) if c in "，。！？；：、…")
    for w1, w2 in zip(words, words[1:]):
        if w2.start - w1.end > 0.55: gaps.append(round(w2.start - w1.end, 2))
    npunct = len(re.findall(r"[，。！？；：、…]+", line.rstrip("。！？…")))
    flags = []
    if extra: flags.append("REP")
    if syl > nchar * 1.12 + 1: flags.append(f"SYL{syl}/{nchar}")
    if len(gaps) > npunct: flags.append(f"GAP{gaps}")
    if q["speech_len"] > 1.45 * max(q["tts_len"], 0.8) and q["tts_len"] > 1.5: flags.append(f"SLOW{q['speech_len']/q['tts_len']:.2f}")
    out[k] = {"flags": flags, "heard": heard, "extra": extra, "miss": miss, "syl": syl, "chars": nchar, "gaps": gaps}
    print(f"{'BAD' if flags else 'ok '} {k:9s} {plans[sid]['who']} {' '.join(flags):40s} | {heard[:46]}", flush=True)
old = json.loads((st / "qc2.json").read_text(encoding="utf-8")) if (st / "qc2.json").exists() else {}
old.update(out); (st / "qc2.json").write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
