"""Provenance-only index for verified local image bytes and locked Visual IDs.
An approved source record is NOT proof of live HNS authority migration/binding.
"""
import argparse,hashlib,json,sys
from pathlib import Path
R=Path("D:/Git PWA");T=R/"TAKY";W=R/"TAKY_AI_WORKBENCH"
KNOWN=R/"TAKY-ASSETS"/"registry"/"known-approved-provenance.json"
CREW=T/"MASTER"/"CREW24_VISUAL_ID_METADATA_BACKFILL_SOURCE_2026-10-08.json"
OUT=W/"00_CONTROL"/"TAKY_VISUAL_APPROVAL_REFERENCE_INDEX.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(262144),b""):h.update(b)
 return h.hexdigest()
def build():
 d=json.loads(KNOWN.read_text(encoding="utf-8-sig"))
 assert d["schema"]=="TAKY_KNOWN_APPROVAL_PROVENANCE_V1"
 approved=[]
 for x in d["assets"]:
  source=Path(x["source_path"])
  manifest=Path(x["source_manifest"])
  if not source.is_file() or sha(source)!=x["sha256"]:
   raise ValueError("PROVENANCE_LOCAL_SOURCE_HASH_MISMATCH:"+x["visual_id"])
  if not manifest.is_file():raise ValueError("APPROVAL_MANIFEST_MISSING:"+x["visual_id"])
  approved.append({
   "visual_id":x["visual_id"],"consumer_app":x["app"],
   "local_source_ref":str(source),"source_sha256":x["sha256"],
   "approval_evidence_manifest_ref":str(manifest),
   "upstream_approval_evidence_status":"LOCAL_SOURCE_AND_RECORDED_PROVENANCE_MATCH",
   "current_hns_master_binding":"UNVERIFIED",
   "actual_app_runtime_binding":x["runtime_binding"],
   "canonical_cloud_migration":x["canonical_migration"],
   "allowed_to_promote_current":False
  })
 crew=json.loads(CREW.read_text(encoding="utf-8-sig"))
 characters=[]
 for m in crew["members"]:
  characters.append({
   "visual_id":m["visual_id"],
   "canonical_code":m["canonical_code"],
   "canonical_name":m["canonical_name_ko"],
   "declared_drive_master_source":m["approved_source_path"],
   "declared_source_sha256":m["approved_source_sha256"],
   "source_lock_status":m["source_lock_status"],
   "local_source_bytes_verified":False,
   "actual_runtime_binding":"UNVERIFIED",
   "current_approval_migration_status":"ORIGINAL_RETRIEVAL_REQUIRED"
  })
 if len(characters)!=24 or len(approved)!=2:raise ValueError("UNEXPECTED_APPROVAL_SOURCE_COUNT")
 return {"schema":"TAKY_VISUAL_APPROVAL_REFERENCE_INDEX_V1",
   "source_authority":"CURRENT/DESIGN_UI_ASSET_SOURCE_DEFAULT_2026-09-29.json",
   "known_approved_local_provenance_count":len(approved),
   "crew_locked_metadata_count":len(characters),
   "verified_canonical_hns_master_file_count":0,
   "approved_asset_master_promoted":False,
   "raw_assets_moved_or_copied":False,
   "provenance_only":approved,"crew24_lock_metadata":characters}
def main():
 parser=argparse.ArgumentParser()
 group=parser.add_mutually_exclusive_group(required=True)
 group.add_argument("--build",action="store_true")
 group.add_argument("--check",action="store_true")
 args=parser.parse_args()
 doc=build()
 if args.build:
  tmp=OUT.with_suffix(".json.tmp")
  tmp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  tmp.replace(OUT)
 else:
  if not OUT.is_file() or json.loads(OUT.read_text(encoding="utf-8-sig"))!=doc:
   raise SystemExit("VISUAL_ASSET_REFERENCE_DRIFT")
 print(json.dumps({"status":"PASS","verified_provenance_assets":2,
   "locked_crew_metadata":24,"source_bytes_for_crew24_verified":False,
   "canonical_master_promotions":0,"index":str(OUT)},ensure_ascii=False))
if __name__=="__main__":sys.exit(main())
