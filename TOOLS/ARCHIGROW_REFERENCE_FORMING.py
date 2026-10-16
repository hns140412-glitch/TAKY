#!/usr/bin/env python3
"""TAKY Archi Grow read-only original-evidence FORMING consumer.

Uses real SOURCE-VAULT SHA-bound candidate (ZIP / PDF member / page / quote).
Produces domain-question FRONTIER candidates and an explicit project-data HOLD.
No CURRENT, LEARNING, app or SOURCE-VAULT writes and no external calls.
This is not an automated legal/regulatory compliance decision.
"""
from __future__ import annotations
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

MAX_ARCHIVE_BYTES = 160 * 1024 * 1024
MAX_PDF_BYTES = 8 * 1024 * 1024
MAX_CITATIONS = 12
_SHA64 = re.compile(r"^[a-f0-9]{64}$")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(2 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError("FORMING_EXPECTED_JSON_OBJECT")
    return obj


def within(path: Path, directory: Path) -> bool:
    return path.resolve().is_relative_to(directory.resolve())


def checked_digest(value: str, label: str) -> None:
    if not isinstance(value, str) or not _SHA64.fullmatch(value):
        raise ValueError("FORMING_INVALID_HASH_" + label)


def build(evidence_manifest: str | Path, collector_candidate_pointer: str | Path, project_id: str) -> dict:
    from pypdf import PdfReader

    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("FORMING_PROJECT_ID_REQUIRED")
    evidence_path = Path(evidence_manifest).resolve()
    pointer_path = Path(collector_candidate_pointer).resolve()
    root = pointer_path.parent.parent.parent
    if pointer_path != (root / "data" / "pipeline_bridge" / "COLLECTOR_CANDIDATE_CURRENT.json").resolve():
        raise ValueError("FORMING_COLLECTOR_POINTER_NOT_ACTIVE_PATH")
    base = (root / "reports" / "generations").resolve()
    manifest = read_json(evidence_path)
    pointer = read_json(pointer_path)
    recovery_path = (root / "data" / "pipeline_bridge" / "COLLECTOR_SEARCH_RECOVERY_CURRENT.json").resolve()
    recovery = read_json(recovery_path)
    if (
        manifest.get("schema") != "TAKY_ARCHIGROW_ACTUAL_COLLECTOR_RAW_ZIP_MEMBER_CITED_CHECKLIST_V1"
        or manifest.get("source_reference_type") != "PRIVATE_ARCHIVED_THIRD_PARTY_CHECKLIST_NOT_LEGAL_AUTHORITY"
        or manifest.get("CURRENT_promotion") is not False
        or manifest.get("LEARNING_or_app_applied") is not False
        or manifest.get("auto_approved_condition_count") != 0
        or manifest.get("actual_project_drawings_uploaded") is not False
        or manifest.get("reviewer_decision_recorded") is not False
        or manifest.get("project_id") != "UNASSIGNED_NO_LIVE_PROJECT_INPUT"
    ):
        raise ValueError("FORMING_NONAUTHORITATIVE_SOURCE_GATE")
    if (
        pointer.get("batch_key") != recovery.get("batch_key")
        or manifest.get("source_batch") != pointer.get("batch_key")
        or pointer.get("do_not_publish") is not True
        or recovery.get("do_not_publish") is not True
        or recovery.get("recovered_count") != 0
        or recovery.get("learning_integrated") != 0
        or recovery.get("content_published") != 0
    ):
        raise ValueError("FORMING_SOURCE_BATCH_OR_AUTHORITY_DRIFT")
    recorded = manifest.get("source_vault_pointer_hashes_unchanged")
    if not isinstance(recorded, dict) or recorded.get(str(pointer_path)) != digest(pointer_path) or recorded.get(str(recovery_path)) != digest(recovery_path):
        raise ValueError("FORMING_SOURCE_POINTER_SHA_DRIFT")
    index_path = Path(pointer["index_path"]).resolve()
    if not within(index_path, base) or not index_path.is_file():
        raise ValueError("FORMING_INDEX_CANDIDATE_PATH_CHANGED")
    index = read_json(index_path)
    # SOURCE-VAULT pointer hashes canonical JSON, not prettified on-disk bytes.
    canonical = hashlib.sha256(json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if canonical != pointer["index_sha256"]:
        raise ValueError("FORMING_INDEX_CANDIDATE_SOURCE_CHANGED")
    if index.get("authority_promoted") is not False or index.get("source_count") != pointer.get("source_count"):
        raise ValueError("FORMING_INDEX_AUTHORITY_INVALID")
    source_id = manifest.get("original_source_id")
    records = [rec for rec in index.get("records", []) if rec.get("source_id") == source_id]
    if len(records) != 1:
        raise ValueError("FORMING_SOURCE_ID_NOT_IN_ACTIVE_INDEX")
    record = records[0]
    archive = Path(record["raw_path"]).resolve()
    if (
        not archive.is_file()
        or archive.stat().st_size > MAX_ARCHIVE_BYTES
        or archive.suffix.casefold() != ".zip"
        or record.get("index_authoritative") is not False
        or record.get("forming_authorized") is not False
    ):
        raise ValueError("FORMING_ORIGINAL_SOURCE_NOT_ALLOWED")
    archive_hash = digest(archive)
    checked_digest(archive_hash, "ARCHIVE")
    if archive_hash != record["raw_sha256"] or archive_hash != manifest["archive_original_sha256"]:
        raise ValueError("FORMING_ORIGINAL_ARCHIVE_SHA_MISMATCH")
    captions = manifest.get("source_citations")
    if not isinstance(captions, list) or not 1 <= len(captions) <= MAX_CITATIONS:
        raise ValueError("FORMING_SOURCE_QUOTE_COUNT_INVALID")
    if manifest.get("exact_citation_count") != len(captions):
        raise ValueError("FORMING_MANIFEST_QUOTE_COUNT_MISMATCH")
    member_name = manifest.get("origin_reference_name")
    if not isinstance(member_name, str) or not member_name.lower().endswith(".pdf") or member_name.startswith("/") or ".." in member_name.replace("\\", "/").split("/"):
        raise ValueError("FORMING_ARCHIVE_MEMBER_PATH_UNSAFE")
    with zipfile.ZipFile(archive) as z:
        info = z.getinfo(member_name)
        if (
            info.is_dir()
            or info.flag_bits & 1
            or info.file_size <= 0
            or info.file_size > MAX_PDF_BYTES
            or info.file_size / max(1, info.compress_size) > 100
        ):
            raise ValueError("FORMING_ARCHIVE_MEMBER_RESOURCE_OR_ENCRYPTION")
        with z.open(info) as stream:
            raw = stream.read(MAX_PDF_BYTES + 1)
    if len(raw) != info.file_size:
        raise ValueError("FORMING_ARCHIVE_MEMBER_INCOMPLETE")
    member_hash = hashlib.sha256(raw).hexdigest()
    if member_hash != manifest.get("pdf_member_sha256"):
        raise ValueError("FORMING_ARCHIVE_MEMBER_SHA_DRIFT")
    pdf = PdfReader(io.BytesIO(raw), strict=False)
    cache = {}
    candidates = []
    seen = set()
    for citation in captions:
        if not isinstance(citation, dict):
            raise ValueError("FORMING_MALFORMED_CITATION")
        page_num = citation.get("source_page_number")
        phrase = citation.get("source_quote")
        if not isinstance(page_num, int) or isinstance(page_num, bool) or not 1 <= page_num <= len(pdf.pages):
            raise ValueError("FORMING_CITATION_PAGE_OUT_OF_RANGE")
        if not isinstance(phrase, str) or not 5 <= len(phrase) <= 350:
            raise ValueError("FORMING_CITATION_MISSING_OR_LONG")
        if page_num not in cache:
            cache[page_num] = pdf.pages[page_num - 1].extract_text() or ""
        page_text = cache[page_num]
        if (
            phrase not in page_text
            or page_text.find(phrase) != citation.get("quote_exact_in_original_pdf_offset")
            or hashlib.sha256(page_text.encode("utf-8")).hexdigest() != citation.get("source_page_full_extracted_SHA256")
            or hashlib.sha256(phrase.encode("utf-8")).hexdigest() != citation.get("quote_SHA256")
            or citation.get("source_RAW_archive_SHA256") != archive_hash
            or citation.get("source_PDF_member_SHA256") != member_hash
            or citation.get("source_archive_member_path") != member_name
            or citation.get("source_original_index_id") != source_id
            or citation.get("provisional_action") != "HOLD_NO_PROJECT_INPUT"
            or citation.get("site_compliance_approved") is not False
            or citation.get("quote_proves_reference_text_only") is not True
            or citation.get("source_is_independent_official_law") is not False
        ):
            raise ValueError("FORMING_SOURCE_CITATION_NOT_GROUNDED")
        task_id = citation.get("rule_id")
        question = citation.get("review_question_candidate")
        needs = citation.get("needed_real_project_documents")
        if (
            not isinstance(task_id, str)
            or not re.fullmatch(r"[A-Z][A-Z0-9_]{3,80}", task_id)
            or task_id in seen
            or not isinstance(question, str)
            or not 10 <= len(question) <= 300
            or not isinstance(needs, str)
            or not needs.strip()
        ):
            raise ValueError("FORMING_INVALID_OR_DUPLICATE_QUESTION")
        seen.add(task_id)
        candidates.append({
            "id": task_id,
            "type": "FRONTIER",
            "origin_stage": "SHA_VERIFIED_RAW_REFERENCE",
            "reference_quote": phrase,
            "reference_page": page_num,
            "reference_quote_sha256": citation["quote_SHA256"],
            "source_raw_sha256": archive_hash,
            "source_pdf_member_sha256": member_hash,
            "source_id": source_id,
            "review_question": question,
            "project_specific_documents_required": needs,
            "status": "HOLD_NO_PROJECT_SOURCE",
            "legal_or_project_conclusion": "NOT_EVALUATED",
            "strategy_candidate_not_approved": True,
        })
    return {
        "schema": "TAKY_ARCHIGROW_REFERENCE_FORMING_RECEIPT_V1",
        "project_id": project_id,
        "status": "HOLD",
        "failure_class": "PROJECT_SOURCE_NOT_PROVIDED",
        "source_stage": "SOURCE_VAULT_RAW_SHA_VERIFIED",
        "mining_stage": "EXTRACTIVE_QUOTE_VERIFIED_ONLY_NOT_FULL_SEMANTIC_MINING",
        "index_stage": "CANDIDATE_NONAUTHORITATIVE",
        "forming_stage": "FRONTIER_QUESTIONS_PENDING_PROJECT_EVIDENCE",
        "learning_stage": "NOT_APPLIED",
        "domain_consumer": "ARCHIGROW_PIPELINE_RUN.REFERENCE_FORMING",
        "source_batch_key": pointer["batch_key"],
        "raw_archive_sha256": archive_hash,
        "evidence_manifest_sha256": digest(evidence_path),
        "candidate_question_count": len(candidates),
        "candidates": candidates,
        "missing_project_evidence": True,
        "reviewer_approval_required": True,
        "reference_only_no_official_law": True,
        "actual_project_compliance_approved": 0,
        "source_vault_writes": 0,
        "CURRENT_promotion": False,
        "LEARNING_promotion": False,
        "app_rule_applied": False,
        "model_calls": 0,
        "paid_api_calls": 0,
        "network_calls": 0,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--evidence-manifest", required=True)
    p.add_argument("--collector-candidate-pointer", required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    output = build(a.evidence_manifest, a.collector_candidate_pointer, a.project_id)
    target = Path(a.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "candidates": len(output["candidates"]),
                      "stage": output["forming_stage"]}, ensure_ascii=False))
