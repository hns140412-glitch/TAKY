"""Verified review-RAW and line-anchored MINING -> existing TAKY Central Source Factory.

Single transactional ingestion. Do not assert semantic approval, FORMING,
Learning promotion, app success, or modify a CURRENT authority file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import taky_central_source_factory as factory

ROOT = factory.ROOT
EVIDENCE = ROOT / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
SOURCE_ROOT = ROOT / "TAKY-SOURCE-VAULT" / "data" / "direction_intake"
INDEX = EVIDENCE / "USER_REVIEW_AI_DISCOVERY_INDEX_MINED_CANDIDATE_20261014.json"
MINING = EVIDENCE / "USER_REVIEW_MARKDOWN_EVIDENCE_CANDIDATE_20261014.json"
TRIAGE = EVIDENCE / "TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json"
MAX_RAW = 8_000_000
MAX_DOCS = 50

def sha(b):
    return hashlib.sha256(b).hexdigest()

def read_json(file, limit=12_000_000):
    file=Path(file)
    if not 0 < file.stat().st_size <= limit:
        raise ValueError("REVIEW_EVIDENCE_SIZE_INVALID")
    return json.loads(file.read_text(encoding="utf-8-sig"))

def verified_documents(index_path=INDEX, mining_path=MINING, triage_path=TRIAGE):
    idx=read_json(index_path)
    mining=read_json(mining_path)
    triage=read_json(triage_path)
    if (idx.get("schema")!="TAKY_AI_REFERENCE_INDEX_V1"
        or idx.get("authoritative") is not False
        or mining.get("schema")!="TAKY_REVIEW_MARKDOWN_EVIDENCE_UNREVIEWED_V1"
        or triage.get("schema")!="TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_V1"):
        raise ValueError("SOURCE_CANDIDATE_SCHEMA_INVALID")
    records=idx["records"]
    if not 0 < len(records) <= MAX_DOCS:
        raise ValueError("SOURCE_CANDIDATE_COUNT_INVALID")
    mined={x["source_id"]:x for x in mining["sources"]}
    proposed={x["source_id"]:x for x in triage["source_triage"]}
    if (len(mined)!=len(records) or len(proposed)!=len(records)
        or len(set(x["source_id"] for x in records))!=len(records)
        or {x["source_id"] for x in records}!=set(mined) or set(mined)!=set(proposed)):
        raise ValueError("SOURCE_SET_INCONSISTENT")
    output=[]
    vault=SOURCE_ROOT.resolve(strict=True)
    for rec in records:
        sid=rec["source_id"]
        if not sid.startswith("USER_REVIEW:") or rec["source_family"]!="USER_PROVIDED_TREND_REVIEW":
            raise ValueError("SOURCE_KIND_NOT_REVIEW")
        raw=Path(rec["path"]).resolve(strict=True)
        if not raw.is_relative_to(vault) or raw.name!="response.bin":
            raise ValueError("RAW_PATH_UNTRUSTED:"+sid)
        data=raw.read_bytes()
        if not 0 < len(data) <= MAX_RAW or sha(data)!=rec["content_hash"]:
            raise ValueError("RAW_HASH_MISMATCH:"+sid)
        doc=mined[sid]
        if (doc.get("raw_sha256")!=sha(data)
            or Path(doc.get("raw_path","")).resolve(strict=True)!=raw
            or doc.get("capture_scope")!="SINGLE_DOCUMENT_NOT_FULL_REPOSITORY"):
            raise ValueError("EXTRACTION_DOCUMENT_ID_MISMATCH:"+sid)
        lines=data.decode("utf-8-sig").splitlines()
        units=doc.get("units",[])
        if not isinstance(units,list) or not units:
            raise ValueError("EXTRACTION_UNITS_MISSING:"+sid)
        for unit in units:
            start=unit["source_anchor"]["line_start"]
            end=unit["source_anchor"]["line_end"]
            if not 1<=start<=end<=len(lines):
                raise ValueError("LINE_SPAN_OUT_OF_RANGE:"+sid)
            content="\n".join(lines[start-1:end]).strip().encode("utf-8")
            if sha(content)!=unit["content_sha256"]:
                raise ValueError("EXTRACTIVE_SHA_CHANGED:"+sid)
        proposal=proposed[sid]
        if (proposal["raw_sha256"]!=sha(data)
            or proposal.get("anchored_extract_units_verified")!=len(units)
            or proposal.get("independent_semantic_approval") is not False):
            raise ValueError("REVIEW_TRIAGE_PROVENANCE_INVALID:"+sid)
        if proposal.get("learning_promoted") is not False:
            raise ValueError("UNAPPROVED_LEARNING_MARK_INVALID:"+sid)
        output.append({
            "source_id":sid,"title":rec["title"],"url":rec["url"],
            "raw_path":str(raw),"raw_sha256":sha(data),"raw_bytes":len(data),
            "mtime_ns":raw.stat().st_mtime_ns,
            "mined_units":len(units),"consumer_candidate":proposal["proposed_consumer"],
            "triage_state":proposal["triage"],
            "lineage_index_source":"USER_REVIEW_AI_DISCOVERY_INDEX_MINED_CANDIDATE_20261014.json",
            "lineage_extract_source":"USER_REVIEW_MARKDOWN_EVIDENCE_CANDIDATE_20261014.json",
            "lineage_triage_source":"TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json",
        })
    return output

def ingest(c, documents):
    created=0;unchanged=0;mapped=[]
    for doc in documents:
        raw=Path(doc["raw_path"])
        if not raw.is_file() or factory.file_hash(raw)!=doc["raw_sha256"] or raw.stat().st_mtime_ns!=doc["mtime_ns"]:
            raise ValueError("RAW_CHANGED_BETWEEN_PREFLIGHT_AND_WRITE")
        content_id="raw:"+doc["raw_sha256"]
        current=c.execute("SELECT id,status,authoritative_review FROM source WHERE id=?",(content_id,)).fetchone()
        if current and current["authoritative_review"]!="UNREVIEWED":
            raise ValueError("ALREADY_AUTHORIZED_SOURCE_REQUIRES_REVIEW")
        saved=c.execute("""SELECT source_id FROM location
          WHERE provider='LOCAL_FILE' AND account='TAKY_REVIEW_RAW' AND locator=?""",
          (str(raw),)).fetchone()
        if saved:
            if saved["source_id"]!=content_id:
                raise ValueError("REGISTERED_SOURCE_REPOINT_CONFLICT")
            stage=c.execute("SELECT state FROM stage WHERE source_id=? AND stage='INDEX'",(content_id,)).fetchone()
            if stage and stage["state"]=="TECHNICAL_INDEX_READY":
                unchanged+=1
                mapped.append((doc["source_id"],content_id))
                continue
        canonical=factory.register(c,"LOCAL_FILE","TAKY_REVIEW_RAW",str(raw),doc["title"],
            "REFERENCE_REVIEW_CANDIDATE",sha=doc["raw_sha256"],size=doc["raw_bytes"],
            modified=str(doc["mtime_ns"]),meta={
                "original_source_id":doc["source_id"],"origin_url":doc["url"],
                "source_scope":"SINGLE_DOCUMENT_ONLY",
                "mining_units_sha_verified":doc["mined_units"],
                "proposed_consumer_not_approved":doc["consumer_candidate"],
                "triage":doc["triage_state"],
                "technical_ingest_not_semantic_review":True
            },consumer=None)
        if canonical!=content_id:
            raise ValueError("CENTRAL_SHA_ID_MISMATCH")
        c.execute("""INSERT INTO evidence VALUES(?,?,?,?,?,?)
          ON CONFLICT(source_id) DO UPDATE SET
            raw_sha256=excluded.raw_sha256,parse_state=excluded.parse_state,
            summary=excluded.summary,index_terms=excluded.index_terms,
            modified_at=excluded.modified_at""",
            (canonical,doc["raw_sha256"],
             "LINE_ANCHORED_MARKDOWN_VERIFIED_NOT_SEMANTICALLY_REVIEWED",
             "Source title: "+doc["title"]+"; selected consumer is proposal only.",
             factory.compact([]),factory.utc()))
        facts={"original_source_id":doc["source_id"],"raw_sha256":doc["raw_sha256"],
               "line_anchored_units":doc["mined_units"],"reference_only":True}
        for stage,state,extra in [
            ("EXTRACT","DONE",{"bounded_text_extract":True}),
            ("ANALYZE","DRAFT_ONLY",{"semantic_review_done":False,"proposed_consumer":doc["consumer_candidate"]}),
            ("REVIEW","WAITING_AUTHORIZED_REVIEW",{"independent_approval":False}),
            ("INDEX","TECHNICAL_INDEX_READY",{"deep_semantic_index":False}),
            ("FORMING","BLOCKED_REVIEW_NOT_APPROVED",{"forming_approved":False}),
            ("LEARNING","BLOCKED_FORMING_NOT_APPROVED",{"learning_applied":False}),
            ("CONSUME","BLOCKED_NO_APPROVED_CONTRACT",{"app_consumption_approved":False})
        ]:
            factory.put_stage(c,canonical,stage,state,{**facts,**extra})
        c.execute("UPDATE source SET status='INDEXED_CANDIDATE',changed_at=? WHERE id=?",
                  (factory.utc(),canonical))
        factory.event(c,canonical,"ANCHOR_VERIFIED_REVIEW_SOURCE_IMPORTED",{
            **facts,"candidate_consumer":doc["consumer_candidate"],
            "code_adoption_not_automatically_proven":True,
            "index_source":doc["lineage_index_source"],
            "extract_source":doc["lineage_extract_source"]})
        created+=1
        mapped.append((doc["source_id"],canonical))
    return {"created":created,"reused":unchanged,"source_ids":mapped,
            "semantic_approved":0,"forming_promoted":0,
            "learning_consumed":0,"release_approved":False}

def readback(c, documents):
    statuses=[]
    for row in documents:
        content_id="raw:"+row["raw_sha256"]
        record=c.execute("SELECT id,status,authoritative_review FROM source WHERE id=?",(content_id,)).fetchone()
        stages={r["stage"]:r["state"] for r in c.execute(
            "SELECT stage,state FROM stage WHERE source_id=?",(content_id,))}
        relation=c.execute("SELECT COUNT(*) FROM relation WHERE source_id=? AND relation_type NOT IN ('REFERENCE_CONSUMER','REVIEW_CANDIDATE_LOCAL_METHOD_NOT_APPROVED')",(content_id,)).fetchone()[0]
        if not record or record["status"]!="INDEXED_CANDIDATE" or record["authoritative_review"]!="UNREVIEWED":
            raise AssertionError("SOURCE_AUTHORITY_WRONG")
        if (stages.get("VERIFY")!="DONE" or stages.get("EXTRACT")!="DONE"
            or stages.get("REVIEW")!="WAITING_AUTHORIZED_REVIEW"
            or stages.get("INDEX")!="TECHNICAL_INDEX_READY"
            or stages.get("FORMING")!="BLOCKED_REVIEW_NOT_APPROVED"
            or stages.get("LEARNING")!="BLOCKED_FORMING_NOT_APPROVED"
            or stages.get("CONSUME")!="BLOCKED_NO_APPROVED_CONTRACT" or relation):
            raise AssertionError("SOURCE_STAGE_OR_AUTHORITY_WRONG:"+row["source_id"])
        statuses.append({"source_id":row["source_id"],"central_id":content_id,
                         "status":record["status"],"stage":stages})
    return statuses

def index_extractive_details(c, documents):
    """Persist original-backed DETAIL anchors in the existing Central Factory.

    One immutable unit per source SHA + section ID; no semantic review, no
    classification promotion or application authorization.
    """
    extra=read_json(MINING)
    by_id={x["source_id"]:x for x in extra["sources"]}
    touched=0
    new_sources=0
    for doc in documents:
        item=by_id.get(doc["source_id"])
        if item is None or item["raw_sha256"]!=doc["raw_sha256"]:
            raise ValueError("DETAIL_EXTRACTIVE_SOURCE_MISMATCH")
        raw_path=Path(doc["raw_path"])
        data=raw_path.read_bytes()
        if sha(data)!=doc["raw_sha256"]:
            raise ValueError("DETAIL_RAW_CHANGED")
        lines=data.decode("utf-8-sig").splitlines()
        sid="raw:"+doc["raw_sha256"]
        source=c.execute("SELECT authoritative_review,status FROM source WHERE id=?",(sid,)).fetchone()
        if not source or source["authoritative_review"]!="UNREVIEWED" or source["status"]!="INDEXED_CANDIDATE":
            raise ValueError("DETAIL_UNAUTHORIZED_SOURCE")
        inserted=0
        units=item["units"]
        if len(units)!=doc["mined_units"]:
            raise ValueError("DETAIL_INDEX_COUNT_MISMATCH")
        if len({x["unit_id"] for x in units})!=len(units):
            raise ValueError("DETAIL_DUPLICATE_UNIT_ID")
        for unit in units:
            start=unit["source_anchor"]["line_start"]
            end=unit["source_anchor"]["line_end"]
            if not 1<=start<=end<=len(lines):
                raise ValueError("DETAIL_LINE_RANGE_INVALID")
            body="\n".join(lines[start-1:end]).strip()
            if sha(body.encode("utf-8"))!=unit["content_sha256"]:
                raise ValueError("DETAIL_UNIT_CONTENT_SHA_MISMATCH")
            if unit.get("unit_state")!="EXTRACTED_MARKDOWN_TEXT_UNREVIEWED":
                raise ValueError("DETAIL_UNIT_PRETENDS_TO_BE_REVIEWED")
            if len(body)>65536:
                raise ValueError("DETAIL_SECTION_EXCEEDS_INDEX_BOUND")
            args=(sid,unit["unit_id"],doc["raw_sha256"],start,end,
                  unit["content_sha256"],body,"EXTRACTIVE_UNREVIEWED")
            prior=c.execute("""SELECT raw_sha256,line_start,line_end,content_sha256,
                                       excerpt,review_state FROM evidence_unit
                              WHERE source_id=? AND unit_id=?""",(sid,unit["unit_id"])).fetchone()
            if prior is not None:
                if tuple(prior) == args[2:]:
                    continue
                # Earlier collector persisted only the first 2,000 chars;
                # repair that search-index truncation ONLY from the original
                # verified RAW, with unchanged full-section SHA and authority.
                if (tuple(prior[:4])==args[2:6]
                    and prior["review_state"]=="EXTRACTIVE_UNREVIEWED"
                    and len(body)>2000
                    and prior["excerpt"]==body[:2000]):
                    c.execute("""UPDATE evidence_unit SET excerpt=?
                      WHERE source_id=? AND unit_id=? AND content_sha256=?
                        AND review_state='EXTRACTIVE_UNREVIEWED'""",
                        (body,sid,unit["unit_id"],unit["content_sha256"]))
                    inserted+=1
                    continue
                raise ValueError("DETAIL_IMMUTABLE_UNIT_MISMATCH")
            c.execute("""INSERT INTO evidence_unit
                 (source_id,unit_id,raw_sha256,line_start,line_end,content_sha256,
                  excerpt,review_state) VALUES(?,?,?,?,?,?,?,?)""",args)
            inserted+=1
        if inserted:
            factory.event(c,sid,"SOURCE_DETAIL_ANCHORS_INDEXED",{
              "origin_id":doc["source_id"],"raw_sha256":doc["raw_sha256"],
              "unit_count":len(units),"index_only":True,
              "full_semantic_review":False,"forming_authorized":False})
            new_sources+=1
        touched+=inserted
        count=c.execute("SELECT COUNT(*) FROM evidence_unit WHERE source_id=?",(sid,)).fetchone()[0]
        if count!=len(units):
            raise AssertionError("SOURCE_DETAIL_ROUNDTRIP_COUNT_MISMATCH")
    return {"source_count":len(documents),"expected_unit_count":sum(x["mined_units"] for x in documents),
      "units_new":touched,"sources_new_detail":new_sources,"semantically_reviewed":0,
      "independent_approval":False,"current_changed":False}

# Source-aware semantic dispositions are review proposals, not approval.
SEMANTIC_DISPOSITIONS={
 "agent-browser / README.md":"COMPARE_EXISTING",
 "awesome-llm-apps / README.md":"REFERENCE_ONLY",
 "skills / skills/find-skills/SKILL.md":"COMPARE_EXISTING",
 "graphify / README.md":"COMPARE_EXISTING",
 "gsd-core / README.md":"COMPARE_EXISTING",
 "hyperframes / README.md":"HOLD_NO_CONSUMER",
 "skills / skills/mcp-builder/SKILL.md":"COMPARE_EXISTING",
 "playwright-mcp / README.md":"LOCAL_ADOPTION_EVIDENCED",
 "taste-skill / README.md":"REFERENCE_ONLY",
 "superpowers / README.md":"COMPARE_EXISTING",
 "ui-ux-pro-max-skill / README.md":"REFERENCE_ONLY",
 "ui-ux-pro-max-skill / .claude/skills/ui-ux-pro-max/SKILL.md":"REFERENCE_ONLY",
}

def attach_selected_semantic_claims(c, documents):
    """Source-grounded one-claim review candidates, never owner-approved logic."""
    from global_source_learning_feedback import CLAIMS
    extracted=read_json(MINING)
    by_id={x["source_id"]:x for x in extracted["sources"]}
    updated=0
    details=[]
    for doc in documents:
        title=doc["title"]
        if title not in CLAIMS or title not in SEMANTIC_DISPOSITIONS:
            raise ValueError("SOURCE_CLAIM_MAPPING_NOT_REVIEWED")
        phrase, interpretation, exclusion=CLAIMS[title]
        rows=by_id[doc["source_id"]]["units"]
        raw=Path(doc["raw_path"])
        raw_text=raw.read_text(encoding="utf-8-sig").splitlines()
        selected=None
        for unit in rows:
            anchor=unit["source_anchor"]
            quote="\n".join(raw_text[anchor["line_start"]-1:anchor["line_end"]]).strip()
            if phrase.casefold() not in quote.casefold():
                continue
            if sha(quote.encode("utf-8"))!=unit["content_sha256"]:
                raise ValueError("SELECTED_CLAIM_ANCHOR_CHANGED")
            selected=unit
            break
        if selected is None:
            raise ValueError("SELECTED_CLAIM_NOT_IN_ORIGINAL_RAW:"+doc["source_id"])
        sid="raw:"+doc["raw_sha256"]
        grounded=factory.read_verified_evidence_unit(c,sid,selected["unit_id"])
        if not grounded or grounded["content_sha256"]!=selected["content_sha256"]:
            raise ValueError("CENTRAL_DETAIL_SEMANTIC_EVIDENCE_REQUIRED")
        row=c.execute("SELECT authoritative_review FROM source WHERE id=?",(sid,)).fetchone()
        if row is None or row["authoritative_review"]!="UNREVIEWED":
            raise ValueError("SELECTED_CLAIM_REVIEW_AUTHORITY_INVALID")
        claim={
            "original_source_id":doc["source_id"],
            "source_raw_sha256":doc["raw_sha256"],
            "source_unit_id":selected["unit_id"],
            "source_line_start":selected["source_anchor"]["line_start"],
            "source_line_end":selected["source_anchor"]["line_end"],
            "source_chunk_sha256":selected["content_sha256"],
            "claim_phrase":phrase,
            "candidate_interpretation":interpretation,
            "reject_or_hold_rule":exclusion,
            "semantic_disposition":SEMANTIC_DISPOSITIONS[title],
            "suggested_consumer":doc["consumer_candidate"],
            "only_one_selected_claim":True,
            "complete_semantic_mining":False,
            "independent_semantic_approval":False,
            "forming_authorized":False,
            "learner_application_authorized":False
        }
        if factory.put_stage(c,sid,"ANALYZE","DRAFT_ONLY",claim):
            updated+=1
        details.append({"source_id":doc["source_id"],"central_id":sid,
                        "source_chunk_sha256":claim["source_chunk_sha256"],
                        "suggested_consumer":doc["consumer_candidate"],
                        "claim_line_start":claim["source_line_start"],
                        "claim_line_end":claim["source_line_end"]})
    return {"status":"SELECTED_SOURCE_CLAIMS_ANCHORED_IN_CENTRAL_ANALYZE",
            "source_count":len(details),"updated":updated,
            "claim_count":len(details),"selected_claims":details,
            "semantic_approved":0,"forming_promoted":0,"learning_consumed":0}

def record_existing_adoption_observation(c, candidate_path=None):
    """Attach *observed local tool use*, not approved FORMING or app pedagogy.

    Uses the independent browser receipt verifier and keeps the Central Factory
    stage authority blocked. Records a source-level relation and immutable event.
    """
    from global_source_learning_feedback import check_runtime, CODE, GUARD
    file=Path(candidate_path or EVIDENCE/
        "TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json").resolve(strict=True)
    if not file.is_relative_to(EVIDENCE.resolve(strict=True)):
        raise ValueError("ADOPTION_REPORT_OUTSIDE_EVIDENCE_ROOT")
    payload=read_json(file)
    adoption=payload.get("selected_adoption",{})
    source_id=adoption.get("source_id")
    checksum=adoption.get("raw_sha256")
    if (payload.get("schema")!="TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_V1"
        or payload.get("authority")!="WORKBENCH_REVIEW_CANDIDATE_NOT_CURRENT"
        or source_id!="USER_REVIEW:1fe7096c36a73359acf8"
        or not isinstance(checksum,str) or len(checksum)!=64):
        raise ValueError("LOCAL_ADOPTION_CANDIDATE_SCOPE_INVALID")
    central_id="raw:"+checksum
    current=c.execute("SELECT status,authoritative_review,original_sha256 FROM source WHERE id=?",
                      (central_id,)).fetchone()
    loc=c.execute("""SELECT metadata_json FROM location
                     WHERE source_id=? AND provider='LOCAL_FILE' AND account='TAKY_REVIEW_RAW'""",
                  (central_id,)).fetchone()
    if not current or not loc or current["status"]!="INDEXED_CANDIDATE":
        raise ValueError("CENTRAL_REVIEW_SOURCE_NOT_REGISTERED")
    metadata=json.loads(loc["metadata_json"])
    if (metadata.get("original_source_id")!=source_id
        or current["original_sha256"]!=checksum
        or current["authoritative_review"]!="UNREVIEWED"):
        raise ValueError("CENTRAL_SOURCE_AUTHORITY_CONFLICT")
    implementation=adoption.get("implementation",{})
    if (implementation.get("runner_sha256")!=factory.file_hash(CODE)
        or implementation.get("guard_sha256")!=factory.file_hash(GUARD)):
        raise ValueError("CODE_ADOPTION_IMPLEMENTATION_HASH_CHANGED")
    observations=adoption.get("local_consumer_observations")
    if not isinstance(observations,list) or len(observations)!=4:
        raise ValueError("LOCAL_CONSUMER_COVERAGE_INVALID")
    multi=read_json(EVIDENCE/"TAKY_MULTI_APP_EVIDENCE_VERIFIED_V2_20261014.json")
    if multi.get("source_id")!=source_id or len(multi.get("method_consumers",[]))!=4:
        raise ValueError("MULTI_APP_EVIDENCE_SOURCE_MISMATCH")
    by_run={x["run_id"]:x for x in multi["method_consumers"]}
    observed=[]
    for item in observations:
        source_row=by_run.get(item["run_id"])
        if source_row is None:
            raise ValueError("LOCAL_RUN_NOT_IN_ORIGINAL_EVIDENCE")
        checked=check_runtime(source_row,adoption["work_id"])
        if checked!=item or not checked["observed_local_scenario_verified"]:
            raise ValueError("LOCAL_BROWSER_RECEIPT_CHANGED")
        observed.append({"app":item["consumer_app"],"run_id":item["run_id"],
                         "browser_receipt_sha256":item["runtime_receipt_sha256"],
                         "steps":item["tested_steps"]})
    if len({x["app"] for x in observed})!=4:
        raise ValueError("MULTI_APP_OBSERVATIONS_DUPLICATED")
    report_hash=factory.file_hash(file)
    event_details={
        "original_source_id":source_id,"central_source_id":central_id,
        "raw_sha256":checksum,"observation_report_sha256":report_hash,
        "observation_report_path":str(file),
        "consumer":"TAKY_EXECUTION_EVIDENCE","local_observations":observed,
        "evidence_state":"LOCAL_TECHNIQUE_CONSUMPTION_CANDIDATE",
        "semantic_review_approved":False,"knowledge_promotion":False,
        "user_learning_outcome_verified":False,"operating_current_changed":False
    }
    kind="LOCAL_TECHNIQUE_USE_FEEDBACK_CANDIDATE"
    prior=c.execute("SELECT event_id,detail_json FROM event WHERE source_id=? AND kind=?",
                    (central_id,kind)).fetchall()
    fingerprint=factory.compact(event_details)
    existing=next((item["event_id"] for item in prior
                   if item["detail_json"]==fingerprint),None)
    if existing is None:
        factory.event(c,central_id,kind,event_details)
        event_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.execute("INSERT OR IGNORE INTO relation VALUES(?,?,?)",
                  (central_id,"TAKY_EXECUTION_EVIDENCE",
                   "REVIEW_CANDIDATE_LOCAL_METHOD_NOT_APPROVED"))
    else:
        event_id=existing
    stage=c.execute("SELECT state FROM stage WHERE source_id=? AND stage='LEARNING'",
                    (central_id,)).fetchone()
    if not stage or stage["state"]!="BLOCKED_FORMING_NOT_APPROVED":
        raise AssertionError("CANDIDATE_COULD_NOT_CHANGE_LEARNING_AUTHORITY")
    return {
        "status":"CENTRAL_SOURCE_LOCAL_USE_FEEDBACK_CANDIDATE",
        "central_source_id":central_id,
        "event_id":event_id,"inserted_new_event":existing is None,
        "observed_local_scenarios":len(observed),
        "observed_local_steps":sum(x["steps"] for x in observed),
        "learning_promoted":False,"user_outcomes_verified":False,
        "global_knowledge_feedback_approved":False
    }

def learn_from_observed_local_method(c):
    """Existing SYSTEM_GROW Learning consumer, strictly evidence candidate.

    This uses actual Central Source Factory evidence and AI Learning projection.
    It does not approve FORMING, write CURRENT, or authorize application use.
    """
    from ai_reference_projection import build_learning
    sid="USER_REVIEW:1fe7096c36a73359acf8"
    expected_sha="b33aa71a13d655e96e6b736d0c9de1e5ddea52f205916ca20b876387ff830e87"
    central_id="raw:"+expected_sha
    source=c.execute(
        "SELECT original_sha256,status,authoritative_review FROM source WHERE id=?",
        (central_id,)).fetchone()
    if (not source or source["original_sha256"]!=expected_sha
        or source["authoritative_review"]!="UNREVIEWED"
        or source["status"]!="INDEXED_CANDIDATE"):
        raise ValueError("SOURCE_NOT_IN_INDEPENDENT_REVIEW_STATE")
    stages={r["stage"]:(r["state"],json.loads(r["receipt_json"])) for r in
      c.execute("SELECT stage,state,receipt_json FROM stage WHERE source_id=?",(central_id,))}
    if (stages.get("LEARNING",("?",))[0]!="BLOCKED_FORMING_NOT_APPROVED"
        or stages.get("FORMING",("?",))[0]!="BLOCKED_REVIEW_NOT_APPROVED"):
        raise ValueError("FORMING_AUTHORITY_UNEXPECTED")
    analyzed=stages.get("ANALYZE",("?",{}))[1]
    if (stages.get("ANALYZE",("?",))[0]!="DRAFT_ONLY"
        or analyzed.get("original_source_id")!=sid
        or analyzed.get("independent_semantic_approval") is not False
        or analyzed.get("claim_phrase")!="structured accessibility snapshots"
        or analyzed.get("source_raw_sha256")!=expected_sha):
        raise ValueError("ANCHORED_SEMANTIC_REVIEW_CANDIDATE_REQUIRED")
    # Crucial INDEX/DETAIL -> SYSTEM_GROW consumer boundary:
    # an unindexed source file cannot be smuggled directly into Learning.
    units=c.execute("""SELECT unit_id FROM evidence_unit WHERE source_id=?
                       AND line_start=? AND line_end=? AND content_sha256=?
                       AND raw_sha256=? AND review_state='EXTRACTIVE_UNREVIEWED'""",
        (central_id,analyzed["source_line_start"],analyzed["source_line_end"],
         analyzed["source_chunk_sha256"],expected_sha)).fetchall()
    if len(units)!=1:
        raise ValueError("CENTRAL_DETAIL_ANCHOR_REQUIRED")
    grounded=factory.read_verified_evidence_unit(c,central_id,units[0]["unit_id"])
    if (not grounded or grounded["raw_sha256"]!=expected_sha
        or grounded["content_sha256"]!=analyzed["source_chunk_sha256"]
        or grounded["source_authority"]!="UNREVIEWED"
        or grounded["review_state"]!="EXTRACTIVE_UNREVIEWED"
        or analyzed["claim_phrase"].casefold() not in grounded["content"].casefold()):
        raise ValueError("LEARNING_CLAIM_ANCHOR_CHANGED")
    events=c.execute("""SELECT event_id,detail_json FROM event
      WHERE source_id=? AND kind='LOCAL_TECHNIQUE_USE_FEEDBACK_CANDIDATE'
      ORDER BY event_id DESC""",(central_id,)).fetchall()
    if len(events)!=1:
        raise ValueError("LOCAL_METHOD_CONSUMPTION_EVIDENCE_MISSING_OR_AMBIGUOUS")
    evidence=json.loads(events[0]["detail_json"])
    report_path=Path(evidence.get("observation_report_path",""))
    if (not report_path.is_file()
        or not report_path.resolve().is_relative_to(EVIDENCE.resolve())
        or factory.file_hash(report_path)!=evidence.get("observation_report_sha256")):
        raise ValueError("LOCAL_METHOD_EVENT_PROVENANCE_MISMATCH")
    report=read_json(report_path)
    code=report.get("selected_adoption",{}).get("implementation",{})
    from global_source_learning_feedback import CODE,GUARD,check_runtime
    if (code.get("runner_sha256")!=factory.file_hash(CODE)
        or code.get("guard_sha256")!=factory.file_hash(GUARD)):
        raise ValueError("CONSUMER_CODE_REQUIRES_REVERIFICATION")
    if (evidence.get("raw_sha256")!=expected_sha
        or evidence.get("semantic_review_approved") is not False
        or evidence.get("knowledge_promotion") is not False):
        raise ValueError("TECHNIQUE_EVENT_AUTHORITY_CONFLICT")
    rows=evidence.get("local_observations",[])
    if len(rows)!=4 or len({x.get("app") for x in rows})!=4:
        raise ValueError("FOUR_CONSUMER_RECEIPTS_REQUIRED")
    multi=read_json(EVIDENCE/"TAKY_MULTI_APP_EVIDENCE_VERIFIED_V2_20261014.json")
    observed={x["run_id"]:x for x in multi.get("method_consumers",[])}
    for evidence_row in rows:
        datum=observed.get(evidence_row["run_id"])
        if datum is None:
            raise ValueError("LOCAL_CONSUMER_PROOF_NOT_FOUND")
        real=check_runtime(datum,report["selected_adoption"]["work_id"])
        if (real["runtime_receipt_sha256"]!=evidence_row["browser_receipt_sha256"]
            or real["consumer_app"]!=evidence_row["app"]
            or real["tested_steps"]!=evidence_row["steps"]):
            raise ValueError("CONSUMPTION_RECEIPT_MISMATCH")
    # A narrow knowledge candidate: an adoption lesson justified by the
    # real local tool execution, not general claims across all 12 sources.
    insight=("For selected local TAKY browser checks, structured accessibility "
             "snapshots provide source-grounded state evidence alongside "
             "screenshots; this observation is not approved UI or app completion.")
    learning_id="AI-LRN-ACCESSIBILITY-LOCAL-REVIEW-CANDIDATE"
    input_record={
      "source_id":sid, "ai_categories":[],
      "learning_eligible":True,
      "learning_candidates":[{"learning_id":learning_id,"insight":insight}]
    }
    projection=build_learning([input_record])
    learned=[x for x in projection["learnings"] if x["learning_id"]==learning_id]
    if (len(learned)!=1 or len(projection["learnings"])!=1
        or learned[0]["evidence_refs"]!=["INDEX:"+sid]
        or learned[0]["state"]!="EVIDENCE_CANDIDATE"
        or learned[0]["canonical_promotion"] is not False
        or projection["authoritative"] is not False):
        raise ValueError("GLOBAL_AI_LEARNING_UNAUTHORIZED_OR_WRONG")
    audit={
      "source_id":sid,"central_id":central_id,
      "source_raw_sha256":expected_sha,
      "selected_claim_anchor_sha256":analyzed["source_chunk_sha256"],
      "local_consumption_event_id":events[0]["event_id"],
      "local_consumption_report_sha256":evidence["observation_report_sha256"],
      "observed_app_count":4,"observed_step_count":sum(x["steps"] for x in rows),
      "ai_learning_id":learning_id,
      "ai_learning_insight_sha256":sha(insight.encode("utf-8")),
      "learning_consumer":"EXISTING_ai_reference_projection.build_learning",
      "learning_result":"SYSTEM_GROW_EVIDENCE_CANDIDATE_ONLY",
      "semantic_approval":False,"current_written":False,
      "production_app_changed":False,"user_outcome_verified":False,
      "knowledge_feedback_approved":False
    }
    kind="GLOBAL_AI_LEARNING_LOCAL_TECHNIQUE_CANDIDATE"
    fingerprint=factory.compact(audit)
    previous=c.execute("SELECT event_id,detail_json FROM event WHERE source_id=? AND kind=?",
                       (central_id,kind)).fetchall()
    already=next((r["event_id"] for r in previous if r["detail_json"]==fingerprint),None)
    if already is None:
        factory.event(c,central_id,kind,audit)
        event_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]
    else:
        event_id=already
    return {
      "status":"EXISTING_SYSTEM_GROW_LEARNING_CONSUMED_EVIDENCE_CANDIDATE",
      "source_id":sid,"learning_id":learning_id,
      "reference_learning_state":learned[0]["state"],
      "learning_event_id":event_id,
      "inserted_new_learning_event":already is None,
      "origin_consumption_event_id":events[0]["event_id"],
      "operating_current_changed":False,
      "global_knowledge_authority_granted":False,
      "actual_user_outcome":False,
      "learned_reference":learned[0]
    }

def advance_verified_review_pipeline(c, documents, *, replay_verified_local_feedback=False, reconcile_live_feedback=False):
    """One source-owner transaction, end-to-end non-operational linkage.

    Rerunnable without creating duplicate source, stage, consumption or
    Learning events. Any failed evidence boundary rolls back all writes.
    """
    gathered=ingest(c,documents)
    details=index_extractive_details(c,documents)
    analyzed=attach_selected_semantic_claims(c,documents)
    consumed=record_existing_adoption_observation(c)
    learned=learn_from_observed_local_method(c)
    local_feedback=None
    if replay_verified_local_feedback:
        import global_source_learning_feedback as feedback
        observations=feedback.load_json(
            feedback.EVIDENCE / "TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json"
        )["selected_adoption"]["local_consumer_observations"]
        if len(observations)<1:
            raise ValueError("VERIFIED_LOCAL_OBSERVATION_MISSING")
        local_feedback=feedback.consume_verified_local_observation(
            c, "TAKY-EXISTING-LOCAL-REPLAY-20261014", observations[0]["run_id"])
    live_feedback=None
    if reconcile_live_feedback:
        if replay_verified_local_feedback:
            raise ValueError("MIXED_LOCAL_FEEDBACK_VERIFIERS_FORBIDDEN")
        import global_source_live_consumer as live_consumer
        live_feedback=live_consumer.reconcile_verified_live_receipts(c)
    confirmed=readback(c,documents)
    if (len(confirmed)!=len(documents) or
        analyzed["semantic_approved"]!=0 or gathered["semantic_approved"]!=0
        or learned["origin_consumption_event_id"]!=consumed["event_id"]
        or learned["reference_learning_state"]!="EVIDENCE_CANDIDATE"
        or learned["global_knowledge_authority_granted"] is not False):
        raise AssertionError("NON_OPERATIONAL_GLOBAL_LEARNING_LINKAGE_INCOMPLETE")
    return {
      "status":"CENTRAL_RAW_TO_GLOBAL_AI_LEARNING_CANDIDATE_LINKED",
      "verified_source_count":len(documents),
      "original_anchor_units":sum(x["mined_units"] for x in documents),
      "durable_detail_units":details["expected_unit_count"],
      "new_detail_units":details["units_new"],
      "created_sources":gathered["created"],
      "existing_sources":gathered["reused"],
      "analyzed_claims":analyzed["claim_count"],
      "new_analysis_reviews":analyzed["updated"],
      "local_consumption_event_id":consumed["event_id"],
      "global_ai_learning_event_id":learned["learning_event_id"],
      "new_consumption_event":consumed["inserted_new_event"],
      "new_learning_event":learned["inserted_new_learning_event"],
      "learning_state":"SYSTEM_GROW_EVIDENCE_CANDIDATE_ONLY",
      "semantic_approval_count":0,
      "forming_promoted":False,
      "operating_current_updated":False,
      "app_deployed":False,
      "real_user_outcome_verified":False,
      **({"verified_local_feedback":local_feedback} if local_feedback is not None else {}),
      **({"live_feedback_reconciliation":live_feedback} if live_feedback is not None else {})
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,default=factory.DB)
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--adoption-feedback-only",action="store_true")
    p.add_argument("--semantic-candidates-only",action="store_true")
    p.add_argument("--global-learning-candidate-only",action="store_true")
    p.add_argument("--advance-existing-pipeline",action="store_true")
    p.add_argument("--replay-verified-local-feedback",action="store_true")
    p.add_argument("--reconcile-live-feedback",action="store_true")
    p.add_argument("--index-detail-only",action="store_true")
    a=p.parse_args()
    if a.replay_verified_local_feedback and a.reconcile_live_feedback:
        p.error("MIXED_LOCAL_FEEDBACK_VERIFIERS_FORBIDDEN")
    if a.replay_verified_local_feedback or a.reconcile_live_feedback:
        import tempfile
        if (not a.advance_existing_pipeline or a.dry_run or
            not a.db.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()) or
            a.db.resolve()==factory.DB.resolve()):
            p.error("Verified local feedback requires --advance-existing-pipeline "
                    "and an explicit disposable --db under the system temp directory")
    documents=verified_documents()
    if a.index_detail_only:
        with factory.connect(a.db) as c:
            details=index_extractive_details(c,documents)
        print(json.dumps(details,ensure_ascii=False))
        return
    if a.advance_existing_pipeline:
        with factory.connect(a.db) as c:
            result=advance_verified_review_pipeline(
                c,documents,replay_verified_local_feedback=a.replay_verified_local_feedback,
                reconcile_live_feedback=a.reconcile_live_feedback)
        print(json.dumps(result,ensure_ascii=False))
        return
    if a.global_learning_candidate_only:
        with factory.connect(a.db) as c:
            learning=learn_from_observed_local_method(c)
        print(json.dumps(learning,ensure_ascii=False))
        return
    if a.semantic_candidates_only:
        with factory.connect(a.db) as c:
            semantic=attach_selected_semantic_claims(c,documents)
        print(json.dumps(semantic,ensure_ascii=False))
        return
    if a.adoption_feedback_only:
        with factory.connect(a.db) as c:
            feedback=record_existing_adoption_observation(c)
        print(json.dumps(feedback,ensure_ascii=False))
        return
    if a.dry_run:
        print(json.dumps({"status":"PREFLIGHT_PASS","verified_raw_docs":len(documents),
                          "anchored_mining_units":sum(x["mined_units"] for x in documents),
                          "source_ids":[x["source_id"] for x in documents]},ensure_ascii=False))
        return
    with factory.connect(a.db) as c:
        result=ingest(c,documents)
        validated=readback(c,documents)
        summary={"status":"CENTRAL_SOURCE_INTAKE_CANDIDATE_COMMITTED",
                 "verified":len(validated),
                 "mining_units_verified":sum(x["mined_units"] for x in documents),
                 **result}
    with factory.connect(a.db) as c:
        repeated=ingest(c,documents)
        if repeated["created"]!=0 or repeated["reused"]!=len(documents):
            raise AssertionError("INGEST_NOT_IDEMPOTENT")
        readback(c,documents)
    print(json.dumps({**summary,"repeat_run_idempotent":True},ensure_ascii=False))
if __name__=="__main__":
    main()
