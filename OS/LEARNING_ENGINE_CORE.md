# Learning Engine Core — Independent Domain Contract

Status: ACTIVE_CANDIDATE_V2
Date: 2026-09-25
Parent authority: TAKY -> LEARNING_OS -> LEARNING_ENGINE_CORE
Related apps: Ready & Set / Hide & Seek / Snap & Pop are consumers/adapters, not the engine.

## 0. Purpose

Learning Engine Core is the domain intelligence that turns verified learning facts and learning evidence into an explainable learner state and pedagogical intent.

It does NOT own:
- calendar dates or time slots;
- family capacity allocation;
- Ready session runtime;
- Hide/Snap interaction UI;
- assignment fact capture;
- deploy/platform mechanics.

Core invariant:

FACT + DOMAIN INTERPRETATION + LEARNER EVIDENCE
-> LEARNER SKILL STATE
-> PEDAGOGICAL INTENT
-> ADAPTER / PLANNER

LEARNING ENGINE CORE != READY & SET
LEARNING ENGINE CORE != PLANNER
LEARNING ENGINE CORE != SPECIALIST APP
REVIEW NEED != REVIEW DATE

## 1. Why V2 exists

External comparison identified four useful patterns:

1. Bayesian Knowledge Tracing: per-skill latent state, guess/slip/learn uncertainty, individualized parameters.
2. FSRS / DSR: separate difficulty, stability and current retrievability; memory state is not the same thing as a due date.
3. Open adaptive-learning implementations: mastery and memory are separate concerns and can drive different interventions.
4. Production/community failure evidence: ambiguous rating semantics, invalid inputs and scheduler/user-model coupling can corrupt adaptation.

TAKY localization:
- keep skill state explicit and inspectable;
- never infer a precise mastery probability before an estimator is calibrated;
- preserve observation provenance;
- keep scheduler/date authority outside Core;
- allow multiple estimators behind one stable Core contract.

## 2. Core ownership

Learning Engine Core owns:
- learner-state schema;
- evidence normalization and provenance requirements;
- concept/skill scoped state derivation;
- uncertainty / evidence sufficiency;
- memory / mastery / assistance / confusion signals;
- pedagogical review need and strategy intent;
- estimator registry and estimator-version provenance;
- policy explanation.

Learning Engine Core does not own:
- dated TODO;
- deadline;
- calendar availability;
- family schedule;
- session runtime state;
- UI navigation;
- specialist app world/reward;
- child/parent account authority.

## 3. Scope key

Primary learner-state key:

member_id x subject x concept_skill_target

Optional deeper key:
skill_variant / item_family / lexical_id / misconception_id

Subject-only state is a roll-up/projection, not the primary adaptive state.

## 4. Evidence contract

Minimum evidence fields:
- event_id
- observed_at
- member_id
- subject
- concept_skill_target
- evidence_type
- source_app
- instrument_version
- interaction_mode
- assisted / unassisted / unknown
- attempt_count when meaningful
- response_latency_ms when meaningful
- outcome semantics
- provenance / authority

Hard locks:
- CHILD_SELF_REPORT != VERIFIED_PERFORMANCE
- HELP != FAILURE
- LONG_TIME != STUCK
- COMPLETED != MASTERED
- SINGLE_SUCCESS != STABLE_MASTERY
- APP_SCORE != UNIVERSAL_MASTERY_SCORE
- MISSING_FIELD != NEGATIVE_EVIDENCE

## 5. Learner Skill State V2

Core state contains observed facts and inferred state separately.

Observed:
- unique_evidence_count
- spaced_observation_days
- first_observed_at / last_observed_at
- assisted_count / unassisted_count
- success/failure/partial counts where evidence semantics permit
- memory strengths / priorities when supplied
- source/instrument versions

Inferred:
- evidence_sufficiency: NONE / SPARSE / EMERGING / ESTABLISHED
- trend: INSUFFICIENT_EVIDENCE / IMPROVING / STABLE / DECLINING
- assistance_dependency_signal
- repeated_confusion_signal
- retention_signal
- mastery_estimate: nullable
- mastery_confidence: UNKNOWN until an estimator is bound
- estimator_id / estimator_version

No precise mastery probability may be emitted by the default observational model.

## 6. Estimator architecture

Stable Core API, replaceable estimator.

Candidate estimators:
- OBSERVATIONAL_V1: deterministic, explainable, no false mastery precision.
- BKT_ADAPTER: future calibrated per-skill probabilistic mastery.
- MEMORY_DSR_ADAPTER: future FSRS-inspired memory-state estimator for retrieval-heavy skills.

Estimator selection is evidence/domain dependent.
Do not force a memory model onto reasoning/writing/performance tasks.

