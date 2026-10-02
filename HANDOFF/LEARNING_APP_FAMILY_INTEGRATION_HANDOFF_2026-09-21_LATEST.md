# LEARNING APP FAMILY — INTEGRATION HANDOFF — 2026-10-02 CURRENT

## Resume command
최신 TAKY 기준으로 Learning App Family 통합 작업을 재개해.

## Authority note
This handoff supersedes the stale 2026-09-21 live-baseline assumptions while preserving their history.
Do not restore deprecated READY_LEARNING_CONTEXT_V1 as a parallel authority.

## Reconciled status

### CLOSED
- LAF-INT-002: Ready runtime maps HELP_NEEDED -> WAITING_FOR_PARENT and keeps BLOCKED distinct.
- Core Decision -> Planner dated TODO -> Ready execution path is implemented and regression-tested.
- Ready legacy embedded learner logic extraction is APPLIED; compatibility-only logic is quarantined and is not default authority.

### SUPERSEDED
- LAF-INT-001: READY_LEARNING_CONTEXT_V1 gap.
  - Replaced by current central Learning Decision / observation handoff contracts plus shared runtime boundaries.
  - Current Ready evidence includes ready-central-learning-decision-intake-v01.js, ready-central-intent-to-planner-v01.js and central-learning-roundtrip tests.
  - Hide preserves Learning Engine review-need and Planner dated-allocation ownership.
  - Do not create a duplicate READY_LEARNING_CONTEXT_V1 contract.

### OPEN
- LAF-INT-003: Snap legacy active branch reconciliation.
  - branch: taky/snap-pop-implementation-2026-09-20
  - latest verified relation to main: +1112 / -17 / DIVERGED
  - original +584 / -3 numbers are stale.
  - do not broad-rebase or blindly merge.
  - reconcile only capabilities/evidence needed for the intended release candidate.

## Current Learning Evidence OPEN/HOLD outside these stale atoms
- Hosted central evidence transport production binding: HOLD.
- Retention estimator promotion: HOLD pending enough real verified retrieval targets and promotion gates.
- Calibrated BKT promotion: HOLD pending enough real verified targets/calibration/promotion review.
- Netlify/production deployment: HOLD.

## Cross-app hard locks
- Learning Engine owns learner-state/pedagogical intent, not calendar dates.
- Planner owns dated allocation.
- Ready executes Planner sessions; it is not learner-model authority.
- Hide memory signals do not independently schedule long-term review.
- Snap references do not automatically become learner-authored evidence.
- shared mechanisms != shared domain semantics.
- user != tester/debugger.

## Next OPEN
1. Reconcile LAF-INT-003 Snap legacy branch against current main capabilities without history rewrite.
2. Keep hosted transport and estimator promotions as explicit HOLDs; do not confuse them with missing implementation.
3. Device/production/deployment validation remains separate and HOLD unless authorized.
