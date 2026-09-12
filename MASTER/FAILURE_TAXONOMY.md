# TAKY FAILURE / DISCREPANCY TAXONOMY

Status: REV_00 / CANONICAL NORMATIVE TAXONOMY
Role: Single normative source for execution, recovery, reflection, handoff, and recurrence failure/discrepancy classes used across TAKY.

## 0. Single-source rule — HARD LOCK

This file is the normative definition source for the classes below.
Other TAKY documents MAY cite these tokens and describe local handling, but SHALL NOT redefine the same token with different semantics.

`TOKEN REFERENCE ≠ TOKEN REDEFINITION`.
`DUPLICATED LIST ≠ SINGLE SOURCE OF TRUTH`.

If a local protocol and this taxonomy diverge, this file controls unless a later explicitly authorized canonical change supersedes it.

## 1. Intent / result discrepancy axis

- `INTENT_DRIFT` — the executed meaning materially differs from the user command/latest correction.
- `SCOPE_SHRINKAGE` — requested feasible coverage was reduced without authority.
- `SUBSTITUTE_RESULT` — a different/easier deliverable was produced instead of the requested result.
- `OUTPUT_FORM_MISMATCH` — content may be related, but the requested artifact/form was not produced.
- `OMISSION` — a materially required item was left out of the result.
- `STALE_STATE` — superseded/older state was used over the current valid state.
- `UNCLASSIFIED_CONFLICT` — competing material states exist but were not surfaced/classified.
- `PREMATURE_PASS` — completion/PASS was claimed while a material gate remained failed, unknown, unverified, or not performed.
- `PREMATURE_STOP` — execution stopped at narration/intermediate state even though the user had delegated continuation, an authorized executable next action remained, and no real blocker or required human decision had been reached.
- `USER_AS_QA` — the user was made the default searcher/debugger/proof collector for work TAKY could materially perform itself.

## 2. Recovery / evidence axis

- `TRUE_UNAVAILABLE` — the original material source is genuinely inaccessible after applicable available recovery paths were checked.
- `UNVERIFIED_SOURCE_COVERAGE` — coverage state used when a material source region cannot be independently verified. This is a state, not proof of nonexistence and not a synonym for `RECOVERY_FAILED`.
- `RECOVERY_FAILED` — a materially recoverable source was not recovered before a decision/claim that depended on it.
- `FALSE_MISSING_DECLARATION` — TAKY/Assistant declared material absent/not found/never stated without sufficient recovery, and later evidence proves it existed.
- `USER_FORCED_RECOVERY` — the user had to search an old chat, locate a file, capture a screenshot, re-upload evidence, or otherwise recover evidence TAKY should reasonably have attempted to recover.
- `POST_CORRECTION_REOCCURRENCE` — the same material omission, recovery failure, misinterpretation, or execution failure recurred after an applicable correction or canonical rule already existed.

## 3. Reflection / trace / handoff axis

- `MISSING` — an active material decision/requirement lacks its required current representation/owner/result.
- `WRONG_REFLECTION` — the requirement is represented, but materially incorrectly.
- `HANDOFF_LOSS` — materially recoverable state required for resume/independent validation is absent or unusable in the handoff path.
- `UNJUSTIFIED_HOLD` — an item was deferred without adequate reason/owner/exit condition or despite available execution authority.
- `UNJUSTIFIED_REJECT` — an item was rejected without source-grounded authority/rationale.
- `UNRESOLVED_CONFLICT` — competing active decisions remain unresolved and materially block correct execution.

## 4. Enforcement / rule-application axis

- `RULE_NOT_APPLIED` — an applicable canonical rule was loaded/cited/known but the actual result violated it.
- `ENFORCEMENT_MISSING` — a material replayable/mechanically-checkable rule has only prose and no fit-for-purpose enforcement expression where one is feasible.
- `REPLAY_NOT_PERFORMED` — a recurrence-prevention claim was made without the representative replay/equivalent check required by the applicable fixture.
- `STATE_CLAIM_MISMATCH` — narrative/history/completion wording claims a higher or different state than the governing state/manifest/evidence supports.
- `HUMAN_APPROVAL_MISSING` — an action/promotion that requires explicit human approval lacks a recoverable approval record/token.
- `AUTHORITY_BOUNDARY_VIOLATION` — reference-only, external, candidate, lower-authority, or unverified material was promoted into canonical/execution-controlling authority without the required validation, localization, impact/regression check, and human approval when applicable.

