# TAKY SYSTEMWIDE NEW CHAT START — 2026-10-11 LATEST

## RESUME
최신 TAKY 기준으로 재개한다.
기존 CLOSED / LOCKED / VERIFIED는 그대로 상속하고 OPEN만 진행한다.
문서/바인딩/동기화 재작업을 제품 발전으로 계산하지 않는다.
USER != DEBUGGER. 가능한 브라우저/목업/로컬 E2E는 먼저 자동 검증한다.

## HARD GUARDS
- dirty worktree 보존
- reset / checkout / clean / stash-all 금지
- push / merge / deploy / Netlify 금지(사용자 승인 전)
- paid / usage-based API 금지(사용자 승인 전)
- 동일 실패 반복 금지
- 오래된 전역 문서가 최신 실제 repo/runtime 증거를 덮어쓰지 못함

## OBSERVED REPOSITORIES — 2026-10-11
- TAKY
  - D:\Git PWA\TAKY
  - branch character-asset-behavior-separation-2026-09-30
  - HEAD fee09fa8cdd0
  - dirty 549
- READY
  - D:\Git PWA\READY-WEBAPP-20261006
  - branch taky/ready-webapp-vertical-slice-20261006
  - HEAD 2d10583713a8
  - dirty 40
- HIDE
  - D:\Git PWA\Hide & Seek
  - branch family-character-profile-consumer-2026-09-30
  - HEAD 5b29db829923
  - dirty 35
- SNAP
  - D:\Git PWA\Snap & Pop
  - branch family-character-profile-consumer-2026-09-30
  - HEAD 94d548545b3c
  - dirty 15
- PLAY CAMP
  - D:\Git PWA\HANGUL-PLAY-20261007
  - branch main
  - HEAD bb9defb5582f
  - dirty 195
- TAKY MOBILE
  - D:\Git PWA\TAKY-MOBILE
  - branch main
  - HEAD 9bcb7d966083
  - dirty 8
- SAVEY
  - D:\Git PWA\SAVEY
  - branch main
  - HEAD 939b229e2b55
  - dirty 75

## CLOSED — LEARNING FAMILY USER LOOP
Do not reopen unless new regression evidence appears.

### Ready -> Hide
Verified real browser mock:
parent FACT -> Planner -> child Ready session -> Hide TRACE/LINK/CORE/RECALL -> TASK_COMPLETED -> Ready Planner completion -> session end -> Ready history -> parent replan.
Result:
- PASS
- gaps 0
- errors 0
- completed task not reprojected after replan

Evidence:
- READY tools/mock-family-learning-loop-e2e.cjs
- READY artifacts/mock-family-loop-20261010/

### Ready -> Snap
Verified real browser mock:
Ready task -> Snap landmark -> 3 authored expression steps -> Snap record/gem -> TASK_COMPLETED -> Ready completion/history/replan.
Result:
- PASS
- gaps 0
- errors 0

Evidence:
- READY tools/mock-family-snap-loop-e2e.cjs
- READY artifacts/mock-family-snap-loop-20261010/

### Ready -> Play Camp
Implemented optional fail-closed Ready route:
- Play Camp is available only when play_camp_target is provided.
- no fake/default production URL was invented.
- trusted origin and inbound result acceptance include play-camp only while target is present.
- Ready suggestion routes Play Camp-owned activities only:
  CVC / phonics / sound blending / fractions / shapes / nets / origami / patterns / number blocks / matchsticks / 3D spatial concepts.
- generic English/math remains Ready/other specialist ownership.

Play Camp bridge:
- src/lib/readyBridge.ts
- src/main.tsx boot
- learning observation completion promotes existing Play Camp evidence to Ready task completion
- partial/completed return button to Ready
- completion is not newly invented; existing Play Camp completion_state is reused.

Verified browser mock:
Ready -> Play Camp CVC activity -> 3 phoneme stones -> blend -> BLEND_SEQUENCE_COMPLETED -> Ready COMPLETED -> history/replan.
Result:
- PASS
- gaps 0
- errors 0
- suggested_app = play-camp

