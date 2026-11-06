from TAKY2.state_store import load_bundle
a,r,h=load_bundle()
attempts=r.get("active_attempts",{})
calls=r.get("execution_calls",{})
print("ACTIVE_COUNT",len(attempts))
for k,v in attempts.items():
 rec=v.get("receipt_id");c=calls.get(rec,{})
 print("ACTIVE",str(k)[:16],v.get("status"),v.get("claimed_by"),"receipt",str(rec)[:18],"call",c.get("status"),"provider",c.get("provider"),"tool",c.get("method_or_tool"))
print("EXECUTION_CALLS",len(calls))
for key,a0 in attempts.items():
 if a0.get("status")!="PENDING":continue
 rid=a0.get("receipt_id")
 rp=r.get("preflight_receipts",{}).get(rid,{})
 print("PENDING_DETAIL",rid,"receipt",rp.get("consumed"),"scope",rp.get("execution_scope"),"task",str(rp.get("task_id"))[:60],"attempt",str(a0.get("attempt"))[:160],
       "created",str(rp.get("created_at") or rp.get("timestamp") or rp.get("preflight_at"))[:80],
       "claimed",rid in calls,
       "outcome",rid in r.get("execution_outcomes",{}),
       "done",rid in r.get("completion_registry",{}))

