# TAKY GROWTH LINEAGE CONTRACT V1

Status: ACTIVE / LOCAL
Purpose: Make TAKY learn by changing verified execution behavior, not by accumulating notes.

## Canonical loop
RAW -> INDEX -> LEARNING -> RELATION -> EXECUTION -> OUTCOME -> GROWTH

## GROW domain model
`GROW` is the shared growth core, not a third domain beside ArchiGrow/Learning Grow.
Registered domains live in `DOMAIN/GROW_DOMAIN_REGISTRY.json`.
- `ARCHI_GROW` = architecture/design/workflow/result growth.
- `LEARNING_GROW` = learning-domain growth, with `LEARNER_GROWTH` separated from `LEARNING_SYSTEM_GROWTH`.
Shared GROW owns lineage integrity and promotion gates only; domain truth remains with each domain owner.

Every downstream node keeps parent_refs + source_ref. A missing link is a HOLD, not an inferred success.

## CURRENT resolution
- GROW consumers SHALL resolve `DOMAIN/GROW_DOMAIN_REGISTRY.json -> shared_core.current_index` before interpreting any older GROW CURRENT file.
- The pointed `TAKY_GROW_CURRENT_INDEX_*.json` is the first resolution surface for scope pointers, `active_open`, CURRENT_BEST strategy, and superseded `open/next/next_gate/remaining` surfaces.
- Older GROW files may preserve historical `open` or `next*` fields for evidence, but those fields are inactive when listed under `superseded_open_surfaces`.
- `active_open=[]` means no current GROW implementation item is open. Only a new contradictory real outcome, relevant regression failure, or newly scoped GROW requirement may reopen it.
- Registry validation SHALL fail closed when `shared_core.current_index` is missing, absent on disk, or points to an older index revision.

## Stage ownership
- RAW: preserve source/evidence as observed.
- INDEX: deduplicate, entity-resolve, exact/fuzzy retrieval metadata, provenance.
- LEARNING: interpret applicability, contradiction, uncertainty and candidate lesson.
- RELATION: typed edge only: SUPPORTS / CONTRADICTS / REFINES / DEPENDS_ON / DERIVED_FROM /
  APPLIES_TO / FAILED_UNDER / SUCCEEDED_UNDER / SUPERSEDES / SAME_ENTITY.
- EXECUTION: bind the lesson to an executable rule, skill, hook, test, template or tool route.
- OUTCOME: preserve actual verified/failed/unverified result and context.
- GROWTH: decide FRONTIER/CURRENT_BEST eligibility. Never auto-promote CURRENT_BEST.

## Growth gates
FRONTIER requires verified supporting evidence.
CURRENT_BEST requires:
1. at least two distinct verified real outcomes;
2. more than one context/project condition;
3. explicit verification authority;
4. every verified outcome carries an evidence_ref and candidate evidence refs are bound to verified outcome refs;
5. synthetic outcomes/regressions are excluded from promotion evidence;
6. no unresolved confirmed failure;
7. at least one independent PASS regression with verification authority and workflow_run;
8. regression workflow runs are deduplicated and may not overlap outcome workflow runs;
9. missing or unrecognized regression status HOLDS; non-passing GitHub-style conclusions (including FAILURE/ERROR/CANCELLED/TIMED_OUT) are regression failures, never ignored;
10. no confirmed regression failure;
11. any design_parity_claim requires a USER_SIGNOFF:* design_user_signoff_ref;
12. human review before promotion, bound to the approved evidence ref using TAKY_CANONICAL_JSON_DIGEST_V1 so whitespace/line-ending conversion does not change the approval digest.
CURRENT_BEST never auto-promotes. Candidate contract violations such as promotion_authorized!=false, authority_transfer!=false, or missing event_id force HOLD before review readiness.

## Producer emission
Material producers SHALL emit `GROW_LINEAGE_EVENT_V1` automatically.
- Reference Intake: materializes RAW / INDEX / LEARNING events into the append-only shared lineage ledger.
- ArchiGrow competition learning: materializes RAW / LEARNING events into the shared architecture lineage ledger.
- Learning Grow strategy ledger: embeds OUTCOME / GROWTH events in the existing family/member durable strong store. Learner-specific raw identity/history is not copied into a global cross-domain ledger.
- Learning system growth aggregation: only privacy-safe aggregate candidates may cross the learner boundary; minimum member/outcome thresholds apply and no member identifiers are emitted. Eligible candidates are persisted idempotently in a family-scoped strong-store through `durable-learning-system-growth-store-adapter.js`; raw member rows are transient input and are not persisted in that system-growth state. After durable family-scoped persistence, the sanitized aggregate candidate is best-effort enqueued into the common `taky/grow/review-queue-v1` strong-store namespace. Queue failure never rolls back learner/system evidence and never authorizes promotion.
All producer events set `promotion_authorized=false` and `authority_transfer=false`. Materialization is idempotent by stable event id.

## Failure learning
A repeated confirmed failure is not a memory note.
It becomes:
FAILURE EVIDENCE -> ROOT CAUSE CLASS -> ALTERNATE ROUTE -> RECOVERY OUTCOME -> REGRESSION CANDIDATE.
An unresolved failure remains searchable and blocks unchanged repetition.
Resolved failure remains history and regression evidence.

## Retrieval
Use hybrid retrieval:
1. exact identifiers/constraints/current authority;
2. typed entity/relation traversal;
3. semantic similarity for discovery;
4. outcome utility/risk reranking.
Ranking precedence is hard-ordered as `EXACT -> CURRENT -> OUTCOME_UTILITY -> RETRIEVAL_SCORE`. Outcome utility is bounded secondary evidence; missing utility is neutral zero. Semantic similarity or utility may suggest/reorder within lower tiers; neither may override exact CURRENT/authority matches.
Global GROW lineage is projected into the non-authoritative `TAKY_DATA_INDEX_OUTCOME_UTILITY_V1` sidecar by `ENFORCEMENT/data_index_outcome_utility.py`. Shared `grow-lineage.jsonl` materialization refreshes this sidecar automatically as a best-effort derivative; a projection failure never rolls back or invalidates the authoritative evidence append. DATA INDEX search auto-discovers the default sidecar when present, with optional `TAKY_DATA_INDEX_OUTCOME_UTILITY` path override; explicit/CURRENT authority precedence is unchanged. Learner-private receipt identifiers are not projected as DATA source utility.

## Context/compaction defense
CLAUDE.md or memory text is advisory unless bound to executable gates.
Anti-loop execution state is durable but bounded: default storage is `~/.claude/taky/outcome-gate-state`, written atomically, without prompt excerpts, cleaned by TTL and max-file limits. This state preserves failure/verification continuity across reboot/cleanup without becoming a long-term semantic memory store.
After session resume/compaction, reload only:
CURRENT authority + active task contract + unresolved failures + relevant lineage refs.
Do not replay stale execution arguments as fresh authority.

## External/deployment boundary
LOCAL VERIFIED != DEPLOY VERIFIED.
For Netlify or another external runtime:
LOCAL RESULT -> PREVIEW/EXTERNAL VERIFICATION RECEIPT -> HUMAN APPROVAL -> PRODUCTION.
Push/merge/deploy/paid API remain approval-gated.

## Handoff policy
Handoff is recovery/transport, not semantic authority and not the default memory store.
Create a handoff only at a genuine context/process boundary; otherwise update lineage/current state.
