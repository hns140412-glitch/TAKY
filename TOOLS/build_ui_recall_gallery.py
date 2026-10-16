from pathlib import Path
import os,json,html,datetime
root=Path(r"D:\Git PWA")
wb=root/"TAKY_AI_WORKBENCH"
apps={"READY-SET":"Ready & Set","HIDE-SEEK":"Hide & Seek","PLAY-CAMP":"Play Camp","SNAP-POP":"Snap & Pop","SAVEY":"SAVEY","TAKY-MOBILE":"TAKY-MOBILE","TAKY_ARCHI-GROW":"TAKY_ARCHI GROW"}
skip={".git","node_modules",".local","dist","build",".venv","__pycache__"}
selected=[]
for alias,folder in apps.items():
 base=root/folder
 for parent,dirs,files in os.walk(base):
  dirs[:]=[d for d in dirs if d not in skip]
  for name in files:
   p=Path(parent)/name
   if p.suffix.lower() not in {".png",".jpg",".jpeg",".webp"}:continue
   rel=p.relative_to(base).as_posix()
   low=rel.lower()
   if folder=="TAKY_ARCHI GROW" and "runtime/apps/" in low:continue
   if any(k in low for k in ("node_modules","characters/ui_cutouts","turnaround-front","icons/")):continue
   if not any(k in low for k in ("screenshot","screen","design","mock","final","home","hero","artifacts","reference","ui")):continue
   if "guide-" in low or "icon-" in low: continue
   state="REVIEW_NEEDED"
   if "candidate" in low or "mock" in low:state="DRAFT_OR_CANDIDATE"
   if "fail" in low:state="REJECTED_OR_FAILED"
   selected.append({"app":alias,"file":str(p),"relative":rel,"label":p.stem,"classification":state,"approval":"NOT_VERIFIED","ui_state":"UNMAPPED","approval_evidence":None,"implementation_match":"UNVERIFIED"})
selected.sort(key=lambda x:(x["app"],x["relative"]))
out=wb/"20_DESIGN_STUDIO"/"UI-UX"
(out/"INDEX").mkdir(parents=True,exist_ok=True)
data={"schema":"TAKY_UI_SCREEN_RECALL_INDEX_V1","generated_at":datetime.datetime.now().isoformat(),"disclaimer":"File/name is not proof of approval; read-only pointers, never a duplicate original.","items":selected}
(out/"INDEX"/"SCREEN_INVENTORY.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
groups={}
for d in selected:groups.setdefault(d["app"],[]).append(d)
style="""body{font:14px system-ui;background:#101725;color:#e8edf5;margin:0;padding:25px}h1{font-size:25px}section{margin:30px 0}h2{border-bottom:1px solid #43516a;padding-bottom:12px} .gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:15px}.tile{background:#1c293b;padding:10px;border-radius:12px;overflow:hidden}.tile img{width:100%;height:240px;object-fit:contain;background:#101725}.meta{font-size:11px;color:#b7c7dd;overflow-wrap:anywhere}.warning{padding:14px;border:1px solid #756242;border-radius:12px}a{color:#9cd1ff}"""
parts=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>TAKY UI 시안 회상 갤러리</title><style>'+style+'</style><body><h1>TAKY UI 시안 회상 갤러리</h1><p class="warning">⚠️ 확정 여부 미검증: 파일명 FINAL/GOLDEN도 승인 증거가 아닙니다. 이미지는 원본 파일을 직접 참조합니다. 이 갤러리는 복사본을 생성하지 않습니다.</p><p>프로젝트별로 실제 존재하는 화면·시안 파일을 찾아볼 수 있습니다. 원본 이미지를 클릭하면 원래 파일 위치가 열립니다.</p>']
for name,items in groups.items():
 parts.append(f'<section><h2>{html.escape(name)} — {len(items)}건</h2><div class="gallery">')
 for d in items:
  uri=Path(d["file"]).as_uri()
  parts.append(f'<article class="tile"><a href="{html.escape(uri,quote=True)}"><img loading="lazy" src="{html.escape(uri,quote=True)}"></a><p>{html.escape(d["label"])}</p><p class="meta">{html.escape(d["relative"])}</p><p class="meta">승인 미검증 · 실제 구현 미검증</p></article>')
 parts.append('</div></section>')
parts.append('</body></html>')
(out/"TAKY_UI_SCREEN_GALLERY.html").write_text("\n".join(parts),encoding="utf-8")
readme=out/"README_UI_SCREEN_RECALL.md"
readme.write_text("# TAKY UI 시안 회상 인덱스\n\n- [갤러리](TAKY_UI_SCREEN_GALLERY.html) 파일을 로컬 브라우저에서 엽니다.\n- INDEX/SCREEN_INVENTORY.json은 실제 이미지 위치를 참조합니다. 승인 인증이 아닙니다.\n- FINAL / GOLDEN 등의 파일명은 상태 증거가 아닙니다.\n- 승인 원본의 SHA·Visual ID·사용자 승인 이력과 화면 상태를 대조한 후에만 APPROVED로 변경합니다.\n- 앱별 확정 UI, 초안, 실제 구현 화면을 각각 구분할 예정입니다.\n- 이미지 원본은 옮기거나 복제하지 않았습니다.\n",encoding="utf-8")
print(json.dumps({"total":len(selected),"by_app":{k:len(v) for k,v in groups.items()},"gallery":str(out/"TAKY_UI_SCREEN_GALLERY.html")},ensure_ascii=False))
