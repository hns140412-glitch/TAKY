#!/usr/bin/env python3
"""Validate TAKY Design-to-UI Pipeline V1 manifests.

This validates contract/source integrity and reports unresolved production layers
without pretending they are Design PASS. It uses only the Python standard library.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

SCHEMA = "TAKY_DESIGN_TO_UI_PIPELINE_V1"
SCREEN_SCHEMA = "TAKY_SCREEN_CONTRACT_V2"
LAYER_SCHEMA = "TAKY_LAYER_CONTRACT_V1"
SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
LAYER_ROLES = {"BACKGROUND","FOREGROUND","OBJECT","CHARACTER_SLOT","FUNCTION_UI"}
LAYER_STATUSES = {"BOUND","ASSET_PRODUCTION_OPEN","NOT_APPLICABLE"}

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def safe_file(root: Path, rel: str) -> Path | None:
    try:
        p = (root / rel).resolve()
        p.relative_to(root.resolve())
    except (ValueError, TypeError):
        return None
    return p

def read_json_file(root: Path, rel: str, expected_sha: str, errors: list[str], label: str):
    if not rel:
        errors.append(f"{label}:PATH_MISSING")
        return None
    p = safe_file(root, rel)
    if p is None:
        errors.append(f"{label}:PATH_ESCAPES_ROOT")
        return None
    if not p.is_file() or p.stat().st_size == 0:
        errors.append(f"{label}:FILE_MISSING")
        return None
    if not SHA64.match(expected_sha or ""):
        errors.append(f"{label}:SHA_MISSING")
    elif sha256(p).lower() != expected_sha.lower():
        errors.append(f"{label}:SHA_MISMATCH")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        errors.append(f"{label}:JSON_INVALID")
        return None

def validate(cfg: dict, root: Path) -> dict:
    errors: list[str] = []
    blockers: list[str] = []

    if cfg.get("schema") != SCHEMA:
        errors.append("SCHEMA_INVALID")
    if not str(cfg.get("project","")).strip():
        errors.append("PROJECT_MISSING")
    if not SHA40.match(str(cfg.get("source_commit",""))):
        errors.append("SOURCE_COMMIT_INVALID")

    pol = cfg.get("policy", {})
    for key in (
        "runtime_must_not_auto_become_golden",
        "flattened_mockup_runtime_forbidden",
        "evidence_files_required",
        "image_generation_optional",
    ):
        if pol.get(key) is not True:
            errors.append(f"POLICY_{key.upper()}_NOT_HARD")

    screens = cfg.get("screens")
    if not isinstance(screens, list) or not screens:
        errors.append("SCREENS_MISSING")
        return {"contract_valid": False, "design_pass_ready": False, "errors": errors, "blockers": blockers}

    seen_ids: set[str] = set()
    for screen in screens:
        sid = str(screen.get("id","")).strip()
        if not sid or sid in seen_ids:
            errors.append("SCREEN_ID_INVALID_OR_DUPLICATE")
            sid = sid or "<unknown>"
        seen_ids.add(sid)

        if not str(screen.get("authority_ref","")).strip():
            errors.append(f"{sid}:AUTHORITY_REF_MISSING")

        golden = screen.get("golden", {})
        if golden.get("use") != "REFERENCE_ONLY":
            errors.append(f"{sid}:GOLDEN_USE_MUST_BE_REFERENCE_ONLY")
        gstatus = str(golden.get("status",""))
        if gstatus not in ("BOUND","IMPORT_OPEN"):
            errors.append(f"{sid}:GOLDEN_STATUS_INVALID")
        if not str(golden.get("source_receipt","")).strip():
            errors.append(f"{sid}:GOLDEN_SOURCE_RECEIPT_MISSING")
        gpath = str(golden.get("path",""))
        gsha = str(golden.get("sha256",""))
        if not SHA64.match(gsha):
            errors.append(f"{sid}:GOLDEN_SHA_MISSING")
        gp = safe_file(root, gpath) if gpath else None
        if gp is None:
            errors.append(f"{sid}:GOLDEN_PATH_INVALID")
        elif gstatus == "BOUND":
            if not gp.is_file():
                errors.append(f"{sid}:GOLDEN_MISSING")
            elif SHA64.match(gsha) and sha256(gp).lower() != gsha.lower():
                errors.append(f"{sid}:GOLDEN_SHA_MISMATCH")
        elif gstatus == "IMPORT_OPEN":
            blockers.append(f"{sid}:GOLDEN_IMPORT_OPEN")

        sc = screen.get("screen_contract", {})
        scfg = read_json_file(root, str(sc.get("path","")), str(sc.get("sha256","")), errors, f"{sid}:SCREEN_CONTRACT")
        if isinstance(scfg, dict):
            if scfg.get("schema") != SCREEN_SCHEMA:
                errors.append(f"{sid}:SCREEN_CONTRACT_SCHEMA_INVALID")
            if scfg.get("screen_id") != sid:
                errors.append(f"{sid}:SCREEN_CONTRACT_ID_MISMATCH")
            for req in ("regions","typography","components","responsive","interactions","states"):
                if not scfg.get(req):
                    errors.append(f"{sid}:SCREEN_CONTRACT_{req.upper()}_MISSING")

        lc = screen.get("layer_contract", {})
        lcfg = read_json_file(root, str(lc.get("path","")), str(lc.get("sha256","")), errors, f"{sid}:LAYER_CONTRACT")
        if isinstance(lcfg, dict):
            if lcfg.get("schema") != LAYER_SCHEMA:
                errors.append(f"{sid}:LAYER_CONTRACT_SCHEMA_INVALID")
            if lcfg.get("screen_id") != sid:
                errors.append(f"{sid}:LAYER_CONTRACT_ID_MISMATCH")
            layers = lcfg.get("layers")
            if not isinstance(layers, list):
                errors.append(f"{sid}:LAYERS_MISSING")
            else:
                by_role = {}
                for layer in layers:
                    role = layer.get("role")
                    status = layer.get("status")
                    if role not in LAYER_ROLES:
                        errors.append(f"{sid}:LAYER_ROLE_INVALID:{role}")
                        continue
                    if role in by_role:
                        errors.append(f"{sid}:LAYER_ROLE_DUPLICATE:{role}")
                    by_role[role] = layer
                    if status not in LAYER_STATUSES:
                        errors.append(f"{sid}:LAYER_STATUS_INVALID:{role}")
                    if status == "BOUND":
                        path = str(layer.get("path",""))
                        expected = str(layer.get("sha256",""))
                        p = safe_file(root, path) if path else None
                        if p is None or not p.is_file():
                            errors.append(f"{sid}:BOUND_LAYER_MISSING:{role}")
                        elif not SHA64.match(expected):
                            errors.append(f"{sid}:BOUND_LAYER_SHA_MISSING:{role}")
                        elif sha256(p).lower() != expected.lower():
                            errors.append(f"{sid}:BOUND_LAYER_SHA_MISMATCH:{role}")
                    elif status == "ASSET_PRODUCTION_OPEN":
                        blockers.append(f"{sid}:ASSET_PRODUCTION_OPEN:{role}")
                missing_roles = sorted(LAYER_ROLES - set(by_role))
                for role in missing_roles:
                    errors.append(f"{sid}:LAYER_ROLE_UNDECLARED:{role}")

        viewports = screen.get("viewports")
        if not isinstance(viewports, list) or not viewports:
            errors.append(f"{sid}:VIEWPORTS_MISSING")
            viewport_ids = set()
        else:
            viewport_ids = set()
            for v in viewports:
                vid = str(v.get("id","")).strip()
                if not vid or vid in viewport_ids:
                    errors.append(f"{sid}:VIEWPORT_ID_INVALID_OR_DUPLICATE")
                viewport_ids.add(vid)
                if not isinstance(v.get("width"), int) or v["width"] < 240:
                    errors.append(f"{sid}:{vid}:VIEWPORT_WIDTH_INVALID")
                if not isinstance(v.get("height"), int) or v["height"] < 320:
                    errors.append(f"{sid}:{vid}:VIEWPORT_HEIGHT_INVALID")
                if not isinstance(v.get("dpr"), (int,float)) or v["dpr"] <= 0:
                    errors.append(f"{sid}:{vid}:VIEWPORT_DPR_INVALID")

        states = screen.get("states")
        if not isinstance(states, list) or not states:
            errors.append(f"{sid}:STATES_MISSING")
        else:
            state_ids = set()
            for state in states:
                stid = str(state.get("id","")).strip()
                if not stid or stid in state_ids:
                    errors.append(f"{sid}:STATE_ID_INVALID_OR_DUPLICATE")
                state_ids.add(stid)
                fpath = str(state.get("fixture_path",""))
                fsha = str(state.get("fixture_sha256",""))
                fp = safe_file(root, fpath) if fpath else None
                if fp is None or not fp.is_file():
                    errors.append(f"{sid}:{stid}:FIXTURE_MISSING")
                elif not SHA64.match(fsha):
                    errors.append(f"{sid}:{stid}:FIXTURE_SHA_MISSING")
                elif sha256(fp).lower() != fsha.lower():
                    errors.append(f"{sid}:{stid}:FIXTURE_SHA_MISMATCH")

    return {
        "schema": "TAKY_DESIGN_TO_UI_CONTRACT_VALIDATION_V1",
        "contract_valid": not errors,
        "design_pass_ready": (not errors and not blockers),
        "errors": errors,
        "blockers": blockers,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = validate(cfg, args.root)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["contract_valid"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
