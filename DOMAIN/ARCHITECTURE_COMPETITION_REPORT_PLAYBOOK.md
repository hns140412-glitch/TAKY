# ARCHITECTURE COMPETITION REPORT / DRAWING REPRESENTATION PLAYBOOK

Status: ACTIVE / 2026-10
Owner: `DOMAIN/ARCHITECTURE_WORK_OS.md`
Registry: `DOMAIN/ARCHITECTURE_COMPETITION_REPRESENTATION_REGISTRY.json`
Visual quality: `DOMAIN/ARCHITECTURE_COMPETITION_VISUAL_QUALITY_REGISTRY.json`
Artifact schema: `DOMAIN/ARCHITECTURE_COMPETITION_ARTIFACT_SCHEMA.json`
Public source registry: `REFERENCE/ARCHITECTURE_COMPETITION_PUBLIC_SOURCE_REGISTRY.json`
Evidence: `REFERENCE/ARCHITECTURE_COMPETITION_REPRESENTATION_EVIDENCE_2026-10-03.json`

## 1. Outcome
During an architecture competition, TAKY/ArchiGrow SHALL be able to propose and produce a report/board drawing-representation package that helps the reviewer understand:
`WHY THIS DESIGN -> HOW IT WORKS -> WHAT THE DRAWINGS PROVE -> WHAT THE EXPERIENCE BECOMES`.

This is an execution playbook, not a new semantic owner.

## 2. Authority order
1. Competition brief / official submission instructions.
2. Verified project geometry, numbers, program and design decisions.
3. User-confirmed narrative / visual direction.
4. Company CURRENT_BEST where applicable.
5. Representation registry / external reference evidence.
6. AI-generated candidate techniques.

Generic graphic advice never overrides a project-specific submission rule.

## 3. Intake contract
Before proposing output, resolve:
- competition type and review stage;
- required submission format: panel/report/PPT/drawing book/video;
- page/panel size and count;
- mandatory drawings and scales;
- anonymity, file size, color or printing constraints;
- whether content is frozen after submission;
- project type, site condition and core design argument;
- verified source drawings/models available;
- unresolved geometry/data that must not be beautified into false certainty.

If the brief is unavailable, output a candidate package marked `BRIEF_UNVERIFIED`, never a compliance PASS.

## 4. Story-to-drawing compiler
Map each design claim to the minimum drawing that proves it:
- site reason -> CONTEXT;
- form reason -> CONCEPT / AXONOMETRIC;
- program relation -> PROGRAM;
- movement/arrival -> CIRCULATION;
- functional organization -> PLAN;
- vertical/spatial relation -> SECTION;
- frontage/envelope -> ELEVATION;
- climate/technical claim -> PERFORMANCE / TECHNICAL;
- atmosphere/key space -> EXPERIENCE.

No claim should depend only on decorative text when a spatial drawing can prove it.

## 5. Recommended report sequence
Default A3 report chapter logic:
1. ONE-LINE IDEA + key image/parti.
2. SITE / CONTEXT question and response.
3. CONCEPT / MASS transformation.
4. PROGRAM + circulation relationship.
5. PLAN proof at relevant levels.
6. SECTION proof through the most important spatial condition.
7. ELEVATION / envelope / urban edge.
8. PERFORMANCE / structure / parking / area / feasibility as relevant.
9. EXPERIENCE views tied back to verified geometry.
10. SUMMARY spread: criteria -> design move -> evidence.

Do not mechanically include every chapter. Remove anything that does not strengthen the project argument.

## 6. Drawing treatment
### Plans
Prefer clean vector hierarchy first. Add poche, furniture, entourage, textures or program tint only when they improve comprehension.
Keep wall/structure/void/circulation hierarchy visually distinct.
Rendered plans are explanatory derivatives; the measured plan remains geometry authority.

### Sections
Use cut-line dominance, foreground/background depth and human-scale cues.
Use rendered/sectional-perspective variants when the section itself is the design argument.
Keep levels and critical dimensions traceable.

### Diagrams
One diagram = one question/claim whenever possible.
Use a small stable semantic palette across program, circulation, landscape and performance.
Sequence diagrams when showing transformation; do not compress unrelated causes into one graphic.

### Axonometrics
Use exploded/cutaway axons to show relationships that are cumbersome in separate plans/sections.
Explosion order must reflect a meaningful assembly/program/spatial sequence.

### Perspectives / CG
Use as experiential proof, not as a substitute for resolved drawings.
Camera, openings, mass, floor count, landscape boundaries and fixed architecture must match verified sources.
AI enhancement is allowed only after geometry lock and must pass geometry-drift review.

## 7. Graphic system
For one submission, define and reuse:
- type family and size ladder;
- 3-5 lineweight roles;
- semantic color tokens;
- hatch/texture roles;
- entourage style;
- diagram arrow/label syntax;
- caption syntax;
- scale/north/level notation.

