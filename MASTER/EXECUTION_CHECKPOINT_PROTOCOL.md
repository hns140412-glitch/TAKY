# TAKY ATOMIC CURRENT CHECKPOINT PROTOCOL

Status: REV_00 / ACTIVE OPERATIONAL PROTOCOL
Rule ID: TKY-CHECKPOINT-001
Purpose: Persist the smallest sufficient current execution state immediately after each independently meaningful atomic work unit so a stalled or terminated chat can resume without replaying the prior conversation.
Authority: TAKY / GRAND MASTER > this protocol > lower-layer checkpoint specializations.
Related: `STATE.md`, `MASTER/CONVERSATION_CONTINUITY_PROTOCOL.md`, `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md`, `MASTER/HANDOFF_PROTOCOL.md`.

## 0. Core doctrine — HARD LOCK

> **DEEP MEMORY — LIGHT EXECUTION.**
> Durable history stays deep; the active resume surface stays small.

`CHAT != SOURCE OF TRUTH`
`BATCH CLOSED -> CURRENT WRITTEN -> NEXT BATCH`
`HANDOFF != REQUIRED FOR EVERY SMALL RESUME`
`CURRENT != CANONICAL OWNER`
`CURRENT = VERIFIED RESUME POINTER`

A material atomic unit SHALL NOT be treated as safely closed until its current checkpoint is persisted.

## 1. Atomic checkpoint boundary

An atomic unit is the smallest independently meaningful piece of work whose result changes what should happen next.

Examples:
- one CAP batch classified;
- one implementation slice completed and focused tests recorded;
- one mining candidate family closed;
- one review decision set resolved;
- one source-ingest packet verified.

The checkpoint MUST be written before starting the next atomic unit when any of these changed:
- DONE scope;
- OPEN/FRONTIER;
- correction;
- source-family split/merge;
- next action;
- authority/source pointer;
- blocker;
- acceptance/test state.

Do not wait for conversation end or a large milestone.

## 2. Two-surface persistence model

### CURRENT
Mutable, smallest sufficient resume pointer.

Default repository path:
`CURRENT/<namespace>/<task_id>.json`

Contains only the state needed to continue safely:
- task / namespace;
- just-closed atomic unit;
- status;
- concise DONE;
- explicit OPEN;
- NEXT;
- material corrections;
- source/evidence pointers;
- update timestamp;
- optional parent checkpoint hash/reference;
- for material pipeline stages: input/output revision or hash, applied contract/version, checks/evidence, dependency/failure class, next route, side effects/rollback and approval scope when relevant.
- when the checkpoint represents a human-approval boundary, `approval_binding` SHALL bind the requested action to `action_kind + action_payload_hash`; resume/consumption evidence must match that exact stored binding and the current task/action request.
- checkpoint CURRENT mutation SHALL be serialized; approval completion uses compare-and-swap against the guarded checkpoint hash so a stale consumer cannot overwrite a newer CURRENT.
- HISTORY append uses create-once immutable writes; a concurrent conflicting history identity fails closed before CURRENT advances.

### HISTORY
Immutable minimal checkpoint evidence.

Default repository path:
`HISTORY/CHECKPOINTS/<namespace>/<task_id>/<timestamp>.json`

History is append-only evidence, not the default resume surface.

`CURRENT = WHERE TO CONTINUE`
`HISTORY = HOW WE GOT HERE WHEN NEEDED`

## 2.1 Durable side-effect ledger — HARD LOCK

Checkpoint progress and external side effects are related but not interchangeable.

For a material action that can create remote/public/irreversible or otherwise non-idempotent effects (for example send, publish, delete, merge, deploy, permission/account mutation, external write), maintain a side-effect ledger record before resume/retry decisions.

Deterministic implementation:
`ENFORCEMENT/side_effect_ledger.py`.

Minimum identity:
- `effect_id`;
- `task_id / namespace`;
- `action_kind`;
- exact `action_payload_hash`;
- `idempotency_key`;
- `state_schema_version`;
- `target_ref`;
- `execution_status`;
- `replay_policy`;
- before/after state evidence or external receipt when available;
- approval reference when required.

