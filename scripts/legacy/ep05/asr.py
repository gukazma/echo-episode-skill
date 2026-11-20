"""faster-whisper transcripts with segment timestamps -> qc/asr_<key>.txt   python asr.py key[:lang] ...  (lang default en)"""
import sys
from pathlib import Path
from faster_whisper import WhisperModel
ep = Path(__file__).resolve().parent
(ep / "qc").mkdir(exist_ok=True)
m = WhisperModel("medium", device="cuda", compute_type="float16")
for a in sys.argv[1:]:
    k, _, lang = a.partition(":")
    out = ep / "qc" / f"asr_{k}.txt"
    if out.exists():
        print(k, "exists", flush=True); continue
    src = ep / "footage" / f"{k}.mp4"
    if not src.exists():
        print(k, "MISSING", flush=True); continue
    segs, _ = m.transcribe(str(src), language=lang or "en", beam_size=5, vad_filter=True)
    out.write_text("\n".join(f"{s.start:7.1f}-{s.end:7.1f} {s.text.strip()}" for s in segs), encoding="utf-8")
    print(k, "ok", flush=True)
print("ASR_DONE", flush=True)
