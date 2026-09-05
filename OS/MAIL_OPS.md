# TAKY WORK OS — MAIL OPS

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Owner: WORK OS
Purpose: Lightweight business mail history, evidence preservation, contact extraction and project-aware archiving.

## 1. Scope

MAIL OPS is an operational business memo / correspondence-history function. It is NOT, by default, architecture design-overview logic, submission/release logic, or GRAND MASTER governance.

Primary goals:
1. Review designated folders plus received and sent mail together.
2. Reconstruct correspondence as request → reply → follow-up → material transmission → response → closed/open.
3. Preserve a readable copy, recoverable original when available, original attachments, and minimal metadata.
4. Build searchable business history without fabricating missing content.
5. Extract only confirmed business contact information.

## 2. Evidence Rules

UNKNOWN remains UNKNOWN. UNVERIFIED remains UNVERIFIED.

Hard rules:
- ATTACHMENT NAME ≠ ATTACHMENT CONTENT EVIDENCE
- EXPIRED LINK ≠ SAVED ATTACHMENT
- EMAIL ADDRESS ≠ CONFIRMED NAME / TITLE
- AI PROJECT GUESS ≠ PROJECT ASSIGNMENT
- SUBJECT MATCH ≠ THREAD PROOF
- PDF RENDER ≠ ORIGINAL MESSAGE

If an attachment cannot be read, record only what is evidenced, e.g. `자료 송부 이력 확인 / 첨부내용 미확인`.

Attachment status vocabulary:
`AVAILABLE | DOWNLOADED | CONTENT_VERIFIED | EXPIRED_LINK | ACCESS_DENIED | MISSING | UNVERIFIED`

## 3. Thread Reconstruction

Thread association priority:
1. Message-ID
2. In-Reply-To
3. References
4. provider/connector Thread ID
5. normalized subject
6. sender/recipient + temporal/context similarity

Lower-confidence matching SHALL NOT silently override higher-confidence evidence. Ambiguous association remains UNVERIFIED or requires confirmation.

Recommended business-flow state:
`REQUEST → RESPONSE → FOLLOW_UP → MATERIAL_SENT → RE_RESPONSE → CLOSED / OPEN`

## 4. Project Assignment

Priority:
1. Explicit user assignment → VERIFIED
2. Existing verified thread inheritance → AUTO_VERIFIED
3. Known counterpart + subject/body/context → SUGGESTED
4. Ambiguous → UNCLASSIFIED

A SUGGESTED classification SHALL NOT be treated as a verified project assignment without the configured confidence/approval gate.

## 5. Archive Structure

Default staging-first structure:

```text
MAIL_ARCHIVE
├─ SENT
│  └─ PROJECT
│     └─ YYYY-MM-DD_HHMM_subject-summary
│        ├─ EMAIL.eml
│        ├─ EMAIL.pdf
│        ├─ ATTACHMENTS/
│        └─ mail_meta.json
└─ RECEIVED
   └─ PROJECT
      └─ YYYY-MM-DD_HHMM_subject-summary
         ├─ EMAIL.eml
         ├─ EMAIL.pdf
         ├─ ATTACHMENTS/
         └─ mail_meta.json
```

If the connector cannot provide EML/raw source, mark original-message preservation `UNAVAILABLE/UNVERIFIED`; do not synthesize an EML and call it original.

Roles:
- `EMAIL.eml` = recoverable original message when actually obtainable.
- `EMAIL.pdf` = human-readable rendered copy.
- `ATTACHMENTS/` = original-format attachments when obtainable.
- `mail_meta.json` = searchable metadata and validation state.

Staging-first is preferred for initial implementation:
`mail detected → classify/suggest project → create staging archive → validate → user/approved policy confirms → move to project archive`

## 6. Minimum Mail Index

Recommended minimum fields:
`DATE | DIRECTION | PROJECT_ID | COMPANY | PERSON | SUBJECT | SUMMARY | ATTACHMENT_COUNT | REPLY_STATUS | MESSAGE_ID | THREAD_ID | ARCHIVE_PATH | ARCHIVE_STATUS`

Extended correspondence record when useful:
`COMM_ID | PROJECT_ID | THREAD_ID | ISSUE_ID | DATE | FROM | TO_CC | DIRECTION | SUBJECT | SUMMARY | REQUEST | OUR_RESPONSE | COUNTERPART_RESPONSE | DECISION | ACTION_ITEM | DUE_DATE | ATTACHMENT_NAME | ATTACHMENT_STATUS | STATUS`

Do not force every mail into the extended schema when the lightweight index is sufficient.

## 7. Contact Extraction

Only confirmed business information from body/signature/business card or other evidenced source:
`PERSON_ID | NAME | COMPANY | DEPARTMENT | TITLE | ROLE | EMAIL | WORK_PHONE | SOURCE | VERIFIED_DATE | PROJECT_ID | ACTIVE_OLD`

Do not infer name/title solely from an email address. Preserve historical changes instead of silently overwriting company/title history.

## 8. Duplicate / Idempotency Control

Prefer Message-ID as the primary duplicate key. When unavailable, use a composite candidate key such as provider id + account + date + normalized subject + sender, marked with confidence.

Re-running an archive job SHALL NOT create a second archive for an already-verified message unless the operation is an explicit revision/recovery.

## 9. Automation / Approval

Initial policy: semi-automatic before fully automatic.

Safe progression:
`MANUAL PROJECT DESIGNATION → THREAD INHERITANCE → AI SUGGESTION → CONFIDENCE GATE → OPTIONAL AUTO-ARCHIVE`

External sending, deletion, destructive moves, or high-impact actions inherit GRAND MASTER Human Approval policy.

Monitoring frequency/trigger policy is separate from connection state and must be explicitly designed before enabling frequent automatic checking.

## 10. Current Connector State

Verified 2026-09-05 KST:
- NATE account `soma17@nate.com`
- Custom IMAP host: `imap.nate.com`
- status: ACTIVE
- onboarding: COMPLETED
- syncing: TRUE
- read/send/organize: enabled

This is runtime evidence and may become stale. Recheck before relying on it.

## 11. Implementation Gates

Before E2E PASS, validate at least:
- received message archive
- sent message archive
- reply-chain reconstruction
- duplicate rerun
- attachment available
- attachment inaccessible/expired
- PDF rendering
- EML/raw preservation capability
- project assignment inheritance
- ambiguous project handling
- contact extraction with/without signature
- staging → approved destination move
- rollback/recovery
- searchable index consistency

Status at creation:
`LOGIC PASS / IMPLEMENTATION NOT YET VALIDATED / E2E NOT YET PASS`

## 12. Revision Rule

`/반영 ≠ REV increment`.
Remain REV_00 until explicit user finalization under TAKY Revision Governance.
