# TAKY Learning Evidence I/O Closure — 2026-10-02

Status: CLOSED / BRANCH VALIDATED
Scope: Learning evidence ownership + Learning Engine output + Planner materialization
Main merge: HOLD
CURRENT promotion: HOLD
Canonical promotion: HOLD
Deployment: HOLD

## 1. Canonical closed loop

PLANNER ALLOCATION
-> READY EXECUTION
-> READY / HIDE / SNAP / IMAGINATION CLOUD RAW EVIDENCE
-> TAKY LEARNING ENGINE INTERPRETATION
-> REVIEW NEED / LEARNING INTENSITY / RECOMMENDED QUANTITY INTENT / QUESTION-HINT-GROWTH INTENT
-> READY PLANNER DATE + ACTUAL QUANTITY MATERIALIZATION
-> READY EXECUTION

Learning Engine never owns dates or actual allocated quantity.
Planner never owns learner state or pedagogical meaning.

## 2. Common raw-evidence identity

Official contract:
- LEARNING/contracts/learning-evidence-io-contract.js
- LEARNING/contracts/learning-engine-output-contract.js
- LEARNING/adapters/canonical-evidence.js

Session/task evidence preserves:
- member / learner
- session_id
- task_id
- lap / segment
- assignment_id where available
- subject
- concept / skill target
- learning_target_id
- source app / source event
- observed_at

Cross-session Ready friction is explicit AGGREGATED_EXECUTION.
No fake session/task identity is manufactured.

Reference provenance is role-separated:
- CURRICULUM_ALIGNMENT
- LEXICAL_SEMANTICS
- LANGUAGE_USAGE
- PEDAGOGICAL_USAGE
- GENERAL_REFERENCE

Role authority comes from indexed / Learning Index metadata.
Provider name / file title / similar text may not invent a role.

## 3. Ready & Set evidence

Ready owns execution facts only:
- Planner allocation provenance/value
- actual start / end
- actual elapsed time
- performed quantity when directly known
- task execution state
- blocking reason
- explicit parent confirmation
- session/task/lap continuity

Ready execution fact and execution friction:
- do NOT count as learner performance
- do NOT change retention interpretation
- do NOT change recovery interpretation
- do NOT create learner state
- do NOT create local review TODO from Hide advisory

Validated Ready branch:
taky/ready-learning-authority-reconcile-2026-10-02
validated SHA: 731b498fc56df8c1b9cc822c012000fe6a1062d8

Validation:
- Ready Integration CI 36939086823 — SUCCESS
- Learning Runtime Bridge Validation 36939086822 — SUCCESS
- Ready Runtime E2E 36939086862 — SUCCESS

## 4. Hide & Seek evidence

Hide owns memory / retrieval observations:
- correct / incorrect where objectively observed
- confusion
- hint stage
- help / assistance
- response latency
- self-correction where directly observed
- recall observation where directly measured or explicitly reported
- LINK connection evidence
- CORE spelling evidence
- interaction mode
- word / item identity
- source sheet
- role-specific reference refs carried from central intent

TRACE / LINK / CORE emit actual telemetry.
Hide never owns mastery, long-term learner state or dated review scheduling.

Validated Hide branch:
taky/hide-memory-routing-learning-engine-2026-10-02
validated SHA: 706a12bd247d4fd6a0a8df7a94c6a17b218ecb00

Validation:
- Learning Runtime Bridge Validation 36941552630 — SUCCESS
- Validate Hide & Seek 36941552685 — SUCCESS

CANDIDATE ONLY — NOT CORE:
- per-word automatic memory-state routing
- adaptive past-word ratio
- delayed-recall automation

## 5. Snap & Pop evidence

Snap preserves child-authored raw production:
- production text / transcript when available
- actually reused handoff vocabulary
- raw step structure / lengths
- applied growth-control context
- pending growth-review dimensions
- role-specific reference refs carried from central intent

Automatic completion does NOT grade:
- grammar stability
- expression quality
- reasoning quality/depth
- perspective shift quality
- story quality
- direct-English thinking quality
- reuse quality
- self-correction quality

These stay UNKNOWN / UNVERIFIED until permitted verification,
including dimension-level HUMAN_GROWTH_RUBRIC evidence.

Validated Snap branch:
taky/snap-growth-engine-handoff-2026-10-02
validated SHA: 1250b8871f8d9ae7c460f183d65f849aabe10a3d

