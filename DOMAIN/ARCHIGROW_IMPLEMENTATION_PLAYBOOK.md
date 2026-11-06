# ARCHIGROW IMPLEMENTATION PLAYBOOK

Status: ACTIVE / 2026-10
Authority: subordinate to `DOMAIN/ARCHITECTURE_WORK_OS.md` and TAKY governance.
Purpose: Turn architecture examples and user intents into repeatable implementation routes, not reference-only inspiration.

## 1. Execution contract
Every material architecture-production task should resolve:
`DESIRED RESULT -> INPUT TYPE -> REQUIRED INTERPRETATION -> TOOLCHAIN -> INTERMEDIATE ARTIFACTS -> QUALITY GATES -> FINAL OUTPUT -> LEARNING`.

Do not stop at advice when an authorized workstation/tool path can materially produce or improve the requested artifact.

## 2. Case schema
Each reusable case records:
- `CASE_ID`
- `USER_GOAL`
- `INPUTS`
- `LOCKED_FACTS`
- `ASSUMPTIONS`
- `TOOLCHAIN`
- `TRANSFORM_STEPS`
- `INTERMEDIATE_ARTIFACTS`
- `QUALITY_CRITERIA`
- `VALIDATION_EVIDENCE`
- `FINAL_OUTPUTS`
- `FAILURE_MODES`
- `WHY_IT_WORKED`
- `REUSABLE_STRATEGY`
- `PROMOTION_STATE`: one value from the vocabulary owned by `DOMAIN/ARCHITECTURE_WORK_OS.md` §7 (CASE / STRATEGY / FRONTIER / CURRENT_BEST / FAILURE_LESSON); this playbook records state but does not own promotion semantics

## 3. Initial implementation routes
### A. Sketch / reference image -> drawing
`SKETCH/IMAGE -> SCALE/GRID/AXIS INFERENCE -> SPACE/BOUNDARY INTERPRETATION -> 2D VECTOR/CAD DRAFT -> DIMENSION/AREA CHECK -> USER-INTENT COMPARE -> REVISION`.
Required: keep uncertain geometry explicit; never invent dimensions as project facts. Produce CAD/DXF/DWG or vector intermediate when tool support permits.

### B. CAD drawing -> presentation vector
`DWG/DXF -> CLEAN LAYERS -> LINEWEIGHT/TEXT/HATCH NORMALIZATION -> SVG -> TARGET-SCALE CHECK -> PPT/REPORT/WEB`.
Canonical derivative: SVG. Raster is fallback only.

### C. Drawing / sketch -> 3D mass/model
`2D GEOMETRY -> LEVEL/HEIGHT/PROGRAM ASSUMPTIONS -> 3D MASS -> OPENING/CORE/ENVELOPE -> CAMERA CHECK -> GEOMETRY VALIDATION -> MODEL EXPORT`.
Preserve source dimensions and clearly tag inferred heights/materials.

### D. Verified 3D -> exterior rendering / CG
`VERIFIED MODEL -> CAMERA -> MATERIAL -> LIGHT -> LANDSCAPE/CONTEXT -> RENDER -> OPTIONAL AI ENHANCEMENT -> GEOMETRY-DRIFT CHECK -> FINAL CG`.
AI enhancement must not silently alter approved mass, openings, floor count, structure or site geometry.

### E. Plan/model -> interior perspective
`ROOM/PLAN FACTS -> CAMERA/EYE HEIGHT -> WALL/OPENING/FIXED ELEMENTS -> MATERIAL/FURNITURE/LIGHTING -> RENDER -> PLAN/MODEL CROSS-CHECK -> FINAL INTERIOR VIEW`.
Separate fixed architectural facts from styling candidates.

