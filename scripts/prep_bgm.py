import subprocess
from pathlib import Path
Path("bgm").mkdir(exist_ok=True)
for s in sorted(Path("bgm_src").glob("bgm_*.*")):
    out = Path("bgm") / (s.stem[4:] + ".wav")
    if out.exists(): continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(s), "-ac", "2", "-ar", "48000", str(out)], check=True)
    print("BGM", out.name, flush=True)
print("BGM_DONE")
