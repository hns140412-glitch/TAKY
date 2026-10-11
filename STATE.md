# TAKY CANONICAL RUNTIME STATE

Status: ACTIVE / CANONICAL STATE SURFACE
Authority: subordinate to `MASTER/MASTER_LOGIC.md`; authoritative for current operational situation/decisions/open issues when consistent with higher canonical rules.

## Boot rule
A new conversation/session SHALL NOT reconstruct current TAKY/project state from conversational memory, a user-written summary, or a handoff summary first.

Required first recovery sequence:
`READ STATE.md -> RESOLVE system:current via MASTER/MASTER_FILE_REGISTRY.json -> READ CURRENT/SYSTEM_WIDE_REVIEW.json -> RESOLVE semantic owner/current -> VERIFY exact source refs and resume evidence -> CONTINUE`.

If `STATE.md` cannot be read, current state is `STATE_REHYDRATION_BLOCKED`; do not assume remembered state is current.

## Current governance state
- repository enforcement: `REPOSITORY_EXECUTABLE + CI_ENFORCED`
- role/action/owner classification trust source: `UNVERIFIED`
- repository C2S preflight composition: `REPOSITORY_EXECUTABLE + CI_ENFORCED`
- NotebookLM legacy recovery: `INACTIVE_DEFAULT / LEGACY_REFERENCE_ONLY`; active historical recovery uses direct Drive + TAKY C2S unless explicitly re-enabled
- conversation continuity/context economy: `CANONICAL_PROTOCOL_IMPLEMENTED + CI_ENFORCED`
- saved-share transcript sanitization: `IMPLEMENTED + ACTUAL_DRIVE_PILOT_PASS + CI_ENFORCED`
- hosted ChatGPT native tool-call automatic preflight: `UNVERIFIED`
- live hosted runtime fail-closed claim: `PROHIBITED`
- P0 open architecture issue: `#2 Trusted routing authority + runtime preflight interception`
- Visual design/UI asset-source default (user decision 2026-09-29): `TKY-ASSET-001` at `MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md`; original reusable assets and layers go to GitHub `TAKY-ASSETS`, app repos keep pinned manifest + verified deployment copies. Image/ZIP alone does not satisfy asset upload or UI implementation; current hosted cross-chat automatic interception remains UNVERIFIED.

## Current unresolved root issues
1. Trusted routing authority independent from executor is not implemented.
2. Hosted ChatGPT native tool dispatch does not have a repository-proven mandatory preflight interception hook.
3. Validation-only evidence must not be allowed to advance authoritative product-progress state without functional acceptance evidence.
4. Resume/context-compression must use verified canonical/history rehydration evidence rather than self-reported booleans.
5. Hosted conversation runtime still lacks repository-proven automatic C2S invocation/interception even though a repository-executable C2S bridge exists.

## Work / Codex resource-routing policy
Work and Codex SHALL be treated as scarce execution resources. TAKY SHALL NOT route work to either merely because the capability exists.

Before proposing or invoking Work or Codex, TAKY SHALL perform a usage-impact review:
1. determine whether the task can be completed in ordinary Chat with already-available connectors/tools;
2. if yes, prefer ordinary Chat and do not consume Work/Codex allowance;
3. if Work/Codex is necessary, choose the smallest execution surface and smallest independently useful work unit;
4. assess expected context size, file/source count, reasoning depth, tool calls, test/runtime loops, browser/E2E loops, and likely retries;
5. classify usage risk at least as `LOW / MEDIUM / HIGH / VERY_HIGH`;
6. `HIGH` or `VERY_HIGH` work SHALL NOT be launched as a monolithic task without explicit usage-risk disclosure and a cheaper/smaller routing attempt first;
7. whole-history recovery, broad multi-repository analysis, or large Drive/chat/GitHub sweeps default to `VERY_HIGH` until demonstrated otherwise;
8. implementation work sent to Codex SHOULD arrive as a narrow TASK CONTRACT after TAKY has already done orchestration, scope selection, and acceptance definition outside Codex where practical;
9. Work SHALL NOT be the default always-on orchestrator for development loops; reserve it for tasks whose browser/file/multi-step execution materially requires Work;
10. when remaining Work/Codex allowance is not directly observable, TAKY SHALL state that it is unknown and SHALL NOT claim that sufficient allowance remains.

