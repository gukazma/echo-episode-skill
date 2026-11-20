"""LAN video site for the iPhone (skill: lan-video-site): finished videos on this PC, sorted 项目 → 作品 → 版本, played in Safari.
http://<渲染机IP>:8090   Read-only; only the delivery roots and video/image types are served.  Started hidden by run.vbs (pythonw).

Classification (see the skill's naming rules):
  D:\\Lumo视频\\<项目>\\[<子目录>\\]<项目>_<标题>_<类型>_v<N>[_<YYYYMMDD>].mp4   -> 项目 = first folder (files directly in the root: name prefix before "_")
  D:\\OpenMontage\\output\\echo_epNN\\EPNN_<片名>_<类型>v<N>.mp4                 -> 项目 = 回声号, 作品 = 第N期 <片名>
  作品 = file name without 类型 / version / date tokens; its versions are sorted 正片 > 预览 > others, then v number, then time."""
import base64, hashlib, html, json, re, subprocess, threading, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8090
HERE = Path(__file__).resolve().parent
THUMBS = HERE / "thumbs"; THUMBS.mkdir(exist_ok=True)
META = HERE / "meta.json"
LUMO = Path(r"D:\Lumo视频")
ECHO = Path(r"D:\OpenMontage\output")
VIDEO = {".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/mp4"}
IMAGE = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
INTERNAL = re.compile(r"审片|rejected|footage_|不快放|_debug|_tmp", re.I)  # working files left in a project folder - not deliveries
TYPES = ["正片", "终版", "定稿", "成片", "预览", "样片", "初剪", "试拍", "演示", "讲解", "汇报", "教程", "宣传片", "花絮", "测试"]
RANK = {"正片": 9, "终版": 9, "定稿": 9, "成片": 9, "预览": 5, "样片": 4, "初剪": 4, "试拍": 2, "测试": 1}


def parse(stem):
    """file stem -> (作品名, 类型, 版本号 or None, 日期 or '')"""
    s = stem
    ver, vtxt = None, ""
    m = list(re.finditer(r"(?:^|[_\-\s(（]|(?<=[\u4e00-\u9fff]))[vV](\d{1,3})([a-z]?)(?=$|[_\-\s)）.])", s))
    if m:
        ver = int(m[-1].group(1)) + (0.5 if m[-1].group(2) else 0); vtxt = m[-1].group(1) + m[-1].group(2)
        s = s[:m[-1].start()] + s[m[-1].end():]
    date = ""
    d = re.search(r"(?:^|_)(20\d{6})(?=$|_)", s)
    if d:
        date = d.group(1); s = s[:d.start()] + s[d.end():]
    typ = ""
    for t in TYPES:
        if re.search(rf"(?:^|_){t}(?=$|_)", s):  # only a separate token (…_正片_v1 / …_正片v1); "流程讲解" stays part of the title
            typ = t; s = re.sub(rf"_?{t}(?=$|_)", "", s, count=1); break
    s = re.sub(r"[_\-\s]+$", "", re.sub(r"__+", "_", s)).strip("_ ")
    return s or stem, typ, (ver, vtxt) if ver is not None else None, date


def find_cover(folder, stem):
    imgs = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE and p.is_file()]
    key = parse(stem)[0]
    for cond in (lambda p: "封面" in p.name and "16x9" in p.name and key.split("_")[0] in p.name,
                 lambda p: "封面" in p.name and p.stem.split("_封面")[0] in stem,
                 lambda p: "封面" in p.name and "16x9" in p.name,
                 lambda p: "封面" in p.name or "cover" in p.name.lower()):
        c = next((p for p in sorted(imgs) if cond(p)), None)
        if c:
            return c
    return None


def sources():
    """[(项目, 子分组, video path, cover)]"""
    out = []
    for ep in sorted(ECHO.glob("echo_ep*")):
        m_ = re.match(r"echo_ep(\d+)$", ep.name)
        if not ep.is_dir() or not m_:
            continue
        n = int(m_.group(1))
        cov = find_cover(ep, f"EP{n:02d}") or (find_cover(ep / "cover", f"EP{n:02d}") if (ep / "cover").is_dir() else None)
        for v in ep.iterdir():
            if v.suffix.lower() in VIDEO and v.is_file() and not INTERNAL.search(v.stem):
                out.append(("回声号", f"第{n}期", v, cov))
    if LUMO.exists():
        for v in LUMO.rglob("*"):
            if v.suffix.lower() not in VIDEO or not v.is_file() or INTERNAL.search(v.stem):
                continue
            rel = v.relative_to(LUMO).parts
            if len(rel) == 1:
                proj, sub = (v.stem.split("_")[0] if "_" in v.stem else "其他"), ""
            else:
                proj, sub = rel[0], " / ".join(rel[1:-1])
            out.append((proj, sub, v, find_cover(v.parent, v.stem)))
    return out


