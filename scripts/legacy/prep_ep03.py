"""prep: bgm wavs, Korean ASR of speech clips (to place O() windows), contact sheets per footage file."""
import json, subprocess, sys
from pathlib import Path
ep = Path(__file__).resolve().parent
what = sys.argv[1:] or ["bgm", "asr", "sheets"]
def run(c): subprocess.run(c, check=True)
def probe(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip() or 0)
if "bgm" in what:
    (ep / "bgm").mkdir(exist_ok=True)
    M = {"evergreen_viola": "bgm_evergreen_viola", "evergreen_piano": "bgm_evergreen_piano", "evergreen_piano2": "bgm_evergreen_piano2",
         "tense": "bgm_attorney_painful", "rise": "bgm_attorney_99", "ensemble": "bgm_evergreen_ensemble", "suite": "bgm_attorney_suite"}
    for k, src in M.items():
        f = ep / "bgm_src" / f"{src}.m4a"
        if f.exists() and not (ep / "bgm" / f"{k}.wav").exists():
            run(["ffmpeg", "-y", "-v", "error", "-i", str(f), "-af", "loudnorm=I=-20:TP=-3,aresample=48000", "-ac", "2", str(ep / "bgm" / f"{k}.wav")])
            print("bgm", k, round(probe(ep / "bgm" / f"{k}.wav"), 1), flush=True)
if "asr" in what:
    from faster_whisper import WhisperModel
    m = WhisperModel("medium", device="cuda", compute_type="float16")
    out = {}
    for k in ["bexco2002", "bongha_feelgood", "probe_bus", "memorial2017", "ad_evergreen", "roh_citizens", "moon_inaug_speech", "moon2012_concede", "bongha2022"]:
        f = ep / "footage" / f"{k}.mp4"
        if not f.exists():
            continue
        segs, _ = m.transcribe(str(f), language="ko", vad_filter=True, beam_size=5)
        out[k] = [[round(s.start, 1), round(s.end, 1), s.text.strip()] for s in segs]
        print("asr", k, len(out[k]), flush=True)
    (ep / "asr.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
if "sheets" in what:
    (ep / "sheets").mkdir(exist_ok=True)
    for f in sorted((ep / "footage").glob("*.mp4")):
        o = ep / "sheets" / f"{f.stem}.jpg"
        if o.exists():
            continue
        d = probe(f)
        if d <= 0:
            continue
        n = 12
        step = d / (n + 1)
        ins = []
        for j in range(n):
            ins += ["-ss", f"{step * (j + 1):.1f}", "-i", str(f)]
        lab = ";".join(f"[{j}:v]scale=480:-2,setsar=1,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='{step * (j + 1):.0f}s':fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6:x=6:y=6,"
                       f"scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2[p{j}]" for j in range(n))
        lay = "|".join(f"{(j % 4) * 480}_{(j // 4) * 270}" for j in range(n))
        try:
            run(["ffmpeg", "-y", "-v", "error", *[x for x in ins], "-filter_complex", lab + ";" + "".join(f"[p{j}]" for j in range(n)) + f"xstack=inputs={n}:layout={lay}",
                 "-frames:v", "1", "-q:v", "4", str(o)])
            print("sheet", f.stem, round(d), flush=True)
        except subprocess.CalledProcessError:
            print("sheet FAIL", f.stem, flush=True)
print("PREP_DONE", flush=True)
