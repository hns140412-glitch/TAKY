# -*- coding: utf-8 -*-
"""TAKY HNS architectural reference workbook row projection (UNREVIEWED).
Read verified, SHA-bound XLSX derivations. Index rows and explicit ID links in the
existing central SQLite; do not alter approved CURRENT, geometry or app runtimes.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,sqlite3,sys
ROOT=pathlib.Path(r"D:\Git PWA")
sys.path.insert(0,str(ROOT/"TAKY_AI_WORKBENCH"/"40_AI_COLLAB"/"CODEX"))
sys.path.insert(0,str(ROOT/"TAKY"/"ENFORCEMENT"))
from work_reference_xlsx_reader_20261015 import FILES,BASE,load
import taky_central_source_factory as fac
WORKBOOKS={"REF":("1NXr40dDVG1pzLDJmesaXJ2svd-5oJSx3yQLRM1MAcCw","853f80e2f7288500fd81276d054fe8a6be82e4aabcc1025ac0bcd83433d0d49d"),
"METHOD":("18ieiIsf6LY_ohq_W_AWGt_kxzB1lhFSJkxzTjS3ZIuM","a4c827d1fe993b803ad3cc63b674fc6d43548fc33a2bc7084c9603183a2e15c1")}
SOURCE_KEYS={"REFERENCE_INDEX":"ID","ARCHIGROW_APPLICATION":"ITEM_ID","ARCHIGROW_SOURCES":"SOURCE_ID",
"ARCHIGROW_REPORT_REFS":"REF_USE_ID","ARCHIGROW_CAPABILITIES":"CAP_ID",
"ARCHIGROW_OFFICES_RND":"OFFICE_ID","ARCHIGROW_PUBLIC_DATA":"DATA_ID",
"DESIGN_OUTPUT_SPEC":"SPEC_ID","DESIGN_GATE":"GATE_ID",
"DESIGN_PRODUCTION_SPEC":"SPEC_ID","DESIGN_GATE_RUNS":"RUN_ID","METHOD_INDEX":"METHOD_ID"}
LINK_TAG=re.compile(r"(?<![A-Z0-9-])(?:REF-\d{3}|M-\d{3}|AG-[SDC]\d{2,3})(?![A-Z0-9])")
def sha(data):return hashlib.sha256(data).hexdigest()
def compact(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def prepare(conn):
 conn.executescript("""
 CREATE TABLE IF NOT EXISTS work_ref_row(
 source_id TEXT NOT NULL REFERENCES source(id), sheet TEXT NOT NULL,
 row_number INTEGER NOT NULL, record_id TEXT NOT NULL,
 row_sha256 TEXT NOT NULL, workbook_drive_id TEXT NOT NULL,
 source_status TEXT NOT NULL, original_json TEXT NOT NULL,
 search_text TEXT NOT NULL, review_state TEXT NOT NULL DEFAULT 'EXTRACTED_UNREVIEWED',
 PRIMARY KEY(source_id,sheet,row_number));
 CREATE INDEX IF NOT EXISTS work_ref_row_key ON work_ref_row(record_id);
 CREATE TABLE IF NOT EXISTS work_ref_link(
 source_id TEXT NOT NULL, record_id TEXT NOT NULL, target_record_id TEXT NOT NULL,
 link_basis TEXT NOT NULL, target_source_id TEXT NOT NULL,
 PRIMARY KEY(source_id,record_id,target_record_id,link_basis));
 CREATE INDEX IF NOT EXISTS work_ref_link_target ON work_ref_link(target_record_id);
 """)
def trusted(conn,which):
 fid,digest=WORKBOOKS[which];p=BASE/FILES[which]
 if not p.is_file() or sha(p.read_bytes())!=digest:raise RuntimeError("DERIVED_XLSX_SHA_MISMATCH:"+which)
 sid="raw:"+digest
 rows=conn.execute("""SELECT l.locator FROM location l JOIN source s ON s.id=l.source_id
 WHERE s.id=? AND s.original_sha256=? AND l.provider='LOCAL_FILE' AND l.account='TAKY_WORKBENCH_DERIVED'
 AND l.locator=?""",(sid,digest,str(p))).fetchall()
 rel=conn.execute("SELECT 1 FROM relation WHERE source_id=? AND consumer=? AND relation_type=?",
                  (sid,"GOOGLE_DRIVE:HNS:"+fid,"DERIVED_SPREADSHEET_EXPORT_FROM_NATIVE")).fetchone()
 if len(rows)!=1 or not rel:raise RuntimeError("CLOUD_EXPORT_PROVENANCE_NOT_BOUND:"+which)
 return sid,fid,digest
def extract(conn):
 rows=[];byid={};inventory={}
 for which in ("REF","METHOD"):
  sid,fid,digest=trusted(conn,which)
  sheets=load(which)
  for sheet,records in sheets.items():
   idkey=SOURCE_KEYS.get(sheet)
   if not idkey:raise RuntimeError("UNKNOWN_SOURCE_SHEET:"+sheet)
   inventory[sheet]=len(records)
   for entry in records:
    index=entry.get(idkey)
    if not index:raise RuntimeError("MISSING_PRIMARY_ID:"+sheet+":"+str(entry.get("__row__")))
    if index in byid:raise RuntimeError("DUPLICATE_REFERENCE_ID:"+index)
    rown=entry["__row__"];status=str(entry.get("STATUS",entry.get("SOURCE_STATUS",entry.get("REVIEW_RESULT","UNLABELED"))))
    contents=compact(entry)
    if len(contents)>150000:raise RuntimeError("ROW_SIZE_UNBOUNDED:"+index)
    record=(sid,sheet,rown,index,sha(contents.encode("utf-8")),fid,
         status,contents,contents.casefold(),"EXTRACTED_UNREVIEWED")
    rows.append(record)
    byid[index]=(sid,sheet,index)
 links=[]
 app=load("REF")["ARCHIGROW_APPLICATION"]
 link_integrity={"application_rows":len(app),"rows_with_no_explicit_link":0,"unresolved_explicit_tokens":[],"links":0,"complex_reference_not_expanded":[]}
 for item in app:
  id_=item["ITEM_ID"];src=byid[id_][0];found=set()
  for field in ("SOURCE_REF_ID","METHOD_ID"):
   value=item.get(field,"")
   if ".." in value or "/" in value or "Library " in value:
    link_integrity["complex_reference_not_expanded"].append({"id":id_,"field":field})
   for match in LINK_TAG.finditer(value):
    target=match.group(0)
    key=(target,field)
    if key in found:continue
    found.add(key)
    if target not in byid:
     link_integrity["unresolved_explicit_tokens"].append({"id":id_,"field":field,"target":target})
    else:links.append((src,id_,target,field,byid[target][0]))
  if not found:link_integrity["rows_with_no_explicit_link"]+=1
 link_integrity["links"]=len(links)
 return rows,links,inventory,link_integrity
def ingest(conn):
 prepare(conn)
 rows,links,inv,integrity=extract(conn)
 inserted=0;new_links=0
 with conn:
  for row in rows:
   existing=conn.execute("SELECT row_sha256 FROM work_ref_row WHERE source_id=? AND sheet=? AND row_number=?",
                       (row[0],row[1],row[2])).fetchone()
   if existing:
    if existing[0]!=row[4]:raise RuntimeError("SAME_SOURCE_ROW_CHANGED:"+row[3])
   else:
    conn.execute("INSERT INTO work_ref_row VALUES(?,?,?,?,?,?,?,?,?,?)",row)
    inserted+=1
  for link in links:
   before=conn.total_changes
   conn.execute("INSERT OR IGNORE INTO work_ref_link VALUES(?,?,?,?,?)",link)
   new_links+=conn.total_changes-before
  if conn.execute("PRAGMA quick_check").fetchone()[0]!="ok":raise RuntimeError("SQLITE_QUICK_CHECK_FAILED")
 return {"state":"INDEXED_ROW_PROJECTION_UNREVIEWED","workbooks":2,"worksheet_count":len(inv),
         "rows_total":len(rows),"rows_new":inserted,
         "links_total":len(links),"links_new":new_links,
         "sheets":inv,"links_validation":integrity,
         "semantic_approval":False,"forming_learning_applied":False,"app_runtime_modified":False}
def detail(conn,id_):
 rows=conn.execute("""SELECT source_id,sheet,row_number,workbook_drive_id,source_status,original_json,review_state
 FROM work_ref_row WHERE record_id=? ORDER BY sheet,row_number LIMIT 10""",(id_,)).fetchall()
 result=[]
 for row in rows:
  data=json.loads(row[5]);data.pop("__row__",None)
  links=conn.execute("SELECT target_record_id,link_basis FROM work_ref_link WHERE source_id=? AND record_id=? ORDER BY link_basis,target_record_id",
                     (row[0],id_)).fetchall()
  result.append({"record_id":id_,"sheet":row[1],"excel_row":row[2],
       "drive_document_id":row[3],"source_status":row[4],"review_state":row[6],
       "fields":data,"validated_links":[{"id":x[0],"from":x[1]} for x in links]})
 return {"query_id":id_,"records":result,"approved":False}
def search(conn,term,limit):
 if not isinstance(term,str) or not 2<=len(term)<=160:raise ValueError("QUERY_LENGTH_2_TO_160")
 # Search aliases are lexical translations, not source claims or semantic approvals.
 glossary={"주차장":["parking"],"단면":["section"],"평면":["floor plan","plan"],
  "동선":["circulation"],"접근":["access"],"도면":["drawing"],
  "조경":["landscape"],"마이닝":["mining"],"한남":["hannam"]}
 tokens=list(dict.fromkeys([term.strip().casefold(),*glossary.get(term.strip(),[])]))
 patterns=["%"+t.replace("\\","\\\\").replace("%","\\%").replace("_","\\_")+"%" for t in tokens]
 where=" OR ".join(["search_text LIKE ? ESCAPE '\\'"]*len(patterns))
 rows=conn.execute(f"""SELECT record_id,sheet,row_number,source_status,workbook_drive_id,original_json
  FROM work_ref_row WHERE ({where}) ORDER BY
   CASE WHEN lower(record_id)=? THEN 0 ELSE 1 END, sheet,row_number LIMIT ?""",
  [*patterns,term.strip().casefold(),limit]).fetchall()
 hits=[]
 for r in rows:
  data=json.loads(r[5]);title=next((data[k] for k in
   ("TITLE","TECHNIQUE","CAPABILITY","COMPONENT","SITE","RESOURCE","PURPOSE","DATASET / PLATFORM","METHOD_ID")
   if data.get(k)),"")
  hits.append({"id":r[0],"sheet":r[1],"row":r[2],"title":str(title)[:115],
   "status":r[3][:125],"drive_file_id":r[4]})
 return {"query":term,"hits":hits,"count":len(hits),"authority":"UNREVIEWED_DERIVED_PROJECTION"}
def verify(conn):
 a=conn.execute("SELECT COUNT(*),COUNT(DISTINCT record_id) FROM work_ref_row").fetchone()
 b=conn.execute("SELECT COUNT(*) FROM work_ref_link").fetchone()[0]
 return {"rows":a[0],"unique_record_ids":a[1],"links":b,
  "AG-002":detail(conn,"AG-002")["records"][0]["validated_links"],
  "method_026":bool(detail(conn,"M-026")["records"]),
  "quick_check":conn.execute("PRAGMA quick_check").fetchone()[0]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("action",choices=["index","search","detail","verify"])
 p.add_argument("value",nargs="?")
 p.add_argument("--limit",type=int,default=12)
 a=p.parse_args()
 if a.action in ("search","detail") and not a.value:p.error("search/detail requires a query/id")
 if not 1<=a.limit<=30:p.error("limit 1..30")
 with fac.connect() as c:
  if a.action=="index":result=ingest(c)
  elif a.action=="search":result=search(c,a.value,a.limit)
  elif a.action=="detail":result=detail(c,a.value)
  else:result=verify(c)
 print(json.dumps(result,ensure_ascii=True,indent=2),flush=True)
if __name__=="__main__":main()
