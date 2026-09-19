# TAKY CODEX TASK CONTRACT

Status: CANONICAL EXECUTION TEMPLATE
Purpose: Convert TAKY orchestration intent into a bounded, auditable implementation contract for Codex or another coding agent.

## Required task record

Every implementation task SHALL materialize the following fields before `IN_PROGRESS`:

```yaml
task_id: <unique id>
project: <project name>
repository: <owner/repo>
base_branch: <branch>
verified_base_head: <commit sha or explicitly UNVERIFIED>
role:
  orchestrator: TAKY
  executor: CODEX
objective: <single implementation objective>
working_model:
  primary_outcome: <what useful result must exist>
  priority_order:
    - <priority controlling trade-offs>
  protected_state:
    - <confirmed state that must survive>
  execution_implications:
    - <what the loaded rules change in this task>
  rule_to_execution:
    - rule_ref: <applicable canonical/project rule>
      effect: ACTION | CONSTRAINT | ACCEPTANCE | HOLD | NOT_APPLICABLE
      implication: <concrete execution consequence>
  next_action: <first executable action>
  stop_conditions:
    - <real blocker / approval / completion boundary>
source_of_truth:
  - current_user_instruction
  - taky_canonical_rules
  - verified_live_repository_state
change_scope:
  allowed:
    - <path/component>
  forbidden:
    - unrelated_refactor
    - silent_requirement_change
    - direct_production_deploy
investigate:
  - <suspected area>
acceptance_tests:
  - <observable condition>
acceptance_checks:
  - criterion: <exact acceptance_tests item>
    mode: PROFILE_CHECK | EVIDENCE_ONLY | MANUAL
validation:
  required:
    - diff_scope
    - build
    - relevant_tests
    - regression
  profile: <trusted repository-local validation profile>
  mobile_runtime_required: false
executor_automation:
  profile: <trusted executor profile>
  target_repository_local: true | false
human_approval:
  merge_required: true
  production_deploy_required: true
deliverables:
  - root_cause_or_rationale
  - changed_files
  - validation_commands
  - validation_results
  - unresolved_risks
  - commit_ref
requested_transition: CODEX_DONE
```

## Trusted executable evidence — HARD LOCK

Executor automation SHALL NOT execute arbitrary shell commands supplied by a queue issue, conversation, or external task payload.

Machine execution is bound to **repository-owned validation profiles**. A task may name a profile such as `READY_SET_STATIC_V1`; the target repository owns the actual commands/scripts behind that profile.

Acceptance items declare how evidence is expected:
- `PROFILE_CHECK` — verified by the trusted repository-local validation profile;
- `EVIDENCE_ONLY` — executor must return concrete evidence but TAKY does not execute task-supplied code;
- `MANUAL` — requires human/device review and remains UNVERIFIED until that evidence exists.

`TASK-SUPPLIED COMMAND != TRUSTED COMMAND`.
`NO AUTOMATED CHECK != PASS`.
`MANUAL CHECK != BLOCK PRODUCTIVE EXECUTION UNLESS MATERIAL TO THE CLAIM`.

This keeps automation productive without turning GitHub Issue content into a command-injection surface.

## Controlled-runtime materialization

In TAKY-controlled repository runtime, an authorized `SPECIFY_ACCEPTANCE -> CODEX` route SHOULD materialize this contract through `ENFORCEMENT/codex_task_contract_builder.py`.

Required sequence:
`RUNTIME WORKING MODEL -> AUTHORIZED ROUTE -> TASK CONTRACT BUILD -> CONTRACT VALIDATION -> CODEX EXECUTION`.

The builder SHALL NOT invent missing product scope, acceptance tests, repository target or authority. Missing material context blocks contract generation instead of silently filling placeholders.

Task lifecycle transitions are owned by `ENFORCEMENT/execution_state_engine.py`. Review failure transitions to `REWORK` only with concrete defect evidence; merge/deploy approval boundaries remain explicit.

## Hard locks

