# TAKY Mining — baseline recovery, ecosystem comparison, and scoped improvement review
Date: 2026-09-29 / Scope: operations and a bounded regression in Draft PR #176 / Status: WORKING_DRAFT_NOT_CANONICAL

## Authority and separation
Original slogans apply globally, verbatim:
- Think Again, Keep Your Key.
- Think Again, You’re The Key.
- USER != DEBUGGER.

Canonical governance owner: MASTER/MASTER_LOGIC.md and MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md.
Mining V2 scoped implementation remains CLOSED in C2S/MINING_ENGINE_V2_CLOSURE_2026-09-25.md and CURRENT/MINING_ENGINE_CURRENT.json on its isolated V2 branch. Its verified historical implementation SHA is a historical proof, **not** current live HEAD. Operations target is 12 independently observed user-outcome runs across at least 4 families; ledger stays 0/12 until actual outcomes are recorded. A deterministic replay is not a real user result. Do not reopen ten steps, fabricate V3, rebase divergent branches, or merge/deploy without applicable review.

Roles:
- Mining: interpret user goal, recover sources, decompose questions, source/search strategy, acquire, compare, verify evidence, preserve gaps and propose changes.
- Index: durable RAW/INDEX/DETAIL/CURRENT relations/identity/search projection and original provenance; a retrieved candidate is not verified evidence.
- Domain/Learning/App/Work owner: decide applicability and utilization; Mining's research readiness is not product release approval.
- Human: purpose/meaningful decision; system performs recoverable research and validation without shifting debugging to human.

Baseline execution contract:
HUMAN INTENT → CURRENT/OWNER/SOURCE RECOVERY → QUESTION/EXPECTED PROOF → INDEX-FIRST → TARGETED EXTERNAL SEARCH → SOURCE/EXACT-CLAIM TRACE → CONFLICT/INDEPENDENCE/FRESHNESS → GAP AND ALTERNATIVE ANALYSIS → FULL-GOAL ASSURANCE → OWNER ACTION/HANDOFF → REAL OUTCOME/REGRESSION. Search hit ≠ evidence; evidence score ≠ all requirements closed; current batch complete ≠ whole goal complete; candidate report ≠ operational decision.

## Inspection and research evidence
Internal: branch TAKY/taky/mining-evidence-frontier-regression-2026-09-29 (live SHA separately checked), MASTER/MASTER_LOGIC.md; MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md; CURRENT/MINING_ENGINE_CURRENT.json; C2S/MINING_ENGINE_V2_CLOSURE_2026-09-25.md; HANDOFF/MINING_ENGINE_OPERATIONS_NEW_CHAT_START_2026-09-25_LATEST.md; existing ENFORCEMENT modules for goal decomposition, depth, Index retrieval, provider receipts, Core, provenance, pending actions, benchmark and gate workflow.

