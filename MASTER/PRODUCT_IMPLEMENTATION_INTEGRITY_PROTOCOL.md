# PRODUCT IMPLEMENTATION INTEGRITY PROTOCOL

ID: TKY-PRODUCT-001
Status: ACTIVE OWNER
Authority: TAKY / GRAND MASTER > this protocol > project implementation status reports
Date: 2026-09-21

## 0. Purpose

Prevent recurrence of product-completion inflation where code existence, CI success, isolated runtime checks, or documentation closure are reported as if they prove a usable product.

Core invariant:

`CODE EXISTS != PRODUCT WORKS != PRODUCT FEELS COMPLETE != DEVICE VERIFIED != RELEASE PASS`.

This protocol applies to material implementation/progress claims for interactive products, PWAs, apps, web apps, mobile experiences, and integrated learning products.

## 1. Product completion dimensions — HARD LOCK

A material product progress claim SHALL inspect the applicable dimensions separately:

1. FUNCTIONAL PATH — core user tasks actually execute end-to-end.
2. STRUCTURAL INTEGRITY — responsibilities, state ownership, coupling, change amplification and failure containment are acceptable for continued implementation.
3. UI/UX REALIZATION — screens, states, interaction feedback, responsive behavior and accessibility are actually implemented, not merely planned or mocked.
4. REPRESENTATIVE INPUT — tests include representative real/production-shaped input, not only fixtures or happy-path synthetic data.
5. INTEGRATION REALIZATION — cross-app/service/provider handoffs use the actual current contract/runtime path rather than stale, hard-coded, demo or historical endpoints.
6. RESILIENCE/RECOVERY — recoverable failures, restart/resume, stale state, offline/online boundaries and partial completion behave truthfully.
7. RUNTIME EVIDENCE — browser/runtime evidence exists for the current candidate.
8. DEVICE EVIDENCE — physical-device evidence exists when the claim depends on camera, permissions, keyboard, touch, install, PWA lifecycle, mobile browser behavior or other device-only behavior.
9. RELEASE EVIDENCE — deployment/release provenance exists only when release is claimed.

No single dimension SHALL substitute for another.

## 2. Claim ladder — HARD LOCK

Report at least:
- CODED
- CI_VERIFIED
- RUNTIME_VERIFIED
- DEVICE_VERIFIED
- RELEASE_VERIFIED where applicable

Also report a separate `PRODUCT_COMPLETION` value only when the denominator is the actual product requirement set, not test count, file count, gate count, or code volume.

`CI PASS != PRODUCT COMPLETION`.
`DOCUMENTATION CLOSURE != PRODUCT COMPLETION`.
`ARCHITECTURE CONTRACT PRESENT != STRUCTURAL INTEGRITY PASS`.
`FIXTURE E2E != REPRESENTATIVE REAL-INPUT E2E`.

## 3. Completion inflation prevention — HARD LOCK

The following SHALL NOT directly increase PRODUCT_COMPLETION by themselves:
- adding tests for already-existing behavior;
- adding governance/docs/C2S/handoff files;
- adding isolated adapters not connected to the active product path;
- passing CI against fixtures only;
- adding a contract without its consumer/producer round-trip;
- creating a UI shell without the underlying task path;
- creating code that is unreachable from the active app;
- splitting files without reducing ownership ambiguity or coupling.

These may increase confidence in a specific validation dimension, but not product completion unless actual user-facing capability is increased and connected.

## 4. Structural-integrity gate — HARD LOCK

Before continued feature growth on a materially evolving application, inspect:
- responsibility count per major module/file;
- state ownership and global/shared mutable state;
- UI rendering ownership;
- domain logic vs presentation coupling;
- cross-module dependency direction;
- change amplification: how many unrelated areas must change for one feature;
- test isolation and ability to validate modules independently;
- stale/hard-coded integration endpoints and environment coupling;
- migration/compatibility burden;
- error containment and recovery boundaries.

