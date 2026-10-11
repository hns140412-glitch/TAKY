# TAKY 2.0 — SAVEY AI ECONOMY BALANCE CHECKPOINT — 2026-10-08

Status: LOCAL IMPLEMENTATION + SIGNED AUTHORITY REBIND + REGRESSION PASS
Authority: USER
Repo: D:\Git PWA\TAKY-2.0-ORCH
Branch: taky-2.0-orchestrator-2026-10-05

## User correction
SAVEY_AI_ECONOMY must optimize cost AFTER acceptance quality is protected.
It is not a blanket call blocker.

Resource treatment:
- Remote / local deterministic work: unmetered; do not suppress for cost.
- Claude / Codex subscription quota: scarce, but bounded useful calls may proceed without per-call USER approval.
- Paid API / real incremental spend: trusted USER approval required.
- Same-failure repetition / runaway agentic exploration remains blocked.

## Runtime changes
- EXTERNAL_OPTIONAL no longer requires approval merely because it is optional.
- Trusted billing_class: UNMETERED / SUBSCRIPTION_QUOTA / PAID_API.
- PAID_API requires exact-call trusted approval.
- Authority may still explicitly set require_optional_approval=true.
- dry_run paid_api must match trusted billing_class.
- review:external-model is bound to billing_class=SUBSCRIPTION_QUOTA.
- review:external-model is bound to execution_mode=PACKET_ONLY.

## PACKET_ONLY defense
Independent review packet is prepared by TAKY/Remote first.
Claude judgment route requires:
- bound stdin packet digest
- noninteractive --print
- empty --tools
- --permission-prompts none
- --no-session-persistence

Purpose: prevent one apparent review invocation from expanding into uncontrolled Claude Code agent/tool turns.

## Signed authority rebind
old digest: e839989ae44a73d7e12a
new digest: 1cf6c20a71b364b01e16
runtime: v52 -> staged v53 -> rebound v54
event_ref: chat:user:savey-balance-go:2026-10-08
KEY_AMEND=false
startup readback receipt rebound to new digest.

## Verification
- targeted enforcement + bridges: 126 passed + 35 subtests
- full TAKY2: 175 passed + 54 subtests
- compileall: PASS
- git diff --check: PASS (existing LF->CRLF warnings only)

## Live smoke
SAVEY economy: COST_OK
dry-run: DRY_RUN_OK
billing: SUBSCRIPTION_QUOTA

Preflight remains stopped at ROUTE because the existing external-model route ledger already exhausted its different-route budget through prior Codex ENVIRONMENT failures.
Do not erase or reset that history.
A future external independent review requires a legitimate route-budget decision/new materially different route.

V3 remains HOLD until actual independent concrete-diff review evidence exists.
No push / merge / deploy / Netlify / paid API.

## 2026-10-08 CORRECTIVE ROUTER / OPTIMIZER REFINEMENT

User correction: TAKY/SAVEY must guide and correct execution, not stop useful work merely because a policy threshold was reached.

Canonical behavior:
- ALLOW -> CORRECT_AND_RUN -> SHRINK_AND_RUN -> REROUTE_AND_RUN -> VERIFY.
- Same failed route/failure-class remains prohibited; choose a materially different route instead.
- Distinct-route budget is a SOFT optimization budget. Exceeding it no longer requires USER approval by itself.
- Transient retry cap returns REROUTE_REQUIRED to TAKY; USER is not the debugger.
- USER decision remains reserved for real authority/scope changes, irreversible actions, explicit USER stop, or real incremental paid spend.

SAVEY requirement classes:
- CAPABILITY_REQUIRED: tool/capability is required to create the accepted artifact (e.g. UI image/design generation, voice/TTS generation). Do not suppress merely for cost.
- QUALITY_REQUIRED: review/model/tool is needed to meet acceptance/verification quality. Optimize usage but preserve the quality floor.
- OPTIONAL_CONVENIENCE: may be reused, localized, shrunk or skipped when acceptance remains satisfied.

