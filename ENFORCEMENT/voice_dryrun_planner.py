from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from voice_asset_reuse_router import VoiceAssetRequest, route_voice_asset, semantic_asset_key


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "CURRENT" / "VOICE_ASSET_REGISTRY_CURRENT.json"
REQUEST = ROOT / "CURRENT" / "VOICE_ELEVENLABS_DRYRUN_CURRENT.json"
RECEIPT = ROOT / "CURRENT" / "VOICE_ELEVENLABS_DRYRUN_ROUTE_RECEIPT_CURRENT.json"


def _meaning_for(step: dict[str, Any]) -> str:
    return str(step.get("preview_text") or step.get("text") or step.get("type") or "").strip()


def _technical_allowance(request: dict[str, Any], step: dict[str, Any]) -> dict[str, Any] | None:
    if step.get("dryrun_exception") != "EXPLICIT_DRYRUN_ALLOWANCE":
        return None

    allowance = request.get("technical_probe_allowance") or {}
    if request.get("explicit_user_authorization") is not True:
        raise RuntimeError("technical dry-run requires explicit user authorization")
    if allowance.get("enabled") is not True:
        raise RuntimeError("technical dry-run allowance is disabled")
    if step.get("type") != "TECHNICAL_TTS":
        raise RuntimeError("dry-run allowance applies only to TECHNICAL_TTS")
    if step.get("generation_reason") != "TECHNICAL_DRY_RUN":
        raise RuntimeError("technical dry-run requires TECHNICAL_DRY_RUN reason")
    if step.get("production_candidate") is not False:
        raise RuntimeError("technical dry-run must not be registered as a production candidate")

    max_calls = int(allowance.get("max_generation_calls", 1))
    step_calls = int(step.get("max_calls", 1))
    if step_calls != 1 or max_calls != 1:
        raise RuntimeError("technical dry-run is exactly one generation call")

    text = _meaning_for(step)
    max_chars = int(allowance.get("max_text_chars", 60))
    if not text or len(text) > max_chars:
        raise RuntimeError(f"technical dry-run text exceeds allowance: {len(text)} > {max_chars}")

    if int(allowance.get("retries_allowed", 0)) != 0:
        raise RuntimeError("technical dry-run retries must stay disabled")

    return {
        "route": "DRYRUN_TECHNICAL_ALLOWED",
        "reason": "Explicit user-authorized one-call connectivity probe",
        "asset_id": None,
        "next_action": "Run exactly one short TTS call, record the result/usage if exposed, then stop. Do not promote this clip as a production asset.",
    }


def plan() -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    assets = registry.get("assets", [])
    hard_cap = float(request["hard_credit_cap"])

    if hard_cap > 500:
        raise RuntimeError(f"dry-run hard cap exceeds authority: {hard_cap}")

    paid_calls = 0
    technical_calls = 0
    routed_steps: list[dict[str, Any]] = []

    for step in request.get("steps", []):
        item = dict(step)
        if not step.get("paid_generation"):
            item["route"] = "READ_ONLY_OPTIONAL" if not step.get("required", False) else "READ_ONLY"
            routed_steps.append(item)
            continue

        paid_calls += int(step.get("max_calls", 1))
        allowance = _technical_allowance(request, step)
        if allowance is not None:
            technical_calls += 1
            item["route_decision"] = allowance
            item["semantic_asset_key"] = None
            routed_steps.append(item)
            continue

        role = str(step["role"])
        locale = str(step["locale"])
        meaning = _meaning_for(step)
        intent = str(step.get("type") or "DRY_RUN")
        key = semantic_asset_key(
            role=role,
            locale=locale,
            intent=intent,
            meaning=meaning,
        )
        decision = route_voice_asset(
            VoiceAssetRequest(
                semantic_asset_key=key,
                role=role,
                locale=locale,
                text=meaning,
                intent=intent,
            ),
            assets,
        )
        item["semantic_asset_key"] = key
        item["route_decision"] = asdict(decision)
        routed_steps.append(item)

    if paid_calls != 1:
        raise RuntimeError(f"this technical dry-run must contain exactly 1 paid call, found {paid_calls}")
    if technical_calls != 1:
        raise RuntimeError(f"this technical dry-run must contain exactly 1 allowance call, found {technical_calls}")

    result = {
        "schema_version": "TAKY_ELEVENLABS_DRYRUN_ROUTE_RECEIPT_V2",
        "request_id": request["request_id"],
        "hard_credit_cap": hard_cap,
        "paid_call_budget": paid_calls,
        "route_policy": "ROUTE_BEFORE_CREATE_WITH_TECHNICAL_ALLOWANCE",
        "registry_asset_count": len(assets),
        "steps": routed_steps,
        "preflight": {
            "explicit_user_authorization": True,
            "cap_le_500": True,
            "paid_calls_exactly_1": True,
            "technical_probe_exactly_1": True,
            "usage_before_non_blocking": True,
            "retries_allowed": 0,
            "batch_generation": False,
            "voice_design_in_same_run": False,
        },
        "status": "READY_FOR_SINGLE_TECHNICAL_TTS",
    }
    RECEIPT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    receipt = plan()
    print(json.dumps(receipt["preflight"], ensure_ascii=False))
    for step in receipt["steps"]:
        if step.get("paid_generation"):
            d = step["route_decision"]
            print(step["id"], d["route"], d["reason"])
    print("receipt=" + str(RECEIPT))
