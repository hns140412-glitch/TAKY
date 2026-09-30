# TAKY EXPLORATION CREW CANONICAL

Status: REV_00 / ACTIVE CANONICAL SHARED CREW CONTRACT
Role: Shared Exploration Crew semantic/runtime contract for Ready & Set / Hide & Seek / Snap & Pop.
Authority: TAKY / GRAND MASTER > GUIDE FAMILY LEARNING OS > EXPLORATION CREW CANONICAL > project-specific crew presentation/behavior.

Source verification:
- Snap-Pop Draft PR #10 working implementation verified at commit `8ea7b985eaf792e866e4d21d174eaac824a23567`.
- `Validate Snap & Pop` SUCCESS.
- `Companion Onboarding Source/Asset Gate` SUCCESS.
- Central promotion includes shared contract only; Snap-specific UI, art binaries, release state and onboarding flow are excluded.

## 1. Core architecture — HARD LOCK

`EXPLORATION_CREW_CANONICAL_LOGIC`
→ `CHARACTER_BEHAVIOR_ENGINE`
→ `SEMANTIC_ACTION_COMMAND`
→ `ASSET_ENGINE`
→ `UI_RENDERER`

Responsibilities:
- Behavior Engine decides character, role, relation state, behavior state, interaction mode and semantic intent only.
- Semantic Action Command carries meaning without asset paths or image identity mutation.
- Asset Engine resolves only approved Visual ID / SHA / provenance / manifest compositions.
- UI Renderer places approved composition without changing behavior, relation or affinity meaning.

`BEHAVIOR MEANING != ASSET SELECTION`
`ASSET AVAILABILITY != RELATIONSHIP STATE`
`RENDERER != SEMANTIC OWNER`
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

## 6. Version contract — HARD LOCK

Current shared contract pointers:
- `contract_version = CREW_PIPELINE_V1`
- `manifest_version = CREW_COMPOSABLE_MANIFEST_V1`
- `runtime_schema_version = CREW_RUNTIME_TRACE_V1`

Consumer implementation shall fail closed when required pointers disagree.

## 7. Runtime trace minimum — HARD LOCK

Runtime trace shall be able to record:
- semantic_action_command
- selected_asset_composition
- fallback_reason when applicable
- renderer_result
- Behavior Gate verdict
- Asset Gate verdict
- Integration Gate verdict
- relation_mutated = false
- affinity_mutated = false
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

`OS/GUIDE_CHARACTER_RELATIONSHIP.md` owns shared character/relationship meaning.
This file owns crew behavior-to-asset runtime separation and shared crew composition gates.
`OS/GUIDE_FAMILY_LEARNING_OS.md` remains the higher Learning OS owner.
`MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md` owns cross-app family contract and inheritance.
Project canonical files own project-specific presentation and behavior.

When rules conflict:
higher authority and later explicit user correction prevail; project code shall not silently redefine this shared contract.

## 12. Current release boundary

Central semantic contract: ACTIVE.
Verified Snap working implementation evidence: PASS at cited exact commit.
Central promotion does not imply Snap main merge, ROOT activation, Netlify deployment, image generation or human visual approval.