Evidence:
- READY tools/mock-family-play-camp-loop-e2e.cjs
- READY artifacts/mock-family-play-camp-loop-20261010/
- PLAY tests/readyBridge.test.ts

### One Ready session -> three apps
Verified:
one Ready canonical session with 3 tasks:
1. word -> Hide
2. sentence expression -> Snap
3. CVC -> Play Camp

Result:
- all 3 tasks COMPLETED
- all 3 laps closed with result_state COMPLETED
- Planner 3/3 COMPLETED
- session ended once
- Ready history created as one session record
- PASS

Evidence:
- READY tools/mock-family-three-app-one-session-e2e.cjs
- READY artifacts/mock-family-three-app-one-session-20261010/

### Regression state after integration
- READY test files: 26/26 PASS
- READY ready-runtime-v07.js syntax PASS
- READY ready-stage-d-base-v1.js syntax PASS
- READY diff --check PASS
- PLAY readyBridge targeted: 4/4 PASS
- PLAY npm test PASS
- PLAY build PASS
- PLAY diff --check PASS

Relevant local files:
READY:
- M ready-runtime-v07.js
- M ready-stage-d-base-v1.js
- tools/mock-family-learning-loop-e2e.cjs
- tools/mock-family-snap-loop-e2e.cjs
- tools/mock-family-play-camp-loop-e2e.cjs
- tools/mock-family-three-app-one-session-e2e.cjs
- corresponding artifacts/mock-family-*/

PLAY:
- M src/main.tsx
- src/lib/readyBridge.ts
- src/lib/learningEngine.ts
- tests/readyBridge.test.ts
- existing learning engine tests remain active

## CLOSED — TAKY MOBILE -> FULL LEARNING LOOP
TAKY Mobile already has START_LEARNING_LOOP / nonce-bound result handling / CONTINUE execution.

Verified current-code E2E:
TAKY Mobile `ㄱ`
-> Ready
-> Hide
-> Snap
-> Play Camp
-> Ready session completion
-> TAKY Mobile
-> COMPLETED / LEARNING_LOOP_RESULT_RECEIVED

Result:
- PASS
- multi-specialist roundtrip real browser E2E
- TAKY Mobile test files 5/5 PASS
- src/app.js syntax PASS
- src/execution.mjs syntax PASS
- diff --check PASS

Evidence:
- TAKY-MOBILE tests/learning-loop-multi-specialist-roundtrip-e2e.cjs
- TAKY-MOBILE tests/learning-loop-execution.test.mjs

Do not spend the next session rebuilding CONTINUE or app dispatch.

## CLOSED / VERIFIED — EXPLORER CREW VISUAL + SCRIPT
Keep inherited:
- 07-24 approved FRONT assets are physically consumed in Ready/Hide/Snap and Play Camp.
- Ready/Hide/Snap: 54 paths browser-render verified.
- Play Camp: 18/18 Hub render verified.
- approved turnaround SHA preserved.
- no Visual ID redefinition.

Dialogue:
- R10 source lock = EXPLORER_CREW_V2_SOURCE_LOCK_20261009_SCRIPT_LOCK_R10
- MAIN_CREW E5/E6 144/144 SCRIPT_LOCKED
- PLAY_CAMP Core6 36/36 SCRIPT_LOCKED + runtime enabled
- MAIN sourced scene blocked from Play Camp.
- Crew suite 6/6 PASS.
- paid ElevenLabs generation remains HOLD.

## SAVEY — CURRENT RESUME PRIORITY
Authority:
- D:\Git PWA\SAVEY\HANDOFF\SAVEY_NEW_CHAT_START_2026-10-09_LATEST.md
- includes 2026-10-11 addendum
- Google Sheets canonical + append-only MUTATION_JOURNAL rules unchanged
- finance authority remains SAVEY-owned
- no deployed/auth privilege expansion

### Already verified — do not repeat as product work
1. Local offline/reconnect full loop:
   OFFLINE MANUAL ENTRY
   -> IndexedDB queue
   -> reconnect
   -> INBOX
   -> journal ACK
   -> effective pull
   -> queue 0
   -> canonical UI status
   -> record rendered

