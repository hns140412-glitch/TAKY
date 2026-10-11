# TAKY Beta local code-track evidence — 2026-10-03

Task: `TAKY-BETA-CODE-2026-10-03`. Local changes and validation only; overall suite is **not green** and no TAKY_PASS is claimed.

## Verified ref and scope

Repository: `D:/Git PWA/TAKY`; branch: `character-asset-behavior-separation-2026-09-30`; HEAD: `fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e`.
No commit/ref produced. No branch switch, push, merge, deploy, paid API call, remote-service mutation, or destructive cleanup. CURRENT/MASTER/HANDOFF authority files were not edited. Existing dirty files were preserved; all 851 baseline files were compared by SHA-256, and only the two intended validator files changed. See `scope_verification.json` and `task_contract.json`.

## Fixes and rationale

1. `ENFORCEMENT/evidence_ref_validator.py`: history provenance depended on the textual `HISTORY/` prefix. A correct hash for `HISTORY/../TAKY.md` passed. Resolve repository-file targets and require containment in canonical HISTORY; reject parent traversal in commit evidence paths before git lookup. Existing hash/history checks remain in place.
2. `ENFORCEMENT/execution_checkpoint.py`: the CURRENT guard verified structure/hash/unit but never matched the loaded record's task_id and namespace against the requested identity. A correctly hashed record belonging to another task/owner passed. Bind both fields exactly, including identities that collide after filename slugging.

Regression files added:
- `ENFORCEMENT/evidence_history_boundary_test.py` — 5 tests (including two traversal subcases, valid file/commit controls, and a mocked resolved-link escape).
- `ENFORCEMENT/execution_checkpoint_identity_test.py` — 6 tests (valid identity, wrong task/owner, slug collision, stale unit/hash).

Before edits, these tests demonstrated 7 failing assertions/subcases; after edits, all 11 tests pass. See `regression_before.json`, `history_bypass_before.json`, `checkpoint_bypass_before.json`, and `validation_after.json`. Link behavior is mocked; no OS symlink was created.

## Validation actually run

The complete command argv, stdout, stderr, exit code, and expected exit where applicable are retained in JSON logs beside this report.

- `baseline_results.json`: 133 local commands: 108 exit 0, 25 nonzero. Includes every existing ENFORCEMENT `*_test.py`, four local regression scripts, eight repository lint/validator commands, seven replay sets, Alpha manifest validation, and all 77 BADGE/SHARED/LEARNING `*.test.js` files.
- `python -B ENFORCEMENT/evidence_history_boundary_test.py`: 5 tests pass.
- `python -B ENFORCEMENT/execution_checkpoint_identity_test.py`: 6 tests pass.
- `python -B ENFORCEMENT/execution_state_approval_binding_test.py`: 8 tests pass.
- `python -B ENFORCEMENT/runtime_hardening_integration_test.py`: 6 tests pass (individual gates, not proof the whole live runtime passes).
- `python -B ENFORCEMENT/execution_checkpoint_test.py` and `python -B ENFORCEMENT/approval_checkpoint_resume_test.py`: rerun; remain blocked by temporary-directory access errors.
- `python -B ENFORCEMENT/evidence_bridge_regression.py`: rerun; fails the pre-existing evidence-seed hash.
- `python -B ENFORCEMENT/rule_registry_lint.py`: pass.
- `python -B ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_cases_v5.json` and `.../replay_cases_v6.json`: pass, including external-call/deploy safety replay gates.
- `python -B ENFORCEMENT/alpha_manifest_validator.py HANDOFF/TAKY_ALPHA_LOCAL_MANIFEST_2026-10-03.json`: pass, 32 files, both before and after.
- `python -B ENFORCEMENT/outcome_hook_regression.py` with `PYTHONUTF8=1`: pass; initial failure was under inconsistent parent/child encoding settings. See `outcome_hook_utf8_results.json`.
- `python -B ENFORCEMENT/beta_validation_2026_10_03/integration_probe.py`: pass. Actual local checkpoint persist/readback accepts matching identity and rejects a correctly hashed wrong identity. Preflight accepts a control and rejects history traversal. Only the in-memory control's fixture hash is refreshed to match local bytes; no stored authority/evidence is rewritten.
- Supplemental C2S valid/invalid closure fixtures, review-result missing-evidence fixture, and forbidden CODEX_DONE->MERGED fixture: all five produce expected exits. Handoff bundle pass fixture fails integrity checks. Exact commands and output in `integration_results.json`.
- Python in-memory `compile(source, path, 'exec')` for the two changed validators, two new tests and integration probe: pass. These stdlib Python changes have no separate application build/typecheck configured in the inspected enforcement workflow.
- `git diff --check`: pass. Git emits existing Windows LF/CRLF conversion notices.

