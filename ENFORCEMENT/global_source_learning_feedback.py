"""TAKY selected-source adoption feedback candidate. No CURRENT write or promotion.

Full source-universe triage + one confirmed source -> FORMING -> code adoption
-> local app execution -> evidence-backed global feedback *candidate*.
This does NOT claim approved LEARNING or real user outcomes.
"""
import hashlib
import json
from pathlib import Path

from content_supply_index_bridge import _browser_runtime_receipt_verified

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"
SOURCE_ID = "USER_REVIEW:1fe7096c36a73359acf8"
INDEX = EVIDENCE / "USER_REVIEW_AI_DISCOVERY_INDEX_MINED_CANDIDATE_20261014.json"
EXTRACT = EVIDENCE / "USER_REVIEW_MARKDOWN_EVIDENCE_CANDIDATE_20261014.json"
FORMING = EVIDENCE / "TAKY_ONE_SOURCE_FORMING_REAL_APP_20261014.json"
MULTI = EVIDENCE / "TAKY_MULTI_APP_EVIDENCE_VERIFIED_V2_20261014.json"
CODE = REPO / "TAKY" / "ENFORCEMENT" / "ui_playwright_capture.mjs"
GUARD = REPO / "TAKY" / "ENFORCEMENT" / "ai_execution_guard.py"
MAX_BYTES = 8 * 1024 * 1024

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load_json(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("EXCESSIVE_EVIDENCE_BYTES")
    return json.loads(path.read_text(encoding="utf-8-sig"))

def source_assessment(rec, mining_doc):
    sid = rec["source_id"]
    raw_path = Path(rec["path"]).resolve(strict=True)
    root = (REPO / "TAKY-SOURCE-VAULT" / "data" / "direction_intake").resolve(strict=True)
    if raw_path.name != "response.bin" or not raw_path.is_relative_to(root):
        raise ValueError("RAW_OUTSIDE_CAPTURE_ROOT:" + sid)
    data = raw_path.read_bytes()
    if not 0 < len(data) <= MAX_BYTES or sha(data) != rec["content_hash"]:
        raise ValueError("RAW_HASH_MISMATCH:" + sid)
    if mining_doc["source_id"] != sid or mining_doc["raw_sha256"] != sha(data):
        raise ValueError("MINING_SOURCE_SHA_MISMATCH:" + sid)
    lines = data.decode("utf-8-sig").splitlines()
    unit_count = 0
    for unit in mining_doc.get("units", []):
        a = unit["source_anchor"]
        start, end = a["line_start"], a["line_end"]
        if not (1 <= start <= end <= len(lines)):
            raise ValueError("MINING_ANCHOR_RANGE_INVALID:" + sid)
        contents = "\n".join(lines[start-1:end]).strip().encode("utf-8")
        if sha(contents) != unit["content_sha256"]:
            raise ValueError("MINING_ANCHOR_CONTENT_CHANGED:" + sid)
        unit_count += 1
    return {
        "source_id":sid, "title":rec["title"],
        "raw_sha256":sha(data), "raw_verified":True,
        "anchored_extract_units_verified":unit_count,
        "semantic_review_complete":False,
        "index_authoritative":False,
        "learning_promoted":False,
    }

# One-on-one source triage. These are scope choices, NOT mined/approved knowledge.
TRIAGE = {
 "agent-browser / README.md":("TAKY_EXECUTOR_BROWSER","COMPARE_ONLY","Existing browser evidence method; compare CLI cost, no installation"),
 "awesome-llm-apps / README.md":("TAKY_AI_WORKBENCH_REFERENCE","DISCOVERY_ONLY","Catalogue, not independent app production proof"),
 "skills / skills/find-skills/SKILL.md":("TAKY_SKILL_NECESSITY_GATE","CANDIDATE","Capability discovery must not auto-install skills"),
 "graphify / README.md":("TAKY_CODE_RELATION_INDEX","CANDIDATE","Graph view must not replace RAW/INDEX/CURRENT authority"),
 "gsd-core / README.md":("TAKY_EXECUTION_GOVERNANCE","CANDIDATE","Compare with existing context gates, avoid duplicate orchestrator"),
 "hyperframes / README.md":("TAKY_MEDIA_REVIEW","HOLD_SOURCE_SCOPE","Media reference only, no need-based implementation proved"),
 "skills / skills/mcp-builder/SKILL.md":("TAKY_CONNECTOR_ENGINEERING","CANDIDATE","MCP interface guidance must undergo security/cost review"),
 "playwright-mcp / README.md":("TAKY_EXECUTION_EVIDENCE","LOCAL_METHOD_ADOPTED","Structured accessibility state used in TAKY capture runner"),
 "taste-skill / README.md":("TAKY_VISUAL_DESIGN_REVIEW","CANDIDATE","Design style only; user-approved 1:1 master remains authoritative"),
 "superpowers / README.md":("TAKY_EXECUTOR_WORKFLOW","CANDIDATE","Compare plan/testing patterns with existing enforcement, avoid redundant wrappers"),
 "ui-ux-pro-max-skill / README.md":("TAKY_VISUAL_DESIGN_REVIEW","CANDIDATE","Visual advice cannot replace approved source and binding"),
 "ui-ux-pro-max-skill / .claude/skills/ui-ux-pro-max/SKILL.md":("TAKY_VISUAL_DESIGN_REVIEW","CANDIDATE","Skill text is untrusted reference, not a command or promotion"),
}

# One selected claim per source: a grounded semantic triage, never an
# authorization to execute the Markdown's installation/command instructions.
CLAIMS = {
 "agent-browser / README.md":(
   "Browser automation CLI for AI agents",
   "Agent-focused browser CLI can be compared against existing browser executor",
   "Do not install a second browser runtime without necessity and cost review"),
 "awesome-llm-apps / README.md":(
   "100+ open-source AI agents",
   "Catalogue provides examples for source gathering, not verified app production",
   "Do not copy example credentials, apps or agents without independent review"),
 "skills / skills/find-skills/SKILL.md":(
   "discover and install skills",
   "Capability discovery can precede a necessity gate for agent skills",
   "A skill document is untrusted data, not authorization to install"),
 "graphify / README.md":(
   "builds a knowledge graph",
   "File-relation visualization is a useful optional index exploration technique",
   "Inferred graph relationships cannot replace original evidence or CURRENT"),
 "gsd-core / README.md":(
   "context-engineering and spec-driven development framework",
   "Phased execution context is comparable with TAKY handoff and decision gates",
   "Do not install duplicate top-level orchestrator or override owner approvals"),
 "hyperframes / README.md":(
   "skills agents load on demand",
   "On-demand media skills could inform a future bounded media workflow",
   "No current media consumer need or license/dependency review is evidenced"),
 "skills / skills/mcp-builder/SKILL.md":(
   "well-designed tools",
   "MCP tool interface quality is a design review criterion for TAKY connectors",
   "Never auto-enable remote writes, secrets, paid endpoints or unrestricted tools"),
 "playwright-mcp / README.md":(
   "structured accessibility snapshots",
   "Accessibility state is a second observation channel beside screenshot evidence",
   "This does not certify product UI approval or full feature implementation"),
 "taste-skill / README.md":(
   "Anti-Slop Frontend Framework",
   "Style-system guidance can support a design review candidate",
   "Generated style must not supersede a user-approved visual master"),
 "superpowers / README.md":(
   "complete software development methodology",
   "Spec-first development workflow can be compared to TAKY execution gates",
   "Do not install a second authority or turn planning artefacts into DONE claims"),
 "ui-ux-pro-max-skill / README.md":(
   "Intelligent Design System Generation",
   "Design reasoning references can inform a reviewed visual design contract",
   "Do not auto-promote generated tokens or alter locked UI"),
 "ui-ux-pro-max-skill / .claude/skills/ui-ux-pro-max/SKILL.md":(
   "Searchable local UI/UX guidance",
   "Queryable style and accessibility checks are possible review inputs",
   "Unverified skill contents are non-executable and not UI approval"),
}

def selected_semantic_claim(rec, doc):
    phrase, interpretation, exclusion = CLAIMS[rec["title"]]
    unit = next((u for u in doc["units"]
        if phrase.casefold() in u.get("excerpt","").casefold()),None)
    if unit is None:
        raise ValueError("SOURCE_SELECTED_CLAIM_NOT_EXTRACTED:" + rec["source_id"])
    return {
        "source_claim_search_phrase":phrase,
        "reviewed_interpretation":interpretation,
        "reject_or_hold_rule":exclusion,
        "anchored_unit_id":unit["unit_id"],
        "anchored_start_line":unit["source_anchor"]["line_start"],
        "anchored_end_line":unit["source_anchor"]["line_end"],
        "anchored_content_sha256":unit["content_sha256"],
        "claim_review_scope":"ONE_SELECTED_SOURCE_CLAIM_NOT_WHOLE_DOCUMENT",
        "adoption_authority":"SEMANTIC_CANDIDATE_ONLY",
        "full_mining_and_forming_done":False
    }

def check_runtime(row, work_id):
    app = row["app"]
    run_id = row["run_id"]
    if not run_id.startswith(("taky-cross-app-", "source-playwright-playcamp-")):
        raise ValueError("RUN_ID_UNKNOWN")
    file = EVIDENCE / "UI_BROWSER_RECEIPTS" / run_id / "browser_receipt.json"
    if not file.is_file():
        raise ValueError("EXECUTION_RECEIPT_MISSING:" + app)
    data = load_json(file)
    if data["run_id"] != run_id or data.get("target_kind") != "LOOPBACK_APP":
        raise ValueError("RUNTIME_SCOPE_MISMATCH:" + app)
    if data["work_id"] not in (work_id, "TAKY-PLAYWRIGHT-SOURCE-MULTIAPP"):
        raise ValueError("RUNTIME_WORK_SCOPE_MISMATCH:" + app)
    if any(s.get("status") != "PASS" for s in data.get("steps", [])):
        raise ValueError("RUNTIME_STEPS_FAILED:" + app)
    if row.get("steps") != len(data["steps"]):
        raise ValueError("RUNTIME_STEP_COUNT_CHANGED:" + app)
    if (row["screenshot_sha256"] != data["rendered_screenshot"]["sha256"]
        or row["accessibility_sha256"] != data["accessibility_snapshot"]["sha256"]):
        raise ValueError("RUNTIME_IMAGE_OR_A11Y_HASH_MISMATCH:" + app)
    receipt_hash = sha(file.read_bytes())
    context = {
        "work_id":data["work_id"], "screen_id":data["screen_id"],
        "run_id":run_id, "viewport":data["viewport"],
        "visual":{"rendered_screenshot":data["rendered_screenshot"]},
        "browser_runtime_receipt":{"path":str(file),"sha256":receipt_hash},
    }
    if not _browser_runtime_receipt_verified(context):
        raise ValueError("RUNTIME_GUARD_REJECTED:" + app)
    if data.get("page_errors") or data.get("is_approved_design") is not False:
        raise ValueError("RUNTIME_UNEXPECTED_RESULT:" + app)
    return {
        "consumer_app":app,"run_id":run_id,
        "tested_steps":len(data["steps"]),
        "observed_text":row.get("observed_final_accessibility_text"),
        "runtime_receipt_sha256":receipt_hash,
        "observed_local_scenario_verified":True,
        "application_learning_event_consumed":False,
        "deployment_approved":False,
    }

def main():
    index = load_json(INDEX)
    mining = load_json(EXTRACT)
    forming = load_json(FORMING)
    multi = load_json(MULTI)
    assert index["authoritative"] is False
    records = index["records"]
    by_id = {x["source_id"]:x for x in records}
    mined_by_id = {x["source_id"]:x for x in mining["sources"]}
    if len(records) != 12 or len(by_id) != 12 or set(by_id) != set(mined_by_id):
        raise ValueError("SOURCE_UNIVERSE_COVERAGE_INVALID")
    reviews = []
    for record in records:
        checked = source_assessment(record, mined_by_id[record["source_id"]])
        consumer,action,reason = TRIAGE[record["title"]]
        checked.update({
            "proposed_consumer":consumer,"triage":action,"rationale":reason,
            "source_scope":"SINGLE_DOCUMENT_NOT_FULL_REPO_OR_SOCIAL_POST",
            "independent_semantic_approval":False,
        })
        reviews.append(checked)
    selected = by_id[SOURCE_ID]
    selected_doc = mined_by_id[SOURCE_ID]
    if forming["source"]["source_id"] != SOURCE_ID or forming["source"]["sha256"] != selected["content_hash"]:
        raise ValueError("FORMING_SOURCE_ID_OR_HASH_CHANGED")
    line_no = forming["source"]["selected_source_line"]
    source_lines = Path(selected["path"]).read_text(encoding="utf-8-sig").splitlines()
    if not 1 <= line_no <= len(source_lines):
        raise ValueError("SEMANTIC_LINE_OUTSIDE_RAW")
    line_text = source_lines[line_no-1]
    if "structured accessibility snapshots" not in line_text:
        raise ValueError("SOURCE_CLAIM_NOT_GROUNDED")
    if not any(u["source_anchor"]["line_start"] <= line_no <= u["source_anchor"]["line_end"] for u in selected_doc["units"]):
        raise ValueError("SOURCE_CLAIM_NOT_EXTRACTED")
    if (forming["execution"]["result"] != "REAL_BUILT_APP_BROWSER_INTERACTION_PASS_NOT_APPROVED_UI"
        or forming["forming"]["semantic_forming_scope"] != "ONE_METHOD_ONE_VERIFIED_APP_SCENARIO"):
        raise ValueError("ADOPTION_SCOPE_MISMATCH")
    code = CODE.read_bytes()
    guard = GUARD.read_bytes()
    if b"ariaSnapshot" not in code or b"accessibility_snapshot" not in code:
        raise ValueError("ADOPTED_METHOD_MISSING_IN_EXECUTOR")
    if b"_browser_runtime_receipt_verified" not in guard:
        raise ValueError("RECEIPT_GATE_NOT_IN_CODE")
    if multi["source_id"] != SOURCE_ID or multi["status"] != "LOCAL_RUNTIME_EVIDENCE_VERIFIED_NOT_APP_COMPLETION":
        raise ValueError("MULTI_APP_EVIDENCE_SCOPE_MISMATCH")
    outcomes = [check_runtime(x,forming["work_id"]) for x in multi["method_consumers"]]
    if len(outcomes) != 4 or len({x["consumer_app"] for x in outcomes}) != 4:
        raise ValueError("UNEXPECTED_APP_COVERAGE")
    # Adversarial self-test. Any forged source hash or observed screenshot must fail.
    spoof = dict(selected);spoof["content_hash"] = "0"*64
    try: source_assessment(spoof,selected_doc)
    except ValueError as exc: assert "RAW_HASH_MISMATCH" in str(exc)
    else: raise AssertionError("FORGED_RAW_HASH_WAS_ACCEPTED")
    spoof_run = dict(multi["method_consumers"][0]);spoof_run["screenshot_sha256"] = "0"*64
    try: check_runtime(spoof_run,forming["work_id"])
    except ValueError as exc: assert "RUNTIME_IMAGE_OR_A11Y_HASH_MISMATCH" in str(exc)
    else: raise AssertionError("FORGED_IMAGE_HASH_WAS_ACCEPTED")
    report={
      "schema":"TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_V1",
      "authority":"WORKBENCH_REVIEW_CANDIDATE_NOT_CURRENT",
      "source_count":len(reviews),
      "extractive_units_sha_verified":sum(x["anchored_extract_units_verified"] for x in reviews),
      "source_triage":reviews,
      "selected_adoption":{
        "source_id":SOURCE_ID,"raw_sha256":selected["content_hash"],
        "work_id":forming["work_id"],
        "claim_anchor":{"line":line_no,"source_line_sha256":sha(line_text.encode("utf-8"))},
        "method":"Structured accessibility snapshots complement screenshot-based browser evidence",
        "implementation":{"runner":"TAKY/ENFORCEMENT/ui_playwright_capture.mjs",
           "runner_sha256":sha(code),
           "guard":"TAKY/ENFORCEMENT/ai_execution_guard.py",
           "guard_sha256":sha(guard)},
        "local_consumer_observations":outcomes,
        "feedback_candidate":{
            "observed_behavior":"Existing TAKY browser evidence collector operated on four different local app scenarios",
            "verified_local_scenario_count":4,
            "verified_local_step_count":sum(x["tested_steps"] for x in outcomes),
            "known_limit":"Screens are evidence of runner behavior, not proof of app education, formal approval or production rollout",
            "proposed_next_knowledge_action":"Compare Playwright CLI token cost vs MCP only when a real necessity gate warrants it; preserve independently reviewed source and do not install by default",
            "global_knowledge_update_approved":False,
            "global_forming_semantic_review_complete":False,
            "real_user_feedback_received":False,
            "persistent_source_attributed_user_outcome":False,
        }
      },
      "global_pipeline":{
       "RAW":"VERIFIED_12_OFFICIAL_DOCS",
       "EXTRACTIVE_MINING":"SOURCE_ANCHORED_12_DOCS",
       "SEMANTIC_MINING":"TRIAGE_ONLY_REVIEW_REQUIRED",
       "INDEX":"CANDIDATE_ONLY_NOT_AUTHORITY",
       "FORMING":"ONE_METHOD_LOCAL_ADOPTION_11_PENDING",
       "LEARNING":"REVIEW_FEEDBACK_CANDIDATE_ONLY",
       "APP_CONSUMPTION":"4_LOCAL_BROWSER_SCENARIOS_NOT_PEDAGOGY",
       "USER_OUTCOME":"NOT_PROVEN",
       "FEEDBACK":"LOCAL_EVIDENCE_CANDIDATE_NOT_APPLIED_TO_CURRENT"
      },
      "negative_checks":["FORGED_RAW_SHA_REJECTED","FORGED_RUNTIME_SCREENSHOT_SHA_REJECTED"],
      "operating_current_modified":False,
      "cost_incurred":False,
    }
    output=EVIDENCE/"TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json"
    with output.open("x",encoding="utf-8") as file:
        json.dump(report,file,ensure_ascii=False,indent=2)
    print(json.dumps({
      "status":"GLOBAL_FEEDBACK_CANDIDATE_READY_NOT_PROMOTED",
      "source_count":len(reviews),
      "extracted_line_anchored_units":report["extractive_units_sha_verified"],
      "local_scenario_count":len(outcomes),
      "test_steps":report["selected_adoption"]["feedback_candidate"]["verified_local_step_count"],
      "other_sources_remaining_semantic_review":11,
      "user_outcome_verified":False,
      "output":str(output)
    },ensure_ascii=False))
# This API extends the existing Central event stream, not a second knowledge DB.
# The caller owns its transaction. No function commits or changes source/stage,
# CURRENT, schema, learner data, or application code.
FEEDBACK_KIND = "SYSTEM_GROW_CODE_CONSUMER_FEEDBACK_V1"
DECISION_KIND = "SYSTEM_GROW_CODE_CONSUMER_DECISION_V1"


def _forming(binding, trusted_policy=None):
    import subprocess
    bridge = Path(__file__).with_name("system_grow_forming_bridge.cjs")
    result = subprocess.run(
        ["node", str(bridge)], input=json.dumps({"binding": binding,
        "trustedPolicy": trusted_policy}), text=True, encoding="utf-8",
        capture_output=True, timeout=20, check=True)
    return json.loads(result.stdout)


def _technical_binding(c):
    """Resolve the selected claim from Central, then verify original bytes again."""
    import taky_central_source_factory as factory
    sid = "raw:b33aa71a13d655e96e6b736d0c9de1e5ddea52f205916ca20b876387ff830e87"
    row = c.execute("SELECT receipt_json FROM stage WHERE source_id=? AND stage='ANALYZE'",
                    (sid,)).fetchone()
    if row is None:
        raise ValueError("SEMANTIC_CANDIDATE_MISSING")
    claim = json.loads(row[0])
    unit = factory.read_verified_evidence_unit(c, sid, claim.get("source_unit_id"))
    if (not unit or unit["raw_sha256"] != claim.get("source_raw_sha256")
        or unit["content_sha256"] != claim.get("source_chunk_sha256")
        or claim.get("original_source_id") != SOURCE_ID
        or claim.get("suggested_consumer") != "TAKY_EXECUTION_EVIDENCE"
        or claim.get("claim_phrase") != "structured accessibility snapshots"
        or claim["claim_phrase"] not in unit["content"]
        or not claim.get("candidate_interpretation") or not claim.get("reject_or_hold_rule")):
        raise ValueError("TECHNICAL_SOURCE_SEMANTIC_BINDING_INVALID")
    source = c.execute("SELECT original_sha256 FROM source WHERE id=?", (sid,)).fetchone()
    if source is None or source[0] != unit["raw_sha256"]:
        raise ValueError("CENTRAL_SOURCE_HASH_MISMATCH")
    origins = {}
    for key, kind in (("consumption", "LOCAL_TECHNIQUE_USE_FEEDBACK_CANDIDATE"),
                      ("projection", "GLOBAL_AI_LEARNING_LOCAL_TECHNIQUE_CANDIDATE")):
        rows = c.execute("SELECT event_id,detail_json FROM event WHERE source_id=? AND kind=?",
                         (sid, kind)).fetchall()
        if len(rows) != 1:
            raise ValueError("EXISTING_SYSTEM_GROW_LINEAGE_MISSING_OR_AMBIGUOUS")
        origins[key] = (rows[0][0], json.loads(rows[0][1]))
    use, learned = origins["consumption"][1], origins["projection"][1]
    if (use.get("original_source_id") != SOURCE_ID
        or use.get("raw_sha256") != unit["raw_sha256"]
        or learned.get("source_id") != SOURCE_ID
        or learned.get("source_raw_sha256") != unit["raw_sha256"]
        or learned.get("selected_claim_anchor_sha256") != unit["content_sha256"]
        or learned.get("local_consumption_event_id") != origins["consumption"][0]
        or learned.get("local_consumption_report_sha256") != use.get("observation_report_sha256")):
        raise ValueError("EXISTING_SYSTEM_GROW_LINEAGE_CHANGED")
    code = CODE.read_bytes()
    if b"ariaSnapshot" not in code or b"accessibility_snapshot" not in code:
        raise ValueError("CODE_CONSUMER_METHOD_MISSING")
    return {"source_id": sid, "original_source_id": SOURCE_ID,
        "unit_id": unit["unit_id"], "raw_sha256": unit["raw_sha256"],
        "anchor_sha256": unit["content_sha256"],
        "line_start": unit["line_start"], "line_end": unit["line_end"],
        "owner": "SYSTEM_GROW", "consumer": "TAKY_EXECUTION_EVIDENCE",
        "consumer_path": "ENFORCEMENT/ui_playwright_capture.mjs",
        "consumer_revision": sha(code), "guard_revision": sha(GUARD.read_bytes()),
        "semantic_decision": claim["candidate_interpretation"],
        "exclusion": claim["reject_or_hold_rule"],
        "semantic_disposition": claim.get("semantic_disposition"),
        "origin_consumption_event_id": origins["consumption"][0],
        "origin_projection_event_id": origins["projection"][0],
        "evidence_refs": ["CENTRAL_DETAIL:" + sid + ":" + unit["unit_id"]]}


def _fingerprint(value):
    import taky_central_source_factory as factory
    return sha(factory.compact(value).encode("utf-8"))


def _event_payload(c, event_id, kind, sid):
    row = c.execute("SELECT source_id,kind,detail_json FROM event WHERE event_id=?",
                    (event_id,)).fetchone()
    if row is None or row[0] != sid or row[1] != kind:
        raise ValueError("FEEDBACK_EVENT_LINK_INVALID")
    data = json.loads(row[2])
    check = dict(data)
    digest = check.pop("payload_sha256", None)
    if digest != _fingerprint(check):
        raise ValueError("FEEDBACK_EVENT_HASH_CHANGED")
    return data


def _append_once(c, sid, kind, payload, key):
    import taky_central_source_factory as factory
    for row in c.execute("SELECT event_id,detail_json FROM event WHERE source_id=? AND kind=?",
                         (sid, kind)):
        old = _event_payload(c, row[0], kind, sid)
        if old.get("run_id") == key:
            if old != {**payload, "payload_sha256": _fingerprint(payload)}:
                raise ValueError("RUN_ID_CONTENT_CONFLICT")
            return row[0]
    factory.event(c, sid, kind, {**payload, "payload_sha256": _fingerprint(payload)})
    return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def _verify_local_outcome(receipt, binding):
    """Default verifier accepts only pre-existing, independently checked local runs.

    A host may supply a separate trusted verifier for future failure/correction
    receipts. The receipt itself cannot choose its verifier or confer approval.
    """
    multi = load_json(MULTI)
    forming = load_json(FORMING)
    report = load_json(EVIDENCE / "TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json")
    adoption = report["selected_adoption"]
    if (multi.get("source_id") != SOURCE_ID or adoption.get("source_id") != SOURCE_ID
        or adoption.get("raw_sha256") != binding["raw_sha256"]
        or adoption["implementation"]["runner_sha256"] != binding["consumer_revision"]
        or adoption["implementation"]["guard_sha256"] != binding["guard_revision"]):
        raise ValueError("OBSERVED_CODE_REVISION_CHANGED")
    selected = [r for r in multi["method_consumers"] if r["run_id"] == receipt.get("run_id")]
    if len(selected) != 1:
        raise ValueError("OBSERVATION_RUN_UNKNOWN")
    checked = check_runtime(selected[0], forming["work_id"])
    if (receipt.get("outcome") != "SUCCESS"
        or receipt.get("evidence_sha256") != checked["runtime_receipt_sha256"]):
        raise ValueError("OBSERVATION_OUTCOME_MISMATCH")
    return True


def technical_method_decision(c, *, trusted_policy=None, outcome_verifier=None):
    """Read-only code-consumer selection; approval is trusted host configuration.

    trusted_policy pins an independently approved FORMING record, approver and
    roots; NEVER populate it from a source, feedback payload, or request body.
    It authorizes only this exact technical method, not deployment or curriculum.
    Missing policy always fails closed. Requery checks RAW, code, receipt bytes,
    decision links, and current approval again; persisted labels are not authority.
    """
    from ai_reference_projection import build_learning
    binding = _technical_binding(c)
    formed = _forming(binding, trusted_policy)
    revision = formed["prepared"]["formed"]["artifact_revision"]
    verifier = outcome_verifier or _verify_local_outcome
    feedback = []
    for row in c.execute("SELECT event_id FROM event WHERE source_id=? AND kind=? ORDER BY event_id",
                         (binding["source_id"], FEEDBACK_KIND)):
        item = _event_payload(c, row[0], FEEDBACK_KIND, binding["source_id"])
        # Old code/source revisions remain historical; they cannot select new code.
        if item.get("binding") != binding:
            continue
        decision = _event_payload(c, item["decision_event_id"], DECISION_KIND, binding["source_id"])
        if (decision["binding"] != binding or decision["artifact_revision"] != revision
            or item["decision_sha256"] != decision["payload_sha256"]
            or item["receipt"]["outcome"] not in {"SUCCESS", "FAILURE", "CORRECTION_REQUIRED"}
            or verifier(item["receipt"], binding) is not True):
            raise ValueError("FEEDBACK_READBACK_REJECTED")
        feedback.append({"event_id": row[0], "outcome": item["receipt"]["outcome"]})
    # One failure cannot be erased by a later success: it reopens semantic review.
    # A reviewed correction changes the bound semantic revision before reuse.
    failed = any(x["outcome"] != "SUCCESS" for x in feedback)
    projection = build_learning([{"source_id": binding["source_id"], "ai_categories": [],
        "learning_eligible": True, "learning_candidates": [{
            "learning_id": "AI-LRN-ACCESSIBILITY-LOCAL-REVIEW-CANDIDATE",
            "insight": binding["semantic_decision"]}]}],
            verified_dynamic_source_ids=frozenset({binding["source_id"]}))
    learned = projection.get("learnings", [])
    if (projection.get("owner") != "SYSTEM_GROW" or projection.get("authoritative") is not False
        or len(learned) != 1 or learned[0].get("state") != "EVIDENCE_CANDIDATE"
        or learned[0].get("canonical_promotion") is not False
        or learned[0].get("insight") != binding["semantic_decision"]
        or learned[0].get("evidence_refs") != ["INDEX:" + binding["source_id"]]):
        raise ValueError("SYSTEM_GROW_CONSUMER_PROJECTION_REJECTED")
    # The code selector consumes the existing projection only after its exact
    # source/meaning is matched to the independently gated FORMING revision.
    action = "REVIEW_REQUIRED" if failed else "REUSE_CANDIDATE" if feedback else "LOCAL_EVALUATION_REQUIRED"
    approved = formed["gate"].get("ok") is True and not failed
    if approved:
        action = "SELECT_APPROVED_LOCAL_METHOD"
    return {"binding": binding, "artifact_revision": revision,
        "selected_learning_id": learned[0]["learning_id"],
        "selected_learning_sha256": _fingerprint(learned[0]),
        "prepared": formed["prepared"], "approval_gate": formed["gate"],
        "decision": action, "approved_local_consumption": approved,
        "feedback": feedback, "knowledge_projection": projection,
        "current_written": False, "release_approved": False,
        "educational_learning": False}


def record_technical_method_decision(c, run_id, *, trusted_policy=None, outcome_verifier=None):
    import re
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{3,120}", run_id):
        raise ValueError("DECISION_RUN_ID_INVALID")
    result = technical_method_decision(c, trusted_policy=trusted_policy, outcome_verifier=outcome_verifier)
    payload = {k: result[k] for k in ("binding", "artifact_revision", "decision", "approved_local_consumption",
                                     "selected_learning_id", "selected_learning_sha256")}
    payload.update(run_id=run_id, feedback_event_ids=[x["event_id"] for x in result["feedback"]],
                   authority="LOCAL_TECHNICAL_DECISION_NOT_CANONICAL", current_written=False)
    event_id = _append_once(c, result["binding"]["source_id"], DECISION_KIND, payload, run_id)
    return {**result, "decision_event_id": event_id}


def record_technical_feedback(c, decision_event_id, receipt, *, outcome_verifier=None):
    binding = _technical_binding(c)
    decision = _event_payload(c, decision_event_id, DECISION_KIND, binding["source_id"])
    if decision["binding"] != binding:
        raise ValueError("FEEDBACK_CODE_OR_SOURCE_REVISION_CHANGED")
    if (not isinstance(receipt, dict) or not receipt.get("run_id")
        or receipt.get("outcome") not in {"SUCCESS", "FAILURE", "CORRECTION_REQUIRED"}
        or (outcome_verifier or _verify_local_outcome)(receipt, binding) is not True):
        raise ValueError("FEEDBACK_OUTCOME_UNVERIFIED")
    payload = {"run_id": receipt["run_id"], "binding": binding,
        "decision_event_id": decision_event_id, "decision_sha256": decision["payload_sha256"],
        "receipt": receipt, "authority": "TECHNICAL_FEEDBACK_CANDIDATE",
        "approved_knowledge": False, "current_written": False}
    return _append_once(c, binding["source_id"], FEEDBACK_KIND, payload, receipt["run_id"])


def consume_verified_local_observation(c, decision_run_id, observed_run_id, *, trusted_policy=None):
    """Bridge an independently verified prior browser run into durable Central feedback.

    This is a local evidence replay/consumer adapter, NOT a live browser hook,
    semantic approval, production activation, or a new learning engine.
    Caller owns the SQLite connection; original RAW/CURRENT are never written.
    Both event inserts are atomic, including in an existing host transaction.
    """
    import re
    if not isinstance(decision_run_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{3,120}", decision_run_id):
        raise ValueError("DECISION_RUN_ID_INVALID")
    report = load_json(EVIDENCE / "TAKY_GLOBAL_SOURCE_SEMANTIC_TRIAGE_FEEDBACK_CANDIDATE_20261014.json")
    observed = [r for r in report["selected_adoption"]["local_consumer_observations"]
                if r.get("run_id") == observed_run_id]
    if len(observed) != 1 or not observed[0].get("observed_local_scenario_verified"):
        raise ValueError("OBSERVATION_RUN_UNKNOWN_OR_UNVERIFIED")
    receipt = {"run_id": observed_run_id, "outcome": "SUCCESS",
               "evidence_sha256": observed[0]["runtime_receipt_sha256"]}
    c.execute("SAVEPOINT verified_local_observation")
    try:
        before = technical_method_decision(c, trusted_policy=trusted_policy)
        binding = before["binding"]
        if _verify_local_outcome(receipt, binding) is not True:
            raise ValueError("OBSERVATION_OUTCOME_UNVERIFIED")
        existing = []
        for row in c.execute("SELECT event_id FROM event WHERE source_id=? AND kind=?",
                             (binding["source_id"], DECISION_KIND)):
            item = _event_payload(c, row[0], DECISION_KIND, binding["source_id"])
            if item["run_id"] == decision_run_id:
                existing.append((row[0], item))
        if len(existing) > 1:
            raise ValueError("DECISION_RUN_ID_AMBIGUOUS")
        if existing:
            decision_event_id, recorded = existing[0]
            if recorded["binding"] != binding or recorded["artifact_revision"] != before["artifact_revision"]:
                raise ValueError("DECISION_REPLAY_BINDING_CHANGED")
        else:
            decision_event_id = record_technical_method_decision(
                c, decision_run_id, trusted_policy=trusted_policy)["decision_event_id"]
        feedback_event_id = record_technical_feedback(c, decision_event_id, receipt)
        after = technical_method_decision(c, trusted_policy=trusted_policy)
        result = {"status": "LOCAL_VERIFIED_EVIDENCE_REPLAYED",
                  "source_id": binding["source_id"], "original_source_id": binding["original_source_id"],
                  "raw_sha256": binding["raw_sha256"], "anchor_sha256": binding["anchor_sha256"],
                  "forming_revision": before["artifact_revision"],
                  "consumer_revision": binding["consumer_revision"],
                  "decision_event_id": decision_event_id, "feedback_event_id": feedback_event_id,
                  "before": before["decision"], "after": after["decision"],
                  "feedback_count": len(after["feedback"]),
                  "semantic_approved": after["approved_local_consumption"],
                  "global_knowledge_approved": after["knowledge_projection"]["authoritative"],
                  "production_consumption_verified": False,
                  "source_and_current_written": False}
        c.execute("RELEASE SAVEPOINT verified_local_observation")
        return result
    except BaseException:
        c.execute("ROLLBACK TO SAVEPOINT verified_local_observation")
        c.execute("RELEASE SAVEPOINT verified_local_observation")
        raise


if __name__=="__main__":
    import sys
    if sys.argv[1:] == ["--technical-decision-readback"]:
        import sqlite3
        from contextlib import closing
        import taky_central_source_factory as factory
        # This entry point cannot write even accidentally via an imported helper.
        with closing(sqlite3.connect(factory.DB.as_uri() + "?mode=ro", uri=True)) as c:
            c.row_factory = sqlite3.Row
            print(json.dumps(technical_method_decision(c), ensure_ascii=False))
    elif sys.argv[1:]:
        raise SystemExit("Use --technical-decision-readback or no arguments for legacy report")
    else:
        main()
