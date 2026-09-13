# 2026-09-14 GEMINI + CLAUDE ENFORCEMENT ROUND-2 INTEGRATION

Status: REPOSITORY_CORRECTIONS_APPLIED / CI_PASS / LIVE_RUNTIME_UNVERIFIED

## External findings reconciled

### ADOPT
1. `repo_commit` evidence must prove real git existence and, by default, HEAD ancestry.
2. Historical-failure evidence must prove relevance to canonical `HISTORY/`, not merely present a valid commit SHA.
3. Missing/unknown role, action class, or execution owner must fail closed when pre-execution gating is required.
4. Negative regressions must cover unknown/missing action metadata in addition to the known Ready & Set role-drift case.
5. Review-package integrity mismatch is itself a handoff/evidence failure and must not be hidden by a CI-success claim.

### ADJUST
Gemini suggested automatic evidence-hash synchronization. This is not adopted as an automatic default because blindly rewriting expected hashes to match changed content would defeat tamper/change detection. Hash regeneration is allowed only as an intentional canonical change followed by replay/CI validation.

Gemini also suggested adding a wrapper that calls `preflight_bridge.py` before LLM/API tool execution. A repository-only wrapper that is not actually connected to the hosted ChatGPT/native tool router would reproduce `RULE WRITTEN != RULE ENFORCED`; therefore no fake runtime wrapper is added. The live runtime boundary remains explicit.

Claude correctly separated repository enforcement from live hosted-runtime enforcement and identified the earlier review-bundle fixture mismatch. That mismatch was a packaging error, not a canonical seed mismatch, and is treated as `HANDOFF_LOSS / PACKAGE_INTEGRITY_FAIL` evidence.

## Canonical deltas
- `ENFORCEMENT/evidence_ref_validator.py`
  - real git commit existence check;
  - HEAD-ancestor check by default;
  - canonical-history relevance check for `history_query_refs`;
  - repo commit history refs require `evidence_paths` under `HISTORY/` that exist at that commit.
- `ENFORCEMENT/fixtures/preflight_evidence_pass.json`
  - history commit bound to `HISTORY/2026-09-14_GEMINI_ENFORCEMENT_REVIEW_INTEGRATION.md`.
- `ENFORCEMENT/taky_gate.py`
  - required pre-execution role/action/owner are fail-closed;
  - unknown role/action and disallowed role/action combinations are failures.
- `ENFORCEMENT/evidence_bridge_regression.py`
  - bad repo hash;
  - fake commit;
  - unbound history commit;
  - history path outside canonical history;
  - missing history;
  - orchestrator implementation drift;
  - unknown action;
  - missing role;
  - missing execution owner;
  - validation-only progress drift;
  - runtime-enforcement overclaim.
- `.github/workflows/taky-enforcement.yml`
  - full git history checkout (`fetch-depth: 0`) so commit/ancestor checks are real.
- `HISTORY/FAILURE_LEDGER_2026-09-14_READYSET_ORCHESTRATOR_DRIFT.md`
  - stale pointers to deleted parallel enforcement files removed;
  - current canonical controls and live-runtime boundary recorded.

## Verified repository evidence
Canonical enforcement workflow run `34789249530` for commit `1095190f7bc2cf8e5a0841e3d7954ff524e8514c` completed `success` after the history-relevance and fail-closed regression additions.

## Remaining unresolved boundary
`REPOSITORY_EXECUTABLE + CI_ENFORCED != LIVE_RUNTIME_ENFORCED`.

The repository still cannot prove that hosted ChatGPT invokes `preflight_bridge.py` before every native tool call. Role/action/owner classification also needs a trustworthy upstream source to eliminate semantically wrong but syntactically valid classifications.

Highest truthful state:
`REPOSITORY_EXECUTABLE + CI_ENFORCED / LIVE_RUNTIME_AUTO_INVOCATION_UNVERIFIED`.