_lock = threading.Lock()
_cache = {"t": 0, "projects": [], "by": {}}
_meta = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}


def tok(s):
    return base64.urlsafe_b64encode(hashlib.sha1(str(s).encode("utf-8")).digest()[:12]).decode().rstrip("=")


def duration(p):
    st = p.stat(); k = f"{p}|{st.st_size}|{int(st.st_mtime)}"
    if k not in _meta:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                           capture_output=True, text=True, creationflags=0x08000000)
        try:
            _meta[k] = float(r.stdout.strip())
        except ValueError:
            _meta[k] = 0.0
        META.write_text(json.dumps(_meta, ensure_ascii=False), encoding="utf-8")
    return _meta[k]


def scan():
    """projects: [{name, id, works:[{title, id, sub, versions:[item...] best first}], mtime, count}] newest first"""
    with _lock:
        if time.time() - _cache["t"] < 30:
            return _cache["projects"], _cache["by"]
        works, by = {}, {}
        for proj, sub, v, cov in sources():
            st = v.stat()
            title, typ, ver, date = parse(v.stem)
            if proj == "回声号":
                title = re.sub(r"^EP\d+_", "", title)
            it = {"id": tok(v), "path": v, "cover": cov, "file": v.name, "size": st.st_size, "mtime": st.st_mtime, "dur": duration(v),
                  "type": typ, "ver": ver[0] if ver else None, "date": date, "proj": proj, "sub": sub, "title": title}
            it["label"] = " ".join(x for x in [typ, f"v{ver[1]}" if ver else (date[4:6] + "-" + date[6:] if date else "")] if x) or "—"
            key = (proj, sub, title)
            works.setdefault(key, []).append(it); by[it["id"]] = it
        projects = {}
        for (proj, sub, title), vs in works.items():
            vs.sort(key=lambda x: (RANK.get(x["type"], 3), x["ver"] or 0, x["mtime"]), reverse=True)
            w = {"title": title, "sub": sub, "id": tok(("w", proj, sub, title)), "versions": vs, "mtime": max(x["mtime"] for x in vs), "proj": proj}
            for x in vs:
                x["work"] = w
            by[w["id"]] = w
            p = projects.setdefault(proj, {"name": proj, "id": tok(("p", proj)), "works": []})
            p["works"].append(w)
        for p in projects.values():
            p["works"].sort(key=lambda w: -w["mtime"])
            p["mtime"] = p["works"][0]["mtime"]; p["count"] = sum(len(w["versions"]) for w in p["works"])
            by[p["id"]] = p
        plist = sorted(projects.values(), key=lambda p: -p["mtime"])
        _cache.update(t=time.time(), projects=plist, by=by)
        return plist, by


def thumb(item):
    if item.get("cover") and Path(item["cover"]).exists():
        return Path(item["cover"])
    t = THUMBS / (item["id"] + ".jpg")
    if not t.exists():
        d = item.get("dur") or 0
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(8.0, d / 3):.1f}", "-i", str(item["path"]), "-frames:v", "1",
                        "-vf", "scale=640:-2", str(t)], creationflags=0x08000000)
    return t


def mmss(s):
    s = int(s); return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def mb(n):
    return f"{n / 1e9:.1f} GB" if n > 1e9 else f"{n / 1e6:.0f} MB"


def day(t):
    return time.strftime("%m-%d %H:%M", time.localtime(t))


def fresh(t):
    return time.time() - t < 2 * 86400


