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
- Language memory / retrieval specialist → Hide & Seek
- Writing / expression specialist → Snap & Pop
- Family identity / member / role / shared profile → Family Platform
- Cross-app storage / sync primitives → Shared Runtime
- Crew / Badge / Achievement / World State → Exploration System

`CODE LOCATION != FUNCTION OWNERSHIP`

## 2. Shared contracts — current feature-branch state

### TAKY_APP_EXECUTION_CONTEXT_V1
Status: IMPLEMENTED / ENFORCEMENT VERIFIED

Preserves:
- family_id
- member_id = learner / data subject
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

### TAKY_FAMILY_MEMBER_STORAGE_SCOPE_V1
Status: IMPLEMENTED / VERIFIED

Rule:
`FAMILY BOUNDARY = DATA BOUNDARY = STORAGE BOUNDARY`

### TAKY_FAMILY_CONTEXT_V1
Status: IMPLEMENTED / VERIFIED

Lock:
`authentication != member identity != role != storage connection`

### TAKY_FAMILY_MEMBER_REGISTRY_V1
Status: IMPLEMENTED / VERIFIED

Owns:
- family membership projection
- stable member identity
- CHILD/PARENT role projection
- shared member profile: display_name / avatar_ref
- parent active-child projection

### TAKY_EXPLORATION_EVENT_V1
Status: IMPLEMENTED / VERIFIED

Normalizes Ready / Hide / Snap events into:
- EXECUTION
- RETRIEVAL
- EXPRESSION
- HANDOFF
- SUPPORT
- SYSTEM

### TAKY_ACHIEVEMENT_DECISION_V1
Status: IMPLEMENTED / VERIFIED

Owns:
- rule + event matching
- threshold decision
- no duplicate award decision
- no app-local badge authority

### TAKY_ACHIEVEMENT_LEDGER_V1
Status: IMPLEMENTED / ENFORCEMENT VERIFIED

Owns:
- member-scoped award ledger
- achievement-id idempotency
- source-event dedupe
- no cross-member ledger mutation

### TAKY_BADGE_CANDIDATE_REVIEW_V1
Status: IMPLEMENTED / ENFORCEMENT PENDING/VERIFY

Rules:
- evidence_event_ids required
- REVIEW_REQUIRED by default
- active=false
- award_authorized=false
- catalog_insert_authorized=false
- trigger_activation_authorized=false
- review may advance only to catalog-review state or reject
- no auto award / no auto catalog insertion

### TAKY_CREW_REGISTRY_V1
Status: IMPLEMENTED / VERIFIED

Core starter 6:
- Dubi / Lori / Ink / Nova / Take / Zero

Rules:
- starter roster reference only
- roster ceiling = 20
- one primary companion
- rename history preserved
- no functional/power advantage

### TAKY_CREW_VISUAL_PROJECTION_V1
Status: IMPLEMENTED / VERIFIED CONTRACT

Current boundary:
- identity lineage recovered
- reviewed asset binding is still OPEN
- visual projection may not mutate identity / power / reward

### TAKY_WORLD_STATE_V1
Status: IMPLEMENTED / VERIFIED

Owns:
- crew presence
- meaningful episode relationships
- special encounter state
- world memories
- no raw-presence affinity increase
- no absence decay
- no power advantage
- exact encounter probability/cadence remains unresolved

### TAKY_BADGE_THEME_EXPRESSION_V1
Status: IMPLEMENTED / VERIFIED CONTRACT

Rules:
- cosmetic-only expression
- identity mutation forbidden
- tier / growth / power / reward / economy mutation forbidden
- REVIEWED_ASSET_SET requires actual reviewed asset refs
- exact reviewed theme asset binding remains OPEN

## 3. Badge source recovery authority

Recovered current-scope sources:
- Drive `SNAP_POP_HANDOFF_2026-09-21_LATEST`
- Ready historical HOLD boundary
- sanitized account-transcript provenance
- recovered historical Snap badge source files

Recovered artifacts:
- `EXPLORATION/recovery/snap-2026-09-21/SNAP_POP_BADGE_SOURCE_RECOVERY_2026-09-21.md`
- `RECOVERY/BADGE/SNAP_BADGE_SYSTEM_RECOVERED_2026-09-21.json`
- `RECOVERY/BADGE/SNAP_BADGE_CATALOG_WORKING_RECOVERED_2026-09-21.json`

### CONFIRMED
- Badge = process / experience collection axis.
- Badge != Character Level / EXP / Gem / Affinity / World State / Leaderboard / Power.
- behavior families include:
  SELF_START, TIME_CREATION, EXTRA_TASK, FOCUS, RETURN_RECOVERY, HELP_REQUEST,
  ERROR_DISCOVERY, RETRY, DEEP_THINKING, ISSUE_DURATION, SELF_EXPLANATION,
  PLAN_ADAPTATION, SPECIAL_BEHAVIOR, WRITING_EXPLORATION.
- visual language: circular / hand-drawn-pastel direction.
- Profile Character is protagonist.
- tiers GREEN / BLUE / RED / GOLD / PLATINUM.
- 1–5 upper-semicircle gem/star growth marks.
- no punishment for absence / no earned-experience removal / no streak pressure.

### HOLD
- character growth economy as badge mechanic
- advanced reward economy
- social competition / leaderboard
- badge → EXP/Gem/Affinity/Power automatic conversion

