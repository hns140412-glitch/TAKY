# TAKY PC evidence observation — Draft candidate

Task: LOCAL-GROWTH-OBSERVATION-20260928. Exact starting main SHA: `8e78af8b77d1f3e132f05c99cd6b69a7f258a23e`.

## Purpose
Turn the existing PC and Drive-synced files into low-cost **change evidence** that can be routed to TAKY's EXISTING Mining / Indexing / Learning / Growth owners. Never instantiate independent engines in PowerShell. No raw source, private evidence, child-related personal records, whole index, or Source Vault snapshots are copied into GitHub. No canonical promotion or automatic acknowledgement.

Reuse:
- `MASTER/GROWTH_INTELLIGENCE_PROTOCOL.md` (outcome-driven, not more checking for its own sake)
- `ENFORCEMENT/reference_intake_router.py` (source-to-existing-owner route)
- `ENFORCEMENT/learning_evidence_gap_broker.py` (reference gap: Index first, Mining if insufficient; learner-performance gap: specialist evidence)
- `LEARNING/lifecycle/outcome-growth-feedback.js` (verified result vs observation signal)
- `OS/DRIVE_STORAGE_MAP.json`, `OS/LOCAL_DRIVE_WORKSPACE.md` (existing Drive/local storage boundaries)
- Draft PR #169 owns SOURCE VAULT incremental Notion handoff. This observer does not compete with it, acknowledge its queue, run Notion, or infer Mining/Indexing completion.
- Draft PR #170 owns continuity and Console; this candidate stays a separate Draft until integration is validated.

## Exact scope and first run
The operator supplies a local JSON configuration. All files listed must be owned by the user and paths explicitly known; **this is not whole-F Drive discovery**. Example shape (replace placeholders with verified sources, and store privately on the PC):
```json
{
  "schema": "TAKY_OBSERVATION_SCOPE_V1",
  "source_root": "F:/YOUR_VERIFIED_SOURCE_FOLDER",
  "sources": [
    {
      "source_id": "EXACT_STABLE_SOURCE_ID",
      "relative_path": "relative/file.json",
      "owner": "MINING",
      "kind": "SOURCE_RAW"
    }
  ]
}
```
Run after reviewed configuration and local installation:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\TAKY\Tools\TAKY-GROWTH.ps1" -ConfigPath "PATH_TO_PRIVATE_CONFIG.json" -OpenReport
```
First run yields FIRST_OBSERVATION, not "new source" or completed Mining. For next run, pass the exact last receipt using `-PreviousReceipt '.../OBSERVATION_RECEIPT.json'`. This does not automatically modify the previous receipt, scan more folders, write sources, or schedule jobs.

## Evidence and owner boundary
Explicit observed kinds: SOURCE_RAW, INDEX_OWNER_RECEIPT, LEARNING_VERIFIED_RECEIPT, OUTCOME_EVIDENCE and CURRENT_CHECKPOINT. These are *declared types*, not independently authenticated by this watcher. It emits route hints, not verified owner receipts. Content SHA proves local bytes only; it does not prove Google Drive sync freshness or semantic content quality. Scope identity/owner/type changes invalidate the previous comparison instead of generating a misleading delta.

Output outside the declared root: `OBSERVATION_RECEIPT.json`, `OBSERVATION_REPORT.md`. No automatic uploading/sharing/commit and no source file copying. OWNER must independently check source and receipt, validate provenance and approve the corresponding state transition. `REFERENCE != CANONICAL`, `MINED != INDEXED`, `INDEXED != LEARNED`.

## External research / choice boundaries
- DVC external-data pointers and remote stores illustrate separating Git metadata from bulk data; this does NOT authorize a DVC migration or treating a local hash as a remote version.
- GitHub Actions can validate deterministic tests with read-only token permissions; it cannot access the user's private local Drive without explicitly supplied authorization.
- Netlify build hooks and deploy previews are deployment side effects, not local evidence observers; HOLD applies. No Netlify SDK, hook, deploy or paid API call is used here.
- Community reports on DVC directory-manifest/cache integrity and Netlify prebuilt deploy bundling illustrate why success claims need exact source/operation proof, not command names.

## Acceptance
- first/unchanged/changed and missing separation, no false "new" claim;
- explicit bounded source list, safe relative path, no root traversal, previous scope mismatch fail-closed;
- metadata only, no source or repo writes;
- Windows/Ubuntu unit regression and Windows PowerShell parser gate;
- Windows PC actual path/config/Drive-sync runtime proof remains OPEN; do not deploy or merge.
