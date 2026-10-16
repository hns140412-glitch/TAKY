from pathlib import Path
import sys,json,re,os
sys.path.insert(0,r"D:\Git PWA\TAKY\ENFORCEMENT")
import taky_review_reference_intake as intake
base=Path("C:/Users/YKH_1507-03/Desktop")/"드라이브"
roots=[base/"OLD"/"LEGACY_SHARED_TAKY-WORK-OS_2026-09-05"/"04_REFERENCE",base/"OLD"/"LEGACY_SHARED_TAKY-WORK-OS_2026-09-05"/"03_TEMPLATES",base]
allow={".pdf",".hwp",".hwpx",".docx",".xlsx",".xls",".pptx",".ppt"}
exclude=re.compile("계약|개인|주민|인감|사업자등록|통장|급여|보험|등기|신분|대외비|견적|청구|명단|연락처|소송|날인|서명|자격증",re.I)
receipt=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\REFERENCE\99_CONTROL\LOCAL_SHARED_REFERENCE_GATHER.ndjson")
done=set()
if receipt.exists():
 for l in receipt.open(encoding="utf-8"):
  try:
   j=json.loads(l)
   if j.get("status") in {"CAPTURED","DEDUPED"}:done.add(j["source"])
  except Exception:pass
candidate=[]
for root in roots:
 if not root.is_dir():continue
 if root==base:
  it=(p for p in root.iterdir() if p.is_file())
 else:
  it=(Path(d)/f for d,dirs,files in os.walk(root) for f in files)
 for p in it:
  if p.suffix.lower() not in allow or p.name.startswith("~$") or exclude.search(str(p.relative_to(base))):continue
  try:s=p.stat().st_size
  except OSError:continue
  if 0<s<=50*1048576:candidate.append((p,s))
out={"eligible":len(candidate),"previously_logged":0,"new":0,"deduped":0,"errors":0,"bytes":0}
for p,s in sorted(candidate,key=lambda t:t[1]):
 if str(p) in done:
  out["previously_logged"]+=1;continue
 if out["new"]+out["deduped"]+out["errors"]>=80:break
 try:
  r=intake.from_file(p,title="로컬 공유폴더 참고자료 / "+p.name,consumer="TAKY_REFERENCE")
  state="CAPTURED" if r["new_physical_copy_created"] else "DEDUPED"
  out["new" if state=="CAPTURED" else "deduped"]+=1
  if state=="CAPTURED":out["bytes"]+=s
  row={"source":str(p),"canonical":r["canonical_path"],"status":state,"sha256":r["sha256"]}
 except Exception as e:
  out["errors"]+=1;row={"source":str(p),"status":"ERROR","reason":str(e)[:150]}
 with receipt.open("a",encoding="utf-8") as f:f.write(json.dumps(row,ensure_ascii=False)+"\n")
print(json.dumps(out,ensure_ascii=False),flush=True)
