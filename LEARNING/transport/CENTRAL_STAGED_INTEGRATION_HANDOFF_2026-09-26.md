# CENTRAL LEARNING GOOGLE / REGISTRY / SPECIALIST / ACK / DRIVE — staged integration handoff (2026-09-26)

## Authority and inherited state
- Start with CURRENT/LEARNING_ENGINE_VERIFICATION_CURRENT_2026-09-25.md; exact main inherited at 8e78af8b77d1f3e132f05c99cd6b69a7f258a23e (merged PR #158), followed by CENTRAL_GOOGLE_NODE_PILOT_HANDOFF_2026-09-26.md.
- This handoff is DRAFT PR #159 evidence only, not a new main/CURRENT authority until reviewed and merged.
- All Core, learner-state, verification, receipt, adaptive-plan, Planner calendar authority, Drive storage roles, badge/gem ledgers and prior CLOSED are inherited unchanged. Retention and calibrated BKT promotion remain HOLD.
- Google Drive is reference/index/versioned archive, NOT active learner state/award/gem transaction storage.

## Newly implemented in draft PR #159
1. server-family-registry-provider.js: read-only ETag-strong Google sub (hashed key) -> administratively provisioned membership projection, active family member grant cross-check, expiry and immediate no-cache revocation. No browser permission authority. Actual registry admin provisioning and live Google login are NOT installed.
2. central-google-node-host.js: composes original google-learning-principal.js + registry read adapter + original central-learning-http-endpoint.js + Node bridge. Explicit origins, stores and official verifier runtime injection, no service deployment.
3. server-specialist-verifier.js: injected server-owned immutable assessment reference for Hide deterministic retrieval and Ready answer key; explicit separately persisted authorized human rubric for Snap. Missing reference/review stays OBSERVATION_ONLY. Provider outage fails closed. App producer formats, live reference issuance and server reviewer workflow are NOT yet bound.
4. central-store-conformance.js and central HTTP retry fix: disposable namespace checks strong create/readback, 12 parallel conditional writes, exactly one CAS winner, stale and duplicate rejection. Exhausted CAS maps to retryable HTTP 503, never ACK. LocalJsonStrongStore is a pilot fixture, not an operational store suitability approval; disaster recovery/FS durability, backup, encryption, region/quotas/costs are OPEN.
5. pwa-central-evidence-ack-client.js: evidence-only HTTPS POST adapter; obtains bearer token at flush, credential cookies omitted, validates source/family/member and durable central receipt before handing ACK to caller. It does NOT reuse Ready planner/app_state snapshot sync queue, persist its own outbox or switch application queues to ACKED. Ready/Hide/Snap actual binding and per-member session selection remain OPEN.
6. encrypted-drive-archive-export.js: injected trusted central source, AES-256-GCM encryption, source digest verification, existing-folder create-only versioned provider, ciphertext readback SHA-256 and appendVerifiedDelta only after readback. Failed upload/readback/index leaves archival work pending and never changes central learning receipt. All Drive/index/key providers in tests are TEST FIXTURES; no live Drive write, data migration, key setup, production credential, consent or API billing was triggered.

## Test interpretation
- CI steps are wired into TAKY Enforcement for the above new modules.
- Tests use local loopback Node, deliberately fake Google-style verifier tickets, local strong JSON or in-memory supplier fixtures; successes are FUNCTIONAL ADAPTER VALIDATION, not LIVE OPERATIONAL CONNECTIVITY.
- Existing #157/#158 CLOSED tests remain in workflow.
- Refer to the exact PR head's GitHub Actions result rather than claiming that a previous head tested newer commits.

## Remaining OPEN, strictly distinct from code-only tests
A. Real OAuth consent/client ID/official google-auth-library and server-admin family registry enrollment/revocation credentials/records, with approved costs and privacy policy.
B. Actual server reference assignment + Hide/Ready interaction producer fields and Snap separately authenticated reviewer workflow; prevent forged assessment issuance and event-ID replay divergence.
C. Select/provision production atomic durable store; run conformance in explicitly approved disposable namespace, failover/recovery and quota/cost tests, real HTTPS host and request-rate protection.
D. Integrate each product repo's evidence-specific durable pending queue -> central adapter -> trusted ACK -> scoped local state; test sign-out/member switch/retry/duplicate/out-of-order. Do NOT mix Ready's existing planner/app_state sync with learning-evidence ingestion. Separately authorized scoped Core decision read endpoint still OPEN.
E. Inject approved existing Google Drive folder, server KMS key, create-only Drive uploader/readback and idempotent Indexing delta sink, verify live versioned exports. Google Drive is not a live Learning Engine database.
F. HOLD retention estimator and calibrated BKT promotion; HOLD Netlify/deployment/production activation; PR #159 remains DRAFT unless separately reviewed and authorized.

USER != DEBUGGER. Do not ask the user to run fixture tests. No rollback of Core CLOSED, and do not claim an OPEN is CLOSED because a mock provider passed.

## LATEST DELTA — event-bound ACK / replay integrity / server reference store

- Security correction: central HTTP ACK now binds both `packet_id` and `event_id` as well as family/member/app. PWA adapter rejects an otherwise plausible ACK for a different event/packet, and rechecks active family/member AFTER the asynchronous HTTP round-trip before returning an ACK to the owning outbox. A selected-child change or sign-out cannot silently ACK an old member's packet.
- The central endpoint calculates a canonical, deterministic SHA-256 over the browser packet AFTER stripping all untrusted proof fields and BEFORE any server verifier additions. The fingerprint is passed into the existing atomic ETag ingest state, and event+packet identifiers are bound with conditional write. Same ID / different content returns `EVENT_OR_PACKET_ID_REPLAY_PAYLOAD_MISMATCH`; identical retry remains idempotent. Old un-fingerprinted event replay requires explicit reconciliation rather than false equality/ACK.
- New `server-specialist-reference-store.js` is the strong, server-only, read-only lookup adapter for server-issued Hide/Ready assessment references and separately approved Snap reviewer records. Namespaced hashed keys bind family/member/event/source/reference. It requires ETag-backed strong reads, checked provenance and issuer authorization; Snap reviews additionally require reviewer authorization receipt. Missing/unissued references remain observation-only. `central-google-node-host.js` now optionally composes this reference store with the previously implemented server specialist verifier, so the Node host actually uses it rather than relying solely on a test callback.
- Tests added for swapped ACK packet/event, selected-member switch while HTTP is pending, divergent replay, no false ACK after mismatch, forged/unissued reference/reviewer record, and Node loopback host -> strong family registry -> strong server reference -> verified central learning receipt. All credential and reference records in tests remain FIXTURES.
- Product repo evidence Outbox persistence/binding, live Google OAuth and family admin enrollment, real trusted assessment/reviewer issuance service, selected operational durable store, Drive SDK/KMS/Indexing and hosted runtime remain OPEN. PR #159 is DRAFT, main unchanged, no Netlify and no live Drive write. Retention / BKT promotion HOLD.

## LATEST DELTA — scoped evidence outbox contract

- New `scoped-evidence-outbox.js`: provider-injected atomic persistent read/CAS queue, distinct from Ready planner/app_state snapshot sync. Immutable packet digest and packet-ID conflict rejection, family/member/app scope, exclusive bounded lease, stale worker rejection, retryable offline PENDING, non-retryable scope/auth BLOCKED, exact receipt/packet/event-bound ACKED. No unverified HTTP result can ACK a row. The existing central ACK client now returns the already-validated packet/event IDs to this queue.
- New regression tests cover dedupe, divergent payload, competing claims, offline retry, member switch blocking, wrong receipt, exact receipt, cross-member isolation and expired lease takeover.
- This is an INJECTABLE QUEUE CONTRACT + in-memory atomic fixture test, not browser IndexedDB persistence, not Ready/Hide/Snap repo integration, and not operational central connectivity. Browser persistent CAS implementation, explicit BLOCKED recovery UI, selected-member session handling and app-specific producer binding remain OPEN.
- Do not merge PR #159 or call Netlify without separate approval. Retention estimator and calibrated BKT remain HOLD.

## LATEST DELTA — IndexedDB browser persistence and product-repo discovery

- `indexeddb-evidence-outbox-store.js` implements the existing outbox storage contract with a browser IndexedDB readwrite transaction enclosing read/version check/write, so multiple tabs cannot both commit the same CAS version. Its database is explicitly separate from planner/app_state snapshot sync. Cross-instance transaction fixture added to CI; this is a deterministic fake IndexedDB transaction, not an actual Safari/Chrome device/browser certification.
- Product repositories discovered: `hns140412-glitch/Ready-Set`, `Hide-Seek`, `Snap-Pop`. Ready currently has `ready-local-first-v01.js` and `ready-sync-adapter-v01.js` for app-state/Planner snapshots. No product repo was modified in this slice. Next OPEN is inspect exact current product heads and existing event producers, then introduce evidence-only adapter and test per product without replacing snapshot sync or Netlify deployment.
- Live OAuth/admin registry, trusted reference issuer/reviewer workflow, production durable central store, live Drive/KMS/Indexing and product PWA binding remain OPEN. PR #159 stays draft; main unchanged.

## LATEST DELTA — product bridge inspection / lease identity

- Prior IndexedDB correction exact-head CI #36249896885 SUCCESS. Product main bridge source inspection: Ready `ready-integration-v1.js` consumes candidate Learning actions but keeps Planner date authority; Hide `hide-bridge.js` emits observation-only memory signals; Snap `snap-bridge.js` emits contextual learning outcomes and separately requests rubric review. None of those source paths alone establishes authenticated family_id/selected_member_id plus trusted central assessment issuance. Do not auto-bind a guessed child_id to central member_id.
- Scoped outbox claim now carries unique per-claim nonce, checked on settle, with bounded 32 CAS retries. A stale worker cannot settle a newer claim even if owner text is reused or spoofed. Regression added.
- No product repository mutation, main merge, Netlify call or live data transfer. Product-specific family/session identity adapter and evidence packet mapping remain OPEN; no unverified local learning signal can become REAL_EVIDENCE_RECEIPT.

## LATEST DELTA — browser evidence pipeline composition
- Exact prior nonce-hardening handoff HEAD `0852e4da` CI #36250569986 SUCCESS.
- `pwa-scoped-evidence-pipeline.js` now composes scoped outbox + IndexedDB transaction store + authenticated ACK client with explicit `enqueue`, one-item `flushOne`, active-member-only listing and close. Host-supplied session must match family/member on enqueue and flush. No implicit background loop, no credentials or invented family mapping. Mid-flight selection change cannot ACK previous member; offline remains pending.
- Integration fixture tests authenticated enqueue, duplicate, wrong-member refusal, offline retry, mid-flight member switch and isolated listing. No real product repo mutation or browser-device/live central test; next OPEN is per-product source adapter plus approved trusted session/auth binding.

## LATEST DELTA — specialist source observation mapping and browser compatibility finding
- Prior exact-head `476e5a09` CI #36250643442 SUCCESS.
- New `specialist-observation-packet-mapper.js` explicitly maps three named observation types into source-scoped packets only with authenticated family/selected-member session and matching source event/member. It denies family/member mismatch and unauthorized mastery/award/Planner-date claims. Test covers all three apps. This does not silently treat existing raw bridge event as centrally verified assessment.
- IMPORTANT OPEN found during integration review: `scoped-evidence-outbox.js` currently imports Node `node:crypto` and modules are CommonJS. These are not directly loadable as unbundled browser scripts. Before claiming actual PWA integration, provide tested browser-compatible bundling or Web Crypto implementation and real browser IndexedDB transaction tests. No live app repository or deployment changes.

## LATEST DELTA — Web Crypto and browser bundle
- Prior exact-head `513dd85b` CI #36251030155 SUCCESS.
- Replaced outbox Node-only crypto with injected standard Web Crypto `subtle.digest('SHA-256')` and `randomUUID()`. Existing Node tests inject `node:crypto.webcrypto` as a fixture; production browser uses `globalThis.crypto`. Digest remains canonical SHA-256, no weakened hash or plaintext token persistence.
- Added audited five-module, dependency-free browser bundle builder and isolated Node-free browser-like VM test. Builder runs at build time only; the browser artifact has no Node builtin dependency. This is a build/test contract, not yet a committed distributable in Ready/Hide/Snap or real mobile browser certification.
- Remaining OPEN: actual PWA asset distribution and trusted session integration; real browser IndexedDB multi-tab test (current fixture is deterministic), central live service and credentialed end-to-end. Draft PR only; no main merge or Netlify.
