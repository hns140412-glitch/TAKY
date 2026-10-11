from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional


FINAL_REUSE = {"LOCKED", "USER_APPROVED", "QA_PASS"}
REVIEW_FIRST = {"CANDIDATE"}
REGENERATABLE = {"REJECTED"}


@dataclass(frozen=True)
class VoiceAssetRequest:
    semantic_asset_key: str
    role: str
    locale: str
    text: str
    voice_family: Optional[str] = None
    character_id: Optional[str] = None
    intent: Optional[str] = None


@dataclass(frozen=True)
class RouteDecision:
    route: str
    reason: str
    asset_id: Optional[str] = None
    next_action: Optional[str] = None


def _same_semantic_key(asset: Mapping[str, object], request: VoiceAssetRequest) -> bool:
    return str(asset.get("semantic_asset_key") or "") == request.semantic_asset_key


def route_voice_asset(
    request: VoiceAssetRequest,
    assets: Iterable[Mapping[str, object]],
) -> RouteDecision:
    """
    TAKY shepherding rule:
    - guide to reuse when a usable equivalent already exists;
    - guide to review when only a candidate exists;
    - guide to regenerate only from an explicitly rejected predecessor;
    - guide to create when no semantic equivalent exists.

    This router does not hard-block the executor. It returns the correct route and
    the evidence/reason that must accompany the next action.
    """
    matches = [a for a in assets if _same_semantic_key(a, request)]

    for status in ("LOCKED", "USER_APPROVED", "QA_PASS"):
        hit = next((a for a in matches if str(a.get("status")) == status), None)
        if hit:
            return RouteDecision(
                route="REUSE_EXISTING",
                reason=f"{status} semantic equivalent exists",
                asset_id=str(hit.get("asset_id") or ""),
                next_action="Bind the existing asset to the requesting UI/runtime surface; do not generate a duplicate.",
            )

    candidate = next((a for a in matches if str(a.get("status")) in REVIEW_FIRST), None)
    if candidate:
        return RouteDecision(
            route="REVIEW_EXISTING_CANDIDATE",
            reason="A semantic-equivalent CANDIDATE already exists",
            asset_id=str(candidate.get("asset_id") or ""),
            next_action="Listen/review this candidate first; approve, reject, or revise its metadata before requesting another generation.",
        )

    rejected = next((a for a in matches if str(a.get("status")) in REGENERATABLE), None)
    if rejected:
        return RouteDecision(
            route="REGENERATE_WITH_REASON",
            reason="Only a REJECTED semantic-equivalent asset exists",
            asset_id=str(rejected.get("asset_id") or ""),
            next_action="Generate a replacement only after carrying forward the rejection reason and predecessor asset id.",
        )

    return RouteDecision(
        route="CREATE_NEW",
        reason="No semantic-equivalent asset exists",
        next_action="Create one bounded candidate, record cost/voice/model/settings, then return to QA before any batch expansion.",
    )


def semantic_asset_key(
    *,
    role: str,
    locale: str,
    meaning: str,
    voice_family: Optional[str] = None,
    character_id: Optional[str] = None,
    intent: Optional[str] = None,
) -> str:
    parts = [
        role.strip().upper(),
        locale.strip().lower(),
        (voice_family or "-").strip().upper(),
        (character_id or "-").strip().upper(),
        (intent or "-").strip().upper(),
        " ".join(meaning.split()).strip().lower(),
    ]
    return "|".join(parts)
