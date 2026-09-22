# TAKY MASTER LOGIC — VERTICAL / HORIZONTAL ARCHITECTURE AUDIT
Date: 2026-09-22
Status: AUDIT_COMPLETE__CANONICAL_CORRECTION_PENDING
Scope: TAKY -> Shared Technical Capability / Work OS / Learning OS -> Learning Domain / Learning App Family -> Ready / Hide / Snap -> implementation
Authority: review only; this document does not silently rewrite canonical owners.

## 0. Audit trigger
User observation: 전후 / 상하 로직이 틀어진 것 같다.

Finding:
The global TAKY hierarchy is largely intact.
The primary structural distortion is below LEARNING_OS:
- domain semantic owners,
- domain engines,
- family runtime contracts,
- app execution hosts
have been partially collapsed into Ready & Set.

This creates dependency inversion:
a lower PROJECT_APP is acting as owner of semantics that higher Learning OS documents already define as domain-level.

## 1. What is still structurally correct

PASS:
- TAKY_CORE remains global governance, not domain/product owner.
- WORK_OS and LEARNING_OS are siblings.
- SHARED_TECHNICAL_CAPABILITY is semantic-light.
- shared mechanism != shared semantic authority.
- Learning App Family is below Learning OS.
- Hide and Snap remain specialist apps.
- Netlify/GitHub/platform mechanics remain adapter-level.
- Work<->Learning identity federation remains HOLD.

These should NOT be rebuilt.

## 2. P0 structural conflicts

### P0-01 — Missing explicit Learning Domain Core layer
Evidence:
- LEARNING_APP_FAMILY_MASTER says "Shared Learning Domain owns long-term source/task/session/history meaning."
- GUIDE_FAMILY_LEARNING_OS defines MAIN / SUBJECT SUB-MASTER / FUNCTIONAL APP separation.
- SYSTEM_LAYER_OWNERSHIP_MAP jumps directly from LEARNING_OS -> LEARNING_APP_FAMILY -> apps.

Problem:
The semantic owner described in prose has no explicit machine-readable layer.
Its responsibilities leak downward into Ready.

Classification:
MISSING_OWNER_LAYER / OWNER_DRIFT

Required correction:
Introduce an explicit Learning Domain/Core service layer under LEARNING_OS, above app family execution.

Candidate children:
- LEARNING_ENGINE
- PLANNER_ENGINE
- LEARNING_EVIDENCE / HISTORY
- family identity/authority semantics
These are semantic services, not Shared Technical Capability.

### P0-02 — Ready Learning Engine ownership inversion
Evidence:
- current Ready code/module names: ready-learning-master, learner-context, specialist-router.
- Drive closure: "Ready Learning Engine owns review interpretation."
- specialist router authority: READY_LEARNING_ENGINE_ROUTING.
- Notion routing matrix: Ready owns learning-unit construction, subject progression/range/review context.

Conflict:
GUIDE_FAMILY_LEARNING_OS says:
- MAIN = HOW TO MANAGE
- SUBJECT/PRACTICE SUB-MASTER = HOW TO UNDERSTAND
- FUNCTIONAL APP = HOW TO HELP EXECUTE

Ready is a FUNCTIONAL APP / BASE CAMP execution experience.
It may orchestrate the user journey, but should not become the semantic owner of the Learning Engine.

Classification:
OWNER_DRIFT / IMPLEMENTATION_LOCATION_PROMOTED_TO_AUTHORITY

Correction direction:
Learning Engine becomes LEARNING_OS domain service.
Ready consumes a versioned projection and may host adapter/UI.
Hide/Snap consume scoped specialist context.
Implementation may temporarily live in Ready repository during extraction, but repository location != semantic ownership.

### P0-03 — Planner Engine ownership inversion
Evidence:
- SYSTEM_LAYER_OWNERSHIP_MAP: Learning schedule/planner/assignment semantics owner = LEARNING_OS.
- GUIDE_FAMILY_LEARNING_OS: MAIN owns life schedule, allocation, carry-over, forecast.
- Drive docs repeatedly say "Ready Planner owns dates/times."
- Ready repository currently owns planner policy/projection/store/runtime.

Problem:
Ready product projection and Planner Engine semantics are conflated.

