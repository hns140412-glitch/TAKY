#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/"OS"/"DRIVE_STORAGE_MAP.json"

def load_map():
    return json.loads(MAP.read_text(encoding="utf-8"))

def resolve(account, role):
    d=load_map()
    account=account.lower()
    if account not in {"hns","siezeall"}:
        raise KeyError(f"UNKNOWN_ACCOUNT:{account}")
    ns=d.get("final_storage_namespace") or {}
    paths=(ns.get("logical_role_paths") or {}).get(account) or {}
    ids=(ns.get("logical_role_ids") or {}).get(account) or {}
    root=((ns.get(account) or {}).get("root") or {})
    immediate=((ns.get(account) or {}).get("immediate_children") or {})
    if role in paths:
        return {"account":account.upper(),"role":role,"path":paths[role],"id":ids.get(role),"kind":"LOGICAL_ROLE"}
    if role in immediate:
        return {"account":account.upper(),"role":role,"path":"TAKY/"+role,"id":immediate[role],"kind":"ROOT_GROUP"}
    if role=="TAKY":
        return {"account":account.upper(),"role":"TAKY","path":"TAKY","id":root.get("id"),"kind":"ROOT"}
    raise KeyError(f"UNKNOWN_ROLE:{account}:{role}")

def main():
    if len(sys.argv)!=3:
        print("usage: drive_route_resolver.py <hns|siezeall> <role>",file=sys.stderr)
        return 2
    try:
        print(json.dumps(resolve(sys.argv[1],sys.argv[2]),ensure_ascii=False,indent=2))
        return 0
    except KeyError as e:
        print(str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
