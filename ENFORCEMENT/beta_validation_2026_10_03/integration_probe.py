"""Local-only Beta probes; fixture state stays beside this evidence script."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ENFORCEMENT"))
from execution_checkpoint import checkpoint_hash, guard, persist
from preflight_bridge import run


def main():
    results = {}
    # Refresh only this in-memory probe's seed hash, not repository evidence.
    base = json.loads((ROOT / "ENFORCEMENT/fixtures/preflight_evidence_pass.json").read_text(encoding="utf-8"))
    seed = base["applicable_rule_refs"][0]
    seed["sha256"] = hashlib.sha256((ROOT / seed["path"]).read_bytes()).hexdigest()
    results["preflight_control"] = run(base, ROOT)
    assert results["preflight_control"]["pass"], results
    base["history_query_refs"] = [{
        "source_kind": "repo_file", "source_id": "not-history",
        "path": "HISTORY/../TAKY.md",
        "sha256": hashlib.sha256((ROOT / "TAKY.md").read_bytes()).hexdigest(),
    }]
    results["preflight_traversal"] = run(base, ROOT)
    assert not results["preflight_traversal"]["pass"], results
    assert any("HISTORY_PATH_OUTSIDE_CANONICAL_HISTORY" in x for x in results["preflight_traversal"]["detected"])

    state_root = Path(__file__).resolve().parent / "checkpoint_probe"
    record = {
        "checkpoint_version": "1.0", "task_id": "BETA_PROBE", "namespace": "TEST",
        "atomic_unit": "probe", "status": "RUNNING", "done": [], "open": [],
        "next": "review", "corrections": [], "source_refs": ["local-probe"],
        "updated_at": "2026-10-03T00:00:00Z",
    }
    results["persist"] = persist(record, state_root)
    assert results["persist"]["pass"], results
    results["guard_control"] = guard(state_root, "TEST", "BETA_PROBE")
    assert results["guard_control"]["pass"], results
    current = Path(results["persist"]["current_path"])
    record["task_id"] = "OTHER_TASK"
    record["namespace"] = "OTHER_OWNER"
    record["checkpoint_hash"] = checkpoint_hash(record)
    current.write_text(json.dumps(record), encoding="utf-8")
    results["guard_wrong_identity"] = guard(state_root, "TEST", "BETA_PROBE")
    assert not results["guard_wrong_identity"]["pass"], results
    assert set(results["guard_wrong_identity"]["detected"]) == {
        "CURRENT_CHECKPOINT_TASK_ID_MISMATCH", "CURRENT_CHECKPOINT_NAMESPACE_MISMATCH"
    }, results
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
