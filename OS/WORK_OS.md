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

### 1.0A Work OS / Learning OS sibling boundary — HARD LOCK

Work OS is not the parent/common semantic container of Learning OS.

Current relation:
`TAKY -> WORK_OS`
`TAKY -> LEARNING_OS`

They may reuse semantic-light shared technical mechanisms, but Work organization/team roles, permissions, approvals and project-task meaning remain Work-owned. Family/child/parent identity, learning roles and learning-plan meaning remain Learning-owned.

Cross-domain linkage, if ever required, SHALL use an explicit scoped federation/projection contract rather than implicit role/identity inheritance.

Machine-readable support map:
`MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json`.

## 1.1 Productive execution pipeline — HARD LOCK

Work OS default productive rhythm:
`GOAL -> DISCOVER -> BUILD -> VERIFY -> SHIP -> LEARN`.

Meaning:
- GOAL: define the useful outcome and protected constraints.
- DISCOVER: gather only the evidence/options needed to act.
- BUILD: create/improve the actual result.
- VERIFY: run material checks tied to real risk/claim.
- SHIP: deliver or hand off the authorized result.
- LEARN: capture reusable lessons/assets and next growth opportunity.

`VERIFY != CENTER OF WORK`.
`NO BUILD DELTA + MORE CHECKS AVAILABLE != PRODUCTIVE PROGRESS`.

Machine routing baseline:
`OS/ACTION_SKILL_REGISTRY.json`
`ENFORCEMENT/work_os_productive_router.py`.

### _LAB ideation routing

Ideas are routed to `_LAB` with minimal metadata:
`idea / novelty / usefulness / cost / evidence_state`.

`_LAB != CANONICAL`.
The router SHALL NOT auto-promote ideas into MASTER/project requirements.

### Visualization routing

Default relationship mapping:
- comparison -> table
- process/sequence -> flow diagram
- numeric relation -> chart
- interface structure -> wireframe
- spatial location -> map
- simple explanation -> text

This is a working-output choice, not a governance authority.

## 1.2 Reusable recipe registry

Reusable operating recipes are registered in:
`OS/ASSET_SKILL_RECIPE_REGISTRY.json`.

A recipe is allowed only when it represents a real recurring workflow with evidence pointers.
Required semantics include:
`recipe_id / owner / version / evidence_count / source_pointers / preserve / allowed_change / rights_or_consent / verification / utilization / deprecation`.

`RECIPE != CANONICAL AUTHORITY`.
`ONE-OFF TASK != REUSABLE RECIPE`.
`RECIPE WITHOUT EVIDENCE != ACTIVE RECIPE`.

Recipes should reduce repeated reconstruction while preserving source authority, rights/consent boundaries, and validation requirements.

## 1.3 Volatile capability registry

Claims about tools, models, connectors, costs, quotas, compatibility and availability can become stale.
Material routing or user-facing decisions that rely on such claims SHOULD use:
`OS/VOLATILE_CAPABILITY_REGISTRY.json`.

Each volatile claim must retain:
`checked_at / source / freshness_ttl / recheck_trigger / fallback / owner`.

`PAST CAPABILITY != CURRENT CAPABILITY`.
`STALE CLAIM != ROUTING AUTHORITY`.

When a material claim is outside its freshness window or a recheck trigger fires, Work OS must refresh the claim before using it to choose a route or make a definitive current-state statement.

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


## 10. Production Execution / User Exposure Governance — HARD LOCK (2026-09-23)

This section corrects a structural failure discovered during the Hannam drawing/report workflow.

### 10.1 Engine enforcement

A reusable engine is not considered operational merely because code exists.

`ENGINE_AVAILABLE + BYPASS_USED = GOVERNANCE_FAILURE`

For governed production work, the allowed path is:

`TASK -> ROUTER -> AUTHORIZED_ENGINE -> VALIDATION -> USER_EXPOSURE_GATE -> OUTPUT`

A one-off Python script, ReportLab routine, generic HTML generator, raster masking script, generative redraw path, or similar local workaround MAY be used only as `EXPERIMENT / DIAGNOSTIC` unless explicitly registered as an authorized engine.

