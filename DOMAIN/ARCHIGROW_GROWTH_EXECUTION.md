# ARCHI GROW — domain growth execution binding (draft)

This is an **execution adapter of existing** `DOMAIN/ARCHITECTURE_GROWTH_MAP.md`, `DOMAIN/ARCHITECTURE_WORK_OS.md`, `MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md` (`TKY-GROWTH-001`) and TAKY's Work OS. It is not a new OS, semantic authority, self-changing agent or project delivery engine.

## Core growth motor

`real architectural question / failed output -> existing INDEX query -> MINING only on proven source deficiency -> ARCHI GROW method comparison/localization -> WORK OS bounded real-work trial -> independently evidenced outcome and regression -> ARCHI GROW adjust/re-test or human adoption review -> existing CURRENT_BEST/FRONTIER owner.`

Separate `CASE` (observed project), `STRATEGY` (reusable method), `FRONTIER` (credible candidate), `CURRENT_BEST` (approved scope-specific method), `FAILURE/LESSON` (observed failure). All evidence retains original source, project/REV and status. Research findings and fixture pass are not successful real-work outcomes.

### What actually triggers progress

- Every material new project result, review discrepancy or new external case creates/updates a **single stable gap** in the existing domain gap ledger, not a new policy document.
- The deterministic adapter `architecture_growth_cycle.py` emits one next-owner and one proof-oriented next action. `architecture_growth_event_replay.py` accepts source-owner receipts as append-only JSONL, rejects duplicate-content conflicts and frozen-scope events, and derives a fresh next-action board without rewriting RAW or CURRENT. It never executes searches, deployment or edits other repositories.
- `architecture_source_probe.py` directly loads the EXISTING `ENFORCEMENT/data_index_search.py` and a separately supplied real V26 or later index payload; the output is candidates, snapshot SHA and owner-review checklist, NEVER an `INDEX_RESULT` or `sufficient=true` receipt. Source-role context (`DOMAIN_GAP_CONTEXT`) cannot be used as eligible project/method evidence.
- If Indexing has not returned a dated receipt: request indexed evidence first. Only a checked, insufficient index result may trigger a Mining request. No duplicate blind collection.
- `architecture_work_os_proof.py` checks actual bytes against a Work OS-owned manifest, project/revision/trial/outcome bindings and baseline/observed values. A replayed `PASS` without an evidence root and manifest hash is rejected; the hash preflight alone does NOT verify technical truth or authorize adoption.
- Once a source-backed method is documented, hand off its measurable baseline/acceptance/metric to the existing Work OS. An actual result with independent verification and regression evidence is required for adoption review; not sufficient for automatic promotion.
- Failed or partial outcomes route to architectural method correction, rather than repeated identical validation. HUMAN decides changes to accepted company standards.

### Protected scope

CTB, LISP and Hannam case are explicit user HOLD. They cannot be selected even if mistakenly marked OPEN while carrying a frozen tag. No main merge, deployment, legal compliance claim, autonomous source authority change, or synthetic project metrics. An explicit user resume instruction is required.

## One evidence packet and one board

`architecture_growth_backlog.json` is the single small **support** record for gap identity and next-evidence contract. It does not hold raw files. Raw evidence remains with the original owner; the refs identify its location, revision and role. Output is only a disposable derived board, not a second CURRENT. Existing Work OS owns task execution and outcome receipts; TAKY owns final governance.

Run:

```bash
python3 DOMAIN/architecture_growth_cycle.py DOMAIN/architecture_growth_backlog.json --output /tmp/architecture_growth_board.json
python3 -m unittest discover -s DOMAIN -p 'test_architecture*.py' -v
# When source owners supply an append-only receipts file:
python3 DOMAIN/architecture_source_probe.py --backlog DOMAIN/architecture_growth_backlog.json --index path/to/actual-V26.json --search-engine ENFORCEMENT/data_index_search.py --output /tmp/architecture_index_candidates.json
python3 DOMAIN/architecture_work_os_proof.py --manifest path/to/work-os-owned-manifest.json --evidence-root path/to/evidence-folder
python3 DOMAIN/architecture_growth_event_replay.py DOMAIN/architecture_growth_backlog.json path/to/receipts.jsonl --evidence-root path/to/evidence-folder --output /tmp/architecture_growth_replayed.json
```

Initial next action is **AG-GAP-001 INDEX_QUERY_REQUEST**. This is *not* an assertion that Indexing already ran; the next owner must provide a real receipt before the machine can route to Mining or method synthesis. The backlog also carries cross-project ALT continuity and nonresidential transfer gaps, plus protected HOLDs.

## Definition of meaningful growth

A gap closes only when a real deliverable/evidence trace meets its own declared acceptance and an authorized review records scope, trade-offs, failure conditions and regression result. Count source collections and test executions separately from user-visible improvements. Use Work OS `GOAL -> DISCOVER -> BUILD -> VERIFY -> SHIP -> LEARN` without copying its implementation here.

## Status / authority

Draft PR only until reviewed. No canonical adoption, main replacement, actual Mining invocation, public API call or Work OS project execution is implied by successful routing tests.

## Explicit unclosed integration gates

- A real V26 index metadata check found 27 architecture-classified source entries; all were `METADATA_INDEXED` and `WORK_REFERENCE_NOT_RUNTIME_TRACED`. These are candidates, not 27 validated usable sources. Actual payload and source IDs are not redistributed in this public repository.
- The source suitability/currentness/applicability review and actual owner-issued Indexing receipt are OPEN. An index result issuer string and hash alone are evidence consistency hints, not external identity authentication.
- Neither remote project files nor hosted APIs are fetched by this router; Work OS real-project execution is not established.
