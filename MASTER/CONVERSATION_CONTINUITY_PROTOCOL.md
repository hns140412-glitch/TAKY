# TAKY CONVERSATION CONTINUITY / CONTEXT ECONOMY PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-CONTINUITY-001
Role: Preserve the total meaning of conversation across chats without forcing the full historical corpus into every turn, and prevent unnecessary user re-asking.
Authority: TAKY / GRAND MASTER > this protocol > lower-layer project/domain continuity specializations.
Related: `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md`, `MASTER/NOTEBOOKLM_RECOVERY_PROTOCOL.md`, `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`, `STATE.md`.

## 0. Core doctrine — HARD LOCK

> **TOTALITY STORED, CONTEXT SELECTIVE.**
> 전체 맥락은 보존하고, 실행 컨텍스트에는 필요한 만큼만 불러온다.

`TOTAL CONVERSATION != TOTAL CONTEXT LOADED EVERY TURN`
`LIGHTWEIGHT != LOSSY`
`NO RE-ASK != ALWAYS FULL-SCAN`
`NOTEBOOKLM AVAILABLE != NOTEBOOKLM ALWAYS-ON`

The system SHALL preserve material conversational totality through raw evidence, C2S atoms, state/history, source registries and indexed recovery surfaces while keeping ordinary execution on the smallest sufficient working set.

## 1. Four-layer memory model

### L0 — HOT / ACTIVE WORKING SET
Use:
- current conversation;
- active task contract;
- immediately relevant confirmed constraints;
- current unresolved decision.

Default for ordinary same-chat continuation.

### L1 — WARM / CANONICAL CONTINUITY
Use:
- `STATE.md`;
- applicable canonical owner(s);
- relevant C2S/history/open items;
- current project/domain state;
- verified Handoff only when applicable.

Default for new-chat resume and durable work.

### L2 — INDEXED / TARGETED RECOVERY
Use:
- NotebookLM topic/project notebook or prepared source pack;
- Drive Source Registry;
- targeted historical search/index;
- derived analysis as REFERENCE_ONLY.

Use only when L0/L1 does not safely resolve a material historical/context question.

### L3 — COLD / RAW SOURCE VERIFICATION
Use:
- original/raw conversation transcript;
- original attachment;
- saved evidence/source file;
- historical canonical revision.

Use when exact wording, correction lineage, canonical backfill, contradiction resolution or high-impact factual verification requires original evidence.

### L4 — FULL FORENSIC / GLOBAL RECONSTRUCTION
Use:
- all materially accessible source families;
- cross-conversation recurrence scan;
- full reverse reconstruction.

Default state: OFF.
Activation: explicit user request for full/global/all-conversation reconstruction or another separately authorized full-forensic task.

## 2. Progressive retrieval ladder — HARD LOCK

Default execution:
`L0 -> L1 -> L2 -> L3` only as necessary.

Do not jump to a heavier level merely because it exists.

Escalate only when the unresolved context can materially change:
- the requested result;
- a governing requirement;
- user intent;
- latest correction;
- canonical write;
- safety/authority;
- irreversible/high-impact action.

Stop at the lowest level that gives a sufficiently reliable answer/action.

`MORE HISTORY != BETTER CONTEXT`
`MINIMUM SUFFICIENT CONTEXT > MAXIMUM LOADED CONTEXT`

## 3. ASK LAST — HARD LOCK

TAKY SHALL NOT ask the user to repeat or re-explain a materially recoverable prior detail while a reasonable system-side recovery path remains.

Before re-asking, attempt the lowest-cost applicable sequence:
1. current conversation / active contract;
2. L1 canonical continuity;
3. targeted L2 NotebookLM/index search when relevant;
4. targeted L3 raw-source verification when needed.

Ask only when:
- the required source is genuinely unavailable;
- multiple materially different interpretations remain after recovery;
- the missing choice is subjective/new rather than historical;
- human authority/approval is required.

If asking is necessary, ask only for the smallest unresolved item, not the whole context again.

`RECOVERABLE CONTEXT + USER RE-ASK = FAIL`

## 4. FULL SCAN LAST — HARD LOCK

L4 full forensic/global reconstruction SHALL NOT run:
- on every new chat;
- on every `ㄱ`;
- at every conversation end;
- because a NotebookLM notebook exists;
- because a minor historical detail is uncertain.

L4 is reserved for explicit full/global historical audit or an equivalently authorized reconstruction task.

Routine gaps use targeted L2/L3 retrieval.

`FULL CORPUS PRESERVED != FULL CORPUS RELOADED`

## 5. New-chat resume rule

For a new conversation using TAKY:
1. identify the active project/domain;
2. if a project context manifest exists, load it before project implementation/validation;
3. load L1 state/canonical owners required by that manifest;
4. recover the active task/project and unresolved material deltas;
5. validate required-context coverage; if required context is missing, recover it before executing dependent work;
6. continue without re-asking settled details;
7. use L2 NotebookLM/Drive and L3 raw verification only for material gaps/conflicts identified by the manifest or current task.

