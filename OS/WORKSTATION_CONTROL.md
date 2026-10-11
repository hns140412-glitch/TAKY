# TAKY WORKSTATION CONTROL OS

Status: ACTIVE OPERATING POLICY / 2026-10
Rule ID: `TKY-WORKSTATION-001`
Role: Govern controlled PC-side work for CAD, Excel, documents, images and architecture production under TAKY.

## 1. Principle
`PC ACCESS != FULL PC AUTHORITY`.
`CLEANUP SURVIVAL != CACHE PRESERVATION`.
AI system continuity SHALL NOT depend on `%TEMP%`, browser cache, transient session files, or disposable startup artifacts. Durable configuration lives in governed repository/user-profile/Drive locations; transient artifacts must be reproducible after cleanup or reboot.
TAKY may use the workstation as an execution surface only inside explicit workspace, application and action boundaries.
`WORKSTATION OWNS EXECUTION / STORAGE / VERIFICATION MECHANICS; DOMAIN / PROJECT OWNERS OWN FACTS / LAW / DESIGN SEMANTICS / APPROVAL AUTHORITY`.

Default flow:
`REQUEST -> TARGET FILE/PROJECT -> SOURCE PRESERVE -> OPEN/INSPECT -> EDIT/CREATE -> APP/RENDER VERIFY -> SAVE AS VERSION -> CROSS-CHECK -> LEARN`.

The user requests the result; TAKY owns the implementation path, tool choice, validation and recovery within authorized scope.

## 2. Workspace classes
- `W0_READ_REFERENCE` — source/reference locations; read by default.
- `W1_ACTIVE_PROJECT` — authorized project working folders; reversible create/edit allowed.
- `W2_OUTPUT` — generated review/final outputs; write allowed with provenance.
- `W3_SENSITIVE` — credentials, personal/system/security data; deny unless explicitly scoped and necessary.
- `W4_SYSTEM` — OS/program/system directories; no ordinary project writes.

Original source files SHALL NOT be silently overwritten. Prefer versioned copy / SAVE AS / working copy unless exact in-place editing is explicitly required and recoverable.
## 3. Application classes
Initial governed applications/surfaces:
- CAD/BIM: AutoCAD/BricsCAD/Rhino/Revit or equivalent when available.
- Spreadsheet: Excel-compatible workflows.
- Documents/presentations: Word/PowerPoint-compatible workflows.
- PDF/image/render outputs for review and comparison.

Application automation must preserve actual project semantics. GUI success alone is not result PASS.

## 4. CAD / Excel result gate
CAD review should prefer object/geometry evidence: layer, entity type, closed boundary, coordinate/location, area/dimension and revision context.
Excel review should preserve formulas, source values, subtotals/totals, units, named ranges/print areas and cross-sheet consistency where material.

For coupled work use:
`CAD GEOMETRY -> AREA/KPI EXTRACTION -> EXCEL CALCULATION -> REVERSE CHECK TO CAD -> RENDER/PDF/PRINT VERIFY`.

`FILE SAVED != RESULT VERIFIED`.
`GUI LOOKS RIGHT != GEOMETRY/FORMULA PASS`.

## 5. Action authority
- READ/INSPECT/SEARCH: allowed inside governed workspace.
- CREATE/EDIT/SAVE-AS: allowed for authorized project work when reversible and provenance is preserved.
- OVERWRITE ORIGINAL / BULK RENAME / MOVE: require a recoverable plan and exact task need.
- DELETE / SYSTEM CONFIG / INSTALL / UNINSTALL / SECURITY / EXTERNAL SEND / CLOUD SHARE: human approval gate.

## 6. ArchiGrow learning bridge
Architecture workstation results feed ArchiGrow as evidence:
`DESIRED RESULT -> CAD/EXCEL IMPLEMENTATION -> ACTUAL OUTPUT -> GAP/ERROR -> RULE/STRATEGY CAUSE -> DOMAIN LEARNING CANDIDATE`.
Learning-state semantics and promotion are owned by `DOMAIN/ARCHITECTURE_WORK_OS.md` §7. This workstation layer supplies implementation/result evidence only.
Do not learn only the final appearance; capture how geometry, law, calculation, detailing and production rules were resolved.
## 7. CAD-to-SVG / presentation-quality vector pipeline
For CAD drawings that must enter PPT, reports, web diagrams or design reviews, prefer a vector-preserving path instead of raster screenshots.

