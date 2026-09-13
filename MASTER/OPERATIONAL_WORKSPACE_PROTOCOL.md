# TAKY OPERATIONAL WORKSPACE / PROJECTION PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Role: Normative GRAND MASTER child protocol for operational collaboration surfaces such as Notion, task/issue systems, dashboards, wikis and external projections.
Authority: `MASTER/MASTER_LOGIC.md` governs this protocol. This protocol SHALL NOT override project/domain source-of-truth rules.

## 1. Core Principle — HARD LOCK

An operational workspace is a coordination and traceability surface, not automatically the authority for every datum it displays.

`OPERATIONAL WORKSPACE ≠ CANONICAL MASTER SOURCE`
`OPERATIONAL WORKSPACE ≠ NUMERIC / CALCULATION AUTHORITY`
`OPERATIONAL WORKSPACE ≠ GEOMETRY / DRAWING AUTHORITY`
`OPERATIONAL WORKSPACE ≠ ORIGINAL EVIDENCE REPOSITORY`
`PROJECTION WRITE ≠ SOURCE COMMIT`
`TOOL CAPABILITY ≠ PROCESS CORRECTNESS`

Each materially important data class SHALL have one approved authority/owner system. Other tools may project, reference, summarize or coordinate that data but SHALL NOT become a second manually maintained authority without an explicit migration/ownership decision.

Project-specific authority mapping belongs to the owning DOMAIN / PROJECT / WORKFLOW master.

## 2. Operational Record Contract — HARD LOCK

Material work items SHOULD preserve, as applicable: stable ID, Project/entity link, accountable owner, reviewer/approver when required, due date/gate, state, priority/blocker, source/evidence link, decision/approval link, affected dependencies, completion evidence, latest validation state, and change/history pointer.

`EVERYONE OWNS IT ≠ ACCOUNTABLE OWNER`
`STATUS = COMPLETE ≠ EVIDENCE OF COMPLETION`
`REVIEWER ≠ EXECUTION OWNER` when independent review is required.

A completion state SHALL NOT be treated as authoritative when material required evidence, review, approval or downstream reflection is missing.

## 3. One Dataset, Multiple Views — HARD LOCK

Role-specific views SHALL normally be projections of the same underlying operational records rather than duplicated personal databases.

`ONE DATASET + MANY VIEWS > MANY MANUALLY COPIED DATABASES`
`VIEW ≠ NEW SOURCE OF TRUTH`

Different roles may see different filters/groups/priorities while record identity and lineage remain shared. A copied database that creates independent editable truth is a divergence risk and requires explicit justification.

## 4. Decision / Evidence / Change Graph

Where material, operational work SHOULD be traceable as:
`PROJECT FACT / REQUIREMENT / RULE → ISSUE / WORK ITEM → OWNER / DUE / STATE → EVIDENCE → DECISION / APPROVAL → AFFECTED ITEM → DESIGN / CALCULATION / SUBMISSION REFLECTION → VALIDATION → SNAPSHOT / HISTORY`.

`VALUE CHANGED ≠ IMPACT CLOSED`
`DECISION RECORDED ≠ DECISION REFLECTED`
`DOCUMENT LINKED ≠ DOCUMENT VALIDATED`

## 5. Evidence / Knowledge Validity

Operational knowledge, wiki, SOP or reference pages that influence material work SHOULD preserve owner, source, effective/valid date where relevant, verification state and review/expiry condition.

`VERIFIED PAGE BADGE ≠ LEGAL / TECHNICAL ACCURACY`
`WIKI EXISTS ≠ KNOWLEDGE CURRENT`
`SOP EXISTS ≠ SOP APPLIES TO THIS CASE`

Repeated/high-variance/handoff-critical work is a suitable SOP candidate. Not every task should be documented as an SOP merely because a workspace can store one.

## 5.1 Reference Authority Envelope — HARD LOCK

Material imported from Notion, external AI, web/community references, templates, imported notes, Handoffs, or other non-canonical surfaces SHALL carry an authority envelope before it can influence canonical execution.

Minimum conceptual fields:
- `source_origin`;
- `authority_class`;
- `execution_eligible`;
- `promotion_state`;
- source/evidence pointer;
- validation state.

