import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "MASTER" / "EVENT_THEME_REGISTRY_CANDIDATE_2026-10-07.json"

REQUIRED_IMMUTABLE = {
    "layout","navigation_model","learning_logic","primary_action_hierarchy",
    "touch_targets","character_visual_id","timer_semantics","planner_semantics"
}
PROHIBITED_RENDER = {
    "layout_rewrite","navigation_rewrite","learning_rule_change",
    "character_identity_change","baked_live_text","baked_user_data","baked_controls"
}
VALID_TONES = {"CELEBRATION","SEASONAL","TRADITIONAL","NATIONAL_COMMEMORATION","MEMORIAL"}
VALID_TRIGGERS = {"FIXED_DATE","LUNAR_RESOLVER","USER_DATE","MANUAL_OVERRIDE"}

def validate(data):
    errors = []
    if data.get("status") != "CANDIDATE_NOT_PROMOTED":
        errors.append("candidate status must stay explicit until promotion")
    if not REQUIRED_IMMUTABLE.issubset(set(data.get("immutable", []))):
        errors.append("immutable design invariants incomplete")
    if not PROHIBITED_RENDER.issubset(set(data.get("render_contract", {}).get("prohibited", []))):
        errors.append("prohibited render mutations incomplete")
    ids = set()
    for event in data.get("events", []):
        eid = event.get("id")
        if not eid or eid in ids:
            errors.append(f"invalid/duplicate event id: {eid}")
        ids.add(eid)
        if event.get("tone") not in VALID_TONES:
            errors.append(f"{eid}: invalid tone")
        trigger = event.get("trigger", {})
        if trigger.get("kind") not in VALID_TRIGGERS:
            errors.append(f"{eid}: invalid trigger")
        if trigger.get("kind") == "LUNAR_RESOLVER" and trigger.get("calendar") != "KOREAN_LUNAR":
            errors.append(f"{eid}: lunar event must use KOREAN_LUNAR resolver")
    memorial = next((e for e in data.get("events", []) if e.get("id") == "memorial_day"), None)
    if not memorial or memorial.get("tone") != "MEMORIAL":
        errors.append("Memorial Day must remain MEMORIAL")
    return errors

if __name__ == "__main__":
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    errs = validate(data)
    if errs:
        raise SystemExit("\n".join(errs))
    print(f"PASS: {len(data['events'])} event themes validated")
