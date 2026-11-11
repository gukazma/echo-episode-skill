"""QC EP02 studio takes: pinyin diff vs line, voice match vs TTS (duration, F0, envelope correlation), frame strip.
python studio_qc.py <plan.json>   → studio/qc.json + studio/review/<take>.jpg"""
import difflib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
ep = Path(__file__).resolve().parent; st = ep / "studio"
plan = {s["id"]: s for s in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["shots"]}
sc = {s["id"]: s for s in json.loads((ep / "script_v4.json").read_text(encoding="utf-8"))["shots"]}
rv = st / "review"; rv.mkdir(exist_ok=True)
qp = st / "qc.json"; qc = json.loads(qp.read_text(encoding="utf-8")) if qp.exists() else {}
def pcm(p):
    raw = subprocess.run(["ffmpeg","-v","error","-i",str(p),"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(float)
def f0(x, fs=16000):
    r = []
    for i in range(0, len(x) - 1024, 400):
        w = x[i:i+1024]
        if np.sqrt((w**2).mean()) < 600: continue
        c = np.correlate(w, w, "full")[1023:]; lo, hi = fs // 400, fs // 70; r.append(fs / (lo + np.argmax(c[lo:hi])))
    return float(np.median(r)) if r else 0
def env(x, hop=160):
    n = len(x) // hop; return np.sqrt((x[:n*hop].reshape(n, hop)**2).mean(1))
def speech_span(x, fs=16000):
    e = env(x); th = max(e.max() * 0.08, 300); idx = np.where(e > th)[0]
    return (idx[0] * 160 / fs, idx[-1] * 160 / fs) if len(idx) else (0, 0)
def py(t): return re.sub(r"[^\u4e00-\u9fff0-9a-zA-Z]", "", t)
model = WhisperModel("medium", device="cuda", compute_type="float16")
for mp4 in sorted((st / "clips").glob("*_t*.mp4")):
    key = mp4.stem; sid = key.split("_t")[0]
    if (key in qc and "--redo" not in sys.argv) or sid not in plan or mp4.stat().st_size == 0: continue
    p = plan[sid]; s = {"line": p.get("line") or sc[sid]["line"]}
    dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(mp4)],capture_output=True,text=True).stdout)
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(mp4),"-vf",f"fps=5/{dur:.2f},scale=384:-1,tile=5x1","-frames:v","1",str(rv / f"{key}.jpg")])
    heard = "".join(x.text for x in model.transcribe(str(mp4), language="zh", vad_filter=False, beam_size=5)[0])
    a, b = lazy_pinyin(py(s["line"])), lazy_pinyin(py(heard)); tx = py(s["line"])
    diffs = [f"{op}:{tx[i1:i2]}({' '.join(a[i1:i2])})->{' '.join(b[j1:j2])}" for op, i1, i2, j1, j2 in
             difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if op != "equal"]
    sim = difflib.SequenceMatcher(None, "".join(a), "".join(b)).ratio()
    xv, xt = pcm(mp4), pcm(p["audio_refs"][0])
    sv, st_ = speech_span(xv), speech_span(xt)
    ev, et = env(xv[int(sv[0]*16000):int(sv[1]*16000)]), env(xt[int(st_[0]*16000):int(st_[1]*16000)])
    m = min(len(ev), len(et)); corr = float(np.corrcoef(ev[:m], et[:m])[0, 1]) if m > 50 else 0
    fv, ft = f0(xv), f0(xt)
    rec = json.loads(mp4.with_suffix(".json").read_text(encoding="utf-8"))
    qc[key] = {"sim": round(sim, 3), "diffs": diffs, "heard": heard, "dur": round(dur, 1), "speech": [round(sv[0], 2), round(sv[1], 2)],
               "speech_len": round(sv[1] - sv[0], 2), "tts_len": round(st_[1] - st_[0], 2), "env_corr": round(corr, 2),
               "f0": round(fv), "f0_tts": round(ft), "cost": rec.get("cost_cny")}
    qp.write_text(json.dumps(qc, ensure_ascii=False, indent=1), encoding="utf-8")
    q = qc[key]; flag = "OK " if sim >= 0.9 and not diffs else "CHK"
    print(f"{flag} {key} sim={sim:.2f} speech {q['speech_len']}s vs tts {q['tts_len']}s corr={corr:.2f} F0 {fv:.0f}/{ft:.0f} cost={q['cost']} | {heard[:40]} {diffs[:3]}", flush=True)
