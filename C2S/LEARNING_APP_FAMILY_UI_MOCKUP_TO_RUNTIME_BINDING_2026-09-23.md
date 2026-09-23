# LEARNING APP FAMILY — MOCKUP → RUNTIME BINDING CONTRACT — 2026-09-23

Status: HARD_LOCK / ENFORCED IMPLEMENTATION GATE
Authority:
- C2S/TAKY_TOP_LEVEL_EXECUTION_PRINCIPLES_CANONICAL_2026-09-23.md
- C2S/LEARNING_APP_FAMILY_INTEGRATED_LOGIC_UI_CANONICAL_2026-09-22.md
- C2S/LEARNING_APP_FAMILY_UI_VISUAL_BASE_DELTA_MAP_2026-09-23.md

Purpose:
prevent high-fidelity approved mockups from degrading into unrelated generic runtime UI.

## 1. Core rule

APPROVED MOCKUP != DECORATIVE REFERENCE.

An approved mockup becomes a runtime implementation anchor only after it is converted into:

`VISUAL_ANCHOR`
→ `SCREEN_PURPOSE`
→ `COMPONENT_MAP`
→ `LAYOUT_ZONES`
→ `VISUAL_TOKENS`
→ `STATE / EVENT CONTRACT`
→ `MOTION CONTRACT`
→ `RUNTIME SCREENSHOT CHECK`.

Implementation may adapt to real data and interaction states, but it may not silently replace the visual grammar.

## 2. Required binding packet per approved screen

Each screen must have all of the following before implementation can be called UI-complete:

- ANCHOR_ID
- APPROVED_VISUAL_SOURCE
- FLOW_STEP
- SCREEN_PURPOSE
- REQUIRED_COMPONENTS
- FORBIDDEN_COMPONENTS
- LAYOUT_ZONES
- CHARACTER / CREW SLOT RULE
- BACKGROUND / WORLD CONTEXT RULE
- PRIMARY CTA
- SECONDARY ACTIONS
- MOTION / DEPTH RULE
- REDUCED-MOTION FALLBACK
- DATA BINDING
- NON-HAPPY STATES
- 390x844 SCREENSHOT BASELINE
- REGRESSION CHECKLIST.

Missing packet = IMPLEMENTATION_NOT_READY.

## 3. Global visual invariants

For current Learning App Family onboarding lineage:

- baseline = 390 × 844 portrait
- full-bleed illustrated world / preparation-space background where the flow calls for it
- functional surfaces may be translucent/frosted/paper-like but must not erase the world
- no generic dashboard/card-wall replacement
- no arbitrary white full-screen form shell
- no unrelated 5-tab navigation
- one dominant primary CTA
- Crew/User Character must appear from locked runtime assets, not redrawn ad hoc
- accepted warm cinematic travel-preparation material language must survive implementation
- UI density may be reduced for usability, but hierarchy and scene identity must remain recognizable.

Rule:
`SIMPLIFY CONTENT DENSITY IF NEEDED; DO NOT SIMPLIFY AWAY THE ART DIRECTION.`

## 4. Character Formation preparation-space anchor

Current accepted world premise:
CHARACTER FORMATION = BEFORE-TRAVEL PACKING / PREPARATION SPACE.

Not:
- already on island
- already at Base Camp
- generic fantasy town
- generic classroom
- generic dashboard.

Island appears only as destination hints:
- postcard
- map
- photo
- distant view
- travel note.

The preparation room / packing surface remains the dominant context until world-entry stages.

## 5. Core 6 runtime identity binding

Core 6:
두비 / 로리 / 잉크 / 노바 / 테이크 / 제로.

Runtime UI MUST bind to approved Visual ID assets.

A component may change:
- expression
- pose
- gesture
- action
- screen position
- short dialogue / reaction.

It may not change:
- species
- face
- silhouette
- body proportion
- identity markings
- canonical clothing/equipment structure
- identity palette.

If the exact approved runtime asset is unavailable:
PLACEHOLDER / BLOCKED > INVENTED CHARACTER.

## 6. Current onboarding implementation sequence

1. Crew familiarity
2. Primary companion selection
3. Companion display name / nickname
4. User photo
5. Signature Item
6. Direction Round 1
7. Direction Round 2
8. System auto-contrast
9. A/B/C same-child result
10. A/B/C selection
11. likeness correction
12. Visual ID confirm
13. Shared Expedition Accent
14. Voyage / Drop
15. Island discovery
16. Island naming
17. Base Camp move
18. Base Camp naming
19. Ready entry

