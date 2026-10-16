"""Physical classification of the 221 earlier references; retain paths.

Architecture docs => 20_ARCHITECTURE/PROJECT_RECORDS (NTFS hardlink alias).
Claude reference skills => 30_AI_TECH/CLAUDE_SKILLS (junction).
Generated architectural output examples => 90_DERIVED/ARCHCOMP_OUTPUT_BUILD_TEST.
No content copies; original hashes and callers retain their old paths.
"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
R=Path(r"D:\Git PWA")
WB=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
ROOT_DOCS=(
 "ARCHIGROW_COMPETITION_BRIEF_SAMPLE.json",
 "ARCHIGROW_COMPETITION_REPORT_SAMPLE_URBAN_CIVIC.md",
 "ARCHIGROW_COMPETITION_REPORT_SAMPLE_WITH_BRIEF.md",
 "ARCHIGROW_LEARNING_BINDING_LEDGER_2026-10-12.json",
 "ARCHITECTURE_COMPETITION_PUBLIC_SOURCE_REGISTRY.json",
 "ARCHITECTURE_COMPETITION_REPRESENTATION_EVIDENCE_2026-10-03.json"
)
MOVES=(
 ("ARCHCOMP_OUTPUT_BUILD_TEST","90_DERIVED/ARCHCOMP_OUTPUT_BUILD_TEST"),
 ("CLAUDE_SKILLS","30_AI_TECH/CLAUDE_SKILLS")
)
RECEIPT=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"WORKBENCH_LEGACY_REFERENCE_CLASSIFICATION_20261013.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(262144),b""):h.update(b)
 return h.hexdigest()
def junction(src,dst):
 result=subprocess.run(["cmd.exe","/c","mklink","/J",str(src),str(dst)],
  capture_output=True,text=True,errors="replace",timeout=12)
 if result.returncode or not src.is_junction() or not os.path.samefile(src,dst):
  raise RuntimeError("JUNCTION_CREATION_FAILED:"+str(src))
def one_file(name,apply):
 old=WB/name
 dest=WB/"20_ARCHITECTURE"/"PROJECT_RECORDS"/name
 if dest.is_file():
  if not old.is_file() or not os.path.samefile(old,dest):raise RuntimeError("DOC_HARDLINK_NOT_PRESENT:"+name)
  return {"name":name,"status":"ALREADY_LINKED","sha256":sha(dest)}
 if not old.is_file():raise RuntimeError("LEGACY_ARCH_DOC_MISSING:"+name)
 expected=sha(old)
 if not apply:return {"name":name,"status":"READY","sha256":expected}
 dest.parent.mkdir(parents=True,exist_ok=True)
 os.rename(old,dest)
 try:
  os.link(dest,old) # physically one NTFS file, two path references.
  if not os.path.samefile(dest,old) or sha(dest)!=expected:raise RuntimeError("NTFS_HARDLINK_ORIGINAL_DRIFT")
 except:
  if not old.exists() and dest.exists():os.rename(dest,old)
  raise
 return {"name":name,"status":"MOVED_WITH_HARDLINK_ALIAS","sha256":expected}
def one_dir(source_rel,target_rel,apply):
 source=WB/source_rel;dest=WB/target_rel
 if dest.is_dir():
  if not source.is_junction() or not os.path.samefile(source,dest):
   raise RuntimeError("DIR_ALIAS_MISSING:"+source_rel)
  return {"name":source_rel,"status":"ALREADY_LINKED"}
 if not source.is_dir() or source.is_junction():
  raise RuntimeError("LEGACY_DIRECTORY_INVALID:"+source_rel)
 if not apply:return {"name":source_rel,"status":"READY"}
 dest.parent.mkdir(parents=True,exist_ok=True)
 os.rename(source,dest)
 try:junction(source,dest)
 except:
  if not source.exists():os.rename(dest,source)
  raise
 return {"name":source_rel,"status":"MOVED_WITH_JUNCTION_ALIAS"}
def main():
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 a=p.parse_args()
 actions=[one_file(n,a.apply) for n in ROOT_DOCS]+[one_dir(n,t,a.apply) for n,t in MOVES]
 if a.apply:
  RECEIPT.parent.mkdir(parents=True,exist_ok=True)
  rec={"status":"WORKBENCH_LEGACY_REFERENCE_CATEGORIZED",
   "actions":actions,"physical_duplication":False,
   "legacy_paths_preserved":True,"hardlinks_created":6,"junctions_created":2}
  temp=RECEIPT.with_suffix(".json.tmp")
  temp.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  os.replace(temp,RECEIPT)
 return {"status":"APPLIED" if a.apply else "PRECHECK","docs":len(ROOT_DOCS),
  "directories":len(MOVES),"all_paths_resolve":all((WB/n).exists() for n in ROOT_DOCS)}
if __name__=="__main__":print(json.dumps(main(),ensure_ascii=False))
