import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from execution_checkpoint import guard, persist


def record(unit: str, updated_at: str, *, next_unit: str | None = "NEXT") -> dict:
    return {
        "checkpoint_version": "1.0",
        "task_id": "TEST_TASK",
        "namespace": "TEST",
        "atomic_unit": unit,
        "status": "RUNNING",
        "done": [f"{unit} done"],
        "open": [],
        "next": next_unit,
        "corrections": [],
        "source_refs": ["TEST_SOURCE"],
        "updated_at": updated_at,
    }


with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)

    first = record("UNIT-001", "2026-09-24T14:00:00+09:00")
    result = persist(first, repo)
    assert result["pass"], result
    current = repo / "CURRENT" / "TEST" / "TEST_TASK.json"
    assert current.exists()
    assert guard(repo, "TEST", "TEST_TASK", "UNIT-001")["pass"]
    stale = guard(repo, "TEST", "TEST_TASK", "UNIT-000")
    assert not stale["pass"]
    assert "CURRENT_CHECKPOINT_STALE_OR_WRONG_UNIT" in stale["detected"]

    # Replaying identical immutable history is idempotent.
    repeat = persist(first, repo)
    assert repeat["pass"], repeat

    # Same history identity with different content must fail and must not
    # mutate CURRENT.
    before = current.read_text(encoding="utf-8")
    conflict = record("UNIT-001", "2026-09-24T14:00:00+09:00", next_unit="DIFFERENT")
    blocked = persist(conflict, repo)
    assert not blocked["pass"], blocked
    assert "HISTORY_IMMUTABILITY_CONFLICT" in blocked["detected"]
    assert current.read_text(encoding="utf-8") == before

    second = record("UNIT-002", "2026-09-24T14:05:00+09:00")
    advanced = persist(second, repo)
    assert advanced["pass"], advanced
    assert guard(repo, "TEST", "TEST_TASK", "UNIT-002")["pass"]

print("execution_checkpoint: PASS")
