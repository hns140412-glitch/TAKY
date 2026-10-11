# SAVEY — AI Economy Governor

Status: ACTIVE OPERATING POLICY / 2026-10
Rule ID: `TKY-SAVEY-001`
Role: economic operation only. TAKY remains the authority and orchestration owner.

## Principle
**더 현명하게 쓰고, 더 똑똑하게 아끼자.**
Use already-paid subscription capacity before metered API spend.
Cost optimization must not redefine the requested result or TAKY authority.

## Default route
Cost tiers only; semantic executor roles are owned by MASTER/AI_COLLABORATION_PROTOCOL.md (TKY-AICOLLAB-001).
1. Local deterministic tools / existing repository logic.
2. Current subscription session and already-authenticated CLI/tool route selected by TAKY under TKY-AICOLLAB-001.
3. Reuse active subscription context/session and batch related work before consuming additional quota.
4. Prefer the lower sufficient model/quota tier; use a higher tier only when the expected quality gain materially justifies the extra usage.
5. Paid/metered API only when the above cannot meet the outcome and the user explicitly approves the cost.
Acceptance criteria are never lowered to save cost.

## Hard rules
- ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY are not a silent fallback.
- TAKY wrappers clear provider API-key variables before subscription/OAuth CLI calls.
- openai API CLI, Netlify AI Gateway, or direct provider API requests are COST-BEARING paths unless proven otherwise.
- Production deploy / merge / push are authority gates, not cost-routing shortcuts.
Enforcement owner: external call budget and approval gates are owned by `MASTER/ENFORCEMENT_PROTOCOL.md` (§4.5 call budget, §5 approval gate). SAVEY holds routing preference only and SHALL NOT restate those gates.

## Usage discipline
- Executor/reviewer selection and duplicate-agent discipline are owned by MASTER/AI_COLLABORATION_PROTOCOL.md (TKY-AICOLLAB-001); SAVEY does not redefine them.
- Reuse the active session when context is still useful.
- Batch related checks instead of repeated single-question calls.
- Prefer targeted file reads and diffs over repository-wide scans.
- Stop validation when evidence is sufficient and further checks are equivalent/redundant.
- Record failure patterns that can reduce future calls; do not create logs that cost more to maintain than they save.

## Decision record
For a material delegated call, retain only:
`TASK / PROVIDER / WHY / SUBSCRIPTION_OR_API / RESULT / FAILURE / NEXT_RULE_CANDIDATE`.

SAVEY may recommend a cheaper route.
SAVEY may not lower acceptance criteria, bypass verification, or override the user.
