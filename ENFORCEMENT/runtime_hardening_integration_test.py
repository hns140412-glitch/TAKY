#!/usr/bin/env python3
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import codex_task_contract_builder as builder
import preflight_bridge as preflight
import runtime_orchestrator as ro
from runtime_orchestrator import run


ROOT = Path(__file__).resolve().parents[1]
BASE_FIXTURE = ROOT / "ENFORCEMENT" / "fixtures" / "runtime_orchestrator_pass.json"


def base_record():
    return json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))


def attach_delegated_worker(record, *, return_fields):
    record["forbidden_actions"] = ["production_deploy", "secret_read"]
    record["approval_scope"] = ["merge_review"]
    record["connection_scope"] = ["github_read"]
    record["cost_ceiling"] = 10
    record["worker_context"] = {
        "isolated": True,
        "allowed_context_refs": ["CURRENT:task"],
        "return_fields": list(return_fields),
    }
    parent = ro._delegation_parent_snapshot(record)
    record["delegation_contract"] = {
        "parent_task_id": record["task_id"],
        "parent_contract_hash": ro._canonical_hash(parent),
        "child_id": "worker-1",
        "inherited_rule_refs": list(parent["rule_refs"]),
        "inherited_change_scope": list(parent["change_scope"]),
        "inherited_forbidden_actions": list(parent["forbidden_actions"]),
        "inherited_approval_scope": list(parent["approval_scope"]),
        "inherited_connection_scope": list(parent["connection_scope"]),
        "inherited_cost_ceiling": 5,
        "return_contract": list(return_fields),
    }
    return record


def codes(result, prefix):
    return [x for x in result.get("detected", []) if str(x).startswith(prefix)]


def approval_binding_for(record, action_kind, action_payload, delegation=None):
    state, failures = ro.derive_runtime_state(record)
    if failures:
        raise AssertionError(f"invalid test record: {failures}")
    authority = ro._runtime_authority_snapshot(
        record,
        state,
        delegation or {"child_id": None, "contract_hash": None},
    )
    return {
        **authority,
        "runtime_authority_hash": ro._canonical_hash(authority),
        "action_kind": action_kind,
        "action_payload_hash": ro._canonical_hash(action_payload),
    }


