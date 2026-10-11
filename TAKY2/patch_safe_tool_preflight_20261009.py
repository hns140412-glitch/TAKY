from pathlib import Path

p=Path(r"D:\Git PWA\TAKY-2.0-ORCH\TAKY2\enforcement.py")
s=p.read_text(encoding="utf-8")
anchor='''def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()[:20]


'''
insert='''def safe_tool_gate(tool_action: Mapping[str, Any] | None) -> GateResult:
    """Deterministic pre-tool safety/route check.

    This is a precheck, not a sixth HARD GATE. Existing non-tool plans may omit
    tool_action. Tool-mediated plans should supply one normalized declaration.
    """
    if tool_action is None:
        return GateResult(True, "SAFE_TOOL_NOT_APPLICABLE", "no tool_action declared")
    if not isinstance(tool_action, Mapping):
        return GateResult(False, "SAFE_TOOL_BLOCKED", "tool_action must be an object")

    detected: list[str] = []
    purpose = str(tool_action.get("purpose") or "").strip()
    purposes = tool_action.get("purposes")
    if purposes is not None:
        if not isinstance(purposes, list) or len([x for x in purposes if str(x or "").strip()]) != 1:
            detected.append("ONE_CALL_ONE_PRIMARY_PURPOSE_REQUIRED")
    elif not purpose:
        detected.append("PRIMARY_PURPOSE_MISSING")

    target = str(tool_action.get("target") or "").strip()
    if not target:
        detected.append("EXACT_TARGET_REQUIRED")

    operation = str(tool_action.get("operation") or "").strip().lower()
    transport = str(tool_action.get("transport") or "").strip().lower()
    command = str(tool_action.get("command") or "")
    connector_available = tool_action.get("connector_available") is True
    drive_id = str(
        tool_action.get("drive_file_id")
        or tool_action.get("drive_folder_id")
        or ""
    ).strip()

    if operation in {"google_drive", "drive", "drive_intake"} and connector_available and drive_id:
        if transport in {"local_scan", "drivefs_reverse_lookup", "shell_drive_search"}:
            detected.append("DRIVE_CONNECTOR_ID_ROUTE_REQUIRED")

    if re.match(r"^[A-Za-z]:\\?$", target) or re.match(r"^[A-Za-z]:\\Users\\?$", target, re.I):
        detected.append("BROAD_ROOT_SCAN_FORBIDDEN")

    combined = "\n".join([target, command])
    auth_patterns = (
        r"\\AppData\\.*\\Google\\DriveFS",
        r"\\AppData\\.*\\Credentials?",
        r"\\\.ssh(?:\\|$)",
        r"credential",
    )
    if tool_action.get("explicit_auth_inspection") is not True:
        if any(re.search(pattern, combined, re.I) for pattern in auth_patterns):
            detected.append("AUTH_ADJACENT_ENUMERATION_REQUIRES_EXPLICIT_NECESSITY")

    if re.search(r"Get-ChildItem\\s+Env:", command, re.I):
        detected.append("BROAD_ENV_ENUMERATION_FORBIDDEN")

    previous = str(tool_action.get("previous_block_signature") or "").strip()
    current = str(tool_action.get("action_signature") or "").strip()
    if previous and current and previous == current:
        detected.append("BLOCKED_ACTION_SIGNATURE_RETRY_FORBIDDEN")

    if tool_action.get("file_io_only") is True and transport == "shell":
        detected.append("FILE_TOOL_REQUIRED_BEFORE_SHELL")

    if detected:
        return GateResult(
            False,
            "SAFE_TOOL_BLOCKED",
            ";".join(detected),
            tuple(detected),
        )
    return GateResult(True, "SAFE_TOOL_OK", "safe tool precheck passed")


'''
assert anchor in s
if "def safe_tool_gate(" not in s:
    s=s.replace(anchor,anchor+insert)
if "import re
" not in s:
    s=s.replace("import json
","import json
import re
")
p.write_text(s,encoding="utf-8")

p=Path(r"D:\Git PWA\TAKY-2.0-ORCH\TAKY2\orchestrator.py")
s=p.read_text(encoding="utf-8")
if "    safe_tool_gate,
" not in s:
    s=s.replace("    route_gate,
","    route_gate,
    safe_tool_gate,
")
old='''    scoped = _scoped_trusted(trusted, execution_scope)
    economy_result = evaluate_savey_ai_economy(
'''
new='''    scoped = _scoped_trusted(trusted, execution_scope)

    # SAFE_TOOL is a deterministic precheck before the five HARD GATE flow.
    # It prevents avoidable unsafe/wasteful tool routes without redefining the
    # canonical KEY/CONTEXT/ROUTE/COST/DONE gate model.
    safe_tool_result = safe_tool_gate(plan.get("tool_action"))
    if not safe_tool_result.allowed:
        guidance = guidance_for_failure("ROUTE", safe_tool_result.state, safe_tool_result.reason)
        return {
            "allowed": False,
            "blocked_by": "SAFE_TOOL",
            "results": [_gate_item("SAFE_TOOL", safe_tool_result)],
            "receipt_id": None,
            "call_allowed": False,
            "mode": guidance["mode"],
            "terminal": False,
            "reason": safe_tool_result.reason,
            "guidance": guidance,
            "orchestration": role_assignment(
                action,
                verification_tier=verification_tier(action),
            ),
            "safe_tool_evaluation": _gate_item("SAFE_TOOL", safe_tool_result),
        }

    economy_result = evaluate_savey_ai_economy(
'''
assert old in s
s=s.replace(old,new)
old2='''    checks = [
        ("KEY", lambda: key_gate(trusted, plan)),
'''
new2='''    checks = [
        ("SAFE_TOOL", lambda: safe_tool_result),
        ("KEY", lambda: key_gate(trusted, plan)),
'''
assert old2 in s
s=s.replace(old2,new2)
p.write_text(s,encoding="utf-8")
print("TAKY2_SAFE_TOOL_PREFLIGHT_PATCHED")
