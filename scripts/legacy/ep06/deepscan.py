"""Deep host-shot scan of the rendered film (v1/concat.txt = what 正片 was built from).
Per host segment: (1) speech split at pauses, every chunk transcribed ALONE (whole-segment ASR smooths repeats away),
pinyin-diff vs script -> INSERT (repeated / extra words), MISS; (2) picture: per-frame change spikes inside the segment
(in-clip cut / sudden jump) and at the boundary to the previous host segment; saves before/after frames to qc/deep/.
python deepscan.py [host|vo]"""
import json, re, difflib, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
mode = sys.argv[1] if len(sys.argv) > 1 else "host"
sys.argv = ["x", "none"]
import make_ep06 as m
from pypinyin import lazy_pinyin, pinyin, Style
from faster_whisper import WhisperModel
ep = Path(".").resolve(); out = ep / "qc" / "deep"; out.mkdir(parents=True, exist_ok=True)
segs = [l.split("'")[1] for l in (ep / "v1" / "concat.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
pr = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
t = pr(segs[0]); start = {}
for s, p in zip(m.SHOTS, segs[1:]):
    start[s["id"]] = t; t += pr(p)
model = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
mmss = lambda x: f"{int(x // 60)}:{x % 60:04.1f}"
D = "零一二三四五六七八九"
def cn(n):
    n = int(n)
    if n >= 1000: return "".join(D[int(c)] for c in str(n))
    if n >= 100: return D[n // 100] + "百" + (("零" if n % 100 < 10 else "") + cn(n % 100) if n % 100 else "")
    if n >= 10: return ("" if n < 20 else D[n // 10]) + "十" + (D[n % 10] if n % 10 else "")
    return D[n]
def clean(x):
    x = x.replace("C罗", "西罗"); x = re.sub(r"\d+", lambda g: cn(g.group()), x)
    return re.sub(r"[^\u4e00-\u9fff]", "", x)
hetero = lambda s: [set(pinyin(c, style=Style.NORMAL, heteronym=True)[0]) for c in s]

def audio(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def chunks(x):
    n = len(x) // 160; e = np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))
    if n == 0: return []
    sm = np.convolve(e, np.ones(5) / 5, "same"); on = sm > 0.1 * np.percentile(sm, 95)
    res, j = [], 0
    while j < n:
        if on[j]:
            k = j
            while k < n and (on[k] or (k + 25 < n and on[k:k + 25].any())): k += 1  # bridge pauses < 0.25 s
            res.append((max(0, j - 15) / 100, min(n, k + 15) / 100)); j = k
        else: j += 1
    return res

def hear(x, cs):
    words = []
    for a, b in cs:
        sg, _ = model.transcribe(x[int(a * 16000):int(b * 16000)], language="zh", word_timestamps=True, beam_size=5,
                                 condition_on_previous_text=False, vad_filter=False, temperature=0)
        words += [(a + w.start, w.word, w.probability) for s_ in sg for w in s_.words]
    return words

def diff(line, heard):
    A, B = lazy_pinyin(line), lazy_pinyin(heard); HA, HB = hetero(line), hetero(heard); errs = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        if op == "equal": continue
        if op == "replace" and a2 - a1 == b2 - b1 and all(HA[a1 + j] & HB[b1 + j] for j in range(a2 - a1)): continue
        errs.append(f"{op}:「{line[a1:a2]}」→「{heard[b1:b2]}」")
    return errs

W, H = 192, 108
def frames(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)

def snap(p, t0, name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t0 - 0.12):.3f}", "-i", str(p), "-frames:v", "4", "-vf", "scale=480:-2,tile=4x1",
                          "-f", "image2pipe", "-vcodec", "mjpeg", "-"], capture_output=True).stdout
    (out / name).write_bytes(raw)

res, prev_last, prev_who = {}, None, None
for i, s in enumerate(m.SHOTS, 1):
    host = s["id"] in m.ACC
    if mode == "host" and not host:
        prev_last, prev_who = None, None; continue
    if mode == "vo" and (host or not s["line"] or s["who"] == "无" or s["pic"].startswith("fc:")): continue
    p = Path(segs[i]) if host else m.voice(s)
    x = audio(p); cs = chunks(x); ws = hear(x, cs)
    heard = clean("".join(w for _, w, _ in ws)); line = clean(m.say_text(s["line"]))
    errs = diff(line, heard)
    r = {"t": mmss(start[s["id"]]), "who": s["who"], "line": s["line"], "heard": heard, "errs": errs, "chunks": len(cs),
         "low": [f"{w.strip()}@{a:.1f}({pb:.2f})" for a, w, pb in ws if pb < 0.4]}
    if host:
        f = frames(p); d = np.abs(np.diff(f, axis=0)).mean((1, 2)); med = float(np.median(d)) + 0.5
        spikes = [(j + 1) / 25 for j in range(1, len(d)) if d[j] > max(10, 5 * med)]
        r["spikes"] = [round(v, 2) for v in spikes]; r["med"] = round(med, 2)
        for v in spikes: snap(p, v, f"{s['id']}_spike_{v:.2f}.jpg")
        if prev_last is not None:
            bd = float(np.abs(f[0] - prev_last).mean()); r["boundary"] = round(bd, 1)
            if prev_who == s["who"]:
                r["same_who_cut"] = True
        prev_last, prev_who = f[-1], s["who"]
    res[s["id"]] = r
    flag = errs or r.get("spikes")
    print(("FLAG " if flag else "ok   ") + f"{r['t']} {s['id']} {s['who']} {' '.join(errs)} spikes={r.get('spikes')} bd={r.get('boundary')} | {s['line']} || {heard}", flush=True)
(out / f"deep_{mode}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("DEEP_DONE", mode, sum(1 for r in res.values() if r["errs"] or r.get("spikes")))
