# TAKY LOCAL + GOOGLE DRIVE WORKSPACE

Status: REV_00 / ACTIVE OPERATIONAL PROFILE
Role: Define the local-first execution workspace backed by Google Drive for desktop while preserving GitHub and Drive authority boundaries.

## 0. Goal

Use a normal local filesystem for fast execution and let Google Drive for desktop continuously protect the durable working subset.

`LOCAL = EXECUTION SURFACE`
`GOOGLE DRIVE COMPUTER BACKUP = DURABLE MIRROR`
`GOOGLE DRIVE TAKY ROOT = DURABLE SOURCE / RESULT / REVIEW SURFACE`
`GITHUB = CODE / GOVERNANCE / VERSION AUTHORITY`

This profile does not make the Google Drive `Computers` view a second governance authority.

## 1. Recommended local layout

Choose one ordinary local parent that is NOT itself a Git repository.

```text
<TAKY_LOCAL_ROOT>/
├─ drive-sync/                 # select this folder in Google Drive for desktop
│  ├─ CURRENT/
│  ├─ INDEX/
│  ├─ C2S_WORK/
│  ├─ HANDOFF/
│  ├─ HISTORY/
│  └─ EXPORT/
├─ local-only/                 # never intentionally sync
│  ├─ cache/
│  ├─ temp/
│  ├─ extracted/
│  └─ renders/
└─ repos/                      # Git working trees; keep outside drive-sync
   ├─ TAKY/
   ├─ Ready-Set/
   ├─ Hide-Seek/
   └─ Snap-Pop/
```

Google Drive for desktop SHOULD back up only `<TAKY_LOCAL_ROOT>/drive-sync`.
Do not place `.git` working trees under `drive-sync`.

## 2. Atomic checkpoint path

For local execution, the preferred durable checkpoint root is:

`<TAKY_LOCAL_ROOT>/drive-sync`

The atomic checkpoint surface becomes:

`drive-sync/CURRENT/<namespace>/<task_id>.json`

with minimal immutable evidence under:

`drive-sync/HISTORY/CHECKPOINTS/<namespace>/<task_id>/...`

The repository checkpoint utility accepts an explicit state root so local execution can write directly to this synced surface.

## 3. Writer rule

One task CURRENT has one active writer at a time.

`ONE TASK CURRENT = ONE ACTIVE WRITER`

Google Drive sync is a mirror/transport layer, not a concurrent writer.

If another machine needs to resume:
1. allow Drive sync to finish;
2. hydrate/read the latest CURRENT;
3. verify the checkpoint;
4. only then assume active-writer ownership.

## 4. Durable Drive routing

The existing `OS/DRIVE_STORAGE_MAP.json` remains the durable Drive routing map for project source/result/review/Handoff material.

The local `drive-sync` tree is an execution-continuity mirror. It does not replace the established Drive TAKY root or create a new canonical governance root.

Promote material results from local execution to the mapped Drive project/review/Handoff destination when the owning workflow requires it.

## 5. What stays local-only

Do not sync disposable/high-churn material by default:
- caches;
- temporary conversions;
- extracted video frames;
- transient contact sheets;
- browser/runtime scratch;
- build products that can be regenerated.

This prevents needless sync churn and reduces conflict risk.

## 6. Git boundary

Git repositories belong under `repos/` or another non-synced local location.

Do not deliberately synchronize:
- `.git/objects`;
- Git lock files;
- worktree metadata;
- node/package caches merely because they sit beside source.

GitHub remains the authoritative version surface for code and governance.

## 7. Bootstrap

Repository utility:

`python ENFORCEMENT/local_drive_workspace.py init --root <TAKY_LOCAL_ROOT>`

Validation:

`python ENFORCEMENT/local_drive_workspace.py doctor --root <TAKY_LOCAL_ROOT>`

The utility writes `<TAKY_LOCAL_ROOT>/.taky-local-workspace.json` and creates the directory contract. It does not configure Google Drive for desktop itself; the user selects the generated `drive-sync` folder in Google Drive for desktop once.

## 8. Runtime environment

Optional environment variable:

`TAKY_STATE_ROOT=<TAKY_LOCAL_ROOT>/drive-sync`

When supplied to `ENFORCEMENT/execution_checkpoint.py`, CURRENT/HISTORY persistence uses that root instead of the repository root.

## 9. Claim boundary

TAKY cannot silently configure or inspect the user's desktop Google Drive client from hosted ChatGPT.

Repository implementation can:
- create/validate the folder contract when run locally;
- write/guard CURRENT in the configured synced state root;
- prevent common repo-inside-sync mistakes.

Google Drive desktop authentication, local folder selection and OS-level sync status remain platform/client responsibilities.

END
