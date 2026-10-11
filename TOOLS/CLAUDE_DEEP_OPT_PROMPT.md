[TAKY DEEP OPTIMIZATION CYCLE]
You are reviewing and improving the existing local Notion collector and its post-collector pipeline.

Working directories:
- D:\Git PWA\TAKY
- D:\Git PWA\TAKY-SOURCE-VAULT

Read these authorities first:
- D:\Git PWA\TAKY\CLAUDE.md
- D:\Git PWA\TAKY\TAKY.md
- D:\Git PWA\TAKY\C2S\REFERENCE_INTAKE_NEW_CHAT_START_2026-10-02_LATEST.md
- D:\Git PWA\TAKY\C2S\REFERENCE_INTAKE_END_TO_END_CURRENT_2026-10-02.json

Target:
- Existing local Notion collector
- Scheduled/manual runners
- New RUN_TAKY_POST_COLLECT_PIPELINE.ps1 bridge
- Mining -> Indexing -> Learning/Domain handoff

Required workflow:
1. COMPARE current implementation against robust local incremental collector patterns and the TAKY contract.
2. REVIEW all collector, scheduler, recovery, queue, generation, handoff, index/learning bridge logic.
3. IDENTIFY concrete gaps by severity.
4. BACK UP every file before modifying it.
5. IMPROVE and OPTIMIZE locally where safe and authorized.
6. ERROR VERIFY: syntax, runtime assumptions, file-lock/EPERM handling, stale tmp, missing/deleted/moved pages, retries/backoff, pagination stability, duplicate/idempotency, overlap/run lock, stale fixed queue, generation pointer, signed URL persistence, permission failure vs source absence, legacy Notion write paths.
7. SELF VERIFY your own changes against the original findings and TAKY authority.
8. REGRESSION VERIFY existing tests + add focused tests where needed.
9. Verify post-collector flow: successful collector -> delta detection -> Mining -> Indexing -> Learning/Domain -> regression; no-change -> no Claude call; collector failure -> downstream blocked.
10. Produce final evidence with changed files, backups, tests run, exact PASS/FAIL/HOLD.

Hard gates:
- DO NOT PATCH/WRITE TO NOTION.
- DO NOT run legacy write-capable source_vault/sync scripts.
- DO NOT deploy, push, merge, release, or modify remote state.
- DO NOT use paid/provider API keys.
- Claude subscription/OAuth only.
- CURRENT/Master/Canonical promotion remains HOLD.
- Preserve USER != DEBUGGER.
- Do not silently weaken fail-closed guards.
- Prefer minimal safe diffs.
- If a change could risk data loss, do not apply it; report HOLD instead.
- Do not treat access failure as source absence.

Specific previously observed issues that MUST be re-checked, not blindly accepted:
- disappeared/deleted/moved/access-revoked pages not tracked
- fixed INCREMENTAL_QUEUE stale/EPERM split-brain
- no cross manual/scheduled run lock
- no consumer ACK ledger / queue never drains
- signed S3 URLs persisted in raw block snapshots
- stale .tmp files
- pagination sort/dedup/fallback masking
- legacy write-capable paths remain reachable
- scheduled task naming/registration drift
- post-collector pipeline trigger correctness

At end print:
TAKY_CLAUDE_COLLECTOR_OPTIMIZATION: PASS
or
TAKY_CLAUDE_COLLECTOR_OPTIMIZATION: HOLD <reason>
and include:
- CHANGED FILES
- BACKUPS
- TESTS
- REGRESSION
- REMAINING OPEN
- SAFE TO RUN: YES/NO/CONDITIONAL