"""One-time SQLite rebind: metadata locator -> true WORKBENCH physical file.

No new source identity, data copy, or pipeline execution. Source records and
immutable event history remain. Requires 420 verified capture directory routes.
"""
import argparse,json,os,sqlite3
from pathlib import Path
R=Path(r"D:\Git PWA")
WAREHOUSE=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
OLD=R/"TAKY-SOURCE-VAULT"/"REFERENCE"
DB=WAREHOUSE/"99_CONTROL"/"SOURCE_UNIVERSE"/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3"
ROUTE=WAREHOUSE/"99_CONTROL"/"WEB_CAPTURE_CLASSIFICATION_CURRENT.json"
RECEIPT=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"WORKBENCH_SOURCE_LOCATOR_REBIND_20261013.json"
def plan():
 doc=json.loads(ROUTE.read_text(encoding="utf-8-sig"))
 mapping={x["name"]:Path(x["canonical_dir"]) for x in doc["records"]}
 if len(mapping)!=420:raise RuntimeError("CAPTURE_CLASSIFICATION_INCOMPLETE")
 conn=sqlite3.connect(str(DB),timeout=10)
 try:
  rows=conn.execute("SELECT provider,account,locator FROM location WHERE provider='LOCAL_FILE'").fetchall()
 finally:conn.close()
 old_count=0;changes=[];none=0
 for provider,account,loc in rows:
  p=Path(loc)
  try:rel=p.relative_to(OLD)
  except ValueError:
   if p.is_relative_to(WAREHOUSE):none+=1;continue
   raise RuntimeError("UNKNOWN_LOCAL_REFERENCE_SOURCE_OUTSIDE_WAREHOUSE:"+str(p))
  if rel.parts[0]=="WEB_SOURCE_ARCHIVE":
   if len(rel.parts)<3:raise RuntimeError("WEB_LEGACY_RELATIVE_FILEPATH_SHORT")
   capture=rel.parts[1]
   if capture not in mapping:raise RuntimeError("UNKNOWN_CAPTURE_FOLDER:"+capture)
   new=mapping[capture].joinpath(*rel.parts[2:])
  else:
   new=WAREHOUSE/rel
  if not new.is_file() or not p.is_file() or not os.path.samefile(new,p):
   raise RuntimeError("REBOUND_FILE_NOT_SAME_PHYSICAL:"+loc)
  changes.append((str(new),provider,account,loc))
  old_count+=1
 if len(changes)+none!=len(rows):raise RuntimeError("UNACCOUNTED_LOCAL_LOCATORS")
 return changes,none
def apply():
 changes,already=plan()
 if not changes:
  return {"status":"ALREADY_CENTRALIZED","physical_local_locations":already}
 conn=sqlite3.connect(str(DB),timeout=20)
 try:
  conn.execute("BEGIN IMMEDIATE")
  for new,provider,account,old in changes:
   conn.execute("UPDATE location SET locator=? WHERE provider=? AND account=? AND locator=?",
    (new,provider,account,old))
  remaining=conn.execute("SELECT COUNT(*) FROM location WHERE provider='LOCAL_FILE' AND locator LIKE ?",
   (str(OLD)+"%",)).fetchone()[0]
  if remaining:raise RuntimeError("OLD_LOCAL_LOCATORS_REMAIN:"+str(remaining))
  conn.execute("COMMIT")
 except BaseException:
  conn.rollback();raise
 finally:conn.close()
 doc={"status":"REFERENCE_DB_LOCATIONS_CANONICAL_WORKBENCH",
  "routes_updated":len(changes),"already_canonical":already,
  "source_row_id_changes":0,"drive_file_ids_untouched":True,
  "old_to_new_paths":[{"from":o,"to":n} for n,p,a,o in changes],
  "remaining_source_vault_physical_locators":0}
 temp=RECEIPT.with_suffix(".json.pending")
 temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 os.replace(temp,RECEIPT)
 return {"status":doc["status"],"routes_updated":len(changes),
   "already_canonical":already,"drive_file_ids_untouched":True}
if __name__=="__main__":
 a=argparse.ArgumentParser()
 g=a.add_mutually_exclusive_group(required=True)
 g.add_argument("--audit",action="store_true")
 g.add_argument("--apply",action="store_true")
 opt=a.parse_args()
 if opt.audit:
  changes,done=plan()
  result={"status":"READY" if changes else "COMPLETE","to_rebind":len(changes),"canonical":done}
 else:result=apply()
 print(json.dumps(result,ensure_ascii=False))