Any estimator must provide:
- estimator_id
- estimator_version
- required evidence semantics
- calibration provenance
- confidence / uncertainty
- explanation
- forbidden outputs

## 7. Pedagogical intent

Core may output:
- RETRIEVE
- RELEARN
- UNDERSTAND
- APPLY
- COMPARE
- EXPLAIN
- VISUALIZE
- PRACTICE
- CREATE
- PERFORM
- REFLECT
- SHORT_CHECKPOINT
- RETRIEVAL_CHECKPOINT

Core may output review urgency/need:
- UNKNOWN
- LOW
- MEDIUM
- HIGH

Core must not output:
- schedule_date
- planner_date
- due_at
- fixed calendar time.

Planner/Main converts pedagogical need + family constraints into actual placement.

## 8. Adapter boundaries

Ready Adapter:
- sends confirmed assignment context and execution evidence to Core;
- consumes learning-unit/pedagogical intent;
- may own assignment decomposition and execution-load metadata only;
- local review logic is fallback-only when central Learning Engine is unavailable;
- central Learning Engine takes precedence for learner state, growth control and review policy;
- Planner remains the only dated allocation owner;
- must not become learner-model or growth-control authority.

Hide Adapter:
- sends retrieval evidence with interaction semantics and provenance;
- consumes retrieval/memory strategy intent;
- must not choose the review date.

Snap Adapter:
- sends learner-production evidence;
- consumes production/explanation strategy intent;
- must not claim objective mastery from authorship alone.

## 9. Anti-overfitting / growth rules

- Do not adapt from one weak event alone.
- Preserve old evidence; do not delete it merely because it is old.
- Recency may change weight, not historical truth.
- Separate changed learner behavior from changed instrument/version.
- Do not train on ambiguous rating semantics as if labels were stable.
- Require minimum evidence before personalized parameters replace safe defaults.
- New estimator/model version must replay prior evidence before promotion.
- Compare new policy against a baseline and held-out evidence when data volume permits.

## 10. Validation gates

ERROR VALIDATION:
- reject invalid state values / NaN / impossible counts;
- reject schedule authority leakage;
- reject evidence missing scope when adaptation is requested;
- reject estimator output without estimator provenance.

SELF-VALIDATION:
- every adaptive decision must expose evidence ids and explanation;
- no inferred field may overwrite raw evidence;
- uncertainty must remain explicit;
- model output must remain deterministic for identical inputs/config.

REGRESSION VALIDATION:
- member isolation;
- subject isolation;
- concept_skill_target isolation;
- event deduplication;
- replay/idempotency;
- old/new instrument version separation;
- child self-report cannot silently become verified performance;
- Planner/date fields cannot enter Core output;
- same input replay yields same state;
- new evidence may change state, duplicated evidence may not.

## 11. External evidence summary

Patterns considered:
- CAHLR pyBKT: per-skill mastery tracking with guess/slip/learn variants.
- pyKT: deep KT and forgetting/uncertainty variants as benchmark space, not an immediate runtime dependency.
- Open Spaced Repetition / FSRS: difficulty/stability/retrievability separation and trainable review-history parameters.
- ts-fsrs roadmap/issues: input validation, API/model separation, reproducibility and testability matter.
- SkillCoco: practical open-source BKT + spaced repetition + local-first adaptive path example.
- Netlify Async Workloads/Background Functions: useful later for durable offline optimization/replay jobs, not semantic ownership.
- Community reports: inconsistent user grading semantics and retention/workload coupling can skew adaptive models.

## 12. Estimator promotion lane

Candidates are benchmarked behind the stable Core contract.

Current candidates:
- OBSERVATIONAL_BENCHMARK_V1
- BKT_BENCHMARK_CANDIDATE
- DSR_MEMORY_BENCHMARK_CANDIDATE

Synthetic/fixture tests may prove:
- determinism;
- invalid-input handling;
- cold-start behavior;
- sparse-data behavior;
- instrument-change handling;
- absence of schedule authority leakage.

Synthetic/fixture tests may NOT prove model superiority.

Promotion requires real replay evidence and all of:
1. time-based held-out evaluation, not only retrospective fit;
2. same semantic instrument/version or explicit drift handling;
3. enough evidence volume for the target skill family;
4. baseline comparison against the current observational model;
5. no material degradation in cold-start/sparse-data cases;
6. calibration/uncertainty evidence where numeric probability is emitted;
7. deterministic replay for the same model version/config;
8. human-readable decision provenance;
9. regression success across member/subject/skill isolation;
10. no calendar/date authority leakage.

No candidate may self-promote.
Model promotion requires a new validated CURRENT decision.

## 13. Real evidence replay dataset contract

