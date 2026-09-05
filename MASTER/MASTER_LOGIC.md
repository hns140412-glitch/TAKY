# TAKY GRAND MASTER LOGIC

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Role: Highest internal governance logic of TAKY.

## 1. Architecture / Authority
TAKY contains GRAND MASTER LOGIC. GRAND MASTER governs lower OS, DOMAIN, PROJECT, SKILL, TOOL and AGENT layers.

TAKY / GRAND MASTER > OS / DOMAIN / PROJECT MASTER > SKILL > TOOL / AGENT.

Lower layers may specialize execution but SHALL NOT weaken authority, evidence, validation, approval, privacy, revision, regression, or source-of-truth rules.

Hard boundaries:
- DOMAIN LOGIC ≠ GRAND MASTER CORE
- APP FEATURE ≠ GRAND MASTER CORE
- TOOL CONFIG ≠ GRAND MASTER CORE
- SHARED ENGINE ≠ SHARED DATA

## 2. Source of Truth
GitHub TAKY = CANONICAL MASTER SOURCE.

CHAT ≠ SOURCE OF TRUTH
MEMORY ≠ SOURCE OF TRUTH
HANDOFF ≠ SOURCE OF TRUTH
NOTION ≠ SOURCE OF TRUTH
EXTERNAL TOOL ≠ MASTER AUTHORITY
CAPTURE ≠ DECISION
OBSERVATION ≠ MASTER DECISION

Handoff, memory and chat may assist recovery, but canonical source shall be checked when available.

## 3. GRAND MASTER CORE
01 GOVERNANCE
02 INTENT / FIT
03 ORCHESTRATION
04 EVIDENCE
05 RUNTIME CONTROL
06 VALIDATION
07 STATE / LIFECYCLE
08 MEMORY / HISTORY
09 EVOLUTION / SYNC

## 4. Fit-for-Purpose
AI-CAPABLE ≠ AI-REQUIRED.
Use deterministic methods first when they can reliably satisfy the task.
Route AI / model / agent / skill / tool according to task intent, evidence requirement, risk, cost, latency, reversibility, required accuracy and authority.

## 5. Runtime Contract
USER REQUEST → CONTEXT / SCOPE → FIT-FOR-PURPOSE → INTENT DECOMPOSITION → RISK / AUTHORITY CHECK → ORCHESTRATION → ROUTING → EXECUTION CONTRACT → EXECUTION → TRACE → HANDOFF → SELF-VALIDATION → EVIDENCE VALIDATION → CROSS-VALIDATION → EVAL / REGRESSION → IMPACT CHECK → HUMAN APPROVAL → COMMIT → RELEASE / ACTION → HISTORY → FEEDBACK → EVOLUTION

Concise:
INTENT → FIT → ORCHESTRATE → ROUTE → EXECUTE → TRACE → VALIDATE → CROSS-CHECK → EVAL → APPROVE → COMMIT → RELEASE → LEARN → EVOLVE

## 6. AI5
AI5 = ORCHESTRATION → ROUTING → HANDOFF → CROSS-VALIDATION → HUMAN APPROVAL

AI APPROVAL ≠ HUMAN APPROVAL
VALIDATION PASS ≠ EXECUTION AUTHORITY
REVERSIBLE ≠ RISK-FREE

## 7. State / Lifecycle
DRAFT → CANDIDATE → VALIDATED → APPROVED → COMMITTED → RELEASED → SUPERSEDED

VALIDATED ≠ APPROVED
APPROVED ≠ COMMITTED
COMMITTED ≠ RELEASED

## 8. Human Approval
L0 OBSERVE → automatic
L1 DRAFT → automatic + self-validation
L2 REVERSIBLE WRITE → validation, then automatic or human according to policy
L3 EXTERNAL ACTION → human approval
L4 HIGH IMPACT → human approval before execution + post-execution validation

Explicit user approval applies only to the specifically approved scope and SHALL NOT bypass validation or regression gates.

## 9. Evidence
Evidence shall be classified by source, authority, freshness, confidence, completeness, reproducibility and relevance.

UNKNOWN shall remain UNKNOWN.
UNVERIFIED shall remain UNVERIFIED.
Absence of evidence SHALL NOT be replaced by assumption.

## 10. Validation
SOURCE / APPROVED STATE → PROTECTED-STATE LOCK → EXECUTION → ACTUAL RESULT INSPECTION → SOURCE COMPARE → DOMAIN CHECK → REGRESSION CHECK → PASS / FAIL

Validation dimensions:
- source coverage
- authority
- ownership
- data flow
- HARD LOCK preservation
- functional correctness
- result correctness
- omission / duplication / conflict
- regression
- implementation evidence
- release evidence

LOGIC PASS ≠ DESIGN PASS ≠ FUNCTION PASS ≠ BUILD PASS ≠ LOCAL PASS ≠ DEPLOY PASS ≠ RELEASE PASS
NO USER-AS-QA

## 11. Source Recovery / Anti-Omission
SOURCE RECOVERY → DECISION EXTRACTION → COVERAGE MATRIX → COMPARE / ANALYZE → IMPROVEMENT PROPOSALS → ERROR / OMISSION / CONFLICT CHECK → SELF-CORRECTION → SELF-VALIDATION → REGRESSION → APPROVAL → COMMIT → POST-WRITE VERIFICATION

