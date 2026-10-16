"""Non-authoritative INDEX lookup for the TAKY content supply contract.

A RAW filename in the INDEX is a reference, not an implementation or a
FORMING-ready source. The bounded receipt below rechecks only matched review
RAW files and restores the missing MINING stage before FORMING.
"""
import hashlib
import json
from pathlib import Path
from ai_execution_guard import _browser_runtime_receipt_verified
from content_supply_contract import audit
from data_index_search import load_index, search

REVIEW_RAW_ROOT = Path(__file__).resolve().parents[2] / "TAKY-SOURCE-VAULT" / "data" / "direction_intake"
MAX_REVIEW_RAW_BYTES = 8 * 1024 * 1024


def _review_raw_receipt(record):
    if (not isinstance(record, dict)
        or record.get("source_family") != "USER_PROVIDED_TREND_REVIEW"
        or not str(record.get("source_id") or "").startswith("USER_REVIEW:")):
        return None
    location = str(record.get("locator") or "")
    digest = str(record.get("content_hash") or "").lower()
    base = {"source_id": record["source_id"], "scope": "SINGLE_URL_DOCUMENT",
            "content_mining_state": record.get("mining_extraction_state") or "NOT_VERIFIED",
            "extractive_evidence_ref": record.get("extractive_evidence_ref"),
            "extracted_unit_count": record.get("extracted_unit_count", 0),
            "semantic_review_state": "PENDING",
            "forming_state": "NOT_STARTED", "raw_status": "UNVERIFIED"}
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return {**base, "raw_status": "HASH_MISSING"}
    try:
        target = Path(location).resolve(strict=True)
        root = REVIEW_RAW_ROOT.resolve(strict=True)
        if target.name != "response.bin" or not target.is_relative_to(root):
            return {**base, "raw_status": "OUTSIDE_MANAGED_INTAKE"}
        size = target.stat().st_size
        if not target.is_file() or not 0 < size <= MAX_REVIEW_RAW_BYTES:
            return {**base, "raw_status": "MISSING_OR_OVERSIZED"}
        h = hashlib.sha256()
        with target.open("rb") as f:
            for chunk in iter(lambda: f.read(256 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != digest:
            return {**base, "raw_status": "HASH_CHANGED"}
        return {**base, "raw_status": "HASH_VERIFIED_AT_LOOKUP",
                "content_sha256": digest, "raw_path": str(target)}
    except (OSError, ValueError, RuntimeError):
        return {**base, "raw_status": "RAW_UNREADABLE"}


EVIDENCE_ROOT = Path(__file__).resolve().parents[2] / "TAKY_AI_WORKBENCH" / "01_BACKLOG_AND_ADOPTION" / "80_EVIDENCE"


def _bounded_evidence_json(source, limit=2_000_000):
    """Read existing review evidence; never treat its text as executable instructions."""
    try:
        root = EVIDENCE_ROOT.resolve(strict=True)
        target = Path(source).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file():
            return None
        if not 0 < target.stat().st_size <= limit:
            return None
        data = json.loads(target.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, TypeError, UnicodeError):
        return None


def _forming_capability_receipt(record, requirement, contract, receipt, forming_file):
    """Verify selected-source capability adoption without ever authorizing app content.

    The outcome applies ONLY to the exact WORK_ID, SOURCE_ID and observed app
    scenario. It cannot mark MINING of other sources, learning, UI approval or
    deployment complete.
    """
    result = {"state": "FORMING_EVIDENCE_RECHECK_REQUIRED", "evidence_based_next_stage": "FORMING",
              "forming_verified": False, "release_approved": False, "learning_consumed": False}
    def reject(reason):
        return {**result, "forming_validation_error": reason}
    if (not isinstance(record, dict) or not isinstance(requirement, dict)
        or receipt.get("raw_status") != "HASH_VERIFIED_AT_LOOKUP"):
        return reject("RAW_NOT_VERIFIED")
    formed = _bounded_evidence_json(forming_file)
    if not formed or formed.get("schema") != "TAKY_ONE_SOURCE_FORMING_REAL_APP_V1":
        return reject("FORMING_SCHEMA_OR_PATH_INVALID")
    source = formed.get("source") or {}
    forming = formed.get("forming") or {}
    execution = formed.get("execution") or {}
    if not all(isinstance(x, dict) for x in (source, forming, execution)):
        return reject("FORMING_FIELDS_INVALID")
    if (formed.get("work_id") != contract.get("work_id")
        or not isinstance(formed.get("work_id"), str)
        or requirement.get("source_id") != record.get("source_id")
        or source.get("source_id") != record.get("source_id")
        or source.get("sha256") != record.get("content_hash")
        or source.get("source_url") != record.get("origin_locator")):
        return reject("WORK_SOURCE_HASH_ID_MISMATCH")
    def normalize_owner(value):
        return str(value or "").upper().replace(" ", "_").replace("-", "_")
    if normalize_owner(forming.get("downstream_app")) != normalize_owner(contract.get("consumer")):
        return reject("CONSUMER_OWNER_MISMATCH")
    if (formed.get("assessment") != "SELECTED_CAPABILITY_FORMED_AND_REAL_BUILT_APP_VALIDATED_NOT_PRODUCTION_PROMOTED"
        or execution.get("result") != "REAL_BUILT_APP_BROWSER_INTERACTION_PASS_NOT_APPROVED_UI"
        or not isinstance(source.get("selected_claim"), str)
        or not source["selected_claim"].strip()
        or execution.get("approved_master_visual_fidelity_verified") is not False
        or execution.get("playcamp_live_working_tree_rebuilt") is True):
        return reject("APPROVAL_OR_COVERAGE_OVERCLAIM")
    try:
        raw = Path(receipt["raw_path"]).resolve(strict=True)
        if raw != Path(source.get("raw_path", "")).resolve(strict=True):
            return reject("RAW_PATH_MISMATCH")
        span_line = source.get("selected_source_line")
        if not isinstance(span_line, int) or isinstance(span_line, bool) or span_line < 1:
            return reject("SOURCE_LINE_INVALID")
        contents = raw.read_bytes().decode("utf-8-sig")
        lines = contents.splitlines()
        if span_line > len(lines) or not lines[span_line - 1].strip():
            return reject("SOURCE_LINE_NOT_FOUND")
        # Proof that this exact line was preserved by the extractive miner.
        extraction = _bounded_evidence_json(record.get("extractive_evidence_ref"),limit=5_000_000)
        if (not extraction
            or extraction.get("schema") != "TAKY_REVIEW_MARKDOWN_EVIDENCE_UNREVIEWED_V1"
            or extraction.get("holds")):
            return reject("MINING_EVIDENCE_MISSING")
        doc = next((x for x in extraction.get("sources", [])
                    if isinstance(x, dict) and x.get("source_id") == record.get("source_id")), None)
        if not doc or doc.get("raw_sha256") != source.get("sha256"):
            return reject("MINING_SOURCE_ID_MISMATCH")
        covering = next((u for u in doc.get("units", [])
                         if isinstance(u, dict)
                         and isinstance(u.get("source_anchor"), dict)
                         and u["source_anchor"].get("line_start", 1) <= span_line <= u["source_anchor"].get("line_end", 0)), None)
        if not covering:
            return reject("MINING_SOURCE_LINE_NOT_ANCHORED")
        anchor = covering["source_anchor"]
        chunk = "\n".join(lines[anchor["line_start"]-1:anchor["line_end"]]).strip()
        if hashlib.sha256(chunk.encode("utf-8")).hexdigest() != covering.get("content_sha256"):
            return reject("MINING_SOURCE_ANCHOR_HASH_CHANGED")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        return reject("RAW_OR_LINEAGE_READBACK_FAILED")
    target = _bounded_evidence_json(execution.get("browser_receipt_path"),limit=128_000)
    if (not target or target.get("schema") not in {
        "TAKY_UI_BROWSER_RUNTIME_RECEIPT_V1",
        "TAKY_UI_BROWSER_RUNTIME_RECEIPT_V2",
    }
        or target.get("run_id") != execution.get("run_id")
        or target.get("work_id") != formed.get("work_id")
        or target.get("target_kind") != "LOOPBACK_APP"):
        return reject("RUNTIME_PROOF_MISSING_OR_MISMATCHED")
    runtime = execution.get("browser_receipt_path")
    try:
        receipt_hash = hashlib.sha256(Path(runtime).read_bytes()).hexdigest()
        runtime_context = {
            "work_id":target["work_id"], "screen_id":target["screen_id"],
            "run_id":target["run_id"], "viewport":target["viewport"],
            "visual":{"rendered_screenshot":target["rendered_screenshot"]},
            "browser_runtime_receipt":{"path":runtime,"sha256":receipt_hash},
        }
        if not _browser_runtime_receipt_verified(runtime_context):
            return reject("BROWSER_RUNTIME_EVIDENCE_INVALID")
        steps = target.get("steps")
        if (len(steps) != execution.get("browser_interaction_steps_passed")
            or len(steps) != execution.get("browser_interaction_steps_total")
            or execution.get("screenshot_sha256_verified") is not True
            or execution.get("accessibility_snapshot_sha256_verified") is not True):
            return reject("RUNTIME_STEPS_OR_SCREENSHOT_UNSUPPORTED")
    except (OSError, KeyError, ValueError, TypeError):
        return reject("RUNTIME_READBACK_FAILED")
    return {
        "state":"REVIEW_FORMING_RUNTIME_VERIFIED",
        "evidence_based_next_stage":"INTEGRATION",
        "forming_verified":True,"release_approved":False,"learning_consumed":False,
        "capability_scope":"ONE_SOURCE_ONE_EXISTING_APP_BUILD_SCENARIO",
        "forming_evidence_ref":str(forming_file),
        "runtime_receipt_ref":str(runtime),
        "verified_source_id":source["source_id"],
        "verified_run_id":execution["run_id"],
        "consumer_adapter":"TAKY_CODE_CAPABILITY_LOCAL_SCENARIO_ONLY",
    }


def inspect(contract, index_path, forming_evidence_path=None):
    result = audit(contract)
    if result.get('reason'):
        return result
    try:
        rows = load_index(Path(index_path))
    except (OSError, ValueError, TypeError) as exc:
        return {**result, 'status': 'HOLD', 'index_error': type(exc).__name__}
    row_by_id = {x.get('source_id'): x for x in rows if isinstance(x, dict)}
    findings = []
    for item in contract['requirements']:
        query = str(item.get('query') or '').strip()
        if not query:
            findings.append({'id': item['id'], 'state': 'QUERY_REQUIRED', 'candidates': []})
            continue
        try:
            hits = search(rows, query, filters={}, limit=5, relation_depth=1).get('results', [])
            ids = [h['source_id'] for h in hits if isinstance(h, dict) and h.get('source_id')]
            receipts = [r for source_id in ids if (r := _review_raw_receipt(row_by_id.get(source_id))) is not None]
            forming_receipt = None
            if receipts:
                verified = [r for r in receipts if r['raw_status'] == 'HASH_VERIFIED_AT_LOOKUP']
                broken = [r for r in receipts if r['raw_status'] != 'HASH_VERIFIED_AT_LOOKUP']
                # A single corrupt review reference must never be masked by a
                # second healthy hit from a related repository.
                next_stage = 'MINING' if verified and not broken else 'GATHERING'
                state = 'RAW_READY_FOR_MINING' if verified and not broken else 'RAW_RECHECK_REQUIRED'
                if (forming_evidence_path is not None and verified and not broken
                    and isinstance(item.get("source_id"), str)
                    and item["source_id"] in ids):
                    selected = row_by_id.get(item["source_id"])
                    raw_receipt = next((r for r in verified if r["source_id"] == item["source_id"]), None)
                    forming_receipt = _forming_capability_receipt(
                        selected, item, contract, raw_receipt, forming_evidence_path
                    ) if raw_receipt else None
                    if forming_receipt:
                        state = forming_receipt["state"]
                        next_stage = forming_receipt["evidence_based_next_stage"]
            else:
                next_stage = None
                state = 'REUSE_CANDIDATES' if ids else 'COVERAGE_RECHECK'
            findings.append({
                'id': item['id'], 'state': state, 'candidates': ids,
                'review_raw_receipts': receipts, 'evidence_based_next_stage': next_stage,
                'forming_receipt': forming_receipt, 'candidate_is_not_consumer_supply': True,
            })
        except (OSError, ValueError, TypeError, KeyError):
            findings.append({'id': item['id'], 'state': 'SEARCH_FAILED', 'candidates': []})
    return {
        **result, 'status': 'HOLD', 'inventory': findings,
        'raw_verified': False, 'production_invoked': False, 'release_approved': False,
        'stage_rule': 'RAW_REFERENCE_ONLY; MINING_BEFORE_FORMING; FORMING_BEFORE_PRODUCTION',
    }
