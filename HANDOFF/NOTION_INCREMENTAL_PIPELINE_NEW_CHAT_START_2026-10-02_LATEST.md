# TAKY 신규자료 파이프라인 NEW CHAT START — 2026-10-02 LATEST

## Resume authority
- Source generation: `INCREMENTAL_QUEUE.20261002T040003612Z.json`
- CURRENT: `CURRENT/DATA/NOTION_INCREMENTAL_PIPELINE_CURRENT_20261002.json`
- Durable evidence package: HISTORY/NOTION_INCREMENTAL_2026-10-02/
  - `DELTA_MINING_GATE_20261002.json`
  - `DELTA_MINING_CLASSIFICATION_20261002.json`
  - `DELTA_INDEX_OWNER_REVIEW_QUEUE_20261002.json`
  - `DELTA_INDEX_OWNER_RECEIPTS_20261002.json`
  - `DELTA_DOMAIN_REQUERY_HANDOFF_20261002.json`
  - `DELTA_LEARNING_POLICY_CHECK_20261002.json`

## Closed
- Current source queue verified: 161/161 unique rows and CURRENT entries.
- Delta isolated from prior 148-source gate: 13 rows, 11 unique URLs, 2 duplicate URL rows.
- 11 delta sources mined; second-pass review resolved the 3 REVIEW items to scoped Index references. 3 HOLD remain.
- Base Index V6/679 compared; no exact duplicate evidence among 5 candidates.
- R1: 5 candidates independently reviewed and persisted as INDEXED + EVIDENCE_CANDIDATE under `V6+DELTA_20261002_R1`.
- R2: 3 former REVIEW items independently reviewed as scoped references under `V6+DELTA_20261002_R2`: Twinkl time-sensitive resource / RedrawAI design tool / SpectrumHub secondary official-link hub.
- SpectrumHub QABA links were cross-checked against QABA official forms/credential pages; SpectrumHub itself remains secondary authority.
- Correction: 0wonloop was over-promoted in R1 despite insufficient inline body; append-only `NEEDS_MORE_EVIDENCE` now deactivates it until actual content is reacquired.
- Domain split: Learning 2 / Design 3.
- Index -> Learning handoff contract passes for both Learning candidates.
- Learning policy correctly FAIL-CLOSED:
  - writing scaffold lacks `WRITING_CORPUS_SOURCE_REF`
  - reading prompt lacks `SOURCE_SPECIFIC_REF` and `CONSTRUCT_SOURCE_LABEL`
- Design 3 remain indexed references only and never become learner-performance evidence.

## Open
- Do not invent missing Learning provenance. Re-open only when independent evidence satisfies the policy registry.
- REVIEW queue is closed for this delta.
- Former media-only HOLD 2 were browser-recovered into R3 REVIEW; 1 vehicle-maintenance source remains out-of-scope HOLD.
- R3 REVIEW 2 resolved against canonical V6: no exact duplicate evidence; both are now INDEXED reference-only under V6+DELTA_20261002_R3.
- Full canonical Source Index promotion remains separate; no silent overwrite of V6.
- Deployment and Netlify remain HOLD.

## R3 recovery update
- Browser render recovered substantive content for both former media-only HOLD sources.
- AI-15 page -> REFERENCE_TOOL_DISCOVERY, community-curated/time-sensitive reference only; Learning use disabled.
- Free-domain TOP 5 page -> DEV_INFRA_REFERENCE, community-curated reference only; deployment authorization disabled.
- Notion later returned intermittent challenge pages, so evidence is marked partial/non-stable where applicable.
- Canonical Source Index V6 was read directly from connected Google Drive; source URL/title/core names were absent, so no exact duplicate evidence was found. Both are INDEXED reference-only under V6+DELTA_20261002_R3.
- Durable evidence: HISTORY/NOTION_INCREMENTAL_2026-10-02/DELTA_R3_BROWSER_RECOVERY_REVIEW_20261002.json and DELTA_INDEX_OWNER_RECEIPTS_R3_20261002.json.

## Latest operational state
- PR #203 merged to main: `a6703e1e6935fe8d1e7f8d2f717dd6a7ed8de9b5`.
- PR #204 merged to main: `4af88d609d5b09fc673f342c77b7b6df33b9cf02`.
- Daily 08:00 KST automation enabled: deep-mine all TAKY reference sites for only new/materially changed content.
- Automation scope: new posts + new categories + linked docs + resource libraries + guides + attachments/subpages; dedupe by URL/hash/title/body similarity; then Mining -> duplicate/version decision -> Indexing candidate -> domain routing.
- Existing/previously reviewed material must not be reprocessed or re-reported.
- Paid API / usage-billed path prohibited without separate user approval. Netlify/deployment remain HOLD.

## Next OPEN sequence
1. Keep the vehicle-maintenance source as out-of-scope HOLD.
2. Keep the two Learning references fail-closed until independent provenance satisfies policy.
3. Reverify time-sensitive tool/provider status against first-party sources only when these references are actually used.
4. Continue only with new/materially changed reference-site discoveries; do not repeat previously mined evidence.

## Resume command
`최신 TAKY 기준으로 신규자료 파이프라인 재개`