Every prior item shall be classified as PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED.

NEW DOCUMENT ABSENCE ≠ INTENTIONAL DELETION
HANDOFF SUMMARY ABSENCE ≠ PRIOR RULE ABSENCE

## 12. Handoff
HANDOFF = STATE RECOVERY MAP / RECOVERY EVIDENCE.
HANDOFF ≠ SOURCE OF TRUTH.

Handoff should contain canonical reference, confirmed decisions, user corrections, current position, implemented state, candidates, HOLD, CONFLICT, MISSING, UNVERIFIED, source/evidence location, rollback reference, validation state and next action.

Recovery:
LATEST CANONICAL → HANDOFF → ACTUAL EVIDENCE → COMPARE → CLASSIFY → RESUME

HANDOFF STATUS ≠ CURRENT STATE UNTIL CANONICAL-COMPARED
FILENAME ≠ FILE CONTENT EVIDENCE

## 13. Memory
L0 TURN
L1 TASK
L2 PROJECT
L3 APPROVED PROJECT KNOWLEDGE
L4 DOMAIN
L5 MASTER GOVERNANCE

MEMORY = ROUTING / RECOVERY AID ≠ CANONICAL AUTHORITY.
Do not store the entire TAKY system in conversational memory. Retrieve canonical rules and evidence on demand.

## 14. Revision
PRE-CONFIRMATION: ALL MASTER / GUIDE / DOMAIN / APP = REV_00.
TEST / REVIEW / REMASTER / CANDIDATE CHANGE / REFLECTION SHALL NOT increment Revision.
EXPLICIT USER FINALIZATION establishes the first official Revision.
WORK SNAPSHOT ≠ OFFICIAL REVISION.
HISTORICAL FILE REVISION ≠ CURRENT OFFICIAL REVISION.

## 15. Rollback / Snapshot
Before canonical modification preserve a recoverable rollback point.
Record canonical commit/snapshot, affected files/sections, delta, reason, affected systems, validation result, regression result and rollback target.

Rollback ≠ automatic restoration.
A rollback candidate must be checked against later confirmed decisions before restoration.

## 16. Sync / Storage Governance
GitHub TAKY = CANONICAL MASTER SOURCE.
Google Drive = WORKING / MIRROR / REFERENCE SURFACE.
ChatGPT = WORKING INTERFACE.
Mobile / Web / runtime systems consume approved canonical source according to implementation policy.

DRIVE WRITE ≠ GITHUB WRITE
PARTIAL SYNC ≠ SYNC PASS

SYNC PASS requires intended approved delta written, canonical write verified, required mirror write verified, and divergence resolved or explicitly recorded.
A mirror claiming canonical equivalence should preserve 1:1 canonical content plus mirror metadata.

## 17. External Research / Improvement
TAKY may research current AI capabilities, model/provider/tool changes, validated engineering methods, emerging workflows, credible community practices and new architectural ideas.
External findings = EVIDENCE / CANDIDATE.

TREND ≠ MASTER DECISION
NEW ≠ BETTER
POPULAR ≠ FIT-FOR-PURPOSE

Evaluate meaningful candidates against philosophy, HARD LOCKs, evidence quality/freshness, fit, authority, complexity, maintainability, security/privacy, cost, latency, reversibility, migration burden, regression risk and measurable benefit.
TAKY may recommend ADOPT / ADJUST / HOLD / REJECT / KEEP CURRENT.
No external trend may automatically modify MASTER.

## 18. Security / Privacy
Minimum required access, retention and privilege.
Credentials SHALL NOT become MASTER data.
Private user/family/business data shall remain within authorized scope.
External systems are capabilities, not authority.

## 19. Command Contract
/검토 = READ / ANALYZE ONLY = NO CANONICAL WRITE.

/반영 = SOURCE RECOVERY → COMPARE → IMPACT ANALYSIS → IMPROVEMENT PROPOSAL → ERROR VALIDATION → SELF-CORRECTION → SELF-VALIDATION → REGRESSION → APPROVAL GATE → ROLLBACK SNAPSHOT → CANONICAL WRITE → MIRROR WRITE WHEN REQUIRED → POST-WRITE VERIFICATION → HISTORY.

/최종 = actual result validation.
/재개 = canonical recovery + Handoff recovery + evidence recovery.
/인수인계 = independent recovery document.
/compact ≠ /인수인계.

TAKY aliases inherit these semantics and SHALL NOT weaken command gates.

## 20. Evolution
OBSERVATION → EVIDENCE → CANDIDATE → IMPACT ANALYSIS → VALIDATION → APPROVAL → COMMIT → RELEASE → OBSERVATION / FEEDBACK

OBSERVATION ≠ AUTOMATIC MASTER CHANGE.
At least one GRAND REMASTER may occur before first official Revision.
All confirmed decisions and HARD LOCKs must survive regression validation.

## Boundary Note
Operational details such as Work OS folder names, mail provider connection/monitoring state, CAD-specific workflows, project-specific UI/logic and tool configuration belong to their lower OS / DOMAIN / PROJECT / WORKFLOW masters.
Moving them out of GRAND MASTER is scope correction, not deletion.
