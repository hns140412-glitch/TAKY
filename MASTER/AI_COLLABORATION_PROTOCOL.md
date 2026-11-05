# AI_COLLABORATION_PROTOCOL

Rule ID: TKY-AICOLLAB-001
Status: CANONICAL OWNER
Scope: AI role assignment, executor routing, delegated-agent discipline, shared-context resume ("로그"), and shared-log policy for the TAKY workspace.

## 1. Ownership
1.1 This file is the only semantic owner of AI collaboration roles and routing.
1.2 AGENTS.md, CLAUDE.md, TAKY.md, OS/SAVEY_AI_ECONOMY.md, PROJECTIONS/ACTIVE_RULE_PROFILE.md, and any other projection may activate or reference this rule. They must not redefine it.
1.3 If a projection conflicts with this file, this file wins. Report the conflict; do not reconcile it silently.
1.4 Economic/cost routing is owned by OS/SAVEY_AI_ECONOMY.md (TKY-SAVEY-001). SAVEY decides cost tier only. It does not assign semantic roles.

## 2. Role matrix
| ID | Actor | Role | Default? |
|----|-------|------|----------|
| T | TAKY / ChatGPT | Top-level orchestrator: intent, authority boundary, task contract, integration, final review. | Always |
| X | Codex CLI | Independent implementation-level verification when materially needed; conditional fallback code executor when Claude capacity is insufficient and TAKY approves the route. Never independently certify its own changes. | Review / fallback by need |
| C | Claude general chat | Large-structure review, long reasoning, adversarial review, independent audit, design/architecture critique. | On review need |
| K | Claude CLI / Claude Code | Primary code implementation, modification and focused implementation testing within TAKY-approved task scope, when authenticated subscription capacity is available. | Primary code executor |
| L | Local collectors / CLI tools | Collection, indexing, deterministic verification. | Preferred first |
| S | GitHub / Drive / Notion | Source, evidence, and state surfaces. Not actors. Not authority by themselves. | n/a |
| E | SAVEY | Economic routing only (TKY-SAVEY-001). | Always (cost) |
| G | Gemini | Long-context or research review, only when TAKY explicitly routes a material task to it. | NOT default |

## 3. Routing
3.1 TAKY issues the task contract: objective, acceptance criteria, boundaries, executor.
3.2 Use deterministic local tooling when sufficient. For implementation needing an AI code executor, Claude Code is the primary subscription route when available and justified by the task contract; TAKY determines actual call necessity before dispatch. Availability is verified, never inferred from a prior session or model name.
3.3 When Claude capacity is limited, blocked, or demonstrably uneconomical for the accepted task, TAKY may route bounded implementation to Codex using the usage monitor and an explicit dry-run estimate (context, calls, tests, retries). Codex may also perform independent verification when it adds material confidence relative to local deterministic checks. Record the reason and actual executor in the task contract/receipt. No always-call rule, unapproved metered fallback, or lowering of acceptance criteria.
3.4 Claude general chat is used for structural, adversarial, architecture, or long-form review. It does not modify files.
3.5 Delegated-agent runs are scarce. Do not launch duplicate or parallel agents for the same objective by default. After each delegated run, TAKY inspects the actual diff, receipt and evidence; further runs need an evidence-backed reason. A code author cannot be the sole independent verifier of its own material change.
3.6 Cost-tier, paid/metered API approval, and provider-key fallback semantics are owned by TKY-SAVEY-001. This protocol does not redefine them.

## 4. Executor guardrails
4.1 No executor may silently redefine product requirements, acceptance criteria, architecture boundaries, release policy, or human-approval requirements.
4.2 If an executor finds a requirement conflict, it stops the conflicting change and reports the conflict. It does not invent a product decision.

## 5. Shared-context resume: literal "로그"
5.1 When the user's input is literally "로그", resume from shared context. Do not ask the user to restate known context.
5.2 Read TAKY_WORKSPACE/CURRENT/AI_SHARED_CONTEXT_CURRENT.md first.
5.3 Then, only if more detail is needed, read TAKY_WORKSPACE/C2S_WORK/AI_SESSION_POINTERS.md to find the caller's last-read sequence and consume only the unread delta from TAKY_WORKSPACE/HISTORY/AI_SHARED_CHAT_LOG_YYYY-MM.md.
5.4 Do not re-read history that has already been consumed.
5.5 If CURRENT is stale, missing, or conflicts with a newer unread delta, recover from the available delta/evidence and ask only for the smallest unresolved human-only gap; never ask for a full context restatement.
5.6 Delivery is not complete by file creation alone. For callable clients, the bridge must send CURRENT plus recipient-targeted unread delta and receive a validated ACK.
5.7 Advance a client last-read pointer only after the ACK confirms the expected CURRENT sequence and delivered event identities.
5.8 After a validated receiver result, append a RECEIPT/RESULT event to the shared log and let TAKY promote only reviewed reusable state into CURRENT.
5.9 If a client cannot append to the shared log directly, its pending-event file remains pending evidence until TAKY/bridge assigns a monotonic sequence and appends it to the main shared log.

