"""Whisper word probabilities per take: low-probability words are suspects for 'filled-in' (actually unspoken) characters.
python wordprob.py key1 key2 ...   (keys = studio/clips/<key>.mp4)"""
import sys
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cuda", compute_type="float16")
for k in sys.argv[1:]:
    segs, _ = m.transcribe(f"studio/clips/{k}.mp4", language="zh", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
    ws = [w for s in segs for w in s.words]
    print(k, " ".join(f"{w.word.strip()}({w.probability:.2f})" for w in ws), flush=True)
