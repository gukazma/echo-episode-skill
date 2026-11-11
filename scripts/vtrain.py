import os, uuid, json, base64, requests, sys, time
from dotenv import load_dotenv
load_dotenv(r"D:\OpenMontage\.env"); K = os.environ["VOLC_TTS_APIKEY"]
B = "https://openspeech.bytedance.com"
V = r"D:\OpenMontage\output\echo_ep01_final\voices"
JOBS = [("<老渡音色ID>", V + r"\laodu_clone_train.wav"), ("<小柚音色ID>", V + r"\xiaoyou_clone_train.wav")]
def H(): return {"X-Api-Key": K, "X-Api-Request-Id": str(uuid.uuid4()), "X-Api-Resource-Id": "seed-icl-2.0", "Content-Type": "application/json"}
for spk, wav in JOBS:
    data = base64.b64encode(open(wav, "rb").read()).decode()
    body = {"speaker_id": spk, "audio": {"data": data, "format": "wav"}, "language": 0, "model_type": 4,
            "extra_params": {"enable_audio_denoise": True}}
    r = requests.post(B + "/api/v3/tts/voice_clone", json=body, headers=H(), timeout=300)
    print(spk, "v3 clone", r.status_code, r.text[:300], flush=True)
for k in range(30):
    time.sleep(10)
    st = [requests.post(B + "/api/v3/tts/get_voice", json={"speaker_id": s}, headers=H(), timeout=30).json().get("status") for s, _ in JOBS]
    print("status", st, flush=True)
    if all(x in (2, 4, 3) for x in st): break