Validation:
- Learning Runtime Bridge Validation 36941557539 — SUCCESS
- Validate Snap & Pop 36941557533 — SUCCESS

## 6. Imagination Cloud evidence

Official producer contract:
LEARNING/contracts/imagination-cloud-evidence-contract.js

Records support observation only:
- invocation reason
- target concept
- visualization used
- explanation used
- response before support
- response after support
- additional help needed
- curiosity-only

It cannot set:
- mastery
- learner state
- review policy
- schedule
- pedagogical decision

LEARNING_SUPPORT_OBSERVATION does NOT count as learner performance,
retention evidence or recovery evidence.

## 7. Learning Engine output

Learning Engine may emit:
- learner-state interpretation
- review need
- learning intensity
- recommended quantity intent
- question depth / difficulty intent
- hint policy / fading
- next growth intent
- role-specific reference gaps

Consequential output preserves:
- learner evidence IDs
- indexed source refs
- confidence / basis where available

Forbidden:
- schedule_date
- planner_date
- deadline
- calendar_time
- allocated_date
- actual allocated_quantity

recommended_quantity:
- authority = LEARNING_ENGINE_QUANTITY_INTENT_ONLY
- planner_must_materialize = true
- allocated_quantity = null

Nested date or actual allocation leakage is recursively rejected.

## 8. Planner materialization

Planner alone turns Learning intent into:
- date
- calendar placement
- actual quantity
- rescheduling

Planner allocation authority:
READY_SET_PLANNER_ALLOCATION

Hard lock:
LEARNING ENGINE RECOMMENDED QUANTITY != PLANNER ALLOCATED QUANTITY

## 9. Indexed reference state

V27 receipt:
MIGRATION/INDEX_OWNER/DATA_INDEX_V27_INDEX_OWNER_RECEIPT_2026-10-02_V1.json

State:
- base: 679
- added: 178
- total: 857
- CURRICULUM_ALIGNMENT: 177 INDEXED
- LEXICAL_SEMANTICS: OEWN 2025 x1 INDEXED
- LANGUAGE_USAGE: 0 / HOLD

V27 is:
INDEXED
NOT CURRENT
NOT CANONICAL
NO CURRENT POINTER CHANGE
NO MAIN MERGE
NO DEPLOYMENT

OEWN guard:
OEWN gloss != child-level easy English.
Easy-English wording remains derived + traceable + attributable.

## 10. Final TAKY validation

Validated implementation SHA:
6ef9f12283a78de25ad10d4f347ccd5bf5212396

- TAKY Mining Indexing Learning Integration
  run 36941955807 — SUCCESS
- TAKY Enforcement Replay
  run 36941955742 — SUCCESS

The authority matrix itself also passed after V27 state correction:
- Integration 36941873993 — SUCCESS
- Enforcement 36941873964 — SUCCESS

## 11. Remaining OPEN

Separate from this CLOSED I/O scope:

1. LANGUAGE_USAGE source
- UD English-EWT remains precheck candidate
- license / ShareAlike compatibility + Index Owner review OPEN
- no indexed LANGUAGE_USAGE authority yet

2. Hide enhancement candidates
- per-word automatic routing
- adaptive past-word ratio
- delayed recall automation

3. Governance / release gates
- CURRENT promotion: HOLD
- CANONICAL promotion: HOLD
- main merge: HOLD
- deployment: HOLD
- require separate human approval / release gate

## 12. Non-regression locks

RAW APP EVIDENCE != LEARNER STATE
READY EXECUTION FACT != LEARNER PERFORMANCE
READY EXECUTION FRICTION != LEARNING FAILURE
IMAGINATION CLOUD SUPPORT != MASTERY
SNAP COMPLETION != GROWTH SUCCESS
HIDE MEMORY EVIDENCE != MASTERY
REVIEW NEED != REVIEW DATE
LEARNING ENGINE != SCHEDULER
PLANNER != PEDAGOGICAL INTERPRETER
LEARNING ENGINE RECOMMENDED QUANTITY != PLANNER ALLOCATED QUANTITY
CURRICULUM_ALIGNMENT != LEXICAL_SEMANTICS
LEXICAL_SEMANTICS != LANGUAGE_USAGE
INDEXED != CURRENT
INDEXED != CANONICAL
USER != DEBUGGER