Required split:
PLANNER_ENGINE owns:
- schedule commitments
- availability/capacity
- allocation
- dated todo planning semantics
- carry-over/reflow
- adaptive estimate
- plan-vs-actual planning interpretation

READY owns:
- TODAY presentation
- Mission/Focus interaction
- result capture UX
- child-facing plan adjustment interaction
- Ready-specific projections

Rule:
PLANNER_ENGINE != READY_UI
READY_TODAY != PLANNER_AUTHORITY

### P0-04 — Family identity / Parent-Child authority implementation drift
Evidence:
SYSTEM_LAYER_OWNERSHIP_MAP:
- family/child/parent identity, relationships, roles, permissions -> LEARNING_OS.

Conflicting handoff wording:
- "Ready retains family authentication and Parent/Child authority."

Correct interpretation:
- generic auth transport may be shared technical.
- learning family identity/relationship/role/permission semantics belong to LEARNING_OS.
- Ready may host login/profile/review UI and an implementation adapter.
- Ready must not become the semantic authority merely because current auth code lives there.

Classification:
SEMANTIC_OWNER_VS_IMPLEMENTATION_HOST_COLLAPSE

### P0-05 — Assignment / FACT ownership drift
Evidence:
SYSTEM_LAYER_OWNERSHIP_MAP:
- assignment intake/review-before-FACT semantics -> LEARNING_OS.

Conflicting implementation/handoff:
- Ready retains assignment / FACT semantics.
- Ready capture and Parent confirm currently implement the flow.

Correction:
LEARNING_OS owns Assignment FACT lifecycle semantics.
Ready owns Ready-specific capture/review UI and adapter.
OCR mechanism remains Shared Technical Capability.
Source/capture storage implementation may remain project-owned if scoped, but FACT meaning does not.

## 3. P1 cross-app routing/session conflicts

### P1-01 — Specialist routing authority too low
Current:
Ready specialist router decides Hide/Snap routing and is named READY_LEARNING_ENGINE_ROUTING.

Desired:
Learning-domain routing policy determines semantic need:
- memory/retrieval -> Hide
- expression/production -> Snap
- general execution/orchestration -> Ready

Ready may execute the route/handoff in the product journey.
The route policy should not be defined as Ready-owned semantic authority.

Candidate owner:
LEARNING_APP_FAMILY if routing is purely cross-app runtime contract,
or LEARNING_ENGINE if routing depends on learning interpretation.
Recommended composition:
LEARNING_ENGINE classifies learning need -> FAMILY_ROUTER maps need to app -> Ready hosts current base-camp transition UI.

### P1-02 — Session contract vs session state host not distinguished
Current Family Master:
- LEARNING_APP_FAMILY owns cross-app session contract.
- Ready = ONE SESSION STATE OWNER / session orchestrator.

This can be valid only if two meanings are separated:
- semantic contract owner = LEARNING_APP_FAMILY
- current runtime host/coordinator = Ready

Current wording often collapses these into "Ready owns session."

Correction:
Use distinct fields:
- SESSION_SEMANTIC_OWNER = LEARNING_APP_FAMILY
- SESSION_RUNTIME_COORDINATOR = READY_SET (current implementation)
- SESSION_UI_HOST = READY_SET
A future runtime extraction must not require semantic redefinition.

## 4. P1 stale experience/identity layers

### P1-03 — Character Visual ID incorrectly embedded in Ready
User correction on 2026-09-22:
Character Visual ID is developed separately and integrated later.

Current corrective implementation:
- Ready branch retains consumer contract only.
- Character implementation preserved on independent branch.

Required master placement:
Character Visual ID should be modeled as a Learning-family experience capability, not Ready-owned and not Shared Technical Capability.

It owns visual-character generation semantics only.
It must not own family identity/permission.
It consumes a scoped learner/member reference and publishes a Visual ID projection.

### P1-04 — Intro / Drop / Voyage world entry should be expansion capability
Latest user direction:
develop separately as expansion pack.

Therefore historical hard-lock onboarding sequences that force island discovery/base-camp/world-entry into core startup must be reclassified.
Core learning app usability must not depend on cinematic/world-entry expansion.

