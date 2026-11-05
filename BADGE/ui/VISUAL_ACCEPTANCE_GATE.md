# Badge UI visual acceptance gate

Status: BLOCKED — NOT VISUALLY VERIFIED. Draft PR only. Do not merge, activate registry, or deploy on the basis of code-only tests.

## Authority
- Approved four-screen storybook concept: home, collection, earned/locked detail, acquisition. The concept image is a reference, not an exportable asset sheet.
- Existing 60 WOW-inspired display titles/toasts/flavor text from BADGE/badge-wow-inspired-copyworking.json; preserve IDs and exact strings.
- Original character and crew visual identities only; no invented or duplicated character art.

## Visual requirements
- Warm ivory, wood, olive, parchment. No blue buttons or bottom bar.
- Original pastel hand-drawn illustration; fixed approved frame and recessed depth. Do not alter the frame when revising interior illustration.
- Frame pastel gradient fades outwards; tier is STAR COLOR ONLY: green, blue, red, gold, platinum rainbow.
- First earned = one star, maximum five, along the upper arc. Locked = silhouette. Award ledger, not telemetry, governs earned state.
- Individual 60 assets with approved Visual IDs; never crop a concept sheet. Layers: background, interior, foreground, crew when story needs it, shadow, frame, effect; separate child-scoped profile overlay.
- Asset approval and ownership are distinct; unapproved asset is not a shippable badge image.

## Open blockers
1. No verified, individually authored 60 original layered illustrations or reviewed asset paths in registry.
2. No verified original crew assets mapped to Visual IDs.
3. No pixel/side-by-side comparison of actual browser rendering against approved screen concept at mobile viewport.
4. Home hero currently CSS scenery, not original high-density illustrated art; acquisition screen and connected app navigation are not implemented here.
5. Updated renderer tests and integrated runtime/visual tests must pass on exact head.

## Release condition
Only report identical after approved original assets are linked, all screens rendered at target sizes, visual differences corrected, interaction/accessibility/regression tests pass, and review evidence is recorded. No Netlify invocation without deployment authorization.
