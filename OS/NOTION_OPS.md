# TAKY NOTION OPS

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Role: Work OS operational module for Notion collaboration/work-management use.
Authority: `MASTER/MASTER_LOGIC.md` + `MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md` > this module > project-specific Notion schema/config.

## 1. Purpose / Boundary
Notion is used as an operational collaboration surface for work visibility, tasks/issues, decisions, evidence links, changes, snapshots, SOP/knowledge and role-specific views.

Notion is not TAKY canonical source-of-truth by use alone.
Notion is not the sole authority for project calculations, geometry/drawings, original evidence files, laws/regulations or official approvals when those owners remain elsewhere.

## 1.1 Reference-Only Isolation — HARD LOCK

Material collected from Notion as an idea/reference/page excerpt defaults to:

`[STATUS: REFERENCE_ONLY / NON_EXECUTABLE]`

Structured authority state should also preserve:
- `source_origin = NOTION`
- `authority_class = REFERENCE_ONLY`
- `execution_eligible = false`
- `promotion_state = CANDIDATE`

The visible header helps people; the structured authority envelope is the enforceable state.

A Notion reference SHALL NOT directly become a TAKY canonical rule, authoritative numeric/regulatory value, self-modification instruction, release decision, or execution-controlling policy.

Promotion requires the path owned by `MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md`:
`REFERENCE_ONLY → CANDIDATE → SOURCE_VALIDATED → LOCALIZED → IMPACT/REGRESSION_VALIDATED → HUMAN_APPROVED when required → CANONICAL_DELTA → CANONICAL_WRITE → POST_WRITE_VERIFY`.

Direct promotion or use before those applicable gates = `AUTHORITY_BOUNDARY_VIOLATION`.

## 1.2 Notion Review Pending Register — HARD LOCK

When Notion links/pages are being reviewed for possible TAKY / Work OS / Skill / Protocol / Project adoption, preserve the review as a distinct append-only review record before canonical reflection.

`SOURCE CAPTURED ≠ ANALYZED`
`ANALYZED ≠ ADOPTED`
`ADOPTED ≠ CANONICAL REFLECTED`
`CANONICAL REFLECTED ≠ RUNTIME VERIFIED`
`REVIEW PENDING ≠ EXECUTION ELIGIBLE`

A review register exists to preserve the decision process and evidence before reflection; it does not become canonical authority by existence.

The register SHALL NOT collapse materially different dimensions into one linear status field. Preserve separate axes when applicable:

- `SOURCE_STATE`: `INBOX / CAPTURED / VERIFIED / PARTIAL / UNAVAILABLE`
- `ANALYSIS_STATE`: `NOT_ANALYZED / ANALYZED / RECHECK_REQUIRED`
- `DISPOSITION`: use the canonical disposition semantics owned elsewhere, including `PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED` as applicable
- `REFLECTION_STATE`: `NOT_REFLECTED / OWNER_REFLECTED / REFLECTION_FAILED`
- `VERIFICATION_STATE`: `NOT_APPLICABLE / PENDING / VERIFIED / REGRESSION_FAIL`

`OWNER_REFLECTED` means actual evidence exists that the decision was written to the correct canonical owner. It SHALL NOT be inferred merely because review finished, a summary exists, or a candidate was approved in prose.

Use owner-oriented terminology rather than assuming every accepted item belongs in GRAND MASTER. The reflection target may be MASTER core, OS, DOMAIN, PROJECT, Skill, Protocol, or another governed owner.

## 1.3 Review Register Provenance / Immutable Snapshot Contract

A material Notion review record SHOULD preserve, when available:
- `review_item_id`
- immutable `review_snapshot_id`
- `record_type`
- Notion page/database/data-source ID
- raw URL
- normalized URL
- source snapshot timestamp
- source version/hash/content fingerprint where available
- Drive or other governed preservation path
- source/recovery state
- original-content coverage
- missing/constraint notes
- extracted insight linked to the source
- disposition and reason
- target owner
- reflection path/commit/evidence
- verification/regression evidence
- `supersedes / superseded_by`
- next action / priority

A compact field such as `핵심 3줄` may be used as a retrieval projection, but it is not authority and does not replace the preserved source or review evidence.

Review snapshots are append-only in meaning. A later decision SHALL NOT erase an earlier review basis. When a newer decision replaces an older one, preserve the older record as `SUPERSEDED` and link the replacement.

Where the review materially affects conversation continuity, corrections, or decision lineage, link to `MASTER/CONVERSATION_CONTEXT_LEDGER_PROTOCOL.md` rather than redefining its semantics here.

## 1.4 Active Rule Loading Boundary — HARD LOCK

Notion review candidates SHALL NOT be injected into an active execution-rule profile merely because they are high-value, analyzed, or marked ADOPT/ADJUST candidate.

Only a rule/decision with actual `OWNER_REFLECTED` evidence may become eligible for automatic active-rule loading, and it remains subject to the canonical owner, scope, supersession and current-version checks.

`REVIEW_PENDING / CANDIDATE / HOLD / REJECT / CONFLICT ≠ ACTIVE RULE`

A pending register may be loaded as review context when the task is to continue that review, but pending material remains `REFERENCE_ONLY / NON_EXECUTABLE` until governed reflection is complete.

Canonical load order remains:
`LATEST TAKY + APPLICABLE CANONICAL OWNERS → RELEVANT UNRESOLVED REVIEW REGISTER → ACTUAL SOURCE / IMPLEMENTATION EVIDENCE`.

A review register SHALL NOT outrank current canonical TAKY or a later valid user correction.

## 2. Recommended Minimal Data Model
Project-specific implementation may specialize this model, but a robust baseline is:

### Projects
- Project ID
- stage / current gate
- PM / accountable lead
- baseline date
- next gate
- links to Issues, Decisions, Evidence, Changes, Snapshots

