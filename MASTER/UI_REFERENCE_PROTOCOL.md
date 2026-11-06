# TAKY UI REFERENCE PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-UIREF-001
Role: Use external UI/UX references to generate better possibilities, vocabulary, implementation choices and learning while protecting project authority; validation is a supporting filter, not the primary purpose.
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

External UI references are valuable first for expanding possibilities, learning patterns and improving implementation; when a project direction is locked, they also provide targeted validation dimensions.

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
- external UI references are used to discover better patterns, implementation options and reusable UI knowledge, then to check clarity/platform fit/state completeness where material;
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

For material UI/UX work, select the smallest useful stack that helps create or improve the result; do not load a comparison stack merely to perform validation:

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

## 20. Case-derived design-gate criteria — 2026-11-06

Status: ACTIVE criteria under TKY-UIREF-001. Origin: Claude independent case review of the DG-00..10 / PS-00..23 design-gate contract (`TAKY_DESIGN_GATE_MINING_SNAPSHOT_20261004.json`) against external cases, building on the prior review `TAKY_DESIGN_GATE_CLAUDE_REVIEW_20261004.json` (C-01..C-14). USER approved reflection 2026-11-06.

Scope: these are criteria, not new gates. DG IDs and order stay unchanged and append-only. Until the DG contract itself is promoted into a MASTER owner, each criterion binds through the gate ID named here and through `ENFORCEMENT/design_gate_receipt.py` only where a field already exists. No enforcement is claimed for fields the receipt code does not check.

`CASE EVIDENCE != PROJECT AUTHORITY` — §0 and §3 still govern. The cases explain why a criterion exists. They do not transfer any brand, composition or product decision.

### 20.1 Criteria

