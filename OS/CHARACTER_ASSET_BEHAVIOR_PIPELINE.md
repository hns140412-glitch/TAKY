# TAKY CHARACTER ASSET / BEHAVIOR PIPELINE

Status: REV_00 / IMPLEMENTATION CONTRACT
Authority: TAKY > GUIDE FAMILY LEARNING OS > this pipeline > project-specific runtime.
Related: `OS/GUIDE_CHARACTER_RELATIONSHIP.md`, `MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md`.

## 1. HARD SEPARATION

`ASSET GENERATION ENGINE != CHARACTER BEHAVIOR ENGINE`.

The Asset Generation Engine creates, validates, versions and registers reusable visual assets.
The Character Behavior Engine never generates canonical art at runtime. It selects and composes already-approved assets according to relationship, scene and interaction state.

This separation exists to preserve character identity, reduce image-generation cost/latency, keep PWA behavior deterministic and prevent visual drift.

## 2. ASSET GENERATION ENGINE

Responsibilities:
- create or transform Character Master, approved companion/Guide assets, badge motifs, backgrounds and UI illustration assets;
- preserve approved Visual ID / Character Master identity;
- generate only required derivatives such as pose, expression, prop, alpha and optimized WebP/PNG variants;
- validate anatomy, silhouette, identity consistency, dimensions, alpha and rights/consent boundaries;
- calculate SHA/version and register the approved derivative;
- write canonical reusable binaries to `TAKY-ASSETS` and provide exact consumer pointers.

The engine SHALL NOT decide story behavior, relationship progression, dialogue intent, reward logic or live scene selection.## 3. USER CHARACTER PIPELINE

For an intro/onboarding user character:

`CAPTURE -> INPUT VALIDATION -> GENERATE CANDIDATES -> REVIEW/SELECT -> CHARACTER MASTER -> DERIVATIVES -> SHA/VERSION -> CHARACTER REGISTRY -> APP BINDING`.

The original child photo is private input and SHALL NOT be published to a public PWA or central public asset repository.
Only consented, release-safe derived character assets may be distributed to app deployment copies.

A Character Master is the identity authority for later derivatives.
Later poses/expressions SHALL derive from that authority instead of independently redrawing the child on every event.

Minimum registry fields:
- `character_id`
- `member_id` or child scope
- `master_asset_ref`
- `visual_version`
- `sha256`
- `derivative_refs`
- `consent/release_scope`
- `status`

## 4. CHARACTER BEHAVIOR ENGINE

Responsibilities:
- consume relationship/lifecycle state;
- consume app/scene state;
- decide dialogue intent and timing;
- select pose/expression/prop/animation cues;
- select companion presence and spatial role;
- return a render contract referencing approved registry assets.

Example render contract fields:
`character_id, relationship_state, action_id, pose_id, expression_id, prop_id, animation_cue, dialogue_intent, asset_refs`.

The Behavior Engine SHALL NOT call image generation as a normal response to `ACTION`, `EXPRESSION` or `SCENE` changes.## 5. RUNTIME RULE

Normal runtime:
`STATE -> BEHAVIOR ENGINE -> CHARACTER REGISTRY -> UI RENDERER`.

Asset production:
`MISSING REQUIRED ASSET -> ASSET GENERATION ENGINE -> VALIDATION -> REGISTRY PROMOTION -> RUNTIME AVAILABLE`.

If a required visual variant is absent, runtime uses an approved fallback or marks the asset gap.
It SHALL NOT silently generate a new canonical character variant in the live child session.

## 6. CROSS-APP BINDING

A single approved user `character_id` is shared across Ready & Set, Hide & Seek and Snap & Pop where permitted.
Project apps may use different scene skins, poses and interaction cues, but SHALL NOT fork the underlying child identity.

Badge rendering may consume the same child-scoped character overlay reference.
Base badge art and child character overlay remain separate assets/layers.

### 6.1 Family Character Profile Projection — HARD LOCK

User-generated child Character Masters are private family/member data, not public TAKY-ASSETS content.
`TAKY-ASSETS` may contain schemas, static shared assets and release-safe shared metadata, but SHALL NOT become the public storage location for a child's raw photo or private Character Master merely because the character is reused across apps.

Cross-app sharing uses a family/member-scoped runtime projection owned by the Learning/Family domain:

`READY CHARACTER MASTER CONFIRMATION -> FAMILY CHARACTER PROFILE PROJECTION -> READY / HIDE / SNAP CONSUMERS`.

Minimum projection fields:
- `member_id`
- `character_id`
- `identity_version`
- `master_asset_ref`
- `master_sha256` when available
- `asset_version`
- `derivative_refs`
- `status`
- `updated_at`

The projection SHALL NOT contain the raw source photo.
Apps may cache the resolved release-safe Character Master locally for offline use, but the local cache is not a new identity authority.

Ownership:
- Ready onboarding may create and confirm the user's Character Master.
- Family profile runtime/storage owns the cross-app pointer and member binding.
- Hide & Seek and Snap & Pop consume the projection; they SHALL NOT independently regenerate the same child identity.
- Character Behavior Engine consumes the confirmed `character_id` and approved asset refs only.

Provider/transport remains adapter-driven. Until an authorized family-profile backend/provider is configured, cross-origin propagation is `NOT_RUNTIME_COMPLETE`; local app state alone SHALL NOT be reported as cross-app sync.

## 7. INTRO / ONBOARDING CONTRACT

The approved intro flow may invoke the Asset Generation Engine during character creation, then persist the resulting Character Master before normal app entry.
After confirmation, the intro stores the selected `character_id`; subsequent app launches resolve that identity through the registry rather than re-running character generation.

Character creation is therefore an onboarding production flow, not a per-screen render behavior.

## 8. COMPLETION STATES

Report separately:
`CAPTURE_READY | GENERATOR_ADAPTER_READY | CHARACTER_MASTER_CONFIRMED | DERIVATIVES_READY | REGISTRY_BOUND | READY_BOUND | HIDE_BOUND | SNAP_BOUND | BADGE_OVERLAY_BOUND | RUNTIME_VERIFIED`.

Do not call the character pipeline complete when only camera capture or photo display exists.

END