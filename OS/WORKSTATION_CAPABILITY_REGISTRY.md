# TAKY WORKSTATION CAPABILITY REGISTRY

Verified: 2026-10-03
Device: YKH-SangMinYang

## Capability evidence levels
- `INSTALLED_VERIFIED`: executable/path existence verified.
- `LAUNCH_VERIFIED`: application/CLI launch verified.
- `REPRESENTATIVE_TASK_VERIFIED`: a governed representative task completed with output evidence.
- `PIPELINE_VERIFIED`: the capability completed its intended upstream/downstream handoff with acceptance evidence.

`INSTALLED_VERIFIED != REPRESENTATIVE_TASK_VERIFIED != PIPELINE_VERIFIED`.

## Installed verified
- AutoCAD 2024: `C:/Program Files/Autodesk/AutoCAD 2024/acad.exe` — INSTALLED_VERIFIED
- AutoCAD Core Console: `C:/Program Files/Autodesk/AutoCAD 2024/accoreconsole.exe` — `PIPELINE_VERIFIED` for the verified CAD→Excel→SVG/PPT lane
- Excel: `C:/Program Files/Microsoft Office/root/Office16/EXCEL.EXE` — `PIPELINE_VERIFIED` for the verified KPI/reverse-check lane
- PowerPoint: `C:/Program Files/Microsoft Office/root/Office16/POWERPNT.EXE` — `PIPELINE_VERIFIED` for verified SVG placement/PPTX/PNG delivery
- Word: `C:/Program Files/Microsoft Office/root/Office16/WINWORD.EXE` — INSTALLED_VERIFIED
- Hancom HWP 2024: `C:/Program Files (x86)/Hnc/Office 2024/HOffice130/Bin/Hwp.exe` (13.0.0.711) — `REPRESENTATIVE_TASK_VERIFIED`
- Hancom HWP 2010 legacy: `C:/Program Files (x86)/Hnc/Hwp80/Hwp.exe` — INSTALLED_VERIFIED

## Runtime / representative evidence
### AutoCAD Core Console
- state: `REPRESENTATIVE_TASK_VERIFIED`
- LAST_VERIFY: 2026-10-03
- TOOL: AutoCAD Core Console U.61.0.0 / file version 24.3.61.0.0
- INPUT: versioned copy of a valid DWG; scripted 10 x 20 closed rectangle
- OUTPUT: DXF export; audit receipt `D:/Git PWA/TAKY_AUDIT_LOCAL/TAKY_CAD_REP_VERIFY_20261003.json`
- CHECKS: process exit 0; exported DXF parsed independently; closed 4-vertex polyline found at (0,0)/(10,0)/(10,20)/(0,20); computed area = 200.0; output SHA-256 recorded
- PIPELINE: the same verified geometry was handed to Excel reverse-check, SVG generation and PowerPoint delivery; see `TAKY_CAD_EXCEL_SVG_RECEIPT_20261003.json` and `TAKY_CAD_PPT_RECEIPT_20261003.json`.
- LIMITATIONS: this verifies the governed 2D geometry/KPI/presentation lane; it does not generalize to arbitrary DWG semantics, plotting, xrefs, annotative scales or every CAD production case.

### Excel
- state: `REPRESENTATIVE_TASK_VERIFIED` and `PIPELINE_VERIFIED` for the KPI/reverse-check lane
- LAST_VERIFY: 2026-10-03
- REPRESENTATIVE TASK: created/saved/reopened `TAKY_EXCEL_REP_20261003.xlsx`; formulas survived reopen with values `0.6 / 2.5 / 31` and exact formulas `=B2/B1`, `=B3/B1`, `=B4/B1*1000`; PASS; SHA-256 `830FCBD2B26AE3504077EDFC4BAA32ED90457211D7F9E1AD350BDB045FBD73FC`.
- PIPELINE TASK: CAD area `200.0` imported from verified CAD receipt; Excel reverse-check returned `PASS` with `delta=0`; workbook SHA-256 `F3E00DE4AA4D0E7ADA236D4576E6029E64A107485038A0643F907F82E800DE39`.
- LIMITATIONS: this validates deterministic formula/KPI handoff and reopen integrity, not every macro/add-in/external-link workbook.

### Hancom HWP 2024
- state: `REPRESENTATIVE_TASK_VERIFIED`
- LAST_VERIFY: 2026-10-03
- CHECKS: `HWPFrame.HwpObject` COM launch PASS; new document via `XHwpDocuments.Add`; text inserted with `HAction/InsertText`; in-memory text match PASS; modal `SaveAs` path was abandoned after blocking; alternate `HAction/FileSaveAs` returned `True` and created a 7,168-byte HWP.
- FILE EVIDENCE: `TAKY_HWP_REP_ACTION_20261003.hwp`; SHA-256 `19010155A4E128793FD54B8F7D2C3128D1D870F49C5578203ABCAF243F5F9648`.
- REOPEN CHECK: direct `Open()` path blocked and was not repeated; alternate read-only `HAction/FileOpen` returned `True`, `GetTextFile('TEXT')` returned exactly `TAKY HWP Representative Task 2026-10-03`, PASS.
- LIMITATIONS: HWP representative create/save/reopen/content path is verified; complex tables/styles/forms, legal-review templates and HWPX conversion remain task-specific validation.

### CAD -> Excel -> SVG -> PowerPoint pipeline
- state: `PIPELINE_VERIFIED`
- LAST_VERIFY: 2026-10-03
- FLOW: verified CAD geometry/DXF -> independent area parse (`200.0`) -> Excel KPI/reverse-check (`PASS`, delta `0`) -> SVG derivative -> PowerPoint SVG placement -> PPTX reopen -> 1600x900 PNG export -> actual PNG visual inspection.
- STRUCTURAL CHECKS: PPTX save PASS; PNG export PASS; slide shapes `3` before and after reopen; CAD-area and Excel-PASS text survived reopen.
- VISUAL CHECK: exported PNG inspected at delivery surface; rectangle preserved 10:20 proportion, no clipping, dimensions `10` and `20`, area `200.0`, reverse-check `PASS` and delta `0` readable.
- EVIDENCE: `TAKY_CAD_EXCEL_SVG_RECEIPT_20261003.json`, `TAKY_CAD_PPT_RECEIPT_20261003.json`, `TAKY_CAD_PIPELINE_PRESENTATION_20261003.pptx`, `TAKY_CAD_PIPELINE_SLIDE_20261003.png`.
- PPTX SHA-256: `3CFBAD85A9D1E8E08E250BCF7CAB0FABEE537A41E36ED1998D469D4E269F3F26`; PNG SHA-256: `F2B808DC570AF570D7D7B931F7BD11869ADD5602FD22BCF99987B0D6E8F446D5`.

No representative-task or full-pipeline capability is implied beyond the separately recorded evidence above.

## Not verified at common paths
- Rhino 8
- BricsCAD
- Blender
- Inkscape

`NOT VERIFIED != NOT INSTALLED`; alternative/custom install paths may exist.

## Initial execution priority
1. AutoCAD Core Console for deterministic/batch DWG processing where possible.
2. AutoCAD GUI only when interactive visual work is required.
3. Excel/PowerPoint/Word automation for calculation, reporting and presentation assembly.
4. CAD -> vector/SVG intermediary via available deterministic conversion route; add converter only after capability/security/cost review.
5. 3D/render routes remain capability discovery / FRONTIER until a verified local engine is bound.