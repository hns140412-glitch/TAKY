# TAKY 콘텐츠·확장팩·에셋 무배포 갱신 절대 운영 기준 V1.1
Date: 2026-10-13
State: POLICY_STANDARD_PASS (CLAUDE REVIEW + CODEX INITIAL HOLD REMEDIATED + CODEX DELTA RECHECK PASS); RUNTIME_HOLD; LIVE PUBLISH BLOCKED PENDING GATES.
Authority: existing TAKY OS/DRIVE_STORAGE_MAP.json, MASTER/ASSET_DISTRIBUTION_MANIFEST_SCHEMA.json, ENFORCEMENT/asset_distribution_manifest_validator.py, CURRENT/DRIVE_ROOT_LAYOUT_LOCK_CURRENT_2026-10-07.json, CURRENT/CLOUD_ID_DRIVE_ASSET_DELTA_CURRENT_2026-10-07.json. No new parallel master.

## 1. Non-negotiable intent
- New learning packs, expansion chapters, problems, vocabulary, images, backgrounds, badges, dialogue and recordings shall refresh as content/data WITHOUT GitHub push or Netlify build/deploy, IF an already-deployed app shell/runtime supports their schema/slots/capabilities.
- GitHub is code/schema/governance history; Netlify delivers only the versioned PWA shell and runtime when code change needs release. A content-only update must not trigger a web deployment.
- Local development, review and integration use D:/Git PWA/TAKY_AI_WORKBENCH by WORK_ID. Collaborative AI scratch folders are internal; user experiences only apps and clear preview/approval screens.
- Do not silently rewrite approved UI, Visual ID, learner progress, character identity or voice identity.

## 2. Account/store responsibility, no invented Drive folder roots
- HNS Drive = internal operations, authoritative approved asset master bytes and private current/operational state; never a user-facing Drive browser.
- SIEZEALL Drive = user-specific records, assignments/homework, uploads, group/household sharing, user sync and approved distribution package route; app API is sole user-facing surface.
- Both Drive TAKY roots KEEP existing 4 locked groups: 00_CONTEXT, 10_DOMAINS, 20_PLATFORM, 90_MAINTENANCE. Reuse stable Drive folder IDs and leaf role IDs, particularly SIEZEALL 03_UPDATES and 04_USER_DATA; no new root hierarchy or duplicate inbox.
- TAKY-ASSETS = local authoring/asset evidence, Visual ID and production staging. HNS Drive approved master is the durable approved distribution binary authority per existing master. A local copy, SIEZEALL delivery copy, and device cache are not alternate approval masters; every derived/transfer copy preserves source asset_id + approved SHA + provenance.
- TAKY-SOURCE-VAULT retains acquired RAW sources. Unapproved production material remains in WORKBENCH and shall not be served to apps.
- Never expose OAuth tokens, Drive credentials, private Drive file URLs, ACL internals or unrestricted write grants to app clients.

## 3. One route: author -> verify -> approve -> publish -> activate
A. WORKBENCH: produce content pack/audio/asset with work_id, owning app, reviewed baseline, Visual ID / slot id, required runtime feature ids.
B. Validate content schema, dependency list, uniqueness, locale, license/distribution scope, expected app slot set, asset origin, SHA-256, accessible runtime resource size, media compatibility; reject unknown executable markup/scripts.
C. Apply real user approval gate for visual/voice authority changes. Changes to learning content follow the applicable approved content publishing policy; no silent user-authority promotion. Bind approved package_id/version to immutable source revision.
D. Stage immutable release package and versioned manifest; compare HNS approved source SHA to SIEZEALL distributed content SHA (where route applies). Authenticate publisher; never treat SHA alone as proof of publisher identity.
E. Write only necessary changed blobs and publish pointer/manifest LAST, with compare-and-swap/version precondition or equivalent serialized writer lock. Verify by remote file-ID metadata/hash readback and permission check.
F. Apps fetch authenticated approved catalog/manifest via controlled access path, validate schema + app compatibility + signatures/authenticated provenance + hash; cache immutable version locally and atomically switch pointer AFTER successful download/validation.
G. On network failure, corruption or incompatible pack, use only a previously verified, currently authorized, non-revoked compatible version. A package, signer key or user access grant marked REVOKED is INELIGIBLE for fallback or offline activation; if no eligible version exists, block content and explain recovery. Enforce offline authorization lease/expiry and reauthentication policy; while offline, never claim current revocation status beyond last verified authorization. Support versioned rollback only to an eligible non-revoked revision, by a new signed higher-generation catalog. Do not start a Netlify release as recovery for a data-only fault.
H. Record effective version, consumer app, change evidence, verification receipt, device activation and rollback status. User sees content freshness/approval status inside app, not Drive folders.

