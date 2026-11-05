#!/usr/bin/env python3
"""TAKY PR event watch (TAKY-001): read-only, single-pass GitHub PR observer.

One invocation fetches `gh pr view` + `gh pr checks` as JSON, compares the
observation against a bounded checkpoint file, atomically updates the checkpoint
and prints JSON events ONLY for meaningful transitions:
ci_failure, ci_recovered, review_needed, conflict,
merge_ready_for_human_review, merged, closed.

Hard limits: observer only. No push / merge / deploy / comment / label / any
GitHub mutation, no polling loop, no background watcher, no API key, no shell.
Anything unreadable or inconsistent fails closed as status=UNKNOWN (exit 3):
no synthetic green, no events, no checkpoint update.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "taky.pr_event_watch.v1"
FORBIDDEN_ACTIONS = ["push", "merge", "deploy", "github_mutation"]
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORK_ID_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}-[0-9]{1,6}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
STATES = ("OPEN", "CLOSED", "MERGED")
CI_VALUES = ("PASS", "FAIL", "PENDING", "NO_CHECKS")
BUCKETS = ("pass", "fail", "pending", "skipping", "cancel")
FLAG_KEYS = ("review_needed", "conflict", "merge_ready")
MAX_CHECKPOINT_BYTES = 65536
MAX_NAMES = 50
MAX_NAME_LEN = 200
GH_TIMEOUT_SECONDS = 60
STALE_LOCK_SECONDS = 600
ALLOWED_GH = (("pr", "view"), ("pr", "checks"))  # read-only subcommands only

ACTIONABLE = ("ci_failure", "ci_recovered", "review_needed", "conflict")
ACTIVE_STATUSES = ("NOT_STARTED", "DISCOVERY", "EVALUATION", "READY", "IMPLEMENTING")
MAX_PENDING = 16
TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

VIEW_FIELDS ="number,url,headRefOid,state,isDraft,mergeable,mergeStateStatus,reviewDecision"
CHECK_FIELDS = "name,bucket,state"


class Unknown(Exception):
    """Observation or state could not be trusted; fail closed."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _run_gh(args):
    """Run read-only gh; returns (rc|None, stdout, stderr). Never raises."""
    if tuple(args[:2]) not in ALLOWED_GH:
        raise Unknown("gh_subcommand_not_allowed")
    try:
        cp = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GH_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "", type(exc).__name__
    return cp.returncode, cp.stdout or "", (cp.stderr or "")[:200]


def _gh_json(args, ok_codes):
    rc, out, _err = _run_gh(args)
    if rc is None:
        raise Unknown("gh_unavailable")
    if rc not in ok_codes:
        raise Unknown("gh_exit_%s" % rc)
    try:
        return json.loads(out)
    except ValueError:
        raise Unknown("gh_json_malformed")


def _view(repo, pr):
    data = _gh_json(["pr", "view", str(pr), "--repo", repo, "--json", VIEW_FIELDS], (0,))
    if not isinstance(data, dict):
        raise Unknown("view_shape_invalid")
    return data


def _check_view(data, repo, pr):
    required = ("number", "url", "headRefOid", "state", "isDraft",
                "mergeable", "mergeStateStatus", "reviewDecision")
    if not isinstance(data, dict) or any(key not in data for key in required):
        raise Unknown("view_fields_missing")
    url = data["url"]
    if not isinstance(url, str):
        raise Unknown("identity_mismatch")
    try:
        parsed = urlsplit(url)
    except ValueError:
        raise Unknown("identity_mismatch")
    if (type(data["number"]) is not int or data["number"] != pr
            or parsed.scheme != "https" or parsed.netloc.lower() != "github.com"
            or parsed.path.casefold() != ("/%s/pull/%d" % (repo, pr)).casefold()
            or parsed.query or parsed.fragment):
        raise Unknown("identity_mismatch")
    head = data["headRefOid"]
    if not isinstance(head, str) or not SHA_RE.fullmatch(head):
        raise Unknown("head_sha_invalid")
    if (data["state"] not in STATES or type(data["isDraft"]) is not bool
            or not isinstance(data["mergeable"], str)
            or not isinstance(data["mergeStateStatus"], str)
            or data["reviewDecision"] not in ("", "APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED")):
        raise Unknown("view_fields_invalid")
    return head


