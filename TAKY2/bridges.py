from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import os
import secrets
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Mapping

from .enforcement import (
    ACCOUNT_AUTH_SOURCE,
    ACCOUNT_IDENTITY_PROVIDER,
    VALID_EVIDENCE_TYPES,
    canonical_startup_readback_sources,
    record_failure,
    required_verifications_for_tier,
    stable_hash,
    startup_readback_receipt_id,
)


class BridgeViolation(RuntimeError):
    pass


EXECUTION_EVIDENCE_TYPES = {
    "tool_output", "artifact", "diff", "runtime_test", "state_snapshot",
}


def _empty_ledger() -> dict[str, Any]:
    return {
        "route_budget": 3,
        "seen_routes": [],
        "failed_signatures": [],
        "transient_failures": {},
        "last_failure_by_route": {},
    }


def _receipt(runtime: Mapping[str, Any], receipt_id: str) -> Mapping[str, Any]:
    receipt = runtime.get("preflight_receipts", {}).get(receipt_id)
    if not isinstance(receipt, Mapping) or receipt.get("allowed") is not True:
        raise BridgeViolation("valid preflight receipt required")
    if receipt.get("consumed"):
        raise BridgeViolation("preflight receipt already consumed")
    return receipt


def _active_attempt(runtime: Mapping[str, Any], receipt: Mapping[str, Any]) -> Mapping[str, Any]:
    execution_key = receipt.get("execution_key")
    active = runtime.get("active_attempts", {}).get(execution_key)
    if not isinstance(active, Mapping) or active.get("receipt_id") != receipt.get("receipt_id", active.get("receipt_id")):
        # Persisted receipts do not duplicate receipt_id inside the receipt body in older states.
        if not isinstance(active, Mapping):
            raise BridgeViolation("receipt has no active attempt")
    return active


def bind_account_attestation(
    runtime: Mapping[str, Any],
    authority: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    if not callable(verifier):
        raise BridgeViolation("account evidence verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("verifier_id required")
    verifier_name = verifier_id.strip()
    if verifier(evidence) is not True:
        raise BridgeViolation("account evidence verification failed")

    target = authority.get("key", {}).get("AUTHORIZED_TARGET", {})
    expected_account = target.get("value") if isinstance(target, Mapping) else None
    account = evidence.get("account")
    source = evidence.get("source")
    evidence_ref = evidence.get("evidence_ref")
    session_id = evidence.get("session_id")
    identity_provider = evidence.get("identity_provider")
    principal_id = evidence.get("principal_id")
    family_id = evidence.get("family_id")
    self_member_id = evidence.get("self_member_id")

    required = (
        expected_account,
        account,
        source,
        evidence_ref,
        session_id,
        identity_provider,
        principal_id,
        family_id,
        self_member_id,
    )
    if not all(isinstance(v, str) and v.strip() for v in required):
        raise BridgeViolation("authenticated account identity evidence is incomplete")

    expected_account = expected_account.strip()
    account = account.strip()
    source = source.strip()
    evidence_ref = evidence_ref.strip()
    session_id = session_id.strip()
    identity_provider = identity_provider.strip()
    principal_id = principal_id.strip()
    family_id = family_id.strip()
    self_member_id = self_member_id.strip()

    if account != expected_account:
        raise BridgeViolation("authenticated account does not match authorized target")
    if evidence.get("authenticated") is not True:
        raise BridgeViolation("authenticated session evidence required")
    if source != ACCOUNT_AUTH_SOURCE:
        raise BridgeViolation("account attestation source is not the trusted central family session")
    if identity_provider != ACCOUNT_IDENTITY_PROVIDER:
        raise BridgeViolation("account identity provider is not trusted")
    verifier_token = verifier_name.casefold()
    if verifier_token in {
        account.casefold(),
        principal_id.casefold(),
        self_member_id.casefold(),
    }:
        raise BridgeViolation("authenticated account principal/member cannot self-verify")

    updated = deepcopy(dict(runtime))
    runtime_section = updated.setdefault("runtime", {})
    existing = runtime_section.get("account_attestation")
    stable_identity = {
        "account": account,
        "identity_provider": identity_provider,
        "principal_id": principal_id,
        "family_id": family_id,
        "self_member_id": self_member_id,
    }

    if existing is None:
        first_bound_evidence_ref = evidence_ref
        first_bound_session_id = session_id
    else:
        if not isinstance(existing, Mapping):
            raise BridgeViolation("existing account attestation is malformed")
        required_existing = (
            existing.get("account"),
            existing.get("identity_provider"),
            existing.get("principal_id"),
            existing.get("family_id"),
            existing.get("self_member_id"),
            existing.get("source"),
            existing.get("verified_by"),
            existing.get("first_bound_evidence_ref"),
            existing.get("first_bound_session_id"),
        )
        if existing.get("verified") is not True:
            raise BridgeViolation("existing account attestation is not verified")
        if existing.get("binding_mode") != "FIRST_AUTH_RUNTIME":
            raise BridgeViolation("existing account attestation requires explicit migration")
        if not all(isinstance(v, str) and v.strip() for v in required_existing):
            raise BridgeViolation("existing runtime identity binding is incomplete")
        if existing.get("account") != account:
            raise BridgeViolation("authorized target is already bound to another account")

        existing_identity = {
            key: existing.get(key)
            for key in ("account", "identity_provider", "principal_id", "family_id", "self_member_id")
        }
        if existing_identity != stable_identity:
            raise BridgeViolation("authenticated identity changed for bound target")
        if existing.get("source") != source or existing.get("verified_by") != verifier_name:
            raise BridgeViolation("account attestation source/verifier changed; explicit migration required")
        first_bound_evidence_ref = existing["first_bound_evidence_ref"]
        first_bound_session_id = existing["first_bound_session_id"]
    runtime_section["account_attestation"] = {
        **stable_identity,
        "verified": True,
        "binding_mode": "FIRST_AUTH_RUNTIME",
        "source": source,
        "evidence_ref": evidence_ref,
        "session_id": session_id,
        "first_bound_evidence_ref": first_bound_evidence_ref,
        "first_bound_session_id": first_bound_session_id,
        "verified_by": verifier_name,
    }
    return updated


def _argv_identity(invocation: Mapping[str, Any]) -> str:
    argv = invocation.get("argv")
    if not isinstance(argv, list) or not argv or not isinstance(argv[0], str):
        return ""
    return Path(argv[0]).stem.strip().lower()


def _argv_option_value(argv: list[str], *names: str) -> str | None:
    for index, arg in enumerate(argv):
        if arg in names:
            if index + 1 >= len(argv):
                return None
            value = argv[index + 1]
            return value if isinstance(value, str) else None
        for name in names:
            prefix = name + "="
            if arg.startswith(prefix):
                return arg[len(prefix):]
    return None


RISKY_EXTERNAL_ENV_EXACT = {
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CONFIG_DIR",
    "NODE_OPTIONS",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
}
RISKY_EXTERNAL_ENV_PREFIXES = (
    "ANTHROPIC_",
    "OPENAI_",
    "GEMINI_",
    "GOOGLE_",
    "AWS_",
    "BEDROCK_",
    "VERTEX_",
    "CLAUDE_CODE_USE_",
)
PACKET_ENV_ALLOWLIST = {
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "HOMEDRIVE",
    "HOMEPATH",
    "USERNAME",
    "USERDOMAIN",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMW6432",
    "PROCESSOR_ARCHITECTURE",
    "PATHEXT",
}


def _is_risky_external_env_name(name: str) -> bool:
    upper = str(name or "").strip().upper()
    return (
        upper in RISKY_EXTERNAL_ENV_EXACT
        or any(upper.startswith(prefix) for prefix in RISKY_EXTERNAL_ENV_PREFIXES)
    )


def _scrubbed_external_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not _is_risky_external_env_name(key)
    }


def _minimal_packet_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if (
            key.upper() in PACKET_ENV_ALLOWLIST
            and not _is_risky_external_env_name(key)
        )
    }
    system_root = next(
        (
            value
            for key, value in os.environ.items()
            if key.upper() in {"SYSTEMROOT", "WINDIR"} and value
        ),
        r"C:\Windows",
    )
    env["PATH"] = os.pathsep.join([
        str(Path(system_root) / "System32"),
        str(Path(system_root)),
    ])
    return env


