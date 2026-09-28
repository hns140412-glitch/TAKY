# TAKY Local Bridge (Draft, READ ONLY)

Task ID: LOCAL-BRIDGE-20260928. Base main SHA verified before work: `8e78af8b77d1f3e132f05c99cd6b69a7f258a23e`.

## Objective and scope
Register the user-PC-tested v0.2 Git/Drive metadata inventory as a small, separately versioned script; v0.3 normalizes empty error output to valid JSON `[]` and adds opt-in `-OpenReport`. This is a PC inspection surface, **not** a new authority, Mining, Indexing, Source Vault intake, a background agent, or an automatic ChatGPT control channel.

Protect Git repositories, working trees, Drive files, pre-existing CURRENT/HANDOFF, approval state and WORK-OS HOLD. No fetch, pull, checkout, merge, reset, push, deletion, script installation, scheduled task, Drive sync, credential collection or Netlify invocation. All output goes outside repositories under the user's Documents/TAKY-PC-Reports by default.

## Existing role reuse / no duplication
- `OS/LOCAL_DRIVE_WORKSPACE.md` and `ENFORCEMENT/local_drive_workspace.py` already govern the durable local/Drive workspace. The bridge DOES NOT initialize or change it.
- `OS/DRIVE_STORAGE_MAP.json` remains the destination map.
- Draft PR #169 owns SOURCE VAULT -> TAKY source handoff, snapshots and acquisition receipts. The bridge neither consumes nor acknowledges queues.
- GitHub is code/governance/version authority, Drive is permitted durable source/result storage, local PowerShell is a read-only execution surface, ChatGPT may inspect explicitly shared reports. A mount check does not prove Drive sync freshness.

## Run from Windows Terminal / PowerShell 5.1+
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File 'D:\Git PWA\TAKY\TOOLS\LOCAL_BRIDGE\TAKY-LOCAL-BRIDGE.ps1' -Root 'D:\Git PWA' -DriveRoot 'F:\' -OpenReport
```
This example path is valid only **after** this Draft is explicitly made available locally. The user's local TAKY main was 515 commits behind the remote at inspection time, so do not assume the file exists in the old local main and DO NOT auto-pull or switch branches to obtain it. Use the approved staged file or a separate review worktree after checking for current changes.

Expected files: `CHATGPT_REPORT.md`, `REPOSITORIES.csv`, `DRIVE_INVENTORY.json`, `ERRORS.json`. Reports may contain private paths and remote URLs; do not auto-commit, auto-upload or publish them. In particular, private SOURCE VAULT contents never go to GitHub.

## Acceptance / verification
- Existing v0.2 user PC evidence: 7 repositories, mounted F:, zero reported issues, ZIP reports attached in chat. This is **not** Windows proof for v0.3.
- v0.3: validate PowerShell parse/run locally, 7 repository values not `System.Object[]`, `ERRORS.json` parses as JSON array even with 0 issues, compare live server main only when authentication permits, reports outside repository, `-SkipRemote` works, opening report folder is opt-in.
- Existing working branches and WORK-OS dirty state remain unchanged after local test.
- Any versioned promotion to main requires TAKY review and explicit human approval. PR stays DRAFT; no Netlify or production deploy.

## Known limits
`AheadOfTracking` and `BehindTracking` are local tracking-ref comparisons, not server-side main divergence. Drive inventory is top-level metadata, not content verification. Scheduled automation and automatic ChatGPT reads are not delivered by this script.