### TAKY / Codex implementation-role hard lock
Usage optimization SHALL NOT redefine Codex as a patch-only or modification-only tool.

For software/product implementation work, the default role boundary is:
`USER INTENT -> TAKY WHAT/WHY/BOUNDARY/ACCEPTANCE -> CODEX HOW/CODE/IMPLEMENTATION TEST -> TAKY REVIEW/REWORK -> HUMAN APPROVAL WHEN REQUIRED`.

Rules:
1. TAKY owns orchestration, requirement interpretation, product intent, scope, sequencing, acceptance criteria, risk/authority checks, implementation-owner routing, and post-implementation review.
2. Codex owns implementation design within the accepted boundary, new code authoring, existing code modification, refactoring only when authorized, focused implementation tests, and implementation evidence reporting.
3. New feature/code creation is a Codex responsibility when Codex is the selected implementation owner; it SHALL NOT be shifted back to TAKY merely to reduce Codex usage.
4. TAKY SHALL reduce Codex usage by removing unnecessary repository-wide discovery, duplicate product reasoning, repeated context reconstruction, broad unrelated testing, and avoidable retries before dispatch — not by pre-writing the implementation for Codex.
5. A Codex task SHOULD be implementation-ready before dispatch: target outcome, authoritative inputs, known relevant files/modules when available, explicit constraints, acceptance criteria, required regressions, and delivery evidence SHOULD already be bounded by TAKY.
6. Codex MAY inspect additional implementation context when needed to write correct code, but SHALL NOT be asked to rediscover settled product requirements or re-orchestrate the whole project.
7. TAKY SHALL NOT perform product implementation writes while acting as ORCHESTRATOR merely because Codex allowance is scarce. If no valid implementation owner is available, report `EXECUTION_BLOCKED_NO_OWNER` or defer the implementation unit rather than silently taking the implementer role.
8. Codex completion is implementation evidence only: `CODEX_DONE != TAKY_PASS`.
9. Usage risk SHALL be assessed separately from implementation ownership: `HIGH_USAGE_RISK != TAKY_MAY_IMPLEMENT`.
10. Where task size is too large, TAKY SHALL decompose by independently useful user-visible/implementation slices and keep Codex as the code author for each selected slice.

### Codex validation-budget policy
Codex SHALL NOT perform every available validation layer on every implementation turn by default.

Default execution ladder:
`IMPLEMENT -> SMALLEST RELEVANT STATIC/CONTRACT TESTS -> REPORT EVIDENCE -> TAKY REVIEW`.

Escalate to browser/mobile/E2E only when at least one of the following applies:
- the changed behavior cannot be established by focused automated evidence;
- the task is at an integration/acceptance checkpoint;
- TAKY explicitly marks runtime/mobile evidence as required for that slice;
- prior evidence indicates a browser/runtime-specific regression risk.

Rules:
1. Previously obtained valid runtime evidence SHALL be reused when the subsequent change cannot affect that path; do not rerun expensive browser flows mechanically.
2. Browser/mobile/E2E verification SHOULD be batched at meaningful integration checkpoints rather than repeated after every small implementation edit.
3. Baseline failures SHALL be compared against the recorded start HEAD with the smallest possible command/test set; do not rerun the full suite merely to classify a known failure.
4. A usage-limit interruption SHALL preserve work state. Resume from existing changes/results and run only unfinished checks; never restart the whole contract by default.
5. Codex task reports SHALL separate `IMPLEMENTATION COMPLETE`, `FOCUSED TEST PASS`, `RUNTIME VERIFIED`, `RUNTIME UNVERIFIED`, and `BLOCKED_BY_USAGE_LIMIT` rather than converting missing expensive validation into failure or fabricated PASS.
6. Expensive validation is evidence work, not code-authoring authority. Deferring it does not transfer implementation ownership from Codex to TAKY.

