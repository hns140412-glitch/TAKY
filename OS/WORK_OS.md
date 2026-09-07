# TAKY WORK OS

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Role: Operational OS layer under TAKY / GRAND MASTER.

## 1. Authority / Boundary

Authority inherits:
`TAKY / GRAND MASTER > OS / DOMAIN / PROJECT MASTER > SKILL > TOOL / AGENT`

This document owns cross-project operational workflows. It SHALL NOT weaken GRAND MASTER governance, evidence, validation, approval, privacy, revision, regression, source-of-truth, Deep Analysis, anti-omission, traceability, or operational-workspace authority rules.

Operational details belong here or in subordinate modules rather than GRAND MASTER core.

Normative operational-workspace governance:
`MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md`

Central `TAKY/OS/WORK_OS.md` is the normative cross-project Work OS semantic contract.
The `TAKY-WORK-OS` repository is a subordinate implementation / operating repository for reusable workflows, automation, schemas, scripts and integrations.
When an external Work OS rule conflicts with this central contract, central TAKY authority governs unless an approved ownership change explicitly says otherwise.
The implementation repository SHOULD record the inherited central Work OS contract/version where useful for drift control.

## 2. Conversation Continuity / Persistent Work Surfaces

`CONTINUITY IS THE PURPOSE; FOLDERS ARE IMPLEMENTATION SURFACES`

The purpose of Work OS continuity is to preserve recoverable sources, decisions, user corrections, HOLD / CONFLICT / SUPERSEDED state, work state and next action across conversations and work sessions.

TAKY Work OS SHALL preserve the distinction between conversation convenience and actual persistent storage.

Canonical operational surfaces:
- `_PROJECTS` = project-classified persistent work
- `_TEMP` = conversation files / materials whose project destination is not yet reliable
- `_HANDOFF` = latest and historical handoff packets and resume pointers
- `_LAB` = pre-canonical ideas, experiments, research and exploratory references
- `_COMMON` = reusable shared working resources

`CHAT ATTACHMENT EXISTS ≠ PERSISTENT FILE SAVED`
`FILE NAME RECORDED ≠ FILE BYTES RECOVERABLE`
`HANDOFF POINTER EXISTS ≠ POINTER RECOVERABLE`

For a material conversation file, Work OS should verify whether the source was actually persisted before later claiming recoverability.
If project identity is clear, classify to the applicable project work item.
If material ambiguity remains, preserve in `_TEMP` rather than guessing a project.

`_LAB` content SHALL NOT automatically become MASTER, approved project requirement or implementation scope.
LAB promotion requires later review and applicable user approval.

`_LAB` is schema-light by default.
The user SHALL NOT be required to classify an idea into a rigid taxonomy before saving it.
TAKY may maintain internal semantic tags, relations, project affinity and resurfacing metadata.
When new work materially relates to a LAB item, TAKY may surface the matching candidate for `ADOPT / HOLD / REJECT` review.

`LAB RELEVANCE ≠ AUTO-PROMOTION`

Historical rigid user-facing trees such as `Inbox / Ideas / Research / AI / YouTube / Incubator / Adopted` are not mandatory Work OS structure.

## 3. Attachment / Source Registry — IMPLEMENTATION CONTRACT

Work OS shall maintain or provide an equivalent recoverable index for material conversation attachments and generated source-dependent artifacts.

Required semantic fields:
- source/attachment identity
- conversation or work-item relation
- original filename
- project/classification when known
- intended/actual destination
- persistence status
- persistence verification time/evidence
- original vs derived status
- handoff/source pointer
- checksum/version when available and useful

Exact schema names remain implementation-owned; the semantic requirements above are normative.

A failed or unsupported save SHALL be reported as failed/unsupported and SHALL NOT be rewritten as completed.

## 4. Conversation Close / Resume Workflow

When the user requests conversation close, full preservation or handoff, the workflow should, within available tool capability:

`FILES USED / UPLOADED → PERSISTENCE CHECK → TEMP / PROJECT CLASSIFICATION → USER CORRECTIONS → CONFIRMED / HOLD / CONFLICT / SUPERSEDED → CURRENT STATE → NEXT ACTION → HANDOFF → SOURCE POINTERS → RESUME INSTRUCTION`

Handoff filenames should avoid collisions and preserve latest/history distinction.

