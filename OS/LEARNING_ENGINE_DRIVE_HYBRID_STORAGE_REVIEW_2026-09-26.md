# CENTRAL LEARNING ENGINE + GOOGLE DRIVE HYBRID STORAGE REVIEW — 2026-09-26

Status: IMPLEMENTABLE ARCHITECTURE CANDIDATE / NO PRODUCTION OR DEPLOY AUTHORIZATION.

## Direct user correction — do not alter existing approved ownership
**Learning Engine Core is not inside any PWA.** Ready & Set, Hide & Seek and Snap & Pop are client/interaction/verified-evidence adapters. A local PWA may have an offline outbox and limited presentation calculation; neither its JS bundle nor its local task score becomes the authoritative learner state, cross-app pedagogy, Award Ledger or Gem Wallet.

Authority inheritance (do not reopen CLOSED):
- `OS/LEARNING_ENGINE_CORE.md` and `CURRENT/LEARNING_ENGINE_VERIFICATION_CURRENT_2026-09-25.md`: independent Core, immutable verified evidence, state/decision/adaptive-plan intent, policy evaluation implemented. Current bounded OPEN includes hosted identity + Function endpoint, and held retention/BKT promotion. Ready is not the engine, and Learning Core cannot choose Planner calendar dates.
- Google Drive `C2S/MINING_INDEXING_LEARNING_ROLE_CONTRACT_2026-09-25_V1.json`: Mining gets sources; Indexing classifies/relates/retrieves; Learning decides their learning-context use. `INDEXING != LEARNING`.
- `OS/DRIVE_STORAGE_MAP.json`: existing TAKY single Drive root and PC-synced `TAKY_WORKSPACE`; GitHub canonical governance/code. No parallel root, duplicated Git tree under sync, or NotebookLM prerequisite.
- `CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json`: source Index V26 / Utilization V26 / 679 INDEX L1 as checked at this review. Query Index, escalate to selected Detail L2 and RAW only on demand, not full Drive corpus scanning for each learning request.

## Correct runtime architecture (logical deployment, not PWA bundling)

```text
Ready / Hide / Snap — PWA (interaction, local-first, pending outbox)
  -> authenticated CENTRAL API (server verifies family_id/member_id and source_app)
  -> canonical verification + immutable REAL_LEARNING_EVIDENCE_RECEIPT
  -> central durable learner event/state store
  -> TAKY LEARNING ENGINE CORE (replay/learner state/adaptive-plan intent)
      <- Indexing search/Detail pointer when reference evidence is required
      -> Learning decision intent (not schedule date, not Award Ledger)
  -> Ready Adapter -> Planner (only owner of actual date/time) -> PWA presentation

Approved achievement decision -> separate authorized atomic Badge Award Ledger
Explicit authorized family praise -> separate family Gift Journal / Gem Wallet consumer

Verified committed versioned exports -> Google Drive (secondary long-lived source/results,
evidence-provenance pointer, policy snapshots, encrypted backups, review/C2S/handoff)
```

A central API may technically be hosted as functions alongside a site or as a separate service; this does not make the Learning Engine part of its static PWA bundle. Code ownership/deployment artifacts stay versioned under TAKY and consumers receive contracts/adapters, not separate independent learner-model algorithms. The existing `LEARNING/transport/` authenticated provider-neutral resolver, durable evidence adapter and Netlify Blobs transport are reuse candidates; their actual hosted server-side identity/endpoint binding is still OPEN. No fresh standalone Learning Engine rewrite.

## Which data belongs where

| Data/event | Owner / authoritative runtime | Google Drive use | PWA use |
|---|---|---|---|
| Uploaded worksheets, references, source PDFs | Mining source provenance, Index L1/Detail L2 | existing Data/INBOX -> RAW -> INDEX/DETAIL; incremental | selected content only |
| Verified attempt/retrieval/production evidence | Central Learning evidence intake and committed receipt store | encrypted versioned archive, source/checkpoint metadata | local provisional outbox then ACK |
| Per-skill learner state, retention signal and adaptive plan intent | Central Learning Core | reviewed versioned policy/evaluation and encrypted replay snapshot | selected explained decision; offline last-known display marked stale |
| Planned task/date/assignment fact | Planner | scheduled exports and review records if useful | editable Planner projection with existing local-first rules |
| Achievement first/reaward/promotion | separate authoritative atomic Award Ledger | encrypted signed backup only | verified earned read projection |
| Family praise badge/gems and balances | separate Gift Journal / atomic Gem Wallet | encrypted audit/archive only | verified authorized transaction results |
| Source catalog / CURRENT / C2S / handoff | Indexing / owner-specific GitHub CURRENT | existing governed Drive source/result/reference routes | not a competing governance repository |

Drive's version history, folder rename or copied JSON file does not provide a transactional commit, unique award decision, member authorization or reliable balance by itself. Likewise a successful Google Drive file upload is not canonical promotion or a verified engine receipt.

## Existing Drive mapping — NO new folder created in this review

