# TAKY DRIVE / MINING / STORAGE CLEANUP — NEW CHAT START — 2026-10-07

Status: RESUME READY / NO COMMIT / NO PUSH / NO DEPLOY
Scope: continue only the current Drive/mining/storage cleanup. Do not redefine TAKY master logic, Beta/Alpha, Visual ID, or already CLOSED/PROMOTED work.

## 0. Repository / worktree safety

TAKY repo:
- path: D:\Git PWA\TAKY
- branch: character-asset-behavior-separation-2026-09-30
- resume HEAD: fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e
- worktree: heavily DIRTY with unrelated OPEN work
- prohibited: reset / checkout / clean / broad rewrite
- prohibited without user approval: commit / push / merge / deploy / Netlify

SOURCE VAULT:
- path: D:\Git PWA\TAKY-SOURCE-VAULT
- this folder is currently NOT a git repository; do not invent git state for it.

## 1. HARD LOCK — Drive physical presentation

TAKY root on BOTH HNS and SIEZEALL is physically grouped as exactly:
- 00_CONTEXT
- 10_DOMAINS
- 20_PLATFORM
- 90_MAINTENANCE

00_CONTEXT stays directly under TAKY.

HNS current physical paths:
- TAKY/00_CONTEXT
- TAKY/10_DOMAINS/01_LEARNING
- TAKY/10_DOMAINS/02_ARCHIGROW
- TAKY/20_PLATFORM/03_COMMON
- TAKY/20_PLATFORM/UI_SOURCE_AUTHORITY
- TAKY/90_MAINTENANCE/AUDIT
- TAKY/90_MAINTENANCE/20_REVIEWS_C2S
- TAKY/90_MAINTENANCE/80_HANDOFF
- TAKY/90_MAINTENANCE/90_ARCHIVE
- TAKY/90_MAINTENANCE/90_TEMP
- TAKY/90_MAINTENANCE/99_DELETE_PENDING

SIEZEALL current physical paths:
- TAKY/00_CONTEXT
- TAKY/10_DOMAINS/01_LEARNING_SHARE
- TAKY/10_DOMAINS/02_ARCHIGROW_SHARE
- TAKY/20_PLATFORM/03_UPDATES
- TAKY/20_PLATFORM/04_USER_DATA
- TAKY/90_MAINTENANCE/90_TEMP

Stable leaf Drive IDs were preserved while moving. Do not recreate the old flat root.

Authority/readback:
- OS/DRIVE_STORAGE_MAP.json
- CURRENT/DRIVE_ROOT_LAYOUT_LOCK_CURRENT_2026-10-07.json
- CURRENT/CLOUD_ID_DRIVE_ASSET_DELTA_CURRENT_2026-10-07.json

Validators currently PASS:
- ENFORCEMENT/drive_storage_map_validator.py
- ENFORCEMENT/drive_route_resolver_test.py
- ENFORCEMENT/drive_path_reference_guard.py
- ENFORCEMENT/mobile_app_development_registry_validator.py
- ENFORCEMENT/drive_physical_layout_guard.py hns "F:\내 드라이브\TAKY"

## 2. Cloud / account / inbox lock

- Google Cloud project / OAuth Client ID / Drive API owner = SIEZEALL.
- HNS = internal/admin approved master; not a user file-drop surface.
- SIEZEALL = user/shared input + approved distribution/user sync.
- single user reference inbox = F:\내 드라이브\Work\REFERENCE\00_INBOX_USER
- local collector watches the SIEZEALL-facing synced inbox.
- collector boundary = acquire/hash/direction preserve/Mining dispatch only.
- Indexing/Learning/Canonical promotion remain downstream.

Existing inbox baseline:
- 58 existing files were baselined without bulk re-mining.
- existing baseline must not be redispatched unless explicitly requested or changed.

IMPORTANT OPEN defect:
- SOURCE-VAULT reference inbox state/summary currently contains mojibake for the Korean path and latest summary says HOLD_INBOX_UNAVAILABLE.
- Fix encoding/path serialization first. Do NOT wipe the 58-file baseline or rebuild state destructively.
- After fix, validate the exact real path F:\내 드라이브\Work\REFERENCE\00_INBOX_USER and preserve existing baseline identities.