CSS = """
:root{--bg:#faf8f5;--card:#fff;--fg:#1f1b16;--mut:#6b6259;--line:#e8e2da;--acc:#b45309;--acc2:#fff3e6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-text-size-adjust:100%}
header{position:sticky;top:0;z-index:5;background:rgba(250,248,245,.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:12px 16px}
h1{font-size:19px;margin:0}.sub{color:var(--mut);font-size:13px}
.wrap{max-width:1100px;margin:0 auto;padding:12px 14px 48px}
.crumb a{color:var(--acc);text-decoration:none}.crumb{font-size:14px;margin-bottom:2px}
h2{font-size:16px;margin:22px 2px 10px;border-left:4px solid var(--acc);padding-left:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
a.card,.work{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;color:inherit;text-decoration:none}
.thumb{position:relative;aspect-ratio:16/9;background:#eee center/cover no-repeat}
.tag{position:absolute;bottom:8px;background:rgba(0,0,0,.72);color:#fff;font-size:12px;padding:1px 7px;border-radius:6px}
.dur{right:8px}.ver{left:8px;background:var(--acc)}
.new{position:absolute;left:8px;top:8px;background:#fff;color:var(--acc);border:1px solid var(--acc);font-size:12px;padding:0 7px;border-radius:6px;font-weight:600}
.meta{padding:9px 12px 11px}.t{font-weight:600;font-size:15px;word-break:break-all}.s{color:var(--mut);font-size:13px;margin-top:2px}
details{border-top:1px solid var(--line);padding:6px 12px 10px}summary{color:var(--acc);font-size:14px;cursor:pointer;padding:4px 0}
.vl a{display:flex;justify-content:space-between;gap:8px;padding:7px 2px;border-bottom:1px dashed var(--line);color:var(--fg);text-decoration:none;font-size:14px}
.vl a span:last-child{color:var(--mut);white-space:nowrap}
.vl a.cur{color:var(--acc);font-weight:600}
video{width:100%;max-height:78vh;background:#000;border-radius:10px;display:block}
.info{color:var(--mut);font-size:14px;margin:8px 2px 4px}.dl{color:var(--acc)}.file{color:var(--mut);font-size:12px;word-break:break-all;margin:0 2px}
.empty{color:var(--mut);padding:40px 0;text-align:center}
"""


def page(title, body):
    return (f"<!doctype html><html lang=zh-CN><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1,viewport-fit=cover'>"
            f"<meta name=apple-mobile-web-app-capable content=yes><meta name=apple-mobile-web-app-title content='视频'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}</body></html>").encode("utf-8")


def thumb_div(x, extra=""):
    return (f"<div class=thumb style=\"background-image:url('/t/{x['id']}')\">{'<span class=new>新</span>' if fresh(x['mtime']) else ''}"
            f"{extra}<span class='tag dur'>{mmss(x['dur'])}</span></div>")


def index():
    projects, _ = scan()
    cards = []
    for p in projects:
        lead = p["works"][0]["versions"][0]
        cards.append(f"<a class=card href='/p/{p['id']}'>{thumb_div(lead)}<div class=meta><div class=t>{html.escape(p['name'])}</div>"
                     f"<div class=s>{len(p['works'])} 个作品 · {p['count']} 个版本 · 更新于 {day(p['mtime'])}</div></div></a>")
    total = sum(p["count"] for p in projects)
    body = (f"<header><h1>视频</h1><div class=sub>{len(projects)} 个项目 · {total} 个视频 · 最近更新的在前</div></header>"
            f"<div class=wrap><div class=grid>{''.join(cards) or '<div class=empty>没有视频</div>'}</div></div>")
    return page("视频", body)


def work_card(w):
    best = w["versions"][0]; older = w["versions"][1:]
    hist = ""
    if older:
        rows = "".join(f"<a href='/v/{x['id']}'><span>{html.escape(x['label'])}</span><span>{mmss(x['dur'])} · {day(x['mtime'])}</span></a>" for x in older)
        hist = f"<details><summary>历史版本（{len(older)}）</summary><div class=vl>{rows}</div></details>"
    vtag = '<span class="tag ver">' + html.escape(best["label"]) + "</span>"
    return (f"<div class=work><a href='/v/{best['id']}' style='color:inherit;text-decoration:none'>{thumb_div(best, vtag)}"
            f"<div class=meta><div class=t>{html.escape(w['title'])}</div><div class=s>{day(best['mtime'])} · {mb(best['size'])}</div></div></a>{hist}</div>")


