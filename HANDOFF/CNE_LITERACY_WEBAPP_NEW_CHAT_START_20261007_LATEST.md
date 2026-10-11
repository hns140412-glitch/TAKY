# CNE LITERACY → CHILD WEBAPP NEW CHAT START — 2026-10-07 LATEST

## RESUME RULES
- Resume only this OPEN stream. Do not re-audit/rewrite MASTER/Beta/Alpha or unrelated TAKY work.
- All listed repos are dirty. **NO reset / checkout / clean / mass-format / overwrite of unrelated dirty work.**
- USER≠DEBUGGER. Avoid repeating failed paths.
- Netlify / deploy / push / merge / paid API: NOT AUTHORIZED.
- Family private / non-commercial / non-public use. Mining default = RAW-first.
- RAW originals are evidence authority and immutable; INDEX/DETAIL/Learning Projection are derived and regenerable.
- External redistribution/sharing is the point where a rights gate is re-opened; do not impose commercial-distribution constraints on private family learning runtime.

## REPOS / RESUME HEADS
- TAKY: D:\Git PWA\TAKY
  - HEAD fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e
- Hide & Seek: D:\Git PWA\Hide & Seek
  - HEAD 5b29db8299237d41f9ce6d054256dda765f9cd09
- Snap & Pop: D:\Git PWA\Snap & Pop
  - HEAD 94d548545b3c4bd04008d767a27c9cc9e0bcf28c
- Ready & Set: D:\Git PWA\READY-WEBAPP-20261006
  - HEAD 2d10583713a82dae2fb55f2aa7f482df4f578193
- Source vault (not git): D:\Git PWA\TAKY-SOURCE-VAULT

## FIXED INTENT
Mining is not complete when materials are merely collected/indexed.
Completion path:
RAW → INDEX → Learning Projection → app consumer contract/code → test → child learning value.

Child-app role boundary:
- Hide & Seek = vocabulary / term decoding / retrieval evidence.
- Snap & Pop = concept-expression / read-to-write transfer evidence.
- Ready & Set = execution/base camp; Planner owns dated allocation.
- Learning Engine = interpretation/adaptive intent; does NOT own dates.

## CNE LITERACY RAW / VERIFIED FACTS
Base:
D:\Git PWA\TAKY-SOURCE-VAULT\data\external_raw\cne_literacy\2026-10-07

Primary files include:
- ACADEMIC_VOCAB_1387_RESEARCH_2024.pdf
- ACADEMIC_VOCAB_1387_FULL_ORIGINAL.pdf
  - SHA256 b3da6a46f6f6505d3c5a92c594a477d96145f4139ef614f760e89e98bcd07b88
  - 69 pages
  - exact extracted families = 1,387
  - level counts = 43 / 293 / 585 / 466
  - count_validation = PASS
- CNE_ONDOK_INDEX_2026.pdf
- CNE_ONDOK_USAGE_LECTURE_2025.pdf
- CNE_SAGAKSAGAK_ONGEUL_2026.pdf
- CNE_2026_EVALINFO_PLAN.pdf
- CNE_ONGEUL_ANNOUNCEMENT_2025.html
- CNE_SAGAKSAGAK_PAGE_2026.html

Derived:
- ACADEMIC_VOCAB_1387_INDEX_V1.json
- ACADEMIC_VOCAB_1387_LEVEL_MAP_V1.json
- ACADEMIC_VOCAB_ELEMENTARY_336_V1.json
  - level 1 = 43
  - level 2 = 293
  - E5/E6 policy: level 2 primary, level 1 foundation; do not dump all 336 to child
- CNE_LITERACY_INDEX_CANDIDATE_20261007.json
- CNE_LITERACY_LEARNING_PROJECTION_CANDIDATE_20261007.json
- CNE_WEBAPP_CONSUMER_PROFILE_20261007.json
- CNE_LITERACY_WEBAPP_E2E_RECEIPT_20261007.json

Important interpretation:
- Existing subject/curriculum term catalog and academic vocabulary are PARALLEL layers, not the same vocabulary set.
- Exact cross-match against current 26 curriculum terms found only 2 exact matches.
- Therefore do NOT merge/replace curriculum terms with all 1,387 academic vocabulary.
- Use academic vocabulary as a cross-subject literacy overlay/context signal.
- Ondok is a material readability signal, NOT learner-ability truth.

## IMPLEMENTED THIS STREAM

### TAKY
New:
- LEARNING/pedagogy/literacy-webapp-bridge.js
- LEARNING/pedagogy/literacy-webapp-bridge.test.js
- LEARNING/projection/academic-vocab-elementary-336-v1.json

Modified:
- LEARNING/transport/term-recommendation-http-endpoint.js
  - returns literacy_intent with term recommendations
- LEARNING/transport/term-recommendation-http-endpoint.test.js