Large file size, line count or module count are heuristics only. They trigger inspection; they do not determine PASS/FAIL by themselves.

Structural-integrity FAIL when evidence shows the architecture itself is a material cause of:
- repeated regression;
- inability to isolate behavior;
- unsafe feature growth;
- misleading validation confidence;
- broad change amplification;
- product-path ambiguity;
- or test-only correctness that does not map cleanly to actual runtime ownership.

If structural integrity fails, new feature growth SHOULD pause except for bounded stabilization needed to preserve/recover behavior.

## 5. REPAIR vs REFACTOR vs REWRITE/REBUILD decision gate — HARD LOCK

When structural integrity is materially degraded, compare the minimum truthful options:

A. REPAIR — localized defect; current boundaries remain valid.
B. REFACTOR — behavior is sound, but responsibilities/boundaries need extraction or reorganization.
C. REWRITE/REBUILD — current boundaries/state model/execution model are themselves a root cause and preserving them would preserve the defect class.

A rewrite/rebuild decision SHALL identify:
- assets/contracts to preserve;
- behavior to preserve;
- state/data migration boundary;
- interfaces to re-establish;
- rollback/reference implementation;
- staged acceptance tests;
- cutover condition;
- what is intentionally not migrated.

`REWRITE != DISCARD EVERYTHING`.
A rewrite SHOULD preserve validated domain logic, evidence contracts, fixtures, test cases and canonical decisions while replacing the defective execution architecture.

## 6. User-experience completion gate — HARD LOCK

For interactive apps, product completion SHALL include representative screen/state evidence for:
- empty/loading/error/success/resume states;
- primary task path;
- keyboard/touch/camera/file interactions where applicable;
- responsive viewport behavior;
- navigation continuity;
- visible recovery from failure;
- state persistence across restart/return when required.

A headless or unit-test-complete system can still be product-incomplete.

## 7. Representative-input gate — HARD LOCK

When OCR, camera, uploaded files, free-form text, external provider output, or other variable input is central:
- fixture-only success is insufficient for real-input completion;
- preserve evidence provenance;
- classify unsupported/ambiguous input truthfully;
- do not convert provider/fixture confidence into product completion.

## 8. Integration freshness gate — HARD LOCK

Cross-app/service integration SHALL verify the active current path:
- current branch/HEAD or frozen candidate;
- current endpoint/configuration;
- producer/consumer contract;
- round-trip result;
- stale historical deployment URLs SHALL NOT count as current integration evidence.

## 9. Product completion matrix — HARD LOCK

Every material implementation/progress report SHALL maintain a matrix with at least:
- feature/domain;
- status: NOT_STARTED / SKELETON / PARTIAL / FUNCTIONAL / RUNTIME_VERIFIED / DEVICE_VERIFIED;
- evidence ref;
- user-facing path reachable: yes/no;
- representative input: yes/no/not applicable;
- known gaps.

Overall completion MUST be derived from the actual requirement inventory with higher weight on core user journeys and lower weight on secondary/internal capabilities.

## 10. Claim ceiling

If a critical product journey is not reachable end-to-end, overall PRODUCT_COMPLETION cannot be reported as near-complete.

If structural-integrity status is FAIL/REWRITE_REQUIRED, the report SHALL explicitly distinguish:
- reusable validated assets;
- current-product completion;
- target-rewrite completion.

Do not average reusable assets into the new product's implementation rate.

## 11. Relationship to existing TAKY rules

This protocol strengthens but does not replace:
- VALIDATION_RULES claim ladder;
- ENFORCEMENT_PROTOCOL;
- ENGINEERING_EXECUTION_PROFILE_PROTOCOL;
- UI_REFERENCE_PROTOCOL;
- TRACEABILITY_PROTOCOL;
- C2S.

It exists specifically to prevent `VALIDATION_SUCCESS -> PRODUCT_SUCCESS` false convergence.
