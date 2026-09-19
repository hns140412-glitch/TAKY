# TAKY DIRECT DRIVE → C2S PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL SPECIALIZATION
Rule ID: TKY-DRIVEC2S-001
Role: Make Google Drive the direct durable interchange surface for ChatGPT/Work outputs and route them into TAKY C2S without NotebookLM dependency.
Authority: TAKY / GRAND MASTER > this protocol > project-specific Drive intake conventions.

## 0. Core model — HARD LOCK

`CHATGPT / WORK RESULT -> GOOGLE DRIVE SOURCE -> TAKY DIRECT READ -> C2S -> OWNER REFLECTION`.

NotebookLM is NOT part of the default or required path.

`DRIVE SAVE != CANONICAL ADOPTION`.
`SOURCE STORED != SOURCE UNDERSTOOD`.
`SOURCE READ != RULE APPLIED`.
`NOTEBOOKLM ABSENT != C2S BLOCKED`.

## 1. /저장반영 command

Natural-language equivalents:
- `/저장반영`
- `결과 저장하고 반영`
- `드라이브 저장 후 타키 반영`
- `이 결과 저장해서 기준에 반영`

Default execution contract:
1. identify the current material result/source payload;
2. determine project/domain destination from active context without asking when recoverable;
3. persist the source/result to governed Google Drive;
4. record stable Drive pointer + source class + timestamp/context;
5. directly read the persisted source from Drive;
6. activate TKY-C2S-001 when the material contains durable rule/decision/correction/strategy/system changes;
7. atomize and map to owner/disposition;
8. route required owner/canonical reflection as a separate reflection state;
9. when the user command requires reflection and write authority exists, perform the authorized owner/canonical write;
10. verify post-write state and record unresolved OPEN/HOLD/CONFLICT separately.

If the material is only a deliverable with no durable rule/system delta, stop after durable Drive save + pointer verification.

## 2. Drive source envelope

Every material direct-C2S intake SHOULD retain:
- intake_id;
- source_title;
- drive_file_id / URL;
- project/domain;
- source_class;
- source_actor when known;
- captured_at / source_date;
- request/context summary;
- latest user correction pointer when material;
- canonical impact: NONE | CANDIDATE | REQUIRED;
- C2S status;
- owner/destination;
- unresolved coverage.

## 3. Default source classes

- CURRENT_CHAT_RESULT
- WORK_RESULT
- USER_ATTACHMENT_DERIVATIVE
- RAW/PRESERVED
- PROJECT_REFERENCE
- DERIVED_ANALYSIS
- EXTERNAL_REFERENCE

Derived analysis is never allowed to outrank available primary/raw/user-confirmed evidence.

## 4. NotebookLM exclusion — HARD LOCK

Current operating policy:
`NOTEBOOKLM DEFAULT ROUTE = OFF`.

TAKY SHALL NOT:
- create NotebookLM-only query packs as a prerequisite for C2S;
- block direct C2S on NotebookLM login/sync/output;
- mark a direct Drive/C2S task PENDING because NotebookLM is unavailable;
- route ordinary continuity through NotebookLM.

NotebookLM-related historical files MAY remain preserved as legacy/reference artifacts. They are not execution prerequisites.

NotebookLM may re-enter only by explicit future user decision that re-enables it for a specific optional use.

## 5. Minimum-click behavior

When Drive write access is available in the active ChatGPT/Work environment, `/저장반영` SHOULD complete the Drive save and direct C2S steps without asking the user to manually move/copy files.

Human interaction is reserved for genuine authority/permission gates, ambiguous project ownership that cannot be recovered, or unavailable account authorization.

## 6. Direct C2S gate

For `canonical_impact=REQUIRED`:
- raw/current user evidence takes priority;
- actor and latest correction must be known or explicitly unresolved;
- every material atom receives disposition and owner;
- C2S compile closure and owner-reflection state must be reported separately;
- if the active user command requires canonical reflection, canonical write must be evidenced before that **task** is called complete;
- coverage within declared scope must close under TKY-C2S-001 independently of downstream implementation/runtime/deployment/device state.

For `canonical_impact=CANDIDATE`, save + atomize + HOLD/OPEN is allowed without forced promotion.

## 7. Claim boundaries

Allowed claims:
- DRIVE_SAVED
- DRIVE_POINTER_VERIFIED
- DIRECT_C2S_INTAKE_READY
- C2S_ATOMIZED
- OWNER_REFLECTED
- CANONICAL_WRITTEN_VERIFIED

Disallowed:
- "반영 완료" when only Drive save happened;
- "C2S 완료" when material atoms remain unmapped;
- "NotebookLM 대기" as a blocker under this protocol.

END