Target flow:
`CAD/DWG/DXF -> CLEAN VIEW/LAYER SET -> VECTOR EXPORT/CONVERSION -> SVG NORMALIZE -> VISUAL VERIFY -> PPT/REPORT/WEB EMBED`.

Requirements when materially relevant:
- preserve line/vector geometry; avoid rasterization unless explicitly needed;
- control layer visibility, lineweight, linetype, hatch density and text before export;
- crop to intended drawing extents and remove off-canvas residue;
- normalize SVG viewBox, page bounds and scale;
- preserve readable text where possible, or convert fonts/labels only when compatibility requires it;
- keep transparent background unless a specified presentation surface requires otherwise;
- verify stroke hierarchy at target slide/report scale, not only at CAD zoom;
- generate a high-resolution raster fallback only as a compatibility derivative, never as the primary source when SVG is viable.

Presentation route:
`SOURCE CAD -> CANONICAL PRESENTATION SVG DERIVATIVE -> PPT/REPORT DERIVATIVE`.
The SVG is canonical only for the presentation/vector derivative lane, never a replacement for authoritative source geometry. Keep it separately stored so downstream documents do not become the only surviving copy.

Quality gate:
`EXPORT EXISTS != PRESENTATION PASS`.
Check actual placement in PPT/report for scale, clipping, line legibility, text readability, contrast and visual hierarchy.
## 8. HWP/HWPX legal-review document pipeline
Korean architecture/legal review documents in HWP/HWPX are governed first-class inputs and outputs, not unsupported side files.

Target flow:
`CAD/PROJECT FACT -> EXCEL DESIGN OVERVIEW/KPI HUB -> HWP/HWPX LEGAL REVIEW -> CURRENT LAW SOURCE CHECK -> CAD/EXCEL/HWP CROSS-CHECK -> REVIEW DELTA -> VERSIONED HWP/HWPX FINAL SUBMISSION + PDF/DOCX DERIVATIVES`.

Excel Design Overview is a structured project-fact projection/hub for quantified architecture review, not the semantic owner of project facts. Each material value must preserve its originating project/domain source, version, unit and verification state. CAD, HWP/HWPX legal-review documents, area/parking/FAR calculations, PPT/report outputs and ArchiGrow review should reference the same verified dataset instead of maintaining untraceable independent copies.

Preferred linkage:
`CAD GEOMETRY -> EXCEL DESIGN OVERVIEW -> LAW/REVIEW LOGIC -> HWP/HWPX SUBMISSION -> PPT/REPORT`.

The design-overview dataset should expose stable fields/IDs for material project facts such as site area, building area, gross floor area, use, floors, coverage ratio, FAR, parking, unit/program counts and other project-specific KPIs so downstream outputs can be regenerated and cross-checked from one structured source.

HWP/HWPX is the default governed delivery format for Korean architecture/legal-review submissions when applicable; file format does not own the legal conclusion or project fact authority. PDF/DOCX are review/preview/interchange derivatives unless the user explicitly requests another submission format.

Required structure when materially relevant:
- project / site identity;
- Excel design-overview source/version;
- site area, building area, gross floor area, floor count, use/program, building coverage ratio, FAR, parking count and other applicable core project KPIs;
- cited law / ordinance / notice / guideline;
- article / paragraph / item;
- effective date / source date;
- applicability conditions;
- review conclusion and assumptions;
- related area/FAR/parking/height/setback/egress/fire/accessibility or other design variable;
- source authority and verification state;
- change impact on CAD / Excel / report outputs.

Rules:
- preserve the original HWP/HWPX and never silently overwrite it;
- converted PDF/DOCX/text is a working derivative, not a replacement authority;
- legal conclusions must be rechecked against current authoritative sources when the task depends on present applicability;
- extracted numbers/conditions should reverse-check against CAD geometry and Excel calculations where applicable;
- a formatted legal-review report is not PASS if source applicability or project identity is unverified.
