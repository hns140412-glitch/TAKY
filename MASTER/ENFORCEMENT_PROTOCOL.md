# TAKY ENFORCEMENT / REPLAY PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Role: Convert material TAKY prose rules into executable or auditable gates and prevent `RULE WRITTEN ≠ RULE ENFORCED` recurrence.
Normative taxonomy: `MASTER/FAILURE_TAXONOMY.md`.
Executable reference implementation: `ENFORCEMENT/taky_gate.py`.
Representative cases: `ENFORCEMENT/replay_cases.json`.

## 0. Core rule — HARD LOCK

`RULE WRITTEN ≠ RULE ENFORCED`.
`FIXTURE DESCRIBED ≠ FIXTURE REPLAYED`.
`CHECKSUM MATCH ≠ EXTERNAL SOURCE VERIFIED`.
`PACKAGE OPENS ≠ HANDOFF RECOVERABLE`.
`HUMAN APPROVAL REQUIRED ≠ HUMAN APPROVAL ASSUMED`.

A material rule that is mechanically checkable or replayable SHALL have a concrete enforcement expression when technically feasible.

Concrete enforcement expressions include:
- deterministic pre-response/pre-execution assertions;
- schema/contract validation;
- replay fixtures with expected outcomes;
- CI/release blocking;
- post-write readback and compare;
- explicit human approval records for genuinely human-governed transitions.

If no executable enforcement exists for a material mechanically-checkable rule, status is `ENFORCEMENT_MISSING`; prose existence alone SHALL NOT be described as recurrence-prevention PASS.

## 1. Pre-response negative-existence gate — HARD LOCK

Before a material claim equivalent to “없다 / 말한 적 없다 / 규칙이 없다 / 자료가 없다 / 확인되지 않는다” that would affect recovery, deletion, HOLD, supersession, implementation, or user effort, the response contract SHALL contain evidence sufficient for the gate to decide whether the claim is allowed.

Minimum mechanically-auditable fields when applicable:
- `negative_existence_claim`;
- `recovery_paths_checked`;
- `material_alternate_path_available`;
- `source_found_after_claim`;
- `source_recoverable_by_taky`;
- `user_had_to_recover`.

Hard behavior:
- material alternate recovery path remains + only one/single-path miss ⇒ negative-existence claim blocked;
- source later found after premature absence claim ⇒ `FALSE_MISSING_DECLARATION`;
- user had to recover evidence TAKY could materially recover ⇒ `USER_FORCED_RECOVERY` + normally `USER_AS_QA`;
- genuinely inaccessible after applicable paths ⇒ `TRUE_UNAVAILABLE / UNVERIFIED_SOURCE_COVERAGE`, not “never existed”.

The executable gate SHALL fail closed when required recovery evidence fields are absent for a material negative-existence claim.

## 2. Maximum/full handoff portability gate — HARD LOCK

When the user requests `최대한 / 모두 / 전체 / 원문 / 최대 / full / maximum` handoff/transfer and the recipient may lack repository access, the package SHALL be independently recoverable without silently relying on inaccessible repository pointers.

Required machine-auditable fields when applicable:
- `handoff_requested_maximum`;
- `recipient_repo_access`;
- `portable_source_snapshots`;
- `portable_diff_with_base`;
- `repo_pointers_only`;
- `source_manifest_present`;
- `evidence_authority_classified`;
- `resume_simulation_passed`;
- `claims_complete`.

Hard behavior:
- recipient has no repo access + only SHA/blob pointers ⇒ `HANDOFF_LOSS / FAIL`;
- recipient has no repo access + neither full source snapshot nor reconstructable diff+base ⇒ `HANDOFF_LOSS / FAIL`;
- maximum/full requested + material accessible sources not inventoried/classified ⇒ `SCOPE_SHRINKAGE / PREMATURE_PASS` if called complete;
- CURRENT / HISTORICAL / SUPERSEDED / CONFLICT / PROCESS evidence mixed without classification ⇒ NOT PASS;
- package checksum may prove package internal integrity only; it SHALL NOT be used as proof that referenced live repository HEAD/blob state was independently verified.

Allowed verification labels:
- `SNAPSHOT_VERIFIED`;
- `LIVE_HEAD_VERIFIED`;
- `LIVE_HEAD_UNVERIFIED`.

## 3. Replay gate — HARD LOCK

A correction that claims recurrence prevention for an applicable F-01~F-06 class SHALL run a representative replay or equivalent deterministic check before recurrence-prevention PASS.

Required sequence:
`HISTORICAL FAILURE INPUT/STATE → CURRENT GATE → EXPECTED BLOCK/CLASSIFICATION → POST-FIX COMPLIANT INPUT/STATE → EXPECTED PASS → RECORDED LOG`.

A prose fixture without an executed replay is `REPLAY_NOT_PERFORMED`.

The canonical executable fixture set lives in `ENFORCEMENT/replay_cases.json` and is exercised by `ENFORCEMENT/taky_gate.py --replay ...`.

## 4. Rule-application gate — HARD LOCK

