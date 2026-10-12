#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NEW_GUARD_IDS={
 "AI-LRN-NECESSITY-BEFORE-ADOPTION",
 "AI-LRN-SECURITY-BEFORE-CREDENTIAL",
 "AI-LRN-OBSERVABLE-SUCCESS-CRITERIA",
 "AI-LRN-SUPPLY-CHAIN-IDENTITY-CHECK",
 "AI-LRN-SELF-REPORT-NOT-RUNTIME-PROOF",
 "AI-LRN-UPSTREAM-TOOL-CLAIMS-VERIFY",
 "AI-LRN-DEVICE-OBSERVATION-BEFORE-CLOSE",
 "AI-LRN-CAPABILITY-GAP-BEFORE-TOOL",
 "AI-LRN-CONNECTOR-PERMISSION-BOUNDARY",
 "AI-LRN-COST-GUARD-AS-CODE",
 "AI-LRN-METADATA-FIRST-FILE-DIAGNOSIS",
 "AI-LRN-REVIEW-BUDGET-DOES-NOT-FORCE-PASS",
 "AI-LRN-SAFE-COMPUTER-USE-SEQUENCE",
 "AI-LRN-SENSITIVE-AGENT-ISOLATION",
}
EXISTING_VERIFIED_IDS={
 "AI-LRN-APPROVAL-BOUND-TO-ARTIFACT",
 "AI-LRN-BOUNDED-GOAL-PLUS-SCOPE-FREEZE",
}
Q2_LOCAL_VERIFIED_IDS={
 "AI-LRN-SEPARATE-TOOLS-BEFORE-COMBINE",
 "AI-LRN-REFERENCE-SETS-MUST-NOT-MERGE",
 "AI-LRN-PUBLIC-ACQUISITION-SEPARATION",
}
DOMAIN_HANDOFF_IDS={
 "AI-LRN-PROMPT-TEMPLATE-STRUCTURE",
 "AI-LRN-INSTALL-DOC-OBSERVABILITY",
 "AI-LRN-HUMAN-EDITABLE-OUTPUT",
 "AI-LRN-DESIGN-PIPELINE-NOT-PROMPT-ONLY",
 "AI-LRN-DESIGN-REFERENCE-PLUS-REVIEW",
 "AI-LRN-DESIGN-TASTE-AS-EXPLICIT-CONSTRAINT",
 "AI-LRN-FLUENCY-INCLUDES-DISCERNMENT-AND-RESPONSIBILITY",
 "AI-LRN-LEVEL-ADAPTIVE-AI-LEARNING",
 "AI-LRN-LITERACY-BEFORE-TOOL-SPEED",
 "AI-LRN-MENTAL-MODEL-OF-CAPABILITIES-AND-LIMITS",
 "AI-LRN-MULTIPLE-REPRESENTATIONS-FOR-LEARNING",
 "AI-LRN-PROMPT-AUDIENCE-AND-BOUNDS",
 "AI-LRN-PROMPT-EVALUATION-DIMENSIONS",
 "AI-LRN-PROMPT-ROLE-SHORT-CONTEXT-SPECIFIC",
 "AI-LRN-SOURCE-ASSET-QUALITY-SETS-OUTPUT-CEILING",
 "AI-LRN-SPECIFIC-TRIGGERS-OVER-BROAD-SKILLS",
 "AI-LRN-STUDY-PASSIVE-TO-ACTIVE-RETRIEVAL",
 "AI-LRN-TRANSFORM-EXISTING-ASSET-BEFORE-RECREATE",
}
REFERENCE_VERIFY_IDS={
 "AI-LRN-PROMPT-MACRO-NOT-NATIVE",
 "AI-LRN-MEMORY-NEED-DOES-NOT-VALIDATE-TOOL",
 "AI-LRN-MCP-DOES-NOT-REPLACE-API",
 "AI-LRN-MEMORY-TOOL-IS-SEPARATE-FROM-MEMORY-PATTERN",
 "AI-LRN-PERSONA-LIBRARY-IS-NOT-AUTONOMOUS-AGENT",
 "AI-LRN-STYLE-SIGNAL-NOT-AUTHORSHIP-PROOF",
}
EXPERIMENT_IDS={
 "AI-LRN-STAGED-ARTIFACT-WORKFLOW",
 "AI-LRN-CONTEXT-CLAIM-NEEDS-MEASUREMENT",
 "AI-LRN-BUDGET-AWARE-MODEL-TIERING",
 "AI-LRN-COST-BOTTLENECK-BEFORE-OPTIMIZATION",
 "AI-LRN-CROSS-MODEL-REVIEW-INDEPENDENCE",
 "AI-LRN-DURABLE-MANUAL-OVER-EPHEMERAL-AGENT",
 "AI-LRN-FAILURE-UPDATES-OPERATING-MANUAL",
 "AI-LRN-INTENT-CONSTRAINTS-SUCCESS-OVER-UNNEEDED-STEPS",
 "AI-LRN-INTERFACE-REASONING-SEPARATION",
 "AI-LRN-LOCAL-EDIT-BEFORE-REGENERATION",
 "AI-LRN-MEMORY-CAPTURE-STORE-RETRIEVE",
 "AI-LRN-PRUNE-STALE-SCAFFOLDING",
 "AI-LRN-SURFACE-SELECTION-BY-JOB-DIMENSION",
 "AI-LRN-TOOL-OVERHEAD-CAN-NEGATE-SAVINGS",
}

