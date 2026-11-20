import sys
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cuda", compute_type="float16")
for f in sys.argv[1:]:
    ws = [w for s in m.transcribe(f, language="zh", word_timestamps=True, beam_size=5)[0] for w in s.words]
    print(f, " ".join(f"{w.word}@{w.start:.2f}-{w.end:.2f}" for w in ws), flush=True)
