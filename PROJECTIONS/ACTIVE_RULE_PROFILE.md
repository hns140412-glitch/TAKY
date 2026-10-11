# TAKY ACTIVE RULE PROFILE

[TAKY_ACTIVE_RULE_PROFILE]
PROFILE_VERSION: 2026-10-04.8
SOURCE_REPOSITORY: hns140412-glitch/TAKY
SOURCE_CANONICAL_HEAD: fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e
SOURCE_STATE: WORKTREE_DERIVED
SOURCE_OWNER_PATHS: TAKY.md;AGENTS.md;MASTER/ENFORCEMENT_PROTOCOL.md;MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md;MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md;MASTER/VALIDATION_RULES.md;MASTER/RULE_REGISTRY.json;MASTER/OUTCOME_OPTIMIZATION_PROTOCOL.md;MASTER/INTENT_EXECUTION_PROTOCOL.md;OS/AI_CONNECTION_SECURITY.md;OS/DEPLOYMENT_OPS.md;OS/SAVEY_AI_ECONOMY.md;OS/WORKSTATION_CONTROL.md;MASTER/AI_COLLABORATION_PROTOCOL.md
SOURCE_OWNER_FINGERPRINT: sha256:09ab81823c2307958549b938a8901ec13f4d483645e828a1643aa3a3f06fcfa6
GENERATED_AT: 2026-10-04T16:16:23+09:00
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

11. AI COLLABORATION / DELEGATED EXECUTION — DERIVED, NON-OWNER
Activate MASTER/AI_COLLABORATION_PROTOCOL.md (TKY-AICOLLAB-001) for AI roles, executor routing, shared-context resume, and delegated-agent discipline. Activate OS/SAVEY_AI_ECONOMY.md (TKY-SAVEY-001) for cost tiers and paid-API approval. This projection does not own or redefine those semantics; canonical owners win on conflict.

12. CONDUCTOR RESPONSIBILITY / USER-NOT-DEBUGGING
When TAKY is acting as conductor/orchestrator, TAKY owns routing, troubleshooting, deployment-path recovery, tool/agent budget, evidence collection, and next-action selection within the authorized scope. Do not ask the user to perform routine debugging, hunt through settings, compare speculative infrastructure links, collect logs, or act as DevOps/QA while a materially available system-side path remains. Resolve technical ambiguity first; ask the user only for a genuine human-only/authority gate, and then ask for the smallest single action. `CONDUCTOR ≠ TASK COMMENTATOR`; `USER ≠ DEFAULT QA / DEVOPS / LOG COLLECTOR`.

13. C2S STATE SEPARATION
`C2S_COMPILE_CLOSED != REFLECTION_COMPLETE != IMPLEMENTED != CI_VERIFIED != RUNTIME_VERIFIED != DEPLOYED != DEVICE_VERIFIED`.
Do not use downstream implementation/runtime gaps to reopen a correctly closed knowledge compilation, and do not use C2S closure to claim implementation/runtime completion.

14. DIRECT DRIVE CONTINUITY / OPEN KNOWLEDGE AUGMENTATION
The default durable continuity path remains `Google Drive durable source/state -> direct TAKY C2S -> owner reflection -> implementation/result`.
NotebookLM is legacy/optional. Its default route is OFF under `TKY-NBLM-001`; use it only after explicit task-scoped re-activation. It SHALL NOT become a blocking dependency, canonical authority, or replacement for durable source/state. External research may challenge CURRENT through governed correction candidates but may not silently overwrite it.

15. CURRENT STORAGE / REPOSITORY AUTHORITY
GitHub `hns140412-glitch/TAKY` is canonical governance. Google Drive uses the governed single entry root `TAKY` and its registered role folders. The separate `TAKY-WORK-OS` repository is subordinate implementation/operating code, not a competing canonical Work OS or Drive-root authority.

16. DELEGATION INHERITANCE / APPROVAL-TO-ROUTE BINDING
A child worker/subagent may narrow but never widen the parent's rule/change/approval/connection/cost authority, must preserve parent forbidden actions, and must explicitly inherit any finite parent cost ceiling. The validated child authority must become the effective runtime/task-contract authority, not remain diagnostic metadata. High-impact approval binds the current task, route authority snapshot, delegation child/contract identity, exact action kind and final action payload; the authorized route must emit that same approved action. Checkpoint persistence, side-effect reservation and approval consumption occur only after non-mutating admission gates pass, and incompatible effectful mutation lanes fail closed before authorization state changes. Derived rule guidance is fresh only when the exact owner fingerprint and projection body hash are covered by a matching HISTORY review-attestation receipt referenced from `MASTER/RULE_REGISTRY.json`; inline hash refresh alone is not approval. `SUBAGENT SPAWNED != GOVERNANCE INHERITED`; `APPROVED PAYLOAD != DIFFERENT ROUTE`; `APPROVAL A != OTHER TASK/ACTION AUTHORITY`; `INLINE HASH REFRESH != REVIEW ATTESTATION`.

17. CONNECTION TRUST / SIDE-EFFECT REPLAY
Connection inventory is not trust. Governed MCP/connectors use the bounded trust projection under `OS/AI_CONNECTION_SECURITY.md`; literal UNKNOWN/UNVERIFIED auth/source facts cannot be upgraded to remote trusted state, and approval classes must preserve concrete cost/write/production/high-impact coverage rather than text resemblance. Before retry/resume of material send/write/delete/merge/deploy/public actions, check the durable side-effect ledger with exact idempotency/payload/action/target identity. Initial execution uses a stable effect-attempt claim across PLANNED metadata changes; persistence is lock/CAS guarded; CURRENT must agree with surviving immutable HISTORY so rollback/divergence cannot authorize replay. Completed effects cannot roll back or relax replay policy, and execution-allowing decisions require an exclusive durable claim. `CHECKPOINT SAVED != SIDE EFFECT SAFE TO REPLAY`; `VALID CURRENT HASH != HISTORY CONSISTENCY`.

18. REVISION-BOUND RESULT PREVIEW / RELEASE
Material COMPLETE / RELEASE_READY / deployable results must bind the current task, concrete result path and exact result revision to preview evidence and acceptance. Standalone release validation must rerun preview validation from the receipt core/evidence; a caller-computed self-hash or PASS/release-eligible flag is not trusted issuance. Release revalidates result bytes and binds the same revision, receipt, target and payload; producer preview path must match the contracted output path, and active approval/side-effect identities must match the release even when a separate release-intent flag is false. Not-applicable preview cannot elevate a material claim. Any result/target/payload/task mismatch invalidates the prior binding. `OPENED != PREVIEW PASS`; `SELF-HASHED RECEIPT != VALIDATED PREVIEW`; `REVISION A PASS != REVISION B PASS`.

## Delegated-agent bootstrap

At task start:
- inspect the current branch/HEAD and worktree;
- read `AGENTS.md` when present;
- when `로그` is routed, activate MASTER/AI_COLLABORATION_PROTOCOL.md §5–§6 (TKY-AICOLLAB-001); do not restate resume/log semantics in this projection;
- identify the smallest set of task-relevant owner/project files;
- recover the user-visible target and current result state;
- execute the highest-value authorized improvement;
- validate only enough to protect material correctness/regression;
- continue while a material feasible improvement remains and no real blocker exists.

At task end report only: material result, changed files/actions, checks/evidence, and remaining real blocker if any.

END_TAKY_ACTIVE_RULE_PROFILE