GUARD_MAP={
 "AI-LRN-NECESSITY-BEFORE-ADOPTION":"AI_ADOPTION_GATE",
 "AI-LRN-SECURITY-BEFORE-CREDENTIAL":"AI_ADOPTION_GATE",
 "AI-LRN-SUPPLY-CHAIN-IDENTITY-CHECK":"AI_ADOPTION_GATE",
 "AI-LRN-UPSTREAM-TOOL-CLAIMS-VERIFY":"AI_ADOPTION_GATE",
 "AI-LRN-CAPABILITY-GAP-BEFORE-TOOL":"AI_ADOPTION_GATE",
 "AI-LRN-CONNECTOR-PERMISSION-BOUNDARY":"AI_ADOPTION_GATE",
 "AI-LRN-SENSITIVE-AGENT-ISOLATION":"AI_ADOPTION_GATE",
 "AI-LRN-OBSERVABLE-SUCCESS-CRITERIA":"AI_SUCCESS_EVIDENCE_GATE",
 "AI-LRN-SELF-REPORT-NOT-RUNTIME-PROOF":"AI_SUCCESS_EVIDENCE_GATE",
 "AI-LRN-DEVICE-OBSERVATION-BEFORE-CLOSE":"AI_SUCCESS_EVIDENCE_GATE",
 "AI-LRN-COST-GUARD-AS-CODE":"AI_COST_GUARD",
 "AI-LRN-REVIEW-BUDGET-DOES-NOT-FORCE-PASS":"AI_REVIEW_TERMINATION_GATE",
 "AI-LRN-METADATA-FIRST-FILE-DIAGNOSIS":"AI_COMPUTER_USE_GATE",
 "AI-LRN-SAFE-COMPUTER-USE-SEQUENCE":"AI_COMPUTER_USE_GATE",
}

