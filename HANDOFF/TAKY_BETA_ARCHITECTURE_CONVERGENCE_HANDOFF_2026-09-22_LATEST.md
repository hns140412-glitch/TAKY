# TAKY BETA ARCHITECTURE CONVERGENCE — HANDOFF — 2026-09-22 LATEST

Status: HANDOFF_READY / C2S_COMPILE_CLOSED / CONSULTING_CONTINUES
Branch: `taky/system-architecture-realignment-2026-09-22`

## Read first

1. `C2S/TAKY_BETA_ARCHITECTURE_CONVERGENCE_C2S_CLOSURE_2026-09-22.md`
2. `C2S/TAKY_BETA_ARCHITECTURE_CONVERGENCE_ATOMS_2026-09-22.json`
3. `BETA/TAKY_BETA_RESTRUCTURE_PROGRAM_2026-09-22.md`
4. `BETA/TAKY_BETA_ARCHITECTURE_PLAN_2026-09-22.md`
5. `BETA/TAKY_BETA_LOSSLESS_C2S_PLAN_2026-09-22.md`
6. `BETA/TAKY_BETA_EXECUTION_ROUTING_CLEANUP_GATE_2026-09-22.md`
7. `MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json`
8. `MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md`
9. `OS/GUIDE_CHARACTER_RELATIONSHIP.md`
10. `OS/GUIDE_FAMILY_LEARNING_OS.md`

Then live-refresh the branch and compare the current exact HEAD with the latest commit before making any write.

## Current phase

This is still consulting / attack-review / standard derivation.

Do NOT:
- perform architecture cleanup;
- modify canonical ownership map merely because a candidate seems attractive;
- dispatch Codex;
- merge;
- deploy;
- call Netlify;
- claim PRE_DEVICE_CANDIDATE;
- freeze BETA prematurely.

UI review, C2S/source acquisition, data-completeness work and app development are happening in parallel. New evidence reopens only affected nodes/edges unless a top-level invariant changes.

## Strong current conclusions

### TAKY
- Preserve deep governance/history; reduce active task surface.
- `DEEP MEMORY — LIGHT EXECUTION`.
- Semantic owner normalization and current-truth reduction matter more than raw file-count reduction.
- Operational expression proliferation / activation cost is a stronger problem than “too many rules”.
- C2S is necessary complexity, not the primary bloat cause.
- Incident-specific local failures were often locally contained; direct incident→global-rule leakage is weaker than first suspected.

### Learning
- Learning Engine interprets.
- Planner manages dated allocation/capacity/carry-over/replan.
- Ready executes and hosts the current session runtime/UI where applicable.
- Hide is vocabulary/language retrieval specialist.
- Snap is thought/expression specialist.
- Learning App Family owns cross-app session/handoff/routing semantics.
- App switch does not end the family learning session.

### Cross-cutting Exploration Crew
- Must be consistent across Ready/Hide/Snap.
- Model as `EXPLORATION_CREW_DOMAIN`.
- Current canonical/steward/incubator is Snap, but the semantic domain should not be permanently equated with the Snap application lifecycle.
- Same Crew ID / Visual ID lineage / core personality / name history / relationship semantics across apps.
- Apps may vary only contextual behavior.
- Ready local Guide system is a migration/compatibility issue.
- Hide V2 adapter direction is closer to the desired model.
- `GUIDE_CHARACTER_RELATIONSHIP` should likely become family-wide relationship governance/constraint source, not actual crew roster/personality owner.
- Special Friend, Ready Random Guest and Snap Special Crew remain separate/HOLD until evidence proves a relation.

### Cross-cutting Badge Experience
- Must be consistent across Ready/Hide/Snap.
- Model as `BADGE_EXPERIENCE_DOMAIN`.
- Current implementation/canonical material lives mainly in Snap; logical domain is cross-app.
- Apps emit factual/explicit events; Badge Domain interprets eligibility/progress/award.
- Apps must not directly award badges.
- Badge stars are tier/grade.
- Badge stars != Gem != Wish != EXP != character power.
- Current universal count→tier runtime is not safe as canonical policy.
- Historical ~60-item catalog remains working draft, not active.
- Ready/Hide badge producers and cross-app Badge History are not complete.
- Ready generic `done*5 -> 획득 별` is a strong supersede/update candidate.

### Histories
Keep separate:
- Learning History
- Badge History
- Crew Relationship Memory
- Wish Economy Ledger

One source event may be referenced/interpreted by several owners. Do not build a mega global history.

### Profile / Visual Identity
- stable learner/profile ID is a reference key, not owner of Badge/Crew.
- distinguish Profile Character Visual ID from Exploration Crew Visual ID.
- shared image pipeline != shared visual identity semantics.
- Ready profile UI host != identity semantic owner.

### Share
- Share is a composition surface.
- It receives projections from result/profile/crew/badge.
- It does not infer badge meaning or mutate domains.

## Strong architecture invariants

