# TAKY 2.0 — Claude Code activation (noncanonical)

This file activates existing TAKY governance for work within this repository. It is not an authority owner and must not redefine rules.

## Before any implementation
1. Respect the user's current instruction and read `D:\Git PWA\TAKY\TAKY.md`.
2. Read `D:\Git PWA\TAKY\MASTER\AI_COLLABORATION_PROTOCOL.md` for current execution roles. Claude Code is the primary code executor when an AI coding route is needed and available; Codex is independent verification or justified fallback, with usage and approval gates.
3. Read local `AGENTS.md`, actual Git HEAD/branch/worktree, relevant TAKY authority and target acceptance criteria.
4. Read `D:\Git PWA\TAKY\OS\SAVEY_AI_ECONOMY.md` for cost decisions; do not silently invoke provider API-key or metered fallbacks.
5. Load only task-relevant skills from `.claude/skills/`. Currently these are hash-verified physical copies of TAKY-owned portable skills (22 consumers), not necessarily junctions; existing checked links are also supported. File presence does not prove live runtime skill activation.
6. Read the same cross-executor derived context as Codex: `F:\내 드라이브\TAKY\20_PLATFORM\03_COMMON\03_HANDOFF\TAKY_ANTIGRAVITY_SHARED_AGENT_CONTEXT_CANDIDATE_20261012.json`. Verify its live source hashes with `python "D:\Git PWA\TAKY\TOOLS\TAKY_SHARED_AGENT_CONTEXT_PROJECTION_CANDIDATE.py" --check` before relying on it. It is NONCANONICAL, not an instruction to consume unread events or claim ACK; live canonical owners always prevail.

## Preserve and verify
- The existing project's dirty files and sessions are protected. No reset/checkout/clean/stash-all, unsolicited push, merge, publish, deployment or paid API.
- Validate intent, allowed files, forbidden actions, tests and evidence under current TAKY authority before modifying code.
- Use existing project tools only after confirming their availability and approval. This project's `.mcp.json` includes ONLY the version-pinned local `playwright` and `chrome-devtools` MCP configurations, copied from TAKY after trust-manifest validation. The `playwright` name also exists in User scope as `@latest`; the TAKY2-only Local scope override now resolves to `@playwright/mcp@0.0.83` and CLI reports Connected. `chrome-devtools` remains Pending approval in Claude; do not bypass its workspace trust prompt. MCP protocol read-only handshakes verified tool discovery, not tool invocation. `netlify` and `scenario` remote MCPs remain excluded pending trust/cost/approval verification.
- Do not silently import contradictory skill rules. The older `savey-ai-economy` skill's default-builder text must not override the canonical AI collaboration protocol.
- The ChatGPT/Antigravity bridge remains an isolated candidate: `D:\Git PWA\TAKY\TOOLS\taky_antigravity_bridge_v3_candidate.py`. Do not interpret mailbox ACKs as Claude inference or native panel control.

## Evidence
Return task ID, exact current branch/HEAD, changes, commands run, tests, open risks and receipt location. A statement of completion without independently checked evidence is not TAKY PASS.