def classify(learning_id:str)->dict[str,str]:
    if learning_id in NEW_GUARD_IDS:
        return {"state":"ADOPTED_TESTED_NEW_GUARD","next_required":"CAPTURE_REAL_OUTCOMES","implementation_ref":"ENFORCEMENT/ai_execution_guard.py","guard":GUARD_MAP[learning_id]}
    if learning_id in EXISTING_VERIFIED_IDS:
        ref="ENFORCEMENT/execution_checkpoint.py" if "APPROVAL" in learning_id else "ENFORCEMENT/runtime_orchestrator.py"
        return {"state":"ADOPTED_TESTED_EXISTING","next_required":"CAPTURE_REAL_OUTCOMES","implementation_ref":ref}
    if learning_id in Q2_LOCAL_VERIFIED_IDS:
        refs={
          "AI-LRN-SEPARATE-TOOLS-BEFORE-COMBINE":"ENFORCEMENT/ai_execution_guard.py",
          "AI-LRN-REFERENCE-SETS-MUST-NOT-MERGE":"ENFORCEMENT/ai_reference_projection.py",
          "AI-LRN-PUBLIC-ACQUISITION-SEPARATION":"ENFORCEMENT/reference_acquisition_adapter.py",
        }
        return {"state":"ADOPTED_TESTED_Q2","next_required":"CAPTURE_REAL_OUTCOMES","implementation_ref":refs[learning_id]}
    if learning_id in DOMAIN_HANDOFF_IDS:
        return {"state":"DOMAIN_HANDOFF_READY","next_required":"BOUNDED_DOMAIN_APPLICATION_TEST"}
    if learning_id in REFERENCE_VERIFY_IDS:
        return {"state":"REFERENCE_ONLY_VERIFY","next_required":"VERIFY_WHEN_OPERATIONALLY_NEEDED"}
    if learning_id in EXPERIMENT_IDS:
        return {"state":"EXPERIMENT_READY","next_required":"RUN_BOUNDED_EXPERIMENT_WITH_BASELINE_AND_REGRESSION"}
    return {"state":"UNCLASSIFIED","next_required":"MANUAL_REVIEW"}

def build(projection:dict[str,Any])->dict[str,Any]:
    rows=[]
    for x in projection.get("learnings") or []:
        lid=str(x.get("learning_id") or "")
        c=classify(lid)
        rows.append({
          "learning_id":lid,"insight":x.get("insight"),"evidence_refs":x.get("evidence_refs") or [],
          **c,
        })
    states={}
    for r in rows: states[r["state"]]=states.get(r["state"],0)+1
    return {
      "schema":"TAKY_AI_LEARNING_QUEST_QUEUE_V1",
      "authoritative":False,
      "owner":"SYSTEM_GROW",
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "source_learning_count":len(rows),
      "quest_cycle":["LEARNING","TEST","ADOPT_OR_HOLD","OUTCOME","GROWTH"],
      "states":states,
      "all_classified":all(r["state"]!="UNCLASSIFIED" for r in rows),
      "quests":[
        {"quest_id":"AI-Q1-DETERMINISTIC-GUARDS","state":"COMPLETE_LOCAL",
         "scope":"new deterministic guards + existing enforcement confirmation",
         "member_count":states.get("ADOPTED_TESTED_NEW_GUARD",0)+states.get("ADOPTED_TESTED_EXISTING",0)},
        {"quest_id":"AI-Q2-LOCAL-STRUCTURAL-VALIDATION","state":"COMPLETE_LOCAL",
         "member_count":states.get("ADOPTED_TESTED_Q2",0)},
        {"quest_id":"AI-Q3-BOUNDED-EXPERIMENTS","state":"OPEN",
         "member_count":states.get("EXPERIMENT_READY",0)},
        {"quest_id":"AI-Q4-DOMAIN-APPLICATION","state":"OPEN",
         "member_count":states.get("DOMAIN_HANDOFF_READY",0)},
        {"quest_id":"AI-Q5-VERIFY-WHEN-NEEDED","state":"OPEN_ON_DEMAND",
         "member_count":states.get("REFERENCE_ONLY_VERIFY",0)},
      ],
      "items":rows,
      "guards":["LEARNING != AUTO_PROMOTION","TEST_BEFORE_ADOPTION","OUTCOME_REQUIRED_FOR_GROWTH","NO_CANONICAL_PROMOTION"],
    }

def refresh(repo_root:Path)->dict[str,Any]:
    src=repo_root/"CURRENT"/"DATA"/"AI_LEARNING_PROJECTION.json"
    out=repo_root/"CURRENT"/"DATA"/"AI_LEARNING_QUEST_QUEUE.json"
    data=json.loads(src.read_text(encoding="utf-8"))
    payload=build(data)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return payload

if __name__=="__main__":
    root=Path(__file__).resolve().parents[1]
    print(json.dumps(refresh(root),ensure_ascii=False,indent=2))
