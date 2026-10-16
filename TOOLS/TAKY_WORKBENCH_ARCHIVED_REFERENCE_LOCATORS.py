"""Resolve 221 legacy raw-sha references to categorized WORKBENCH physical paths."""
import json,os,sqlite3
from pathlib import Path
R=Path(r"D:\Git PWA")
WB=R/"TAKY_AI_WORKBENCH"/"REFERENCE"
DB=WB/"99_CONTROL"/"SOURCE_UNIVERSE"/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3"
IDX=R/"TAKY_AI_WORKBENCH"/"00_CONTROL"/"TAKY_REFERENCE_UNIVERSE_INDEX.json"
EVIDENCE=R/"TAKY_AI_WORKBENCH"/"01_BACKLOG_AND_ADOPTION"/"80_EVIDENCE"/"LEGACY_REFERENCE_221_SQLITE_ROUTE_20261013.json"
def apply():
 records=json.loads(IDX.read_text(encoding="utf-8-sig"))["items"]
 if len(records)!=221:raise RuntimeError("REFERENCE_221_INDEX_MISSING")
 updated=0
 db=sqlite3.connect(str(DB),timeout=15)
 try:
  db.execute("BEGIN IMMEDIATE")
  for rec in records:
   legacy=str(WB/rec["relative_path"])
   actual=rec["physical_path"]
   if not Path(actual).is_file() or not Path(legacy).is_file() or not os.path.samefile(legacy,actual):
    raise RuntimeError("REFERENCE_221_PHYSICAL_CLASSIFICATION_MISMATCH:"+rec["relative_path"])
   if legacy==actual:continue
   cur=db.execute("""UPDATE location SET locator=? WHERE provider='LOCAL_FILE'
      AND account='TAKY_SOURCE_VAULT' AND locator=?""",(actual,legacy))
   updated+=cur.rowcount
  db.commit()
 finally:db.close()
 EVIDENCE.parent.mkdir(parents=True,exist_ok=True)
 EVIDENCE.write_text(json.dumps({"status":"DONE","canonical_reference_db":str(DB),
  "migrated_legacy_221_physical_routes":updated,
  "source_records_unchanged":True,"drive_file_refs_unchanged":True},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return {"status":"PASS","ref_paths_changed":updated}
if __name__=="__main__":print(json.dumps(apply(),ensure_ascii=False))
