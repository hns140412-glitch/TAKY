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

The supplied Notion screen recording recovers the intended 9-site reference set as 10 reference entries across 9 sites/domains: Apple HIG + Apple Design Tips (same Apple site), Material Design 3, Flutter Widget catalog, Ionic Components, daisyUI, Uiverse, Penpot, IBM Carbon and Mobbin. The page also organizes the UI vocabulary into 11 groups: screen scaffolding, navigation, lists, input, selection, actions/buttons, overlays, status/display, motion/dynamic effects, stacking/overlap and presentation/mockup frames. The exact 110-term count is treated as the page author's declared count unless mechanically enumerated from a stable source export.

### Source-quality boundary — HARD LOCK

The recovered Notion page is an educational glossary/curation artifact. Its labels, warnings and numeric heuristics are useful orientation aids but are not automatically official platform requirements.

Examples visible in the source include shorthand such as bottom-navigation item-count guidance, a 44pt touch target note, FAB usage notes and simplified component descriptions. Before any numeric/platform constraint becomes a project rule, verify it against the current official source when available.

`GLOSSARY EXPLANATION != OFFICIAL REQUIREMENT`
`AUTHOR HEURISTIC != PLATFORM HARD LOCK`
`TERM PRESENT != COMPONENT REQUIRED`

Machine-readable evidence index: `MASTER/UI_REFERENCE_REGISTRY.json`.

## 13. Broad comparison stack — HARD LOCK

TAKY SHALL NOT treat one UI guide, library or gallery as a complete design authority.

For material UI/UX review, select the smallest useful stack from distinct evidence layers:

1. `PROJECT AUTHORITY` — approved project contract, Golden UI, Visual ID, user-confirmed flow.
2. `PLATFORM GUIDANCE` — Apple HIG / Material or equivalent platform guidance.
3. `ACCESSIBILITY / SEMANTIC STANDARD` — WCAG / WAI-ARIA Authoring Practices or equivalent standards.
4. `MATURE DESIGN SYSTEM` — Carbon / Fluent / GOV.UK or equivalent systems that document usage, errors, states and accessibility.
5. `ACCESSIBLE PRIMITIVES` — Radix / React Aria / equivalent implementation primitives for focus, keyboard and ARIA behavior.
6. `IMPLEMENTATION LIBRARY` — shadcn/ui / daisyUI / Ionic / Flutter widget references or equivalent.
7. `DESIGN-SYSTEM OPERATIONS` — Penpot/design-token/component-instance patterns.
8. `REAL-WORLD FLOW EVIDENCE` — Mobbin or other production-flow references.
9. `INSPIRATION` — Uiverse and effect galleries.

Higher list position does not mean higher visual authority. Project authority remains first; external layers are evidence/validation sources.

`ONE SOURCE AGREES != CROSS-VALIDATED`
`MULTIPLE POPULAR SOURCES AGREE != PROJECT FIT`

## 14. Cross-source comparison axes

When comparing references, evaluate at least the materially relevant axes rather than asking which source is "best":

- purpose / user outcome;
- information hierarchy;
- navigation model;
- interaction semantics;
- component appropriateness;
- state completeness;
- error prevention and recovery;
- keyboard/focus behavior;
- accessible name/role/state;
- screen-reader implications;
- target size / touch ergonomics where officially supported;
- content clarity;
- responsive/reflow behavior;
- safe-area/device constraints;
- motion/reduced-motion behavior;
- implementation feasibility;
- token/component reuse;
- project identity fit;
- child/adult cognitive fit where applicable;
- evidence status and source authority.

A source may be strong on one axis and weak or irrelevant on another. Do not average them into a synthetic "universal UI".

## 15. Accessibility and semantics layer — HARD LOCK

For web/PWA implementation, visual similarity is insufficient.

Material interactive components SHALL be checked, where applicable, for:
- semantic element/role;
- accessible name/description;
- keyboard reachability and expected keys;
- visible focus;
- focus entry/return for overlays;
- modal containment when modal;
- error association and recovery;
- selected/expanded/disabled/invalid state exposure;
- sufficient contrast and reflow;
- motion preference handling.

Use WCAG as conformance guidance and WAI-ARIA Authoring Practices as interaction-pattern evidence. A third-party primitive/library may help satisfy these behaviors but does not prove the integrated application is accessible.

`LIBRARY ACCESSIBLE != APPLICATION ACCESSIBLE`
`ARIA PRESENT != CORRECT INTERACTION`

## 16. State-completeness model

For each material interactive component/flow, consider only applicable states but do not omit them silently:

`DEFAULT / HOVER / PRESSED / FOCUS / SELECTED / DISABLED / LOADING / EMPTY / ERROR / OFFLINE / SUCCESS / PARTIAL / RETRY / RECOVERY`

Mobile-only experiences may not require hover. Domain-specific states may extend this set.

State review SHALL include:
- what the user sees;
- what action remains possible;
- what data/state is preserved;
- whether recovery is possible;
- whether assistive technology receives equivalent meaning.

## 17. Design-token and component-source discipline

Reusable visual decisions SHOULD be represented as tokens/components rather than copied screen-by-screen when the implementation scale justifies it.

Candidate token families:
- color;
- typography;
- spacing;
- radius;
- elevation/shadow;
- motion/duration/easing;
- icon size;
- control sizing.

Preferred relationship:
`TOKEN -> MAIN COMPONENT -> INSTANCE/VARIANT -> PROJECT SCREEN`

Local overrides are allowed when intentional and traceable. Repeated arbitrary overrides indicate design-system drift.

## 18. Content design and recovery

UI copy is part of interaction design.

For material controls/errors:
- use short, literal, context-appropriate labels;
- distinguish user-correctable validation errors from service/system failures;
- state what happened and what the user can do next;
- avoid relying only on color or spatial terms;
- preserve cancel/back/retry/undo/resume paths where the flow requires them.

For child-facing Ready surfaces, plain language and immediate action clarity take precedence over design-system terminology.

## 19. Target-specific reference profile

Do not load every source for every screen.

Default selection examples:
- iPhone/PWA child execution screen -> Project contract + Apple/platform + WCAG/WAI-ARIA + one mature design system + accessible primitive evidence + actual device QA.
- Parent data-entry/form flow -> Project contract + WCAG/WAI-ARIA + GOV.UK/Fluent/Carbon form/error evidence + primitive/library implementation check.
- visual exploration -> Project contract + Mobbin/Penpot/Uiverse as candidates, then return to platform/accessibility/project gates before adoption.
- component implementation -> Project contract + chosen framework/library + primitive accessibility behavior + regression evidence.

Machine-readable comparison profile: `MASTER/UI_REFERENCE_COMPARISON_MATRIX.json`.


END
