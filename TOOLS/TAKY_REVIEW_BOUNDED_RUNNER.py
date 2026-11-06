#!/usr/bin/env python3
"""Bound the *existing* TAKY_MODEL_REVIEW.ps1 invocation, without an AI engine.

A model transport can hang after TAKY2's own subprocess times out. Never
retry an uncertain call. On outer timeout, terminate only this invocation's
spawned process tree and return OUTCOME_UNKNOWN, never PASS/FAILED.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time

REVIEW_SCRIPT = Path(r"D:\Git PWA\TAKY\TOOLS\TAKY_MODEL_REVIEW.ps1")
ORCH = Path(r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH")
REPO_ALLOWLIST = {
    r"D:\Git PWA\TAKY",
    r"D:\Git PWA\TAKY\.local\TAKY-2.0-ORCH",
    r"D:\Git PWA\Play Camp",
    r"D:\Git PWA\Ready & Set",
    r"D:\Git PWA\Hide & Seek",
    r"D:\Git PWA\Snap & Pop",
    r"D:\Git PWA\TAKY-MOBILE",
    r"D:\Git PWA\SAVEY",
}
TIMEOUT_SEC = 225
OUTPUT_LIMIT = 24000
MAX_CHILD_MEMORY_MB = 500
MAX_SUSTAINED_CPU_SECONDS = 35


def _windows_process_resources(pid: int) -> tuple[int, float] | None:
    """Use Windows APIs (no pip installs) to observe direct child memory/CPU."""
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    class Memory(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE,
                                      ctypes.POINTER(wintypes.FILETIME),
                                      ctypes.POINTER(wintypes.FILETIME),
                                      ctypes.POINTER(wintypes.FILETIME),
                                      ctypes.POINTER(wintypes.FILETIME)]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return None
    try:
        memory = Memory()
        memory.cb = ctypes.sizeof(memory)
        created, exited, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
            return None
        if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                      ctypes.byref(kernel_time), ctypes.byref(user_time)):
            return None
        def seconds(ft):
            return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 10_000_000
        return memory.WorkingSetSize, seconds(kernel_time) + seconds(user_time)
    finally:
        kernel.CloseHandle(handle)


def run_bounded(argv: list[str], *, timeout: float, cwd: Path | None = None,
                env: dict[str, str] | None = None, capture_receipt: bool = False) -> dict:
    """Execute one explicit subprocess; never automatically retry.

    Tests call this helper only with deterministic local commands.
    """
    if not argv or not isinstance(timeout, (int, float)) or not 0 < timeout <= 240:
        raise ValueError("INVALID_BOUNDED_RUN")
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="TAKY_BOUNDED_RUN_") as folder:
        stdout_path = Path(folder) / "stdout.txt"
        stderr_path = Path(folder) / "stderr.txt"
        bridge_receipt_path = Path(folder) / "governed-receipt.json"
        actual_argv = [*argv, "-ReceiptOut", str(bridge_receipt_path)] if capture_receipt else argv
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            kwargs = {"cwd": str(cwd) if cwd else None, "env": env,
                      "stdin": subprocess.DEVNULL, "stdout": stdout,
                      "stderr": stderr, "shell": False}
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(actual_argv, **kwargs)
            timed_out = False
            resource_violation = None
            peak_child_memory_mb = 0.0
            try:
                while process.poll() is None:
                    age = time.monotonic() - start
                    if age > timeout:
                        timed_out = True
                        break
                    try:
                        metric = _windows_process_resources(process.pid)
                    except (OSError, ValueError, AttributeError):
                        metric = None
                    if metric is not None:
                        working_set, cpu_seconds = metric
                        peak_child_memory_mb = max(peak_child_memory_mb, working_set / 1048576)
                        if working_set > MAX_CHILD_MEMORY_MB * 1048576:
                            resource_violation = "CHILD_MEMORY_LIMIT"
                            break
                        if age > MAX_SUSTAINED_CPU_SECONDS + 5 and (
                            cpu_seconds >= MAX_SUSTAINED_CPU_SECONDS
                            and cpu_seconds / max(age, 1) >= 0.75
                        ):
                            resource_violation = "CHILD_SUSTAINED_CPU_LIMIT"
                            break
                    try:
                        process.wait(timeout=min(1.0, max(0.1, timeout - age)))
                    except subprocess.TimeoutExpired:
                        pass
            finally:
                if process.poll() is None:
                    if os.name == "nt":
                        # Kill only this invocation's tree, never other CLI/IDE sessions.
                        try:
                            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                                           check=False, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
                        except (OSError, subprocess.TimeoutExpired):
                            pass
                    if process.poll() is None:
                        process.kill()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        pass
        out = stdout_path.read_bytes()[:OUTPUT_LIMIT].decode("utf-8", errors="replace")
        err = stderr_path.read_bytes()[:OUTPUT_LIMIT].decode("utf-8", errors="replace")
        bridge_receipt = None
        if capture_receipt and bridge_receipt_path.is_file() and bridge_receipt_path.stat().st_size <= 8192:
            try:
                marker = json.loads(bridge_receipt_path.read_text(encoding="utf-8-sig"))
                if (isinstance(marker, dict) and
                    re.fullmatch(r"[0-9a-f]{32}", str(marker.get("task_id", ""))) and
                    re.fullmatch(r"pf:[A-Za-z0-9:_-]{8,150}", str(marker.get("receipt_id", "")))):
                    bridge_receipt = {k: marker.get(k) for k in
                                      ("task_id", "receipt_id", "provider", "executor_state")}
                    raw_manifest = marker.get("source_manifest")
                    digest = marker.get("packet_digest")
                    if (isinstance(raw_manifest, list) and len(raw_manifest) <= 8 and
                            re.fullmatch(r"[0-9a-f]{20}", str(digest or ""))):
                        valid = []
                        for source in raw_manifest:
                            if not isinstance(source, dict):
                                break
                            name = source.get("path")
                            sha = source.get("sha256")
                            included = source.get("includedLines")
                            total = source.get("totalLines")
                            if (not isinstance(name, str) or len(name) > 190 or
                                    not re.fullmatch(r"[A-Za-z0-9_./-]+", name) or
                                    not re.fullmatch(r"[0-9a-f]{64}", str(sha or "")) or
                                    type(included) is not int or type(total) is not int or
                                    not 0 <= included <= total <= 100000):
                                break
                            valid.append({"path": name, "sha256": sha,
                                          "includedLines": included, "totalLines": total})
                        else:
                            bridge_receipt["packet_digest"] = digest
                            bridge_receipt["source_manifest"] = valid
                            skill_entries = marker.get("skill_manifest")
                            if isinstance(skill_entries, list) and 2 <= len(skill_entries) <= 4:
                                checked = []
                                for item in skill_entries:
                                    if (not isinstance(item, dict) or set(item) != {"name", "sha256"}
                                            or not isinstance(item["name"], str)
                                            or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", item["name"])
                                            or not isinstance(item["sha256"], str)
                                            or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"])):
                                        break
                                    checked.append({"name": item["name"],
                                                    "sha256": item["sha256"]})
                                else:
                                    if len({row["name"] for row in checked}) == len(checked):
                                        bridge_receipt["skill_manifest"] = checked
                            # Keep the original governed call manifest for
                            # later comparison with the signed TAKY2 call_digest.
                            # This is evidence of claimed input only, NOT authorization.
                            candidate_call = marker.get("call_manifest")
                            if (isinstance(candidate_call, dict)
                                    and candidate_call.get("packet_digest") == digest
                                    and candidate_call.get("source_manifest") == raw_manifest
                                    and candidate_call.get("skill_manifest") == skill_entries
                                    and len(json.dumps(candidate_call)) <= 6000):
                                bridge_receipt["call_manifest"] = candidate_call
            except (OSError, ValueError, UnicodeError):
                pass
        return {
            "governedReceipt": bridge_receipt,
            "status": "OUTCOME_UNKNOWN_RESOURCE_LIMIT" if resource_violation else (
                "OUTCOME_UNKNOWN_TIMEOUT" if timed_out else (
                    "RETURNED_UNVERIFIED" if process.returncode == 0 else "FAILED_OR_BLOCKED")),
            "returncode": None if (timed_out or resource_violation) else process.returncode,
            "timeout": timed_out,
            "resourceLimitBreach": resource_violation,
            "peakChildMemoryMb": round(peak_child_memory_mb, 1),
            "modelCallConfirmed": False,
            "elapsedSeconds": round(time.monotonic() - start, 1),
            "stdout": out,
            "stderr": err,
            "outputTruncated": stdout_path.stat().st_size > OUTPUT_LIMIT or
                               stderr_path.stat().st_size > OUTPUT_LIMIT,
        }


def release_if_proven_preinvoke(outcome: dict, signed: dict) -> dict:
    """One guarded local state transition after a terminated wrapper; no retry.

    The wrapper has already exited (or its process tree was terminated) and
    TAKY2's signed ledger shows a preflight but *no execution claim*. An
    uncertain CALLING/CLAIMED execution is not eligible for this recovery.
    """
    marker = outcome.get("governedReceipt")
    if not isinstance(marker, dict) or not isinstance(signed, dict):
        return {"state": "NO_PROVEN_PREINVOKE"}
    rid = marker.get("receipt_id")
    ident = outcome.get("task_id")
    if (not isinstance(rid, str) or
            not re.fullmatch(r"pf:external-review-[a-f0-9]{32}:[a-f0-9]{16,32}", rid) or
            not isinstance(ident, str) or
            not rid.startswith("pf:external-review-" + ident + ":") or
            signed.get("state") != "PREFLIGHT_ONLY" or
            signed.get("receiptId") != rid or
            signed.get("preflightAllowed") is not True):
        return {"state": "HOLD_UNPROVEN_OR_MISMATCHED_RECEIPT"}
    terminal = outcome.get("status")
    if terminal not in ("OUTCOME_UNKNOWN_RESOURCE_LIMIT",
                        "OUTCOME_UNKNOWN_TIMEOUT", "FAILED_OR_BLOCKED",
                        "RETURNED_UNVERIFIED"):
        return {"state": "HOLD_WRAPPER_NOT_SETTLED"}
    reason = ("LOCAL_RESOURCE_GUARD_BEFORE_CLAIM"
              if terminal == "OUTCOME_UNKNOWN_RESOURCE_LIMIT" else
              "WRAPPER_INTERRUPTED_BEFORE_CLAIM")
    args = [sys.executable, "-m", "TAKY2.orchestrator",
            "release-uninvoked", rid, reason]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ORCH)
    for secret in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env.pop(secret, None)
    try:
        completed = subprocess.run(
            args, cwd=str(ORCH), env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=False, timeout=10,
        )
        # Fail closed. Never accept a bare process return code as state proof.
        payload = json.loads(completed.stdout[:2400].decode("utf-8-sig"))
        if (completed.returncode == 0 and isinstance(payload, dict)
                and payload.get("allowed") is True
                and payload.get("state") == "PREINVOKE_RELEASED"
                and payload.get("receipt_id") == rid
                and payload.get("model_call_registered") is False
                and payload.get("route_failure_recorded") is False):
            return {"state": "PREINVOKE_RELEASED", "receiptId": rid,
                    "reason": reason}
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        pass
    return {"state": "RELEASE_NOT_CONFIRMED_NO_RETRY"}


def execute_request(request: dict) -> dict:
    if not isinstance(request, dict):
        raise ValueError("INVALID_RUNNER_REQUEST")
    provider, repo, prompt = request.get("provider"), request.get("repo"), request.get("prompt")
    if provider not in ("codex", "claude"):
        raise ValueError("UNSUPPORTED_PROVIDER")
    if repo not in REPO_ALLOWLIST or not Path(repo).is_dir():
        raise ValueError("UNAPPROVED_REPOSITORY")
    if not isinstance(prompt, str) or not 0 < len(prompt) <= 2500:
        raise ValueError("INVALID_PROMPT")
    task_id = request.get("task_id")
    if not isinstance(task_id, str) or re.fullmatch(r"[0-9a-f]{32}", task_id) is None:
        raise ValueError("TASK_ID_REQUIRED_FOR_CORRELATION")
    if not REVIEW_SCRIPT.is_file():
        raise ValueError("GOVERNED_REVIEW_SCRIPT_MISSING")
    if os.environ.get("TAKY_USER_EXPLICIT_AUTHORIZATION") != "1":
        raise ValueError("MODEL_AUTHORIZATION_REQUIRED")
    timeout_seconds = request.get("timeoutSeconds", TIMEOUT_SEC)
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 45 <= timeout_seconds <= TIMEOUT_SEC):
        raise ValueError("INVALID_REVIEW_TIME_BUDGET")
    output_mode = request.get("outputMode", "Envelope")
    if output_mode not in ("Envelope", "Raw"):
        raise ValueError("UNSUPPORTED_OUTPUT_MODE")
    from TAKY_TRUSTED_SHELL import resolve_trusted_shell
    review_shell = resolve_trusted_shell()
    child = [
        review_shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
        "Bypass", "-File", str(REVIEW_SCRIPT), "-Provider", provider,
        "-Prompt", prompt, "-TaskId", task_id, "-Repo", repo, "-ClaudeMaxTurns", "1",
        "-OutputMode", output_mode,
    ]
    # Council evidence is opt-in. Bind the stage/source/target inside the
    # existing signed TAKY2 call; this supervisor never bypasses that gate.
    council_binding = request.get("councilBinding")
    if council_binding is not None:
        if not isinstance(council_binding, dict):
            raise ValueError("COUNCIL_BINDING_INVALID")
        import re as _re
        required = {"schema", "work_id", "stage", "source_sha256", "target_sha256"}
        if (set(council_binding) != required
                or council_binding["schema"] != "TAKY_COUNCIL_BINDING_V1"
                or not isinstance(council_binding["work_id"], str)
                or not council_binding["work_id"].strip()
                or not isinstance(council_binding["stage"], str)
                or _re.fullmatch(r"(?:ADVISOR_|PEER_)(?:CONTRARIAN|FIRST_PRINCIPLES|EXPANSIONIST|OUTSIDER|EXECUTOR)|CHAIR",
                                  council_binding["stage"]) is None
                or not isinstance(council_binding["source_sha256"], str)
                or _re.fullmatch(r"[a-f0-9]{64}", council_binding["source_sha256"]) is None
                or (council_binding["target_sha256"] is not None
                    and (not isinstance(council_binding["target_sha256"], str)
                         or _re.fullmatch(r"[a-f0-9]{20,64}", council_binding["target_sha256"]) is None))):
            raise ValueError("COUNCIL_BINDING_INVALID")
        child.extend(["-CouncilBindingJson", json.dumps(council_binding, separators=(",", ":"))])
    scoped_digest = request.get("scopedEditTaskSha256")
    if scoped_digest is not None:
        if (output_mode != "Raw" or not isinstance(scoped_digest, str)
                or re.fullmatch(r"[a-f0-9]{64}", scoped_digest) is None):
            raise ValueError("SCOPED_EDIT_CALL_BINDING_INVALID")
        child.extend(["-ScopedEditTaskSha256", scoped_digest])
    target_receipt = request.get("targetReceiptId")
    if target_receipt is not None:
        if (not isinstance(target_receipt, str) or
                re.fullmatch(r"pf:[A-Za-z0-9:_-]{8,150}", target_receipt) is None
                or output_mode != "Envelope"):
            raise ValueError("TARGET_REVIEW_RECEIPT_INVALID")
        child.extend(["-TargetReceiptId", target_receipt])
    env = dict(os.environ)
    for secret in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env.pop(secret, None)
    outcome = run_bounded(child, timeout=timeout_seconds, cwd=Path(repo), env=env, capture_receipt=True)
    outcome["task_id"] = task_id
    outcome["shellRuntime"] = "POWERSHELL_7" if Path(review_shell).name.lower() == "pwsh.exe" else "WINDOWS_POWERSHELL"
    # Independently verify TAKY2 signed runtime. This reads a local integrity-
    # checked ledger and cannot trigger a retry or an inference call.
    from TAKY_SIGNED_EXECUTION_READBACK import read_signed
    marker = outcome.get("governedReceipt")
    bound_receipt = marker.get("receipt_id") if isinstance(marker, dict) else None
    claimed_input = marker.get("call_manifest") if isinstance(marker, dict) else None
    outcome["signedReadback"] = read_signed(task_id, bound_receipt, claimed_input)
    outcome["preinvokeRelease"] = release_if_proven_preinvoke(outcome, outcome["signedReadback"])
    if outcome["preinvokeRelease"]["state"] == "PREINVOKE_RELEASED":
        outcome["signedReadback"] = read_signed(task_id, bound_receipt, claimed_input)
    return outcome


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    path = args.request.resolve(strict=True)
    if path.stat().st_size > 9000:
        raise SystemExit("RUN_REQUEST_OVERSIZE")
    request = json.loads(path.read_text(encoding="utf-8-sig"))
    # Always a machine-readable response if the child started and returned.
    print(json.dumps(execute_request(request), ensure_ascii=False))


if __name__ == "__main__":
    main()
