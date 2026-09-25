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
- must not become learner-model authority.

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

END
