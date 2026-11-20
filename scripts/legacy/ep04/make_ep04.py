"""EP04 preview/final film (forked from EP03 make_ep03) (forked from EP02 make_v4): full-screen pictures + 老渡 voice (Doubao TTS) + BGM + subtitles.

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

sys.path.insert(0, r"D:\OpenMontage")
load_dotenv(r"D:\OpenMontage\.env")
ep = Path(__file__).resolve().parent
sc = json.loads((ep / "script_ep04.json").read_text(encoding="utf-8"))
SHOTS, BGM, MONT = sc["shots"], sc["bgm"], sc.get("montages", {})
W, H, FPS = 1920, 1080, 25
work = ep / "v1"
for d in ("pic", "tts", "seg"):
    (work / d).mkdir(parents=True, exist_ok=True)
APIKEY = os.environ.get("VOLC_TTS_APIKEY", "")
IDS = json.loads((ep.parent / "echo_ep03" / "voice_ids.json").read_text(encoding="utf-8")) if (ep.parent / "echo_ep03" / "voice_ids.json").exists() else {}
VOICE = {"老渡": (IDS["laodu"], "seed-icl-2.0") if IDS.get("laodu") else ("zh_male_m191_uranus_bigtts", "seed-tts-2.0"),
         "小柚": (IDS["xiaoyou"], "seed-icl-2.0") if IDS.get("xiaoyou") else ("zh_female_vv_uranus_bigtts", "seed-tts-2.0")}
RATE = {"老渡": 10 if IDS.get("laodu") else -8, "小柚": 15 if IDS.get("xiaoyou") else 0}  # clones speak ~19% slower than presets
SAY = {}  # polyphone hints for TTS only


def run(cmd):
    subprocess.run(cmd, check=True)


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
    if s["pic"].startswith(("clip:", "mont:", "f:", "d:", "fc:", "fa:")):
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
    key = f"{spk}|{rid}|{s['line']}" if not spk.startswith("S_") else f"{spk}|{rid}|m4|r{s.get('rate', 0)}|{s.get('ctx', '')}|{s['line']}"
    return work / "tts" / (hashlib.md5(key.encode()).hexdigest()[:16] + ".mp3")


def voice(s):
    """Narration audio as used in the film: the TTS line with mid-line pauses > 0.75 s cut down to 0.6 s.
    Audio only - narration plays over footage, so nothing visible jumps (host shots are never cut: a splice there is a visible jump = 卡顿)."""
    src = tts_path(s)
    if os.environ.get("VO_TIGHT", "1") != "1":
        return src
    out = work / "tts_t" / (src.stem + ".wav")
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
                    if (r - j) * 0.01 > 0.75:  # pause > 0.75 s -> 0.6 s: keep 0.45 s after the word (soft endings) and 0.15 s before the next
                        keep.append((cur, (j + 45) * hop)); cur = (r - 15) * hop
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
    body = {"user": {"uid": "echo"}, "req_params": {"text": say_text(s["line"]), "speaker": spk,
                                                     "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": s.get("rate", 0)}}}
    if spk.startswith("S_"):  # clone 2.0: model_type MUST be inside the additions JSON string, else it silently runs clone 1.0
        ad = {"model_type": 4}
        if s.get("ctx"):
            ad["context_texts"] = [s["ctx"]]
        body["req_params"]["additions"] = json.dumps(ad, ensure_ascii=False)
    for attempt in range(3):
        r = requests.post("https://openspeech.bytedance.com/api/v3/tts/unidirectional", json=body, stream=True, timeout=180,
                          headers={"X-Api-Key": APIKEY, "X-Api-Request-Id": str(uuid.uuid4()), "X-Api-Resource-Id": rid, "Content-Type": "application/json"})
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
            out.write_bytes(audio)
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
        f, ss, vol = BGM[mode]
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
    f, ss, vol = BGM[M["music"]]
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


RAMP_MAX, RAMP_EDGE, RAMP_CAP = 0.55, 0.15, 4.0  # target gap (s), 1x margin each side, max speed
RAMP_LOG = {}
END_AT = {}  # per-take "end 0.5 s after the last word" overrides (EP04: none yet)


def ramp_plan(src, a, b):
    """[(t0, t1, speed)] covering a..b: silent gaps > RAMP_MAX between words get their middle played fast.
    Speed is capped by motion so the ramp never moves faster than the person does while talking (no visible whip)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float); n = len(x) // 160
    e = np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1))
    i0, i1 = int(a * 100), min(n, int(b * 100))
    peak = np.percentile(e[i0:i1], 95)
    sm = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(e, 3, mode="edge"), 7), axis=1)
    loud = np.where(sm[i0:i1] >= 0.12 * peak)[0] + i0
    if len(loud) < 2:
        return [(a, b, 1.0)]
    Wm, Hm = 160, 90
    vr = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vf", f"scale={Wm}:{Hm},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(vr, np.uint8).reshape(-1, Hm, Wm).astype(float)
    mot = np.abs(np.diff(fr, axis=0)).mean((1, 2))  # mot[f] = change from frame f to f+1 (24 fps)
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
    for g0, g1 in gaps:
        r0, r1 = g0 + RAMP_EDGE, g1 - RAMP_EDGE
        want = (r1 - r0) / max(0.05, RAMP_MAX - 2 * RAMP_EDGE)
        # motion-limited speed: the sped-up per-frame change must stay <= typical talking motion
        gm = max(1e-3, np.mean(tfr(r0, r1)))
        sp = float(min(RAMP_CAP, want, max(1.0, talk / gm * 1.0)))
        # spike guard: a frozen stretch followed by a catch-up move becomes a whip when sped up - the summed change across the
        # frames skipped by one output frame must stay below the fastest talking frame
        seg_m = tfr(r0, r1)
        while sp >= 1.2 and len(seg_m) > 1:
            w = max(1, int(np.ceil(sp)))
            if np.convolve(seg_m, np.ones(w), "valid").max(initial=0) <= talk_max: break
            sp -= 0.1
        if sp < 1.2:
            continue
        parts += [(x0, r0, 1.0), (r0, r1, sp)]; x0 = r1
        log.append((round(g0, 2), round(g1 - g0, 2), round(sp, 2), round(2 * RAMP_EDGE + (r1 - r0) / sp, 2)))
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
        a = max(0.0, q["speech"][0] - 0.3)
        b = min(cd, max(q["speech"][1], TAIL.get(key, 0)) + (s.get("pad", 0.45) if j == len(takes) - 1 else 0.25))
        b = min(b, END_AT.get(key, b))
        # RAMP (default on): speech stays 1x (lip-sync untouched); only the middle of long silent gaps plays fast, so a 1-2 s
        # "staring" pause becomes ~0.55 s WITHOUT a jump cut (every frame still in order). CONFORM: Seedance is 24 fps, the film 25 -
        # fps=25 would repeat one frame per second (micro-hitch); play the take 25/24 faster instead (atempo keeps pitch).
        parts = ramp_plan(src, a, b) if os.environ.get("RAMP", "1") == "1" else [(a, b, 1.0)]
        k = (FPS / 24.0) if os.environ.get("CONFORM", "1") == "1" else 1.0
        d = sum((t1 - t0) / sp for t0, t1, sp in parts) / k
        n = len(parts)
        fo = 0.06 if b >= cd - 0.05 else 0.2  # take ends mid-word (013 "呀"): keep the last syllable audible
        pre = ""
        for m, (t0, t1, sp) in enumerate(parts):
            lo = (t1 - t0) / sp  # output length of this piece (before conform)
            pre += f"[0:v]trim=start={t0:.4f}:end={t1:.4f},setpts=(PTS-STARTPTS)/{sp * k:.5f}[v{m}];"
            # silent gap: keep its first `lo` seconds of room tone (no speech inside by construction)
            pre += (f"[0:a]atrim=start={t0:.4f}:end={t0 + lo:.4f},asetpts=PTS-STARTPTS,"
                    f"afade=t=in:d=0.012,afade=t=out:st={max(0, lo - 0.012):.4f}:d=0.012[a{m}];")
        pre += "".join(f"[v{m}][a{m}]" for m in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca0];"
        pre += f"[ca0]atempo={k:.6f}[ca];" if k != 1.0 else "[ca0]anull[ca];"
        out = work / "seg" / f"{i:03d}_s{j}.mkv"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex",
             pre + f"[cv]fps={FPS},scale={W}:{H}:flags=lanczos,format=yuv420p[v];"
             "[ca]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-17.5:TP=-2,aresample=48000,afade=t=in:d=0.15,"
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


