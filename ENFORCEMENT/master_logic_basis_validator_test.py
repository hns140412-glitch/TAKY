#!/usr/bin/env python3
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import master_logic_basis_validator as basis  # noqa: E402

MASTER_TEXT = (ROOT / "MASTER" / "MASTER_LOGIC.md").read_text(encoding="utf-8")
MAP_DATA = json.loads((ROOT / "MASTER" / "SYSTEM_LAYER_OWNERSHIP_MAP.json").read_text(encoding="utf-8"))
OWNERSHIP_VALIDATOR = HERE / "system_layer_ownership_validator.py"


def mutate(old, new):
    assert old in MASTER_TEXT, old
    return MASTER_TEXT.replace(old, new, 1)


class MasterLogicBasisTest(unittest.TestCase):
    def test_current_master_passes(self):
        self.assertEqual(basis.validate(MASTER_TEXT), [])

    def test_sixth_gate_rejected(self):
        text = mutate("exactly `KEY / CONTEXT / ROUTE / COST / DONE`", "exactly `KEY / CONTEXT / ROUTE / COST / DONE / NECESSITY`")
        self.assertIn("SIXTH_HARD_GATE", basis.validate(text))

    def test_necessity_as_gate_rejected(self):
        text = mutate("It SHALL NOT become a sixth hard gate.", "Necessity is a sixth hard gate.")
        fail = basis.validate(text)
        self.assertIn("NECESSITY_PROMOTED_TO_GATE", fail)
        self.assertIn("MISSING_BASIS_TOKEN:It SHALL NOT become a sixth hard gate.", fail)

    def test_vendor_as_role_ontology_rejected(self):
        text = mutate("`NAVIGATOR` (direction", "`NAVIGATOR` = Claude (direction")
        self.assertIn("VENDOR_NAME_IN_ROLE_BASIS:Claude", basis.validate(text))

    def test_mandatory_agent_spawn_loss_rejected(self):
        text = mutate("SHALL NOT require spawning one agent or AI call per role", "requires one agent per role")
        self.assertTrue(any("spawning one agent" in x for x in basis.validate(text)))

    def test_candidate_promotion_rejected(self):
        text = mutate("Implementation-reconciliation candidates", "V3 is promoted to canonical. Implementation-reconciliation candidates")
        self.assertIn("CANDIDATE_PROMOTED_TO_CANONICAL", basis.validate(text))

    def test_acceptance_floor_loss_rejected(self):
        text = mutate("`CHEAPEST != CHEAPEST_SUFFICIENT`", "cheapest wins")
        self.assertIn("MISSING_BASIS_TOKEN:`CHEAPEST != CHEAPEST_SUFFICIENT`", basis.validate(text))

    def test_user_confirmation_distinction_loss_rejected(self):
        text = mutate("does not weaken §6 approval levels", "replaces §6 approval levels")
        self.assertIn("MISSING_BASIS_TOKEN:does not weaken §6 approval levels", basis.validate(text))

    def test_inserted_gate_rejected(self):
        text = mutate("exactly `KEY / CONTEXT / ROUTE / COST / DONE`", "exactly `KEY / CONTEXT / ROUTE / COST / NECESSITY / DONE`")
        self.assertIn("SIXTH_HARD_GATE", basis.validate(text))

    def test_renamed_gate_rejected(self):
        text = mutate("exactly `KEY / CONTEXT / ROUTE / COST / DONE`", "exactly `KEY / CONTEXT / ROUTE / BUDGET / DONE`")
        self.assertIn("HARD_GATES_ALTERED", basis.validate(text))

    def test_drive_as_canonical_master_source_rejected(self):
        text = mutate("Google Drive = WORKING / MIRROR / REFERENCE SURFACE.", "Google Drive = CANONICAL MASTER SOURCE.")
        self.assertIn("DRIVE_DECLARED_CANONICAL_MASTER_SOURCE", basis.validate(text))

    def test_current_as_canonical_rejected(self):
        text = mutate("- `CANONICAL` = promoted meaning/rules.", "- `CURRENT` = CANONICAL operational authority.")
        self.assertIn("CURRENT_DECLARED_CANONICAL", basis.validate(text))

    def test_github_canonical_source_loss_rejected(self):
        text = MASTER_TEXT.replace("GitHub TAKY = CANONICAL MASTER SOURCE.", "GitHub TAKY = mirror.")
        self.assertIn("MISSING_BASIS_TOKEN:GitHub TAKY = CANONICAL MASTER SOURCE.", basis.validate(text))

    def test_drive_github_conflict_block_loss_rejected(self):
        text = mutate("record a `CONFLICT` and block material mutation", "prefer the newer file")
        self.assertIn("MISSING_BASIS_TOKEN:record a `CONFLICT` and block material mutation", basis.validate(text))

    def test_done_semantics_change_rejected(self):
        text = mutate("does not change current DONE gate semantics", "redefines DONE as USER_CONFIRMED")
        self.assertIn("MISSING_BASIS_TOKEN:does not change current DONE gate semantics", basis.validate(text))

    def test_duplicate_subsection_id_rejected(self):
        text = mutate("### 0.2B Shepherding", "### 0.2A Shepherding")
        self.assertIn("DUPLICATE_SECTION_ID:0.2A", basis.validate(text))

    def test_vendor_reference_outside_role_ontology_allowed(self):
        text = mutate("- `HANDOFF` = recovery pointer, not authority (§12).", "- `HANDOFF` = recovery pointer, not authority (§12); a historical Codex or ChatGPT handoff is evidence only.")
        self.assertEqual(basis.validate(text), [])

    def test_shared_economy_policy_loss_rejected(self):
        text = mutate("two diverging economy policies are a defect.", "each may keep its own policy.")
        self.assertTrue(any("two diverging economy policies" in x for x in basis.validate(text)))

    def test_economy_evaluator_claimed_enforced_rejected(self):
        text = mutate("The single runtime evaluator remains implementation-OPEN (V2 §0.1); this rule SHALL NOT be reported as mechanically enforced until implemented and verified.", "The single runtime evaluator is mechanically enforced.")
        fail = basis.validate(text)
        self.assertIn("ECONOMY_POLICY_CLAIMED_ENFORCED", fail)
        self.assertTrue(any("implementation-OPEN" in x for x in fail))

    def test_acceptance_floor_partial_loss_rejected(self):
        text = mutate("acceptance criteria, authority, safety or evidence quality.", "acceptance criteria.")
        self.assertTrue(any(x.startswith("MISSING_BASIS_TOKEN:Cost saving") for x in basis.validate(text)))

    def test_two_stage_policy_candidate_caveat_loss_rejected(self):
        text = mutate("any two-stage completion policy built on them remains CANDIDATE until promoted.", "the two-stage completion policy is adopted.")
        fail = basis.validate(text)
        self.assertIn("TWO_STAGE_COMPLETION_PROMOTED", fail)
        self.assertTrue(any("remains CANDIDATE until promoted" in x for x in fail))

    def test_done_redefined_as_user_confirmed_rejected(self):
        text = mutate("`USER != DEBUGGER`: routine", "DONE requires USER_CONFIRMED. `USER != DEBUGGER`: routine")
        self.assertIn("DONE_REDEFINED_AS_USER_CONFIRMED", basis.validate(text))

    def test_no_auto_promotion_loss_rejected(self):
        text = mutate("They SHALL NOT be automatically promoted to Canonical, MASTER or a global rule.", "They may be promoted after recurrence.")
        self.assertIn("MISSING_BASIS_TOKEN:SHALL NOT be automatically promoted to Canonical, MASTER or a global rule.", basis.validate(text))

    def test_auto_promotion_allowed_rejected(self):
        text = mutate("Discovery, mining, index and learning outputs are EVIDENCE/CANDIDATE.", "Discovery, mining, index and learning outputs are EVIDENCE/CANDIDATE. Recurring learning outputs are automatically promoted.")
        self.assertIn("AUTO_PROMOTION_ALLOWED", basis.validate(text))

    def test_pipeline_specific_text_rejected(self):
        text = mutate("SHALL NOT be globalized by recurrence (§1.1, §22.1).", "SHALL NOT be globalized by recurrence (§1.1, §22.1).\n- `HTTP 200 / TITLE / SHELL-ONLY CONTENT != SUBSTANTIVE LEARNING EVIDENCE`.")
        self.assertIn("PIPELINE_SPECIFIC_TEXT_IN_MASTER_BASIS:HTTP\\s*200", basis.validate(text))

    def test_missing_section_rejected(self):
        text = MASTER_TEXT.replace("## 0.2 ", "## 0.9 ", 1)
        self.assertEqual(basis.validate(text), ["MISSING_SECTION:0.2"])


