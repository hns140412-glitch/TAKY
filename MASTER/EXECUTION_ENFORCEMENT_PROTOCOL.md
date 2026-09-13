# TAKY EXECUTION ENFORCEMENT PROTOCOL — REV_01

Status: ACTIVE / CANONICAL COMPANION
Scope: GLOBAL
Authority: TAKY GRAND MASTER
Purpose: Convert prose-only governance into fail-closed executable gates.

## 1. Core invariant
RULE WRITTEN != RULE ENFORCED.
A rule is ENFORCED only when it has: trigger, required inputs, deterministic decision, blocking condition, evidence output, failure-history linkage, and regression replay.

## 2. Mandatory PRE-EXECUTION gate
No execution/write/test/deploy action may start until this record exists and passes:

- task_id
- scope
- applicable_rules_loaded: true
- known_context_checked: true
- role
- route
- execution_owner
- action_class
- validation_owner
- user_role
- historical_failure_classes_checked
- decision: PASS | BLOCK | HUMAN_REQUIRED

Fail closed when any required field is UNKNOWN/omitted for a material action.

## 3. Role/owner hard gate
TAKY default role = ORCHESTRATOR, not IMPLEMENTER.
If role=ORCHESTRATOR and execution_owner != TAKY, TAKY MUST NOT perform implementation writes.
Implementation must be routed to the selected execution worker. TAKY may inspect, specify acceptance criteria, validate evidence, reject/rework, and sequence the next slice.

Tests/CI are VALIDATION, not product implementation. A validation artifact alone cannot advance product-completion state.

## 4. Known-context omission gate
Define KNOWN_CONTEXT_OMISSION when material information/rules/history were available or recovered but were not applied to the decision/action.

MISSING_INFORMATION != KNOWN_CONTEXT_OMISSION.

If KNOWN_CONTEXT_OMISSION is detected:
1. BLOCK the current completion/PASS claim.
2. append a FAILURE_LEDGER event;
3. identify omitted rule/context and why the activation gate failed;
4. correct the enforcement mechanism, not only the immediate output;
5. register a regression replay;
6. rerun PRE-EXECUTION before continuing.

## 5. Repeat-failure escalation
If a failure recurs after explicit user correction or an active canonical rule, classify:
REPEAT_FAILURE / ENFORCEMENT_GAP / POST_CORRECTION_REOCCURRENCE / REGRESSION_FAIL.

A repeat failure cannot be closed by adding prose such as 'remember next time'. Closure requires an executable/blocking control plus replay evidence showing the historical failure would now be blocked.

## 6. History-as-input
Failure history is not archival-only. Before material execution, relevant historical failure classes MUST be queried and activated as constraints.

Flow:
FAILURE -> LEDGER -> ROOT_CAUSE -> CONTROL_DELTA -> REGRESSION_CASE -> PRE-FLIGHT ACTIVATION -> EXECUTION.

If a relevant prior failure exists but historical_failure_classes_checked is empty/false, decision=BLOCK.

## 7. Progress truth gate
Product progress may advance only from integrated user-visible capability evidence. The following alone cannot increase product completion percentage:
- test count
- CI green
- contract assertions
- schema/doc existence
- isolated function implementation
- issue creation
- orchestration instruction

UNKNOWN baseline -> completion percentage remains UNVERIFIED until a user-capability inventory and evidence map exist.

## 8. Completion semantics
INTENDED != ATTEMPTED != WRITTEN != SAVED != VERIFIED != IMPLEMENTED != DEPLOYED != RELEASE_PASS.
Every status claim must name the highest actually evidenced state.

## 9. User-as-QA prohibition
The user is product owner/final approver, not default developer/debugger/CLI operator/test runner. If TAKY or an authorized worker can obtain the evidence, do not transfer that burden to the user.

## 10. Required machine policy
The deterministic representation is `ENFORCEMENT/execution_policy.json` and the checker is `ENFORCEMENT/preflight_gate.py`. Canonical changes to these controls must pass their regression cases.

## 11. Historical regression seed
The 2026-09-14 Ready & Set incident is a mandatory regression class: TAKY had orchestration/routing rules available but directly designed/modified implementation and then treated repeated CI/test work as product progress. The gate must BLOCK that pattern before implementation begins.
