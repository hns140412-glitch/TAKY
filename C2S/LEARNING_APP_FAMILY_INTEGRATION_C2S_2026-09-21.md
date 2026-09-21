# LEARNING APP FAMILY — INTEGRATION C2S — 2026-09-21

Status: INTEGRATION_IMPLEMENTATION_CLOSED_BRANCH_VERIFIED__DEVICE_PRODUCTION_OPEN
Scope: TAKY → Learning OS → Learning App Family → Ready & Set / Hide & Seek / Snap & Pop

## 1. Live source baseline

### TAKY
- repo: hns140412-glitch/TAKY
- baseline main before this C2S: `3381dd4482b52a1362b1d4595a5e3825c4a05b77`
- master-logic realization closure: VALIDATED_CLOSURE

### Ready & Set
- repo: hns140412-glitch/Ready-Set
- authoritative runtime baseline: main
- current main: `98df214a6078f16f2b6710016898a4d7798798db`
- R1 session ownership consolidation: merged / targeted CI+runtime verified
- R4 Child FACT → Parent Confirm: merged / targeted verified
- R5 daily + weekly confirmed availability → Planner free-window: merged / targeted verified
- R6 legacy authority isolation: merged / targeted verified
- DEVICE / PRODUCTION: not asserted

### Hide & Seek
- repo: hns140412-glitch/Hide-Seek
- active development branch: `implementation/hide-seek-capture-session-v02`
- current branch head: `7136c22b23e05b5f902a15f7e421d79aeb7a8574`
- relation to main: ahead 526 / behind 0
- PR #4: DRAFT / HOLD / DO NOT MERGE
- product owner: Language Memory & Meaning Engine
- deploy / Netlify: prohibited in current branch scope

### Snap & Pop
- repo: hns140412-glitch/Snap-Pop
- active development branch: `taky/snap-pop-implementation-2026-09-20`
- current branch head: `3af4d5076ed464b43c7f8e3fa60f7612539376fe`
- relation to main: ahead 584 / behind 3 / DIVERGED
- current work is branch-only; previous frozen candidate superseded
- deploy / Netlify: not authorized

## 2. Cross-app architecture lock

Learning App Family contract remains:

`ONE LEARNING JOURNEY / READY SESSION OWNER / SPECIALIST TASK OWNERSHIP`

- Ready = session / task routing / Planner / DATED TODO owner.
- Hide = vocabulary/language-memory specialist.
- Snap = thought/expression/writing/speaking specialist.
- specialist completion may complete a task/lap only.
- specialist app SHALL NOT complete the Ready session.
- APP_SWITCH != SESSION_END.
- APP_SWITCH != automatic PAUSE.
- Ready maintains at most one Planner task IN_PROGRESS and at most one active lap.

Shared transport IDs:
- session_id
- goal_id
- task_id
- lap_id
- return_target

These IDs are correlation/orchestration identity only. They do not transfer domain authority.

## 3. Integration findings

### GAP-INT-001 — CLOSED — Learning context producer/consumer chain

Current evidence:
- Snap active branch has a fail-closed `READY_LEARNING_CONTEXT_V1` decoder and LearningContextProvider.
- Snap handoff says Ready supplies minimal FACT_CONFIRMED learning context.
- Ready current `launchSpecialist()` sends session/goal/task/lap/return_target but does NOT send `learning_context`.
- Hide active branch does not currently expose an equivalent `READY_LEARNING_CONTEXT_V1` decoder; its shared context is generic query-param projection.

Conclusion:
`DOCUMENTED_BRIDGE != END_TO_END_IMPLEMENTED_BRIDGE`

Required downstream work:
1. Define one Learning App Family owned `READY_LEARNING_CONTEXT_V1` contract.
2. Ready constructs it from the active Planner/Learning Unit lineage.
3. Ready sends it only when source FACT/Learning Unit evidence exists.
4. Snap keeps its current consumer, aligned to the central contract.
5. Hide adds a consumer of the same resolved context.
6. Context is advisory learning metadata, not authority transfer.

