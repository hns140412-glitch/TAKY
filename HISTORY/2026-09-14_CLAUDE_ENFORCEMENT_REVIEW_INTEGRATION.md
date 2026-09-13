# 2026-09-14 Claude Enforcement Review Integration

Status: REVIEW_REQUIRED / PARTIALLY CORRECTED

## External review disposition
Claude independently converged with Gemini on three material concerns: live runtime auto-invocation is unverified; evidence references can become self-report if their targets/integrity are not checked; validation-only progress controls must be tied to an actual consuming path rather than narrative claims.

Claude also repeated two findings that were based on the earlier V1 package rather than the current canonical V2 state: the removed parallel `preflight_gate.py/execution_policy.json` path and an orphan-protocol assumption. Current canonical boot in `TAKY.md` explicitly loads `MASTER/ENFORCEMENT_PROTOCOL.md`, and `MASTER/RULE_REGISTRY.json` assigns `TKY-ENFORCEMENT-001` to that file. Therefore the orphan finding is ADJUST, not blindly adopted.

## Adopted corrections
1. Added `ENFORCEMENT/evidence_ref_validator.py`.
2. Added `ENFORCEMENT/preflight_bridge.py` as the repository-level bridge that combines structured evidence integrity validation with the existing `taky_gate.py`.
3. Added a positive evidence fixture and regression that rejects wrong repo hashes, missing history evidence, orchestrator implementation drift, validation-as-product-progress, and runtime-enforcement overclaims.
4. Integrated those checks into the existing canonical `.github/workflows/taky-enforcement.yml`; no parallel workflow/semantic owner is introduced.

## Evidence semantics
Repository-file evidence must name a real path and SHA-256 matching checked-out bytes. Repository commits require a commit-shaped immutable identifier. External/session evidence requires a stable source identifier plus captured time and either digest or immutable revision metadata. This materially raises the bar above boolean/self-report, but does not make external evidence independently re-fetched or cryptographically trusted by the repository gate.

## Remaining unresolved boundary
`REPOSITORY_EXECUTABLE + CI_ENFORCED` remains the highest supported enforcement claim.

Hosted ChatGPT native tool routing is not proven to invoke `ENFORCEMENT/preflight_bridge.py` before every tool call. Therefore:
- `LIVE_RUNTIME_ENFORCED` = UNVERIFIED
- `HOSTED_CHATGPT_FAIL_CLOSED` = UNVERIFIED
- `AUTO_INVOKED_BEFORE_EVERY_TOOL_CALL` = UNVERIFIED

This is not to be hidden by prose, CI success, or replay success.

## History feedback-loop state
FAILURE -> LEDGER -> ROOT_CAUSE -> CONTROL_DELTA -> REGRESSION -> REPOSITORY PRE-FLIGHT BRIDGE is now evidenced inside the canonical repository.

The final arrow `REPOSITORY PRE-FLIGHT BRIDGE -> HOSTED CHATGPT TOOL EXECUTION INTERCEPT` remains open/unverified. Do not claim recurrence-prevention PASS for the hosted runtime until an actual platform/runtime hook or equivalent externally evidenced intercept exists.

## Next governance consequence
For current ChatGPT conversations, TAKY must treat the canonical enforcement repository as an authoritative audit/decision-control source but must not misrepresent it as a native platform interceptor. Runtime drift discovered in conversation remains a governance regression and must be recorded/replayed, while the platform-hook gap stays explicit.