**Source-recovery result**: the operations handoff points to `C2S/MINING_INDEXING_LEARNING_ROLE_CONTRACT_2026-09-25_V1.json` and `C2S/DATA_INDEX_SCHEMA_CONTRACT_2026-09-25_V1.json`. Both exact paths returned NOT_FOUND in the checked GitHub feature branch and did not appear in its recursive tree. A separate *exact-title* search of the connected TAKY Google Drive found and fetched their full original JSON text:
- [Mining / Indexing / Learning role contract, Drive document](https://docs.google.com/document/d/1CQbKPr4uKXvy8F3SCfIbdQ1FvuCcpeG7IDGSZq2MpR4/edit?usp=drivesdk), status `ACTIVE_CROSS_ENGINE_ROLE_CONTRACT`, 2026-09-25, 6,201 text characters.
- [Data Index schema contract, Drive document](https://docs.google.com/document/d/1tGde9cw6lgnxlaC3Cnq0SfTFja_ta3R8cmavxdfmOCw/edit?usp=drivesdk), status `ACTIVE_CONTRACT`, 2026-09-25, 4,692 text characters.

The missing GitHub pointers are therefore a **repository/mirror coverage gap**, not `SOURCE_NONEXISTENT`. Drive originals preserve the explicit role map and RAW/INDEX/DETAIL/CURRENT model, but as a working/mirror surface they are not promoted into the missing GitHub path without exact source/revision reconciliation and authorized canonical write. In particular, the Index schema separates `VERSION_OF` and `EXACT_DUPLICATE_OF`; version lineage alone is NOT evidence identity.

External, classified **case/reference evidence** rather than TAKY authority:
- LangChain open_deep_research, GitHub issue #284 (2026-06-25): reported partial section completion triggering whole-report completion. #283 (2026-06-23): reported child research exception can end the supervisor, masking missing sibling work. Repo archived/read-only 2026-08-21; treat incidents as design counterexamples, not proof the current main is unfixed.
  https://github.com/langchain-ai/open_deep_research/issues/284
  https://github.com/langchain-ai/open_deep_research/issues/283
  https://github.com/langchain-ai/open_deep_research
- Its #252 (2026-03-09) reports latest-context loss during compression; #296 (2026-07-26) proposes concept-diff ingestion/token savings, but is a proposal and not a validated universal zero-loss result.
  https://github.com/langchain-ai/open_deep_research/issues/252
  https://github.com/langchain-ai/open_deep_research/issues/296
- GPT-Researcher issue #1893 (2026-07-13; later closed) documents source URL metadata loss causing fabricated placeholder citations. Its research tooling distinguishes snippet retrieval from full-source reading and tests citation grounding. Older issue state must not be presented as current unresolved behavior.
  https://github.com/assafelovic/gpt-researcher/issues/1893
  https://github.com/assafelovic/gpt-researcher/blob/main/deep_agents/BENCHMARK.md
- Official OpenAI Agents SDK documentation documents separate tool/input/output validation and traceability; use this as a pattern comparison, not an instruction to add many agents or migrate the stack.
  https://openai.github.io/openai-agents-python/guardrails/
  https://openai.github.io/openai-agents-python/tracing/

## Scoped gap / disposition / owner

| ID | Evidence-backed missing or weak behavior | Disposition and owner | Exit proof |
| --- | --- | --- | --- |
| MG-01 | Handoff references two exact paths missing in GitHub, though originals recovered in connected Drive | SOURCE_RECOVERED_IN_DRIVE / GOVERNANCE provenance reconciliation HOLD; preserve semantic ownership | Verify Drive original content/revision against authorized canonical owner, then repair pointer explicitly without overwriting branch state |
| MG-02 | Core candidate score can be high without fetched original/exact anchor/claim review | ADJUST / MINING operations assurance, implemented in Draft #176 `mining_research_assurance.py`; Core legacy candidate scoring retained | Required goal IDs all source-grounded in independent audit; missing proof yields next action |
| MG-03 | Partial batch CLOSED may be mistaken for whole-goal CLOSED after resume | ADJUST / MINING Core in Draft #176, preserve original required inventory and queued depth overflow | 2-stage 3-critical-item regression; defer third until evidence and no premature STOP |
| MG-04 | Provider/source URL or source group can vanish / be miscounted across adapters | ADJUST / Mining exact-ID read-only Index provenance bridge + operational snapshot digest/quote audit | Source identity, exact excerpt and citation trace survive normal receipt, checkpoint and planned report; URL alone not independent publisher proof |
| MG-05 | Caller could nominate its own trusted reviewer through payload | ADJUST / MINING host boundary: orchestrator ignores caller-supplied reviewer allowlist; direct audit requires separate host-owned trusted list | Forged request allowlist and provider self-certification do not produce operational READY; authenticated host integration remains OPEN |
| MG-06 | `fresh_enough=True` default does not prove current validity of changing rules/data | ADJUST / operational assurance requires explicit as-of and source-update date when freshness requested; domain owns acceptable window | Missing dates/threshold = FRESHNESS_UNVERIFIED; stale version = reacquisition action |
| MG-07 | Same failed/empty route retry can turn into failure churn | ADJUST / existing failure memory and provider changed-route fallback; query-revision planner remains OPEN | Failure preserves successful siblings, yields changed permitted route or HOLD; no false full success |
| MG-08 | Report/export citations may still lose references after compression or snapshots | OPEN / Mining synthesis + consuming report owner | Per-claim source-pointer round-trip at report/export; no placeholder citation or missing referenced IDs |
| MG-09 | Repeated source content is costly yet can hide new conflicts | HOLD EXPERIMENT / Index/Mining candidate, inspired by #296 only | Immutable RAW pointer + compact claim diff; before/after comparison proves zero material omission/conflict loss, cost benefit |
| MG-10 | Test fixtures/live-captured receipts might be mistaken for user outcomes | PRESERVE / OPERATIONS ledger strict, 0/12 | Independent recorded usable outcome, not a test run or source listing |
| MG-11 | End-to-end publisher identity is uncertain when Index has no reviewed group; reviewed-group fields used in a test are not part of the recovered INDEX_L1 schema | HOLD OWNER CONTRACT EXTENSION / Index authority, Mining fail-closed corroboration | Index-owned reviewed group identity contract before any upstream write; no independent-source count inferred from URL count |

**Recovered schema-specific correction:** `VERSION_OF` and `SUPERSEDES` describe version relations, not exact evidence duplication. Only `EXACT_DUPLICATE_OF` is used by the temporary Mining read-only bridge to group publication surfaces; even that cannot establish two independent reviewed publishers. The extra sample `canonical_source_id` and `source_group_reviewed` fields are working assumptions only, not claimed native fields in the recovered 2026-09-25 Index L1 schema.

## Targeted standard (working draft, not adopted canonical)
1. Each materially required frontier ID must survive depth caps, fallback, checkpoint/resume and synthesis with ID, question, owner, reason, next action, completion evidence and source pointer. Generic scaffolding is optional unless authorized into scope.
2. A source record requires real locator, source/version or snapshot identity, retrieval/access outcome (FETCHED / ACCESS_HOLD / NOT_FOUND_UNVERIFIED), date/freshness scope and original authoritative class. `SEARCH MISS != SOURCE ABSENCE`; `ACCESS FAILURE != SOURCE ABSENCE`.
3. A claim that can enter an operational result requires an actual fetched source snapshot (raw bytes/text checked), SHA-256, an exact passage and its location, separate claim-support review with reviewer identity issued by a **trusted host** (not user/provider request), and alignment to the same frontier/source/revision. A mere citation-shaped string, source hit, high score, or provider `direct_support` assertion is a candidate.
4. Corroboration counts distinct verified source groups, not multiple URLs/pages of one publisher or provider-declared counts. Conflict/published-date/applicability gaps remain OPEN and cannot be collapsed by synthesis. A current official listing proves service description, not live authenticated endpoint success.
5. Completion is whole-goal, not per-child/per-batch. Any missing required item, tool exception, access failure, unresolved contradiction, stale source, lost citation or unauthorized reviewer gives a classified HOLD/OPEN with next action. Preserve successful sibling receipts. Neither token compression nor handoff may delete immutable source pointers/revision or newer corrections.
6. A valid operational synthesis has a claim → exact excerpt → verified source → frontier/goal → current authority → owning consumer path in both directions. Consumer acceptance and user outcome are separately recorded; no automatic promotion/merge/deploy.
7. Source handling minimizes sensitive raw data, never treats page content as tool instructions, and avoids unauthorized access. User authority does not transfer operational debugging to user.

## Exact implementation boundary
The attached Draft #176 includes source/claim operational assurance, scoped input/output tests and explicit `operational_research_ready`. This is **not** a universal source reader, authenticated-review identity service, source-publisher cryptographic verification, new canonical Index contract, full report/export QA, or externally exercised real task. The caller-supplied `trusted_reviewer_ids` field is deliberately ignored by normal orchestrator; host-owned reviewer authentication/wiring stays OPEN. A passing CI fixture is not a real Operations outcome. Main, CURRENT and Netlify remain unchanged and PR stays Draft/HOLD.

## Next bounded execution (no default V3)
- Recover the exact owner location of MG-01 references without inventing lost material.
- Wire a privileged reviewer identity and source-reader receipts to the standalone operational gate only when real hosting authorization exists; validate end-to-end source-claim-report citation trace.
- Test injected child failure/partial parallel scope, empty or stale source, SOURCE_NOT_RETRIEVED, duplicate current/old sources and lossless compressed manifest.
- Run actual 12-run operations campaign only with independently observed user outcomes (at least 4 task families; at least 3 for any family-specific strategy review), record measured useful results with timestamps and evidence pointers.
- Reclassify after concrete new findings; no main merge or Netlify deployment by implication.

End: COMPARE TO LEARN, NOT TO COPY; DEEP MEMORY — LIGHT EXECUTION; USER != DEBUGGER.