Evidence:
- SAVEY artifacts/mock-offline-reconnect-full-loop-20261010/result.json
Result:
- pass true
- amount 8,500
- queue 1 -> 0
- cachedRows 1
- canonical status "canonical 원장 반영 확인 완료"
- gaps 0 / errors 0

2. Mobile emulation audit:
- parent + child
- widths 320 / 375 / 390 / 430 / 1024
- all pass
- no horizontal overflow
- confirm flow preserved

Evidence:
- SAVEY artifacts/device-mock-audit-20261011/result.json
- 10 cases PASS
- this is Chrome mobile emulation, not physical iOS verification.

3. Real authenticated Google HTTP/journal path:
Historical live evidence already proves:
- browser IndexedDB enqueue
- personal INBOX stage
- authenticated push
- MUTATION_JOURNAL append
- IndexedDB queue removal
- effective pull
- Google INBOX readback
- Google journal readback
- physical base sheet unchanged
- UI canonical status
- append-only compensation / cleanup

Evidence:
- SAVEY _savey_open1_http_e2e5.log
- SAVEY HANDOFF/SAVEY_OPEN1_INTEGRATED_HARDENING_EVIDENCE_2026-10-04.md

Do NOT rerun live Google mutation E2E casually. It writes synthetic live rows and compensates them. Only rerun if sync/journal/auth code materially changes or user specifically asks.

4. Latest inherited SAVEY validation from 2026-10-11 addendum:
- npm test 171/171 PASS
- build PASS
- git diff --check PASS
- design remains provisional/revise, not Golden-approved.

### SAVEY OPEN — next session starts here
Priority is user-visible function, not another regression sweep.

OPEN A — child live period projection
- child month/all-time values must come from canonical/live projections or fail closed.
- preview/demo values must never appear as canonical.
- finish/verify actual period projection consumption in child UI.

OPEN B — family input UX actually consumed
- take one realistic family expense/planned-spend/event/car example through existing local pipeline.
- confirm the final parent/child screens surface the new canonical/effective data in the expected chapter.
- use synthetic/local mock first.
- do not touch live Google unless the local gap cannot be resolved and a live recheck is necessary.

OPEN C — design fidelity
- current design status is REVISE / provisional composite.
- do not call functional PASS a Golden visual approval.
- compare current rendered parent/child screens against approved/provisional composite authority and fix only meaningful user-visible mismatch.
- no source authority rewrite.

OPEN D — deployed TAKY shell auth / real iOS
- remains gated by deployment / physical-device context.
- do not block local product work on this.
- no Netlify deploy without user approval.

After SAVEY user-visible OPEN closes, next broad system priority:
- Work OS real workflow execution (Notion/Mail/task/calendar), because it remains the weakest systemwide execution axis.
- do not return to Crew/audio unless a real product dependency requires it.

## EXECUTION ORDER ON RESUME
1. Read this file.
2. Read SAVEY/HANDOFF/SAVEY_NEW_CHAT_START_2026-10-09_LATEST.md.
3. Verify only SAVEY HEAD/status; preserve dirty tree.
4. Inspect child period projection consumer and current rendered child values.
5. Mock realistic SAVEY family data through existing pipeline.
6. Fix actual user-visible gap only.
7. Run targeted tests + build + diff-check.
8. Report what works now / what still does not.
9. No push/deploy/paid API.

## REPORTING RULE
Do not emphasize "development/progress".
Report only:
- currently works
- currently does not work
- user-visible effect
- remaining OPEN

## RESUME SENTENCE
최신 TAKY 기준으로 재개. 먼저 D:\Git PWA\TAKY\HANDOFF\TAKY_SYSTEMWIDE_NEW_CHAT_START_2026-10-11_LATEST.md 를 전체 읽고, SAVEY의 현재 HEAD/status를 확인한다. Learning Family / TAKY Mobile 통합 E2E는 CLOSED로 상속하고 재검증에 매몰되지 않는다. SAVEY OPEN A(child live period projection)부터 사용자 체감 기준으로 진행한다. dirty worktree 보존, reset/checkout/clean/stash 금지, push/merge/deploy/paid API 금지.
