#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "governance" / "ui-generation-contract.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def fail(msgs):
    for m in msgs:
        print("FAIL:", m)
    return 1

def validate(req, contract):
    errors = []
    screen_id = req.get("screen_id")
    screens = contract["screen_contracts"]

    if screen_id not in screens:
        errors.append(f"unauthorized screen_id: {screen_id!r}")
        return errors

    if req.get("output", {}).get("one_screen_per_image") is not True:
        errors.append("one_screen_per_image must be true")
    if req.get("output", {}).get("device") != "iphone_portrait":
        errors.append("device must be iphone_portrait")
    if req.get("output", {}).get("multiple_phones", 0) not in (0, 1):
        errors.append("multiple phones/poster boards are forbidden")
    if req.get("output", {}).get("poster") is True:
        errors.append("poster layout is forbidden")

    sc = screens[screen_id]
    user_char = bool(req.get("entities", {}).get("user_character"))
    if not sc.get("user_character_allowed", False) and user_char:
        errors.append(f"user character forbidden at {screen_id}")

    crew_ids = req.get("entities", {}).get("crew_ids", [])
    allowed = set(["dooby","lori","ink","nova","take","zero"])
    unknown = sorted(set(crew_ids) - allowed)
    if unknown:
        errors.append("invented/noncanonical crew ids: " + ", ".join(unknown))

    forb = set(contract.get("global_forbidden", [])) | set(sc.get("forbidden", []))
    features = set(req.get("features", []))
    bad = sorted(forb & features)
    if bad:
        errors.append("forbidden features: " + ", ".join(bad))

    if screen_id == "CHARACTER_PREP":
        choices = req.get("choice_sets", {})
        expected = sc["required_choice_sets"]
        if choices.get("round_1") != expected["round_1"]:
            errors.append("ROUND 1 labels/order must match canonical exactly")
        if choices.get("round_2") != expected["round_2"]:
            errors.append("ROUND 2 labels/order must match canonical exactly")

    if screen_id == "CHARACTER_REVEAL":
        if req.get("candidate_count") != 3:
            errors.append("A/B/C candidate_count must be exactly 3")
        if req.get("same_child") is not True:
            errors.append("A/B/C must be the same child")

    if screen_id == "SHARED_EXPEDITION_ACCENT":
        if req.get("shared_expedition_accent") is not True:
            errors.append("shared_expedition_accent must be true")

    if screen_id == "WORLD_ENTRY":
        steps = req.get("world_entry_steps", [])
        if steps != sc["required_steps"]:
            errors.append("world entry steps are missing/reordered")

    if screen_id == "READY_WEEKLY":
        if req.get("planner_first") is not True:
            errors.append("Ready Weekly must be planner_first")
        present = set(req.get("required_components", []))
        missing = [x for x in sc["required"] if x not in present]
        if missing:
            errors.append("Ready Weekly missing: " + ", ".join(missing))

    if req.get("tts", {}).get("actual_speech") is True:
        errors.append("actual TTS speech is HOLD")

    return errors

def self_test(contract):
    good = {
        "screen_id":"CHARACTER_PREP",
        "output":{"one_screen_per_image":True,"device":"iphone_portrait","multiple_phones":1,"poster":False},
        "entities":{"user_character":False,"crew_ids":[]},
        "choice_sets":{
            "round_1":["신나고 발랄하게","따뜻하고 다정하게","차분하고 똑똑하게"],
            "round_2":["가볍고 활동적인 모습","편안하고 자연스러운 모습","조금 더 모험가다운 모습"]
        },
        "features":[],
        "tts":{"actual_speech":False}
    }
    bad = dict(good)
    bad["entities"] = {"user_character": True, "crew_ids":["made_up"]}
    if validate(good, contract):
        return ["self-test: valid manifest was rejected"]
    if not validate(bad, contract):
        return ["self-test: invalid manifest was accepted"]
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
        sys.exit(fail(errors))
    if args.self_test:
        print("PASS: validator self-test")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
