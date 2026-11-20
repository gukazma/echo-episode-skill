import subprocess
from pathlib import Path
Path("bgm").mkdir(exist_ok=True)
for out in ("experience", "nuvole", "divenire", "wangchunfeng"):
    s = next(Path("bgm_src").glob(f"bgm_{out}.*"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(s), "-ac", "2", "-ar", "48000", f"bgm/{out}.wav"], check=True)
    print("BGM", out, s.name, flush=True)
