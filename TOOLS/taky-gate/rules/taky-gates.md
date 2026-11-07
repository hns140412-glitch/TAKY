# TAKY 5 HARD GATES — 유도형 (v0.2)

원칙: 막지 않고 맞는 길로 보낸다. USER != DEBUGGER. 승인은 작업 단위로 한 번.

| 상황 | 훅의 응답 | 누가 움직이나 |
|---|---|---|
| 평소 작업 | 아무것도 안 함 | - |
| 더 안전한 같은 의도가 있음 (dirty reset/checkout → stash 먼저, rm -r → ~/.taky/trash로 이동, netlify → routes.json의 --site) | 고쳐서 실행 + Claude에게 알림 | 아무도 안 누름 |
| 승인 범위 안 (USER가 `승인 push,deploy 2h` 입력) | 조용히 통과, 사용 내역 기록 | 아무도 안 누름 |
| 작업 브랜치 push, 백업한 브랜치 삭제 (USER 상시 허용, 11-05) | 통과 + 메모(삭제는 SHA 백업 기록) | 아무도 안 누름 |
| 승인 범위 밖 (main push, merge, deploy, prod, paid, destroy) | Claude에게 올바른 경로를 안내 (deny 사유) | Claude가 필요한 승인을 모아 USER에게 한 번 요청 |
| 고정 규칙 (사이트 모르는 netlify deploy, 프로젝트 밖·광범위 rm, 저장소 삭제) | 승인으로도 열리지 않음, 대안 안내 | Claude가 경로를 고침 |
| 같은 명령 3번째 안내 | "더 시도하지 말고 한 번에 보고" | Claude가 보고 |

승인 형식: `승인 push,deploy 2h` · `승인 merge,prod 30m` · `승인 전부 1h` · `승인 취소`
종류: push, merge, deploy(draft), prod(운영), paid, destroy, 전부. 기본 2시간, 최대 12시간.
승인 기록(~/.taky/grants.json)은 USER 입력 훅만 쓴다. Claude의 Write/Edit/Bash 쓰기는 거부된다.
이 훅은 Claude Code 승인 창(ask)을 스스로 띄우지 않는다.

## 모드
- 기본은 **observe**: 아무것도 막거나 고치지 않고, 했을 판단만 `~/.taky/delta/<날짜>.jsonl`에 `"kind":"observe"`로 남긴다.
- 기록을 보고 오탐이 없으면 `~/.taky/guide-mode` 파일에 `guide` 한 단어를 쓰면 유도가 켜진다. 지우면 다시 observe.
- 공용 상태(delta, grants, routes, trash)는 저장소가 아니라 `~/.taky/`에 둔다. git status를 더럽히지 않는다.
