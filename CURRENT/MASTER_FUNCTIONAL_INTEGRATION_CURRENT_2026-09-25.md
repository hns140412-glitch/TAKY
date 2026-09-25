# TAKY MASTER FUNCTIONAL INTEGRATION CURRENT — 2026-09-25

Status: FEATURE_BRANCH_INTEGRATION_CURRENT  
Branch: `taky/master-functional-contract-reconcile-2026-09-25`  
Promotion: NOT YET  
Deployment: NOT AUTHORIZED

## 1. Functional ownership lock

- Governance / orchestration → TAKY
- Mining → Mining Engine
- Index / semantic retrieval → Indexing
- Learning interpretation / learner state / adaptive intent → Learning Engine
- Dated allocation / replanning → Planner
- Session execution → Ready & Set
- Language memory/retrieval specialist → Hide & Seek
- Writing/expression specialist → Snap & Pop
- Family identity / member / role / profile → Family Platform
- Cross-app storage / sync primitives → Shared Runtime
- Crew / Badge / world-wide experience rules → Exploration System (OPEN integration audit)

`CODE LOCATION != FUNCTION OWNERSHIP`

## 2. Shared contracts implemented on feature branch

### TAKY_APP_EXECUTION_CONTEXT_V1
Status: IMPLEMENTED / TAKY ENFORCEMENT VERIFIED

Preserves:
- family_id
- member_id = learner/data subject
- actor_member_id = authenticated actor
- profile_id
- assignment_id
- analysis_id
- learning_unit_id
- todo_id
- session_id
- task_id
- lap_id
- source / target / return lineage

### TAKY_CANONICAL_LEARNING_EVIDENCE_V1
Status: PRE-EXISTING CORE + EXECUTION LINEAGE EXTENDED / VERIFIED

Execution provenance now retains actor/learner and assignment→lap lineage.

### TAKY_FAMILY_MEMBER_STORAGE_SCOPE_V1
Status: IMPLEMENTED / VERIFIED

Rule:
`FAMILY BOUNDARY = DATA BOUNDARY = STORAGE BOUNDARY`

Authenticated storage keys are scoped by family × learner member. Anonymous local mode retains legacy keys.

### TAKY_FAMILY_CONTEXT_V1
Status: IMPLEMENTED / VERIFIED

Locks:
`authentication != member identity != role != storage connection`

FamilyContext owns normalized:
- authenticated state
- family_id
- member_id
- role
- session_id
- auth provider provenance

Provider credentials/password handling remain provider-owned and are not part of FamilyContext.

### TAKY_FAMILY_MEMBER_REGISTRY_V1
Status: IMPLEMENTED / VERIFIED

Owns:
- family membership projection
- stable member identity
- CHILD/PARENT role projection
- shared member profile: display_name / avatar_ref
- parent local active-child selection

App-specific guide/companion/style state is explicitly NOT family-profile authority.

## 3. Ready integration state

Feature branch:
`taky/family-member-scope-isolation-2026-09-25`

Verified slices:
- FamilyContext adapter
- Netlify Identity → FamilyContext mapping
- family/member local-first isolation
- remote sync member provenance
- actor_member_id vs learner member_id separation
- Parent active-child selection
- Planner / Assignment learner-scoped persistence
- Ready app_state actor-scoped persistence
- family members read API
- shared profile update API
- active learner UI in Settings / Planner Admin
- specialist launch carries learner identity + actor provenance + learning lineage

Latest verified Ready Runtime E2E evidence before this CURRENT write:
- `d5994eba7594e2ad754eab9394043d5fcffc3ee1` — SUCCESS
- newer integration commits remain feature-branch only and require exact-head green before promotion.

## 4. Hide integration state

Feature branch:
`taky/family-member-scope-isolation-2026-09-25`

Implemented:
- member-scoped local state
- member-scoped asset DB
- execution lineage bridge
- actor_member_id provenance
- shared member display-name projection
- authenticated shared display name is Family Platform authoritative
- Hide guide / companion remains Hide-owned

Last fully green baseline before newest profile-authority guard:
- `4c7eab9a38418aece0abc33c15424c5b2001c979` — SUCCESS

Newest profile-authority guard requires exact-head green before promotion.

## 5. Snap integration state

Feature branch:
`taky/family-member-scope-isolation-2026-09-25`

Implemented:
- member-scoped IndexedDB
- execution lineage bridge
- actor_member_id provenance
- shared member display-name projection in header
- Snap guide / exploration semantics remain Snap-owned

Verified:
- `b3a8459e6515cdf741fb55a00fd30ba5656ecb79` — SUCCESS

## 6. Key corrected architectural defect

Previous ambiguity:
- authenticated actor member == learning-data subject

Corrected rule:
- `actor_member_id` = authenticated user performing action
- `member_id` = learner / data subject

Example:
Parent edits Child A Planner:
- actor_member_id = PARENT
- member_id = CHILD_A
- Planner / Assignment storage = CHILD_A scope
- Ready parent UI state = PARENT scope

## 7. Promotion boundary

DO NOT claim main implementation for these slices until each repository exact-head branch is green and explicit promotion occurs.

Current state:
- TAKY contracts: FEATURE_BRANCH_VERIFIED
- Ready integration: FEATURE_BRANCH_IMPLEMENTED / partial exact-head verification in progress
- Hide integration: FEATURE_BRANCH_IMPLEMENTED / newest exact-head verification in progress
- Snap integration: FEATURE_BRANCH_VERIFIED
- main merge: NOT DONE
- Netlify deployment: NOT DONE
- production verification: NOT DONE

## 8. Next functional OPEN

1. Finish exact-head verification for newest Ready + Hide integration commits.
2. Audit common Crew / Badge / World authority:
   - current Snap-centric badge runtime
   - Ready external expedition-member dependency
   - Hide companion state
   - cross-app achievement event contract
3. Build one common Exploration System contract without moving repositories prematurely.
4. Verify badge/crew events preserve family/member + execution lineage.
5. Recalculate master functional implementation rate after Exploration System audit.

Think Again, Keep Your Key.  
Think Again, You’re The Key.
