# TAKY UI REFERENCE PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-UIREF-001
Role: Govern intake, evaluation, project application and validation use of external UI/UX references without allowing reference material to overwrite TAKY authority or user-approved project design.
Authority: TAKY / GRAND MASTER > this protocol > project-specific UI contracts > implementation.
Related: `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md`, `MASTER/VALIDATION_RULES.md`, `MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`.

## 0. Core invariant — HARD LOCK

`REFERENCE != AUTHORITY`
`POPULAR PATTERN != PROJECT DECISION`
`DESIGN SYSTEM != READY GOLDEN UI`
`EXTERNAL EXAMPLE != USER APPROVAL`

External UI/UX sources may improve vocabulary, discover patterns, expose platform constraints and strengthen validation. They SHALL NOT silently replace a user-approved visual direction, project rule, domain rule or canonical TAKY requirement.

## 1. Reference classes

Classify each source before use:

- `PLATFORM_GUIDANCE` — official platform guidance, accessibility, interaction, layout or component conventions.
- `DESIGN_SYSTEM_REFERENCE` — documented component/system patterns from a design system.
- `COMPONENT_LIBRARY_REFERENCE` — implementation-oriented component naming/state patterns.
- `REAL_WORLD_PATTERN_LIBRARY` — observed production-app flows/screens/patterns.
- `VOCABULARY_REFERENCE` — terminology normalization only.
- `INSPIRATION_ONLY` — aesthetic or exploratory material with no governing authority.

Classification describes use; it does not promote authority.

## 2. Source intake fields

Every material UI reference record SHOULD include:
- stable source id;
- source name;
- URL;
- source class;
- publisher/provider;
- access/retrieval date;
- verification state;
- applicable platforms;
- applicable project(s);
- extracted patterns/terms;
- design/interaction implications;
- conflicts with current project locks;
- disposition;
- destination;
- evidence note.

Unknown or inaccessible sources remain `UNVERIFIED_SOURCE_COVERAGE`; do not infer missing content.

## 3. Project protection — HARD LOCK

Before applying an external UI pattern:

1. load current project UI/UX contract;
2. identify protected/confirmed visual and interaction decisions;
3. compare the candidate pattern against those locks;
4. classify the delta as `PRESERVE / ADOPT / ADJUST / HOLD / REJECT / CONFLICT`;
5. require human approval for any material change to an explicitly confirmed project direction.

A reference may refine implementation quality without changing project identity.

`REFERENCE IMPROVEMENT -> PROJECT-COMPATIBILITY CHECK -> AUTHORIZED DELTA -> IMPLEMENTATION`

## 4. Golden UI non-override — HARD LOCK

When a project has an approved Golden UI, approved mockup, Visual ID, or confirmed screen direction:

- external references may validate usability, accessibility, consistency, responsive behavior and state completeness;
- they may suggest candidate refinements;
- they SHALL NOT replace the approved composition, hierarchy, identity, theme or interaction model without explicit approval.

If external guidance conflicts with a project lock, surface the conflict; do not silently converge.

## 5. Platform guidance use

Official platform guidance can create a validation obligation when the target platform materially depends on it.

For Apple-targeted/iPhone/PWA work, check applicable items such as:
- touch-target adequacy;
- legibility and contrast;
- screen-fit and safe-area behavior;
- clear organization/alignment;
- familiar feedback and recoverability;
- accessibility;
- platform-appropriate interaction.

Platform guidance remains subordinate to explicit TAKY/project authority except where a mandatory platform/runtime requirement makes the project behavior impossible or materially unsafe; such conflicts require explicit resolution.

## 6. Design-system/component-library use

Design systems and component libraries may be used for:
- terminology;
- component states;
- accessibility patterns;
- interaction-state completeness;
- implementation consistency;
- rapid prototyping.

They SHALL NOT cause a project to inherit a generic visual language by default.

`COMPONENT NAME / STATE MODEL MAY TRANSFER`
`BRAND / THEME / COMPOSITION DOES NOT AUTO-TRANSFER`

## 7. Real-world pattern library use

Production UI libraries may be used to inspect:
- complete user flows;
- common interaction patterns;
- transitions;
- onboarding;
- navigation;
- task-start/task-complete patterns;
- dialogs, bottom sheets, toasts, tabs, progress and other UI elements.

Use them as comparative evidence, not as proof that a pattern is correct for the current user/project.

Do not copy a third-party product's branded composition wholesale.

## 8. UI vocabulary normalization

TAKY SHOULD maintain a shared UI vocabulary so natural-language user descriptions can map to standard component/pattern names and then to project-specific component IDs.

Preferred mapping:
`USER PHRASE -> NORMALIZED UI TERM -> PROJECT COMPONENT/PATTERN -> IMPLEMENTATION ID`

Vocabulary normalization SHALL reduce ambiguity, not force the user to use specialist terminology.

## 9. C2S integration

External reference material entering a material system-building conversation shall be compiled as one or more atoms such as:
- `EVIDENCE`
- `IDEA`
- `STRATEGY`
- `CONSTRAINT`
- `FRONTIER`
- `CONFLICT`

Reference-origin atoms default to `REFERENCE_ONLY` or candidate status until project/global promotion is separately justified.

Required lineage:
`SOURCE -> EXTRACTED PATTERN/TERM -> DISPOSITION -> DESTINATION -> PROJECT IMPACT -> VALIDATION/APPROVAL`

## 10. Validation use

External UI references are most valuable as validation dimensions when a project direction is already locked.

Applicable checks may include:
- hierarchy;
- typography/legibility;
- spacing;
- layout;
- control hit area;
- navigation clarity;
- component consistency;
- state feedback;
- empty/loading/error/success states;
- responsive behavior;
- accessibility;
- motion restraint;
- platform fit.

A validation finding is not automatically authorization to redesign.

## 11. Ready & Set activation

For Ready & Set specifically:
- the confirmed adventure/exploration identity remains project authority;
- the confirmed Focus UI and existing Ready visual locks remain protected;
- external UI references are used first to improve clarity, platform fit, component-state completeness and validation;
- generic SaaS/dashboard inheritance remains disallowed;
- Material/Apple/component-library/Mobbin patterns may inform implementation or candidate refinements only when they preserve Ready's project identity.

## 12. Current reviewed reference set — 2026-09-19

Verified visible sources from the supplied reference message:
1. Material Design 3 components — `https://m3.material.io/components`
2. Apple UI/HIG guidance — `https://developer.apple.com/design/tips/` and current HIG pages
3. daisyUI components — `https://daisyui.com/components/`
4. Mobbin — `https://mobbin.com/`

The supplied message states a larger set of 9 sites and 110 UI terms. The other 5 sites and the full 110-term list are not yet recoverable from the accessible source, so they remain `UNVERIFIED_SOURCE_COVERAGE` and SHALL NOT be fabricated.

Machine-readable evidence index: `MASTER/UI_REFERENCE_REGISTRY.json`.

END
