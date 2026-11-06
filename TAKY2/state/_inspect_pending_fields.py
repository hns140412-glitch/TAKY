from TAKY2.state_store import load_bundle
a,r,_=load_bundle()
for k,x in r.get("active_attempts",{}).items():
 if x.get("status")!="PENDING":continue
 rid=x.get("receipt_id");p=r.get("preflight_receipts",{}).get(rid,{})
 print("task",p.get("task_id"),"status",x.get("status"),"scope",x.get("execution_scope"),
 "receiptConsumed",p.get("consumed"),"callExists",rid in r.get("execution_calls",{}),
 "outcomeExists",rid in r.get("execution_outcomes",{}),
 "completionExists",rid in r.get("completion_registry",{}),
 "caller",x.get("claimed_by"),"registeredPreflight",p.get("allowed"),
 "preflightFields",sorted(p.keys()),"activeFields",sorted(x.keys()))
