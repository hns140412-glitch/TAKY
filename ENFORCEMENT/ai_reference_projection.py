#!/usr/bin/env python3
from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT=Path(__file__).resolve().parents[1]
AI_INDEX=ROOT/"CURRENT"/"DATA"/"AI_REFERENCE_INDEX.json"
AI_LEARNING=ROOT/"CURRENT"/"DATA"/"AI_LEARNING_PROJECTION.json"
SOURCE_VAULT=ROOT.parent/"TAKY-SOURCE-VAULT"
VIDEO_AI_IDS={
 "VID-20261003-001","VID-20261003-003",
 "VID-20261003-014","VID-20261003-015","VID-20261003-016","VID-20261003-017","VID-20261003-018","VID-20261003-019",
 "VID-20261003-020","VID-20261003-021","VID-20261003-022","VID-20261003-023","VID-20261003-024",
 "VID-20261003-052","VID-20261003-053",
}

CATEGORY_RULES={
 "MODEL": (r"\bmodel\b",r"model routing",r"chatgpt",r"claude",r"gemini",r"astra"),
 "TOOL": (r"\btool\b",r"plugin",r"open[- ]source",r"agent reach",r"open-slide",r"cli"),
 "AGENT": (r"\bagent\b",r"agent[-_ ]native",r"agent team"),
 "ORCHESTRATION": (r"orchestrat",r"model routing",r"plugin",r"workflow",r"necessity",r"route"),
 "PROMPT": (r"prompt",r"design\.md",r"macro pattern",r"slash",r"command[_ -]?ux"),
 "SOURCE_ACQUISITION": (r"source acquisition",r"web mining",r"external source",r"rss",r"youtube",r"github"),
 "COST": (r"\bcost\b",r"token econom",r"cost saving",r"usage optimization",r"savey"),
 "SECURITY": (r"security",r"supply chain",r"credential",r"cookie",r"login",r"risk"),
 "WORKFLOW": (r"workflow",r"pipeline",r"automation",r"presentation",r"artifact",r"process"),
}
AI_ANCHORS=(
 "ai_"," ai ","claude","chatgpt","gemini","astra","agent","prompt","plugin",
 "model routing","open-slide","agent reach","genspark","notebooklm"
)
EXCLUDE_ONLY_SIGNALS=("ai_training_prohibition_notice",)

def _list(v:Any)->list:
    if v is None:return []
    return v if isinstance(v,list) else [v]

def _text(record:dict)->str:
    values=[
      record.get("title"),record.get("source_family"),record.get("source_type"),
      record.get("authority_level"),record.get("value_statement"),
      *_list(record.get("domain_facets")),*_list(record.get("controlled_terms")),
      *_list(record.get("keywords")),*_list(record.get("entities"))
    ]
    return " ".join(str(x or "") for x in values).lower()

def classify_ai_record(record:dict)->list[str]:
    text=_text(record)
    # A copyright/training restriction mentioning AI is not by itself AI operational knowledge.
    stripped=text
    for sig in EXCLUDE_ONLY_SIGNALS:
        stripped=stripped.replace(sig,"")
    if not any(a in stripped for a in AI_ANCHORS):
        return []
    cats=[]
    for category,patterns in CATEGORY_RULES.items():
        if any(re.search(p,text,re.I) for p in patterns):
            cats.append(category)
    return cats or ["WORKFLOW"]

def project_record(record:dict, *, origin_file:str|None=None)->dict|None:
    cats=classify_ai_record(record)
    if not cats:return None
    sid=str(record.get("source_id") or "").strip()
    if not sid:return None
    return {
      "source_id":sid,
      "title":record.get("title"),
      "source_ref":record.get("source_ref") or f"INDEX:{sid}",
      "url":record.get("url"),
      "source_family":record.get("source_family"),
      "source_type":record.get("source_type"),
      "authority_level":record.get("authority_level"),
      "current_relation":record.get("current_relation"),
      "duplicate_relation":record.get("duplicate_relation"),
      "version_relation":record.get("version_relation"),
      "applicability_scope":_list(record.get("applicability_scope")),
      "ai_categories":cats,
      "domain_facets":_list(record.get("domain_facets")),
      "controlled_terms":_list(record.get("controlled_terms")),
      "keywords":_list(record.get("keywords")),
      "verification_needed":_list(record.get("verification_needed")),
      "claims_to_exclude":_list(record.get("claims_to_exclude")),
      "value_statement":record.get("value_statement") or "",
      "publisher_or_account":record.get("publisher_or_account"),
      "origin_file":origin_file,
      "record_kind":"SOURCE_REFERENCE",
      "learning_eligible":True,
      "canonical_promotion":False,
    }

