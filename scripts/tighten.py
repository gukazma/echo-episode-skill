"""Pause/stutter tightening for accepted Seedance takes -> studio/tighten.json {take: [[cut_start, cut_end], ...]} (clip time).
- mid-line pause > 0.55 s (whisper word gap, confirmed quiet by RMS) -> shortened to KEEP s
- immediate duplicated single char (的的/操操/在在) not present doubled in the script line -> first copy removed"""
import json, re, subprocess
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
st = Path("studio"); qc = json.loads((st / "qc.json").read_text(encoding="utf-8"))
SC = {s["id"]: s for s in json.loads(Path("script_v4.json").read_text(encoding="utf-8"))["shots"]}
ACC = json.loads((st / "accepted.json").read_text(encoding="utf-8"))
KEEP, HEAD, GAP = 0.40, 0.20, 0.75
m = WhisperModel("medium", device="cuda", compute_type="float16")
def rms(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float); n = len(x) // 160
    return np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))  # 10 ms frames
out, log, tails = {}, [], {}
for sid, keys in ACC.items():
    line = re.sub(r"[^一-鿿]", "", SC[sid]["line"]).replace("她", "他")
    for k in keys:
        p = st / "clips" / f"{k}.mp4"; q = qc[k]
        a, b = max(0.0, q["speech"][0] - 0.3), q["speech"][1] + 0.5
        e = rms(p); peak = np.percentile(e[int(a * 100):int(b * 100)], 95)
        quiet = lambda s, t: e[int(s * 100):int(t * 100)].max(initial=0) < 0.12 * peak
        ws = [w for s in m.transcribe(str(p), language="zh", vad_filter=False, word_timestamps=True, condition_on_previous_text=False, beam_size=5)[0] for w in s.words]
        ws = [w for w in ws if a <= w.start <= b]
        cuts, dups = [], []
        if ws:
            # acoustic pauses (quiet runs) between the first and last word - catches pauses whisper hides inside a stretched word
            f0, f1 = int(ws[0].end * 100), int(ws[-1].start * 100)
            qf = e < 0.07 * peak
            j = f0
            while j < f1:
                if qf[j]:
                    r = j
                    while r < f1 and qf[r]: r += 1
                    g = (r - j) / 100
                    if g > GAP:
                        cuts.append([round(j / 100 + HEAD, 2), round(r / 100 - (KEEP - HEAD), 2)]); log.append(f"{k} pause {g:.2f}s -> cut {g - KEEP:.2f}s @ {j / 100:.2f}")
                    j = r
                else: j += 1
            tails[k] = round(max(q["speech"][1], min(ws[-1].end, q["speech"][1] + 0.8)), 2)
        for w1, w2 in zip(ws, ws[1:]):
            c1, c2 = w1.word.strip().replace("她", "他"), w2.word.strip().replace("她", "他")
            if len(c1) == 1 and c1 == c2 and re.match(r"[一-鿿]", c1) and c1 * 2 not in line and w2.start - w1.start < 0.4:
                dups.append([round(w1.start, 2), round(w2.start, 2)]); log.append(f"{k} dup '{c1}' cut {w2.start - w1.start:.2f}s @ {w1.start:.2f}")
        # never cut into the sounding end of a recognised word (soft syllables like 也 can sit under the quiet threshold)
        # protect a word's last 0.3 s only if something is actually audible there (> 3% of peak); whisper often stretches word ends into silence
        floor = np.percentile(e[int(a * 100):int(b * 100)], 10)
        prot = [(w.end - 0.3, w.end) for w in ws if e[int((w.end - 0.3) * 100):int(w.end * 100)].max(initial=0) > max(0.03 * peak, 3 * floor)]
        safe = []
        for c0, c1 in cuts:
            for p0, p1 in prot:
                if p0 < c1 and p1 > c0:
                    if p0 >= c0: c1 = min(c1, p0)
                    else: c0 = max(c0, p1)
            if c1 - c0 >= 0.15: safe.append([round(c0, 2), round(c1, 2)])
            else: log.append(f"{k} cut dropped (word protection) @ {c0:.2f}")
        cuts = safe + dups
        merged = []
        for c in sorted(cuts):
            if merged and c[0] <= merged[-1][1] + 0.05: merged[-1][1] = max(merged[-1][1], c[1])
            else: merged.append(c)
        if merged: out[k] = merged
(st / "tighten.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(st / "tail.json").write_text(json.dumps(tails, indent=1), encoding="utf-8")
print("\n".join(log)); print("takes tightened:", len(out))
