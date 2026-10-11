from pathlib import Path

ROOT = Path(r"D:\Git PWA\TAKY")
VISIBLE = ROOT / "TOOLS" / "TAKY_REMOTE_VISIBLE.ps1"
EXECUTOR = ROOT / "TOOLS" / "TAKY_RECEIPT_EXEC.py"


def test_remote_visible_has_no_raw_invoke_expression():
    text = VISIBLE.read_text(encoding="utf-8-sig")
    assert "Invoke-Expression" not in text
    assert "TAKY_RECEIPT_EXEC.py" in text
    assert "plan_json" in text
    assert "invocation_json" in text


def test_receipt_executor_uses_taky2_preflight_and_execute_and_stays_unverified():
    text = EXECUTOR.read_text(encoding="utf-8")
    assert '"TAKY2.orchestrator", "preflight"' in text
    assert '"TAKY2.orchestrator", "execute"' in text
    assert '"verification_state": "UNVERIFIED"' in text
    assert "receipt_id" in text