1. Missing material required fields => `TASK_CONTRACT_INCOMPLETE`.
1A. Applicable rules listed without a usable `working_model` / `rule_to_execution` mapping => preflight FAIL; reading/citing rules alone is not task readiness.
2. `verified_base_head: UNVERIFIED` is allowed only when execution cannot technically verify it; the completion report MUST preserve `LIVE_HEAD_UNVERIFIED` and MUST NOT imply freshness was proven.
3. Executor MUST NOT enlarge `change_scope.allowed` without orchestrator approval.
4. Acceptance criteria are controlled by the orchestrator/user authority chain, not silently rewritten by the executor.
5. `CODEX_DONE` means implementation work has been returned for review. It is never equivalent to `TAKY_PASS`, `MERGED`, or `DEPLOYED`.
6. Any failed review gate routes to `REWORK`, with failure evidence.
7. `MERGED` and `DEPLOYED` transitions requiring human approval are blocked without recoverable approval evidence.

## Required lifecycle

`READY -> ASSIGNED_TO_CODEX -> IN_PROGRESS -> CODEX_DONE -> TAKY_REVIEW -> REWORK | HUMAN_APPROVAL -> MERGED -> DEPLOYED`

Forbidden shortcuts include:
- `READY -> MERGED`
- `IN_PROGRESS -> DEPLOYED`
- `CODEX_DONE -> MERGED`
- `TAKY_REVIEW -> DEPLOYED` when approval is required but missing

## Executor transport boundary

Controlled TAKY runtime uses `MASTER/EXECUTOR_TRANSPORT_SCHEMA.json` and `ENFORCEMENT/executor_transport.py` to wrap a validated task contract in an integrity-bound dispatch envelope.

Built-in transports are `FILE_QUEUE` and `GITHUB_ISSUE_QUEUE`. `GITHUB_ISSUE_QUEUE` publishes the immutable dispatch envelope as an auditable GitHub Issue via the protocol in `OS/GITHUB_EXECUTOR_QUEUE.md`. Queue publication means the task is available to an executor adapter; it **does not** mean Codex accepted or executed it.

An external adapter must return a receipt bound to:
`task_id + provider + task_contract_sha256 + executor_run_id + status`.

Executor results are accepted only when they preserve the same task id, provider and contract hash. `ENFORCEMENT/executor_result_ingest.py` rejects mismatched/tampered returns before review.

The controlled return cycle is:
`DISPATCH ENVELOPE -> EXTERNAL EXECUTOR/ADAPTER -> RESULT INGEST -> TAKY REVIEW -> STATE TRANSITION`.

`ENFORCEMENT/executor_cycle.py` composes the last three stages.

`DISPATCH_READY != DISPATCHED`.
`DISPATCHED != EXECUTED`.
`EXECUTOR RESULT != TAKY PASS`.

## Executor return -> TAKY review loop

Codex/executor completion evidence SHALL use the shape owned by `MASTER/EXECUTOR_RESULT_SCHEMA.json`.

Controlled-runtime review path:
`CODEX_DONE EVIDENCE -> TAKY_REVIEW -> PASS ? HUMAN_APPROVAL : REWORK -> UPDATED TASK -> CODEX`.

`ENFORCEMENT/executor_review_loop.py` deterministically checks:
- task identity;
- changed-file scope;
- every acceptance criterion has explicit evidence;
- every required validation gate has explicit status/evidence;
- required mobile runtime evidence;
- scope deviations;
- blocking unresolved risks;
- commit reference.

A failed review does not ask the user to debug. It emits concrete defect evidence and a REWORK transition that can be returned to the executor.

This loop is an evidence/control implementation. It does not prove semantic correctness beyond the evidence supplied, and it does not itself invoke an external Codex service.

## Review gates

TAKY review SHALL evaluate, when applicable:
- requirement_match
- diff_scope
- static_checks
- build
- targeted_tests
- regression
- runtime_integration
- mobile_device_behavior
- release_boundary
- human_approval

A gate not run MUST be reported as `NOT_RUN`, `NOT_APPLICABLE`, or `UNVERIFIED`; absence of evidence is not PASS.
