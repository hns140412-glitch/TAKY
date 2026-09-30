# TAKY EXPLORATION CREW CANONICAL

Status: REV_02 / DRAFT RUNTIME V2 CUTOVER CANDIDATE — ACTIVE MAIN REMAINS AUTHORITY UNTIL MERGE
Role: Shared Exploration Crew semantic/runtime contract for Ready & Set / Hide & Seek / Snap & Pop.
Authority: TAKY / GRAND MASTER > GUIDE FAMILY LEARNING OS > EXPLORATION CREW CANONICAL > project-specific crew presentation/behavior.

Source verification:
- Explorer Crew Runtime V2 is implemented as one shared runtime spine with project-thin consumers in Snap / Hide / Ready Draft branches.
- Exact current candidate heads and CI evidence are recorded in `AUDIT/EXPLORER_CREW_CENTRAL_CORRECTION_PACKET_20261001.md`.
- The shared common runtime is protected by a 34-file Source Lock.
- Source Lock hashing is SHA-256 over UTF-8 text after CRLF/LF → LF normalization so content identity is OS-independent.
- Central promotion includes shared contract only; project UI, art binaries, release state and deployment remain project-owned and separately gated.

## 1. Core architecture — HARD LOCK

`EXPLORATION_CREW_CANONICAL_LOGIC`
→ `CHARACTER_BEHAVIOR_ENGINE`
→ `SEMANTIC_ACTION_COMMAND`
→ `RUNTIME_POLICY` (thin arbitration only)
→ `DIALOGUE / SCENE`
→ `MANIFEST → ASSET_ENGINE`
→ `UI_RENDER_PLAN`
→ `INTERACTION / RELATION / MEMORY UPDATE`
→ `UNIFIED_RUNTIME_TRACE`

Responsibilities:
- Behavior Engine decides character, role, relation state, behavior state, semantic interaction and semantic intent only.
- Semantic Action Command carries meaning without asset paths or image identity mutation.
- Runtime Policy is thin arbitration only: reaction budget, scene slot, recent-action repetition suppression, interruptibility, dialogue-intent rotation and cooldown/selection-reason trace. It SHALL NOT become Behavior Engine.
- Dialogue / Scene consumes the arbitrated semantic result without redefining relationship or behavior meaning.
- Asset Engine resolves only approved Visual ID / SHA / provenance / manifest compositions.
- UI Render Plan/UI Renderer places approved composition without changing behavior, relation or affinity meaning.
- Interaction / relation / memory updates remain evidence-owned state transitions and are not asset or renderer side effects.
- Unified Runtime Trace records the end-to-end decision and gate evidence.

`BEHAVIOR MEANING != ASSET SELECTION`
`ASSET AVAILABILITY != RELATIONSHIP STATE`
`RENDERER != SEMANTIC OWNER`

## 1.1 Semantic interaction and delivery axes — HARD LOCK

Semantic interaction axis:
- `SILENT`
- `TALK`
- `LISTEN`
- `GUIDE`

Delivery axis:
- `NONE`
- `TEXT`
- `VOICE`
- `TEXT_AND_VOICE`

Rules:
- semantic interaction and delivery are independent fields;
- `SILENT` requires `NONE`;
- active `TALK` / `GUIDE` requires explicit non-`NONE` delivery;
- `LISTEN` may use `NONE`;
- compatibility adapters may translate transport shape but SHALL NOT redefine semantic meaning;
- unsupported behavior/action states fail closed and SHALL NOT be force-mapped.

## 2. Ambient behavior contract — HARD LOCK

Minimum Ambient actions:
- READ_BOOK
- READ_MAP
- WRITE_NOTE
- CHECK_COMPASS
- ORGANIZE_BAG
- USE_MAGNIFIER
- USE_RADIO
- REST

A project may add project-owned actions only if they do not redefine these shared meanings or bypass the shared gates.

## 3. Composable asset contract — HARD LOCK

Per Visual ID groups:
- MASTER_FULL
- PROFILE
- PUPPET_BODY
- FACE_STATES
- ACTION_PARTS
- PEEK_MASK
- DEPTH_SHADOW

Shared equipment:
- BOOK
- MAP
- NOTEBOOK
- PEN
- RADIO
- MAGNIFIER
- BAG
- COMPASS

Character art, background art, shared FX and dialogue UI remain separable asset concerns.
## 4. Source and fallback safety — HARD LOCK

Required provenance before an asset may be consumed:
- immutable Visual ID
- approved source
- source SHA verification
- approval reference
- asset manifest registration

Rules:
- Name/code-only image generation is prohibited.
- Missing parts do not authorize generation.
- Visual ID/source SHA mismatch = FAIL CLOSED.
- Cross-character part substitution is prohibited.
- Relation/affinity shall not select unapproved visual state.
- Asset availability shall not mutate relation/affinity.
- Runtime fallback shall never manufacture art.

Safe fallback:
`SAME CHARACTER ONLY → PUPPET_BODY:FIELD_NEUTRAL + FACE_STATES:neutral + approved depth`

No equipment or action part is added when fallback is caused by a missing/unapproved required part.

## 5. Three gates — HARD LOCK

Behavior Gate:
- valid character / role / relation / behavior / interaction mode
- Ambient action valid only under Ambient behavior
- no asset path, PNG, source SHA or Visual ID mutation fields in semantic command
Asset Gate:
- Visual ID matches character
- source SHA verified
- approval reference present
- selected character parts approved
- same-character part ownership
- shared equipment approved
- fallback is same-character neutral
- generated asset prohibited