Raw learning evidence is never promoted directly into estimator training/evaluation.

Canonical replay flow:

RAW EVIDENCE
-> semantic validation
-> scope isolation
-> instrument/version preservation
-> label classification
-> chronological normalization
-> time-held-out split
-> candidate benchmark
-> calibration/error analysis
-> promotion review

Replay rules:
- CHILD_SELF_REPORT remains OBSERVATION_ONLY unless independently verified by a permitted performance source.
- Missing or ambiguous outcome is OBSERVATION_ONLY, not failure.
- Duplicate event_id is deduplicated.
- Different member / subject / concept_skill_target evidence cannot enter the same skill replay.
- Instrument-version changes are preserved and must be surfaced at the train/holdout boundary.
- Raw evidence remains immutable; replay records are derived projections.
- Only VERIFIED_TARGET rows may be scored as prediction targets.
- Time order must be preserved; random split is not the default.
- Real-evidence replay and synthetic fixtures must be provenance-distinguishable.
- REAL_EVIDENCE declaration alone is not promotion evidence; an evidence_receipt_id from the owning evidence pipeline is required before promotion review.

Authoritative schema:
- LEARNING/replay/learning-replay-dataset.schema.json

Validator/builder:
- LEARNING/replay/replay-dataset.js

## 14. Canonical Learning Evidence adapter contract

Apps do not write learner-state truth directly.

Canonical path:

APP EVENT
-> CANONICAL LEARNING EVIDENCE ADAPTER
-> REPLAY LABEL CLASSIFICATION
-> LEARNER STATE / ESTIMATOR

Responsibilities:

APP:
- emit actual interaction/result signals;
- preserve source-specific meaning;
- do not claim global mastery.

CANONICAL ADAPTER:
- normalize field names and provenance;
- preserve raw app signals;
- preserve member/subject/concept scope;
- never convert an app-local score into mastery by itself;
- never create a verified target unless an explicit verification layer supplies verified_outcome.

REPLAY CLASSIFIER:
- VERIFIED_TARGET only for explicit verified binary target evidence;
- CHILD_SELF_REPORT remains OBSERVATION_ONLY;
- authorship/completion alone remains OBSERVATION_ONLY;
- missing outcome remains OBSERVATION_ONLY.

CORE / ESTIMATOR:
- interpret canonical evidence;
- maintain uncertainty;
- produce learner-state/pedagogical intent only.

Current canonical adapter:
- LEARNING/adapters/canonical-evidence.js

Hard locks:
- HIDE caseMastery != universal mastery.
- SNAP child_authored != objective mastery.
- READY completed != mastered.
- APP completion state != verified prediction target.
- VERIFIED_TARGET requires explicit verification semantics.

## 15. Verification layer

A binary verified target must be backed by a versioned verification receipt.

Canonical verification path:

APP / TASK EVIDENCE
-> VERIFIER
-> LEARNING_VERIFICATION_RECEIPT
-> CANONICAL EVIDENCE
-> REPLAY VERIFIED_TARGET

Allowed verifier classes:
- Hide & Seek MEMORY_RETRIEVAL_EVIDENCE -> RETRIEVAL_EXACT_MATCH
- Ready structured-practice evidence -> ANSWER_KEY_EXACT
- Snap & Pop learner-production evidence -> HUMAN_RUBRIC_BINARY
- Snap & Pop learner-production evidence -> HUMAN_GROWTH_RUBRIC for dimension-level growth evidence

Generic verifier names exist, but app/evidence combinations are constrained by LEARNING/verification/verifier-policy.js.

Required receipt fields:
- receipt_id
- target_event_id
- verified_at
- verifier_type
- verifier_version
- outcome: 0 or 1
- member_id
- subject
- concept_skill_target
- reference_id
- reviewer_role when human rubric is used

Rules:
- CHILD_SELF_REPORT cannot become a verified target.
- APP completion cannot become a verified target.
- APP-local mastery/score cannot become a verified target.
- Receipt event/member/subject/skill must match the canonical evidence.
- Human rubric verification requires an explicit rubric/reference and reviewer role.
- A raw verified_outcome without receipt authority is OBSERVATION_ONLY.
- Verification proves only the target event outcome; it does not prove global mastery.
- HUMAN_GROWTH_RUBRIC has no global binary outcome.
- HUMAN_GROWTH_RUBRIC may verify VOCABULARY / GRAMMAR / EXPRESSION / THINKING / ENGLISH_THINKING separately as SUCCESS / PARTIAL / FAIL.
- Dimension-level rubric evidence must not become global correctness or mastery.

Current implementation:
- LEARNING/verification/verification-layer.js


## 16. Real Evidence Receipt Pipeline

REAL_EVIDENCE is not a caller-declared label.