### Issues / Tasks
- Issue ID
- title
- status
- accountable owner
- reviewer when applicable
- due date
- priority / blocker
- project link
- source fact/rule link
- evidence link
- decision link
- affected item / dependency
- completion evidence

### Decisions
- Decision ID
- issue/topic
- decision
- approver
- decision date
- superseded-by / replaces
- evidence
- affected items

### Evidence
- Evidence ID
- file/source link
- document/effective date
- owner
- validation status
- authority class / execution eligibility when reference material is involved
- review/expiry date when applicable
- related rule/issue/decision/workbook input

### Changes
- Change ID
- before / after
- reason
- affected items
- validation state
- drawing/calculation/submission links

### Snapshots
- version / hash or governed file link
- created date
- approval state
- regression result
- project/workbook/report relation

Exact fields are lower-layer/project-owned; the baseline is a traceability contract, not a mandatory copy-paste schema.

## 3. Views
Role dashboards should normally be saved views of shared records rather than duplicated databases.

Examples:
- PM: all / delayed / blockers / next gates
- designer: my work / this week / missing evidence
- admin/reviewer: approval pending / automation failure / regression/check failures

`ROLE VIEW ≠ DUPLICATE DATABASE`

## 4. Completion / Evidence
A status change to complete is not sufficient where the work requires a deliverable, review, approval or reflected downstream change.

`COMPLETE → required evidence? → required review? → required approval? → downstream reflection? → VALIDATED COMPLETE`

If required evidence is absent, keep the record in REVIEW_REQUIRED / EVIDENCE_MISSING / equivalent lower-layer state rather than silently closing it.

For review-register promotion, the existence of a checklist does not require every review item to receive the same validation cost. Source authority, coverage, conflict, disposition, target owner, duplicate semantics and reflection evidence must be resolved as applicable; Human Approval, impact/regression depth and runtime verification are proportional to authority, scope, reversibility, risk and whether runtime behavior exists.

`REVIEW GATE COVERAGE ≠ MAXIMUM VALIDATION VOLUME`.
`LOW-RISK REFERENCE LOCALIZATION ≠ HIGH-IMPACT CANONICAL CHANGE`.

## 5. Automation
Suitable automation candidates:
- due-date delay flagging and PM surfacing;
- reviewer notification after review-ready state;
- candidate next-gate task creation;
- evidence replacement causing prior verification to expire and impact-check task creation;
- snapshot comparison creating difference/impact candidates;
- validation FAIL blocking report/release candidate and assigning remediation;
- automation failure entering retry/escalation state.

Human approval remains required for official completion/release, authoritative numeric/regulatory promotion, irreversible external actions and exceptions when the owning policy requires it.

`AUTOMATION START ≠ OFFICIAL CONFIRMATION`

## 5.1 Link Review Normalization / Duplicate Safety

For URL-oriented review databases:
- preserve `raw_url` before normalization;
- normalize obvious tracking/query variants only as a candidate comparison aid;
- do not classify `DUPLICATE` from URL normalization alone when materially different content may exist;
- compare source identity/content fingerprint/version or equivalent evidence before destructive deduplication;
- retain the representative source and preservation links before deleting/merging records.

Rows without an external URL SHALL NOT be automatically classified as broken. Use `record_type` (for example `EXTERNAL_URL`, `NOTION_CONTAINER`, `ATTACHMENT_SOURCE`, `NOTE`, or project-specific equivalent) before declaring `URL_MISSING`.

`NO URL ≠ BROKEN RECORD`.
`NORMALIZED URL MATCH ≠ CONTENT IDENTITY PROVEN`.

## 6. AI Use
Allowed candidates:
- search/summarize workspace material with source pointers;
- draft status summaries;
- detect missing fields/evidence;
- compare versions and generate candidate impact tasks;
- suggest classifications or next actions.

Not allowed as automatic authority:
- final legal/regulatory conclusion;
- authoritative project numeric value promotion;
- official approval/issuance;
- silent replacement of source calculations or drawings;
- direct use of REFERENCE_ONLY Notion content as canonical execution logic.

## 7. Offline / Sync
Notion app/browser offline capability SHALL NOT be assumed to satisfy a project runtime offline contract.
When a separate web/PWA/runtime requires reliable offline capture, implement and validate a local durable queue/outbox, stable event/entity IDs, base-version/conflict handling, retry/backoff, evidence references and reconciliation to authority.

Notion may receive a projection after authoritative/local commit according to project policy.

## 8. Source / Tool Authority Example for Architecture
Project-specific authority mapping must be validated. A common safe pattern is:
- spreadsheet: numeric/formula/cross-check authority;
- CAD/BIM: geometry/object/drawing authority;
- Google Drive/governed file storage: original/evidence-file authority;
- Notion: task/issue/decision/status collaboration surface;
- TAKY: governance/validation/orchestration.

Never hand-maintain the same authoritative value independently in multiple systems without an explicit ownership/migration rule.

## 9. Current Implementation Status
This module defines logic only.
The connected Notion workspace implementation status must be established from actual schema/runtime evidence; do not upgrade it from document existence alone.

- Notion operational schema implementation: UNVERIFIED unless actual schema evidence exists
- Notion review-register structured fields/runtime: UNVERIFIED unless actual schema evidence exists
- Notion automation runtime: UNVERIFIED unless runtime evidence exists
- offline synchronization / conflict handling: UNVERIFIED unless tested
- project-specific implementation: lower-layer owned

`REFERENCE-ONLY RULE PRESENT ≠ NOTION RUNTIME ENFORCEMENT VERIFIED`.
`REVIEW REGISTER RULE PRESENT ≠ REVIEW REGISTER RUNTIME VERIFIED`.
