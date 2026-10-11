# TAKY Portable AI — Antigravity-independent local runtime

Status: LOCAL FUNCTIONAL SLICE. It does not replace the existing TAKY2 authority kernel.

## Commands (PowerShell from D:\Git PWA\TAKY-2.0-ORCH)

    python -m TAKY2.portable_ai doctor
    python -m TAKY2.portable_ai submit --title "UI audit" --owner CODEX --scope "Review approved UI and capture evidence"
    python -m TAKY2.portable_ai list
    python -m TAKY2.portable_ai show TASK_ID
    python -m TAKY2.portable_ai evidence TASK_ID --file "D:\Git PWA\TAKY-2.0-ORCH\TAKY2\README.md"
    python -m TAKY2.portable_ai serve --port 8787

Browser: http://127.0.0.1:8787/

Default local task storage: ~/.taky/portable-ai (outside Git). A global --root DIRECTORY option allows isolated stores, useful for testing. TASK_ID is the hexadecimal ID returned by submit.

## What works
- doctor: offline/read-only census of Codex, Claude, Git, Node and Python executables; reports skill locations and MCP server names only; no AI calls or secrets.
- submit / list / show: durable task and status store with canonical JSON SHA-256 integrity checks and atomic writes.
- evidence: allowlisted filesystem intake, SHA-256, immutable copied evidence. State changes only to REVIEW_PENDING, never self-certifies VERIFIED.
- serve: localhost-only, read-only GET dashboard; HTML escaping, evidence hash verification, file-download isolation.
- execute: delegates EXCLUSIVELY to the existing TAKY2.orchestrator preflight/execute receipt-bound gates using approved plan and invocation JSON files located within the repository. Never executes arbitrary task text or a direct provider CLI. A successful exit is UNVERIFIED until separately reviewed. This route has NOT been exercised against a live provider.

External execution (explicit existing TAKY authority required):

    python -m TAKY2.portable_ai execute TASK_ID --plan-json "D:\Git PWA\TAKY-2.0-ORCH\TAKY2\plan.json" --invocation-json "D:\Git PWA\TAKY-2.0-ORCH\TAKY2\invocation.json"

Only use existing, valid action contracts; the sample filenames above are placeholders and are NOT created.

## Portability and safety
- Antigravity IDE, its workflows or account state are not runtime dependencies.
- TAKY remains top-level authority: KEY / CONTEXT / ROUTE / COST / DONE, Necessity within COST, user is final Key owner.
- User confirmation, approval, independent reviewer and deployed state are NOT synthesized by this module.
- No new API key, paid subscription, external connection, Git push/merge, or Netlify deploy.
- Never save secrets as evidence. No automatic retry or parallel mutation of a shared Git worktree.

## Capability parity — truthful scope
- Task manager / basic artifacts: available now in this local module.
- Skills: standard Agent Skills discovery only, actual consumption by Codex/Claude requires separate load test.
- MCP: names-only registry census, no new server or live external access.
- Claude/Codex AI agent execution: installed locally, existing TAKY2 receipt executor available, end-to-end integration not established by this module.
- Browser agent, editor autocomplete, parallel agent scheduler, video capture and true visual verification: NOT INCLUDED. Existing Playwright/browser and editor tools can be integrated behind the TAKY gates later; do not claim parity now.
- ChatGPT ordinary chat -> local bridge: authorized Remote Desktop Commander is available in this conversation; no native hands-free hosted ChatGPT event interception is claimed.

## Test
    python -m unittest TAKY2.test_portable_ai -v
    git diff --check

Local test PASS proves only the isolated features; it is NOT a production E2E or independent reviewer PASS.
