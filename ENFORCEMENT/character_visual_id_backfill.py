import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_BACKFILL_REGISTRY_24_CANDIDATE_2026-10-08.json"
TEMPLATE = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_REGISTRATION_TEMPLATE_V1_CANDIDATE.json"
CARD_DIR = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_CARDS"
OPEN = "OPEN_FROM_APPROVED_SOURCE"

def source_ref(entry):
    if entry["roster_class"] == "CORE6":
        return "drive:1tJ4LMOFJw5gEQWZL0fEKQTrlPAvjRmhQ"
    return "drive:1FaBgowmiDcraIdr9dmGM0pssVrT4lvWI"

def make_card(entry):
    base = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    base["status"] = "BACKFILL_CANDIDATE"
    base["visual_id"] = entry["visual_id"]
    base["revision"] = "BACKFILL_2026-10-08"
    base["display_name_en"] = entry["display_name_en"]
    base["display_name_ko"] = entry.get("display_name_ko", "")
    base["runtime_key"] = entry["runtime_key"]
    base["roster_class"] = entry["roster_class"]
    base["authority"]["approved_source_refs"] = [source_ref(entry)]
    base["authority"]["approval_ref"] = "INHERITED_EXISTING_APPROVED_SOURCE"
    base["authority"]["base_asset_policy"] = "INHERIT_EXISTING_APPROVED_ASSET__DO_NOT_REGENERATE"
    base["authority"]["exact_runtime_asset_pointer_status"] = "OPEN_BIND_EXISTING_ASSET_PATH"

    # Never invent identity details during backfill.
    hf = base["identity_lock"]["head_face"]
    hf["shape"] = OPEN
    for key in ["shape","size","spacing","angle","iris_color","distinctive"]:
        hf["eyes"][key] = OPEN
    for key in ["shape","weight"]:
        hf["brows"][key] = OPEN
    for key in ["structure","distinctive"]:
        hf["nose_muzzle_beak"][key] = OPEN
    for key in ["shape","distinctive"]:
        hf["mouth_lips"][key] = OPEN
    hf["ears_horns_antennae"]["structure"] = OPEN
    for key in ["silhouette","texture","hairline_or_pattern"]:
        hf["hair_fur_feather"][key] = OPEN
    hf["base_tone"] = OPEN
    hf["resting_expression"] = OPEN

    body = base["identity_lock"]["body"]
    for key in ["scale_class","head_body_ratio","torso_shoulders","limbs","hand_paw_wing_flipper","foot_leg","tail_appendages","posture_center_of_gravity","silhouette"]:
        body[key] = OPEN

    for key in list(base["detail_anchors"]):
        base["detail_anchors"][key] = OPEN
    base["turnaround_views"] = {
        "status": "APPROVED_BOUND",
        "authority_registry": "/TAKY/HANDOFF/GUIDE_VISUAL_ID_07_24/TAKY_EXPLORER_CREW_TURNAROUND_BINDING_24_LATEST.json",
        "manifest_authority": "PER_MEMBER_MANIFEST_AUTHORITY",
        "detail": "CLOSED__DO_NOT_REBUILD_OR_REBIND"
    }

    base["variable_derivatives"] = {
        "expression_states": ["OPEN"],
        "phoneme_mouth_states": ["OPEN_IF_NEEDED"],
        "gaze_states": ["OPEN"],
        "action_states": ["OPEN"],
        "tool_states": ["OPEN"],
        "event_accessories": ["OPEN_OPTIONAL"],
    }
    base["identity_fingerprint"]["digest"] = None
    base["identity_fingerprint"]["status"] = "OPEN_UNTIL_LOCK_FIELDS_BACKFILLED"
    base["runtime"] = {
        "base_asset_status": "INHERITED_EXISTS",
        "base_asset_refs": [],
        "face_sheet_refs": [],
        "action_sheet_refs": [],
        "derived_part_refs": [],
        "fallback": "BASE_BODY_NEUTRAL_POSE",
    }
    base["qa_flags"] = entry.get("qa_flags", [])
    base["forbidden_aliases"] = entry.get("forbidden_aliases", [])
    base["backfill_rule"] = "NO_GUESSING__ONLY_APPROVED_SOURCE_EVIDENCE"
    return base

def generate_missing():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    created = []
    preserved = []
    for entry in registry["roster"]:
        path = ROOT / entry["card_path"]
        if path.exists():
            preserved.append(path.name)
            continue
        path.write_text(json.dumps(make_card(entry), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created.append(path.name)
    return created, preserved

def validate():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors = []
    roster = registry.get("roster", [])
    if len(roster) != 24:
        errors.append(f"roster count != 24: {len(roster)}")
    ids = [x.get("visual_id") for x in roster]
    if ids != [f"{i:02d}" for i in range(1,25)]:
        errors.append("visual IDs must be exactly 01..24")
    if not registry.get("invariants", {}).get("base_regeneration_forbidden"):
        errors.append("base regeneration must remain forbidden")
    id24 = next((x for x in roster if x.get("visual_id") == "24"), None)
    if not id24 or id24.get("display_name_en") != "VIVI" or id24.get("display_name_ko") != "비비":
        errors.append("ID24 canonical must be VIVI/비비")
    if not id24 or "NOVA" not in id24.get("forbidden_aliases", []):
        errors.append("ID24 must forbid NOVA alias")

    for entry in roster:
        path = ROOT / entry["card_path"]
        if not path.exists():
            errors.append(f"missing card: {entry['card_path']}")
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        if card.get("visual_id") != entry["visual_id"]:
            errors.append(f"{entry['visual_id']}: card ID mismatch")
        if card.get("runtime", {}).get("base_asset_status") != "INHERITED_EXISTS":
            errors.append(f"{entry['visual_id']}: base asset must be inherited")
        if card.get("authority", {}).get("base_asset_policy") != "INHERIT_EXISTING_APPROVED_ASSET__DO_NOT_REGENERATE":
            errors.append(f"{entry['visual_id']}: base asset policy drift")
        if card.get("backfill_rule") != "NO_GUESSING__ONLY_APPROVED_SOURCE_EVIDENCE":
            errors.append(f"{entry['visual_id']}: no-guessing rule missing")
        tv = card.get("turnaround_views", {})
        if tv.get("status") != "APPROVED_BOUND":
            errors.append(f"{entry['visual_id']}: turnaround must remain APPROVED_BOUND")
        if tv.get("detail") != "CLOSED__DO_NOT_REBUILD_OR_REBIND":
            errors.append(f"{entry['visual_id']}: turnaround binding must remain CLOSED")
        if entry["visual_id"] == "24" and "NOVA" not in card.get("forbidden_aliases", []):
            errors.append("24: card must forbid NOVA alias")
    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-missing", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.generate_missing:
        created, preserved = generate_missing()
        print(f"CREATED={len(created)} PRESERVED={len(preserved)}")
    if args.validate:
        errors = validate()
        if errors:
            raise SystemExit("\n".join(errors))
        print("PASS: 24/24 Visual ID backfill cards")
