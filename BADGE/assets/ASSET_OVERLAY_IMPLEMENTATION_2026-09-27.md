# TAKY Badge — separately managed assets and optional character overlays

Date: 2026-09-27. Draft PR #163, based on draft PR #160, **not main**.

## Implemented
- 60 distinct original badge ID/Visual ID pointers in `BADGE/assets/asset-registry-working.json`, preserving source story and motif. Existing vector art: `BADGE/ui/assets/individual/001..060/{background,interior}.svg`; these source files remain candidate sketches, not replaced, falsely approved, duplicated or cropped.
- Four shared reusable SVG source files: `BADGE/assets/shared/rim.svg`, `shadow.svg`, `star-mask.svg`, `lock.svg`; per-badge stars or tier-specific frame copies are not generated.
- 60 candidate overlay anchor entries in `BADGE/assets/overlays/slots-working.json` for a separately approved child profile / Snap-owned individual Crew. The positions are provisional, not accepted as safe over an unproduced final scene.
- `BADGE/ui/badge-atlas.js`: composition of approved independent background/interior/optional foreground; optional profile and optional Snap Crew, behind or above foreground only with reviewed per-scene anchor; shared rim and star/lock states remain outside individual art. Approved character-free base is renderable. Locked badges never show child-specific overlays; foreign/malformed or unreviewed overlays fail closed.
- Read-only central additive plan `BADGE/badge-managed-asset-compositor.js` reuses original badge renderer checks without changing CLOSED logic. No client flag proves actual signed Ledger or server authorization.
- Tests: `BADGE/ui/badge-atlas.test.cjs` (also executes ESM test and managed compositor test), `BADGE/assets/test_badge_assets.py`, existing structural/raster scene tests. Verified successful checks at exact implementation HEAD `495eaeaba962743817150edb6de24fa7367f9dc4`: Badge UI contract checks run 36294806728 SUCCESS and Badge Visual Registry Validation run 36294806666 SUCCESS. CI success is technical only.

## Deliberately not claimed
- The 60 flat vector scene candidates fail visual parity with original high-density watercolor/painterly six-screen reference (001 and 026 were opened and failed; the remaining 58 have no style certification). Final accepted art 0/60.
- No actual reviewed child avatar / Snap Crew visual asset was added or invented. No child account was used.
- No runtime approved registry or real Award Ledger binding, Catalog activation, Work OS activity, Netlify deployment or main merge.
- User does not need to approve 60 pieces one by one: the execution owner self-verifies each story, physically separate layers, responsive 64/120/200/320 render and asset identity as a batch. Editorial/layout/release authorities must still be real evidence, not artificial boolean toggles.

## Next OPEN
Replace rejected vector sketches with individual high-density illustrations reflecting each badge's own motif; maintain separate background/interior/foreground and independent optional overlay; review layout against *actual final art*, then connect approved scoped profile/Crew providers and server-verified child Ledger. Validate final browser screens against user-original storyboard. Do not use rejected sketches as automatic fillers.
