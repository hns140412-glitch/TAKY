# TAKY SESSION DELTA LOG

Status: APPEND-ONLY OPERATIONAL HISTORY
Purpose: preserve material per-session changes without reconstructing or rewriting prior conversation history.

Rules:
- append new session deltas; do not rewrite earlier entries except explicit correction with trace;
- record only material state changes, decisions, corrections, open/closed issues, canonical writes, validation evidence and unresolved blockers;
- conversation prose is not durable state until reflected here or in another canonical owner;
- each entry SHOULD include session/date, source conversation identifier if available, canonical files changed, decisions, unresolved items, evidence/commit refs, and next verified resume point;
- later correction SHALL reference the prior entry rather than silently replacing it.

---

## 2026-09-14 — enforcement architecture correction

Delta:
- Added `STATE.md` as canonical current operational state surface subordinate to GRAND MASTER.
- New-session resume must begin from actual `STATE.md` retrieval/verification, not conversational summary reconstruction.
- `resume_simulation_passed` naked boolean is no longer sufficient evidence by policy; validator hardening required.
- Handoff is treated as a verifiable artifact, not a summary product.
- Session consolidation model changed from post-hoc whole-history synthesis to per-session material delta append.

Open root issues:
- trusted role/action/execution-owner source independent from executor;
- mandatory preflight interception on actual hosted ChatGPT native tool dispatch;
- progress authority integration;
- machine-verifiable resume evidence.

Related issue: TAKY #2 `P0 — Trusted routing authority + runtime preflight interception`.

---

## 2026-09-14 — Work/Codex usage-aware routing correction

Trigger:
- User reported that a monolithic Work assignment exhausted the available short-window usage allowance, making the prior recommendation to use Work as an always-on orchestration layer operationally unsuitable.

Decision:
- Work and Codex are scarce execution resources and require a usage-impact review before routing.
- Ordinary Chat with available connectors/tools is the default orchestration surface when it can perform the task.
- Work is removed as the default always-on development orchestrator.
- Codex should receive narrow implementation TASK CONTRACTS after orchestration/scope/acceptance work is done outside Codex where practical.
- Large whole-history/chat/Drive/GitHub sweeps default to `VERY_HIGH` usage risk.
- `HIGH`/`VERY_HIGH` tasks must not be launched monolithically without usage-risk disclosure and a cheaper/smaller routing attempt first.
- If remaining allowance cannot be directly observed, TAKY must say it is unknown rather than assume capacity.

Current routing consequence:
- Until fresh allowance evidence is available, avoid additional Work/Codex execution and continue through ordinary Chat where possible.

Canonical change:
- `STATE.md` updated with `Work / Codex resource-routing policy`.

Evidence:
- STATE update commit: `8af6c6b849d975b1548b43f36107e6afbccfa2b6`.

Claim boundary:
- `CAPABILITY AVAILABLE != RESOURCE-AFFORDABLE`
- `WORK/CODEX AVAILABLE != WORK/CODEX SHOULD BE USED`
