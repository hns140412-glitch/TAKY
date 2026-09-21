# Hide & Seek Product Integrity / Rewrite Decision C2S

Date: 2026-09-21
Status: ACTIVE DECISION CANDIDATE ON GOVERNANCE BRANCH
Scope: TAKY product-validation correction + Hide & Seek rewrite disposition

## Source correction

Observed implementation status exposed a validation-system weakness:

- a large monolithic `app.js` accumulated UI, state, learning flow, memory logic, mission management and persistence responsibilities;
- many CI/browser checks passed while the product still lacked representative real-input, device, UI/UX and current cross-app integration evidence;
- implementation percentages were inflated by code/contracts/tests that did not directly increase the actual usable product path.

This is not treated as only a Hide & Seek local code defect. It is a TAKY validation false-convergence defect.

## Canonical correction

1. `CI PASS != PRODUCT COMPLETION`.
2. Documentation/C2S/handoff closure does not directly raise product completion.
3. Fixture-only browser E2E does not prove representative real-input completion.
4. Structural integrity is a first-class product gate.
5. When the execution architecture itself is causal, REWRITE/REBUILD must be evaluated explicitly rather than preserving the boundary by default.
6. Product completion reports must use the actual requirement inventory and separate CODED / CI / RUNTIME / DEVICE / RELEASE evidence.
7. Reusable validated assets are not averaged into the implementation rate of a new rewrite target.

Canonical owner: `MASTER/PRODUCT_IMPLEMENTATION_INTEGRITY_PROTOCOL.md` (TKY-PRODUCT-001).

## Hide & Seek disposition

Current V1 architecture status: `REWRITE_REQUIRED`.

Reason:
- monolithic execution ownership;
- broad shared mutable state;
- UI/domain/state coupling;
- change amplification;
- tests proving many isolated contracts without proving the same level of usable product completion;
- current integration evidence includes branch/runtime contracts but not a fully current real-device cross-app loop.

### Preserve
- Language Model truth gates;
- Language Evidence semantics;
- Ready Learning Basis adapter;
- Family OCR transport/evidence contract;
- Capture asset preservation semantics;
- Hide memory advisory contract;
- Ready Learning Engine / Planner ownership contract;
- representative regression fixtures and failure cases;
- canonical product decisions and C2S history.

### Replace
- monolithic `app.js` execution architecture;
- mixed screen/domain/state ownership;
- uncontrolled direct DOM/state coupling;
- stale/hard-coded integration endpoints as evidence of current integration;
- completion-rate logic that rewards internal artifact count.

### Rewrite target
`Hide & Seek Runtime V2`:
- app shell/router/store;
- mission domain;
- capture/review;
- learning-session engine;
- language-memory modules;
- memory/review advisory;
- integrations;
- persistence;
- UI screens/components.

## Validation reset

Legacy V1 reusable-asset maturity and V2 implementation completion are separate metrics.

Initial V2 status:
- reusable validated assets: substantial;
- target V2 implementation: NOT YET IMPLEMENTED except any explicitly migrated module;
- DEVICE_VERIFIED: 0;
- RELEASE_VERIFIED: 0.

No merge/deploy/release is authorized by this decision alone.
