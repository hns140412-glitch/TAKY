# TAKY 2.0 — CURRENT / CANDIDATE POINTER

Status: LOCAL POINTER / GOOGLE DRIVE IS OPERATIONAL SOURCE
Updated: 2026-10-06 final integration reconciliation

## Mandatory Drive startup set

1. [START HERE] TAKY_2.0_NEW_CHAT_START_AND_WORKING_PREMISE
   - document_id: 11BG91-phb11WmmIHoF6rS2TfWFK6yuJJEszFTsQ7B9M
2. [CANONICAL] TAKY_2.0_UNIFIED_STANDARDS_AND_RULES
   - document_id: 1YWeGE6L1ya9cIbKDqE-IzUTBNwSZFO6iPDbPwXXYpqc
3. TAKY_2.0_SYSTEMWIDE_LOGIC_RECONCILIATION_V2_CANONICAL_20261006
   - document_id: 1FodnFDgmNr0ZHFFl_zw1mUonpPBj7T9B6O-hauYHhYE
4. [CURRENT] TAKY_2.0_CURRENT_CANDIDATE_PROGRESS
   - document_id: 1Cb_nJ55KyKui1sAoc_yOgkTsQ-7vVNqM6Hr19LoNd1c

Implementation-reconciliation candidate:
5. [CANONICAL] TAKY_2.0_SYSTEMWIDE_LOGIC_RECONCILIATION_V3_FINAL_INTEGRATED_20261006
   - document_id: 1FJkxaNOn_i9hEnS2UQzPFjbA7983ieXpdE7kPiMLj5U

AI/mining/index/learning only:
6. [CANDIDATE] TAKY_AI_MINING_INDEX_LEARNING_FINAL_INTEGRATION_20261006
   - document_id: 1f1K3pQ81uUHbOnVab37blX0sczbsqtaMsDZvdnGEI58
7. local AI_CURRENT_QUEST_RESUME
8. local AI_OPEN_QUEST_CURRENT
9. only task-matched Q3/Q4/Q5 evidence

Disposition history (not routine startup):
- [HISTORY] TAKY_2.0_CURRENT_DISPOSITION_RECEIPTS
  - document_id: 1X3gn2wK2Qb0hyOqEO-SLUYypvzMh2FEjSAlAxe-5iQ4

## Startup rule

- Read the mandatory Drive set before implementation/mutation.
- Check PREMISE / CANONICAL / CURRENT / OPEN-ONLY.
- Drive readback failure => inspection/recovery only; no mutation from memory.
- CLOSED/PROMOTED items removed from CURRENT must not be silently reopened.
- CURRENT contains live work only.
- Candidate findings are not Canonical until promotion requirements pass.
- Do not reread all AI sources/history by default.

## Canonical Design vs implementation candidate

Already Canonical Design Authority:
- NAVIGATOR / GUARDIAN / DRIVER+SAVEY_AI_ECONOMY / SCOUT
- ROLE != AGENT
- 5 HARD GATE only
- SAVEY_AI_ECONOMY != SAVEY_FAMILY_FINANCE

V3 remains Candidate for promotion, but the runtime implementation reconciliation is locally implemented for:
- machine-readable control-role/runtime schema + Control Incident Trace
- role_registry / default_actor_bindings separation
- semantic_owner first-class action -> receipt -> evidence/completion -> DONE binding
- reusable task-fit worker-role schema
- one shared SAVEY_AI_ECONOMY evaluator consumed by Driver + COST
- whole-system owner registry with explicit OWNER_GAP preservation
- startup readback receipt / mutation block
- technical delivery vs explicit USER confirmation state split

The previous second V3 draft is SUPERSEDED-DRAFT in Drive ARCHIVE_REFERENCE.
There is one active V3 candidate pointer now.

## Active OPEN categories

Locally IMPLEMENTED / awaiting final independent closure evidence:
- CUR-001 CONTROL ROLE RUNTIME SCHEMA
- CUR-002 SEMANTIC OWNER FIRST-CLASS BINDING
- CUR-003 WORKER ROLE CONTRACTS
- CUR-004 SAVEY_AI_ECONOMY SHARED POLICY
- CUR-008 NEW-CHAT STARTUP CONTEXT GATE

Still OPEN:
- CUR-005 WHOLE-SYSTEM OWNER MAP COMPLETENESS — registry implemented; unresolved domains remain explicit OWNER_GAP, not guessed
- CUR-006 REAL HNS FIRST-AUTH SESSION / DEVICE E2E — account-binding implementation CLOSED; actual login/use runtime E2E only
- CUR-007 CROSS-CHAT / SOURCE COMPLETENESS AUDIT — Delta only
- CUR-009 SYSTEMWIDE V3 IMPLEMENTATION RECONCILIATION — implementation delta complete locally; promotion/Canonical decision still OPEN

Do not treat this local pointer as a substitute for Drive readback.

## MASTER CLOSURE POINTER — CLOSED

MASTER semantic reconciliation is CLOSED.

Authority snapshot:
- branch: `taky/master-logic-20261006-claude`
- semantic commit: `1d0afb9b6b1ed8a04cbe44478f6d56bc29d01fce`
- closure receipt commit: `ca33ec956bbc26380af7e85178eae194379b9724`
- Claude Code final read-only decision: `CLOSE_WITH_NOTE`
- blocking findings: `NONE`
- master_logic_basis tests: `60/60 PASS`

This supersedes any earlier local pointer that described MASTER as `VERIFYING` or `CODEX_REVERIFY_PENDING`.
Codex is optional defense-in-depth after closure, not a blocker.

