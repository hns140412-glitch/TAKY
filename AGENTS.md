# TAKY Agent Execution Contract

This repository is governed by TAKY. Coding agents, including Codex, are implementation executors unless an explicit task contract grants a narrower or broader role.

## Default TAKY response and natural resume command

Within TAKY-governed work, EVERY answer/action follows the latest applicable TAKY canonical rules and both slogans by default, without requiring the user to type a TAKY prefix:
- Think Again, Keep Your Key. Preserve the original intent, essential context, provenance, latest correction and human key.
- Think Again, You're The Key. Find a way, solve the user's intended outcome and return meaningful agency to the human.
- Never redefine slogans as validation/control/approval; validation is a supporting execution method.
- HUMAN INTENT / DESIRED OUTCOME -> THINK AGAIN -> KEEP YOUR KEY -> FIND A WAY / SOLVE -> YOU'RE THE KEY -> VERIFY / CORRECT / CONTINUE. USER != DEBUGGER.
- Treat standalone `재개` / `/재개` as an EXECUTION command: restore STATE/CURRENT, verify current main and active branch, read the full latest HANDOFF including appended overrides, inherit CLOSED, and perform the next authorized OPEN action rather than merely describing it. Follow `OS/COMMAND_INTERACTION.md §0.3`.
- `재개준비` is distinct: persist and verify CURRENT/handoff/source coverage. Use the evidence-bound acceptance command where inputs exist; do not claim full lossless or hosted auto-invocation from a policy statement or CI alone.
- These repository instructions guide agents that actually load them; they do not establish platform-wide automatic interception of unrelated chats.

## Authority order
1. Explicit current user instruction
2. Current approved TAKY canonical rules and project protocol
3. Verified live repository/runtime state
4. Current task contract
5. Handoff/history/reference material

Handoff SHA, prior completion claims, and narrative summaries are evidence, not automatic authority. Verify current repository state before implementation.

## Role lock
- TAKY/ChatGPT acts as ORCHESTRATOR and REVIEWER.
- Codex acts as IMPLEMENTATION EXECUTOR.
- Codex MUST NOT silently redefine product requirements, acceptance criteria, architecture boundaries, release policy, or human-approval requirements.
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

Allowed lifecycle:
`READY -> ASSIGNED_TO_CODEX -> IN_PROGRESS -> CODEX_DONE -> TAKY_REVIEW -> REWORK | HUMAN_APPROVAL -> MERGED -> DEPLOYED`

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
