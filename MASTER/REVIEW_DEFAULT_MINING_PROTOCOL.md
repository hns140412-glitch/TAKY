# REVIEW DEFAULT MINING PROTOCOL

Status: ACTIVE
Owner: TAKY / Source Acquisition + Mining + Indexing
Effective: 2026-10-07

## Default interpretation

When the user supplies or points to an external/reference material and asks to
"검토", "봐봐", "확인해", "참고해", "적용 가능성 검토", or equivalent review,
the default operation is NOT a transient visual inspection.

The default is:

REFERENCE INTAKE
→ RAW preservation
→ source metadata + hash/dedup
→ mining
→ INDEX / DETAIL
→ domain or Learning Projection
→ compare / applicability review
→ implementation candidate when justified
→ verification.

## Independent-first comparative review — USER CORRECTION 2026-11-06

When the user asks to mine/review sources and existing materials, derive an optimal option, **then** compare it with TAKY (or any named incumbent), preserve that order as an execution contract:

1. INDEPENDENT SOURCE ANALYSIS: read and assess each mined/original source and the requested prior materials on their own merits, identifying reproducible methods, strengths, failure cases, limits, evidence quality, and unresolved gaps. Do not use the incumbent as the scoring baseline in this phase.
2. CASE-BASED CROSS-ANALYSIS: compare independently verified cases with one another; evaluate competing approaches against explicit, source-grounded outcome, cost, accuracy, feasibility, maintainability and risk criteria. Reject ungrounded promotional claims.
3. OPTIMAL OPTION: derive the best-fit architecture/operating proposal from phases 1–2, with alternatives, evidence, tradeoffs, and HOLD conditions. The choice MUST NOT be reverse-engineered to justify an existing TAKY design.
4. TAKY GAP COMPARISON **LAST**: only after a recoverable independent conclusion exists, load/check the latest applicable TAKY CURRENT and owning rules, then map `SAME / BETTER_EXTERNAL / BETTER_TAKY / GAP / CONFLICT / NOT_VERIFIED`. Record where TAKY must change, where the external idea fails, and where a result remains unproven.
5. EXECUTION/VALIDATION: implement only approved, scoped changes at their proper owner and verify actual behavior. A comparison report or rule text alone is not implementation or recurrence-prevention PASS.

If current TAKY must be checked before a tool call for **authority/security/permission protection**, perform only that safety preflight; do not treat it as an early comparative judgment or a predetermined answer.

**Hard failure gate:** `TAKY-FIRST COMPARISON`, `EXTERNAL CASES SELECTED TO FIT TAKY`, or `AFTER-THE-FACT RATIONALIZATION` before independent criteria and an independent optimal option are recorded = `INTENT_DRIFT / RULE_NOT_APPLIED` and **FAIL / REWORK_REQUIRED**. Do not reinterpret a user's explicit sequence as a suggestion, change the task to "verify existing TAKY", or defend a reversed order by pointing to preexisting rules. If source evidence is insufficient, mark the exact phase `HOLD_SOURCE_UNVERIFIED` rather than substituting a TAKY-first conclusion.

Representative incident and replay fixture: `HISTORY/2026-11-06_REVIEW_ORDER_INVERSION_FAILURE_CASE.md`; `MASTER/EXECUTION_REGRESSION_FIXTURES.md#f-07`. This section specializes the existing `TKY-INTENT-001` fidelity rule; it creates no separate semantic authority.

This applies to:
- uploaded screenshots/images
- PDFs/documents
- books/workbooks shown in images
- webpages/social posts/videos
- examples/case studies
- external tools/products/workflows
- user-provided reference artifacts.

## RAW-first rule

Preserve the materially available original before deriving summaries.
Record, where available:
- original file or immutable source pointer
- SHA-256/content hash
- source/account/publisher
- acquisition timestamp
- URL or conversation/library reference
- public/private/right/use context
- duplicate relation.