## 3. Asset route lock

Current route:
HNS approved master
-> manifest/hash gate
-> SIEZEALL approved distribution
-> device SHA-256 verified cache / safe activation

Current important paths:
- HNS UI master: TAKY/20_PLATFORM/UI_SOURCE_AUTHORITY
- HNS app/learning asset surface: TAKY/10_DOMAINS/01_LEARNING/05_ASSETS
- SIEZEALL distribution: TAKY/20_PLATFORM/03_UPDATES

Netlify = PWA shell/runtime delivery only; never asset-binding authority.
GitHub TAKY-ASSETS = historical migration/catalog evidence, not current binary master.
Routine asset/data package refresh does not require GitHub/Netlify deploy unless code/schema/slot/rendering logic changes.

## 4. Completed in this session

- HNS/SIEZEALL TAKY roots visually grouped into four folders.
- 00_CONTEXT promoted to top-level on both accounts.
- old root clutter moved non-destructively under grouping/maintenance; Drive IDs preserved.
- path consumers updated in Drive map, asset current/protocol/handoff, mobile app registry.
- current route resolver + path guard + physical layout guard added.
- stale current flat paths and stale current GitHub-binary-authority wording removed from active governance surfaces.
- Google Drive START/CURRENT/storage docs received grouped-layout delta/readback.
- no destructive delete, no commit, no push, no deploy.

## 5. NEXT OPEN — execute in this order

1. FIX SOURCE-VAULT INBOX ENCODING / PATH
   - repair Korean path serialization/mojibake without discarding CURRENT baseline
   - validate exact inbox availability
   - run incremental scanner with max 0 / validate-only first
   - existing 58 files remain baseline

2. 90_MAINTENANCE CLEANUP
   - inspect AUDIT / 20_REVIEWS_C2S / 80_HANDOFF / 90_ARCHIVE / 90_TEMP / 99_DELETE_PENDING
   - classify CURRENT-NEEDED / EVIDENCE-KEEP / DUPLICATE / REGENERABLE / DELETE-CANDIDATE
   - move/merge by ID where safe; no name-only deletion
   - do not touch root four-group layout

3. MASTER / OS / CURRENT TRASH CLEANUP
   - remove stale transitional wording, duplicate current pointers, obsolete flat-path assumptions, superseded route fragments
   - preserve immutable history/evidence
   - do not rewrite master logic from scratch
   - RULE WRITTEN != RULE ENFORCED; retain working validators/guards
   - run stale-reference scans after every cleanup batch

4. REAL DATA-FLOW E2E
   - use one NEW/CHANGED inbox item only
   - SIEZEALL 00_INBOX_USER -> local collector -> Mining -> Indexing -> HNS CURRENT/projection -> SIEZEALL approved distribution as applicable
   - verify receipts/readback/hash
   - no bulk re-mining

5. REAL ASSET PACKAGE E2E
   - use one existing approved asset set
   - HNS master -> manifest/hash -> SIEZEALL 03_UPDATES -> device/cache consumer
   - verify slot_id -> asset_id -> Visual ID -> hash -> distribution ref
   - prove no Netlify filename inference is required

6. FINAL REGRESSION
   - drive_storage_map_validator
   - drive_route_resolver_test
   - drive_path_reference_guard
   - drive_physical_layout_guard
   - mobile_app_development_registry_validator
   - asset manifest validator
   - git diff --check
   - report what is CLOSED vs still OPEN

## 6. Execution principles

- USER != DEBUGGER.
- same failure must not repeat.
- preserve stable Drive IDs.
- do not create new inbox/root/archive trees.
- unexpected root item -> 90_MAINTENANCE/90_TEMP HOLD.
- source deletion is HOLD until extraction + Indexing + readback are verified.
- raw/source may later be deleted if extraction/index/provenance is proven complete; current fragmentation cleanup phase remains conservative.
- no Netlify / paid API / push / merge / deploy without explicit approval.

Resume command:
"최신 TAKY 기준으로 재개. HANDOFF/TAKY_DRIVE_MINING_STORAGE_CLEANUP_NEW_CHAT_START_2026-10-07_LATEST.md 먼저 읽고, CLOSED/LOCKED는 상속하고 OPEN 1번부터 진행해."