A Handoff summary alone is insufficient when canonical/state pointers are available, but a full historical audit is also unnecessary.

Default:
`PROJECT -> CONTEXT MANIFEST -> STATE/APPLICABLE OWNERS -> ACTIVE/OPEN DELTAS -> CONTEXT GATE -> CONTINUE`.

`RECOVERABLE REQUIRED PROJECT CONTEXT MISSING + EXECUTION CONTINUES = FAIL`.

## 6. Same-chat continuation rule

For `ㄱ / 계속 / 진행`:
- preserve the active contract;
- remain at L0 unless a material dependency requires escalation;
- do not rehydrate unrelated historical context;
- do not run NotebookLM merely because continuation occurs.

## 7. Conversation-end rule

At conversation end:
- persist material delta through C2S/state/history as applicable;
- preserve OPEN/FRONTIER/CONFLICT/corrections;
- update pointers needed for resume;
- release unnecessary historical context.

Do **not** perform full NotebookLM/global rescan by default.

This creates a cheap incremental continuity loop:
`TALK -> MATERIAL DELTA -> C2S/STATE -> RELEASE CONTEXT`.

## 8. NotebookLM role in lightweight continuity

NotebookLM is a **targeted cold-memory index/recovery accelerator**, not the always-loaded memory layer.

Use NotebookLM when:
- the user asks about prior discussions not resolved by L1;
- multiple conversations on the same topic must be compared;
- correction history or omitted details need recovery;
- a domain/project notebook can answer without loading global history.

Do not use NotebookLM when:
- current conversation already contains the answer;
- STATE/canonical owner resolves the task;
- the question is unrelated to historical context.

NotebookLM output remains governed by TKY-NBLM-001.

## 9. Notebook partition / global index strategy

Avoid one giant notebook as the only recovery surface.

Preferred:
- TAKY Core / Governance;
- Work OS / Notion;
- Ready & Set;
- Architecture;
- project-specific notebooks as material;
- other domain notebooks when justified.

Maintain a lightweight global Source Registry / Topic Map containing:
- source ID;
- date/range;
- topic/project/domain;
- source class;
- notebook/source-pack destination;
- latest correction/status pointers.

For cross-domain questions, use the global index to select the smallest relevant notebook/source set rather than querying every notebook.

## 10. Materiality filter

Not every conversational sentence becomes active context.

Persist when it materially affects:
- requirement;
- decision;
- correction;
- constraint;
- strategy;
- open issue;
- source/evidence;
- future execution;
- user preference specific to the work;
- authority/approval;
- failure/lesson.

Transient pleasantries, redundant acknowledgements and non-material repetition need not enter the durable working set.

`NO SILENT LOSS OF MATERIAL CONTENT != STORE EVERY TOKEN AS ACTIVE MEMORY`

## 11. Confidence / stop rule

Stop retrieval when:
- the intended action can be performed without material ambiguity;
- the latest correction is known;
- required authority/source class is sufficient;
- additional history is unlikely to change the result materially.

Escalate if:
- a contradiction changes the action;
- user correction lineage is unclear;
- canonical change would rely on uncertain history;
- exact source evidence is required.

Do not chase perfect historical completeness for an ordinary task when the remaining gap is non-material. Record the gap if relevant.

## 12. Canonical-write rule

For conversation-derived canonical change:
- L1 canonical context is mandatory;
- current conversation evidence may be sufficient for new current decisions;
- NotebookLM-derived historical claims require L3 raw recheck before promotion;
- C2S coverage applies to the declared material source scope;
- full account-history scan is not required unless the user's requested scope is global/full.

`CANONICAL WRITE != GLOBAL HISTORY SCAN BY DEFAULT`

## 13. Lightweight completion metrics

A continuity episode SHOULD be judged by:
- user did not have to repeat recoverable settled context;
- only materially relevant sources were loaded;
- latest corrections survived;
- unresolved items stayed explicit;
- no silent loss in the declared material scope;
- no unnecessary full-history scan;
- resume can continue from L1 without replaying the entire conversation.

The target is **high continuity / low context cost**.

## 14. Failure conditions

Fail or correct course when:
- user is asked to repeat recoverable context;
- L4 was used without explicit full/global reconstruction scope;
- NotebookLM was invoked despite L0/L1 being sufficient;
- a summary replaced raw evidence for a material disputed decision;
- old context remained loaded after it was safely persisted and no longer needed;
- cross-project context contaminated the active task;
- lack of full historical certainty was incorrectly converted into a blocked ordinary task.

## 15. Runtime claim boundary

This protocol defines canonical selection/recovery behavior and repository-testable continuity records.

It does not prove that hosted ChatGPT automatically reads repository state or calls NotebookLM on every new chat. Where platform auto-invocation is unavailable, an explicit TAKY invocation remains the reliable bootstrap.

END