A replay dataset may claim REAL_EVIDENCE only when the verified canonical events are bound to an immutable batch receipt.

Canonical path:

VERIFIED CANONICAL EVIDENCE
-> REAL_LEARNING_EVIDENCE_RECEIPT
-> digest revalidation
-> REAL_EVIDENCE replay dataset
-> time-held-out benchmark

Receipt invariants:
- all events share one member / subject / concept_skill_target scope;
- every event has LEARNING_VERIFICATION_RECEIPT authority;
- duplicate event_id is rejected;
- event order is normalized chronologically;
- assessment instrument versions are preserved;
- receipt contains event ids, verification receipt ids, source apps and instrument versions;
- a SHA-256 digest binds the batch to the evidence used to issue it;
- replay creation recomputes and compares the digest;
- any evidence mutation after issuance invalidates the receipt.

A string evidence_receipt_id alone is insufficient.
The actual REAL_LEARNING_EVIDENCE_RECEIPT object must validate against the canonical evidence at replay-build time.

Current implementation:
- LEARNING/receipts/real-evidence-receipt.js


## 17. Estimator promotion policy V1

Promotion review is blocked until enough real verified evidence exists.

Initial conservative thresholds:
- minimum verified targets per member × subject × concept_skill_target: 30
- minimum time-held-out prediction points: 8
- minimum stable-instrument held-out points: 8
- maximum instrument-drift fraction in held-out: 20%
- minimum Brier improvement over observational baseline: 0.01
- candidate may not be worse than baseline on aggregate Brier
- maximum calibration MAE: 0.15
- maximum allowed sparse-data Brier degradation vs baseline: 0.03

These are promotion-review gates, not claims of educational validity.
They are versioned and may change only through evidence-backed review.

A candidate becomes promotion-review eligible only when:
1. dataset-level gates pass;
2. candidate Brier improvement gate passes;
3. calibration gate passes;
4. sparse-data degradation gate passes;
5. instrument-drift gate passes;
6. real evidence receipt provenance is present.

Even when eligible:
- auto_promotion = false;
- a human promotion review is required;
- no candidate may change runtime Core authority without a new validated CURRENT decision.

Current implementation:
- LEARNING/benchmark/promotion-policy.js


## 18. No-loss evaluation lifecycle

Promotion is not a retention boundary.

Hard locks:
- HOLD != DROP
- REJECTED != DELETE
- NOT_ELIGIBLE != DISCARD
- SUPERSEDED != ERASED
- CURRENT != HISTORY

Every estimator evaluation is appended to an immutable evaluation ledger.

Required lifecycle:
BENCHMARK RESULT
-> PROMOTION REPORT
-> IMMUTABLE EVALUATION LEDGER
-> CURRENT PROJECTION
-> RECONSIDERATION QUEUE

Retention rules:
- HOLD results are retained with blockers and evidence receipt provenance.
- HUMAN_REVIEW_AVAILABLE results are retained even when not promoted.
- REJECTED decisions retain both the original evaluation and rejection rationale.
- PROMOTED decisions retain the source evaluation and human decision.
- policy/version changes never overwrite prior evaluations.
- new evidence receipts trigger reconsideration of the latest retained evaluation for the same member × subject × concept_skill_target.
- identical report replay is idempotently deduplicated, not duplicated.
- no promotion report is considered complete unless it has a ledger entry.

Current implementations:
- LEARNING/lifecycle/evaluation-ledger.js
- LEARNING/lifecycle/evaluation-orchestrator.js


## 19. Retention-state baseline candidate

An explainable retention-state baseline is implemented as an advisory candidate.

It uses only verified MEMORY_RETRIEVAL_EVIDENCE with LEARNING_VERIFICATION_RECEIPT authority.

Outputs may include:
- retention_state
- forgetting_risk
- stability_days
- retrievability_estimate
- confidence

Hard boundaries:
- promoted = false until real time-held-out promotion gates pass;
- Core model.retention_probability remains null before promotion;
- retention signal may influence pedagogical intent only;
- no review date, due date or calendar placement may be emitted;
- Planner remains the only dated scheduling owner.

Current implementation:
- LEARNING/estimators/retention-state-baseline.js

Current lifecycle:
- candidate implementation: complete
- runtime promotion: HOLD
- blocker: insufficient real verified retrieval targets + promotion policy not passed


## 20. Mining / Learning Index runtime boundary

The learning evidence supply path is split into four independent roles:

MINING ENGINE
-> MINING INDEX
-> LEARNING INDEX
-> LEARNING ENGINE

### Mining Engine
Owns discovery, research strategy, provider routing, external traversal, acquisition,
counter-evidence acquisition and mining strategy/failure memory.

