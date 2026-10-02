# TAKY Beta External Deep Research / Comparative Hardening

Date: 2026-10-02
Scope: External benchmark research after Frozen Beta
Frozen Beta source boundary: `64ba56274d2f12f6745db4fa77eac792f4c41ab4`
Rule: This research does NOT mutate Frozen Beta. It informs Claude Alpha design.

## 1. External evidence classes

### A. Durable workflow / human approval

LangGraph's human-in-the-loop pattern pauses execution with an interrupt, persists graph state via a checkpointer, and resumes from the persisted state after human input.
AutoGen demonstrates the same general shape: persist runtime state while waiting for a human, then rehydrate and continue.

Implication for TAKY:
- CURRENT/checkpoint + approval binding is directionally correct.
- approval must bind to the exact persisted state, not merely to prose or a conversation turn.
- a resume should rehydrate from durable state first and then consume human input.

### B. GitHub deployment protection

GitHub Environments can require reviewers before a job executes, restrict branches, apply wait timers and custom deployment protection rules.
GitHub also supports preventing self-review for protected environments.

Implication for TAKY:
- MERGE approval and DEPLOY approval should remain separate states.
- production deployment should use an environment-level protection rule rather than only an agent-side convention.
- where practical, the actor initiating production should not be the sole reviewer.
- deployment protection should remain outside the model's own decision loop.

### C. Claude Code managed permission / hook controls

Anthropic's strict settings examples:
- disable bypass-permissions mode;
- require approval for Bash;
- allow only managed permission rules/hooks;
- constrain plugin marketplaces;
- sandbox Bash.

Important limit:
- the sandbox applies to Bash only, not Read/Write/Web/MCP/hooks.
- community/issue evidence shows hook/settings fragility, including settings rewrites dropping hooks and plugin-installed hook scripts losing executable permission.

Implication for TAKY:
- Claude hooks are useful interception layers but MUST NOT be the sole root of trust.
- every critical hook needs:
  1. presence check,
  2. executable/parse check,
  3. settings hash/self-heal check,
  4. CI regression,
  5. a canonical rule outside the hook.
- managed settings / permission policy should be the first barrier; hooks are a second barrier.

### D. Claude Code GitHub Action security

Anthropic's action security guidance emphasizes:
- only users with write access can normally trigger Claude;
- bots are blocked by default;
- non-write-user bypass is risky;
- short-lived repository-scoped tokens are preferred;
- permissions should be minimized;
- prompt injection from public content remains a material risk;
- default behavior keeps PR creation under human oversight.

Implication for TAKY:
- public/community/mined content = UNTRUSTED until quarantined and normalized.
- worker agents must not inherit broad repository secrets or cross-repo authority by default.
- use short-lived, repository-scoped credentials where possible.
- GitHub/Claude automation should create candidate branches/PRs, not silently promote main.

### E. Netlify deployment model

Netlify separates:
- production deploy,
- deploy preview,
- branch deploy,
- local/dev,
with deploy contexts and context-specific variables.
Deploy Preview has a mutable PR preview URL and each deploy also has an immutable permalink.
Branch deploys can be disabled entirely.
Preview access can be protected.

Implication for TAKY:
- keep Netlify production outside ordinary implementation flow.
- prefer explicit preview generation only after a gate.
- record immutable deploy permalink as evidence when a preview is actually reviewed.
- do not enable branch deploys for every branch by default.
- production deploy requires a separate human-authorized transition.

### F. Community implementation patterns (Lazy Builder)

Useful recurring patterns:
- plan before file creation;
- test before live execution;
- dry-run / paper mode before real effects;
- explicit multi-condition gate before live;
- output reports should calculate values rather than invent them;
- high-impact final publication/execution remains human-approved.

TAKY interpretation:
- adopt the staged-risk pattern, not the literal implementation.
- community material remains reference evidence, never canonical authority.

## 2. Comparative conclusions

### KEEP

1. `CURRENT != CANONICAL_OWNER`
2. CURRENT-first resume.
3. exact approval-context binding.
4. merge and deploy as separate gates.
5. human approval after validation, not instead of validation.
6. hosted-runtime automatic interception remains UNVERIFIED unless directly proven.
7. deployment HOLD by default.
8. untrusted external sources quarantined before privileged use.
9. DEEP MEMORY — LIGHT EXECUTION.

### IMPROVE IN ALPHA

1. Add a formal Promotion State Machine:
   `DRAFT -> IMPLEMENTED -> TESTED -> ADVERSARIAL_VALIDATED -> DEFENSE_HARDENED -> REVIEW_READY -> HUMAN_APPROVAL -> MERGED -> DEPLOY_APPROVAL -> DEPLOYED -> PRODUCTION_VERIFIED`

2. Add independent gate layers:
   - canonical semantic gate;
   - runtime implementation gate;
   - CI/replay gate;
   - human approval gate;
   - deployment environment gate.

