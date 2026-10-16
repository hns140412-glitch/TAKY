"""Read-only RAW candidate verification; use checked open-handle bytes once.

The handle/hash result is evidence for local candidate formation, not proof of
publisher authority, accuracy, license, sufficiency, or release eligibility.
"""
import hashlib
import os
from pathlib import Path

def _read_checked(base, rel):
    if not isinstance(rel,str) or not rel.strip():
        return None, "EVIDENCE_INCOMPLETE"
    raw=rel.replace("\\","/")
    parts=raw.split("/")
    if raw.startswith("/") or ":" in raw or any(p in ("",".","..") for p in parts):
        return None, "PATH_ESCAPES_ROOT"
    try:
        if os.name=="nt":
            from gongbang_scope_gate_candidate import _read_windows_handle
            data, reason, _ = _read_windows_handle(base, parts)
        elif os.name=="posix":
            from gongbang_scope_gate_candidate import _safe_open_supported, _read_fd_relative
            if not _safe_open_supported():
                return None, "RAW_HANDLE_CHECK_UNSUPPORTED"
            data, reason = _read_fd_relative(base,parts)
        else:
            return None, "RAW_HANDLE_CHECK_UNSUPPORTED"
    except (OSError, ValueError, RuntimeError, TypeError):
        return None, "RAW_UNAVAILABLE"
    return data, reason

def verify_raw_candidates(inventory, *, root, manifest, capture_bytes=False):
    base=Path(root).resolve()
    if not isinstance(manifest,dict) or not isinstance(inventory,list):
        return {"status":"HOLD","reason":"INPUT_INVALID","items":[]}
    findings=[]
    verified_bytes={}
    for requirement in inventory:
        found=[]
        for sid in requirement.get("candidates",[]):
            evidence=manifest.get(sid)
            state="PROVENANCE_MISSING"
            if isinstance(evidence,dict) and evidence.get("source_id")==sid:
                rel=evidence.get("raw_path")
                digest=evidence.get("sha256")
                if isinstance(digest,str) and len(digest)==64:
                    data,reason=_read_checked(base,rel)
                    if reason:
                        state=reason
                    elif not data:
                        state="RAW_FILE_EMPTY"
                    elif hashlib.sha256(data).hexdigest()!=digest.lower():
                        state="RAW_HASH_MISMATCH"
                    else:
                        state="RAW_HASH_MATCH_CANDIDATE"
                        if capture_bytes:
                            verified_bytes[sid]=data
                else:
                    state="EVIDENCE_INCOMPLETE"
            found.append({"source_id":sid,"state":state})
        findings.append({"requirement_id":requirement.get("id"),"raw_candidates":found})
    result={"status":"HOLD","items":findings,"release_approved":False,
            "content_sufficient":False,"evidence_scope":"OPEN_HANDLE_HASH_CANDIDATE_ONLY",
            "note":"RAW hash/handle evidence does not prove source authority or consumer delivery."}
    if capture_bytes:
        result["verified_bytes"]=verified_bytes
    return result
