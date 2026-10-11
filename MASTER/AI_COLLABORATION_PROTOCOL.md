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
| X | Codex CLI | Default executor for code implementation, modification, tests, and regression when coding is required. | Default coder |
| C | Claude general chat | Large-structure review, long reasoning, adversarial review, independent audit, design/architecture critique. | On review need |
| K | Claude CLI / Claude Code | Selective executor for difficult refactors, debugging, implementation, or review. Used only when materially justified (§3.3). | NOT default |
| L | Local collectors / CLI tools | Collection, indexing, deterministic verification. | Preferred first |
| S | GitHub / Drive / Notion | Source, evidence, and state surfaces. Not actors. Not authority by themselves. | n/a |
| E | SAVEY | Economic routing only (TKY-SAVEY-001). | Always (cost) |
| G | Gemini | Long-context or research review, only when TAKY explicitly routes a material task to it. | NOT default |

## 3. Routing
3.1 TAKY issues the task contract: objective, acceptance criteria, boundaries, executor.
3.2 Use deterministic local tooling whenever it can produce the result. When coding is required, route to Codex CLI.
3.3 Claude CLI / Claude Code is justified only when at least one of these holds, and the justification is recorded in the task contract or receipt:
- Codex produced a failed or insufficient run, with specific evidence;
- the change is a cross-cutting refactor or debugging task whose difficulty materially exceeds the default path;
- an independent implementation-level review of a material change is needed;
- TAKY explicitly routes the task to Claude CLI / Claude Code.
3.4 Claude general chat is used for structural, adversarial, architecture, or long-form review. It does not modify files.
3.5 Delegated-agent runs are a limited resource, not a default validation mechanism. Do not launch parallel or sequential duplicate agents for the same objective by default. After one delegated run, TAKY inspects the result, diff, receipt, and relevant validation evidence. Another run requires a specific, evidence-backed purpose.
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

## 8. Codex minimum-use gate
8.1 Codex is not used for collection, file discovery, status reconciliation, long-form review, planning, document synthesis, or deterministic validation when TAKY/local tools can do them directly.
8.2 Before any Codex call, TAKY must complete: authority lock -> exact objective -> allowed files -> forbidden actions -> acceptance criteria -> required tests -> expected output. Codex never receives an exploratory "figure it out" task by default.
8.3 Default execution order:
1) TAKY/ChatGPT: recover context, collect evidence, resolve authority, integrate decisions.
2) Local collectors/CLI: search, indexing, diff, parsing, deterministic checks, regression already available locally.
3) Claude general chat: one targeted structural/adversarial/long-context review when independent reasoning materially helps.
4) Codex CLI: one bounded implementation run only if code or test files actually need modification.
5) TAKY/local tools: inspect diff and run deterministic verification.
6) A second Codex run is allowed only for a concrete failed acceptance criterion that cannot be corrected safely without code editing.
8.4 Do not use Codex merely to re-run tests, summarize files, inspect status, review prose, search repositories, or repeat a review already completed by another actor.
8.5 When multiple code changes are independent but share one authority/task boundary, batch them into one prepared Codex task instead of one call per file or issue.
8.6 Codex output is never trusted as completion by itself. TAKY validates the resulting diff/evidence locally and only re-calls Codex if a specific code defect remains.
8.7 For Alpha/Beta consolidation, Codex is normally excluded from collection and synthesis. Use it only when consolidation reveals an actual implementation defect or a validator/test that must be changed.
8.8 Usage rule: MINIMUM CALLS, MAXIMUM PREPARATION. One well-scoped implementation call is preferred over exploratory multi-agent iteration.