A runtime screen must not regress to a previously completed step.

## 7. Signature Item binding — CURRENT NEXT IMPLEMENTATION ANCHOR

FLOW_STEP = SIGNATURE_ITEM.

Required options:
- 카메라
- 나침반
- 탐험 노트
- 쌍안경
- 물병

Exactly one active selection.

Required visual structure:
- preparation-space background persists
- selected primary companion may remain as contextual guide
- item picker is the functional protagonist
- five item choices clearly differentiated
- selected state visible without relying only on animation
- primary CTA = next Direction Round 1
- progress indicator active at Signature Item.

Forbidden:
- photo capture panel
- example child photos
- camera/gallery upload controls
- companion personality re-selection
- completed user Character
- island-arrival composition.

## 8. Layout parity gate

Runtime does not need pixel-for-pixel duplication of generated art, but the following must remain within the same hierarchy:

A. WORLD / BACKGROUND
- visible behind functional surface
- not replaced by blank background

B. CHARACTER / CREW CONTEXT
- upper or mid visual anchor
- does not cover task controls

C. TASK SURFACE
- dominant functional area
- visually integrated with preparation-space art direction

D. PRIMARY CTA
- visually dominant
- near lower action zone
- not buried in nav/card noise

E. FLOW PROGRESS
- visible but subordinate
- current step accurate.

A runtime screenshot that preserves text but loses A–E = VISUAL REGRESSION.

## 9. Motion/depth parity

Approved motion language:
- micro-motion, not constant bouncing
- character action layer only
- sensor parallax optional
- character-only sensor depth is default safe tier
- background full-depth only after performance profile pass
- reduced-motion keeps all hierarchy without required movement.

Motion must enhance the accepted composition.
It must not be used to excuse a different layout.

## 10. Screenshot regression gate

At 390×844, implementation review must compare:

- screen purpose
- background/world continuity
- character identity
- major composition zones
- dominant CTA
- selected state
- progress-step accuracy
- typography hierarchy
- functional surface opacity / world visibility
- no stale or invented navigation.

Status categories:
- PASS
- PASS_WITH_MINOR_DELTA
- FAIL_VISUAL_REGRESSION
- FAIL_SEMANTIC_REGRESSION
- BLOCKED_ASSET_BINDING.

A screen cannot be marked UI_COMPLETE with either FAIL status.

## 11. Implementation completion definition

UI_COMPLETE requires all three:

`FUNCTIONAL_CONTRACT_PASS`
+
`VISUAL_BINDING_PASS`
+
`SCREENSHOT_REGRESSION_PASS`.

CODE EXISTS != UI COMPLETE.
HIGH-FI MOCKUP EXISTS != UI COMPLETE.
CI GREEN != VISUAL COMPLETE.

## 12. Human burden rule

The user must not be the regression detector.

Before presenting a runtime screen:
- compare it internally to the bound anchor;
- reject obvious drift;
- correct it before user review.

`USER != DEBUGGER`.

Think Again, Keep Your Key.
Think Again, You're The Key.


## 13. Assetization / result-presentation rule — 2026-09-23

Approved mockups are executable visual anchors, not full-screen runtime assets.

Required implementation path:

`APPROVED MOCKUP`
→ `SCENE DECOMPOSITION`
→ `HIGH-DENSITY INDIVIDUAL ILLUSTRATION ASSETS`
→ `APP ASSETS FOLDER`
→ `LIVE DOM/CSS COMPOSITION`
→ `MOTION / SENSOR DEPTH`
→ `390×844 RUNTIME SCREENSHOT`
→ `ANCHOR COMPARISON`.

Forbidden:
- crop a complete approved mockup and ship it as a screen/background;
- bake functional buttons/text/progress/selected state into a screenshot;
- ignore an approved anchor and produce a generic runtime form;
- claim UI quality from a mockup when the actual runtime has not been compared.

Asset layers should be separable where the scene requires:
- background/world;
- Crew/Character;
- task-specific object/item;
- foreground occlusion props;
- texture/surface;
- light/shadow/FX.

The actual application result presented for approval must be the runtime composition whenever implementation is the task.

A new high-fi mockup is allowed only for:
- an unresolved screen with no accepted base; or
- an explicit DELTA that cannot be resolved from the current approved anchor.

This is a direct consequence of:
`Think Again, Keep Your Key.`
→ preserve the accepted visual/product key.

`Think Again, You're The Key.`
→ carry the accepted result through to executable implementation instead of transferring regression detection to the user.


