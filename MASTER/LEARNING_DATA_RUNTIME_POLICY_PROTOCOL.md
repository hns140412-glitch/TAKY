# LEARNING DATA RUNTIME POLICY PROTOCOL

Status: IMPLEMENTATION_CANDIDATE / POLICY_GATE_ONLY
Owner: TAKY Learning Domain governance
Source authority: LEARNING_DATA_COMPLETENESS_MATRIX_2026-09-23_V49
Human approval scope: POLICY_GATE_IMPLEMENTATION_ONLY

## Core
`CONTRACT WRITTEN != CONTRACT ENFORCED`
`PROVENANCE PRESENT != BEHAVIOR AUTHORIZED`
`FACTUAL EVIDENCE VALID != PEDAGOGICAL USE AUTHORIZED`
`HOLD != WARNING`
`UNKNOWN POLICY = DENY`

This protocol is an executable projection of current Learning Data readiness. It is not a new pedagogical authority and it does not mutate the V49 matrix.

## Ownership
- Learning-data authorization semantics: TAKY Learning Domain governance.
- App behavior semantics remain app-owned.
- Planner date authority remains Ready-owned.
- Hide memory remains advisory.
- Snap authorship/truth semantics remain Snap-owned.
- SHARED/runtime remains semantic-light and may transport decision metadata only.

## Authorization classes
- READY_WITH_GUARDS: allowed only for explicitly listed behavior and only while guards remain true.
- CONDITIONAL: allowed only when required provenance/context conditions are satisfied.
- HOLD: runtime execution denied.

## Fail-closed
Unknown function, unknown consumer, missing policy, missing required provenance/context, authority mismatch, forbidden behavior, cannot_claim collision, or missing required human review MUST deny.

## Human approval
Approval is scope- and policy-version-bound. A global boolean is invalid. Approval for one consumer/function/version does not transfer to another.

## Runtime integration
Consumers call the policy adapter before consuming a governed Learning Data function. Adapters may translate ALLOW/ALLOW_CONDITIONAL into app-owned behavior. Adapters may not weaken DENY/HOLD or remove cannot_claim.

## Shared transport
Existing event-envelope may carry immutable policy decision metadata in payload/reference. Event transport is not policy authority.

## Current locked HOLD
- LE-H01 prerequisite causal routing
- LE-H02 K-basics numeric threshold automation
- LE-H03 Almaengi product-specific critical-evaluation routing

## Deployment
This implementation scope excludes feature activation, merge to production branches, Netlify deployment, and production rollout.
