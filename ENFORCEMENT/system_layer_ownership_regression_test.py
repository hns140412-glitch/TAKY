#!/usr/bin/env python3
"""Negative regression for the source-owned Planner/FACT support-map boundary.

This tests document/validator consistency only, not a deployed Planner runtime.
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = json.loads((ROOT / "MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json").read_text(encoding="utf-8"))
VALIDATOR = ROOT / "ENFORCEMENT/system_layer_ownership_validator.py"


def run_case(label, payload, expected_exit, expected_marker):
    with tempfile.TemporaryDirectory(prefix="taky-planner-map-") as temp:
        root = Path(temp)
        (root / "MASTER").mkdir()
        (root / "ENFORCEMENT").mkdir()
        (root / "MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        shutil.copyfile(VALIDATOR, root / "ENFORCEMENT/system_layer_ownership_validator.py")
        result = subprocess.run(
            [sys.executable, str(root / "ENFORCEMENT/system_layer_ownership_validator.py")],
            capture_output=True, text=True, encoding="utf-8"
        )
        output = result.stdout + result.stderr
        if result.returncode != expected_exit or expected_marker not in output:
            raise AssertionError(
                f"{label}: expected exit={expected_exit} and {expected_marker!r}, "
                f"got exit={result.returncode}: {output}"
            )
        print(f"PASS: {label} (exit={result.returncode})")


run_case("candidate owner map", MAP, 0, "PASS: TAKY/Work/Learning")

missing_planner = copy.deepcopy(MAP)
del missing_planner["layers"]["PLANNER_ENGINE"]
run_case("missing independent Planner blocked", missing_planner, 1, "MISSING_LAYERS:PLANNER_ENGINE")

wrong_parent = copy.deepcopy(MAP)
wrong_parent["layers"]["PLANNER_ENGINE"]["parent"] = "READY_SET"
run_case("Ready-owns-Planner inversion blocked", wrong_parent, 1, "PLANNER_ENGINE_PARENT_INVALID")

missing_fact = copy.deepcopy(MAP)
del missing_fact["layers"]["ASSIGNMENT_FACT_DOMAIN"]
run_case("missing confirmed FACT owner blocked", missing_fact, 1, "MISSING_LAYERS:ASSIGNMENT_FACT_DOMAIN")

wrong_learning_parent = copy.deepcopy(MAP)
wrong_learning_parent["layers"]["LEARNING_ENGINE_CORE"]["parent"] = "LEARNING_OS"
run_case("Learning Engine bypasses domain core blocked", wrong_learning_parent, 1, "LEARNING_ENGINE_CORE_PARENT_INVALID")

wrong_classification = copy.deepcopy(MAP)
next(x for x in wrong_classification["capability_classification"] if x["item"] ==
     "Planner dated allocation, carry-over and cross-app plan/progress meaning")["owner"] = "READY_SET"
run_case("Planner capability wrongly assigned to Ready blocked", wrong_classification, 1,
         "WRONG_CLASSIFICATION:Planner dated allocation")