Integration Gate:
- semantic command preserved
- asset plan does not alter behavior meaning
- relation/affinity unchanged
- renderer receives no unapproved asset
- missing-part fallback creates no new art

`LOGIC PASS != RUNTIME PASS != INTEGRATION PASS != RELEASE PASS`

Promotion separation:
- `STATIC_APPROVED_ONLY`
- `COMPOSABLE_ACTION_APPROVED`
- `MOTION_RENDER_PLAN_READY`

These are independent gates. `motionReady != releasePass != ROOT activation`.

## 6. Version contract — HARD LOCK

Current shared contract pointers:
- `contract_version = CREW_PIPELINE_V1`
- `manifest_version = CREW_COMPOSABLE_MANIFEST_V1`
- `runtime_schema_version = CREW_RUNTIME_TRACE_V2`

Consumer implementation shall fail closed when required pointers disagree.

## 6.1 Runtime V2 ownership and Source Lock — HARD LOCK

Runtime V2 owner:
- `EXPLORER_CREW_SYSTEM_V2` is the single canonical runtime owner.
- canonical ownership state is `runtime = CANONICAL_ONLY`.
- App consumers SHALL report `behaviorOwner=false`, `relationOwner=false`, `memoryOwner=false`, `assetResolver=false`, `runtimeOwner=false`.
- Ready / Hide / Snap adapters are thin project edges only. They may project app context and render approved plans, but SHALL NOT recreate shared behavior, relation, memory, Runtime Policy or asset ownership.

Shared-source identity:
- Snap / Hide / Ready SHALL consume the same source-locked common Explorer Crew runtime bundle.
- current Source Lock scope = 34 common runtime/contract files.
- hash algorithm = SHA-256.
- text normalization = UTF-8 with CRLF/LF normalized to LF before hashing.
- missing locked file, changed normalized content, or unexpected common-runtime file = FAIL CLOSED.
- Source Lock equality proves common runtime content identity only; it does not imply release approval, main merge, ROOT activation, composable promotion or motion promotion.

## 7. Runtime trace minimum — HARD LOCK

Runtime trace shall be able to record:
- behavior decision
- semantic_action_command
- semantic interaction mode
- delivery mode
- Runtime Policy decision / rejection reason
- scene slot / interruptibility / cooldown / reaction budget
- selected_asset_composition
- selected Visual ID / source SHA / asset status
- fallback_reason and composition readiness when applicable
- UI render-plan state
- renderer_result
- Behavior Gate verdict
- Asset Gate verdict
- Integration Gate verdict
- relation_changed / memory_changed / persistence status
- embedded compatible legacy/PR trace when conversion is valid
- relation_not_owned_by_asset = true
- memory_not_owned_by_asset = true
- runtime_policy_not_behavior_owner = true
- motion_ready_does_not_imply_release = true
## 8. Legacy 3+6 contract

Legacy slots:
`IDENTITY_BODY / PERSONALITY_PROP / THEME_GEAR / OBSERVE / LISTEN / IDEA / REACT / WAIT / COMPLETE`

State:
`LEGACY_3_PLUS_6_ASSET_CONTRACT_HOLD_PENDING_COMPOSABLE_ASSET_MIGRATION`

Rules:
- production authority = false
- regression-only preservation
- mass production prohibited
- do not delete until composable regression proof is stable
- 24×9=216 shall not be treated as current final-art production target

## 9. Ownership boundary

Central TAKY owns:
- shared crew semantics
- shared engine boundaries
- shared gate contract
- version/trace contract
- cross-app inheritance boundary

Specialist asset pipeline owns:
- production state
- work queue
- cutout/mask/art/QA progression

TAKY-ASSETS owns:
- approved binary results
- immutable hashes
- provenance
- consumer pointers

App runtime owns:
- consuming verified pointers
- project-specific rendering/integration
- never manufacturing missing art
Ready / Hide / Snap remain owners of project-specific:
- scene presentation
- project interaction
- dialogue/performance details
- approved screen composition
- project release decision

## 10. Non-centralized scope

This Canonical does not centralize:
- Snap onboarding screen flow
- Snap ROOT UI
- project-specific dialogue
- project-specific reward/world rules
- unapproved character art
- deployment/Netlify state
- project release approval

## 11. Relationship with other canonical owners

`OS/GUIDE_CHARACTER_RELATIONSHIP.md` owns shared character/relationship meaning, including the 24-person relationship/Main lifecycle, first-encounter boundary, evidence/Story Gate eligibility and personality provenance classes.
This file owns crew behavior-to-asset runtime separation and shared crew composition gates.
`OS/GUIDE_FAMILY_LEARNING_OS.md` remains the higher Learning OS owner.
`MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md` owns cross-app family contract and inheritance.
Project canonical files own project-specific presentation and behavior.

When rules conflict:
higher authority and later explicit user correction prevail; project code shall not silently redefine this shared contract.

## 12. Current release boundary

Central semantic contract: DRAFT V2 CUTOVER CANDIDATE.
Verified Runtime V2 evidence spans Snap / Hide / Ready Draft consumers and the shared Source Lock; exact heads and CI status are recorded in the audit packet.
Central promotion does not imply any project main merge, ROOT activation, Netlify deployment, image generation, composable production promotion, motion release or human visual approval.
