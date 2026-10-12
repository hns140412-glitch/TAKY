# ACTIVE_RULE_PROFILE owner-to-projection review — 2026-10-12

Receipt: `HISTORY/PROJECTION_ATTESTATIONS/ACTIVE_RULE_PROFILE_1b9896e9633965a88c8ebe3c4f77e25d591e26a2c66ffad0a60498ca2d523b21.json`
Supersedes: `ACTIVE_RULE_PROFILE_b8e64013393e21aff6efb43d0f56fbecd3b18fa6d5d2462651f953fc2123d3fa.json` (reviewed 2026-10-04T16:17:45+09:00, worktree-derived on fee09fa8).
Reviewer role: TAKY_VALIDATOR, executed by Claude Code under the USER instruction of 2026-10-12 to fix the four failing TAKY tests (ROLE != AGENT). No independent second-model review has been performed on this attestation.
Source: COMMITTED_SNAPSHOT at `6a25b468b2d8b8b058fe6f3ec0a2c925dc679ad8`. All owner files are clean at that HEAD.

## Trigger
`active_rule_profile_freshness_validator_test.test_current_repository_profile_passes` failed with
`OWNER_FINGERPRINT_STALE / SOURCE_ATTESTATION_MISMATCH / REVIEW_ATTESTATION_OWNER_MISMATCH`.

## Owner delta since the prior attestation
Owner files modified after 2026-10-04T16:17 (mtime):
- `MASTER/AI_COLLABORATION_PROTOCOL.md` (TKY-AICOLLAB-001 role matrix, routing, Codex minimum-use gate).
  Profile §11 and the bootstrap already activate it by reference only, which satisfies its §1.2 (projections may activate, not redefine). No conflict.
- `TAKY.md`: SAVEY/connection boundary pointers (already projected in §11/§17), the review-default mining route (orchestrator intent routing, not delegated-executor guidance), and the `로그` shortcut (already in the bootstrap). No conflict.
- `MASTER/RULE_REGISTRY.json` (semantic part, `projection_bindings` excluded): new owners registered, including
  **TKY-SAFEEXEC-001** (`MASTER/SAFE_TOOL_EXECUTION_PROTOCOL.md`, pre-tool execution safety). This is always-on guidance for delegated executors and was missing from the profile.

The remaining owner deltas against fee09fa8 (delegation inheritance, side-effect ledger, preview/release binding, attestation gate) predate the prior attestation. They are already projected in §16–§18.

## Projection change
- §11: added activation-only reference `MASTER/SAFE_TOOL_EXECUTION_PROTOCOL.md (TKY-SAFEEXEC-001) before tool execution`. No semantics were restated.
- `SOURCE_OWNER_PATHS`: added `MASTER/SAFE_TOOL_EXECUTION_PROTOCOL.md`, so a later SAFEEXEC change invalidates this attestation.
- Header: `PROFILE_VERSION 2026-10-12.1`, `SOURCE_STATE COMMITTED_SNAPSHOT`, `SOURCE_CANONICAL_HEAD`, `SOURCE_OWNER_FINGERPRINT` and `GENERATED_AT` were refreshed together with the new receipt and the registry binding.

## Result
PASS: `active_rule_profile_freshness_validator.validate` passes on the current repository, and the validator test suite passes 10/10.

## Open risk
The owner fingerprint hashes raw worktree bytes. With `core.autocrlf=true`, a checkout using different line endings yields a different fingerprint. This is pre-existing and was not changed here.