## 14. LOCK STATE — 2026-09-23

`MOCKUP_TO_RUNTIME_METHOD = HARD_LOCK`

Authority:
latest explicit user instruction.

Locked pipeline:
`APPROVED VISUAL → ANCHOR BINDING → DECOMPOSED ASSETS → ASSETS FOLDER → LIVE UI → MOTION/DEPTH → 390×844 RUNTIME CAPTURE → REGRESSION CHECK`.

Forbidden substitutions:
- full-screen mockup crop as implementation;
- generic UI shell replacing approved art direction;
- recreating locked Crew/Character identity;
- showing a newly generated mockup as proof of implemented UI;
- skipping runtime screenshot comparison;
- silently resetting to a previous flow step.

Completion:
`FUNCTIONAL_CONTRACT_PASS + ASSET_BINDING_PASS + VISUAL_BINDING_PASS + SCREENSHOT_REGRESSION_PASS`.

Reopen:
`EXPLICIT_USER_REOPEN_ONLY`.

Any conflicting downstream instruction is STALE unless it is a later explicit user correction.


## 15. PRE-OUTPUT RULE APPLICATION GATE — HARD LOCK

Before generating, editing, implementing, or presenting a Learning App Family UI/visual result, state the exact rule application brief first.

Required brief:
- source / approved anchor;
- locked Visual ID or accepted lineage;
- current flow step;
- invariants to preserve;
- exact DELTA;
- forbidden regression;
- validation check that will be used.

Execution:
`RULE BRIEF → BUILD → COMPARE → CORRECT → PRESENT`.

For Core 6 work, the brief must explicitly name the locked member(s) and state that species / face / silhouette / proportion / identity markings / canonical clothing structure will not be reinterpreted.

For approved UI work, the brief must explicitly state whether the output is:
- REFERENCE ASSET,
- DECOMPOSED RUNTIME ASSET,
- LIVE RUNTIME UI,
- or VALIDATION EVIDENCE.

A full-screen board, concept sheet or newly interpreted character cannot silently substitute for a requested runtime asset.

If the generated result contradicts the declared brief:
`RESULT = REJECT`
and it must not be promoted to an approved anchor or runtime asset.

`RULE_FIRST_OUTPUT_SECOND = HARD_LOCK`
`EXPLICIT_USER_REOPEN_ONLY`.


## 16. CORE 6 DERIVATIVE SOURCE BINDING — HARD LOCK

Core 6 Visual ID derivatives must be generated from the exact canonical Visual ID reference image, not from a text description of the character.

`CANONICAL VISUAL ID IMAGE → DERIVATIVE EDIT / PROJECTION`

Forbidden:
- text-only re-generation of a locked Core 6 member;
- using a stale or legacy species/version as a source candidate;
- synthesizing a “similar” character and treating it as the same Visual ID;
- mixing multiple historical variants into a new interpretation.

Allowed delta only:
- expression;
- pose;
- gesture;
- action;
- screen position;
- contextual prop interaction.

Identity layers remain immutable:
- species;
- face;
- silhouette;
- body proportion;
- identity markings;
- fur / primary identity color;
- canonical clothing structure;
- canonical equipment structure.

If the exact canonical reference cannot be bound into the generation/edit process:
`BLOCKED_ASSET_BINDING`
and generation must stop.

If a derivative mismatches:
`DERIVATIVE = REJECT`
`CORE6_VISUAL_ID = REMAINS_HARD_LOCK`

Reopen:
`EXPLICIT_USER_REOPEN_ONLY`.


## 17. EXISTING BIND MUST BE CONSUMED — CORRECTION — 2026-09-23

Correction:
Core 6 canonical Visual ID binding already exists and is HARD LOCKED.

Therefore the failure mode is not automatically `BLOCKED_ASSET_BINDING`.

Correct classification:

`CANONICAL_BIND = EXISTS`
+
`GENERATION CALL DOES NOT CONSUME BIND`
=
`EXECUTION_BINDING_BYPASS`.

When a canonical bind already exists:
- do not search for another source;
- do not reselect historical candidate files;
- do not reconstruct identity from text;
- do not reopen Visual ID authority;
- pass the existing bound canonical reference into the generation/edit operation.

Only when the canonical bind itself is genuinely unavailable may the state become `BLOCKED_ASSET_BINDING`.

Hard rule:
`BOUND SOURCE EXISTS → USE BOUND SOURCE DIRECTLY`.

A generation result created without consuming the existing bind is REJECT even if it looks visually similar.
