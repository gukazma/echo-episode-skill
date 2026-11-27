"""List recent Ark Seedance tasks (no secrets printed) and download the latest succeeded one of a given model to a path.
python recover_task.py <model-substring> <out.mp4>"""
import os, sys, requests
sys.path.insert(0, os.environ.get("OPENMONTAGE", r"D:\OpenMontage"))
from dotenv import load_dotenv
load_dotenv(os.environ.get("OPENMONTAGE", r"D:\OpenMontage") + r"\.env")
from tools.video.seedance_ark import SeedanceArkVideo
tool = SeedanceArkVideo()
base = tool._get_base_url()
h = {"Authorization": "Bearer " + os.environ["ARK_API_KEY"].removeprefix("Bearer ").strip()}
r = requests.get(f"{base}/contents/generations/tasks", params={"page_num": 1, "page_size": 10}, headers=h, timeout=60)
print("HTTP", r.status_code)
items = r.json().get("items", [])
for t in items:
    print(t.get("id"), t.get("model"), t.get("status"), t.get("created_at"), (t.get("content") or {}).get("video_url", "")[:60])
want = [t for t in items if sys.argv[1] in str(t.get("model")) and t.get("status") == "succeeded"]
if want:
    url = want[0]["content"]["video_url"]
    open(sys.argv[2], "wb").write(requests.get(url, timeout=300).content)
    print("SAVED", sys.argv[2], want[0]["id"])
