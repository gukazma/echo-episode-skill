"""CPU whisper on the TTS of lines with polyphone names -> pinyin of what is heard (EP09 example name list - edit W per episode)"""
import json, sys
sys.argv = ["x", "none"]
import make_episode as m
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin, Style
W = ["单于", "阏氏", "浑邪", "休屠", "冠军侯", "骠骑", "剽姚", "焉支", "终不还", "无以家为", "卫少儿", "蕃息"]
md = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
for s in m.SHOTS:
    hit = [w for w in W if w in (s["line"] or "")]
    if not hit: continue
    txt = "".join(x.text for x in md.transcribe(str(m.voice(s)), language="zh", beam_size=5)[0])
    print(s["id"], hit, "|", " ".join(lazy_pinyin(txt, style=Style.TONE3))[:160], "|", txt[:60], flush=True)
print("PRON_DONE")