def _classify_checks(checks):
    if not isinstance(checks, list):
        raise Unknown("checks_shape_invalid")
    pairs = []
    for item in checks:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) \
                or item.get("bucket") not in BUCKETS:
            raise Unknown("checks_entry_invalid")
        pairs.append((item["name"][:MAX_NAME_LEN], item["bucket"]))
    pairs.sort()
    failing = sorted({n for n, b in pairs if b in ("fail", "cancel")})[:MAX_NAMES]
    if not pairs:
        ci = "NO_CHECKS"  # zero checks is never PASS
    elif failing:
        ci = "FAIL"
    elif any(b == "pending" for _n, b in pairs):
        ci = "PENDING"
    else:
        ci = "PASS"
    return ci, failing, pairs


def observe(repo, pr):
    first = _view(repo, pr)
    head = _check_view(first, repo, pr)
    checks = _gh_json(["pr", "checks", str(pr), "--repo", repo, "--json", CHECK_FIELDS], (0, 1, 8))
    ci, failing, pairs = _classify_checks(checks)
    # Re-read to detect a head change between the two reads (stale CI data).
    second = _view(repo, pr)
    if _check_view(second, repo, pr) != head or second["state"] != first["state"]:
        raise Unknown("stale_head_during_read")
    if any(second[k] != first[k] for k in
           ("isDraft", "mergeable", "mergeStateStatus", "reviewDecision", "url")):
        raise Unknown("pr_metadata_changed_during_read")
    state = first["state"]
    draft = first["isDraft"]
    mergeable = first.get("mergeable") or ""
    merge_state = first.get("mergeStateStatus") or ""
    review = first.get("reviewDecision") or ""
    is_open = state == "OPEN"
    flags = {
        "review_needed": is_open and not draft and review in ("CHANGES_REQUESTED", "REVIEW_REQUIRED"),
        "conflict": is_open and mergeable == "CONFLICTING",
        "merge_ready": is_open and not draft and ci == "PASS" and mergeable == "MERGEABLE"
        and merge_state in ("CLEAN", "HAS_HOOKS") and review in ("", "APPROVED"),
    }
    return {
        "head_sha": head, "state": state, "draft": draft, "mergeable": mergeable,
        "merge_state": merge_state, "review": review, "ci": ci, "failing": failing,
        "flags": flags, "checks": pairs,
    }


def _snapshot_hash(ident, snap):
    body = dict(ident)
    body.update({k: snap[k] for k in ("head_sha", "state", "draft", "mergeable", "merge_state",
                                      "review", "ci", "failing", "flags", "checks")})
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_events(prev, snap):
    """Pure transition logic. prev is a validated checkpoint dict or None."""
    events = []
    if snap["state"] != "OPEN":
        if prev is None or prev["state"] != snap["state"]:
            events.append(("merged" if snap["state"] == "MERGED" else "closed", {}))
        return events
    prev_open = prev is not None and prev["state"] == "OPEN"
    same_head = prev_open and prev["head_sha"] == snap["head_sha"]
    seen = set(prev["failing"]) if same_head else set()
    new_fail = [n for n in snap["failing"] if n not in seen]
    if new_fail:
        events.append(("ci_failure", {"new_failing_checks": new_fail, "failing_checks": snap["failing"]}))
    if prev_open and prev["open_failure"] and snap["ci"] == "PASS":
        events.append(("ci_recovered", {}))
    names = {"review_needed": "review_needed", "conflict": "conflict",
             "merge_ready": "merge_ready_for_human_review"}
    for key in FLAG_KEYS:
        if snap["flags"][key] and not (prev_open and prev["flags"][key]):
            events.append((names[key], {}))
    return events


def _open_failure(prev, snap):
    if snap["state"] != "OPEN":
        return False
    if snap["ci"] == "FAIL":
        return True
    if snap["ci"] == "PASS":
        return False
    return bool(prev and prev["state"] == "OPEN" and prev["open_failure"])


