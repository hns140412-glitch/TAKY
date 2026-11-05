#!/usr/bin/env python3
"""Local deterministic tests for runtime_orchestrator.assess_design_direction.

Structural checks only: a READY_TO_EXECUTE_CHECKS state never proves design
correctness, execution or runtime verification, and nothing here exercises a
hosted ChatGPT runtime, network, or paid API.
"""
import copy
import json
import unittest
from pathlib import Path

from runtime_orchestrator import (
    assess_design_direction,
    assess_logic_council,
    derive_runtime_state,
    execute_local_steering_read_and_reassess,
    run,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "ENFORCEMENT" / "fixtures" / "runtime_orchestrator_pass.json"
SEED = "ENFORCEMENT/fixtures/evidence_seed.bin"
SEED_SHA = "d8e0e35dd505bed4ff6cc4fdfe04ba698b840ce2c39aa9c0d75ccad18d11f5c1"


def base_record():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def packet(**over):
    wm = base_record()["working_model"]
    p = {
        # Bound to the fixture's actual working_model outcome / protected_state.
        "user_outcome": wm["primary_outcome"],
        "current_evidence_refs": [{"path": SEED, "sha256": SEED_SHA}],
        "protected_constraints": list(wm["protected_state"]),
        "alternatives": [
            {"id": "A_NEW_ENGINE", "summary": "Separate design engine",
             "rejected_reason": "Duplicates runtime_orchestrator authority."},
            {"id": "B_REUSE", "summary": "Extend existing runtime_orchestrator.run",
             "reuses_existing": True},
        ],
        "chosen_route_id": "B_REUSE",
        "rationale": "Reuse keeps one authority path.",
        "predicted_outcome": "Material design task without packet is not authorized.",
        "falsification_triggers": ["a legacy ordinary task starts failing"],
    }
    p.update(over)
    return p


def arch_record(pkt="__none__"):
    r = base_record()
    r["architecture_change_planned"] = True
    if pkt != "__none__":
        r["design_direction"] = pkt
    return r


def dd(result):
    return result["design_direction"]


def codes(result):
    return [c for c in result["detected"] if c.startswith("DESIGN_DIRECTION")]


class DesignDirectionShepherdTests(unittest.TestCase):
    def test_trivial_task_bypass_and_legacy_compat(self):
        r = run(base_record(), ROOT, None)
        self.assertEqual(dd(r)["state"], "NOT_REQUIRED")
        self.assertFalse(dd(r)["required"])
        self.assertEqual(codes(r), [])

    def test_arbitrary_action_with_arch_flag_not_demanded(self):
        rec = base_record()
        rec["action_class"] = "INSPECT"
        rec["architecture_change_planned"] = True
        r = run(rec, ROOT, None)
        self.assertEqual(dd(r)["state"], "NOT_REQUIRED")

    def test_material_architecture_task_without_packet_blocks(self):
        r = run(arch_record(), ROOT, None)
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_PACKET_MISSING", r["detected"])
        self.assertFalse(r["authorized_to_continue"])
        self.assertIsNone(r["route"])

    def test_explicit_flag_activates_on_any_action(self):
        rec = base_record()
        rec["action_class"] = "INSPECT"
        rec["design_direction_required"] = True
        r = run(rec, ROOT, None)
        self.assertIn("DESIGN_DIRECTION_PACKET_MISSING", r["detected"])

    def test_missing_current_evidence_blocks(self):
        r = run(arch_record(packet(current_evidence_refs=[])), ROOT, None)
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_CURRENT_EVIDENCE_MISSING", r["detected"])

    def test_invalid_candidate_chosen_route_blocks(self):
        r = run(arch_record(packet(chosen_route_id="Z_UNKNOWN")), ROOT, None)
        self.assertIn("DESIGN_DIRECTION_CHOSEN_ROUTE_INVALID", r["detected"])
        self.assertFalse(r["authorized_to_continue"])

    def test_rejected_route_requires_reason(self):
        p = packet()
        del p["alternatives"][0]["rejected_reason"]
        r = run(arch_record(p), ROOT, None)
        self.assertIn("DESIGN_DIRECTION_REJECTED_REASON_MISSING:A_NEW_ENGINE", r["detected"])

    def test_valid_packet_ready_but_not_claimed_verified(self):
        r = run(arch_record(packet()), ROOT, None)
        d = dd(r)
        self.assertEqual(d["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertEqual(d["detected"], [])
        self.assertEqual(d["evidence_refs"][0]["status"], "READ_HASH_MATCHED")
        self.assertEqual(d["chosen_vs_rejected"][0]["rejected"], "A_NEW_ENGINE")
        self.assertEqual(d["semantic_validity"], "NOT_PROVEN_BY_STRUCTURE")
        self.assertFalse(d["design_correct_claimed"])
        self.assertFalse(d["executed"])
        self.assertFalse(d["verified"])
        self.assertFalse(r["hosted_chatgpt_auto_invocation_verified"])
        self.assertFalse(d["hosted_chatgpt_interception_verified"])
        self.assertEqual(codes(r), [])

    def test_single_alternative_allowed_no_fixed_count(self):
        p = packet(alternatives=[{"id": "B_REUSE", "summary": "Extend existing runtime"}])
        self.assertEqual(dd(run(arch_record(p), ROOT, None))["state"], "READY_TO_EXECUTE_CHECKS")

    def test_string_evidence_is_declared_not_verified(self):
        r = run(arch_record(packet(current_evidence_refs=["CURRENT/foo.md"])), ROOT, None)
        d = dd(r)
        self.assertEqual(d["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertEqual(d["evidence_refs"][0]["status"], "DECLARED_NOT_VERIFIED")

    def test_evidence_hash_mismatch_and_unreadable_hold(self):
        bad = packet(current_evidence_refs=[{"path": SEED, "sha256": "0" * 64}])
        r = run(arch_record(bad), ROOT, None)
        self.assertEqual(dd(r)["state"], "HOLD")
        self.assertFalse(r["authorized_to_continue"])
        gone = packet(current_evidence_refs=[{"path": "../outside.txt"}])
        r2 = run(arch_record(gone), ROOT, None)
        self.assertEqual(dd(r2)["state"], "HOLD")
        self.assertNotIn(str(ROOT), json.dumps(dd(r2)))

    def test_explicit_hold(self):
        r = run(arch_record(packet(hold={"reason": "awaiting owner decision"})), ROOT, None)
        self.assertEqual(dd(r)["state"], "HOLD")
        self.assertIn("DESIGN_DIRECTION_HOLD", r["detected"])

    def _finding(self, **over):
        f = {"id": "F1", "source": "independent-claude-review", "severity": "MATERIAL",
             "targets_route_id": "B_REUSE",
             "counterexample": "orchestrator.run is shared by legacy replay; new gate breaks it",
             "disposition": "OPEN"}
        f.update(over)
        return f

    def test_counterexample_forces_redirect_state_transition(self):
        # Same packet: without finding -> READY; with material counterexample -> REDIRECT_REQUIRED.
        ready = run(arch_record(packet()), ROOT, None)
        self.assertEqual(dd(ready)["state"], "READY_TO_EXECUTE_CHECKS")
        blocked = run(arch_record(packet(critique=[self._finding()])), ROOT, None)
        self.assertEqual(dd(blocked)["state"], "REDIRECT_REQUIRED")
        self.assertIn("DESIGN_DIRECTION_MATERIAL_COUNTEREXAMPLE_UNRESOLVED:F1", blocked["detected"])
        self.assertFalse(blocked["authorized_to_continue"])
        self.assertIsNone(blocked["route"])
        self.assertTrue(dd(blocked)["findings"][0]["blocks_chosen_route"])

    def test_redirect_to_evidence_backed_alternative_passes(self):
        p = packet(
            alternatives=[
                {"id": "B_REUSE", "summary": "Extend runtime_orchestrator.run in place",
                 "rejected_reason": "Counterexample F1: shared by legacy replay."},
                {"id": "C_OPT_IN", "summary": "Opt-in assessment, legacy tasks bypass",
                 "reuses_existing": True},
            ],
            chosen_route_id="C_OPT_IN",
            critique=[self._finding(disposition="ACCEPTED_REDIRECT")],
            supersedes={"previous_route_id": "B_REUSE", "finding_id": "F1",
                        "rationale": "Opt-in activation keeps legacy tasks untouched."},
        )
        r = run(arch_record(p), ROOT, None)
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertEqual(codes(r), [])

    def test_accepted_redirect_label_without_route_change_still_blocks(self):
        p = packet(critique=[self._finding(disposition="ACCEPTED_REDIRECT")])
        self.assertEqual(dd(run(arch_record(p), ROOT, None))["state"], "REDIRECT_REQUIRED")

    def test_supersedes_must_reference_real_finding(self):
        p = packet(
            alternatives=[
                {"id": "B_REUSE", "summary": "x", "rejected_reason": "r"},
                {"id": "C_OPT_IN", "summary": "y"},
            ],
            chosen_route_id="C_OPT_IN",
            critique=[self._finding()],
            supersedes={"previous_route_id": "B_REUSE", "finding_id": "NOPE", "rationale": "r"},
        )
        r = run(arch_record(p), ROOT, None)
        self.assertIn("DESIGN_DIRECTION_SUPERSEDES_INVALID", r["detected"])
        self.assertFalse(r["authorized_to_continue"])

    def test_rebuttal_needs_rationale_and_evidence(self):
        weak = packet(critique=[self._finding(disposition="REBUTTED")])
        self.assertEqual(dd(run(arch_record(weak), ROOT, None))["state"], "REDIRECT_REQUIRED")
        strong = packet(critique=[self._finding(
            disposition="REBUTTED",
            disposition_rationale="Legacy replay verified unaffected by opt-in gating.",
            evidence_refs=[{"path": SEED, "sha256": SEED_SHA}])])
        r = run(arch_record(strong), ROOT, None)
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertEqual(dd(r)["findings"][0]["disposition"], "REBUTTED")  # recorded, not discarded
        self.assertEqual(dd(r)["findings"][0]["rebuttal_evidence_status"], ["READ_HASH_MATCHED"])

    # ---- P0 corrective regressions (independent Codex review bypasses) ----

    def _rebut(self, refs):
        return run(arch_record(packet(critique=[self._finding(
            disposition="REBUTTED", disposition_rationale="claimed unaffected",
            evidence_refs=refs)])), ROOT, None)

    def test_p0b_fake_rebuttal_evidence_does_not_unblock(self):
        for refs in ([None], [""], ["   "], [SEED], ["https://example.com/x"],
                     [{"path": "ENFORCEMENT/fixtures/does_not_exist.bin", "sha256": SEED_SHA}],
                     [{"path": SEED, "sha256": "0" * 64}],
                     [{"path": SEED}],
                     [{"path": "../outside.txt", "sha256": SEED_SHA}],
                     "not-a-list", []):
            r = self._rebut(refs)
            self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED", refs)
            self.assertFalse(r["authorized_to_continue"], refs)

    def test_p0b_real_hash_matched_local_rebuttal_unblocks(self):
        good = {"path": SEED, "sha256": SEED_SHA}
        r = self._rebut([good, dict(good)])
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")

    def test_p0b3_mixed_wrong_and_correct_sha_rebuttal_stays_blocked(self):
        good = {"path": SEED, "sha256": SEED_SHA}
        for refs in ([good, {"path": SEED, "sha256": "0" * 64}],
                     [{"path": SEED, "sha256": "0" * 64}, good],
                     [good, None]):
            r = self._rebut(refs)
            self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED", refs)
            self.assertFalse(r["authorized_to_continue"], refs)

    def test_p0d3_contradictory_provenance_only_outcome_not_ready(self):
        p = packet(user_outcome="Build a second engine and edit CURRENT owner files.",
                   outcome_provenance={"source": "working_model.primary_outcome",
                                       "rationale": "paraphrase of the owner outcome"})
        r = run(arch_record(p), ROOT, None)
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_OUTCOME_UNVERIFIED", r["detected"])
        self.assertFalse(r["authorized_to_continue"])

    def test_p0d3_added_conflicting_constraint_not_ready(self):
        wm = base_record()["working_model"]
        p = packet(protected_constraints=list(wm["protected_state"]) + ["second engine allowed"])
        r = run(arch_record(p), ROOT, None)
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_EXTRA_CONSTRAINT_UNBOUND:second engine allowed", r["detected"])
        self.assertFalse(r["authorized_to_continue"])

    def test_p0a_route_change_without_supersedes_stays_redirect(self):
        alts = [
            {"id": "B_REUSE", "summary": "x", "rejected_reason": "F1"},
            {"id": "C_OPT_IN", "summary": "y"},
        ]
        for disp in ("OPEN", "ACCEPTED_REDIRECT"):
            p = packet(alternatives=alts, chosen_route_id="C_OPT_IN",
                       critique=[self._finding(disposition=disp)])  # supersedes missing
            r = run(arch_record(p), ROOT, None)
            self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED", disp)
            self.assertFalse(r["authorized_to_continue"])
            p["supersedes"] = None
            self.assertEqual(dd(run(arch_record(p), ROOT, None))["state"], "REDIRECT_REQUIRED")

    def test_p0a_supersedes_must_match_finding_target_and_finding(self):
        alts = [
            {"id": "A_NEW_ENGINE", "summary": "w", "rejected_reason": "dup"},
            {"id": "B_REUSE", "summary": "x", "rejected_reason": "F1"},
            {"id": "C_OPT_IN", "summary": "y"},
        ]
        f1 = self._finding(disposition="ACCEPTED_REDIRECT")  # targets B_REUSE
        f2 = self._finding(id="F2", targets_route_id="A_NEW_ENGINE")
        # supersedes names the wrong previous route for F1 -> not a redirect proof
        wrong_prev = packet(alternatives=alts, chosen_route_id="C_OPT_IN", critique=[f1],
                            supersedes={"previous_route_id": "A_NEW_ENGINE",
                                        "finding_id": "F1", "rationale": "r"})
        self.assertEqual(dd(run(arch_record(wrong_prev), ROOT, None))["state"], "REDIRECT_REQUIRED")
        # supersedes cites an unrelated finding (F2) as proof for F1
        unrelated = packet(alternatives=alts, chosen_route_id="C_OPT_IN",
                           critique=[f1, dict(f2, disposition="ACCEPTED_REDIRECT")],
                           supersedes={"previous_route_id": "A_NEW_ENGINE",
                                       "finding_id": "F2", "rationale": "r"})
        r = run(arch_record(unrelated), ROOT, None)
        self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED")
        self.assertIn("F1", [f["id"] for f in dd(r)["findings"] if f["blocks_chosen_route"]])
        # correct matching supersedes passes
        ok = packet(alternatives=alts, chosen_route_id="C_OPT_IN", critique=[f1],
                    supersedes={"previous_route_id": "B_REUSE", "finding_id": "F1",
                                "rationale": "opt-in keeps legacy untouched"})
        self.assertEqual(dd(run(arch_record(ok), ROOT, None))["state"], "READY_TO_EXECUTE_CHECKS")

    def test_p0a_unknown_finding_target_fails(self):
        p = packet(critique=[self._finding(targets_route_id="GHOST", disposition="REBUTTED",
                                           disposition_rationale="r",
                                           evidence_refs=[{"path": SEED, "sha256": SEED_SHA}])])
        r = run(arch_record(p), ROOT, None)
        self.assertIn("DESIGN_DIRECTION_FINDING_TARGET_UNKNOWN:F1", r["detected"])
        self.assertFalse(r["authorized_to_continue"])
        self.assertNotEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")

    def test_p0c_severity_normalized_and_invalid_never_downgrades(self):
        for sev in (" material ", "Material", "MATERIAL"):
            r = run(arch_record(packet(critique=[self._finding(severity=sev)])), ROOT, None)
            self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED", sev)
        for sev in (None, "", 7, ["MATERIAL"], "SEVERE-ish", {"x": 1}):
            f = self._finding(severity=sev)
            if sev is None:
                del f["severity"]
            r = run(arch_record(packet(critique=[f])), ROOT, None)
            self.assertNotEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS", sev)
            self.assertFalse(r["authorized_to_continue"], sev)
            self.assertIn("DESIGN_DIRECTION_FINDING_SEVERITY_INVALID:F1", r["detected"])

    def test_p0c_invalid_action_class_types_do_not_raise(self):
        # Direct call: this function's own robustness (other stages are out of scope).
        for bad in (None, 5, ["ORCHESTRATE"], {"a": 1}, True):
            rec = arch_record(packet())
            rec["action_class"] = bad
            rec["design_direction_required"] = True
            state, _ = derive_runtime_state(rec)
            res = assess_design_direction(rec, state, ROOT)  # must not raise TypeError
            self.assertTrue(res["required"])
            self.assertIn("DESIGN_DIRECTION_ACTION_CLASS_INVALID", res["detected"])
            self.assertNotEqual(res["state"], "READY_TO_EXECUTE_CHECKS")

    def test_p0d_contradictory_packet_not_ready(self):
        rec = arch_record(packet(
            user_outcome="Build a second engine and edit CURRENT owner files.",
            protected_constraints=["second engine allowed"]))
        rec["working_model"]["primary_outcome"] = "Keep one runtime; no CURRENT edits."
        rec["working_model"]["protected_state"] = ["one runtime", "no CURRENT edits"]
        r = run(rec, ROOT, None)
        self.assertNotEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertIn("DESIGN_DIRECTION_OUTCOME_UNVERIFIED", r["detected"])
        self.assertIn("DESIGN_DIRECTION_PROTECTED_STATE_DROPPED:one runtime", r["detected"])
        self.assertFalse(r["authorized_to_continue"])

    def test_p0d_binding_paraphrase_needs_named_provenance_and_is_unverified(self):
        para = "Extend the existing runtime with design assessment."
        bare = arch_record(packet(user_outcome=para))
        self.assertEqual(dd(run(bare, ROOT, None))["state"], "DECISION_PENDING")
        bogus = arch_record(packet(user_outcome=para, outcome_provenance={
            "source": "somewhere.else", "rationale": "r"}))
        self.assertEqual(dd(run(bogus, ROOT, None))["state"], "DECISION_PENDING")
        ok = arch_record(packet(user_outcome=para, outcome_provenance={
            "source": "working_model.primary_outcome", "rationale": "shortened wording"}))
        r = run(ok, ROOT, None)
        # Upper working_model.primary_outcome exists and differs: provenance alone cannot verify.
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_OUTCOME_UNVERIFIED", r["detected"])
        self.assertEqual(dd(r)["semantic_validity"], "NOT_PROVEN_BY_STRUCTURE")
        exact = dd(run(arch_record(packet()), ROOT, None))
        self.assertEqual(exact["outcome_binding"], "MATCHES_ANCHOR")

    def test_p0e_voluntary_empty_packet_on_trivial_inspect_does_not_block(self):
        base = run(dict(base_record(), action_class="INSPECT"), ROOT, None)
        for pkt in ({}, None, "junk", [], {"critique": "bad"}):
            rec = base_record()
            rec["action_class"] = "INSPECT"
            rec["design_direction"] = pkt
            r = run(rec, ROOT, None)
            self.assertFalse(dd(r)["required"])
            self.assertEqual(dd(r)["state"], "NOT_REQUIRED")
            self.assertEqual(codes(r), [])
            self.assertEqual(r["detected"], base["detected"])
            self.assertEqual(r["authorized_to_continue"], base["authorized_to_continue"])

    def test_p0e_explicit_mandatory_blocks_malformed_packet(self):
        for pkt in ({}, "junk", [], {"critique": "bad"}):
            rec = base_record()
            rec["action_class"] = "INSPECT"
            rec["design_direction_required"] = True
            rec["design_direction"] = pkt
            r = run(rec, ROOT, None)
            self.assertTrue(dd(r)["required"])
            self.assertNotEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
            self.assertTrue(codes(r))
            self.assertFalse(r["authorized_to_continue"])
        # truthy-but-not-True flags cannot bypass mandatory activation
        for flag in ("true", "YES", 1):
            rec = base_record()
            rec["material_design_decision"] = flag
            self.assertIn("DESIGN_DIRECTION_PACKET_MISSING", run(rec, ROOT, None)["detected"], flag)

    def test_material_finding_without_counterexample_is_not_theater(self):
        p = packet(critique=[self._finding(counterexample="")])
        r = run(arch_record(p), ROOT, None)
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_MATERIAL_FINDING_WITHOUT_COUNTEREXAMPLE:F1", r["detected"])

    def test_reviewer_label_never_grants_independent_verification(self):
        p = packet(critique=[self._finding(severity="MINOR", independently_verified=True,
                                           source="INDEPENDENT_VERIFIED_RECEIPT")])
        r = run(arch_record(p), ROOT, None)
        self.assertFalse(dd(r)["findings"][0]["independently_verified"])
        self.assertFalse(dd(r)["reviewer_label_trusted"])
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")  # no auto-approval or auto-block

    def test_scout_state_from_advisory_without_authority(self):
        rec = base_record()
        rec["idea_exploration"] = {"idea": "dynamic massing"}
        r = run(rec, ROOT, None)
        self.assertEqual(dd(r)["state"], "SCOUT")
        self.assertFalse(dd(r)["required"])
        self.assertEqual(codes(r), [])
        self.assertIsNotNone(r["idea_exploration_advisory"])

    def test_existing_idea_and_case_advisories_unchanged(self):
        rec = base_record()
        rec["idea_exploration"] = {"idea": "site law to 3D mass"}
        rec["case_comparison"] = {"cases": [{"source_ref": "github:example/app", "lane": "OPEN_SOURCE"}]}
        r = run(rec, ROOT, None)
        self.assertTrue(r["idea_exploration_advisory"]["pass"])
        self.assertEqual(r["case_comparison_advisory"]["status"], "EVIDENCE_REVIEW_OPEN")
        self.assertIsNone(r["design_direction"]["chosen_route_id"])  # advisories are not design approval

    def _steer(self, rec):
        r = run(rec, ROOT, None)
        return r, r["steering_continuation"]

    def test_steering_redirect_with_known_alternative_keeps_route_unauthorized(self):
        r, s = self._steer(arch_record(packet(critique=[self._finding()])))
        self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED")
        self.assertFalse(r["authorized_to_continue"])
        self.assertIsNone(r["route"])
        self.assertTrue(s["blocking"])
        # Original fixture: A_NEW_ENGINE was rejected -> history only, never viable.
        self.assertEqual(s["alternative_ids"], [])
        self.assertIn("F1", s["failure"]["findings"][0]["id"])
        self.assertTrue(s["steps"])
        for st in s["steps"]:
            self.assertEqual(st["status"], "PROPOSED_NOT_EXECUTED")
        self.assertFalse(s["steering_authorizes_route"])
        self.assertFalse(s["original_route_authorized"])
        self.assertFalse(s["auto_dispatch"])
        self.assertFalse(s["executed"])
        self.assertFalse(s["verified"])

    def test_material_open_finding_can_keep_source_grounded_candidate_under_evaluation(self):
        candidate = {
            "id": "C_EVALUATE", "summary": "Evaluate existing local reuse",
            "evaluation_pending_reason": "Open F1 needs a falsification witness",
            "compatibility": {
                "rationale": "Same existing runtime, no duplicate owner",
                "evidence_refs": [{"path": SEED, "sha256": SEED_SHA}],
            },
        }
        p = packet(critique=[self._finding()], alternatives=[
            {"id": "B_REUSE", "summary": "Existing route"},
            candidate,
            {"id": "A_NEW_ENGINE", "summary": "Parallel engine",
             "rejected_reason": "Violates single owner"},
        ])
        r = run(arch_record(p), ROOT, None)
        self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED")
        self.assertFalse(r["authorized_to_continue"])
        self.assertNotIn("DESIGN_DIRECTION_REJECTED_REASON_MISSING:C_EVALUATE",
                         dd(r)["detected"])
        self.assertEqual(dd(r)["chosen_vs_evaluating"][0]["candidate"],
                         "C_EVALUATE")
        matches = dd(r)["steering_facts"]["alternatives"]
        self.assertEqual(next(a for a in matches if a["id"] == "C_EVALUATE")
                         ["steering_status"], "VIABLE_GROUNDED")
        self.assertEqual(next(a for a in matches if a["id"] == "A_NEW_ENGINE")
                         ["steering_status"], "REJECTED_HISTORY_ONLY")

    def test_candidate_evaluation_reason_cannot_bypass_closed_or_ungrounded_decision(self):
        candidate = {
            "id": "C_EVALUATE", "summary": "Review candidate",
            "evaluation_pending_reason": "Proposal is not yet accepted",
            "compatibility": {
                "rationale": "Existing context needs review",
                "evidence_refs": [{"path": SEED, "sha256": SEED_SHA}],
            },
        }
        missing_finding = packet(alternatives=[
            {"id": "B_REUSE", "summary": "Existing route"}, candidate
        ])
        done = run(arch_record(missing_finding), ROOT, None)
        self.assertEqual(dd(done)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_REJECTED_REASON_MISSING:C_EVALUATE",
                      dd(done)["detected"])

        ungrounded = copy.deepcopy(candidate)
        ungrounded["compatibility"]["evidence_refs"][0]["sha256"] = "0" * 64
        active = packet(critique=[self._finding()], alternatives=[
            {"id": "B_REUSE", "summary": "Existing route"}, ungrounded
        ])
        result = run(arch_record(active), ROOT, None)
        self.assertEqual(dd(result)["state"], "REDIRECT_REQUIRED")
        self.assertIn("DESIGN_DIRECTION_REJECTED_REASON_MISSING:C_EVALUATE",
                      dd(result)["detected"])
        self.assertFalse(result["authorized_to_continue"])

    def test_steering_redirect_without_alternative_inspects_current(self):
        p = packet(alternatives=[{"id": "B_REUSE", "summary": "Extend existing runtime_orchestrator.run"}],
                   critique=[self._finding()])
        _, s = self._steer(arch_record(p))
        self.assertEqual(s["alternative_ids"], [])
        self.assertIn("NO_VIABLE_DECLARED_ALTERNATIVE", s["evidence_gaps"])
        self.assertEqual(s["steps"][0]["permission"], "AGENT_LOCAL_READ_ONLY")
        self.assertNotIn("A_NEW_ENGINE", json.dumps(s))  # no fabricated candidate

    def test_steering_missing_evidence_picks_smallest_action(self):
        r, s = self._steer(arch_record(packet(current_evidence_refs=[])))
        self.assertEqual(dd(r)["state"], "DECISION_PENDING")
        self.assertIn("DESIGN_DIRECTION_CURRENT_EVIDENCE_MISSING", s["evidence_gaps"])
        self.assertEqual(len(s["steps"]), 1)
        self.assertEqual(s["steps"][0]["permission"], "AGENT_LOCAL_READ_ONLY")
        self.assertFalse(r["authorized_to_continue"])

    def test_steering_user_only_approval_flagged_not_authorized(self):
        p = packet(hold={"reason": "needs owner sign-off", "requires_human_approval": True})
        r, s = self._steer(arch_record(p))
        self.assertEqual(dd(r)["state"], "HOLD")
        self.assertTrue(s["human_approval_unresolved"])
        self.assertEqual(s["steps"][0]["permission"], "HUMAN_ONLY")
        self.assertEqual(s["steps"][0]["owner"], "HUMAN")
        self.assertFalse(r["authorized_to_continue"])
        self.assertFalse(s["steering_authorizes_route"])

    def test_steering_evidence_hold_is_agent_restorable_not_human(self):
        bad = packet(current_evidence_refs=[{"path": SEED, "sha256": "0" * 64}])
        _, s = self._steer(arch_record(bad))
        self.assertFalse(s["human_approval_unresolved"])
        self.assertEqual(s["steps"][0]["permission"], "AGENT_PROPOSABLE_NO_AUTHORITY")

    def test_steering_normal_flow_unmodified(self):
        r = run(base_record(), ROOT, None)
        self.assertIsNone(r["steering_continuation"])
        self.assertEqual(dd(r)["state"], "NOT_REQUIRED")
        ready = run(arch_record(packet()), ROOT, None)
        self.assertIsNone(ready["steering_continuation"])  # no reuse opportunity grounded

    def test_steering_opportunity_only_when_grounded(self):
        # Chosen route is the reuse one -> no opportunity. Choose the other -> grounded reuse alt.
        p = packet(chosen_route_id="A_NEW_ENGINE")
        p["alternatives"][0].pop("rejected_reason")
        p["alternatives"][1]["rejected_reason"] = "heavier migration"
        r, s = self._steer(arch_record(p))
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertTrue(s["opportunity"]["nonblocking"])
        self.assertEqual(s["opportunity"]["alternative_ids"], ["B_REUSE"])
        self.assertFalse(s["blocking"])
        self.assertEqual(s["steps"], [])

    def test_steering_never_conflicts_with_protected_intent(self):
        p = packet(user_outcome="Totally different outcome", protected_constraints=["something else"])
        r, s = self._steer(arch_record(p))
        self.assertTrue(s["protected_intent_conflict"])
        self.assertFalse(r["authorized_to_continue"])
        text = json.dumps(s["steps"]).lower()
        self.assertIn("do not alter", text)
        self.assertNotIn("drop", text)

    def test_steering_no_dangerous_auto_dispatch(self):
        for rec in (arch_record(packet(critique=[self._finding()])), arch_record(),
                    arch_record(packet(hold={"reason": "x", "requires_human_approval": True}))):
            r, s = self._steer(rec)
            self.assertIsNone(r["route"])
            self.assertIsNone(r["dispatch_envelope"])
            self.assertIsNone(r["executor_adapter"])
            self.assertFalse(s["auto_dispatch"])
            self.assertFalse(s["executed"] or s["verified"])
            for st in s["steps"]:
                self.assertEqual(st["status"], "PROPOSED_NOT_EXECUTED")

    def test_review_rejected_alternative_is_history_only_never_viable(self):
        r, s = self._steer(arch_record(packet(critique=[self._finding()])))
        self.assertEqual(dd(r)["state"], "REDIRECT_REQUIRED")
        self.assertEqual(s["alternative_ids"], [])
        self.assertEqual(s["scout_candidate_ids"], [])
        hist = s["rejected_alternatives"]
        self.assertEqual([h["id"] for h in hist], ["A_NEW_ENGINE"])
        self.assertEqual(hist[0]["label"], "REJECTED_HISTORY_ONLY")
        self.assertEqual(hist[0]["rejected_reason"], "Duplicates runtime_orchestrator authority.")
        self.assertIn("compatibility_status", hist[0])
        self.assertIn("NO_VIABLE_DECLARED_ALTERNATIVE", s["evidence_gaps"])
        # No step proposes or names the rejected option.
        self.assertNotIn("A_NEW_ENGINE", json.dumps(s["steps"]))
        self.assertEqual(s["steps"][0]["action_code"], "READ_ONLY_REBIND_CURRENT_OWNER")
        self.assertEqual(s["steps"][0]["permission"], "AGENT_LOCAL_READ_ONLY")
        self.assertIn("SCOUT_VIABLE_ROUTE", [st["action_code"] for st in s["steps"]])
        self.assertFalse(r["authorized_to_continue"])

    def test_review_rejected_stays_history_even_with_grounded_compatibility(self):
        p = packet(critique=[self._finding()])
        p["alternatives"][0]["compatibility"] = {
            "rationale": "claims compatible", "evidence_refs": [{"path": SEED, "sha256": SEED_SHA}]}
        _, s = self._steer(arch_record(p))
        self.assertEqual(s["alternative_ids"], [])
        self.assertEqual(s["rejected_alternatives"][0]["compatibility_status"], "GROUNDED")
        self.assertNotIn("A_NEW_ENGINE", json.dumps(s["steps"]))

    def _alt_candidate(self, compat):
        p = packet(critique=[self._finding()])
        cand = {"id": "C_GROUNDED", "summary": "Opt-in assessment", "reuses_existing": True}
        if compat is not None:
            cand["compatibility"] = compat
        p["alternatives"].append(cand)
        return arch_record(p)

    def test_review_grounded_alternative_is_evaluation_only(self):
        compat = {"rationale": "Opt-in keeps protected state intact",
                  "evidence_refs": [{"path": SEED, "sha256": SEED_SHA}]}
        r, s = self._steer(self._alt_candidate(compat))
        self.assertEqual(s["alternative_ids"], ["C_GROUNDED"])
        self.assertEqual([h["id"] for h in s["rejected_alternatives"]], ["A_NEW_ENGINE"])
        st = s["steps"][0]
        self.assertEqual(st["action_code"], "EVALUATE_GROUNDED_ALTERNATIVE")
        self.assertIn("evaluation only", st["action"])
        self.assertEqual(st["status"], "PROPOSED_NOT_EXECUTED")
        self.assertFalse(r["authorized_to_continue"])
        self.assertIsNone(r["route"])
        self.assertFalse(s["steering_authorizes_route"])
        self.assertFalse(s["auto_dispatch"])

    def test_review_declared_unverified_alternative_is_scout_only(self):
        for compat in (None, "claimed compatible",
                       {"rationale": "x", "evidence_refs": [{"path": SEED, "sha256": "0" * 64}]}):
            _, s = self._steer(self._alt_candidate(compat))
            self.assertEqual(s["alternative_ids"], [], compat)
            self.assertEqual(s["scout_candidate_ids"], ["C_GROUNDED"], compat)
            codes_ = [st["action_code"] for st in s["steps"]]
            self.assertNotIn("EVALUATE_GROUNDED_ALTERNATIVE", codes_)
            scout = next(st for st in s["steps"] if st["action_code"] == "SCOUT_VIABLE_ROUTE")
            self.assertEqual(scout["args"]["scout_candidate_ids"], ["C_GROUNDED"])

    def _human_blocked(self, rec):
        rec["approval_resume"] = {"required": True}
        rec.pop("human_approval_evidence", None)
        return self._steer(rec)

    def test_review_global_human_blocker_not_hidden_by_ready_design(self):
        for rec, state in ((base_record(), "NOT_REQUIRED"), (arch_record(packet()), "READY_TO_EXECUTE_CHECKS")):
            r, s = self._human_blocked(rec)
            self.assertEqual(dd(r)["state"], state)
            self.assertIn("HUMAN_APPROVAL_EVIDENCE_MISSING_FOR_RESUME", r["detected"])
            self.assertFalse(r["authorized_to_continue"])
            self.assertIsNotNone(s)
            self.assertTrue(s["blocking"])
            self.assertTrue(s["human_approval_unresolved"])
            human = [st for st in s["steps"] if st["permission"] == "HUMAN_ONLY"]
            self.assertEqual(len(human), 1)
            self.assertEqual(human[0]["owner"], "HUMAN")
            self.assertEqual(human[0]["category"], "HUMAN_AUTHORIZATION")
            self.assertEqual(s["next_best_step_id"], human[0]["step_id"])
            self.assertFalse(s["original_route_authorized"])
            self.assertFalse(s["steering_authorizes_route"])

    def test_review_global_human_blocker_with_reuse_candidate_still_human_step(self):
        p = packet(chosen_route_id="A_NEW_ENGINE")
        p["alternatives"][0].pop("rejected_reason")
        p["alternatives"][1]["rejected_reason"] = "heavier migration"
        r, s = self._human_blocked(arch_record(p))
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertTrue(s["opportunity"]["nonblocking"])
        self.assertTrue(s["human_approval_unresolved"])
        self.assertEqual(s["steps"][-1]["permission"], "HUMAN_ONLY")
        self.assertIsNone(r["route"])

    def test_review_reuse_opportunity_excludes_previously_rejected(self):
        # B_REUSE was the previous route superseded by a finding -> no opportunity.
        p = packet(
            alternatives=[
                {"id": "B_REUSE", "summary": "Extend in place", "reuses_existing": True,
                 "rejected_reason": "Counterexample F1."},
                {"id": "C_OPT_IN", "summary": "Opt-in assessment"},
            ],
            chosen_route_id="C_OPT_IN",
            critique=[self._finding(disposition="ACCEPTED_REDIRECT")],
            supersedes={"previous_route_id": "B_REUSE", "finding_id": "F1",
                        "rationale": "Opt-in keeps legacy untouched."},
        )
        r, s = self._steer(arch_record(p))
        self.assertEqual(dd(r)["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertIsNone(s)

    def test_review_steps_are_typed_machine_consumable_and_bounded(self):
        allowed_cat = {"SCOUT", "INSPECTION", "EVIDENCE_REPAIR", "HUMAN_AUTHORIZATION"}
        recs = (
            arch_record(packet(critique=[self._finding()])),
            arch_record(packet(current_evidence_refs=[])),
            arch_record(packet(current_evidence_refs=[{"path": SEED, "sha256": "0" * 64}])),
            arch_record(packet(hold={"reason": "needs owner sign-off", "requires_human_approval": True})),
            arch_record(),
        )
        for rec in recs:
            _, s = self._steer(rec)
            self.assertTrue(s["steps"])
            self.assertEqual(s["next_best_step_id"], s["steps"][0]["step_id"])
            self.assertEqual(s["reassess_after"]["category"], "REASSESS")
            self.assertEqual(s["reassess_after"]["after_step_ids"], [st["step_id"] for st in s["steps"]])
            self.assertEqual(s["continuation_scope"], "DESIGN_STEERING_NOT_MINING")
            self.assertFalse(s["new_executor"] or s["tool_execution_claimed"])
            for st in s["steps"]:
                self.assertRegex(st["action_code"], r"^[A-Z_]+$")
                self.assertIn(st["category"], allowed_cat)
                self.assertIsInstance(st["args"], dict)
                self.assertTrue(st["preconditions"])
                self.assertTrue(st["success_evidence_expected"])
                self.assertEqual(st["status"], "PROPOSED_NOT_EXECUTED")
                for v in st["args"].values():
                    self.assertTrue(isinstance(v, (str, list, bool, int)))
                    if isinstance(v, list):
                        self.assertLessEqual(len(v), 8)

    def test_review_evidence_repair_args_name_only_grounded_refs(self):
        bad = packet(current_evidence_refs=[{"path": SEED, "sha256": "0" * 64}])
        _, s = self._steer(arch_record(bad))
        self.assertEqual(s["steps"][0]["action_code"], "REPAIR_EVIDENCE_REF")
        self.assertEqual(s["steps"][0]["args"]["evidence_paths"], [SEED])

    def test_input_record_not_mutated(self):
        rec = arch_record(packet(critique=[self._finding()]))
        before = copy.deepcopy(rec)
        run(rec, ROOT, None)
        self.assertEqual(rec, before)


class SteeringLocalReadReassessTests(unittest.TestCase):
    """Bounded read-only steering continuation: one read, one re-assessment."""

    OWNER = "MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md"

    def _go(self, rec, src=OWNER, root=ROOT):
        return execute_local_steering_read_and_reassess(rec, root, src)

    def _missing(self):
        return arch_record(packet(current_evidence_refs=[]))

    def _counterexample(self):
        f = {"id": "F1", "source": "independent-claude-review", "severity": "MATERIAL",
             "targets_route_id": "B_REUSE", "counterexample": "legacy replay breaks",
             "disposition": "OPEN"}
        return arch_record(packet(critique=[f]))

    def test_missing_evidence_transitions_with_real_hash(self):
        import hashlib
        rec = self._missing()
        before = copy.deepcopy(rec)
        out = self._go(rec)
        self.assertEqual(out["status"], "EXECUTED_LOCAL_READ_ONLY_REASSESSED")
        self.assertEqual(out["assessment_before"]["state"], "DECISION_PENDING")
        self.assertEqual(out["assessment_after"]["state"], "READY_TO_EXECUTE_CHECKS")
        data = (ROOT / self.OWNER).read_bytes()
        rc = out["receipt"]
        self.assertEqual(rc["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(rc["read_bytes"], len(data))
        self.assertEqual(rc["action_code"], "INSPECT_CURRENT_ATTACH_EVIDENCE")
        self.assertEqual(rc["read_status"], "READ_HASH_COMPUTED")
        self.assertEqual(rc["reassessment_hash_status"], "READ_HASH_MATCHED")
        self.assertFalse(rc["semantic_relevance_verified"])
        self.assertEqual(rc["execution_status"], "EXECUTED_LOCAL_READ_ONLY")
        self.assertEqual(rc["original_route_authorized"], "unchanged")
        self.assertIs(rc["provider_invoked"], False)
        self.assertEqual(out["delta"]["state_transition"], ["DECISION_PENDING", "READY_TO_EXECUTE_CHECKS"])
        self.assertFalse(out["delta"]["still_unresolved"])
        self.assertFalse(out["design_correct_claimed"])
        self.assertFalse(out["recursive"])
        self.assertEqual(rec, before)  # input record never mutated

    def test_unrelated_global_gate_keeps_original_unauthorized(self):
        rec = self._missing()
        rec["approval_resume"] = {"required": True}
        rec.pop("human_approval_evidence", None)
        out = self._go(rec)
        # Human approval blocks the original mutation, not independent safe local
        # evidence collection. The read can proceed and approval must still persist.
        self.assertEqual(out["status"], "EXECUTED_LOCAL_READ_ONLY_REASSESSED")
        self.assertEqual(out["receipt"]["execution_status"], "EXECUTED_LOCAL_READ_ONLY")
        self.assertFalse(out["original_route_authorized"])
        self.assertTrue(out["checked_original_action_still_blocked"])
        self.assertTrue(out["next_steering"]["human_approval_unresolved"])
        self.assertEqual(out["next_steering"]["steps"][0]["action_code"], "OBTAIN_HUMAN_APPROVAL")
        self.assertFalse(out["next_steering"]["auto_dispatch"])

    def test_counterexample_stays_redirect_after_rebind(self):
        out = self._go(self._counterexample())
        self.assertEqual(out["status"], "EXECUTED_LOCAL_READ_ONLY_REASSESSED")
        self.assertEqual(out["receipt"]["action_code"], "READ_ONLY_REBIND_CURRENT_OWNER")
        self.assertEqual(out["assessment_after"]["state"], "REDIRECT_REQUIRED")
        self.assertTrue(out["delta"]["still_unresolved"])
        self.assertIsNone(out["delta"]["state_transition"])
        self.assertFalse(out["original_route_authorized"])
        self.assertTrue(out["checked_original_action_still_blocked"])
        self.assertTrue(out["next_steering"]["blocking"])

    def test_ineligible_action_code_untouched(self):
        rec = arch_record(packet(critique=[{
            "id": "F1", "source": "r", "severity": "MATERIAL", "targets_route_id": "B_REUSE",
            "counterexample": "x", "disposition": "OPEN"}], alternatives=[
            {"id": "B_REUSE", "summary": "Extend", "reuses_existing": True},
            {"id": "C", "summary": "grounded", "compatibility": {
                "rationale": "ok", "evidence_refs": [{"path": SEED, "sha256": SEED_SHA}]}}]))
        out = self._go(rec)
        self.assertEqual(out["status"], "INELIGIBLE")
        self.assertEqual(out["ineligible_action_code"], "EVALUATE_GROUNDED_ALTERNATIVE")
        self.assertIsNone(out["receipt"])
        self.assertIsNone(out["assessment_after"])

    def test_no_eligible_step_when_not_blocked(self):
        out = self._go(arch_record(packet()))
        self.assertEqual(out["status"], "INELIGIBLE")
        self.assertIsNone(out["receipt"])

    def test_prior_sensitive_evidence_denied_before_any_evaluation(self):
        from unittest.mock import patch
        rec = self._missing()
        rec["design_direction"]["current_evidence_refs"] = [
            {"path": "MASTER/.env.md", "sha256": "0" * 64}
        ]
        with patch("runtime_orchestrator.assess_design_direction",
                   side_effect=AssertionError("untrusted evidence evaluated")):
            out = self._go(rec)
        self.assertEqual(out["status"], "DENIED")
        self.assertEqual(out["reason"],
                         "EVIDENCE_PREFLIGHT_DENIED:SOURCE_TYPE_OR_SECRET_DENIED")
        self.assertIsNone(out["receipt"])

    def test_prior_evidence_count_budget_denied(self):
        rec = self._missing()
        rec["design_direction"]["current_evidence_refs"] = [
            {"path": SEED, "sha256": SEED_SHA} for _ in range(17)
        ]
        out = self._go(rec)
        self.assertEqual(out["status"], "DENIED")
        self.assertEqual(out["reason"], "EVIDENCE_READ_COUNT_EXCEEDED")
        self.assertIsNone(out["receipt"])

    def test_need_source_binding_without_source(self):
        for src in (None, "", "  "):
            out = self._go(self._missing(), src)
            self.assertEqual(out["status"], "NEED_SOURCE_BINDING")
            self.assertIsNone(out["receipt"])

    def test_source_denials(self):
        import tempfile
        cases = {
            "../README.md": "SOURCE_NOT_REPO_RELATIVE_OR_TRAVERSAL",
            "MASTER/../AGENTS.md": "SOURCE_NOT_REPO_RELATIVE_OR_TRAVERSAL",
            str(ROOT / self.OWNER): "SOURCE_NOT_REPO_RELATIVE_OR_TRAVERSAL",
            "/etc/passwd": "SOURCE_NOT_REPO_RELATIVE_OR_TRAVERSAL",
            "AGENTS.md": "SOURCE_OUTSIDE_AUTHORITY_ALLOWLIST",
            "ENFORCEMENT/runtime_orchestrator.py": "SOURCE_OUTSIDE_AUTHORITY_ALLOWLIST",
            "MASTER/" + "a" * 300 + ".md": "SOURCE_PATH_TOO_LONG",
            "MASTER/NOPE_DOES_NOT_EXIST.md": "SOURCE_NOT_A_FILE",
            "MASTER/.env.md": "SOURCE_TYPE_OR_SECRET_DENIED",
            "MASTER/binary.bin": "SOURCE_TYPE_OR_SECRET_DENIED",
        }
        for src, code in cases.items():
            rec = self._missing()
            before = copy.deepcopy(rec)
            out = self._go(rec, src)
            self.assertEqual((out["status"], out["reason"]), ("DENIED", code), src)
            self.assertIsNone(out["receipt"], src)
            self.assertEqual(rec, before)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "MASTER").mkdir()
            (root / "MASTER" / "big.md").write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            out = self._go(self._missing(), "MASTER/big.md", root)
            self.assertEqual(out["reason"], "SOURCE_TOO_LARGE")
            outside = root / "outside.md"
            outside.write_text("secret", encoding="utf-8")
            try:
                (root / "MASTER" / "link.md").symlink_to(outside)
            except (OSError, NotImplementedError):
                return  # symlink creation not permitted on this host
            out = self._go(self._missing(), "MASTER/link.md", root)
            self.assertEqual(out["reason"], "SOURCE_SYMLINK_OR_ALIAS_REDIRECT")
            self.assertIsNone(out["receipt"])

    def test_cli_requires_opt_in_and_runs_once(self):
        import contextlib
        import io
        import tempfile
        from runtime_orchestrator import main
        with tempfile.TemporaryDirectory() as td:
            rp = Path(td) / "rec.json"
            rp.write_text(json.dumps(self._missing()), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                main(["--record", str(rp), "--repo-root", str(ROOT), "--steering-source", self.OWNER])
            self.assertEqual(cm.exception.code, 2)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["--record", str(rp), "--repo-root", str(ROOT),
                           "--continue-steering-readonly", "--steering-source", self.OWNER])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(buf.getvalue())["assessment_after"]["state"],
                             "READY_TO_EXECUTE_CHECKS")

    def test_local_read_calls_full_runtime_only_once_and_reassesses_purely(self):
        from unittest.mock import patch
        with patch("runtime_orchestrator.run", wraps=run) as runtime:
            out = self._go(self._missing())
        self.assertEqual(runtime.call_count, 1)
        self.assertEqual(out["status"], "EXECUTED_LOCAL_READ_ONLY_REASSESSED")
        self.assertEqual(out["reassessment_scope"],
                         "DESIGN_STRUCTURE_ONLY_NOT_RUNTIME_AUTHORIZATION")
        self.assertEqual(out["assessment_after"]["state"], "READY_TO_EXECUTE_CHECKS")
        self.assertFalse(out["original_route_authorized"])
        self.assertTrue(out["checked_original_action_still_blocked"])
        self.assertFalse(out["provider_invoked"])

    def test_ineligible_continuation_does_not_run_effectful_runtime(self):
        from unittest.mock import patch
        with patch("runtime_orchestrator.run",
                   side_effect=AssertionError("full runtime should not execute")):
            out = self._go(arch_record(packet()))
        self.assertEqual(out["status"], "INELIGIBLE")
        self.assertEqual(out["reason"], "DESIGN_NOT_BLOCKED_FOR_LOCAL_STEERING")
        self.assertIsNone(out["receipt"])



class SteeringExecutorHandoffTests(unittest.TestCase):
    """Handoff provenance is tested without pretending Claude was invoked."""

    def _delegate_case(self):
        f = {"id": "F1", "source": "independent-review", "severity": "MATERIAL",
             "targets_route_id": "B_REUSE", "counterexample": "existing implementation fails",
             "disposition": "OPEN"}
        p = packet(critique=[f], alternatives=[
            {"id": "B_REUSE", "summary": "Existing route", "reuses_existing": True},
            {"id": "C_COMPATIBLE", "summary": "Alternative, evaluation only",
             "compatibility": {
                 "rationale": "Protected state retained",
                 "evidence_refs": [{"path": SEED, "sha256": SEED_SHA}],
             }},
        ])
        rec = arch_record(p)
        rec["steering_handoff_executor"] = "CLAUDE_CODE"
        rec["steering_handoff_reviewer"] = "CODEX"
        return rec

    def test_grounded_alternative_prepares_not_dispatches(self):
        from runtime_orchestrator import prepare_steering_executor_handoff
        rec = self._delegate_case()
        result = run(rec, ROOT, None)
        self.assertEqual(result["design_direction"]["state"], "REDIRECT_REQUIRED")
        handoff = prepare_steering_executor_handoff(rec, result, ROOT)
        self.assertEqual(handoff["status"], "PREPARED_NOT_DISPATCHED")
        self.assertEqual(handoff["handoff"]["next_step"]["action_code"],
                         "EVALUATE_GROUNDED_ALTERNATIVE")
        self.assertEqual(handoff["handoff"]["primary_outcome"],
                         rec["working_model"]["primary_outcome"])
        self.assertEqual(handoff["handoff"]["protected_state"],
                         rec["working_model"]["protected_state"])
        self.assertEqual(handoff["handoff"]["executor_role"],
                         "CLAUDE_PRIMARY_ANALYST_OR_IMPLEMENTER")
        targeted = handoff["handoff"]["targeted_candidate_evidence"]
        self.assertEqual([x["id"] for x in targeted], ["C_COMPATIBLE"])
        self.assertEqual(targeted[0]["steering_status"], "VIABLE_GROUNDED")
        self.assertEqual(targeted[0]["compatibility_evidence_refs"][0]["path"], SEED)
        self.assertNotIn("A_NEW_ENGINE", json.dumps(targeted))
        self.assertEqual(handoff["handoff"]["unresolved_focus_findings"][0]["id"], "F1")
        self.assertFalse(handoff["claude_invoked"])
        self.assertFalse(handoff["runtime_authorized"])

    def test_local_read_and_human_step_not_delegated(self):
        from runtime_orchestrator import prepare_steering_executor_handoff
        missing = arch_record(packet(current_evidence_refs=[]))
        self.assertEqual(
            prepare_steering_executor_handoff(missing, run(missing, ROOT, None), ROOT)["status"],
            "USE_LOCAL_READ_ONLY_CONTINUATION")
        human = arch_record(packet(hold={"reason": "requires owner",
                                        "requires_human_approval": True}))
        self.assertEqual(
            prepare_steering_executor_handoff(human, run(human, ROOT, None), ROOT)["status"],
            "HUMAN_DECISION_REQUIRED")

    def test_completed_local_read_advances_to_scoped_claude_scout(self):
        from runtime_orchestrator import prepare_steering_executor_handoff
        f = {"id": "F1", "source": "independent-review", "severity": "MATERIAL",
             "targets_route_id": "B_REUSE", "counterexample": "existing route fails",
             "disposition": "OPEN"}
        rec = arch_record(packet(critique=[f]))
        rec["steering_handoff_executor"] = "CLAUDE_CODE"
        rec["steering_handoff_reviewer"] = "CODEX"
        initial = run(rec, ROOT, None)
        self.assertEqual(initial["steering_continuation"]["steps"][0]["action_code"],
                         "READ_ONLY_REBIND_CURRENT_OWNER")
        prepared = prepare_steering_executor_handoff(
            rec, initial, ROOT, "MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md"
        )
        self.assertEqual(prepared["status"], "PREPARED_NOT_DISPATCHED")
        contract = prepared["handoff"]
        self.assertEqual(contract["next_step"]["action_code"], "SCOUT_VIABLE_ROUTE")
        self.assertEqual(contract["completed_local_read_proof"]["read_status"],
                         "READ_HASH_COMPUTED")
        self.assertEqual(contract["completed_local_read_proof"]["reassessment_hash_status"],
                         "READ_HASH_MATCHED")
        self.assertEqual(contract["completed_local_read_proof"]["task_id"],
                         rec["task_id"])
        self.assertFalse(prepared["claude_invoked"])

    def test_forged_or_wrong_task_runtime_cannot_prepare(self):
        from runtime_orchestrator import prepare_steering_executor_handoff
        rec = self._delegate_case()
        valid = run(rec, ROOT, None)
        fake = copy.deepcopy(valid)
        fake["steering_continuation"]["steps"][0]["args"] = {"alternative_ids": ["FORGED"]}
        self.assertEqual(prepare_steering_executor_handoff(rec, fake, ROOT)["status"],
                         "STEERING_GUIDANCE_NOT_BOUND_TO_RECORD")
        wrong = copy.deepcopy(rec)
        wrong["task_id"] = "different-task"
        self.assertEqual(
            prepare_steering_executor_handoff(wrong, valid, ROOT)["status"],
            "STALE_OR_UNTRUSTED_RUNTIME_RESULT")
        stale = copy.deepcopy(valid)
        stale["source_record_hash"] = "sha256:" + "0"*64
        self.assertEqual(
            prepare_steering_executor_handoff(rec, stale, ROOT)["status"],
            "STALE_OR_UNTRUSTED_RUNTIME_RESULT")

    def test_local_claude_cli_launch_adapter_with_stub_without_paid_calls(self):
        from runtime_orchestrator import (
            prepare_steering_executor_handoff, invoke_prepared_steering_claude)
        import tempfile
        import subprocess
        from pathlib import Path
        rec = self._delegate_case()
        prepared = prepare_steering_executor_handoff(rec, run(rec, ROOT, None), ROOT)
        self.assertEqual(prepared["status"], "PREPARED_NOT_DISPATCHED")
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            fake_executable = folder / "claude.exe"
            fake_executable.write_bytes(b"local-test-marker")
            calls = []
            def stub(args, **options):
                calls.append((args, options))
                return subprocess.CompletedProcess(args, 0, "Scout option comparison\n", "")
            receipt = invoke_prepared_steering_claude(
                prepared, ROOT, current_record=rec, runner=stub, cli_path=str(fake_executable))
            self.assertEqual(receipt["status"], "CLI_OUTPUT_RECEIVED_UNREVIEWED")
            self.assertTrue(receipt["process_launched"])
            self.assertFalse(receipt["claude_content_verified"])
            self.assertFalse(receipt["independently_verified"])
            self.assertFalse(receipt["route_authorized"])
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0][calls[0][0].index("--tools")+1],
                             "Read,Grep,Glob")
            self.assertNotIn("ANTHROPIC_API_KEY", calls[0][1]["env"])
            sent_prompt = calls[0][0][calls[0][0].index("-p") + 1]
            sent_brief = json.loads(sent_prompt.split("\n", 1)[1])
            self.assertEqual(sent_brief["primary_outcome"],
                             rec["working_model"]["primary_outcome"])
            self.assertEqual(sent_brief["protected_state"],
                             rec["working_model"]["protected_state"])
            self.assertEqual(sent_brief["targeted_candidate_evidence"][0]["id"],
                             "C_COMPATIBLE")
            self.assertEqual(sent_brief["targeted_candidate_evidence"][0]
                             ["compatibility_evidence_refs"][0]["sha256"], SEED_SHA)
            self.assertEqual(sent_brief["unresolved_focus_findings"][0]["id"], "F1")
            transcript = ROOT / receipt["local_transcript"]
            stored_receipt = ROOT / receipt["local_receipt_path"]
            self.assertTrue(transcript.is_file())
            self.assertTrue(stored_receipt.is_file())
            checked = receipt["local_return_assessment"]
            self.assertEqual(checked["status"], "UNVERIFIED_EXECUTOR_RETURN_CLAIM")
            self.assertFalse(checked["accepted"])
            self.assertFalse(checked["independently_verified"])
            from runtime_orchestrator import prepare_codex_review_from_steering_return
            handoff = prepare_codex_review_from_steering_return(
                prepared, receipt, rec, ROOT)
            self.assertEqual(handoff["status"], "CODEX_REVIEW_PREPARED_NOT_INVOKED")
            self.assertEqual(handoff["review"]["primary_outcome"],
                             rec["working_model"]["primary_outcome"])
            self.assertEqual(handoff["review"]["claude_transcript_sha256"],
                             receipt["stdout_sha256"])
            self.assertFalse(handoff["reviewer_invoked"])
            self.assertFalse(handoff["original_route_authorized"])
            from runtime_orchestrator import invoke_prepared_steering_codex
            import tempfile
            import subprocess
            from pathlib import Path
            with tempfile.TemporaryDirectory() as reviewer_tmp:
                fake_codex = Path(reviewer_tmp) / "codex.cmd"
                fake_codex.write_bytes(b"stub")
                reviewer_calls = []
                def reviewer_stub(args, **kwargs):
                    reviewer_calls.append((args, kwargs))
                    proposal = {
                        "verdict": "PROPOSE_REDIRECT",
                        "task_id": rec["task_id"],
                        "handoff_sha256": prepared["handoff_sha256"],
                        "claude_transcript_sha256":
                            handoff["review"]["claude_transcript_sha256"],
                        "finding_id": "F1",
                        "previous_route_id": "B_REUSE",
                        "recommended_route_id": "C_COMPATIBLE",
                        "rationale": "The original route fails. Earlier logs quoted TAKY REROUTE_REQUIRED; this is not a current CLI failure.",
                    }
                    return subprocess.CompletedProcess(
                        args, 0, json.dumps(proposal, ensure_ascii=False) + "\n", "")
                codex_result = invoke_prepared_steering_codex(
                    handoff, rec, ROOT, runner=reviewer_stub,
                    cli_path=str(fake_codex))
                self.assertEqual(codex_result["status"],
                                 "CODEX_TEXT_RECEIVED_UNVERIFIED")
                self.assertTrue(codex_result["reviewer_invoked"])
                self.assertFalse(codex_result["independently_verified"])
                self.assertFalse(codex_result["design_route_changed"])
                self.assertFalse(codex_result["user_goal_complete"])
                self.assertEqual(len(reviewer_calls), 1)
                self.assertEqual(reviewer_calls[0][0][2:4], ["-s", "read-only"])
                self.assertIn(".review-prompt.txt", reviewer_calls[0][0][-1])
                prompt_path = ROOT / codex_result["review_prompt_path"]
                self.assertTrue(prompt_path.is_file())
                body = prompt_path.read_text(encoding="utf-8")
                self.assertIn("handoff_sha256", body)
                self.assertIn(rec["working_model"]["primary_outcome"], body)
                self.assertEqual(codex_result["review_prompt_sha256"],
                                 __import__("hashlib").sha256(body.encode("utf-8")).hexdigest())
                self.assertNotIn("OPENAI_API_KEY", reviewer_calls[0][1]["env"])
                self.assertEqual(reviewer_calls[0][1]["env"].get(
                    "TAKY_USER_EXPLICIT_AUTHORIZATION"), "1")
                self.assertIn("read-only", reviewer_calls[0][1]["env"].get(
                    "TAKY_USER_INTENT", ""))
                reviewer_file = ROOT / codex_result["local_transcript"]
                self.assertTrue(reviewer_file.is_file())
                from runtime_orchestrator import draft_steering_redirect_from_codex_review
                original_chosen = rec["design_direction"]["chosen_route_id"]
                draft = draft_steering_redirect_from_codex_review(
                    prepared, receipt, codex_result, rec, ROOT)
                self.assertEqual(draft["status"], "REDIRECT_DRAFT_AWAITING_FALSIFICATION")
                from runtime_orchestrator import build_post_review_steering_continuation
                next_action = build_post_review_steering_continuation(
                    draft, rec, ROOT, prepared=prepared,
                    claude_receipt=receipt, codex_receipt=codex_result)
                self.assertEqual(next_action["status"],
                                 "FOLLOWUP_ACTION_PREPARED_NOT_EXECUTED")
                self.assertEqual(next_action["next_action_code"],
                                 "GATHER_REBUTTAL_EVIDENCE")
                self.assertEqual(next_action["next_task"]["candidate_route_id"],
                                 "C_COMPATIBLE")
                self.assertEqual(next_action["next_task"]["finding_id"], "F1")
                self.assertEqual(next_action["next_task"]["original_counterexample"],
                                 "existing implementation fails")
                self.assertTrue(next_action["next_task"]["reproduction_plan"])
                self.assertTrue(next_action["next_task"]["acceptance_conditions"])
                self.assertEqual(next_action["original_finding_status"], "OPEN")
                self.assertFalse(next_action["executor_invoked"])
                self.assertFalse(next_action["user_goal_complete"])
                stale = copy.deepcopy(rec)
                stale["design_direction"]["current_evidence_refs"][0]["sha256"] = "0" * 64
                stale_next = build_post_review_steering_continuation(
                    draft, stale, ROOT, prepared=prepared,
                    claude_receipt=receipt, codex_receipt=codex_result)
                self.assertEqual(stale_next["status"], "SOURCE_REBIND_REQUIRED")
                self.assertIsNone(stale_next["next_task"])
                self.assertEqual(stale_next["next_action_code"],
                                 "READ_ONLY_REBIND_CURRENT_OWNER")
                self.assertEqual(rec["design_direction"]["chosen_route_id"],
                                 original_chosen)
                held = build_post_review_steering_continuation(
                    {"status": "REVIEW_SUGGESTS_MORE_EVIDENCE",
                     "reason": "NO_PROVEN_ROUTE_CORRECTION"}, rec, ROOT,
                    prepared=prepared, claude_receipt=receipt,
                    codex_receipt=codex_result)
                self.assertIsNone(held["next_task"])
                self.assertEqual(held["reason"],
                                 "REVIEW_FEEDBACK_NOT_BOUND_TO_RECEIPTS")
                rejected = copy.deepcopy(draft)
                rejected["delta"]["proposed_route_id"] = "A_NEW_PARALLEL_ENGINE"
                denied = build_post_review_steering_continuation(
                    rejected, rec, ROOT, prepared=prepared,
                    claude_receipt=receipt, codex_receipt=codex_result)
                self.assertIsNone(denied["next_task"])
                self.assertEqual(denied["reason"], "REVIEW_FEEDBACK_NOT_BOUND_TO_RECEIPTS")
                forged = copy.deepcopy(draft)
                forged["delta"]["rationale"] = "fabricated but plausible"
                fake = build_post_review_steering_continuation(
                    forged, rec, ROOT, prepared=prepared,
                    claude_receipt=receipt, codex_receipt=codex_result)
                self.assertIsNone(fake["next_task"])
                self.assertEqual(fake["reason"], "REVIEW_FEEDBACK_NOT_BOUND_TO_RECEIPTS")
                missing_receipt = build_post_review_steering_continuation(
                    draft, rec, ROOT)
                self.assertIsNone(missing_receipt["next_task"])
                self.assertEqual(missing_receipt["reason"],
                                 "BOUND_MODEL_RECEIPTS_REQUIRED")
                self.assertEqual(draft["assessment_before"], "REDIRECT_REQUIRED")
                self.assertEqual(draft["assessment_after"], "REDIRECT_REQUIRED")
                self.assertFalse(draft["structural_validation"])
                self.assertEqual(draft["draft_record"]["design_direction"]["critique"][0]["disposition"],
                                 "OPEN")
                self.assertEqual(draft["draft_record"]["design_direction"]["chosen_route_id"],
                                 "C_COMPATIBLE")
                self.assertEqual(rec["design_direction"]["chosen_route_id"],
                                 original_chosen)
                self.assertFalse(draft["reviewer_identity_verified"])
                self.assertFalse(draft["original_route_authorized"])
                self.assertFalse(draft["changes_persisted"])
                original_reviewer_text = reviewer_file.read_bytes()
                try:
                    reviewer_file.write_bytes(original_reviewer_text + b" TAMPER")
                    tampered_review = draft_steering_redirect_from_codex_review(
                        prepared, receipt, codex_result, rec, ROOT)
                    self.assertEqual(tampered_review["reason"],
                                     "CODEX_OUTPUT_TAMPERED")
                    self.assertIsNone(tampered_review["draft_record"])
                finally:
                    reviewer_file.unlink()
                    prompt_path.unlink()
            # A changed output is not allowed to go forward to independent review.
            original_bytes = transcript.read_bytes()
            try:
                transcript.write_bytes(original_bytes + b" TAMPER")
                tampered = prepare_codex_review_from_steering_return(
                    prepared, receipt, rec, ROOT)
                self.assertEqual(tampered["status"], "NOT_ELIGIBLE")
                self.assertEqual(tampered["reason"],
                                 "TRANSCRIPT_HASH_OR_SIZE_MISMATCH")
                self.assertIsNone(tampered["review"])
            finally:
                transcript.write_bytes(original_bytes)
                transcript.unlink()
                stored_receipt.unlink()

    def test_external_local_directory_junction_is_rejected(self):
        from unittest.mock import patch
        from runtime_orchestrator import _trusted_steering_local_dir
        original_resolve = Path.resolve
        def displaced_resolve(p, *args, **kwargs):
            if p.name == ".local" and p.parent == ROOT:
                return ROOT.parent / "outside-local"
            return original_resolve(p, *args, **kwargs)
        with patch.object(Path, "resolve", displaced_resolve):
            self.assertIsNone(_trusted_steering_local_dir(ROOT))

    def test_oversized_brief_does_not_truncate_intent_or_launch(self):
        from runtime_orchestrator import (
            prepare_steering_executor_handoff, invoke_prepared_steering_claude)
        from executor_transport import sha256_json
        from unittest.mock import patch
        rec = self._delegate_case()
        # A large body of optional evidence can consume the entire prompt.
        # A self-hashed altered contract is NOT a source of CURRENT authority.
        valid = prepare_steering_executor_handoff(rec, run(rec, ROOT, None), ROOT)
        self.assertEqual(valid["status"], "PREPARED_NOT_DISPATCHED")
        bloated = copy.deepcopy(valid)
        bloated["handoff"]["existing_current_evidence_refs"] = [
            {"path": SEED, "sha256": SEED_SHA, "note": "x" * 15000}
        ]
        bloated["handoff_sha256"] = sha256_json(bloated["handoff"])
        with patch("subprocess.run",
                   side_effect=AssertionError("must never launch")):
            out = invoke_prepared_steering_claude(
                bloated, ROOT, current_record=rec)
        self.assertEqual(out["status"], "HANDOFF_CURRENT_TASK_BINDING_MISMATCH")
        self.assertFalse(out["process_launched"])

        # Even a CURRENT-bound oversized protected intent must never be
        # silently cut before reaching the delegated model.
        rec = self._delegate_case()
        rec["working_model"]["protected_state"].append("X" * 13000)
        rec["design_direction"]["protected_constraints"] = list(
            rec["working_model"]["protected_state"])
        prepared = prepare_steering_executor_handoff(rec, run(rec, ROOT, None), ROOT)
        self.assertEqual(prepared["status"], "PREPARED_NOT_DISPATCHED")
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as t:
            fake_exe = Path(t) / "claude.exe"
            fake_exe.write_bytes(b"stub")
            def should_not_run(*args, **kwargs):
                raise AssertionError("no truncated prompt may be sent")
            result = invoke_prepared_steering_claude(
                prepared, ROOT, current_record=rec,
                runner=should_not_run, cli_path=str(fake_exe))
        self.assertEqual(result["status"], "SCOUT_BRIEF_NEEDS_FOCUSED_EVIDENCE")
        self.assertFalse(result["process_launched"])

    def test_cli_session_limit_and_invalid_handoff_do_not_claim_execution(self):
        from runtime_orchestrator import (
            prepare_steering_executor_handoff, invoke_prepared_steering_claude)
        import tempfile
        import subprocess
        from pathlib import Path
        rec = self._delegate_case()
        prepared = prepare_steering_executor_handoff(rec, run(rec, ROOT, None), ROOT)
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            executable = folder / "claude.exe"
            executable.write_bytes(b"local-test-marker")
            seen = []
            def stub(args, **options):
                seen.append(args)
                return subprocess.CompletedProcess(
                    args, 1, "", "You've hit your session limit")
            capped = invoke_prepared_steering_claude(
                prepared, ROOT, current_record=rec, runner=stub, cli_path=str(executable))
            self.assertEqual(capped["status"], "CLAUDE_SESSION_LIMIT")
            self.assertFalse(capped["user_goal_complete"])
            self.assertFalse(capped["independently_verified"])
            self.assertEqual(len(seen), 1)
            stale_record = copy.deepcopy(rec)
            stale_record["working_model"]["primary_outcome"] = "other user goal"
            stale_result = invoke_prepared_steering_claude(
                prepared, ROOT, current_record=stale_record,
                runner=stub, cli_path=str(executable))
            self.assertEqual(stale_result["status"], "HANDOFF_CURRENT_TASK_BINDING_MISMATCH")
            self.assertEqual(len(seen), 1)
            altered = copy.deepcopy(prepared)
            altered["handoff"]["primary_outcome"] = "tampered"
            denied = invoke_prepared_steering_claude(
                altered, ROOT, current_record=rec, runner=stub, cli_path=str(executable))
            self.assertEqual(denied["status"], "HANDOFF_INTEGRITY_FAILED")
            self.assertEqual(len(seen), 1)
            altered = copy.deepcopy(prepared)
            altered["handoff"]["next_step"]["action_code"] = "IMPLEMENTATION_WRITE"
            from executor_transport import sha256_json
            altered["handoff_sha256"] = sha256_json(altered["handoff"])
            denied = invoke_prepared_steering_claude(
                altered, ROOT, current_record=rec, runner=stub, cli_path=str(executable))
            self.assertEqual(denied["status"], "CLAUDE_SCOUT_SCOPE_INVALID")
            self.assertEqual(len(seen), 1)

    def test_handoff_sensitive_evidence_denied_before_design_eval(self):
        from unittest.mock import patch
        from runtime_orchestrator import prepare_steering_executor_handoff
        rec = self._delegate_case()
        rec["design_direction"]["current_evidence_refs"] = [
            {"path": "MASTER/.env.md", "sha256": "0" * 64}]
        with patch("runtime_orchestrator.assess_design_direction",
                   side_effect=AssertionError("precheck not applied")):
            out = prepare_steering_executor_handoff(rec, {"detected": []}, ROOT)
        self.assertEqual(out["status"], "HANDOFF_EVIDENCE_PRECHECK_DENIED")
        self.assertIsNone(out["handoff"])

    def test_handoff_cannot_hide_missing_global_approval(self):
        from runtime_orchestrator import prepare_steering_executor_handoff
        rec = self._delegate_case()
        rec["approval_resume"] = {"required": True}
        real_result = run(rec, ROOT, None)
        forged = copy.deepcopy(real_result)
        forged["detected"] = [c for c in real_result["detected"]
                              if "APPROVAL" not in str(c).upper()]
        self.assertEqual(prepare_steering_executor_handoff(rec, forged, ROOT)["status"],
                         "GLOBAL_APPROVAL_BOUNDARY_MISMATCH")

    def test_return_mismatch_and_unverified_evidence(self):
        from runtime_orchestrator import (
            prepare_steering_executor_handoff, validate_steering_handoff_return)
        rec = self._delegate_case()
        out = prepare_steering_executor_handoff(rec, run(rec, ROOT, None), ROOT)
        contract = out["handoff"]
        receipt = {"task_id": contract["task_id"],
                   "step_id": contract["next_step"]["step_id"],
                   "action_code": contract["next_step"]["action_code"],
                   "handoff_sha256": out["handoff_sha256"],
                   "executor_role": "CLAUDE_PRIMARY_ANALYST_OR_IMPLEMENTER",
                   "executor_run_id": "external-unverified-test",
                   "result_status": "EXECUTED_WITH_EVIDENCE",
                   "evidence": [{"path": SEED, "sha256": SEED_SHA}]}
        mismatch = dict(receipt, handoff_sha256="0"*64)
        self.assertEqual(validate_steering_handoff_return(out, mismatch)["status"],
                         "RETURN_BINDING_MISMATCH")
        accepted = validate_steering_handoff_return(out, receipt)
        self.assertEqual(accepted["status"], "UNVERIFIED_EXECUTOR_RETURN_CLAIM")
        self.assertFalse(accepted["accepted"])
        self.assertFalse(accepted["executor_origin_verified"])
        self.assertEqual(accepted["task_id"], contract["task_id"])
        self.assertFalse(accepted["independently_verified"])
        self.assertFalse(accepted["design_route_changed"])
        self.assertFalse(accepted["human_approval_inferred"])
        self.assertEqual(
            validate_steering_handoff_return(out, dict(receipt, evidence=[]))["status"],
            "RESULT_EVIDENCE_MISSING")



class GuidedSteeringCycleTests(unittest.TestCase):
    """Deterministic stubs prove sequencing, not real model quality/execution."""

    def setUp(self):
        from design_direction_shepherd_test import SteeringExecutorHandoffTests
        self.record = SteeringExecutorHandoffTests()._delegate_case()
        from runtime_orchestrator import prepare_steering_executor_handoff
        self.prepared = prepare_steering_executor_handoff(
            self.record, run(self.record, ROOT, None), ROOT)
        self.assertEqual(self.prepared["status"], "PREPARED_NOT_DISPATCHED")

    @staticmethod
    def _cleanup(result):
        for item in (result.get("claude_receipt") or {},
                     result.get("codex_receipt") or {}):
            for label in ("local_transcript", "local_receipt_path", "review_prompt_path"):
                rel = item.get(label)
                if not isinstance(rel, str):
                    continue
                candidate = (ROOT / rel).resolve()
                if (candidate.parent == (ROOT / ".local").resolve()
                        and candidate.name.startswith("taky-local-")
                        and candidate.is_file()):
                    candidate.unlink()

    def test_single_cycle_scopes_claude_then_codex_then_reassesses(self):
        from runtime_orchestrator import run_guided_steering_cycle
        import subprocess
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            executable_claude = Path(folder) / "claude.exe"
            executable_codex = Path(folder) / "codex.cmd"
            executable_claude.write_bytes(b"fake")
            executable_codex.write_bytes(b"fake")
            calls = []
            def claude_runner(args, **kwargs):
                calls.append("CLAUDE")
                return subprocess.CompletedProcess(
                    args, 0, "Read-only Scout: inspect existing alternative\n", "")
            def codex_runner(args, **kwargs):
                calls.append("CODEX")
                import re
                match = re.search(
                    r"\.local/taky-local-codex-[0-9a-f]{32}\.review-prompt\.txt",
                    args[-1])
                self.assertIsNotNone(match)
                prompt_body = (ROOT / match.group()).read_text(encoding="utf-8")
                prompt_data = json.loads(prompt_body.split("\n", 1)[1])
                self.assertEqual(prompt_data["task_id"], self.record["task_id"])
                self.assertEqual(prompt_data["primary_outcome"],
                                 self.record["working_model"]["primary_outcome"])
                claim = {
                    "verdict": "PROPOSE_REDIRECT",
                    "task_id": prompt_data["task_id"],
                    "handoff_sha256": prompt_data["handoff_sha256"],
                    "claude_transcript_sha256": prompt_data["claude_transcript_sha256"],
                    "finding_id": "F1",
                    "previous_route_id": "B_REUSE",
                    "recommended_route_id": "C_COMPATIBLE",
                    "rationale": "Existing route fails; examine source-grounded alternative.",
                }
                return subprocess.CompletedProcess(args, 0,
                                                   json.dumps(claim) + "\n", "")
            before = copy.deepcopy(self.record)
            result = None
            try:
                result = run_guided_steering_cycle(
                    self.prepared, self.record, ROOT,
                    claude_runner=claude_runner, codex_runner=codex_runner,
                    claude_cli_path=str(executable_claude),
                    codex_cli_path=str(executable_codex))
                self.assertEqual(calls, ["CLAUDE", "CODEX"])
                self.assertEqual(result["status"],
                                 "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED")
                from runtime_orchestrator import inspect_local_guided_cycle_evidence
                observed = result["f1_local_evidence"]
                self.assertEqual(observed["status"],
                                 "TEST_INJECTED_OPEN_FINDING_OBSERVATION")
                self.assertEqual(observed["finding_disposition_after_review"],
                                 "OPEN")
                self.assertFalse(observed["user_goal_complete"])
                self.assertFalse(observed["model_origin_verified"])
                self.assertFalse(observed["current_code_f1_reproduced"])
                self.assertFalse(observed["provider_invoked_by_this_probe"])
                no_origin = copy.deepcopy(result)
                no_origin["claude_receipt"].pop("runner_origin", None)
                no_origin["codex_receipt"].pop("runner_origin", None)
                no_origin_observation = inspect_local_guided_cycle_evidence(
                    self.prepared, self.record, no_origin, ROOT)
                self.assertEqual(no_origin_observation["status"],
                                 "OPEN_FINDING_OBSERVED_ORIGIN_UNVERIFIED")
                self.assertFalse(no_origin_observation["model_origin_verified"])
                mismatched_draft = copy.deepcopy(result)
                mismatched_draft["design_feedback"]["delta"]["proposed_route_id"] = "B_REUSE"
                bad_draft = inspect_local_guided_cycle_evidence(
                    self.prepared, self.record, mismatched_draft, ROOT)
                self.assertEqual(bad_draft["reason"],
                                 "REVIEW_OUTPUT_VS_DRAFT_MISMATCH")
                third_route = copy.deepcopy(result)
                third_route["design_feedback"]["draft_record"]["design_direction"][
                    "chosen_route_id"] = "A_NEW_PARALLEL_ENGINE"
                third = inspect_local_guided_cycle_evidence(
                    self.prepared, self.record, third_route, ROOT)
                self.assertEqual(third["reason"],
                                 "OPEN_F1_BOUNDARY_NOT_REPRODUCED")
                missing_task = copy.deepcopy(self.prepared)
                record_no_id = copy.deepcopy(self.record)
                record_no_id.pop("task_id", None)
                missing_task["handoff"].pop("task_id", None)
                from executor_transport import sha256_json
                missing_task["handoff"]["record_sha256"] = sha256_json(record_no_id)
                missing_task["handoff_sha256"] = sha256_json(missing_task["handoff"])
                no_id = inspect_local_guided_cycle_evidence(
                    missing_task, record_no_id, result, ROOT)
                self.assertEqual(no_id["reason"],
                                 "HISTORICAL_TASK_BINDING_MISMATCH")
                bad_nested = copy.deepcopy(result)
                bad_nested["review_request"]["review"] = [1]
                nested = inspect_local_guided_cycle_evidence(
                    self.prepared, self.record, bad_nested, ROOT)
                self.assertEqual(nested["reason"],
                                 "INDEPENDENT_REVIEW_REQUEST_UNVERIFIED")
                broken = copy.deepcopy(result)
                broken["codex_receipt"]["stdout_sha256"] = "0" * 64
                tampered = inspect_local_guided_cycle_evidence(
                    self.prepared, self.record, broken, ROOT)
                self.assertEqual(tampered["reason"],
                                 "MODEL_TRANSCRIPT_HASH_OR_EXIT_INVALID")
                wrong_task = copy.deepcopy(self.record)
                wrong_task["working_model"]["primary_outcome"] = "tampered"
                rebound = inspect_local_guided_cycle_evidence(
                    self.prepared, wrong_task, result, ROOT)
                self.assertEqual(rebound["reason"],
                                 "HISTORICAL_TASK_BINDING_MISMATCH")
                self.assertEqual(result["post_review_continuation"]["status"],
                                 "FOLLOWUP_ACTION_PREPARED_NOT_EXECUTED")
                self.assertEqual(result["post_review_continuation"]["next_action_code"],
                                 "GATHER_REBUTTAL_EVIDENCE")
                self.assertFalse(result["post_review_continuation"]["user_goal_complete"])
                self.assertEqual(result["design_feedback"]["assessment_before"],
                                 "REDIRECT_REQUIRED")
                self.assertEqual(result["design_feedback"]["assessment_after"],
                                 "REDIRECT_REQUIRED")
                self.assertFalse(result["design_feedback"]["structural_validation"])
                self.assertEqual(result["design_feedback"]["draft_record"]
                                 ["design_direction"]["chosen_route_id"],
                                 "C_COMPATIBLE")
                self.assertEqual(self.record, before)
                self.assertFalse(result["original_route_authorized"])
                self.assertFalse(result["changes_persisted"])
                self.assertFalse(result["user_goal_complete"])
                self.assertFalse(result["automatic_retry"])
            finally:
                if isinstance(result, dict):
                    self._cleanup(result)

    def test_claude_failure_guides_without_invoking_codex(self):
        from runtime_orchestrator import run_guided_steering_cycle
        import subprocess
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            exe_claude = Path(folder) / "claude.exe"
            exe_codex = Path(folder) / "codex.cmd"
            exe_claude.write_bytes(b"fake")
            exe_codex.write_bytes(b"fake")
            called = []
            def limit_runner(args, **kwargs):
                called.append("CLAUDE")
                return subprocess.CompletedProcess(
                    args, 1, "", "You've hit your session limit")
            def forbidden_codex(*args, **kwargs):
                raise AssertionError("Codex cannot run without Claude receipt")
            result = run_guided_steering_cycle(
                self.prepared, self.record, ROOT,
                claude_runner=limit_runner, codex_runner=forbidden_codex,
                claude_cli_path=str(exe_claude), codex_cli_path=str(exe_codex))
            self.assertEqual(called, ["CLAUDE"])
            self.assertEqual(result["status"], "CLAUDE_EXECUTION_NOT_AVAILABLE")
            self.assertEqual(result["claude_receipt"]["status"],
                             "CLAUDE_SESSION_LIMIT")
            self.assertIsNone(result["codex_receipt"])
            self.assertIsNone(result["design_feedback"])
            self.assertFalse(result["user_goal_complete"])

    def test_cli_one_cycle_writes_truthful_local_receipt(self):
        from runtime_orchestrator import main
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from uuid import uuid4
        import io
        identifier = uuid4().hex
        record_path = ROOT / ".local" / ("test-steering-record-" + identifier + ".json")
        handoff_path = ROOT / ".local" / ("test-steering-handoff-" + identifier + ".json")
        local_receipt = None
        try:
            record_path.write_text(json.dumps(self.record), encoding="utf-8")
            handoff_path.write_text(json.dumps({"prepared": self.prepared}),
                                    encoding="utf-8")
            simulated = {
                "schema": "TAKY_BORDER_COLLIE_GUIDED_CYCLE_V1",
                "status": "CLAUDE_EXECUTION_NOT_AVAILABLE",
                "claude_receipt": {"status": "CLAUDE_SESSION_LIMIT"},
                "codex_receipt": None,
                "design_feedback": None,
                "original_route_authorized": False,
                "changes_persisted": False,
                "user_goal_complete": False,
            }
            stream = io.StringIO()
            with patch("runtime_orchestrator.run_guided_steering_cycle",
                       return_value=simulated) as cycle, redirect_stdout(stream):
                code = main([
                    "--repo-root", str(ROOT),
                    "--record", str(record_path),
                    "--prepared-handoff", str(handoff_path),
                    "--run-guided-steering-cycle",
                ])
            self.assertEqual(code, 1)
            cycle.assert_called_once()
            observed = json.loads(stream.getvalue())
            self.assertEqual(observed["status"], "CLAUDE_EXECUTION_NOT_AVAILABLE")
            self.assertIsNone(observed["codex_receipt"])
            self.assertFalse(observed["user_goal_complete"])
            local_receipt = ROOT / observed["local_cycle_receipt"]
            self.assertTrue(local_receipt.is_file())
            on_disk = json.loads(local_receipt.read_text(encoding="utf-8"))
            self.assertEqual(on_disk["status"], observed["status"])
            self.assertFalse(on_disk["original_route_authorized"])
        finally:
            for p in (record_path, handoff_path, local_receipt):
                if p is not None and p.is_file():
                    p.unlink()

    def test_invalid_handoff_runs_neither_provider(self):
        from runtime_orchestrator import run_guided_steering_cycle
        forged = copy.deepcopy(self.prepared)
        forged["handoff"]["primary_outcome"] = "forged"
        def must_not_invoke(*args, **kwargs):
            raise AssertionError("invalid contract cannot invoke an executor")
        result = run_guided_steering_cycle(
            forged, self.record, ROOT,
            claude_runner=must_not_invoke, codex_runner=must_not_invoke)
        self.assertEqual(result["status"], "CLAUDE_EXECUTION_NOT_AVAILABLE")
        self.assertEqual(result["claude_receipt"]["status"],
                         "HANDOFF_INTEGRITY_FAILED")
        self.assertIsNone(result["codex_receipt"])


class F1FollowupExecutionTests(unittest.TestCase):
    """F1 S2 continuation: local read-only evidence, never model/stub success.

    No network or LLM; injected CLI runners only exercise sequencing.
    """

    def setUp(self):
        from design_direction_shepherd_test import SteeringExecutorHandoffTests
        from runtime_orchestrator import prepare_steering_executor_handoff
        self.record = SteeringExecutorHandoffTests()._delegate_case()
        self.prepared = prepare_steering_executor_handoff(
            self.record, run(self.record, ROOT, None), ROOT)
        self.assertEqual(self.prepared["status"], "PREPARED_NOT_DISPATCHED")

    def _cycle(self, *, verdict="PROPOSE_REDIRECT", **options):
        import re
        import subprocess
        import tempfile
        from runtime_orchestrator import run_guided_steering_cycle
        with tempfile.TemporaryDirectory() as folder:
            exe_claude = Path(folder) / "claude.exe"
            exe_codex = Path(folder) / "codex.cmd"
            exe_claude.write_bytes(b"fake")
            exe_codex.write_bytes(b"fake")

            def claude_runner(args, **kwargs):
                return subprocess.CompletedProcess(args, 0, "Read-only Scout\n", "")

            def codex_runner(args, **kwargs):
                match = re.search(
                    r"\.local/taky-local-codex-[0-9a-f]{32}\.review-prompt\.txt", args[-1])
                data = json.loads((ROOT / match.group()).read_text(
                    encoding="utf-8").split("\n", 1)[1])
                claim = {
                    "verdict": "PROPOSE_REDIRECT", "task_id": data["task_id"],
                    "handoff_sha256": data["handoff_sha256"],
                    "claude_transcript_sha256": data["claude_transcript_sha256"],
                    "finding_id": "F1", "previous_route_id": "B_REUSE",
                    "recommended_route_id": "C_COMPATIBLE",
                    "rationale": "Existing route fails; examine source-grounded alternative.",
                }
                if verdict == "HOLD":
                    claim = {"verdict": "HOLD",
                             "reason": "F1 requires a concrete reproduction of the first refusal"}
                return subprocess.CompletedProcess(args, 0, json.dumps(claim) + "\n", "")

            result = run_guided_steering_cycle(
                self.prepared, self.record, ROOT,
                claude_runner=claude_runner, codex_runner=codex_runner,
                claude_cli_path=str(exe_claude), codex_cli_path=str(exe_codex), **options)
        self.addCleanup(GuidedSteeringCycleTests._cleanup, result)
        self.assertEqual(result["status"],
                         "GUIDED_REVIEW_NEEDS_ADDITIONAL_EVIDENCE"
                         if verdict == "HOLD" else
                         "GUIDED_REDIRECT_PROPOSED_NOT_APPLIED")
        return result

    def _execute(self, cycle, **options):
        from runtime_orchestrator import execute_post_review_f1_followup
        return execute_post_review_f1_followup(
            cycle["post_review_continuation"], self.record, ROOT,
            prepared=self.prepared, claude_receipt=cycle["claude_receipt"],
            codex_receipt=cycle["codex_receipt"], **options)

    def test_local_read_only_execution_leaves_f1_open_with_route_state_intact(self):
        before = copy.deepcopy(self.record)
        cycle = self._cycle(execute_f1_followup=True)
        out = cycle["f1_followup_execution"]
        self.assertEqual(out["status"], "READ_ONLY_EXECUTED_WITH_EVIDENCE")
        self.assertEqual(out["evidence_origin"], "LOCAL_READ_ONLY_FILES")
        self.assertTrue(out["executed_read_only"])
        self.assertTrue(out["model_receipts_injected"])  # stub runners are labelled, not trusted
        self.assertEqual(out["f1_status"], "OPEN")
        for flag in ("independently_verified", "f1_resolved", "user_goal_complete",
                     "original_route_authorized", "changes_persisted",
                     "current_owner_modified", "provider_invoked", "automatic_retry"):
            self.assertFalse(out[flag], flag)
        self.assertEqual(out["highest_status_reachable_locally"],
                         "READ_ONLY_EXECUTED_WITH_EVIDENCE")
        evidence = out["evidence"]
        self.assertTrue(all(r["read_status"] == "READ" for r in evidence["source_observation"]))
        self.assertEqual(evidence["static_dispatch_probe"]["result"],
                         "CALL_SITES_PRESENT_UNVERIFIED")
        self.assertFalse(evidence["static_dispatch_probe"][
                         "static_call_sites_are_execution_proof"])
        self.assertTrue(evidence["runtime_source_provenance"]["matches"])
        self.assertEqual(evidence["forged_feedback_probe"]["result"], "PASSED")
        self.assertEqual(out["next_task"]["action_code"],
                         "REQUEST_INDEPENDENT_REVIEW_OF_F1_EVIDENCE")
        self.assertEqual(out["next_task"]["next_role"], "CODEX_INDEPENDENT_REVIEW")
        self.assertEqual(out["next_task"]["evidence_receipt_sha256"], out["evidence_sha256"])
        self.assertEqual(out["next_task"]["status"], "PROPOSED_NOT_EXECUTED")
        from executor_transport import sha256_json
        self.assertEqual(out["evidence_sha256"], sha256_json(evidence))
        self.assertEqual(cycle["executed_vs_prepared"]["followup_executed"],
                         "READ_ONLY_EXECUTED_WITH_EVIDENCE")
        # Route chosen + rejected alternatives untouched; no CURRENT/record mutation.
        self.assertEqual(self.record, before)
        packet = self.record["design_direction"]
        self.assertEqual(packet["chosen_route_id"], "B_REUSE")
        rejected = {a["id"] for a in packet["alternatives"] if a.get("rejected_reason")}
        rejected_before = {a["id"] for a in before["design_direction"]["alternatives"]
                           if a.get("rejected_reason")}
        self.assertEqual(rejected, rejected_before)

    def test_hold_review_guides_to_evidence_without_route_adoption(self):
        from runtime_orchestrator import execute_post_review_f1_followup
        cycle = self._cycle(verdict="HOLD", execute_f1_followup=True)
        self.assertEqual(cycle["design_feedback"]["status"],
                         "REVIEW_SUGGESTS_MORE_EVIDENCE")
        out = cycle["f1_followup_execution"]
        self.assertEqual(out["status"], "READ_ONLY_EXECUTED_WITH_EVIDENCE")
        self.assertEqual(out["f1_status"], "OPEN")
        self.assertFalse(out["f1_resolved"])
        self.assertFalse(out["independently_verified"])
        self.assertFalse(out["original_route_authorized"])
        self.assertTrue(out["model_receipts_injected"])
        self.assertEqual(out["evidence"]["hold_review_trace"]["verdict"], "HOLD")
        self.assertFalse(out["evidence"]["hold_review_trace"][
                         "reviewer_identity_authenticated"])
        review_stage = out["evidence"]["observed_stage_sequence"][1]
        self.assertTrue(review_stage["review_transcript_hash_matched"])
        self.assertTrue(review_stage["source_hash_matched"])
        from unittest.mock import patch
        import runtime_orchestrator as ro
        with patch.object(ro, "_verify_local_ref",
                          return_value=("HASH_MISMATCH", SEED)):
            stale_feedback = ro.draft_steering_redirect_from_codex_review(
                self.prepared, cycle["claude_receipt"], cycle["codex_receipt"],
                self.record, ROOT)
            stale_continuation = ro.build_post_review_steering_continuation(
                stale_feedback, self.record, ROOT, prepared=self.prepared,
                claude_receipt=cycle["claude_receipt"],
                codex_receipt=cycle["codex_receipt"])
            stale = ro.execute_post_review_f1_followup(
                stale_continuation, self.record, ROOT, prepared=self.prepared,
                claude_receipt=cycle["claude_receipt"],
                codex_receipt=cycle["codex_receipt"])
        self.assertEqual(stale["status"], "READ_ONLY_EXECUTED_WITH_EVIDENCE")
        stale_stage = stale["evidence"]["observed_stage_sequence"][1]
        self.assertTrue(stale_stage["review_transcript_hash_matched"])
        self.assertFalse(stale_stage["source_hash_matched"])
        self.assertTrue(stale_stage["source_rebind_required"])
        self.assertEqual(stale["next_action_code"], "REBIND_REVIEW_TO_CURRENT_SOURCE")
        self.assertFalse(stale["f1_resolved"])
        self.assertEqual(out["next_task"]["action_code"],
                         "REPRODUCE_F1_FIRST_REFUSAL")
        self.assertEqual(out["next_task"]["next_role"], "CLAUDE_CODE")
        self.assertTrue(out["next_task"]["required_next_evidence"])
        self.assertEqual(cycle["executed_vs_prepared"]["followup_executed"],
                         "READ_ONLY_EXECUTED_WITH_EVIDENCE")
        tampered = copy.deepcopy(cycle["codex_receipt"])
        tampered["stdout_sha256"] = "0" * 64
        fail = execute_post_review_f1_followup(
            cycle["post_review_continuation"], self.record, ROOT,
            prepared=self.prepared, claude_receipt=cycle["claude_receipt"],
            codex_receipt=tampered)
        self.assertEqual(fail["status"], "INPUT_UNVERIFIED")
        self.assertFalse(fail["executed_read_only"])

    def test_default_cycle_only_prepares_and_reports_not_requested(self):
        cycle = self._cycle()
        self.assertNotIn("f1_followup_execution", cycle)
        self.assertEqual(cycle["executed_vs_prepared"]["followup_executed"], "NOT_REQUESTED")
        self.assertEqual(cycle["executed_vs_prepared"]["followup_prepared"],
                         "FOLLOWUP_ACTION_PREPARED_NOT_EXECUTED")

    def test_injected_observer_is_capped_at_action_prepared(self):
        cycle = self._cycle()
        calls = []

        def observer(repo_root, refs):
            calls.append(len(refs))
            return [{"path": "x", "read_status": "READ", "changed_since_review": False}]
        out = self._execute(cycle, observer=observer)
        self.assertEqual(len(calls), 1)
        self.assertGreater(calls[0], 0)
        self.assertEqual(out["status"], "ACTION_PREPARED")
        self.assertEqual(out["evidence_origin"], "TEST_INJECTED_OBSERVER")
        self.assertFalse(out["executed_read_only"])
        self.assertNotIn("evidence", out)
        self.assertIsNone(out["next_task"])
        self.assertFalse(out["f1_resolved"])

        def broken(repo_root, refs):
            raise RuntimeError("boom")
        failed = self._execute(cycle, observer=broken)
        self.assertEqual(failed["status"], "ACTION_PREPARED")
        self.assertEqual(failed["reason"], "OBSERVER_FAILED")

    def test_loaded_code_must_match_disk_source_before_observation(self):
        from unittest.mock import patch
        import runtime_orchestrator as ro
        cycle = self._cycle()
        with patch.object(ro, "_F1_LOADED_MODULE_SHA256", "0" * 64):
            out = self._execute(cycle)
        self.assertEqual(out["status"], "ACTION_PREPARED")
        self.assertFalse(out["executed_read_only"])
        self.assertEqual(out["reason"], "SOURCE_CHANGED_AFTER_IMPORT_RESTART_REQUIRED")
        self.assertEqual(out["next_action_code"],
                         "RESTART_RUNTIME_ON_PINNED_SOURCE_BEFORE_F1_PROBE")
        self.assertFalse(out["f1_resolved"])

    def test_forged_or_foreign_next_task_is_input_unverified(self):
        cycle = self._cycle()
        forged = copy.deepcopy(cycle["post_review_continuation"])
        forged["next_task"]["candidate_route_id"] = "A_NEW_ENGINE"
        forged_cycle = dict(cycle, post_review_continuation=forged)
        out = self._execute(forged_cycle)
        self.assertEqual(out["status"], "INPUT_UNVERIFIED")
        self.assertEqual(out["reason"], "NEXT_TASK_NOT_BOUND_TO_CURRENT_RECEIPTS")
        self.assertIsNone(out["next_task"])
        self.assertFalse(out["executed_read_only"])
        for bad in (None, {}, [], "GATHER_REBUTTAL_EVIDENCE"):
            self.assertEqual(self._execute(dict(cycle, post_review_continuation=bad))[
                "status"], "INPUT_UNVERIFIED")
        tampered_receipt = copy.deepcopy(cycle["codex_receipt"])
        tampered_receipt["stdout_sha256"] = "0" * 64
        swapped = self._execute(dict(cycle, codex_receipt=tampered_receipt))
        self.assertEqual(swapped["status"], "INPUT_UNVERIFIED")

    def test_source_change_after_review_forces_rebind_never_resolution(self):
        from unittest.mock import patch
        from runtime_orchestrator import build_post_review_steering_continuation
        import runtime_orchestrator as ro
        cycle = self._cycle()
        real = ro._verify_local_ref
        stale = ("HASH_MISMATCH", SEED)
        with patch.object(ro, "_verify_local_ref",
                          side_effect=lambda root, ref: stale):
            rebind = build_post_review_steering_continuation(
                ro.draft_steering_redirect_from_codex_review(
                    self.prepared, cycle["claude_receipt"], cycle["codex_receipt"],
                    self.record, ROOT),
                self.record, ROOT, prepared=self.prepared,
                claude_receipt=cycle["claude_receipt"],
                codex_receipt=cycle["codex_receipt"])
            out = ro.execute_post_review_f1_followup(
                rebind, self.record, ROOT, prepared=self.prepared,
                claude_receipt=cycle["claude_receipt"],
                codex_receipt=cycle["codex_receipt"])
        self.assertIs(ro._verify_local_ref, real)
        self.assertFalse(out["f1_resolved"])
        self.assertFalse(out["independently_verified"])
        self.assertEqual(out["f1_status"], "OPEN")
        if out["status"] == "READ_ONLY_EXECUTED_WITH_EVIDENCE":
            self.assertTrue(out["source_rebind_required"])
            self.assertEqual(out["next_action_code"], "REBIND_REVIEW_TO_CURRENT_SOURCE")
        else:  # earlier guard refused the stale chain: still no execution claim
            self.assertEqual(out["status"], "INPUT_UNVERIFIED")
            self.assertFalse(out["executed_read_only"])

    def test_source_observation_is_bounded_and_refuses_untrusted_paths(self):
        import hashlib
        import tempfile
        from runtime_orchestrator import _f1_observe_sources, _F1_SOURCE_MAX_BYTES
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.txt").write_bytes(b"one\ntwo\n")
            old = hashlib.sha256(b"one\ntwo\n").hexdigest()
            (root / "big.bin").write_bytes(b"0" * (_F1_SOURCE_MAX_BYTES + 1))
            refs = [{"path": "a.txt", "sha256": old},
                    {"path": "../outside.txt", "sha256": old},
                    {"path": "/etc/passwd", "sha256": old},
                    {"path": "C:/Windows/win.ini", "sha256": old},
                    {"path": "missing.txt", "sha256": old},
                    {"path": "big.bin", "sha256": old}]
            rows = {r["path"]: r for r in _f1_observe_sources(root, refs)}
            self.assertFalse(rows["a.txt"]["changed_since_review"])
            self.assertEqual(rows["a.txt"]["line_count"], 2)
            for unsafe in ("../outside.txt", "/etc/passwd", "C:/Windows/win.ini"):
                self.assertEqual(rows[unsafe]["read_status"], "UNSAFE_PATH")
                self.assertIsNone(rows[unsafe]["current_sha256"])
            self.assertEqual(rows["missing.txt"]["read_status"], "UNREADABLE")
            self.assertEqual(rows["big.bin"]["read_status"], "TOO_LARGE")
            (root / "a.txt").write_bytes(b"one\ntwo\nthree\n")
            changed = _f1_observe_sources(root, refs[:1])[0]
            self.assertTrue(changed["changed_since_review"])
            self.assertEqual(changed["pinned_sha256"], old)
            self.assertNotEqual(changed["current_sha256"], old)
            self.assertEqual(changed["line_count"], 3)
            try:
                (root / "link.txt").symlink_to(root / "a.txt")
            except (OSError, NotImplementedError):
                return  # symlink creation not permitted on this host
            link = _f1_observe_sources(root, [{"path": "link.txt", "sha256": old}])[0]
            self.assertEqual(link["read_status"], "SYMLINK_REFUSED")
            self.assertIsNone(link["current_sha256"])

    def test_cli_flag_requires_an_executing_mode(self):
        import io
        from contextlib import redirect_stderr
        from runtime_orchestrator import main
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            main(["--repo-root", str(ROOT), "--execute-f1-followup"])
        self.assertEqual(caught.exception.code, 2)


class LogicCouncilGateTests(unittest.TestCase):
    """Local replay of the controlled-runtime gate; no model is called."""

    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.roles = ["CONTRARIAN", "FIRST_PRINCIPLES", "EXPANSIONIST",
                      "OUTSIDER", "EXECUTOR"]

    def evidence(self, name, content):
        import hashlib
        data = content if isinstance(content, bytes) else json.dumps(
            content, ensure_ascii=False, sort_keys=True).encode("utf-8")
        path = self.root / name
        path.write_bytes(data)
        return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}

    def build(self, *, material=False):
        source = self.evidence("source.txt", b"USER_INTENT_AND_CURRENT_LOCKED")
        reports, digests = [], {}
        for role in self.roles:
            issues = ([{"id": "C1", "counterexample": "unsafe rollback"}]
                      if material and role == "CONTRARIAN" else [])
            report = {"perspective": role, "source_sha256": source["sha256"],
                      "analysis": "Independent perspective: " + role,
                      "material_findings": issues}
            if role == "CONTRARIAN":
                report["minority_position"] = "Keep rollback protected"
            ref = self.evidence(role + ".json", report)
            digests[role] = ref["sha256"]
            reports.append({"perspective": role, "evidence_ref": ref,
                            "origin_receipt_id": "pf:advisor:" + role})
        cross = []
        for index, target in enumerate(self.roles):
            reviewer = self.roles[(index + 1) % len(self.roles)]
            evidence = self.evidence("cross_" + target + ".json", {
                "reviewer": reviewer, "target": target,
                "source_sha256": source["sha256"],
                "target_sha256": digests[target],
                "critique": "Checked assumptions of " + target,
                "material_findings": []})
            cross.append({"reviewer": reviewer, "target": target,
                          "evidence_ref": evidence,
                          "origin_receipt_id": "pf:peer:" + reviewer})
        decision = {"chosen_route_id": "KEEP_EXISTING",
                    "minority_positions": [{"perspective": "CONTRARIAN",
                                             "position": "Keep rollback protected"}]}
        critique = ([{"id": "C1", "severity": "MATERIAL",
                     "counterexample": "unsafe rollback", "disposition": "OPEN"}]
                    if material else [])
        synthesis_ref = self.evidence("chair.json", {
            "source_sha256": source["sha256"],
            "chosen_route_id": "KEEP_EXISTING",
            "recommendation": "Keep existing design with verified conditions",
            "addressed_finding_ids": ["C1"] if material else []})
        return {"action_class": "GOVERNANCE_WRITE",
                "task_id": "RUNTIME-ORCH-PASS-001",
                "design_direction": {"chosen_route_id": "KEEP_EXISTING",
                                     "critique": critique},
                "logic_council": {"source_ref": source, "reviews": reports,
                                  "cross_reviews": cross, "decision": decision,
                                  "synthesis": {"evidence_ref": synthesis_ref,
                                                "origin_receipt_id": "pf:chair"}}}

    def signed_trace_fixture(self, council):
        """Test-only simulated signed ledger; no actual provider invocation."""
        from runtime_orchestrator import _canonical_hash
        from logic_council_origin import _stable_hash
        rows = council["reviews"] + council["cross_reviews"] + [council["synthesis"]]
        report_sha = {x["perspective"]: x["evidence_ref"]["sha256"]
                      for x in council["reviews"]}
        peer_sha = sorted(x["evidence_ref"]["sha256"]
                          for x in council["cross_reviews"])
        signed = {"authority_digest": "TEST_AUTH", "preflight_receipts": {},
                  "execution_calls": {}}
        for item in rows:
            rid = item["origin_receipt_id"]
            ref = item["evidence_ref"]
            payload = json.loads((self.root / ref["path"]).read_text(encoding="utf-8"))
            if rid.startswith("pf:advisor:"):
                stage, target_sha = "ADVISOR_" + item["perspective"], None
            elif rid.startswith("pf:peer:"):
                stage = "PEER_" + item["reviewer"]
                target_sha = report_sha[item["target"]]
            else:
                stage, target_sha = "CHAIR", _canonical_hash(peer_sha).removeprefix("sha256:")
            binding = {
                "schema": "TAKY_COUNCIL_BINDING_V1",
                "work_id": "RUNTIME-ORCH-PASS-001",
                "stage": stage,
                "source_sha256": council["source_ref"]["sha256"],
                "target_sha256": target_sha,
            }
            original_sha = council["source_ref"]["sha256"]
            if stage.startswith("ADVISOR_"):
                digests = [original_sha]
            elif stage.startswith("PEER_"):
                digests = [original_sha, target_sha]
            else:
                digests = [original_sha] + peer_sha
            call = {
                "model": "sonnet", "expected_calls": 1,
                "packet_digest": "a" * 20,
                "source_manifest": [
                    {"path": f"evidence/{i}.json", "sha256": digest, "complete": True}
                    for i, digest in enumerate(digests)
                ],
                "council_binding": binding}
            item["origin_call"] = call
            signed["preflight_receipts"][rid] = {
                "allowed": True, "call_allowed": True,
                "action_id": "review:external-model",
                "authority_digest": "TEST_AUTH",
                "call_digest": _stable_hash(call)}
            output = {"returncode": 0, "stdout": json.dumps(payload)}
            signed["execution_calls"][rid] = {
                "executor_id": "TAKY_MODEL_REVIEW_CLAUDE",
                "provider": "anthropic", "model": "sonnet",
                "status": "RETURNED", "actual_calls": 1,
                "result": output, "result_digest": _stable_hash(output)}
        return signed

    def test_five_prose_files_cannot_masquerade_as_real_council(self):
        outcome = assess_logic_council(self.build(), self.root)
        self.assertEqual(outcome["state"], "HOLD")
        self.assertIn("LOGIC_COUNCIL_TAKY2_TRUSTED_STORE_UNAVAILABLE",
                      outcome["detected"])
        self.assertEqual(len(outcome["perspectives_verified"]), 5)
        self.assertEqual(outcome["provider_calls_executed"], 0)
        self.assertFalse(outcome["independence_verified"])
        self.assertFalse(outcome["semantic_accuracy_verified"])

    def test_governance_action_cannot_omit_council(self):
        rec = self.build()
        rec.pop("logic_council")
        result = assess_logic_council(rec, self.root)
        self.assertEqual(result["detected"], ["LOGIC_COUNCIL_PACKET_MISSING"])
        runtime = base_record()
        runtime["action_class"] = "GOVERNANCE_WRITE"
        routed = run(runtime, ROOT, None)
        self.assertIn("LOGIC_COUNCIL_PACKET_MISSING", routed["detected"])
        self.assertFalse(routed["authorized_to_continue"])

    def test_routine_task_not_forced(self):
        rec = self.build()
        rec["action_class"] = "INSPECT"
        rec.pop("logic_council")
        self.assertFalse(assess_logic_council(rec, self.root)["required"])
        rec["logic_rule_change_planned"] = True
        self.assertIn("LOGIC_COUNCIL_PACKET_MISSING",
                      assess_logic_council(rec, self.root)["detected"])

    def test_governance_scope_cannot_hide_as_implementation(self):
        rec = self.build()
        rec.pop("logic_council")
        rec["action_class"] = "IMPLEMENTATION_WRITE"
        rec["allowed_change_scope"] = ["src/component.py"]
        self.assertFalse(assess_logic_council(rec, self.root)["required"])
        for scope in ("MASTER/MASTER_LOGIC.md", "OS/AI_CONNECTION_SECURITY.md",
                      "ENFORCEMENT/taky_gate.py", "TAKY.md",
                      "**/*", "**/*.md", "MASTER*"):
            rec["allowed_change_scope"] = [scope]
            self.assertIn("LOGIC_COUNCIL_PACKET_MISSING",
                          assess_logic_council(rec, self.root)["detected"])
            self.assertTrue(assess_design_direction(
                rec, derive_runtime_state(rec)[0], self.root)["required"])
        runtime = base_record()
        runtime["action_class"] = "IMPLEMENTATION_WRITE"
        runtime["allowed_change_scope"] = ["MASTER/MASTER_LOGIC.md"]
        routed = run(runtime, ROOT, None)
        self.assertIn("LOGIC_COUNCIL_PACKET_MISSING", routed["detected"])
        self.assertFalse(routed["authorized_to_continue"])

    def test_missing_or_tampered_report_blocks(self):
        rec = self.build()
        rec["logic_council"]["reviews"].pop()
        out = assess_logic_council(rec, self.root)
        self.assertTrue(any(c.startswith("LOGIC_COUNCIL_PERSPECTIVES_MISSING:")
                            for c in out["detected"]))
        rec = self.build()
        (self.root / "CONTRARIAN.json").write_text("TAMPERED", encoding="utf-8")
        out = assess_logic_council(rec, self.root)
        self.assertIn("LOGIC_COUNCIL_REVIEW_EVIDENCE_UNVERIFIED:CONTRARIAN",
                      out["detected"])
        rec = self.build()
        rec["logic_council"]["source_ref"]["path"] = "../outside.txt"
        self.assertIn("LOGIC_COUNCIL_SOURCE_UNVERIFIED",
                      assess_logic_council(rec, self.root)["detected"])

    def test_cross_review_bindings_and_coverage_block(self):
        rec = self.build()
        rec["logic_council"]["cross_reviews"].pop()
        self.assertIn("LOGIC_COUNCIL_CROSS_COVERAGE_INCOMPLETE",
                      assess_logic_council(rec, self.root)["detected"])
        rec = self.build()
        ref = rec["logic_council"]["cross_reviews"][0]["evidence_ref"]
        payload = json.loads((self.root / ref["path"]).read_text(encoding="utf-8"))
        payload["target_sha256"] = "0" * 64
        rec["logic_council"]["cross_reviews"][0]["evidence_ref"] = self.evidence(
            ref["path"], payload)
        self.assertTrue(any(c.startswith("LOGIC_COUNCIL_CROSS_REVIEW_CONTENT_MISMATCH")
                            for c in assess_logic_council(rec, self.root)["detected"]))

    def test_material_findings_and_minority_must_be_preserved(self):
        rec = self.build(material=True)
        self.assertFalse(any(x.startswith("LOGIC_COUNCIL_MATERIAL_FINDING_")
                             for x in assess_logic_council(rec, self.root)["detected"]))
        rec["design_direction"]["critique"].clear()
        self.assertIn("LOGIC_COUNCIL_MATERIAL_FINDING_NOT_TRANSFERRED:C1",
                      assess_logic_council(rec, self.root)["detected"])
        rec = self.build()
        rec["logic_council"]["decision"]["minority_positions"] = []
        self.assertIn("LOGIC_COUNCIL_MINORITY_POSITION_LOST:CONTRARIAN",
                      assess_logic_council(rec, self.root)["detected"])

    def test_peer_discovered_material_finding_cannot_disappear(self):
        rec = self.build()
        cross = rec["logic_council"]["cross_reviews"][0]
        ref = cross["evidence_ref"]
        peer = json.loads((self.root / ref["path"]).read_text(encoding="utf-8"))
        peer["material_findings"] = [{"id": "PEER1",
                                     "counterexample": "A newly found breach"}]
        cross["evidence_ref"] = self.evidence(ref["path"], peer)
        out = assess_logic_council(rec, self.root)
        self.assertIn("LOGIC_COUNCIL_MATERIAL_FINDING_NOT_TRANSFERRED:PEER1",
                      out["detected"])
        rec["design_direction"]["critique"] = [
            {"id": "PEER1", "counterexample": "A newly found breach",
             "severity": "MATERIAL", "disposition": "OPEN"}]
        self.assertFalse(any(x.startswith("LOGIC_COUNCIL_MATERIAL_FINDING_")
                             for x in assess_logic_council(rec, self.root)["detected"]))
        # The existing design-direction gate still blocks an OPEN material issue.
        full = arch_record(packet(critique=rec["design_direction"]["critique"]))
        assessed = run(full, ROOT, None)
        self.assertEqual(assessed["design_direction"]["state"], "REDIRECT_REQUIRED")
        self.assertFalse(assessed["authorized_to_continue"])

    def test_real_signed_store_rejects_fabricated_receipt_ids(self):
        """Exercise actual HMAC+anchor loader, never patch its trust boundary."""
        import shutil
        import tempfile
        rec = self.build()
        with tempfile.TemporaryDirectory(prefix=".taky_logic_gate_", dir=ROOT) as temp:
            for source in self.root.iterdir():
                if source.is_file():
                    shutil.copyfile(source, Path(temp) / source.name)
            prefix = Path(temp).relative_to(ROOT).as_posix()
            council = copy.deepcopy(rec["logic_council"])
            all_refs = ([council["source_ref"]]
                        + [r["evidence_ref"] for r in council["reviews"]]
                        + [r["evidence_ref"] for r in council["cross_reviews"]]
                        + [council["synthesis"]["evidence_ref"]])
            for ref in all_refs:
                ref["path"] = prefix + "/" + ref["path"]
            runtime = base_record()
            runtime["action_class"] = "GOVERNANCE_WRITE"
            runtime["logic_council"] = council
            runtime["design_direction"] = packet()
            council["decision"]["chosen_route_id"] = "B_REUSE"
            # A wrong chairman's route must block independently of call proofs.
            route = run(runtime, ROOT, None)
            self.assertEqual(route["logic_council"]["state"], "HOLD")
            self.assertEqual(route["logic_council"]["provider_calls_executed"], 0)
            self.assertFalse(route["authorized_to_continue"])
            self.assertTrue(any(
                "RECEIPT_NOT_FOUND_IN_SIGNED_STATE" in x
                or "TAKY2_SIGNED_STORE_READBACK_FAILED" in x
                for x in route["detected"]
            ), route["detected"])

    def test_signed_origin_fixture_runtime_route(self):
        """Mocked seal for positive unit route, not real 11-model execution."""
        from unittest.mock import patch as patch_callable
        import shutil
        import tempfile
        rec = self.build()
        council = copy.deepcopy(rec["logic_council"])
        council["decision"]["chosen_route_id"] = "B_REUSE"
        original_chair = json.loads((self.root / "chair.json").read_text(encoding="utf-8"))
        original_chair["chosen_route_id"] = "B_REUSE"
        council["synthesis"]["evidence_ref"] = self.evidence("chair.json", original_chair)
        trusted_fixture = self.signed_trace_fixture(council)
        with tempfile.TemporaryDirectory(prefix=".taky_logic_gate_", dir=ROOT) as temp:
            for source in self.root.iterdir():
                if source.is_file():
                    shutil.copyfile(source, Path(temp) / source.name)
            prefix = Path(temp).relative_to(ROOT).as_posix()
            refs = ([council["source_ref"]]
                    + [r["evidence_ref"] for r in council["reviews"]]
                    + [r["evidence_ref"] for r in council["cross_reviews"]]
                    + [council["synthesis"]["evidence_ref"]])
            for ref in refs:
                ref["path"] = prefix + "/" + ref["path"]
            runtime = base_record()
            runtime["action_class"] = "GOVERNANCE_WRITE"
            runtime["design_direction"] = packet()
            runtime["logic_council"] = council
            with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                                return_value=trusted_fixture):
                routed = run(runtime, ROOT, None)
            self.assertEqual(routed["logic_council"]["state"],
                             "EVIDENCED_CALLS_SEMANTICS_UNVERIFIED", routed["detected"])
            self.assertEqual(routed["logic_council"]["provider_calls_executed"], 11)
            self.assertEqual(routed["design_direction"]["state"], "READY_TO_EXECUTE_CHECKS")
            self.assertFalse(any(c.startswith(("LOGIC_COUNCIL", "DESIGN_DIRECTION"))
                                 for c in routed["detected"]), routed["detected"])
            self.assertTrue(routed["authorized_to_continue"], routed["detected"])

    def test_signed_receipt_mismatches_rejected(self):
        from unittest.mock import patch as patch_callable
        rec = self.build()
        trusted = self.signed_trace_fixture(rec["logic_council"])
        call = trusted["execution_calls"]["pf:advisor:CONTRARIAN"]
        call["result"]["stdout"] = json.dumps({"perspective": "CONTRARIAN", "fake": True})
        with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                            return_value=trusted):
            out = assess_logic_council(rec, self.root)
        self.assertEqual(out["state"], "HOLD")
        self.assertTrue(any("PROVIDER_RESULT_DIGEST_MISMATCH" in x
                            for x in out["detected"]), out["detected"])
        from logic_council_origin import _stable_hash
        call["result_digest"] = _stable_hash(call["result"])
        with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                            return_value=trusted):
            out = assess_logic_council(rec, self.root)
        self.assertTrue(any("FROZEN_REPORT_DIFFERS_FROM_EXECUTED_OUTPUT" in x
                            for x in out["detected"]), out["detected"])
        trusted = self.signed_trace_fixture(rec["logic_council"])
        rec["logic_council"]["cross_reviews"][0]["origin_receipt_id"] = (
            "pf:advisor:CONTRARIAN")
        with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                            return_value=trusted):
            out = assess_logic_council(rec, self.root)
        self.assertTrue(any("RECEIPT_ID_MISSING_OR_REUSED" in x
                            for x in out["detected"]), out["detected"])

    def test_governance_write_open_counterexample_is_not_advisory(self):
        rec = base_record()
        rec["action_class"] = "GOVERNANCE_WRITE"
        rec["design_direction"] = packet(critique=[{
            "id": "F1", "severity": "MATERIAL", "disposition": "OPEN",
            "counterexample": "Chosen rule breaks protected state",
            "targets_route_id": "B_REUSE"}])
        result = run(rec, ROOT, None)
        self.assertTrue(result["design_direction"]["required"])
        self.assertEqual(result["design_direction"]["state"], "REDIRECT_REQUIRED")
        self.assertTrue(any(x.startswith("DESIGN_DIRECTION_MATERIAL_COUNTEREXAMPLE_UNRESOLVED:")
                            for x in result["detected"]))
        self.assertIn("LOGIC_COUNCIL_PACKET_MISSING", result["detected"])
        self.assertFalse(result["authorized_to_continue"])

    def test_source_and_peer_material_must_enter_signed_model_packet(self):
        from unittest.mock import patch as patch_callable
        from logic_council_origin import _stable_hash
        for failure, receipt_id, mutation in (
            ("ORIGINAL_SOURCE_NOT_IN_CALL", "pf:advisor:CONTRARIAN",
             lambda data: data["source_manifest"][0].update(sha256="c" * 64)),
            ("FROZEN_TARGET_NOT_IN_PEER_CALL", "pf:peer:CONTRARIAN",
             lambda data: data["source_manifest"][1].update(sha256="d" * 64)),
            ("FIVE_FROZEN_PEERS_NOT_IN_CHAIR_CALL", "pf:chair",
             lambda data: data["source_manifest"].pop()),
            ("SIGNED_SOURCE_INPUTS_UNVERIFIED", "pf:advisor:CONTRARIAN",
             lambda data: data["source_manifest"][0].update(complete=False)),
        ):
            rec = self.build()
            trusted = self.signed_trace_fixture(rec["logic_council"])
            item = (next(x for x in rec["logic_council"]["reviews"]
                         if x["origin_receipt_id"] == receipt_id)
                    if receipt_id.startswith("pf:advisor:") else
                    next(x for x in rec["logic_council"]["cross_reviews"]
                         if x["origin_receipt_id"] == receipt_id)
                    if receipt_id.startswith("pf:peer:") else
                    rec["logic_council"]["synthesis"])
            mutation(item["origin_call"])
            trusted["preflight_receipts"][receipt_id]["call_digest"] = (
                _stable_hash(item["origin_call"]))
            with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                                return_value=trusted):
                checked = assess_logic_council(rec, self.root)
            self.assertEqual(checked["state"], "HOLD")
            self.assertTrue(any(failure in item for item in checked["detected"]),
                            checked["detected"])

    def test_signed_call_wrong_role_or_packet_is_hold(self):
        from unittest.mock import patch as patch_callable
        from logic_council_origin import _stable_hash
        rec = self.build()
        ledger = self.signed_trace_fixture(rec["logic_council"])
        role = rec["logic_council"]["reviews"][0]
        call = role["origin_call"]
        call["council_binding"]["stage"] = "ADVISOR_EXECUTOR"
        rid = role["origin_receipt_id"]
        ledger["preflight_receipts"][rid]["call_digest"] = _stable_hash(call)
        with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                            return_value=ledger):
            result = assess_logic_council(rec, self.root)
        self.assertTrue(any("CALL_INPUT_UNBOUND" in x
                            for x in result["detected"]), result["detected"])
        rec = self.build()
        ledger = self.signed_trace_fixture(rec["logic_council"])
        role = rec["logic_council"]["reviews"][0]
        role["origin_call"]["packet_digest"] = "INVALID"
        ledger["preflight_receipts"][role["origin_receipt_id"]]["call_digest"] = (
            _stable_hash(role["origin_call"]))
        with patch_callable("runtime_orchestrator.load_trusted_execution_runtime",
                            return_value=ledger):
            result = assess_logic_council(rec, self.root)
        self.assertEqual(result["state"], "HOLD")
        self.assertTrue(any("CALL_INPUT_UNBOUND" in x
                            for x in result["detected"]), result["detected"])

    def test_untrusted_repository_cannot_run_fake_signer(self):
        from logic_council_origin import (load_trusted_execution_runtime,
                                          CouncilOriginError)
        hostile = self.root / "TAKY"
        python_module = hostile / ".local" / "TAKY-2.0-ORCH" / "TAKY2"
        python_module.mkdir(parents=True)
        marker = self.root / "marker.txt"
        (python_module / "state_store.py").write_text(
            "open(" + repr(str(marker)) + ", 'w').write('EXECUTED')",
            encoding="utf-8")
        with self.assertRaisesRegex(CouncilOriginError,
                                    "TAKY2_TRUSTED_STORE_UNAVAILABLE"):
            load_trusted_execution_runtime(hostile)
        self.assertFalse(marker.exists())

    def test_chosen_route_mismatch_blocks(self):
        rec = self.build()
        rec["logic_council"]["decision"]["chosen_route_id"] = "NEW_ENGINE"
        self.assertIn("LOGIC_COUNCIL_DECISION_ROUTE_UNBOUND",
                      assess_logic_council(rec, self.root)["detected"])


if __name__ == "__main__":
    unittest.main()
