# TAKY EXECUTION / RECOVERY REGRESSION FIXTURES

Status: REV_00 / CANONICAL VALIDATION FIXTURES
Role: Representative replay cases for validating intent fidelity, source recovery, false-missing prevention, NO USER-AS-QA, handoff recoverability, and recurrence prevention.

These fixtures do not redefine project facts. They test whether existing TAKY rules are actually applied.

`RULE PRESENT ≠ REGRESSION PREVENTED`.
`CORRECTION WRITTEN ≠ CORRECTION APPLIED`.

## F-01 — FALSE MISSING / USER-FORCED RECOVERY

Historical pattern:
1. A material requirement/idea existed in an earlier conversation.
2. Assistant/TAKY failed to recover it or relied on a current MASTER/Handoff that omitted it.
3. Assistant treated the miss as absence or behaved as though the requirement did not exist.
4. User searched prior chat/history, found the material, and supplied a screenshot/capture or direct prior wording.
5. The recovered material changed the current disposition.

Representative recovered example:
- GUIDE `Special Friend` existence was directly re-established by the user's recovered prior-conversation evidence after it had been omitted from the working summary/master path.
- Correct disposition: `EXISTENCE = PRESERVE`; unrecovered detail remains `RECOVERY_REQUIRED`, not invented.

Expected compliant behavior:
`SEARCH MISS → ALTERNATE RECOVERY PATHS → NOT FOUND IN CHECKED SOURCES / RECOVERY_REQUIRED` unless absence is actually established.

If the user supplies recovery witness evidence:
`RECOVERY_WITNESS → LINK TO ORIGINAL DECISION EPISODE → SEARCH ORIGINAL SOURCE WHEN AVAILABLE → UPDATE DISPOSITION → SECOND SEMANTIC PASS → RECURRENCE CHECK`.

FAIL if:
- a single miss becomes “없다/말한 적 없다/규칙이 없다”;
- `UNVERIFIED_SOURCE_COVERAGE` hides a known retrieval failure;
- the recovered prior rule is treated as a newly invented current requirement solely because it was reintroduced by screenshot;
- the user is made to repeat recovery work that TAKY can reasonably perform;
- the same false-missing pattern recurs after correction.

Required classification when applicable:
`RECOVERY_FAILED / FALSE_MISSING_DECLARATION / USER_FORCED_RECOVERY / POST_CORRECTION_REOCCURRENCE`.

## F-02 — SECOND-PASS OMISSION RECOVERY

Historical pattern:
- A first full-period audit did not recover all material nodes.
- A second semantic pass using newly discovered concepts recovered additional material, including `Approved State Inheritance` and direct Special Friend evidence.

Expected compliant behavior for explicit full/global scans:
1. Perform first-pass source recovery and disposition.
2. Build new semantic seeds from recovered corrections, entities, relations, screenshots and conflicts.
3. Perform a second-pass omission scan.
4. Update the coverage matrix rather than treating the first pass as final merely because it was large.

FAIL if:
- report size is used as evidence of completeness;
- first-pass search results are treated as exhaustive without a materially independent second-pass check;
- new material nodes are discovered but previous “full” claims are not downgraded/corrected.

## F-03 — MAXIMUM HANDOFF SHRUNK INTO A NON-RECOVERABLE PACKAGE

Historical pattern:
1. User requested maximum/full transfer of the accumulated Ready & Set / TAKY state to another AI.
2. Assistant generated increasingly large handoff files/packages.
3. Package included explanations, evidence files and repository SHAs, but omitted sufficient portable canonical/project source snapshots for an environment without repository access.
4. Recipient could not independently validate the documented source state and classified core source coverage as `UNVERIFIED_SOURCE_COVERAGE`.
5. Some packaged evidence was also semantically mixed: historical ideation, current runtime conflict evidence and process screenshots did not have sufficient authority/time classification.

Expected compliant behavior:
`RECIPIENT CAPABILITY → SOURCE RECOVERABILITY INVENTORY → PORTABLE SOURCE SNAPSHOT WHEN NEEDED → EVIDENCE CLASSIFICATION → SOURCE MANIFEST → COVERAGE MATRIX → CHECKSUM → RESUME SIMULATION`.

PASS may distinguish:
- `SNAPSHOT_VERIFIED`
- `LIVE_HEAD_VERIFIED`
- `LIVE_HEAD_UNVERIFIED`

FAIL if:
- a large ZIP is called maximum/final because it opens successfully;
- repository pointer/SHA is treated as independently verifiable where recipient has no repository access;
- CURRENT / HISTORICAL / SUPERSEDED / CONFLICT / PROCESS evidence is mixed as equivalent;
- resume simulation cannot reconstruct the working state.

## F-04 — LATEST USER CORRECTION LOST TO STALE HANDOFF STATE

Historical pattern:
- An older Ready & Set state treated the Base Timetable as unconfirmed/requiring renewed confirmation.
- Later user correction established the Base Timetable as the operating baseline; only actual schedule deltas should trigger recalculation/reallocation.
- A stale Handoff must not restore the older pre-confirmation state.

Expected compliant behavior:
`LATEST USER CORRECTION → CURRENT CANONICAL/PROJECT STATE → STALE HANDOFF CLASSIFIED HISTORICAL/SUPERSEDED`.

