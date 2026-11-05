# TAKY BADGE ART BINDING — NEW CHAT START / 2026-10-01

Resume from the current badge-art binding without re-mining or regenerating the 60 current images.

Authority:
- `/TAKY/ASSETS/BADGES/CURRENT_60_V1/TAKY_BADGE_ART_BINDING_MANIFEST_V1.json`
- `/TAKY/ASSETS/BADGES/CURRENT_60_V1/TAKY_BADGE_ART_REVISION_HISTORY_V1.json`
- `/TAKY/ASSETS/BADGES/CURRENT_60_V1/TAKY_BADGE_60_PRODUCTION_SPEC_V3_0_SCENE_FIRST.md`
- `/TAKY/ASSETS/BADGES/CURRENT_60_V1/BADGE_ART_REPLACEMENT_CONTRACT_V1.md`
- `/TAKY/CURRENT/BADGE_ART_BINDING_CURRENT_2026-10-01.json`

State:
- 60/60 current images present.
- Stable identity is fixed: `BDG-DRAFT-NNN` + `BADGE_VISUAL_DRAFT_NNN` + `TAKY_BADGE_ART_NNN`.
- R001 SHA-256 registered for all 60 and byte-verified PASS.
- Groups: 7 CURRENT_APPROVED / 29 CURRENT_CANDIDATE / 24 CURRENT_FUTURE_UPDATE.
- Current art is usable as the working/current 60-image set; future quality work is replacement, not re-binding.

Replacement rule:
- Keep badge_id, visual_id, asset_slot_id and all badge/reward logic.
- Replace only the original image bytes in the same logical slot, recompute SHA-256, increment revision Rxxx, append revision history, refresh manifest/CURRENT.
- Shared rim/star/tier/lock/profile/Crew overlays remain separate.

Repository metadata branch:
- `taky/badge-art-binding-current-20261001`
- Main merge: NOT PERFORMED
- Netlify/deployment: HOLD