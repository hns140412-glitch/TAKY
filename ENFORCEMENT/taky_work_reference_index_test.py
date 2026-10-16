# -*- coding: utf-8 -*-
"""Independent bounded regression for two SHA-verified Work workbook projections."""
import sys,sqlite3,json,pathlib
sys.path.insert(0,r"D:\Git PWA\TAKY\ENFORCEMENT")
import taky_work_reference_index as idx
import taky_central_source_factory as f
checks={}
with f.connect() as db:
 a=idx.verify(db)
 checks["rows_459_and_unique"]=a["rows"]==459 and a["unique_record_ids"]==459
 checks["links_59"]=a["links"]==59
 checks["quick_check"]=a["quick_check"]=="ok"
 checks["foreign_keys"]=not db.execute("PRAGMA foreign_key_check").fetchall()
 q=idx.detail(db,"AG-002")["records"]
 checks["parking_row_exact_source"]=len(q)==1 and q[0]["sheet"]=="ARCHIGROW_APPLICATION" and q[0]["excel_row"]==3 and q[0]["source_status"]=="PROPOSED_NOT_APPLIED"
 checks["parking_evidence_gap_preserved"]=bool(q) and "parking count" in q[0]["fields"].get("EVIDENCE_GAP","")
 checks["parking_3_valid_links"]={x["id"] for x in q[0]["validated_links"]}=={"REF-039","M-017","M-026"}
 checks["Korean_lexical_search"]=any(x["id"]=="AG-002" for x in idx.search(db,"주차장",10)["hits"])
 checks["ref_method_search_exact"]=any(x["id"]=="M-026" for x in idx.search(db,"M-026",10)["hits"])
 checks["literal_percent_not_wildcard"]=idx.search(db,"M-0%",10)["count"]==0
 checks["missing_id_safe"]=idx.detail(db,"AG-NO-EXIST")["records"]==[]
 hold=idx.detail(db,"AG-006")["records"]
 checks["hold_no_approval"]=len(hold)==1 and hold[0]["source_status"]=="FACT_CONFLICT_HOLD" and hold[0]["review_state"]=="EXTRACTED_UNREVIEWED"
 checks["methods_not_approved"]=idx.detail(db,"M-026")["records"][0]["review_state"]=="EXTRACTED_UNREVIEWED"
 for kind in idx.WORKBOOKS:
  try:idx.trusted(db,kind)
  except:checks["SHA_provenance_"+kind]=False
  else:checks["SHA_provenance_"+kind]=True
 for kind in idx.WORKBOOKS:
  sid="raw:"+idx.WORKBOOKS[kind][1]
  s=db.execute("SELECT authoritative_review FROM source WHERE id=?",(sid,)).fetchone()
  checks["source_remains_UNREVIEWED_"+kind]=bool(s) and s[0]=="UNREVIEWED"
 report={"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"passes":sum(checks.values()),"total":len(checks)}
 print(json.dumps(report,ensure_ascii=True),flush=True)
if report["status"]!="PASS":raise SystemExit(2)
