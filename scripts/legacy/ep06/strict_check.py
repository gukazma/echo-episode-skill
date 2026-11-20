"""Strict line check of Seedance takes: Whisper word-level (no previous-text conditioning) vs script, compared by toneless pinyin.
Any missing / extra / different-sound syllable fails (homophones pass).  python strict_check.py [--accepted] [keys...] -> studio/strict.json"""
import difflib, json, re, sys
from pathlib import Path
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin, pinyin, Style
st = Path("studio")
sc = {s["id"]: s for s in json.loads(Path("script_ep06.json").read_text(encoding="utf-8"))["shots"]}
keys = [k for v in json.loads((st / "accepted.json").read_text()).values() for k in v] if "--accepted" in sys.argv else []
keys += [a for a in sys.argv[1:] if not a.startswith("--")]
SAY = {"C罗": "西罗"}
D = "零一二三四五六七八九"
def cn(n):  # Whisper writes numbers as digits: 11 -> 十一, 23 -> 二十三, 2003 -> 二零零三
    n = int(n)
    if n >= 1000: return "".join(D[int(c)] for c in str(n))
    if n >= 100: return D[n // 100] + "百" + (("零" if n % 100 < 10 else "") + cn(n % 100) if n % 100 else "")
    if n >= 10: return ("" if n < 20 else D[n // 10]) + "十" + (D[n % 10] if n % 10 else "")
    return D[n]
def clean(t):
    for k, v in SAY.items(): t = t.replace(k, v)
    t = re.sub(r"\d+", lambda mm: cn(mm.group()), t)
    return re.sub(r"[^\u4e00-\u9fff]", "", t)
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
res = json.loads((st / "strict.json").read_text(encoding="utf-8")) if (st / "strict.json").exists() else {}
for k in keys:
    sid = k.split("_t")[0]
    segs, _ = m.transcribe(str(st / "clips" / f"{k}.mp4"), language="zh", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    ws = [w for s in segs for w in s.words]
    heard = clean("".join(w.word for w in ws))
    line = clean(sc[sid]["line"])
    if ws and not lazy_pinyin(heard)[:2] == lazy_pinyin(line)[:2] and ws[0].start > 1.5:  # Whisper sometimes drops the opening: re-hear it alone
        hs, _ = m.transcribe(str(st / "clips" / f"{k}.mp4"), language="zh", word_timestamps=True, beam_size=5, condition_on_previous_text=False,
                             clip_timestamps=[0, ws[0].start])
        head = [w for s_ in hs for w in s_.words]
        ws = head + ws; heard = clean("".join(w.word for w in ws))
    hetero = lambda t: [set(pinyin(c, style=Style.NORMAL, heteronym=True)[0]) for c in t]  # per character: phrase pinyin hides readings (于斯/于思)  # any shared reading = same sound (着/著, 地/的, 将/降)
    A, B = lazy_pinyin(line), lazy_pinyin(heard)
    HA, HB = hetero(line), hetero(heard)
    errs = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op == "equal": continue
        if op == "replace" and a2 - a1 == b2 - b1 and all(HA[a1 + j] & HB[b1 + j] for j in range(a2 - a1)): continue
        errs.append(f"{op}: 「{line[a1:a2]}」→「{heard[b1:b2]}」")
    low = [f"{w.word.strip()}({w.probability:.2f})" for w in ws if w.probability < 0.5]
    res[k] = {"ok": not errs, "errs": errs, "heard": heard, "low": low}
    print(("OK  " if not errs else "FAIL"), k, sc[sid]["line"], "||", heard, " ".join(errs), ("LOW " + " ".join(low)) if low else "", flush=True)
(st / "strict.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("STRICT_DONE", sum(1 for k in keys if not res[k]["ok"]), "fail of", len(keys))
