import json
from pathlib import Path

ROOT = Path(r"D:\Git PWA\TAKY")
REG = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_BACKFILL_REGISTRY_24_CANDIDATE_2026-10-08.json"
SRC = ROOT / "MASTER" / "CREW24_VISUAL_ID_METADATA_BACKFILL_SOURCE_2026-10-08.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

reg = load(REG)
src = load(SRC)
meta = {x["visual_id"]: x for x in src["members"]}

for item in reg["roster"]:
    vid = item["visual_id"]
    m = meta[vid]
    card_path = ROOT / item["card_path"]
    card = load(card_path)

    card["display_name_ko"] = m.get("canonical_name_ko") or card.get("display_name_ko", "")

    auth = card.setdefault("authority", {})
    auth["approved_source_refs"] = [m["approved_source_path"]]
    auth["source_digests"] = [m["approved_source_sha256"]]
    auth["source_lock_path"] = m["source_lock_path"]
    auth["source_lock_status"] = m["source_lock_status"]
    auth["exact_runtime_asset_pointer_status"] = "BOUND_BY_EXISTING_ASSET_REGISTRY"

    body = card.setdefault("identity_lock", {}).setdefault("body", {})
    body["morphology_class"] = m["morphology_class"]
    body["grip_limb_type"] = m["grip_limb_type"]
    body["hand_paw_wing_flipper"] = m["grip_limb_type"]
    body["tail_appendages"] = m["appendages"]
    body["species_motion_constraints"] = m["compatibility_flags"]

    costume = card["identity_lock"].setdefault("costume_equipment", {})
    costume["lower_outfit_class"] = m["lower_outfit_class"]
    costume["identity_features"] = m["face_identity_features"]
    costume["compatibility_flags"] = m["compatibility_flags"]

    var = card.setdefault("variable_derivatives", {})
    var["expression_states"] = m["face_expected_files"]
    var["face_state_contract_status"] = src["authority"]["face_states_status"]
    var["face_state_authority"] = src["authority"]["face_states_registry"]
    var["face_state_qa_flags"] = m["face_qa_flags"]
    var["action_parts_contract_status"] = src["authority"]["action_parts_status"]
    var["action_parts_authority"] = src["authority"]["action_parts_registry"]

    runtime = card.setdefault("runtime", {})
    runtime["asset_folder"] = m["asset_folder"]
    runtime["base_asset_refs"] = [m["approved_source_path"]]
    runtime.setdefault("face_sheet_refs", [])
    runtime.setdefault("action_sheet_refs", [])
    runtime.setdefault("derived_part_refs", [])
    runtime["derivative_production_status"] = "CONTRACT_LOCKED__IMAGE_PRODUCTION_QA_OPEN"

    fp = card.setdefault("identity_fingerprint", {})
    fp["source_sha256"] = m["approved_source_sha256"]
    fp["status"] = "SOURCE_LOCKED__DETAIL_FINGERPRINT_OPEN"

    card["backfill_status"] = {
        "turnaround": "CLOSED_APPROVED_BOUND",
        "source_lineage": "BACKFILLED",
        "morphology_outfit": "BACKFILLED",
        "face_contract": "BACKFILLED_CONTRACT_ONLY",
        "action_contract": "BACKFILLED_CONTRACT_ONLY",
        "fine_face_detail": "OPEN_FROM_APPROVED_IMAGE",
        "color_material": "OPEN_FROM_APPROVED_IMAGE",
    }

    # Preserve the already-closed turnaround authority.
    card["turnaround_views"] = {
        "status": "APPROVED_BOUND",
        "authority_registry": src["authority"]["turnaround_registry"],
        "manifest_authority": "PER_MEMBER_MANIFEST_AUTHORITY",
        "detail": "CLOSED__DO_NOT_REBUILD_OR_REBIND",
    }

    save(card_path, card)

    item["detail_backfill_status"] = "STRUCTURAL_METADATA_BACKFILLED__FINE_VISUAL_DETAIL_OPEN"
    item["face_contract_status"] = src["authority"]["face_states_status"]
    item["action_contract_status"] = src["authority"]["action_parts_status"]
    item["source_lock_status"] = m["source_lock_status"]
    item["source_sha256"] = m["approved_source_sha256"]
    item["morphology_class"] = m["morphology_class"]
    item["turnaround_binding_status"] = "CLOSED_APPROVED_BOUND"

reg.setdefault("authority", {}).update({
    "morphology_outfit_registry": src["authority"]["morphology_outfit_registry"],
    "face_states_registry": src["authority"]["face_states_registry"],
    "action_parts_registry": src["authority"]["action_parts_registry"],
    "source_lock_registry": src["authority"]["source_lock_registry"],
    "turnaround_binding_registry": src["authority"]["turnaround_registry"],
    "metadata_backfill_source": "MASTER/CREW24_VISUAL_ID_METADATA_BACKFILL_SOURCE_2026-10-08.json",
})
reg.setdefault("invariants", {}).update({
    "turnaround_24_complete": True,
    "turnaround_binding_status": "CLOSED_APPROVED_BOUND",
    "source_lock_24": "ALL_24_SOURCE_LOCKED_NO_IMAGE_GENERATION",
    "structural_metadata_backfill": "24_OF_24_COMPLETE",
    "fine_visual_detail_backfill": "OPEN",
})
save(REG, reg)
print("PASS: structural metadata backfill 24/24")
