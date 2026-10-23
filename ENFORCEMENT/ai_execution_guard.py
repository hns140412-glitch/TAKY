#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from pathlib import Path
import hashlib
import json
from urllib.parse import urlsplit

FAIL = {
    "ADOPTION": "AI_ADOPTION_GATE_MISSING",
    "SUCCESS": "AI_OBSERVABLE_SUCCESS_EVIDENCE_MISSING",
    "COST": "AI_COST_GUARD_MISSING",
    "REVIEW": "AI_REVIEW_PASS_UNJUSTIFIED",
    "COMPUTER": "AI_COMPUTER_USE_GUARD_MISSING",
    "UI": "AI_UI_COMPLETION_EVIDENCE_MISSING",
}

def _nonempty(v: object) -> bool:
    return isinstance(v, str) and bool(v.strip())

def _refs(v: object) -> bool:
    return isinstance(v, list) and any(isinstance(x, str) and x.strip() for x in v)

def _pos_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0

def _number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0

def _verified_local_artifact(value: object) -> bool:
    """Read and hash evidence bytes; a filename or claimed PASS is not proof."""
    if not isinstance(value, dict):
        return False
    location = value.get("path")
    expected = value.get("sha256")
    if not _nonempty(location) or not isinstance(expected, str):
        return False
    digest = expected.strip().lower()
    if len(digest) != 64 or any(x not in "0123456789abcdef" for x in digest):
        return False
    try:
        target = Path(location)
        if not target.is_file():
            return False
        actual = hashlib.sha256()
        with target.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                actual.update(chunk)
        return actual.hexdigest() == digest
    except (OSError, ValueError, TypeError):
        return False


_APPROVAL_INDEX = (
    Path(__file__).resolve().parents[2]
    / "TAKY_AI_WORKBENCH" / "00_CONTROL"
    / "TAKY_VISUAL_APPROVAL_REFERENCE_INDEX.json"
)

def _valid_image_artifact(ref: object) -> bool:
    if not _verified_local_artifact(ref):
        return False
    path = Path(ref["path"])
    try:
        from PIL import Image
        if path.stat().st_size > 32 * 1024 * 1024:
            return False
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            return False
        with Image.open(path) as img:
            width, height = img.size
            if not 0 < width <= 16384 or not 0 < height <= 16384:
                return False
            if width * height > 32 * 1024 * 1024:
                return False
            img.verify()
        # verify() checks file structure; load() checks actual pixel decodability.
        with Image.open(path) as img:
            img.load()
        return True
    except Exception:
        # Fail closed on corrupt images, decoder errors and decompression bombs.
        return False


def _pixel_fidelity_verified(reference: object, rendered: object, viewport: dict) -> bool:
    """Bounded pixel comparison. Prevent self-reported visual PASS on divergent images.

    Pixel tolerances are intentionally conservative and cannot be overridden by
    the submitted report. A real browser run still requires separate attestation.
    """
    if not (_valid_image_artifact(reference) and _valid_image_artifact(rendered)):
        return False
    try:
        from PIL import Image, ImageChops
        approved = Path(reference["path"])
        observed = Path(rendered["path"])
        with Image.open(approved) as src, Image.open(observed) as dst:
            if (src.size != dst.size
                or src.size != (viewport["width"], viewport["height"])
                or src.width * src.height > 8_000_000):
                return False
            # Flatten transparent assets on the same neutral canvas.
            def flatten(img):
                rgba = img.convert("RGBA")
                return Image.alpha_composite(
                    Image.new("RGBA", img.size, (255, 255, 255, 255)), rgba
                ).convert("RGB")
            diff = ImageChops.difference(flatten(src), flatten(dst))
            red, green, blue = diff.split()
            maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
            hist = maximum.histogram()
            pixels = src.width * src.height
            changed_fraction = sum(hist[24:]) / pixels
            mean_normalized_error = (
                sum((channel_bin % 256) * count for channel_bin, count in enumerate(diff.histogram()))
                / (pixels * 3 * 255)
            )
            return changed_fraction <= 0.03 and mean_normalized_error <= 0.01
    except Exception:
        return False


def _json_evidence(ref: object) -> dict[str, Any] | None:
    if not _verified_local_artifact(ref):
        return None
    path = Path(ref["path"])
    try:
        if path.suffix.lower() != ".json" or path.stat().st_size > 2 * 1024 * 1024:
            return None
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except (OSError, UnicodeError, ValueError, TypeError):
        return None