MASTER semantic scope is not an Active OPEN category anymore.
Keep V2 §8 runtime implementation work in CUR-001/002/003/004/005/008/009 as applicable without reopening MASTER meaning.

Implementation priority after this pointer:
actual usable webapp result, measured as
`SCREEN -> INTERACTION -> DATA/STATE -> END-TO-END RESULT -> EVIDENCE`.

No merge/push/deploy/Netlify publish is authorized by this pointer.

## Local runtime reconciliation checkpoint — 2026-10-07

Implemented in TAKY2 runtime:
- formal structure name: ROLE_BASED_COLLABORATIVE_EXECUTION_STRUCTURE
- Shepherding / Border Collie language retained as explanatory metaphor only
- ROLE != AGENT enforced by role_registry + default_actor_bindings
- semantic owner registry + OWNER_GAP fail-closed behavior
- task-fit Worker Role profiles
- shared SAVEY_AI_ECONOMY evaluator; Necessity remains inside COST/Driver, never a sixth Gate
- Control Incident Trace with cause/evidence/control-role/decision/route/result/remaining-unknown
- startup readback receipt validator/bridge
- technical delivery != USER confirmation
- verifier/reviewer role IDs separated from default actor IDs

Runtime authority rebind:
- old digest: e92831fc4e23ff21c979
- new digest: 85474e09166708960f60
- signed runtime: v9 -> staged v10 -> rebound v11
- KEY_AMEND: false
- event: chat:user:continue:2026-10-07

Latest local verification before external reattack:
- full TAKY2: 127 passed + 51 subtests
- py_compile: PASS
- git diff --check: PASS
- post-rebind state/bridge: 53 passed + 34 subtests
- worker blocked-path negative test added after self-reattack

No push / merge / deploy / Netlify publish performed.

## Local reconciliation delta — 2026-10-11

Supersedes the digest/runtime figures above (85474…/v11 are historical).
- authority digest: e48ca039a387299fb3ea / runtime v178
- TAKY2: 213 passed + 54 subtests; ENFORCEMENT: 120 passed + 3 subtests
- Codex FINAL MICRO RECHECK: VERDICT PASS / FINDINGS NONE
  receipt pf:taky2-v3-final-micro-codex-20261011:3dad5028561f0e7d
  result TAKY2/TAKY2_V3_FINAL_MICRO_CODEX_RESULT_20261011.json
- subprocess_runner UTF-8 decoding fix (cp949 locale dropped CLI evidence) + regression test; internal verification only
- V3 PROMOTION: NOT PROMOTED — awaiting USER decision
- Drive CURRENT §22 records this delta; header figures refreshed; duplicate 15/16 labels renumbered 18-21
- Known gap: ENFORCEMENT user_authorized_development has no live caller
- No push / merge / deploy / Netlify publish.
- Codex UTF-8 CAPTURE RECHECK: VERDICT PASS / FINDINGS NONE
  receipt pf:taky2-v3-utf8-capture-codex-20261011:f3c55cb07097b782
  result TAKY2/TAKY2_V3_UTF8_CAPTURE_CODEX_RESULT_20261011.json (full stderr captured post-fix)
- all V3 implementation deltas now have independent PASS; promotion still awaits explicit USER decision
- V3 PROMOTED by explicit USER decision 2026-10-11 (Drive CURRENT §23; V3 doc PROMOTION RECEIPT header)
  CUR-001/002/003/004/008/009 = PROMOTED, pending HISTORY receipt transfer before Active removal
- ENFORCEMENT authorized-development budget now bound to trusted USER authorization
  (scope=external_development_calls in signed TAKY2 authority); none registered => OFF (commit 956e8f10)
- pushed: origin/taky-2.0-orchestrator-2026-10-05 = 968a9940; later local commits not pushed
- HISTORY disposition receipts written (Drive [HISTORY] TAKY_2.0_CURRENT_DISPOSITION_RECEIPTS, 2026-10-11 V3 PROMOTION);
  CUR-001/002/003/004/008/009 removed from Drive Active CURRENT
- Active CURRENT now: CUR-005 / CUR-006 / CUR-007 / CUR-010 / CUR-011
- pending: V3 Drive title rename [CANDIDATE] -> [CANONICAL]; fresh startup readback receipt next session
- V3 Drive title renamed [CANDIDATE] -> [CANONICAL] (START HERE / CURRENT references updated); Drive readback verified

## Startup readback + push — 2026-10-12

- PUSH (USER-approved, work branches only, no force): ORCH `968a9940..534d72aa`; TAKY `8a6806b3..130e20d9`. Merge / deploy: NOT DONE.
- Drive consistency: CURRENT header refreshed + §24 added; START HERE gained a V3 PROMOTION NOTICE superseding stale "V3 remains Candidate" lines (§13/§14/§17); Canonical §13 operational pointer now names V3 as [CANONICAL] (pointer only, V2 design meaning unchanged).
- Startup readback receipt `startup:63e2b948f8040e8845df` recorded in the signed runtime (v182 -> v183, authority digest e48ca039a387299fb3ea, verified_by CLAUDE_CODE_DRIVE_READBACK_20261012). All four documents were read in full via the Drive connector. Revision = Drive modifiedTime:
  - START_HERE `modified:2026-10-12T05:40:01.674Z`
  - CANONICAL `modified:2026-10-12T05:40:21.655Z`
  - SYSTEMWIDE_V2 `modified:2026-10-06T03:30:08.078Z`
  - CURRENT `modified:2026-10-12T05:39:06.015Z`
  Any later edit to these documents makes this receipt stale; record a fresh one then.
- ORCH index: four archived leftovers unstaged from a parallel session's staging set (files kept on disk).