If an applicable rule was loaded/cited/known and the actual result violates it, classify `RULE_NOT_APPLIED` regardless of how accurately the rule was quoted.

`RULE CITED + RESULT VIOLATES RULE = FAIL`.

A completion claim is blocked when:
- `rule_cited = true` and `rule_violated = true`;
- or any other hard enforcement violation remains unresolved.

## 4.1 Delegated-continuation / premature-stop gate — HARD LOCK

When the user explicitly delegates continued execution with wording equivalent to `확인이 필요할 때까지 진행`, `계속 진행`, `멈추지 마`, `알아서 진행`, `ㄱ`, or another context-grounded continue instruction, TAKY SHALL continue through authorized executable next actions until a real blocker, required human-only decision, safety/permission boundary, or requested completion condition is reached.

Minimum machine-auditable fields when applicable:
- `delegated_continuation`;
- `authorized_next_action_available`;
- `real_blocker_present`;
- `human_confirmation_required_now`;
- `stopped_before_blocker`.

If continuation was delegated, an authorized next action existed, no real blocker/human decision was due, and execution stopped anyway, classify `PREMATURE_STOP / FAIL`.

Status narration, another plan, or a request that the user perform avoidable debugging SHALL NOT be treated as a valid blocker.

`CONTINUE UNTIL BLOCKER ≠ STOP AFTER EACH SUBSTEP`.
`PROGRESS UPDATE ≠ EXECUTION STOP`.

## 4.2 Result-not-narration gate — HARD LOCK

When the user requests a concrete artifact/action/result and the system has authority/capability to produce it, explanation or intention text alone is not the requested result.

Minimum machine-auditable fields when applicable:
- `artifact_or_action_required`;
- `artifact_or_action_delivered`;
- `explanation_only`;
- `authorized_action_available`.

If a concrete result was required, the authorized result could be produced, and the response stopped at explanation/plan without delivery, classify at least `SUBSTITUTE_RESULT`; add `OUTPUT_FORM_MISMATCH` when the requested result form was not supplied, and `PREMATURE_STOP` when delegated continuation was also active.

`I WILL DO IT ≠ DONE`.
`PLAN FOR RESULT ≠ RESULT`.

## 5. Human-approval gate — HARD LOCK

For promotions/actions whose governance requires human approval, the transition SHALL carry a recoverable approval record/token.

Minimum fields when applicable:
- `human_approval_required`;
- `human_approval_present`;
- `approval_scope`.

If approval is required and not present, classify `HUMAN_APPROVAL_MISSING / FAIL` for that transition.

Names such as “Prime Agent”, “continual harness”, “lesson evolution”, “AI approval”, or “validated” SHALL NOT substitute for human approval.

## 6. State/history claim consistency gate — HARD LOCK

Narrative result/history wording SHALL NOT claim a higher state than the governing machine/state manifest supports.

Minimum fields when applicable:
- `claims_complete`;
- `external_validation_state`;
- `state_manifest_consistent`.

If external validation remains `PENDING` or another material gate is not complete, wording may state completed local/canonical deltas but SHALL NOT present the entire validation program as unqualified complete.

Mismatch ⇒ `STATE_CLAIM_MISMATCH` and, when completion was claimed, `PREMATURE_PASS`.

## 7. Full-source/diff portability rule — HARD LOCK

For an offline/isolated review package that cites canonical files, use one of:
1. full canonical text snapshot; or
2. reconstructable diff plus its complete base snapshot/known base artifact.

Excerpt + blob/SHA alone is insufficient when the recipient lacks repository access and independent reconstruction is required.

This rule applies to TAKY’s own validation packages as well as project handoffs.

## 8. CI / repository enforcement

The canonical repository SHOULD run the deterministic replay harness on push/pull request for changes touching governance/enforcement/fixture files.

Current reference CI: `.github/workflows/taky-enforcement.yml`.

CI success proves only that deterministic repository checks passed. It does NOT prove live LLM behavior, external service state, deployment, or human-only judgment.

`CI PASS ≠ LIVE RUNTIME PASS`.

## 9. Enforcement evidence record

A recurrence-prevention claim SHALL be accompanied by a replay record containing:
- canonical commit/ref tested;
- validator version/path;
- fixture version/path;
- per-case result;
- remaining non-automatable/human-only boundary;
- overall scope of what the replay does and does not prove.

Store completed canonical replay evidence under `HISTORY/`.

## 10. Fail-closed completion rule

If a material rule is designated executable but the enforcement mechanism was not run, failed to run, or lacks required evidence, TAKY SHALL NOT upgrade that rule to enforcement PASS.

Allowed wording:
- `RULE PRESENT / ENFORCEMENT NOT PERFORMED`;
- `DETERMINISTIC GATE PASS / LIVE RUNTIME UNVERIFIED`;
- `HUMAN APPROVAL PENDING`;
- `LIVE HEAD UNVERIFIED`.

Disallowed wording:
- “재발 방지 완료” solely because prose was added;
- “최대 인수인계 완료” solely because ZIP/checksum exists;
- “검증 완료” while governing STATE is still PENDING.

END