### F. CAD + Excel -> quantified design review
`CAD OBJECT/AREA -> EXTRACT -> EXCEL FORMULA/KPI -> CROSS-SHEET CHECK -> REVERSE CHECK TO CAD -> OPTION COMPARISON -> REPORT/PPT`.
Tools (candidate output only): `TOOLS/ARCHIGROW_AREA_DXF_SVG.py` (layer-mapped DXF boundaries -> SVG/CSV/area overview + TKY-ARCHIPIPE-001 stage receipt; exact overlap/containment, unit-conflict and hidden-block HOLD gates), `TOOLS/ARCHIGROW_DESIGN_OVERVIEW_BIND.py` (stale-source/geometry HOLD; never overwrites the approved overview), `TOOLS/ARCHIGROW_USE_GROUP_CLASSIFIER.py` (use-group review index; legal classification remains source-verified), `TOOLS/ARCHIGROW_WORKFLOW_ROUTER.py` (non-executing route plan). Regression: `ENFORCEMENT/architecture_area_evidence_test.py`. Connected execution (area -> overview -> KPI -> CAD/model reverse cross-check, plus regulatory/geometry/production/competition stages): `TOOLS/ARCHIGROW_PIPELINE_RUN.py`.

### H. Contractor manual + existing CAD/SVG -> source-bound design review and options
`CONTRACTOR STANDARD ORIGINAL + VERSION/PAGE -> TRANSCRIBED RULE CANDIDATES -> DRAWING REVISION/PROJECT LOCK -> TAGGED VECTOR GEOMETRY -> CHECK -> FEASIBLE DESIGN VARIABLES -> CANDIDATE ALTERNATIVES -> 2D/3D CROSS-CHECK -> EXCEL/PPT DESIGN GATE -> SOURCE-TO-OUTPUT REVIEW`.

- The manual's original file and SHA/revision/page are prerequisites; a transcribed requirement is a candidate until independently compared with the source. Distinguish legal obligations, contractor mandatory items, recommendations, standard example plans, and project-authorized exceptions.
- SVG shapes are display geometry, not trustworthy wall/door/room semantics. Bind to CAD layer/object handles and Rhino/Grasshopper outputs via explicit identity/provenance. Missing mappings, unsupported paths/transforms and unknown heights produce HOLD, not invented objects.
- Structural walls, slabs, MEP shafts and approved facts remain locked unless an alternate scope explicitly authorizes their candidate revision.
- Analyze both rule violations and improvement opportunities. Propose variants with actual geometry and quantified deltas, not only prose; distinguish concept geometry from usable project design.
- Parking: stall count/aisle/entrance/slope/height/3D obstacle review and verified vehicle swept-path analysis are separate checks. Simple 2.5D extruded-clearance checks do not prove safe circulation.
- Recalculate impacted tables from the same source data and expose SVG overlays + Excel rows + PPT slots with independent rendering/print QA, before treating a report as client-ready.
- Initial opt-in executable: `TOOLS/ARCHIGROW_DESIGN_RULE_REVIEW.py` and `PLAN_MANUAL_REVIEW` in `TOOLS/ARCHIGROW_WORKFLOW_ROUTER.py`. Generates candidate JSON, alternative vector overlay, CSV and local read-only HTML preview. Numeric demo data is never a real contractor/project precedent; tests: `ENFORCEMENT/architecture_design_rule_review_test.py`.
- Commercial/reference exemplars: Finch plan library/constraints, Solibri rule sets/model checks, TestFit parking solver. Extract design principles; don't claim their underlying algorithm is implemented.

### G. Architecture competition -> report / presentation drawing package
`COMPETITION BRIEF -> STORY CONTRACT -> SOURCE LOCK -> DRAWING QUESTIONS -> REPRESENTATION METHOD -> VECTOR/RENDER PRODUCTION -> REPORT/PANEL ASSEMBLY -> ACTUAL-SCALE REVIEW -> SOURCE CROSS-CHECK -> CORRECT -> FINAL`.

Load `DOMAIN/ARCHITECTURE_COMPETITION_REPORT_PLAYBOOK.md` and the representation registry.
The system should present concrete output candidates: required/recommended drawing list, purpose, representation technique, source requirement, page/panel role, production path and validation.
When the brief is unavailable, the result is `BRIEF_UNVERIFIED`; generic best practice never substitutes for official submission requirements.

## 4. Tool-selection rule
Choose tools by result quality and reversibility, not habit.
Preferred order:
1. native project application / deterministic geometry-data path;
2. local conversion or scripting;
3. governed browser/desktop automation;
4. render/AI enhancement only after geometry is stable;
5. external paid/API path only after explicit approval.

A tool is replaceable. The implementation contract, intermediate assets and evidence are not.