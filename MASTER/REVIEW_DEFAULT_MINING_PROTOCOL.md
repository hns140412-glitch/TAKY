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