## 4. Expansion package manifest minimum
Required: package_id, package_version, kind [LEARNING_CONTENT, EXPANSION, VISUAL_ASSET, VOICE_ASSET, CONFIG_SAFE], app_id, target_slots, schema_version, runtime_contract_min, runtime_contract_max, dependencies, asset_entries [{asset_id,visual_id?,locale?,slot_id,sha256,mime_type,bytes,source_ref,distribution_ref,release_scope}], approved_by/evidence, approval_state, source_authority, content_hash, effective_manifest_version, published_at, rollback_ref, access_scope.
Content package may never deliver raw JS, new privileged operations, auth bypasses, updated code execution or arbitrary HTML in the guise of 'data'. New capability or schema requires code-release evaluation.

## 5. Hard split: code release vs data update
NO GIT/NETLIFY: existing engine can render/execute the package without new JS/CSS/API endpoints/auth behavior/schema migrations; approved asset content binds preexisting slots; language/problem/question/config values in allowlist.
RELEASE REVIEW REQUIRED: new UI element type, interaction engine, geometry rule, runtime event/voice binding contract, permission/identity change, service worker/caching logic, backend endpoint, data schema incompatible with deployed client, or content requiring new library code.
A pure manifest/approved slot binding refresh is data route; editing repository manifest scripts is NOT necessary when client consumes remote manifests.
Mixed change is split: compatible pack now via data route; incompatible code by separate release gate.

## 6. Security, identity and cost gates
- Resolve owner_user_id / family_id / group_id server-side. SIEZEALL user data uses per-record ACL; user sharing and user records are distinct from publicly distributable content. Never broaden access as shortcut.
- PUBLIC_RELEASE_SAFE only to legitimately public/read-safe distributions, FAMILY_PRIVATE_AUTHENTICATED uses authenticated channel, INTERNAL_ONLY never goes to SIEZEALL package. Existing 'ANYONE_WITH_LINK_WRITER' exposure is OPEN_SECURITY_REMEDIATION; do not imply remediation already occurred.
- Immutable package versions; uniqueness and no downgrade without explicit rollback receipt. Upload idempotency, concurrency conflict handling, quota/retry/backoff, audit provenance.
- Necessity gate before AI/Drive API calls; local checks first; delta-only uploads. GitHub Push / Netlify deploy / paid API require separate explicit user authorization. No automated cron that triggers Git/Netlify by package refresh.
- A link/shortcut/file-ID is not access authorization; explicitly verify permissions. Service worker stale-cache and offline behavior must be exercised on devices.

## 7. Enforceable acceptance tests (all required for runtime PASS)
T1. Existing deployed shell loads a new approved learning pack without new GitHub commit, build or Netlify deploy.
T2. Approved Visual ID asset replacement shows correctly in all consumer apps and old source SHA cannot silently overwrite it.
T3. Approved voice replacement plays against real script/event/locale and interrupt/replay behavior without app code change.
T4. Invalid SHA, missing slot, unauthorized user, wrong app/schema, incompatible client or revoked package fails closed.
T5. Offline fallback activates last verified version; recovered network refreshes only changed package.
T6. Concurrent upload and partial transfer never create visible half-release; rollback restores prior verified state.
T7. Audit shows source/delivery/device hash equal, publisher authorization, access scope, active package version and consumer receipts.
T8. GitHub push count = 0 and Netlify deploy count = 0 for every content-only test; no paid API.
T9. HNS/SIEZEALL root layouts and stable Drive folder IDs unchanged; no new duplicate official asset original.
T10. Failure trace from source -> distribution -> app cache is recoverable and user-friendly (no raw Drive paths shown).