def load_checkpoint(path, ident):
    if not os.path.exists(path):
        return None
    try:
        if os.path.getsize(path) > MAX_CHECKPOINT_BYTES:
            raise ValueError("too large")
        with open(path, "r", encoding="utf-8") as fh:
            cp = json.load(fh)
        ok = (
            isinstance(cp, dict) and cp.get("schema") == SCHEMA
            and isinstance(cp.get("snapshot_hash"), str)
            and isinstance(cp.get("head_sha"), str) and cp.get("state") in STATES
            and cp.get("ci") in CI_VALUES and isinstance(cp.get("open_failure"), bool)
            and isinstance(cp.get("failing"), list) and all(isinstance(n, str) for n in cp["failing"])
            and isinstance(cp.get("flags"), dict)
            and all(isinstance(cp["flags"].get(k), bool) for k in FLAG_KEYS)
        )
    except (OSError, ValueError):
        ok = False
    if not ok:
        raise Unknown("checkpoint_corrupt")
    if any(cp.get(k) != v for k, v in ident.items()):
        raise Unknown("checkpoint_identity_mismatch")
    if "pending" in cp:
        pend = cp["pending"]
        if (not isinstance(pend, list) or len(pend) > MAX_PENDING or not all(
                isinstance(p, dict) and set(p) == {"event", "snapshot_hash", "key"}
                and p["event"] in ACTIONABLE and isinstance(p["snapshot_hash"], str)
                and HEX64_RE.match(p["snapshot_hash"])
                and p["key"] == _event_key(p["snapshot_hash"], p["event"]) for p in pend)):
            raise Unknown("checkpoint_pending_corrupt")
    return cp


def write_checkpoint(path, cp):
    """Atomic write: temp file in same dir, fsync, os.replace."""
    directory = os.path.dirname(os.path.abspath(path))
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".prwatch-", suffix=".tmp", dir=directory)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cp, fh, sort_keys=True, separators=(",", ":"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    except OSError:
        raise Unknown("state_write_failed")
    finally:
        if tmp is not None:
            try:
                os.remove(tmp)
            except OSError:
                pass


class _Lock:
    """Windows kernel-backed byte lock; released on process exit, never stale-unlinked.

    A permanent sidecar inode prevents an old waiter from unlinking a newer
    owner's lock. Only one process can own the locked byte at a time.
    """

    def __init__(self, state_path):
        self.path = state_path + ".lock"
        self.fd = None

    def __enter__(self):
        if os.name != "nt":
            raise Unknown("platform_lock_unavailable")
        import msvcrt
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_BINARY, 0o600)
            self.fd = fd
            if os.fstat(fd).st_size == 0:
                os.write(fd, b"0")
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except OSError:
                raise Unknown("state_locked")
            return self
        except Unknown:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
            raise
        except OSError:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
            raise Unknown("state_lock_failed")

    def __exit__(self, *_exc):
        if self.fd is not None:
            import msvcrt
            try:
                os.lseek(self.fd, 0, os.SEEK_SET)
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
            finally:
                os.close(self.fd)
                self.fd = None


def _event_key(digest, kind):
    return hashlib.sha256(("%s:%s" % (digest, kind)).encode("utf-8")).hexdigest()[:16]


def _registered_gate(work_id, repo, pr):
    """Read the canonical task register; return (ok, reason). Never infers binding."""
    try:
        if str(TOOLS_DIR) not in sys.path:
            sys.path.insert(0, str(TOOLS_DIR))
        from TAKY_ORCHESTRATION_ADVANCE import DEFAULT_BOARD
        board_path = DEFAULT_BOARD.resolve(strict=True)
        if board_path.stat().st_size > 4 * 1024 * 1024:
            return False, "board_untrusted"
        with open(board_path, "r", encoding="utf-8") as fh:
            board = json.load(fh)
    except Exception:  # any import/read failure fails closed to HOLD
        return False, "board_unavailable"
    return _gate_row(board, work_id, repo, pr)


