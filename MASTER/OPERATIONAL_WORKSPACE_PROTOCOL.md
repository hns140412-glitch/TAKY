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

Project-specific authority mapping belongs to the owning DOMAIN / PROJECT / WORKFLOW master. Typical professional mappings may use spreadsheets for structured calculations, CAD/BIM for geometry/object evidence, governed file storage for originals/evidence, an operational workspace for issues/tasks/decisions/status, and TAKY for governance/validation/orchestration. These examples are patterns, not universal mandates.

## 2. Operational Record Contract — HARD LOCK

Material work items SHOULD preserve, as applicable:
- stable Work / Issue / Task ID;
- Project / entity link;
- one accountable execution owner;
- reviewer / approver separated when required;
- due date / target gate;
- current state;
- priority / blocker;
- source/evidence link;
- decision / approval link;
- affected item / dependency links;
- completion evidence;
- latest validation state;
- change/history pointer.

`EVERYONE OWNS IT ≠ ACCOUNTABLE OWNER`
`STATUS = COMPLETE ≠ EVIDENCE OF COMPLETION`
`REVIEWER ≠ EXECUTION OWNER` when independent review is required.

A completion state SHALL NOT be treated as authoritative when material required evidence, review, approval or downstream reflection is missing.

## 3. One Dataset, Multiple Views — HARD LOCK

Role-specific views SHALL normally be projections of the same underlying operational records rather than duplicated personal databases.

`ONE DATASET + MANY VIEWS > MANY MANUALLY COPIED DATABASES`
`VIEW ≠ NEW SOURCE OF TRUTH`

Different roles may see different filters, groups, priorities or dashboards while record identity and lineage remain shared. A copied database that creates independent editable truth is a divergence risk and requires explicit justification.

## 4. Decision / Evidence / Change Graph

Where material, operational work SHOULD be traceable as a graph rather than isolated checklist rows:

`PROJECT FACT / REQUIREMENT / RULE → ISSUE / WORK ITEM → OWNER / DUE / STATE → EVIDENCE → DECISION / APPROVAL → AFFECTED ITEM → DESIGN / CALCULATION / SUBMISSION REFLECTION → VALIDATION → SNAPSHOT / HISTORY`

A change to a material source value, rule, evidence item or decision SHALL identify affected downstream calculations, drawings, reports, submissions, tasks or approvals when applicable.

`VALUE CHANGED ≠ IMPACT CLOSED`
`DECISION RECORDED ≠ DECISION REFLECTED`
`DOCUMENT LINKED ≠ DOCUMENT VALIDATED`

## 5. Evidence / Knowledge Validity

Operational knowledge, wiki, SOP or reference pages that influence material work SHOULD preserve an owner, source, effective/valid date where relevant, verification state and review/expiry condition.

`VERIFIED PAGE BADGE ≠ LEGAL / TECHNICAL ACCURACY`
`WIKI EXISTS ≠ KNOWLEDGE CURRENT`
`SOP EXISTS ≠ SOP APPLIES TO THIS CASE`

Repeated/high-variance/handoff-critical work is a suitable SOP candidate. Not every task should be documented as an SOP merely because a workspace can store one.

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

At minimum, lower-layer design SHALL distinguish when applicable:
- authoritative entity / source version;
- projected workspace record ID;
- event/change ID;
- base version / concurrency evidence;
- pending / synced / failed / conflict state;
- evidence reference;
- bounded retry and escalation;
- reconciliation back to authority.

Browser or app offline features SHALL NOT be assumed to satisfy a project's offline correctness requirements. If reliable offline capture is required, the owning runtime/workflow must provide and validate a durable local queue/outbox, replay/idempotency, conflict policy and reconciliation path appropriate to the platform.

## 8. Tool-Specific Boundary: Notion

Notion may be used as an operational collaboration surface for projects, issues/tasks, decisions, evidence links, changes, snapshots, wiki/SOP and role-specific views.

Notion SHALL NOT become TAKY canonical authority by use alone.
Notion SHALL NOT replace approved spreadsheet calculation authority, CAD/BIM geometry/object authority, governed evidence/original-file storage, or explicit human approval where those remain the approved owners.

Notion database properties, relations, rollups, views, automations, verification and webhooks are capabilities. Their existence SHALL NOT be treated as proof that the underlying data is complete, correct, current, authorized or synchronized.

Exact database schemas, views, automations and connector configuration are owned by Work OS / Project masters, not GRAND MASTER core.

## 9. Validation / Reverse-Validation

For material operational-workspace changes, run distinct gates:

`ERROR VALIDATION → SELF-CORRECTION → SELF-VALIDATION → INDEPENDENT CROSS-VALIDATION → IMPACT VALIDATION → REGRESSION VALIDATION → REVERSE TRACE`

Validate both directions:

Forward:
`SOURCE / REQUIREMENT → OWNER → OPERATIONAL RECORD → EVIDENCE / DECISION → DOWNSTREAM REFLECTION → VALIDATION / HISTORY`

Reverse:
`VISIBLE STATUS / DASHBOARD / COMPLETION → RECORD → EVIDENCE / DECISION → SOURCE / AUTHORITY → VALIDATION EVIDENCE`

Mandatory failure patterns include:
- duplicated authority across tools;
- completed state without required evidence/review/approval;
- orphan operational records without project/source rationale;
- source changes without downstream impact tasks;
- dashboards based on stale/missing properties;
- manual copies drifting from the authoritative record;
- automation failure hidden as success;
- AI-generated conclusions promoted without authority/approval;
- offline/sync assumptions without tested reconciliation.

## 10. Disposition / Adoption Rule

External templates, videos, seller systems and community workflows are evidence/candidates only.

`TEMPLATE ≠ MASTER DECISION`
`POPULAR WORKFLOW ≠ FIT-FOR-PURPOSE`
`NOTION-ONLY ≠ BETTER SYSTEM`

TAKY SHALL extract transferable operating principles, localize them to actual tool authority and project constraints, then classify `PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED`.

Promotional performance claims, pricing funnels and testimonials are not adopted as governance evidence without independent validation.