## 8. Current state / non-claims
- 2026-10-07 READY_HOME_UI_E2E single PNG, single READY_SET consumer, Windows %LOCALAPPDATA% cache route shows HNS→SIEZEALL→device cache SHA alignment and no Netlify; it is NOT browser PWA hot-update proof. Existing readback noted SIEZEALL ANYONE_WITH_LINK_WRITER security finding, so this is PASS_WITH_OPEN_SECURITY_FINDING for current adoption decisions; historical immutable receipt is retained unchanged.
- Existing Snap/Hide bundled asset manifests and Service Workers enumerate static assets; remote catalog consumers and refresh activation require per-app implementation/readback. Do not mark T1-T10 PASS without execution evidence.
- NO CHANGES to live Drive ACLs, physical layout, Netlify settings, GitHub remote or deployment in this standards work.
- Proceed: Claude independent read-only review -> reconcile issues -> Codex read-only verification -> report unresolved gaps and implementation gate backlog.

## 9. Independent Claude review merged 2026-10-13 — P0 implementation blockers
- Review artifact: D:/Git PWA/TAKY_AI_WORKBENCH/40_AI_COLLAB/SHARED-RESULTS/CLAUDE_INDEPENDENT_REVIEW_20261013.md; verdict CONDITIONAL. Independent review is NOT runtime PASS.
- G-ACL HARD STOP: before any new live package publication or production catalog pointer update, read back permissions on SIEZEALL 03_UPDATES and every effective distribution folder. If any ANYONE / ANYONE_WITH_LINK writer or commenter is present, BLOCK publication and do not claim clean PASS. Only explicitly authorized publisher can write. Existing 2026-10-07 one-PNG pass is classified as PASS_WITH_OPEN_SECURITY_FINDING for new decisions. Remediation requires user approval; do not mutate ACLs silently.
- G-TRUST HARD STOP: source SHA and distribution SHA prove bytes match, NOT authenticated publisher. Runtime requires signed/authenticated immutable manifest/catalog, trusted client public-key set (e.g. Ed25519 with key_id), server-side signing key in private HNS, key rotation/revocation plan and signature verification fail-closed. Signing scheme canonicalization and client platform support must be tested before release.
- G-ACCESS HARD STOP: clients must never use unprotected Drive file links or OAuth credentials. Read-only Auth/Access API contract GET /catalog and GET /blob/{asset_id}@{sha} (authenticated access + immutable response, audience/scope restrictions, version and MIME checks) must exist and pass auth tests before enabling private/production distribution. This is a proposed contract, not proof that an API is deployed.
- G-RUNTIME HARD STOP: examined Hide & Seek cache-first and Snap & Pop network-first/precache SW paths do NOT prove authenticated verified remote updates; if an adequate external loader is not independently evidenced for a given app, that app requires a separately approved initial loader code release. Audit each app's complete consumer path before deciding; never claim all apps unconditionally lack an external loader or that all already support hot updates.
- G-ATOMIC HARD STOP: stage content into immutable versioned caches, verify ALL blobs plus manifest signature, then update one ACTIVE_POINTER record only at a safe session boundary; retain previous_verified and storage budget, reject partially downloaded/unverified responses. Avoid caching unchecked same-URL responses as active assets. Test recovery and rollback.

