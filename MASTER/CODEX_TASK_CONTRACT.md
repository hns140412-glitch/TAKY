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
validation:
  required:
    - diff_scope
    - build
    - relevant_tests
    - regression
  mobile_runtime_required: false
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
