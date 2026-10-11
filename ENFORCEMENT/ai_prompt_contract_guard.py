#!/usr/bin/env python3
from __future__ import annotations
from typing import Any

FAIL_PROMPT="AI_PROMPT_CONTRACT_MISSING"
FAIL_INSTALL="AI_INSTALL_DOC_OBSERVABILITY_MISSING"

def _text(v:object)->bool:
    return isinstance(v,str) and bool(v.strip())

def _list_text(v:object)->bool:
    return isinstance(v,list) and bool(v) and all(_text(x) for x in v)

def validate_ai_prompt_contract(record:dict[str,Any])->list[str]:
    failures=[]

    if record.get("ai_prompt_contract_required") is True:
        c=record.get("ai_prompt_contract")
        if not isinstance(c,dict):
            failures.append(FAIL_PROMPT)
        else:
            if not _text(c.get("role")) or len(str(c.get("role","")).strip())>240:
                failures.append(FAIL_PROMPT)
            if not _text(c.get("purpose")):
                failures.append(FAIL_PROMPT)
            if not _list_text(c.get("input_refs")):
                failures.append(FAIL_PROMPT)
            if not _list_text(c.get("constraints")):
                failures.append(FAIL_PROMPT)
            if not _text(c.get("output_spec")):
                failures.append(FAIL_PROMPT)
            if not _list_text(c.get("verification")):
                failures.append(FAIL_PROMPT)

            if c.get("audience_sensitive") is True and not _text(c.get("audience")):
                failures.append(FAIL_PROMPT)
            if c.get("quality_request") is True and not _list_text(c.get("evaluation_dimensions")):
                failures.append(FAIL_PROMPT)

            if c.get("reusable_skill") is True:
                triggers=c.get("trigger_conditions")
                if not _list_text(triggers):
                    failures.append(FAIL_PROMPT)
                else:
                    broad={"*","all","any","any task","all tasks","everything"}
                    if any(str(x).strip().lower() in broad for x in triggers):
                        failures.append(FAIL_PROMPT)
                if str(c.get("trigger_scope") or "").strip().upper()!="SPECIFIC":
                    failures.append(FAIL_PROMPT)

    if record.get("ai_install_doc_contract_required") is True:
        d=record.get("ai_install_doc_contract")
        required=["command_surface","fallback","observable_verification","prohibited_actions","provenance","license"]
        if not isinstance(d,dict) or any(not _text(d.get(k)) for k in required):
            failures.append(FAIL_INSTALL)

    return list(dict.fromkeys(failures))