def _items(payload:dict)->list[dict]:
    return payload.get("items") or payload.get("source_entries") or []

def load_reference_deltas(root:Path=ROOT)->list[dict]:
    out=[]
    for p in sorted((root/"C2S").glob("NOTION_REFERENCE_INDEX_DELTA_V*.json")):
        try:d=json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:continue
        for r in _items(d):
            if isinstance(r,dict):
                x=project_record(r,origin_file=p.relative_to(root).as_posix())
                if x:out.append(x)
    # latest source_id wins; deterministic file order makes newer V revisions override older.
    by={}
    for x in out:by[x["source_id"]]=x
    return [by[k] for k in sorted(by)]

def load_validated_ai_mining_atoms(vault:Path=SOURCE_VAULT)->list[dict]:
    p=vault/"reports"/"VIDEO_REMINING_VALIDATED_INDEX_20261003.json"
    if not p.exists(): return []
    try:d=json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:return []
    out=[]
    for bucket in ("safe_to_index","reference_only"):
        for x in d.get(bucket) or []:
            cid=str(x.get("candidate_id") or "")
            if cid not in VIDEO_AI_IDS: continue
            statement=str(x.get("statement") or "").strip()
            if not statement: continue
            out.append({
              "source_id":"AIATOM:"+cid,
              "title":f"{cid} — {x.get('domain') or 'AI mining atom'}",
              "source_ref":cid,
              "url":None,
              "source_family":"VALIDATED_VIDEO_REMINING",
              "source_type":"VALIDATED_MINING_ATOM",
              "authority_level":x.get("promotion_ceiling") or ("INDEX_ONLY" if bucket=="safe_to_index" else "REFERENCE_ONLY"),
              "current_relation":"REFERENCE_ONLY" if bucket=="reference_only" else "INDEX_ONLY",
              "duplicate_relation":None,
              "version_relation":None,
              "applicability_scope":[x.get("domain"),x.get("consumer")],
              "ai_categories":[],
              "domain_facets":["ai_orchestration",str(x.get("domain") or "")],
              "controlled_terms":[
                str(x.get("atom_type_raw") or ""),
                str(x.get("validated_disposition") or ""),
                str(x.get("evidence_class") or ""),
              ],
              "keywords":[str(x.get("candidate_owner") or ""),str(x.get("consumer") or "")],
              "verification_needed":[str(x.get("codex_reason") or "")] if x.get("codex_reason") else [],
              "claims_to_exclude":[],
              "value_statement":statement,
              "publisher_or_account":x.get("source_report"),
              "origin_file":"TAKY-SOURCE-VAULT/reports/VIDEO_REMINING_VALIDATED_INDEX_20261003.json",
              "record_kind":"VALIDATED_MINING_ATOM",
              "mining_validation_status":x.get("validation_status"),
              "mining_disposition":x.get("validated_disposition"),
              "mining_confidence":x.get("validated_confidence"),
              "evidence":x.get("evidence"),
              "learning_eligible":True,
              "canonical_promotion":False,
            })
    atom_category_map={
      "AI orchestration / 검증 절차":["ORCHESTRATION","WORKFLOW"],
      "AI orchestration / prompt pack":["PROMPT","ORCHESTRATION"],
      "토큰/컨텍스트":["ORCHESTRATION","COST"],
      "오케스트레이션":["ORCHESTRATION","TOOL"],
      "자기 점검":["ORCHESTRATION","WORKFLOW"],
      "레퍼런스 색인":["ORCHESTRATION","TOOL"],
      "증거 등급":["ORCHESTRATION","WORKFLOW"],
      "EXTERNAL_TOOLING_REFERENCE":["TOOL","SECURITY"],
      "WORK_TOOLING_DOC_FORMAT":["WORKFLOW"],
      "VERIFICATION_PROTOCOL":["ORCHESTRATION","WORKFLOW"],
      "SUPPLY_CHAIN_CHECK":["SECURITY","TOOL"],
      "VERIFICATION_LOOP":["ORCHESTRATION","WORKFLOW"],
    }
    for r in out:
        domain=(r.get("applicability_scope") or [""])[0] or ""
        r["ai_categories"]=atom_category_map.get(str(domain),classify_ai_record(r) or ["ORCHESTRATION"])
    return out

