"""Synthetic regression: CLN-001 audit/apply-safe contract vs static scanner exit codes.

No production path is touched: scanner and every mutating helper are mocked.
Run: python TOOLS/TAKY_WORKSPACE_CLEANUP_audit_decoupling_test.py
"""
import contextlib, importlib.util, io, json, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "cleanup", Path(__file__).with_name("TAKY_WORKSPACE_CLEANUP.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def scan(status, missing=0, unver=0, drift=0, apps=6):
    return json.dumps({"status": status, "apps_checked": apps, "source_files_checked": 320,
                       "missing_file_count": missing, "git_unversioned_count": unver,
                       "head_worktree_source_drift_count": drift})

def gate(code, out, err=""):
    return m.static_source_gate(lambda: (code, out, err))

def raises(fn):
    try:
        fn()
    except RuntimeError as exc:
        return str(exc)
    raise AssertionError("expected RuntimeError")

# 1. exit 0 PASS_STATIC_ONLY (plain and real-guard suffixed) -> no hold.
for st in ("PASS_STATIC_ONLY", "PASS_STATIC_ONLY_HEAD_BROWSER_NOT_PROVEN"):
    g = gate(0, scan(st))
    assert g["head_replay_hold"] is False and g["binary_runtime_ui_verified"] is False, g

# 2. exit 3 HEAD replay hold, 0 missing/unversioned -> structured HOLD with counts.
g = gate(3, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", drift=62))
assert g["head_replay_hold"] is True and g["head_replay"] == "HEAD_REPLAY_NOT_PROVEN"
assert g["static_dependencies"] == "STATIC_DEPENDENCIES_PRESERVED"
assert g["head_worktree_source_drift_count"] == 62 and g["source_files_checked"] == 320

# 3. fatal data stays ERROR, never PASS/HOLD.
bad = [
    (2, scan("BLOCK", missing=1)),
    (2, scan("BLOCK", unver=2)),
    (3, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", unver=1, drift=62)),
    (3, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", missing=1, drift=62)),
    (3, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", drift=62, apps=5)),
    (3, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", drift=0)),   # hold without drift
    (0, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", drift=62)),  # exit/status mismatch
    (0, scan("PASS_STATIC_ONLY", drift=3)),                        # pass but drift
    (2, "not json"), (3, ""), (0, "[]"),
]
for code, out in bad:
    assert raises(lambda: gate(code, out)).startswith("APP_STATIC_TRANSITIVE_SOURCE_GATE"), (code, out)

# 4. main(): --audit / --apply-safe contract with mocked audit and mutators.
def fake_audit(hold, converged=True):
    proof = gate(3, scan("WORKTREE_STATIC_PASS_HEAD_REPLAY_HOLD", drift=62)) if hold \
        else gate(0, scan("PASS_STATIC_ONLY"))
    return {"mode": "READONLY", "global_cleanup_complete": False,
            "completion_scope": "HISTORICAL_RELOCATION_CHECKS_ONLY",
            "git_stale": {"X": {"registered": 1, "dangling": [] if converged else [{"path": "p"}]}},
            "audio": {"status": "ALREADY_MOVED"},
            "empty_candidates": [{"present": False}],
            "global_custody_gates": {"runtime_static_dependency_proof": proof},
            "custody_status": "PARTIAL_CUSTODY_HOLD" if hold else "STATIC_CUSTODY_PASS_NOT_COMPLETE",
            "source_gate_hold": hold}

mutations = []
def boom(name):
    def f(*a, **k):
        mutations.append(name)
        raise AssertionError("mutation attempted: " + name)
    return f
for name in ("backup_and_prune", "move_audio", "remove_empty", "update_refs"):
    setattr(m, name, boom(name))
m.RECEIPT = type("R", (), {"parent": type("P", (), {"mkdir": boom("mkdir")})(),
                           "write_text": boom("receipt")})()

def run(flag, audit_fn):
    m.audit = audit_fn
    sys.argv = ["x", flag]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = m.main()
    return rc, json.loads(buf.getvalue())

rc, out = run("--audit", lambda: fake_audit(True))
assert rc == 0 and out["custody_status"] == "PARTIAL_CUSTODY_HOLD" and out["global_cleanup_complete"] is False
rc, out = run("--audit", lambda: fake_audit(False))
assert rc == 0 and out["global_cleanup_complete"] is False

# apply-safe with hold: fail closed, even when historically converged AND when not.
for conv in (True, False):
    rc, out = run("--apply-safe", lambda c=conv: fake_audit(True, c))
    assert rc == 3 and out["status"] == "HOLD_SOURCE_GATE_NO_MUTATION", out
    assert out["historical_convergence_noop"] is conv
    assert out["global_cleanup_complete"] is False and out["paths_moved"] == 0
    assert out["receipt_written"] is False and out["deployment_allowed"] is False

# apply-safe on clean converged gate -> idempotent no-op, still not global completion.
rc, out = run("--apply-safe", lambda: fake_audit(False))
assert rc == 0 and out["status"] == "ALREADY_CONVERGED_NO_MUTATION" and out["global_cleanup_complete"] is False

# fatal audit failure -> structured ERROR_HOLD in both modes, exit non-zero, no mutation.
def fatal():
    raise RuntimeError("APP_STATIC_TRANSITIVE_SOURCE_GATE_DRIFT:exit=2:status=BLOCK")
for flag in ("--audit", "--apply-safe"):
    rc, out = run(flag, fatal)
    assert rc == 2 and out["status"] == "ERROR_HOLD" and out["mutation_performed"] is False

assert not mutations, mutations
print("TAKY_WORKSPACE_CLEANUP_audit_decoupling_test: PASS")
