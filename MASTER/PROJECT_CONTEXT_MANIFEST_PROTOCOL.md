# TAKY PROJECT CONTEXT MANIFEST PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-CONTEXT-001
Owner: TAKY
Purpose: Ensure that "타키 기준", resume, and project execution reconstruct the project's required durable context before implementation or validation begins.

## 0. Core rule — HARD LOCK

A project may not claim TAKY-context readiness merely because global TAKY rules are loaded.

Required chain:

`PROJECT IDENTIFY
→ LOAD PROJECT CONTEXT MANIFEST
→ LOAD REQUIRED CANONICAL OWNERS
→ LOAD LATEST CORRECTIONS / HARD LOCKS / SUPERSEDED / OPEN-CONFLICT
→ LOAD CURRENT IMPLEMENTATION STATE
→ TARGETED NOTEBOOKLM/DRIVE RECOVERY WHEN GAPS REMAIN
→ CONTEXT COVERAGE VALIDATION
→ EXECUTE`

`GLOBAL TAKY LOADED != PROJECT CONTEXT COMPLETE`

## 1. Trigger

This gate is required when the user says, or clearly invokes:
- 타키 기준
- 최신 타키 기준
- /재개
- 최신 기준으로 재개
- project continuation where prior user decisions materially constrain implementation
- C2S reconstruction/backfill

## 2. Context manifest

Each durable project SHOULD own one machine-readable manifest listing:
- project_id / aliases
- canonical project baselines
- required project contracts
- required global TAKY rules
- latest correction/history ledgers
- known HOLD / OPEN / CONFLICT items
- superseded/rejected items
- current implementation authority
- Drive long-memory sources
- NotebookLM recovery packs / topic maps
- escalation order
- coverage stop conditions

## 3. Layered recovery — HARD LOCK

Use smallest sufficient working set:
- L0 HOT: current conversation / current task state
- L1 WARM: current truth, project manifest, latest handoff, latest corrections
- L2 INDEXED: NotebookLM / Drive source registry / topic map
- L3 RAW: original preserved conversations / attachments / source captures
- L4 FULL FORENSIC: full available-source reconstruction

Rules:
- ASK LAST
- FULL SCAN LAST
- do not re-ask recoverable facts
- do not infer missing historical decisions
- inaccessible coverage remains UNVERIFIED_SOURCE_COVERAGE

## 4. NotebookLM boundary

NotebookLM is a context-recovery and evidence-assist layer, not canonical authority.

`NOTEBOOKLM OUTPUT → RAW SOURCE POINTER → USER/ASSISTANT AUTHORITY CHECK → LATEST CORRECTION CHECK → C2S ATOMIZE → CONTEXT MANIFEST/OWNER UPDATE`

NotebookLM output without source confirmation is REFERENCE_ONLY / EVIDENCE_ASSIST.

## 5. Execution block

For manifest-controlled project work:

`REQUIRED_CONTEXT_MISSING > 0 = CONTEXT_GATE FAIL`

A FAIL blocks implementation claims that depend on the missing context.

The system may continue only to recover/fix the missing context.

## 6. Freshness

A project context manifest must identify freshness anchors for:
- latest canonical contract
- latest project current truth
- latest correction ledger
- current implementation branch/head when implementation state matters

Stale Handoff or summaries may not override fresher authoritative state.

## 7. Reverse reconstruction

Before context gate PASS, the loaded context must reconstruct without invention:
- project role/purpose
- key UX/product semantics
- hard locks
- latest user corrections
- rejected/superseded directions
- unresolved conflicts
- current implementation state
- next executable gate

## 8. Claim boundaries

`MANIFEST EXISTS != SOURCES LOADED`
`SOURCES LOADED != CONTEXT COVERAGE PASS`
`NOTEBOOKLM ANSWER != CANONICAL DECISION`
`CONTEXT PASS != IMPLEMENTED`
`IMPLEMENTED != DEVICE/RELEASE VERIFIED`

END