class OwnershipMapBasisTest(unittest.TestCase):
    def run_map(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run([sys.executable, str(OWNERSHIP_VALIDATOR), str(path)], capture_output=True, text=True)

    def assertMapFails(self, data, token):
        result = self.run_map(data)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(token, result.stdout)

    def test_current_map_passes(self):
        result = self.run_map(MAP_DATA)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_sixth_gate_in_kernel_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["TAKY2_ENFORCEMENT_KERNEL"]["hard_gates"].append("NECESSITY")
        self.assertMapFails(data, "HARD_GATES_NOT_EXACTLY_FIVE")

    def test_necessity_outside_cost_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["TAKY2_ENFORCEMENT_KERNEL"]["necessity_location"] = "NECESSITY_GATE"
        self.assertMapFails(data, "NECESSITY_NOT_INSIDE_COST")

    def test_control_role_bound_to_agent_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["SHEPHERDING_CONTROL_PLANE"]["mandatory_agent_spawn"] = True
        self.assertMapFails(data, "CONTROL_ROLE_BOUND_TO_AGENT")

    def test_duplicate_control_role_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["SHEPHERDING_CONTROL_PLANE"]["control_roles"].append("SCOUT")
        self.assertMapFails(data, "CONTROL_ROLES_INVALID")

    def test_plane_claiming_semantics_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["TAKY2_ENFORCEMENT_KERNEL"]["owns"] = ["Ready session meaning"]
        self.assertMapFails(data, "PLANE_CLAIMS_SEMANTIC_OWNERSHIP:TAKY2_ENFORCEMENT_KERNEL")

    def test_beta_as_owner_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["BETA_EVIDENCE"]["semantic_owner"] = "BETA"
        self.assertMapFails(data, "BETA_PLANE_CLAIMS_SEMANTIC_OWNER")

    def test_silently_dropped_owner_gap_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["owner_gaps"] = [x for x in data["owner_gaps"] if x["system"] != "EUNHA_FARM"]
        self.assertMapFails(data, "WHOLE_SYSTEM_OWNER_UNREGISTERED:EUNHA_FARM")

    def test_duplicate_owner_gap_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["owner_gaps"].append(copy.deepcopy(data["owner_gaps"][0]))
        self.assertMapFails(data, "OWNER_GAP_DUPLICATE:" + data["owner_gaps"][0]["system"])

    def test_guessed_gap_owner_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["owner_gaps"][0]["semantic_owner"] = "OS/GUESSED.md"
        self.assertMapFails(data, "OWNER_GAP_GUESSES_OWNERSHIP:" + data["owner_gaps"][0]["system"])

    def test_savey_namespace_invariant_loss_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["invariants"] = [x for x in data["invariants"] if "SAVEY" not in x]
        self.assertMapFails(data, "MISSING_INVARIANT:SAVEY_AI_ECONOMY != SAVEY_FAMILY_FINANCE")

    def promote(self, system, **layer):
        data = copy.deepcopy(MAP_DATA)
        data["owner_gaps"] = [x for x in data["owner_gaps"] if x["system"] != system]
        data["layers"][system] = dict({"class": "PROJECT_APP", "parent": "LEARNING_OS"}, **layer)
        return data

    def test_promoted_layer_with_placeholder_owner_rejected(self):
        data = self.promote("PIANO_PRACTICE", semantic_owner="fixture")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_AUTHORITY_REF_MISSING:PIANO_PRACTICE")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_SEMANTIC_OWNER_REF_MISSING:PIANO_PRACTICE")

    def test_promoted_layer_placeholder_refs_rejected(self):
        for value in ("UNKNOWN", "UNRESOLVED", "fixture", "TODO", "OWNER_GAP"):
            data = self.promote("PIANO_PRACTICE", authority_ref="TAKY2/TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL_20261006.md#10", semantic_owner_ref=value)
            self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_SEMANTIC_OWNER_REF_PLACEHOLDER:PIANO_PRACTICE")

    def test_promoted_layer_unresolvable_ref_rejected(self):
        data = self.promote("PIANO_PRACTICE", authority_ref="TAKY2/DOES_NOT_EXIST.md", semantic_owner_ref="piano owner")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_AUTHORITY_REF_NOT_FOUND:PIANO_PRACTICE")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_SEMANTIC_OWNER_REF_INVALID_FORMAT:PIANO_PRACTICE")

    def test_system_in_both_layer_and_gap_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["layers"]["EUNHA_FARM"] = {"class": "PROJECT_APP"}
        self.assertMapFails(data, "WHOLE_SYSTEM_OWNER_CONFLICT:EUNHA_FARM")

    def test_gap_owner_field_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["owner_gaps"][0]["owner"] = "LEARNING_OS"
        self.assertMapFails(data, "OWNER_GAP_GUESSES_OWNERSHIP:" + data["owner_gaps"][0]["system"])

    V2_REF = "TAKY2/TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL_20261006.md#10"
    CROSS_REF = "hns140412-glitch/Piano-Practice:PIANO_PRACTICE_CANONICAL_PRODUCT_CONTRACT.md"

    def test_promoted_layer_with_local_refs_passes(self):
        # Test-only promotion in a temp copy; the production map and its owner_gaps are not changed.
        data = self.promote("PIANO_PRACTICE", authority_ref=self.V2_REF, semantic_owner_ref="PROJECTS/PIANO_PRACTICE.md")
        result = self.run_map(data)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_promoted_layer_cross_repo_owner_without_verification_rejected(self):
        data = self.promote("PIANO_PRACTICE", authority_ref=self.V2_REF, semantic_owner_ref=self.CROSS_REF)
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_SEMANTIC_OWNER_REF_CROSS_REPO_UNVERIFIED:PIANO_PRACTICE")

    def test_promoted_layer_cross_repo_authority_without_verification_rejected(self):
        data = self.promote("PIANO_PRACTICE", authority_ref="hns140412-glitch/Piano-Practice:AUTHORITY.md", semantic_owner_ref="PROJECTS/PIANO_PRACTICE.md")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_AUTHORITY_REF_CROSS_REPO_UNVERIFIED:PIANO_PRACTICE")

    def test_promoted_layer_missing_verification_evidence_rejected(self):
        data = self.promote("PIANO_PRACTICE", authority_ref=self.V2_REF, semantic_owner_ref=self.CROSS_REF, owner_verification_ref="HISTORY/DOES_NOT_EXIST_RECEIPT.json")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_OWNER_VERIFICATION_REF_NOT_FOUND:PIANO_PRACTICE")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_SEMANTIC_OWNER_REF_CROSS_REPO_UNVERIFIED:PIANO_PRACTICE")

    def test_promoted_layer_cross_repo_verification_evidence_rejected(self):
        data = self.promote("PIANO_PRACTICE", authority_ref=self.V2_REF, semantic_owner_ref=self.CROSS_REF, owner_verification_ref="hns140412-glitch/Piano-Practice:RECEIPT.json")
        self.assertMapFails(data, "WHOLE_SYSTEM_LAYER_OWNER_VERIFICATION_REF_NOT_LOCAL:PIANO_PRACTICE")

    def test_promoted_layer_cross_repo_owner_with_local_evidence_passes(self):
        # Temporary test-only receipt inside the repo; removed afterwards. Not a production promotion.
        with tempfile.NamedTemporaryFile("w", suffix=".json", prefix="owner_verify_", dir=HERE, delete=False) as fh:
            fh.write("{}")
        receipt = Path(fh.name)
        try:
            data = self.promote("PIANO_PRACTICE", authority_ref=self.V2_REF, semantic_owner_ref=self.CROSS_REF, owner_verification_ref="ENFORCEMENT/" + receipt.name)
            result = self.run_map(data)
            self.assertEqual(result.returncode, 0, result.stdout)
        finally:
            receipt.unlink()

    def test_production_owner_gaps_unchanged(self):
        systems = [x["system"] for x in MAP_DATA["owner_gaps"]]
        self.assertEqual(systems, ["SAVEY_FAMILY_FINANCE", "TAKY_MOBILE", "PLANNER", "PIANO_PRACTICE", "EXPLORER_CREW", "BADGE_REWARD", "EUNHA_FARM"])
        self.assertTrue(all(x["state"] == "OWNER_GAP" for x in MAP_DATA["owner_gaps"]))

    def test_extra_control_role_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["SHEPHERDING_CONTROL_PLANE"]["control_roles"].append("ORACLE")
        self.assertMapFails(data, "CONTROL_ROLES_INVALID")

    def test_reordered_control_roles_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["SHEPHERDING_CONTROL_PLANE"]["control_roles"].reverse()
        self.assertMapFails(data, "CONTROL_ROLES_INVALID")

    def test_duplicate_role_replacing_canonical_rejected(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"]["SHEPHERDING_CONTROL_PLANE"]["control_roles"] = ["NAVIGATOR", "GUARDIAN", "DRIVER+SAVEY_AI_ECONOMY", "NAVIGATOR"]
        self.assertMapFails(data, "CONTROL_ROLES_INVALID")

    def test_malformed_kernel_plane_fails_structurally(self):
        for bad in (["KEY"], "KERNEL", 5):
            data = copy.deepcopy(MAP_DATA)
            data["cross_cutting_planes"]["TAKY2_ENFORCEMENT_KERNEL"] = bad
            result = self.run_map(data)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("PLANE_MALFORMED:TAKY2_ENFORCEMENT_KERNEL", result.stdout)
            self.assertIn("HARD_GATES_NOT_EXACTLY_FIVE", result.stdout)

    def test_malformed_shepherd_plane_fails_structurally(self):
        for bad in (["NAVIGATOR"], "SHEPHERD", 0):
            data = copy.deepcopy(MAP_DATA)
            data["cross_cutting_planes"]["SHEPHERDING_CONTROL_PLANE"] = bad
            result = self.run_map(data)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("SHEPHERDING_CONTROL_PLANE", result.stdout)
            self.assertIn("CONTROL_ROLES_INVALID", result.stdout)

    def test_malformed_planes_container_fails_structurally(self):
        data = copy.deepcopy(MAP_DATA)
        data["cross_cutting_planes"] = ["BETA_EVIDENCE"]
        result = self.run_map(data)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("PLANES_MALFORMED", result.stdout)

if __name__ == "__main__":
    unittest.main()
