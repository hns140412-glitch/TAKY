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