def _minimal_codex_env() -> dict[str, str]:
    env = _minimal_packet_env()
    program_files = next(
        (
            value
            for key, value in os.environ.items()
            if key.upper() == "PROGRAMFILES" and value
        ),
        r"C:\Program Files",
    )
    node_dir = Path(program_files) / "nodejs"
    env["PATH"] = os.pathsep.join([str(node_dir), env["PATH"]])
    return env


NONINTERACTIVE_TIMEOUT_SEC = 180.0
NONINTERACTIVE_TIMEOUT_MAX_SEC = 300.0


def subprocess_runner(invocation: Mapping[str, Any]) -> dict[str, Any]:
    argv = invocation.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not isinstance(argv[0], str)
        or not argv[0]
        or not all(isinstance(x, str) for x in argv)
    ):
        raise BridgeViolation("argv must be a string list with a non-empty executable")

    stdin_text = invocation.get("stdin_text")
    if stdin_text is not None and not isinstance(stdin_text, str):
        raise BridgeViolation("stdin_text must be a string when provided")

    timeout_raw = invocation.get("timeout_sec", NONINTERACTIVE_TIMEOUT_SEC)
    if not isinstance(timeout_raw, (int, float)) or isinstance(timeout_raw, bool):
        raise BridgeViolation("timeout_sec must be numeric")
    timeout_sec = float(timeout_raw)
    if timeout_sec <= 0 or timeout_sec > NONINTERACTIVE_TIMEOUT_MAX_SEC:
        raise BridgeViolation("timeout_sec must be > 0 and <= 300")

    cwd = invocation.get("cwd")
    if cwd is not None and (not isinstance(cwd, str) or not cwd.strip()):
        raise BridgeViolation("cwd must be a non-empty string when provided")

    bridge_last_message_path = invocation.get("_bridge_last_message_path")
    if bridge_last_message_path is not None:
        if not isinstance(bridge_last_message_path, str) or not bridge_last_message_path.strip():
            raise BridgeViolation("bridge last-message path must be a non-empty string")
        if not isinstance(cwd, str) or not cwd.strip():
            raise BridgeViolation("bridge last-message capture requires bridge-owned cwd")
        try:
            capture_path = Path(bridge_last_message_path).resolve()
            capture_root = Path(cwd).resolve()
            capture_path.relative_to(capture_root)
        except (OSError, ValueError) as exc:
            raise BridgeViolation("bridge last-message path must stay inside cwd") from exc

    env_override = invocation.get("env")
    if env_override is not None:
        if not isinstance(env_override, Mapping) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in env_override.items()
        ):
            raise BridgeViolation("env must be a string mapping when provided")

    stdin_file = None
    try:
        run_kwargs = {
            "shell": False,
            "text": True,
            "capture_output": True,
            "check": False,
            "timeout": timeout_sec,
        }
        if cwd is not None:
            run_kwargs["cwd"] = cwd

        minimal_env_mode = invocation.get("minimal_env")
        if minimal_env_mode in {True, "packet", "codex"}:
            if env_override is not None:
                raise BridgeViolation("minimal_env execution does not allow env overrides")
            run_kwargs["env"] = (
                _minimal_codex_env()
                if minimal_env_mode == "codex"
                else _minimal_packet_env()
            )
        elif minimal_env_mode not in {None, False}:
            raise BridgeViolation("unknown minimal_env mode")
        elif invocation.get("scrub_api_keys") is True or env_override is not None:
            child_env = (
                _scrubbed_external_env()
                if invocation.get("scrub_api_keys") is True
                else os.environ.copy()
            )
            if env_override is not None:
                child_env.update(dict(env_override))
            run_kwargs["env"] = child_env

        if stdin_text is None:
            run_kwargs["stdin"] = subprocess.DEVNULL
        elif invocation.get("stdin_transport") == "tempfile":
            # Some Windows model CLIs do not reliably consume a Python PIPE.
            # Use a seekable temporary file as stdin without exposing packet text
            # in argv or persisting it in the target repository.
            stdin_file = tempfile.TemporaryFile(
                mode="w+t",
                encoding="utf-8",
                newline="",
            )
            stdin_file.write(stdin_text)
            stdin_file.seek(0)
            run_kwargs["stdin"] = stdin_file
        else:
            run_kwargs["input"] = stdin_text
        completed = subprocess.run(argv, **run_kwargs)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        timeout_note = f"TAKY_NONINTERACTIVE_TIMEOUT after {timeout_sec:g}s"
        stderr = (str(stderr).rstrip() + "\n" + timeout_note).lstrip("\n")
        return {
            "returncode": 124,
            "stdout": str(stdout),
            "stderr": stderr,
            "timed_out": True,
            "outcome_unknown": True,
            "timeout_sec": timeout_sec,
        }
    finally:
        if stdin_file is not None:
            stdin_file.close()

    captured_stdout = completed.stdout if isinstance(completed.stdout, str) else ""
    captured_stderr = completed.stderr if isinstance(completed.stderr, str) else ""
    if bridge_last_message_path is not None:
        try:
            final_message = Path(bridge_last_message_path).read_text(
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            final_message = ""
        if final_message.strip():
            captured_stdout = final_message

    return {
        "returncode": completed.returncode,
        "stdout": captured_stdout,
        "stderr": captured_stderr,
    }


def record_startup_readback(
    runtime: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise BridgeViolation("startup readback receipt must be an object")
    if not callable(verifier):
        raise BridgeViolation("startup readback verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("startup readback verifier_id required")
    if verifier(receipt) is not True:
        raise BridgeViolation("startup readback verification failed")
    if receipt.get("authority_digest") != runtime.get("authority_digest"):
        raise BridgeViolation("startup readback authority mismatch")
    normalized, error = canonical_startup_readback_sources(receipt.get("sources"))
    if error or normalized is None:
        raise BridgeViolation(error or "startup readback sources invalid")
    receipt_id = startup_readback_receipt_id(
        str(runtime.get("authority_digest") or ""),
        normalized,
    )
    if not receipt_id:
        raise BridgeViolation("startup readback receipt id could not be derived")
    updated = deepcopy(dict(runtime))
    context = updated.setdefault("context", {})
    context["startup_readback_receipt"] = {
        "receipt_id": receipt_id,
        "authority_digest": runtime.get("authority_digest"),
        "sources": normalized,
        "verified": True,
        "verified_by": verifier_id.strip(),
    }
    return updated



def _receipt_billing_class(receipt: Mapping[str, Any]) -> str | None:
    economy = receipt.get("economy_evaluation")
    if not isinstance(economy, Mapping):
        return None
    evidence = economy.get("evidence")
    if not isinstance(evidence, list):
        return None
    values = {
        item.split(":", 1)[1].strip().upper()
        for item in evidence
        if isinstance(item, str) and item.startswith("billing-class:")
    }
    if len(values) != 1:
        return None
    value = next(iter(values))
    return value if value in {"UNMETERED", "SUBSCRIPTION_QUOTA", "PAID_API"} else None


def _external_dry_run_receipt_ok(receipt: Mapping[str, Any]) -> bool:
    """Defense-in-depth: execution bridge revalidates persisted DRY_RUN evidence."""
    economy = receipt.get("economy_evaluation")
    if not isinstance(economy, Mapping):
        return False
    dry = economy.get("dry_run")
    if not isinstance(dry, Mapping) or dry.get("state") != "DRY_RUN_OK":
        return False
    gates = receipt.get("gate_receipts")
    if not isinstance(gates, list):
        return False
    for item in gates:
        if not isinstance(item, Mapping) or item.get("gate") != "COST":
            continue
        evidence = item.get("evidence")
        if isinstance(evidence, list) and any(
            isinstance(x, str) and x.startswith("dry-run:") for x in evidence
        ):
            return True
    return False


def claim_execution_receipt(
    runtime: Mapping[str, Any],
    receipt_id: str,
    *,
    executor_id: str,
) -> tuple[dict[str, Any], str]:
    """Atomically claim intent in runtime before an external/local runner is invoked."""
    receipt = _receipt(runtime, receipt_id)
    if not isinstance(executor_id, str) or not executor_id.strip():
        raise BridgeViolation("executor_id required")
    calls = runtime.get("execution_calls", {})
    if isinstance(calls, Mapping) and receipt_id in calls:
        raise BridgeViolation("receipt already has an executor call")

    execution_key = receipt.get("execution_key")
    active = runtime.get("active_attempts", {}).get(execution_key)
    if not isinstance(active, Mapping) or active.get("receipt_id") != receipt_id:
        raise BridgeViolation("receipt has no matching active attempt")
    if active.get("status") != "PENDING":
        raise BridgeViolation("active attempt is not pending")

    token = secrets.token_hex(24)
    token_hash = stable_hash(token)
    updated = deepcopy(dict(runtime))
    updated_active = updated.setdefault("active_attempts", {}).get(execution_key)
    if not isinstance(updated_active, dict):
        raise BridgeViolation("active attempt state is not mutable")
    updated_active.update({
        "status": "RESERVED",
        "claimed_by": executor_id.strip(),
        "claim_token_hash": token_hash,
        "claim_runtime_version": runtime.get("runtime_version"),
    })
    updated.setdefault("execution_calls", {})[receipt_id] = {
        "executor_id": executor_id.strip(),
        "provider": None,
        "model": None,
        "actual_calls": 0,
        "method_or_tool": None,
        "result_digest": None,
        "result": None,
        "status": "CLAIMED",
        "claim_token_hash": token_hash,
    }
    return updated, token


def reconcile_execution_claim(
    runtime: Mapping[str, Any],
    receipt_id: str,
    *,
    reconciler_id: str,
    reason: str,
) -> dict[str, Any]:
    """Terminalize a persisted CLAIMED/CALLING receipt after an interrupted/blocked runner path."""
    receipt = _receipt(runtime, receipt_id)
    if not isinstance(reconciler_id, str) or not reconciler_id.strip():
        raise BridgeViolation("reconciler_id required")
    if not isinstance(reason, str) or not reason.strip():
        raise BridgeViolation("reconcile reason required")

    call_record = runtime.get("execution_calls", {}).get(receipt_id)
    if not isinstance(call_record, Mapping):
        raise BridgeViolation("execution claim missing")
    if call_record.get("status") not in {"CLAIMED", "CALLING"}:
        raise BridgeViolation("execution claim is already terminal")

    updated = deepcopy(dict(runtime))
    calls = updated.setdefault("execution_calls", {})
    execution_key = receipt.get("execution_key")
    active = updated.setdefault("active_attempts", {}).get(execution_key)
    possibly_invoked = (
        call_record.get("status") == "CALLING"
        or (isinstance(active, Mapping) and active.get("status") == "CALLING")
    )
    terminal_status = "OUTCOME_UNKNOWN" if possibly_invoked else "FAILED"
    failed_result = {
        "returncode": 125 if possibly_invoked else 127,
        "stdout": "",
        "stderr": (
            "TAKY_EXECUTION_OUTCOME_UNKNOWN:"
            if possibly_invoked
            else "TAKY_EXECUTION_RECONCILED:"
        ) + reason.strip(),
    }
    calls[receipt_id].update({
        "result_digest": stable_hash(failed_result),
        "result": failed_result,
        "status": terminal_status,
        "reconciled_by": reconciler_id.strip(),
    })
    if isinstance(active, dict):
        active.update({
            "status": terminal_status,
            "reconciled_by": reconciler_id.strip(),
        })
    return updated


def execute_with_receipt(
    runtime: Mapping[str, Any],
    receipt_id: str,
    invocation: Mapping[str, Any],
    *,
    runner: Callable[[Mapping[str, Any]], Mapping[str, Any]] = subprocess_runner,
    executor_id: str,
    preclaimed: bool = False,
    claim_token: str | None = None,
    pre_run_checkpoint: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = _receipt(runtime, receipt_id)
    if not isinstance(executor_id, str) or not executor_id.strip():
        raise BridgeViolation("executor_id required")
    if not isinstance(invocation, Mapping):
        raise BridgeViolation("invocation must be an object")

    existing_calls = runtime.get("execution_calls", {})
    existing_call = (
        existing_calls.get(receipt_id)
        if isinstance(existing_calls, Mapping)
        else None
    )
    if preclaimed:
        if not isinstance(existing_call, Mapping):
            raise BridgeViolation("persisted execution claim missing")
        if existing_call.get("status") != "CLAIMED":
            raise BridgeViolation("persisted execution claim is not active")
        if existing_call.get("executor_id") != executor_id.strip():
            raise BridgeViolation("persisted execution claim executor mismatch")
        if not isinstance(claim_token, str) or not claim_token:
            raise BridgeViolation("persisted execution claim token required")
        if existing_call.get("claim_token_hash") != stable_hash(claim_token):
            raise BridgeViolation("persisted execution claim token mismatch")
    elif existing_call is not None:
        raise BridgeViolation("receipt already has an executor call")

    call = invocation.get("call")
    if not isinstance(call, Mapping):
        raise BridgeViolation("invocation call binding required")
    if stable_hash(dict(call)) != receipt.get("call_digest"):
        raise BridgeViolation("actual invocation call does not match receipt")

    provider = str(invocation.get("provider") or "").strip().lower()
    model = str(call.get("model") or "").strip().lower()
    if not provider or not model:
        raise BridgeViolation("actual provider/model required")
    if model != "local" and runner is subprocess_runner and not preclaimed:
        raise BridgeViolation("external subprocess execution requires persisted receipt claim")

    billing_class = None
    if receipt.get("call_allowed") is not True:
        if provider != "local" or model != "local":
            raise BridgeViolation("LOCAL_ONLY receipt cannot invoke external provider")
    else:
        if provider != "local" or model != "local":
            if not _external_dry_run_receipt_ok(receipt):
                raise BridgeViolation("external execution requires persisted DRY_RUN_OK evidence")
            billing_class = _receipt_billing_class(receipt)
            if billing_class is None:
                raise BridgeViolation("external execution requires one trusted billing-class receipt")
            expected_calls = call.get("expected_calls", 1)
            if expected_calls != 1:
                raise BridgeViolation(
                    "current receipt executor supports exactly one external invocation; "
                    "batch workload inside one invocation instead of multi-call receipt"
                )

    external_invocation = (
        receipt.get("call_allowed") is True
        and (provider != "local" or model != "local")
    )
    if preclaimed and external_invocation and pre_run_checkpoint is None:
        raise BridgeViolation(
            "external preclaimed execution requires durable pre-run checkpoint"
        )

    execution_key = receipt.get("execution_key")
    active = runtime.get("active_attempts", {}).get(execution_key)
    if not isinstance(active, Mapping) or active.get("receipt_id") != receipt_id:
        raise BridgeViolation("receipt has no matching active attempt")
    if preclaimed:
        if active.get("status") != "RESERVED":
            raise BridgeViolation("preclaimed active attempt is not reserved")
        if active.get("claimed_by") != executor_id.strip():
            raise BridgeViolation("preclaimed active attempt executor mismatch")
    elif active.get("status") != "PENDING":
        raise BridgeViolation("active attempt is not pending")

    expected_tool = str(active.get("attempt", {}).get("method_or_tool") or "").strip().lower()
    actual_tool = str(invocation.get("method_or_tool") or "").strip().lower()
    if expected_tool and actual_tool != expected_tool:
        raise BridgeViolation("actual executor route does not match receipt")

    argv_tool = _argv_identity(invocation)
    aliases = {
        "python": {"python", "python3", "py"},
        "python3": {"python", "python3", "py"},
        "py": {"python", "python3", "py"},
        "powershell": {"powershell", "pwsh"},
        "pwsh": {"powershell", "pwsh"},
        "git": {"git"},
        "claude": {"claude"},
        "codex": {"codex"},
        "codex-ephemeral": {"codex"},
        "codex-app-ephemeral": {"codex"},
        "codex-app-devnull": {"codex"},
        "gemini": {"gemini"},
    }
    if actual_tool in aliases and argv_tool and argv_tool not in aliases[actual_tool]:
        raise BridgeViolation("argv executable does not match receipt-bound route")
    if receipt.get("call_allowed") is not True and argv_tool in {"claude", "codex", "openai"}:
        raise BridgeViolation("LOCAL_ONLY receipt cannot invoke external model CLI")
    if receipt.get("call_allowed") is True and model != "local" and provider == "local":
        raise BridgeViolation("external-model receipt requires non-local provider")

    execution_mode = str(call.get("execution_mode") or "").strip().upper()
    runner_invocation = dict(invocation)
    if billing_class in {"UNMETERED", "SUBSCRIPTION_QUOTA"}:
        if invocation.get("env") is not None:
            raise BridgeViolation("subscription/unmetered route does not allow env overrides")
        runner_invocation["scrub_api_keys"] = True

    argv = invocation.get("argv")
    if model != "local" and actual_tool == "claude":
        if provider not in {"anthropic", "claude"}:
            raise BridgeViolation("Claude external route requires Anthropic provider")
        if not isinstance(argv, list) or not argv:
            raise BridgeViolation("Claude external route requires argv")
        argv_model = _argv_option_value(argv, "--model", "-m")
        if str(argv_model or "").strip().lower() != model:
            raise BridgeViolation("Claude argv model must match receipt-bound model")
        expected_effort = str(call.get("effort") or "").strip().lower()
        argv_effort = _argv_option_value(argv, "--effort")
        if expected_effort and str(argv_effort or "").strip().lower() != expected_effort:
            raise BridgeViolation("Claude argv effort must match receipt-bound effort")
    elif model != "local" and actual_tool == "codex":
        if execution_mode != "CODEX_VERIFY_ONLY":
            raise BridgeViolation("Codex external execution requires a dedicated hardened verifier contract")
        if model != "codex":
            raise BridgeViolation("Codex verifier receipt model must be codex")
        if provider not in {"openai", "codex"}:
            raise BridgeViolation("Codex verifier route requires OpenAI provider")

    packet_temp_dir = None
    if execution_mode == "PACKET_ONLY":
        packet = invocation.get("stdin_text")
        if not isinstance(packet, str) or not packet:
            raise BridgeViolation("PACKET_ONLY execution requires stdin_text packet")
        if stable_hash(packet) != call.get("packet_digest"):
            raise BridgeViolation("PACKET_ONLY stdin packet digest mismatch")

        argv = invocation.get("argv")
        if not isinstance(argv, list) or not argv:
            raise BridgeViolation("PACKET_ONLY execution requires argv")

        # PACKET_ONLY is fail-closed: only explicitly hardened executors may run.
        if actual_tool != "claude" or argv_tool != "claude":
            raise BridgeViolation("PACKET_ONLY executor is not hardened/allowed")

        if provider not in {"anthropic", "claude"}:
            raise BridgeViolation("PACKET_ONLY Claude route requires Anthropic provider")

        argv_model = _argv_option_value(argv, "--model", "-m")
        if str(argv_model or "").strip().lower() != model:
            raise BridgeViolation("PACKET_ONLY Claude argv model must match receipt-bound model")
        expected_effort = str(call.get("effort") or "").strip().lower()
        argv_effort = _argv_option_value(argv, "--effort")
        if expected_effort and str(argv_effort or "").strip().lower() != expected_effort:
            raise BridgeViolation("PACKET_ONLY Claude argv effort must match receipt-bound effort")

        if invocation.get("cwd") is not None:
            raise BridgeViolation("PACKET_ONLY cwd is bridge-owned and must not be supplied")

        required_flags = {
            "--no-session-persistence",
            "--strict-mcp-config",
        }
        if not required_flags.issubset(set(argv)):
            raise BridgeViolation("PACKET_ONLY Claude execution missing hardened isolation flags")
        if not any(arg in {"-p", "--print"} for arg in argv):
            raise BridgeViolation("PACKET_ONLY Claude execution requires --print")

        forbidden_flags = {
            "--add-dir",
            "--mcp-config",
            "--allowedTools",
            "--allowed-tools",
            "--plugin-dir",
            "--plugin-url",
            "--agents",
        }
        for arg in argv:
            if arg in forbidden_flags or any(
                arg.startswith(flag + "=") for flag in forbidden_flags
            ):
                raise BridgeViolation("PACKET_ONLY Claude execution contains forbidden expansion flag")

        try:
            tools_index = argv.index("--tools")
            permission_index = argv.index("--permission-prompts")
            setting_sources_index = argv.index("--setting-sources")
            settings_index = argv.index("--settings")
            output_format_index = argv.index("--output-format")
        except ValueError as exc:
            raise BridgeViolation(
                "PACKET_ONLY Claude execution must disable tools/prompts and isolate settings"
            ) from exc
        if tools_index + 1 >= len(argv) or argv[tools_index + 1] != "":
            raise BridgeViolation("PACKET_ONLY Claude execution requires empty --tools")
        if permission_index + 1 >= len(argv) or argv[permission_index + 1] != "none":
            raise BridgeViolation("PACKET_ONLY Claude execution requires --permission-prompts none")
        if setting_sources_index + 1 >= len(argv) or argv[setting_sources_index + 1] != "":
            raise BridgeViolation("PACKET_ONLY Claude execution requires empty --setting-sources")
        if settings_index + 1 >= len(argv) or argv[settings_index + 1] != "{}":
            raise BridgeViolation("PACKET_ONLY Claude execution requires empty --settings object")
        if output_format_index + 1 >= len(argv) or argv[output_format_index + 1] != "json":
            raise BridgeViolation("PACKET_ONLY Claude execution requires --output-format json")

        expected_exe = (Path.home() / ".local" / "bin" / "claude.exe").resolve()
        try:
            actual_exe = Path(argv[0]).resolve()
        except OSError as exc:
            raise BridgeViolation("PACKET_ONLY Claude executable could not be resolved") from exc
        if actual_exe != expected_exe:
            raise BridgeViolation("PACKET_ONLY Claude executable path is not pinned")
        expected_tail = [
            "-p",
            "--input-format", "text",
            "--output-format", "json",
            "--model", model,
            "--effort", expected_effort,
            "--tools", "",
            "--permission-prompts", "none",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--settings", "{}",
        ]
        if argv[1:] != expected_tail:
            raise BridgeViolation("PACKET_ONLY Claude argv must match the exact hardened template")

        packet_temp_dir = tempfile.mkdtemp(prefix="TAKY2_PACKET_ONLY_")
        runner_invocation["cwd"] = packet_temp_dir
        runner_invocation["argv"] = [str(expected_exe), *argv[1:]]
        runner_invocation["stdin_transport"] = "tempfile"
        runner_invocation["minimal_env"] = True

    elif execution_mode == "CODEX_VERIFY_ONLY":
        packet = invocation.get("stdin_text")
        if not isinstance(packet, str) or not packet:
            raise BridgeViolation("CODEX_VERIFY_ONLY requires stdin_text packet")
        if stable_hash(packet) != call.get("packet_digest"):
            raise BridgeViolation("CODEX_VERIFY_ONLY stdin packet digest mismatch")

        argv = invocation.get("argv")
        if not isinstance(argv, list) or not argv:
            raise BridgeViolation("CODEX_VERIFY_ONLY requires argv")
        if actual_tool != "codex" or argv_tool != "codex":
            raise BridgeViolation("CODEX_VERIFY_ONLY executor is not Codex")
        if invocation.get("cwd") is not None:
            raise BridgeViolation("CODEX_VERIFY_ONLY cwd is bridge-owned and must not be supplied")

        expected_exe = (
            Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
        ).resolve()
        try:
            actual_exe = Path(argv[0]).resolve()
        except OSError as exc:
            raise BridgeViolation("CODEX_VERIFY_ONLY executable could not be resolved") from exc
        if actual_exe != expected_exe:
            raise BridgeViolation("CODEX_VERIFY_ONLY executable path is not pinned")

        expected_effort = str(call.get("effort") or "").strip().lower()
        if expected_effort not in {"low", "medium", "high"}:
            raise BridgeViolation("CODEX_VERIFY_ONLY requires low/medium/high receipt effort")
        effort_config = f'model_reasoning_effort="{expected_effort}"'
        disabled_features = [
            "shell_tool",
            "unified_exec",
            "shell_snapshot",
            "multi_agent",
            "apps",
            "hooks",
            "remote_plugin",
        ]
        tool_disable_args = [
            token
            for feature in disabled_features
            for token in ("--disable", feature)
        ]
        expected_tail = [
            "exec",
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "-c", effort_config,
            "-c", 'web_search="disabled"',
            *tool_disable_args,
            "-",
        ]
        if argv[1:] != expected_tail:
            raise BridgeViolation("CODEX_VERIFY_ONLY argv must match the exact hardened template")

        packet_temp_dir = tempfile.mkdtemp(prefix="TAKY2_CODEX_VERIFY_")
        last_message_path = str(Path(packet_temp_dir) / "codex-last-message.txt")
        runner_invocation["cwd"] = packet_temp_dir
        runner_invocation["argv"] = [
            str(expected_exe),
            "exec",
            "--sandbox", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "-c", effort_config,
            "-c", 'web_search="disabled"',
            *tool_disable_args,
            "-C", packet_temp_dir,
            "--output-last-message", last_message_path,
            "-",
        ]
        runner_invocation["stdin_transport"] = "tempfile"
        runner_invocation["minimal_env"] = "codex"
        runner_invocation["_bridge_last_message_path"] = last_message_path

    updated = deepcopy(dict(runtime))
    calls = updated.setdefault("execution_calls", {})
    if receipt_id in calls and not preclaimed:
        raise BridgeViolation("receipt already has an executor call")
    if receipt_id not in calls:
        calls[receipt_id] = {
            "executor_id": executor_id.strip(),
            "provider": provider,
            "model": model,
            "actual_calls": 1,
            "method_or_tool": actual_tool,
            "result_digest": None,
            "result": None,
            "status": "CALLING",
        }
    calls[receipt_id].update({
        "provider": provider,
        "model": model,
        "actual_calls": 1,
        "method_or_tool": actual_tool,
        "status": "CALLING",
    })
    updated_active = updated.setdefault("active_attempts", {}).get(execution_key)
    if not isinstance(updated_active, dict):
        raise BridgeViolation("active attempt state is not mutable")
    updated_active["status"] = "CALLING"

    if pre_run_checkpoint is not None:
        checkpointed = pre_run_checkpoint(updated)
        if not isinstance(checkpointed, Mapping):
            raise BridgeViolation("pre-run checkpoint must return runtime state")
        updated = deepcopy(dict(checkpointed))
        calls = updated.setdefault("execution_calls", {})
        call_record = calls.get(receipt_id)
        updated_active = updated.setdefault("active_attempts", {}).get(execution_key)
        if not isinstance(call_record, dict) or call_record.get("status") != "CALLING":
            raise BridgeViolation("pre-run checkpoint did not persist CALLING receipt")
        if not isinstance(updated_active, dict) or updated_active.get("status") != "CALLING":
            raise BridgeViolation("pre-run checkpoint did not persist CALLING attempt")

    try:
        try:
            result = dict(runner(runner_invocation))
        except Exception as exc:
            result = {
                "returncode": 125,
                "stdout": "",
                "stderr": f"TAKY_EXECUTOR_EXCEPTION:{type(exc).__name__}:{exc}",
                "outcome_unknown": True,
            }
    finally:
        if packet_temp_dir is not None:
            shutil.rmtree(packet_temp_dir, ignore_errors=True)

    returncode = result.get("returncode")
    if (
        external_invocation
        and returncode not in {None, 0}
        and result.get("provider_call_confirmed_absent") is not True
    ):
        # A nonzero model-CLI exit does not prove the provider was never invoked.
        # Treat uncertain external side effects/spend as unknown so the receipt
        # cannot be silently retried as an ordinary failure.
        result["outcome_unknown"] = True

    result_digest = stable_hash(result)
    status = (
        "OUTCOME_UNKNOWN"
        if result.get("outcome_unknown") is True
        else ("RETURNED" if returncode in {None, 0} else "FAILED")
    )
    calls[receipt_id].update({
        "result_digest": result_digest,
        "result": result,
        "status": status,
    })
    updated_active["status"] = status
    # Executor is intentionally forbidden from writing SUCCESS/completion/evidence.
    return updated, result


def record_independent_review(
    runtime: Mapping[str, Any],
    receipt_id: str,
    review: Mapping[str, Any],
    *,
    reviewer_id: str,
    review_verifier: Callable[
        [Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], bool
    ],
    review_verifier_id: str,
) -> dict[str, Any]:
    receipt = _receipt(runtime, receipt_id)
    call_record = runtime.get("execution_calls", {}).get(receipt_id)
    if not isinstance(call_record, Mapping):
        raise BridgeViolation("executor result missing before independent review")
    if call_record.get("status") != "RETURNED":
        raise BridgeViolation("independent review requires a successful returned executor call")
    if not isinstance(review, Mapping):
        raise BridgeViolation("independent review must be an object")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise BridgeViolation("independent reviewer_id required")
    if not callable(review_verifier):
        raise BridgeViolation("independent review attestation verifier required")
    if not isinstance(review_verifier_id, str) or not review_verifier_id.strip():
        raise BridgeViolation("independent review verifier_id required")
    if review_verifier(review, receipt, call_record) is not True:
        raise BridgeViolation("independent review attestation verification failed")

    orchestration = receipt.get("orchestration", {})
    if not isinstance(orchestration, Mapping):
        raise BridgeViolation("receipt orchestration binding missing")
    expected_role = orchestration.get("independent_reviewer_role")
    expected_actor = orchestration.get("independent_reviewer_actor")
    if review.get("reviewer_role") != expected_role:
        raise BridgeViolation("independent review must use receipt-bound reviewer role")
    if review.get("reviewer_actor") != expected_actor:
        raise BridgeViolation("independent review must use receipt-bound reviewer actor")

    reviewer_id = reviewer_id.strip()
    review_verifier_id = review_verifier_id.strip()
    if reviewer_id == call_record.get("executor_id"):
        raise BridgeViolation("executor cannot act as independent reviewer")
    if review_verifier_id in {reviewer_id, call_record.get("executor_id")}:
        raise BridgeViolation("independent review attestation verifier must be separate")

    evidence_ref = review.get("evidence_ref")
    source_ref = review.get("source_or_artifact_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        raise BridgeViolation("independent review evidence_ref required")
    evidence_ref = evidence_ref.strip()
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise BridgeViolation("independent review source/artifact ref required")
    if review.get("receipt_id") != receipt_id:
        raise BridgeViolation("independent review is not receipt-bound")
    if review.get("target_result_digest") != call_record.get("result_digest"):
        raise BridgeViolation("independent review target result mismatch")
    if review.get("authority_digest") != receipt.get("authority_digest"):
        raise BridgeViolation("independent review authority mismatch")

    critical_gaps = review.get("critical_gaps", [])
    if not isinstance(critical_gaps, list):
        raise BridgeViolation("independent review critical_gaps must be a list")
    passed = review.get("passed") is True and not critical_gaps
    acceptance_state = "ACCEPTED" if passed else "REJECTED"
    review_digest = stable_hash(dict(review))

    updated = deepcopy(dict(runtime))
    review_registry = updated.setdefault("independent_review_registry", {})
    evidence_registry = updated.setdefault("evidence_registry", {})
    if evidence_ref in review_registry or evidence_ref in evidence_registry:
        raise BridgeViolation("independent review evidence_ref already exists")

    review_entry = {
        "receipt_id": receipt_id,
        "reviewer_role": expected_role,
        "reviewer_actor": expected_actor,
        "reviewer_id": reviewer_id,
        "bridge_id": review_verifier_id,
        "acceptance_state": acceptance_state,
        "critical_gaps": list(critical_gaps),
        "target_result_digest": call_record.get("result_digest"),
        "authority_digest": receipt.get("authority_digest"),
        "semantic_owner_ref": receipt.get("semantic_owner_ref"),
        "semantic_owner_scope": receipt.get("semantic_owner_scope"),
        "execution_scope": receipt.get("execution_scope"),
        "source_or_artifact_ref": source_ref.strip(),
        "review_digest": review_digest,
    }
    review_registry[evidence_ref] = review_entry
    evidence_registry[evidence_ref] = {
        "type": "independent_review",
        "evidence_type": "independent_review",
        "verified": True,
        "acceptance_state": acceptance_state,
        "claim_supported": "independent_review",
        "scope": receipt.get("execution_scope"),
        "producer": reviewer_id,
        "validator": review_verifier_id,
        "verified_by": review_verifier_id,
        "verifier_role": expected_role,
        "independent_reviewer_role": expected_role,
        "independent_reviewer_actor": expected_actor,
        "independent_reviewer": expected_actor,
        "independent_reviewer_id": reviewer_id,
        "source_or_artifact_ref": source_ref.strip(),
        "revision_or_hash": review_digest,
        "authority_digest_or_key_version": receipt.get("authority_digest"),
        "semantic_owner_ref": receipt.get("semantic_owner_ref"),
        "semantic_owner_scope": receipt.get("semantic_owner_scope"),
        "verification_tier": receipt.get("verification_tier", "STANDARD"),
        "source_status": "CURRENT",
        "receipt_id": receipt_id,
        "plan_digest": receipt.get("plan_digest"),
        "action_digest": receipt.get("action_digest"),
        "call_digest": receipt.get("call_digest"),
        "result_digest": call_record.get("result_digest"),
    }
    return updated


def verify_execution(
    runtime: Mapping[str, Any],
    receipt_id: str,
    *,
    verifier: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
    verifier_id: str,
) -> dict[str, Any]:
    receipt = _receipt(runtime, receipt_id)
    call_record = runtime.get("execution_calls", {}).get(receipt_id)
    if not isinstance(call_record, Mapping):
        raise BridgeViolation("executor result missing")
    if call_record.get("status") not in {"RETURNED", "FAILED"}:
        raise BridgeViolation("verification requires a terminal executor call")
    if not callable(verifier):
        raise BridgeViolation("independent verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("verifier_id required")
    if verifier_id.strip() == call_record.get("executor_id"):
        raise BridgeViolation("executor cannot self-certify")

    verdict = verifier(call_record, receipt)
    if not isinstance(verdict, Mapping):
        raise BridgeViolation("verifier verdict must be an object")

    orchestration = receipt.get("orchestration", {})
    if not isinstance(orchestration, Mapping):
        raise BridgeViolation("receipt orchestration binding missing")
    expected_verifier_role = orchestration.get("verifier_role")
    expected_verifier_actor = orchestration.get("verifier_actor")
    if verdict.get("verifier_role") != expected_verifier_role:
        raise BridgeViolation("verification must use receipt-bound verifier role")
    if verdict.get("verifier_actor") != expected_verifier_actor:
        raise BridgeViolation("verification must use receipt-bound verifier actor")

    evidence_ref = verdict.get("evidence_ref")
    evidence_type = verdict.get("evidence_type")
    if not isinstance(evidence_ref, str) or not evidence_ref:
        raise BridgeViolation("verifier evidence_ref required")
    if evidence_type not in VALID_EVIDENCE_TYPES:
        raise BridgeViolation("unsupported verifier evidence type")
    if evidence_type not in EXECUTION_EVIDENCE_TYPES:
        raise BridgeViolation("execution verifier cannot launder non-execution evidence type")

    updated = deepcopy(dict(runtime))
    outcomes = updated.setdefault("execution_outcomes", {})
    active = updated.setdefault("active_attempts", {})
    execution_key = receipt.get("execution_key")

    if verdict.get("passed") is not True:
        outcomes[receipt_id] = "VALIDATION"
        active_item = active.get(execution_key)
        scope = receipt.get("execution_scope")
        if isinstance(active_item, Mapping) and isinstance(scope, str) and scope:
            ledgers = updated.setdefault("route_ledgers", {})
            ledger = ledgers.setdefault(scope, _empty_ledger())
            ledgers[scope] = record_failure(
                ledger,
                active_item.get("attempt", {}),
                "VALIDATION",
            )
        if execution_key in active:
            active.pop(execution_key, None)
        return updated

    required = verdict.get("required_verifications", ["technical", "intent"])
    passed = verdict.get("passed_verifications", [])
    gaps = verdict.get("critical_gaps", [])
    if not isinstance(required, list) or not isinstance(passed, list) or not isinstance(gaps, list):
        raise BridgeViolation("verification lists are malformed")
    minimum = required_verifications_for_tier(
        receipt.get("verification_tier", "STANDARD")
    )
    if not minimum.issubset(set(required)):
        raise BridgeViolation("verifier under-specifies required verification tier")

    independent_review_ref = None
    independent_review = None
    if "independent" in set(required):
        expected_reviewer_role = orchestration.get("independent_reviewer_role")
        expected_reviewer_actor = orchestration.get("independent_reviewer_actor")
        if verdict.get("independent_reviewer_role") != expected_reviewer_role:
            raise BridgeViolation(
                "independent verification must use receipt-bound reviewer role"
            )
        if verdict.get("independent_reviewer_actor") != expected_reviewer_actor:
            raise BridgeViolation(
                "independent verification must use receipt-bound reviewer actor"
            )
        independent_review_ref = verdict.get("independent_review_ref")
        if not isinstance(independent_review_ref, str) or not independent_review_ref.strip():
            raise BridgeViolation("STRONG verification requires independent review receipt")
        independent_review_ref = independent_review_ref.strip()
        review_registry = runtime.get("independent_review_registry", {})
        independent_review = (
            review_registry.get(independent_review_ref)
            if isinstance(review_registry, Mapping)
            else None
        )
        if not isinstance(independent_review, Mapping):
            raise BridgeViolation("independent review receipt missing")
        if independent_review.get("receipt_id") != receipt_id:
            raise BridgeViolation("independent review receipt mismatch")
        if independent_review.get("reviewer_role") != expected_reviewer_role:
            raise BridgeViolation("independent reviewer role mismatch")
        if independent_review.get("reviewer_actor") != expected_reviewer_actor:
            raise BridgeViolation("independent reviewer actor mismatch")
        if independent_review.get("acceptance_state") != "ACCEPTED":
            raise BridgeViolation("independent review is not accepted")
        if independent_review.get("target_result_digest") != call_record.get("result_digest"):
            raise BridgeViolation("independent review target result mismatch")
        if independent_review.get("authority_digest") != receipt.get("authority_digest"):
            raise BridgeViolation("independent review authority mismatch")
        if independent_review.get("execution_scope") != receipt.get("execution_scope"):
            raise BridgeViolation("independent review scope mismatch")
        independent_reviewer_id = independent_review.get("reviewer_id")
        if not isinstance(independent_reviewer_id, str) or not independent_reviewer_id.strip():
            raise BridgeViolation("independent reviewer identity missing")
        if independent_reviewer_id.strip() == call_record.get("executor_id"):
            raise BridgeViolation("executor cannot act as independent reviewer")
        if independent_reviewer_id.strip() == verifier_id.strip():
            raise BridgeViolation("primary verifier cannot also be independent reviewer")

    if verdict.get("key_match") is not True:
        raise BridgeViolation("verifier did not confirm Key match")
    if gaps:
        raise BridgeViolation("verifier reports critical gaps")
    if set(required) - set(passed):
        raise BridgeViolation("verifier has missing required checks")

    outcomes[receipt_id] = "SUCCESS"
    if execution_key in active:
        active[execution_key]["status"] = "SUCCESS"

    evidence_refs = [evidence_ref]
    verification_evidence = {name: evidence_ref for name in passed}
    if independent_review_ref is not None:
        if independent_review_ref not in evidence_refs:
            evidence_refs.append(independent_review_ref)
        verification_evidence["independent"] = independent_review_ref

    updated.setdefault("evidence_registry", {})[evidence_ref] = {
        "type": evidence_type,
        "evidence_type": evidence_type,
        "verified": True,
        "acceptance_state": "ACCEPTED",
        "claim_supported": str(verdict.get("claim_supported") or "execution_verification"),
        "scope": receipt.get("execution_scope"),
        "producer": call_record.get("executor_id"),
        "validator": verifier_id.strip(),
        "verified_by": verifier_id.strip(),
        "verifier_role": verdict.get("verifier_role"),
        "verifier_actor": verdict.get("verifier_actor"),
        "independent_reviewer_role": verdict.get("independent_reviewer_role"),
        "independent_reviewer_actor": verdict.get("independent_reviewer_actor"),
        "independent_reviewer": verdict.get("independent_reviewer_actor"),
        "independent_review_ref": independent_review_ref,
        "source_or_artifact_ref": evidence_ref,
        "revision_or_hash": call_record.get("result_digest"),
        "authority_digest_or_key_version": receipt.get("authority_digest"),
        "semantic_owner_ref": receipt.get("semantic_owner_ref"),
        "semantic_owner_scope": receipt.get("semantic_owner_scope"),
        "verification_tier": receipt.get("verification_tier", "STANDARD"),
        "source_status": "CURRENT",
        "receipt_id": receipt_id,
        "plan_digest": receipt.get("plan_digest"),
        "action_digest": receipt.get("action_digest"),
        "call_digest": receipt.get("call_digest"),
        "result_digest": call_record.get("result_digest"),
    }
    updated.setdefault("completion_registry", {})[receipt_id] = {
        "plan_digest": receipt.get("plan_digest"),
        "action_digest": receipt.get("action_digest"),
        "call_digest": receipt.get("call_digest"),
        "authority_digest": receipt.get("authority_digest"),
        "semantic_owner_ref": receipt.get("semantic_owner_ref"),
        "semantic_owner_scope": receipt.get("semantic_owner_scope"),
        "verification_tier": receipt.get("verification_tier", "STANDARD"),
        "evidence_refs": evidence_refs,
        "verification_evidence": verification_evidence,
        "key_match": True,
        "critical_gaps": [],
        "required_verifications": list(required),
        "passed_verifications": list(passed),
        "verifier_role": verdict.get("verifier_role"),
        "verifier_actor": verdict.get("verifier_actor"),
        "independent_reviewer_role": verdict.get("independent_reviewer_role"),
        "independent_reviewer_actor": verdict.get("independent_reviewer_actor"),
        "independent_reviewer": verdict.get("independent_reviewer_actor"),
        "independent_review_ref": independent_review_ref,
        "user_confirmation_ref": None,
        "verified_by": verifier_id.strip(),
    }
    return updated


def record_user_confirmation(
    runtime: Mapping[str, Any],
    receipt_id: str,
    event: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    _receipt(runtime, receipt_id)
    if not callable(verifier):
        raise BridgeViolation("USER event verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("USER event verifier_id required")
    if verifier(event) is not True:
        raise BridgeViolation("USER event verification failed")
    if event.get("actor") != "USER" or event.get("explicit") is not True:
        raise BridgeViolation("only explicit USER confirmation is trusted")
    if event.get("kind") != "confirmation" or event.get("receipt_id") != receipt_id:
        raise BridgeViolation("USER confirmation is not bound to receipt")

    event_ref = event.get("event_ref")
    if not isinstance(event_ref, str) or not event_ref.strip():
        raise BridgeViolation("event_ref required")
    if runtime.get("execution_outcomes", {}).get(receipt_id) != "SUCCESS":
        raise BridgeViolation("cannot confirm an unverified execution")
    completion = runtime.get("completion_registry", {}).get(receipt_id)
    if not isinstance(completion, Mapping):
        raise BridgeViolation("completion record required before confirmation")

    updated = deepcopy(dict(runtime))
    events = updated.setdefault("user_events", {})
    if event_ref in events:
        raise BridgeViolation("user event_ref already exists")
    events[event_ref] = {
        "actor": "USER",
        "kind": "confirmation",
        "receipt_id": receipt_id,
        "explicit": True,
        "verified_by": verifier_id.strip(),
    }
    updated["completion_registry"][receipt_id]["user_confirmation_ref"] = event_ref
    return updated


def record_user_stop(
    runtime: Mapping[str, Any],
    receipt_id: str,
    event: Mapping[str, Any],
    *,
    verifier: Callable[[Mapping[str, Any]], bool],
    verifier_id: str,
) -> dict[str, Any]:
    receipt = _receipt(runtime, receipt_id)
    if not callable(verifier):
        raise BridgeViolation("USER stop verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("USER stop verifier_id required")
    if verifier(event) is not True:
        raise BridgeViolation("USER stop verification failed")
    if (
        event.get("actor") != "USER"
        or event.get("kind") != "stop"
        or event.get("explicit") is not True
        or event.get("receipt_id") != receipt_id
    ):
        raise BridgeViolation("explicit receipt-bound USER stop required")

    event_ref = event.get("event_ref")
    if not isinstance(event_ref, str) or not event_ref.strip():
        raise BridgeViolation("event_ref required")

    updated = deepcopy(dict(runtime))
    events = updated.setdefault("user_events", {})
    if event_ref in events:
        raise BridgeViolation("user event_ref already exists")
    events[event_ref] = {
        "actor": "USER",
        "kind": "stop",
        "receipt_id": receipt_id,
        "explicit": True,
        "verified_by": verifier_id.strip(),
    }

    updated.setdefault("execution_outcomes", {})[receipt_id] = "ABANDONED"
    execution_key = receipt.get("execution_key")
    if execution_key:
        updated.setdefault("active_attempts", {}).pop(execution_key, None)
    stored_receipt = updated.setdefault("preflight_receipts", {}).get(receipt_id)
    if isinstance(stored_receipt, dict):
        stored_receipt["consumed"] = True
        stored_receipt["abandoned_by"] = event_ref
    completion = updated.setdefault("completion_registry", {}).get(receipt_id)
    if isinstance(completion, dict):
        completion["abandoned_by"] = event_ref
    return updated


ECONOMY_BRIDGE_DECISION_KINDS = {
    "EXTERNAL_NOT_NECESSARY",
    "REUSE_SUFFICIENT",
    "LOCAL_SUFFICIENT",
}


def record_economy_decision(
    runtime: Mapping[str, Any],
    action: Mapping[str, Any],
    decision: Mapping[str, Any],
    *,
    verifier: Callable[
        [Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], bool
    ],
    verifier_id: str,
) -> dict[str, Any]:
    """Record a verifier-attested SAVEY_AI_ECONOMY decision into runtime state."""
    if not isinstance(action, Mapping):
        raise BridgeViolation("economy action must be an object")
    if not isinstance(decision, Mapping):
        raise BridgeViolation("economy decision must be an object")
    if not callable(verifier):
        raise BridgeViolation("economy decision verifier required")
    if not isinstance(verifier_id, str) or not verifier_id.strip():
        raise BridgeViolation("economy decision verifier_id required")

    authority_digest = runtime.get("authority_digest")
    if not isinstance(authority_digest, str) or not authority_digest.strip():
        raise BridgeViolation("economy decision requires current authority digest")

    decision_kind = decision.get("decision_kind")
    if decision_kind not in ECONOMY_BRIDGE_DECISION_KINDS:
        raise BridgeViolation("unsupported economy decision kind")

    evidence_ref = decision.get("evidence_ref")
    source_ref = decision.get("source_or_artifact_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        raise BridgeViolation("economy decision evidence_ref required")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise BridgeViolation("economy decision source/artifact ref required")

    owner_ref = action.get("semantic_owner_ref")
    owner_scope = action.get("semantic_owner_scope")
    if not isinstance(owner_ref, str) or not owner_ref.strip():
        raise BridgeViolation("economy action semantic_owner_ref required")
    if not isinstance(owner_scope, str) or not owner_scope.strip():
        raise BridgeViolation("economy action semantic_owner_scope required")

    policy = action.get("call_policy", {})
    if not isinstance(policy, Mapping):
        raise BridgeViolation("economy action call_policy required")
    mode = policy.get("mode")
    requirement_class = str(
        policy.get("requirement_class")
        or ("QUALITY_REQUIRED" if mode == "EXTERNAL_REQUIRED" else "OPTIONAL_CONVENIENCE")
    ).strip().upper()
    required_capability = None
    acceptance_ref = decision.get("acceptance_ref")
    if requirement_class in {"CAPABILITY_REQUIRED", "QUALITY_REQUIRED"}:
        if not isinstance(acceptance_ref, str) or not acceptance_ref.strip():
            raise BridgeViolation("required economy decision acceptance_ref required")
    if requirement_class == "CAPABILITY_REQUIRED":
        required_capability = str(policy.get("required_capability") or "").strip().upper()
        if not required_capability:
            raise BridgeViolation("capability-required economy action missing required_capability")

    if verifier(decision, action, runtime) is not True:
        raise BridgeViolation("economy decision verification failed")

    evidence_ref = evidence_ref.strip()
    updated = deepcopy(dict(runtime))
    registry = updated.setdefault("economy_evidence_registry", {})
    if evidence_ref in registry:
        raise BridgeViolation("economy decision evidence_ref already exists")

    registry[evidence_ref] = {
        "decision_kind": decision_kind,
        "verified": True,
        "acceptance_state": "ACCEPTED",
        "source_status": "CURRENT",
        "authority_digest": authority_digest.strip(),
        "action_digest": stable_hash(dict(action)),
        "semantic_owner_ref": owner_ref.strip(),
        "semantic_owner_scope": owner_scope.strip(),
        "requirement_class": requirement_class,
        "required_capability": required_capability,
        "acceptance_ref": acceptance_ref.strip() if isinstance(acceptance_ref, str) else None,
        "source_or_artifact_ref": source_ref.strip(),
        "revision_or_hash": str(
            decision.get("revision_or_hash") or stable_hash(dict(decision))
        ),
        "verified_by": verifier_id.strip(),
        "decision_digest": stable_hash(dict(decision)),
    }
    return updated
