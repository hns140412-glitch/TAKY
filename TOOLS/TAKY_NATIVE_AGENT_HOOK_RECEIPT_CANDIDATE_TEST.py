#!/usr/bin/env python3
"""Offline test for signed hook metadata; no actual model session or live ACK."""
import json,pathlib,tempfile
import TAKY_NATIVE_AGENT_HOOK_RECEIPT_CANDIDATE as h
import taky_antigravity_bridge_v3_candidate as b
TASKS={"CLAUDE":"fbc544e8b18342df929ed0287454cd53",
       "CODEX":"336cab100f824164aa7c33f60f962bd1"}
with tempfile.TemporaryDirectory(prefix="TAKY_AGENT_HOOK_TEST_") as d:
    dest=pathlib.Path(d)
    for provider,taskid in TASKS.items():
        data={"hook_event_name":"UserPromptSubmit",
              "cwd":str(b.ALLOWED["TAKY2"]),"session_id":"mock-session-12345",
              "prompt":"Please inspect the signed envelope. TAKY_TASK_ID="+taskid+"\nSensitive phrase XYZ",
              "_taky_installed_provider":provider}
        result=h.on_prompt(data,dest)
        assert result["state"]=="HOOK_SUBMIT_METADATA_SIGNED",result
        receipt=list((dest/provider).glob("*.json"))
        assert len(receipt)==1
        obj=json.loads(receipt[0].read_text(encoding="utf-8"))
        assert obj["actual_model_completed"] is False
        assert obj["native_panel_binding_verified"] is False
        assert obj["current_ack_cursor_advanced"] is False
        assert obj["session_id_sha256"] and obj["task_id"]==taskid
        assert "Sensitive phrase XYZ" not in receipt[0].read_text(encoding="utf-8")
        assert h.on_prompt(data,dest)["state"]=="HOOK_RECEIPT_ALREADY_PRESENT"
        assert h.on_prompt({**data,"_taky_installed_provider":"CODEX" if provider=="CLAUDE" else "CLAUDE"},dest)["state"]=="IGNORED_WRONG_PROVIDER"
        assert h.on_prompt({**data,"cwd":str(pathlib.Path(d))},dest)["state"]=="IGNORED_OTHER_REPO"
        assert h.on_prompt({**data,"prompt":"Hello without task ID"},dest)["state"]=="IGNORED_NO_TASK_MARKER"
        assert h.on_prompt({**data,"session_id":""},dest)["state"]=="IGNORED_NO_SESSION"
    assert list(dest.rglob("*.json"))
print("TAKY_NATIVE_HOOK_OFFLINE_QA_PASS providers=2 metadata_only=1 no_model_call=1")
