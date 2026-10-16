# TAKY Google Drive Dual Account Storage Contract
Status: CURRENT POLICY CORRECTION 2026-10-13 / Runtime enforcement unverified

## Authority
- HNS (hns140412@gmail.com) = PRIVATE OPERATION SERVER. TAKY governance, master/current authority, orchestration, system configuration and operational state.
- SIEZEALL (siezeall@gmail.com) = USER DATA SERVER. Per-user homework, learning records, uploads, task evidence, sharing scopes and user/group material.
- Neither account is a user-facing file browser. User-facing surfaces are TAKY apps (Ready & Set, Hide & Seek, Play Camp, Snap & Pop, SAVEY, TAKY Mobile).
- Google Drive provides storage via authenticated Drive API, not web server or transactional database functionality. Application API owns identity, authorization, isolation, concurrent writes, reconciliation and UI.

## Operating model
APP UI -> TAKY Auth/Access API -> policy check -> HNS configuration read or SIEZEALL per-user record/file operation -> journal/index -> UI result.
Never expose raw Drive credentials, refresh tokens, service credentials or unrestricted file URLs in browser/client code.
Use stable user_id/family_id/group_id/project_id/work_id and file_id, not folder names as identity.
Family/group sharing requires explicit grant and scope validation; a family member does not gain access to another household by default.
SAVEY financial/household records must remain private with stronger ACLs and cannot inherit broad shared permissions.

## Minimal folder model (not navigated by users)
HNS and SIEZEALL TAKY roots: {00_CONTEXT,10_DOMAINS,20_PLATFORM,90_MAINTENANCE} (existing locked Drive folder IDs; do NOT recreate).
HNS uses 10_DOMAINS for domain masters and 20_PLATFORM for common/UI source authority; SIEZEALL uses 20_PLATFORM/03_UPDATES for approved packages and 20_PLATFORM/04_USER_DATA for individual records; existing 00_INBOX_USER is the sole external reference intake.
Subfolder layout is implementation detail; do not create new physical branches before checking existing Drive folders and migration impact.
In SIEZEALL, partition by stable owner IDs and attach metadata to file records; group/shared data uses explicit ACL references and no uncontrolled copies.
WORKBENCH remains a local AI project-production workspace, not the SIEZEALL user database.

## Data contract
Each record: record_id, record_type, owner_user_id, family_id(optional), group_id(optional), visibility, storage_account, drive_file_id, version, sha256(for binary), created_at, updated_at, status.
Homework: assignment_id, learner_id, subject, due_date, attachment_refs, submission_refs, state, audit.
Learning event: event_id, learner_id, app_id, source_work_id, observed_at, evidence_ref, version.
Sharing: share_id, resource_id, grantee_user_id_or_group_id, permissions, expiry(optional), revocation_status.
Use append-only mutation journal with idempotency key, version check, retry/backoff and explicit conflict reporting. An upload is not complete until Drive metadata readback and app index consistency verify.
Raw Drive folder path must never be authorization proof.

## No user folder-navigation workflow
Users manage projects, homework, uploads, approvals and records only in the app UI. Folder names like CONTEXT/DOMAINS/PLATFORM must not appear as required UI navigation.
AI-to-AI logs, MCP/skills, design drafts and tests stay in TAKY_AI_WORKBENCH under internal paths.
Approved visual/audio origin remains TAKY-ASSETS; user assignments and submissions belong to SIEZEALL user data store.

## Operations and cost gates
Local work first; minimal Drive API calls with batch/delta indexing where appropriate.
No GitHub push, Netlify deploy, paid API, broad public share, mass move/delete without explicit authorization.
Do not create duplicate physical masters or automatically mirror HNS and SIEZEALL.
Runtime write/read/share/revoke E2E and owner-boundary tests are required before declaring enforcement PASS.

## Supersession
This corrects the earlier user-facing SIEZEALL Drive HOME and four-folder browsing model. These are NOT valid user navigation requirements.
The exact existing Drive folder IDs and ACLs must be inventoried before physical migration.

## App-only storage boundary — verified clarification (2026-10-13)
- Normal users NEVER browse, log into, manage or directly share any HNS/SIEZEALL Drive folder. App UI is the sole user-facing interface (homework, learner history, attachments, uploads, group/family sharing).
- Backend authenticates each user, authorizes user_id/family_id/group_id and record ownership, and selects SIEZEALL 04_USER_DATA by stable Drive folder ID; user-provided path and folder names grant NO access.
- App content updates use SIEZEALL 03_UPDATES through approved service-side catalog/blob access; user records/uploads are NOT expansion content and MUST NOT go in 03_UPDATES.
- HNS operations/current/approved master are server-only; TAKY-ASSETS is the local authoring/Visual ID evidence location, not another user database.
- TAKY ENFORCEMENT/app_drive_access_route.py provides a pure server-side route planning contract; this is NOT a deployed Auth/Access API, and it must not be callable with user-asserted verification flags as authorization. Enforcement is pending real middleware and E2E evidence.
- Security finding: connected SIEZEALL metadata readback on 2026-10-13 showed anyone/writer on 03_UPDATES and 04_USER_DATA, and their parent folders. Ordinary users are NOT given Drive navigation or folder management by TAKY apps; however, this UI policy is separate from Drive's underlying link permissions. Anyone-with-link writer remains an external exposure risk (not proof of access or exfiltration). Do not change or revoke live ACLs before identifying the exact application read/write identity, upload path and fallback behavior; preserve working app recording while auditing, block any new package publication through unsafe scopes, and require approved least-privilege migration plus app upload/read/share regression before marking security remediated.
- Existing 4 locked Drive root groups and stable IDs are preserved. HNS UI_SOURCE_AUTHORITY's previously missing logical ID was confirmed via connector readback and added to OS/DRIVE_STORAGE_MAP.json without creating or moving any Drive folder.

## Actual runtime path reconciliation (2026-10-13)
- HNS operational runtime: central authenticated family member API and strong ETag/CAS transaction state. Learning OS owns family data meaning; Learning Engine only interprets evidence; Planner alone allocates calendar dates.
- SIEZEALL user-data storage: encrypted versioned approved user record archive at existing TAKY/20_PLATFORM/04_USER_DATA (stable Drive ID from OS/DRIVE_STORAGE_MAP.json). No user browses Drive. Drive is NOT the concurrent transaction engine.
- Central POST/GET /api/family/user-data -> LEARNING/transport/family-user-data-store.js -> durable archive outbox (family-user-data-archive-outbox.js) -> private authenticated worker (family-user-data-siezeall-archive-publisher.js) -> SIEZEALL Drive after ACL validation, immutable encrypted upload and byte/hash readback. Until live provider and permissions pass, backup remains PENDING, NEVER falsely ARCHIVED.
- Ready & Set local assignment/schedule/planner keys -> ready-family-planner-sync-v1.js -> central scoped PLANNER_SNAPSHOT under family_id/member_id. Legacy user data import must be explicitly confirmed and simultaneous device edits block on ETag conflicts. Member switch preserves separately scoped local state. Ready/Hide/Snap send source evidence to existing Learning Engine adapter, not Planner directly.
- Local fixture tests demonstrate code contract, NOT real hosted endpoint/Drive persistence/device PASS. Current SIEZEALL public writer on root/20_PLATFORM/04_USER_DATA blocks private upload; do not change live ACL without approved nonbreaking migration.
