#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
Q3=ROOT/"CURRENT"/"DATA"/"AI_BOUNDED_EXPERIMENT_QUEUE.json"
Q4=ROOT/"CURRENT"/"DATA"/"AI_DOMAIN_APPLICATION_QUEUE.json"
Q5=ROOT/"CURRENT"/"DATA"/"AI_VERIFY_ON_NEED_QUEUE.json"

def _load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def _open_ids()->set[str]:
    ids=set()
    q3=_load(Q3)
    for x in q3.get("items") or []:
        if x.get("state") in {"READY_WHEN_REPRESENTATIVE_TASK_EXISTS","INCONCLUSIVE_BASELINE_MISSING"}:
            ids.add(str(x.get("learning_id")))
    q4=_load(Q4)
    for x in q4.get("items") or []:
        if x.get("state")=="READY_FOR_BOUNDED_DOMAIN_TEST":
            ids.add(str(x.get("learning_id")))
    q5=_load(Q5)
    for x in q5.get("items") or []:
        if x.get("state")=="VERIFY_ON_OPERATIONAL_NEED":
            ids.add(str(x.get("learning_id")))
    return ids

def route(task:dict[str,Any])->dict[str,Any]:
    open_ids=_open_ids()
    selected=[]

    def add(lid:str, reason:str):
        if lid in open_ids and lid not in {x["learning_id"] for x in selected}:
            selected.append({"learning_id":lid,"reason":reason})

    if task.get("artifact_production") is True:
        if task.get("representative_baseline_available") is True:
            add("AI-LRN-STAGED-ARTIFACT-WORKFLOW","artifact task has a comparable baseline")
        if task.get("existing_artifact_or_source") is True and task.get("small_correction") is True:
            add("AI-LRN-LOCAL-EDIT-BEFORE-REGENERATION","small correction on an existing artifact")
        if task.get("existing_artifact_or_source") is True:
            add("AI-LRN-TRANSFORM-EXISTING-ASSET-BEFORE-RECREATE","existing approved content/source is available")
        if task.get("editable_output_required") is True:
            add("AI-LRN-HUMAN-EDITABLE-OUTPUT","final artifact must remain human-editable")
        if task.get("visual_design") is True:
            add("AI-LRN-DESIGN-TASTE-AS-EXPLICIT-CONSTRAINT","visual design output requires explicit taste constraints")
            if task.get("approved_source_asset") is True:
                add("AI-LRN-SOURCE-ASSET-QUALITY-SETS-OUTPUT-CEILING","approved source asset drives the creative result")

    if task.get("learning_flow") is True and task.get("learner_response_available") is True:
        if task.get("ai_literacy_topic") is True:
            add("AI-LRN-FLUENCY-INCLUDES-DISCERNMENT-AND-RESPONSIBILITY","AI-literacy flow has observable learner response")
            add("AI-LRN-LITERACY-BEFORE-TOOL-SPEED","AI-literacy flow can test understanding before tool speed")
            add("AI-LRN-MENTAL-MODEL-OF-CAPABILITIES-AND-LIMITS","AI-literacy flow can test capability/limit understanding")
        if task.get("multiple_representations") is True:
            add("AI-LRN-MULTIPLE-REPRESENTATIONS-FOR-LEARNING","same learning target is represented in multiple forms")

    if task.get("model_routing") is True and task.get("cost_telemetry_available") is True:
        add("AI-LRN-BUDGET-AWARE-MODEL-TIERING","model routing has comparable quality and cost telemetry")
    if task.get("overspecified_instruction_candidate") is True and task.get("reversible_task") is True:
        add("AI-LRN-INTENT-CONSTRAINTS-SUCCESS-OVER-UNNEEDED-STEPS","reversible task allows instruction ablation")
    if task.get("ui_reasoning_split_candidate") is True:
        add("AI-LRN-INTERFACE-REASONING-SEPARATION","task has a genuine interface/reasoning boundary")
    if task.get("multiple_surfaces_candidate") is True:
        add("AI-LRN-SURFACE-SELECTION-BY-JOB-DIMENSION","task can be routed across multiple product surfaces")
    if task.get("repeatable_workflow") is True and task.get("independent_repeat_available") is True:
        add("AI-LRN-DURABLE-MANUAL-OVER-EPHEMERAL-AGENT","repeatable task can compare durable manual vs session-only execution")

    # Verify-on-need items are routed only when a real task depends on the claim.
    if task.get("current_product_fact_dependency") is True:
        for lid in [
            "AI-LRN-PROMPT-MACRO-NOT-NATIVE",
            "AI-LRN-MEMORY-NEED-DOES-NOT-VALIDATE-TOOL",
            "AI-LRN-MCP-DOES-NOT-REPLACE-API",
            "AI-LRN-MEMORY-TOOL-IS-SEPARATE-FROM-MEMORY-PATTERN",
            "AI-LRN-PERSONA-LIBRARY-IS-NOT-AUTONOMOUS-AGENT",
        ]:
            add(lid,"current operational decision depends on this reference claim")

    return {
        "schema":"TAKY_AI_OPEN_QUEST_ROUTE_V1",
        "advisory":True,
        "selected_count":len(selected),
        "selected":selected,
        "guards":["ONLY_CURRENT_OPEN_QUESTS","NO_AUTO_ADOPTION","NO_REMOTE_CALL_JUST_FOR_QUEST_MATCHING"],
    }