def load_ai_discovery_candidates(vault:Path=SOURCE_VAULT)->list[dict]:
    out=[]
    # Routed web references: authorized for index-state only, but not mined enough for learning.
    p=vault/"reports"/"WEB_NEW_REFERENCE_ROUTING_20261002.json"
    if p.exists():
        try:d=json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:d={}
        for x in d.get("items") or []:
            out.append({
              "source_id":"DISCOVERY:"+str(x.get("source_id") or ""),
              "title":x.get("title"),"source_ref":x.get("source_id"),"url":x.get("source_url"),
              "source_family":"WEB_NEW_REFERENCE_ROUTING","source_type":"DISCOVERY_REFERENCE",
              "authority_level":"DISCOVERY_ONLY__BODY_MINING_REQUIRED",
              "current_relation":"DISCOVERY_ONLY","duplicate_relation":None,"version_relation":None,
              "applicability_scope":[x.get("domain"),(x.get("route") or {}).get("consumer")],
              "domain_facets":[x.get("domain")],"controlled_terms":["BODY_MINING_REQUIRED"],
              "keywords":[],"verification_needed":["Acquire and mine source body before learning."],
              "claims_to_exclude":["Do not learn product/workflow claims from title or routing metadata alone."],
              "value_statement":"","publisher_or_account":None,
              "origin_file":"TAKY-SOURCE-VAULT/reports/WEB_NEW_REFERENCE_ROUTING_20261002.json",
              "record_kind":"DISCOVERY_REFERENCE","learning_eligible":False,"canonical_promotion":False,
            })
    # Daily deep mining: only INDEX_CANDIDATE records enter discovery index; REVIEW/HOLD remain out.
    p=vault/"reports"/"DEEP_MINING_20261003_0800.json"
    if p.exists():
        try:d=json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:d={}
        for i,x in enumerate(d.get("new_items") or [],start=1):
            if x.get("disposition")!="INDEX_CANDIDATE": continue
            out.append({
              "source_id":f"DISCOVERY:DEEP-20261003-{i:02d}",
              "title":x.get("title"),"source_ref":f"DEEP_MINING_20261003_0800:{i}","url":x.get("source_url"),
              "source_family":"DEEP_MINING_DAILY","source_type":"DISCOVERY_REFERENCE",
              "authority_level":"REFERENCE_ONLY__UPSTREAM_VERIFICATION_REQUIRED",
              "current_relation":"DISCOVERY_ONLY","duplicate_relation":None,"version_relation":None,
              "applicability_scope":[x.get("domain"),x.get("route")],"domain_facets":[x.get("domain")],
              "controlled_terms":list(x.get("guards") or []),"keywords":[str(x.get("route") or "")],
              "verification_needed":["Verify upstream/project facts before adoption or execution."],
              "claims_to_exclude":[],"value_statement":str(x.get("reason") or ""),
              "publisher_or_account":None,"origin_file":"TAKY-SOURCE-VAULT/reports/DEEP_MINING_20261003_0800.json",
              "record_kind":"DISCOVERY_REFERENCE","learning_eligible":False,"canonical_promotion":False,
            })
    for r in out:
        r["ai_categories"]=classify_ai_record(r)
        if not r["ai_categories"] and ("AI" in str(r.get("title") or "") or "Claude" in str(r.get("title") or "")):
            r["ai_categories"]=["TOOL"]
    # Dedupe by URL/title; keep deterministic source_id.
    by={}
    for r in out:
        key=(str(r.get("url") or "").strip().lower(),str(r.get("title") or "").strip().lower())
        if key not in by: by[key]=r
    return list(by.values())

