import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "MASTER" / "CHARACTER_VISUAL_ID_REGISTRATION_TEMPLATE_V1_CANDIDATE.json"

def validate_template(data):
    errors = []
    if data.get("schema_version") != "TAKY_CHARACTER_VISUAL_ID_REGISTRATION_V1_CANDIDATE":
        errors.append("visual-id registration schema drift")
    identity = data.get("identity_lock", {})
    for key in ["head_face","body","costume_equipment","color_material_palette"]:
        if key not in identity:
            errors.append(f"missing identity lock section: {key}")
    if "expression_states" not in data.get("variable_derivatives", {}):
        errors.append("expression states must remain variable derivatives")
    gate = data.get("gate", {})
    if gate.get("actual_image_review_required") is not True:
        errors.append("actual image review must be required")
    if gate.get("app_may_reinterpret_identity") is not False:
        errors.append("apps must not reinterpret character identity")
    if gate.get("registration_image_generation_forbidden") is not True:
        errors.append("Visual ID registration image generation must remain forbidden")
    if gate.get("generated_reference_sheet_is_asset") is not False:
        errors.append("generated reference sheet must never be treated as an asset")
    if data.get("identity_fingerprint", {}).get("algorithm") != "SOURCE_DIGEST_PLUS_CANONICAL_LOCK_FIELDS":
        errors.append("identity fingerprint contract drift")
    authority = data.get("authority", {})
    if authority.get("drive_document_id") != "1147YLCEYO3jI6iAYGgyZszZwhF8risUldnTJQJz-y0M":
        errors.append("visual-id registration Drive authority pointer drift")
    return errors

if __name__ == "__main__":
    data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    errors = validate_template(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print("PASS: character visual-id registration template")