USE = {  # usable ranges per source (subagent contact-sheet review 11-12)
    "budokan_song": (0, 29), "budokan_song_full": (3, 394), "budokan_mic_alt": (20, 93), "budokan_after": (39, 565), "budokan_ext_b": (0, 22),
    "budokan_ext": (0, 144), "retire_day": (12, 118), "koto_party": (0, 230), "wedding_news": (26, 545), "couple_lovelove": (30, 930),
    "star_tanjo_b": (168, 270), "star_tanjo_e": (8, 160), "star_tanjo_d": (16, 150), "toshigoro_b": (40, 379), "cm_pretz": (0, 15),
    "cm_pretz_b": (0, 9), "cm_cecil": (0, 55), "cm_almond": (0, 50), "cm_1978long": (0, 55), "cm_coll": (0, 150), "izu": (4, 138),
    "shiosai": (4, 148), "zessho": (4, 148), "shunkinsho": (4, 128), "koto": (4, 26), "kazetachinu": (4, 148), "doro": (4, 90),
    "honoo": (4, 90), "whitelove": (14, 80), "tenshi": (4, 86), "akai_c": (0, 500), "akai_scenes_song": (0, 215), "akai_a": (0, 170),
    "akai_op": (5, 205), "akai_d": (20, 38), "akai_e": (0, 21), "song_cosmos": (12, 216), "songs_tbs": (1153, 2404),
    "song_tabidachi": (8, 185), "song_tabidachi_b": (60, 349), "song_playback": (30, 190), "song_playback_b": (6, 195),
    "bestten_sayonara": (40, 377), "tv_yoruhit_sayonara1980": (10, 470), "tv_farewell_mc": (0, 440), "tv_final_yoruhit_b": (0, 284),
    "railways": (16, 80), "shizumanu": (20, 35), "katsuragi": (20, 45), "son_yutaro": (5, 19), "son_yutaro_live": (10, 360),
    "son_arigato_live": (20, 276), "quilt": (9, 40), "quilt_d": (0, 45), "yokosuka": (10, 26), "yokosuka_c": (25, 386),
    "yokosuka_d": (0, 115), "shunkin_last": (4, 470), "shiosai_kotoba": (60, 150), "akai_bl_ep29": (540, 1240), "miura_kinejun_speech": (0, 250), "miura_2024": (0, 215), "momoe_iv": (28, 126), "izu_last": (360, 525), "yokosuka_b": (11, 500), "tokyo80s_c": (20, 585), "tokyo80s_b": (0, 440), "tokyo80s": (15, 455),
}
CLEAN = "crop=iw*0.96:ih*0.92:iw*0.02:ih*0.04"
CHY20 = "crop=iw*0.86:ih*0.66:iw*0.07:ih*0.09"      # chyron / captions on the bottom ~20%
CHY25 = "crop=iw*0.84:ih*0.60:iw*0.08:ih*0.10"      # big chyron + ticker on the bottom ~25%
SIGN = "crop=iw*0.76:ih*0.68:iw*0.04:ih*0.08"       # sign-language inset bottom-right
TOPLOGO = "crop=iw*0.86:ih*0.80:iw*0.05:ih*0.14"   # logo / watermark top-right + some bottom text
CROPS = {**{k: CHY20 for k in ("koto_party", "wedding_news", "izu", "shiosai", "zessho", "shunkinsho", "koto", "kazetachinu", "doro", "honoo",
                               "whitelove", "tenshi", "songs_tbs", "song_playback_b", "bestten_sayonara", "son_yutaro", "railways", "shizumanu",
                               "katsuragi", "star_tanjo_b", "star_tanjo_d", "son_yutaro_live")},
         **{k: CHY25 for k in ("budokan_song_full", "akai_op", "quilt", "quilt_d", "toshigoro_b")},
         **{k: TOPLOGO for k in ("budokan_after", "tv_yoruhit_sayonara1980", "tv_farewell_mc", "tv_final_yoruhit_b", "akai_e", "song_playback",
                                 "son_arigato_live", "cm_coll", "budokan_song")},
         "couple_lovelove": "crop=iw*0.60:ih*0.86:iw*0.20:ih*0.07", "quilt": "crop=iw*0.56:ih*0.54:iw*0.10:ih*0.15",
         "momoe_kids": "crop=iw*0.78:ih*0.54:iw*0.08:ih*0.10",            # 4:3 after cropdetect; big captions at ~70% + inset top-right
         "akai_bl_ep29": CHY20, "akai_bl_ep0506": CHY20,                    # burned-in Chinese subs at the bottom
         "wedding_news": "delogo=x=255:y=210:w=180:h=110,crop=iw*0.96:ih*0.92:iw*0.02:ih*0.04",                 # big caption bottom-right (y>0.6, x>0.55)
         "izu_last": TOPLOGO, "miura_kinejun_speech": CHY20, "miura_2024": TOPLOGO, "momoe_talk2": "crop=ih*1.30:ih*0.80:(iw-ih*1.30)/2:ih*0.06"}