It does not own persistent source classification, learner state or pedagogical decisions.

### Mining Index
This is the existing shared Indexing/source authority expressed as the Mining-facing index layer.
It owns RAW / INDEX_L1 / DETAIL_L2 / CURRENT, source identity, provenance, authority metadata,
source-family classification, duplicate/version/fragment relations and retrieval state.

Mining Engine may return candidates to Mining Index but may not self-authorize INDEXED state.

### Learning Index
Learning Index is the explicit name for the rebuildable learning-semantic projection previously
described as Learning Projection. It is derived from Mining Index + verified domain mappings.

It may contain curriculum alignment, term/morpheme/root links, subject meanings, concept links,
candidate prerequisite relations, confusion/contrast relations, representation bridges,
cross-subject links, transfer targets and role-tagged language-growth resources.

Learning evidence roles are derived from indexed provenance, not filenames/titles:
- CURRICULUM_ALIGNMENT
- LEXICAL_SEMANTICS
- LANGUAGE_USAGE
- PEDAGOGICAL_USAGE
- GENERAL_REFERENCE

Ambiguous role provenance fails closed.
GENERAL_REFERENCE does not automatically gain language-growth authority.

It may not contain learner mastery, memory strength, review dates, calendar slots, Planner
decisions or automatic remediation authority.

### Learning Engine
Consumes Learning Index + learner evidence and owns learner-state interpretation,
evidence selection, pedagogical strategy, review/diagnostic/remediation policy and outcome feedback.

### Reverse evidence-gap call

REFERENCE EVIDENCE GAP:
LEARNING ENGINE
-> LEARNING INDEX QUERY
-> MINING INDEX EXISTENCE CHECK
-> only if insufficient: MINING ENGINE REQUEST
-> provider execution / acquisition
-> MINING INDEX owner review + index
-> LEARNING INDEX incremental rebuild
-> LEARNING ENGINE requery

LEARNER PERFORMANCE GAP:
LEARNING ENGINE
-> SPECIALIST EVIDENCE ACQUISITION

External Mining is forbidden for learner-performance evidence gaps.

Hard locks:
- Learning Engine emits a gap; it does not directly authorize Mining.
- Mining Engine discovers/acquires; it does not grant Index authority.
- Mining Index preserves source truth; it does not make pedagogical decisions.
- Learning Index is derived/rebuildable; it is not learner state.
- Learning Engine decides learning use; it does not own dated scheduling.
- REVIEW NEED != REVIEW DATE.

Validated candidate implementation:
- branch: taky/learning-mining-runtime-integration-2026-10-01
- Learning Index: LEARNING/index/learning-index.js
- provider invocation host: ENFORCEMENT/mining_runtime_host.py
- cross-engine closed-loop host: ENFORCEMENT/learning_mining_closed_loop.py
- integration regression run 36883758174: SUCCESS
- enforcement replay run 36883758191: SUCCESS

## 21. Hide & Seek word-memory adaptive routing — PROPOSAL / NOT CORE AUTHORITY

Authority correction — 2026-10-02:
- per-word automatic branching,
- adaptive past-word proportion,
- delayed-recall automation

remain PROPOSAL / CANDIDATE.
The validated branch implementation is retained as an experiment and regression asset only.
It SHALL NOT be treated as promoted CURRENT Learning Engine behavior until separately approved.

Hide & Seek remains the specialist executor. If this proposal is later promoted,
Learning Engine would own the adaptive decision.

### 21.1 Per-word automatic route

Learning Engine may emit one recommended Hide mode per learning target:

- NEW / unobserved -> TRACE
- recognition failure -> TRACE
- confusion / meaning-link weakness -> LINK
- orthographic / spelling weakness -> CORE
- assisted-only or retrieval weakness -> RECALL
- recent unassisted success -> RECALL with delayed confirmation
- multi-day unassisted stable -> low-priority RECALL maintenance

This is a specialist routing intent, not a mastery claim and not a forced global stage order.
The child-facing app may still expose direct mode choice.

### 21.2 Current vs past-word mixture

Established baseline:
CURRENT 12 + PAST 24 = past exposure share 2/3.

Adaptive bounds:
- insufficient / early current-word evidence -> keep 2/3 baseline
- current-word evidence weak -> past exposure share 0.50
- current-word evidence strong -> past exposure share 0.75

Hard locks:
- all current assignment words remain mandatory
- the ratio changes prompt exposure / distractor / review mixture only
- current assignment facts are never mutated
- unobserved new words are NOT classified as weak
- stronger TRACE/recall evidence may increase past-word exposure

### 21.3 Delayed recall

