# TAKY2 — ACCOUNT TARGET BINDING EVIDENCE — 2026-10-06

Status: OPEN / FAIL-CLOSED
Scope: HNS alias -> authenticated central family/session identity

## VERIFIED EVIDENCE

1. Google Drive connector authenticated profile
- profile email: hns140412@gmail.com
- profile id: 102814704779691664323
- profile name: soma “Taky”
- evidence source: provider-authenticated Google Drive connector read on 2026-10-06

2. HNS storage authority documents in the authenticated HNS Drive
- FINAL_STORAGE_NAMESPACE_REGISTRY
  - Drive file id: 1r1Cx9hdFqMTxPgYtCmIP0p6N4pNdfhTjsnPEgML3hqE
  - states HNS Drive owns internal master data
  - repository pointer: hns140412-glitch/TAKY
- FINAL_DRIVE_STORAGE_MAP
  - Drive file id: 1pW6tp46AZKNrA8zlenZrw1S04tS7uKSLZFQb9qcDh1M
  - states HNS Drive = INTERNAL_MASTER_DATA_AND_LONG_TERM_SOURCE

3. Central family-auth runtime implementation exists in Ready & Set
- Ready local HEAD observed: 16026f4
- taky-google-account-auth-v1.js obtains Google ID token and POSTs /api/family/session
- taky-family-auth-runtime-v1.js selects family_id and exposes self_member_id / authorized_member_ids from the server session
- public config does not statically bind preferredFamilyId
- family/session identity is therefore runtime-derived, not inferable from HNS naming

4. TAKY2 current runtime
- runtime.account_attestation = null
- authority digest remains 3a3eff76549ad5262f46

## GAP

No authority-owned explicit mapping was found that binds:
HNS
-> GOOGLE_OIDC_VERIFIED principal_id
-> family_id
-> self_member_id

The Google Drive profile proves the HNS Google account connection, but it does NOT by itself prove the central family/session subject or membership identity. The connector profile id MUST NOT be silently treated as Google OIDC principal_id.

## ENFORCEMENT RESULT

- Do not invent alias equivalence.
- Do not write an executable ACCOUNT TARGET BINDING yet.
- External writes that require HNS account attestation remain fail-closed.
- Actual attestation targeted E2E is NOT truthfully runnable until a real /api/family/session response for the HNS account is available to TAKY.
- Claude/Codex calls are not necessary at this stage because no executable binding/code change is authorized by the evidence.

## NEXT SAFE ROUTE

When TAKY can directly observe an authenticated HNS /api/family/session response, bind the stable provider principal and selected family/member identity to HNS, then run:
actual attestation targeted E2E -> CODEX verification if SUCCESS is claimed -> CLAUDE independent review if STRONG tier -> final regression.

USER != DEBUGGER. Do not ask the user to copy tokens, IDs, or debug the auth session.
