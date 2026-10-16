#!/usr/bin/env python3
"""Isolated regression of TAKY shared-context delta. NO MODELS, NO CANONICAL WRITES."""
import json,tempfile
from pathlib import Path
import taky_antigravity_bridge_v3_candidate as b
import TAKY_SHARED_CONTEXT_DELTA_CANDIDATE as delta
def save(file,obj):
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(obj),encoding="utf-8")
with tempfile.TemporaryDirectory(prefix="TAKY_DELTA_QA_") as tmp:
    root=Path(tmp)
    b.HOST_KEY=root/"key.bin"
    b.LOCAL_BRIDGE_DIR=root/"local"
    src=root/"provenance"
    original=json.dumps({"task_id":delta.SOURCE_ID,"status":"EXECUTED_E2E_REPLY_VERIFIED"}).encode()
    p=src/(delta.SOURCE_ID+".json");p.parent.mkdir(parents=True);p.write_bytes(original)
    a={"status":"E2E_RESPONSE_AND_REQUEST_BOUND_PASS","source_receipt_sha256":delta.sha(original),
       "agent":"CLAUDE","source_task_id":delta.SOURCE_ID}
    b.seal_receipt(a)
    save(src/(delta.SOURCE_ID+".attestation.json"),a)
    current=root/"derived.json"
    save(current,{"authority_status":"DERIVED_NON_AUTHORITY","status":"CANDIDATE"})
    d=delta.Delta(root/"candidate",current,src)
    assert d.seed()["status"]=="APPENDED"
    assert d.seed()["status"]=="ALREADY_PRESENT"
    assert len(d.events())==1
    deliveries={}
    for actor in ("CLAUDE","CODEX"):
        info=d.delivery(actor)
        assert info["status"]=="PREPARED_NOT_DELIVERED_TO_PROVIDER" and info["unread_count"]==1
        assert d.delivery(actor)["status"]=="ALREADY_PREPARED"
        assert d.cursor(actor)==0
        packet=delta.read(Path(info["file"]))
        assert delta.signed(packet) and packet["current"]["status"]=="DERIVED_NON_AUTHORITY"
        ack={"actor":actor,"delivery_id":packet["delivery_id"],
             "current_sha256":packet["current"]["sha256"],
             "event_ids":packet["event_ids"],"event_seq_end":packet["event_seq_end"]}
        assert d.validate_ack(packet,ack,simulation=False)=="RECEIVER_PROVIDER_PROOF_UNVERIFIED"
        assert d.validate_ack(packet,ack,proof={"provider_binding_verified":True,"delivery_id":packet["delivery_id"]},simulation=False)=="RECEIVER_PROVIDER_PROOF_UNVERIFIED"
        wrong=dict(ack,event_ids=["INVALID"])
        assert d.validate_ack(packet,wrong,simulation=True)=="ACK_CONTEXT_OR_EVENTS_MISMATCH"
        deliveries[actor]=(packet,ack)
    claude_ack=deliveries["CLAUDE"][1]
    assert d.simulation_ack("CLAUDE",claude_ack)["status"]=="SIMULATED_ACK_PASS_NOT_REAL_DELIVERY"
    assert d.cursor("CLAUDE")==1 and d.cursor("CODEX")==0
    cursorfile=root/"candidate"/"cursors"/"CLAUDE.json"
    signedcursor=cursorfile.read_bytes()
    forgedcursor=delta.read(cursorfile);forgedcursor["last_ack_seq"]=987
    save(cursorfile,forgedcursor)
    try:
        d.cursor("CLAUDE")
        raise AssertionError("FORGED_CURSOR_ACCEPTED")
    except RuntimeError as e:assert str(e)=="CURSOR_SIGNATURE_INVALID"
    cursorfile.write_bytes(signedcursor)
    assert d.cursor("CLAUDE")==1
    assert d.simulation_ack("CLAUDE",claude_ack)["error"]=="POINTER_ALREADY_ADVANCED"
    assert d.delivery("CLAUDE")["status"]=="NO_UNREAD_EVENTS"
    assert d.delivery("CODEX")["status"]=="ALREADY_PREPARED"
    # Tampered delivery must fail its sender signature.
    p=root/"candidate"/"deliveries"/"CODEX"/(deliveries["CODEX"][0]["delivery_id"]+".json")
    doc=delta.read(p);doc["event_ids"]=["FORGED"];save(p,doc)
    assert d.simulation_ack("CODEX",deliveries["CODEX"][1])["error"]=="DELIVERY_SIGNATURE_INVALID"
    assert d.cursor("CODEX")==0
    # Main/real namespace cannot use simulated ACKs, even with valid values.
    main=delta.Delta()
    assert main.simulation_ack("CLAUDE",claude_ack)["status"]=="HOLD_REAL_PROVIDER_ACK_REQUIRED"
    # Controlled CLI integration tests: mocks only, never run a real subscription CLI.
    import shutil
    import TAKY_SHARED_CONTEXT_CLI_RECEIVER_CANDIDATE as receiver
    # Regression: live TAKY2 CODEX_VERIFY_ONLY must use method_or_tool=codex.
    wrapper=(Path(__file__).parent/"TAKY_MODEL_REVIEW.ps1").read_text(encoding="utf-8-sig")
    assert "$routeTool='codex'" in wrapper
    assert "$routeTool='codex-ephemeral'" not in wrapper
    assert "TAKY_PREFLIGHT_BOUNDED.py" in wrapper
    import TAKY_PREFLIGHT_BOUNDED as supervisor
    task_id="external-review-"+"a"*32
    rid="pf:"+task_id+":"+"b"*16
    fake_runtime={
        "preflight_receipts":{rid:{"task_id":task_id,"call_allowed":True}},
        "execution_calls":{},
        "active_attempts":{"route_x":{"receipt_id":rid,"status":"PENDING"}}
    }
    assert supervisor.releasable_preinvoke(fake_runtime,task_id)==rid
    fake_runtime["execution_calls"][rid]={"status":"CALLING"}
    assert supervisor.releasable_preinvoke(fake_runtime,task_id) is None
    del fake_runtime["execution_calls"][rid]
    fake_runtime["active_attempts"]["route_x"]["status"]="CALLING"
    assert supervisor.releasable_preinvoke(fake_runtime,task_id) is None
    # Exercise the real preflight timeout handler using a synthetic runner.
    # No canonical runtime mutation, model call or live provider access.
    from unittest.mock import patch as mock_patch
    import subprocess
    plan_path=root/"bounded_plan.json"
    plan_path.write_text(json.dumps({"task_id":task_id}),encoding="utf-8")
    def forced_timeout(argv,**kwargs):
        assert argv[3:5]==["TAKY2.orchestrator","preflight"]
        assert kwargs["timeout"]==supervisor.PREFLIGHT_TIMEOUT
        raise subprocess.TimeoutExpired(argv,kwargs["timeout"])
    with mock_patch.object(supervisor,"safe_release",return_value="PREINVOKE_RELEASED") as release_mock:
        assert supervisor.run(plan_path,runner=forced_timeout)==124
        release_mock.assert_called_once()
    def forced_success(argv,**kwargs):
        assert kwargs["shell"] is False
        return subprocess.CompletedProcess(argv,0,stdout='{"allowed":false,"mode":"HOLD"}\\n',stderr="")
    assert supervisor.run(plan_path,runner=forced_success)==0
    original_event = d.eventfiles()[0].read_bytes()
    assert receiver._governed_rejection_summary(json.dumps({
        "allowed":False,"blocked_by":"ROUTE","mode":"REROUTE_REQUIRED",
        "reason":"same failed route/failure-class cannot repeat"})) == {
        "gate":"ROUTE","mode":"REROUTE_REQUIRED",
        "reason":"same failed route/failure-class cannot repeat"}
    assert receiver._governed_rejection_summary("not-json") is None
    assert receiver._cli_error_category("CreateProcess failed: Access is denied") == "WINDOWS_PROCESS_ACCESS"
    assert receiver._cli_error_category("tool rejected: blocked by policy") == "TOOL_POLICY_BLOCKED"
    assert receiver._cli_error_category("unexpected argument --oops") == "CLI_ARGUMENT_REJECTED"
    assert receiver._cli_error_category("unknown provider outage") == "CLI_ERROR_UNCLASSIFIED"

    def fresh(label):
        newroot = root / ("cli_" + label)
        event = newroot / "events" / "000001.json"
        event.parent.mkdir(parents=True, exist_ok=True)
        event.write_bytes(original_event)
        return delta.Delta(newroot, current, src)

    def mock_runner(mode="ok"):
        def run(argv, **kw):
            assert kw.get("shell") is False
            assert kw.get("env") is not None
            assert all(k not in kw["env"] for k in receiver.NO_API_KEYS)
            if "-Provider" in argv and "codex" in argv:
                from pathlib import Path as _P
                assert any(str(x).endswith("TAKY_MODEL_REVIEW.ps1") for x in argv)
                assert argv[argv.index("-OutputMode")+1]=="Envelope"
                assert "D:\\Git PWA\\TAKY" in kw.get("cwd","")
                assert kw.get("shell") is False
                prompt=argv[argv.index("-Prompt")+1]
                prefix="following exact JSON receipt (no Markdown, commentary or extra fields):\n"
                response=json.loads(prompt.split(prefix,1)[1].split("\nDelivery data:",1)[0])
                if mode=="challenge":response["challenge"]="badchallenge"
                if mode=="events":response["event_ids"]=["BAD_EVENT"]
                if mode=="hold":response["status"]="HOLD"
                rid="pf:external-review-"+"a"*32+":"+"b"*16
                state="EXECUTOR_RETURNED_UNVERIFIED"
                output=json.dumps(response)
                if mode=="bad_jsonl":output="NOT_JSON"
                if mode=="no_completion":output=""
                result_code=6 if mode=="failed_turn" else 0
                body={"allowed":mode not in ("tool_used","preflight_missing"),
                      "state":state,"receipt_id":rid,
                      "result":{"returncode":result_code,"stdout":output,"stderr":""}}
                if mode!="no_receipt":
                    receipt_path=_P(argv[argv.index("-ReceiptOut")+1])
                    receipt_path.write_text(json.dumps({
                        "provider":"codex",
                        "receipt_id":"pf:external-review-"+"c"*32+":"+"b"*16 if mode=="receipt_mismatch" else rid,
                        "executor_state":state}),encoding="utf-8")
                text=delta.GOVERNED_CODEX_PREFIX+"\n"+json.dumps(body)
                if mode=="preflight_missing":text=json.dumps(body)
                return type("Result",(),{
                    "returncode":2 if mode in ("nonzero","authfail","wrong_auth") else 0,
                    "stdout":text,"stderr":"test diagnostic"})()
            if argv[1:] == ["auth", "status"]:
                return type("Result", (), {"returncode": 0 if mode != "authfail" else 1,
                                           "stdout": json.dumps({
                    "loggedIn": True, "authMethod": "claude.ai",
                    "apiProvider": "firstParty"})})()
            if argv[1:] == ["login", "status"]:
                return type("Result", (), {"returncode": 1 if mode == "authfail" else 0,
                    "stdout": "Logged in using ChatGPT" if mode != "wrong_auth" else "Not logged in",
                    "stderr": ""})()
            is_codex = argv[1:] == delta.CODEX_CLI_ARGV_TAIL
            assert is_codex or argv[1:] == delta.CLI_ARGV_TAIL
            prompt = kw["input"]
            prefix = "following exact JSON receipt (no Markdown, commentary or extra fields):\n"
            assert prefix in prompt
            response = json.loads(prompt.split(prefix, 1)[1].split("\nDelivery data:", 1)[0])
            if mode == "challenge":
                response["challenge"] = "badchallenge"
            if mode == "events":
                response["event_ids"] = ["BAD_EVENT"]
            if mode == "hold":
                response["status"] = "HOLD"
            raw = json.dumps({"type": "result", "subtype": "success",
                              "is_error": False,
                              "session_id": "" if mode == "no_session" else "session_fixture_1",
                              "result": json.dumps(response)})
            if is_codex:
                entries = [
                    {"type": "thread.started", "thread_id": "codex_fixture_thread"},
                    {"type": "turn.started"},
                    {"type": "item.completed", "item": {
                        "id": "msg1", "type": "agent_message", "text": json.dumps(response)}},
                    {"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 19}}
                ]
                if mode == "bad_jsonl":
                    entries[2]["item"]["text"] = "not-json"
                if mode == "tool_used":
                    entries.insert(2, {"type": "item.started",
                                       "item": {"type": "command_execution"}})
                if mode == "no_completion":
                    entries.pop()
                if mode == "failed_turn":
                    entries[-1] = {"type": "turn.failed"}
                raw = "\n".join(json.dumps(e) for e in entries) + "\n"
            return type("Result", (), {"returncode": 1 if mode == "nonzero" else 0,
                                       "stdout": raw})()
        run._taky_mode=mode
        return run

    good = fresh("success")
    good_id = good.delivery("CLAUDE")["delivery_id"]
    assert receiver.receive_once("CLAUDE", target=good, runner=mock_runner(), cli="mock-claude")["error"] == "EXACT_DELIVERY_ID_REQUIRED"
    good_result = receiver.receive_once("CLAUDE", delivery_id=good_id, target=good,
                                        runner=mock_runner(), cli="mock-claude")
    assert good_result["status"] == delta.LOCAL_ACK_STATUS, good_result
    assert good_result["provider_signed"] is False
    assert good.cursor("CLAUDE") == 1
    assert good.cursor("CODEX") == 0
    proof_file = good.root / "receiver_evidence" / "CLAUDE" / (
        good_result.get("delivery_id", "") + ".json")
    actual_file = next((good.root / "receiver_evidence" / "CLAUDE").glob("*.json"))
    proof_doc = delta.read(actual_file)
    ack = {"actor": "CLAUDE", "delivery_id": proof_doc["delivery_id"],
           "current_sha256": proof_doc["current_sha256"],
           "event_ids": proof_doc["event_ids"],
           "event_seq_end": proof_doc["event_seq_end"],
           "challenge": proof_doc["challenge"]}
    delivery_doc = delta.read(good.root / "deliveries" / "CLAUDE" /
                              (proof_doc["delivery_id"] + ".json"))
    assert good.validate_ack(delivery_doc, ack, proof=actual_file) is None
    assert good.validate_ack(delivery_doc, {k:v for k,v in ack.items()
                                           if k != "challenge"}, proof=actual_file) == "EVIDENCE_BINDING_MISMATCH"
    assert good.validate_ack(delivery_doc, ack, proof={"provider_binding_verified":True}) == "RECEIVER_PROVIDER_PROOF_UNVERIFIED"
    assert receiver.receive_once("CLAUDE", delivery_id="0"*24, target=good,
                                 runner=mock_runner(), cli="mock-claude")["error"] == "DELIVERY_NOT_PREPARED"
    proof_doc["session_id"] = "tampered"
    save(actual_file, proof_doc)
    assert good.validate_ack(delivery_doc, ack, proof=actual_file) == "EVIDENCE_SIGNATURE_INVALID"
    assert receiver.receive_once("CLAUDE", delivery_id=good_id, target=good,
                                 runner=mock_runner(), cli="mock-claude")["error"] == "POINTER_ALREADY_ADVANCED"

    for mode in ("challenge", "events", "no_session", "hold", "nonzero", "authfail"):
        bad = fresh(mode)
        bad_id = bad.delivery("CLAUDE")["delivery_id"]
        outcome = receiver.receive_once("CLAUDE", delivery_id=bad_id,
                                        target=bad, runner=mock_runner(mode), cli="mock-claude")
        assert outcome["status"] == "HOLD", (mode, outcome)
        assert bad.cursor("CLAUDE") == 0, mode
        assert not list((bad.root / "ack_receiver").glob("**/*.json")), mode

    unsupported = fresh("unsupported")
    assert receiver.receive_once("CODEX", target=unsupported)["error"] == "EXACT_DELIVERY_ID_REQUIRED"
    assert unsupported.cursor("CODEX") == 0

    # Existing ACK/evidence regression uses a fake governed *result*, never a
    # model or production TAKY2 runtime. Direct-stage tests run separately.
    def fake_governed_result(prompt, env, runner):
        mode=getattr(runner,"_taky_mode","ok")
        rid="pf:external-review-"+"a"*32+":"+"b"*16
        if mode in ("authfail","wrong_auth","nonzero"):
            return subprocess.CompletedProcess([],2,"AUTH_OR_PREFLIGHT_BLOCKED",""),None
        if mode=="no_receipt":
            raise RuntimeError("TAKY_EXECUTION_RECEIPT_NOT_DURABLE")
        prefix="following exact JSON receipt (no Markdown, commentary or extra fields):\n"
        response=json.loads(prompt.split(prefix,1)[1].split("\nDelivery data:",1)[0])
        if mode=="challenge":response["challenge"]="badchallenge"
        if mode=="events":response["event_ids"]=["BAD_EVENT"]
        if mode=="hold":response["status"]="HOLD"
        text=json.dumps(response)
        if mode=="bad_jsonl":text="NOT_JSON"
        if mode=="no_completion":text=""
        code=6 if mode=="failed_turn" else 0
        body={"allowed":mode not in ("tool_used","preflight_missing"),
              "state":"EXECUTOR_RETURNED_UNVERIFIED","receipt_id":rid,
              "result":{"returncode":code,"stdout":text,"stderr":""}}
        wrapper=delta.GOVERNED_CODEX_PREFIX+"\n"+json.dumps(body)
        actual_rid="pf:external-review-"+"c"*32+":"+"b"*16 if mode=="receipt_mismatch" else rid
        return subprocess.CompletedProcess([],2 if code else 0,wrapper,""),{
            "receipt_id":actual_rid,"executor_state":"EXECUTOR_RETURNED_UNVERIFIED",
            "provider":"codex"}
    original_direct=receiver._run_governed_codex
    receiver._run_governed_codex=fake_governed_result

    codex_good = fresh("codex_good")
    codex_id = codex_good.delivery("CODEX")["delivery_id"]
    codex_reply = receiver.receive_once("CODEX", delivery_id=codex_id,
                                       target=codex_good, runner=mock_runner(), cli="mock-codex")
    assert codex_reply["status"] == delta.LOCAL_ACK_STATUS, codex_reply
    assert codex_reply["provider_signed"] is False
    assert codex_good.cursor("CODEX") == 1
    assert codex_good.cursor("CLAUDE") == 0
    assert (codex_good.root / "ack_receiver" / "CODEX" / (codex_id + ".json")).is_file()
    codex_proof = codex_good.root / "receiver_evidence" / "CODEX" / (codex_id + ".json")
    codex_record = delta.read(codex_proof)
    assert codex_record["execution_route"]=="TAKY2_CODEX_VERIFY_ONLY"
    assert codex_record["governed_receipt_id"]=="pf:external-review-"+"a"*32+":"+"b"*16
    assert codex_record["session_kind"]=="LOCAL_GOVERNED_RECEIPT_NOT_CODEX_SESSION"
    assert codex_record["argv_tail"]==delta.GOVERNED_CODEX_ROUTE
    codex_ack = {key: codex_record[key] for key in (
        "actor", "delivery_id", "current_sha256", "event_ids", "event_seq_end", "challenge")}
    codex_envelope = delta.read(codex_good.root / "deliveries" / "CODEX" / (codex_id + ".json"))
    assert codex_good.validate_ack(codex_envelope,codex_ack,proof=codex_proof) is None
    assert codex_good.validate_ack(codex_envelope,codex_ack,proof={"provider_ack":True}) == "RECEIVER_PROVIDER_PROOF_UNVERIFIED"
    assert codex_good.validate_ack(codex_envelope,{**codex_ack,"challenge":"0"*48},
                                   proof=codex_proof) == "EVIDENCE_BINDING_MISMATCH"
    proof_bytes=codex_proof.read_bytes()
    codex_record["auth"]["auth_method"]="forged"
    save(codex_proof,codex_record)
    assert codex_good.validate_ack(codex_envelope,codex_ack,proof=codex_proof) == "EVIDENCE_SIGNATURE_INVALID"
    codex_proof.write_bytes(proof_bytes)
    assert receiver.receive_once("CODEX", delivery_id=codex_id, target=codex_good,
                                 runner=mock_runner(), cli="mock-codex")["error"] == "POINTER_ALREADY_ADVANCED"
    for mode in ("challenge","events","hold","nonzero","authfail","wrong_auth",
                 "bad_jsonl","tool_used","no_completion","failed_turn",
                 "no_receipt","receipt_mismatch","preflight_missing"):
        cd = fresh("codex_" + mode)
        cid = cd.delivery("CODEX")["delivery_id"]
        cr = receiver.receive_once("CODEX", delivery_id=cid, target=cd,
                                   runner=mock_runner(mode), cli="mock-codex")
        assert cr["status"] == "HOLD", (mode,cr)
        assert cd.cursor("CODEX") == 0, mode
        assert not list((cd.root / "ack_receiver").glob("**/*.json")), mode

    receiver._run_governed_codex=original_direct
    stale = fresh("stale")
    stale_id = stale.delivery("CLAUDE")["delivery_id"]
    before = current.read_bytes()
    save(current, {"authority_status": "DERIVED_NON_AUTHORITY", "status": "CHANGED"})
    try:
        outcome = receiver.receive_once("CLAUDE", delivery_id=stale_id, target=stale,
                                        runner=mock_runner(), cli="mock-claude")
        assert outcome["error"] == "STALE_CURRENT"
        assert stale.cursor("CLAUDE") == 0
    finally:
        current.write_bytes(before)

    # No-PowerShell direct TAKY2 route: fake all OS subprocesses and the
    # durable runtime readback. Never touch the live TAKY2 runtime or models.
    import sys
    sys.path.insert(0,str(receiver.GOVERNED_ORCH))
    import TAKY2.state_store as direct_store
    durable_calls = {}
    direct_state = {}
    def direct_mock(argv, **kw):
        assert kw.get("shell") is False
        assert all(k not in kw["env"] for k in receiver.NO_API_KEYS)
        if argv[0] == str(receiver.PINNED_CODEX) and argv[1:] == ["login","status"]:
            return subprocess.CompletedProcess(argv,0,"Logged in using ChatGPT","")
        if any("TAKY_MODEL_REVIEW_PACKET.py" in str(a) for a in argv):
            p=json.loads(Path(argv[argv.index("--prompt-file")+1]).read_text(encoding="utf-8"))
            direct_state["prompt"]=p["prompt"]
            Path(argv[argv.index("--packet-file")+1]).write_text(p["prompt"],encoding="utf-8")
            return subprocess.CompletedProcess(argv,0,json.dumps({
                "packet_digest":"a"*40,"packet_chars":len(p["prompt"]),
                "included_source_files":[]}),"")
        if "preflight" in argv:
            plan=json.loads(Path(argv[-1]).read_text(encoding="utf-8"))
            assert plan["attempt"]["method_or_tool"]=="codex"
            assert plan["call"]["execution_mode"]=="CODEX_VERIFY_ONLY"
            direct_state["rid"]="pf:"+plan["task_id"]+":"+"b"*16
            return subprocess.CompletedProcess(argv,0,json.dumps({
                "allowed":True,"call_allowed":True,
                "receipt_id":direct_state["rid"]}),"")
        if "execute" in argv:
            inv=json.loads(Path(argv[argv.index("execute")+2]).read_text(encoding="utf-8"))
            assert argv[argv.index("execute")+1]==direct_state["rid"]
            assert inv["provider"]=="openai"
            assert inv["method_or_tool"]=="codex"
            assert inv["argv"][0]==str(receiver.PINNED_CODEX)
            assert inv["argv"][1:4]==["exec","--sandbox","read-only"]
            assert inv["argv"][-1]=="-"
            assert inv["call"]["execution_mode"]=="CODEX_VERIFY_ONLY"
            prefix="following exact JSON receipt (no Markdown, commentary or extra fields):\n"
            response=json.loads(direct_state["prompt"].split(prefix,1)[1].split("\nDelivery data:",1)[0])
            result={"returncode":0,"stdout":json.dumps(response),"stderr":""}
            durable_calls[direct_state["rid"]]={"status":"RETURNED","result":result}
            return subprocess.CompletedProcess(argv,0,json.dumps({
                "allowed":True,"state":"EXECUTOR_RETURNED_UNVERIFIED",
                "receipt_id":direct_state["rid"],"result":result}),"")
        raise AssertionError(("UNEXPECTED_SUBPROCESS",argv))
    direct_target=fresh("codex_direct")
    direct_id=direct_target.delivery("CODEX")["delivery_id"]
    with mock_patch.object(direct_store,"load_bundle",
                           return_value=({},{"execution_calls":durable_calls},"fixture")):
        direct_result=receiver.receive_once(
            "CODEX",delivery_id=direct_id,target=direct_target,
            runner=direct_mock)
    assert direct_result["status"]==delta.LOCAL_ACK_STATUS,direct_result
    assert direct_target.cursor("CODEX")==1 and direct_target.cursor("CLAUDE")==0
    assert direct_result["provider_signed"] is False
    assert direct_state["rid"] in durable_calls
print("TAKY_CONTEXT_DELTA_QA_PASS: seed,idempotency,per-client cursor,integrity,simulation,local-cli-success, codex-direct-governed-route, tamper,challenge,event,session,HOLD,stale,replay")