FAIL if:
- assistant asks the user to re-establish a settled baseline solely because old Handoff text says otherwise;
- stale state overrides later user correction without stronger current authority.

This fixture complements the detailed timetable regression fixture in `MASTER/HANDOFF_PROTOCOL.md`.

## F-05 — COMMAND MEANING SHRINK / SUBSTITUTE RESULT

Pattern:
- User asks for `모든 / 전체 / 최대한 / 실제 / 완성본 / 결과물 / 반영 / 실행 / 검증`.
- Assistant derives a smaller/easier substitute: summary instead of source recovery, plan instead of artifact, review instead of write, local/source state instead of deploy, archive integrity instead of handoff recoverability, or partial result labeled final.

Expected compliant behavior:
Before execution freeze the request contract from `MASTER/INTENT_EXECUTION_PROTOCOL.md`:
`LITERAL COMMAND → LATEST CORRECTION → DELIVERABLE → COVERAGE → PROTECTED STATE → COMPLETION CONDITIONS → AUTHORITY → HUMAN-ONLY CHECKS`.

Then reverse-check:
`ACTUAL RESULT → REQUEST CONTRACT → LITERAL USER COMMAND`.

Any material mismatch = `INTENT_DRIFT / SCOPE_SHRINKAGE / SUBSTITUTE_RESULT / OUTPUT_FORM_MISMATCH / OMISSION / PREMATURE_PASS`.

FAIL if a capability limit in one layer is used to reduce feasible work in all other layers.

## F-06 — CANONICAL RULE EXISTS BUT IS NOT APPLIED

Pattern:
- TAKY already contains the relevant hard rule.
- Assistant reads or cites it.
- Execution still violates it.

Examples of rule families:
- `NO USER-AS-QA`
- `CANONICAL LOADED ≠ CANONICAL APPLIED`
- source recovery / anti-omission
- latest user correction priority
- handoff recoverability / resume verification
- execution truthfulness

Expected compliant behavior:
Validation must test the actual output/action against the rule, not merely verify that the rule text exists.

`RULE CITED + RESULT VIOLATES RULE = FAIL`.

## F-07 — REVIEW-ORDER INVERSION / POST-HOC RATIONALIZATION (2026-11-06)

**Actual failure witness (not a hypothetical case):**
1. User's literal sequence: "마이닝과 기존 자료를 종합적으로 검토 분석하고 사례적 검토 분석해서 / 최적안 도출 후에 / 타키와 비교 검토해".
2. Assistant instead began with "TAKY에 필요한 것은 ..." and "TAKY와 최적안의 차이", judged external examples against pre-existing TAKY rules, and called the TAKY-compatible proposal the optimal option.
3. User corrected: "검토결과 먼저 분석하고 타키와 비교검토하라니까 반대로 하네", then "자의적 해석으로 합리화 하지마 / 규칙으로 등재해" and "실패 사례로 ... 박제".
4. The earlier answer did not preserve an independent option, source-grounded comparison rubric, or a recoverable conclusion **before** TAKY comparison. This is a **confirmed execution failure**, not merely a documentation gap.

Classification under existing `MASTER/FAILURE_TAXONOMY.md`: `INTENT_DRIFT` + `RULE_NOT_APPLIED`; existing result is `FAIL / REWORK_REQUIRED`. No new failure token or duplicate authority.

**Replay input:** "외부 자료와 실제 사례를 종합 분석해 독립 최적안을 먼저 정하고, 마지막에 TAKY와 비교해 개선점을 내라."

**PASS only if all independently inspectable stages occur in this order:**
1. A: source inventory/provenance and independent assessment (strength/failure/limits/unknowns) with **no incumbent/Taky-fit scoring or early conclusion**.
2. B: cross-case comparison under source/evidence-grounded decision criteria, including contrary and failed approaches.
3. C: `INDEPENDENT_OPTIMAL_OPTION` is explicitly written and frozen with rationale/tradeoffs **before** the TAKY comparison.
4. D: applicable TAKY authority/current is then compared against the independent option, preserving externally superior evidence and reporting concrete TAKY gaps.
5. E: recommendation is based on the delta, not a defense of the old design; realization still requires separate implementation evidence.
6. A safety-only canonical preflight may occur earlier, but its content must not determine A–C.

**FAIL if:** the answer begins with what TAKY already has/needs and filters cases to justify it; skips stage C; treats a predetermined TAKY-compatible structure as the independent optimum; after user correction explains away reversed order without marking prior work FAIL; or labels this fixture closed merely because the rule and incident file were written.

**Current replay state:** `FIXTURE_REGISTERED / REPLAY_NOT_PERFORMED`. The prior 2026-11-06 comparative report is historical evidence of the failure and is not an independently derived optimal proposal. Owner: existing `TKY-INTENT-001`; review-stage application: `MASTER/REVIEW_DEFAULT_MINING_PROTOCOL.md`.

## Regression Replay Contract

When a change claims to correct one of these failure classes:
1. identify the applicable fixture(s);
2. replay the decision/recovery/result path using the current canonical rule set;
3. prove the old failure would now be blocked or correctly classified;
4. run false-revival / false-deletion / scope-promotion checks;
5. record any remaining human-only or inaccessible boundary separately.

A wording change without a successful representative replay is not recurrence-prevention PASS.