Classification:
STALE_CORE_BINDING / NEEDS_SUPERSESSION_REVIEW

### P1-05 — Guide terminology and ownership stale
Current TAKY still contains:
- GUIDE_CHARACTER_RELATIONSHIP
- GUIDE_CORE6_CHARACTER
- Ready legacy Guide settings/names.

Latest product terminology:
탐험대 / 탐험대원, with Snap-origin rules and cross-family use through explicit projection/contract.

Required:
Do not mass-delete historical GUIDE lineage until source-by-source mapping is complete.
But active projections must stop treating legacy GUIDE terminology as current product authority where superseded.

## 5. Corrected target vertical architecture — CANDIDATE

TAKY_CORE
├─ SHARED_TECHNICAL_CAPABILITY
│  └─ transport / queue / event / PWA / OCR / HTTP / generic mechanisms
├─ WORK_OS
│  └─ work domains/projects
└─ LEARNING_OS
   ├─ LEARNING_IDENTITY_AUTHORITY
   │  └─ child / parent / family learning roles & scoped authority
   ├─ LEARNING_DOMAIN_CORE
   │  ├─ LEARNING_ENGINE
   │  │  ├─ learner context
   │  │  ├─ subject interpretation
   │  │  ├─ learning-unit sizing
   │  │  ├─ difficulty/load/review interpretation
   │  │  └─ specialist-need classification
   │  ├─ PLANNER_ENGINE
   │  │  ├─ schedule / availability / capacity
   │  │  ├─ allocation / DATED TODO planning semantics
   │  │  ├─ carry-over / reflow
   │  │  └─ adaptive estimate / forecast
   │  ├─ ASSIGNMENT_FACT_DOMAIN
   │  └─ LEARNING_HISTORY / EVIDENCE
   ├─ LEARNING_APP_FAMILY
   │  ├─ cross-app session/handoff contract
   │  ├─ app-routing projection
   │  ├─ CHARACTER_VISUAL_ID (separate family experience capability)
   │  ├─ optional WORLD_ENTRY_EXPANSION
   │  ├─ READY_SET
   │  │  └─ TODAY / Mission / Focus / Result / Base Camp execution UX
   │  ├─ HIDE_SEEK
   │  │  └─ language-memory specialist UX
   │  └─ SNAP_POP
   │     └─ expression/exploration specialist UX + exploration-crew source ownership
   └─ external subject/reference sources and verified evidence adapters

This hierarchy is a correction candidate, not yet canonical.

## 6. Horizontal data-flow correction

Current problematic tendency:
SOURCE -> READY -> Planner/Learning interpretation -> Hide/Snap

Correct candidate:
SOURCE
-> Assignment FACT Domain
-> Learning Engine interpretation
-> Learning Unit / evidence projection
-> Planner Engine placement
-> Family Router / Session Contract
-> Ready / Hide / Snap execution
-> specialist evidence
-> Learning History/Evidence
-> Learning Engine review interpretation
-> Planner Engine next-plan adjustment
-> app projections

Rule:
APP RESULT MAY FEED DOMAIN ENGINE.
APP SHALL NOT BECOME DOMAIN ENGINE AUTHORITY.

## 7. Before / during / after correction

BEFORE:
- app repository location frequently implied semantic ownership.
- Ready accumulated Planner + Learning + Assignment + family authority.
- Family/Domain prose and machine map disagreed.
- routing and scheduling worked, but hierarchy was inverted.

DURING:
- Character already separated.
- Ready keeps consumer slot only.
- Planner and Learning Engine need the same pattern, but with finer split because Ready UX legitimately consumes them deeply.

AFTER:
- engines are independently owned and testable.
- apps consume projections/contracts.
- Ready remains important as Base Camp / execution orchestrator without becoming the entire Learning OS.
- Hide/Snap can evolve without importing Ready internals.
- integration can be validated through stable contracts.

## 8. Do NOT overcorrect

Do not:
- move Planner UI/TODAY/Mission/Focus out of Ready.
- move all code immediately just to match folders.
- make Learning engines Shared Technical Capability.
- centralize Work/Learning identities.
- turn every family experience capability into global TAKY.
- remove Ready as current session runtime coordinator before a replacement runtime exists.
- break validated current flows while correcting semantic ownership.

