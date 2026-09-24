import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "local_drive_workspace.py"
CHECKPOINT = ROOT / "execution_checkpoint.py"

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp) / "TAKY"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--root", str(base)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)

    d = subprocess.run(
        [sys.executable, str(SCRIPT), "doctor", "--root", str(base)],
        capture_output=True,
        text=True,
    )
    assert d.returncode == 0, (d.stdout, d.stderr)
    result = json.loads(d.stdout)
    assert result["pass"]

    record = base / "checkpoint.json"
    record.write_text(json.dumps({
        "checkpoint_version": "1.0",
        "task_id": "LOCAL_TEST",
        "namespace": "TEST",
        "atomic_unit": "UNIT-001",
        "status": "RUNNING",
        "done": ["UNIT-001"],
        "open": [],
        "next": "UNIT-002",
        "corrections": [],
        "source_refs": ["LOCAL_TEST"],
        "updated_at": "2026-09-24T15:00:00+09:00"
    }), encoding="utf-8")

    env = dict(os.environ)
    env["TAKY_STATE_ROOT"] = str(base)
    w = subprocess.run(
        [sys.executable, str(CHECKPOINT), "write", "--record", str(record), "--repo-root", str(base / "repos")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert w.returncode == 0, (w.stdout, w.stderr)
    written = json.loads(w.stdout)
    assert written["state_root"] == str(base.resolve())

    current = base / "CURRENT" / "TEST" / "LOCAL_TEST.json"
    assert current.exists()

    g = subprocess.run(
        [sys.executable, str(CHECKPOINT), "guard", "--namespace", "TEST", "--task-id", "LOCAL_TEST", "--expected-atomic-unit", "UNIT-001"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert g.returncode == 0, (g.stdout, g.stderr)

print("local_drive_workspace: PASS")
