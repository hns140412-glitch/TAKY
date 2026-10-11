# TAKY AI Source Acquisition Runbook V1

Scope: public AI/reference acquisition only. This runbook does not authorize authenticated/private access.

## Procedure
1. Classify each source as public, connector/private, dynamic-shell, or inaccessible.
2. Public HTTP(S) acquisition must use per-item connect and total timeouts.
3. Batch work must isolate failures: one stalled source must not block the whole batch.
4. Preserve partial outcomes and per-source status before fallback.
5. For Notion public pages with shell-only HTML, use preserved local block snapshots first; public page-data recovery may be used only when it remains public.
6. Authenticated/private sources must not be bypassed. Route to an authorized connector or HOLD.
7. Do not learn from title-only or shell-only content.
8. Record source hash/provenance before Index/Learning.
9. Re-run only failed/thin items, not the entire successful batch.
10. A procedure change is complete only after a comparable replay passes.

## Default bounded capture profile
- workers: 4
- connect timeout: 5 seconds
- per-item total timeout: 12 seconds
- max body used for triage: 64 KiB
- preserve response status/final URL/content type
- no credentials/cookies unless explicitly authorized

## Acceptance
- batch completes despite individual failures,
- every requested source has a terminal per-item result,
- no private/authenticated bypass,
- successful items are not redundantly re-fetched during fallback.
