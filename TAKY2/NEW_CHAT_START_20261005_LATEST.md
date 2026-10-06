# TAKY 2.0 — NEW CHAT START / SHEPHERDING COOPERATIVE LATEST

## COPY / RESUME
최신 TAKY 2.0 별도 브랜치 기준으로 재개해.

먼저 `TAKY2/NEW_CHAT_START_20261005_LATEST.md`와 현재 HEAD만 확인하고, CLOSED는 그대로 상속해. 전체 Beta/Alpha 재감사·전제문서 반복 재독·이미 끝난 Gate 재구현은 하지 말고 OPEN만 진행해.

현재 로컬 authority:
- repo: `D:\Git PWA\TAKY-2.0-ORCH`
- branch: `taky-2.0-orchestrator-2026-10-05`
- canonical promotion: LOCAL COMMIT authority; 현재 SHA는 `git rev-parse HEAD`로 확인
- additional/ongoing worktree changes may remain; diff 검토 없이 reset/checkout로 버리지 말 것
- authority digest: `e92831fc4e23ff21c979`
- runtime version: `9`
- regression: `pytest 93 passed + 36 subtests`
- systemwide canonical: `TAKY2/TAKY_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL_20261006.md`
- py_compile: PASS
- git diff --check: PASS
- push / merge / deploy: 금지, 사용자 명시 승인 전 실행하지 말 것.

### 슬로건 하위 실행정의 — SHEPHERDING COOPERATIVE EXECUTION MODEL
이 정의는 선택적 비유가 아니라 TAKY2 실행계약이다.

- TAKY = 최상위 시스템 / 거버넌스 프레임워크
- ChatGPT = `CHATGPT_LEAD_ORCHESTRATOR` — TAKY 하위 실행모델의 Lead Orchestrator
- 구현 역할 = `CODE_WRITER` (역할 범주; 실제 implementer actor는 TASK_FIT_NECESSITY로 작업별 배정)
- 검증 = `CODEX`
- 독립검토 = `CLAUDE`
- USER = Key Owner / Final Authority

목적:
`GUIDE_TO_RESULT`

실행 루프:
`OBSERVE → CLASSIFY → ASSIGN → EXECUTE → CROSS_CHECK → REDIRECT → VERIFY → DELIVER`

Gate의 목적은 차단 자체가 아니다.
잘못된 길을 감지한 뒤 올바른 길로 재유도하여 검증된 결과물에 도달하게 하는 것이다.
기본 정책은 `REDIRECT_BEFORE_ESCALATE`.
USER에게 디버깅을 떠넘기지 않는다. `USER != DEBUGGER`.

런타임 강제상태:
- orchestration contract가 없으면 KEY Gate fail-closed
- 성공 preflight는 TAKY system relation / ChatGPT Lead Orchestrator / CODE_WRITER / CODEX / CLAUDE / USER 역할을 receipt에 바인딩
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
- ACCOUNT TARGET BINDING — `FIRST_AUTH_RUNTIME` implementation
- EXECUTOR WRAPPER
- VERIFIER BRIDGE
- USER EVENT BRIDGE
- integration E2E kernel path
- fixture targeted E2E: `null attestation → first-auth bind → external-write preflight`
- Claude 공유문서 비교보완
- TAKY shepherding cooperative execution authority binding + runtime role enforcement

ACCOUNT TARGET BINDING 확정 방식:
- USER_STATED logical target = `HNS`
- 사전 `HNS ↔ family_id` 고정표를 만들지 않는다
- 실제 사용 중 검증된 `/api/family/session`의 `identity_provider + principal_id + family_id + self_member_id`를 최초 1회 runtime binding
- 동일 identity 재로그인은 session/evidence 갱신 허용
- 다른 principal/family/member로 변하면 fail-closed
- Google Drive profile id를 OIDC principal로 추정 금지
- 첫 인증 전 external write는 fail-closed

### OPEN — RUNTIME ONLY
`REAL HNS FIRST-AUTH SESSION / DEVICE E2E`

이 항목은 실제 사용/로그인 시 자연스럽게 수행한다. USER에게 token/ID 복사나 디버깅을 요구하지 않는다.
실제 첫 인증 시:
`verified /api/family/session → FIRST_AUTH_RUNTIME bind → targeted preflight → runtime evidence → final regression`

evidence: `TAKY2/ACCOUNT_TARGET_BINDING_EVIDENCE_20261006.md`

관련 기준:
- `TAKY2/SHEPHERDING_COOPERATIVE_EXECUTION_MODEL_V1.md`
- `TAKY2/IMPLEMENTATION_STATUS_20261005.md`
- `TAKY2/CLAUDE_DRIVE_COMPARISON_PATCH_20261005.md`

Claude/Codex/Remote는 Necessity Check가 YES일 때만 최소 사용해.
같은 실패를 반복하지 말고, Shepherding Cooperative Execution Model에 따라 잘못된 경로를 감지하면 역할을 재배치하고 다른 안전한 경로로 재유도해.