### WORKING
- historical `BDG-DRAFT-001..060`
- exact historical names / trigger wording
- exact threshold / cadence / display copy
- all 60 remain `WORKING_DRAFT_NOT_ACTIVE`
- all remain `active=false`

### OPEN
- final active badge catalog membership
- canonical award thresholds/cadence
- old-observation migration
- exact display-surface ownership
- exact reviewed theme asset binding
- remaining unrecovered source coverage

## 4. SP-BADGE recovery status

### SP-BADGE-006
Status: PARTIAL / DO NOT CLOSE

Implemented centrally:
- behavior taxonomy / anti-labeling boundary
- strong evidence guard for:
  - ERROR_DISCOVERY
  - DEEP_THINKING
  - SPECIAL_BEHAVIOR
- weak proxies forbidden:
  elapsed time, silence, retry/edit counts, score/confidence, AI/model inference

Implemented source contracts:
- `TAKY_BADGE_SOURCE_EVIDENCE_V1`
- `TAKY_CHILD_SELF_CORRECTION_V1`
- `TAKY_CHILD_REFLECTION_ARTIFACT_V1`
- `TAKY_DECLARED_SPECIAL_ACTION_V1`
- each requires explicit child action and rejects inference-only evidence.
- central source contract → strong badge validator compatibility is Enforcement verified.

Current runtime gap:
- Ready / Hide / Snap load the source-evidence contract but do NOT auto-call it.
- existing app UX does not yet provide strong enough child-authored source artifacts for:
  ERROR_DISCOVERY / DEEP_THINKING / SPECIAL_BEHAVIOR.
- Hide explicit RETRY remains RETRY evidence only and must not be promoted to ERROR_DISCOVERY.
- Ready parent/system replanning must not be used as child badge evidence.
- therefore ERROR_DISCOVERY / DEEP_THINKING / SPECIAL_BEHAVIOR remain runtime-producer OPEN and must not be inferred or awarded.

### SP-BADGE-008
Status: PARTIAL

Implemented:
- stable Profile Character identity layer
- badge visual compositor semantics recovered
- GREEN / BLUE / RED / GOLD / PLATINUM growth presentation contract
- Theme Expression contract
- cosmetic-only fail-closed guard

OPEN:
- exact reviewed Theme Expression assets/system binding

## 5. Ready integration state

Feature branch:
`taky/family-member-scope-isolation-2026-09-25`

Latest exact-head:
`1c36fd2f540f0c483eba4e43c59e1628ad851d27`

Ready Runtime E2E: SUCCESS

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
- shared Crew read/update boundary
- shared World State endpoint + Ready adapter
- explicit World State browser mutation regression
- specialist launch carries learner / actor / learning lineage / companion identity
- Exploration Event projection

## 6. Hide integration state

Feature branch:
`taky/family-member-scope-isolation-2026-09-25`

Latest verified exact-head:
`7a08e6d882f66f668007d7f244868c0783b2a8d2`

Validate Hide & Seek: SUCCESS

Verified:
- member-scoped state / asset DB
- execution lineage
- actor provenance
- shared profile authority
- companion context continuity
- Exploration Event projection

## 7. Snap integration state

Feature branch:
`taky/family-member-scope-isolation-2026-09-25`

Latest verified exact-head:
`49241d0f29e67ef620adbf6869de494bb91107dc`

Validate Snap & Pop: SUCCESS

Verified:
- member-scoped IndexedDB
- execution lineage
- actor provenance
- shared member profile projection
- companion context continuity
- Exploration Event projection

Snap local EXP / Gem / Growth / Blessing remain Snap-local progression and are NOT common badge authority.

## 8. Key architectural locks

### Actor vs learner
- `actor_member_id` = authenticated user performing the action
- `member_id` = learner / data subject

### Badge vs economy
- Badge != EXP
- Badge != Gem
- Badge != Affinity
- Badge != World State
- Badge != Character power

### Crew
- Character choice does not grant capability advantage.
- SPECIAL is encounter style only, not a power tier.
- exact encounter probability/cadence remains OPEN.

### Badge activation
Historical 60-item catalog is recovery material only.
No item may activate merely because it exists in recovered source.

## 9. Promotion boundary

- TAKY shared contracts: FEATURE_BRANCH_VERIFIED except newest candidate-review exact-head verification until green.
- Ready: FEATURE_BRANCH_VERIFIED
- Hide: FEATURE_BRANCH_VERIFIED
- Snap: FEATURE_BRANCH_VERIFIED
- main merge: NOT DONE
- Netlify deployment: NOT DONE
- production verification: NOT DONE

## 10. Next functional OPEN

1. Verify newest `TAKY_BADGE_CANDIDATE_REVIEW_V1` exact-head Enforcement.
2. Keep SP-BADGE-006 PARTIAL until real explicit child source producers exist.
3. Shared source-evidence contracts are implemented and loaded in Ready / Hide / Snap with auto-wiring forbidden by regression tests.
4. Define/implement explicit source UX only where product behavior genuinely supplies strong evidence; never infer from weak proxies.
5. Add cross-app member-scoped badge candidate/award storage runtime only after an active catalog item is separately confirmed.
6. Bind Crew / Badge Theme visuals only to reviewed asset refs.
7. Recalculate overall master functional completion after badge runtime activation boundary is resolved.

Think Again, Keep Your Key.  
Think Again, You’re The Key.