def _gate_row(board, work_id, repo, pr):
    rows = board.get("tasks") if isinstance(board, dict) else None
    if not isinstance(rows, list):
        return False, "board_untrusted"
    match = [r for r in rows if isinstance(r, dict) and r.get("id") == work_id]
    if len(match) != 1:
        return False, "work_id_not_unique_in_register"
    row = match[0]
    if row.get("status") not in ACTIVE_STATUSES:
        return False, "work_not_active"
    if row.get("approval_required") is not False:
        return False, "approval_required"
    binding = row.get("github_pr")
    if (not isinstance(binding, dict) or set(binding) != {"repo", "pr"}
            or binding["repo"] != repo or type(binding["pr"]) is not int or binding["pr"] != pr):
        return False, "github_pr_binding_absent_or_conflicting"
    deps = row.get("dependencies", [])
    if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps):
        return False, "dependencies_invalid"
    return True, list(deps)


def _engine_dispatch(work_id, deps, key):
    """Invoke ONLY the existing canonical registered-queue engine, once."""
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from ENFORCEMENT.taky_registered_goal_queue import execute_registered_queue
    doc = {"schema": "TAKY_GOAL_QUEUE_V2", "queue_id": "prwatch-%s-%s" % (work_id, key),
           "items": [{"work_id": work_id, "depends_on": deps}]}
    return execute_registered_queue(doc, ROOT_DIR, ROOT_DIR / ".local")


def _dispatch_pending(cp, work_id, repo, pr):
    """Returns (info, remaining_pending). Pending is cleared only after the engine answered."""
    pending = cp.get("pending", [])
    if cp["state"] != "OPEN":
        return {"status": "DROPPED_PR_NOT_OPEN", "dispatch_calls": 0}, []
    if not pending:
        return {"status": "NONE_PENDING", "dispatch_calls": 0}, []
    # Old-head events are preserved for reconciliation, but cannot wake current work.
    current = next((p for p in pending if p["snapshot_hash"] == cp["snapshot_hash"]), None)
    if current is None:
        return {"status": "STALE_PENDING_HOLD", "dispatch_calls": 0,
                "pending_count": len(pending)}, pending
    ok, deps = _registered_gate(work_id, repo, pr)
    if not ok:
        return {"status": "HOLD", "reason": deps, "dispatch_calls": 0}, pending
    try:
        res = _engine_dispatch(work_id, deps, current["key"])
    except Exception as exc:  # uncertain: keep pending; engine's durable claim guards replay
        return {"status": "DISPATCH_ERROR", "reason": type(exc).__name__, "dispatch_calls": 1}, pending
    status = res.get("status") if isinstance(res, dict) else None
    if not isinstance(res, dict) or (isinstance(status, str) and status.startswith("QUEUE_V2_")):
        # engine rejected before any claim: nothing started, safe to keep and replay
        return {"status": "ENGINE_REJECTED", "engine_status": status, "dispatch_calls": 1}, pending
    if not _ack_ok(res, work_id):
        # deferred / missing receipt / wrong item: not an ACK; hold, retry only on a later invocation
        return {"status": "ENGINE_RESULT_NOT_ACKED", "engine_status": status,
                "dispatch_calls": 1}, pending
    return {"status": "DISPATCHED_OBSERVATION_NOT_DONE", "engine_result": res,
            "dispatch_calls": 1}, [p for p in pending if p["key"] != current["key"]]


def _receipt_durable(ref, expected):
    """An ACK needs the exact queue receipt bytes, not merely a file at the right path."""
    if not isinstance(ref, str) or not re.fullmatch(r"\.local[\\/]taky-goal-queue-[0-9a-f]{32}\.json", ref):
        return False
    try:
        local = (ROOT_DIR / ".local").resolve(strict=True)
        candidate = ROOT_DIR / ref
        if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
            return False
        file = candidate.resolve(strict=True)
        if file.parent != local or not file.is_file() or not 0 < file.stat().st_size <= 1000000:
            return False
        recorded = json.loads(file.read_text(encoding="utf-8"))
        return recorded == {k: v for k, v in expected.items() if k != "local_queue_receipt"}
    except (OSError, UnicodeError, ValueError, TypeError):
        return False


