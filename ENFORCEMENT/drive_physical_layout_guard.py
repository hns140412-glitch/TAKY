#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"OS"/"DRIVE_STORAGE_MAP.json"

def expected(account):
    d=json.loads(MAP.read_text(encoding="utf-8"))
    layout=(d.get("physical_presentation_layout") or {}).get(account) or {}
    groups=layout.get("groups") or {}
    return {
        "root": list((d.get("structure_lock") or {}).get(f"{account}_allowed_root_children") or []),
        "groups": {k:list((v or {}).get("children") or []) for k,v in groups.items()}
    }

def names(p):
    return sorted([x.name for x in p.iterdir() if x.is_dir()])

def validate(account,root_path):
    root=Path(root_path)
    exp=expected(account)
    errors=[]
    if not root.exists():
        return {"state":"HOLD_ROOT_UNAVAILABLE","account":account.upper(),"root":str(root),"errors":["ROOT_UNAVAILABLE"]}
    got_root=names(root)
    if sorted(exp["root"])!=got_root:
        errors.append({"code":"ROOT_CHILD_DRIFT","expected":sorted(exp["root"]),"actual":got_root})
    # Only validate direct children that are represented physically in this locally mounted account.
    for group,children in exp["groups"].items():
        gp=root/group
        if not gp.exists():
            errors.append({"code":"GROUP_MISSING","group":group})
            continue
        got=names(gp)
        missing=sorted(set(children)-set(got))
        if missing:
            errors.append({"code":"GROUP_REQUIRED_CHILD_MISSING","group":group,"missing":missing,"actual":got})
    return {"state":"PASS" if not errors else "HOLD_DRIFT","account":account.upper(),"root":str(root),"errors":errors}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("account",choices=["hns","siezeall"])
    ap.add_argument("root")
    args=ap.parse_args()
    r=validate(args.account,args.root)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0 if r["state"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())