Semantic ownership correction precedes physical repository extraction.

## 9. Required canonical corrections — pending human-approved application

P0:
1. Add explicit Learning Domain Core to SYSTEM_LAYER_OWNERSHIP_MAP.
2. Reclassify Learning Engine semantic ownership from Ready -> Learning OS domain core.
3. Reclassify Planner Engine semantic ownership from Ready -> Learning OS domain core.
4. Clarify family identity/Parent-Child authority as Learning OS-owned; Ready = implementation/UI host only.
5. Clarify Assignment FACT lifecycle as Learning OS-owned; Ready = capture/review host.
6. Split session semantic owner vs current runtime coordinator.

P1:
7. Reclassify specialist routing policy into Learning Engine + Learning App Family composition.
8. Add Character Visual ID as separate family experience capability.
9. Mark world-entry intro/drop/voyage as deferred expansion capability.
10. Run legacy Guide -> 탐험대/탐험대원 terminology/source migration audit.

## 10. Evidence/state truth

AUDIT_COMPLETE = TRUE
CANONICAL_CORRECTION_APPLIED = FALSE
IMPLEMENTATION_EXTRACTION_COMPLETE = FALSE
READY_CURRENT_RUNTIME_PRESERVED = TRUE
CHARACTER_SEPARATION_STARTED = TRUE
PLANNER_SEPARATION = NOT_STARTED
LEARNING_ENGINE_SEPARATION = NOT_STARTED

This audit intentionally avoids false convergence.


## 11. User correction — Planner is an independent planning/progress manager
Date: 2026-09-22
Disposition: CORRECTION / P0 ARCHITECTURE UPDATE CANDIDATE

User correction:
Ready & Set is primarily an execution tool. Planner must be independently responsible for receiving schedule/event/assignment/homework inputs, producing and maintaining the plan, receiving progress/completion evidence back from execution tools, and continuously managing the combined plan state.

### Corrected ownership
PLANNER is NOT a Ready child module.
PLANNER is an independent semantic service under LEARNING_OS.

PLANNER owns:
- life events / commitments / academy schedules / fixed events
- assignment / homework scheduling inputs
- deadlines / recurrence / due windows
- available-time and capacity interpretation for planning
- weekly/daily plan composition
- DATED TODO planning semantics
- carry-over / rescheduling / reflow
- plan-vs-actual comparison
- progress / completion aggregation
- adaptive duration estimates
- forecast / next-plan continuity
- overall plan state across multiple execution apps

READY_SET owns:
- child-facing execution of a selected/planned work item
- TODAY/Mission/Focus/Result experience
- focus/timer interaction
- execution-state capture
- child adjustment/feedback UI within allowed planner constraints
- sending execution events/results back to Planner

READY_SET does NOT own:
- the global learning plan
- assignment/date authority
- schedule integration
- carry-over policy
- cross-app overall progress aggregation
- next-plan forecasting

### Corrected Planner event flow
INPUT SOURCES
- family/life schedule events
- academy/school events
- assignment/homework facts
- deadlines
- parent/child plan adjustments
- Learning Engine learning-unit estimates/recommendations

-> PLANNER
- reconcile commitments
- calculate available windows
- compose weekly/daily plan
- publish executable plan projection

-> READY / HIDE / SNAP / OTHER EXECUTION TOOLS
- execute relevant work
- emit progress / partial / completed / blocked / deferred / actual-time / help/check evidence

-> PLANNER
- aggregate actual progress
- maintain remaining work
- carry-over/reflow
- update estimates
- produce next executable projection

This is a closed planning loop, not a Ready-owned loop.

Canonical shorthand:
`EVENTS + ASSIGNMENTS + LEARNING UNITS -> PLANNER -> EXECUTION TOOLS -> PROGRESS/RESULT -> PLANNER -> NEXT PLAN`

### Relationship to Learning Engine
PLANNER and LEARNING_ENGINE are sibling semantic services under LEARNING_DOMAIN_CORE.

LEARNING_ENGINE answers:
- what the learner needs to learn/practice/review
- how a subject/task should be interpreted
- difficulty/load/review recommendation
- suggested learning unit size and specialist need