## 10. Schema and catalog evolution, no destructive V1 replacement
- Existing TAKY_ASSET_DISTRIBUTION_MANIFEST_V1 remains readable and validator behavior unchanged. Do NOT rename its keys to match draft V2.
- Design TAKY_ASSET_DISTRIBUTION_MANIFEST_V2 as additive: retain V1 schema markers/required fields including generated_at, source_authority, distribution_authority, assets[slot_id, asset_id, master_ref, master_revision, source_sha256, distribution_ref, distribution_sha256, mime_type, release_scope, consumer_apps, status]. Add kind, runtime bounds, approval evidence, dependencies, signature/kid, published_at, monotonic effective_manifest_version and rollback/revocation fields. Version per package, per app and per asset slot independently.
- V2 retains V1 assets[] with all existing per-entry names; earlier §4 asset_entries is ONLY a conceptual draft alias and SHALL NOT be a second source of asset truth. V2 uses assets[] for binaries, and content_entries[] for immutable typed learning/activity JSON. required_slots is V1 OPTIONAL (not one of required_top_level) and is mandatory in V2 only for slot-bound packages. Add a version-specific validator and V1 regression; preserve existing V1 manifests.
- Sanitize and strictly allowlist content MIME / bytes / URI schemes / field types. Disallow executable JS/HTML, active SVG scripts, javascript:/data: URLs, external uncontrolled references, dangerous dynamic templates. Child-facing text stays text, not HTML injection.
- Only a specifically authorized HNS publisher may promote immutable approved master revisions; no in-place overwrite of an approved binary/master ID. Bind master_revision to stable Drive revision identity where supported AND content SHA, not mutable 'modified:' time alone. Single authorized writer serializes catalog promotions; do not assume native Google Drive CAS. Publish immutable blobs first, then the small catalog pointer LAST with prev_catalog_sha and monotonic generation. Client rejects stale/replayed catalogs; recovery uses a NEW signed higher-generation rollback catalog, not silent downgrade.
- Folder routing is through stable IDs; versioned package namespace MAY be logically placed under existing SIEZEALL TAKY/20_PLATFORM/03_UPDATES/packages/<package_id>/<version>/ (no new TAKY root). User record uploads remain under existing 04_USER_DATA; existing separate 00_INBOX_USER is the single reference intake outside TAKY root.

## 11. Refresh timing, privacy and observability
- Check catalog on app cold start and foreground re-entry with bounded minimum recheck interval; do not activate during an active learning/session/voice play. Stage on Wi-Fi/available network with quota-aware download; activate at next safe session boundary. Exact intervals/cache budget are per-app runtime parameters to be verified, not invented constants.
- Support iOS Safari/PWA eviction and offline-first recovery. Immutable cache entries must be revalidated and automatically recovered; no complete-content guarantee when OS evicts storage.
- User homework, private submissions, user recordings, personal/child learning telemetry and SAVEY data MUST NOT enter public expansion-pack distribution. FAMILY_PRIVATE_AUTHENTICATED uses verified access control + TLS; sensitive cached data gets scoped encryption/expiry/deletion design. No cross-household reads.
- Existing V1 asset validator checks SHA-256 format but NOT source/distribution hash equality, signer trust, ACLs or generated_at requirement; its PASS is syntax/shape evidence only, NOT distribution security or runtime PASS. A separate publisher promotion gate MUST compare remote readback hashes, valid authority, signer, ACL, and immutable version. Existing SW activate cleanup must delete only owned code-cache namespace, never immutable approved content-cache or active/previous_verified packages.
- Consumer receipt collects minimum needed package/app/revision information, no unnecessary user/device tracking. Publication receipts record effective Drive file IDs, ACL readback, authorized signer, hashes and device activation outcomes.
- Verify GitHub/Netlify no-call via bounded before/after evidence when possible; absence of a new file alone is not proof of no deploy.

