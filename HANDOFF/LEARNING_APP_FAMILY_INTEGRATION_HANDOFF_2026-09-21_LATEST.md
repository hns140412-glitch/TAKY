# LEARNING APP FAMILY — INTEGRATION HANDOFF — 2026-09-21 LATEST

## Resume command

최신 TAKY 기준으로 Learning App Family 통합 작업을 재개해.

FIRST READ:
1. TAKY `C2S/LEARNING_APP_FAMILY_INTEGRATION_C2S_2026-09-21.md`
2. TAKY `C2S/LEARNING_APP_FAMILY_INTEGRATION_ATOMS_2026-09-21.json`
3. this handoff
4. each app's latest own C2S/handoff before editing.

## Live baseline at handoff

Ready & Set
- repo: hns140412-glitch/Ready-Set
- main: `98df214a6078f16f2b6710016898a4d7798798db`
- R1/R4/R5/R6 merged and targeted verified.
- latest state must be live-refreshed before edit.

Hide & Seek
- repo: hns140412-glitch/Hide-Seek
- branch: `implementation/hide-seek-capture-session-v02`
- head: `7136c22b23e05b5f902a15f7e421d79aeb7a8574`
- PR #4 DRAFT / HOLD / DO NOT MERGE
- relation to main: +526 / -0
- no deploy/Netlify.

Snap & Pop
- repo: hns140412-glitch/Snap-Pop
- branch: `taky/snap-pop-implementation-2026-09-20`
- head: `3af4d5076ed464b43c7f8e3fa60f7612539376fe`
- relation to main: +584 / -3 / DIVERGED
- current active work must not be treated as main.
- no blind rebase.
- no deploy/Netlify without a new frozen candidate + TAKY external gate.

## Integration priority

P1 Ready:
- fix HELP_NEEDED → WAITING_FOR_PARENT.
- preserve BLOCKED separately.

P2 Ready:
- implement central READY_LEARNING_CONTEXT_V1 producer in specialist launch.

P3 Hide:
- consume READY_LEARNING_CONTEXT_V1.
- no independent Hanja grade inference.
- Language Memory remains Hide-owned.

P4 Snap:
- align existing learning-context decoder to central contract.
- preserve vocabulary sourceOwner / expression-material-only rule.

P5 Snap:
- capability-reconcile the 3 missing main commits (README authority + shared release/PWA + shared event envelope) into the active branch.
- do not rewrite 584-commit history.

P6 cross-app:
- Ready→Hide→Ready
- Ready→Snap→Ready
- Ready→Hide→Snap→Ready
- exactly one Ready Planner task IN_PROGRESS.
- session_id/goal_id/task_id/lap_id/return_target preserved.
- specialist cannot end Ready session.

## Hard locks
- Work/Learning authority is not commonized.
- Family/child identity/role/permission is not shared technical authority.
- shared mechanisms != shared semantics.
- user is not tester/debugger.
- CODED / CI / RUNTIME / DEVICE / PRODUCTION remain separate.
- no Netlify/deploy until frozen candidate + external-resource gate.
- blocked path => classify cause; do not repeat identical failing attempt.

## New chat start prompt

“최신 TAKY 기준으로 Learning App Family 통합 작업을 재개해. 먼저 TAKY의 `C2S/LEARNING_APP_FAMILY_INTEGRATION_C2S_2026-09-21.md`, `C2S/LEARNING_APP_FAMILY_INTEGRATION_ATOMS_2026-09-21.json`, `HANDOFF/LEARNING_APP_FAMILY_INTEGRATION_HANDOFF_2026-09-21_LATEST.md`를 읽고 Ready/Hide/Snap 최신 live HEAD를 다시 확인해. Ready의 HELP_NEEDED→WAITING_FOR_PARENT 정정부터 시작하고, READY_LEARNING_CONTEXT_V1을 Ready→Hide/Snap 공통 계약으로 실제 연결한 뒤 Snap active branch의 main-behind 3개 shared-foundation capability를 broad rebase 없이 reconcile해. 각 앱의 현재 개발을 덮어쓰지 말고 통합계약만 연결해. 사용자 테스트 금지, Netlify/배포 금지, CODED/CI/RUNTIME/DEVICE/PRODUCTION 분리.” 
