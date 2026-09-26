# BADGE VISUAL & REAWARD CONTRACT — latest user correction, 2026-09-26

Authority: direct user correction overrides older "grade classification" interpretation.
Scope: correct star semantics and visual presentation; preserve the already closed Evidence → Candidate Review → Achievement Decision → Award Ledger logic.

## Meaning of a badge
A fictional exploration crew's campaign/achievement insignia (탐험대 공적 훈장 / 부대 표장 느낌), not a score, a weapon, a power-up, or an actual military decoration. Maintain a child-friendly hand-drawn pastel look.

## Acquisition and stars
- FIRST approved acquisition: activate the badge in the child's collection; zero stars.
- Each subsequent DISTINCT, approved acquisition of the SAME badge for the SAME child: one additional star.
- 5 re-acquisition stars: change to the next tier. The five-star promotion threshold is user-confirmed. Showing five stars during the promotion and resetting the new tier to zero are PROVISIONAL presentation/projection policies pending separate confirmation.
- A mere repeated activity event, time spent, right/wrong answer, raw telemetry, EXP or gem does not count as reacquisition. Only accepted Award Ledger receipts following the existing review/decision process qualify.
- Dedupe by award receipt ID; reject cross-child or cross-badge projection.
- Historical tier-name/palette lineage: GREEN / BLUE / RED / GOLD / PLATINUM. The final tier list and what happens AFTER the last tier remain OPEN; do not invent a rank beyond the defined list.

This REPLACES and supersedes the obsolete "1–5 stars = grade classification" text in earlier documents and code. The old historical preview's automatic observation-count → tier/stars calculation must not be restored.

## Five separate visual layers
1. Approved badge base art: round, pastel, fictional campaign-merit composition, expedition icon/ribbon, NO baked-in individual child character.
2. CHILD_PROFILE character overlay: separate and child-scoped; never transplant another child's profile/identity.
3. Ownership state: LOCKED = silhouette/desaturated; EARNED = active color after verified award.
4. Reacquisition progress: 0–5 stars per current tier, driven only by approved reawards.
5. Border: soft radial/conic pastel gradient that dissipates towards the edge.

For a real image, registry approval and child's ownership are separate. An unapproved image remains unrenderable even in silhouette; a non-owned badge with approved art appears only as a LOCKED silhouette, not as an awarded item.

## Approval and historical content
60 draft names remain WORKING_DRAFT_NOT_ACTIVE. Both recovered 12-badge sheets remain reference candidates, not approved final per-badge assets. User favors the pastel final direction but the exact historical final source file has not been verified. No silent selection, cropping, asset promotion, catalog activation, or automatic award.

## Implementation boundary
- Central registry validates semantic contract and approval.
- `badge-reaward-progress.js` is a pure projection from PREVALIDATED authoritative award receipts; it does not itself award badges or validate the cryptographic origin of input.
- Renderer consumes approved assets and an authoritative ownership projection; it is NOT itself a decision maker.
- Child profile overlay must come from the matching child's profile.
- `badge-visual-presentation.css` is a shared style contract until explicitly imported by an app.
- Actual app surface wiring remains OPEN.
