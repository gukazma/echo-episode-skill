"""YouTube auto/manual English captions (json3) for given 'key id' pairs -> qc/sub_<key>.txt  ('start-end text' per caption event)"""
import json, sys
from pathlib import Path
import yt_dlp
ep = Path(__file__).resolve().parent
(ep / "qc").mkdir(exist_ok=True)
pairs = [a.split("=") for a in sys.argv[1:]]
for k, vid in pairs:
    out = ep / "qc" / f"sub_{k}.txt"
    tmp = ep / "qc" / f"_sub_{k}"
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "writesubtitles": True, "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-orig", "ja", "zh-Hant", "zh-TW", "zh"], "subtitlesformat": "json3", "outtmpl": str(tmp)}
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            y.download([f"https://www.youtube.com/watch?v={vid}"])
    except Exception as e:
        print(k, "ERR", str(e)[:200], flush=True)
    fs = sorted(ep.glob(f"qc/_sub_{k}*.json3"))
    if not fs:
        print(k, "no subs", flush=True); continue
    f = next((x for x in fs if ".en" in x.name), fs[0])
    j = json.loads(f.read_text(encoding="utf-8"))
    lines = []
    for e in j.get("events", []):
        t = "".join(s.get("utf8", "") for s in e.get("segs", []) or []).replace("\n", " ").strip()
        if t:
            a = e["tStartMs"] / 1000; b = a + e.get("dDurationMs", 0) / 1000
            lines.append(f"{a:8.1f}-{b:8.1f} {t}")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(k, "ok", f.name, len(lines), flush=True)
print("SUBS_DONE", flush=True)
