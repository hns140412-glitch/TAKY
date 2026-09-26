# TAKY GITHUB EXECUTOR QUEUE PROTOCOL

Status: CONTROLLED TRANSPORT ADAPTER
Owner: `MASTER/CODEX_TASK_CONTRACT.md`
Purpose: Use GitHub Issues as an auditable task queue / receipt channel when a direct executor API is unavailable.

## Boundary

GitHub Issue publication proves only that a dispatch envelope was published to the queue.

`ISSUE CREATED != EXECUTOR ACCEPTED`
`EXECUTOR RECEIPT != IMPLEMENTATION COMPLETE`
`RESULT COMMENT != TAKY PASS`

## Dispatch

The authorized orchestrator:
1. creates a validated task contract;
2. wraps it with `MASTER/EXECUTOR_TRANSPORT_SCHEMA.json`;
3. serializes it through `ENFORCEMENT/github_issue_executor_queue.py`;
4. creates one GitHub Issue containing the immutable machine dispatch block;
5. records repository + issue number + issue URL as queue evidence.

Expected label: `taky-executor-queue` when available.

## Receipt

An executor/bridge posts a comment containing:

`<!-- TAKY_EXECUTOR_RECEIPT_JSON_BEGIN -->`

JSON with at least:
- `task_id`
- `provider`
- `task_contract_sha256`
- `executor_run_id`
- `status: ACCEPTED | STARTED | COMPLETED`

`<!-- TAKY_EXECUTOR_RECEIPT_JSON_END -->`

Receipt validation remains owned by `ENFORCEMENT/executor_transport.py`.

## Executor Liveness / Recovery

An `ACCEPTED` receipt is execution ownership evidence, not permanent ownership.

For provider-bound adapters that expose run/job status, the adapter must distinguish:
- active run: keep ownership; do not dispatch a duplicate executor;
- terminal failed/cancelled/timed-out run with materialization confirmed not started: controlled reclaim may create a new attempt;
- successful run without a RESULT: reconcile missing result evidence before any replay;
- run where materialization may have started: reconcile external side effects before any replay;
- provider liveness unknown: fail closed; do not blind-takeover.

Recovery receipts preserve `attempt` and `recovery_of_run_id` so task lineage remains auditable.

`CONCURRENCY != LIVENESS`.
`RECEIPT != PERMANENT LEASE`.
`DEAD WORKER != BLIND RETRY`.

Executor recovery must not bypass `SIDE_EFFECT_RETRY_CONTRACT`. If an earlier attempt may have produced an external side effect, effect reconciliation remains mandatory before replay.

The Ready & Set GitHub/Codex adapter implements this contract by resolving GitHub Actions run/job state before selecting a previously accepted task.

## Result

Completion is posted as a second machine block:

`<!-- TAKY_EXECUTOR_RESULT_JSON_BEGIN -->`

JSON matching the executor-result contract:
- `task_id`
- `provider`
- `task_contract_sha256`
- `completion_report`

`<!-- TAKY_EXECUTOR_RESULT_JSON_END -->`

The result then flows through:
`executor_result_ingest.py -> executor_review_loop.py -> execution_state_engine.py`.

## Rework

If TAKY review returns REWORK, the orchestrator posts a new dispatch or explicit rework comment bound to the same task lineage and updated contract hash. Silent mutation of the original machine dispatch block is forbidden.

## Event + Poll Fallback

Primary consumer workflow:
`.github/workflows/taky-executor-queue-consumer.yml`

Fallback poller:
`.github/workflows/taky-executor-queue-poller.yml`

Some GitHub mutations created by automation credentials may not recursively trigger another workflow event. Therefore queue reliability does not depend on the issue/comment event alone.

The fallback poller scans open TAKY queue issues every 15 minutes and processes only unacknowledged machine blocks.

Idempotency markers:
- `<!-- TAKY_QUEUE_ISSUE_ACK -->` — queue issue already evaluated.
- `<!-- TAKY_QUEUE_SOURCE_COMMENT:<id> -->` — executor receipt/result comment already consumed.

`EVENT MISSED != QUEUE LOST`.
`POLL RETRY != DUPLICATE REVIEW`.

The poller does not create executor receipts or results. It only consumes evidence that already exists in the queue.

## Closure

Queue issue closure is allowed only after one of:
- task cancelled/not planned with explicit reason;
- executor result accepted and lifecycle advanced;
- smoke/test queue item explicitly marked as test evidence.

Closing an issue does not imply merge or deployment.
