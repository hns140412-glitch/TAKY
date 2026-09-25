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
-> REAL_LEARNING_EVIDENCE_RECEIPT
-> SKILL-SCOPED INTAKE
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


## Real Evidence accumulation

Verified canonical evidence is accumulated with immutable receipts.

Rules:
- one receipt scope = member × subject × concept_skill_target;
- duplicate event_id is rejected;
- batch digest is SHA-256 bound to canonical verified evidence;
- replay revalidates the digest before accepting REAL_EVIDENCE;
- string receipt ids alone are insufficient;
- incremental growth creates a new receipt linked to parent_receipt_id + parent evidence digest;
- prior receipts are not overwritten;
- broken parent receipt/digest chains fail validation;
- multi-scope intake partitions evidence before receipt issuance;
- unverified evidence is rejected from real verified intake.

Current modules:
- LEARNING/receipts/real-evidence-receipt.js
- LEARNING/intake/real-evidence-intake.js

Validation:
- immutable batch receipt regression: GREEN
- tamper/digest mismatch regression: GREEN
- incremental receipt chain regression: GREEN
- duplicate event regression: GREEN
- member/subject/skill scope partition regression: GREEN
- unverified evidence rejection: GREEN
- TAKY run 36102162246: all Learning Engine receipt/intake steps SUCCESS at checkpoint


## No-loss promotion / reflection lifecycle

Unapplied or unpromoted work is not discarded.

Hard locks:
- HOLD != DROP
- REJECTED != DELETE
- NOT_ELIGIBLE != DISCARD
- SUPERSEDED != ERASED
- CURRENT != HISTORY

Estimator evaluations:
- every promotion report is appended to LEARNING/lifecycle/evaluation-ledger.js;
- HOLD and HUMAN_REVIEW_AVAILABLE results are both retained;
- human REJECTED/PROMOTED/DEFERRED decisions append new decision entries and never erase the source evaluation;
- a new evidence receipt or policy version creates a reconsideration-queue entry for the same skill scope;
- identical replay is deduplicated idempotently.

Learning Engine changes generally:
- estimator, policy, learner-state, evidence-schema, pedagogy-rule, adapter-contract and validation-rule proposals use LEARNING/lifecycle/change-ledger.js;
- APPLIED / HOLD / DEFERRED / REJECTED / SUPERSEDED states all remain immutable history;
- CURRENT/LEARNING_ENGINE_CHANGE_LEDGER_CURRENT.json retains unresolved and applied findings;
- CI fails if retained deep-review items disappear.

Existing retained OPEN/HOLD findings include:
- Metacognitive self-reflection evidence
- Pedagogical feedback intent
- Forgetting and retention estimator
- Calibrated BKT estimator
- Concept prerequisite and dependency graph

## Retention baseline candidate

Implemented:
- explainable retention-state baseline from verified retrieval evidence
- Core advisory retention_signal integration
- pedagogical RETRIEVAL_CHECKPOINT mapping for RETENTION_AT_RISK
- duplicate intent merging while preserving multiple evidence bases

Not promoted:
- model.retention_probability remains null
- scheduling authority remains false
- candidate remains HOLD in change ledger pending enough real verified retrieval targets and promotion-policy pass


## Learner State V2 integration audit

Integrated runtime axes:
- evidence sufficiency
- personal trend
- retention / forgetting risk baseline
- item-scoped recovery
- assistance dependence
- self-reported confusion / metacognition
- declared prerequisite readiness
- instrument drift

These axes remain separate signals. They are not collapsed into one opaque score.

Unified runtime entry:
- LEARNING/runtime/decision-contract.js

Runtime Decision Contract:
- receives learner state + pedagogical feedback intent + optional prerequisite readiness;
- resolves priority/conflicts;
- emits pedagogical action intent only;
- HOLDs interpretation when evidence is absent or instrument drift invalidates comparison;
- keeps sparse evidence as advisory rather than fabricating certainty;
- Ready may translate intent to execution plan;
- Planner alone owns dated allocation;
- specialist apps own interaction execution/evidence.

Recovery correction:
- item recovery episodes now require verified_outcome + LEARNING_VERIFICATION_RECEIPT;
- learning_target_id alone is insufficient;
- unverified target events remain excluded.

No-loss automatic real-evidence evaluation:
- every valid REAL_LEARNING_EVIDENCE_RECEIPT is evaluated and retained, even below replay minimum;
- below-minimum results are recorded as HOLD rather than discarded;
- identical receipt/report replay is deduplicated;
- new receipts remain independently traceable.

Validation checkpoint:
- exact HEAD ba7e1e70336f56d38bd81b48c31894998676013c
- TAKY Enforcement run 36106173148: SUCCESS
- unified runtime decision contract: SUCCESS
- verified-only recovery regression: SUCCESS
- retention baseline: SUCCESS
- calibrated BKT candidate: SUCCESS
- prerequisite graph + candidate retention: SUCCESS
- no-loss ledgers / CURRENT retention: SUCCESS

## Remaining OPEN

1. Accumulate enough real verified retrieval targets per concept_skill_target for retention-candidate promotion review.
2. Calibrate/evaluate BKT candidate on real time-held-out evidence.
3. Build concept prerequisite/dependency graph contract without premature inference.
4. No estimator promotion until real-evidence thresholds and promotion review pass.
5. Production/Netlify deployment remains HOLD.

Netlify / production deployment: HOLD.
