"""Seedance prompt/reference dossier for the host-take review reel (No.1-35) + retake appendix -> folder + zip.
Run with Python311 (python-docx).  Paths in the document are relative; no keys, no voice IDs."""
import json, os, shutil, subprocess, zipfile
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

ep = Path(__file__).resolve().parent
st = ep / "studio"; clips = st / "clips"
OUT = ep / "EP05_Seedance提示词整理"
if OUT.exists(): shutil.rmtree(OUT)
for d in ("参考图", "参考音频", "生成结果_视频", "生成结果_截帧"): (OUT / d).mkdir(parents=True)

script = {s["id"]: s for s in json.loads((ep / "script_ep05.json").read_text(encoding="utf-8"))["shots"]}
acc = json.loads((st / "accepted.json").read_text(encoding="utf-8"))
REEL_OLD = {"057": "057_t1", "070": "070_t1", "116": "116_t1", "116b": "116b_t1"}  # the review reel was cut before these four were retaken
order = [s for s in script if s in acc]
reel = [(n, sid, REEL_OLD.get(sid, acc[sid][0])) for n, sid in enumerate(order, 1)]
samples = [("E1", "007", "007_t1"), ("E2", "009", "009_t1"), ("E3", "009", "009_t2"), ("E4", "009", "009_t3"), ("E5", "106", "106_t1"), ("E6", "110", "110_t1")]
retakes = [("R1", "057", "057_t2"), ("R2", "070", "070_t2"), ("R3", "116", "116_t2"), ("R4", "116b", "116b_t2")]
strict = json.loads((st / "strict.json").read_text(encoding="utf-8")) if (st / "strict.json").exists() else {}
qc2 = json.loads((st / "qc2.json").read_text(encoding="utf-8")) if (st / "qc2.json").exists() else {}
ISSUE = {"057_t1": "多说了一个字：『这个年轻人顺眼』说成『这个年轻人是顺眼』",
         "070_t1": "漏字：『他一说就是三十多年』说成『他一说是三十多年』（漏『就』）",
         "116_t1": "漏字：『从九岁那台录音机』说成『从九岁台录音机』（漏『那』）——人工审片发现",
         "116b_t1": "漏字：『离倒闭只有三十天』说成『离倒闭有三十天』（漏『只』）——人工审片发现",
         "007_t1": "2.0 mini 720p（首次试拍）：说话像『烫嘴』——语速连读、几乎没有句读停顿；另有重复字『停在、在加州』。当时参考音频的句间停顿被收紧到 ≤0.6 s，提示词写了『紧凑自然，句与句之间只停顿半秒』",
         "009_t1": "2.0 mini 720p：参考音频改为原速未收紧、提示词改为『语速从容，逗号换气、句号稍停』后仍『烫嘴』；且出现重复字『黑黑皮夹克』。本条表演说明里有『低头看皮夹克、摇头』等头部动作",
         "009_t2": "2.0 mini 720p：参考音频放慢到约 85%、提示词改为『语速节奏停顿以音频1为准、说话时头部稳定』后，句读出来了，但吐字含糊/吞字（『今晚要讲的』的『要』听不到，『行头』含糊），句号后停顿 1.4 s",
         "009_t3": "2.0 fast 720p（与 E3 同一提示词和参考）：吐字清楚、停顿均匀，但人物脸型偏离参考图（明显变瘦，像换了个人）。同设置改 480p 后（No.03）脸型反而更接近参考",
         "106_t1": "2.0 fast 480p：结巴——『只是每次都骗自己一句』说成『只是每签字骗是每次都骗骗自己一句』",
         "110_t1": "2.0 fast 480p：『天将降大任』听起来像『天将将大任』（与 No.31 同样存疑）",
         "110_t2": "疑似：『天将降大任』听起来像『天将将大任』（同音，机器无法区分，待人耳确认）"}
plans = sorted(st.glob("plan_*.json"), key=lambda p: p.stat().st_mtime)

def plan_for(key):
    sid = key.rsplit("_t", 1)[0]; tj = (clips / f"{key}.json").stat().st_mtime
    best = None
    for p in plans:
        if p.stat().st_mtime <= tj:
            sh = {x["id"]: x for x in json.loads(p.read_text(encoding="utf-8"))["shots"]}
            if sid in sh: best = sh[sid]
    return best

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0

shared = {}  # src path -> name in 参考图
def ref_name(src, label):
    src = Path(src)
    if str(src) not in shared:
        name = f"{label}{src.suffix}"
        if not src.exists(): return f"{label}（文件已不在）"
        shutil.copy2(src, OUT / "参考图" / name); shared[str(src)] = name
    return shared[str(src)]

