"""Index existing C2S / HANDOFF / HISTORY / CURRENT, without copying or moving.
CURRENT is a role designation; filename similarity is not authority promotion.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(r"D:/Git PWA/TAKY")
INDEX=Path(r"D:/Git PWA/TAKY_AI_WORKBENCH/00_CONTROL/TAKY_SOURCE_RECORD_LOCATION_INDEX.json")
ROLES=("RAW", "C2S", "HANDOFF", "HISTORY", "CURRENT")
SOURCES=("C2S","HANDOFF","HISTORY","CURRENT")
def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as fp:
  for b in iter(lambda:fp.read(262144),b""):h.update(b)
 return h.hexdigest()
def records():
 out=[]
 for namespace in SOURCES:
  directory=ROOT/namespace
  if not directory.is_dir():raise FileNotFoundError(namespace)
  for f in sorted(directory.iterdir()):
   if not f.is_file():continue
   out.append({"source_group":namespace,
    "role":"CURRENT" if namespace=="CURRENT" else ("HISTORY" if namespace=="HISTORY" else namespace),
    "name":f.name,"path":str(f),"size":f.stat().st_size,"sha256":digest(f)})
 return out
def make():
 items=records(); hashes={}
 for item in items:hashes.setdefault(item["sha256"],[]).append(item["path"])
 return {"schema":"TAKY_SOURCE_RECORD_LOCATION_INDEX_V1",
         "authority_rule":"CURRENT_NAMESPACE_IS_LOGICAL_AUTHORITY_NOT_ANY_LATEST_NAMED_FILE",
         "immutable_source_policy":"NO_AUTO_DELETE_MOVE_OR_OVERWRITE",
         "physical_source_root":str(ROOT),
         "role_counts":{n:sum(x["source_group"]==n for x in items) for n in SOURCES},
         "exact_duplicate_groups":[v for v in hashes.values() if len(v)>1],
         "records":items}
def main():
 ap=argparse.ArgumentParser()
 ex=ap.add_mutually_exclusive_group(required=True)
 ex.add_argument("--build",action="store_true")
 ex.add_argument("--check",action="store_true")
 ex.add_argument("--lookup")
 args=ap.parse_args()
 if args.lookup:
  if not INDEX.is_file():raise SystemExit("INDEX_NOT_BUILT")
  data=json.loads(INDEX.read_text(encoding="utf-8"))
  matched=[x for x in data["records"] if x["name"]==args.lookup]
  print(json.dumps({"matches":matched},ensure_ascii=False,indent=2))
  return 0 if matched else 1
 current=make()
 if args.build:
  INDEX.parent.mkdir(parents=True,exist_ok=True)
  INDEX.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 else:
  if not INDEX.is_file():raise SystemExit("INDEX_MISSING")
  saved=json.loads(INDEX.read_text(encoding="utf-8"))
  if saved!=current:raise SystemExit("SOURCE_RECORD_DRIFT")
 print(json.dumps({"result":"PASS","role_counts":current["role_counts"],
   "exact_duplicate_groups":len(current["exact_duplicate_groups"]),
   "source_files_moved":False,"index_path":str(INDEX)},ensure_ascii=False))
 return 0
if __name__=="__main__":raise SystemExit(main())
