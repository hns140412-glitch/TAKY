# TAKY SYNC CONTRACT V1

## Purpose
A shared persistence and synchronization rule for TAKY-family apps including Ready & Set, Hide & Seek, Snap & Pop, and SAVEY.

## Canonical principles
1. Local PWA storage is cache/queue, never silent authority over canonical data.
2. Every mutable record must have a stable identity.
3. Conflict detection must not rely on `updated_at` alone.
4. When available, compare all three signals:
   - stable record id
   - version/time metadata
   - canonical content fingerprint
5. If the remote canonical record changed since the local mutation base, do not silently overwrite it.
6. Conflicted mutations remain recoverable until explicit resolution.
7. Offline writes are idempotent through a stable mutation id.
8. Queue flush is serialized per app/session to prevent duplicate concurrent writes.
9. Successful mutations are removed only after canonical write confirmation.
10. Schema/header mismatch is a hard stop, not an auto-repair opportunity.

## Canonical fingerprint
- Fingerprint is calculated from the canonical record payload using deterministic key ordering.
- Volatile transport metadata must be excluded.
- If a canonical source does not expose `updated_at`, fingerprint comparison remains mandatory.
- A matching timestamp with a different fingerprint is still a conflict.

## Pull
`REMOTE CANONICAL -> SCHEMA VALIDATE -> NORMALIZE -> FINGERPRINT -> LOCAL CACHE`

## Offline mutation
Each queued mutation carries:
- mutation_id
- record_id
- canonical namespace/sheet/collection
- operation
- payload
- base version/time when present
- base fingerprint
- created_at
- retry_count

## Push
`QUEUE -> READ REMOTE -> ID/SCHEMA CHECK -> VERSION/FINGERPRINT CHECK -> WRITE -> READBACK VERIFY -> ACK`

Conflict outcomes:
- REMOTE_NEWER
- REMOTE_CHANGED
- ROW_MISSING
- SCHEMA_MISMATCH
- VALIDATION_FAILED

## User edits
Direct canonical-source edits by the authorized user are authoritative. Apps must absorb them on the next pull and must not restore stale cached values over them.

## Security
- API keys, OAuth refresh tokens, service-account secrets and provider secrets must not be bundled into PWAs.
- Secrets belong behind an approved server-side or TAKY-managed secret boundary.
- Sensitive write operations may require re-authentication/approval according to the app's security contract.

## Validation boundary
`CODED != CI_VERIFIED != RUNTIME_VERIFIED != DEVICE_VERIFIED != PRODUCTION_VERIFIED`

No deployment or production claim is implied by adoption of this contract.