Minimum payload:
- contract_version
- learning_unit_id
- analysis_id
- assignment_id
- subject
- concept_skill_target
- activity_types
- cognitive_load_profile
- confidence
- unresolved_flags

Forbidden:
- Parent/Child permission transfer
- DATED TODO allocation authority transfer
- Hanja grade inference inside Hide
- specialist mutation of Ready FACT / Learning Master

### GAP-INT-002 — CLOSED — HELP_NEEDED semantic correction at Ready return

Current evidence:
- Hide and Snap can emit `HELP_NEEDED`.
- Ready canonical result model distinguishes `WAITING_FOR_PARENT` from `BLOCKED`.
- Ready `normalizeInboundState()` currently maps `HELP_NEEDED → BLOCKED`.

Conclusion:
This collapses two different learner states and loses semantics.

Required correction:
- `HELP_NEEDED → WAITING_FOR_PARENT`
- explicit `TASK_BLOCKED/BLOCKED → BLOCKED`
- preserve specialist provenance/event id.
- carry-over / Parent review must use the normalized Ready state without overwriting specialist evidence.

### GAP-INT-003 — CLOSED BY CAPABILITY RECONCILIATION — Snap shared-foundation divergence

Current evidence:
- active Snap branch: +584 / -3 relative to main.
- missing main-side reconciliation includes:
  - current README authority pointer/status,
  - shared release/PWA runtime,
  - shared event-envelope runtime/provenance.

Risk:
A direct merge/rebase after continued feature accumulation can create a large conflict surface or silently regress shared runtime rules.

Required correction:
- do NOT blind rebase 584-commit branch.
- perform a bounded reconciliation branch from current active Snap head.
- port the 3 missing main changes by capability, not by broad history rewrite.
- run Snap branch closure validators + shared runtime contract/browser gates after reconciliation.
- only then declare a new frozen candidate.

### GAP-INT-004 — Hide language-memory ownership must stay separate from Learning Engine

Locked correction already present in Hide handoff:
- Language Memory != homework / assignment / Hanja grade.
- Ready Learning Engine owns homework interpretation, Learning Unit, and Hanja grade/level resolution.
- Hide consumes resolved learningContext.
- Hide owns cumulative language-memory evidence / Memory Ladder.
- Hide SHALL NOT infer Hanja grade independently.

Integration action:
Encode this in the central learning-context contract and regress it.

### GAP-INT-005 — Hide → Snap vocabulary bridge is aligned and should remain source-owned

Current Snap branch:
- vocabulary material contract preserves `sourceOwner`.
- role = EXPRESSION_MATERIAL_ONLY.
- autoInsertAllowed=false.
- masteryMutationAllowed=false.
- vocabularyOwnershipTransferred=false.

Disposition:
PRESERVE.
Snap may use Hide vocabulary as expression material but cannot claim mastery or rewrite Hide memory state.

### GAP-INT-006 — Badge/crew shared events must remain semantic-light

Current Snap branch has badge observation/shared-event work.

Disposition:
PRESERVE WITH BOUNDARY.
- shared technical event envelope is acceptable;
- badge award/economy/catalog activation remains Snap/domain-owned;
- family identity/role/permission is not commonized;
- working badge catalog remains inactive until separately approved.

## 4. Implementation order

P0 — Freeze integration contract, not product branches.
- this C2S is the central contract for next work.

P1 — Ready return-state correction.
- HELP_NEEDED → WAITING_FOR_PARENT.
- focused regression + Ready Integration + Runtime E2E.

P2 — READY_LEARNING_CONTEXT_V1 producer.
- implement in Ready.
- no new authority semantics.

P3 — Hide learning-context consumer.
- consume resolved context only.
- preserve Language Memory ownership.
- no Hanja-grade inference.

P4 — Snap learning-context contract alignment.
- compare current decoder against central contract.
- change only if needed.

P5 — Snap shared-foundation reconciliation.
- reconcile 3 missing main capabilities into active 584-commit branch.
- no broad rebase.
- full branch closure + shared runtime tests.

P6 — Cross-app contract regression.
Verify:
Ready → Hide → Ready
Ready → Snap → Ready
Ready → Hide → Snap → Ready
with preserved:
session_id / goal_id / task_id / lap_id / return_target
and exactly one Ready active Planner task.

