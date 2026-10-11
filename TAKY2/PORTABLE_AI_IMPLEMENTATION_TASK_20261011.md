# TAKY portable AI implementation contract — 2026-10-11

USER INTENT: Implement and secure a TAKY-governed AI system independent of Google Antigravity IDE; retain its useful capabilities through standards-based local tooling. This is USER-EXPLICIT work. Not permission for paid APIs, deployment, push or broad refactor.

AUTHORITY/BASE:
- repo D:\Git PWA\TAKY-2.0-ORCH branch taky-2.0-orchestrator-2026-10-05 HEAD e6bb5fa18152f1ca877c5f21e11450309f31bb9b (verify before write).
- read AGENTS.md, STATE.md relevant passages, TAKY2/README.md and TAKY2/orchestrator.py preflight/execute entry points. Current canon: V2 and SHEPHERDING, 5 gates KEY CONTEXT ROUTE COST DONE, Necessity inside COST; ROLE!=AGENT. Existing dirty files absolutely preserve.
- TAKY orchestrates; you are the bounded code implementer. No status promotion to PASS without evidence.

IMPLEMENTATION SCOPE: only add a small new, dependency-free Python standard library module under TAKY2/portable_ai/ + focused unit tests TAKY2/test_portable_ai.py + concise TAKY2/PORTABLE_AI.md and one skill under .agents/skills/taky-portable-ai/SKILL.md. Do not edit canonical rules/runtime/authority or existing modules unless essential and explicitly justified; don't add new package managers.

Produce a REAL offline-operational first slice:
1. python -m TAKY2.portable_ai doctor : read-only capability census for git/codex/claude/node/python, workspace paths, portable skills and MCP presence (do not print secret tokens). All paths OS-portable and scoped to repository.
2. python -m TAKY2.portable_ai submit --title ... --owner CODEX|CLAUDE --scope ... creates uniquely identified durable task with small JSON manifest, UTC timestamps, SHA256 integrity checksum and task status; safe atomic persistence under configurable local non-git work directory with no hardcoded Windows paths. Permit CLI --root <path> for tests. No arbitrary shell strings or unsafe user-supplied paths/HTML.
3. python -m TAKY2.portable_ai list / show / evidence <task-id> --file ... : artifacts/manifest through allowlisted workspace boundaries with immutable evidence attachment copy + sha256 and relative refs. State differentiates SUBMITTED, EVIDENCE_RECORDED, REVIEW_PENDING, VERIFIED only if independently attestable; DO NOT permit self-declared verified or DONE. If verification not implemented leave REVIEW_PENDING/UNVERIFIED.
4. python -m TAKY2.portable_ai serve [--port 8787]: local 127.0.0.1 ONLY, GET-only clear simple browser dashboard showing tasks, statuses, evidence links/sha256, no mutation over HTTP, escape all HTML, no external CDN. Must not expose secrets, hidden directories, arbitrary files, or be network accessible.
5. python -m TAKY2.portable_ai execute --plan-json ... --invocation-json ... --task-id ... : NEVER execute arbitrary shell or direct Codex/Claude. Use existing TAKY2.orchestrator preflight/execute receipt-bound command sequence ONLY by delegated subprocess, with no automatic retry, no config/authority modification. Prefer an OPTIONAL guarded bridge: fail closed when not explicitly bound/authorized; if safe binding is too complex, provide an explicit BLOCKED/UNIMPLEMENTED execution state and don't advertise executing tasks as successful.
6. Standard SKILL.md with progressive disclosure, cross-runner local usage, never claims IDE-specific support; no forced install or symlink changes.
7. Tests focus durability/atomicity, path traversal, HTML injection, localhost-only dashboard, fail-closed execute, no unauthorized status elevation. Run focused tests & git diff --check. Leave existing dirty files untouched.

NOTE: User wants functional system, not merely plans. Build robust runnable CLI + dashboard now. No Git commit/push/merge/deploy, no paid provider invocation other than this single Codex work session, no user setup questions, never alter device global defaults. Report exact commands and outcomes. If needed decompose within these files, prioritize working task/evidence/dashboard over feature promises.
