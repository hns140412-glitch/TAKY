---
name: taky-log
description: TAKY 공용 맥락 복원. 사용자가 정확히 "로그"라고 입력하면 사용한다. CURRENT 머리말만 읽고 현재 목표, authority, OPEN, 다음 실행을 3~5줄로 답한다.
---

# 로그 (TAKY LOG FAST PATH)

1. `TAKY_AI_CURRENT`의 머리말(PURPOSE부터 RESPONSE RULE까지)만 읽는다. DELTA 본문은 읽지 않는다.
2. CURRENT TAKY2 RESUME에 지정된 namespace CURRENT / NEW_CHAT_START가 있으면 그 포인터만 읽는다.
3. 역할·authority가 서로 다를 때만 `TAKY_AI_PROTOCOL`을 읽는다.
4. 실제로 부족한 정보가 있을 때만 `AI_SHARED_CONTEXT_CURRENT`와 미읽은 DELTA 중 최신 3개를 읽는다.
5. HISTORY, 전체 HANDOFF, 과거 대화 replay는 하지 않는다. CLOSED/PROMOTED는 새 상충 증거 없이 다시 열지 않는다.

답은 3~5줄:
- 현재 목표
- 복원 authority (USER = Final Authority)
- 현재 OPEN (ID만)
- 바로 다음 실행 1개

DEEP MEMORY — LIGHT EXECUTION.
