# Current Identity & Change History Governance

Status: DRAFT TRANSITION ON WORK BRANCH / NOT YET MAIN
Role: Existing revision-governance owner; replaces serial document-revision authority once promoted.
Source: user direction on 2026-09-27 to stop revision proliferation, stale revision selection and rebuild-induced numbering. Original numbered policy is recoverable from main at `8e78af8b77d1f3e132f05c99cd6b69a7f258a23e` and Git history.

## Outcome
TAKY and its sibling Work OS / Learning OS systems should have **one discoverable current identity per semantic owner/namespace**, without an arbitrary visible sequence of REV/V file names. More rebuilding, review and reflection must not create new document-revision numbers.

- `CURRENT` is a logical owner-specific pointer verified against the live authority; it is not a filename/date/number.
- `HISTORY` keeps immutable source snapshots, older aliases, original exact identifiers, migrations and provenance.
- `CHANGE` records reason and delta; Git commit SHA, Drive file ID/revision/receipt or a content hash can prove exact bytes.
- `STATUS` is explicit, e.g. DRAFT / CANDIDATE / APPROVED / COMMITTED / ACTIVE / SUPERSEDED / HOLD / UNVERIFIED. Neither a higher number nor a newer-looking title promotes authority.

`CURRENT != MAX(REV/V)`. `NEW FILE != NEW AUTHORITY`. `REMASTER != NUMBER INCREMENT`. `VERSION-FREE DISPLAY != HISTORY DELETION`.

## Stable source names and selectors
Prefer `<NAMESPACE>/<SEMANTIC_OWNER>` as a stable logical identity and, after compatibility migration, a versionless physical canonical filename. A single namespace CURRENT record resolves that identity to its actual owning repository/path or Drive file ID and evidence-bound promotion/selection receipt. Read latest live Git main HEAD or authenticated Drive object metadata at use time; stored SHA and last-checked time are evidence, not perpetual freshness. If duplicate active candidates exist, fail to CONFLICT instead of guessing by title/date/number.

- Current authority order: explicit latest authorized user change within scope; applicable active canonical owner on latest verified main/namespace CURRENT; relevant promotion/selection receipt; full latest handoff and original source as recovery evidence; history/legacy as lineage only.
- Cross-project ownership and Work vs Learning remain unchanged. `IMPLEMENTED_IN != OWNS`.
- New files are created only for necessary new roles or material evidence, never merely to roll a number.
- No automatic alias-following that upgrades historical names; old links are mapped to current semantic owner and retain `HISTORICAL` status after migration.

## Preserve actual technical compatibility versions
Do NOT strip or repurpose runtime schema, API/wire contract, database migration, PWA/service worker/cache release, model/index compatibility or legal effective-date identifiers where a consumer needs them. Label these `TECHNICAL_COMPATIBILITY_VERSION`, `RELEASE_BUILD_ID`, `DATASET_SNAPSHOT_ID` or `HISTORICAL_SOURCE_LABEL`; none alone decides CURRENT. Do not rename external immutable receipts or an in-use source file in place. The user-facing operating and handoff display should normally show semantic owner, current state, evidence and OPEN rather than REV/V.

## Migration safety
1. Independently inventory active source owners and all consumers/links of each numbered path.
2. Freeze original source ID, path, content hash, current main/Drive ID and last valid decision.
3. Publish a stable logical alias pointing to the SAME content while old links remain usable. Do not create a competing active copy.
4. Update readers, registries and handoffs to resolve the alias/namespace CURRENT; add tests against stale/ambiguous/higher-number selection.
5. Verify forward and reverse source/decision/result lineage, regress actual consumers and only then change physical names if the affected owner needs it.
6. Retain prior filenames and revision labels as immutable HISTORY/LEGACY redirects or recoverable source pointers. Never delete evidence to make an index look clean.
7. Track `MAPPED -> READER_MIGRATED -> VERIFIED -> LEGACY_ONLY` per owner. Unmigrated dependencies are HOLD, not secretly complete.

## Known baseline examples (not new authority)
- `MASTER/MASTER_LOGIC.md` is the stable TAKY owner. Its prior REV_00 label is a historical status label, not the future document identity.
- `MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md` has an internally REV_00 status already: keep the exact original file and owner now, expose stable logical alias `LEARNING_APP_FAMILY_MASTER`, and rename physical path only after link/consumer migration.
- `CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json` presently selects the explicitly promoted source and utilization index by Drive file IDs plus receipt. The historic V6/V26 titles and 679-source evidence MUST NOT be erased, and no newer-looking V file may override the selected receipt.
- Historic Ready/Hide/Snap UI revision filenames are not global current decisions; resolve each active project main/owner, preserving any inherited approved details. Badge work is owned by another chat; Work OS feature work remains HOLD.

## Status of this transition
This draft is a bounded structural candidate, not a main merge, automatic hosted-ChatGPT enforcement, or completed migration. The accompanying C2S migration matrix records scoped baseline and OPEN items. Application-specific technical version and release behavior must not be changed by a naming clean-up.
