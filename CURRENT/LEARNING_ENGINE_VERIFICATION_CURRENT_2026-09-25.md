# Learning Engine Verification CURRENT — 2026-09-25

STATE: CURRENT_VALIDATED
SCOPE: verified learning evidence pipeline for independent Learning Engine Core
AUTHORITY:
- OS/LEARNING_ENGINE_CORE.md
- LEARNING/verification/verification-layer.js
- LEARNING/verification/verifier-policy.js
- LEARNING/adapters/canonical-evidence.js
- LEARNING/replay/replay-dataset.js
- LEARNING/replay/replay-benchmark.js

## Canonical chain

APP RESULT
-> CANONICAL LEARNING EVIDENCE
-> VERIFICATION POLICY
-> LEARNING_VERIFICATION_RECEIPT
-> VERIFIED_TARGET / OBSERVATION_ONLY
-> TIME-HELD-OUT REPLAY
-> ESTIMATOR BENCHMARK
-> HUMAN PROMOTION REVIEW

## Hard boundaries

- Ready / Hide / Snap are not the Learning Engine.
- App completion is not mastery.
- App-local score is not universal mastery.
- CHILD_SELF_REPORT is observation-only.
- Snap child_authored is not objective mastery.
- Hide caseMastery is not a verified target.
- raw verified_outcome without receipt authority is observation-only.
- REVIEW NEED != REVIEW DATE.
- Learning Engine Core has no calendar authority.

## App-specific verifier policy

Hide & Seek:
- eligible evidence: MEMORY_RETRIEVAL_EVIDENCE
- verifier: RETRIEVAL_EXACT_MATCH
- automatic verification allowed only for deterministic exact-match candidates
- current producer: CODE RED recordCodeResult
- CORRECT -> target outcome 1
- WRONG / HINT_USED / TIMEOUT -> target outcome 0 for UNASSISTED_EXACT_RETRIEVAL semantics
- PASS is not promoted
- caseMastery is not promoted

Ready & Set:
- eligible evidence: STRUCTURED_PRACTICE_EVIDENCE
- verifier: ANSWER_KEY_EXACT
- requires verified answer-key reference and deterministic match
- Ready completion/session state alone is not verification

Snap & Pop:
- eligible evidence: LEARNER_PRODUCTION_EVIDENCE
- verifier: HUMAN_RUBRIC_BINARY
- automatic verification forbidden
- requires explicit rubric/reference and allowed reviewer role

## Provenance

Canonical evidence preserves:
- event_id / observed_at
- member / subject / concept_skill_target
- source_app
- actual assessment instrument_version
- interaction_mode
- assistance
- attempt_count
- response_latency_ms
- verifier receipt id/type/version when verified

Actual assessment instrument version has precedence over adapter/bridge context version.

## Replay target rule

VERIFIED_TARGET requires:
1. verified_outcome 0/1;
2. verification receipt id;
3. verification authority = LEARNING_VERIFICATION_RECEIPT;
4. canonical scope consistency;
5. applicable verifier policy.

Otherwise the record remains OBSERVATION_ONLY.

## Validation evidence

TAKY exact-head functional validation:
- Core V2: SUCCESS
- Estimator benchmark: SUCCESS
- Replay dataset: SUCCESS
- Replay benchmark bridge: SUCCESS
- Verification layer: SUCCESS
- App-specific verifier policy: SUCCESS
- Canonical Learning Evidence adapter: SUCCESS
- Canonical evidence -> replay labels: SUCCESS
- Learning Engine evidence normalizer: SUCCESS

Validated functional HEAD at this checkpoint:
- df19f9e4250c95b37e5c103deb64fbd366da3dda
- workflow run 36099999248 had all Learning Engine-related steps SUCCESS when this CURRENT was written; remaining unrelated TAKY replay steps were still executing.

Hide verification producer:
- app commit 50d26324bc8e57a0de1c95a8340aecd0b77bc963
- contract regression commit 02005bc8a7d772c48c6a8bfda5d90d67660bee1a
- validate workflow 36099927544 SUCCESS
- parallel GitHub Pages deployment workflow failed at Configure Pages; this is not a Learning Engine/Hide functional validation failure.

## Remaining OPEN

1. Ready verified-answer-key producer adapter.
2. Snap human-rubric receipt producer flow.
3. Real evidence receipt pipeline for replay datasets.
4. Accumulate real verified targets by skill.
5. Compare Observational/BKT/DSR candidates on real time-held-out evidence.
6. No estimator promotion until real-evidence thresholds and promotion review pass.

Netlify / production deployment: HOLD.
