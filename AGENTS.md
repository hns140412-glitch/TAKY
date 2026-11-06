# TAKY Agent Execution Contract

This repository is governed by TAKY. Claude Code is the primary implementation executor when a delegated coding task is authorized; Codex is an independent reviewer or a usage-justified fallback executor under the canonical role owner. Neither agent gains authority from this activation document.

## Authority order
1. Explicit current user instruction
2. Current approved TAKY canonical rules and project protocol
3. Verified live repository/runtime state
4. Current task contract
5. Handoff/history/reference material

Handoff SHA, prior completion claims, and narrative summaries are evidence, not automatic authority. Verify current repository state before implementation.

## Shared Claude/Codex execution context (noncanonical)
Claude and Codex can reference the same source-verified candidate at `F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\03_HANDOFF\TAKY_ANTIGRAVITY_SHARED_AGENT_CONTEXT_CANDIDATE_20261012.json`; file existence and Drive sync do NOT prove either model actually received or read it. Before a material task, check it using `python "D:\Git PWA\TAKY\TOOLS\TAKY_SHARED_AGENT_CONTEXT_PROJECTION_CANDIDATE.py" --check`. Refresh if stale; canonical TAKY master/CURRENT rules outrank this view. Pending deliveries and cursor 0 are NOT model-received ACKs. No new Codex model call or native-panel takeover is authorized by this pointer.

## Role lock
Activation only: canonical semantic owner is `D:\Git PWA\TAKY\MASTER\AI_COLLABORATION_PROTOCOL.md` (TKY-AICOLLAB-001). Do not redefine role routing here.
- TAKY/ChatGPT acts as ORCHESTRATOR and REVIEWER.
- Claude Code is the primary code executor when a model is needed and subscription capacity is available; Codex is a conditional fallback executor or independent reviewer under TAKY's necessity/usage gates.
- No executor may silently redefine product requirements, acceptance criteria, architecture boundaries, release policy, or human-approval requirements.
- If implementation discovers a requirement conflict, stop the conflicting change and report the conflict; do not invent a product decision.

## Mandatory preflight before implementation
For every implementation task, record or verify:
- task_id
- repository and target branch
- current remote/base HEAD or otherwise verified current ref
- objective
- operational working model: primary outcome, priority order, protected state, rule-to-execution implications, next action, stop conditions
- allowed change scope
- forbidden/unrelated changes
- acceptance tests
- required validation commands
- human approval requirements

If any material field is missing, status is `TASK_CONTRACT_INCOMPLETE`; implementation completion MUST NOT be claimed.

Reading or citing TAKY/project files is not sufficient preflight. The applicable rules must be translated into concrete task effects before implementation begins.

## Change discipline
- Prefer the smallest sufficient diff.
- No unrelated refactor, formatting sweep, dependency upgrade, architecture rewrite, or production deployment unless explicitly authorized.
- Preserve existing behavior outside the approved scope.
- Never treat a successful edit as proof of runtime correctness.

## Required validation
Run every applicable gate available in the target project:
1. requirement/acceptance-criteria check
2. diff-scope check
3. lint/typecheck/build
4. relevant automated tests
5. regression checks
6. runtime/integration validation
7. mobile-device validation when the task is mobile-specific

A Codex self-report is evidence only. `CODEX_DONE` is not `TAKY_PASS`.

## State machine
In a TAKY-controlled repository runtime, lifecycle transitions SHOULD be executed/checked through `ENFORCEMENT/execution_state_engine.py` rather than inferred from narration.

Allowed lifecycle (runtime compatibility names):
`READY -> ASSIGNED_TO_CODEX -> IN_PROGRESS -> CODEX_DONE -> TAKY_REVIEW -> REWORK | HUMAN_APPROVAL -> MERGED -> DEPLOYED`.
The `ASSIGNED_TO_CODEX` / `CODEX_DONE` tokens are legacy runtime aliases for neutral `ASSIGNED_TO_EXECUTOR` / `EXECUTOR_DONE`; actual Claude/Codex identity is recorded separately and these aliases do not select an executor.

Rules:
- `CODEX_DONE -> MERGED` is forbidden.
- `CODEX_DONE -> DEPLOYED` is forbidden.
- Failed TAKY review MUST transition to `REWORK` with concrete defect evidence and updated acceptance criteria when needed.
- Merge or production deployment requiring human approval MUST remain blocked until recoverable approval evidence exists.

## Completion report
Every implementation completion report MUST include:
- root cause / implementation rationale
- files changed
- scope deviations, if any
- validation commands actually run
- pass/fail results
- runtime/mobile validation status
- unresolved risks
- commit/ref produced
- requested next transition

Do not claim `PASS`, `MERGED`, `DEPLOYED`, or `recurrence prevented` without evidence for the corresponding gate.
