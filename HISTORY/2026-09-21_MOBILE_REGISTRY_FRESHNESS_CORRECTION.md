# 2026-09-21 Mobile Registry Freshness Correction

Status: VALIDATION RECORD
Scope: Close the stale-snapshot ambiguity discovered during the Work OS / Learning OS / mobile-app ownership review.

## Trigger

The mobile app development registry stores GitHub main heads and deploy relationships. Those values are useful operational snapshots but can become stale after app merges. Treating SOURCE_CURRENT as perpetual live-head truth would violate current-state evidence requirements.

## Changes

- registry version -> 2026-09-21.2;
- add VOLATILE_OPERATIONAL_SNAPSHOT freshness policy;
- require live refresh before material current-main/open-PR/release/deploy claims;
- refresh Ready / Snap / Hide main-head evidence for this review;
- update Snap deployed relation from EXACT_SHA_MATCH to DEPLOYED_STALE after README-only main change;
- preserve runtime/device claim separation;
- update deterministic validator to require freshness semantics;
- close Ready README drift and Snap README drift findings in SYSTEM_LAYER_OWNERSHIP_MAP;
- mark registry freshness gap PARTIAL rather than falsely complete.

## Verified project documentation corrections

Ready & Set:
- PR #74
- merge: 5b1d88a153c54d470db044bf81c5a237fa0d66a8
- current README points to Ready canonical product contract and removes historical Time Attack identity.

Snap & Pop:
- PR #2
- merge: 1c1a4e8d009c25e37e74c8d07b0ae33f0a89c6d0
- current README points to REV12 instead of REV10.

## Claim boundary

A refreshed registry snapshot is not a permanent live feed.
Automated refresh remains OPEN as a future optimization and should be added only if its operational value exceeds its maintenance/call cost.

END
