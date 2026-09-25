# Learning Engine Growth Deep Review — 2026-09-25

STATE: REVIEWED_CURRENT
Scope: independent Learning Engine Core growth research and localization

## Compared references

- CAHLR/pyBKT: per-skill Bayesian mastery; individual priors/learn/guess/slip variants.
- pyKT toolkit: deep KT benchmark family including forgetting-aware and uncertainty-aware models.
- 2025 session-to-session validation research: retrospective KT fit can degrade under time-based future prediction and may miss spacing/forgetting dynamics.
- 2025 uncertainty-aware KT: interaction uncertainty should be modeled explicitly rather than collapsed into a single certain state.
- Open Spaced Repetition FSRS / ts-fsrs: difficulty, stability, retrievability separation; optimizer from review logs; pure model/scheduler APIs.
- SkillCoco: open-source BKT + spaced repetition + local-first mastery loop.
- Netlify Functions / Background Functions / Async Workloads: immutable deployments and durable async/event jobs.
- GitHub issues/community: input validation, rating-semantic misuse, workload spikes, model/API separation.
- Reddit Anki community: inconsistent Hard/Again semantics can skew learned parameters; high desired retention can create workload pressure; model outputs need user-facing interpretation.

## Adopt

1. Independent Learning Engine Core layer under LEARNING_OS.
2. Primary adaptive scope = member x subject x concept_skill_target.
3. Observation and inference are stored/separated conceptually.
4. Evidence provenance includes instrument version, interaction mode and assistance semantics.
5. Default Core emits no fake mastery probability before estimator calibration.
6. Estimator architecture is pluggable: observational baseline first, BKT/DSR candidates later.
7. Review need remains pedagogical; dated placement remains MAIN/Planner.
8. Heavy optimizer/replay jobs may run asynchronously later; runtime Core stays lightweight/deterministic.
9. Model/version promotion requires replay/regression evidence.

## Reject / do not copy wholesale

- FSRS due-date scheduler inside Learning Engine Core.
- one universal memory model for writing/reasoning/performance tasks.
- subject-level score as primary learner state.
- single success = mastery.
- app-specific score promoted directly to global mastery.
- deep KT black box before enough clean labeled history exists.
- promoting BKT/forgetting variants from retrospective fit alone without time-based held-out validation.
- cloud/background function as semantic authority.

## Hold until evidence volume is sufficient

- calibrated BKT parameters;
- individualized DSR/FSRS-like memory parameters;
- numeric mastery probability;
- automated model selection;
- automatic threshold tuning;
- cross-skill transfer/prerequisite graph learning.

## Failure patterns converted to TAKY guards

- ambiguous grade semantics -> explicit evidence semantics + instrument version.
- invalid NaN/state inputs -> boundary validation.
- scheduler/model coupling -> Core cannot output dates.
- workload optimization confused with learning optimization -> Planner owns capacity/time.
- optimizer overfits small history -> safe defaults + minimum evidence + replay before promotion.
- changed instrument mistaken for changed learner -> instrument_version is part of provenance.

## Implemented in this review

- OS/LEARNING_ENGINE_CORE.md
- MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json adds LEARNING_ENGINE_CORE.
- LEARNING/runtime/learner-state-core.js pure Ready-independent baseline.
- LEARNING/runtime/learner-state-core.test.js regression suite.
- TAKY Enforcement runs the Core regression suite.
- Ready evidence ontology V02 preserves Core-relevant provenance.
- Ready is reclassified as adapter/host; old Ready-local engine authority superseded.

END
