# CENTRAL LEARNING GOOGLE IDENTITY + NODE HTTP PILOT — 2026-09-26

## Why this slice
The user confirmed that the Learning Engine is a separate TAKY-owned service, not a bundle inside Ready, Hide, or Snap, and Google Drive is reference/index/archive rather than live state. The prior `central-learning-http-endpoint.js` could ingest locally with injected trusted callbacks but had no actual HTTP transport or Google subject-to-family mapping. This slice provides both reusable server adapters without activating a cloud runtime.

## Reuse rather than reimplementation
- Authoritative Core: `OS/LEARNING_ENGINE_CORE.md`; evaluated evidence, model, adaptive-plan intent remain there.
- Endpoint: `LEARNING/transport/central-learning-http-endpoint.js` from PR #157.
- Canonical verified-intake and durable ETag ACK remain unchanged.
- Drive's `drive-archive-route.js` and existing `OS/DRIVE_STORAGE_MAP.json` remain backup/reference routes; no personal Drive file used as live database.
- PWA pending outboxes stay clients; Planner alone assigns actual calendar dates.

## Newly implemented server adapters
`LEARNING/transport/google-learning-principal.js`:
1. Uses actual `google-auth-library`'s `OAuth2Client.verifyIdToken({idToken,audience})` through the `createFromGoogleAuthLibrary` method once installed/provisioned in a selected server runtime. It never simply base64-decodes a JWT. Validates accepted Google issuer, client ID audience and authorized presenter, token expiry, issue time, and Google `sub`.
2. Resolves `sub` against an injected **server-authoritative TAKY membership provider**. The Google email address, avatar, arbitrary role/name/permissions in the PWA, and the Google token alone are NOT enough to authorize a target child.
3. CHILD may submit own evidence only; PARENT gets only explicit server-granted child target IDs. FAMILY_ADULT (e.g., grandparent/guardian) with family-praise permission alone is not allowed to submit learning evidence for a child; requires separate `LEARNING_EVIDENCE_SUBMIT` permission and scoped target grant. Inactive/duplicate families fail closed.
4. Constructs the principal expected by the pre-existing family/member identity resolver. No raw Google ID token/email is returned in the principal or client ACK.
5. The Google Identity Services `credential` form-post login callback is a **different flow**: Google's official guidance requires CSRF protection for that cookie-based POST. The central evidence endpoint uses an explicit Bearer token and does not implicitly adopt cookies. A real user login/session exchange and sign-out/revocation model remain OPEN.

`LEARNING/transport/node-http-learning-bridge.js`:
- Real Node HTTP request/response handler for the existing POST `/api/learning/evidence`; accepts only explicitly configured HTTPS browser Origin(s), no wildcard or ambient cookies. Validated preflight; no CORS approval to other origins.
- Early and streamed 64 KiB request bound, JSON only, no-store/no-cache headers on all routes/errors, no logging of token or child data.
- Passes only method, path, headers and string body to the previously tested central endpoint; neither endpoint nor this bridge generates awards or writes Google Drive.
- Can be mounted on a separately approved server host; tests use `http.createServer` bound only to 127.0.0.1 with ephemeral port and `LocalJsonStrongStore`.

## Tests and limits
`google-node-central-integration.test.js` uses an explicitly TEST-ONLY Google ticket stub and server membership fixtures, and exercises real loopback HTTP, observation-only forged PWA exact-match, family/child/sibling authorization, changed email but stable Google `sub`, adult gift-only denial, expiry/issuer/audience checks, Origin and preflight, large body, and committed no-store ACK.

**A green test means the connection and security boundaries work with fixtures; it does not mean a real Google-signed ID token has been issued or verified in the user's account.** Production must install `google-auth-library`, configure approved OAuth Client IDs and actual issuer verifier, HTTPS ingress, a family membership/permission backend, rate limits/abuse controls, credential handling and retry rules, real server-owned answer/verifier sources, and selected central storage. No live OAuth credentials or secrets are written to GitHub or Google Drive.

## Cost and Drive boundary
No new paid service, Netlify function, Google Drive API call, OAuth consent, scope grant or deployment was created. This Node binding can run in a separate service or dedicated functions later; the ability to share a host with a PWA does not make the Learning Engine part of its static client bundle. If Google Drive exports are enabled later, they must be encrypted (where private), source-verified, versioned, hash-read-back and separately acknowledged; a failed archive upload must not invalidate or fabricate a learning receipt.

## Still OPEN, ordered
1. Provision approved real login/session flow and Google Auth Library + OAuth client IDs, then populate the server-owned family membership/grant provider.
2. Bind central route into an authorized hosted endpoint and durable atomic/conditional receipt store; confirm origin, quotas, region and permission boundaries.
3. Implement actual trusted specialist evidence verification from server-owned reference/parent rubric authority; browser claims alone remain observation only.
4. Connect each PWA's pending-outbox ACK to this server without cross-member data leakage; read back central Core learning decisions via a separately scoped endpoint.
5. Implement versioned encrypted Drive archive upload/readback and incremental Indexing changes feed in existing folders only, no duplicate workspace.
6. Keep real time-held-out retention and calibrated BKT promotion in HOLD. No Netlify deployment or Ready/Snap draft main merge in this slice.

Official Google ID-token validation guidance: https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
