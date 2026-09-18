# 2026-09-19 — TAKY × NotebookLM Conversation Recovery Pipeline

Status: CANONICAL CHANGE RECORD

## Trigger
User approved proceeding with NotebookLM integration for original-conversation/context recovery under TAKY C2S.

## Drive implementation
Created logical recovery hub:
`TAKY-WORK-OS / SOURCE_ARCHIVE / NOTEBOOKLM_RECOVERY`
with Source Registry, Raw Source Packs, NotebookLM Working, NotebookLM Output, TAKY C2S Review, Accepted Backfill and Unverified Source layers.

Created:
- `TAKY_NOTEBOOKLM_RECOVERY_CONTROL`
- `TAKY_NOTEBOOKLM_SOURCE_REGISTRY_20260919`
- Pilot working folder `PILOT_01_TAKY_CORE`
- `PILOT_01_TAKY_CORE_NOTEBOOKLM_PROMPT`.

## Security finding
Inspection of representative 6aa* saved HTML share-page sources showed that page files can contain large non-conversation application/session/bootstrap material. Therefore 6aa* HTML is preserved as evidence but is not direct NotebookLM input. It is classified `SECURITY_HOLD / SANITIZE_REQUIRED` until a transcript-only sanitized derivative is verified.

## Canonical delta
- Added TKY-NBLM-001 NotebookLM Conversation Recovery Protocol.
- Added machine-readable NotebookLM source schema and validator.
- Added CI PASS/expected-FAIL fixtures for source-security and authority boundaries.
- NotebookLM output is locked to `REFERENCE_ONLY / EVIDENCE_ASSIST` until raw-source recheck + C2S disposition.
- Duplicate archived copies are not counted as independent evidence.

## Runtime boundary
No dedicated NotebookLM plugin was available in the current plugin directory check. Current consumer flow therefore uses Google Drive as the interchange surface and leaves notebook creation/source selection as a human UI step.
Hosted/API automation may be added later if a trusted supported NotebookLM/Notebook Enterprise integration is available and authorized.

END