| ID | Gate | Criterion | Case basis (evidence grade) |
|---|---|---|---|
| DGC-01 | DG-00 | Every design run declares `mode: EXPLORE \| EXECUTE`. With no approved direction or no token manifest, the run is EXPLORE. EXPLORE output is `PILOT_FIXTURE_ONLY` and cannot enter DG-07 until approval is bound at DG-05. | Claude Design: without tokens or readable components, Claude makes its own visual choices (secondary). Prior C-07. |
| DGC-02 | DG-00 / DG-04 | An imported or generated design system is `DERIVED`, not authority. Record `design_system_source = {repo, commit, token_file}` and `design_system_id@version`. A source commit change marks dependent receipts stale. One active design system per project. | Claude Design builds a team design system from codebase and design files during onboarding, and supports several systems (official announcement and help center). `/design-sync` converts a repo's React design system and uploads it (official Claude Code commands page). |
| DGC-03 | every receipt | Each receipt names one owner ROLE (DRI), not a joint owner. ROLE != AGENT. | Apple directly-responsible-individual practice (secondary: Lashinsky, *Inside Apple*). |
| DGC-04 | DG-02 | Each conditional PS row and each material UI element carries a `requirement_owner`. An unowned requirement becomes an N_A candidate and DG-06 audits it. Forced-applicable rules from prior C-10 still apply. | Tesla/SpaceX "question every requirement; a named person defends it or it goes" (secondary: Isaacson biography, McNeill *The Algorithm*). |
| DGC-05 | DG-05 | In EXPLORE, show at least N materially different candidates before the user picks. Default N=3. COST may lower it and must record why. "Materially different" means a change in IA, hierarchy, palette role, type scale, component set or density class (prior C-14). Pixel deltas inside the same tokens do not count. | Apple "10 → 3 → 1" concept narrowing (secondary: 2008 SXSW talk summary). |
| DGC-06 | DG-06 | Add a `DELETION_PASS {removed[], reason, re-added[]}` before freeze. If nothing was removed, a reason is required. Re-added items go into the pilot delta list (prior C-01). Safety and accessibility affordances are protected and cannot be deleted for minimalism. | Tesla "delete before you optimize" (secondary). Tesla removed the Model 3 turn-signal stalk and in Aug 2025 made it standard again in China, with a paid retrofit (reputable secondary: Carscoops, InsideEVs, Electrek, Drive Tesla Canada). |
| DGC-07 | DG-06 / PS-20 | The freeze reference is a render-level mockup with a hash, not a wireframe. `visual_compare` binds to that hash (reference hash, renderer, viewport/page, tolerance). This matches the existing `approved_reference_sha256` receipt field. | Apple polished, unambiguous mockups (secondary). Prior C-12. |
| DGC-08 | DG-06 → DG-07 | A tool handoff (for example Claude Design → Claude Code, local or web) carries the frozen `spec_version/spec_hash`. A handoff without one cannot enter DG-07. | Claude Design packages a handoff bundle for Claude Code with "Send to local coding agent" and "Send to Claude Code Web" (official). Bundle contents are not documented, so TAKY must add the hash itself. |
| DGC-09 | DG-08 | `EXPORT SUCCESS != EDITABLE PASS`. Exported PPTX/PDF/HTML/Google Slides/ZIP output still runs FONT_PRINT_PDF and INTERACTION_EDITABILITY against TARGET_ENVIRONMENT (prior C-03). | Claude Design exports .zip, PDF, PPTX, Google Slides and standalone HTML, and sends to Canva and others (official help center). Figma export is not in any official list. |
| DGC-10 | DG-03 / DG-08 | Apple-targeted work checks against the current HIG direction: hierarchy (content first, controls don't compete), harmony with system materials and colors, and consistency with platform patterns. Count the screen's competing focal points and keep them at or below K, declared at DG-02. | Apple's Liquid Glass overview: establish hierarchy, create harmony, maintain consistency (official snippet; full HIG body text not machine-readable in this review). |
| DGC-11 | DG-09 | In continuous release (OTA-style), a receipt is invalid when the spec, artifact or `design_system_id@version` differs from what it recorded. | Tesla single-screen UI with OTA updates (general knowledge). Prior C-02. |
| DGC-12 | DG-10 / ENFORCEMENT | Automate last. A new automated gate check is added only after the same check passes manual replay at a threshold declared at DG-02. `RULE WRITTEN != RULE ENFORCED`. | Tesla "automate last; early factory automation was the mistake" (secondary: Isaacson). Prior C-09. |

### 20.1b Criteria from Instagram and Claude Design practitioner cases

| ID | Gate | Criterion | Case basis (evidence grade) |
|---|---|---|---|
| DGC-13 | DG-00 / DG-05 | Changes to primary navigation, feed or other core surfaces list the affected stakeholder groups in the scope lock and require a staged pilot (limited group or region, opt-in where possible) before broad release. | Instagram's full-screen feed test (2022) was rolled back after creator backlash; Mosseri said the design was "not yet good" (REPUTABLE_SECONDARY: Platformer, Engadget, NBC). The Reels/DM navigation (Oct 2025) went to a regional test and then opt-in (REPUTABLE_SECONDARY: Engadget). |
| DGC-14 | DG-02 / DG-08 | The output contract carries at least one user-experience criterion that can outrank an engagement metric. Default: content does not change under the user's eye. | Instagram removed "rug-pull" feed refresh in Nov 2024 and accepted some engagement loss (REPUTABLE_SECONDARY; reports differ on whether it applied to Reels or the main feed). |
| DGC-15 | DG-09 | A change to an output contract (aspect ratio, grid, size class) ships in the same release as a migration path for assets made under the old contract. Otherwise those assets are marked broken. | Instagram changed the profile grid from 1:1 to a taller ratio in Jan 2025, and "Adjust Preview" followed (REPUTABLE_SECONDARY; 4:5 vs 3:4 is unresolved, so no number is cited). |
| DGC-16 | DG-02 / DG-08 | Each form factor gets its own output contract and render check. A scaled-up build from another form factor fails TARGET_RENDER. | Instagram served iPad a scaled-up iPhone app until the native iPad app in Sep 2025 (REPUTABLE_SECONDARY: Bloomberg). |
| DGC-17 | DG-01 | For a brand or identity change, separate recognised core elements from decoration before freeze (for example a recall test). | The 2016 Instagram icon redesign used a draw-from-memory step (REPUTABLE_SECONDARY). |
| DGC-18 | DG-06 | The frozen spec is a file (DESIGN.md or equivalent) that holds tokens plus composition and layout rules **and a prohibition list** (banned generic defaults). `TOKEN MATCH != DESIGN PASS`. | Practitioners report correct token extraction with poor composition, and generic "AI look" defaults when no system or prohibitions are supplied (SNIPPET_ONLY: blogs, skill mirrors). |
| DGC-19 | DG-08 FONT_PRINT_PDF | Check that the loaded fonts match the spec. CJK text names an explicit font (for example Pretendard or Noto Sans KR). Each export target is rendered, and the output contract declares print-safe CSS (no gradient-clipped text or mask-image for PDF). | Reports of silent font fallback and of PDF exports covering text with colour blocks (SNIPPET_ONLY, including a Korean blog). |
| DGC-20 | DG-04 / DG-09 | Treat design-system sync as a snapshot. A design-system change requires re-sync and marks earlier synced outputs stale (extends DGC-02). | `/design-sync` pulls the design system into the repo or pushes back to Claude Design (official @ClaudeDevs post and help center, seen as snippets). |
| DGC-21 | DG-05 | The pilot declares a cost budget per iteration so the pilot does not end before the candidates (DGC-05) are produced. COST-internal; not a new gate. | A tester used about 80% of a weekly Pro allowance in about 25 minutes at launch; a later update reduced per-turn usage (REPUTABLE_SECONDARY: PCWorld, VentureBeat). |

### 20.1c Harness binding — 2026-11-06

The mechanical parts of DGC-01/02/16/18/19 and A11Y basics are executable:
- `ENFORCEMENT/design_gate_harness.py` (judge, receipt) + `ENFORCEMENT/design_gate_render.mjs` (Playwright/Chromium render probe). Sub-receipts in fixed order: HARNESS_HEALTH, SPEC_LINT, TARGET_RENDER, TOKEN_FIDELITY, FONT_PRINT_PDF, A11Y_BASIC, GENERIC_TELLS (advisory only). A harness failure is HOLD, not FAIL. Receipts carry `spec_sha256`, `artifact_sha256` and `design_system_id@version`.
- Procedure: `.claude/skills/taky-design-gate/SKILL.md`. Independent review: `.claude/agents/design-gate-reviewer.md`. Browser eye for interaction: `.mcp.json` Playwright MCP (pinned).
- Tests: `ENFORCEMENT/design_gate_harness_test.py` with fixtures in `ENFORCEMENT/fixtures/design_gate/`.
- Not added to CI on purpose (DGC-12: automate last). Promote to CI after manual replay on real project screens passes.
- No third-party design skill is installed (Notion review RVR-121 disposition: hold).

### 20.2 Apple vs Tesla conflict resolution

| Stage | Dominant principle |
|---|---|
| DG-00..02 scope and contract | Tesla: question requirements, require owners |
| DG-05 pilot | Apple: wide, materially different candidates |
| DG-06 freeze | Both: delete first (Tesla), then freeze at render level (Apple) |
| DG-07..08 implementation and QA | Tesla: simplify, then speed up |
| Gate automation | Tesla: automate last |

N (candidate count) and deletion intensity are COST-internal Necessity judgments. They do not create a sixth hard gate.

### 20.3 Claim ceiling

`DESIGN_CONTRACT_CASE_REVIEWED`. Most case facts come from secondary sources. The official sources are Anthropic's announcement, help center and Claude Code commands page, and Apple's Liquid Glass overview snippet. Note: the standalone claude.ai/design site closes by 2026-12-14 (official), so DGC-08/09 must be rechecked against the successor surface. Instagram and practitioner cases (DGC-13..21) come from search-result text; no Instagram or Threads post was readable, and DGC-18/19 rest on SNIPPET_ONLY evidence and should be re-verified before any numeric rule is derived from them. No runtime, receipt-code or CI binding is claimed for DGC-01..21 beyond the existing `design_gate_receipt.py` fields.


END