## OPEN items and limits

1. Sixteen Python test scripts cannot use/clean their `tempfile.TemporaryDirectory` directories here: `PermissionError` / Windows error 5. Reproduced after pointing TEMP/TMP at a task-owned workspace directory. No ACL change or test weakening was attempted. Their full integration results remain unverified.
2. Seven BADGE scripts fail assertions. Instrumenting the representative calendar test caught `EPERM` at `fs.fsyncSync`; see `badge_diagnostic.json`. A platform durability fallback could change the persistence guarantee, so it was not selected in this code track. The other six failures have not individually been proven to share that cause.
3. Evidence seed fixture expects SHA-256 `d8e0e35dd505bed4ff6cc4fdfe04ba698b840ce2c39aa9c0d75ccad18d11f5c1`; local CRLF bytes hash to `26caecc5a2cef3ba8d27d454fb7086cc4e12e2114fdd51b40998f77e0696398e`. Converting CRLF to LF yields the expected hash. Raw-byte validation correctly rejects the mismatch. No evidence hashes or normalization policy changed.
4. `python -B ENFORCEMENT/handoff_bundle_validator.py ENFORCEMENT/fixtures/handoff_bundle_pass` rejects declared hashes and resume state binding in the checked-out fixture. The expected-positive fixture is not currently valid; authoritative evidence was not regenerated.
5. Runtime/UI/data/asset linkage is covered only by executed local tests, including the passing three-app character runtime and local character asset HTTP tests. No real browser/mobile-device or remote runtime validation was performed. Mobile validation is not required for these Python validator changes.
6. No exhaustive security/bypass closure claim. The new tests are standalone local scripts; CI workflow wiring was not changed. Global runtime/authority consolidation and production approval remain outside this task.

Baseline failures:

| Command (Python/Node interpreter omitted) | Finding |
| --- | --- |
| `ENFORCEMENT/approval_checkpoint_resume_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/architecture_competition_output_pipeline_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/architecture_competition_visual_quality_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/cross_engine_growth_e2e_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/data_index_local_query_provider_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/data_index_search_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/data_index_vector_materialization_validate_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/data_index_vector_search_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/execution_checkpoint_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/learning_evidence_gap_broker_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/local_drive_workspace_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/mining_verified_archive_manifest_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/producer_artifact_gate_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/reference_acquisition_adapter_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/reference_index_owner_receipt_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/reference_intake_executor_test.py` | Temporary-directory access denied |
| `ENFORCEMENT/outcome_hook_regression.py` | Resolved with PYTHONUTF8=1; no code edit |
| `ENFORCEMENT/evidence_bridge_regression.py` | CRLF/LF evidence seed mismatch |
| `BADGE/badge-award-calendar.test.js` | Badge assertion failure; representative fsync EPERM reproduced |
| `BADGE/badge-award-ledger-store.test.js` | Badge assertion failure; representative fsync EPERM reproduced |
| `BADGE/badge-family-gift-calendar.test.js` | Badge assertion failure; representative fsync EPERM reproduced |
| `BADGE/badge-family-read-access.test.js` | Badge assertion failure; representative fsync EPERM reproduced |
| `BADGE/badge-ledger-visual-binding.test.js` | Badge assertion failure; representative fsync EPERM reproduced |
| `BADGE/family-praise-gift.test.js` | Badge assertion failure; representative fsync EPERM reproduced |
| `BADGE/parent-praise-gift-journal.test.js` | Badge assertion failure; representative fsync EPERM reproduced |

## Artifacts and next transition

Changed/added implementation and regression files are the four ENFORCEMENT paths above. All other task additions are under `ENFORCEMENT/beta_validation_2026_10_03/`: this report, task contract, SHA-256 snapshot/scope result, command/result logs, reproducible `integration_probe.py`, and task-owned local probe/temp files. Temporary artifacts are retained per the no-destructive-cleanup instruction. `checkpoint_probe/CURRENT` is isolated test data, not repository CURRENT authority.

Scope deviations: none in production code. Additional local evidence files support review and are explicitly non-authoritative. Full-suite validation remains OPEN as detailed above.

Requested next transition: TAKY review of the local diff and OPEN findings; no lifecycle state file was mutated, no TAKY_PASS, MERGED or DEPLOYED claim, and no merge/deployment approval requested.
