# TAKY2 — ACCOUNT TARGET BINDING EVIDENCE — 2026-10-06

Status: IMPLEMENTATION CLOSED / REAL FIRST-LOGIN RUNTIME E2E OPEN
Scope: HNS logical target alias -> first verified central family/session identity

## VERIFIED AUTHORITY EVIDENCE

1. Google Drive connector authenticated HNS profile
- profile email: hns140412@gmail.com
- profile id: 102814704779691664323
- profile name: soma “Taky”
- this proves the connected HNS Google Drive account only
- Drive profile id MUST NOT be inferred as the Google OIDC principal_id

2. HNS storage authority documents
- FINAL_STORAGE_NAMESPACE_REGISTRY
  - Drive file id: 1r1Cx9hdFqMTxPgYtCmIP0p6N4pNdfhTjsnPEgML3hqE
  - HNS Drive owns internal master data
- FINAL_DRIVE_STORAGE_MAP
  - Drive file id: 1pW6tp46AZKNrA8zlenZrw1S04tS7uKSLZFQb9qcDh1M
  - HNS Drive = INTERNAL_MASTER_DATA_AND_LONG_TERM_SOURCE

3. Existing Ready & Set authentication path
- observed Ready local HEAD: 16026f4
- taky-google-account-auth-v1.js obtains Google ID token and POSTs /api/family/session
- taky-family-auth-runtime-v1.js receives server-authorized family_id, self_member_id and authorized_member_ids
- family/session identity is runtime-derived rather than safely inferable from the HNS label

## DECISION

A static pre-registration table such as:
HNS -> hard-coded family_id/member_id
is NOT required.

The correct authority path is:
USER_STATED target alias HNS
-> actual Google sign-in during use
-> verifier-approved /api/family/session response
-> FIRST_AUTH_RUNTIME binding
-> reuse the stable bound identity on later sessions

## IMPLEMENTED ENFORCEMENT

bind_account_attestation now requires:
- account
- authenticated=true
- source
- evidence_ref
- session_id
- identity_provider
- principal_id
- family_id
- self_member_id
- trusted verifier callback + verifier_id

On first verified authentication:
- account must equal USER-authorized HNS
- source must equal `central-family-session`
- identity_provider must equal `GOOGLE_OIDC_VERIFIED`
- account/identity/source/evidence/session values are canonicalized before storage
- account/principal/member cannot self-verify, including case/whitespace variants
- stable identity is stored in runtime
- binding_mode = FIRST_AUTH_RUNTIME
- first_bound_evidence_ref and first_bound_session_id are anchored

On later authentication:
- same stable identity may refresh only evidence_ref/session_id
- first-binding anchors remain unchanged
- source and verifier remain unchanged
- different principal_id, family_id, self_member_id, provider, source or verifier fails closed
- legacy/incomplete/unverified existing bindings are never silently promoted
- logical account alias cannot silently change

State-store persistence additionally enforces:
- persisted first-auth binding cannot be cleared
- identity/source/verifier/first anchors are immutable
- evidence_ref/session_id may refresh only on the same bound identity
- malformed/noncanonical/self-verified bindings are rejected before save
- lock + CAS + HMAC + external anchor remain active

KEY Gate external-write enforcement independently requires:
- FIRST_AUTH_RUNTIME binding mode
- trusted central-family-session source
- GOOGLE_OIDC_VERIFIED identity provider
- principal_id + family_id + self_member_id
- first binding evidence/session anchors
- canonical ordinary account attestation evidence fields
- no account/principal/member self-verification

Before the first verified login, external write remains fail-closed.
Current persisted runtime remains `account_attestation: null`, so no legacy migration is required before the real first login.

## TEST EVIDENCE

Regression: 98/98 PASS

Coverage includes:
- stable identity fields are mandatory
- exact trusted source/provider are mandatory
- first verified auth binds HNS runtime identity
- same identity can refresh evidence/session without rebinding
- identity/provider/source/verifier drift cannot silently replace the bound identity
- legacy/incomplete/unverified records cannot silently promote
- persisted binding cannot be cleared or reset through save_runtime
- direct persistence cannot bypass self-verification checks
- whitespace and case variants cannot bypass self-verification
- noncanonical evidence/session fields fail closed
- KEY external-write denial paths cover missing binding metadata, wrong source/provider, self-verification and noncanonical evidence
- targeted E2E: null attestation -> first-auth runtime bind -> authorized external-write preflight

py_compile: PASS
git diff --check: PASS

Review history:
- Codex identified legacy/incomplete promotion, persistence self-verification and whitespace bypass risks; each was remediated and regression-tested.
- Claude identified reset/rebind monotonicity, source/verifier immutability and source/provider pinning risks; each was remediated and regression-tested.
- final post-hardening CLI re-runs were blocked only by Codex/Claude usage-session limits, not by a code/test failure; no retry was made under the cost/necessity policy.

## REMAINING OPEN — RUNTIME ONLY

REAL HNS FIRST-AUTH SESSION / DEVICE E2E

This is intentionally deferred until actual use. No user debugging step is needed.
When the user signs in normally, TAKY should consume the verified /api/family/session response, create the first runtime binding, run the targeted preflight/runtime evidence check, and then perform final regression.

USER != DEBUGGER.
