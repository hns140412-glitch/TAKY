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

## TAKY Console (opt-in)
`TAKY-CONSOLE.ps1` wraps the existing bridge. It does not talk to the OpenAI API, take control of ChatGPT, install a scheduled task, or automatically upload a report.

Direct invocation, with the Console and Bridge in the same local folder:
```powershell
& "$env:LOCALAPPDATA\TAKY\Tools\TAKY-CONSOLE.ps1" chat
& "$env:LOCALAPPDATA\TAKY\Tools\TAKY-CONSOLE.ps1" status
& "$env:LOCALAPPDATA\TAKY\Tools\TAKY-CONSOLE.ps1" report
& "$env:LOCALAPPDATA\TAKY\Tools\TAKY-CONSOLE.ps1" report -ReportAction copy
```
To enable `taky chat`, `taky status`, `taky report` as short commands, add this manually to the current PowerShell session (no profile mutation is performed by the script):
```powershell
function taky { & "$env:LOCALAPPDATA\TAKY\Tools\TAKY-CONSOLE.ps1" @args }
```
To persist it, the user must deliberately add the function to their PowerShell profile. Never replace an existing profile automatically. Do not paste sensitive output to chat without review. `report` merely opens the report folder; clipboard copy requires explicit `-ReportAction copy`.

No automatic version refresh is implemented. The candidate scripts are on Draft PR #170 and require PC installation and testing before promotion; an old local main may not contain them.

## Targeted continuity restoration candidate (new, not automatic chat sync)
`continuity_resume.py` reads the EXISTING `MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md` compact checkpoint shape from an explicitly configured synced state root. It verifies raw SHA-256 plus the canonical checkpoint hash, checks owner file existence/hash and local Git status, and optionally queries live origin/main using read-only `ls-remote`. It does not infer the latest CURRENT from filenames; explicit namespace/task IDs are required. It never writes CURRENT/HISTORY, mutates Git, scans whole conversation archives or promotes Handoff to authority.

Create a private JSON configuration at your chosen PC location (do NOT commit private paths or files to GitHub):
```json
{
  "state_root": "F:/YOUR_EXISTING_SYNCED_FOLDER/TAKY_WORKSPACE",
  "owners": {
    "DATA": {
      "repo": "D:/Git PWA/TAKY",
      "canonical_path": "MASTER/MASTER_LOGIC.md"
    }
  },
  "tasks": [
    {"namespace": "DATA", "task_id": "EXACT_EXISTING_TASK_ID"}
  ]
}
```
This is a SHAPE EXAMPLE, not a discovered existing state-root or task ID. Use the actual `TAKY_STATE_ROOT`, the exact existing namespace/task checkpoint and its correct canonical owner. The illustrated generic owner path is NOT a recommendation for the DATA task's actual owner. Optional `handoff_relative_path` on each task must be an explicitly verified path relative to the state root (not guessed by filename).

After installing both the updated `TAKY-CONSOLE.ps1` and `continuity_resume.py` in the same local Tools directory, run:
```powershell
taky resume -ConfigPath 'PATH_TO_REVIEWED_LOCAL_CONFIG.json'
```
By default it emits metadata and hashes only to a NEW local `RESUME-EVIDENCE-...` folder under Documents/TAKY-PC-Reports. Explicit opt-in:
```powershell
taky resume -ConfigPath 'PATH_TO_REVIEWED_LOCAL_CONFIG.json' -IncludeContext -LiveRemote
```
This includes compact CURRENT DONE/OPEN/NEXT/corrections in a private local JSON report and queries live main; review before sharing. A missing/mismatched checkpoint or owner makes status BLOCKED. Even a valid local hash yields only REVIEW_REQUIRED: owner authority, source recoverability, remote freshness and simulation are separate gates. There is NO automatic hosted chat ingestion, Google Drive sync-state verification, or canonical write.

Tests: `python -m unittest discover -s TOOLS/LOCAL_BRIDGE -p "continuity_resume_test.py" -v`; dedicated Windows/Ubuntu PR workflow also checks script parsing and a console help smoke test. GitHub CI is distinct from user's PC test.
