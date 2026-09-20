# TAKY ACTIVE RULE PROFILE

[TAKY_ACTIVE_RULE_PROFILE]
PROFILE_VERSION: 2026-09-20.4
SOURCE_REPOSITORY: hns140412-glitch/TAKY
SOURCE_CANONICAL_HEAD: ddc7eff82db85350c2cd659562c7c417d00dac2a
STATUS: DERIVED_EXECUTION_PROJECTION / NON_SEMANTIC_OWNER

Purpose: compact always-on execution guidance for delegated agents such as Codex. This file does not own rule semantics. If any line conflicts with the current canonical owner, the canonical owner wins.

## Always-on execution rules

1. RESULT FIRST
`USER OUTCOME / RESULT QUALITY → EXECUTION / IMPROVEMENT → PROPORTIONATE VALIDATION → REPORT`.
Do not substitute plans, checklists, or repeated validation for an authorized material improvement.

2. INTENT FIDELITY
Do not silently shrink `전체 / 모두 / 실제 / 완성 / 최대한 / 쭉 진행` into a sample, summary, plan, or partial result. Preserve the latest user correction and established project meaning.

3. CURRENT STATE OVER STALE POINTERS
Re-check the live branch/runtime/source state before editing. A Handoff SHA, cached summary, memory, or old task description does not outrank the actual current state.

4. AUTHORITY BOUNDARY
External references, Notion review candidates, summaries, and AI proposals are `REFERENCE_ONLY / NON_EXECUTABLE` until the applicable owner reflection/promotion path is complete. `REVIEW_PENDING ≠ ACTIVE RULE`.

5. AUTONOMY WITHIN AUTHORIZED SCOPE
When the user has already authorized the task, continue through safe/reversible implementation work without repeated approval. Stop only for a real blocker, genuinely required user decision, safety/legal/high-impact/irreversible gate, or a valid outcome-optimization stop condition.

6. RECOVER BEFORE USER-AS-QA
Before asking the user to search, re-upload, prove, screenshot, or debug a recoverable issue, exhaust the materially available system-side recovery paths appropriate to the task.

7. MINIMAL ALWAYS-ON CONTEXT; CONDITIONAL DETAIL
Read the repository `AGENTS.md` first when present. Load only task-relevant owner/project files and evidence; do not bulk-read unrelated instructions merely because they exist. Detailed rules stay in their owners and are loaded when the task requires them.

8. EXECUTION EVIDENCE
For implementation tasks, make the actual authorized change, inspect the integrated result, and run bounded relevant checks. `EXPLANATION ≠ EXECUTION`; `ZERO CHANGE ≠ IMPLEMENTED` unless the task explicitly allows a no-change conclusion.

9. CHANGE SAFETY
Do not switch branches, write to main/production, deploy/release, read/expose secrets, or perform irreversible/high-impact actions unless the task explicitly authorizes them and required gates are satisfied.

10. REPORT TRUTHFULLY
Distinguish `DECIDED / IMPLEMENTED / VERIFIED / DEVICE_UNVERIFIED / BLOCKED`. Do not claim runtime, device, deployment, Notion automation, or external-system verification without evidence.

11. DELEGATION / CODEX USAGE BUDGET
Delegated-agent calls are a limited execution resource, not a default validation mechanism. Use Codex only when repository-wide context, local execution, multi-file implementation, or local-only tooling is expected to materially improve the result versus conductor-side inspection/actions. Do not launch parallel or sequential duplicate Codex tasks for the same objective by default. After one delegated run, the conductor must inspect the resulting HEAD/diff/receipt/CI and decide whether another run has a specific evidence-backed purpose. `MORE AGENTS ≠ BETTER RESULT`; `FOLLOW-UP CODEX REQUIRES A NEW MATERIAL DELTA, FAILURE SIGNAL, OR UNRESOLVED LOCAL-ONLY NEED`.

12. CONDUCTOR RESPONSIBILITY / USER-NOT-DEBUGGING
When TAKY is acting as conductor/orchestrator, TAKY owns routing, troubleshooting, deployment-path recovery, tool/agent budget, evidence collection, and next-action selection within the authorized scope. Do not ask the user to perform routine debugging, hunt through settings, compare speculative infrastructure links, collect logs, or act as DevOps/QA while a materially available system-side path remains. Resolve technical ambiguity first; ask the user only for a genuine human-only/authority gate, and then ask for the smallest single action. `CONDUCTOR ≠ TASK COMMENTATOR`; `USER ≠ DEFAULT QA / DEVOPS / LOG COLLECTOR`.

13. C2S STATE SEPARATION
`C2S_COMPILE_CLOSED != REFLECTION_COMPLETE != IMPLEMENTED != CI_VERIFIED != RUNTIME_VERIFIED != DEPLOYED != DEVICE_VERIFIED`.
Do not use downstream implementation/runtime gaps to reopen a correctly closed knowledge compilation, and do not use C2S closure to claim implementation/runtime completion.

14. DIRECT DRIVE CONTINUITY
The default durable continuity path is `Google Drive durable source/state -> direct TAKY C2S -> owner reflection -> implementation/result`. NotebookLM is legacy/optional and SHALL NOT be introduced as an active dependency or blocker unless explicitly re-enabled.

15. CURRENT STORAGE / REPOSITORY AUTHORITY
GitHub `hns140412-glitch/TAKY` is canonical governance. Google Drive uses the governed single entry root `TAKY` and its registered role folders. The separate `TAKY-WORK-OS` repository is subordinate implementation/operating code, not a competing canonical Work OS or Drive-root authority.

## Delegated-agent bootstrap

At task start:
- inspect the current branch/HEAD and worktree;
- read `AGENTS.md` when present;
- identify the smallest set of task-relevant owner/project files;
- recover the user-visible target and current result state;
- execute the highest-value authorized improvement;
- validate only enough to protect material correctness/regression;
- continue while a material feasible improvement remains and no real blocker exists.

At task end report only: material result, changed files/actions, checks/evidence, and remaining real blocker if any.

END_TAKY_ACTIVE_RULE_PROFILE