The visual language should make cross-page comparison effortless.

## 8. Output candidates TAKY can present
When the user asks "보고서 어떻게 표현하지?" or equivalent, TAKY should return concrete options, not only principles:
- recommended drawing list;
- each drawing's purpose/question;
- representation technique;
- source required;
- suggested page/panel location;
- visual hierarchy;
- candidate caption;
- risk/unknown;
- production path: CAD/SVG/3D/render/PowerPoint/PDF;
- validation checklist.

For an authorized production task, continue from recommendation into the actual intermediate/final artifact instead of stopping at advice.

## 9. Production route
`BRIEF -> STORY CONTRACT -> SOURCE LOCK -> DRAWING SET -> REPRESENTATION SPEC -> VECTOR/RENDER PRODUCTION -> REPORT/PANEL ASSEMBLY -> ACTUAL-SIZE CHECK -> SOURCE CROSS-CHECK -> REVIEW -> CORRECT -> FINAL`.

Default executable route when the user requests a concrete result:
`ARCHIGROW_COMPETITION_RUN.py -> REPORT recommender -> SOURCE BINDER -> result-specific BUILD -> RENDER -> mechanical validation -> VISUAL QUALITY GATE -> visual/source cross-check`.

Result-specific build owners:
- `A1_BOARD`: A1 physical canvas, hero/grid hierarchy, source-bound visuals, PDF print derivative;
- `A3_REPORT`: A3 page sequence, question/drawing/evidence page logic, PDF derivative;
- `PPT`: editable 16:9 PPTX, one-claim-per-slide, time budget, PDF proof derivative;
- `PDF_DRAWING_BOOK`: sheet index + source-bound drawing pages + cross-reference-ready PDF.

Missing sources are shown as `MISSING SOURCE`; they are never invented to make a layout look complete.

Visual-quality implementation is owned by the quality registry and `TOOLS/ARCHIGROW_COMPETITION_QUALITY.py`:
- Noto Sans KR / Malgun Gothic fallback for Korean delivery;
- 12-column grid, restrained warm-neutral paper, dark ink and one semantic accent;
- drawing-first area ratios and explicit whitespace hierarchy;
- result-specific copy hierarchy: short Korean drawing/slide title, longer reasoning in secondary evidence text;
- vector-first measured drawings and minimum raster resolution checks;
- physical page/slide size + page count + source completeness + raster quality gates.
A rendered file may be mechanically `QUALITY_GATE_PASS` while still requiring final visual/source cross-check on the real project.

Preferred derivative route for CAD drawings:
`DWG/DXF -> cleaned vector -> canonical SVG -> report/PPT/PDF placement`.

Maintain the canonical geometry separately from presentation derivatives.

## 10. Learning capture
Learning granularity is mandatory:
`AGENCY -> COMPETITION -> ENTRY -> SUBMISSION_STAGE/REVISION -> BOARD/PAGE -> DRAWING/RENDER`.
Never collapse all entries in one competition into a single "project style". Within-project comparison is preferred because the brief/site/program are held relatively constant while representation choices vary.
Use `TOOLS/ARCHIGROW_COMPETITION_COMPARE.py` to compare entry-by-entry artifact coverage and representation-technique differences before generalizing a pattern.

After each competition/report cycle capture:
- which drawing first communicated the idea;
- which page/panel confused reviewers;
- reviewer questions indicating missing proof;
- drawings oversized/undersized for their information value;
- color/lineweight/text failures;
- geometry drift between drawing/render;
- techniques that reduced explanation time;
- production steps that caused rework;
- final accepted/winning/rejected outcome only as contextual evidence, never as sole proof of a technique.

Classify learned items under the owner vocabulary:
`CASE / STRATEGY / FRONTIER / CURRENT_BEST / FAILURE/LESSON`.

Capture verified outcome evidence through `TOOLS/ARCHIGROW_COMPETITION_LEARN.py` into the append-only architecture competition representation evidence ledger. Store source/artifact references and reviewer signals rather than copying large raw evidence.
The collector may record `CASE / STRATEGY / FRONTIER / FAILURE_LESSON` candidates only. Promotion to CURRENT_BEST requires repeated evidence and owner approval; one competition result is not universal truth.

## 11. Completion gate
A competition-report representation package is not VERIFIED until:
- brief constraints are checked when available;
- required drawings exist;
- actual output is viewed at delivery size;
- major drawings remain legible;
- geometry/numbers match verified sources;
- the story order is understandable to a cold reader;
- post-freeze content rules are respected;
- final file itself opens/renders correctly.

`BEAUTIFUL != CLEAR`
`CLEAR != CORRECT`
`CORRECT + CLEAR + PROJECT-FIT = TARGET`