On `/재개`, TAKY SHALL use Handoff as a recovery index and follow relevant actual files, folders, archives and project sources when available.

`HANDOFF = RECOVERY INDEX / EVIDENCE, NOT RECOVERY BOUNDARY`

Role separation:
- `RAW BACKUP = EVIDENCE ARCHIVE`
- `HANDOFF = RESUME / RECOVERY INDEX`
- `RECOVERY LEDGER = DECISION RECONSTRUCTION`
- `CANONICAL = ACTIVE GOVERNED RULE`

`BACKUP ≠ HANDOFF`

## 5. Notion Operations

Notion is an operational collaboration/work-management surface, not TAKY canonical authority and not a replacement for approved numeric/calculation, geometry/drawing, original evidence-file, legal/regulatory or official approval authorities.

Detailed contract:
`OS/NOTION_OPS.md`

Hard rules:
- `NOTION ≠ SOURCE OF TRUTH`
- `PROJECTION WRITE ≠ SOURCE COMMIT`
- `STATUS = COMPLETE ≠ EVIDENCE OF COMPLETION`
- `ROLE VIEW ≠ DUPLICATE DATABASE`
- `AI SUMMARY ≠ OFFICIAL VALUE`
- `AUTOMATION START ≠ OFFICIAL CONFIRMATION`

Current connected-Notion implementation state from the 2026-09-05 reflection:
- reusable Notion operating logic: LOGIC INTEGRATED
- verified Projects/Issues/Decisions/Evidence/Changes/Snapshots workspace implementation: UNVERIFIED
- Notion automation runtime: UNVERIFIED
- offline/conflict/reconciliation runtime: UNVERIFIED

## 6. Mail Operations

Mail operations are a lightweight business-record / mail-history / archiving capability. They are separate by default from architecture design-overview, calculation, release, and submission logic. A project/domain may link mail evidence later without changing this ownership boundary.

Module ownership:
- MAIL HISTORY: reconstruct business correspondence and decisions.
- MAIL ARCHIVER: preserve message and attachment artifacts.
- THREAD RECONSTRUCTOR: connect request → reply → follow-up → response → closed/open.
- CONTACT EXTRACTOR: retain confirmed business contact details and history.
- PROJECT CLASSIFIER: assign or suggest project association without guessing.

Detailed contract: `OS/MAIL_OPS.md`.

## 7. Mail Runtime State

Provider connection state is operational evidence, not permanent MASTER truth. It must be rechecked from the actual provider/connector when execution depends on it.

Current verified state at 2026-09-05 KST:
- NATE `soma17@nate.com` via Custom IMAP `imap.nate.com`: ACTIVE / ONBOARDING COMPLETED / SYNCING.
- Read / send / organize capabilities: enabled.
- Connection success SHALL NOT be interpreted as autonomous monitoring, local archiving, or E2E archive validation.

Hard rules:
- MAIL CONNECTION ≠ MAIL MONITORING ENABLED
- MAIL SYNC ≠ ARCHIVE COMPLETE
- ARCHIVE LOGIC PASS ≠ LOCAL AUTOMATION PASS
- PROVIDER STATE IN HANDOFF ≠ CURRENT STATE UNTIL RECHECKED

## 8. Validation State

- Operational Workspace Protocol placement: PASS
- Notion Ops ownership placement: PASS
- Notion live operational schema/runtime: UNVERIFIED
- MAIL OPS ownership placement: PASS
- Mailopoly/NATE connection: VERIFIED ACTIVE at stated check time
- Thread reconstruction design: LOGIC PASS / IMPLEMENTATION NOT VALIDATED
- PDF + EML archival design: LOGIC PASS / IMPLEMENTATION NOT VALIDATED
- Project classification design: LOGIC PASS / IMPLEMENTATION NOT VALIDATED
- Windows/local staging archive: NOT IMPLEMENTED
- Full MAIL OPS E2E: NOT YET PASS
- Conversation continuity logic placement: INTEGRATED / RUNTIME VALIDATION REQUIRED
- Attachment/source registry semantic contract: INTEGRATED / IMPLEMENTATION NOT VALIDATED

## 9. Revision

Per GRAND MASTER governance, `/반영` does not increment Revision. This remains REV_00 until explicit user finalization establishes an official revision.
