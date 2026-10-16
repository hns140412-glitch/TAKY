#!/usr/bin/env python3
"""Offline acceptance tests for detached provider adapter: mocks, no model calls."""
import os,sys,json,tempfile
from pathlib import Path
from types import SimpleNamespace
import taky_antigravity_bridge_v3_candidate as b
import TAKY_CLI_DETACHED_E2E_CANDIDATE as cli

with tempfile.TemporaryDirectory(prefix="TAKY_DETACHED_CLI_TEST_") as folder:
    root=Path(folder)
    b.MAILBOX=root/"mailbox"
    b.HOST_KEY=root/"key.bin"
    b.WORKER_LOCK=root/"worker.lock"
    cli.CLAIM_DIR=root/"claims"
    cli.OUT=root/"receipts"
    cli.CLAUDE=Path(sys.executable)
    assert cli.CODEX_SHIM.is_file()
    cases=[]
    for actor in ("CLAUDE","CODEX"):
        staged=b.stage(SimpleNamespace(actor=actor,project="TAKY2",intent="Read only integration acceptance token"))
        cases.append((actor,staged["task_id"]))
    assert b.worker_once()["new_receipts"]==2
    calls=[]
    def simulated_run(command,**kwargs):
        agent="CLAUDE" if command[0]==sys.executable else "CODEX"
        required="TAKY_"+agent+"_"+(cases[0][1] if agent=="CLAUDE" else cases[1][1])[:8].upper()+"_PASS"
        calls.append((agent,kwargs.get("timeout"),kwargs.get("cwd")))
        if agent=="CLAUDE":
            stdout=json.dumps({"result":required,"session_id":"test-only","is_error":False})
        else:
            stdout="\n".join([
                json.dumps({"type":"thread.started","thread_id":"mock-codex-session"}),
                json.dumps({"type":"item.completed","item":{"type":"agent_message","text":required}}),
                json.dumps({"type":"turn.completed","turn":{"status":"completed"}})
            ])
        assert "OPENAI_API_KEY" not in kwargs["env"]
        assert "ANTHROPIC_API_KEY" not in kwargs["env"]
        return SimpleNamespace(returncode=0,stdout=stdout,stderr="")
    cli.subprocess=SimpleNamespace(run=simulated_run,CREATE_NO_WINDOW=0)
    for actor,task_id in cases:
        expected="TAKY_"+actor+"_"+task_id[:8].upper()+"_PASS"
        pre=cli.invoke(task_id,expected,False)
        assert pre["status"]=="PREPARED_NOT_EXECUTED" and not pre["model_called"]
        os.environ.pop("TAKY_USER_EXPLICIT_AUTHORIZATION",None)
        os.environ.pop("TAKY_CLI_DETACHED_MODE",None)
        try:
            cli.invoke(task_id,expected,True)
            raise AssertionError("UNAUTHORIZED_EXECUTION_WAS_ALLOWED")
        except RuntimeError as e:
            assert str(e)=="USER_EXECUTION_AUTHORIZATION_REQUIRED"
        assert not (cli.CLAIM_DIR/(task_id+".json")).exists()
        os.environ["TAKY_USER_EXPLICIT_AUTHORIZATION"]="1"
        os.environ["TAKY_CLI_DETACHED_MODE"]="ACK_SEPARATE_SESSION"
        result=cli.invoke(task_id,expected,True)
        assert result["status"]=="EXECUTED_E2E_REPLY_VERIFIED"
        assert result["verified_expected_reply"]
        assert result["session_mode"]=="NEW_DETACHED_CLI_NOT_IDE_PANEL"
        assert (cli.CLAIM_DIR/(task_id+".json")).exists()
        assert (cli.OUT/(task_id+".json")).exists()
        saved=json.loads((cli.OUT/(task_id+".json")).read_text(encoding="utf-8"))
        digest=b.digest(b.canonical({k:v for k,v in saved.items() if k not in ("receipt_sha256","receipt_mac")}))
        assert saved["receipt_sha256"]==digest
        assert saved["receipt_mac"]==b.mac(digest)
        try:
            cli.invoke(task_id,expected,True)
            raise AssertionError("REPLAY_EXECUTION_WAS_ALLOWED")
        except RuntimeError as e:
            assert str(e)=="FINAL_RECEIPT_EXISTS_NO_REPEAT"
        os.environ.pop("TAKY_USER_EXPLICIT_AUTHORIZATION",None)
        os.environ.pop("TAKY_CLI_DETACHED_MODE",None)
    assert len(calls)==2, calls
print("TAKY_DETACHED_CLI_GATE_OFFLINE_PASS 2_PROVIDERS AUTH_AND_REPLAY_NO_MODEL_CALL")