def load_p0_remined_sources(vault:Path=SOURCE_VAULT)->list[dict]:
    p=vault/"reports"/"AI_P0_REMINING_RESULT_20261005.json"
    if not p.exists(): return []
    try:d=json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:return []
    out=[]
    for x in d.get("records") or []:
        if not isinstance(x,dict): continue
        sid=str(x.get("source_id") or "").strip()
        if not sid.startswith("AIREF:P0:"): continue
        r=dict(x)
        r["record_kind"]="REMINED_SOURCE_REFERENCE"
        r["learning_eligible"]=bool(x.get("learning_eligible"))
        r["canonical_promotion"]=False
        r["origin_file"]="TAKY-SOURCE-VAULT/reports/AI_P0_REMINING_RESULT_20261005.json"
        out.append(r)
    return out

def load_p1_remined_sources(vault:Path=SOURCE_VAULT)->list[dict]:
    p=vault/"reports"/"AI_P1_REMINING_RESULT_20261006.json"
    if not p.exists(): return []
    try:d=json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:return []
    out=[]
    for x in d.get("records") or []:
        if not isinstance(x,dict): continue
        sid=str(x.get("source_id") or "").strip()
        if not sid.startswith("AIREF:P1:"): continue
        r=dict(x)
        r["record_kind"]="REMINED_SOURCE_REFERENCE"
        r["learning_eligible"]=bool(x.get("learning_eligible"))
        r["canonical_promotion"]=False
        r["origin_file"]="TAKY-SOURCE-VAULT/reports/AI_P1_REMINING_RESULT_20261006.json"
        out.append(r)
    return out

def load_recovered_hold_sources(vault:Path=SOURCE_VAULT)->list[dict]:
    p=vault/"reports"/"AI_RECOVERED_HOLDS_RESULT_20261006.json"
    if not p.exists(): return []
    try:d=json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:return []
    out=[]
    for x in d.get("records") or []:
        if not isinstance(x,dict): continue
        sid=str(x.get("source_id") or "").strip()
        if not sid.startswith("AIREF:REC:"): continue
        r=dict(x)
        r["record_kind"]="REMINED_SOURCE_REFERENCE"
        r["learning_eligible"]=bool(x.get("learning_eligible"))
        r["canonical_promotion"]=False
        r["origin_file"]="TAKY-SOURCE-VAULT/reports/AI_RECOVERED_HOLDS_RESULT_20261006.json"
        out.append(r)
    return out

