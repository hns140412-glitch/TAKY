# TAKY CONVERSATION CONTEXT LEDGER PROTOCOL

Status: REV_00 / CANONICAL CROSS-SYSTEM CONTINUITY PROTOCOL
Date: 2026-09-12
Authority: TAKY / GRAND MASTER

## 0. Purpose
Prevent context loss caused by repeated summarization. This protocol preserves recoverable conversational meaning, correction history, decision evolution, evidence links and unresolved work so a new conversation can resume from traceable context rather than from a lossy summary.

`SUMMARY ≠ CONTEXT PRESERVATION`
`HANDOFF ≠ ORIGINAL EVIDENCE`
`CONCLUSION WITHOUT WHY ≠ RECOVERABLE DECISION`

Absolute zero omission cannot be claimed for inaccessible sources. Inaccessible material remains `UNVERIFIED_SOURCE_COVERAGE`.

## 1. Continuity chain

`ORIGINAL CONVERSATION / ATTACHMENT / SOURCE EVIDENCE → CONVERSATION CONTEXT LEDGER → IDEA / DECISION TRACE → CANONICAL OWNER → IMPLEMENTATION EVIDENCE → HANDOFF → NEW-CONVERSATION RECOVERY`

The Ledger is an index and meaning-link layer over evidence. It does not replace the original evidence and does not become authority merely by recording it.

## 2. Preserve the formation of a decision

For material context, preserve the applicable chain:
`USER INTENT → USER STATEMENT / SOURCE → ASSISTANT PROPOSAL → USER CORRECTION / REJECTION / REFINEMENT → WHY IT CHANGED → DECISION → STATUS / DISPOSITION → OWNER → IMPLEMENTATION → VALIDATION → NEXT UNRESOLVED GATE`

Do not retain only the final sentence when earlier turns materially explain scope, meaning, rejection, correction or exceptions.

## 3. Context Event

A material Context Event should retain, when available:
- stable event id
- conversation/date/sequence pointer
- related project/domain/app
- user intent
- relevant original-turn/source pointers
- conversation flow in order
- corrections/refinements and their reason
- decision or unresolved question
- disposition: `PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT / SUPERSEDED`
- canonical owner / reflection status
- implementation evidence/status
- validation status
- supersedes / superseded-by links
- related Context Event ids
- next unresolved gate
- source coverage limitation

This structure is not permission to paraphrase away the original evidence. Original accessible evidence remains recoverable by pointer or preservation record.

## 4. No deletion by summarization

A Handoff or compact context may be generated for speed, but omission from that compact representation SHALL NOT mean deletion, rejection or supersession.

Material ideas/decisions disappear from active routing only through an explicit disposition or ownership transfer, not because a later summary omitted them.

`NOT IN SUMMARY ≠ REJECTED`
`NOT IN HANDOFF ≠ SUPERSEDED`

## 5. New-conversation resume

`/재개`, `최신 타키 기준으로 재개`, or equivalent continuation for a context-bearing project SHALL recover more than the latest summary.

Minimum recovery when material:
1. latest canonical TAKY and applicable owner rules
2. latest Handoff/current-truth pointer
3. unresolved/open Context Events relevant to the project
4. linked material Idea/Decision traces
5. actual current implementation/runtime/test evidence
6. corrections/supersession links that change interpretation
7. first unresolved gate

If a compact Handoff conflicts with recoverable original/context evidence, do not silently trust the compact Handoff. Reconcile against authority and evidence.

## 6. Raw conversation preservation relationship

`/대화전체보존` remains the evidence-preservation path for materially accessible USER↔Assistant conversation in original order.

The Context Ledger complements it:
- Conversation Evidence = what was actually said/shown and in what order.
- Context Ledger = why it mattered, what changed, and what it links to.
- Decision/Idea Trace = lifecycle and disposition.
- Canonical = current approved authority.
- Handoff = efficient recovery pointer/state, not replacement for the above.

## 7. Attachments / URLs / external evidence

When an attachment, image, URL, file, GitHub commit, Notion record, Drive file or runtime result materially changes a decision, preserve its relationship to the relevant Context Event. Do not merely record that an attachment existed.

Where exact content is unavailable later, preserve the pointer and mark coverage limits rather than reconstructing from guesswork.

## 8. Corrections and supersession

User corrections are first-class context. Preserve both the earlier proposal/decision and the later correction when the transition explains current meaning.

`SUPERSEDED` does not mean erased. It means retained as lineage with a forward link to the replacement.

A rejected idea may later be reconsidered only through a new Context Event that records why conditions changed.

## 9. Implementation truth separation

Context/decision state and implementation state remain separate.

Examples:
- `ADOPTED / IMPLEMENTATION_PENDING`
- `IMPLEMENTED_BOUNDED`
- `VERIFIED`
- `DEVICE_UNVERIFIED`
- `GAP`

`DECIDED ≠ IMPLEMENTED`
`IMPLEMENTED ≠ VERIFIED`
`QUEUED ≠ IMPLEMENTED`

## 10. Anti-fragmentation gate

Before inventing a new rule, feature or architecture for an existing project:
1. search applicable Canonical owners
2. recover relevant unresolved Context Events and decision traces
3. inspect related implementation evidence
4. determine whether the apparent new requirement is actually a lost/omitted prior requirement
5. only then classify as new / recovered / adjusted / conflicting

Repeated re-invention caused by summary omission is a continuity failure.

## 11. Storage principle

Do not force one giant monolithic file. The protocol may be implemented as append-only/event files plus indexes, provided links are stable and recoverable.

Recommended logical layers:
- `CONVERSATION_EVIDENCE/`
- `CONTEXT_LEDGER/`
- `DECISION_TRACE/` or existing Decision-Coverage mechanism
- canonical owner files
- `HISTORY/`
- Handoff/current-truth projections

Exact physical folder implementation may be adjusted by Work OS without weakening this protocol.

## 12. Validation

A continuity PASS requires more than a generated summary.

Check:
- material user corrections retained
- unresolved items retained
- superseded lineage linked
- source/attachment relationship retained
- canonical reflection status distinguishable
- implementation truth distinguishable
- next unresolved gate recoverable
- inaccessible coverage marked honestly

`SUMMARY CREATED ≠ CONTINUITY PASS`

## 13. Current bootstrap event — 2026-09-12

Recovered intent from the current conversation:
- User explicitly rejected lossy summary as the desired continuity mechanism because repeated summarization had produced major omissions and fragmentation.
- Desired target is context-dependent recording: preserve how discussion, corrections, evidence and decisions evolved.
- User approved proceeding with this Conversation Context Ledger approach because the current conversation appeared near its practical context limit.

This bootstrap event establishes the protocol; it does not claim historical conversations have already been fully reconstructed into Ledger events. Historical backfill remains a separate recovery task and inaccessible raw history remains `UNVERIFIED_SOURCE_COVERAGE`.

END