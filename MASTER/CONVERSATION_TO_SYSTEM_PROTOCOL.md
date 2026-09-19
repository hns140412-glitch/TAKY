# TAKY CONVERSATION-TO-SYSTEM PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-C2S-001
Role: Convert conversational co-design into durable, traceable, growing TAKY system knowledge without lossy summarization, silent omission, false convergence or premature canonicalization.
Authority: TAKY / GRAND MASTER > this protocol > lower-layer conversation/domain specializations.
Related: `MASTER/CONVERSATION_CONTEXT_LEDGER_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`, `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`, `MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md`.

## 0. Core principle — HARD LOCK

Conversation is not disposable narration. In TAKY, material conversation is a design/source stream from which requirements, corrections, decisions, strategies, open questions, evidence and frontier ideas are progressively formed.

`GOOD SUMMARY != LOSSLESS SYSTEM BUILD`
`FINAL SENTENCE != FULL DECISION FORMATION`
`REFLECTED CORE != DETAIL COVERED`
`CLEAN DOCUMENT != COMPLETE KNOWLEDGE`
`MISSING FROM SUMMARY != INTENTIONALLY REMOVED`

The completion condition is not "a good summary was written." It is:

> Every materially relevant recovered conversation item has a traceable system disposition, destination, lineage and current status, while inaccessible source ranges remain explicitly unverified.

## 1. Two-layer preservation — HARD LOCK

TAKY SHALL preserve both:
1. **Evidence layer** — original recoverable conversation/source evidence and stable pointers;
2. **System layer** — atomic interpreted items linked to canonical owners, project/domain state, implementation and open work.

The system layer SHALL NOT replace the evidence layer.

`RAW/ORIGINAL EVIDENCE -> ATOMIC EXTRACTION -> RELATIONSHIP GRAPH -> OWNER REFLECTION -> IMPLEMENTATION/LEARNING`

## 2. Atomic extraction taxonomy

Material conversation SHALL be decomposed into the smallest decision-relevant units that can change independently.

Allowed primary atom types:
- `REQUIREMENT`
- `DECISION`
- `CORRECTION`
- `IDEA`
- `FRONTIER`
- `STRATEGY`
- `CONFLICT`
- `OPEN`
- `EVIDENCE`
- `ASSUMPTION`
- `REJECTION`
- `CONSTRAINT`
- `OUTCOME`
- `LESSON`

One sentence may create multiple atoms. Multiple sentences may form one atom only when separating them would destroy meaning.

Assistant proposals SHALL NOT silently become user-confirmed decisions.

## 3. Required atom fields

A material atom SHOULD retain, when available:
- stable `atom_id`;
- source/conversation pointer and sequence;
- actor/source class;
- atom type;
- concise semantic content;
- materiality;
- scope: global/domain/project/tool;
- rationale / WHY;
- latest correction pointer;
- disposition;
- canonical owner or destination;
- dependencies;
- affects / impact targets;
- supersedes / superseded_by;
- evidence links;
- implementation status;
- validation/verification status;
- unresolved condition / exit condition;
- coverage status.

Machine-readable baseline schema: `MASTER/CONVERSATION_ATOM_SCHEMA.json`.

## 4. No Silent Loss — HARD LOCK

A material recovered atom SHALL NOT disappear merely because:
- a later summary is shorter;
- a Handoff omits it;
- a new MASTER is cleaner;
- the current task focuses elsewhere;
- the item is inconvenient to classify;
- a newer idea seems similar.

Every material atom must end in an explicit state/destination such as:
`PRESERVE / ADOPT / ADJUST / HOLD / REJECT / EXCLUDE / OWNERSHIP_TRANSFER / CONFLICT / SUPERSEDED / OPEN / FRONTIER`.

Removal from active routing requires a recorded reason and lineage.

## 5. No False Convergence — HARD LOCK

TAKY SHALL NOT merge distinct ideas merely to make the model/document simpler.

Preserve parallel approaches when they represent materially different:
- goals;
- trade-offs;
- risk profiles;
- design philosophies;
- implementation routes;
- stable vs frontier strategies;
- user choices not yet resolved.

A merge is allowed only when the relationship and lost distinctions have been checked. If meaningful distinctions remain, use linked sibling atoms rather than one flattened summary.

## 6. Correction propagation — HARD LOCK

A user correction is not a note attached to the latest answer. It is a graph mutation.

