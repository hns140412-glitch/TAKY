#!/usr/bin/env python3
"""Goal-sufficiency evaluator: evidence sufficient != goal sufficient."""
from __future__ import annotations

def evaluate(task:dict, assessed:list[dict])->dict:
    by={str(x.get("id")):x for x in assessed}
    critical={str(x) for x in task.get("critical_frontier_ids",[]) or []}
    foundation={str(x) for x in task.get("foundation_frontier_ids",[]) or []}
    advanced={str(x) for x in task.get("advanced_frontier_ids",[]) or []}
    alternatives={str(x) for x in task.get("alternative_frontier_ids",[]) or []}
    required=critical|foundation|advanced
    if task.get("alternatives_required"): required|=alternatives
    # If no explicit semantic groups exist, every declared frontier remains required.
    if not required: required=set(by)
    missing=sorted(x for x in required if x not in by)
    unresolved=sorted(x for x in required if x in by and by[x].get("status")!="CLOSED")
    critical_unresolved=sorted(x for x in critical if x not in by or by[x].get("status")!="CLOSED")
    coverage=(len(required)-len(missing)-len(unresolved))/len(required) if required else 1.0
    goal_sufficient=not missing and not unresolved and not critical_unresolved
    return {"goal_sufficient":goal_sufficient,"coverage":round(max(0.0,coverage),4),"required_ids":sorted(required),"missing_required":missing,"unresolved_required":unresolved,"unresolved_critical":critical_unresolved,"dimensions":{"foundation_closed":all(x in by and by[x].get("status")=="CLOSED" for x in foundation),"advanced_closed":all(x in by and by[x].get("status")=="CLOSED" for x in advanced),"alternatives_closed":(not task.get("alternatives_required")) or all(x in by and by[x].get("status")=="CLOSED" for x in alternatives)}}