def project(p):
    subs = []
    for w in p["works"]:
        if w["sub"] not in subs:
            subs.append(w["sub"])
    body = [f"<header><div class=crumb><a href='/'>‹ 全部项目</a></div><h1>{html.escape(p['name'])}</h1>"
            f"<div class=sub>{len(p['works'])} 个作品 · {p['count']} 个版本 · 每个作品显示最新版，旧版本在“历史版本”里</div></header><div class=wrap>"]
    for sub in subs:
        ws = [w for w in p["works"] if w["sub"] == sub]
        if sub:
            body.append(f"<h2>{html.escape(sub)}</h2>")
        body.append(f"<div class=grid>{''.join(work_card(w) for w in ws)}</div>")
    body.append("</div>")
    return page(p["name"], "".join(body))


def player(x):
    projects, by = scan()
    w = x["work"]; p = next(q for q in projects if q["name"] == x["proj"])
    vrows = "".join(f"<a class='{'cur' if y['id'] == x['id'] else ''}' href='/v/{y['id']}'><span>{html.escape(y['label'])}{'（最新）' if i == 0 else ''}</span>"
                    f"<span>{mmss(y['dur'])} · {day(y['mtime'])}</span></a>" for i, y in enumerate(w["versions"]))
    others = [o for o in p["works"] if o is not w][:8]
    body = (f"<header><div class=crumb><a href='/p/{p['id']}'>‹ {html.escape(p['name'])}</a></div></header><div class=wrap>"
            f"<video src='/f/{x['id']}' poster='/t/{x['id']}' controls playsinline preload=metadata></video>"
            f"<div class=t style='margin:12px 2px 0;font-size:17px'>{html.escape(w['title'])} · {html.escape(x['label'])}</div>"
            f"<div class=info>{mmss(x['dur'])} · {mb(x['size'])} · {day(x['mtime'])} · <a class=dl href='/f/{x['id']}?dl=1'>下载</a></div>"
            f"<div class=file>{html.escape(x['file'])}</div>"
            + (f"<h2>全部版本</h2><div class=vl>{vrows}</div>" if len(w["versions"]) > 1 else "")
            + (f"<h2>{html.escape(p['name'])} 的其他作品</h2><div class=grid>{''.join(work_card(o) for o in others)}</div>" if others else "") + "</div>")
    return page(w["title"], body)


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def send_bytes(self, code, data, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        try:
            u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
            parts = u.path.strip("/").split("/")
            if u.path == "/":
                return self.send_bytes(200, index(), "text/html; charset=utf-8")
            _, by = scan()
            if len(parts) == 2 and parts[1] in by:
                x = by[parts[1]]
                if parts[0] == "p" and "works" in x:
                    return self.send_bytes(200, project(x), "text/html; charset=utf-8")
                if "path" in x:
                    if parts[0] == "v":
                        return self.send_bytes(200, player(x), "text/html; charset=utf-8")
                    if parts[0] == "t":
                        t = thumb(x)
                        if t.exists():
                            return self.send_file(t, IMAGE.get(t.suffix.lower(), "image/jpeg"), cache=True)
                    if parts[0] == "f":
                        return self.send_file(x["path"], VIDEO.get(x["path"].suffix.lower(), "video/mp4"), dl="dl" in q)
            self.send_bytes(404, "没有找到".encode("utf-8"), "text/plain; charset=utf-8")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def send_file(self, p, ctype, dl=False, cache=False):
        size = p.stat().st_size; a, b = 0, size - 1
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if m:
            if m.group(1):
                a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
            else:
                a = max(0, size - int(m.group(2)))
            b = min(b, size - 1)
            if a > b:
                self.send_response(416); self.send_header("Content-Range", f"bytes */{size}"); self.send_header("Content-Length", "0"); self.end_headers(); return
        self.send_response(206 if m else 200)
        self.send_header("Content-Type", ctype); self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Length", str(b - a + 1))
        if m:
            self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
        self.send_header("Cache-Control", "max-age=86400" if cache else "no-cache")
        if dl:
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + urllib.parse.quote(p.name))
        self.end_headers()
        if self.command == "HEAD":
            return
        with open(p, "rb") as f:
            f.seek(a); left = b - a + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    break
                self.wfile.write(chunk); left -= len(chunk)


if __name__ == "__main__":
    if "--list" in __import__("sys").argv:  # print the classification (check new deliveries land where expected)
        for p in scan()[0]:
            print(f"[{p['name']}]")
            for w in p["works"]:
                print(f"   {w['sub'] + ' / ' if w['sub'] else ''}{w['title']}: " + ", ".join(x["label"] for x in w["versions"]))
        raise SystemExit
    scan()
    ThreadingHTTPServer.daemon_threads = True
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