3. Add hook integrity:
   - managed settings;
   - hook manifest/hash;
   - session-start hook self-test;
   - fail-closed if a required hook disappears;
   - CI test that simulates permission/settings mutation.

4. Add least-privilege executor envelopes:
   - allowed repository;
   - allowed paths;
   - allowed tools;
   - allowed action classes;
   - max side-effect budget;
   - expiry / single-use approval binding.

5. Add deployment evidence contract:
   - deploy context;
   - source commit;
   - artifact digest;
   - preview immutable permalink;
   - reviewer;
   - approval record;
   - post-deploy verification.

6. Add source trust quarantine:
   - OFFICIAL_PRIMARY;
   - TRUSTED_INTERNAL;
   - VERIFIED_EXTERNAL;
   - COMMUNITY_REFERENCE;
   - UNTRUSTED_EXTERNAL.
   Privileged writes cannot directly consume the final two without validation/promotion.

7. Add Decision Defense Record for material decisions:
   - intent;
   - decision;
   - alternatives considered;
   - rejected alternatives + why;
   - attack cases;
   - containment;
   - automated tests;
   - residual risk;
   - rollback.

### DO NOT IMPORT BLINDLY

1. Do not make hooks the central authority.
2. Do not adopt a multi-agent swarm merely because a plugin offers one.
3. Do not auto-enable all Netlify branch deploys.
4. Do not let a CI PASS imply live/hosted/runtime PASS.
5. Do not let a dry-run PASS imply production permission.
6. Do not copy community prompts as governance.

## 3. New Alpha hardening proposal

### Alpha Defense Stack

Layer 0 — Human Intent Lock
- user intent / latest correction / cost / deployment boundary

Layer 1 — Canonical Resolution
- semantic owner
- namespace CURRENT
- exact source boundary

Layer 2 — Source Trust Firewall
- classify external input
- quarantine untrusted content
- prevent prompt-injection-led privileged action

Layer 3 — Executor Capability Envelope
- minimum tools
- minimum repo/path scope
- side-effect budget
- expiry

Layer 4 — Pre-action Defense Gate
- prerequisites
- exact target
- expected delta
- rollback
- approval requirement

Layer 5 — Execution

Layer 6 — Post-action Evidence
- actual diff/result
- tests
- integrated behavior
- artifact/source digest

Layer 7 — Adversarial Validation
- misuse
- stale state
- wrong target
- bypass flag
- missing hook
- untrusted input
- replay/retry/duplicate

Layer 8 — Human Approval
- only after prior layers pass
- approval bound to exact state/target

Layer 9 — Deployment Protection
- GitHub Environment / provider-side gate
- separate from merge
- Netlify HOLD unless authorized

Layer 10 — Production Verification
- live evidence
- rollback readiness
- no inference from local/CI-only PASS

## 4. Error / self / regression validation

Required Alpha regression families:

1. STALE_CURRENT
2. HANDOFF_OVERRIDES_CURRENT
3. APPROVAL_WRONG_TARGET
4. APPROVAL_STALE_STATE
5. APPROVAL_BYPASS_FLAG
6. PROMOTION_BEFORE_PREREQUISITES
7. CI_PASS_MISTAKEN_FOR_LIVE_PASS
8. HOOK_MISSING
9. HOOK_SETTINGS_MUTATED
10. PLUGIN_EXEC_PERMISSION_LOST
11. UNTRUSTED_PROMPT_INJECTION
12. CROSS_REPO_AUTHORITY_LEAK
13. DEPLOY_PREVIEW_MISTAKEN_FOR_PRODUCTION
14. PRODUCTION_WITHOUT_SEPARATE_APPROVAL
15. DUPLICATE_SIDE_EFFECT_RETRY
16. USER_AS_DEBUGGER
17. SAME_FAILURE_PATH_REPEATED
18. COMMUNITY_REFERENCE_PROMOTED_DIRECTLY
19. SECRET_EXPOSURE_IN_LOG
20. DRY_RUN_MISTAKEN_FOR_LIVE_READINESS

## 5. Decision

Frozen Beta remains valid and should not be rewritten for these findings.

The external research does NOT reveal a reason to reopen the Frozen Beta semantics.
It does reveal additional Alpha requirements, especially:
- hosted/tool interception must be defense-in-depth, not hook-only;
- permission scope and credential scope need first-class contracts;
- provider-side deployment protection should sit outside the agent;
- external/community sources need an explicit trust firewall;
- critical hooks need integrity/self-heal validation.

## 6. Sources reviewed

Primary / official:
- GitHub Actions deployment environments / required reviewers / deployment protection rules
- Netlify deploy overview / deploy contexts / deploy previews / branch deploy controls / deploy protection
- Anthropic claude-code repository strict settings examples
- Anthropic claude-code-action security/configuration
- LangGraph human-in-the-loop / checkpointing
- Microsoft AutoGen async human-in-the-loop persistence sample

Community / secondary:
- Anthropic Claude Code issues around hook/settings durability and permissions
- Lazy Builder guides on Claude Code staged automation, dry-run and high-impact approval

END
