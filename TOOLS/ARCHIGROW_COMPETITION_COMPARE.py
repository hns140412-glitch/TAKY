#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path

def load_rows(path):
    p=Path(path)
    rows=[]
    if not p.exists():
        return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows

def compare(rows, agency, competition):
    selected=[
        r for r in rows
        if (not agency or str(r.get("agency","")).lower()==agency.lower())
        and (not competition or str(r.get("competition","")).lower()==competition.lower())
    ]
    entries=defaultdict(lambda:{
        "artifact_ids":set(),"modes":defaultdict(set),"techniques":set(),
        "boards":set(),"pages":set(),"drawings":set(),"outcomes":defaultdict(int)
    })
    for r in selected:
        e=entries[r.get("entry_id") or "UNKNOWN"]
        if r.get("artifact_id"): e["artifact_ids"].add(r["artifact_id"])
        mode=r.get("representation_mode") or "UNKNOWN"
        tech=r.get("technique")
        if tech:
            e["modes"][mode].add(tech)
            e["techniques"].add(tech)
        if r.get("board_no"): e["boards"].add(str(r["board_no"]))
        if r.get("page_no") is not None: e["pages"].add(str(r["page_no"]))
        if r.get("drawing_name"): e["drawings"].add(r["drawing_name"])
        e["outcomes"][r.get("outcome") or "UNKNOWN"]+=1

    normalized={}
    for entry_id,e in entries.items():
        normalized[entry_id]={
            "artifact_count":len(e["artifact_ids"]),
            "board_count":len(e["boards"]),
            "page_count":len(e["pages"]),
            "modes":{k:sorted(v) for k,v in sorted(e["modes"].items())},
            "techniques":sorted(e["techniques"]),
            "drawing_names":sorted(e["drawings"]),
            "outcomes":dict(e["outcomes"])
        }

    all_entries=list(normalized)
    differences=[]
    modes=set()
    for e in normalized.values():
        modes.update(e["modes"])
    for mode in sorted(modes):
        signatures={}
        for entry_id,e in normalized.items():
            signatures[entry_id]=tuple(e["modes"].get(mode,[]))
        unique={sig for sig in signatures.values()}
        if len(unique)>1:
            differences.append({"mode":mode,"entry_techniques":{k:list(v) for k,v in signatures.items()}})

    return {
        "agency":agency,
        "competition":competition,
        "entry_count":len(all_entries),
        "entries":normalized,
        "within_competition_differences":differences,
        "rule":"Compare entries under the same brief/site before generalizing across projects."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ledger",required=True)
    p.add_argument("--agency",default="")
    p.add_argument("--competition",default="")
    args=p.parse_args()
    print(json.dumps(compare(load_rows(args.ledger),args.agency,args.competition),ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