PLANNER answers:
- when/how much/in what order to place executable work within real-life constraints
- what remains, what moves, what is completed, and what happens next

Rule:
`LEARNING_ENGINE INTERPRETS LEARNING NEED; PLANNER MANAGES TIME/PLAN/PROGRESS; READY EXECUTES.`

### Corrected target hierarchy excerpt
```
LEARNING_OS
├─ LEARNING_IDENTITY_AUTHORITY
├─ LEARNING_DOMAIN_CORE
│  ├─ LEARNING_ENGINE
│  ├─ PLANNER_ENGINE   <-- independent service
│  ├─ ASSIGNMENT_FACT_DOMAIN
│  └─ LEARNING_HISTORY / EVIDENCE
└─ LEARNING_APP_FAMILY
   ├─ READY_SET        <-- execution tool / plan consumer
   ├─ HIDE_SEEK
   └─ SNAP_POP
```

### Implementation consequence
Current Ready planner code may be treated as an implementation-host snapshot only during extraction.
Repository location MUST NOT imply Planner semantic ownership.
Extraction should preserve behavior via a versioned Planner Projection / Event Contract before physical code movement.

Required contracts:
- PLANNER_INPUT_EVENT_V1
- PLANNER_PLAN_PROJECTION_V1
- EXECUTION_PROGRESS_EVENT_V1
- EXECUTION_RESULT_EVENT_V1
- PLANNER_REPLAN_EVENT_V1

Planner separation state: ARCHITECTURE_CORRECTED / CANONICAL_APPLICATION_PENDING / IMPLEMENTATION_EXTRACTION_NOT_STARTED


## 12. User correction — Apps consume multiple independent OS/domain services
Date: 2026-09-22
Disposition: CORRECTION / ARCHITECTURE MODEL EXPANSION

User correction:
Ready & Set / Hide & Seek / Snap & Pop must not be modeled as the primary system center.
There are multiple independent OS/domain services.
Apps consume, share through governed contracts, and return events/evidence to those services.

### Corrected conceptual model

TAKY is governance/orchestration.
Below TAKY are multiple first-class OS/domain-service owners.
Apps are execution/projection surfaces.

Candidate structure:

```
TAKY
├─ SHARED_TECHNICAL_CAPABILITY
│  └─ semantic-light infrastructure mechanisms
│
├─ WORK_OS
│
├─ LEARNING_OS
│  ├─ LEARNING_IDENTITY / AUTHORITY
│  ├─ ASSIGNMENT_FACT_DOMAIN
│  ├─ LEARNING_ENGINE
│  ├─ PLANNER_ENGINE
│  ├─ LEARNING_HISTORY / EVIDENCE
│  └─ LEARNING_APP_FAMILY CONTRACTS
│
├─ CHARACTER / VISUAL ID SERVICE
│  └─ independent identity-visualization capability with scoped learning-family integration
│
├─ EXPERIENCE / WORLD / EXPANSION SERVICES
│  └─ intro / world-entry / optional narrative experiences
│
└─ PROJECT / DOMAIN SERVICES AS NEEDED
```

The exact promotion of CHARACTER/WORLD to OS vs domain-service vs family-capability remains subject to owner analysis.
The key lock is that they are NOT implicitly subordinate to Ready.

### App role

```
READY_SET
- consumes Planner plan projection
- consumes Learning Engine context
- consumes scoped Learning Identity
- may consume Character Visual ID projection
- executes TODAY / Mission / Focus / Result
- emits progress/result/time/help/check events

HIDE_SEEK
- consumes Learning Engine language-memory context
- consumes scoped plan/task context when scheduled
- may consume Character/experience projections
- executes retrieval/memory specialist work
- emits memory/retrieval evidence

SNAP_POP
- consumes Learning Engine production/expression context
- consumes scoped plan/task context when scheduled
- owns exploration-crew product semantics where applicable
- executes expression/exploration work
- emits production/expression evidence
```

Apps do not directly mutate each other's semantic state.

### Exchange rule

Correct pattern:
`OWNER SERVICE -> VERSIONED PROJECTION/COMMAND -> APP -> EVENT/EVIDENCE -> OWNER SERVICE`