def _official_visual_approval(visual_id: str, digest: str) -> bool:
    # Provenance-only references are not approved production masters.
    try:
        index = json.loads(_APPROVAL_INDEX.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeError):
        return False
    if not isinstance(index, dict):
        return False
    for x in index.get("provenance_only", []):
        if not isinstance(x, dict):
            continue
        if x.get("visual_id") != visual_id or x.get("source_sha256") != digest:
            continue
        if (x.get("allowed_to_promote_current") is True
            and x.get("current_hns_master_binding") == "VERIFIED"
            and x.get("actual_app_runtime_binding") == "VERIFIED"):
            return True
    return False


def _report_assertions_pass(report: object, schema: str, key: tuple[str, str, str],
                            required_checks: set[str] | None = None) -> bool:
    if not isinstance(report, dict) or report.get("schema") != schema:
        return False
    if (report.get("work_id"), report.get("screen_id"), report.get("run_id")) != key:
        return False
    if report.get("status") != "PASS":
        return False
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        return False
    names = set()
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("name"), str):
            return False
        if (check.get("status") != "PASS" or not _nonempty(check.get("expected"))
            or not _nonempty(check.get("observed"))):
            return False
        names.add(check["name"])
    return required_checks is None or required_checks.issubset(names)


def _browser_runtime_receipt_verified(evidence: dict[str, Any]) -> bool:
    """Independent readback of browser capture receipt (not a cryptographic attestation)."""
    ref = evidence.get("browser_runtime_receipt")
    receipt = _json_evidence(ref)
    if not receipt or receipt.get("schema") not in {
        "TAKY_UI_BROWSER_RUNTIME_RECEIPT_V1",
        "TAKY_UI_BROWSER_RUNTIME_RECEIPT_V2",
    }:
        return False
    if receipt.get("status") != "SCREENSHOT_CAPTURED_NOT_VISUAL_PASS":
        return False
    if receipt.get("target_kind") != "LOOPBACK_APP":
        # Synthetic fixture proves runner operation, never production UI delivery.
        return False
    try:
        config_path = Path(receipt.get("config_path", ""))
        if not config_path.is_file() or config_path.stat().st_size > 64_000:
            return False
        config_bytes = config_path.read_bytes()
        if hashlib.sha256(config_bytes).hexdigest() != receipt.get("config_sha256"):
            return False
        config = json.loads(config_bytes)
        target = urlsplit(config["url"])
        if (target.scheme != "http"
            or target.hostname not in ("127.0.0.1", "localhost", "::1")
            or target.username or target.password):
            return False
        if config.get("viewport") != evidence.get("viewport"):
            return False
        if any(config.get(k) != evidence.get(k) for k in ("work_id", "screen_id", "run_id")):
            return False
        expected_steps = config.get("steps", [])
        actual_steps = receipt.get("steps", [])
        if not isinstance(expected_steps, list) or not expected_steps or len(expected_steps) != len(actual_steps):
            return False
        if any(a.get("action") != b.get("action") or a.get("selector") != b.get("selector")
               for a,b in zip(expected_steps, actual_steps)):
            return False
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return False
    if any(receipt.get(k) != evidence.get(k) for k in ("work_id", "screen_id", "run_id")):
        return False
    viewport = evidence.get("viewport")
    if receipt.get("viewport") != viewport:
        return False
    observed = receipt.get("observed")
    if not isinstance(observed, dict) or any(observed.get(x) != viewport.get(x) for x in ("width", "height")):
        return False
    if receipt.get("browser_channel") not in ("chrome", "msedge"):
        return False
    if receipt.get("release_approved") is not False or receipt.get("is_approved_design") is not False:
        return False
    shots = receipt.get("rendered_screenshot")
    reported_shot = evidence.get("visual", {}).get("rendered_screenshot")
    if not isinstance(shots, dict) or not isinstance(reported_shot, dict):
        return False
    if (shots.get("sha256") != reported_shot.get("sha256")
        or str(shots.get("path", "")).lower() != str(reported_shot.get("path", "")).lower()):
        return False
    if not _verified_local_artifact(shots):
        return False
    accessibility = receipt.get("accessibility_snapshot")
    if (not isinstance(accessibility, dict)
        or accessibility.get("truncated") is not False
        or not _verified_local_artifact(accessibility)):
        return False
    try:
        snapshot_path = Path(accessibility["path"])
        if (snapshot_path.suffix.lower() != ".txt"
            or snapshot_path.stat().st_size > 128_000):
            return False
        snapshot_text = snapshot_path.read_text(encoding="utf-8")
        if not snapshot_text.strip():
            return False
        for expected_step, observed_step in zip(expected_steps, actual_steps):
            action = expected_step.get("action")
            if receipt["schema"] == "TAKY_UI_BROWSER_RUNTIME_RECEIPT_V2":
                if action == "expectText" and (
                    observed_step.get("expected_text") != expected_step.get("value")
                    or observed_step.get("observed_text") != expected_step.get("value")
                ):
                    return False
                if action == "expectVisible" and observed_step.get("observed_visibility") != "visible":
                    return False
            elif action == "expectText" and expected_step.get("value") not in snapshot_text:
                # Historical V1 receipts lack per-step text observations.
                return False
    except (OSError, UnicodeError, KeyError, TypeError, ValueError):
        return False
    steps = receipt.get("steps")
    if (not isinstance(steps, list) or not steps
        or any(not isinstance(x, dict) or x.get("status") != "PASS" for x in steps)
        or receipt.get("page_errors") != []):
        return False
    return True