Learning Engine may emit delayed-recall semantics:
- AFTER_INTERVENING_ITEMS: generally after 3-5 other items
- AFTER_RECOVERY: recover first, then recheck after intervening items
- NEXT_SESSION_SPACED_RECALL: maintenance in a later session

These are learning-sequence semantics, not calendar dates.

Learning Engine may decide:
- whether delayed recall is needed
- target word
- relative sequence / priority
- recommended interaction mode

Planner alone owns:
- dated allocation
- calendar time
- deadline
- rescheduling across days

### 21.4 Runtime ownership

HIDE WORD EVENT
-> canonical item-level memory evidence
-> LEARNING ENGINE Hide vocabulary policy
-> authenticated decision response
-> Hide policy consumer
-> specialist interaction execution
-> new learner evidence

Hide may not fabricate or locally promote a Learning Engine policy.
If authenticated central policy is unavailable or invalid, Hide keeps the existing safe learning flow.

Validated candidate implementation:
- Learning policy: LEARNING/pedagogy/hide-vocabulary-routing-policy.js
- canonical item signal: LEARNING/adapters/canonical-evidence.js
- central decision surface: LEARNING/transport/central-learning-decision-http-endpoint.js
- Hide consumer branch: taky/hide-memory-routing-learning-engine-2026-10-02
- no main merge / deployment authorized


## 22. Language Growth Engine direction — CORE DIRECTION CONFIRMED

Learning Engine is expanded beyond correct/incorrect and review-need judgment.

Primary growth loop:

OFFICIAL / EDUCATION MINING
-> MINING INDEX
-> LEARNING INDEX
-> ACTUAL LEARNER EVIDENCE
-> LANGUAGE GROWTH PROFILE
-> NEXT ONE-STEP GROWTH INTENT
-> HIDE / SNAP EXECUTION
-> NEW LEARNER EVIDENCE
-> GROWTH PROFILE UPDATE

### 22.1 Growth dimensions

Learning Engine may read and support growth across:

- VOCABULARY — meaning, semantic network, word family, contextual use
- GRAMMAR — noticing and using patterns naturally
- EXPRESSION — chunks, collocations, sentence/speech expansion
- THINKING — connect, compare, explain, infer, justify, create
- ENGLISH_THINKING — direct English meaning/context processing instead of Korean word-by-word substitution

Missing evidence = UNKNOWN, not failure.

### 22.2 Evidence authority

Growth decisions combine two evidence classes:

1. DOMAIN / REFERENCE EVIDENCE
   - CURRICULUM_ALIGNMENT: official curriculum / education authority for achievement-standard, grade and exposure alignment
   - LEXICAL_SEMANTICS: dictionary / lexical reference for easy-English meaning and lexical semantics
   - LANGUAGE_USAGE: corpus / usage reference for chunks, collocations and natural usage patterns
   - PEDAGOGICAL_USAGE: curated learning-resource evidence for scaffolds and English-thinking support
   - each source role keeps separate provenance and may not borrow another role's authority

2. LEARNER EVIDENCE
   - actual Hide retrieval and language-use evidence
   - Snap child-authored production evidence
   - assistance / independence
   - transfer evidence
   - question / explanation depth where legitimately observed
   - direct-English vs translation-dependent signals only when actually evidenced

Learning Index owns the derived domain semantic view.
Learning Engine owns learner interpretation and next-step intent.

CURRICULUM TERM MATCH != LEARNER UNDERSTANDING
AGE / GRADE != THINKING CEILING
CHILD PRODUCTION != AUTOMATIC QUALITY CLAIM

### 22.3 Pull / draw / push growth support

Canonical support progression:

1. SCAFFOLD_LEAD — 끌어주기
   - easier wording
   - easy English definition
   - concrete context
   - useful expression chunk
   - partial model
   - ask the child to complete the final step

2. ELICIT_PULL — 당겨주기
   - short question
   - retrieve a chunk / pattern
   - connect meaning and structure
   - child finishes the idea
   - reduce direct explanation

3. TRANSFER_PUSH — 밀어주기
   - new context
   - compare / explain / infer
   - personalize
   - create / justify
   - minimal cue

The engine may move backward or forward according to evidence.
This is not a one-way level ladder.

### 22.4 Age adaptation

Age / grade adapts:
- wording length,
- vocabulary load,
- abstraction wording,
- number of simultaneous cues,
- hint presentation.

Age / grade SHALL NOT impose a hard ceiling on thinking depth.

AGE CHANGES LANGUAGE LOAD, NOT COGNITIVE CEILING.

Current coarse language-load output:
- VERY_SIMPLE
- SIMPLE
- STANDARD

Actual evidence may still support deeper questions with simpler language.

### 22.5 Question depth

Question depth is evidence-adaptive:

