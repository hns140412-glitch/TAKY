# TAKY BADGE ART REPLACEMENT CONTRACT V1

Status: CURRENT / 2026-10-01

## Immutable identity
Each badge keeps these identifiers permanently:
- `badge_id`: `BDG-DRAFT-001..060`
- `visual_id`: `BADGE_VISUAL_DRAFT_001..060`
- `asset_slot_id`: `TAKY_BADGE_ART_001..060`

## What changes when original art is updated
Only the following fields/bytes change:
1. `BDG-DRAFT-NNN.png` image bytes at the same logical slot/path
2. `sha256` / `content_address`
3. `asset_revision_id` (`R001` → `R002` ...)
4. `source_lineage` and replacement evidence

Do **not** rename or recreate badge IDs, visual IDs, asset slots, badge logic, award logic, title/detail/story authority, tier/star/lock layers, profile overlay, or Snap Crew overlay merely because art is replaced.

## Replacement transaction
1. Select one badge ID.
2. Verify new art against the bound semantic authority in `TAKY_BADGE_60_PRODUCTION_SPEC_V3_0_SCENE_FIRST.md`.
3. Replace the image in the same stable slot.
4. Compute SHA-256.
5. Increment `asset_revision_id`.
6. Update the manifest and CURRENT manifest SHA.
7. Run `verify_badge_art_binding_v1.py`.
8. Keep previous SHA/revision in history before runtime/deployment changes.

This lets UI/runtime bind to stable IDs while only the original artwork bytes are swapped later.