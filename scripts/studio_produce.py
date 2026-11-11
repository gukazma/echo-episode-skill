"""Chain-aware Seedance generation for EP02 studio shots.  python studio_produce.py <plan.json> [variant=mini] [res=720p]
Chains run in parallel (max 3 Ark tasks); inside a chain each shot gets the previous take's API last frame as continuity ref."""
import json, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
sys.path.insert(0, r"D:\OpenMontage")
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env")
from tools.video.seedance_ark import SeedanceArkVideo
ep = Path(__file__).resolve().parent
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
VAR = sys.argv[2] if len(sys.argv) > 2 else "mini"
RES = sys.argv[3] if len(sys.argv) > 3 else "720p"
shots = {s["id"]: s for s in plan["shots"]}
clips = ep / "studio" / "clips"; clips.mkdir(parents=True, exist_ok=True)
slots, lock, _res = threading.Semaphore(3), threading.Lock(), set()
START = {("老渡", "side"): "../echo_ep01_final/clips/S25_t1_last.png"}
def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    with lock:
        with (ep / "studio" / "produce.log").open("a", encoding="utf-8") as f: f.write(line + "\n")
    print(line, flush=True)
def next_take(sid):
    with lock:
        n = 1
        while (clips / f"{sid}_t{n}.json").exists() or (sid, n) in _res: n += 1
        _res.add((sid, n)); return n
def run_shot(sid, prev):
    s = shots[sid]; take = next_take(sid); out = clips / f"{sid}_t{take}.mp4"
    refs = [str((ep / r).resolve()) for r in s["refs"]]; prompt = s["prompt"]
    if prev and prev.exists():
        refs.append(str(prev)); n = len(refs)
        prompt = prompt.replace("【LIGHTING】", f"【CONTINUITY】图{n}是同一机位上一个镜头的最后一帧：背景、光线、坐姿、手的位置和服装与图{n}连贯一致，"
                                              f"像同一场戏紧接着的下一个镜头，开头的姿势要和图{n}衔接上。"
                                              f"图{n}只用来对齐姿势、动作和光线，不要沿用它的取景大小：景别按【SHOT】的要求重新构图，镜头不要越推越近。\n【LIGHTING】", 1)
        prompt = prompt.replace("极慢推近", "固定机位").replace("缓推", "固定机位")
    inputs = {"prompt": prompt, "model_variant": VAR, "model": SeedanceArkVideo.MODEL_IDS[VAR],  # explicit: .env ARK_SEEDANCE_MODEL (2.5) would override the variant
              "duration": s["duration"], "aspect_ratio": "16:9", "resolution": RES,
              "generate_audio": s.get("generate_audio", True), "operation": "reference_to_video", "reference_image_paths": refs, "return_last_frame": True,
              **({"reference_audio_paths": [str(Path(a).resolve()) for a in s["audio_refs"]]} if s["audio_refs"] else {}),
              "output_path": str(out), "timeout_seconds": 1800, "poll_interval_seconds": 8}
    with slots:
        log(f"START {sid} t{take} {VAR} {RES} {s['duration']}s chain={'yes' if prev else 'no'}"); t0 = time.time()
        r = SeedanceArkVideo().execute(inputs)
    data = r.data or {}
    (clips / f"{sid}_t{take}.json").write_text(json.dumps({"id": sid, "take": take, "variant": VAR, "res": RES, "success": r.success, "error": r.error,
        "chain_ref": str(prev) if prev else None, "cost_cny": r.cost_usd, "data": data}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not r.success:
        log(f"FAIL  {sid} t{take}: {str(r.error)[:300]}"); return None
    last = clips / f"{sid}_t{take}_last.png"
    try:
        last.write_bytes(requests.get(data["last_frame_url"], timeout=120).content)
    except Exception as exc:
        log(f"WARN {sid} no API last frame ({exc})"); return None
    log(f"DONE  {sid} t{take} {time.time() - t0:.0f}s cost {r.cost_usd}"); return last
def run_chain(chain):
    s0 = shots[chain[0]]; st = s0.get("seed") or START.get((s0["who"], s0["angle"])); prev = (ep / st).resolve() if st else None
    for sid in chain:
        last = run_shot(sid, prev)
        if last is None: last = run_shot(sid, prev)
        prev = last
log(f"BEGIN {sys.argv[1]} {plan['chains']}")
with ThreadPoolExecutor(len(plan["chains"])) as pool: list(pool.map(run_chain, plan["chains"]))
log("END")