1. NOTICE — notice / identify
2. CONNECT — meaning / relation / chunk
3. EXPLAIN — explain / compare
4. APPLY_TRANSFER — use in a new situation
5. CREATE_JUSTIFY — create / justify / extend

Question count is not a score.
Deeper question != always better.
The engine chooses the next useful step.

### 22.6 Hint strength

Hint policy is separate from answer ownership.

Strong support:
EASY_MEANING_OR_MODEL
-> EXPRESSION_CHUNK
-> PARTIAL_FRAME
-> CHILD COMPLETES

Medium support:
SHORT_QUESTION
-> KEY_CHUNK_OR_PATTERN
-> CHILD FINISHES

Minimal support:
WAIT
-> SHORT_CUE
-> ASK_FOR_REASON_OR_NEW_CONTEXT

The engine SHALL NOT turn a hint into the child's final answer.

### 22.7 Easy English / natural English thinking

When grounded in Learning Index evidence, prefer:
- easy English definition before Korean substitution,
- semantic context before isolated translation,
- expression chunk before word-by-word assembly,
- collocation / pattern before abstract grammar explanation,
- image / situation / action when useful,
- Korean as fallback support, not mandatory first representation.

Canonical direction:

KOREAN TRANSLATION DEPENDENCY
-> EASY ENGLISH MEANING
-> CHUNK / PATTERN
-> CONTEXT
-> CHILD'S OWN SENTENCE / SPEECH
-> NEW CONTEXT TRANSFER

This does not prohibit Korean explanation when it materially helps comprehension.

### 22.8 Hide -> Snap transfer

Hide owns lexical / retrieval interaction.
Snap owns child-authored expression execution.

Growth handoff:

HIDE WORD / MEANING / CHUNK EVIDENCE
-> LEARNING ENGINE GROWTH DECISION
-> SNAP RE-RESOLVES AUTHENTICATED CENTRAL DECISION
-> CHILD SPEAKS / WRITES / EXPLAINS
-> SNAP RETURNS PRODUCTION EVIDENCE
-> LEARNING ENGINE UPDATES GROWTH PROFILE

Hide does NOT send Learning Engine authority through mutable URL parameters.
It sends only continuity scope + learning target / word material.
Snap re-queries the authenticated central Learning Engine.

### 22.9 Role-specific Index-first Mining gaps

Learning Engine checks the required evidence role, not merely whether any indexed source exists.

Possible growth reference gaps:
- CURRICULUM_ALIGNMENT_REFERENCE_REQUIRED
- LEXICAL_SEMANTICS_REFERENCE_REQUIRED
- LANGUAGE_USAGE_REFERENCE_REQUIRED
- PEDAGOGICAL_LANGUAGE_SUPPORT_REFERENCE_REQUIRED

Canonical route:

LEARNING ENGINE ROLE-SPECIFIC GAP
-> LEARNING INDEX ROLE CHECK
-> MINING INDEX provenance-tag check
-> if matching indexed source exists: INDEX_REQUERY
-> only if matching role is insufficient: MINING_REQUEST
-> acquisition
-> Index owner review/classification
-> provenance role preserved in search projection
-> Learning Index rebuild
-> Learning Engine requery

Hard locks:
- learner-performance gaps go to specialist evidence acquisition, never external Mining;
- Learning Engine emits gaps but never authorizes Mining;
- an unrelated indexed source cannot satisfy a role-specific gap;
- curriculum evidence cannot satisfy lexical or corpus authority merely because it contains similar text.

### 22.10 Evidence confidence and anti-oscillation

Growth state SHALL distinguish:
- OBSERVATION
- VERIFIED / human- or deterministic-review-backed evidence
- cross-app convergence
- assisted vs unassisted evidence
- transfer evidence
- applied challenge context

Confidence:
- LOW
- MEDIUM
- HIGH

Hard locks:
- one success does not create a growth-level promotion;
- app completion does not equal successful growth;
- observation-only evidence cannot self-promote to HIGH confidence;
- sparse direct-English evidence cannot label the child translation-dependent;
- strong-scaffold success does not by itself justify an expression-level upshift;
- verified or cross-app evidence is required before stretch promotion;
- challenge context is evidence context, not learner-state authority.

### 22.11 Growth control vector

Learning Engine emits one explicit growth-control intent:

- evidence_confidence: LOW / MEDIUM / HIGH
- learning_intensity:
  - SUPPORT_BUILD
  - BUILD_CONNECT
  - STRETCH_TRANSFER
- expression_level:
  - L1_CHUNK_OR_PHRASE
  - L2_SIMPLE_SENTENCE
  - L3_EXPANDED_SENTENCE
  - L4_REASONED_RESPONSE
  - L5_TRANSFER_CREATION