### Codex workspace bootstrap policy
A Codex implementation contract SHOULD identify repository, canonical work branch, and task-contract path before dispatch. Codex SHALL bootstrap/fetch the named repository/branch when it has repository access instead of asking the user to manually discover task-file paths. User intervention is reserved for genuine authentication, permission, network, or filesystem boundaries that Codex cannot resolve itself.

Historical resource condition - 2026-09-14 (not current task lifecycle):
- user-visible Codex 5-hour allowance reached 0% during `RNS-P0-DAILY-LOOP-001` after approximately 16m30s of implementation/Chrome/runtime/test activity;
- user reported approximately three hours until Codex can be used again;
- visible weekly allowance remained available, but exact future consumption is not predictable from TAKY;
- observed interrupted evidence: 17 related checks, 12 passing and 5 failing; Codex was attempting start-HEAD baseline comparison when usage stopped; Chrome/mobile-width PARTIAL and parent/replanning behavior had already been exercised;
- at that checkpoint, lifecycle was `CODEX_INTERRUPTED_BY_USAGE_LIMIT / WORK_PRESERVED / TAKY_REVIEW_NOT_READY`; it does not define the current task lifecycle;
- during the cooldown, TAKY SHALL continue orchestration, GitHub inspection, acceptance refinement, evidence classification, contract decomposition, and non-product-code governance work using ordinary Chat/connectors. TAKY SHALL NOT take over product implementation code.

Claim boundary:
`CAPABILITY AVAILABLE != RESOURCE-AFFORDABLE`
`WORK/CODEX AVAILABLE != WORK/CODEX SHOULD_BE_USED`
`TASK DISPATCHED != USAGE SAFE`
`USAGE OPTIMIZATION != ROLE REASSIGNMENT`
`TAKY ORCHESTRATION != PRODUCT CODE AUTHORING`
`CODEX IMPLEMENTER != PATCH-ONLY TOOL`
`BROWSER E2E AVAILABLE != BROWSER E2E REQUIRED EVERY TURN`
`USAGE LIMIT INTERRUPTION != RESTART FROM ZERO`

## Semantic CURRENT - audited 2026-10-02
- state_revision: `2026-10-02-authority-current-delta`.
- Stable system resume pointer: `CURRENT/SYSTEM_WIDE_REVIEW.json`; explicit aliases: `MASTER/MASTER_FILE_REGISTRY.json`; resolver: `ENFORCEMENT/semantic_current_resolver.py`.
- TAKY audited base: `ccfb372ed10110121cec5be615c3e3e0c59f3601`; Ready audited main: `daed2ebd072061b870bfd0d2f2472dd344661bad`. Other exact audited main and Draft candidate heads live in system CURRENT. Read-only GitHub comparison matched at this audit; requery before any later live-current claim.
- Learning operational CURRENT: `learning_engine:current` -> `CURRENT/LEARNING_ENGINE_DATA_READINESS_CURRENT.json`. The change ledger is immutable change evidence; the dated verification file is a checkpoint. Neither is the resume pointer. Planner retains dated scheduling authority.
- Learning Data / Index operational CURRENT: `learning_data:current` -> `CURRENT/DATA/DATA_INDEX_SEARCH_PROJECTION.json`; external indexed evidence (including Tatoeba) does not transfer Index-owner, mastery, or scheduling authority to Learning.
- Tatoeba LANGUAGE_USAGE / EXAMPLE_SENTENCE: main/CLOSED after PR #197-#201, CURRENT/Canonical sync and main CI passed at audit. Mining-Index-Learning core loop and Learning-Planner-Ready path remain CLOSED/PASS.
- Explorer canonical V2: main/CLOSED after PR #193. Central runtime PR #191: Draft/Open. Ready V2 consumer: main/CLOSED; Hide/Snap promotion/reapplication: OPEN.
- Badge PR #196: Draft/Open; central hosted E2E remains OPEN. Ready-Set PR #143 is still Draft/Open and not main authority, but its candidate Ready Runtime E2E passed at head `b49ff5fbb76cdeece132264e91c2324d7d034b92` (workflow run #1848; focused badge producer spec 32/32 PASS). This evidence does not activate badge awards/economy, merge to main, or authorize deployment. Design-to-UI PR #194 and TAKY-ASSETS PR #4 remain Draft/Open candidates, not main canonical.
- Snap legacy browser closure remains UNVERIFIED. Deployment/Netlify remain HOLD. Recent family-profile/radio/letter/sealing-wax/handwriting/control-room/voice UX is preserved as OPEN in system CURRENT; canonical reflection and implementation remain separate, and the exact radio tap-vs-hold gesture remains unresolved.
- Resume by explicit semantic owner and verified evidence. Never choose largest REV/V or newest filename, and never reopen valid CLOSED work merely because historical files remain.