def _ui_completion_verified(record: dict[str, Any]) -> bool:
    evidence = record.get("ui_completion_evidence")
    if not isinstance(evidence, dict):
        return False
    viewport = evidence.get("viewport")
    if not isinstance(viewport, dict) or any(
        not _pos_int(viewport.get(name)) for name in ("width", "height")
    ):
        return False
    reference = evidence.get("reference")
    if not isinstance(reference, dict) or not _nonempty(reference.get("approved_id")):
        return False
    visual = evidence.get("visual")
    if not isinstance(visual, dict):
        return False
    if any(visual.get(flag) is not True for flag in (
        "passed", "layout_compared", "color_compared", "approved_assets_compared"
    )):
        return False
    required = [
        reference.get("reference_file"), reference.get("approval_record"),
        visual.get("rendered_screenshot"), visual.get("comparison_report"),
        evidence.get("interaction_report"), evidence.get("data_binding_report"),
        evidence.get("regression_report"), evidence.get("intent_acceptance_report"),
        evidence.get("browser_runtime_receipt"),
    ]
    # A single generic PASS log cannot masquerade as independent evidence.
    paths = [str(x.get("path", "")).lower() for x in required if isinstance(x, dict)]
    if len(paths) != len(required) or len(set(paths)) != len(required):
        return False
    if not all(_verified_local_artifact(x) for x in required):
        return False
    if any(evidence.get(name) is not True for name in (
        "interaction_passed", "data_binding_passed",
        "regression_passed", "intent_acceptance_passed"
    )):
        return False
    if not _pixel_fidelity_verified(
        reference.get("reference_file"), visual.get("rendered_screenshot"), viewport
    ):
        return False
    if not _browser_runtime_receipt_verified(evidence):
        return False
    work_id = evidence.get("work_id")
    screen_id = evidence.get("screen_id")
    run_id = evidence.get("run_id")
    if not all(_nonempty(v) for v in (work_id, screen_id, run_id)):
        return False
    key = (work_id, screen_id, run_id)
    approval = _json_evidence(reference.get("approval_record"))
    original_digest = reference["reference_file"]["sha256"]
    if not approval or any((
        approval.get("approval_state") != "APPROVED",
        approval.get("visual_id") != reference.get("approved_id"),
        approval.get("source_sha256") != original_digest,
        approval.get("screen_id") != screen_id,
    )):
        return False
    if not _official_visual_approval(reference["approved_id"], original_digest):
        return False
    specs = [
        (visual.get("comparison_report"), "TAKY_UI_VISUAL_COMPARE_V1",
         {"layout", "color", "approved_assets"}),
        (evidence.get("interaction_report"), "TAKY_UI_INTERACTION_TEST_V1",
         {"user_interaction"}),
        (evidence.get("data_binding_report"), "TAKY_UI_DATA_BINDING_TEST_V1",
         {"data_consumption"}),
        (evidence.get("regression_report"), "TAKY_UI_REGRESSION_TEST_V1",
         {"existing_behavior"}),
        (evidence.get("intent_acceptance_report"), "TAKY_UI_INTENT_ACCEPTANCE_V1",
         {"user_intent"}),
    ]
    for item, schema, required_checks in specs:
        report = _json_evidence(item)
        if not _report_assertions_pass(report, schema, key, required_checks):
            return False
        if schema == "TAKY_UI_VISUAL_COMPARE_V1":
            if (report.get("reference_sha256") != original_digest
                or report.get("rendered_sha256") != visual["rendered_screenshot"]["sha256"]
                or report.get("tool") != "PLAYWRIGHT"):
                return False
    return True


