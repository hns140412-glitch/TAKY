"""Bounded gathering of eligible local references; no source deletion or recursive traversal."""
import sys,json,re,os,shutil,time
from pathlib import Path
sys.path.insert(0,r"D:\Git PWA\TAKY\ENFORCEMENT")
import taky_review_reference_intake as intake
roots=[Path(r"D:\#. BACKUP\카카오톡 받은 파일"),Path(r"D:\#. BACKUP\다운로드\통합심의서식"),Path(r"D:\#. BACKUP\다운로드")]
words=re.compile(r"가이드|지침|기준|매뉴얼|심의|법규|조례|설계도서|표준|참고|체크리스트|서식|사례|공사비|법령|법률|도서",re.I)
exclude=re.compile(r"계약|개인|주민|인감|사업자등록|통장|급여|보험|등기|신분|대외비|견적|청구|명단|연락처|소송|날인|서명|평가서.*개인|자격증",re.I)
ext={".pdf",".hwp",".hwpx",".docx",".xlsx",".xls",".pptx"}
subdirs=sorted((Path(e.path) for e in os.scandir(Path(r"D:\#. BACKUP\다운로드")) if e.is_dir(follow_symlinks=False) and not exclude.search(e.name)),key=lambda x:x.name.casefold())
roots+=subdirs[100:]
evid=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\REFERENCE\99_CONTROL\D_ADDITIONAL_GATHER_EVENTS.ndjson")
done=set()
if evid.exists():
 for line in evid.open(encoding="utf-8"):
  try:
   x=json.loads(line)
   if x["status"] in ("CAPTURED","DEDUPED"):done.add(x["source"])
  except (ValueError,KeyError):pass
n=0; b=0; stats={"eligible":0,"captured":0,"deduped":0,"errors":0,"bytes":0,"roots":{}}
for root in roots:
 if not root.is_dir():continue
 candidates=[]
 for entry in os.scandir(root):
  if not entry.is_file(follow_symlinks=False):continue
  p=Path(entry.path)
  if p.suffix.lower() not in ext or not words.search(p.name) or exclude.search(p.name) or p.name.startswith("~$"):continue
  s=entry.stat()
  if not 0<s.st_size<=40*1048576:continue
  candidates.append((p,s.st_size))
 stats["roots"][str(root)]=len(candidates);stats["eligible"]+=len(candidates)
 for p,size in sorted(candidates,key=lambda x:x[1]):
  if str(p) in done:continue
  if n>=75 or b+size>120*1048576:break
  if shutil.disk_usage(r"D:\Git PWA").free<80*1073741824:break
  try:
   r=intake.from_file(p,title="로컬 수집 참고자료 / "+p.name,consumer="ARCHI_GROW")
   state="CAPTURED" if r["new_physical_copy_created"] else "DEDUPED"
   stats["captured" if state=="CAPTURED" else "deduped"]+=1
   if state=="CAPTURED":stats["bytes"]+=size;b+=size
   record={"source":str(p),"canonical":r["canonical_path"],"sha256":r["sha256"],"bytes":size,"status":state}
  except Exception as ex:
   stats["errors"]+=1
   record={"source":str(p),"status":"ERROR","reason":str(ex)[:160]}
  evid.parent.mkdir(parents=True,exist_ok=True)
  with evid.open("a",encoding="utf-8") as f:f.write(json.dumps(record,ensure_ascii=False)+"\n")
  n+=1
  if n%5==0:print("PROGRESS",n,stats["captured"],stats["deduped"],flush=True)
stats["nonempty_roots"]={k:v for k,v in stats.pop("roots").items() if v};print(json.dumps(stats,ensure_ascii=False),flush=True)
