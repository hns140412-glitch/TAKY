# TAKY C2S RUNTIME ACTIVATION

Status: REV_00 / CANONICAL OPERATIONAL SPECIALIZATION
Owner semantics: TKY-C2S-001 remains owned by `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md`.
Role: Define when conversational system compilation must be activated at runtime/command-routing surfaces.

## 0. Activation rule

C2S is **conditional**, not an always-on heavy process.

Set `conversation_system_compile_required = true` when the current work materially:
- creates or changes TAKY canonical governance;
- creates or changes DOMAIN/PROJECT/OS standards from conversation-derived decisions;
- claims "타키 반영 / 타키 업데이트 / 기준 반영 / 회사 기준 반영" or equivalent;
- closes a material system-building conversation whose unresolved important deltas would otherwise be lost;
- performs a reconstruction/backfill whose output is intended to become durable system knowledge.

Do **not** require C2S merely because:
- the user asks an ordinary factual question;
- the user requests RAW transcript preservation only;
- a non-system artifact is drafted with no durable rule/standard change;
- `ㄱ` appears in isolation during an unrelated task.

## 1. Command routing

### 타키 반영 / 타키 업데이트 / 기준 반영
`RECOVER APPLICABLE SOURCE -> C2S ATOMIZE/LINK -> COMPARE -> AUTHORIZED WRITE -> COVERAGE CLOSURE -> REVERSE RECONSTRUCTION -> HISTORY`.

A prose-only "반영했습니다" without the durable write/evidence required by the request is not enough.


### 타키 기준 / 최신 타키 기준 / 프로젝트 기준 재개
Before implementation or validation, identify the active project and load its project context manifest when one exists.

Required chain:
`PROJECT IDENTIFY -> PROJECT CONTEXT MANIFEST -> REQUIRED OWNERS/CORRECTIONS/OPEN-CONFLICT -> TARGETED L2/L3 RECOVERY IF NEEDED -> ENFORCEMENT/project_context_validator.py -> EXECUTE`.

For manifest-controlled project work:
`REQUIRED_CONTEXT_MISSING > 0 = CONTEXT_GATE FAIL`.

A context-gate FAIL allows only recovery/repair work; it does not allow implementation claims that depend on the missing context.

NotebookLM remains L2 `REFERENCE_ONLY / EVIDENCE_ASSIST`; any historical claim used to change canonical state requires raw-source recheck under TKY-NBLM-001/TKY-C2S-001.

### ㄱ / 계속 / 진행
Delegated continuation inherits the active execution contract.
If C2S was already required by the active contract, it remains required until the relevant compile/write/coverage stop condition.
If C2S was not required, `ㄱ` does not activate it by itself.

### /대화전체보존
Preserve accessible USER↔Assistant conversation evidence in order.
`RAW PRESERVATION != C2S CANONICAL PROMOTION`.
The preserved transcript may later feed C2S, but transcript preservation alone does not adopt every statement as a system rule.

### 대화 종료
Before Handoff, detect material uncompiled system-building deltas.
If such deltas exist, perform incremental C2S classification/ledgering to preserve destination/status/lineage.
Do not auto-promote OPEN/FRONTIER/CONFLICT items to canonical standards merely because the conversation is ending.

### /재개
Recover unresolved C2S atoms, OPEN/CONFLICT/FRONTIER state, latest correction lineage, and skeleton-growth gaps when relevant to the resumed work.
Resume from the highest-value unresolved executable item, not from a lossy summary.

## 2. Repository-executable bridge

Preferred controlled-runtime chain for conversation-derived governance writes:

`USER REQUEST -> EXECUTION CONTRACT -> C2S ACTIVATION DECISION -> PRE-FLIGHT RECORD -> C2S COVERAGE LEDGER -> ENFORCEMENT/c2s_preflight_bridge.py -> WRITE/REPORT`.

Example:
```bash
python ENFORCEMENT/c2s_preflight_bridge.py \
  --record <preflight.json> \
  --coverage-record <coverage-ledger.json> \
  --repo-root .
```

When `conversation_system_compile_required=true`, missing or failing coverage blocks the bridge.

## 3. Claim boundary

`REPOSITORY C2S BRIDGE EXISTS != HOSTED CHATGPT AUTO-INVOCATION`.

Until a trusted hosted runtime interception/invocation path is independently evidenced, live automatic invocation remains `UNVERIFIED`.
The user-facing system must not claim universal automatic enforcement from repository existence alone.

END
