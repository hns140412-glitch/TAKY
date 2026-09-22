#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "governance" / "ui-generation-contract.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def err(errors, message):
    errors.append(message)

def validate(req, contract):
    errors = []
    sid = req.get("screen_id")
    screens = contract["screen_contracts"]
    if sid not in screens:
        return [f"unknown screen_id: {sid!r}"]

    out = req.get("output", {})
    oc = contract["output_contract"]
    if out.get("artifact") != oc["artifact"]:
        err(errors, f"artifact must be {oc['artifact']}")
    if out.get("device") != oc["device"]:
        err(errors, f"device must be {oc['device']}")

    sc = screens[sid]

    # Positive sequence contract
    expected_seq = sc.get("sequence")
    if expected_seq is not None and req.get("sequence") != expected_seq:
        err(errors, f"sequence must match canonical: {expected_seq}")

    # Positive required component contract
    required = set(sc.get("required_components", []))
    present = set(req.get("required_components", []))
    missing = sorted(required - present)
    if missing:
        err(errors, "missing required components: " + ", ".join(missing))

    # Exact choice sets where canonical requires exact labels
    exact = sc.get("exact_choice_sets")
    if exact is not None:
        got = req.get("choice_sets", {})
        for key, labels in exact.items():
            if got.get(key) != labels:
                err(errors, f"{key} must match canonical labels/order exactly")

    # Invariants
    inv = sc.get("invariants", {})
    req_inv = req.get("invariants", {})
    for key, value in inv.items():
        if req_inv.get(key) != value:
            err(errors, f"invariant {key} must be {value!r}")

    # Entity-state checks
    entities = sc.get("entities", {})
    req_entities = req.get("entities", {})
    if entities.get("user_character") == "ABSENT" and req_entities.get("user_character_present") is True:
        err(errors, "user character must be absent at this stage")
    if entities.get("completed_user_character") == "ABSENT" and req_entities.get("completed_user_character_present") is True:
        err(errors, "completed user character must be absent at this stage")

    # Ready hierarchy
    hierarchy = sc.get("hierarchy")
    if hierarchy is not None and req.get("hierarchy") != hierarchy:
        err(errors, f"hierarchy must match canonical: {hierarchy}")

    # Locked Crew Visual ID contract
    crew_contract = contract.get("crew_visual_id_contract", {})
    if entities.get("crew") == "CORE6_CANONICAL":
        canonical_ids = crew_contract.get("canonical_ids", [])
        if req_entities.get("crew_ids") != canonical_ids:
            err(errors, f"crew_ids must match locked canonical order: {canonical_ids}")
        if req_entities.get("crew_visual_id_state") != "HARD_LOCK_REFERENCE":
            err(errors, "crew_visual_id_state must be HARD_LOCK_REFERENCE")

        ref_state = req.get("crew_reference", {})
        render_mode = req.get("crew_render_mode")
        approved_available = ref_state.get("approved_visual_id_available")
        if approved_available is True and render_mode != "LOCKED_ID_DERIVATIVE":
            err(errors, "approved Crew Visual IDs available: render mode must be LOCKED_ID_DERIVATIVE")
        if approved_available is not True and render_mode != "PLACEHOLDER_ONLY":
            err(errors, "without exact approved Crew Visual ID references, render mode must be PLACEHOLDER_ONLY")

        locked = set(crew_contract.get("locked_layers", []))
        mutations = set(req.get("crew_mutations", []))
        illegal = sorted(locked & mutations)
        if illegal:
            err(errors, "Crew locked Visual ID layers may not mutate: " + ", ".join(illegal))

        allowed = set(crew_contract.get("mutable_action_layers", []))
        if sid == "SHARED_EXPEDITION_ACCENT":
            allowed.add("theme_adaptive_apparel_zones")
        unknown_mutations = sorted(mutations - allowed)
        if unknown_mutations:
            err(errors, "unsupported Crew mutation layers: " + ", ".join(unknown_mutations))

    # Critical regression locks only
    if req.get("tts", {}).get("actual_speech") is True:
        err(errors, "actual TTS speech is HOLD")

    return errors

def self_test(contract):
    good = {
      "screen_id":"CHARACTER_PREP",
      "output":{"artifact":"SINGLE_IPHONE_SCREEN","device":"iphone_portrait"},
      "sequence":["SOURCE_PHOTO","SIGNATURE_ITEM","DIRECTION_ROUND_1","DIRECTION_ROUND_2"],
      "required_components":["PHOTO_SOURCE","ROUND_1","ROUND_2","SIGNATURE_ITEM"],
      "choice_sets":{
        "round_1":["신나고 발랄하게","따뜻하고 다정하게","차분하고 똑똑하게"],
        "round_2":["가볍고 활동적인 모습","편안하고 자연스러운 모습","조금 더 모험가다운 모습"]
      },
      "entities":{"completed_user_character_present":False},
      "tts":{"actual_speech":False}
    }
    bad = dict(good)
    bad["sequence"] = ["SOURCE_PHOTO","SIGNATURE_ITEM_PERSISTENCE"]
    if validate(good, contract):
        return ["self-test: valid manifest rejected"]
    if not validate(bad, contract):
        return ["self-test: invalid manifest accepted"]
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="*")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    contract = load_json(CONTRACT_PATH)
    errors = []
    if args.self_test:
        errors.extend(self_test(contract))
    for path in args.manifests:
        req = load_json(path)
        errs = validate(req, contract)
        if errs:
            errors.extend([f"{path}: {e}" for e in errs])
        else:
            print("PASS:", path)
    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    if args.self_test:
        print("PASS: validator self-test")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
