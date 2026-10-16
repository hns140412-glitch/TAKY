"""Bounded single-window gathering of architectural reference files in D downloads.

Only direct files with design/permit/legislation keywords, no other backup roots.
Exclude personal identity/contract artifacts, Office lock files and executables.
Never delete/move source. Verified originals deduped via central intake gateway.
"""
import argparse,json,re,sys,time,os,shutil
from pathlib import Path
ROOT=Path(r"D:\Git PWA")
SRC=Path(r"D:\#. BACKUP\다운로드")
sys.path.insert(0,str(ROOT/"TAKY"/"ENFORCEMENT"))
import taky_review_reference_intake as intake
EVID=ROOT/"TAKY_AI_WORKBENCH"/"REFERENCE"/"99_CONTROL"/"D_DOWNLOADS_ARCH_REFERENCE_GATHER_EVENTS.ndjson"
PATTERN=re.compile("건축|심의|환경|소방|교통|시방|도서|도면|법규|조례|지침|평가|도시|CAD|레이어|면적|공모|허가|구조|기계설비|정비사업|통합심의|주차|경관|분양",re.I)
EXCLUDE=re.compile("주민등록|개인정보|계약서|명의변경|인감|신분증|사업자등록증|통장사본|서명|여권|증명사진|신용카드|세금계산서|법인등기|급여",re.I)
EXT={".pdf",".hwp",".hwpx",".pptx",".xlsx",".xls",".docx",".dwg",".zip"}
def candidates():
 if not SRC.is_dir():raise RuntimeError("USER_BACKUP_DOWNLOAD_ROOT_ABSENT")
 items=[]
 for file in SRC.iterdir():
  if not file.is_file() or file.is_symlink():continue
  if file.name.startswith(("~$","._")) or EXCLUDE.search(file.name):continue
  if file.suffix.lower() not in EXT or not PATTERN.search(file.name):continue
  stat=file.stat()
  if stat.st_size<=0 or stat.st_size>80*1048576:continue
  items.append((file,stat))
 return sorted(items,key=lambda t:(t[1].st_size,t[0].name.casefold()))
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 p.add_argument("--max-files",type=int,default=180)
 p.add_argument("--budget-mib",type=int,default=550)
 a=p.parse_args()
 prior={}
 if EVID.is_file():
  for line in EVID.read_text(encoding="utf-8-sig").splitlines():
   try:
    x=json.loads(line)
    if x.get("status") in ("CAPTURED","DEDUPED"):
     prior[(x["source"],x["bytes"],x["modified_ns"])]=x["canonical"]
   except (ValueError,KeyError):pass
 results=[]
 source_items=candidates()
 n_new=0;bytes_written=0
 for file,stat in source_items:
  if n_new>=a.max_files or bytes_written>=a.budget_mib*1048576:break
  signature=(str(file),stat.st_size,stat.st_mtime_ns)
  if signature in prior and Path(prior[signature]).is_file():continue
  if bytes_written+stat.st_size>a.budget_mib*1048576:continue
  if shutil.disk_usage(str(ROOT)).free<65*1073741824:
   results.append({"status":"LOW_FREE_DISK_HOLD"});break
  if not a.apply:
   n_new+=1;bytes_written+=stat.st_size;continue
  try:
   item=intake.from_file(file,
      title="건축설계 법규 심의 참고 / "+file.name,
      consumer="ARCHI_GROW")
   out={"status":"CAPTURED" if item["new_physical_copy_created"] else "DEDUPED",
    "source":str(file),"bytes":stat.st_size,"modified_ns":stat.st_mtime_ns,
    "canonical":item["canonical_path"],"sha256":item["sha256"],
    "source_id":item["source_id"]}
  except Exception as e:
   out={"status":"ERROR","source":str(file),"bytes":stat.st_size,
    "reason":type(e).__name__,"detail":str(e)[:120]}
  results.append(out)
  n_new+=1
  if out["status"]=="CAPTURED":bytes_written+=stat.st_size
  EVID.parent.mkdir(parents=True,exist_ok=True)
  with EVID.open("a",encoding="utf-8") as fp:fp.write(json.dumps(out,ensure_ascii=False)+"\n")
  if n_new%20==0:print("DOWNLOADED_REFS",n_new,round(bytes_written/1048576,1),"MiB",flush=True)
 status={"mode":"APPLIED" if a.apply else "AUDIT",
  "reference_candidates":len(source_items),
  "attempted":n_new,"new_copy_bytes":bytes_written,
  "status_counts":{v:sum(x.get("status")==v for x in results) for v in set(x.get("status") for x in results)},
  "original_files_modified":0,"all_candidates_gathered":False}
 print(json.dumps(status,ensure_ascii=False))
if __name__=="__main__":main()
