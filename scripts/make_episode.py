"""EP07 preview/final film (forked from EP06 make_episode) (forked from EP04 make_episode, EP03 make_episode) (forked from EP02 make_v4): full-screen pictures + 老渡 voice (Doubao TTS) + BGM + subtitles.

python make_v4.py pics|tts|video|all
Voices: 老渡 = cloned voice from voice_ids.json["laodu"] (seed-icl-2.0) if present, else preset 云舟 2.0;
        小柚 = preset vivi 2.0.
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid

import numpy as np
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.environ.get("OPENMONTAGE", r"D:\OpenMontage"))
load_dotenv(os.environ.get("OPENMONTAGE", r"D:\OpenMontage") + r"\.env")
ep = Path(__file__).resolve().parent
EPN = os.environ.get("EP") or (re.findall(r"ep(\d+)", str(ep).lower()) or ["00"])[-1].zfill(2)  # episode number (folder echo_epNN or env EP)
sc = json.loads((ep / "script.json").read_text(encoding="utf-8"))
SHOTS, BGM, MONT = sc["shots"], sc["bgm"], sc.get("montages", {})
W, H, FPS = 1920, 1080, 25
work = ep / "v1"
for d in ("pic", "tts", "seg"):
    (work / d).mkdir(parents=True, exist_ok=True)
APIKEY = os.environ.get("VOLC_TTS_APIKEY", "")
APIKEY_NEW = os.environ.get("VOLC_TTS_APIKEY_NEW", "").strip()  # EP08: stock seed-tts-2.0 voices go through a second speech-console key when the first one's stock-voice quota is used up (clones stay on APIKEY)
IDS = json.loads((ep / "voice_ids.json").read_text(encoding="utf-8")) if (ep / "voice_ids.json").exists() else {}  # {"laodu": "S_...", "xiaoyou": "S_..."} cloned voice ids (not in the repo)
VOICE = {"老渡": (IDS["laodu"], "seed-icl-2.0") if IDS.get("laodu") else ("zh_male_m191_uranus_bigtts", "seed-tts-2.0"),
         "小柚": (IDS["xiaoyou"], "seed-icl-2.0") if IDS.get("xiaoyou") else ("zh_female_vv_uranus_bigtts", "seed-tts-2.0")}
VOICE.update({  # EP07 v2: foreign-language originals dubbed in Mandarin (user 11-20: sleep listeners can't follow English/Spanish)
    "配·帕拉多": ("zh_male_yizhipiannan_uranus_bigtts", "seed-tts-2.0"),
    "配·卡塔兰": ("zh_male_yuanboxiaoshu_uranus_bigtts", "seed-tts-2.0"),
    "配·德尔加多": ("zh_male_ruyaqingnian_uranus_bigtts", "seed-tts-2.0"),
    "配·卡内萨": ("zh_male_liufei_uranus_bigtts", "seed-tts-2.0"),
})
RATE = {"老渡": 10 if IDS.get("laodu") else -8, "小柚": 15 if IDS.get("xiaoyou") else 0}  # clones speak ~19% slower than presets
SAY = {}  # polyphone hints for TTS only (homophone substitution, subtitles keep the real text); EP09 example: {"单于": "蝉于", "阏氏": "烟支", "浑邪王": "浑耶王", "冠军侯": "贯军侯", "骠骑": "票骑", "终不还": "终不环", "无以家为": "无以家维"}


def run(cmd):
    subprocess.run(cmd, check=True)


def loud_i(p, ss=None, t=None):
    """integrated loudness (LUFS) of a file / range - for one fixed gain instead of dynamic loudnorm (pumping, overs)"""
    r = subprocess.run(["ffmpeg", "-nostats", "-v", "info"] + (["-ss", f"{ss:.3f}", "-t", f"{t:.3f}"] if ss is not None else []) + ["-i", str(p), "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m_ = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    return float(m_[-1]) if m_ else -23.0


def fixgain(src, a, dur, target):
    """fixed gain to target LUFS + limiter (-3 dBFS) instead of single-pass dynamic loudnorm (pumping/overs, EP06 v4)"""
    return f"highpass=f=60,volume={target - loud_i(src, a, dur):.2f}dB,alimiter=limit=0.708:attack=3:release=60:level=0,"


def probe(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())


# ------------------------------------------------------------------ pictures
def pic_path(s):
    kind, _, rest = s["pic"].partition(":")
    if kind == "d":
        e, t = rest.split(":")
        return work / "pic" / f"d{int(e):02d}_{int(float(t))}.png"
    if kind == "img":
        return ep / "img" / f"{rest}.png"
    return ep / "img" / ("a_" + hashlib.md5(rest.encode()).hexdigest()[:10] + ".png")


def make_pic(s):
    if s["pic"].startswith(("clip:", "mont:", "f:", "d:", "fc:", "fa:", "fd:")):
        return
    out = pic_path(s)
    if out.exists():
        return
    kind, _, rest = s["pic"].partition(":")
    if kind == "d":
        e, t = rest.split(":")
        run(["ffmpeg", "-y", "-v", "error", "-ss", t, "-i", str(ep / "drama" / "eps" / f"e{int(e):02d}.mp4"), "-frames:v", "1",
             "-vf", "crop=iw-40:ih*0.80:20:ih*0.10,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080", str(out)])
    elif kind == "ai":
        from tools.graphics.seedream_ark import SeedreamArkImage
        r = SeedreamArkImage().execute({"prompt": "电影级写实，东汉末年三国时期，16:9，低饱和暖色调。" + rest + "。画面中没有任何文字、字母、水印。",
                                        "model": "flash", "size": "1280x720", "reference_images": [], "output_path": str(out)})
        print("ai", out.name, r.success, r.error if not r.success else "", flush=True)


# ------------------------------------------------------------------ voice
def say_text(t):
    for k, v in SAY.items():
        t = t.replace(k, v)
    return t


def tts_path(s):
    spk, rid = VOICE.get(s["who"], VOICE["老渡"])
    key = (f"{spk}|{rid}|{s.get('ctx', '')}|{s['line']}" if s["who"].startswith("配") else f"{spk}|{rid}|{s['line']}") if not spk.startswith("S_") else f"{spk}|{rid}|m4|pcm2|r{s.get('rate', 0)}|{s.get('ctx', '')}|{s['line']}"
    return work / "tts" / (hashlib.md5(key.encode()).hexdigest()[:16] + ".wav")


def voice(s):
    """Narration audio as used in the film: the TTS line with mid-line pauses > 0.75 s cut down to 0.6 s.
    Audio only - narration plays over footage, so nothing visible jumps (host shots are never cut: a splice there is a visible jump = 卡顿)."""
    src = tts_path(s)
    if os.environ.get("VO_TIGHT", "1") != "1":
        return src
    mp = float(s.get("maxpause", 0.75))  # emotional lines (heavy/poem/tender) keep their pauses up to ~1.4 s
    out = work / "tts_t" / (src.stem + ("" if mp == 0.75 else f"_p{int(mp * 100)}") + ".wav")
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        import numpy as np, wave
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "24000", "-f", "s16le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32)
        hop = 240  # 10 ms
        n = len(x) // hop
        db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) / 32768 + 1e-9)
        db = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(db, 4, mode="edge"), 9), axis=1)  # breath/noise in pauses flickers -34..-46 dB
        TH = -32
        loud = np.where(db > TH)[0]
        keep, cur = [], 0
        if len(loud):
            j, last = loud[0], loud[-1]
            while j < last:
                if db[j] <= TH:
                    r = j
                    while r < last and db[r] <= TH:
                        r += 1
                    if (r - j) * 0.01 > mp:  # pause > mp -> mp-0.15 s: keep the tail after the word (soft endings) and 0.15 s before the next
                        keep.append((cur, (j + max(45, int(mp * 100) - 30)) * hop)); cur = (r - 15) * hop
                    j = r
                else:
                    j += 1
        keep.append((cur, len(x)))
        parts, fade = [], 120  # 5 ms fades at each splice (inside silence, inaudible)
        for a, b in keep:
            seg = x[a:b].copy()
            if len(seg) > 2 * fade and len(keep) > 1:
                seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
            parts.append(seg)
        y = np.concatenate(parts).clip(-32768, 32767).astype(np.int16)
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(y.tobytes())
    return out


def tts(s):
    out = tts_path(s)
    if out.exists() and out.stat().st_size > 1000:
        return
    spk, rid = VOICE.get(s["who"], VOICE["老渡"])
    if rid == "edge":  # EP08: free fallback voice for dubs (DUB_EDGE=1 style mapping in VOICE) -> 24 kHz mono wav with the same 0.3 s clean tail
        import asyncio, edge_tts
        mp3 = out.with_suffix(".mp3")
        asyncio.run(edge_tts.Communicate(s["line"], spk, rate="-8%", pitch="-4Hz").save(str(mp3)))
        run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-af", "apad=pad_dur=0.3", "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(out)])
        mp3.unlink(missing_ok=True)
        return
    # 11-17: the clone model often stops mid-syllable on the last character (tail still voiced); an extra "。" makes it finish
    # the word and then go quiet - the surplus silence is trimmed below
    body = {"user": {"uid": "echo"}, "req_params": {"text": say_text(s["line"]) + "。", "speaker": spk,
                                                     "audio_params": {"format": "pcm", "sample_rate": 24000, "speech_rate": s.get("rate", 0)}}}
    if spk.startswith("S_"):  # clone 2.0: model_type MUST be inside the additions JSON string, else it silently runs clone 1.0
        ad = {"model_type": 4}
        if s.get("ctx"):
            ad["context_texts"] = [s["ctx"]]
        body["req_params"]["additions"] = json.dumps(ad, ensure_ascii=False)
    elif s["who"].startswith("配") and s.get("ctx"):  # stock 2.0 voices take the same request-style emotion hint
        body["req_params"]["additions"] = json.dumps({"context_texts": [s["ctx"]]}, ensure_ascii=False)
    for attempt in range(3):
        r = requests.post("https://openspeech.bytedance.com/api/v3/tts/unidirectional", json=body, stream=True, timeout=180,
                          headers={"X-Api-Key": APIKEY_NEW if (rid == "seed-tts-2.0" and APIKEY_NEW) else APIKEY, "X-Api-Request-Id": str(uuid.uuid4()), "X-Api-Resource-Id": rid, "Content-Type": "application/json"})
        audio, bad = b"", ""
        for line in r.iter_lines():
            if not line:
                continue
            try:
                j = json.loads(line)
            except ValueError:
                continue
            if j.get("data"):
                audio += base64.b64decode(j["data"])
            elif j.get("code") not in (0, 20000000):
                bad = str(j)[:200]
        if audio:
            # 11-17: mp3 streams lost the last frames -> the final syllable was clipped ("金色" ended on "金"); use raw PCM,
            # reject a take whose last 120 ms is still voiced (cut mid-syllable), and add 0.3 s of clean tail
            import numpy as np, wave
            x = np.frombuffer(audio[:len(audio) // 2 * 2], np.int16).astype(np.float32)
            tail = 20 * np.log10(np.sqrt((x[-2880:] ** 2).mean()) / 32768 + 1e-9) if len(x) > 2880 else -99
            if tail > -34 and attempt < 2:
                print("TTS CUT-TAIL retry", s["id"], f"{tail:.0f} dB", flush=True)
                continue
            hop = 240; n = len(x) // hop
            e = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) / 32768 + 1e-9)
            v = np.where(e > -42)[0]
            if len(v):
                x = x[:min(len(x), (v[-1] + 25) * hop)]  # keep 0.25 s of natural decay after the last voiced 10 ms
                x[-1200:] *= np.linspace(1, 0, 1200)
            y = np.concatenate([x, np.zeros(7200, np.float32)]).astype(np.int16)
            with wave.open(str(out), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(y.tobytes())
            if tail > -34:
                print("TTS CUT-TAIL kept", s["id"], f"{tail:.0f} dB", flush=True)
            return
    print("TTS FAIL", s["id"], bad, flush=True)


# ------------------------------------------------------------------ video
def subs_for(text, t0, dur):
    """Split a line at punctuation into subtitle chunks timed by character share."""
    parts = [p for p in re.split(r"(?<=[，。！？；：])", text) if p.strip()]
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) > 22 and cur:
            chunks.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        chunks.append(cur)
    total = sum(len(c) for c in chunks) or 1
    out, t = [], t0
    for c in chunks:
        d = dur * len(c) / total
        out.append((t, t + d, c.rstrip("，。；：")))
        t += d
    return out


def srt_time(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h:02d}:{m:02d}:{t % 60:06.3f}".replace(".", ",")


def clip_segment(i, s):
    _, e, a, b, mode = s["pic"].split(":")
    dur = float(b) - float(a)
    out = work / "seg" / f"{i:03d}.mkv"
    src = str(ep / "drama" / "eps" / f"e{int(e):02d}.mp4")
    vf = (f"[0:v]fps={FPS},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,eq=brightness=-0.12[bg];"
          f"[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p,fade=t=in:d=0.6,fade=t=out:st={dur - 0.8:.3f}:d=0.8[v]")
    if mode == "orig":
        ain = []
        af = f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-18:TP=-2,aresample=48000,afade=t=in:d=0.6,afade=t=out:st={dur - 0.8:.3f}:d=0.8[a]"
    elif mode in BGM:  # the music itself is this clip's sound (drama audio muted)
        f, ss, vol = BGM[mode][:3]
        ain = ["-ss", str(ss), "-i", str(ep / "bgm" / f)]
        af = (f"[1:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-19:TP=-2,aresample=48000,"
              f"volume={vol:.2f},afade=t=in:d=2:curve=qsin,afade=t=out:st={dur - 2:.3f}:d=2:curve=qsin[a]")
    else:
        ain = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        af = "[1:a]anull[a]"
    run(["ffmpeg", "-y", "-v", "error", "-ss", a, "-t", f"{dur:.3f}", "-i", src, *ain, "-filter_complex", vf + ";" + af,
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "pcm_s16le", str(out)])
    return out, dur


NOW_VF = (f"fps={FPS},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,eq=brightness=-0.12[bg];"
          f"[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0")
# memory look: full screen (drops burned-in subtitles and logo), faded warm colours, vignette
FLASH_VF = (f"fps={FPS},crop=iw-40:ih*0.74:20:ih*0.10,scale={W}:{H},eq=saturation=0.55:contrast=0.92:brightness=0.03,"
            "colorbalance=rs=0.08:gs=0.03:bs=-0.08:rm=0.05:bm=-0.05,vignette=PI/4")


def mont_segment(i, s):
    M = MONT[s["pic"].split(":")[1]]
    X, parts, durs = M["xfade"], [], []
    for j, (e, a, b, style) in enumerate(M["pieces"]):
        out = work / "seg" / f"{i:03d}_p{j:02d}.mkv"
        d = b - a
        vf = (NOW_VF if style == "now" else FLASH_VF) + ",format=yuv420p,settb=AVTB[v]"
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-t", f"{d:.3f}", "-i", str(ep / "drama" / "eps" / f"e{int(e):02d}.mp4"),
             "-filter_complex", "[0:v]" + vf, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
        parts.append(out)
        durs.append(d)
    total = sum(durs) - X * (len(durs) - 1)
    fl, last, cum = [], "[0:v]", 0.0
    for k in range(1, len(parts)):
        cum += durs[k - 1]
        lab = f"[x{k}]"
        fl.append(f"{last}[{k}:v]xfade=transition=fade:duration={X}:offset={cum - k * X:.3f}{lab}")
        last = lab
    fl.append(f"{last}fade=t=in:d=0.8,fade=t=out:st={total - 1.2:.3f}:d=1.2[v]")
    f, ss, vol = BGM[M["music"]][:3]
    n = len(parts)
    # original drama dialogue windows [ep, a, b]: placed at their montage time, the song ducks under them
    starts = [sum(durs[:k]) - k * X for k in range(len(durs))]
    wins = []
    for e, oa, ob in M.get("orig", []):
        k = next(k for k, (pe, pa, pb, _) in enumerate(M["pieces"]) if pe == e and pa <= oa and ob <= pb)
        wins.append((e, oa, ob, starts[k] + oa - M["pieces"][k][1]))
    duck = "".join(f"*(1-0.75*max(0,min(1,min((t-{t0 - 1:.3f})/1,({t0 + ob - oa + 1.5:.3f}-t)/1.5))))" for e, oa, ob, t0 in wins)
    fl.append(f"[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-19:TP=-2,aresample=48000,"
              f"volume={vol:.2f},afade=t=in:d=2:curve=qsin,afade=t=out:st={total - 2:.3f}:d=2:curve=qsin"
              + (f",volume=volume='1{duck}':eval=frame" if wins else "") + ("[mu]" if wins else "[a]"))
    ins = [x for p in parts for x in ("-i", str(p))] + ["-ss", str(ss), "-i", str(ep / "bgm" / f)]
    for j, (e, oa, ob, t0) in enumerate(wins):
        ins += ["-ss", f"{oa:.3f}", "-t", f"{ob - oa:.3f}", "-i", str(ep / "drama" / "eps" / f"e{int(e):02d}.mp4")]
        fl.append(f"[{n + 1 + j}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2,aresample=48000,"
                  f"afade=t=in:d=0.3,afade=t=out:st={ob - oa - 0.5:.3f}:d=0.5,adelay={int(t0 * 1000)}|{int(t0 * 1000)},apad[o{j}]")
    if wins:
        fl.append("[mu]" + "".join(f"[o{j}]" for j in range(len(wins))) + f"amix=inputs={len(wins) + 1}:normalize=0:duration=first[a]")
    out = work / "seg" / f"{i:03d}.mkv"
    run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "pcm_s16le", str(out)])
    return out, total


STUDIO = ep / "studio"
ACC = json.loads((STUDIO / "accepted.json").read_text(encoding="utf-8")) if (STUDIO / "accepted.json").exists() else {}
QC = json.loads((STUDIO / "qc.json").read_text(encoding="utf-8")) if (STUDIO / "qc.json").exists() else {}


_TF = STUDIO / "tighten.json"
TIGHT = json.loads(_TF.read_text(encoding="utf-8")) if _TF.exists() and os.environ.get("TIGHTEN", "0") == "1" else {}  # default OFF: a cut inside a host take is a visible jump (卡顿, EP03 v3)
_TL = STUDIO / "tail.json"
TAIL = json.loads(_TL.read_text(encoding="utf-8")) if _TL.exists() else {}  # last spoken word end per take (speech-end from qc.json can clip a final 了)


RAMP_MAX, RAMP_EDGE, RAMP_CAP = 0.7, 0.15, float(os.environ.get("RAMP_CAP", "2.0"))  # 11-13 EP05: cap 1.6x (4x ramps looked like 卡顿 to the user); target gap 0.7 s
RAMP_LOG = {}
MATCH_KEEP, MATCH_TOL = 0.6, float(os.environ.get("MATCH_TOL", "0.8"))  # pause kept after a match cut (s); max look-alike difference vs median talking frame change
END_AT = {}  # per-take "end 0.5 s after the last word" overrides (EP04: none yet)
NO_RAMP = {"169_t1"}  # 11-18: soft "值得吗？" sits under the ramp's 12%-of-peak silence threshold -> was sped away; its pause is the scripted 稍停
ZOOM = {k: (1.25, 0.9, 0.12) for k in ("008b", "011b", "012b", "083b")}  # shot id -> (zoom, x, y): 2nd half of a split line came out at the 1st half's framing -> punch in so the cut reads as a camera change, not a jump (x/y = crop position 0..1)


def ramp_plan(src, a, b):
    """[(t0, t1, speed)] covering a..b: silent gaps > RAMP_MAX between words get their middle played fast.
    Speed is capped by motion so the ramp never moves faster than the person does while talking (no visible whip)."""
    # EP07: 720p takes carry fire crackle / room rumble under the pauses -> band-limit to speech before finding silences
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-af", "highpass=f=200,lowpass=f=4000", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float); n = len(x) // 160
    e = np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))
    i0, i1 = int(a * 100), min(n, int(b * 100))
    peak = np.percentile(e[i0:i1], 95)
    sm = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(e, 3, mode="edge"), 7), axis=1)
    loud = np.where(sm[i0:i1] >= 0.12 * peak)[0] + i0
    if len(loud) < 2:
        return [(a, b, 1.0)]
    Wm, Hm = 160, 90
    vr = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vf", f"crop=iw*0.46:ih*0.78:iw*0.34:ih*0.2,scale={Wm}:{Hm},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(vr, np.uint8).reshape(-1, Hm, Wm).astype(float)
    mot = np.abs(np.diff(fr, axis=0)).mean((1, 2))  # mot[f] = change from frame f to f+1 (24 fps); EP07: person region only - the flickering fireplace (left) vetoed every ramp
    tfr = lambda t0, t1: mot[max(0, int(t0 * 24)):max(int(t0 * 24) + 1, int(t1 * 24))]
    talk_max = float(tfr(loud[0] / 100, loud[-1] / 100).max())
    talk = np.percentile(tfr(loud[0] / 100, loud[-1] / 100), 95)  # ramped idle motion may reach the liveliest talking moments, not beyond
    gaps, j = [], loud[0]
    q = sm < 0.12 * peak
    while j < loud[-1]:
        if q[j]:
            r = j
            while r < loud[-1] and q[r]: r += 1
            if (r - j) / 100 > RAMP_MAX: gaps.append((j / 100, r / 100))
            j = r
        else: j += 1
    parts, x0, log = [], a, []
    talk_med = float(np.median(tfr(loud[0] / 100, loud[-1] / 100)))
    for g0, g1 in gaps:
        # 11-18 MATCH CUT (first choice): inside the silence find frames i < j that look the same (difference <= a typical talking
        # frame-to-frame change) and drop i+1..j-1 - Seedance often holds still / freezes in pauses, so the join is invisible
        lo, hi = int(np.ceil((g0 + 0.12) * 24)), int((g1 - 0.12) * 24)
        want_drop = int((g1 - g0 - MATCH_KEEP) * 24)
        best = None
        if want_drop >= 6 and os.environ.get("MATCH", "0") == "1":
            for i in range(lo, hi):
                for j in range(min(hi, i + 1 + want_drop), i + 6, -1):
                    dd = float(np.abs(fr[j] - fr[i]).mean())
                    if dd <= MATCH_TOL * talk_med:
                        if best is None or (j - i, -dd) > (best[1] - best[0], -best[2]): best = (i, j, dd)
                        break
        if best and (best[1] - best[0] - 1) >= 6:
            i, j, dd = best
            parts.append((x0, (i + 1) / 24, 1.0)); x0 = j / 24
            log.append(("CUT", round(g0, 2), round(g1 - g0, 2), round((j - i - 1) / 24, 2), round(dd / max(1e-3, talk_med), 2)))
            continue
        r0, r1 = g0 + RAMP_EDGE, g1 - RAMP_EDGE
        # 11-18: one sudden move (blink / head jerk) inside the pause used to veto the whole ramp (spike guard) -> pauses stayed
        # 1.3-1.7 s (user: 卡顿). Now the pause is split around such moves: they play 1x, the calm stretches between them ramp.
        f0, f1 = int(r0 * 24), int(r1 * 24)
        big = [f for f in range(f0, f1) if mot[f] > 0.5 * talk_max]
        subs, c0 = [], f0
        for f in big:
            if f - 1 > c0: subs.append((c0, f - 1))
            c0 = f + 2
        if f1 > c0: subs.append((c0, f1))
        need = (g1 - g0) - RAMP_MAX  # seconds to remove
        plan = []
        for u0, u1 in subs:
            if (u1 - u0) / 24 < 0.25: continue
            sm_ = mot[u0:u1]; gm = max(1e-3, float(sm_.mean()))
            sp = float(min(RAMP_CAP, max(1.0, talk / gm)))
            while sp >= 1.15 and len(sm_) > 1:
                w = max(1, int(np.ceil(sp)))
                if np.convolve(sm_, np.ones(w), "valid").max(initial=0) <= talk_max: break
                sp -= 0.1
            if sp >= 1.15: plan.append([u0 / 24, u1 / 24, sp])
        got = sum((t1 - t0) * (1 - 1 / sp) for t0, t1, sp in plan)
        if got > need and got > 0:  # more than enough: ease every piece toward 1x by the same factor
            k_ = need / got
            for q_ in plan:
                q_[2] = 1 / (1 - (1 - 1 / q_[2]) * k_)
        plan = [q_ for q_ in plan if q_[2] >= 1.1]
        if not plan:
            if os.environ.get("RAMP_DEBUG"): print("RAMP_SKIP", Path(src).stem, round(g0, 2), round(g1 - g0, 2), "subs", subs, flush=True)
            continue
        for t0, t1, sp in plan:
            parts += [(x0, t0, 1.0), (t0, t1, sp)]; x0 = t1
        newlen = (g1 - g0) - sum((t1 - t0) * (1 - 1 / sp) for t0, t1, sp in plan)
        log.append((round(g0, 2), round(g1 - g0, 2), [round(q_[2], 2) for q_ in plan], round(newlen, 2)))
    parts.append((x0, b, 1.0))
    RAMP_LOG[Path(src).stem] = log
    print("RAMP", Path(src).stem, "gap(start,len,speed,->len)", log, flush=True)
    return parts


def studio_segment(i, s):
    """Host shot: lip-synced to the approved TTS line (studio/ls/<id>.mp4, see ls_batch.py) - else accepted Seedance takes with their own voice."""
    ls = STUDIO / "ls" / f"{s['id']}.mp4"
    if ls.exists():
        d = probe(ls)
        out = work / "seg" / f"{i:03d}_ls.mkv"
        aud = STUDIO / "ls" / f"{s['id']}_aud.wav"  # the approved TTS line itself (picture from the lip-sync, sound untouched)
        d = probe(aud)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(ls), "-i", str(aud), "-filter_complex",
             f"[0:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration=1,format=yuv420p[v];"
             "[1:a]aresample=48000,aformat=channel_layouts=stereo,apad[a]",
             "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "pcm_s16le", str(out)])
        return out, d
    if os.environ.get("PREVIEW_TTS") == "1":  # storyboard preview: approved TTS voice over the generated picture (mouths synced later)
        dur = probe(tts_path(s)) + 0.25 + s.get("pad", 0.45)
        ins, chain = [], []
        for j, key in enumerate(ACC[s["id"]]):
            ins += ["-ss", f"{max(0.0, QC[key]['speech'][0] - 0.3):.3f}", "-i", str(STUDIO / "clips" / f"{key}.mp4")]
            chain.append(f"[{j}:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1[p{j}]")
        n = len(chain)
        vf = ";".join(chain) + ";" + "".join(f"[p{j}]" for j in range(n)) + f"concat=n={n}:v=1:a=0,tpad=stop_mode=clone:stop_duration=15,format=yuv420p[v]"
        out = work / "seg" / f"{i:03d}_pv.mkv"
        run(["ffmpeg", "-y", "-v", "error", *ins, "-i", str(tts_path(s)), "-filter_complex",
             vf + f";[{n}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=250|250,apad[a]",
             "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "pcm_s16le", str(out)])
        return out, dur
    takes, outs, total = ACC[s["id"]], [], 0.0
    for j, key in enumerate(takes):
        src = STUDIO / "clips" / f"{key}.mp4"
        q, cd = QC[key], probe(src)
        _vd = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip()
        if _vd: cd = min(cd, float(_vd) - 1 / 24)  # 11-18: Seedance audio runs ~0.1-0.2 s past the last picture frame - trimming to the container end froze the tail
        a = max(0.0, q["speech"][0] - 0.3)
        b = min(cd, max(q["speech"][1], TAIL.get(key, 0)) + (s.get("pad", 0.45) if j == len(takes) - 1 else 0.25))
        b = min(b, END_AT.get(key, b))
        if os.environ.get("TAILFIX", "1") == "1" and j == len(takes) - 1:  # EP08: after the last word Seedance often sits dead still -> a 0.8-1.2 s frozen-looking tail; end 0.2 s into the stillness
            e0 = q["speech"][1] + 0.3
            if b > e0 + 0.3:
                vr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{e0:.3f}", "-t", f"{b - e0:.3f}", "-i", str(src), "-vf", "scale=192:108,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
                fr_ = np.frombuffer(vr, np.uint8).reshape(-1, 108, 192).astype(np.float32)
                if len(fr_) > 6:
                    dd_ = np.abs(np.diff(fr_, axis=0)).mean((1, 2))
                    for f_ in range(len(dd_) - 5):
                        if (dd_[f_:f_ + 6] < 0.2).all():  # near-still (breathing only): on a quiet set (no fire flicker) a held pose reads as a frozen frame
                            nb = e0 + f_ / 24 + 0.2
                            if nb < b - 0.1:
                                print("TAILFIX", key, f"{b:.2f}->{nb:.2f}", flush=True); b = nb
                            break
        # RAMP (default on): speech stays 1x (lip-sync untouched); only the middle of long silent gaps plays fast, so a 1-2 s
        # "staring" pause becomes ~0.55 s WITHOUT a jump cut (every frame still in order). CONFORM: Seedance is 24 fps, the film 25 -
        # fps=25 would repeat one frame per second (micro-hitch); play the take 25/24 faster instead (atempo keeps pitch).
        parts = ramp_plan(src, a, b) if os.environ.get("RAMP", "1") == "1" and key not in NO_RAMP else [(a, b, 1.0)]
        g24 = lambda t: round(t * 24) / 24  # piece edges on the 24 fps frame grid: off-grid edges left up-to-1-frame holes that concat filled with a repeated frame
        parts = [(g24(t0), g24(t1), sp) for t0, t1, sp in parts if g24(t1) > g24(t0)]
        k = (FPS / 24.0) if os.environ.get("CONFORM", "1") == "1" else 1.0
        d = sum((t1 - t0) / sp for t0, t1, sp in parts) / k
        n = len(parts)
        fo = 0.06 if b >= cd - 0.05 else 0.2  # take ends mid-word (013 "呀"): keep the last syllable audible
        pre = ""
        for m, (t0, t1, sp) in enumerate(parts):
            lo = (t1 - t0) / sp  # output length of this piece (before conform)
            pre += f"[0:v]trim=start={t0:.4f}:end={t1:.4f},setpts=(PTS-STARTPTS)/{sp:.5f}[v{m}];"  # 11-18: conform (k) is applied AFTER concat - per-piece /k made each video piece 4% shorter than its audio piece and concat padded the gap with a frozen frame (0.2-0.3 s stall at every ramp = 卡顿)
            # silent gap: keep its first `lo` seconds of room tone (no speech inside by construction)
            pre += (f"[0:a]atrim=start={t0:.4f}:end={t0 + lo:.4f},asetpts=PTS-STARTPTS,"
                    f"afade=t=in:d=0.012,afade=t=out:st={max(0, lo - 0.012):.4f}:d=0.012[a{m}];")
        pre += "".join(f"[v{m}][a{m}]" for m in range(n)) + f"concat=n={n}:v=1:a=1[cv0][ca0];[cv0]setpts=PTS/{k:.6f}[cv];"
        pre += f"[ca0]atempo={k:.6f}[ca];" if k != 1.0 else "[ca0]anull[ca];"
        z = ZOOM.get(s["id"]); zc = f"crop=iw/{z[0]}:ih/{z[0]}:(iw-iw/{z[0]})*{z[1]}:(ih-ih/{z[0]})*{z[2]}," if z else ""
        out = work / "seg" / f"{i:03d}_s{j}.mkv"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex",
             pre + f"[cv]fps={FPS},{zc}scale={W}:{H}:flags=lanczos,format=yuv420p[v];"
             f"[ca]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,volume={-17.5 - loud_i(src, a, b - a):.2f}dB,alimiter=limit=0.708:attack=3:release=60:level=0,aresample=48000,afade=t=in:d=0.15,"
             f"afade=t=out:st={max(0, d - fo):.3f}:d={fo},apad[a]",
             "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-c:a", "pcm_s16le", str(out)])
        outs.append(out)
        total += d
    if len(outs) == 1:
        return outs[0], total
    out = work / "seg" / f"{i:03d}.mkv"
    lst = work / "seg" / f"{i:03d}_list.txt"
    lst.write_text("\n".join(f"file '{o.as_posix()}'" for o in outs), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    return out, total


DRAMA_VF = "crop=iw-40:ih*0.665:20:ih*0.135"  # drop the drama's burned-in subtitles (>=82% height) and CCTV logo (<=13%)
FOOT_INNER = "crop=iw*0.90:ih*0.76:iw*0.05:ih*0.11"  # inside the real picture: drop channel logos (top/corners) and burned-in captions (bottom)
_CD = {}


def foot_vf(src, t):
    """Real picture area of a web video (cropdetect around t; removes letterbox/pillarbox), then the logo/caption-safe inner crop."""
    key = (str(src), int(t) // 30)
    if key not in _CD:
        r = subprocess.run(["ffmpeg", "-v", "info", "-ss", f"{max(0, t):.1f}", "-t", "6", "-i", str(src), "-vf", "cropdetect=limit=24:round=2:reset=0",
                            "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
        found = re.findall(r"crop=(\d+:\d+:\d+:\d+)", r)
        _CD[key] = f"crop={found[-1]}," if found else ""
    return _CD[key] + CROPS.get(Path(src).stem, FOOT_INNER)


def shot_vf(s, src, t):
    """per-shot crop override (s["crop"], e.g. one half of a split-screen news shot) after the letterbox cropdetect; else the per-source crop"""
    v = foot_vf(src, t)
    return (v.rsplit("crop=", 1)[0] + s["crop"]) if s.get("crop") else v


USE = {  # usable ranges per source (contact-sheet review -> footage_review.json)
}
CLEAN = "crop=iw*0.96:ih*0.92:iw*0.02:ih*0.04"
CHY20 = "crop=iw*0.86:ih*0.66:iw*0.07:ih*0.09"      # chyron / captions on the bottom ~20%
CHY25 = "crop=iw*0.84:ih*0.60:iw*0.08:ih*0.10"      # big chyron + ticker on the bottom ~25%
SIGN = "crop=iw*0.76:ih*0.68:iw*0.04:ih*0.08"       # sign-language inset bottom-right
TOPLOGO = "crop=iw*0.86:ih*0.80:iw*0.05:ih*0.14"   # logo / watermark top-right + some bottom text
CROPS = {}  # per-source crops (contact-sheet review)
FOOT_INNER = CLEAN

_RV = ep / "footage_review.json"  # EP05: per-shot footage windows, usable ranges and crops from the contact-sheet review
if _RV.exists():
    _rv = json.loads(_RV.read_text(encoding="utf-8"))
    _PRESET = {"CLEAN": CLEAN, "CHY20": CHY20, "CHY25": CHY25, "SIGN": SIGN, "TOPLOGO": TOPLOGO}
    for _k, _v in _rv.get("use", {}).items():
        USE.setdefault(_k, tuple(_v))
    for _k, _v in _rv.get("crops", {}).items():
        CROPS.setdefault(_k, _PRESET.get(_v, _v))
    for _s in SHOTS:
        _r = _rv.get("shots", {}).get(_s["id"])
        if _r and _s["pic"].startswith("f:") and _s["pic"].endswith(":auto") and not _s.get("keep_pic"):
            _s["pic"] = f"f:footage/{_r['key']}.mp4:{_r['t']}"

FOOT_OVR = {  # sources whose logos sit lower / further in
    "djy_aerial2.mp4": "crop=iw*0.84:ih*0.68:iw*0.12:ih*0.19",
    "vox_whc_fan.mp4": "crop=iw*0.88:ih*0.68:iw*0.06:ih*0.21",
    "vox_bjjt_csb2026.mp4": "crop=iw*0.76:ih*0.66:iw*0.12:ih*0.13",
}


FOOT_VF = FOOT_INNER
WIN = {}  # shot id -> (source, start, duration) for moving footage shots


def shot_dur(s):
    if s.get("hold"):
        return float(s["hold"])
    if s["line"] and s["who"] != "无":
        return probe(voice(s)) + 0.25 + s.get("pad", 0.45)
    return 6.0 if s["line"] else 3.5


def plan_windows():
    """Moving footage for d:EP:SEC (94版) and f:FILE:SEC (other footage): the window starts a little before the chosen moment;
    windows never reuse seconds already shown by an earlier shot from the same source."""
    used = {}
    for s in SHOTS:
        kind, _, rest = s["pic"].partition(":")
        if kind not in ("d", "f"):
            continue
        src_, t = rest.rsplit(":", 1)
        src = ep / "drama" / "eps" / f"e{int(src_):02d}.mp4" if kind == "d" else ep / src_
        if not src.exists():
            print("MISSING footage", src.name, "for", s["id"], flush=True)
            continue
        d = shot_dur(s)
        lo, hi = USE.get(src.stem, (2.0, probe(src) - 0.5))
        if t == "auto":  # next unused stretch of this source inside its usable range
            prev = used.get(src, [])
            t = max([b for _, b in prev] + [lo])
            if t + d > hi:  # ran out: wrap to the start of the range
                t = lo
        t = float(t)
        a = t if (s.get("card") or "breath" in s) else max(0.0, t - min(1.5, d * 0.2))
        for ua, ub in ([] if (s.get("again") or "breath" in s) else used.get(src, [])):  # again=True: a deliberate retelling may show the same moment again
            if a < ub and a + d > ua:
                a = ub
        if not s.get("card") and not s.get("again") and "breath" not in s and a + d > hi + 1.0 and t != lo:  # pushed out of the usable range: reuse from its start
            a = lo
        if not s.get("card"):  # a card holds a single frame, so its window may run past the end of the source
            a = min(a, max(0.0, probe(src) - d - 0.1))
        used.setdefault(src, []).append((a, a + d))
        WIN[s["id"]] = (src, a, d)


def card_vf(s, dur):
    """Centred card text (s["card"] = list of lines): each line fades in 1.2 s after the previous, all fade out at the end."""
    lines = s["card"]
    fs, gap = 64, 44
    y0 = (H - (len(lines) * fs + (len(lines) - 1) * gap)) // 2
    out = [f"eq=brightness=-0.10:saturation=0.85"]
    for k, t in enumerate(lines):
        tf = work / "seg" / f"card_{s['id']}_{k}.txt"
        tf.write_text(t, encoding="utf-8")
        t0 = 0.8 + 1.2 * k
        alpha = f"if(lt(t,{t0}),0,if(lt(t,{t0 + 1.0}),(t-{t0})/1.0,if(gt(t,{dur - 1.5}),max(0,({dur}-t)/1.5),1)))"
        tfe = tf.as_posix().replace(":", "\\:")
        font = "simkai.ttf" if any("\u4e00" <= c <= "\u9fff" for c in t) else "georgiai.ttf"  # Latin line (e.g. Spanish quote): simkai has no ñ and spaces Latin letters oddly
        out.append(f"drawtext=fontfile='C\\:/Windows/Fonts/{font}':textfile='{tfe}':"
                   f"fontsize={fs + (14 if k == 0 else 0)}:fontcolor=0xF0E2C0:borderw=2:bordercolor=0x000000@0.6:"
                   f"x=(w-text_w)/2:y={y0 + k * (fs + gap)}:alpha='{alpha}'")
    return ",".join(out)


def motion_segment(i, s):
    src, a, dur = WIN[s["id"]]
    out = work / "seg" / f"{i:03d}.mkv"
    crop = DRAMA_VF + "," if s["pic"].startswith("d:") else foot_vf(src, a) + ","
    card = "," + card_vf(s, dur) if s.get("card") else ""
    if s.get("cap"):
        tf = work / "seg" / f"cap_{s['id']}.txt"
        tf.write_text(s["cap"], encoding="utf-8")
        tfe = tf.as_posix().replace(":", "\\:")
        card += (f",drawtext=fontfile='C\\:/Windows/Fonts/simkai.ttf':textfile='{tfe}':fontsize=40:fontcolor=0xF0E2C0:borderw=2:bordercolor=0x000000@0.6:"
                 f"x=70:y=h-130:alpha='if(lt(t,0.6),0,if(lt(t,1.6),t-0.6,if(gt(t,{dur - 1.2:.2f}),max(0,({dur:.2f}-t)/1.2),1)))'")
    if "breath" in s:  # 留白: no narration, the footage's own sound (crowd / pitch) at s["breath"], music swells over it
        ain = []
        af = (f"[0:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-2,aresample=48000,"
              f"volume={float(s['breath']):.2f},afade=t=in:d=0.5,afade=t=out:st={max(0, dur - 0.8):.3f}:d=0.8,apad[a]")
    elif s["line"] and s["who"] != "无":
        ain = ["-i", str(voice(s))]
        af = "[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=250|250,apad[a]"
    else:
        ain = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        af = "[1:a]anull[a]"
    if "breath" in s and float(s["breath"]) <= 0:
        ain, af = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"], "[1:a]anull[a]"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", str(src), *ain, "-filter_complex",
         f"[0:v]{'trim=end_frame=1,loop=loop=-1:size=1:start=0,setpts=N/' + str(FPS) + '/TB,' if s.get('card') else ''}"  # card: hold one frame
         f"{crop}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,"
         f"tpad=stop_mode=clone:stop_duration=2{card},format=yuv420p[v];{af}",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-c:a", "pcm_s16le", str(out)])
    return out, dur


def _orig_span(s):
    if s["pic"].startswith(("fc:", "fa:")):
        x = s["pic"].split(":")
        return x[1], float(x[2]), float(x[3])
    return None


def cont_flags(s):
    """(joined_in, joined_out): neighbour shot plays the same original file right before/after -> no fade at that seam (fades = audible dips)."""
    k = next(j for j, x in enumerate(SHOTS) if x["id"] == s["id"])
    me = _orig_span(s)
    pv = _orig_span(SHOTS[k - 1]) if k > 0 else None
    nx = _orig_span(SHOTS[k + 1]) if k + 1 < len(SHOTS) else None
    jin = bool(pv and pv[0] == me[0] and abs(pv[2] - me[1]) < 0.05)
    jout = bool(nx and nx[0] == me[0] and abs(me[2] - nx[1]) < 0.05)
    return jin, jout


def joined_span(s):
    """(a, dur) over the run of neighbour shots that play the same original file back to back -> one gain for the whole run (no level jump at the seams)."""
    k = next(j for j, x in enumerate(SHOTS) if x["id"] == s["id"])
    f, a, b = _orig_span(s)
    lo = k
    while lo > 0 and (p := _orig_span(SHOTS[lo - 1])) and p[0] == f and abs(p[2] - _orig_span(SHOTS[lo])[1]) < 0.05:
        lo -= 1
    hi = k
    while hi + 1 < len(SHOTS) and (n := _orig_span(SHOTS[hi + 1])) and n[0] == f and abs(_orig_span(SHOTS[hi])[2] - n[1]) < 0.05:
        hi += 1
    a0, b0 = _orig_span(SHOTS[lo])[1], _orig_span(SHOTS[hi])[2]
    return a0, b0 - a0


def fade_vf(s, dur):
    jin, jout = cont_flags(s)
    v = ("" if jin else "fade=t=in:d=0.4,") + ("" if jout else f"fade=t=out:st={dur - 0.5:.3f}:d=0.5,")
    a = ("" if jin else "afade=t=in:d=0.3,") + ("" if jout else f"afade=t=out:st={dur - 0.5:.3f}:d=0.5,")
    return v, a


DUB_LEAD = 1.0  # original voice heard alone this long, then ducked under the Mandarin dub


def fd_segment(i, s):
    """Foreign original, dubbed: the speaker's own picture from [a, ...]; his voice ~1 s alone, then ducked to -20 dB under the Mandarin dub
    (EP07 v2, user 11-20: keep few English/Spanish originals, and dub the ones kept). Runs past b if the dub is longer than the span."""
    _, f, a, b = s["pic"].split(":")
    v = voice(s)
    dv = probe(v)
    dur = DUB_LEAD + dv + 1.0  # ends ~1 s after the dub (the original span is only where his words start; a longer span would trail on ducked speech)
    out = work / "seg" / f"{i:03d}.mkv"
    duck = f"volume='if(lt(t,{DUB_LEAD - 0.25:.2f}),1,if(lt(t,{DUB_LEAD + 0.25:.2f}),1-0.9*(t-{DUB_LEAD - 0.25:.2f})/0.5,0.1))':eval=frame"
    run(["ffmpeg", "-y", "-v", "error", "-ss", a, "-t", f"{dur:.3f}", "-i", str(ep / f), "-i", str(v), "-filter_complex",
         f"[0:v]{shot_vf(s, ep / f, float(a))},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,"
         f"fade=t=in:d=0.4,fade=t=out:st={dur - 0.5:.3f}:d=0.5,format=yuv420p[v];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{fixgain(ep / f, float(a), float(b) - float(a), -17)}{duck},"
         f"afade=t=in:d=0.3,afade=t=out:st={dur - 0.5:.3f}:d=0.5,apad[o];"
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(DUB_LEAD * 1000)}|{int(DUB_LEAD * 1000)},apad[d];"
         f"[o][d]amix=inputs=2:normalize=0:duration=longest[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-c:a", "pcm_s16le", str(out)])
    return out, dur


def fc_segment(i, s):
    """Modern voice clip (interview / lecture / visitor) with its ORIGINAL sound; source captions cropped away, ours are shown."""
    _, f, a, b = s["pic"].split(":")
    dur = float(b) - float(a)
    fv, fa = fade_vf(s, dur)
    out = work / "seg" / f"{i:03d}.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-ss", a, "-t", f"{dur:.3f}", "-i", str(ep / f), "-filter_complex",
         f"[0:v]{shot_vf(s, ep / f, float(a))},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,"
         f"{fv}format=yuv420p[v];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{fixgain(ep / f, *joined_span(s), -17)}aresample=48000,"
         f"{fa}apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-c:a", "pcm_s16le", str(out)])
    return out, dur


def fa_segment(i, s):
    """Original sound whose own picture is a still/photo: audio from file A [a,b], picture = moving footage from file V at vt."""
    _, f, a, b, vf, vt = s["pic"].split(":")
    dur = float(b) - float(a)
    fv, fa = fade_vf(s, dur)
    out = work / "seg" / f"{i:03d}.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-ss", vt, "-t", f"{dur:.3f}", "-i", str(ep / vf), "-ss", a, "-t", f"{dur:.3f}", "-i", str(ep / f), "-filter_complex",
         f"[0:v]{shot_vf(s, ep / vf, float(vt))},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,"
         f"{fv}format=yuv420p[v];"
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,{fixgain(ep / f, *joined_span(s), -17)}aresample=48000,"
         f"{fa}apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-c:a", "pcm_s16le", str(out)])
    return out, dur


EP02 = ep.parent / "echo_ep02"
_POOL, _PK = {}, {}


def host_pool():
    """EP02 accepted Seedance takes grouped by (who, cam/side) - preview placeholders for EP03 host shots."""
    if not _POOL:
        acc = json.loads((EP02 / "studio" / "accepted.json").read_text(encoding="utf-8"))
        for s2 in json.loads((EP02 / "script_v4.json").read_text(encoding="utf-8"))["shots"]:
            if s2["id"] in acc and s2["pic"].startswith("img:st_"):
                key = (s2["who"], "cam" if s2["pic"].endswith("_cam") else "side")
                _POOL.setdefault(key, []).extend(EP02 / "studio" / "clips" / f"{k}.mp4" for k in acc[s2["id"]])
    return _POOL


LOOK = {"老渡": ep / "look" / "lookclip_ld_t1_last.png", "小柚": ep / "look" / "lookclip_xy_t1_last.png"}  # EP07 look (11-18, Andes mountain hut): set + outfit stills as preview placeholders


def host_placeholder(i, s):
    dur = probe(tts_path(s)) + 0.25 + s.get("pad", 0.45)
    out = work / "seg" / f"{i:03d}.mkv"
    lab = (work / "seg" / "label.txt"); lab.write_text("主持人镜头 · 本期造型占位（正片由 Seedance 拍摄出镜）", encoding="utf-8")
    lf = lab.as_posix().replace(":", "\\:")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(LOOK[s["who"]]), "-i", str(tts_path(s)), "-filter_complex",
         f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
         f"drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':textfile='{lf}':fontsize=26:fontcolor=white@0.85:box=1:boxcolor=black@0.45:boxborderw=10:x=40:y=40,"
         "format=yuv420p[v];[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=250|250,apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "20", "-c:a", "pcm_s16le", str(out)])
    return out, dur


def segment(i, s):
    if s["pic"].startswith("img:st_") and s["id"] not in ACC:
        return host_placeholder(i, s)
    if s["pic"].startswith("mont:"):
        return mont_segment(i, s)
    if s["pic"].startswith("clip:"):
        return clip_segment(i, s)
    if s["pic"].startswith("fd:"):
        return fd_segment(i, s)
    if s["pic"].startswith("fc:"):
        return fc_segment(i, s)
    if s["pic"].startswith("fa:"):
        return fa_segment(i, s)
    if s["id"] in ACC:
        return studio_segment(i, s)
    if s["id"] in WIN:
        return motion_segment(i, s)
    out = work / "seg" / f"{i:03d}.mp4"
    pic = pic_path(s)
    if s["line"] and s["who"] != "无":
        a = voice(s)
        dur = probe(a) + 0.25 + s.get("pad", 0.45)
        ain = ["-i", str(a)]
        af = "[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=250|250,apad[a]"
    else:
        dur = 6.0 if s["line"] else 3.5
        ain = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        af = "[1:a]anull[a]"
    fr = int(dur * FPS) + 1
    zoom = f"scale=3840:2160,zoompan=z='1+0.06*on/{fr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps={FPS}"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(pic), *ain, "-filter_complex",
         f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{zoom},format=yuv420p[v];{af}",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "pcm_s16le", str(out).replace(".mp4", ".mkv")])
    return Path(str(out).replace(".mp4", ".mkv")), dur


def build_after_fit(L):
    """Last music bed (after 诸葛亮's death to the end), exactly L s long: 送别 (full) -> 说了再见 (trimmed to fit) -> 送别 (full),
    the final 送别 ending naturally at L. If there is no room for 说了再见, the first 送别 is shortened instead."""
    A, B, X = ep / "bgm" / "songbie_piano.wav", ep / "bgm" / "shuolezaijian_piano.wav", 5.0
    A1, A2 = 214.0, probe(A)
    norm = "aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-3,aresample=48000"
    out = ep / "bgm" / "after_fit.wav"
    Bp = L - A1 - A2 + 2 * X
    if Bp >= 40:
        fl = (f"[0:a]atrim=0:{A1},{norm}[a1];[1:a]atrim={12}:{12 + Bp:.3f},asetpts=PTS-STARTPTS,{norm}[b];[2:a]{norm}[a2];"
              f"[a1][b]acrossfade=d={X}:c1=qsin:c2=qsin[ab];[ab][a2]acrossfade=d={X}:c1=qsin:c2=qsin[o]")
        ins = ["-i", str(A), "-i", str(B), "-i", str(A)]
    else:
        a1 = max(30.0, L - A2 + X)
        fl = f"[0:a]atrim=0:{a1:.3f},{norm}[a1];[1:a]{norm}[a2];[a1][a2]acrossfade=d={X}:c1=qsin:c2=qsin[o]"
        ins = ["-i", str(A), "-i", str(A)]
    run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fl, "-map", "[o]", "-ar", "48000", "-ac", "2", str(out)])
    print(f"after_fit: L={L:.1f}s 说了再见 part {max(0, Bp):.1f}s -> {probe(out):.1f}s", flush=True)
    return out


def video():
    # final film: every host shot must be a generated studio take - never the old stills (st_xy.png shows 小柚 sunk into the armchair)
    left = [s["id"] for s in SHOTS if (s["pic"].startswith("img:st_") and s["id"] not in ACC) or s["pic"].startswith(("ai:", "img:v_"))]
    left = [x for x in left if not x.startswith("img")] if False else [s["id"] for s in SHOTS if s["pic"].startswith(("ai:", "img:v_"))]
    if left and os.environ.get("ALLOW_STILLS") != "1":
        raise SystemExit(f"shots still on old stills / AI pictures: {left}")
    plan_windows()
    only = set(filter(None, os.environ.get("ONLY", "").split(",")))  # ONLY=049,124 : re-render these, reuse the other segments as they are

    def seg_or_reuse(i, s):
        if only and s["id"] not in only and s["id"] not in ACC:  # host shots are always rebuilt from the accepted takes (cheap; never reuse stale lip-sync segments)
            p = work / "seg" / f"{i:03d}.mkv"
            if p.exists():
                return p, probe(p)
        return segment(i, s)
    with ThreadPoolExecutor(6) as pool:
        segs = list(pool.map(lambda a: seg_or_reuse(*a), list(enumerate(SHOTS, 1))))
    # timeline, subtitles, bgm sections
    # cover = first 2.5 s of the film (a normal segment, so the final encode stays a single-input job)
    cover, CV = ep / "cover" / f"EP{EPN}_cover.jpg", 2.5
    cseg = work / "seg" / "000_cover.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-framerate", f"{FPS}", "-loop", "1", "-t", f"{CV}", "-i", str(cover), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[v]", "-map", "[v]", "-map", "1:a", "-t", f"{CV}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le", str(cseg)])
    t, srt, k, sections, solo = CV, [], 1, [], []
    segs = [(p, probe(p)) for p, _ in segs]  # real container length = what the concat timeline uses
    for (p, d), s in zip(segs, SHOTS):
        if s["line"] and not s.get("card"):
            sub0, subd = (t + DUB_LEAD, probe(globals()["voice"](s))) if s["pic"].startswith("fd:") else (t + 0.25, d - 0.6)
            for a, b, c in subs_for(s["line"], sub0, subd):
                srt.append(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n")
                k += 1
        if s["pic"].endswith(":mute") or "breath" in s:
            solo.append((t, t + d))
        if sections and sections[-1][0] == s["bgm"] and not s.get("newbed"):
            sections[-1][2] = t + d
        else:
            sections.append([s["bgm"], t, t + d, None])
        if s.get("hit") and sections[-1][3] is None:
            sections[-1][3] = t
        t += d
    total = t
    (work / "subs.srt").write_text("\n".join(srt), encoding="utf-8")
    (work / "concat.txt").write_text("\n".join(f"file '{p.as_posix()}'" for p in [cseg] + [p for p, _ in segs]), encoding="utf-8")
    joined = work / "joined.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(work / "concat.txt"), "-c", "copy", str(joined)])
    # music bed: each section's track from its start offset, 3 s soft fades, overlapping edges
    # 11-14: the bed is assembled in numpy (the old chain of per-frame volume expressions went NaN -> silent gaps, bed cut short)
    SR = 48000
    N = int(total * SR) + SR
    bed = np.zeros((N, 2), np.float32)
    for n, (key, a, b, th) in enumerate(s for s in sections if BGM[s[0]][0]):
        f, ss, vol = BGM[key][:3]
        opt = BGM[key][3] if len(BGM[key]) > 3 else {}
        fin = opt.get("fin", 3)
        a2 = max(0.0, a - 1.5) if fin >= 1 else a  # hard entries (fin < 1) start exactly on the cut
        ln = min((b + 2.0), total) - a2
        if th is not None and "hit" in opt:  # this music moment lands on the hit shot
            ss = max(0.0, opt["hit"] - (th - a2))
            print(f"BED {key}: hit {opt['hit']}s at film {th:.1f}s -> start {ss:.1f}s", flush=True)
        src = ep / "bgm" / f
        if b >= total - 0.01 and probe(src) >= ln + 1.0:  # last bed: start late so the piece reaches its own ending with the film
            ss = max(0.0, probe(src) - ln - 0.3)
            inp, tail = ["-ss", f"{ss:.3f}", "-i", str(src)], f"apad,afade=t=out:st={ln - 1.2:.3f}:d=1.2"
        else:
            inp, tail = ["-ss", str(ss), "-stream_loop", "-1", "-i", str(src)], f"afade=t=out:st={ln - 3.5:.3f}:d=3.5:curve=qsin"
        bf = work / "seg" / f"bed_{n:02d}.wav"
        run(["ffmpeg", "-y", "-v", "error", *inp, "-af",
             f"atrim=0:{ln:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-3,aresample=48000,"
             f"volume={vol:.2f},afade=t=in:d={fin}:curve=qsin,{tail},atrim=0:{ln:.3f}", "-ar", "48000", "-ac", "2", "-f", "s16le", str(bf)])
        x = np.frombuffer(bf.read_bytes(), np.int16).reshape(-1, 2).astype(np.float32) / 32768
        k0 = int(a2 * SR)
        m = min(len(x), N - k0)
        bed[k0:k0 + m] += x[:m]
        print(f"BED {n:02d} {key:10s} {a2:7.1f}-{a2 + ln:7.1f} from {ss:.1f}s", flush=True)
    # 留白 windows (adjacent ones merged): music up ~+8 dB with 2 s ramps; the pitch sound in them does not duck the music
    win = []
    for a, b in sorted(solo):
        if win and a - win[-1][1] < 0.5:
            win[-1][1] = max(win[-1][1], b)
        else:
            win.append([a, b])
    g = np.ones(N, np.float32)
    for a, b in win:
        k0, k1 = max(0, int((a - 2) * SR)), min(N, int((b + 2) * SR))
        seg = np.arange(k0, k1, dtype=np.float64) / SR
        ramp = np.clip(np.minimum((seg - (a - 1.0)) / 2.0, ((b + 1.0) - seg) / 2.0), 0, 1)
        g[k0:k1] = np.maximum(g[k0:k1], 1 + 2.4 * ramp)
    bed *= (0.55 * g)[:, None]
    bedf = work / "bed.wav"
    np.clip(bed[:int(total * SR)] * 32767, -32768, 32767).astype(np.int16).tofile(work / "bed.raw")
    del bed
    run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i", str(work / "bed.raw"), str(bedf)])
    # sidechain key = the film's own sound with the 留白 windows silenced
    # 11-18: the voice track was read from joined.mkv through aresample=async=1 - every time the per-segment a/v length drift passed 0.1 s it
    # inserted ~0.12 s of digital silence mid-word (click + dropout = the 卡顿/爆破声 the user heard). Now: decode every segment, pad/trim it
    # to its own container length (= where concat puts the next segment), lay them end to end sample-exactly.
    vparts, pos = [], 0
    for p_ in [cseg] + [p for p, _ in segs]:
        n_ = int(round((pos + probe(p_)) * SR)) - int(round(pos * SR)); pos += probe(p_)
        y_ = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(p_), "-vn", "-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32).reshape(-1, 2)
        vparts.append(np.pad(y_[:n_], ((0, max(0, n_ - len(y_))), (0, 0))))
    voice = np.concatenate(vparts); del vparts
    (work / "voice.f32").write_bytes(voice.astype(np.float32).tobytes())
    voicef = work / "voice.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", str(work / "voice.f32"), "-c:a", "pcm_f32le", str(voicef)])
    kx = np.clip(voice[:int(total * SR)] * 32767, -32768, 32767).astype(np.int16)
    del voice
    for a, b in win:
        kx[int(a * SR):int(b * SR)] = 0
    kx.tofile(work / "key.raw")
    del kx
    keyf = work / "key.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i", str(work / "key.raw"), str(keyf)])
    fl = ["[0:a]aresample=48000[bed]", "[1:a]aresample=48000[key]", "[2:a]aresample=48000[vm]",
          "[bed][key]sidechaincompress=threshold=0.04:ratio=4:attack=30:release=700[duck]",
          "[duck][vm]amix=inputs=2:normalize=0:duration=longest,atrim=0:" + f"{total:.3f}" + "[aout]"]
    premix = work / "premix.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(bedf), "-i", str(keyf), "-i", str(voicef), "-filter_complex", ";".join(fl), "-map", "[aout]",
         "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", str(premix)])
    # one fixed gain to -16 LUFS + true-peak-safe limiter at -1.5 dBFS (dynamic loudnorm pumped and still let AAC overs through)
    g_ = -16.0 - loud_i(premix)
    mix = work / "mix.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(premix), "-af", f"volume={g_:.2f}dB,alimiter=limit=0.84:attack=3:release=80:level=0,aresample=48000",
         "-ar", "48000", "-ac", "2", str(mix)])
    print(f"MIX gain {g_:+.2f} dB", flush=True)
    style = "FontName=Microsoft YaHei,FontSize=17,PrimaryColour=&H00F2F2F2,OutlineColour=&H00000000,BorderStyle=1,Outline=1.2,Shadow=0.6,MarginV=26"
    subs_arg = (work / "subs.srt").as_posix().replace(":", "\\:")
    final = ep / os.environ.get("OUT", f"EP{EPN}_预览.mp4")
    tmp = work / "final_nocover_art.mp4"
    from watermark import render_badge  # bottom-right "老渡 · 小柚" signature, every episode (not on the cover frames)
    badge = render_badge(work / "badge.png", W, H)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-i", str(mix), "-loop", "1", "-i", str(badge), "-map", "[v]", "-map", "1:a",
         "-filter_complex", f"[0:v][2:v]overlay=0:0:shortest=1:enable='gte(t,{CV})',subtitles='{subs_arg}':force_style='{style}'[v]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(tmp)])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-i", str(cover), "-map", "0", "-map", "1", "-c", "copy", "-c:v:1", "mjpeg",
         "-disposition:v:1", "attached_pic", "-movflags", "+faststart", str(final)])  # cover art / thumbnail
    print("VIDEO", final.name, round(probe(final), 1), "s", flush=True)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if os.environ.get("RANGE"):  # e.g. RANGE=118-149 : render only these shots (inserted n/v shots included)
        lo, hi = map(int, os.environ["RANGE"].split("-"))
        SHOTS[:] = [s for s in SHOTS if lo <= int(s["id"][:3]) <= hi]
    if what in ("pics", "all"):
        with ThreadPoolExecutor(4) as pool:
            list(pool.map(make_pic, SHOTS))
        miss = [s["id"] for s in SHOTS if not s["pic"].startswith(("clip:", "mont:", "f:", "d:", "fc:", "fa:", "fd:", "img:st_")) and not pic_path(s).exists()]
        print("pics done, missing:", miss, flush=True)
    if what in ("tts", "all"):
        with ThreadPoolExecutor(4) as pool:
            list(pool.map(tts, [s for s in SHOTS if s["line"] and s["who"] != "无"]))
        print("tts done", VOICE, flush=True)
    if what == "wins":  # print the footage window of every shot (check before a render)
        plan_windows()
        for i, (src, a, d) in WIN.items():
            print("WIN", i, src.stem, f"{a:.1f}-{a + d:.1f}", flush=True)
    if what in ("video", "all"):
        video()
