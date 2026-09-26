# CENTRAL LEARNING EVIDENCE HTTP BOUNDARY — 2026-09-26

## Direct continuation
The independent Learning Engine Core already exists under TAKY, **not in Ready / Hide / Snap PWA**. This implements only the missing provider-neutral HTTP ingress boundary and durable receipt acknowledgment guard, reusing `LEARNING/transport/family-member-identity-resolver.js`, `authenticated-evidence-transport.js`, `durable-evidence-store-adapter.js`, the existing specialist verification policy, and `LEARNING/transport/drive-archive-route.js`. No duplicate learning engine or Planner scheduling authority is introduced.

## Implemented
`LEARNING/transport/central-learning-http-endpoint.js`: server-only `create({verifyBearerToken,store,verifySpecialistEvidence?})` returns `handle(request)` for POST `/api/learning/evidence`. Only the injected trusted server bearer verifier may issue the principal (the browser's principal/identity declarations are ignored); the canonical resolver requires actual authenticated family membership and authorized target member scope before any evidence processing. The method, content type, JSON body size and source-app/event source consistency are checked before ingestion; all responses set no-store/private headers and never return full learner state, other family members' data, storage key, raw event, bearer token, or internal credential.

**Critical evidence authority correction:** Browser-supplied `verification_candidate`, raw `verification_input`, self-declared verification and outcome claims are removed by default. A packet can become a `REAL_EVIDENCE_RECEIPT` only when injected **trusted SERVER** `verifySpecialistEvidence` independently verifies its actual reference/provenance and returns a same-scope packet. If no trusted verifier exists or it returns a negative decision, its event can only be an `OBSERVATION_INGEST_RECEIPT`, not verified performance. Verifier outage or scope mismatch fails. A production verifier must actually check server-owned answer keys/producer evidence or permitted signed rubric review; fixture tests use an explicitly fake verifier and are not production proof.

`LEARNING/transport/durable-evidence-store-adapter.js` now denies missing current-state ETag and does not acknowledge a write without `modified:true` plus returned ETag. Conditional conflicts are bounded and retried. Do not report an accepted/verified ACK if persistence is not confirmed. The real store must implement atomic conditional writes and strong consistent reads; this is an interface requirement rather than a completed cloud-store connection.

## Deployment and Drive split
This is executable core endpoint **composition**, not a registered Netlify Function, deployed URL or configured OAuth service. It imports no cloud SDK and is not accessible to the actual PWAs until a trusted hosting/router, issuer/audience/expiry/revocation verifier, allowed app origins/CORS and rate limits, durable live store and deployment approval are supplied. Static PWAs keep their pending outbox; only server receipt allows SYNCED status. The central Learning Engine owns pedagogical interpretation, but this HTTP slice is evidence ingress; separate decision/read endpoints and final hosted Core binding remain OPEN.

Google Drive is an incremental source/index and versioned verified archive lane. Archive export is downstream of a committed receipt and may fail/retry without changing that receipt; Drive does not receive private plaintext learning state, become an online transaction store, or run the Learning Engine. No Google Drive file, folder, OAuth permission or asset was mutated by this slice.

## Tested gates
Real controlled `LocalJsonStrongStore` persistence and receipt replay; injected bearer token verification and cross-family/member denial; browser's forged principal ignored; forged browser exact-match candidate downgraded to observation; trusted server-only candidate can produce a real receipt; same-scope verifier requirement; duplicate receipt; malformed/big request, wrong method/content type, verifier/store outage; no-store body headers and no private state leakage; missing write ETag does not give false successful ACK. Existing Learning/ready/hide/snap tests remain in the full TAKY Enforcement workflow.

## OPEN
1. Bind hosted actual request framework to provider-neutral endpoint, with server-only trusted Google/OIDC token verifier and authoritative family/member membership source.
2. Bind actual app-specific server verifier/reference source rather than test callback. Verify parent/teacher rubric authority from real review ledger, not browser labels.
3. Bind one approved central durable conditional evidence state store, no competing PWA learner-state authority; install privacy/security monitoring and release gate.
4. Add scoped central Learning outcome read/decision endpoint and connect Ready/Hide/Snap authenticated adapters; store client offline outbox until server ACK.
5. Implement separate encrypted Google Drive versioned archive upload/readback receipt and changes-feed incremental reference mining; never move real-time decisions to Drive.
6. Keep unresolved retention estimator and calibrated BKT in HOLD; do not auto-promote on test mocks.
