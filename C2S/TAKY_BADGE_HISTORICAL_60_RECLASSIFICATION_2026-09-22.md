# TAKY BADGE HISTORICAL 60 RECLASSIFICATION — 2026-09-22

Status: WORKING RECLASSIFICATION / NO ACTIVATION
Source: Snap & Pop data/badge-catalog-working.json
Rule: preserve historical name/trigger provenance; do not auto-activate.

## 1. Reclassification principles

A historical badge draft is not an active badge rule.

Each draft gets:
- historical name;
- historical trigger text;
- proposed event family;
- evidence-risk class;
- disposition.

Evidence-risk:
- LOW: explicit child action can prove it.
- MEDIUM: needs context/artifact/state transition.
- HIGH: wording currently encourages inference from time, speed, focus or ability.

Dispositions:
- KEEP_DIRECTION
- MERGE_REVIEW
- RENAME_REVIEW
- EVIDENCE_RULE_REQUIRED
- HOLD_WEAK_PROXY
- RETIRE_CANDIDATE

## 2. Family groups

### SELF_START
- 해뜰락말락 — EVIDENCE_RULE_REQUIRED
- 시간 발견자 — EVIDENCE_RULE_REQUIRED
- 몰래 시작 — KEEP_DIRECTION
- 말하기 전에 GO — RENAME_REVIEW
- 책상 재등장 — MERGE_REVIEW with RETURN_RECOVERY
- 그래도 출발 — RENAME_REVIEW; avoid health/condition judgment

### TIME_CREATION / ISSUE_DURATION
- 없던시간 뿅 — EVIDENCE_RULE_REQUIRED
- 생각의 동굴 — HOLD_WEAK_PROXY if based on duration alone
- 예상초과 탐험 — HOLD_WEAK_PROXY
- 시간 어디갔지? — HOLD_WEAK_PROXY
- 쉬고 다시 — MERGE_REVIEW with RETURN_RECOVERY

### EXTRA_TASK
- 하나 더! — KEEP_DIRECTION
- 깜짝 추가탐험 — KEEP_DIRECTION

### FOCUS
- 딱 하나 집중 — EVIDENCE_RULE_REQUIRED
- 집중 불꽃 — HOLD_WEAK_PROXY if duration-only
- 조용한 몰입 — HOLD_WEAK_PROXY
- 돌아온 집중 — MERGE_REVIEW with RETURN_RECOVERY
- 집중 회수 — EVIDENCE_RULE_REQUIRED
- 유혹 피하기 — RENAME_REVIEW; avoid moralized willpower framing

### RETURN_RECOVERY
- 밥먹고 한번더 — KEEP_DIRECTION, context-specific
- 다시 왔어 — KEEP_DIRECTION
- 구조 성공 — MERGE_REVIEW HELP_REQUEST + RETURN_RECOVERY
- 잠깐만… — MERGE_REVIEW DEEP_THINKING
- 두번 봤다 — MERGE_REVIEW ERROR_PREVENTION / DEEP_THINKING
- 계획 변경 성공 — move to PLAN_ADAPTATION
- 충전하고 왔어 — KEEP_DIRECTION; absence/rest must never be penalized
- 5분 지킴이 — EVIDENCE_RULE_REQUIRED; timer compliance must not become pressure

### HELP_REQUEST
- 도움 신호 — KEEP_DIRECTION
- 탐험대와 해결 — EVIDENCE_RULE_REQUIRED; must prove minimal help + child solution without awarding for crew dependence

### ERROR_DISCOVERY / CORRECTION
- 뭔가 이상한데? — KEEP_DIRECTION
- 실수 청소부 — RENAME_REVIEW
- 고쳐서 완성 — KEEP_DIRECTION
- 범인은 여기! — KEEP_DIRECTION
- 계산 탐정 — domain-specific; MERGE_REVIEW

### RETRY / METHOD CHANGE
- 한번 더! — KEEP_DIRECTION
- 지우개 용사 — RENAME_REVIEW
- 방법 바꿔보기 — KEEP_DIRECTION

### DEEP_THINKING
- 생각이 길었다 — HOLD_WEAK_PROXY if duration-only
- 생각의 동굴 — candidate belongs here only with reflection/artifact evidence
- 잠깐만… — KEEP_DIRECTION if explicit reconsideration exists

### SELF_EXPLANATION
- 설명해볼게 — KEEP_DIRECTION

### PLAN_ADAPTATION / SELF_DIRECTION
- 작전 짜기 — KEEP_DIRECTION
- 내가 고를래 — KEEP_DIRECTION
- 계획 변경 성공 — KEEP_DIRECTION
- 어려운거 먼저 — EVIDENCE_RULE_REQUIRED, avoid implying universal best strategy
- 쉬운거부터! — EVIDENCE_RULE_REQUIRED, avoid implying universal best strategy

### TASK / COMPLETION EXPERIENCE
- 아침 한입 — context-specific
- 출발 준비 끝 — likely Ready-specific; review whether this is learning badge scope
- 번개 완료 — HOLD_WEAK_PROXY; speed must not imply quality/ability
- 천천히 정확히 — HOLD_WEAK_PROXY; elapsed time alone invalid
- 한칸씩 — KEEP_DIRECTION if task decomposition explicit
- 결국 해냈다 — KEEP_DIRECTION with retry/completion evidence
- 흐름 탔다! — EVIDENCE_RULE_REQUIRED
- 밀린짐 정리 — RENAME_REVIEW; avoid shame around carry-over
- 오늘 안 넘긴다 — RENAME_REVIEW; avoid pressure
- 가볍게 끝! — HOLD_WEAK_PROXY if speed-based
- 마지막 조각 — KEEP_DIRECTION with identifiable prior unresolved issue
- 아하! — EVIDENCE_RULE_REQUIRED; understanding cannot be inferred from correctness alone
- 막힘 돌파 — KEEP_DIRECTION with explicit retry/problem-solving evidence
- 오늘은 여기까지 — KEEP_DIRECTION; stopping appropriately is meaningful and must not be treated as failure
- 어제보다 익숙 — HOLD_WEAK_PROXY; improvement/ability inference risk

### SPECIAL_BEHAVIOR
- 오늘 좀 특별한데? — KEEP_DIRECTION only as candidate generator, never generic AI novelty inference

## 3. High-risk drafts requiring special protection

The following should never activate from time/count/score alone:
- 번개 완료
- 천천히 정확히
- 집중 불꽃
- 조용한 몰입
- 생각이 길었다
- 생각의 동굴
- 예상초과 탐험
- 시간 어디갔지?
- 어제보다 익숙
- 가볍게 끝!

## 4. Cross-app ownership hints

Ready-heavy:
SELF_START / TIME_CREATION / FOCUS / RETURN_RECOVERY / PLAN_ADAPTATION / EXTRA_TASK

Snap-heavy:
HELP_REQUEST / ERROR_DISCOVERY / RETRY / DEEP_THINKING / SELF_EXPLANATION / WRITING_EXPLORATION / SPECIAL_BEHAVIOR

Hide-heavy:
RETURN_RECOVERY / RETRY / HELP_REQUEST / SELF_EXPLANATION / memory-specific error discovery

These are producer tendencies, not award ownership.

## 5. Next catalog closure work

For every retained draft:
1. choose canonical family;
2. define strong/weak evidence;
3. define dedupe window;
4. define repeat/progression semantics;
5. decide whether 5×5 tier/star progression applies;
6. approve child-facing name/copy;
7. approve theme art;
8. activate only after canonical review.

END
