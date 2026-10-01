# TAKY Learning Engine Growth Axis — HANDOFF 2026-10-02

Status: VALIDATED_CANDIDATE_CORE_DIRECTION
Implementation authorization: BRANCH_ONLY
Main merge: HOLD
Deployment: HOLD

## 1. Core direction confirmed

Learning Engine is no longer limited to correct/incorrect, memory and review need.

Core growth axes:
- VOCABULARY
- GRAMMAR
- EXPRESSION
- THINKING
- ENGLISH_THINKING

Primary loop:

OFFICIAL / EDUCATION MINING
-> MINING INDEX
-> LEARNING INDEX
-> ACTUAL LEARNER EVIDENCE
-> LANGUAGE GROWTH PROFILE
-> GROWTH CONTROL
-> HIDE / SNAP EXECUTION
-> APPLIED CHALLENGE CONTEXT + RESULT
-> GROWTH OUTCOME FEEDBACK CANDIDATE
-> CUMULATIVE EVIDENCE
-> RE-DERIVE PROFILE / CONTROL

## 2. Growth-control vector

Learning Engine now emits:
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

Age / grade changes language load, not cognitive ceiling.

## 3. Evidence hardening

Growth evidence distinguishes:
- observation vs verified evidence
- assisted vs unassisted
- transfer evidence
- cross-app convergence
- applied challenge / hint context

Hard locks:
- one success != growth promotion
- app completion != growth success
- sparse direct-English signal != translation dependency
- strong-scaffold success != expression-level upshift
- observation-only cannot self-promote to HIGH confidence
- expression/thinking stretch requires explicit challenge success
- execution context is evidence, not authority

## 4. App role split

Hide & Seek:
- supplies memory evidence;
- TRACE / LINK additionally emit target-scoped VOCABULARY observations;
- CORE spelling success is not promoted to general vocabulary growth;
- does not own long-term learning judgment.

Snap & Pop:
- re-resolves authenticated Learning Engine growth decision;
- consumes learning intensity / expression level / question depth / hint strength;
- keeps child authorship;
- returns applied growth-control context with the result;
- completion alone remains UNKNOWN quality evidence.

Learning Engine:
- owns cumulative growth interpretation and next-step intent.

Planner:
- owns dated allocation only.

## 5. Outcome feedback

Single outcome creates candidate only:
- OBSERVE_MORE
- HOLD_LEVEL
- FADE_HINT_ONE_STEP_CANDIDATE
- HOLD_LEVEL_ADJUST_HINT_CANDIDATE
- INCREASE_SUPPORT_CANDIDATE
- KEEP_SUPPORT_AND_RECHECK
- PRESERVE_OR_STRETCH_CANDIDATE

No single outcome may directly mutate learner state or authorize a control change.

## 6. Memory routing proposal remains separate

The following remain CANDIDATE / NOT CORE AUTHORITY:
- per-word automatic memory-state branching
- adaptive past-word proportion
- delayed-recall automation

Existing branch implementation is retained only as experiment/regression evidence until separately approved.

## 7. Key implementation files

TAKY:
- LEARNING/pedagogy/language-growth-profile.js
- LEARNING/pedagogy/growth-next-step-policy.js
- LEARNING/pedagogy/growth-outcome-feedback.js
- LEARNING/index/learning-index.js
- LEARNING/adapters/canonical-evidence.js
- LEARNING/runtime/learning-engine-runtime.js
- LEARNING/transport/central-learning-decision-http-endpoint.js
- OS/LEARNING_ENGINE_CORE.md

Hide:
- branch: taky/hide-memory-routing-learning-engine-2026-10-02
- hide-bridge.js
- app.js

Snap:
- branch: taky/snap-growth-engine-handoff-2026-10-02
- snap-bridge.js
- app.js
- snap-ready-scope-guard-v01.js

## 8. Validation evidence

TAKY latest:
- Mining Indexing Learning Integration run 36891330108: SUCCESS
- TAKY Enforcement Replay run 36891329955: SUCCESS

Hide latest growth evidence path:
- Learning Runtime Bridge Validation run 36890466371: SUCCESS
- Validate Hide & Seek run 36890466576: SUCCESS

Snap latest growth-control path:
- Learning Runtime Bridge Validation run 36890919063: SUCCESS
- Validate Snap & Pop run 36890919141: SUCCESS

## 9. Remaining OPEN

1. Dimension-specific Snap growth rubric evidence contract:
   production completion must stay UNKNOWN until a permitted rubric/reviewer supplies dimension evidence.
2. Language-support source-role refinement:
   official curriculum grounding and dictionary/corpus/chunk support should remain provenance-distinct.
3. Longitudinal hysteresis:
   persistent level promotion/demotion across longer evidence windows must stay explainable and fail-closed.

No main merge or deployment is authorized by this handoff.