LEARNING_PATTERNS=[
 {
  "learning_id":"AI-LRN-NECESSITY-BEFORE-ADOPTION",
  "categories":["TOOL","ORCHESTRATION"],
  "terms":["necessity","do not auto-install","measurable gap","not a replacement","optional acquisition adapter","experiment candidate"],
  "insight":"Evaluate need, overlap, cost, security and measurable gap before adopting another AI tool or agent.",
 },
 {
  "learning_id":"AI-LRN-SECURITY-BEFORE-CREDENTIAL",
  "categories":["SECURITY"],
  "terms":["credential","cookie","supply chain","security"],
  "insight":"Credential, cookie and supply-chain exposure require a security gate before enabling authenticated AI/tool channels.",
 },
 {
  "learning_id":"AI-LRN-STAGED-ARTIFACT-WORKFLOW",
  "categories":["WORKFLOW","PROMPT"],
  "terms":["content-first","sample slides","one-shot","token economy","full output","1–2 sample"],
  "insight":"For large artifacts, prefer staged plan/design/sample/full-build workflows over one-shot generation when evidence supports lower cost or easier correction.",
 },
 {
  "learning_id":"AI-LRN-PROMPT-MACRO-NOT-NATIVE",
  "categories":["PROMPT"],
  "terms":["not_native_command","macro pattern","slash"],
  "insight":"Reusable prompt macros may improve interaction, but must remain user-defined patterns unless native product support is independently verified.",
 },
 {
  "learning_id":"AI-LRN-SEPARATE-TOOLS-BEFORE-COMBINE",
  "categories":["ORCHESTRATION","WORKFLOW"],
  "source_ids":["AIATOM:VID-20261003-001"],
  "terms":[],
  "insight":"When multiple AI/tooling layers affect the same control path, validate each independently before combining them; a component check does not prove integrated behavior.",
 },
 {
  "learning_id":"AI-LRN-PROMPT-TEMPLATE-STRUCTURE",
  "categories":["PROMPT","ORCHESTRATION"],
  "source_ids":["AIATOM:VID-20261003-003"],
  "terms":[],
  "insight":"Reusable AI task prompts benefit from explicit role, purpose, input, numbered work, constraints, output and verification fields; treat the exact field set as a template candidate, not universal law.",
 },
 {
  "learning_id":"AI-LRN-INSTALL-DOC-OBSERVABILITY",
  "categories":["WORKFLOW"],
  "source_ids":["AIATOM:VID-20261003-020"],
  "terms":[],
  "insight":"AI/tool installation guidance should distinguish app commands from terminal commands and include command, fallback, observable verification, prohibited actions, provenance and license.",
 },
 {
  "learning_id":"AI-LRN-OBSERVABLE-SUCCESS-CRITERIA",
  "categories":["ORCHESTRATION","WORKFLOW"],
  "source_ids":["AIATOM:VID-20261003-021"],
  "terms":[],
  "insight":"AI/tool setup success should be defined by observable checks, not by an assistant saying installation succeeded.",
 },
 {
  "learning_id":"AI-LRN-SUPPLY-CHAIN-IDENTITY-CHECK",
  "categories":["SECURITY","TOOL"],
  "source_ids":["AIATOM:VID-20261003-022"],
  "terms":[],
  "insight":"Before installing AI tooling, verify the official project identity, canonical address and exact package name; similar names are not sufficient evidence.",
 },
 {
  "learning_id":"AI-LRN-SELF-REPORT-NOT-RUNTIME-PROOF",
  "categories":["ORCHESTRATION","WORKFLOW"],
  "source_ids":["AIATOM:VID-20261003-016","AIATOM:VID-20261003-018","AIATOM:VID-20261003-053"],
  "terms":[],
  "insight":"Agent/assistant self-reports and creator demonstrations must be separated from observed runtime evidence; hashes, URLs and success labels require an evidence binding.",
 },
 {
  "learning_id":"AI-LRN-CONTEXT-CLAIM-NEEDS-MEASUREMENT",
  "categories":["ORCHESTRATION","COST"],
  "source_ids":["AIATOM:VID-20261003-014"],
  "terms":[],
  "insight":"Context-compression or token-saving tool claims should remain reference-only until measured in the actual workload.",
 },
 {
  "learning_id":"AI-LRN-MEMORY-NEED-DOES-NOT-VALIDATE-TOOL",
  "categories":["ORCHESTRATION","TOOL"],
  "source_ids":["AIATOM:VID-20261003-015"],
  "terms":[],
  "insight":"A real need for session memory or repeated-task detection does not validate a specific memory/plugin implementation; evaluate the need separately from the tool.",
 },
 {
  "learning_id":"AI-LRN-REFERENCE-SETS-MUST-NOT-MERGE",
  "categories":["ORCHESTRATION","TOOL"],
  "source_ids":["AIATOM:VID-20261003-017"],
  "terms":[],
  "insight":"Different creator/tool bundles must remain separate source nodes unless identity/version evidence proves they are the same set.",
 },
 {
  "learning_id":"AI-LRN-UPSTREAM-TOOL-CLAIMS-VERIFY",
  "categories":["SECURITY","TOOL","WORKFLOW"],
  "source_ids":["AIATOM:VID-20261003-019","AIATOM:VID-20261003-023","AIATOM:VID-20261003-024"],
  "terms":[],
  "insight":"Platform support, install commands, licenses and package claims copied from secondary AI-tool guides remain research references until verified against upstream sources and an isolated runtime.",
 },
 {
  "learning_id":"AI-LRN-DEVICE-OBSERVATION-BEFORE-CLOSE",
  "categories":["ORCHESTRATION","WORKFLOW"],
  "source_ids":["AIATOM:VID-20261003-052"],
  "terms":[],
  "insight":"When success depends on a user device or UI, close the task only after the required observable device evidence is bound; a terse chat reply is not a substitute for evidence.",
 },
 {
  "learning_id":"AI-LRN-PUBLIC-ACQUISITION-SEPARATION",
  "categories":["SOURCE_ACQUISITION"],
  "terms":["source acquisition","web mining","agent reach"],
  "insight":"Public-source acquisition adapters are separate from private workspace connectors; authorization and provenance must stay explicit.",
 },
 {
  "learning_id":"AI-LRN-HUMAN-EDITABLE-OUTPUT",
  "categories":["WORKFLOW","AGENT"],
  "terms":["human visual edit","visual editor","native pptx","editable pptx"],
  "insight":"Prefer AI workflows that preserve editable artifacts and a human correction surface when the final deliverable requires visual or structural fidelity.",
 },
 {
  "learning_id":"AI-LRN-STYLE-SIGNAL-NOT-AUTHORSHIP-PROOF",
  "categories":["ORCHESTRATION"],
  "terms":["not_authorship_detector","false_positive_guard","korean_writing_qa"],
  "insight":"Use AI-like writing-style taxonomies as output-QA signals, not proof of AI authorship; preserve genre/model evidence limits, hold flags and false-positive caveats before rewriting.",
 },
]