`EXPERIMENT / DIAGNOSTIC != PRODUCTION_RESULT`
`ONE_OFF_SCRIPT != USER_FACING_ARTIFACT_AUTHORITY`

If an authorized engine exists for the task, a bypass path SHALL NOT create FINAL, PREVIEW-as-final, RELEASE, or other user-facing production artifacts.

### 10.2 Layer authority

Drawing/presentation execution SHALL preserve this authority order:

`L0 SOURCE AUTHORITY`
`L1 GEOMETRY`
`L2 SEMANTIC`
`L3 PRESENTATION`
`L4 ENTOURAGE`
`L5 ANNOTATION`
`L6 AI / ATMOSPHERE`
`L7 FINAL VALIDATION`
`L8 USER EXPOSURE GATE`

No lower-authority layer may mutate a higher-authority layer without an explicit governed contract.

In particular:
- raster masks cannot have destructive authority over protected geometry;
- generative output cannot become geometry authority;
- presentation cannot precede semantic verification;
- narrative claims cannot exceed evidence strength.

### 10.3 No Pass -> No Show

User-facing production output requires all applicable gates to PASS before exposure.

Minimum gate family:
- SOURCE_GATE
- GEOMETRY_GATE
- FACT_GATE
- SEMANTIC_GATE
- REFERENCE_EFFECT_GATE
- ARCHITECTURAL_READABILITY_GATE
- A3_GATE when applicable
- USER_EFFECT_GATE

`ANY REQUIRED GATE != PASS -> USER EXPOSURE BLOCKED`

This is an execution rule, not a reporting convention. A failed result may be retained internally as diagnostic evidence but SHALL NOT be presented as a completed or approved result.

### 10.4 User is not the debugger

`HUMAN IS THE KEY != HUMAN IS THE DEBUGGER`
`USER != DEBUGGER`

Human approval is reserved for final judgment, design choice, policy choice, or intentional ambiguity that genuinely requires human authority.

Errors that can be mechanically or evidentially checked before exposure — including missing walls/cores/entries, wrong rotation/crop, unverified semantics, unsupported narrative, missing reference effect, generic layout regression, or engine bypass — SHALL be treated as PRE-USER VALIDATION responsibilities.

### 10.5 Reference compiler requirement

Reference mining is not complete until reusable DNA is compiled into execution parameters.

Required trace:

`REFERENCE -> MINED_DNA -> DESIGN_TOKEN -> ENGINE_PARAMETER -> OUTPUT_EFFECT -> VALIDATION`

A reference name or prose description alone SHALL NOT count as applied reference utilization.

`REFERENCE_MENTIONED != REFERENCE_APPLIED`
`CLARITY_GAIN != REFERENCE_EFFECT`

### 10.6 Source freshness

Modification time is evidence about file activity, not proof of content change.

`DATE != CONTENT CHANGE`

Freshness/supersession decisions SHOULD use content identity, revision evidence, source authority, or verified semantic/geometry deltas when available. A later timestamp alone SHALL NOT demote content-identical evidence.

### 10.7 Resume mode vs surgery mode

Handoff MUST declare the intended continuation mode when material:

- `RESUME`: continue a validated structure from current state.
- `RETROSPECTIVE`: analyze failures without continuing production.
- `SURGERY`: change execution contracts/architecture because the current structure is unsafe or ineffective.
- `RE_ARCHITECTURE`: supersede/deprecate structural assumptions and rebuild routing/ownership.

A resume packet SHALL NOT force continuation when evidence shows the preserved structure is itself defective.

`HANDOFF != STRUCTURAL IMMUNITY`
`RESUME != REPEAT THE SAME FAILURE PATH`

### 10.8 Quality state separation

The following states are independent and SHALL NOT be collapsed:

`SOURCE_FIDELITY != PRESENTATION_QUALITY`
`CLARITY_GAIN != REFERENCE_EFFECT`
`CODE_PASS != PRODUCT_PASS`
`ENGINE_PASS != VISUAL_PASS`

Geometry preservation is necessary for drawing work but is not sufficient evidence of presentation quality or professional-family equivalence.