Required flow:
`CORRECTION -> IDENTIFY SUPERSEDED/ADJUSTED ITEM -> IDENTIFY AFFECTED OWNERS/ARTIFACTS -> UPDATE REQUIRED/INVALIDATED/RETEST CLASSIFICATION -> REFLECT -> COVERAGE RECHECK`.

A correction that changes a governing concept SHALL trigger impact review across dependent modules. Updating only one prose surface is incomplete.

`CORRECTION CAPTURED != CORRECTION PROPAGATED`

## 7. Conversation compile flow

For material system-building conversations:

`RECOVER SOURCE SCOPE
-> ATOMIZE
-> LINK WHY/CORRECTIONS/DEPENDENCIES
-> COMPARE WITH CURRENT TAKY
-> CLASSIFY DELTA
-> MAP TO OWNER/FRONTIER/OPEN/HISTORY
-> ROUTE AUTHORIZED REFLECTION / DOWNSTREAM ACTION
-> COVERAGE CLOSURE
-> REVERSE RECONSTRUCTION
-> RECORD COMPILE DELTA
-> APPLY/VERIFY OWNER REFLECTION AS A SEPARATE STATE WHEN REQUIRED`

Do not jump directly from chat to a rewritten MASTER.

### 7.1 Compile closure vs reflection completion — HARD LOCK

C2S compilation and owner reflection are adjacent but independent states.

- `C2S_COMPILE_CLOSED`: recovered-scope material meaning is atomized, linked, dispositioned, owned/destined, coverage-closed and reverse-reconstructable.
- `REFLECTION_COMPLETE`: all atoms whose disposition requires an authorized owner/canonical change have actually been reflected and verified in the owning system.
- `DOWNSTREAM_EXECUTION_COMPLETE`: implementation/runtime/deploy/device work created by those atoms is complete at the required level.

An atom may be fully C2S-compiled while its reflection or implementation remains explicitly `OPEN / PLANNED / PARTIAL / TOOL_BLOCKED`.

However, when the **user command itself** requires "반영 / 저장반영 / canonical write", task completion remains governed by the intent/execution contract and SHALL NOT be claimed merely because C2S compilation closed.

`C2S_COMPILE_CLOSED != USER REQUEST COMPLETE`.
`C2S_COMPILE_CLOSED != REFLECTION_COMPLETE`.
`REFLECTION_COMPLETE != DOWNSTREAM_EXECUTION_COMPLETE`.

## 8. Coverage Closure — HARD LOCK

Within the actually recovered source scope, system compilation is not complete while any material atom is unmapped.

Required metrics:
- recovered source scope;
- material atom count;
- mapped material atom count;
- unmapped material atom count;
- silent-loss count;
- unresolved conflict/open count;
- inaccessible-source limitation.

For claimed compile completion:
`UNMAPPED_MATERIAL = 0`
and
`SILENT_LOSS = 0`.

This does **not** authorize claiming zero omission for inaccessible sources. Those remain `UNVERIFIED_SOURCE_COVERAGE`.

Reference validator:
`python ENFORCEMENT/conversation_coverage_validator.py <coverage-ledger.json>`.

## 9. Reverse Reconstruction Test — HARD LOCK

A compiled TAKY state must be able to reconstruct, without inventing:
- the user's actual primary intent;
- major constraints;
- latest material corrections;
- why important decisions changed;
- unresolved/open/conflict items;
- preserved frontier alternatives;
- the current owner/destination of each material decision.

If an independent reconstruction from current system records would materially distort the user's intent, the compile is not complete even if all files parse.

`STRUCTURAL PASS != SEMANTIC RECONSTRUCTION PASS`

## 10. Skeleton-to-Flesh Growth Map

System-building conversations often create a good skeleton before the detailed operating body exists. TAKY SHALL make missing flesh visible instead of silently treating the skeleton as complete.

For each material capability/domain, track as applicable:
- `SKELETON` — concept/role exists;
- `PARTIAL` — some rules/data/implementation exist;
- `OPERATIONAL` — usable in representative work;
- `MATURE` — repeated evidence and stable operating patterns;
- `FRONTIER` — deliberate next improvement/experiment.

Also track missing dimensions:
- detail/rule depth;
- source/evidence;
- exceptions;
- data schema;
- implementation;
- runtime/tool linkage;
- test/regression;
- outcome feedback;
- ownership/approval.