def _support(record:dict, rule:dict)->bool:
    if record.get("learning_eligible") is False:return False
    allowed=set(rule.get("source_ids") or [])
    if allowed:
        return str(record.get("source_id") or "") in allowed
    text=_text(record)
    if not set(rule["categories"]).intersection(record.get("ai_categories") or []):return False
    return any(t.lower() in text for t in rule["terms"])

def _load_outcome_utility(root:Path)->dict:
    p=root/"LEARNING"/"evidence"/"data-index-outcome-utility.json"
    if not p.exists(): return {}
    try:
        d=json.loads(p.read_text(encoding="utf-8-sig"))
        if d.get("schema")!="TAKY_DATA_INDEX_OUTCOME_UTILITY_V1": return {}
        return d.get("by_source_id") or {}
    except Exception:
        return {}

def _attach_outcome_evidence(records:list[dict], utility:dict)->list[dict]:
    out=[]
    for r in records:
        x=dict(r)
        u=utility.get(r["source_id"]) if isinstance(utility,dict) else None
        u=dict(u) if isinstance(u,dict) else {}
        success=int(u.get("verified_success",0) or 0)
        failure=int(u.get("verified_failure",0) or 0)
        regression=int(u.get("regression_failure",0) or 0)
        if failure or regression: state="VERIFIED_FAILURE_OR_REGRESSION_PRESENT"
        elif success: state="VERIFIED_SUCCESS_PRESENT"
        else: state="NO_VERIFIED_OUTCOME_YET"
        x["outcome_utility"]=u
        x["outcome_evidence_state"]=state
        out.append(x)
    return out

def build_learning(records:list[dict])->dict:
    learn=[]
    seen_ids=set()
    for rule in LEARNING_PATTERNS:
        refs=sorted({r["source_id"] for r in records if _support(r,rule)})
        if not refs:continue
        learn.append({
          "learning_id":rule["learning_id"],
          "insight":rule["insight"],
          "evidence_refs":[f"INDEX:{x}" for x in refs],
          "evidence_count":len(refs),
          "state":"EVIDENCE_CANDIDATE",
          "authority":"SYSTEM_GROW_REFERENCE_LEARNING_ONLY",
          "canonical_promotion":False,
        })
        seen_ids.add(rule["learning_id"])
    # Explicit learnings mined from P0 source bodies. These never use fuzzy matching.
    dynamic={}
    for r in records:
        if r.get("learning_eligible") is False: continue
        sid=str(r.get("source_id") or "")
        for c in r.get("learning_candidates") or []:
            if not isinstance(c,dict): continue
            lid=str(c.get("learning_id") or "").strip()
            insight=str(c.get("insight") or "").strip()
            if not lid or not insight: continue
            row=dynamic.setdefault(lid,{"insight":insight,"source_ids":set()})
            # Same ID with different text is a conflict, not an implicit merge.
            if row["insight"] != insight: raise ValueError("AI_LEARNING_ID_CONFLICT:"+lid)
            row["source_ids"].add(sid)
    for lid in sorted(dynamic):
        row=dynamic[lid]
        refs=sorted(x for x in row["source_ids"] if x)
        if not refs: continue
        if lid in seen_ids: raise ValueError("AI_LEARNING_ID_COLLISION:"+lid)
        learn.append({
          "learning_id":lid,
          "insight":row["insight"],
          "evidence_refs":[f"INDEX:{x}" for x in refs],
          "evidence_count":len(refs),
          "state":"EVIDENCE_CANDIDATE",
          "authority":"SYSTEM_GROW_REMINED_SOURCE_LEARNING_ONLY",
          "canonical_promotion":False,
        })
        seen_ids.add(lid)
    return {
      "schema":"TAKY_AI_LEARNING_PROJECTION_V1",
      "authoritative":False,
      "owner":"SYSTEM_GROW",
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "learning_count":len(learn),
      "learnings":learn,
      "guards":[
        "AI_LEARNING != CANONICAL_POLICY",
        "SOURCE_AUTHORITY_IS_PRESERVED",
        "FAILURE_OR_CONTRADICTORY_EVIDENCE_MAY_REOPEN",
        "CURRENT_PRODUCT_FACTS_REQUIRE_FRESH_VERIFICATION",
      ]
    }