## 5. Cross-axis mapping — HARD LOCK

The axes are related but not interchangeable. A single incident MAY receive multiple classes.

- `FALSE_MISSING_DECLARATION` ⇒ at least `RECOVERY_FAILED`; if the user then recovered the evidence, also `USER_FORCED_RECOVERY`.
- `USER_FORCED_RECOVERY` ⇒ `USER_AS_QA` unless the relevant source was genuinely available only to the user.
- `POST_CORRECTION_REOCCURRENCE` ⇒ regression failure; if the rule was loaded/cited yet violated, also `RULE_NOT_APPLIED`.
- `HANDOFF_LOSS` + requested maximum/full portability ⇒ may also be `SCOPE_SHRINKAGE`, `SUBSTITUTE_RESULT`, or `PREMATURE_PASS` depending on the completion claim.
- `MISSING` describes resulting representation state; `OMISSION` describes the execution discrepancy that caused/left it. They may co-occur but are not synonyms.
- `UNVERIFIED_SOURCE_COVERAGE` SHALL NOT be used to hide `RECOVERY_FAILED`, `FALSE_MISSING_DECLARATION`, or `USER_FORCED_RECOVERY`.
- `RULE_NOT_APPLIED` after a prior correction/rule may also be `POST_CORRECTION_REOCCURRENCE`.
- `STATE_CLAIM_MISMATCH` with a completion claim normally implies `PREMATURE_PASS`.
- delegated continuation + authorized next action + no real blocker/human decision + early stop ⇒ `PREMATURE_STOP`.
- `PREMATURE_STOP` and `PREMATURE_PASS` are distinct: the former is unjustified cessation; the latter is an unjustified completion claim. They may co-occur.
- reference-only/external material controlling execution before governed promotion ⇒ `AUTHORITY_BOUNDARY_VIOLATION`; if required human approval is also absent, add `HUMAN_APPROVAL_MISSING`.

## 6. Fixture mapping

- `F-01` → recovery/evidence axis + `USER_AS_QA`.
- `F-02` → `OMISSION` / coverage insufficiency / possible `PREMATURE_PASS`.
- `F-03` → `HANDOFF_LOSS` with possible `SCOPE_SHRINKAGE`, `SUBSTITUTE_RESULT`, `PREMATURE_PASS`.
- `F-04` → `STALE_STATE` / `WRONG_REFLECTION`.
- `F-05` → intent/result discrepancy axis; when the literal command delegates continued execution, an unjustified early stop may also be `PREMATURE_STOP`.
- `F-06` → `RULE_NOT_APPLIED`; recurrence may add `POST_CORRECTION_REOCCURRENCE`.
- `Q-01` → `RECOVERY_FAILED / USER_AS_QA` when the user is asked to recover evidence before available recovery families are exhausted.
- `A-01` → `AUTHORITY_BOUNDARY_VIOLATION` when REFERENCE_ONLY material is promoted without governed validation/localization.
- `B-01` → `HANDOFF_LOSS` when a claimed self-contained maximum/full handoff fails bundle closure.

## 7. Status boundary

Failure/discrepancy class and execution status are separate dimensions.

Valid result-state vocabulary remains:
`PASS / PASS_WITH_CONDITIONS / FAIL / NOT PASS / UNKNOWN / UNVERIFIED / NOT PERFORMED / HOLD / CONFLICT`.

A class token does not automatically decide final status unless a canonical gate explicitly binds it to FAIL/REGRESSION FAIL.

## 8. Change-control rule

Adding, renaming, merging, splitting, or changing semantics of a taxonomy token requires:
1. source/evidence rationale;
2. impact check across protocols/fixtures/harness;
3. mapping migration for prior tokens;
4. replay/validator update when the token is enforced;
5. human approval when the change alters protected governance meaning;
6. post-write verification that duplicate divergent definitions were not left behind.

END
