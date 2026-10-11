# TAKY CHARACTER VISUAL ID REGISTRATION STANDARD — CANDIDATE
Date: 2026-10-08
Status: CANDIDATE / ADDITIVE REGISTRATION LAYER / DOES NOT REPLACE EXISTING APPROVED VISUAL IDs

## 0. Purpose
Character reference sheets are not mood boards. They are implementation-grade identity registration records.

Goal:
APPROVED SOURCE → IDENTITY LOCK → DERIVATIVE ASSET PRODUCTION → ACTUAL IMAGE QA → RUNTIME BINDING

This standard adds a structured Visual ID registration/fingerprint layer around existing approvals.
It does not reopen or redraw an already approved character.

## 1. Five-part registration package

### A. IDENTITY PORTRAIT LOCK
Record the facial/head traits that must survive every derivative:
- face/head shape
- eye shape, size, spacing, angle
- iris/pupil color and characteristic
- eyebrow shape/weight
- nose/muzzle/beak structure
- mouth/lip shape
- ear/horn/antenna structure
- hair/fur/feather silhouette and texture
- hairline/forehead relation where applicable
- skin/fur/feather base tone
- unique marks, freckles, scars, patches, whiskers
- characteristic resting expression

For non-human crew, use anatomy-equivalent features instead of forcing human labels.

### B. TURNAROUND / BODY IDENTITY LOCK
Required identity views:
- FRONT
- 3/4
- SIDE
- BACK

Record:
- height/scale class
- head-to-body ratio
- shoulder/torso width
- limb length/thickness
- hand/paw/wing/flipper/foot structure
- tail/body appendages
- posture/center of gravity
- silhouette
- species/body-specific motion constraints

Existing approved turnaround remains authoritative when already present.

### C. COSTUME / EQUIPMENT IDENTITY LOCK
Record only identity-critical items:
- base outfit
- signature accessory
- signature equipment
- footwear if identity-critical
- fabric/material
- seams/patterns/details that identify the character

Separate:
IDENTITY_CRITICAL vs SCENE_VARIABLE.
A seasonal/event accessory may never overwrite identity-critical costume.

### D. COLOR & MATERIAL LOCK
For each critical region:
- semantic color name
- sampled HEX/RGB where meaningful
- material/texture
- sheen/roughness/depth cue

Examples:
HAIR/FUR, SKIN, TOP, BOTTOM, EQUIPMENT, METAL, LEATHER, WOOD, CLOTH.

### E. DETAIL ANCHORS
Close-up evidence for the smallest traits most likely to drift:
- eyes
- nose/muzzle/beak
- mouth
- hair/fur/feather
- skin/fur texture
- hand/paw/wing detail
- signature prop attachment/grip point

## 2. Identity Fingerprint
Each registered character receives an identity fingerprint built from:
- Visual ID
- approved source asset digest(s)
- locked anatomy fields
- locked color/material fields
- locked costume/equipment fields

The fingerprint is a QA identity, not biometric recognition.
It exists to detect character-art drift across generations/derivatives.

## 3. Variable assets are NOT identity locks
Keep these outside the immutable identity block:
- expressions
- mouth phoneme states
- gaze direction
- gesture
- hand/arm action
- foot/leg action
- tool use
- temporary costume/event accessory
- ambient pose

These are derivative assets and must inherit the fingerprint.

## 4. Expression Sheet
Recommended semantic set:
NEUTRAL / HAPPY / SAD / SURPRISED / WORRIED / THINK / IDEA / REACT / DETERMINED / COMPLETE

Expression QA checks:
- same face/head proportions
- same eye placement
- same nose/muzzle/beak
- same hair/fur silhouette
- emotion changes expression, not identity

## 5. Action Sheet
Action sheet records body language and runtime parts, not a new body design.

Common semantic actions:
STAND / WALK / SIT / CROUCH / REST
READ_BOOK / READ_MAP / NOTE / COMPASS / BAG / MAGNIFIER / RADIO
POINT / OFFER_RECEIVE

Hands/feet/limbs are species/body aware.
Generic human hands/feet copied across crew are forbidden.

## 6. Human Special Crew
For human-type Special Crew, additionally lock:
- facial proportion triangle
- eye-to-brow spacing
- nose bridge/tip geometry
- lip contour
- jaw/chin line
- hairline + side silhouette
- shoulder/waist/leg proportion
- hand scale
- distinctive age/presentation cues without changing identity

The reference-sheet examples with face close-ups are useful here because small facial drift is visually obvious.

## 7. Animal / hybrid Crew
Do not force human reference anatomy.
Lock:
- muzzle/beak length and width
- ear/horn/antenna geometry
- eye placement relative to head
- fur/feather patch pattern
- paw/wing/flipper structure
- tail geometry
- species-specific head/body ratio
- signature equipment fit

## 8. Registration vs production — HARD
Visual ID registration is **NOT asset production**.

Registration output is limited to:
- metadata / JSON / MD records,
- pointers to existing approved source assets,
- hashes/digests,
- existing approved crops or close-up references,
- annotations that do not redraw pixels.

**IMAGE GENERATION IS FORBIDDEN DURING VISUAL ID REGISTRATION/BACKFILL.**
A registration/reference sheet must never be created by regenerating the character.
If a human-readable sheet is needed, it must compose/cite the **existing approved pixels** without altering the character artwork.

Turnaround/Face/Action assets belong to the production pipeline, not the registration pipeline.
Runtime crop/part = implementation asset only after its production/QA gate.

External reference-sheet examples may inform layout/field structure only; they are never prompts or visual-authority sources.

## 9. Change control
PATCH:
new close-up/detail evidence that does not change identity.

MINOR:
clarifies an existing identity field without visual identity change.

MAJOR:
face/body/species/silhouette/signature costume change.
Requires explicit user approval and a new Visual ID revision.

## 10. Gate
FAIL immediately if registration/backfill attempts to generate or redraw character imagery.

FAIL if a derivative:
- looks like a different person/character
- changes face/head proportions
- changes species anatomy
- changes hair/fur silhouette without authority
- shifts critical colors/materials
- loses signature equipment
- changes body proportion to fit an action
- uses an action sheet as authority to overwrite the base identity

PASS requires actual-image comparison against the registered identity package.

## 11. Storage
Drive:
human-readable approved Visual ID registration sheets + approved source references.

TAKY Git:
machine-readable identity registry, fingerprints, digests, immutable/variable field contracts and validation rules.

App repositories:
consume a pinned Visual ID revision and derivative assets; they do not own or reinterpret identity.