Cross-app sharing occurs through:
- shared domain owner,
- family contract,
- explicit projection/event,
not through implicit shared mutable app state.

Examples:
```
ASSIGNMENT_FACT -> PLANNER
LEARNING_ENGINE -> PLANNER
PLANNER -> READY/HIDE/SNAP
LEARNING_ENGINE -> READY/HIDE/SNAP
READY/HIDE/SNAP -> LEARNING_HISTORY
READY/HIDE/SNAP -> PLANNER progress
LEARNING_HISTORY -> LEARNING_ENGINE
CHARACTER_VISUAL_ID -> READY/HIDE/SNAP projection
```

### Horizontal service composition

A task may consume multiple services at once.

Example:
```
ASSIGNMENT FACT
 + LEARNING ENGINE interpretation
 + PLANNER placement
 + CHARACTER projection
 + FAMILY session contract
 -> READY execution

execution result
 -> PLANNER progress/replan
 -> LEARNING HISTORY
 -> LEARNING ENGINE adaptation
```

Therefore:
`ONE APP != ONE OWNER STACK`
`APP != OS`
`APP REPOSITORY != DOMAIN AUTHORITY`
`SHARED THROUGH CONTRACT != SHARED MUTABLE OWNERSHIP`

### Required architecture correction

The machine-readable owner map must eventually support:
1. vertical ownership hierarchy;
2. horizontal dependency/consumption edges;
3. event/projection return paths;
4. distinction between semantic owner, runtime host, UI host, and implementation repository;
5. service-to-app many-to-many relationships.

A pure tree is insufficient.
Target representation should be an ownership graph.

Suggested edge types:
- OWNS
- CONSUMES
- PUBLISHES_PROJECTION
- ACCEPTS_EVENT
- ROUTES_TO
- COORDINATES
- IMPLEMENTED_IN
- HOSTED_BY
- FEDERATES_WITH
- MUST_NOT_MUTATE

### Consequence for current Ready/Hide/Snap surgery

Ready:
- remove semantic ownership assumptions for Planner/Learning/Assignment/Family authority.
- retain execution UX and adapters.

Hide:
- retain specialist language-memory semantics.
- consume plan/learning projections without scheduling authority.

Snap:
- retain expression/exploration semantics.
- consume plan/learning projections.
- exploration-crew ownership remains Snap-origin unless explicitly transferred.

Planner/Learning/Identity/Character:
- develop and validate independently where their semantics are cross-app.
- integrate by versioned contracts.

Status:
ARCHITECTURE_GRAPH_CORRECTION = IDENTIFIED
TREE_ONLY_MODEL = INSUFFICIENT
CANONICAL_OWNER_MAP_UPDATE = PENDING
APP_EXTRACTION = NOT_STARTED


## 13. Architecture compass — Think Again, Keep Your Key
Date: 2026-09-22
Disposition: USER CORRECTION / GLOBAL ARCHITECTURE COMPASS

TAKY slogan:
`Think Again, Keep Your Key.`
`한 번 더 생각하고, 핵심은 놓치지 마.`

This is not branding only.
It is the architectural compass for TAKY-governed systems.

### Meaning for system structure

THINK AGAIN:
- do not freeze an early tree just because it once worked;
- re-evaluate ownership when implementation pressure distorts architecture;
- re-check upstream/downstream and before/after flow before extracting or integrating;
- allow multiple OS/domain services to evolve independently;
- allow better structures to supersede locally convenient but inverted dependencies.

KEEP YOUR KEY:
- preserve each system's semantic key/authority;
- Work OS must retain Work meaning and authority;
- Learning OS must retain Learning/family meaning and authority;
- TAKY must retain governance/orchestration/validation authority;
- apps/tools must not silently absorb upstream semantic ownership;
- integration must preserve provenance, owner, scope and return path.

Global rule:
`INTEGRATE WITHOUT COLLAPSING OWNERSHIP.`
`SHARE WITHOUT LOSING THE KEY.`
`ROUTE WITHOUT MAKING THE ROUTER THE OWNER.`
`HOST WITHOUT PROMOTING THE HOST TO AUTHORITY.`

### Corrected whole-system model

TAKY is not a monolithic super-app.
TAKY is the governance/orchestration/evidence/validation layer that coordinates multiple first-class OS/domain systems.