P7 — Only after P1-P6:
- update each app C2S/handoff
- evaluate frozen candidate(s)
- external/deploy gate separately
- DEVICE/PRODUCTION remains independent.

## 5. Current positive alignment

PASS / PRESERVE:
- Ready owns session.
- specialist apps return task-level events.
- session/goal/task/lap identifiers are already shared.
- Hide active branch includes latest main shared foundation (behind 0).
- Snap preserves Hide vocabulary source ownership.
- Snap child-authorship guard aligns with Learning App Family boundaries.
- shared technical capability rules remain semantic-light.
- no current evidence justifies globalizing family identity/authority.

## 6. Claim boundary

This review does NOT claim:
- cross-app runtime verified,
- device verified,
- production verified,
- Snap current active branch reconciled,
- learning_context end-to-end implemented,
- hosted deployment approval.

## 7. C2S closure

Within this integration-review scope:
- UNMAPPED_MATERIAL = 0
- SILENT_LOSS = 0
- FALSE_CONVERGENCE = 0
- CORRECTION_PROPAGATION = COMPLETE for the gaps listed above
- DOWNSTREAM_IMPLEMENTATION_COMPLETE = true for P1-P7 branch-only integration scope

END


## 8. Final branch-only implementation closure — 2026-09-21

Central contract:
- `MASTER/READY_LEARNING_CONTEXT_V1.json`
- owner: Learning App Family
- producer: Ready & Set
- consumers: Hide & Seek / Snap & Pop
- semantic-light advisory metadata only.

Exact verified code heads used by the central cross-app regression:
- Ready & Set: `8f2c097ae52fcb53b22ca9bc0f9a867ff660dc48`
- Hide & Seek integration v3: `5ff6a4a4e6b65588acf4c8da503411320365b900`
- Snap & Pop integration v2: `a720b5d35e096feda9b83bc88ffe5d06f89b3ed2`

P1-P7:
- P1 Ready HELP_NEEDED / BLOCKED semantics: COMPLETE.
- P2 Ready READY_LEARNING_CONTEXT_V1 producer: COMPLETE.
- P3 Hide resolved-context consumer / ownership boundary: COMPLETE.
- P4 Snap consumer alignment: COMPLETE.
- P5 Snap README + shared release/PWA + event-envelope capability reconciliation: COMPLETE without broad rebase.
- P6 cross-app contract regression: COMPLETE.
- P7 TAKY + Ready + Hide + Snap C2S/handoff synchronization: COMPLETE.

Cross-app regression paths:
- Ready -> Hide -> Ready: PASS.
- Ready -> Snap -> Ready: PASS.
- Ready -> Hide -> Snap -> Ready: PASS.

Locked invariants re-verified:
- session_id / goal_id / task_id / lap_id / return_target preserved.
- HELP_NEEDED -> WAITING_FOR_PARENT.
- explicit BLOCKED -> BLOCKED.
- Ready Planner IN_PROGRESS <= 1.
- specialist completion != Ready SESSION_END.
- Hide Language Memory != assignment / homework / Hanja grade.
- Hanja grade/level resolution remains Ready Learning Engine authority.
- Hide vocabulary remains source-owned expression material in Snap.
- autoInsert=false / masteryMutation=false / vocabularyOwnershipTransferred=false.
- shared release/PWA/event mechanisms do not transfer family identity, role or permission authority.

Verification state:
- CODED: YES for P1-P6 integration implementation.
- CI_VERIFIED: YES.
- RUNTIME_VERIFIED: YES at each app integration runtime plus central executable cross-app contract harness.
- DEVICE_VERIFIED: NO / NOT_RUN.
- PRODUCTION_VERIFIED: NO / NOT_RUN.
- Netlify / hosted deployment: NOT_RUN for this integration task.
- merge to product main branches: NOT_RUN.

Important:
The exact verified SHAs above are integration evidence points, not permission to overwrite newer active product development.
Before any future edit, refresh live HEAD and carry integration capabilities forward by delta only.

END FINAL INTEGRATION CLOSURE