Derived text, summaries, indexes and Learning Projections are reproducible
layers and must not replace the original.

If the original cannot be durably preserved, do not mark mining COMPLETE.
Use INCOMPLETE_RAW_PRESERVATION and keep the source pointer.

## Review output is a mining result

A useful review may immediately identify applicability and implementation,
but implementation does not substitute for mining persistence.

IMPLEMENTED != MINED
REVIEWED != RAW_PRESERVED
SUMMARY != SOURCE

## Learning references

For education/learning material, mining should additionally capture:
- learner grade / grade band relevance
- subject / unit / concept
- terminology and morphology
- concept hierarchy
- comparison / contrast
- causal / process relations
- context-transfer/question pattern
- evidence provenance and authority class
- reusable learning pattern versus source-specific content.

Learning Engine may consume the resulting projection only within its authority.
It may select grade-appropriate learning targets and activity intent; it does
not own calendar dates or assignment facts.

## Bypass

Do not mine only when the user explicitly says, in substance:
- "보기만 해"
- "마이닝하지 마"
- "저장하지 마"
- "일회성으로만 검토해".

Internal repo/code/runtime review remains implementation review by default
unless the user designates that artifact as a reference/mining source.

## Post-mining learning projection

For references routed to `LEARNING_ENGINE`, local collection and Learning projection stay separated.
The collector acquires/preserves and hands off; it does not choose curriculum content or mutate learner state.
After Mining + Indexing has produced an `EVIDENCE_CANDIDATE`, the local post-mining refresh may run:

`node LEARNING/projection/refresh-mining-learning-projection.js`

That refresh must:
- project only explicitly mapped education-mining signals into reusable learning patterns;
- keep official curriculum/grade authority separate from reference-pattern authority;
- rebuild prelearned projections before runtime selection;
- preserve unknown/unmapped learning references as HOLD rather than guessing a pattern;
- regression-test the Learning Engine and Hide consumer before PASS.

## Completion rule

A reference review is COMPLETE only when:
1. RAW/source pointer is durable,
2. hash/dedup and metadata exist,
3. mining findings are indexed,
4. applicable domain/Learning Projection is emitted or explicitly rejected,
5. learning references with mapped reusable patterns have passed the post-mining projection refresh (or are explicitly HOLD/DISCOVERY_ONLY),
6. implementation/adoption state is recorded separately,
7. verification/read-back succeeds.

## 2026-10-13 USER DECISION — 30-day staging retention after verified RAW

- Every user-provided reference (uploaded file, screenshot, document, social URL, video, GitHub link) is an intake/mining target unless the user explicitly requests not to preserve it.
- FIRST: preserve actual original bytes where available, origin/conversation locator, capture timestamp, SHA-256, revision, rights/scope, and intact RAW pointer. A summary, link, screenshot of a webpage, or temporary file alone never establishes full source preservation.
- SECOND: route verified RAW evidence to MINING -> INDEXING -> FORMING -> applicable consumer, with non-completed stages shown as OPEN.
- The user authorizes disposal of *temporary intake copies or exact duplicates* after 30 full days ONLY if a distinct durable RAW master has been re-read and its SHA-256/size/record pointer verified. Age alone is NOT sufficient.
- Preserve the immutable RAW and its source/lineage metadata indefinitely under existing RAW policy; preserve any last remaining original, failed/partial captures, unverified references and active consumers. No cleanup of the original user's Drive file, unique attached source or canonical RAW based solely on this allowance.
- Default collector action is READ_ONLY_RETENTION_EVALUATION. Physical cleanup must be bound to a verified retention gate and scoped to temporary staging; dry-run and receipt before deleting. Never infer deletion completion from a policy document.
- ChatGPT conversation attachments cannot be assumed to enter local RAW automatically. If connector/capture/binary transfer is missing, record RAW_NOT_VERIFIED and repair intake instead of claiming COMPLETE.
