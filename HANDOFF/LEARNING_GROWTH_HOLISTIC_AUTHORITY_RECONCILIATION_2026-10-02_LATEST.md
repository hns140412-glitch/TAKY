# TAKY Learning Growth — Holistic Authority Reconciliation Handoff

Date: 2026-10-02
Status: VALIDATED_BRANCH_ARCHITECTURE
Main merge: HOLD
Deployment / Netlify: HOLD

## 1. Whole-system authority map

### Mining Engine
Owns:
- discovery strategy
- provider routing
- external acquisition
- counter-evidence acquisition

Does not own:
- source/index authority
- learner state
- pedagogy
- scheduling

### Mining Index
Owns:
- RAW / INDEX_L1 / DETAIL_L2 / CURRENT
- source identity / provenance / authority
- version / duplicate / fragment relations
- learning-evidence provenance tags

Does not own:
- pedagogy
- learner state

### Learning Index
Owns:
- rebuildable learning-semantic projection over indexed evidence
- curriculum alignment
- lexical semantics
- language usage
- pedagogical usage
- concept / transfer / confusion relations

Does not own:
- independent source authority
- learner state
- scheduling

Evidence-role separation:
- CURRICULUM_ALIGNMENT
- LEXICAL_SEMANTICS
- LANGUAGE_USAGE
- PEDAGOGICAL_USAGE
- GENERAL_REFERENCE

One role may not borrow another role's authority.

### Learning Engine
Owns:
- learner-state interpretation
- memory / accuracy / assistance / confusion interpretation
- language growth profile
- vocabulary / grammar / expression / thinking / English-thinking growth
- growth control
- question depth / hint policy
- review / diagnostic / remediation need
- growth outcome feedback candidates
- role-specific reference gaps

Does not own:
- external source acquisition
- source canonicalization
- assignment facts
- calendar dates

### Ready & Set
Owns:
- confirmed assignment decomposition
- operational execution-load metadata
- session / task execution continuity
- forwarding execution / friction evidence

Does not own:
- learner state
- growth control
- central review policy
- dated learning decisions by itself

Legacy Ready adaptive calculations:
- may exist as shadow / compatibility candidate
- execution_authorized = false

Ready local Hide memory review:
- may normalize legacy specialist results
- may not create local review policy
- may not create Planner review TODO
- central Learning Engine required

Carry-over friction:
- observation only
- carry preserved
- no local reinterpretation / cancellation / adaptive reallocation

### Hide & Seek
Owns:
- vocabulary / retrieval specialist interaction
- memory evidence production
- objective TRACE / LINK vocabulary observations

Does not own:
- long-term learner state
- dated review schedule
- growth control authority

Per-word auto routing / adaptive past-word ratio / delayed recall:
- CANDIDATE ONLY
- NOT CORE AUTHORITY

### Snap & Pop
Owns:
- child-authored expression / speaking / writing execution
- applied growth-control interaction
- production evidence
- human growth-rubric review request surface

Does not own:
- objective growth claims from completion
- global mastery
- Learning Engine authority

Snap completion:
- quality UNKNOWN until permitted evidence / rubric exists

### Planner
Owns:
- dates
- calendar placement
- rescheduling
- available-window allocation

Does not own:
- learner state
- pedagogical meaning
- growth level

## 2. Language-growth closed loop

DOMAIN / REFERENCE EVIDENCE
+
LEARNER EVIDENCE
-> LANGUAGE GROWTH PROFILE
-> GROWTH CONTROL
-> HIDE / SNAP EXECUTION
-> APPLIED CHALLENGE CONTEXT
-> RESULT / VERIFIED DIMENSION EVIDENCE
-> GROWTH OUTCOME FEEDBACK CANDIDATE
-> CUMULATIVE EVIDENCE
-> RE-DERIVE PROFILE
-> RE-DERIVE CONTROL

Growth dimensions:
- VOCABULARY
- GRAMMAR
- EXPRESSION
- THINKING
- ENGLISH_THINKING

Growth control:
- evidence confidence
- SUPPORT_BUILD / BUILD_CONNECT / STRETCH_TRANSFER
- expression L1..L5
- easy-English level
- question depth 1..5
- hint strength / fade
- challenge direction

## 3. Anti-tunneling hard locks