def build_projection(records:list[dict])->dict:
    counts={k:0 for k in CATEGORY_RULES}
    for r in records:
        for c in r.get("ai_categories") or []:counts[c]=counts.get(c,0)+1
    return {
      "schema":"TAKY_AI_REFERENCE_INDEX_V1",
      "authoritative":False,
      "projection_role":"AI_REFERENCE_DISCOVERY_AND_SYSTEM_GROW_INPUT",
      "owner":"SYSTEM_GROW",
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "source_count":len(records),
      "record_kind_counts":{
        "source_reference":sum(1 for r in records if r.get("record_kind")=="SOURCE_REFERENCE"),
        "validated_mining_atom":sum(1 for r in records if r.get("record_kind")=="VALIDATED_MINING_ATOM"),
        "discovery_reference":sum(1 for r in records if r.get("record_kind")=="DISCOVERY_REFERENCE"),
        "remined_source_reference":sum(1 for r in records if r.get("record_kind")=="REMINED_SOURCE_REFERENCE"),
      },
      "outcome_evidence_counts":{
        "verified_success":sum(1 for r in records if r.get("outcome_evidence_state")=="VERIFIED_SUCCESS_PRESENT"),
        "verified_failure_or_regression":sum(1 for r in records if r.get("outcome_evidence_state")=="VERIFIED_FAILURE_OR_REGRESSION_PRESENT"),
        "no_verified_outcome_yet":sum(1 for r in records if r.get("outcome_evidence_state")=="NO_VERIFIED_OUTCOME_YET"),
      },
      "category_counts":counts,
      "categories":list(CATEGORY_RULES),
      "records":records,
      "guards":[
        "PROJECTION != SOURCE_OF_TRUTH",
        "INDEXING != CANONICAL_PROMOTION",
        "MODEL_TOOL_FACTS_ARE_TIME_SENSITIVE",
        "AUTHOR != AUTHORITY",
        "DOMAIN_AUTHORITY_NOT_TRANSFERRED_TO_SYSTEM_GROW",
      ]
    }

def refresh_from_repo(root:Path=ROOT, additional_records:Iterable[dict]|None=None)->dict:
    records=load_reference_deltas(root)
    records.extend(load_validated_ai_mining_atoms())
    records.extend(load_ai_discovery_candidates())
    records.extend(load_p0_remined_sources())
    records.extend(load_p1_remined_sources())
    records.extend(load_recovered_hold_sources())
    by={r["source_id"]:r for r in records}
    for r in additional_records or []:
        x=project_record(r,origin_file="RUNTIME_REFERENCE_INTAKE")
        if x:by[x["source_id"]]=x
    records=[by[k] for k in sorted(by)]
    records=_attach_outcome_evidence(records,_load_outcome_utility(root))
    idx=build_projection(records)
    learning=build_learning(records)
    ai_index=root/"CURRENT"/"DATA"/"AI_REFERENCE_INDEX.json"
    ai_learning=root/"CURRENT"/"DATA"/"AI_LEARNING_PROJECTION.json"
    ai_index.parent.mkdir(parents=True,exist_ok=True)
    for path,payload in ((ai_index,idx),(ai_learning,learning)):
        tmp=path.with_suffix(path.suffix+".tmp")
        tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        tmp.replace(path)
    return {"ok":True,"source_count":idx["source_count"],"learning_count":learning["learning_count"],
            "index_path":str(ai_index),"learning_path":str(ai_learning)}

if __name__=="__main__":
    print(json.dumps(refresh_from_repo(),ensure_ascii=False,indent=2))
