# TAKY badge asset management — draft branch only

**Scope:** one independent scene per original 60 badge identities; optional child/crew visual overlays; reusable shared rim, shadow, star mask and lock. This asset directory is **not** the approved runtime registry or active catalog. `CURRENT/BADGE_INDIVIDUAL_ART_CURRENT_2026-09-27.json` and the original six images described in `BADGE/ui/APPROVED_STORYBOARD_2026-09-27.md` remain the visual authority.

## Locations and ownership
- `asset-registry-working.json`: one central pointer per original ID/visual ID, preserves source title, story and motif. Existing vector candidate files remain physically in `BADGE/ui/assets/individual/001..060/{background,interior}.svg` to avoid redundant copies. The rejected flat-vector work is **not** promoted merely because it has file paths.
- `shared/{rim,shadow,star-mask,lock}.svg`: four shared source assets reused by the UI; tier coloration and star count are renderer/CSS and verified Ledger projections, not 5x60 duplicate images.
- `overlays/slots-working.json`: per-badge profile and crew spatial slots, currently **provisional and unapproved**. Geometry is measured against each eventual final artwork. No character image/ID is in the asset registry.
- `BADGE/ui/badge-atlas.js`: optional composition of already-approved base artwork plus separately supplied verified same-child profile and Snap-owned crew overlays. No fallback mascot and no automatic display from current 60 draft sketches.

## Layering
Base: background → interior → optional profile/crew (approved behind foreground) → optional foreground → optional approved front overlays → common frame/rim → Ledger stars/tier and lock state. A fully formed base does not require any character. A supplied malformed, foreign-child, wrong-family or unsourced overlay prevents rendering the artwork. Locked badges never render identity overlays. Optional Crew is supplied only by reviewed Snap-owned individual content, not a generic reference image or inferred Ready avatar.

## Approval and execution separation
1. Source preservation and candidate art file creation do not grant visual approval.
2. High-density visual comparison, real physical independent layers, icon-size QA and source story review provide candidate review evidence.
3. Real approval registry requires separate recorded reviewed art/layout identity and actual safe asset path. Any runtime asset must have explicit approved status, approval evidence, active catalog and renderer binding; an artifact manifest or local browser object cannot grant server authority.
4. A server-verified signed Award Ledger alone determines child ownership/reaward stars. Never activate historical 60 or infer awards from imagery/telemetry. Family gifts are separate.
5. Source original, existing CLOSED code and visual authority are retained. Work OS HOLD; no main merge, Netlify or real activation.

## Quality status
- 60 individual vector sketches, 120 SVG scene files and separate raster previews exist.
- At least 001 and 026 **failed** comparison with the high-density original storyboard; the remaining 58 are not visually certified. Final accepted art: **0/60**. Do not auto-bind these sketches.
- Common reusable asset files and overlay composition are implementation scaffolding, not proof of pixel matching. No new character images have been fabricated.
