"""Raw-take check the whole-clip ASR misses (11-18 EP06 user found 熄着着 / 晚晚一步 / 小柚 jumping to a close-up):
speech split at pauses, every chunk heard ALONE vs the script (extra syllables) + picture spikes (in-clip cut / jump).
python takecheck.py keys... -> studio/takecheck.json {key: {ok, errs, spikes}}"""
import difflib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin, pinyin, Style
st = Path("studio")
sc = {s["id"]: s for s in json.loads(Path("script.json").read_text(encoding="utf-8"))["shots"]}
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
D = "零一二三四五六七八九"
def cn(n):
    n = int(n)
    if n >= 1000: return "".join(D[int(c)] for c in str(n))
    if n >= 100: return D[n // 100] + "百" + (("零" if n % 100 < 10 else "") + cn(n % 100) if n % 100 else "")
    if n >= 10: return ("" if n < 20 else D[n // 10]) + "十" + (D[n % 10] if n % 10 else "")
    return D[n]
def clean(x):
    x = x.replace("C罗", "西罗"); x = re.sub(r"\d+", lambda g: cn(g.group()), x); return re.sub(r"[^一-鿿]", "", x)
het = lambda s: [set(pinyin(c, style=Style.NORMAL, heteronym=True)[0]) for c in s]
res = json.loads((st / "takecheck.json").read_text(encoding="utf-8")) if (st / "takecheck.json").exists() else {}
for k in sys.argv[1:]:
    p = st / "clips" / f"{k}.mp4"; line = clean(sc[k.split("_t")[0]]["line"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n = len(x) // 160
    e = np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)); sm = np.convolve(e, np.ones(5) / 5, "same"); on = sm > 0.1 * np.percentile(sm, 95)
    cs, j = [], 0
    while j < n:
        if on[j]:
            q = j
            while q < n and (on[q] or (q + 25 < n and on[q:q + 25].any())): q += 1
            cs.append((max(0, j - 15), min(n, q + 15))); j = q
        else: j += 1
    heard = ""
    for a, b in cs:
        sg, _ = m.transcribe(x[a * 160:b * 160], language="zh", beam_size=5, condition_on_previous_text=False, temperature=0)
        heard += "".join(s_.text for s_ in sg)
    heard = clean(heard); A, B = lazy_pinyin(line), lazy_pinyin(heard); HA, HB = het(line), het(heard); errs = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and a2 - a1 == b2 - b1 and all(HA[a1 + i] & HB[b1 + i] for i in range(a2 - a1))): continue
        errs.append(f"{op}:「{line[a1:a2]}」→「{heard[b1:b2]}」")
    vr = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", "scale=192:108,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(vr, np.uint8).reshape(-1, 108, 192).astype(np.float32); d = np.abs(np.diff(f, axis=0)).mean((1, 2)); med = float(np.median(d)) + 0.5
    spikes = [round((i + 1) / 24, 2) for i in range(1, len(d)) if d[i] > max(10, 5 * med)]
    ins = [x for x in errs if x.startswith("insert")]  # extra / repeated syllables = hard fail; replace/delete left to strict_check
    res[k] = {"ok": not ins and not spikes, "errs": errs, "spikes": spikes, "heard": heard}
    print(("OK  " if res[k]["ok"] else "FAIL"), k, errs, "spikes", spikes, "||", heard, flush=True)
(st / "takecheck.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("TAKECHECK_DONE")
