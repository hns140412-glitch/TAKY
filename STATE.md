# TAKY CANONICAL RUNTIME STATE

Status: ACTIVE / CANONICAL STATE SURFACE
Authority: subordinate to `MASTER/MASTER_LOGIC.md`; authoritative for current operational situation/decisions/open issues when consistent with higher canonical rules.

## Boot rule
A new conversation/session SHALL NOT reconstruct current TAKY/project state from conversational memory, a user-written summary, or a handoff summary first.

Required first recovery sequence:
`READ STATE.md -> VERIFY state_revision/source refs -> READ required canonical/history refs -> VERIFY resume evidence -> CONTINUE`.

If `STATE.md` cannot be read, current state is `STATE_REHYDRATION_BLOCKED`; do not assume remembered state is current.

## Current governance state
- repository enforcement: `REPOSITORY_EXECUTABLE + CI_ENFORCED`
- role/action/owner classification trust source: `UNVERIFIED`
- hosted ChatGPT native tool-call automatic preflight: `UNVERIFIED`
- live hosted runtime fail-closed claim: `PROHIBITED`
- P0 open architecture issue: `#2 Trusted routing authority + runtime preflight interception`

## Current unresolved root issues
1. Trusted routing authority independent from executor is not implemented.
2. Hosted ChatGPT native tool dispatch does not have a repository-proven mandatory preflight interception hook.
3. Validation-only evidence must not be allowed to advance authoritative product-progress state without functional acceptance evidence.
4. Resume/context-compression must use verified canonical/history rehydration evidence rather than self-reported booleans.

## Work / Codex resource-routing policy
Work and Codex SHALL be treated as scarce execution resources. TAKY SHALL NOT route work to either merely because the capability exists.

Before proposing or invoking Work or Codex, TAKY SHALL perform a usage-impact review:
1. determine whether the task can be completed in ordinary Chat with already-available connectors/tools;
2. if yes, prefer ordinary Chat and do not consume Work/Codex allowance;
3. if Work/Codex is necessary, choose the smallest execution surface and smallest independently useful work unit;
4. assess expected context size, file/source count, reasoning depth, tool calls, test/runtime loops, and likely retries;
5. classify usage risk at least as `LOW / MEDIUM / HIGH / VERY_HIGH`;
6. `HIGH` or `VERY_HIGH` work SHALL NOT be launched as a monolithic task without explicit usage-risk disclosure and a cheaper/smaller routing attempt first;
7. whole-history recovery, broad multi-repository analysis, or large Drive/chat/GitHub sweeps default to `VERY_HIGH` until demonstrated otherwise;
8. implementation work sent to Codex SHOULD arrive as a narrow TASK CONTRACT after TAKY has already done orchestration, scope selection, and acceptance definition outside Codex where practical;
9. Work SHALL NOT be the default always-on orchestrator for development loops; reserve it for tasks whose browser/file/multi-step execution materially requires Work;
10. when remaining Work/Codex allowance is not directly observable, TAKY SHALL state that it is unknown and SHALL NOT claim that sufficient allowance remains.

Current resource condition: user reported that a monolithic Work task exhausted the available short-window allowance. Until fresh allowance evidence is available, avoid additional Work/Codex execution and prefer ordinary Chat routing.

Claim boundary:
`CAPABILITY AVAILABLE != RESOURCE-AFFORDABLE`
`WORK/CODEX AVAILABLE != WORK/CODEX SHOULD BE USED`
`TASK DISPATCHED != USAGE SAFE`

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
- Ready work branch runtime-session-bridge-2026-09-10 observed at a098ffac8b5d6f0aeb22b5e61250f70330d555c7. Current P0 contract remains READY_FOR_CODEX / NOT_DISPATCHED.
- Repository handoff resume evidence binding is implemented at aee98e436c815f638f7b9bb2a98a200c2282f9ae; hosted automatic state read, semantic rehydration, and trusted routing remain UNVERIFIED.
- Full-review completion gate: NOT_PASSED. No product-progress advancement or deployment is implied.