The next conversation/research/build step SHOULD preferentially fill the highest-value missing dimension rather than merely restating the existing skeleton.

## 11. Incremental compile + periodic reconstruction

Default:
- each material conversation -> incremental compile/delta;
- major concept correction -> domain reconstruction;
- large architecture change, repeated drift, or explicit request -> full available-source reconstruction.

Incremental compilation SHALL NOT be assumed sufficient forever. Periodic reverse audit compares current TAKY against recoverable original sources and restores missing, wrongly held, wrongly rejected or falsely converged items.

## 12. Growth, not archival accumulation

Preservation alone is insufficient. Compiled knowledge SHALL support growth:
- recurring cases -> pattern candidate;
- pattern + evidence -> strategy/frontier candidate;
- tested improvement -> current-best candidate;
- failures -> new exploration strategy / guardrail;
- successful exceptions -> expanded search space;
- external cases -> localized experiment, not direct authority.

Conversation compilation therefore feeds both:
1. continuity/traceability;
2. capability evolution.

## 13. User-facing simplicity

Internal atomic tracking SHALL NOT force the user to manage registries manually.

The user may speak naturally. TAKY owns:
- extraction;
- classification;
- linkage;
- impact routing;
- coverage accounting;
- reconstruction checks.

Ask the user only when a real semantic ambiguity materially changes the system and cannot be responsibly resolved from available context.

## 14. Claim boundaries

`ATOM EXTRACTED != CANONICALIZED`
`CANONICALIZED != IMPLEMENTED`
`IMPLEMENTED != VERIFIED`
`COVERAGE PASS != INACCESSIBLE SOURCE RECOVERED`
`SUMMARY PRESENT != WHY PRESERVED`
`RAW PRESERVED != SYSTEM REFLECTED`
`SYSTEM REFLECTED != GROWTH MAP COMPLETE`


## 14.1 C2S closure boundary — HARD LOCK

C2S closure is a knowledge-compilation state, not an implementation, runtime, deployment or device-verification state.

C2S SHALL be judged only on recovered-scope knowledge transformation and traceability:
- evidence preserved or explicitly unavailable;
- material atoms extracted;
- corrections/dependencies/WHY linked;
- each material atom dispositioned and mapped to an owner/destination;
- unresolved OPEN/CONFLICT/FRONTIER items explicitly retained;
- `UNMAPPED_MATERIAL = 0`;
- `SILENT_LOSS = 0`;
- `FALSE_CONVERGENCE = 0` when measured;
- reverse reconstruction passes for the declared recovered scope.

The following are NOT C2S closure requirements:
- code implementation;
- CI execution;
- browser/runtime QA;
- deployment or production provenance;
- physical-device verification;
- external service connection;
- production data migration.

Those belong to downstream execution/verification tracks and may remain OPEN while C2S is CLOSED.

State axes SHALL remain independent:

`C2S_CLOSED != REFLECTION_COMPLETE != IMPLEMENTED != CI_VERIFIED != RUNTIME_VERIFIED != DEPLOYED != DEVICE_VERIFIED`.

A review/result artifact may create downstream implementation or verification actions, but those actions MUST NOT be reclassified as unresolved C2S coverage merely because execution is still pending.

If every material review-result item has a valid disposition, owner/destination, utilization route and next action or terminal reason, C2S may close while the downstream action remains `OPEN / PARTIAL / TOOL_BLOCKED / PLANNED`.

Do not use deployment, runtime or device status as a reason to reopen C2S unless new evidence shows that an atom was omitted, falsely converged, wrongly dispositioned, or mapped to the wrong owner/destination.

## 14.2 Evidence stream / knowledge projection / execution track — HARD LOCK

To prevent C2S from becoming either a lossy summary or an execution-status tracker, TAKY SHALL keep three conceptual layers separate:

1. **Evidence Stream** — recoverable original/user/source evidence and append-only correction lineage.
2. **Knowledge Projection** — current interpreted atoms, relationships, dispositions, owners and canonical/current-state projections.
3. **Execution Track** — implementation, CI, runtime, deployment, device and external-system realization states.

`EVIDENCE STREAM -> KNOWLEDGE PROJECTION -> OPTIONAL DOWNSTREAM EXECUTION`.