def _ack_ok(res, work_id):
    """ACK only an exact single-item observation with a durable receipt and an accepted item status."""
    if res.get("schema") != "TAKY_GOAL_QUEUE_OBSERVATION_V2":
        return False
    if res.get("status") != "REGISTERED_LOCAL_TASKS_OBSERVED":
        return False
    if res.get("items_total") != 1 or res.get("items_deferred") != 0 or res.get("deferred_work_ids") != []:
        return False
    items = res.get("items")
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
        return False
    item = items[0]
    if item.get("work_id") != work_id or item.get("status") not in (
            "LOCAL_DIAGNOSIS_EVIDENCED_NOT_DONE", "REUSED_CANONICAL_LOCAL_EVIDENCE"):
        return False
    return _receipt_durable(res.get("local_queue_receipt"), res)


def run_once(repo, pr, work_id, state_file, resume_registered_local=False):
    ident = {"work_id": work_id, "repo": repo, "pr": pr}
    dispatch = None
    with _Lock(state_file):
        prev = load_checkpoint(state_file, ident)
        snap = observe(repo, pr)
        digest = _snapshot_hash(ident, snap)
        events = compute_events(prev, snap)
        pending = list(prev.get("pending", [])) if prev else []
        if resume_registered_local:
            have = {p["key"] for p in pending}
            for kind, _d in events:
                if kind in ACTIONABLE and _event_key(digest, kind) not in have:
                    pending.append({"event": kind, "snapshot_hash": digest,
                                    "key": _event_key(digest, kind)})
            if len(pending) > MAX_PENDING:
                raise Unknown("pending_overflow")
        changed = prev is None or prev["snapshot_hash"] != digest
        if changed or (resume_registered_local and pending != (prev or {}).get("pending", [])):
            cp = dict(ident)
            cp.update({
                "schema": SCHEMA, "snapshot_hash": digest, "head_sha": snap["head_sha"],
                "state": snap["state"], "ci": snap["ci"], "failing": snap["failing"],
                "open_failure": _open_failure(prev, snap), "flags": snap["flags"],
                "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            if pending:  # preserved even when the flag is off (default run never dispatches)
                cp["pending"] = pending
            write_checkpoint(state_file, cp)  # persist BEFORE emitting/dispatching
            prev_cp = cp
        else:
            prev_cp = prev
        if resume_registered_local:
            dispatch, left = _dispatch_pending(prev_cp, work_id, repo, pr)
            if left != prev_cp.get("pending", []):
                cp = {k: v for k, v in prev_cp.items() if k != "pending"}
                if left:
                    cp["pending"] = left
                write_checkpoint(state_file, cp)
    out = []
    for kind, detail in events:
        ev = {"event": kind, "idempotency_key": _event_key(digest, kind)}
        ev.update(detail)
        out.append(ev)
    result = {
        "schema": SCHEMA, "status": "OK", "work_id": work_id, "repo": repo, "pr": pr,
        "head_sha": snap["head_sha"], "pr_state": snap["state"], "ci": snap["ci"],
        "snapshot_hash": digest, "events": out, "forbidden_actions": FORBIDDEN_ACTIONS,
    }
    if dispatch is not None:
        result["registered_dispatch"] = dispatch
    return result


def _positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer")
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _repo(text):
    if not REPO_RE.match(text):
        raise argparse.ArgumentTypeError("must be owner/name")
    return text


def _work_id(text):
    if not WORK_ID_RE.match(text):
        raise argparse.ArgumentTypeError("must look like TAKY-001")
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description="TAKY read-only PR event observer (single pass).")
    parser.add_argument("--repo", required=True, type=_repo)
    parser.add_argument("--pr", required=True, type=_positive_int)
    parser.add_argument("--work-id", required=True, type=_work_id)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--resume-registered-local", action="store_true",
                        help="opt-in: hand actionable events to the canonical registered queue "
                             "engine, only for a work-id with explicit github_pr binding")
    args = parser.parse_args(argv)
    try:
        result = run_once(args.repo, args.pr, args.work_id, args.state_file,
                          args.resume_registered_local)
        code = 0
    except Unknown as exc:
        result = {
            "schema": SCHEMA, "status": "UNKNOWN", "reason": exc.reason, "work_id": args.work_id,
            "repo": args.repo, "pr": args.pr, "events": [], "forbidden_actions": FORBIDDEN_ACTIONS,
        }
        code = 3
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
