#!/usr/bin/env python3
"""TAKY Antigravity verified inbox inspector.
Read-only: never invokes Claude/Codex, moves cursor, or advances a provider ACK.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
import taky_antigravity_bridge_v3_candidate as bridge
import TAKY_SHARED_CONTEXT_DELTA_CANDIDATE as delta

def inspect(limit=8):
    d=delta.Delta()
    tasks=[]
    paths=sorted((bridge.MAILBOX/"requests").glob("*.json"),
                 key=lambda f:f.stat().st_mtime, reverse=True)
    for path in paths:
        if len(tasks)>=limit:break
        try:
            req=bridge.load(path)
            if req.get("project")!="TAKY2" or req.get("actor") not in ("CLAUDE","CODEX"):
                continue
            error=bridge.validate(req)
            response=bridge.poll(req.get("task_id",""))
            binding=req.get("context_delivery")
            status="HOLD" if error else response.get("status","UNKNOWN")
            task={"task_id":req["task_id"],"agent":req["actor"],
                  "status":status,"request_valid":not bool(error),
                  "context_bundle_id":binding.get("delivery_id") if binding else None,
                  "receiver_ack_verified":False,"provider_inferred_from_queue":False,
                  "intent":str(req.get("intent",""))[:150],
                  "session_mode":"NATIVE_ANTIGRAVITY_PANEL_UNVERIFIED"}
            tasks.append(task)
        except (ValueError,TypeError,KeyError,OSError):
            tasks.append({"status":"HOLD_UNREADABLE_SIGNED_REQUEST",
                          "request_name":path.name,"receiver_ack_verified":False})
    return {
       "schema":"TAKY_ANTIGRAVITY_VERIFIED_INBOX_VIEW_V1",
       "workspace":str(bridge.ALLOWED["TAKY2"]),
       "canonical_current":"UNRESOLVED_DO_NOT_PROMOTE",
       "derivative_context_sha256":bridge.current().get("sha256"),
       "claude_ack_cursor":d.cursor("CLAUDE"),
       "codex_ack_cursor":d.cursor("CODEX"),
       "provider_panel_bound":False,"model_execution_enabled":False,
       "tasks":tasks
    }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=8)
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    if args.limit<1 or args.limit>50:raise ValueError("LIMIT_1_TO_50")
    data=inspect(args.limit)
    if args.json:
        print(json.dumps(data,ensure_ascii=False,indent=2));return
    print("TAKY · ANTIGRAVITY VERIFIED INBOX [READ ONLY]")
    print("Workspace:",data["workspace"])
    print("Derived shared context:",data["derivative_context_sha256"])
    print("Claude ACK cursor:",data["claude_ack_cursor"],
          "| Codex ACK cursor:",data["codex_ack_cursor"])
    print("Native panel control: OPEN | Provider ACK: NOT RECEIVED | Model calls: OFF")
    print("-"*78)
    for item in data["tasks"]:
        print(f"{item.get('agent','UNKNOWN'):6} {item.get('status','HOLD'):23} "
              f"Task {item.get('task_id',item.get('request_name',''))}")
        print("    Context:",item.get("context_bundle_id") or "not bound")
        print("    Intent:",item.get("intent","unreadable"))
    print("-"*78)
    print("This is a task INBOX, not a model-received acknowledgment.")
if __name__=="__main__":main()
