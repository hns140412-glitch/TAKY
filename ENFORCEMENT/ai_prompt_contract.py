#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

REQUIRED_LISTS = (
    "trigger_conditions","inputs","task_steps","constraints",
    "verification","evaluation_dimensions","required_source_markers",
)

def _text(v: object) -> bool:
    return isinstance(v,str) and bool(v.strip())

def validate_contract(c: dict[str,Any], source_text: str | None = None) -> list[str]:
    failures=[]
    if not _text(c.get("contract_id")): failures.append("PROMPT_CONTRACT_ID_MISSING")
    if not _text(c.get("role")) or len(str(c.get("role") or ""))>180:
        failures.append("PROMPT_ROLE_MISSING_OR_TOO_BROAD")
    if not _text(c.get("purpose")): failures.append("PROMPT_PURPOSE_MISSING")
    if not _text(c.get("audience")): failures.append("PROMPT_AUDIENCE_MISSING")
    if not isinstance(c.get("bounds"),dict) or not c["bounds"]:
        failures.append("PROMPT_BOUNDS_MISSING")
    if not isinstance(c.get("output_contract"),dict) or not c["output_contract"]:
        failures.append("PROMPT_OUTPUT_CONTRACT_MISSING")
    for key in REQUIRED_LISTS:
        v=c.get(key)
        if not isinstance(v,list) or not v or not all(_text(x) for x in v):
            failures.append("PROMPT_"+key.upper()+"_MISSING")
    triggers=c.get("trigger_conditions") or []
    if any("*"==str(x).strip() or "always"==str(x).strip().lower() for x in triggers):
        failures.append("PROMPT_TRIGGER_TOO_BROAD")
    if source_text is not None:
        for marker in c.get("required_source_markers") or []:
            if marker not in source_text:
                failures.append("PROMPT_SOURCE_MARKER_MISSING:"+marker)
    return list(dict.fromkeys(failures))

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--source",type=Path)
    args=ap.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8-sig"))
    src=args.source.read_text(encoding="utf-8-sig") if args.source else None
    failures=validate_contract(c,src)
    print(json.dumps({"pass":not failures,"failures":failures,"contract_id":c.get("contract_id")},ensure_ascii=False))
    return 0 if not failures else 2

if __name__=="__main__":
    raise SystemExit(main())
