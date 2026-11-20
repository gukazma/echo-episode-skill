"""ytsearch/bilisearch candidates for EP05 footage -> footage/cands.json (title, id, duration, channel)"""
import json, sys
from pathlib import Path
import yt_dlp
Q = {
 "stanford": ["Jensen Huang Stanford GSB View From The Top 2024", "Jensen Huang pain and suffering Stanford students"],
 "ntu": ["黄仁勋 台大 毕业典礼 2023 演讲 完整", "Jensen Huang NTU commencement speech 2023 full"],
 "caltech": ["Jensen Huang Caltech commencement 2024"],
 "oneida": ["Jensen Huang Oneida Baptist Institute", "Oneida Baptist Institute Kentucky Huang Hall"],
 "dennys": ["Jensen Huang Denny's booth trillion dollar", "Nvidia founded at Denny's Jensen Huang video", "Jensen Huang Denny's dishwasher busboy"],
 "sega": ["Sega Saturn commercial 1995", "Nvidia NV1 Diamond Edge 3D 1995", "Jensen Huang Sega story Irimajiri"],
 "riva": ["Nvidia RIVA 128 1997", "GeForce 256 1999 first GPU commercial", "Nvidia history documentary"],
 "cuda": ["Nvidia CUDA 2007 launch", "Jensen Huang interview 2008", "Jensen Huang CUDA bet Wall Street"],
 "alexnet": ["AlexNet ImageNet 2012 Krizhevsky Hinton GPUs", "Geoffrey Hinton Nvidia GPUs deep learning interview"],
 "dgx": ["Jensen Huang DGX-1 OpenAI 2016 delivery", "Jensen Huang delivers DGX H200 OpenAI 2024"],
 "keynote": ["Jensen Huang GTC 2024 keynote", "Computex 2024 keynote Jensen Huang", "Nvidia I am AI keynote intro", "Jensen Huang CES 2025 keynote", "GTC 2025 keynote Jensen Huang"],
 "taiwan": ["黄仁勋 夜市 2024", "黄仁勋 台北 宁夏夜市 2023", "Jensen Huang Taiwan night market crowd", "黄仁勋 台南 老家"],
 "interview": ["Jensen Huang 60 Minutes", "Acquired podcast Jensen Huang", "Jensen Huang cleaned toilets", "Jensen Huang mother taught English dictionary", "Jensen Huang tattoo Nvidia logo", "Jensen Huang Lori Huang Oregon State lab partner", "Jensen Huang Morris Chang TSMC letter", "Jensen Huang 30 days from going out of business"],
 "market": ["Nvidia trillion dollar market cap news 2023", "Nvidia 5 trillion market cap news", "Nvidia most valuable company news"],
 "scenery": ["Tainan aerial 4K drone", "Oregon State University campus drone", "Silicon Valley 1990s footage", "Kentucky Appalachian countryside drone", "1970s Taiwan footage"],
 "bgm": ["Einaudi Experience piano", "望春风 钢琴", "Einaudi Nuvole Bianche", "Einaudi Divenire", "inspiring piano cinematic"],
}
out = {}
opts = {"quiet": True, "extract_flat": True, "skip_download": True, "no_warnings": True}
with yt_dlp.YoutubeDL(opts) as y:
    for k, qs in Q.items():
        out[k] = []
        for q in qs:
            for pre in ("ytsearch8", "bilisearch6"):
                try:
                    r = y.extract_info(f"{pre}:{q}", download=False)
                    for e in r.get("entries") or []:
                        out[k].append({"src": pre[:2], "q": q, "id": e.get("id"), "url": e.get("url") or e.get("webpage_url"), "title": e.get("title"), "dur": e.get("duration"), "ch": e.get("channel") or e.get("uploader")})
                except Exception as ex:
                    out[k].append({"src": pre[:2], "q": q, "err": str(ex)[:200]})
        print(k, len(out[k]), flush=True)
Path("footage").mkdir(exist_ok=True)
Path("footage/cands.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("FIND_DONE")

