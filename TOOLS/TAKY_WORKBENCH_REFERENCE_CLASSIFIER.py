"""WORKBENCH physical web-capture classification, old source URL paths retained.

420 old WEB_SOURCE_ARCHIVE capture directories move ATOMICALLY on D: into
domain buckets. Each legacy capture directory becomes a Windows junction.
Classifications are heuristic candidates; approval must not be inferred.
"""
import argparse,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\REFERENCE")
LEGACY=ROOT/"WEB_SOURCE_ARCHIVE"
CONTROL=ROOT/"99_CONTROL"
INDEX=CONTROL/"WEB_CAPTURE_CLASSIFICATION_CURRENT.json"
RECEIPT=CONTROL/"WEB_CAPTURE_REHOME_RECEIPT.json"
DOMAINS={
 "10_LEARNING":r"교육|학습|초등|중등|수학|국어|영어|과학|역사|한자|독서|독후|문제집|교과|어휘|학생|시험|학교|유아|영영사전|학년|공부|교육청|토익|TOEFL|reading|vocab|school",
 "20_ARCHITECTURE":r"건축|설계|건설|인허가|주택|공모전|도시계획|정비사업|오토캐드|캐드|CAD\b|아키그로우|ARCHI|건축법|아파트|도면|landscape architecture|revit|rhino|autocad|bim",
 "30_AI_TECH":r"인공지능|챗지피티|GPT|OpenAI|코덱스|Codex|Claude|클로드|MCP\b|AI\b|agent|에이전트|자동화|스킬|skill|프롬프트|prompt|n8n|git\b|github|notion|노션|LLM|API\b|vibe.?coding|바이브코딩|cursor|gemini|안티그래비티",
 "40_DESIGN_MEDIA":r"디자인|디자이너|Figma|피그마|아이콘|illustrat|영상제작|편집|유튜브|에셋|UI\b|UX\b|이미지|브랜딩|사진|PPT|슬라이드|캔바|Canva|3D.?모델|Midjourney|픽셀|인포그래픽|포토샵",
 "50_GENERAL":r"요리|여행|건강|맛집|생활|자동차|생활비|세금|법률|금융|경제|보험|가계부|부동산",
}
def category(name):
 text=re.sub(r"^\d{4}-\d\d-\d\dT[\d-]+Z_","",name)
 for k,pat in DOMAINS.items():
  if re.search(pat,text,re.I):return k
 return "80_UNCLASSIFIED"
def dst(name):
 return ROOT/category(name)/"WEB_CAPTURE"/name
def list_sources():
 if not LEGACY.is_dir():raise RuntimeError("LEGACY_WEB_CAPTURE_FOLDER_MISSING")
 return sorted(p for p in LEGACY.iterdir() if p.is_dir())
def isjunction(p):
 return p.is_dir() and os.path.isjunction(p)
def handle(p,apply):
 target=dst(p.name)
 if target.is_dir():
  if not isjunction(p) or not os.path.samefile(p,target):
   raise RuntimeError("DEST_COLLISION_OR_LEGACY_ALIAS_DRIFT:"+p.name)
  return "ALREADY_CLASSIFIED"
 if isjunction(p):
  raise RuntimeError("UNEXPECTED_LEGACY_CAPTURE_JUNCTION:"+p.name)
 if not p.is_dir():raise RuntimeError("LEGACY_SOURCE_MISSING:"+p.name)
 if not apply:return "READY"
 target.parent.mkdir(parents=True,exist_ok=True)
 os.rename(p,target)
 try:
  result=subprocess.run(["cmd.exe","/c","mklink","/J",str(p),str(target)],
    capture_output=True,text=True,errors="replace",timeout=12)
  if result.returncode or not isjunction(p) or not os.path.samefile(p,target):
   raise RuntimeError("MAKE_JUNCTION_FAILED:"+p.name+":"+result.stderr[-150:])
 except BaseException:
  if target.is_dir() and not p.exists():os.rename(target,p)
  raise
 return "CLASSIFIED_WITH_COMPAT_ALIAS"
