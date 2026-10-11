import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "MASTER" / "TAKY_MOBILE_DESIGN_AUTHORITY_REGISTRY_CANDIDATE_2026-10-07.json"

ORDER = [
    "PROJECT_MASTER_AND_EXPLICIT_USER_RULES",
    "APPROVED_GOLDEN_AND_VISUAL_ID",
    "GOLDEN_JOURNEY_OR_STRONG_CANDIDATE",
    "TAKY_FAMILY_UI_PRINCIPLES",
    "STRUCTURE_ONLY_REFERENCES",
    "EXTERNAL_REFERENCE_PRINCIPLES",
]
REQUIRED_APPS = {"Play-Camp","Ready-Set","Hide-Seek","Snap-Pop"}

def validate(data):
    errors = []
    if data.get("status") != "CANDIDATE_NOT_PROMOTED":
        errors.append("authority candidate must not claim promotion")
    if data.get("authority_order") != ORDER:
        errors.append("authority order drift")
    if not REQUIRED_APPS.issubset(set(data.get("apps", {}))):
        errors.append("required app coverage missing")
    character = data.get("character_visual_id", {})
    if character.get("invariant") != "BASE_IDENTITY_INHERITED__DERIVATIVES_PROGRESSIVE__NO_GUESSING":
        errors.append("character Visual ID invariant drift")
    for rel in [character.get("registration_standard"), character.get("registration_template"), character.get("crew24_backfill_registry")]:
        if not rel or not (ROOT / rel).exists():
            errors.append(f"missing character Visual ID authority file: {rel}")
    event = data.get("event_theme", {})
    if event.get("invariant") != "EVENT_MAY_DECORATE_BUT_MUST_NOT_REWRITE_EXPERIENCE":
        errors.append("event theme invariant drift")
    for rel in [data.get("authority_doc"), event.get("protocol"), event.get("registry")]:
        if not rel or not (ROOT / rel).exists():
            errors.append(f"missing referenced file: {rel}")
    if data.get("external_reference_role") != "VALIDATION_AND_REFINEMENT_ONLY":
        errors.append("external references cannot become design authority")
    device = data.get("device_strategy", {})
    if device.get("dedicated_tablet_ui") != ["Play-Camp"]:
        errors.append("dedicated tablet UI must be Play Camp only")
    if set(device.get("responsive_single_ui", [])) != {"Ready-Set","Hide-Seek","Snap-Pop"}:
        errors.append("Ready/Hide/Snap must remain responsive single-UI consumers")
    play = data.get("apps", {}).get("Play-Camp", {})
    if play.get("device_policy") != "DEDICATED_TABLET_UI":
        errors.append("Play Camp tablet policy drift")
    if play.get("display_name_ko") != "수련 캠프" or play.get("display_name_en") != "Play Camp" or play.get("runtime_id") != "PLAY_CAMP":
        errors.append("Play Camp naming contract drift")
    if play.get("primary_device_mode") != "TABLET" or play.get("tablet_ui_authority") != "SEPARATE_PRIMARY_UI_STANDARD":
        errors.append("Play Camp tablet-primary separate-UI contract drift")
    if play.get("mobile_role") != "SECONDARY_FALLBACK_PRESENTATION":
        errors.append("Play Camp mobile role must remain secondary/fallback")
    tablet_standard = play.get("tablet_ui_standard")
    if tablet_standard != "D:/Git PWA/Play Camp/PLAY_CAMP_TABLET_UI_STANDARD_CANDIDATE_2026-10-07.md":
        errors.append("Play Camp tablet UI standard pointer drift")
    elif not Path(tablet_standard).exists():
        errors.append("Play Camp tablet UI standard file missing")
    review = play.get("tablet_design_gate_review")
    if review != "D:/Git PWA/Play Camp/PLAY_CAMP_TABLET_DESIGN_GATE_REVIEW_2026-10-08.md":
        errors.append("Play Camp tablet design gate review pointer drift")
    elif not Path(review).exists():
        errors.append("Play Camp tablet design gate review file missing")
    if play.get("tablet_design_gate_status") != "CANDIDATE_VISUAL_REVIEW_PASS__GOLDEN_NOT_PROMOTED":
        errors.append("Play Camp tablet design gate status drift")
    binding = play.get("visual_binding_contract")
    if binding != "D:/Git PWA/Play Camp/PLAY_CAMP_VISUAL_BINDING_CONTRACT_CANDIDATE_2026-10-08.md":
        errors.append("Play Camp visual binding contract pointer drift")
    elif not Path(binding).exists():
        errors.append("Play Camp visual binding contract missing")
    if play.get("crew_binding_status") != "BASE_ASSET_INHERITED__EXTRA_PROGRESSIVE":
        errors.append("Play Camp crew base asset must stay inherited while extras remain progressive")
    extra_standard = play.get("crew_additional_asset_standard")
    if extra_standard != "D:/Git PWA/Play Camp/PLAY_CAMP_CREW_ADDITIONAL_ASSET_STANDARD_CANDIDATE_2026-10-08.md":
        errors.append("Play Camp crew additional asset standard pointer drift")
    elif not Path(extra_standard).exists():
        errors.append("Play Camp crew additional asset standard missing")
    extra_contract = play.get("crew_additional_asset_contract")
    if extra_contract != "D:/Git PWA/Play Camp/src/data/crew-additional-asset-contract.v1.json":
        errors.append("Play Camp crew additional asset contract pointer drift")
    elif not Path(extra_contract).exists():
        errors.append("Play Camp crew additional asset contract missing")
    return errors

if __name__ == "__main__":
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errs = validate(data)
    if errs:
        raise SystemExit("\n".join(errs))
    print("PASS: mobile design authority candidate registry")
