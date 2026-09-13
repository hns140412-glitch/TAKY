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
- Notion automation runtime: UNVERIFIED unless runtime evidence exists
- offline synchronization / conflict handling: UNVERIFIED unless tested
- project-specific implementation: lower-layer owned

`REFERENCE-ONLY RULE PRESENT ≠ NOTION RUNTIME ENFORCEMENT VERIFIED`.
