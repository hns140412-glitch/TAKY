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
-> APPLY AUTHORIZED REFLECTION
-> IMPACT CHECK
-> COVERAGE CLOSURE
-> REVERSE RECONSTRUCTION
-> RECORD DELTA`

Do not jump directly from chat to a rewritten MASTER.

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

END
