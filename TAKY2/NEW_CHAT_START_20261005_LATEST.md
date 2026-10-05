# TAKY 2.0 — NEW CHAT START / BORDER COLLIE LATEST

## COPY / RESUME
최신 TAKY 2.0 별도 브랜치 기준으로 재개해.

먼저 `TAKY2/NEW_CHAT_START_20261005_LATEST.md`와 현재 HEAD만 확인하고, CLOSED는 그대로 상속해. 전체 Beta/Alpha 재감사·전제문서 반복 재독·이미 끝난 Gate 재구현은 하지 말고 OPEN만 진행해.

현재 로컬 authority:
- repo: `D:\Git PWA\TAKY-2.0-ORCH`
- branch: `taky-2.0-orchestrator-2026-10-05`
- checkpoint: `f911a989e3f15baa664f66ccae10f5441134576e`
- authority digest: `3a3eff76549ad5262f46`
- regression: `63/63 PASS`
- py_compile: PASS
- git diff --check: PASS
- push / merge / deploy: 금지, 사용자 명시 승인 전 실행하지 말 것.

### 슬로건 하위 실행정의 — BORDER COLLIE ORCHESTRATION
이 정의는 선택적 비유가 아니라 TAKY2 실행계약이다.

- ChatGPT / TAKY = `CHATGPT_TAKY_BORDER_COLLIE` — 오케스트레이터
- 구현 = `CODE_WRITER`
- 검증 = `CODEX`
- 독립검토 = `CLAUDE`
- USER = Key Owner / Final Authority

목적:
`GUIDE_TO_RESULT`

실행 루프:
`DETECT → CLASSIFY → REDIRECT → GUIDE → VERIFY → DELIVER`

Gate의 목적은 차단 자체가 아니다.
잘못된 길을 감지한 뒤 올바른 길로 재유도하여 검증된 결과물에 도달하게 하는 것이다.
기본 정책은 `REDIRECT_BEFORE_ESCALATE`.
USER에게 디버깅을 떠넘기지 않는다. `USER != DEBUGGER`.

런타임 강제상태:
- orchestration contract가 없으면 KEY Gate fail-closed
- 성공 preflight는 Border Collie / CODE_WRITER / CODEX / CLAUDE / USER 역할을 receipt에 바인딩
- recoverable Gate 실패는 가능하면 `REDIRECT + guidance.next_action`
- CODEX 역할 증명 없는 SUCCESS 검증 금지
- STRONG 검증의 independent review는 CLAUDE 역할 증명 필요
- Claude/Codex/Remote 실제 호출은 역할이 있다고 자동 실행하지 말고 Necessity Gate 통과 시에만 최소 호출

### 기존 구조 — 그대로 상속
- Beta = evidence freeze
- Alpha = whole-system semantic / ownership map
- TAKY2 = executable enforcement kernel
- 5 HARD GATE = KEY / CONTEXT / ROUTE / COST / DONE
- versioned Key + explicit KEY_AMEND
- receipt-bound executor / verifier / evidence / completion
- HMAC runtime + rollback anchor + CAS
- USER stop → ABANDONED
- route/transient exhaustion → Escalation Packet

### CLOSED — 재작업 금지
- AUTHORITY REBIND
- ACCOUNT ATTESTATION bridge contract
- EXECUTOR WRAPPER
- VERIFIER BRIDGE
- USER EVENT BRIDGE
- integration E2E kernel path
- Claude 공유문서 비교보완
- Border Collie orchestration authority binding + runtime role enforcement

### OPEN — 이것만 다음
`ACCOUNT TARGET BINDING`
- USER_STATED target = `HNS`
- 실제 central Google/family auth session evidence는 존재
- 하지만 `HNS ↔ authenticated family/session identity`의 authority-owned 명시 매핑은 아직 없음
- 임의 alias 추정 금지
- 외부 write는 매핑 전까지 fail-closed

다음 순서:
`ACCOUNT TARGET BINDING authority evidence 탐색 → 실제 attestation targeted E2E → 최종 회귀`

관련 기준:
- `TAKY2/BORDER_COLLIE_ORCHESTRATION_V1.md`
- `TAKY2/IMPLEMENTATION_STATUS_20261005.md`
- `TAKY2/CLAUDE_DRIVE_COMPARISON_PATCH_20261005.md`

Claude/Codex/Remote는 Necessity Check가 YES일 때만 최소 사용해.
같은 실패를 반복하지 말고, Border Collie처럼 잘못된 경로를 감지하면 스스로 다른 안전한 경로로 재유도해.
