# 2026-09-21 Architecture Boundary Pre-Action Enforcement

Status: VALIDATION RECORD
Scope: Prevent recurrence of "canonical rule known but architecture proposal violates it" by forcing ownership/sharing boundary compilation before structure selection.

## Trigger

User identified a recurring TAKY failure mode: canonical standards exist, but the assistant can still propose a plausible architecture that violates those standards until the user points it out. The immediate witness case was proposing User/Family/Organization identity as a shared common layer before checking Work OS vs Learning OS authority boundaries.

## Root cause

The repository already had:
- `CANONICAL LOADED != CANONICAL APPLIED`;
- generic pre-action rule binding;
- an operational working model;
- an `ARCHITECTURE_CHANGE` execution profile.

But the architecture profile did not force a pre-structure representation of:
- semantic/authority owners;
- what may be shared vs must remain domain-owned;
- protected identity/role/permission boundaries;
- a counterexample that exposes authority leakage.

Therefore a solution-first shared layer could satisfy the old architecture profile while still violating known ownership semantics.

## Correction

Updated `TKY-ENGEXEC-001` architecture execution semantics to require:

`APPLICABLE OWNERS/RULES -> OWNER MAP -> SHARING CLASS -> PROTECTED BOUNDARIES -> COUNTEREXAMPLE -> STRUCTURE CANDIDATE -> INTEGRATION/REGRESSION`.

Sharing classes:
- `SHARED_TECHNICAL_PRIMITIVE`
- `DOMAIN_OWNED_SEMANTIC`
- `EXPLICIT_FEDERATION`
- `NOT_SHARED`

Added deterministic checks to `ENFORCEMENT/taky_gate.py`.

## Historical witness replay

Failure:
- Work OS organization roles and Learning OS parent/child/family roles are acknowledged as separately owned,
- but a common identity layer is still classified as a shared technical primitive,
- shared layer is not semantic-light,
- cross-domain authority sharing is implicit.

Expected: `AUTHORITY_BOUNDARY_VIOLATION`.

Compliant:
- technical transport/storage/sync may be shared;
- Work identity/roles remain Work-owned;
- Family/child identity/roles remain Learning-owned;
- optional same-human account linkage uses `EXPLICIT_FEDERATION`;
- PM authority does not become Parent authority.

Expected: clean PASS.

## Claim boundary

This change strengthens the TAKY-controlled repository execution path and replay gate.

It does NOT prove hosted ChatGPT automatically invokes the repository gate before every response. That runtime interception remains UNVERIFIED.

END