FOOT_INNER = CLEAN

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
        a = t if s.get("card") else max(0.0, t - min(1.5, d * 0.2))
        for ua, ub in ([] if s.get("again") else used.get(src, [])):  # again=True: a deliberate retelling may show the same moment again
            if a < ub and a + d > ua:
                a = ub
        if not s.get("card") and not s.get("again") and a + d > hi + 1.0 and t != lo:  # pushed out of the usable range: reuse from its start
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
        out.append(f"drawtext=fontfile='C\\:/Windows/Fonts/simkai.ttf':textfile='{tfe}':"
                   f"fontsize={fs + (14 if k == 0 else 0)}:fontcolor=0xF0E2C0:borderw=2:bordercolor=0x000000@0.6:"
                   f"x=(w-text_w)/2:y={y0 + k * (fs + gap)}:alpha='{alpha}'")
    return ",".join(out)


def motion_segment(i, s):
    src, a, dur = WIN[s["id"]]
    out = work / "seg" / f"{i:03d}.mkv"
    crop = DRAMA_VF + "," if s["pic"].startswith("d:") else foot_vf(src, a) + ","
    card = "," + card_vf(s, dur) if s.get("card") else ""
    if s["line"] and s["who"] != "无":
        ain = ["-i", str(voice(s))]
        af = "[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=250|250,apad[a]"
    else:
        ain = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        af = "[1:a]anull[a]"
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