ROLE = {"look/lookclip_ld_t1_last.png": "老渡_角色定妆帧", "look/plate_ld_s.jpg": "老渡_布景plate",
        "look/lookclip_xy_t2_last.png": "小柚_角色定妆帧", "look/plate_xy_s.jpg": "小柚_布景plate"}

def entry(no, sid, key):
    rec = json.loads((clips / f"{key}.json").read_text(encoding="utf-8")); data = rec.get("data") or {}
    MID = {"fast": "doubao-seedance-2-0-fast-260128", "mini": "doubao-seedance-2-0-mini-260615"}
    data.setdefault("model", MID.get(rec.get("variant"), rec.get("variant"))); data.setdefault("task_id", rec.get("task", ""))
    data.setdefault("resolution", rec.get("res")); data.setdefault("generate_audio", True)
    pl = plan_for(key) or {}
    refs = []
    for r in pl.get("refs", []):
        refs.append(ref_name(ep / r, ROLE.get(r, Path(r).stem)))
    if rec.get("chain_ref"):
        cr = Path(rec["chain_ref"]); refs.append(ref_name(cr, f"{no}_上一镜末帧_{cr.stem.replace('_last', '')}"))
    auds = []
    for a in pl.get("audio_refs", []):
        a = Path(a); nm = f"{no}_{sid}_参考音频{a.suffix}"; shutil.copy2(a, OUT / "参考音频" / nm); auds.append((nm, probe(a)))
    vid = f"{no}_{key}.mp4"; shutil.copy2(clips / f"{key}.mp4", OUT / "生成结果_视频" / vid)
    d = probe(clips / f"{key}.mp4"); strip = f"{no}_{key}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clips / f"{key}.mp4"), "-vf", f"fps=5/{max(d, 1):.2f},scale=320:-2,tile=5x1",
                    "-frames:v", "1", str(OUT / "生成结果_截帧" / strip)])
    s = script[sid]
    issue = ISSUE.get(key) or ("未发现文字错误" if strict.get(key, {}).get("ok", True) else "；".join(strict[key]["errs"]))
    gaps = qc2.get(key, {}).get("gaps", [])
    return {"no": no, "sid": sid, "key": key, "who": s["who"], "line": s["line"], "model": data.get("model", ""), "task": data.get("task_id", ""),
            "res": f"{data.get('resolution', rec.get('res'))}（{data.get('video_width')}×{data.get('video_height')}）", "dur": data.get("duration"),
            "audio": data.get("generate_audio"), "prompt": data.get("prompt") or pl.get("prompt", ""), "refs": refs, "auds": auds, "vid": vid, "strip": strip,
            "issue": issue, "gaps": gaps, "tts": pl.get("tts_dur"), "cost": rec.get("cost_cny")}

