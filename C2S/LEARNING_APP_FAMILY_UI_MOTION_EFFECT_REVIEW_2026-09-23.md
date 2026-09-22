# LEARNING APP FAMILY UI — MOTION / EFFECT REVIEW — 2026-09-23

Status: REVIEWED / ONB-01 MOTION DELTA READY
Scope: current UI/Visual integration, especially Core 6 onboarding familiarity/select sequence.
Parent:
- C2S/TAKY_TOP_LEVEL_EXECUTION_PRINCIPLES_CANONICAL_2026-09-23.md
- C2S/LEARNING_APP_FAMILY_INTEGRATED_LOGIC_UI_CANONICAL_2026-09-22.md
- C2S/LEARNING_APP_FAMILY_UI_VISUAL_BASE_DELTA_MAP_2026-09-23.md

## 1. External implementation references reviewed

Reference classes:
- Motion stagger/orchestration patterns for sequential group entrance and focus.
- spring-based micro-interaction patterns for short, interruptible response.
- AnimatePresence/shared-layout style state transitions for focus handoff.
- reduced-motion patterns that remove transform/parallax while preserving hierarchy.
- Netlify-hosted public demos showing stagger, exit/enter, reorder and reduced-motion provider patterns.

External examples are implementation references only.
They do not override TAKY product/Visual ID rules and do not become visual authority.

## 2. Existing TAKY motion grammar retained

Shared categories:
1. PLACE_CHANGE
2. STATE_CHANGE
3. FOCUS_CHANGE
4. WORLD_LIFE

No separate global reward-motion system.

For current onboarding:
- Crew member self-promotion = FOCUS_CHANGE
- primary-companion selection = STATE_CHANGE
- Voyage/Drop = PLACE_CHANGE
- flags/lantern/cloud/water = WORLD_LIFE

## 3. Core rule — motion may animate ACTION, never IDENTITY

Core 6 Visual ID = HARD LOCK.

Motion may affect only:
- expression
- pose
- gesture
- action
- screen position
- short dialogue/reaction presentation

Motion/effects must not deform or reinterpret:
- species
- face
- silhouette
- body proportion
- identity markings
- fur/primary identity colors
- signature clothing structure
- signature equipment
- core palette
- Visual ID.

Rule:
`ANIMATE ACTION LAYER, NOT IDENTITY LAYER`.

No squash/stretch that changes body proportion.
No face morph.
No costume transformation outside authorized Shared Expedition Accent adaptive zones.
No camera/effect treatment that makes the Crew unreadable against its locked reference.

## 4. ONB-01 — Core 6 familiarity motion choreography

Goal:
make the six friends feel lively, witty and slightly noisy while preserving legibility and exact Visual IDs.

### 4.1 Initial group reveal
One-time entrance only.

Pattern:
- environment already present;
- Core 6 enter/reveal with short stagger;
- suggested interval: 70–100 ms between members;
- opacity + small positional offset only;
- settle with low-bounce spring;
- total group entrance should feel fast, not like six separate loading animations.

Do not:
- endless bounce;
- spin/flip;
- scale from tiny to huge;
- random entrance direction per character;
- repeat entrance every time the child returns.

### 4.2 Self-promotion focus cycle
At any moment:
- one Crew member is CURRENT_FOCUS;
- current member steps/leans forward slightly;
- performs one short character-specific gesture;
- other five remain alive through micro-reactions but do not compete with equal-amplitude motion.

Character-specific action layer:
- 두비: quick forward step / bag tap / eager hand raise
- 로리: tidies/checks a nearby item / calm amused reaction
- 잉크: map compare / thoughtful glance / tiny point
- 노바: goggles-ready / body angled toward departure / quick “go” gesture
- 테이크: checklist tap / precise count gesture
- 제로: light rhythm/headset/music cue gesture

These are behavior projections, not identity changes.

### 4.3 Focus handoff
Use focus indicator motion instead of morphing the character.

Preferred:
- selected/focused halo, ground plate, speech tag or framing element moves with shared-layout/state transition;
- character itself uses only small translation/scale emphasis;
- short crossfade for dialogue.

Suggested:
- focus transition 220–360 ms;
- character emphasis scale no more than ~1.02–1.04;
- positional offset small enough to preserve group composition;
- spring or ease-out with low bounce.

### 4.4 Tap / select micro-interaction
For tappable Crew/CTA:
- press feedback ~0.97–0.99 scale;
- immediate selection ring/check/state change;
- no delayed “game reward” effect;
- no confetti.

Primary Companion selection:
- chosen member remains in place and gets clear state emphasis;
- other five step back slightly or lower emphasis;
- they do NOT disappear or look rejected.

## 5. Environmental WORLD_LIFE

Allowed subtle loops:
- flag/fabric flutter
- lantern glow variation
- cloud drift
- very small water shimmer
- hanging tag/rope micro sway

Rules:
- background motion never competes with Crew self-promotion;
- no full-screen parallax required for understanding;
- no ambient loop attached to critical CTA state;
- avoid heavy particle fields.

## 6. Reduced Motion

Required:
- honor OS/user reduced-motion preference;
- remove parallax and travel-like transforms;
- replace staggered movement with fast opacity/focus state;
- preserve selected/focused hierarchy;
- preserve all text/state information;
- never make motion necessary to know which Crew member is active.

Recommended implementation semantics:
`reduced_motion = user preference`.

## 7. Motion hierarchy by screen

ONB-01 Crew Familiarity:
HIGH personality motion / LOW visual distortion.

ONB-02 Primary Companion Select:
MED motion; focus + selection clarity.

ONB-03 Naming:
LOW motion.

Photo / Signature Item / Direction choices:
LOW; task clarity first.

A/B/C Reveal:
MED; one-time reveal, no repeated spectacle.

Shared Expedition Accent:
LOW-MED; color adaptation preview only.

Voyage / Drop:
HIGH PLACE_CHANGE once.

Ready Weekly:
LOW; planner comprehension first.

Timer:
LOCKED; no redesign.

## 8. Rejected motion/effect patterns

REJECT:
- continuous character bouncing
- all six moving at full amplitude simultaneously
- RPG aura/light beams
- reward confetti on ordinary selection
- face/body morphing
- 3D flip of character portraits
- heavy blur/glow around locked identity
- camera shake
- scroll/pointer parallax required to understand UI
- auto-looping carousel that moves the focus away from child control
- animation replay on every minor state change.

## 9. Implementation stance

Do not lock the product to one animation library yet.

Acceptable implementation families:
- CSS transitions/keyframes
- Web Animations API
- Motion/Motion for React where the app stack supports it
- equivalent implementation that preserves this semantic contract.

Library choice is subordinate to:
- current app stack
- performance
- reduced-motion support
- deterministic state behavior.

## 10. ONB-01 application decision

APPLY to next Crew familiarity screen/runtime spec:
- one-time 6-member stagger reveal;
- one CURRENT_FOCUS member;
- character-specific single self-promotion gesture;
- shared focus indicator transition;
- subtle micro-reactions from non-focused Crew;
- light WORLD_LIFE in expedition staging environment;
- tap/press micro-feedback;
- reduced-motion equivalent.

Do not alter the recovered high-fi visual lineage to make room for effects.
Motion is an overlay/projection of the same BASE composition.

Think Again, Keep Your Key.
한 번 더 생각하고, 핵심은 놓치지 마.