- Governed TAKY root: `OS/DRIVE_STORAGE_MAP.json` already identifies 00_ACTIVE / 10_PROJECTS / 20_REVIEWS_C2S / 80_HANDOFF / 90_ARCHIVE. Reuse destinations according to those roles; don't create a second TAKY root.
- Independently indexed Data corpus has an existing `Data` folder and `Data/INBOX`. Use the *current* Index pointer, not name matching or a full corpus reread.
- The already synchronized PC Google Drive Computer folder may host `TAKY_WORKSPACE` for durable local workspace snapshots, not Git repositories or high-churn private live transaction stores.
- Sensitive child's raw history needs a restricted/encrypted export lane, not a broadly shared Data or family-readable folder. Never place access/refresh tokens, signing keys, passwords or raw family identifiers in manifest filenames.

## Real incremental Drive pipeline

1. Initial source reconciliation: enumerate only selected existing governed folder scopes; record stable `file_id`, version/fingerprint, parent and authority. Use `changes.getStartPageToken` and `changes.list` for subsequent deltas, not repeated whole-account rescans.
2. When a Drive file changes, do not adopt its text automatically. Resolve file id -> provenance -> canonical source classification -> duplicate/version relation -> incremental Index L1/Detail L2 update -> C2S or domain handoff if applicable. A notification is only a **hint**; fetch the change feed for details.
3. Archive export goes the **other way**: after an actual central commit, construct `LEARNING/transport/drive-archive-route.js` manifest with immutable source checkpoint/digest and an opaque scope digest; encrypt sensitive payload; upload as a distinct versioned artifact; read back hash/metadata; then publish a pointer/receipt. Export errors cannot revoke or rewrite the committed original.
4. `CURRENT` remains namespace-specific logical authority and is promoted only after verified reconciliation. Preserve previous revisions and HOLD/REJECTED history; no auto full-index refresh, no raw source duplication.

Google Drive `appProperties` may help incremental catalog lookup by stable source id/namespace. It is metadata, not the authoritative learning state. `appDataFolder` is hidden from the end user and can be removed when the app is uninstalled; therefore it is **not** the default user-visible review/HISTORY/backup destination.

## Auth & operation choices (selection OPEN)

A. Hosted shared central service (continuous multi-device option): dedicated authenticated API, central durable event/transaction store, TAKY Core as versioned server artifact, Drive only archive/reference. Server-side identity (existing family/member resolver) and separate Drive OAuth scopes/refresh credentials; a ChatGPT Drive connector is NOT an automatic PWA Drive authorization. For the user's own Drive, use scoped OAuth and selected file/folder access; service account cannot own files in a personal My Drive by itself. Confirm region, quotas and possible billing before deployment.

B. Existing-PC local pilot (minimum extra infrastructure): use TAKY local endpoint + `TAKY_WORKSPACE` under the already-synced Drive for desktop folder; when PC is online, export/read referenced source and process verified pending events locally. While PC is off, PWA only queues evidence as PENDING; it must not claim centrally verified mastery/badge or immediate cross-device delivery. PC mirroring/sync != an always-on server and is not a multi-client atomic transaction system. This can validate the workflow without inventing a new paid service.

C. Drive-only live engine/badge ledger: REJECT as system architecture. File edits cannot replace server authorization, transactionality, robust signed replay, or private per-child results. Treat Drive as evidence source and archive, not the engine's runtime or multi-writer financial/reward journal.

Google Drive API quotas were revised effective May 1, 2026; treat API usage as metered/subject to current project limits and potential future charges. Never assert an unlimited/free API or use an experimental provider as production without explicit billing review. Netlify Functions and background/scheduled functions have execution constraints; use only as hosted execution adapters after exact release authorization.

## Implementation evidence and remaining OPEN

IMPLEMENTED CURRENT: independent Learning Core, local-controlled authenticated evidence processing and durable adapter, role contracts, Drive source/C2S map, Data V26 search projection, signed Badge history/calendar and nonproduction conditional CAS experiment. `LEARNING/transport/drive-archive-route.js` adds a **pure routing/manifest policy**, not actual Google API upload or real private archive encryption.

NO new Drive folders or files, OAuth consent, Netlify setup, production DB, PWA source release or deploy were performed by this architecture review.

NEXT OPEN, ordered:
1. Connect the existing server-side family/member Identity resolver to an authenticated **central Learning evidence endpoint**; keep app-specific verification and replay gates (current Core OPEN #3).
2. Choose one durable central receipt store that meets actually needed multi-writer semantics, preserving status and idempotency. Do not force experimental Badge CAS or SQL branch into production without selection and integration proof.
3. Bind Drive change-token incremental Intake to existing Indexing and a separately scoped archive writer, perform encrypt→upload→hash readback→receipt. No Drive file overwrite for live learner state.
4. Expose child-scoped, no-store learning/badge **read projections** to Ready/Snap/Hide, and distinguish pending local events from committed server decisions.
5. Verify offline retry, double submit, family/sibling scope, rollback/replay, Drive outage isolation, PC-off local pilot behavior, costs, and no unapproved images/rewards before explicit release gate.

## Official references checked 2026-09-26
- https://developers.google.com/workspace/drive/api/guides/manage-changes
- https://developers.google.com/workspace/drive/api/guides/push
- https://developers.google.com/workspace/drive/api/guides/properties
- https://developers.google.com/workspace/drive/api/guides/appdata
- https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- https://developers.google.com/workspace/drive/api/guides/limits
- https://developers.google.com/workspace/drive/api/guides/about-shareddrives
- https://support.google.com/drive/answer/13401938
- https://docs.netlify.com/build/functions/configuration/
