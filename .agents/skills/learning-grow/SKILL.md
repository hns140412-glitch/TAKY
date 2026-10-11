---
name: learning-grow
description: Execute Learning Grow evidence, outcome feedback, and strategy-growth review across Ready & Set, Hide & Seek, Snap & Pop and the shared Learning Engine.
---
Load `DOMAIN/GROW_DOMAIN_REGISTRY.json`, `MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md`, and `CURRENT/LEARNING_ENGINE_DATA_READINESS_CURRENT.json`.
Route this domain as `LEARNING_GROW`.

Keep two layers separate:
- LEARNER_GROWTH: learner-specific evidence may adjust review/support/challenge candidates.
- LEARNING_SYSTEM_GROWTH: shared engine strategy changes require repeated verified outcomes and shared GROW promotion gates.

Use existing `LEARNING/lifecycle/outcome-growth-feedback.js` and `growth-strategy-ledger.js`; do not create a second learning ledger.
Preserve receipt immutability, member/family isolation, candidate-only mining feedback, and no automatic strategy promotion.
Ready owns session/planning orchestration; Hide owns vocabulary/memory signals; Snap owns thought/expression results; Learning Engine owns long-term interpretation.
Hide signals may inform Learning Grow but Hide does not own long-term scheduling.
A single success/failure, observation-only event, badge/reward, or app-local state must never become system policy.
For cross-learner `LEARNING_SYSTEM_GROWTH`, use `LEARNING/lifecycle/learning-system-growth-aggregate.js`: minimum 3 distinct members and minimum verified-outcome threshold are required, output is aggregate-only, individual member identifiers are forbidden, and strategy change remains review-gated. Persist eligible aggregate candidates only through `LEARNING/transport/durable-learning-system-growth-store-adapter.js`; it uses a family-scoped strong-store namespace and never stores the input member list. The adapter then best-effort enqueues the sanitized aggregate candidate through `grow-review-queue-adapter.js`; this queue is review-only and cannot promote strategy.
For system-growth review, bind evidence through shared GROW lineage:
RAW -> INDEX -> LEARNING -> RELATION -> EXECUTION -> OUTCOME -> GROWTH.
If evidence is insufficient, retain the candidate/HOLD; do not invent learner history or promote strategy.
