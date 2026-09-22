# TAKY BETA LOSSLESS / C2S PLAN — 2026-09-22

Status: BETA CANDIDATE / PARALLEL LOSS-PREVENTION TRACK

## 1. Purpose

Prevent structural reform from deleting, flattening, misquoting, recreating or misrouting accumulated meaning.

C2S is used as a migration ledger, not as a summary mechanism.

## 2. Source preservation

Before moving or rewriting material:
- preserve source pointer;
- preserve original wording where material;
- preserve original context;
- preserve date/version;
- preserve latest user correction;
- preserve current owner;
- preserve implementation/evidence state.

## 3. Atom model

Use existing C2S classes:
- REQUIREMENT
- DECISION
- CORRECTION
- STRATEGY
- IDEA
- CONFLICT
- OPEN
- EVIDENCE
- FRONTIER

BETA migration metadata:
- SOURCE
- ORIGINAL_INTENT
- LATEST_CORRECTION
- SEMANTIC_OWNER
- CURRENT_TERM
- LEGACY_TERM
- DISPOSITION
- DESTINATION
- CONSUMER
- CONTRACT
- REALIZATION_STATE
- SUPERSESSION_LINK

## 4. Required disposition

Every material atom receives exactly one current disposition:
- PRESERVE
- ADJUST
- OWNERSHIP_TRANSFER
- SUPERSEDED
- HOLD
- CONFLICT
- REJECT
- EXCLUDE

No unclassified disappearance.

## 5. Forward trace

SOURCE
-> ATOM
-> CORRECTION
-> OWNER
-> DISPOSITION
-> DESTINATION
-> CONTRACT/CONSUMER
-> RESULT

## 6. Reverse trace

NEW STRUCTURE / RULE / CONTRACT
-> ACTIVE OWNER
-> DECISION
-> SOURCE
-> CORRECTION LINEAGE
-> EVIDENCE

A reverse-trace break is not PASS.

## 7. Loss failure classes

- SILENT_LOSS
- SOURCE_ORPHAN
- OWNERLESS_ATOM
- DESTINATION_MISSING
- WRONG_OWNERSHIP_TRANSFER
- SUMMARY_SUBSTITUTION
- UNSOURCED_REWRITE
- LEGACY_ERASURE
- CORRECTION_LOSS
- CONFLICT_FLATTENING
- FALSE_SUPERSESSION
- DUPLICATE_ACTIVE_AUTHORITY
- TERM_DRIFT
- WRONG_REFERENCE
- HISTORY_PROMOTED_TO_CURRENT
- CURRENT_PROMOTED_TO_PERMANENT_OWNER

## 8. Rewrite-time protection loop

Every material structural rewrite runs the following loop:

`SOURCE RECOVERY -> ATOM/CORRECTION RECOVERY -> ORIGINAL INTENT -> CURRENT OWNER -> PROPOSED DELTA -> TARGET OWNER/DESTINATION -> REWRITE -> FORWARD TRACE -> REVERSE TRACE -> BEFORE/AFTER SEMANTIC COMPARE -> REGRESSION CHECK`

Reject or HOLD the rewrite when any of the following occurs:
- original intent cannot be recovered sufficiently;
- a material atom has no destination;
- owner changes without explicit transfer;
- a shorter rewrite drops a constraint or exception;
- a legacy term is removed without compatibility/supersession trace;
- a new elegant structure contradicts a protected decision without new evidence;
- a runtime/reference path changes but dependent consumers are not accounted for;
- a summary substitutes for source evidence.

Protection principle:
`LOSSLESS DOES NOT MEAN KEEP EVERY OLD FILE ACTIVE.`
It means every material meaning has an explainable fate and recoverable lineage.

## 9. Lossless migration rule

Do not delete because:
- a newer document is shorter;
- the item seems duplicated;
- a new architecture has no obvious place;
- the old name is deprecated;
- the current implementation moved;
- a summary omitted it.

First classify and route.

## 10. C2S closure separation

C2S_COMPILE_CLOSED
!= REFLECTION_COMPLETE
!= ARCHITECTURE_REALIGNED
!= IMPLEMENTED
!= CI_VERIFIED
!= RUNTIME_VERIFIED
!= PRE_DEVICE_CANDIDATE
!= DEPLOYED

## 11. BETA lossless acceptance

- SILENT_LOSS = 0
- OWNERLESS_MATERIAL = 0
- UNCLASSIFIED_MATERIAL = 0
- UNEXPLAINED_SUPERSESSION = 0
- WRONG_REFERENCE = 0 for active BETA surfaces
- all material corrections preserved
- all material conflicts either resolved or explicitly open
- forward trace PASS
- reverse trace PASS
- original source remains recoverable


## 12. Pre-device lossless acceptance

Before declaring PRE_DEVICE_CANDIDATE:
- rewritten BETA structure must reverse-trace to source and latest correction;
- all ownership transfers must be explicit;
- all runtime/reference migrations must have consumer impact trace;
- active aliases/supersession rules must be machine-resolvable where material;
- no material requirement may exist only in historical/Handoff text without an active destination or explicit disposition;
- implementation realignment must not introduce semantic ownership drift;
- runtime/browser verification failures must be classified as implementation/runtime defects, not patched by changing protected intent unless new evidence justifies a decision change.

`DEVICE_VERIFIED` remains NOT_RUN in this program.