- easy_english_level
- question_depth: 1..5
- hint_strength
- hint_fade
- target_dimensions
- challenge_direction

Growth control is pedagogical intent only.
It cannot own dates, assignment facts or the child's final answer.

### 22.12 Applied challenge evidence

When Snap executes a growth-control intent, the result must preserve the execution context:

- learning_intensity
- expression_level
- question_depth
- hint_strength
- hint_fade
- challenge_direction
- growth intent version

This is stored as SPECIALIST_EXECUTION_CONTEXT_ONLY.

It is used to interpret the next result:
the same correct response under strong scaffolding and under minimal cues is not equivalent evidence.

SPECIALIST EXECUTION CONTEXT != LEARNING ENGINE AUTHORITY
APPLIED DIFFICULTY != LEARNER STATE

### 22.13 Outcome feedback

A single outcome may create only a growth adjustment candidate:

- OBSERVE_MORE
- HOLD_LEVEL
- FADE_HINT_ONE_STEP_CANDIDATE
- HOLD_LEVEL_ADJUST_HINT_CANDIDATE
- INCREASE_SUPPORT_CANDIDATE
- KEEP_SUPPORT_AND_RECHECK
- PRESERVE_OR_STRETCH_CANDIDATE

The outcome feedback layer SHALL NOT directly mutate learner state or authorize a growth-control change.

Canonical loop:

APPLIED GROWTH CONTROL
-> SPECIALIST RESULT
-> GROWTH OUTCOME FEEDBACK CANDIDATE
-> CUMULATIVE EVIDENCE
-> RE-DERIVE GROWTH PROFILE
-> RE-DERIVE NEXT GROWTH CONTROL

CANDIDATE FEEDBACK != STATE MUTATION
ONE RESULT != AUTOMATIC LEVEL CHANGE

### 22.14 Longitudinal growth stability

Growth Profile uses two evidence windows:

RECENT WINDOW:
- drives immediate support and question/hint adjustment;
- default candidate size: recent 8 relevant signals.

STABILITY WINDOW:
- guards promotion/demotion;
- default candidate size: recent 24 relevant signals.

The counts are tunable runtime policy, not curriculum authority.

Stability signals include:
- STRETCH_STABLE
- PROMOTION_CANDIDATE_NOT_STABLE
- TEMPORARY_SUPPORT_WITHOUT_LONG_TERM_DEMOTION
- SUPPORT_NEED_STABLE
- RECENT_EVIDENCE_INSUFFICIENT
- HOLD_OR_DEVELOP

Hard locks:
- recent weakness may increase support without erasing long-term growth;
- recent strength alone cannot trigger TRANSFER_PUSH until the stability window supports it;
- old evidence is preserved historically but cannot dominate current control merely by age/volume.

### 22.15 Ready / Planner authority reconciliation

Ready Learning Master is not a second Learning Engine.

Ready may own:
- assignment decomposition;
- operational execution-load metadata;
- local-first fallback mechanics.

Ready may not own:
- learner-state authority;
- growth-control authority;
- central review-policy authority while TAKY Learning Engine is available.

Ready local memory review:
- LOCAL_FALLBACK_ONLY;
- central Learning Engine takes precedence;
- Planner still owns any dated placement.

READY EXECUTION LOAD != LEARNER GROWTH STATE
LOCAL FALLBACK != CENTRAL AUTHORITY

### 22.16 Dimension-level Snap growth verification

Snap completion remains observation-only quality evidence.

A permitted reviewer may issue HUMAN_GROWTH_RUBRIC evidence for separate dimensions:
- VOCABULARY
- GRAMMAR
- EXPRESSION
- THINKING
- ENGLISH_THINKING

Each dimension may be SUCCESS / PARTIAL / FAIL.

The receipt:
- has outcome = null at global level;
- preserves reviewer/rubric provenance;
- replaces matching UNKNOWN placeholders only for reviewed dimensions;
- cannot create global correctness or mastery.

### 22.17 Current candidate implementation

- LEARNING/pedagogy/language-growth-profile.js
- LEARNING/pedagogy/growth-next-step-policy.js
- LEARNING/pedagogy/growth-outcome-feedback.js
- LEARNING/index/learning-index.js language_growth semantic group
- LEARNING/adapters/canonical-evidence.js growth signal normalization
- LEARNING/runtime/learning-engine-runtime.js growth integration
- LEARNING/transport/central-learning-decision-http-endpoint.js trusted growth decision surface
- Hide candidate branch: taky/hide-memory-routing-learning-engine-2026-10-02
- Snap candidate branch: taky/snap-growth-engine-handoff-2026-10-02

Main merge / deployment remain HOLD until branch regression passes and promotion is explicitly authorized.

END