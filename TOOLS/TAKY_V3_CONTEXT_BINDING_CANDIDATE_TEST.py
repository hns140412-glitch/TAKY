#!/usr/bin/env python3
"""Isolated V3 signed-task ↔ context-delta binding regression; no AI calls."""
import json,tempfile
from pathlib import Path
from types import SimpleNamespace
import taky_antigravity_bridge_v3_candidate as b
with tempfile.TemporaryDirectory(prefix="TAKY_BOUND_DELTA_TEST_") as tmp:
    root=Path(tmp)
    b.CURRENT=root/"derived.json"
    b.CURRENT.write_text('{"authority_status":"DERIVED_NON_AUTHORITY"}',encoding="utf-8")
    b.HOST_KEY=root/"key.bin"
    b.WORKER_LOCK=root/"worker.lock"
    b.MAILBOX=root/"mailbox"
    b.DELTA_DELIVERIES=root/"deliveries"
    delivery_id="b"*24
    delivery=b.DELTA_DELIVERIES/"CLAUDE"/(delivery_id+".json")
    data={"schema":"TAKY_CONTEXT_DELIVERY_V1","delivery_id":delivery_id,
        "actor":"CLAUDE","delivery_state":"PENDING_RECEIVER_ACK",
        "current":{"sha256":b.current()["sha256"]},"event_ids":["a"*24],
        "event_seq_end":1}
    b.seal_receipt(data)
    b.write_new(delivery,data)
    args=SimpleNamespace(actor="CLAUDE",project="TAKY2",
        intent="Read-only transfer contract validation",context_delivery_id=delivery_id)
    staged=b.stage(args)
    assert staged["status"]=="STAGED"
    task=staged["task_id"]
    req=b.load(b.MAILBOX/"requests"/(task+".json"))
    assert req["context_delivery"]["delivery_id"]==delivery_id
    assert b.validate(req) is None
    assert b.worker_once()["new_receipts"]==1
    receipt=b.poll(task)
    assert receipt["status"]=="PREPARED_NOT_EXECUTED"
    assert receipt["data"]["context_delivery_binding"]==req["context_delivery"]
    assert receipt["provider_invoked"] is False
    pristine=delivery.read_bytes()
    forged=json.loads(pristine)
    forged["event_ids"]=["forged"]
    delivery.write_text(json.dumps(forged),encoding="utf-8")
    assert b.validate(req)=="CONTEXT_DELIVERY_NOT_TRUSTED"
    assert b.poll(task)["error"]=="REQUEST_RECEIPT_CHAIN_MISMATCH"
    delivery.write_bytes(pristine)
    assert b.poll(task)["status"]=="PREPARED_NOT_EXECUTED"
    b.CURRENT.write_text('{"authority_status":"DERIVED_NON_AUTHORITY","modified":true}',encoding="utf-8")
    try:
        b.stage(args)
        raise AssertionError("STALE_DELIVERY_ACCEPTED")
    except ValueError as e:
        assert str(e)=="CONTEXT_DELIVERY_STALE_OR_INCOMPLETE"
print("TAKY_V3_CONTEXT_BINDING_QA_PASS signed_request,delivery,mutation_hold,stale_hold,no_ai")