Resource handling remains:
- Remote/local: UNMETERED for cost policy.
- Claude/Codex subscription usage: SUBSCRIPTION_QUOTA; bounded useful calls are allowed, then minimized.
- PAID_API: real incremental spend requires trusted USER approval/budget authority.

Correction rule:
- excessive calls -> shrink to max sufficient count, then run;
- excessive model/effort -> lower only to acceptance-quality floor, then run;
- oversized context -> delta/packetize, then run;
- repeat work -> reuse accepted evidence/artifact, generate only missing delta;
- wrong tool/failed path -> materially different permitted route;
- never force LOCAL merely because external work is constrained when capability/quality is required.

Live no-model-call smoke:
- ROUTE = ROUTE_SOFT_BUDGET_EXCEEDED, allowed=true
- COST = COST_OK
- evidence includes requirement-class:QUALITY_REQUIRED + billing-class:SUBSCRIPTION_QUOTA
- preflight mode = CALL_ALLOWED

Verification:
- targeted enforcement/orchestrator: 99 passed + 20 subtests
- full TAKY2: 175 passed + 54 subtests
- compileall: PASS
- git diff --check: PASS (existing LF->CRLF warnings only)

## 2026-10-08 UI / VOICE CAPABILITY-REQUIRED CONCRETE REGRESSION

Concrete kernel cases added so the policy cannot regress into blanket call suppression:
- UI_IMAGE_GENERATION = CAPABILITY_REQUIRED
- TTS_AUDIO_GENERATION = CAPABILITY_REQUIRED
- capability-required work carries required-capability evidence through SAVEY COST decisions.
- missing required capability metadata => REROUTE_REQUIRED for internal correction, not USER debugging and not silent LOCAL downgrade.
- bounded subscription-quota UI/voice capability calls remain COST_OK.
- real PAID_API spend remains USER-authority gated.

Verification:
- targeted enforcement: 77 passed + 20 subtests
- full TAKY2: 177 passed + 54 subtests
- compileall: PASS
- git diff --check: PASS (existing LF->CRLF warnings only)

## 2026-10-08 DRY-RUN FRICTION REDUCTION + AUTHORITY V5

User correction: dry-run must not duplicate trusted policy fields or become a blocking ritual.

Runtime behavior:
- dry_run_plan is optional for bounded external calls.
- when omitted, TAKY auto-derives safe defaults from trusted action/call policy.
- derived by default: operations, batch_strategy, fallback, paid_api; expected_calls comes from call.
- explicit dry-run values are accepted when consistent; explicit conflicts are corrected/rerouted/rejected.
- dry-run no longer asks USER merely because a redundant no-approval call-count budget was exceeded; action max_calls/COST policy owns that decision.
- PACKET_ONLY remains strict only for packet binding + packet digest because those are non-redundant integrity requirements.
- evidence records AUTO_DERIVED/NORMALIZED and the derived fields.

Authority contract:
- orchestration contract version: 5
- SAVEY operating_mode: CORRECTIVE_ROUTER_OPTIMIZER
- priority: ACCEPTANCE_BEFORE_COST
- dry_run_policy.mode: AUTO_DERIVE_REDUNDANT_FIELDS
- signed authority digest: 29ffb90e216cb1b0bb55
- runtime v56
- rebind event: chat:user:corrective-router-dryrun-go:2026-10-08
- KEY_AMEND=false

Live smoke without dry_run_plan:
- allowed=true / CALL_ALLOWED
- ROUTE_SOFT_BUDGET_EXCEEDED (warning only)
- COST_OK
- DRY_RUN_OK
- evidence: dry-run-source:AUTO_DERIVED

Verification:
- targeted: 102 passed + 20 subtests
- full TAKY2: 178 passed + 54 subtests
- compileall: PASS
- git diff --check: PASS (NEW_CHAT LF->CRLF warning only)