Replay policies:
- `FORBID` — a recorded applied/verified effect blocks duplicate execution;
- `IDEMPOTENT_RETRY` — retry is allowed only for the exact same effect identity/payload;
- `VERIFY_THEN_RETRY` — an ambiguous/applied effect must be verified before retry;
- `COMPENSATE` — compensation/rollback is required before retry.

`APPLYING` is an indeterminate state and fails closed until verified.
A changed payload/idempotency key/action kind/target is not a retry of the same effect and cannot reuse the old ledger identity.
Side-effect lifecycle/replay policy is monotonic: an applied/verified effect cannot be rewritten back to PLANNED or relaxed to a weaker replay policy. COMPENSATED requires the COMPENSATE policy plus concrete compensation evidence.
CURRENT corruption or missing CURRENT with surviving HISTORY fails closed; it SHALL NOT be treated as first execution.
Every final execution-allowing decision is protected by an exclusive durable claim so concurrent callers cannot both receive authorization for the same effect attempt. A controlled runtime may perform an earlier non-reserving side-effect eligibility check, but it SHALL create the durable claim only after all non-mutating admission/validation gates pass. If a later approval-finalization conflict prevents authorization, a just-created reservation must be explicitly released or otherwise reconciled before retry.

Controlled runtimes may bind `side_effect_guard` in `runtime_orchestrator.py`; eligibility checking SHALL precede execution and final reservation SHALL precede the material side effect.

`CHECKPOINT SAVED != SIDE EFFECT SAFE TO REPLAY`.
`RESUME != REPEAT EXTERNAL ACTION`.

## 3. Required execution loop

For material multi-step work:

`LOAD CURRENT -> CHECK SIDE-EFFECT LEDGER WHEN APPLICABLE -> EXECUTE ATOMIC UNIT -> VERIFY DELTA -> WRITE CURRENT -> APPEND MINIMAL HISTORY -> CONTINUE`

The write occurs before the next unit.

If persistence fails:
- do not silently proceed as if the unit were durable;
- preserve the completed result in the active response/tool evidence;
- classify `CHECKPOINT_PERSISTENCE_BLOCKED`;
- retry by another authorized path when available.

## 4. New-chat resume

Default new-chat sequence:

`STATE -> APPLICABLE OWNER -> CURRENT -> OPEN/NEXT -> CONTINUE`

A full Handoff is not required when CURRENT is sufficient and verified.

Use Handoff when:
- ownership/executor changes;
- a large project boundary changes;
- a portable self-contained package is requested;
- CURRENT cannot safely represent required context.

## 5. Anti-loop rules

- CLOSED units are not re-opened without new contradictory evidence.
- Do not re-read already verified sources solely because a new chat started.
- Do not regenerate a Handoff after every atomic unit.
- Do not copy raw source bodies into CURRENT.
- Do not turn CURRENT into a second C2S archive.
- If a correction changes prior grouping/classification, record the correction and affected pointer; do not erase history.

## 6. Claim boundary

Repository utilities can enforce checkpoint creation and pre-next-unit freshness in controlled runtimes.

Hosted ChatGPT automatic invocation is not proven. Therefore:
- canonical behavior requires checkpointing;
- repository-controlled execution can mechanically enforce it;
- hosted chat must use available connectors/tools to persist the checkpoint when performing durable TAKY work;
- absence of platform interception MUST NOT be described as automatic enforcement.

## 7. Minimum record

Required fields are defined by `MASTER/EXECUTION_CHECKPOINT_SCHEMA.json`.

Recommended compact example:

```json
{
  "checkpoint_version": "1.0",
  "task_id": "DATA_UTILIZATION_INDEXING",
  "namespace": "DATA",
  "atomic_unit": "CAP-031-040",
  "status": "RUNNING",
  "done": ["CAP-031~040 reviewed"],
  "open": ["CAP-038 internal split final pointer write"],
  "next": "CAP-041~050",
  "corrections": ["TIME_GROUP != SOURCE_FAMILY"],
  "source_refs": ["DATA_SOURCE_INDEX"],
  "updated_at": "2026-09-24T14:00:00+09:00"
}
```

END