Rules:
- later corrections SHALL supersede/adjust prior meaning without erasing the recoverable prior evidence;
- current canonical/project state SHOULD be treated as a projection of evidence + accepted atom relationships, not as a replacement for source history;
- downstream execution state MAY be referenced from an atom but SHALL NOT determine C2S closure;
- execution evidence that reveals a misunderstood/omitted requirement MAY feed back as new EVIDENCE/CORRECTION/LESSON atoms and reopen only the affected C2S scope;
- a C2S ledger SHOULD record downstream state only as a pointer/status, never as a closure prerequisite.

This separation follows TAKY's own source/system distinction and keeps provenance, current knowledge and realization truth independently inspectable.

## 15. Runtime activation — CONDITIONAL HARD GATE

Runtime/command activation is specialized by `OS/C2S_RUNTIME_ACTIVATION.md`.

C2S is required for material conversation-derived durable system/canonical changes, not for every ordinary conversation.

A continuation command inherits the active contract:
- if a C2S compile/write is in progress, continuation keeps C2S active;
- if no C2S-triggering scope exists, continuation does not create one.

RAW transcript preservation does not canonicalize every utterance. Conversation-end handling may preserve unresolved atoms without promoting them.

For TAKY-controlled repository runtimes, the executable composition bridge is:
`ENFORCEMENT/c2s_preflight_bridge.py`.

`C2S REQUIRED + COVERAGE RECORD MISSING/FAIL = BRIDGE NOT PASS`.
`REPOSITORY BRIDGE PASS != HOSTED CHATGPT AUTO-INVOCATION VERIFIED`.


## 16. Direct Drive intake / external synthesis boundary

Current default durable intake is governed by `OS/DRIVE_C2S_DIRECT.md`.

`CHAT/WORK RESULT -> DRIVE DURABLE SOURCE -> DIRECT READ -> C2S`.

NotebookLM is not required and is excluded from the active default path.

External/derived synthesis of any kind enters C2S as `REFERENCE_ONLY / EVIDENCE_ASSIST` unless independently backed by primary/current user evidence. Before a derived candidate changes canonical TAKY:
1. identify its original/current source pointer;
2. verify actor and decision context;
3. check later user correction/supersession;
4. classify atom/disposition;
5. include it in declared coverage;
6. pass applicable impact/coverage/reconstruction gates.

If original/current evidence cannot be confirmed, keep the candidate `OPEN / HOLD / UNVERIFIED`.

## 16.1 Review/result artifacts are first-class C2S inputs — HARD LOCK

A material review, audit, comparison, analysis, research synthesis, validation report, retrospective, or Work result is itself a system-building result artifact.

`SOURCE REVIEWED -> REVIEW RESULT CREATED -> REVIEW RESULT C2S COMPILED -> UTILIZATION ROUTED`.

TAKY SHALL NOT stop at "review document saved" when the result contains material:
- requirements/corrections;
- discovered gaps;
- implementation candidates;
- rejections/holds;
- evidence corrections;
- new owner/destination assignments;
- reusable strategies/assets;
- unresolved coverage.

Every material review-result item MUST receive:
- stable result-item id;
- source artifact pointer;
- authority/source class;
- disposition;
- owner/destination;
- utilization_state;
- action_ref;
- next_action or explicit terminal reason.

Allowed utilization states include:
`APPLIED_CANONICAL / APPLIED_RUNTIME / IMPLEMENTED_MINIMUM / PARTIAL / PLANNED / HOLD / REJECTED / SUPERSEDED / OPEN`.

`RESULT RECORDED != RESULT UTILIZED`.
`REVIEW SAVED != C2S CLOSED`.
`REVIEW RESULT WITH MATERIAL ITEMS + NO UTILIZATION ROUTE = SILENT LOSS CANDIDATE`.

If a review result is derived from secondary analysis, it remains subordinate to primary/current evidence for authority, but its discovered gaps/actions still require explicit routing rather than disappearance.

## 17. Incremental continuity / context economy

C2S preserves material conversational totality but SHALL NOT require all historical atoms to be loaded into every active turn.

Runtime selection/recovery is governed by TKY-CONTINUITY-001:
- ordinary continuation stays in the smallest sufficient working set;
- new-chat resume loads canonical state/owners/open deltas before historical recovery;
- Drive/raw-source escalation is targeted;
- conversation end persists material deltas and then releases unnecessary history;
- full global reconstruction is not the default prerequisite for ordinary canonical work.

`LOSSLESS PERSISTENCE != MAXIMUM ACTIVE CONTEXT`

END