def validate_ai_execution(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    # Learning: NECESSITY-BEFORE-ADOPTION + CAPABILITY-GAP-BEFORE-TOOL +
    # SECURITY-BEFORE-CREDENTIAL + SUPPLY-CHAIN-IDENTITY-CHECK +
    # CONNECTOR-PERMISSION-BOUNDARY + SENSITIVE-AGENT-ISOLATION.
    if record.get("ai_tool_or_connector_adoption_planned") is True:
        a = record.get("ai_adoption_assessment")
        if not isinstance(a, dict):
            failures.append(FAIL["ADOPTION"])
        else:
            required_true = [
                "overlap_checked",
                "cost_checked",
                "security_checked",
                "upstream_identity_verified",
            ]
            if not _nonempty(a.get("capability_gap")):
                failures.append(FAIL["ADOPTION"])
            if any(a.get(k) is not True for k in required_true):
                failures.append(FAIL["ADOPTION"])
            if a.get("credentials_or_private_access_involved") is True:
                if (
                    a.get("credential_scope_defined") is not True
                    or a.get("permission_boundary_defined") is not True
                    or a.get("isolated_test_planned") is not True
                ):
                    failures.append(FAIL["ADOPTION"])

    # Learning: OBSERVABLE-SUCCESS-CRITERIA + SELF-REPORT-NOT-RUNTIME-PROOF +
    # DEVICE-OBSERVATION-BEFORE-CLOSE.
    if record.get("ai_success_claimed") is True:
        if not _refs(record.get("observable_success_evidence_refs")):
            failures.append(FAIL["SUCCESS"])
        if (
            record.get("device_or_ui_observation_required") is True
            and not _refs(record.get("device_or_ui_observation_refs"))
        ):
            failures.append(FAIL["SUCCESS"])

    # GPT-approved reference -> Claude implementation -> actual visual/functional
    # evidence. Does not decide pixel-fidelity itself: it prevents ungrounded DONE.
    ui_delivery = str(record.get("deliverable_type") or record.get("artifact_kind") or "").strip().upper()
    terminal_states = {"DONE", "COMPLETE", "COMPLETED", "PASS", "PASSED", "PROMOTED"}
    status = str(record.get("status") or "").strip().upper()
    result = str(record.get("result_state") or "").strip().upper()
    ui_done = record.get("ui_implementation_done_claimed") is True or (
        ui_delivery in {"UI", "UI_SCREEN", "UI_IMPLEMENTATION"}
        and (status in terminal_states or result in terminal_states)
    )
    if ui_delivery in {"UI", "UI_SCREEN", "UI_IMPLEMENTATION"}:
        if status and result and ((status in terminal_states) != (result in terminal_states)):
            failures.append(FAIL["UI"])
    if ui_done:
        if not _ui_completion_verified(record):
            failures.append(FAIL["UI"])

    # Learning: COST-GUARD-AS-CODE. This complements, rather than replaces,
    # the existing external call budget gate.
    if record.get("ai_autonomous_cost_exposure") is True:
        c = record.get("ai_cost_guard")
        if not isinstance(c, dict):
            failures.append(FAIL["COST"])
        else:
            if not _number(c.get("cost_ceiling")):
                failures.append(FAIL["COST"])
            if not _pos_int(c.get("iteration_limit")):
                failures.append(FAIL["COST"])
            if not _nonempty(c.get("stop_condition")):
                failures.append(FAIL["COST"])
            if c.get("approval_required_before_exceeding") is not True:
                failures.append(FAIL["COST"])

    # Learning: REVIEW-BUDGET-DOES-NOT-FORCE-PASS.
    if record.get("ai_review_loop") is True:
        unresolved = record.get("review_unresolved_material_issues") is True
        exhausted = record.get("review_round_limit_reached") is True
        decision = str(record.get("review_decision") or "").strip().upper()
        if unresolved and exhausted and decision in {"PASS", "APPROVE", "COMPLETE"}:
            failures.append(FAIL["REVIEW"])

    # Learning: SAFE-COMPUTER-USE-SEQUENCE + METADATA-FIRST-FILE-DIAGNOSIS.
    if record.get("ai_computer_use_action") is True:
        c = record.get("ai_computer_use_guard")
        if not isinstance(c, dict):
            failures.append(FAIL["COMPUTER"])
        else:
            required_true = [
                "read_only_diagnosis_completed",
                "change_plan_defined",
                "bounded_execution_defined",
                "observable_verification_defined",
                "rollback_or_recovery_defined",
            ]
            if any(c.get(k) is not True for k in required_true):
                failures.append(FAIL["COMPUTER"])
            if c.get("content_inspection_needed") is not True and c.get("metadata_first_used") is not True:
                failures.append(FAIL["COMPUTER"])
            if (
                c.get("sensitive_or_destructive_action") is True
                and c.get("explicit_approval_bound") is not True
            ):
                failures.append(FAIL["COMPUTER"])

    return list(dict.fromkeys(failures))
