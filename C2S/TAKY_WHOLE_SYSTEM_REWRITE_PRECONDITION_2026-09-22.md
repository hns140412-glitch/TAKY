# TAKY WHOLE-SYSTEM REWRITE PRECONDITION — 2026-09-22

Status: CANDIDATE / PRE-REWRITE GATE
Purpose: Prevent whole-system canonical rewrite from being built on broken headers, stale pointers, mixed authority, or runtime reference drift.

## P0 rule

Whole-system rewrite SHALL NOT start from existing document wording as-is.

Required order:
1. REFERENCE FORENSICS
2. HEADER / IDENTITY NORMALIZATION
3. CURRENT vs LEGACY CLASSIFICATION
4. RUNTIME / VALIDATOR PATH ALIGNMENT
5. OWNER / ROLE GRAPH FREEZE
6. CANONICAL REWRITE
7. CONTRACT EXTRACTION
8. IMPLEMENTATION REALIGNMENT

## Pre-rewrite failure classes

- BROKEN_LOCAL_REF
- OWNER_POINTER_MISSING
- FILE_NAME_HEADER_MISMATCH
- CURRENT_HEADER_LEGACY_IDENTITY
- STALE_BOOT_POINTER
- STATE_SNAPSHOT_PROMOTED_TO_CURRENT
- DUPLICATE_ACTIVE_AUTHORITY
- VALIDATOR_STALE_CONTRACT
- RUNTIME_PATH_MISMATCH
- SUPERSEDED_TERM_IN_ACTIVE_SURFACE
- IMPLEMENTATION_HOST_PROMOTED_TO_OWNER

Any P0 unresolved item blocks canonical rewrite completion.

## Rewrite acceptance prerequisites

Before rewriting MASTER/OS canonical surfaces:
- every active local path resolves;
- every active owner pointer resolves to a real canonical/support artifact or explicit external owner;
- file/header revision lineage is explicit;
- legacy names are either migrated or retained only through a declared compatibility alias;
- current runtime state is separated from dated historical snapshots;
- boot order references current owner identities;
- runtime/orchestrator/validator paths consume the same canonical identities;
- ownership hierarchy + interaction graph validator PASS;
- canonical reference/header integrity validator PASS.

## Identity migration rule

Do not mass-rename first.

For each legacy identity:
OLD PATH/TERM
-> CURRENT OWNER
-> COMPATIBILITY NEED
-> MIGRATION TARGET
-> REFERENCES TO UPDATE
-> RUNTIME IMPACT
-> SUPERSESSION TRACE
-> SAFE DELETE/KEEP decision

Examples requiring migration review:
- GUIDE_FAMILY_LEARNING_OS -> current Learning OS canonical identity
- GUIDE_CHARACTER_RELATIONSHIP -> current exploration-crew/character relationship owner mapping
- LEARNING_APP_FAMILY_MASTER_REV_01 filename vs REV_00 header lineage
- dated Ready implementation snapshots in STATE.md

## Rewrite rule

The rewrite must be generated from:
SYSTEM MODEL
-> OWNER MODEL
-> CURRENT IDENTITY MAP
-> CONTRACT MODEL
-> CANONICAL DOCUMENT RESPONSIBILITY
-> REWRITTEN DOCUMENTS

Not:
OLD DOCUMENT
-> EDIT PARAGRAPHS
-> CALL IT REWRITE

## Current state

REFERENCE_FORENSICS = STARTED
CANONICAL_REFERENCE_GATE = IMPLEMENTED
BROKEN_OWNER_POINTER_FOUND = TRUE
LEGACY_BOOT_POINTERS_FOUND = TRUE
WHOLE_SYSTEM_REWRITE = BLOCKED_UNTIL_PRECONDITION_CLOSURE