Candidate whole-system architecture:

```
TAKY CORE
├─ Governance / Authority
├─ Orchestration / Routing
├─ Evidence / Validation
├─ C2S / Handoff / Recovery
└─ Growth / Evolution

FIRST-CLASS OS / DOMAIN SYSTEMS
├─ WORK_OS
│  ├─ work identity / organization / role authority
│  ├─ project/workflow/task semantics
│  ├─ mail / source / document operations
│  ├─ architecture/cad/excel/public-data domains
│  └─ work-specific engines/services
│
├─ LEARNING_OS
│  ├─ learning identity / family authority
│  ├─ assignment fact
│  ├─ learning engine
│  ├─ planner engine
│  ├─ learning history/evidence
│  └─ learning-family session/contracts
│
├─ OTHER DOMAIN/OS SYSTEMS AS REAL NEED EMERGES
│  └─ only when semantic ownership is genuinely independent
│
└─ SHARED TECHNICAL CAPABILITY
   └─ semantic-light reusable mechanisms only
```

### Cross-OS relationship

Work OS, Learning OS and future OS/domain systems may consume technical mechanisms and exchange explicit projections/events where a real use case exists.

They SHALL NOT implicitly merge semantic authority.

Examples:
- same person may have Work identity and Learning-family identity, but these are not automatically the same authority object;
- a calendar transport may be shared technically, while Work schedule meaning and Learning planner meaning remain separate;
- a file/OCR mechanism may be shared while architectural-document meaning and homework FACT meaning remain separate;
- a notification transport may be shared while approval/action authority remains domain-owned.

Rule:
`SHARED MECHANISM != SHARED SEMANTIC OWNER.`
`CROSS-OS EVENT != CROSS-OS AUTHORITY.`

### TAKY relationship to OS systems

TAKY may:
- discover the applicable owner;
- route work;
- enforce evidence/validation rules;
- coordinate cross-OS handoff;
- detect conflicts;
- preserve correction lineage;
- trigger human approval when required.

TAKY must not:
- become the semantic owner of every OS/domain object;
- copy domain state into GRAND MASTER as a substitute for owner systems;
- centralize identity/permission semantics merely for convenience;
- turn orchestration into data ownership.

Rule:
`TAKY GOVERNS THE FLOW; OWNERS KEEP THE KEY.`

### Work OS correction implication

The same audit principle used for Learning OS must be applied to Work OS.

Review required:
- which capabilities are truly Work OS semantic owners;
- which are project/domain services under Work OS;
- which are only current implementation hosts;
- which should be independent reusable services;
- which are merely shared technical mechanisms.

Examples to review:
- mail operations
- Notion operations
- project/source registry
- architecture intelligence
- CAD/Excel automation
- public-data adapters
- document/report generation
- approval/submission workflows

Do not assume "currently in Work OS" means "Work OS must own all semantics forever."

### Required master-logic representation

A single parent-child tree is insufficient for the entire TAKY system.

Target model needs BOTH:

1. OWNERSHIP HIERARCHY
- who owns meaning / authority / lifecycle

2. INTERACTION GRAPH
- who consumes whose projection
- who emits events back
- who coordinates
- who hosts implementation
- who must not mutate another owner's state

Required graph edge classes:
- OWNS
- CONSUMES
- PUBLISHES_PROJECTION
- ACCEPTS_EVENT
- ROUTES_TO
- COORDINATES
- IMPLEMENTED_IN
- HOSTED_BY
- FEDERATES_WITH
- MUST_NOT_MUTATE

### Global stop condition

Before any further extraction/integration/rebuild:
1. identify semantic owner;
2. identify implementation host separately;
3. identify consumers;
4. identify input/output contracts;
5. identify event return path;
6. verify upstream/downstream impact;
7. preserve the owner's key.

If these cannot be stated clearly, architecture work is not ready to proceed.

Status:
GLOBAL_FLOW_CORRECTION = IDENTIFIED
LEARNING_ONLY_INTERPRETATION = REJECTED
WORK_OS_REVIEW = REQUIRED
TAKY_ROLE_REVIEW = REQUIRED
OWNERSHIP_GRAPH_MODEL = REQUIRED