- Curriculum evidence does not become dictionary authority.
- Dictionary evidence does not become grade/curriculum authority.
- Corpus usage does not become curriculum authority.
- App completion does not become growth success.
- One success does not become a level promotion.
- Strong-scaffold success does not become stretch evidence by itself.
- Recent weakness may increase support without erasing stable growth.
- Ready execution friction does not become learner state.
- Review need does not become a review date.
- Learning Engine may emit a reference gap but may not authorize Mining.
- Specialist execution context is evidence context, not authority.

## 4. Role-specific missing-evidence route

Possible growth reference gaps:
- CURRICULUM_ALIGNMENT_REFERENCE_REQUIRED
- LEXICAL_SEMANTICS_REFERENCE_REQUIRED
- LANGUAGE_USAGE_REFERENCE_REQUIRED
- PEDAGOGICAL_LANGUAGE_SUPPORT_REFERENCE_REQUIRED

Route:
Learning Engine
-> Learning Index role check
-> Mining Index provenance-role check
-> existing role evidence: Index requery
-> insufficient role evidence only: Mining request
-> acquisition
-> Index owner review
-> Learning Index rebuild
-> Learning Engine requery

Learner-performance gap goes to specialist acquisition, not external Mining.

## 4A. Ready execution-friction route

Ready carry escalation is classified before Learning use.

Schedule/deadline pressure:
READY carry
-> Planner + Parent resolution
-> no Learning evidence

Repeated execution friction:
READY carry
-> READY_EXECUTION_FRICTION_OBSERVATION_ONLY
-> authenticated central evidence outbox
-> canonical READY_EXECUTION_FRICTION_OBSERVATION
-> excluded from learner performance evidence
-> no direct pedagogical decision
-> no direct Planner mutation

Hard locks:
- EXECUTION FRICTION != LEARNING FAILURE
- DEADLINE PRESSURE != LEARNER STATE
- OBSERVATION ACK != PEDAGOGICAL DECISION

## 5. Current branches

TAKY:
- taky/learning-mining-runtime-integration-2026-10-01

Ready:
- taky/ready-learning-authority-reconcile-2026-10-02

Hide:
- taky/hide-memory-routing-learning-engine-2026-10-02

Snap:
- taky/snap-growth-engine-handoff-2026-10-02

## 6. Validation snapshot

TAKY source-role separation:
- Integration 36899264513: SUCCESS
- Enforcement 36899264545: SUCCESS

TAKY explicit role-enforcement broker:
- Learning evidence-gap broker V4 directly validates required_learning_evidence_role against indexed provenance-role tags
- Integration 36899956987: SUCCESS
- Enforcement 36899957119: RUNNING_AT_HANDOFF_UPDATE

Ready authority reconciliation:
- local learner-adaptive review execution: DISABLED / shadow candidate only
- local Hide-memory review -> Planner scheduling: FAIL-CLOSED behind central Learning Engine
- carry escalation routing:
  - DEADLINE_EXCEEDED / REPEATED_CARRY_NEAR_DEADLINE -> Planner + Parent
  - REPEATED_CARRY_LIMIT -> central observation-only friction evidence
- Ready friction observation is centrally ACKed but cannot directly mutate Planner or learner state
- latest Integration 36901050524: SUCCESS
- latest Learning Runtime Bridge 36901050677: SUCCESS
- latest Runtime E2E 36901050649: RUNNING_AT_HANDOFF_UPDATE

Hide and Snap prior growth-axis branch regressions remain PASS.

## 7. Remaining OPEN

1. Complete latest Ready Runtime E2E 36901050649.
2. Target coverage guard:
   - current growth profile tracks target_id but broad dimension promotion does not yet require explicit target diversity;
   - repeated success on one target must not silently become broad vocabulary/expression growth;
   - do not hard-code a minimum count yet because target-specific skills and verified transfer contexts need separate treatment;
   - next design should distinguish TARGET_STABILITY from DIMENSION_GENERALIZATION.
3. Ready friction interpretation:
   - currently observation-only by design;
   - repeated carry must not become learning failure automatically;
   - any future diagnostic policy must separate workload/fatigue/context from learning difficulty.
4. Keep memory-routing trio as Candidate until separate approval.
5. Do not merge main / deploy yet.
6. Before promotion, run one final cross-repository authority regression:
   Mining / Index / Learning / Ready / Hide / Snap / Planner.