```
APP != OS
APP_REPOSITORY != DOMAIN_AUTHORITY
IMPLEMENTED_IN != OWNS
HOSTED_BY != SEMANTIC_OWNER
RUNTIME_COORDINATOR != SEMANTIC_OWNER
UI_HOST != SEMANTIC_OWNER
CROSS_APP_VISIBILITY != CROSS_APP_OWNERSHIP
EVENT SHARING != STATE SHARING
SOURCE FACT != DOMAIN INTERPRETATION
CACHE/FALLBACK != AUTHORITY
ONE MEANING — ONE SEMANTIC OWNER — MANY REFERENCES
ONE EVENT — MANY VALID INTERPRETERS — NO CROSS-OWNER DIRECT MUTATION
ONE CHANGE — MANY AFFECTED CONSUMERS — TARGETED VALIDATION
SEMANTIC NODE != NEW FILE
DOMAIN BOUNDARY != NEW REPOSITORY
LOGICAL SEPARATION BEFORE PHYSICAL EXTRACTION
INDEX/POINTER != SHADOW CANONICAL
```

## TAKY component candidates — not yet canonical changes

- MASTER_LOGIC -> KEEP_OWNER
- C2S_PROTOCOL -> KEEP_OWNER + CONDITIONAL_ACTIVATION
- FAILURE_TAXONOMY -> KEEP_OWNER
- HANDOFF_PROTOCOL -> KEEP_OWNER + CONDITIONAL
- CONTINUITY_PROTOCOL -> KEEP_OWNER + CONDITIONAL
- CONTEXT_LEDGER_PROTOCOL -> CONSOLIDATE candidate
- TRACEABILITY_PROTOCOL -> KEEP + CONDITIONAL
- REVISION_GOVERNANCE -> CONSOLIDATE candidate
- VALIDATION_RULES -> triggered composer/support
- ENFORCEMENT_PROTOCOL -> ROLE_CHANGE candidate toward mechanical/executable support
- ENGINEERING_EXECUTION_PROFILE -> KEEP_OWNER + CONDITIONAL
- INTENT_EXECUTION -> KEEP_OWNER
- OUTCOME_OPTIMIZATION -> KEEP_OWNER, compose compactly at runtime
- RULE_REGISTRY / MASTER_FILE_REGISTRY / SYSTEM_LAYER_OWNERSHIP_MAP -> KEEP_SUPPORT / indexes
- ACTIVE_RULE_PROFILE -> persistent shadow candidate; prefer on-demand composition if consumers permit
- STATE.md -> current/history split + pointerize candidate
- NotebookLM -> legacy/manual-only compatibility
- monolithic enforcement CI -> affected-suite redesign candidate

## CI finding

`.github/workflows/taky-enforcement.yml` is one job with 59 named steps spanning multiple independent concerns.

Candidate target:
```
ALWAYS-RUN AGGREGATOR
  -> FAST CORE
  -> AFFECTED C2S/CONTINUITY
  -> AFFECTED WORK/NOTION/DRIVE
  -> AFFECTED EXECUTOR
  -> AFFECTED ARCHITECTURE/PRODUCT
  -> RELEASE/MIGRATION when required
  -> aggregate result
```

Do not naïvely skip required checks by path in a way that leaves pending/skipped statuses.

Validators/tests are consumers in the impact graph and can become stale.

## Root-cause priority

1. OWNER TYPE COLLAPSE — very strong
2. CANONICAL GENERATION DRIFT — very strong
3. SHADOW CURRENT STATE / PROJECTION — strong
4. OPERATIONAL EXPRESSION PROLIFERATION — strong
5. GOVERNANCE ACTIVATION GAP — strong
6. INCIDENT -> GLOBAL RULE LEAK — medium/weak after correction
7. C2S as root cause — weak/rejected

## Next attack-review stage

Continue without writes unless a separate explicit reflection/write instruction is given.

Recommended sequence:
1. Build the **whole-system disposition matrix** using:
   KEEP_OWNER / KEEP_SUPPORT / CONDITIONAL_ACTIVATION / ROLE_CHANGE / POINTERIZE / CONSOLIDATE / RETIRED_COMPATIBILITY.
2. Apply it to MASTER / OS / STATE / PROJECTIONS / ENFORCEMENT / CI, not just MASTER.
3. For every proposed consolidation or role change, run a **loss test**:
   - what unique meaning disappears?
   - which consumer breaks?
   - which recovery path disappears?
   - does a shadow canonical get created elsewhere?
4. Attack the candidate `EXPLORATION_CREW_DOMAIN` and `BADGE_EXPERIENCE_DOMAIN` against current UI/Data/C2S evidence from other parallel chats.
5. Inspect whether Badge/Crew first-class nodes can be represented only in `SYSTEM_LAYER_OWNERSHIP_MAP` with pointers, without new registries.
6. Trace consumer requirements before retiring persistent `ACTIVE_RULE_PROFILE`.
7. Design STATE.md current/history split candidate.
8. Design affected-suite CI topology with required-check safety.
9. Only after these streams converge, draft BETA FREEZE CANDIDATE.
10. Before any Codex dispatch, estimate bounded task contracts and consumption, then execute only frozen scopes.

## Impact reopening rule

`NEW EVIDENCE -> AFFECTED OWNER -> AFFECTED CONTRACT -> RUNTIME/UI/DATA CONSUMERS -> VALIDATOR CONSUMERS -> TARGETED REGRESSION`

No whole-system reset unless a top-level invariant changes.

## Closure boundary

C2S compilation for this conversation is closed.
Architecture reflection/canonical write remains open.
Implementation remains open.
No deployment/device validation was performed.
