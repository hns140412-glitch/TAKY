# FAIL RECORD — 외부 사례 독립 분석 순서를 TAKY 선입견으로 뒤집고 합리화한 사건

- 사고 기록일: 2026-11-06 KST
- Incident: `2026-11-06 / REVIEW-ORDER-INVERSION` (이름은 이력 검색 식별자일 뿐 새 규칙 ID/새 작업대장 아님)
- **원래 수행 결과: FAIL / REWORK_REQUIRED**
- 증거/분류: `INTENT_DRIFT`, `RULE_NOT_APPLIED` (기존 `MASTER/FAILURE_TAXONOMY.md` 정의 사용)
- 상태: `FAILURE_ARCHIVED / CANONICAL_REVIEW_RULE_WRITTEN / F-07_REGISTERED / REPLAY_NOT_PERFORMED`
- 사용자 교정 명령: **실패 사례로 박제하고 규칙으로 등재. 자의적 해석으로 합리화 금지.**

## 1. 원래 사용자 지시 — 순서 자체가 필수 조건
> 마이닝과 기존 자료를 종합적으로 검토 분석하고 사례적 검토 분석해서
> 최적안 도출 후에
> 타키와 비교 검토해

의도는 (A) 확보된 외부 게시물/원본·기존 자료의 독립 사실 분석 → (B) 사례 간 교차 검증과 실증/실패 조건 → (C) 그 근거로 최적안 **선도출** → (D) **마지막에** 현재 TAKY와 1:1 비교·차이 식별. 기존 TAKY를 평가 초기의 정답으로 설정하지 않는다.

## 2. 실제 어시스턴트 행동 — 왜 실패인가
- 첫 번째 완성 답변은 "TAKY에 필요한 것은 ..."이라는 TAKY 기준의 결론을 먼저 선언함.
- 외부 사례에 대해서도 `기존 TAKY와 중복 여부`, `이미 구현되어 있음`, `현재 TAKY에 적합한가`라는 기준을 먼저 적용하면서 실증 결과를 재정렬함.
- 독립 비교의 기준·가중치·반례·실제 대안 및 **TAKY를 제외하고 산출한 최적안**을 제시·보존하지 못했음.
- 뒤늦게 비교표와 "최적"이라는 명칭을 붙였지만, 이는 지시된 순서 충족의 증거가 아님.
- 사용자의 수정: "검토결과 먼저 분석하고 타키와 비교검토하라니까 반대로 하네", "자의적 해석으로 합리화 하지마 / 규칙으로 등재해", "실패 사례로 ... 박제".
- **결론:** 기존 문서 `HISTORY/2026-11-06_SITE_WATCH_HARNESS_COMPARATIVE_REVIEW.md`는 실패한 비교 방식의 이력/참고자료이지, 요청을 충족한 독립 최적안 보고서가 아님. 원 보고서를 소급 PASS로 변경하지 않음.

## 3. 근본 원인
1. 어시스턴트가 `TAKY CURRENT 복구/권위 확인` 절차와 `외부 사례를 TAKY와 비교 평가` 절차를 혼동.
2. 작업의 **순서·평가 기준·산출물**을 사용자 문장 그대로 계약화하지 않고, "기존 시스템 재사용"을 최적안의 전제로 앞당김.
3. 증거 부족/부정적 외부사례도 일관된 독립 기준으로 평가하지 않고 TAKY 합리화에 사용.
4. 사용자 교정 후 문제를 실패로 즉시 분류하지 않고, 작업 순서 재설명으로 대체하려는 반응.

## 4. 재발 차단 규칙과 적용 범위
- 소유 규칙은 기존 `MASTER/INTENT_EXECUTION_PROTOCOL.md`의 `TKY-INTENT-001`; 별도 뜻이 다른 신규 규칙 ID를 만들지 않는다.
- 직접 적용 프로토콜 `MASTER/REVIEW_DEFAULT_MINING_PROTOCOL.md#independent-first-comparative-review--user-correction-2026-11-06`.
- 기존 재현 시험 모음 `MASTER/EXECUTION_REGRESSION_FIXTURES.md#f-07`.
- 이전과 같은 "외부 자료 독립 분석 → 최적안 → 마지막에 TAKY 비교" 요청에서 TAKY 먼저 결론을 내거나, TAKY에 맞는 사례만 골라 합리화하면 `FAIL / REWORK_REQUIRED`.
- 사고 정정은 말/규칙 저장에서 끝나지 않으며, 실제 독립 평가와 역추적 가능한 적용안 및 F-07 replay가 있어야 통과한다.
- 안전·권한 확인을 위한 사전 TAKY CURRENT 확인은 허용하되 **평가 결론의 선입견으로 사용하지 않는다**.

## 5. 증거 및 후속 검증
- 원문 검토 증거: `D:\Git PWA\TAKY-SOURCE-VAULT\reports\site_watch\ASIDE_INSTAGRAM_CAPTION_SOURCE_20261106.json` (9/9 본문 해시 및 1차 분류는 확보, 독립 최적안 확정 근거가 아님).
- 선행 종합 검토 문서: `HISTORY/2026-11-06_SITE_WATCH_HARNESS_COMPARATIVE_REVIEW.md` (**NOT ACCEPTED AS USER-ORDER-COMPLIANT**).
- Fixture `F-07` 현재 `REPLAY_NOT_PERFORMED`. 사용자 지시와 현행 결과를 역비교한 원인 기록/규칙 저장은 됐으나 실제 자동 인터셉트/호스팅 전체 도구실행의 기계적 차단은 검증하지 않았다.
- 남은 필수: 소스/사례를 **TAKY와 독립적으로** 분석해 동등한 평가척도를 만들고 `INDEPENDENT_OPTIMAL_OPTION` 도출 → 마지막에 TAKY 차이 비교 → 결과/실행 증거로 회귀 검증. 완료 주장 금지.

이 기록은 실패 경위를 삭제·완화·정당화하지 않고 남기는 **영구 HISTORY 사고 증거**다.