## 12. Adoption backlog and acceptance
P0-SEC: confirm 03_UPDATES effective ACL; block unsafe writes; request explicit approval for ACL fixes.
P0-API: verify or implement authenticated read-only catalog/blob delivery, publisher identity and signing.
P0-SCHEMA: additive V2 schema, validator and V1 regression.
P0-LOADER: common immutable cache + active-pointer loader, initial release for incompatible apps with separate user authorization.
P1-UX: in-app installed version / available update / approval status and safe-session activation.
P1-PRIVACY: user/private content strict separation, private cache/data retention tests.
P1-DEVICES: iOS/Android/desktop, offline recovery, SW lifecycle, quota/eviction and concurrent publish tests.
ACCEPTANCE: T1-T10 above plus ACL readback BLOCK test, forged signature, key revocation, old catalog replay, user-boundary ACL, and V1 backward-compatible validator PASS. Until evidenced, STATE=DESIGN_STANDARD_ONLY / RUNTIME_UNVERIFIED.

## 13. Independent review decision and adoption boundary
- Claude independent review: D:/Git PWA/TAKY_AI_WORKBENCH/40_AI_COLLAB/SHARED-RESULTS/CLAUDE_INDEPENDENT_REVIEW_20261013.md — CONDITIONAL.
- Codex independent first verification: D:/Git PWA/TAKY_AI_WORKBENCH/40_AI_COLLAB/SHARED-RESULTS/CODEX_INDEPENDENT_VERIFY_20261013.md — POLICY_HOLD / RUNTIME_HOLD; P0 revoked-cache fallback contradiction identified.
- Codex bounded delta recheck: D:/Git PWA/TAKY_AI_WORKBENCH/40_AI_COLLAB/SHARED-RESULTS/CODEX_DELTA_RECHECK_20261013.md — POLICY_STANDARD_PASS / RUNTIME_HOLD. Optional V1 required_slots wording cleaned after recheck without semantic policy change.
- Decision: this single CURRENT document is the effective governance policy for no-deploy updates. It authorizes NO release, upload, Drive ACL changes, runtime implementation, GitHub push, Netlify deploy or paid API call.
- Reopen condition: any change to security scope, current root folder IDs, manifest trust, runtime contract or revocation/fallback rules requires new impact review. No competing parallel CURRENT.

## 14. 2026-10-13 implementation / conflict readback (local, not live publication)
- Local V2 validation and preflight enforcement: ENFORCEMENT/no_deploy_release_gate.py. Existing V1 validator remains separate and unmodified. Local tests: ENFORCEMENT/no_deploy_release_gate_test.py, including signed manifest tampering, hashed payload mismatch, forbidden MIME/URL, missing slot, private content, runtime block and ACL ancestry.
- Route authority imported from ENFORCEMENT/drive_route_resolver.py -> OS/DRIVE_STORAGE_MAP.json. SIEZEALL 03_UPDATES: TAKY/20_PLATFORM/03_UPDATES, stable folder ID retained. WORKBENCH PATH_REGISTRY points to this resolver without duplicating Drive folder IDs.
- Live authenticated metadata readback found ANYONE/WRITER on SIEZEALL TAKY root, 20_PLATFORM, 03_UPDATES and 04_USER_DATA. All publication is HOLD; user-data privacy requires separate authorized ACL remediation. Evidence: D:/Git PWA/TAKY_AI_WORKBENCH/50_INTEGRATION_TEST/SIEZEALL_03_UPDATES_ACL_READBACK_20261013.json. Snapshot is NOT a continuous live ACL permission attestation.
- HNS additional semantic roles SHARED_REFERENCE and WORK_OS_ARCHIVE were independently verified by existing Drive IDs and parent relations; ENFORCEMENT/drive_storage_map_validator.py was aligned without moving any Drive files. Root four groups and route tests retained.
- Content supply candidate modules remain candidate-only: LOCAL_E2E_PASS from forming/Play Camp ingestion is not approval to publish and cannot bypass this preflight. Existing PWA remote Auth/Access API, release signer operational key, client-loader, safe-cache/rollback and per-device T1-T10 tests remain NOT IMPLEMENTED/UNVERIFIED.
- No GitHub push/merge, Netlify build/deploy, Drive ACL write, content upload or paid API performed.
