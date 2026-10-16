"""Import user review notes as untrusted, append-only reviewer input candidates.

Never treats UI notes, source excerpts, filename, or route hints as approvals.
All results remain separately staged for independent INDEXING_OWNER evaluation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import central_forming_review_queue as review_queue

SOURCE=review_queue.EVIDENCE/"TAKY_FULL_ANCHOR_REVIEW_875283c73ce17d400ac9.json"
DEST=review_queue.EVIDENCE/"LOCAL_OWNER_REVIEW_INPUT_INBOX"
MAX_NOTE_BYTES=1_000_000
MAX_CHARACTERS=10_000
NOTE_SCHEMA="TAKY_LOCAL_REVIEW_NOTES_V1"


def parse_notes(path, projection):
    if not Path(path).is_file() or Path(path).is_symlink():
        raise ValueError("REVIEW_NOTES_NOT_REGULAR_LOCAL_FILE")
    if Path(path).stat().st_size>MAX_NOTE_BYTES:
        raise ValueError("REVIEW_NOTES_SIZE_LIMIT")
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if (not isinstance(value,dict) or value.get("schema")!=NOTE_SCHEMA
        or value.get("source_projection_sha256")!=projection["manifest_sha256"]
        or value.get("non_authoritative") is not True
        or value.get("independent_approval") is not False
        or not isinstance(value.get("records"),list)
        or len(value["records"])>projection["review_ready_sources"]):
        raise ValueError("REVIEW_NOTES_SOURCE_OR_AUTHORITY_INVALID")
    sources={p["source_id"]:p for p in projection["projected_sources"]}
    records=[];seen=set()
    for row in value["records"]:
        if (not isinstance(row,dict) or set(row)!={"source_id","status","text"}
            or row.get("source_id") not in sources
            or row["source_id"] in seen
            or row["status"] not in ("none","noted","revisit")
            or not isinstance(row["text"],str)
            or len(row["text"])>MAX_CHARACTERS):
            raise ValueError("REVIEW_NOTE_ROW_INVALID_OR_DUPLICATED")
        sid=row["source_id"];seen.add(sid)
        s=sources[sid]
        records.append({
            "source_id":sid,"raw_sha256":s["raw_sha256"],
            "source_projection_sha256":value["source_projection_sha256"],
            "route_hint_not_authority":s["owner_route_hint"],
            "operator_note":row["text"].strip(),
            "operator_status":row["status"],
            "independent_index_owner_authorized":False,
            "forming_approved":False,"learning_consumed":False,
            "requires":"INDEPENDENT_INDEXING_OWNER_REVIEW_AND_PROVENANCE_CHECK"})
    if not records:
        raise ValueError("REVIEW_NOTES_EMPTY_NO_NEW_INPUT")
    records.sort(key=lambda x:x["source_id"])
    result={
        "schema":"TAKY_LOCAL_REVIEW_NOTES_STAGED_FOR_INDEX_OWNER_V1",
        "state":"NON_AUTHORITATIVE_OPERATOR_NOTES",
        "source_projection_sha256":projection["manifest_sha256"],
        "source_count":len(records),"notes":records,
        "independent_approved_sources":0,"forming_approved":False,
        "consumer_enabled":False,"operational_db_untouched":True}
    result["manifest_sha256"]=review_queue.digest(result)
    return result


def write_result(proposed,root=DEST):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    target=root/("LOCAL_INDEX_OWNER_INPUT_"+proposed["manifest_sha256"][:20]+".json")
    if target.exists():
        if json.loads(target.read_text(encoding="utf-8"))!=proposed:
            raise ValueError("REVIEW_NOTES_APPEND_ONLY_COLLISION")
        return target,False
    with target.open("x",encoding="utf-8") as out:
        json.dump(proposed,out,ensure_ascii=False,indent=2)
    return target,True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--notes",type=Path,required=True)
    parser.add_argument("--apply-to-local-inbox",action="store_true")
    args=parser.parse_args()
    raw=json.loads(SOURCE.read_text(encoding="utf-8"))
    full=dict(raw)
    sha=full.pop("manifest_sha256")
    if review_queue.digest(full)!=sha:
        raise ValueError("RAW_REVIEW_PROJECTION_HASH_CHANGED")
    result=parse_notes(args.notes,raw)
    state={"state":result["state"],"source_count":result["source_count"],
           "manifest_sha256":result["manifest_sha256"],
           "canonical_source_db_modified":False,
           "independent_owner_approved":False}
    if args.apply_to_local_inbox:
        file,created=write_result(result)
        state.update({"path":str(file),"created":created})
    print(json.dumps(state,ensure_ascii=True))


if __name__=="__main__":
    main()
