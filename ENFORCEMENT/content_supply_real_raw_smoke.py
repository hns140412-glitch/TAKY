"""Materialize one real-RAW local candidate and immutable E2E receipt in staging."""
import hashlib
import json
from pathlib import Path
from content_supply_runner import execute
from content_supply_atomic import publish_bytes

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT.parent/"Play Camp"
DEST=ROOT.parent/"TAKY_AI_WORKBENCH"/"50_INTEGRATION_TEST"/"CONTENT_SUPPLY"/"content_supply_p0"
RAW_REL="LEARNING/data/official-snapshots/standard-object-2022-elementary-v1.json"
SOURCE_ID="TAKY:official-snapshots/standard-object-2022-elementary-v1.json"

def ensure_immutable(path, data):
    rendered=json.dumps(data,sort_keys=True,ensure_ascii=False,indent=2).encode("utf-8")+b"\n"
    try:
        publish_bytes(path, rendered)
    except FileExistsError as exc:
        raise RuntimeError('STAGING_RECEIPT_CONFLICT: '+str(path)) from exc

def main():
    raw=ROOT/RAW_REL
    if not raw.is_file():
        raise RuntimeError("RAW_UNAVAILABLE")
    digest=hashlib.sha256(raw.read_bytes()).hexdigest()
    DEST.mkdir(parents=True,exist_ok=True)
    contract={"demand_id":"TAKY-P0-REAL-RAW-SMOKE","consumer":"PLAY_CAMP",
      "requirements":[{"id":"CURRICULUM-REFERENCE","query":"2022 개정 초등 성취기준"}]}
    index={"fixture_scope":"NON_AUTHORITATIVE_INDEX_READBACK","records":[{
      "source_id":SOURCE_ID,"title":"2022 개정 초등 성취기준 표준 객체",
      "short_summary":"2022 개정 초등 성취기준 참고자료"}]}
    manifest={SOURCE_ID:{"source_id":SOURCE_ID,"raw_path":RAW_REL,"sha256":digest}}
    ensure_immutable(DEST/"contract.json",contract)
    ensure_immutable(DEST/"index_fixture.json",index)
    ensure_immutable(DEST/"raw_manifest.json",manifest)
    result=execute(contract,index=DEST/"index_fixture.json",manifest=manifest,
                   raw_root=ROOT,output=DEST/"candidate.json",app_root=APP)
    if result["supply"].get("status")!="LOCAL_E2E_PASS":
        raise RuntimeError(json.dumps(result,ensure_ascii=False))
    if (DEST/"run_receipt.json").exists():
        prior=json.loads((DEST/"run_receipt.json").read_text(encoding="utf-8"))
        if prior.get("supply",{}).get("artifact_sha256")!=result["supply"].get("artifact_sha256"):
            raise RuntimeError("RECEIPT_REVISION_CONFLICT")
    else:
        ensure_immutable(DEST/"run_receipt.json",result)
    print(json.dumps({"status":"P0_REAL_RAW_CANDIDATE_PASS","candidate":str(DEST/"candidate.json"),
        "receipt":str(DEST/"run_receipt.json"),"source_sha256":digest,
        "release_approved":False,"index_authoritative":False},ensure_ascii=False))
if __name__=="__main__":main()