doc = Document()
stl = doc.styles["Normal"]; stl.font.name = "Microsoft YaHei"; stl.font.size = Pt(10); stl.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
for sec in doc.sections: sec.left_margin = sec.right_margin = Cm(2)
def mono(text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(8.5); r.font.name = "Consolas"; r.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    p.paragraph_format.left_indent = Cm(0.4)
def kv_table(rows):
    t = doc.add_table(rows=0, cols=2); t.style = "Light Grid Accent 1"
    for k, v in rows:
        c = t.add_row().cells; c[0].text = k; c[1].text = str(v); c[0].width = Cm(3.2); c[1].width = Cm(13.8)
    return t

h = doc.add_heading("回声号 EP05 主持人镜头：Seedance 2.0 fast 提示词与参考素材", 0)
doc.add_paragraph(f"整理日期：{datetime.now():%Y-%m-%d}　对应审片视频：EP05_主持人原片审片.mp4（No.1–35，画面左上角有序号）")
doc.add_heading("一、我们想请教的问题", 1)
for q in ["1. 漏字/多字：台词在提示词里一字不差给出，参考音频也是同一句完整配音，但仍会漏掉轻读的单字或多加字（No.19 多『是』，No.22 漏『就』，No.33 漏『那』，No.34 漏『只』）。怎样写能让模型严格按台词逐字说？",
          "2. 语速/停顿：参考音频的停顿收紧时（句间 ≤0.6 s），2.0 mini 说话像『烫嘴』、没有句读；把参考音频放慢到约 85% 并取消收紧后，2.0 fast 又常在句号后停 1–1.7 秒。参考音频与提示词里的语速描述，哪个优先？推荐的写法是什么？",
          "3. 同一句拆成两条（超过 15 s 上限）时，后半条用前半条的最后一帧做参考图（下文『上一镜末帧』），衔接处的姿势/语气如何更连贯？",
          "4. 2.0 fast 在 720p 时人脸会偏离参考（变瘦），480p 反而更像参考图；角色一致性有什么建议（参考图数量、顺序、描述方式）？",
          "5. 提示词结构是否合理（【GLOBAL STYLE】【CHARACTERS】【SCREEN DIRECTION】【POSTURE】【DIALOGUE】【AUDIO REFERENCE】等分块）？哪些块是多余的或互相冲突？"]:
    doc.add_paragraph(q)
doc.add_heading("二、遇到的问题汇总", 1)
doc.add_paragraph("序号说明：No.xx = 审片视频里的序号（最终选用/曾选用的条）；E1–E6 = 早期试拍或被淘汰的问题样例（附录 B）；R1–R4 = 补拍后通过的条（附录 A）。")
pos = {sid: n for n, sid, _ in reel}
long_gaps = [(f"No.{pos[sid]:02d}（{acc[sid][0] if sid not in REEL_OLD else REEL_OLD[sid]}）", g) for sid in order
             for g in [max(qc2.get(REEL_OLD.get(sid, acc[sid][0]), {}).get("gaps", []) or [0])] if g > 1.0]
PROBLEMS = [
 ("1. 漏字", "2.0 fast 480p", "整句台词说得很顺，但漏掉一个轻读的单字，语义被改变。", "No.22 漏『就』（他一说就是三十多年）；No.33 漏『那』（九岁那台录音机）；No.34 漏『只』（离倒闭只有三十天）。在【SHOT】里加『某某字必须清楚说出来，绝不能漏』后补拍都说对了（R2–R4）。另：Whisper 整句识别会按通顺把漏掉的字『补』回来，No.33/34 最初是人工审片才发现。"),
 ("2. 多字", "2.0 fast 480p", "在台词里多加一个字。", "No.19『这个年轻人顺眼』说成『这个年轻人是顺眼』；加提示后补拍正确（R1）。"),
 ("3. 结巴 / 重复字", "2.0 mini 720p、2.0 fast 480p", "单字或多字重复、说错后重说。", "E5『每次都骗自己』→『每签字骗是每次都骗骗自己』；E1『停在、在加州』；E2『黑黑皮夹克』。"),
 ("4. 『烫嘴』：语速连读、没有句读停顿", "2.0 mini 720p", "整句一口气说完，逗号/句号处几乎不停，听感很赶。", "E1（参考音频句间停顿收紧到 ≤0.6 s + 提示词『紧凑、只停半秒』）；E2（换原速参考音频 + 『语速从容、逗号换气』提示词，仍然烫嘴，且表演说明里有低头/摇头动作）。E3 把参考音频放慢到约 85%、提示词改为『语速节奏停顿以音频1为准、说话时头部稳定』后才有句读。"),
 ("5. 吐字含糊 / 吞字", "2.0 mini 720p", "有句读了，但个别字听不清或被吞掉。", "E3『今晚要讲的』的『要』听不到，『行头』含糊。同提示词换 2.0 fast 后吐字清楚（E4、No.03）。"),
 ("6. 句中长停顿（发呆）", "2.0 fast 480p，参考音频放慢到 85%", "句号后停 1–1.7 秒、人物基本不动，成片里像卡住。参考音频本身句间停顿约 0.5–0.8 s。", "；".join(f"{a} 最长停顿 {g:.2f} s" for a, g in long_gaps) or "—"),
 ("7. 人脸偏离参考图", "2.0 fast 720p", "同样的参考图和提示词，720p 生成的人脸比参考明显变瘦，像换了人；480p 更接近参考。", "E4（720p）对比 No.03（480p，同一提示词）。"),
 ("8. 同音重复无法自动判断", "2.0 fast 480p", "『天将降大任』听起来像『天将将大任』，拼音相同，自动检查分不出来。", "E6、No.31。"),
 ("9. 拆句衔接", "2.0（单条上限 15 s）", "超过 15 s 的台词拆成两条，后半条用前半条末帧做图3、提示『紧接上一句、开头不停顿』，接口处换机位。语气/姿势是否能更连贯？", "No.06+07、No.12+13、No.17+18、No.31+32、No.33+34。"),
]
t = doc.add_table(rows=1, cols=4); t.style = "Light Grid Accent 1"
for c, h_ in zip(t.rows[0].cells, ("问题", "出现的模型/设置", "现象", "样例与已尝试的办法")): c.text = h_
for row in PROBLEMS:
    cs = t.add_row().cells
    for c, v in zip(cs, row): c.text = v
doc.add_heading("三、通用设置", 1)
kv_table([("模型", "doubao-seedance-2-0-fast-260128（2.0 fast）"), ("接口", "火山方舟 contents/generations/tasks，operation = reference_to_video"),
          ("分辨率 / 比例", "480p，16:9（成片中放大到 1080p）"), ("时长", "每条按参考音频长度给：老渡 ceil(1.12×音频+1)，小柚 ceil(1.08×音频+0.8)，上限 15 s"),
          ("generate_audio", "true（用 Seedance 自己生成的人声，不做后期配音/对口型）"), ("参考图", "图1 角色定妆帧（由 Seedance 生成，见『参考图』文件夹）；图2 无人布景 plate；连续镜头再加 图3 上一镜末帧"),
          ("参考音频", "同一句台词的克隆音色 TTS（老渡：语速 -15%、不收紧停顿；小柚：句间停顿收紧到 ~0.6 s），见『参考音频』文件夹"),
          ("return_last_frame", "true（末帧用作下一条的连续性参考）")])
doc.add_paragraph("角色定妆帧和布景 plate 见文末『附：角色与布景参考图』和『参考图』文件夹。")
for f, cap in [("老渡_角色定妆帧.png", "老渡 角色定妆帧（图1）"), ("老渡_布景plate.jpg", "老渡 布景 plate（图2）"), ("小柚_角色定妆帧.png", "小柚 角色定妆帧（图1）"), ("小柚_布景plate.jpg", "小柚 布景 plate（图2）")]:
    pass  # inserted after files are copied (below)
doc.add_heading("四、逐条明细（与审片视频序号一致）", 1)
entries = [entry(f"No.{n:02d}", sid, key) for n, sid, key in reel]
app = [entry(r, sid, key) for r, sid, key in retakes]
smp = [entry(r, sid, key) for r, sid, key in samples]
# shared ref thumbnails now exist
p_marker = doc.paragraphs[-2]
def add_entry(e):
    doc.add_heading(f"{e['no']}　镜头 {e['sid']}　{e['who']}　（{e['key']}）", 2)
    kv_table([("台词", e["line"]), ("结果", e["issue"] + (f"；句中停顿 {e['gaps']} s" if e["gaps"] else "")),
              ("模型 / 任务ID", f"{e['model']} / {e['task']}"), ("分辨率 / 时长", f"{e['res']} / {e['dur']} s（参考音频 {e['tts']} s）"),
              ("生成音频", e["audio"]), ("参考图（按顺序 图1、图2、图3）", "；".join(f"图{i+1} 参考图/{r}" for i, r in enumerate(e["refs"]))),
              ("参考音频", "；".join(f"参考音频/{a}（{d:.1f} s）" for a, d in e["auds"])), ("生成结果", f"生成结果_视频/{e['vid']}")])
    doc.add_paragraph("实际发送的提示词：")
    mono(e["prompt"])
    doc.add_picture(str(OUT / "生成结果_截帧" / e["strip"]), width=Cm(16))
    cap = doc.add_paragraph("生成结果截帧（5 帧均匀抽取）"); cap.runs[0].font.size = Pt(8)
for e in entries: add_entry(e)
doc.add_heading("附录 A：补拍后通过的 4 条（与 No.19 / No.22 / No.33 / No.34 对比）", 1)
doc.add_paragraph("补拍时只在【SHOT】表演说明里加了一句『注意：…必须清楚说出来，绝不能漏』，其余不变；两次补拍都说对了。")
for e in app: add_entry(e)
doc.add_heading("附录 B：问题样例（早期试拍 / 被淘汰的条，含当时的提示词）", 1)
doc.add_paragraph("E1–E3 为 2.0 mini 720p，E4 为 2.0 fast 720p，E5–E6 为 2.0 fast 480p。E1→E2→E3 的提示词和参考音频逐步调整，可对比看出差异。")
for e in smp: add_entry(e)
doc.save(OUT / "EP05_主持人镜头_Seedance提示词与参考.docx")
# put shared reference thumbnails into section 二 (re-open to insert is awkward; append a gallery page instead)
d2 = Document(OUT / "EP05_主持人镜头_Seedance提示词与参考.docx")
d2.add_heading("附：角色与布景参考图", 1)
for f in sorted((OUT / "参考图").iterdir()):
    if "定妆帧" in f.name or "plate" in f.name:
        d2.add_paragraph(f.stem); d2.add_picture(str(f), width=Cm(12))
d2.save(OUT / "EP05_主持人镜头_Seedance提示词与参考.docx")
(OUT / "说明.txt").write_text("EP05_主持人镜头_Seedance提示词与参考.docx：逐条提示词与参数（No. 与审片视频一致）\n参考图/：角色定妆帧、布景 plate、连续镜头用的上一镜末帧\n参考音频/：每条的参考音频（同一句台词的 TTS）\n生成结果_视频/：每条生成的原片\n生成结果_截帧/：每条 5 帧截图\n", encoding="utf-8")
z = ep / "EP05_Seedance提示词整理.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in OUT.rglob("*"):
        if f.is_file(): zf.write(f, f.relative_to(ep))
print("DOC_DONE", len(entries), "entries +", len(app), "retakes;", round(z.stat().st_size / 1e6, 1), "MB")