## Historical Ready snapshots - 2026-09-20, not resume authority
The former PR #68 main `6142cfeb5599a625d61ffa1faca866b2b6817cc8` and PR #73 renewal candidate `450caf84b23788b40a93e070742d86edc0165baa` are historical checkpoints. Their then-valid CI/runtime evidence is preserved in repository history and `HISTORY/2026-09-20_READY_LEARNING_ENGINE_FINAL_REVIEW_PR68.json`; they do not route current resume or establish current open gates. No history/checkpoint file is renamed or deleted by this repair.

Detailed 2026-09-20 Ready state remains in Git history and `HISTORY/2026-09-20_READY_LEARNING_ENGINE_FINAL_REVIEW_PR68.json`; it is not repeated on the active STATE surface.

## State mutation rule
Material state changes SHALL update this file or a referenced canonical state owner in the same work episode.
Conversation text alone is not durable state.

Each session/conversation SHALL append only its material delta to `HISTORY/SESSION_DELTA_LOG.md` rather than regenerating a synthetic full-history summary.

## Resume gate
`resume_simulation_passed` SHALL NOT be accepted as a naked boolean.
A valid resume claim requires machine-verifiable resume evidence identifying at minimum:
- state source path;
- exact state SHA-256 or immutable revision;
- state read/verification timestamp or execution record;
- required canonical/history sources recovered;
- reconstruction assertions;
- evidence file SHA-256.

No resume evidence -> no verified resume.

## Claim boundary
`STATE FILE EXISTS != STATE READ`
`STATE READ != REQUIRED SOURCES VERIFIED`
`MANIFEST says PASS != RESUME VERIFIED`
`HANDOFF SUMMARY != CURRENT STATE`

## Historical recovery checkpoint — 2026-09-14
- state_revision: 2026-09-14-source-backfill-01
- recovery_status: PARTIAL_BACKFILL / FULL_REVIEW_PENDING
- recovery evidence owner: HISTORY/2026-09-14_SOURCE_BACKFILL_CHECKPOINT_01.md
- conversation inventory: HISTORY/2026-09-14_SOURCE_INVENTORY_01.json
- 24 original share exports extracted; full semantic reading and attachment recovery are incomplete. Extraction is not full review.
- source TAKY main inspected at 995805ec2d38fcac7911f9b2316554d0d2b58868; this is a pre-backfill snapshot, not an evergreen latest SHA.
- Ready work branch runtime-session-bridge-2026-09-10 observed at a098ffac8b5d6f0aeb22b5e61250f70330d555c7. Historical checkpoint said READY_FOR_CODEX / NOT_DISPATCHED; neither that snapshot nor the interrupted Codex snapshot above routes current resume.
- Repository handoff resume evidence binding is implemented at aee98e436c815f638f7b9bb2a98a200c2282f9ae; hosted automatic state read, semantic rehydration, and trusted routing remain UNVERIFIED.
- Full-review completion gate: NOT_PASSED. No product-progress advancement or deployment is implied.
