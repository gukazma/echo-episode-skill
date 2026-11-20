"""Signal-level check of host-shot audio, stage by stage: raw Seedance take -> rendered segment -> finished film.
Detects clicks (impulsive sample jumps), clipping, low-frequency plosive pops, unnatural dropouts inside speech.
Writes spectrogram strips of every flagged spot to qc/audio/.  python audiocheck.py film.mp4"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt
from PIL import Image
film = sys.argv[1]; sys.argv = ["x", "none"]
import make_ep06 as m
ep = Path(".").resolve(); out = ep / "qc" / "audio"; out.mkdir(parents=True, exist_ok=True)
SR = 48000
def load(p, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.3f}", "-t", f"{t:.3f}"] if ss is not None else []) + ["-i", str(p), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)
LP = butter(4, 150, "low", fs=SR, output="sos"); BP = butter(4, [200, 4000], "band", fs=SR, output="sos")
def frames_db(x, hop=480):
    n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
def group(idx, gap):
    g = []
    for i in idx:
        if g and i - g[-1][1] <= gap: g[-1][1] = i
        else: g.append([i, i])
    return g
def analyse(x):
    r = {}
    r["clip"] = int((np.abs(x) >= 0.985).sum())
    s2 = np.abs(x[2:] - 2 * x[1:-1] + x[:-2]); hop = 480; n = len(s2) // hop
    fm = np.median(s2[:n * hop].reshape(n, hop), axis=1); fm = np.maximum(np.repeat(np.maximum.accumulate(fm[::-1])[::-1] * 0 + fm, hop), 2e-4)
    cand = np.where((s2[:n * hop] > 18 * fm) & (s2[:n * hop] > 0.04))[0]
    r["clicks"] = [round(a / SR, 3) for a, b in group(cand, 240)]
    lf, sb = frames_db(sosfilt(LP, x)), frames_db(sosfilt(BP, x))
    pop = np.where((lf > -24) & (lf - sb > 2))[0]
    r["pops"] = [(round(a / 100, 2), round(lf[a:b + 1].max(), 1)) for a, b in group(pop, 3)]
    db = frames_db(x); sm = np.convolve(db, np.ones(15) / 15, "same"); drops = []
    i = 1
    while i < len(db) - 1:
        if db[i] < sm[i] - 22 and sm[i] > -38:
            j = i
            while j < len(db) and db[j] < sm[i] - 22: j += 1
            if 2 <= j - i <= 12 and db[max(0, i - 3):i].max(initial=-99) > -35 and db[j:j + 3].max(initial=-99) > -35:
                drops.append((round(i / 100, 2), j - i))
            i = j
        i += 1
    r["drops"] = drops
    r["peak_db"] = round(20 * np.log10(np.abs(x).max() + 1e-9), 1)
    return r
def spec(x, t0, name):  # 1.0 s spectrogram around t0, 0-8 kHz, log magnitude
    a = max(0, int((t0 - 0.5) * SR)); seg = x[a:a + SR]
    if len(seg) < 2048: return
    win, hop = 1024, 128; fr = [np.abs(np.fft.rfft(seg[i:i + win] * np.hanning(win)))[:171] for i in range(0, len(seg) - win, hop)]
    S = 20 * np.log10(np.array(fr).T + 1e-6); S = np.clip((S - S.max() + 80) / 80, 0, 1)[::-1]
    Image.fromarray((S * 255).astype(np.uint8)).resize((600, 240)).save(out / name)
segs = [l.split("'")[1] for l in (ep / "v1" / "concat.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
pr = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
t = pr(segs[0]); start = {}
for s, p in zip(m.SHOTS, segs[1:]): start[s["id"]] = (t, pr(p)); t += pr(p)
mmss = lambda x: f"{int(x // 60)}:{x % 60:04.1f}"
res = {}
for i, s in enumerate(m.SHOTS, 1):
    if s["id"] not in m.ACC: continue
    st, d = start[s["id"]]; key = m.ACC[s["id"]][0]
    raw = load(m.STUDIO / "clips" / f"{key}.mp4"); q = m.QC[key]["speech"]; raw = raw[int(max(0, q[0] - 0.3) * SR):int((q[1] + 0.5) * SR)]
    seg = load(segs[i]); fl = load(film, st, d)
    R = {"raw": analyse(raw), "seg": analyse(seg), "film": analyse(fl)}
    # sync: lag of the film slice vs the rendered segment (10 ms envelopes, +-0.4 s search) - must stay ~0
    ea, eb = frames_db(seg), frames_db(fl); k_ = min(len(ea), len(eb)) - 40
    lags = {L: float(np.corrcoef(ea[40:k_], eb[40 + L:k_ + L])[0, 1]) for L in range(-40, 41) if 40 + L >= 0 and k_ + L <= len(eb)}
    R["lag_ms"] = 10 * max(lags, key=lags.get) if lags else None
    res[s["id"]] = {"t": mmss(st), "key": key, **R}
    for stage, x in (("seg", seg), ("film", fl)):
        for c in R[stage]["clicks"][:4]: spec(x, c, f"{s['id']}_{stage}_click_{c:.2f}.png")
        for c, _ in R[stage]["pops"][:4]: spec(x, c, f"{s['id']}_{stage}_pop_{c:.2f}.png")
        for c, _ in R[stage]["drops"][:4]: spec(x, c, f"{s['id']}_{stage}_drop_{c:.2f}.png")
    line = " | ".join(f"{k}: clip{R[k]['clip']} clicks{len(R[k]['clicks'])} pops{len(R[k]['pops'])} drops{len(R[k]['drops'])} pk{R[k]['peak_db']}" for k in ("raw", "seg", "film"))
    print(f"{mmss(st)} {s['id']} {key} {line} | lag {R['lag_ms']} ms", flush=True)
(out / "audiocheck.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("AUDIO_DONE")
