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


## Core Adaptive Plan Intent

Implemented and TAKY Enforcement GREEN:
- LEARNING/pedagogy/adaptive-plan-contract.js
- Unified Runtime Decision Contract now carries Core-owned adaptive_plan.
- Core owns the reason/policy for:
  - unit-span reduction intent
  - retrieval checkpoint intent
  - recovery floor
  - assistance fading
  - target learning IDs
- consumer apps may apply the plan but cannot derive new learner-state policy from it.
- adaptive plan has no dated scheduling authority.

Ready integration:
- Ready Adapter V2 preserves the Core adaptive plan.
- ReadyLearningMaster applies the plan to subject-specific unit structure.
- Planner preserves plan provenance only; Planner alone chooses dates.
- stale Planner outputs are invalidated before Core-driven reanalysis.
- dedicated Core adaptive plan -> Ready reanalysis -> Planner integration regression is GREEN.

Legacy extraction status:
- Core decision paths bypass Ready-local learnerAdaptiveProfile / memoryConcern.
- primary adaptive-loop regressions are being migrated to Core decisions.
- legacy fallback remains compatibility-only until every residual caller is verified/migrated.

## Remaining OPEN

Current no-loss ledger projection has exactly three unresolved items:

1. Forgetting and retention estimator — HOLD
   - advisory retention baseline is implemented;
   - real verified retrieval targets are still insufficient for promotion review;
   - must pass real time-held-out promotion policy before runtime estimator authority changes.

2. Calibrated BKT estimator — HOLD
   - deterministic train-only calibrator is implemented;
   - real time-held-out calibration evidence is still insufficient;
   - must pass calibration/promotion policy and human review before promotion.

3. Hosted central evidence transport connection — HOLD
   - cumulative specialist intake, immutable receipts, durable Ready outbox, fail-safe sync, durable store adapter, family/member auth policy and Netlify Blobs adapter are implemented;
   - remaining boundary is server-side identity resolver + Function endpoint binding;
   - deployment remains explicitly HOLD, so no Netlify call/deploy has been performed.

Closed/applied:
- metacognitive self-reflection evidence;
- pedagogical feedback intent;
- declared concept prerequisite/dependency graph;
- guarded data-derived relation candidate policy;
- item-scoped recovery profile;
- item-level learning_target_id provenance;
- automatic retained evaluation for every real evidence receipt;
- unified Learning Engine runtime decision contract;
- Core Adaptive Plan Intent;
- Ready independent Learning Engine Adapter V2;
- Ready embedded learning logic extraction into explicit compatibility quarantine;
- specialist evidence central intake pipeline;
- durable store/concurrency adapter;
- transport family/member authorization;
- authenticated transport wrapper;
- Netlify Blobs transport adapter.

No estimator auto-promotion.
Ready is not the Learning Engine.
Planner remains dated-allocation authority.
Production / merge / Netlify deployment remains HOLD.

Netlify / production deployment: HOLD.



## LATEST RESUME OVERRIDE — CENTRAL EVIDENCE HTTP BOUNDARY — 2026-09-26

Preserve all previously CLOSED Learning Core, learner state, evidence receipts, Adaptive Plan Intent and independent Core role. The three high-level OPEN lines remain retention/BKT held and hosted transport, but hosted transport has a new **implemented provider-neutral HTTP ingress sub-slice**: `LEARNING/transport/central-learning-http-endpoint.js`, `central-learning-http-endpoint.test.js`, and durable store no-false-ACK regression. Exact PR #157, head `688eaa6be17a0106b07cc1b69949d6f28ba77733`, TAKY Enforcement run `36247334212` SUCCESS at this checkpoint.

This module is not a deployed Function, real OAuth verifier, real app-specific server verification provider or configured production store. Its server-injected `verifyBearerToken` and `verifySpecialistEvidence` must be supplied by the authorized runtime. The PWA's self-declared exact-match/human-review candidate is **observation-only by default**, never verified performance, until checked against a server-owned reference/provenance. A successful receipt is returned only after confirmed durable write with ETag; no full child learning state crosses the ACK. Central Learning Core != PWA; Planner remains calendar authority; Drive keeps only incremental source/index and versioned, verified archive role per `OS/LEARNING_ENGINE_DRIVE_HYBRID_STORAGE_REVIEW_2026-09-26.md`.

Next concrete hosted OPEN: choose/verify actual upstream auth issuer/audience/expiry and authoritative family membership; provide real specialist verification sources; bind a selected durable central store and request framework; exercise PWA offline outbox/ACK and privacy/security before release. Retention/BKT estimator promotion and Netlify deploy remain HOLD. Do not count local fake bearer/verifier tests as real production binding.


## LATEST RESUME OVERRIDE — GOOGLE SERVER PRINCIPAL + REAL NODE HTTP PILOT — 2026-09-26

Inherit all earlier Core/Evidence/Planner CLOSED, and still HOLD the retention estimator and calibrated BKT. Hosted central transport's next tested sub-slice is TAKY DRAFT PR #158: `LEARNING/transport/google-learning-principal.js`, `node-http-learning-bridge.js`, integration tests and `CENTRAL_GOOGLE_NODE_PILOT_HANDOFF_2026-09-26.md`.

- Google ID token verification uses an actual official-library adapter for the eventual host, a configured client-ID allowlist and checked `iss/aud/azp/iat/exp/sub`; **test** supplies a deliberately fake official-style ticket and actual Node loopback HTTP/LocalJsonStrongStore, NOT real user login. Stable `sub`, not email, maps to trusted server-side family/member evidence-submit grants. CHILD only own scope, PARENT explicit target grants; gift-only FAMILY_ADULT has NO automatic learning/child read permissions.
- Browser Origin explicit HTTPS allowlist/CORS, no-store, POST JSON, 64 KiB streaming bound; this is a real Node HTTP *adapter*, not an installed cloud Function or production URL.
- Adversarial finding addressed: PWA `context.verification_receipt` previously survived the #157 payload candidate scrub, and canonical adapters can accept a field-valid fake. Central HTTP now removes nested client-owned receipt/candidate/proof fields from all relevant packet locations, and sends ONLY scrubbed packet into the trusted specialist verifier. Forged Hide exact-match and Snap parent-rubric receipt regression tests remain OBSERVATION_ONLY.
- No operational Google Auth Library install, real Google OAuth issuance, actual central family-registry database, production durable store, real specialist answer verification, actual Drive write or PWA/Netlify deploy. Hosted transport remains OPEN: select credentials/registry/store and authorized release. Existing Drive hybrid map remains unchanged and Drive is NOT the live Learning Engine or Award/Gem transaction store.

Resume: verify exact PR #158 head plus TAKY Enforcement success, then the actual host wiring and specialist verification source / Drive export only, without reimplementing previously CLOSED Learning Core.
