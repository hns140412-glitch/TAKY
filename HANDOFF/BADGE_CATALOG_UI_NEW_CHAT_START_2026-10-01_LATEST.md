# TAKY BADGE CATALOG UI — NEW CHAT START / CURRENT

Authority: `/TAKY/ASSETS/BADGES/CURRENT_60_V1/`.

Current closed:
- 60/60 current badge art files are individually stored.
- Stable Badge ID + Visual ID + Asset Slot ID + SHA-256 + R001 are registered.
- Catalog UI contract and 60-item UI viewmodel are fixed to resolve artwork through `asset_slot_id`.
- POCKET 20 / FIELD 20 / EXPEDITION 14 / SECRET 6.
- Art quality state is separate from learner ownership/award state.
- Tier rim, 0~5 reacquire stars, lock, and profile character are separate UI layers.

Replacement rule:
When art is improved later, keep `badge_id`, `visual_id`, `asset_slot_id`, title, logic and history. Replace only artwork bytes, SHA-256, revision and lineage. UI consumers therefore do not need rebinding.

Next OPEN:
- connect the UI viewmodel to Snap-Pop badge catalog/runtime consumer.
- do not deploy or merge main until runtime tests pass.