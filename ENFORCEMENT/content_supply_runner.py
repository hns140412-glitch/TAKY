"""TAKY local supply run command. Composition only; never publishes to app.

Uses existing search/index/RAW bridges, forms a candidate and has Play Camp
TypeScript validate the exact produced bytes. No autonomous authority changes.
"""
import argparse
import json
from pathlib import Path
from content_supply_e2e_slice import run_slice
from content_supply_app_consumer import consume_playcamp_candidate
from content_supply_feedback import feedback
from content_supply_atomic import publish_bytes
from content_supply_mining_goal_bridge import evaluate_raw_goal

def execute(contract, *, index, manifest, raw_root, output, app_root):
    receipt = run_slice(
        contract, index, manifest, raw_root, output,
        lambda path: consume_playcamp_candidate(path, app_root))
    demand_id=contract.get('demand_id') if isinstance(contract,dict) else None
    next_action = feedback(receipt, demand_id=demand_id if isinstance(demand_id,str) else '')
    items=contract.get('requirements',[]) if isinstance(contract,dict) else []
    required_ids=[x.get('id') for x in items if isinstance(x,dict)] if isinstance(items,list) else []
    if receipt.get('status')=='LOCAL_E2E_PASS' or receipt.get('stage') in ('FORMING','MINING','PRODUCTION','INTEGRATION','VALIDATION'):
        raw_ids=required_ids
    else:
        rows=receipt.get('detail',{}).get('items',[]) if isinstance(receipt.get('detail'),dict) else []
        raw_ids=[row.get('requirement_id') for row in rows if isinstance(row,dict) and any(
            isinstance(x,dict) and x.get('state')=='RAW_HASH_MATCH_CANDIDATE' for x in row.get('raw_candidates',[]))]
    raw_goal=evaluate_raw_goal(required_ids,raw_ids)
    return {"supply": receipt, "feedback": next_action, "raw_goal": raw_goal,
            "release_approved": False,
            "consumer_scope": "PLAY_CAMP_TYPESCRIPT_CANDIDATE_ONLY",
            "app_runtime_bound": False,
            "learning_engine_evidence_sent": False}

def main():
    parser = argparse.ArgumentParser()
    for name in ("contract", "index", "manifest", "raw-root", "output", "app-root"):
        parser.add_argument("--"+name, required=True)
    parser.add_argument('--receipt-out', help='Optional immutable JSON result file; never overwritten')
    args = parser.parse_args()
    try:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        result = execute(contract, index=args.index, manifest=manifest,
                         raw_root=args.raw_root, output=args.output, app_root=args.app_root)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {"supply":{"status":"BLOCKED","stage":"INPUT","reason":type(exc).__name__},
                  "release_approved":False}
    if args.receipt_out:
        try:
            receipt_data=(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
            publish_bytes(args.receipt_out,receipt_data)
        except FileExistsError:
            print(json.dumps({'status':'RECEIPT_EXISTS_UNCHANGED','path':args.receipt_out},ensure_ascii=False))
            return 2
        except OSError as exc:
            print(json.dumps({'status':'RECEIPT_WRITE_FAILED','error':type(exc).__name__},ensure_ascii=False))
            return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("supply",{}).get("status") == "LOCAL_E2E_PASS" else 1

if __name__=="__main__": raise SystemExit(main())