## 6. Logging
6.1 Log automatically only reusable decisions, user corrections or reversals, OPEN/CLOSED changes, authority changes, and material implementation/test/review results.
6.2 Do not log routine chatter, intermediate reasoning, repeated context, or duplicates of content already represented in CURRENT/canonical owners.
6.3 Shared logs and relays are transport/evidence. They are not canonical authority.

## 7. Authority boundary
7.1 This protocol does not own the global TAKY authority order. Follow the authority hierarchy declared by TAKY.md and the registered canonical owners in MASTER/RULE_REGISTRY.json.
7.2 Shared logs, relays, HANDOFF, and HISTORY remain evidence/recovery only under §6.3 and must never override current user instruction or registered canonical authority.

## 8. Delegated execution / Codex minimum-use gate
8.1 Do not use Codex for collection, file discovery, status reconciliation, routine planning, document synthesis or deterministic checks that TAKY/local tools can do directly. Route complex code changes to Claude Code by default when the authenticated subscription has capacity; use Codex independently or as a justified fallback, not automatically.
8.2 Before any delegated model call, TAKY must lock authority, objective, allowed and forbidden files, acceptance criteria, relevant tests, expected evidence, necessity and usage-risk estimate. If observable subscription quota is unknown, state UNKNOWN; never claim sufficient capacity or invent a model allowance.
8.3 Default execution sequence:
1) TAKY/ChatGPT: recover CURRENT, scope, authority, requirements and evidence.
2) Local collectors/CLI: perform bounded discovery, parsing, diffing, and deterministic checks.
3) TAKY: assess call necessity, current usage evidence and dry-run estimated cost/effort; route a bounded task to Claude Code primary executor, or Codex fallback when justified.
4) Selected executor: implement actual code and focused tests within the approved boundary; preserve existing dirty state.
5) TAKY/local tools: inspect diff, verify acceptance and run proportional deterministic regression.
6) Codex independent review, or another suitably independent review route, only when material risk warrants it and the reviewer did not author the same change; concrete defects may be routed back to the appropriate executor.
8.4 Do not use Codex merely to rerun tests, summarize files, search repositories, or repeat equivalent review. Its independent review must cite concrete changed files and revision/evidence.
8.5 Batch related implementation edits under one authorized boundary where this reduces unnecessary model calls and keeps verifiable scope.
8.6 Neither Claude nor Codex completion is TAKY PASS by itself. Distinguish IMPLEMENTED, FOCUSED_TEST_PASS, RUNTIME_VERIFIED, and remaining unverified states.
8.7 Alpha/Beta collection and synthesis use local tools first; code executors are selected only for actual implementation, validator changes, or justified independent review.
8.8 Usage rule: MINIMUM NECESSARY CALLS, MAXIMUM PREPARATION, NO SILENT PAID FALLBACK. Implementation ownership is not reassigned to TAKY merely because a model has insufficient quota.

8.9 Independent-review acceptance: a review counts as `INDEPENDENT_SOURCE_REVIEW` only if its actual source paths/versions or verified source packet are recorded, distinct from the implementation author's summary. `INDEPENDENT_EXECUTION_VERIFIED` additionally requires a separately run, attributable command/test with exit status and matching input revision. A model's exit code 0, review text, PASS assertion, or login status alone is never execution verification. If tools are refused, record `PARTIAL_SOURCE_REVIEW_TOOL_BLOCKED`, preserve concrete source findings, and reroute only the blocked verification step.
8.10 Review economy and correction loop: assign Codex only one bounded, materially different critical review after local deterministic checks and implementation, or when independent source analysis will change scope decisions. Repeated calls require a new code delta, material failure, or untested hypothesis. Set a limited scope and tool/time budget up front, record consumption when observable, and do not silently switch to paid API. A valid defect routes to the primary executor for correction, followed by local regression and an independent recheck only of the changed risk. Model-reported findings stay `FINDING_OPEN` until verified; unsupported assertions are `HOLD`.
8.11 Working-tree safety: prior dirty files and untracked assets are user work, not disposable temporary state. Before any local commit/checkpoint, bind exact paths to one work intent, inspect the staged patch separately from unstaged changes, run relevant regression, and verify receipt/readback. Never stage all 9 repos or infer completion from reducing `git status` counts. A scoped local commit is permitted only when included content is understood and does not silently include unrelated WIP; push/merge/deploy remain separately approved actions.
