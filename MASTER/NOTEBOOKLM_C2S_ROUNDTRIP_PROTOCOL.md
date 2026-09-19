# TAKY DRIVE-FIRST C2S + OPTIONAL NOTEBOOKLM PROTOCOL

Status: REV_01 / OPERATIONAL
Rule ID: TKY-C2S-ROUNDTRIP-001

## 0. Core architecture — HARD LOCK

Canonical recovery path:

`RAW / GOOGLE DRIVE → SOURCE REGISTRY → RAW RECHECK → C2S ATOMS → CANONICAL OWNER → PROJECT CONTEXT MANIFEST → COVERAGE / SEMANTIC INTEGRITY → REVERSE RECONSTRUCTION`

This path MUST work without NotebookLM.

NotebookLM is OPTIONAL evidence assistance only:

`DRIVE RAW → NOTEBOOKLM → CANDIDATE OUTPUT → RAW RECHECK → C2S`

`NOTEBOOKLM AVAILABLE != REQUIRED`
`NOTEBOOKLM UNAVAILABLE != C2S BLOCKED`

## 1. Drive-first source gate

Every material recovery source should have:
- unique source pointer / id;
- source class;
- actor/chronology recoverability where applicable;
- authority classification;
- content/security check before external analysis use;
- explicit inaccessible/unverified status when source cannot be opened.

Derived summaries/Handoffs may assist discovery but may not override recoverable raw/user evidence.

## 2. Required C2S path

For canonical-impact material:
1. open/read raw or preserved source;
2. determine actor;
3. determine chronology;
4. check later user corrections;
5. atomize material content;
6. preserve WHY / relation / supersession;
7. assign disposition and owner/destination;
8. run coverage + semantic-integrity validation;
9. update project context manifest/current truth as appropriate;
10. run reverse reconstruction.

If raw source is unavailable:
- do not invent;
- retain `UNVERIFIED_SOURCE_COVERAGE`, `OPEN`, `HOLD`, or `CONFLICT` as appropriate.

## 3. Required completion gate

A project recovery cycle can PASS without NotebookLM when all required Drive/C2S gates pass:

- required source registry / source pointers available for declared scope;
- raw-source recheck complete for canonical-impact material;
- conversation coverage validator PASS;
- semantic integrity validator PASS;
- project context gate PASS;
- reverse reconstruction PASS;
- `UNMAPPED_MATERIAL = 0`;
- `SILENT_LOSS = 0`;
- `FALSE_CONVERGENCE = 0`.

Historical ranges outside the declared/recoverable scope remain `UNVERIFIED_SOURCE_COVERAGE`.

## 4. Optional NotebookLM assist

NotebookLM may be used for:
- chronology candidates;
- omission/silent-loss candidates;
- correction-lineage candidates;
- contradiction candidates;
- cross-source topic clustering;
- reverse-reconstruction drafts.

NotebookLM output remains:
- `REFERENCE_ONLY` or `EVIDENCE_ASSIST`;
- `NOT_CANONICAL` / `PENDING_RAW_RECHECK`;
- never authoritative without raw recheck.

NotebookLM confidence is not TAKY confidence.

## 5. NotebookLM input/output validation

If NotebookLM is used:
- input source registry must pass NotebookLM source safety/authority validation;
- output must pass NotebookLM output-intake validation;
- all canonical-impact candidates require raw recheck;
- NotebookLM output may never be recursively promoted as RAW/DIRECT_SOURCE.

Failure of this optional assist path blocks only NotebookLM-derived claims, not the core Drive→C2S pipeline.

## 6. C2S semantic integrity

C2S compile cannot PASS when:
- a correction lacks supersedes/affects linkage;
- OPEN/CONFLICT is silently resolved;
- multiple atoms are merged without equivalence evidence;
- inaccessible source ranges coexist with FULL coverage claims;
- derived/NotebookLM output is treated as raw authority;
- reverse reconstruction cannot recover latest corrections, open items, WHY or intent.

## 7. Automation boundary

Current ChatGPT environment has Google Drive access but no direct NotebookLM connector.

Therefore:
- Drive-first C2S is the required automated/recoverable path;
- NotebookLM is an optional external assist path only;
- no user action in NotebookLM is required for C2S completion.

## 8. Next-phase gate

Only after the Drive-first C2S path passes structural, adversarial, real-project and reverse-reconstruction tests may account-wide source audit begin.

END