def run(apply=False):
 if not ROOT.is_dir():raise RuntimeError("WORKBENCH_REFERENCE_NOT_FOUND")
 entries=list_sources()
 # Historic one-shot physical classifier must never overwrite a later
 # content-reviewed manifest or reroute its canonical directories by title.
 # Both --audit and --apply are read-only once the 420-record index exists.
 if INDEX.is_file():
  doc=json.loads(INDEX.read_text(encoding="utf-8-sig"))
  indexed={x["name"]:x for x in doc.get("records",[])}
  captures=[x for x in entries if x.name in indexed]
  extra=[x.name for x in entries if x.name not in indexed]
  # Existing HNS_LEGACY_202609 is a separate physical historic branch;
  # it is not one of the 420 captured website revisions.
  if (len(captures)!=420 or len(indexed)!=420
   or len(doc.get("source_groups",[]))!=109
   or doc.get("historical_hns_202609_union",{}).get("indexed_http200_revisions")!=84
   or sorted(extra)!=["HNS_LEGACY_202609"]):
   raise RuntimeError("CAPTURE_MANIFEST_HISTORY_DRIFT")
  if {x.name for x in captures}!=set(indexed):
   raise RuntimeError("LEGACY_CAPTURE_NAMES_DRIFT")
  for old in captures:
   new=Path(indexed[old.name]["canonical_dir"])
   if not (old.is_junction() and new.is_dir() and os.path.samefile(old,new)):
    raise RuntimeError("CURRENT_REFERENCE_ALIAS_DRIFT:"+old.name)
  return {"status":"CURRENT_CLASSIFICATION_PRESERVED",
   "source_groups":109,"captures":420,
   "category_totals":doc["category_totals"],
   "legacy_paths_verified":len(captures),
   "other_historical_branch_preserved":extra,
   "old_one_shot_apply_blocked":bool(apply),
   "manifest_rewritten":False}
 if len(entries)!=420:
  raise RuntimeError("CAPTURE_SOURCE_FOLDER_COUNT_DRIFT:"+str(len(entries)))
 if any(p.is_file() for p in LEGACY.iterdir()):
  raise RuntimeError("UNREVIEWED_WEB_CAPTURE_ROOT_FILES")
 if len({p.name for p in entries})!=len(entries):
  raise RuntimeError("DUPLICATE_CAPTURE_ENTRY")
 records=[];counts={}
 for n,p in enumerate(entries,1):
  state=handle(p,apply)
  domain=category(p.name)
  counts[domain]=counts.get(domain,0)+1
  records.append({"name":p.name,"category":domain,
   "canonical_dir":str(dst(p.name)),"legacy_compat_dir":str(p),
   "classification":"HEURISTIC_UNREVIEWED","state":state})
  if apply and n%70==0:print("CLASSIFIED_CAPTURE_FOLDERS",n,flush=True)
 if apply:
  CONTROL.mkdir(parents=True,exist_ok=True)
  d={"schema":"TAKY_WORKBENCH_WEB_CAPTURE_CLASSIFICATION_V1",
   "physical_reference_root":str(ROOT),
   "total_capture_dirs":len(records),"category_totals":counts,
   "heuristic_labels_not_approved":True,"records":records,
   "source_vault_pipeline_only":True,
   "legacy_web_capture_paths_preserved":True,
   "data_copies_created":0}
  for file,obj in ((INDEX,d),(RECEIPT,{"status":"CLASSIFICATION_REHOME_VERIFIED",
    "folder_count":len(records),"groups":counts})):
   tmp=file.with_suffix(file.suffix+".pending")
   tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
   os.replace(tmp,file)
 return {"status":"CLASSIFIED" if apply else "READY_TO_CLASSIFY",
  "folders":len(entries),"group_counts":counts,
  "classification_is_heuristic":True,"legacy_paths_maintained":True}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 group=p.add_mutually_exclusive_group(required=True)
 group.add_argument("--audit",action="store_true")
 group.add_argument("--apply",action="store_true")
 a=p.parse_args()
 print(json.dumps(run(a.apply),ensure_ascii=False))