def fade_vf(s, dur):
    jin, jout = cont_flags(s)
    v = ("" if jin else "fade=t=in:d=0.4,") + ("" if jout else f"fade=t=out:st={dur - 0.5:.3f}:d=0.5,")
    a = ("" if jin else "afade=t=in:d=0.3,") + ("" if jout else f"afade=t=out:st={dur - 0.5:.3f}:d=0.5,")
    return v, a


def fc_segment(i, s):
    """Modern voice clip (interview / lecture / visitor) with its ORIGINAL sound; source captions cropped away, ours are shown."""
    _, f, a, b = s["pic"].split(":")
    dur = float(b) - float(a)
    fv, fa = fade_vf(s, dur)
    out = work / "seg" / f"{i:03d}.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-ss", a, "-t", f"{dur:.3f}", "-i", str(ep / f), "-filter_complex",
         f"[0:v]{foot_vf(ep / f, float(a))},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,"
         f"{fv}format=yuv420p[v];"
         f"[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-17:TP=-2,aresample=48000,"
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
         f"[0:v]{foot_vf(ep / vf, float(vt))},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1,"
         f"{fv}format=yuv420p[v];"
         f"[1:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-17:TP=-2,aresample=48000,"
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


LOOK = {"老渡": ep / "look" / "ld_A.png", "小柚": ep / "look" / "xy_A_hair1.png"}  # EP04 chosen look (11-12): set + outfit stills as preview placeholders