Default for externally collected ideas/reference material:
`authority_class = REFERENCE_ONLY`
`execution_eligible = false`
`promotion_state = CANDIDATE`

Allowed promotion path:
`REFERENCE_ONLY → CANDIDATE → SOURCE_VALIDATED → LOCALIZED → IMPACT/REGRESSION_VALIDATED → HUMAN_APPROVED when required → CANONICAL_DELTA → CANONICAL_WRITE → POST_WRITE_VERIFY`.

A textual header such as `[STATUS: REFERENCE_ONLY / NON_EXECUTABLE]` is recommended for human readability, but machine enforcement SHALL rely on structured authority metadata when available.

Any direct use of REFERENCE_ONLY material as canonical/execution-controlling logic before governed promotion is `AUTHORITY_BOUNDARY_VIOLATION` under `MASTER/FAILURE_TAXONOMY.md`.

## 6. AI / Automation Boundary — HARD LOCK

AI may assist with structured search, summarization, draft planning, classification, comparison, missing-field detection and candidate task generation when evidence and authority are preserved.

AI SHALL NOT automatically promote unverified project numbers, regulatory/legal conclusions, technical calculations, official approvals or irreversible external release decisions into authoritative state merely because the operational workspace can automate them.

`AI SUMMARY ≠ OFFICIAL VALUE`
`AI CANDIDATE ≠ APPROVED DECISION`
`AUTOMATION STARTED ≠ OFFICIAL CONFIRMATION`
`ADMIN IMMEDIATE EXECUTION ≠ VALIDATION BYPASS`

Automations SHALL expose material failure state, retry/recovery path and manual escalation when required. Silent drop of a required notification, evidence update, approval gate or downstream impact task is a validation failure.

## 7. External Projection / Offline / Sync

When an operational workspace is an external projection of a runtime/project authority, inherit `MASTER/MASTER_LOGIC.md` Connected / Offline Runtime Sync Governance.

At minimum, lower-layer design SHALL distinguish authoritative entity/source version, projected record ID, event/change ID, base version/concurrency evidence, pending/synced/failed/conflict state, evidence reference, bounded retry/escalation, and reconciliation back to authority.

Browser/app offline features SHALL NOT be assumed to satisfy a project's offline correctness requirements.

## 8. Tool-Specific Boundary: Notion

Notion may be used as an operational collaboration surface for projects, issues/tasks, decisions, evidence links, changes, snapshots, wiki/SOP and role-specific views.

Notion SHALL NOT become TAKY canonical authority by use alone.
Notion SHALL NOT replace approved spreadsheet calculation authority, CAD/BIM geometry/object authority, governed evidence/original-file storage, or explicit human approval where those remain approved owners.

Notion database properties, relations, rollups, views, automations, verification and webhooks are capabilities. Their existence SHALL NOT be treated as proof that the underlying data is complete, correct, current, authorized or synchronized.

Exact schemas/views/automations/connector configuration are owned by Work OS / Project masters, not GRAND MASTER core.

## 9. Validation / Reverse-Validation

For material operational-workspace changes, run distinct gates:
`ERROR VALIDATION → SELF-CORRECTION → SELF-VALIDATION → INDEPENDENT CROSS-VALIDATION → IMPACT VALIDATION → REGRESSION VALIDATION → REVERSE TRACE`.

Validate both directions from source/authority to visible status and back.

Mandatory failure patterns include duplicated authority across tools; complete without required evidence/review/approval; orphan records; source changes without impact tasks; stale dashboards; manual-copy drift; hidden automation failure; AI-generated conclusions promoted without authority/approval; REFERENCE_ONLY material controlling execution; and offline/sync assumptions without tested reconciliation.

## 10. Disposition / Adoption Rule

External templates, videos, seller systems, AI proposals and community workflows are evidence/candidates only.

`TEMPLATE ≠ MASTER DECISION`
`POPULAR WORKFLOW ≠ FIT-FOR-PURPOSE`
`NOTION-ONLY ≠ BETTER SYSTEM`
`REFERENCE_ONLY ≠ CANONICAL RULE`

TAKY SHALL extract transferable operating principles, localize them to actual tool authority and project constraints, then classify `PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED`.

Promotional performance claims, pricing funnels and testimonials are not adopted as governance evidence without independent validation.
