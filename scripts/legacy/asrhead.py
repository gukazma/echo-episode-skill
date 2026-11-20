import sys
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cuda", compute_type="float16")
for k in sys.argv[1:]:
    seg, _ = m.transcribe(f"studio/clips/{k}.mp4", language="zh", vad_filter=False, beam_size=5, word_timestamps=True, initial_prompt="以下是普通话句子。")
    ws = [(round(w.start, 2), w.word) for s in seg for w in s.words]
    print(k, ws, flush=True)
