# TAKY 2.0 공방검토 (攻防 Review) Protocol V1

Status: USER-NAMED OPERATIONAL STANDARD
Scope: comparison / research / verification / adversarial review / defensive response
Parent: TAKY -> 5 HARD GATE (KEY / CONTEXT / ROUTE / COST / DONE)
Rule: 공방검토 is NOT a sixth Gate and does not reopen CLOSED Canonical work by itself.

## Definition

공방검토 is the end-to-end review loop used when a material change needs more than ordinary regression.
It combines constructive improvement with adversarial attack and evidence-bound defense.

Canonical sequence:
1. 비교 검토
2. 분석
3. 보완 / 개선
4. Deep Search + 사례 제안
5. 최적화
6. 오류 검증
7. 자기 검증
8. 회귀 검증
9. 공격적 검증
10. 결정
11. 방어적 대응
12. 재공격 / 재검증
13. CLOSE or HOLD

## Core rules

- RULE WRITTEN != RULE ENFORCED.
- CODE DONE != VALUE DELIVERED.
- 공격 지적을 설명으로만 방어하지 않는다.
- 유효 공격은 코드/계약/테스트/증거 경로를 수정하거나 명시적 수용 위험으로 남긴다.
- 기각 공격은 근거와 반증 evidence를 남긴다.
- 공격 원문/receipt는 방어 후에도 덮어쓰지 않는다.
- 방어 결과는 공격의 target revision / authority / scope에 다시 바인딩한다.
- 동일 실패 반복 금지.
- USER != DEBUGGER.
- external reviewer/model call is selected by Necessity + COST policy, not by role label alone.

## Review levels

BASIC:
- comparison / analysis / improvement
- local error + self + regression verification
- attack simulation may be local
- independent external review is optional by necessity

STRONG:
- material authority, external write, irreversible action, high-impact runtime or explicit STRONG request
- independent review artifact is mandatory
- producer, primary verifier and independent reviewer must be materially separated
- missing independent reviewer => PARTIAL/HOLD, never fake PASS

## Independent review evidence

STRONG independence is evidence, not a role-name string.
Required bindings:
- receipt_id
- reviewer_role
- reviewer_id
- target_result_digest or target revision/hash
- authority_digest / Key version
- execution_scope
- source_or_artifact_ref
- acceptance_state
- critical_gaps
- review_digest

A field such as independent_reviewer="CLAUDE" without a bound review receipt is insufficient.

## Decision process

Each material attack is decided as one of:
- ADOPT: valid defect; defense required.
- REJECT: invalid/stale/out-of-scope; rejection evidence required.
- DEFER: real but non-blocking; owner/scope/re-entry trigger required.
- HOLD: required evidence/reviewer unavailable; no closure claim.

Decision precedence:
1. USER Key / authority
2. current Canonical / CURRENT authority
3. objective runtime/test evidence
4. independent review evidence
5. AI explanation

## Defensive response

For ADOPT:
- apply minimum-sufficient correction
- add a negative test reproducing the attack
- rerun directly affected tests
- rerun whole relevant regression
- bind defense evidence to the same claim/scope/revision

For REJECT:
- preserve attack evidence
- state why it is invalid
- point to contradicting authority/test/runtime evidence
- do not modify implementation merely to satisfy a stale attack

## Closure

CLOSE requires:
- unresolved P0 = 0
- unresolved P1 = 0
- accepted P2 either fixed or explicitly deferred with trigger
- error/self verification PASS
- relevant regression PASS
- no stale/superseded evidence used for current claims
- DONE predicates mapped to accepted evidence
- STRONG: actual independent review receipt present and accepted
- defensive changes survive reattack/negative tests
- decision and defense evidence retained

If an independent reviewer is unavailable because of quota/tool/runtime limits:
- record REVIEW_UNAVAILABLE
- continue local attack/self/regression where useful
- state PARTIAL/HOLD for STRONG
- do not repeatedly burn quota on the same failed path

## External practice basis

This protocol adopts the useful parts of:
- NIST/NASA IV&V: independent, objective review/analysis/testing and evidence-based conclusions.
- OWASP threat modeling: identify threats, agree mitigations, then review/validate whether mitigations are testable and successful.
- Google engineering review: review design/functionality/tests, require tests that would fail on broken behavior, and prefer small reviewable changes.

These references inform the method but do not override TAKY Canonical authority.

## Current implementation mapping

- preflight gate_receipts: validator ownership profile
- independent_review_registry: actual independent-review evidence binding
- evidence_registry: claim/scope/authority/tier evidence
- completion_registry.verification_evidence: predicate -> evidence binding
- done_gate_receipts: DONE decision evidence
- user_events: explicit USER event evidence

DEEP MEMORY — LIGHT EXECUTION.
