# TAKY INDEXING — MULTIDIMENSIONAL REINFORCEMENT / 2026-09-30 / DRAFT

Status: OPEN-only, incremental evidence-backed proposal + staged implementation; NOT new CURRENT, NOT main/release approval.
Scope: shared Indexing infrastructure for all Work/Learning/Visual/Asset/architecture consumers, **wider than Mining's source-acquisition scope**.
Owner authority: Drive \`C2S/DATA_INDEX_SCHEMA_CONTRACT_2026-09-25_V1.json\` and role contract remain operative, subject to newer specific CURRENT/overrides. GitHub main observed at review start \`c6ff1730f9e8c321cd386e585157fddc839837a1\`; PR #174 branch is divergent and MUST reconcile before merge.
Slogans: Think Again, Keep Your Key / Think Again, You're The Key. USER != DEBUGGER.

## 1. Conserved invariants
- Keep RAW / INDEX L1 / DETAIL L2 / per-namespace logical CURRENT; global Source Universe. SEARCH_PROJECTION is derived/non-authoritative.
- A source, project, person, Visual ID, layered asset, approved design, decision, artifact and runtime evidence are different *kinds of entity*. A folder or similar title does not prove they are the same identity.
- Mining discovers/acquires; Indexing owns persistent classification, identity, provenance, versions, source relations, detail locator and retrieval maps; Learning/Work/project consumers decide applicability/use; producer gate owns delivery verification. Neither source content nor a search rank grants domain permission.
- Keep physical originals where their canonical owner dictates: Drive/local for data; GitHub TAKY-ASSETS for approved reusable visual source binaries and layers, subject to rights/consent. App repos pin source revision and verified deployment copies. Do not copy private child originals to a public repo.
- Existing indexed state, historical decisions and CLOSED are inherited. Incremental-on-touch/query, no forced all-source re-ingest and no new parallel OWNER ledger. De-duplicate *meaning and identity*, not proof or history. Lossless != copy expansion.

## 2. External cross-domain findings and TAKY decision
| Axis | Source observations | TAKY disposition |
|---|---|---|
| Origin lineage | W3C PROV-O represents entity/activity/agent and derivation; OpenLineage distinguishes exact input→output edges, not all-input × all-output assumptions. | ADD evidence-anchored edge and producer consumption trace; do not infer all input/output pairings. |
| Taxonomy | DataHub separates curated glossary terms/domains from informal tags and tracks assertion evaluation history. | ADD controlled multi-facet vocab + field lineage/proof state; no silent promotion of heuristic classification. |
| Graph validation | W3C SHACL treats validation as immutable input graphs + distinct report. | ADD read-only identity/edge/conservation/claim-ceiling audit, not graph DB migration. |
| Entity resolution | Splink distinguishes deterministic and probabilistic linkage. Case/title normalization can alter real identity. | KEEP exact provider ID and scope; alias/case collision is a candidate only; binary hash proof required for exact duplicate. |
| Incremental integrity | Microsoft GraphRAG issue #2427 identifies silent mixed-case identity loss; issue #2540 details dangling entity/relationship IDs after incremental merges. | ADD exact-source-set conservation, dangling-edge checks and downstream invalidation tests; never silently drop broken links. |
| Temporal state | Drive Changes API pages \`nextPageToken\` then \`newStartPageToken\` at end. Removal can mean deleted or loss of access. | ADD read-only delta impact; commit change cursor only after complete, independently validated re-index receipt; no auto-delete or current switch. |
| Multimodal location | Docling/Docling Graph distinguish page/chunk/span/box grounding and modality-dependent OCR/layout. | KEEP existing DETAIL candidate; ADD location granularity, review extent, verified locator lineage and no false full-document claim. |
| Retrieval | OpenSearch documents BM25/vector hybrid and rank-based RRF. Ragas defines context precision. | KEEP existing exact/lexical/RRF + separately verified vector channel; compare on independent held-out queries, no new DB/vector stack without measured advantage. |
| Actual downstream effect | OpenLineage run/input/output facets and DataHub assertion history separate metadata existence from observed execution. | ADD source→consumer context→asset/code→render/output→validation references as separate stages. |
| Product quality | TAKY main \`TKY-ASSET-001\` + producer pre/post gate already own visual source/production checks. | BIND existing owners; do not reimplement production quality or call mockup/ZIP an implemented UI. |
| Privacy/rights | Source metadata access does not convey rights to reuse raw bytes or a private asset. | Keep scope-specific authorization, prevent cross-filter context leakage, record rights state and missing evidence explicitly. |
| Efficiency | Graph expansion and multimodal reinspection are more expensive than source metadata lookup. | Delta/event selective re-evaluation, bounded one-hop retrieval, DETAIL before RAW, measured cost/latency/recall; deep memory/light execution. |

Primary sources (selected originals; consulted 2026-09-30):
- https://www.w3.org/TR/prov-o/
- https://openlineage.io/docs/spec/facets/ and https://openlineage.io/docs/spec/facets/job-facets/lineage/
- https://www.w3.org/TR/shacl/
- https://github.com/datahub-project/datahub/blob/master/metadata-models/docs/entities/assertion.md
- https://github.com/moj-analytical-services/splink/blob/master/docs/topic_guides/theory/probabilistic_vs_deterministic.md
- https://github.com/microsoft/graphrag/issues/2427 and https://github.com/microsoft/graphrag/issues/2540
- https://developers.google.com/workspace/drive/api/guides/manage-changes
- https://docling-project.github.io/docling-graph/fundamentals/graph-management/provenance/
- https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/
- https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/

## 3. The minimal shared object graph (logical view only, no new central store)
Identity scope is \`namespace + source/provider native ID + object kind\`; aliases and old display names are relations, never an automatic ID merge.
- SOURCE_ORIGINAL → FRAGMENT/DETAIL_ANCHOR: source_id, locator, modality, coordinates, review coverage, independent proof scope.
- KNOWLEDGE_ATOM → SOURCE: REQUIREMENT/DECISION/CORRECTION/EVIDENCE with exact evidence anchor and authority scope.
- RELATION: from_id, to_id, typed predicate, source evidence, evidence method/review state, as-of/revision, filter/privacy scope. Candidate and recorded evidence ≠ owner attestation.
- APPROVED_VISUAL / ASSET_LAYER → Visual ID/Golden UI and TAKY-ASSETS original revision/hash/consent/slot; approved original ≠ generated preview ≠ packaged ZIP.
- CONSUMPTION_TRACE: query/owner, exact indexed refs+version, material actually used, producer output hash, pre/post gate witnesses, real render/interaction checks. Index only connects refs; owning producer verifies.
- CURRENT: one explicit logical pointer per namespace; latest filename, top search rank, inferred relation or shared asset directory cannot move it.

## 4. Implemented in this Draft
- Existing PR #174: read-only Source V6 × CURRENT V26 composer, exact and hybrid retrieval boundary, staged external bridge and DETAIL, evidence-labelled relation context, Index-first gap router; 701 composed records / 9 staged writing pairs previously replayed as **metadata/identity coverage only**.
- Added \`ENFORCEMENT/data_index_lifecycle_assurance.py\` + adversarial test:
  1. Exact expected source-ID set conservation rather than count equality; casefold title collisions counted but never merged.
  2. Source classification provenance and original-review summary proof census; unknown independent binary hash, privacy scope and DETAIL location receipt are visible coverage gaps, not false PASS.
  3. Dangling physical vs logical family/package references; unproved binary duplicate relation; recorded supersession cycles. Summary returns counts, no raw source IDs.
  4. Reverse dependency delta-impact plan (including visual/source revision and access changes) separately identifies merely RELATED_TO neighbors; repeated event ID is idempotent, conflicting replay rejected; bounded traversal and no auto cursor commit, deletion, re-indexing, CURRENT or domain-use approval.
- CI: compiler + adversarial unit regression added to \`TAKY Enforcement Replay\`. These controls are **synthetic tests**; do not confuse them with live Drive Changes API connector, real 701 post-change evaluation or a producer quality PASS.

## 5. Follow-up gates (OPEN; no premature promotion)
G0 Universe exact ID membership and source authority, scope/rights and no loss.
G1 Classification and alias/identity conflicts with provenance and source/content distinction.
G2 Relation endpoints, family logical nodes, version chains, duplicate evidence, cycle and temporal applicability.
G3 DETAIL page/frame/region coordinate and original locator verified independently.
G4 Incremental refresh correctness: provider change cursors, tombstone/access-loss distinction, impacted projections, repeat/replay, no silent dangling link.
G5 Retrieval evaluation: exact 701 per-ID when permitted, independent held-out queries (precision/recall@5, nDCG@10), negative/counterfactual and permission-leak tests; compare lexical-only vs verified neural hybrid without artificial score promotion.
G6 Consumer context assembly: approved Golden UI/Visual ID/asset manifest or source-backed learning evidence returned with scope, conflicts, missing proof and supersession; no automatic domain decision.
G7 Producer outcome evidence: source and revision actually used, actual binary/layer/hash, rendered comparison, runtime/interaction witnesses, regressions and feedback routed to correct owner.
G8 Merge/release: reconcile PR divergent head against exact live main & newer main producer/Index-owner work; independent owner receipt, authorized human approval. Main merge/Netlify remains HOLD.

Pass language: ID presence != content review; pair metadata relation != independently approved owner edge; synthetically passing CI != real 701 exact-per-ID verification; indexed source != used source; output generated != fidelity-verified production.
