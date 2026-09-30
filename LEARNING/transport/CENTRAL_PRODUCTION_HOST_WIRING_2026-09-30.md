# Central Learning production host wiring — 2026-09-30

## Purpose
`central-learning-production-host.js` is the deployment assembly boundary for the already-tested TAKY central Learning components. It does not deploy a cloud service and does not invent credentials, family membership, Index authority, or specialist verification.

## Required providers
The host refuses to initialize unless all of these are supplied by the authorized server runtime:

1. Google OIDC
   - approved OAuth Web client ID allowlist
   - real `google-auth-library` `OAuth2Client.verifyIdToken` (or injected reviewed equivalent)
   - browser Bearer value is a Google **ID token**, not an OAuth access token
2. Server-owned family membership provider
   - `lookupMemberships({provider:'GOOGLE_OIDC', subject})`
   - ACTIVE family membership and explicit learning-submit target grants only
3. Strong durable store
   - strong read metadata + conditional JSON write semantics
   - Google Drive is not the live state store
4. Server specialist evidence verifier
   - browser verification claims cannot self-promote to real evidence
5. Indexed activity resolver
   - trusted server-side `resolveIndexedEvidence(scope)`
6. Independent Index Owner verifier
   - required whenever governed F07 activity references are resolved
7. Explicit HTTPS browser Origin allowlist
   - no wildcard, no ambient-cookie authority

## Routes
- POST `/api/learning/evidence`
- POST `/api/learning/decision`
- OPTIONS for those exact routes only

## Security behavior
- Both routes share the same verified Google principal boundary.
- CORS allows only configured HTTPS origins.
- No bearer token, raw family registry, other members' state, internal storage keys, or full learner state is returned.
- Missing provider configuration prevents host creation.
- No real OAuth credential, secret, production membership database, production durable store, or deployment is included in this slice.

## Ready contract
Ready's production bootstrap must provide:
- `ReadyCentralAuthHost.currentSession()`: independently verified central session metadata.
- `ReadyCentralAuthHost.idToken()`: Google ID token for TAKY Bearer verification.
- configured HTTPS evidence and decision URLs.

Netlify Identity session/cookie authentication remains separate and is not accepted as the TAKY central bearer credential.

## Verification
The production-host test uses a TEST-ONLY Google ticket stub, loopback Node HTTP, LocalJsonStrongStore, explicit family membership fixture and required provider stubs. It verifies dual routes, CORS, Google subject authorization and zero-evidence HOLD. This is code wiring evidence, not real Google login or production deployment evidence.
