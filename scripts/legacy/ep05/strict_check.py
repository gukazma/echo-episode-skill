"""Strict line check of Seedance takes: Whisper word-level (no previous-text conditioning) vs script, compared by toneless pinyin.
Any missing / extra / different-sound syllable fails (homophones pass).  python strict_check.py [--accepted] [keys...] -> studio/strict.json"""
import difflib, json, re, sys
from pathlib import Path
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin, pinyin, Style
st = Path("studio")
sc = {s["id"]: s for s in json.loads(Path("script_ep05.json").read_text(encoding="utf-8"))["shots"]}
keys = [k for v in json.loads((st / "accepted.json").read_text()).values() for k in v] if "--accepted" in sys.argv else []
keys += [a for a in sys.argv[1:] if not a.startswith("--")]
SAY = {"CUDA": "库达", "GPU": "", "NV1": "", "RIVA": "", "GeForce": "", "DGX": "", "AlexNet": "", "OpenAI": ""}
def clean(t):
    for k, v in SAY.items(): t = t.replace(k, v)
    return re.sub(r"[^\u4e00-\u9fff0-9]", "", t)
m = WhisperModel("medium", device="cuda", compute_type="float16")
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
    hetero = lambda t: [set(x) for x in pinyin(t, style=Style.NORMAL, heteronym=True)]  # any shared reading = same sound (着/著, 地/的, 将/降)
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
