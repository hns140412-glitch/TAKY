# TAKY Agent Execution Contract

This repository is governed by TAKY. Coding agents, including Codex, are implementation executors unless an explicit task contract grants a narrower or broader role.

## Authority order
1. Explicit current user instruction
2. Current approved TAKY canonical rules and project protocol
3. Verified live repository/runtime state
4. Current task contract
5. Handoff/history/reference material

Handoff SHA, prior completion claims, and narrative summaries are evidence, not automatic authority. Verify current repository state before implementation.

## Role lock
Activation only. Semantic owner: MASTER/AI_COLLABORATION_PROTOCOL.md (TKY-AICOLLAB-001). Do not redefine role/routing semantics here.
- Apply the executor role assigned by TAKY under TKY-AICOLLAB-001.
- Economic routing is owned by OS/SAVEY_AI_ECONOMY.md (TKY-SAVEY-001).
- Executor guardrails: follow MASTER/AI_COLLABORATION_PROTOCOL.md §4 (TKY-AICOLLAB-001).

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

Canonical lifecycle semantics are executor-neutral:
`READY -> ASSIGNED_TO_EXECUTOR -> IN_PROGRESS -> EXECUTOR_DONE -> TAKY_REVIEW -> REWORK | HUMAN_APPROVAL -> MERGED -> DEPLOYED`.

For backward compatibility, controlled runtime currently accepts `ASSIGNED_TO_CODEX` as the internal alias of `ASSIGNED_TO_EXECUTOR` and `CODEX_DONE` as the internal alias of `EXECUTOR_DONE`. Executor identity (Claude/Codex/etc.) is recorded separately and must not redefine lifecycle semantics.

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

## Shared-log shortcut
Activation only: follow MASTER/AI_COLLABORATION_PROTOCOL.md §5–§6 (TKY-AICOLLAB-001). Do not redefine resume/log semantics here.
