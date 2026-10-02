from pathlib import Path

crew=Path("OS/EXPLORATION_CREW_CANONICAL.md").read_text(encoding="utf-8")
rel=Path("OS/GUIDE_CHARACTER_RELATIONSHIP.md").read_text(encoding="utf-8")

required_crew=[
    "CANONICAL V2 / MAIN CLOSED",
    "PR #193 MERGED",
    "PR #191 remains Draft/Open",
    "Ready consumer V2 is CLOSED on Ready main",
    "Hide/Snap consumer promotion/reapplication remains OPEN",
    "Old PR #10 onboarding lineage is LEGACY_REFERENCE_ONLY",
    "RUNTIME_POLICY",
    "thin arbitration only",
    "DIALOGUE / SCENE",
    "INTERACTION / RELATION / MEMORY UPDATE",
    "UNIFIED_RUNTIME_TRACE",
    "Semantic interaction and delivery axes",
    "TEXT_AND_VOICE",
    "STATIC_APPROVED_ONLY",
    "COMPOSABLE_ACTION_APPROVED",
    "MOTION_RENDER_PLAN_READY",
    "CREW_RUNTIME_TRACE_V2",
    "runtime_policy_not_behavior_owner = true",
    "Runtime V2 ownership and Source Lock",
    "EXPLORER_CREW_SYSTEM_V2",
    "runtime = CANONICAL_ONLY",
    "behaviorOwner=false",
    "relationOwner=false",
    "memoryOwner=false",
    "assetResolver=false",
    "runtimeOwner=false",
    "current Source Lock scope = 34",
    "CRLF/LF normalized to LF",
]
required_rel=[
    "CANONICAL 24-PERSON RELATIONSHIP LIFECYCLE",
    "FIRST ENCOUNTER remains Core6 only",
    "Canonical ID24 = `VIVI / 비비`",
    "UNSEEN → FIRST_ENCOUNTER → KNOWN → AFFINITY_BUILDING → COMPANION_AVAILABLE → COMPANION → MAIN_COMPANION",
    "RELATION EVIDENCE / STORY GATE",
    "character_id + story_gate_id + evidence_ref",
    "PERSONALITY PROVENANCE BOUNDARY",
    "13–18: user-authorized derived profile",
]
for token in required_crew:
    assert token in crew, token
for token in required_rel:
    assert token in rel, token

for forbidden in [
    "DRAFT RUNTIME V2 CUTOVER CANDIDATE",
    "ACTIVE MAIN REMAINS AUTHORITY UNTIL MERGE",
    "Central semantic contract: DRAFT",
    "initial 5–6 selection requirement = REQUIRED",
    "Core6-only runtime roster = REQUIRED",
    "asset readiness determines relationship eligibility",
]:
    assert forbidden not in crew + rel, forbidden

assert "SPECIAL FRIEND ≠ RANDOM GUEST" in rel
assert "Name/code-only image generation is prohibited." in crew
print("EXPLORER_CREW_CANONICAL_CORRECTION_PASS")