class RuntimeHardeningIntegrationTest(unittest.TestCase):
    def test_intent_fidelity_baseline_contract_allows_original_task(self):
        record = base_record()
        self.assertEqual(preflight.validate_intent_fidelity(record, ROOT), [])
        self.assertEqual(
            [x for x in preflight.run(record, ROOT)["detected"] if x.startswith("INTENT_")],
            [],
        )

    def test_intent_fidelity_does_not_accept_unbound_assistant_contract(self):
        record = base_record()
        record.pop("intent_contract")
        self.assertIn("INTENT_CONTRACT_MISSING",
                      preflight.validate_intent_fidelity(record, ROOT))
        record = base_record()
        record["intent_contract"]["user_source_id"] = "fabricated-source"
        self.assertIn("INTENT_SOURCE_REFERENCE_UNBOUND",
                      preflight.validate_intent_fidelity(record, ROOT))
        record = base_record()
        record["working_model"]["primary_outcome"] = "Build a convenient website instead."
        self.assertIn("INTENT_WORKING_MODEL_OUTCOME_DIVERGED",
                      preflight.validate_intent_fidelity(record, ROOT))

    def test_intent_fidelity_replays_photo_pipeline_to_webapp_drift(self):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = (
            "사진 편집 파이프라인을 분석 검토해서 사례적 검토 후 구현해"
        )
        intent["requested_result"] = "인물의 특징을 지키는 사진 편집 처리 파이프라인"
        intent["requested_kind"] = "PIPELINE"
        intent["planned_kind"] = "APPLICATION"
        intent["planned_result"] = "사진 필터 웹앱"
        record["working_model"]["intent_contract"] = copy.deepcopy(intent)
        record["working_model"]["primary_outcome"] = intent["planned_result"]
        record["artifact_kind"] = "ui"
        detected = preflight.validate_intent_fidelity(record, ROOT)
        self.assertIn("INTENT_DELIVERABLE_KIND_DRIFT", detected)
        self.assertIn("SUBSTITUTE_RESULT_PIPELINE_TO_UI", detected)
        self.assertIn("INTENT_SOURCE_ANALYSIS_EVIDENCE_MISSING", detected)
        self.assertFalse(preflight.run(record, ROOT)["pass"])
        actual_route = run(record, ROOT, None)
        self.assertFalse(actual_route["pass"])
        self.assertIsNone(actual_route["route"])
        self.assertIn("INTENT_DELIVERABLE_KIND_DRIFT", actual_route["detected"])

    def test_literal_intent_prevents_both_sides_mislabeling_pipeline_as_app(self):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = (
            "인물 사진 가공 파이프라인을 세밀히 분석해 구현하라."
        )
        intent["requested_kind"] = "APPLICATION"  # assistant's faulty restatement
        intent["planned_kind"] = "APPLICATION"
        intent["requested_result"] = "사진 필터 웹앱"
        intent["planned_result"] = "사진 필터 웹앱"
        record["working_model"]["primary_outcome"] = intent["planned_result"]
        record["working_model"]["intent_contract"] = copy.deepcopy(intent)
        self.assertIn("INTENT_LITERAL_PIPELINE_RELABELED",
                      preflight.validate_intent_fidelity(record, ROOT))

    def test_latest_correction_can_explicitly_replace_pipeline_with_app(self):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = "파이프라인을 분석한 후 구현해"
        intent["latest_user_correction"] = "파이프라인 말고 웹앱으로 구현해"
        intent["requested_kind"] = "APPLICATION"
        intent["planned_kind"] = "APPLICATION"
        intent["requested_result"] = "웹앱"
        intent["planned_result"] = "웹앱"
        record["working_model"]["primary_outcome"] = "웹앱"
        record["working_model"]["intent_contract"] = copy.deepcopy(intent)
        errors = preflight.validate_intent_fidelity(record, ROOT)
        self.assertNotIn("INTENT_LITERAL_PIPELINE_RELABELED", errors)

    def test_intent_fidelity_requires_actual_source_analysis_before_spec(self):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = "원문을 분석하고 사례 검토한 후 기능 구현"
        intent["requested_result"] = "사진 처리 파이프라인"
        intent["requested_kind"] = "PIPELINE"
        intent["planned_kind"] = "PIPELINE"
        intent["planned_result"] = "사진 처리 파이프라인"
        intent["analysis_before_implementation"] = True
        record["working_model"]["intent_contract"] = copy.deepcopy(intent)
        record["working_model"]["primary_outcome"] = intent["planned_result"]
        self.assertIn("INTENT_SOURCE_ANALYSIS_EVIDENCE_MISSING",
                      preflight.validate_intent_fidelity(record, ROOT))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "original.txt").write_text("actual source input", encoding="utf-8")
            src_hash = hashlib.sha256((path / "original.txt").read_bytes()).hexdigest()
            (path / "review.txt").write_text(f"comparison of source {src_hash}", encoding="utf-8")
            intent["source_analysis_evidence"] = [{
                "source_path": "original.txt", "analysis_path": "review.txt",
                "source_sha256": src_hash,
                "analysis_sha256": hashlib.sha256((path / "review.txt").read_bytes()).hexdigest(),
            }]
            record["working_model"]["intent_contract"] = copy.deepcopy(intent)
            self.assertEqual(preflight.validate_intent_fidelity(record, path), [])
            self.assertIs(preflight.run(record, path)["semantic_analysis_verified"], False)
            (path / "review.txt").write_text("changed without re-review", encoding="utf-8")
            self.assertIn("INTENT_ANALYSIS_PROOF_HASH_MISMATCH",
                          preflight.validate_intent_fidelity(record, path))

    def test_irrelevant_file_hash_is_not_accepted_as_source_analysis(self):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = "원문을 분석하고 사례 검토한 후 기능 구현"
        intent["requested_kind"] = intent["planned_kind"] = "PIPELINE"
        intent["requested_result"] = intent["planned_result"] = "사진 처리 파이프라인"
        intent["analysis_before_implementation"] = True
        record["working_model"]["primary_outcome"] = intent["planned_result"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            (path / "original.txt").write_text("actual source input", encoding="utf-8")
            (path / "unrelated.txt").write_text("a changelog nobody compared", encoding="utf-8")
            src_hash = hashlib.sha256((path / "original.txt").read_bytes()).hexdigest()
            evidence = {
                "source_path": "original.txt", "analysis_path": "unrelated.txt",
                "source_sha256": src_hash,
                "analysis_sha256": hashlib.sha256((path / "unrelated.txt").read_bytes()).hexdigest(),
            }
            for label, ev, expected in (
                ("uncited", evidence, "INTENT_ANALYSIS_DOES_NOT_CITE_SOURCE"),
                ("no source hash", {k: v for k, v in evidence.items() if k != "source_sha256"},
                 "INTENT_ANALYSIS_SOURCE_BINDING_INVALID"),
                ("same file", {**evidence, "analysis_path": "original.txt",
                               "analysis_sha256": src_hash},
                 "INTENT_ANALYSIS_SOURCE_BINDING_INVALID"),
            ):
                intent["source_analysis_evidence"] = [ev]
                record["working_model"]["intent_contract"] = copy.deepcopy(intent)
                self.assertIn(expected, preflight.validate_intent_fidelity(record, path), label)

    def _pipeline_record(self, original, correction="", kind="APPLICATION", planned_kind=None):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = original
        intent["latest_user_correction"] = correction
        intent["requested_kind"] = kind
        intent["planned_kind"] = planned_kind or kind
        intent["requested_result"] = intent["planned_result"] = "결과"
        record["working_model"]["primary_outcome"] = "결과"
        record["working_model"]["intent_contract"] = copy.deepcopy(intent)
        return record

    def test_non_overriding_correction_keeps_original_pipeline_constraint(self):
        original = "photo processing 파이프 라인 사례를 분석한 뒤 구현해"
        for correction in ("분석한 내용 반영해", "더 세밀하게", ""):
            record = self._pipeline_record(original, correction)
            self.assertIn("INTENT_LITERAL_PIPELINE_RELABELED",
                          preflight.validate_intent_fidelity(record, ROOT), correction)

    def test_spaced_korean_pipeline_spelling_is_recognised(self):
        record = self._pipeline_record("사진 파이프 라인을 구현해")
        self.assertIn("INTENT_LITERAL_PIPELINE_RELABELED",
                      preflight.validate_intent_fidelity(record, ROOT))

    def test_pipeline_relabel_caught_when_only_planned_kind_drifts(self):
        record = self._pipeline_record("파이프라인을 구현해", kind="PIPELINE", planned_kind="APPLICATION")
        self.assertIn("INTENT_LITERAL_PIPELINE_RELABELED",
                      preflight.validate_intent_fidelity(record, ROOT))

    def test_genuine_user_override_and_true_pipeline_are_not_blocked(self):
        override = self._pipeline_record("파이프 라인을 분석한 후 구현해", "파이프 라인 말고 웹앱으로 구현해")
        self.assertNotIn("INTENT_LITERAL_PIPELINE_RELABELED",
                         preflight.validate_intent_fidelity(override, ROOT))
        honest = self._pipeline_record("파이프 라인을 구현해", "분석한 내용 반영해", kind="PIPELINE")
        self.assertNotIn("INTENT_LITERAL_PIPELINE_RELABELED",
                         preflight.validate_intent_fidelity(honest, ROOT))

    def test_task_contract_carries_original_intent_and_latest_correction(self):
        record = base_record()
        intent = record["intent_contract"]
        intent["literal_user_request"] = "photo processing 파이프 라인을 구현해"
        intent["latest_user_correction"] = "분석한 내용 반영해"
        result = builder.build(record)
        self.assertTrue(result["pass"], result["detected"])
        task = result["task_contract"]
        self.assertEqual(task["original_user_intent"]["text"], intent["literal_user_request"])
        self.assertEqual(task["original_user_intent"]["source"], "user")
        self.assertEqual(task["latest_user_correction"]["text"], "분석한 내용 반영해")

    def test_task_contract_without_correction_still_carries_original_intent(self):
        result = builder.build(base_record())
        self.assertTrue(result["pass"], result["detected"])
        self.assertIn("original_user_intent", result["task_contract"])
        self.assertNotIn("latest_user_correction", result["task_contract"])

    def test_task_contract_rejects_untraceable_user_intent(self):
        record = base_record()
        record["intent_contract"]["user_source_id"] = "fabricated-source"
        result = builder.build(record)
        self.assertFalse(result["pass"])
        self.assertIn("TASK_INTENT_SOURCE_UNBOUND", result["detected"])
        record = base_record()
        record["intent_contract"]["literal_user_request"] = "  "
        self.assertIn("TASK_INTENT_LITERAL_MISSING", builder.build(record)["detected"])
        record = base_record()
        record["intent_contract"]["latest_user_correction"] = 5
        self.assertIn("TASK_INTENT_CORRECTION_INVALID", builder.build(record)["detected"])

    def test_context_firewall_blocks_bulk_parent_context(self):
        record = attach_delegated_worker(base_record(), return_fields=["finding"])
        record["worker_context"]["full_chat_history"] = ["do not forward"]
        result = run(record, ROOT, None)
        self.assertTrue(
            codes(result, "CONTEXT_FIREWALL_FORBIDDEN_BULK_CONTEXT"),
            result.get("detected"),
        )

    def test_context_firewall_accepts_bounded_context(self):
        record = attach_delegated_worker(
            base_record(),
            return_fields=["finding", "evidence_ref"],
        )
        result = run(record, ROOT, None)
        self.assertEqual(codes(result, "CONTEXT_FIREWALL_"), [])
        self.assertEqual(codes(result, "DELEGATION_"), [])
        self.assertTrue((result.get("delegation_inheritance") or {}).get("valid"))

    def test_worker_context_requires_delegation_contract(self):
        record = base_record()
        record["worker_context"] = {
            "isolated": True,
            "allowed_context_refs": ["CURRENT:task"],
            "return_fields": ["finding"],
        }
        result = run(record, ROOT, None)
        self.assertIn("DELEGATION_CONTRACT_REQUIRED", result.get("detected", []))

    def test_delegation_cannot_widen_change_scope(self):
        record = attach_delegated_worker(base_record(), return_fields=["finding"])
        record["delegation_contract"]["inherited_change_scope"].append(
            "src/unapproved-component"
        )
        result = run(record, ROOT, None)
        self.assertIn("DELEGATION_CHANGE_SCOPE_WIDENED", result.get("detected", []))

    def test_delegation_cannot_drop_parent_forbidden_action(self):
        record = attach_delegated_worker(base_record(), return_fields=["finding"])
        record["delegation_contract"]["inherited_forbidden_actions"] = [
            "production_deploy"
        ]
        result = run(record, ROOT, None)
        self.assertIn("DELEGATION_FORBIDDEN_ACTION_DROPPED", result.get("detected", []))

    def test_delegation_cannot_raise_cost_ceiling(self):
        record = attach_delegated_worker(base_record(), return_fields=["finding"])
        record["delegation_contract"]["inherited_cost_ceiling"] = 11
        result = run(record, ROOT, None)
        self.assertIn("DELEGATION_COST_SCOPE_WIDENED", result.get("detected", []))

    def test_delegation_cannot_drop_bounded_cost_ceiling(self):
        record = attach_delegated_worker(base_record(), return_fields=["finding"])
        record["delegation_contract"].pop("inherited_cost_ceiling")
        result = run(record, ROOT, None)
        self.assertIn("DELEGATION_COST_CEILING_REQUIRED", result.get("detected", []))

    def test_delegation_rejects_nan_cost_ceiling(self):
        record = attach_delegated_worker(base_record(), return_fields=["finding"])
        record["delegation_contract"]["inherited_cost_ceiling"] = float("nan")
        result = run(record, ROOT, None)
        self.assertIn("DELEGATION_COST_CEILING_REQUIRED", result.get("detected", []))

    def test_malformed_worker_context_cannot_disable_delegation(self):
        record = base_record()
        record["worker_context"] = ["not", "a", "contract"]
        result = run(record, ROOT, None)
        self.assertIn("CONTEXT_FIREWALL_WORKER_CONTEXT_INVALID", result.get("detected", []))
        self.assertIn("DELEGATION_WORKER_CONTEXT_INVALID", result.get("detected", []))

    def test_synthesis_barrier_blocks_missing_child(self):
        record = base_record()
        record["synthesis_barrier"] = {
            "required": True,
            "expected_children": ["research-a", "research-b"],
            "child_results": [
                {
                    "child_id": "research-a",
                    "status": "COMPLETED",
                    "structured_result": {"finding": "a"},
                }
            ],
        }
        result = run(record, ROOT, None)
        self.assertIn(
            "SYNTHESIS_CHILD_RESULTS_INCOMPLETE:research-b",
            result.get("detected", []),
        )

    def test_synthesis_barrier_accepts_all_structured_children(self):
        record = base_record()
        record["synthesis_barrier"] = {
            "required": True,
            "expected_children": ["research-a", "research-b"],
            "child_results": [
                {
                    "child_id": "research-a",
                    "status": "COMPLETED",
                    "structured_result": {"finding": "a"},
                },
                {
                    "child_id": "research-b",
                    "status": "COMPLETED",
                    "structured_result": {"finding": "b"},
                },
            ],
        }
        result = run(record, ROOT, None)
        self.assertEqual(codes(result, "SYNTHESIS_"), [])
        barrier = result.get("synthesis_barrier") or {}
        self.assertTrue(barrier.get("synthesis_ready"))

    def test_side_effect_guard_blocks_duplicate_effect(self):
        record = base_record()
        record["side_effect_guard"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "effect_id": "deploy-001",
            "idempotency_key": "idem-deploy-001",
            "action_payload_hash": "sha256:" + "a" * 64,
            "action_kind": "DEPLOY",
            "target_ref": "production:site",
        }
        with mock.patch.object(
            ro,
            "guard_side_effect",
            return_value={
                "pass": False,
                "detected": ["SIDE_EFFECT_DUPLICATE_EXECUTION_FORBIDDEN"],
                "decision": "BLOCK_DUPLICATE",
            },
        ):
            result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertIn(
            "SIDE_EFFECT_DUPLICATE_EXECUTION_FORBIDDEN",
            result.get("detected", []),
        )

    def test_side_effect_guard_allows_first_execution(self):
        record = base_record()
        record["side_effect_guard"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "effect_id": "deploy-001",
            "idempotency_key": "idem-deploy-001",
            "action_payload_hash": "sha256:" + "a" * 64,
            "action_kind": "DEPLOY",
            "target_ref": "production:site",
        }
        with mock.patch.object(
            ro,
            "guard_side_effect",
            return_value={
                "pass": True,
                "detected": [],
                "decision": "ALLOW_FIRST_EXECUTION",
            },
        ):
            result = run(record, ROOT, None)
        self.assertNotIn(
            "SIDE_EFFECT_DUPLICATE_EXECUTION_FORBIDDEN",
            result.get("detected", []),
        )
        self.assertEqual(
            (result.get("side_effect_guard") or {}).get("decision"),
            "ALLOW_FIRST_EXECUTION",
        )

    def test_release_intent_requires_result_preview_guard(self):
        record = base_record()
        record["release_intent"] = True
        result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertIn(
            "RESULT_PREVIEW_GUARD_REQUIRED_FOR_RELEASE",
            result.get("detected", []),
        )

    def test_revision_bound_result_preview_allows_release_lane(self):
        record = base_record()
        record["release_intent"] = True
        record["result_preview_guard"] = {
            "required": True,
            "preview_record": {"synthetic": "preview"},
            "release_request": {"synthetic": "release"},
        }
        with mock.patch.object(
            ro,
            "validate_preview",
            return_value={
                "pass": True,
                "detected": [],
                "task_id": record["task_id"],
                "preview_required": True,
                "acceptance_result": "PASS",
                "release_eligible": True,
                "result_revision_hash": "sha256:" + "a" * 64,
                "preview_receipt_hash": "sha256:" + "b" * 64,
            },
        ), mock.patch.object(
            ro,
            "validate_release",
            return_value={
                "pass": True,
                "detected": [],
                "release_binding_hash": "sha256:" + "c" * 64,
                "release_binding": {"target": "production"},
            },
        ):
            result = run(record, ROOT, None)
        self.assertNotIn(
            "RESULT_PREVIEW_GUARD_REQUIRED_FOR_RELEASE",
            result.get("detected", []),
        )
        gate = result.get("result_preview_guard") or {}
        self.assertTrue(gate.get("pass"), gate)

    def test_release_revision_mismatch_is_blocked(self):
        record = base_record()
        record["release_intent"] = True
        record["result_preview_guard"] = {
            "required": True,
            "preview_record": {"synthetic": "preview"},
            "release_request": {"synthetic": "release"},
        }
        with mock.patch.object(
            ro,
            "validate_preview",
            return_value={
                "pass": True,
                "detected": [],
                "task_id": record["task_id"],
                "preview_required": True,
                "acceptance_result": "PASS",
                "release_eligible": True,
                "result_revision_hash": "sha256:" + "a" * 64,
                "preview_receipt_hash": "sha256:" + "b" * 64,
            },
        ), mock.patch.object(
            ro,
            "validate_release",
            return_value={
                "pass": False,
                "detected": ["RESULT_RELEASE_REVISION_MISMATCH"],
                "release_binding_hash": None,
                "release_binding": None,
            },
        ):
            result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertIn(
            "RESULT_RELEASE_REVISION_MISMATCH",
            result.get("detected", []),
        )

    def test_valid_narrow_delegation_is_applied_to_runtime_change_set(self):
        record = base_record()
        record["allowed_change_scope"] = ["src/a", "src/b"]
        record = attach_delegated_worker(record, return_fields=["finding"])
        record["delegation_contract"]["inherited_change_scope"] = ["src/a"]
        result = run(record, ROOT, None)
        self.assertEqual(codes(result, "DELEGATION_"), [], result.get("detected"))
        self.assertEqual((result.get("runtime_state") or {}).get("change_set"), ["src/a"])

    def test_delegated_side_effect_obeys_narrowed_authority(self):
        record = base_record()
        record["allowed_change_scope"] = ["src/a", "src/b"]
        record = attach_delegated_worker(record, return_fields=["finding"])
        record["delegation_contract"]["inherited_change_scope"] = ["src/a"]
        record["side_effect_guard"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "effect_id": "child-forbidden",
            "idempotency_key": "child-forbidden",
            "action_payload_hash": "sha256:" + "c" * 64,
            "action_kind": "production_deploy",
            "target_ref": "src/b",
        }
        with mock.patch.object(ro, "guard_side_effect") as guarded:
            result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertIn(
            "SIDE_EFFECT_ACTION_FORBIDDEN_BY_DELEGATED_AUTHORITY",
            result.get("detected", []),
        )
        self.assertIn(
            "SIDE_EFFECT_TARGET_OUTSIDE_DELEGATED_CHANGE_SCOPE",
            result.get("detected", []),
        )
        self.assertFalse(guarded.called)

    def test_narrow_delegation_is_applied_to_task_contract_input(self):
        record = base_record()
        record["allowed_change_scope"] = ["src/a", "src/b"]
        record = attach_delegated_worker(record, return_fields=["finding"])
        record["delegation_contract"]["inherited_change_scope"] = ["src/a"]
        with mock.patch.object(
            ro,
            "build_codex_task_contract",
            return_value={"pass": True, "detected": [], "task_contract": None},
        ) as built:
            result = run(record, ROOT, None)
        self.assertEqual(codes(result, "DELEGATION_"), [], result.get("detected"))
        self.assertEqual(built.call_count, 1)
        effective = built.call_args.args[0]
        self.assertEqual(effective.get("allowed_change_scope"), ["src/a"])
        self.assertEqual(
            (result.get("route") or {}).get("runtime_authority", {}).get("allowed_change_scope"),
            ["src/a"],
        )

    def test_artifact_contract_must_match_current_runtime_task(self):
        record = base_record()
        record["artifact_production"] = True
        record["artifact_contract"] = {"task_id": "OTHER-TASK"}
        result = run(record, ROOT, None)
        self.assertIn("ARTIFACT_CONTRACT_CURRENT_TASK_MISMATCH", result.get("detected", []))

    def test_release_identity_cross_checks_apply_even_when_release_intent_false(self):
        record = base_record()
        record["release_intent"] = False
        record["side_effect_guard"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "effect_id": "deploy-identity",
            "idempotency_key": "idem-deploy-identity",
            "action_payload_hash": "sha256:" + "a" * 64,
            "action_kind": "DEPLOY",
            "target_ref": "production:A",
        }
        record["result_preview_guard"] = {
            "required": True,
            "preview_record": {"synthetic": "preview"},
            "release_request": {
                "task_id": record["task_id"],
                "result_revision_hash": "sha256:" + "1" * 64,
                "preview_receipt_hash": "sha256:" + "2" * 64,
                "release_target": "production:B",
                "release_payload_hash": "sha256:" + "b" * 64,
            },
        }
        with mock.patch.object(
            ro,
            "guard_side_effect",
            return_value={
                "pass": True,
                "detected": [],
                "decision": "ALLOW_FIRST_EXECUTION",
                "claim_path": None,
            },
        ), mock.patch.object(
            ro,
            "validate_preview",
            return_value={
                "pass": True,
                "detected": [],
                "task_id": record["task_id"],
                "preview_required": True,
                "acceptance_result": "PASS",
                "release_eligible": True,
                "result_revision_hash": "sha256:" + "1" * 64,
                "preview_receipt_hash": "sha256:" + "2" * 64,
            },
        ), mock.patch.object(
            ro,
            "validate_release",
            return_value={
                "pass": True,
                "detected": [],
                "release_binding_hash": "sha256:" + "3" * 64,
                "release_binding": {"target": "production:B"},
            },
        ):
            result = run(record, ROOT, None)
        self.assertIn("RESULT_RELEASE_SIDE_EFFECT_PAYLOAD_MISMATCH", result["detected"])
        self.assertIn("RESULT_RELEASE_SIDE_EFFECT_TARGET_MISMATCH", result["detected"])

    def test_side_effect_guard_cannot_reference_other_runtime_task(self):
        record = base_record()
        record["side_effect_guard"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": "OTHER-TASK",
            "effect_id": "deploy-001",
            "idempotency_key": "idem-deploy-001",
            "action_payload_hash": "sha256:" + "a" * 64,
            "action_kind": "DEPLOY",
            "target_ref": "production:site",
        }
        result = run(record, ROOT, None)
        self.assertIn("SIDE_EFFECT_GUARD_CURRENT_TASK_MISMATCH", result.get("detected", []))

    def test_late_validation_failure_does_not_reserve_side_effect_claim(self):
        record = base_record()
        record["side_effect_guard"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "effect_id": "deploy-late-fail",
            "idempotency_key": "idem-late-fail",
            "action_payload_hash": "sha256:" + "a" * 64,
            "action_kind": "DEPLOY",
            "target_ref": "production:site",
        }
        record["behavioral_eval"] = {
            "required": True,
            "observed": "not-an-object",
            "assertions": [{"path": "x", "op": "eq", "expected": 1}],
        }
        with mock.patch.object(
            ro,
            "guard_side_effect",
            return_value={
                "pass": True,
                "detected": [],
                "decision": "ALLOW_FIRST_EXECUTION",
                "claim_path": None,
            },
        ) as guarded:
            result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertIn("BEHAVIORAL_EVAL_OBSERVED_INVALID", result["detected"])
        self.assertEqual(guarded.call_count, 1)
        self.assertIs(guarded.call_args.kwargs.get("reserve"), False)

    def test_failed_late_validation_does_not_persist_approval_checkpoint(self):
        record = base_record()
        record["action_class"] = "HUMAN_APPROVAL"
        record["approval_checkpoint"] = {
            "required": True,
            "namespace": "RUNTIME",
            "atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": {"action": "merge", "target_ref": "commit:abc"},
        }
        record["behavioral_eval"] = {
            "required": True,
            "observed": "not-an-object",
            "assertions": [{"path": "x", "op": "eq", "expected": 1}],
        }
        with mock.patch.object(ro, "persist_checkpoint") as persisted:
            result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertFalse(persisted.called)

    def test_approval_resume_payload_hash_is_bound_before_consumption(self):
        record = base_record()
        action_payload = {"action": "merge", "target_ref": "commit:abc"}
        record["approval_resume"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "expected_checkpoint_hash": "sha256:" + "a" * 64,
            "expected_atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": action_payload,
        }
        record["human_approval_evidence"] = {"decision": "APPROVE"}
        stored_binding = approval_binding_for(record, "MERGE", action_payload)
        stored_binding["action_payload_hash"] = ro._canonical_hash(
            {"action": "merge", "target_ref": "commit:other"}
        )
        with mock.patch.object(
            ro,
            "guard_checkpoint",
            return_value={
                "pass": True,
                "detected": [],
                "checkpoint": {"approval_binding": stored_binding},
            },
        ), mock.patch.object(ro, "consume_approval") as consumed:
            result = run(record, ROOT, None)
        self.assertIn(
            "APPROVAL_RESUME_CURRENT_ACTION_MISMATCH:action_payload_hash",
            result.get("detected", []),
        )
        self.assertFalse(consumed.called)

    def test_successful_approval_resume_emits_approved_action_as_route(self):
        record = base_record()
        action_payload = {"action": "merge", "target_ref": "commit:abc"}
        record["approval_resume"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "expected_checkpoint_hash": "sha256:" + "a" * 64,
            "expected_atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": action_payload,
        }
        record["human_approval_evidence"] = {"decision": "APPROVE"}
        stored_binding = approval_binding_for(record, "MERGE", action_payload)
        with mock.patch.object(
            ro,
            "guard_checkpoint",
            return_value={
                "pass": True,
                "detected": [],
                "checkpoint": {"approval_binding": stored_binding},
            },
        ), mock.patch.object(
            ro,
            "consume_approval",
            return_value={"pass": True, "detected": []},
        ), mock.patch.object(
            ro,
            "build_codex_task_contract",
            return_value={"pass": True, "detected": [], "task_contract": None},
        ):
            result = run(record, ROOT, None)
        self.assertTrue(result["pass"], result.get("detected"))
        action = (result.get("route") or {}).get("authorized_action") or {}
        self.assertEqual(action.get("source"), "APPROVAL_RESUME")
        self.assertEqual(action.get("action_kind"), "MERGE")
        self.assertEqual(action.get("action_payload"), action_payload)
        self.assertEqual(action.get("action_payload_hash"), ro._canonical_hash(action_payload))

    def test_approval_and_side_effect_identity_must_match_before_mutation(self):
        payload = {"action": "merge", "target_ref": "commit:approved-A"}
        for mismatch in ("all", "action_kind", "action_payload_hash", "target_ref", None):
            with self.subTest(mismatch=mismatch):
                record = base_record()
                record["approval_resume"] = {
                    "required": True, "namespace": "RUNTIME", "task_id": record["task_id"],
                    "expected_checkpoint_hash": "sha256:" + "a" * 64,
                    "expected_atomic_unit": "approval-boundary",
                    "action_kind": "MERGE", "action_payload": payload,
                }
                record["human_approval_evidence"] = {"decision": "APPROVE"}
                effect = {
                    "required": True, "namespace": "RUNTIME", "task_id": record["task_id"],
                    "effect_id": "approved-effect", "idempotency_key": "approved-idem",
                    "action_kind": "MERGE", "action_payload_hash": ro._canonical_hash(payload),
                    "target_ref": payload["target_ref"],
                }
                unrelated = {"action_kind": "SEND_MESSAGE", "action_payload_hash": ro._canonical_hash(
                    {"action": "send", "target_ref": "remote:unrelated-B"}), "target_ref": "remote:unrelated-B"}
                if mismatch == "all":
                    effect.update(unrelated)
                elif mismatch:
                    effect[mismatch] = unrelated[mismatch]
                record["side_effect_guard"] = effect
                with mock.patch.object(ro, "guard_checkpoint", return_value={
                    "pass": True, "detected": [], "checkpoint": {
                        "approval_binding": approval_binding_for(record, "MERGE", payload)}
                }), mock.patch.object(ro, "guard_side_effect", return_value={
                    "pass": True, "detected": []
                }) as claimed, mock.patch.object(ro, "consume_approval", return_value={
                    "pass": True, "detected": []
                }) as consumed, mock.patch.object(ro, "build_codex_task_contract", return_value={
                    "pass": True, "detected": [], "task_contract": None
                }):
                    result = run(record, ROOT, None)
                if mismatch:
                    self.assertFalse(result["pass"], result)
                    self.assertTrue(any(x.startswith("APPROVAL_SIDE_EFFECT_IDENTITY_MISMATCH:")
                                        for x in result["detected"]))
                    claimed.assert_not_called()
                    consumed.assert_not_called()
                else:
                    self.assertTrue(result["pass"], result["detected"])
                    self.assertTrue(claimed.call_args.kwargs["reserve"])
                    consumed.assert_called_once()
                    self.assertEqual(result["route"]["authorized_action"]["action_payload"], payload)

    def test_effectful_reference_lane_cannot_run_after_approval_consumption(self):
        record = base_record()
        action_payload = {"action": "merge", "target_ref": "commit:abc"}
        record["approval_resume"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "expected_checkpoint_hash": "sha256:" + "a" * 64,
            "expected_atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": action_payload,
        }
        record["human_approval_evidence"] = {"decision": "APPROVE"}
        record["intent_text"] = "자료 검토"
        record["source_url"] = "https://example.invalid/reference"
        record["reference_acquisition_execute"] = True
        stored_binding = approval_binding_for(record, "MERGE", action_payload)
        with mock.patch.object(
            ro,
            "guard_checkpoint",
            return_value={
                "pass": True,
                "detected": [],
                "checkpoint": {"approval_binding": stored_binding},
            },
        ), mock.patch.object(
            ro,
            "route_reference_intake",
            return_value={"pass": True, "detected": [], "route_type": "REFERENCE_INTAKE_REVIEW"},
        ), mock.patch.object(
            ro,
            "build_codex_task_contract",
            return_value={"pass": True, "detected": [], "task_contract": None},
        ), mock.patch.object(ro, "consume_approval") as consumed, mock.patch.object(
            ro, "acquire_reference"
        ) as acquired:
            result = run(record, ROOT, None)
        self.assertIn(
            "AUTHORIZATION_MUTATION_EFFECTFUL_REFERENCE_NOT_ALLOWED",
            result.get("detected", []),
        )
        self.assertFalse(consumed.called)
        self.assertFalse(acquired.called)

    def test_approval_resume_is_bound_to_current_route(self):
        record = base_record()
        state, failures = ro.derive_runtime_state(record)
        self.assertEqual(failures, [])
        record["approval_resume"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "expected_checkpoint_hash": "sha256:" + "a" * 64,
            "expected_atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": {"action": "merge", "target_ref": "commit:abc"},
        }
        record["human_approval_evidence"] = {"decision": "APPROVE"}
        stored_binding = approval_binding_for(
            record,
            "MERGE",
            record["approval_resume"]["action_payload"],
        )
        stored_binding["next_action"] = "different-next-action"
        stored_binding["runtime_authority_hash"] = ro._canonical_hash(
            {
                key: value
                for key, value in stored_binding.items()
                if key not in {"runtime_authority_hash", "action_kind", "action_payload_hash"}
            }
        )
        with mock.patch.object(
            ro,
            "guard_checkpoint",
            return_value={
                "pass": True,
                "detected": [],
                "checkpoint": {"approval_binding": stored_binding},
            },
        ), mock.patch.object(ro, "consume_approval") as consumed:
            result = run(record, ROOT, None)
        self.assertIn(
            "APPROVAL_RESUME_CURRENT_ROUTE_MISMATCH:next_action",
            result.get("detected", []),
        )
        self.assertFalse(consumed.called)

    def test_late_validation_failure_does_not_consume_valid_approval(self):
        record = base_record()
        state, failures = ro.derive_runtime_state(record)
        self.assertEqual(failures, [])
        action_payload = {"action": "merge", "target_ref": "commit:abc"}
        record["approval_resume"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": record["task_id"],
            "expected_checkpoint_hash": "sha256:" + "a" * 64,
            "expected_atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": action_payload,
        }
        record["human_approval_evidence"] = {"decision": "APPROVE"}
        record["behavioral_eval"] = {
            "required": True,
            "observed": "not-an-object",
            "assertions": [{"path": "x", "op": "eq", "expected": 1}],
        }
        stored_binding = approval_binding_for(record, "MERGE", action_payload)
        with mock.patch.object(
            ro,
            "guard_checkpoint",
            return_value={
                "pass": True,
                "detected": [],
                "checkpoint": {"approval_binding": stored_binding},
            },
        ), mock.patch.object(ro, "consume_approval") as consumed:
            result = run(record, ROOT, None)
        self.assertFalse(result["pass"])
        self.assertIn("BEHAVIORAL_EVAL_OBSERVED_INVALID", result["detected"])
        self.assertFalse(consumed.called)

    def test_untrusted_source_blocks_privileged_action_without_clearance(self):
        record = base_record()
        record["action_class"] = "IMPLEMENTATION_WRITE"
        record["source_trust_class"] = "PUBLIC_WEB"
        result = run(record, ROOT, None)
        self.assertIn(
            "UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE",
            result.get("detected", []),
        )

    def test_manifest_untrusted_source_label_also_requires_quarantine(self):
        record = base_record()
        record["action_class"] = "IMPLEMENTATION_WRITE"
        record["source_trust_class"] = "SOURCE_EXTERNAL_UNTRUSTED_RUNTIME_CONTENT"
        result = run(record, ROOT, None)
        self.assertIn(
            "UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE",
            result.get("detected", []),
        )

    def test_approval_resume_cannot_reference_other_task(self):
        record = base_record()
        record["approval_resume"] = {
            "required": True,
            "namespace": "RUNTIME",
            "task_id": "OTHER-TASK",
            "expected_checkpoint_hash": "sha256:" + "a" * 64,
            "expected_atomic_unit": "approval-boundary",
            "action_kind": "MERGE",
            "action_payload": {"action": "merge", "target_ref": "commit:abc"},
        }
        record["human_approval_evidence"] = {"decision": "APPROVE"}
        result = run(record, ROOT, None)
        self.assertIn("APPROVAL_RESUME_CURRENT_TASK_MISMATCH", result.get("detected", []))

    def test_validator_clearance_removes_quarantine_block(self):
        record = base_record()
        record["action_class"] = "IMPLEMENTATION_WRITE"
        record["source_trust_class"] = "PUBLIC_WEB"
        record["quarantine_clearance"] = {
            "authority": "VALIDATOR",
            "evidence_ref": "INDEX:verified-source-1",
            "verified": True,
        }
        result = run(record, ROOT, None)
        self.assertNotIn(
            "UNTRUSTED_SOURCE_PRIVILEGED_ACTION_QUARANTINE",
            result.get("detected", []),
        )
        quarantine = result.get("source_quarantine") or {}
        self.assertTrue(quarantine.get("cleared"))


if __name__ == "__main__":
    unittest.main()
