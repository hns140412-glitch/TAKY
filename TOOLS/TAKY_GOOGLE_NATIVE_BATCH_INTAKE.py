"""Ingest authenticated Drive-native text exports from Drive staging manifest.

Exports are derived text snapshots, not complete Google Docs bytes.
Safe to rerun; skips items whose staged file was already consumed and whose
Drive ID is backed by verified Workbench bytes.
"""
import base64,json,sqlite3,sys
from pathlib import Path
ROOT=Path(r"D:\Git PWA")
sys.path.insert(0,str(ROOT/"TAKY"/"TOOLS"))
import TAKY_GOOGLE_DRIVE_RAW_INTAKE as intake
STAGE=ROOT/"TAKY_AI_WORKBENCH"/"REFERENCE"/"00_INBOX"/"DRIVE_RAW_STAGE"
RESULTS=ROOT/"TAKY_AI_WORKBENCH"/"REFERENCE"/"99_CONTROL"/"DRIVE_NATIVE_EXPORT_INGEST_EVENTS.ndjson"
manifest=STAGE/"NATIVE_EXPORT_BATCH.json"
inputs=json.loads(manifest.read_text(encoding="utf-8-sig"))["items"]
out=[]
for i in inputs:
 stage=STAGE/(i["account"]+"_"+i["drive_id"]+".b64")
 if not stage.exists():
  with sqlite3.connect(str(ROOT/"TAKY_AI_WORKBENCH"/"REFERENCE"/"99_CONTROL"/"SOURCE_UNIVERSE"/"TAKY_CENTRAL_SOURCE_FACTORY.sqlite3")) as c:
   row=c.execute("""SELECT s.original_sha256 FROM location l JOIN source s ON
    l.source_id=s.id WHERE l.provider='GOOGLE_DRIVE' AND l.account=? AND l.locator=?""",
    (i["account"],i["drive_id"])).fetchone()
   if row and row[0]:
    out.append({"id":i["drive_id"],"status":"ALREADY_IMPORTED"})
    continue
  out.append({"id":i["drive_id"],"status":"MISSING_TRANSPORT_BYTES"})
  continue
 try:
  if not i.get('bytes'):
   i['bytes']=len(base64.b64decode(''.join(stage.read_text(encoding='ascii').split()),validate=True))
  result=intake.original(i)
  out.append({"id":i["drive_id"],"status":"IMPORTED","sha256":result["sha256"],"size_bytes":result["size_bytes"]})
 except Exception as ex:
  out.append({"id":i["drive_id"],"status":"ERROR","error":type(ex).__name__,"detail":str(ex)[:180]})
RESULTS.parent.mkdir(parents=True,exist_ok=True)
with RESULTS.open("a",encoding="utf-8") as w:
 for item in out:w.write(json.dumps(item,ensure_ascii=False)+"\n")
print(json.dumps({"status":"NATIVE_EXPORT_BATCH_DONE",
 "requested":len(inputs),"imported":sum(x["status"]=="IMPORTED" for x in out),
 "already":sum(x["status"]=="ALREADY_IMPORTED" for x in out),
 "failed":[x for x in out if x["status"] not in ("IMPORTED","ALREADY_IMPORTED")]},ensure_ascii=False))
