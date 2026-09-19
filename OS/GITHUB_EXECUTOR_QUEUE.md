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

## Closure

Queue issue closure is allowed only after one of:
- task cancelled/not planned with explicit reason;
- executor result accepted and lifecycle advanced;
- smoke/test queue item explicitly marked as test evidence.

Closing an issue does not imply merge or deployment.
