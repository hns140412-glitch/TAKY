# TAKY BETA ARCHITECTURE PLAN — 2026-09-22

Status: BETA CANDIDATE / PLANNING ONLY

## 1. Architecture goal

Create a system that is:
- small at the core;
- explicit at boundaries;
- modular inside domains;
- contract-driven across domains;
- selective in validation;
- recoverable after failure;
- replaceable when tools/platforms change;
- easy to understand without loading the whole system.

## 2. Candidate shape

HUMAN
-> TAKY KERNEL
   -> WORK OS
   -> LEARNING OS
   -> FUTURE DOMAIN SYSTEMS
   -> SHARED TECHNICAL CAPABILITY

Apps/tools are consumers/executors, not implicit authorities.

## 3. TAKY Kernel candidate responsibilities

Keep only global concerns:
- authority
- ownership
- source/evidence
- intent/scope
- routing/orchestration
- validation policy
- recovery/continuity
- human approval
- evolution

Do not embed domain semantics.

## 4. Role separation

Every material component must distinguish:
- semantic owner
- implementation host
- runtime coordinator
- UI host
- consumer
- evidence/result receiver

## 5. Domain design

Prefer modular domain systems before service fragmentation.

Split into independent service only when:
- semantic ownership is independently stable;
- lifecycle differs;
- scaling/availability need differs;
- replacement value is material;
- contract can be defined clearly.

## 6. Runtime simplification

Target request flow:
REQUEST
-> recover minimal applicable context
-> resolve owner
-> choose route
-> execute
-> return evidence/result
-> targeted validation
-> update state/history

Avoid loading unrelated rules and running unrelated gates.

## 7. Failure handling

Every blocked path produces a failure fingerprint:
- operation
- target
- failure class
- evidence
- attempts
- last strategy
- changed condition

Retry only when condition or strategy changes.

## 8. Validation model

L1 FAST STRUCTURAL
- broken refs
- schema
- ownership uniqueness
- dependency direction
- stale current identity

L2 AFFECTED DOMAIN
- only changed domain and consumers

L3 INTEGRATION / RELEASE
- cross-domain
- runtime/browser
- deployment/device

## 9. State model

Separate:
- current state
- history
- evidence
- handoff
- project/app snapshots

Avoid one ever-growing global STATE document.

## 10. Deployment model

Development:
local/static/CI

Integration:
runtime/browser

Release:
frozen candidate
-> external-resource gate
-> deployment

Netlify is a release adapter, not a normal development loop.

## 11. Architecture review axes

Every candidate is compared on:
- complexity
- coupling
- change isolation
- context recovery cost
- validation cost
- runtime cost
- deployment cost
- failure recovery
- migration reversibility
- ownership clarity
- observability
- adaptability