def host_placeholder(i, s):
    dur = probe(tts_path(s)) + 0.25 + s.get("pad", 0.45)
    out = work / "seg" / f"{i:03d}.mkv"
    lab = (work / "seg" / "label.txt"); lab.write_text("主持人镜头 · 造型占位图（正片用 Seedance 2.5 拍摄）", encoding="utf-8")
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
    cover, CV = ep / "cover" / "EP04_cover.jpg", 2.5
    cseg = work / "seg" / "000_cover.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-framerate", f"{FPS}", "-loop", "1", "-t", f"{CV}", "-i", str(cover), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[v]", "-map", "[v]", "-map", "1:a", "-t", f"{CV}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le", str(cseg)])
    t, srt, k, sections, solo = CV, [], 1, [], []
    segs = [(p, probe(p)) for p, _ in segs]  # real container length = what the concat timeline uses
    for (p, d), s in zip(segs, SHOTS):
        if s["line"] and not s.get("card"):
            for a, b, c in subs_for(s["line"], t + 0.25, d - 0.6):
                srt.append(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n")
                k += 1
        if s["pic"].endswith(":mute"):
            solo.append((t, t + d))
        if sections and sections[-1][0] == s["bgm"]:
            sections[-1][2] = t + d
        else:
            sections.append([s["bgm"], t, t + d])
        t += d
    total = t
    (work / "subs.srt").write_text("\n".join(srt), encoding="utf-8")
    (work / "concat.txt").write_text("\n".join(f"file '{p.as_posix()}'" for p in [cseg] + [p for p, _ in segs]), encoding="utf-8")
    joined = work / "joined.mkv"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(work / "concat.txt"), "-c", "copy", str(joined)])
    # music bed: each section's track from its start offset, 3 s soft fades, overlapping edges
    ins, fl, labels = [], [], []
    for n, (key, a, b) in enumerate(s for s in sections if BGM[s[0]][0]):
        f, ss, vol = BGM[key]
        a2, ln = max(0.0, a - 1.5), (b + 2.0) - max(0.0, a - 1.5)
        fit = key == "after" and b >= total - 0.01  # the film ends on this bed: let the final 送别 play out to its natural end
        if fit:
            fitf = build_after_fit((total - 0.5) - a2)
            ins += ["-i", str(fitf)]
            tailfade = f"apad,afade=t=out:st={ln - 2.6:.3f}:d=0.4"
        else:
            ins += ["-ss", str(ss), "-stream_loop", "-1", "-i", str(ep / "bgm" / f)]
            tailfade = f"afade=t=out:st={ln - 3.5:.3f}:d=3.5:curve=qsin"
        fl.append(f"[{n}:a]atrim=0:{ln:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-20:TP=-3,"
                  f"volume={vol:.2f},afade=t=in:d=3:curve=qsin,{tailfade},atrim=0:{ln:.3f},adelay={int(a2 * 1000)}|{int(a2 * 1000)}[m{n}]")
        labels.append(f"[m{n}]")
    n = len(labels)
    # music alone over muted drama footage: raise the bed ~+8 dB with 2 s ramps
    boost = "".join(f",volume=volume='1+1.5*max(0,min(1,min((t-{a:.3f})/2,({b:.3f}-t)/2)))':eval=frame" for a, b in solo)
    ins += ["-i", str(joined)]
    fl.append(f"{''.join(labels)}amix=inputs={n}:normalize=0:duration=longest,atrim=0:{total:.3f},volume=0.55{boost}[bed]")
    fl.append(f"[{n}:a]aresample=48000:async=1:first_pts=0,asplit=2[vk][vm]")  # async: honour pts gaps between segments (lip sync)
    fl.append("[bed][vk]sidechaincompress=threshold=0.04:ratio=4:attack=30:release=700[duck]")
    fl.append("[duck][vm]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    mix = work / "mix.wav"
    run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[aout]", "-ar", "48000", "-ac", "2", str(mix)])
    style = "FontName=Microsoft YaHei,FontSize=17,PrimaryColour=&H00F2F2F2,OutlineColour=&H00000000,BorderStyle=1,Outline=1.2,Shadow=0.6,MarginV=26"
    subs_arg = (work / "subs.srt").as_posix().replace(":", "\\:")
    final = ep / os.environ.get("OUT", "EP04_我会幸福的.mp4")
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
        miss = [s["id"] for s in SHOTS if not s["pic"].startswith(("clip:", "mont:", "f:", "d:", "fc:", "fa:", "img:st_")) and not pic_path(s).exists()]
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