NOTE:
git status also currently shows untracked:
- LEARNING/pedagogy/academic-vocab-overlay.js + test
- LEARNING/pedagogy/academic-vocab-unit-selector.js + test
- LEARNING/intake/term-catalog-source-resolver.js + test
- LEARNING/verification/prelearned-term-universe.e2e.test.js
These were present in the dirty tree at resume-prep time. **Read/understand them before writing overlapping code. Do not overwrite blindly.**

### Hide & Seek
Modified:
- hide-learning-term-loader-v1.js
  - keeps body.literacy_intent in engine projection
  - static pack also consumes pack.literacy_intent
- hide-bridge.js
  - transports literacy_flow / academic_vocab_term / academic_vocab_level / reading_material_ondok to Snap
- index.html
- sw.js

New:
- hide-literacy-adapter-v1.js
  - decorates Learning Engine recommended TRACE/LINK/CORE/RECALL modes
  - enriches Hide evidence with literacy_context

Static recommendation packs:
- data/learning-term-recommendation-packs-v1.json
  - 30 stage×subject packs enriched with literacy_intent

### Snap & Pop
Modified:
- snap-bridge.js
  - accepts literacy context params
- index.html
- sw.js

New:
- snap-literacy-adapter-v1.js
  - READ_TO_WRITE_CONCEPT_TRANSFER prompt adaptation
  - completed Snap evidence adds writing_transfer_stage=TRANSFER_COMPLETED
  - carries academic vocab term/level + reading material ondok

### Ready & Set
Modified:
- ready-runtime-v07.js
  - learningScope can transport literacy_flow / academic_vocab_term / academic_vocab_level / reading_material_ondok
  - specialist handoff passes those params
- Do not disturb existing VS-004 dirty work.

## VERIFIED
PASS:
- node TAKY/LEARNING/pedagogy/literacy-webapp-bridge.test.js
- node TAKY/LEARNING/transport/term-recommendation-http-endpoint.test.js
- CNE_LITERACY_WEBAPP_E2E_VERIFY_20261007.js
  - status PASS
  - Hide static literacy intent
  - adapter load order before evidence
  - offline cache binding
  - Ready→Hide/Snap literacy transport
  - Hide→Snap literacy transport
  - Snap read-to-write prompt runtime
  - evidence enrichment
  - Planner dated-allocation boundary preserved
  - central endpoint literacy_intent
- Ready tests/ready-continuity-b-v2.mjs PASS

Known non-regression blocker:
- tests/ready-specialist-bridge-contract.mjs expects legacy D:\tmp\hide-bridge.js fixture and stops ENOENT.
- Existing Ready docs already note that fixture absence. Do NOT treat it as a new literacy regression.

## NEXT OPEN — DO IN THIS ORDER
1. **First inspect the existing untracked TAKY files**
   - academic-vocab-overlay.js/test
   - academic-vocab-unit-selector.js/test
   - term-catalog-source-resolver.js/test
   Determine whether they already implement the next step. Reuse rather than duplicate.

2. Bind the 336 elementary academic-vocabulary projection into Learning Engine as a **parallel literacy overlay**:
   - E5/E6 primary = level 2
   - level 1 = foundation/fallback
   - higher levels only when curriculum/unit context requires
   - never present all 336 at once

3. Implement/select academic vocab from actual unit/task/problem text:
   curriculum/unit context + sentence/question text + learner evidence → small candidate set.
   TEXT MATCH = candidate signal only, not mastery or official curriculum claim.

4. Ready consumer:
   when a Planner task/problem contains a selected academic vocab target, project:
   - academic_vocab_term
   - academic_vocab_level
   - literacy_flow when expression transfer is useful
   Then specialist routing owns no schedule date changes.

5. Hide:
   selected academic vocab must become an actual child-facing decoding/retrieval activity with evidence.
   Keep subject-term decoding and academic-vocab decoding distinguishable in provenance.

6. Hide → Snap:
   after appropriate recovery/understanding, hand off one target word/context to Snap for read-to-write transfer.
   Evidence must return to Learning Engine.

7. E2E browser verification:
   Ready task → Hide academic vocab → Hide evidence → Snap transfer → Snap evidence → Ready return.
   Preserve same session/task/lap and Planner authority.
   No deploy.

## COMPLETION CRITERION FOR THIS STREAM
Not “1,387 words indexed.”
Complete only when an E5 child task can:
- detect/select a small relevant academic-vocab set,
- practice it in Hide,
- transfer one concept/word into expression in Snap when useful,
- emit learner evidence,
- return to Ready without schedule-authority leakage,
and all of that is backed by RAW provenance + repeatable tests.

## FIRST COMMANDS ON RESUME
1. Read this file only.
2. Check current HEAD/status of the four git repos.
3. Read the four untracked TAKY overlay/resolver files named in NEXT OPEN #1.
4. Continue OPEN only. No reset/clean/rewrite.
