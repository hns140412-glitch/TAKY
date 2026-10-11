# TAKY Post-Alpha Capability Verification — 2026-10-03
Status: LOCAL_CAPABILITY_COMPLETE / EXTERNAL_BOUNDARIES_ONLY
Parent: TAKY Alpha LOCAL COMPLETE

## CLOSED / verified
- AutoCAD Core Console 2024: REPRESENTATIVE_TASK_VERIFIED.
  - controlled copy of valid DWG
  - scripted 10 x 20 closed rectangle
  - DXFOUT completed with exit 0
  - independent DXF parser found exact four vertices and area 200.0
  - evidence: D:/Git PWA/TAKY_AUDIT_LOCAL/TAKY_CAD_REP_VERIFY_20261003.json
- Excel: REPRESENTATIVE_TASK_VERIFIED; workbook created/saved/reopened with formulas and values preserved (`0.6 / 2.5 / 31`); pipeline reverse-check of CAD area `200.0` returned `PASS`, delta `0`.
- Hancom HWP 2024: REPRESENTATIVE_TASK_VERIFIED; `HAction/InsertText` -> alternate `FileSaveAs` -> SHA-fixed HWP -> alternate read-only `FileOpen` -> exact text recovered; direct modal SaveAs/Open routes were abandoned after blocking.
- CAD -> Excel -> SVG -> PowerPoint: PIPELINE_VERIFIED; PPTX reopen PASS, 1600x900 PNG export PASS, actual PNG inspected with correct 10:20 proportion, no clipping, area `200.0`, reverse-check `PASS`, delta `0`.
- HWP 2024 executable: 13.0.0.711.

## External dependencies
No remaining local blocker exists in the scoped representative-task / CAD→Excel→SVG/PPT verification lane.
- host/provider-authenticated human identity proof: EXTERNAL_DEPENDENCY; account-session authentication does not equal human-identity proof.
- hosted ChatGPT/Claude automatic interception verification: EXTERNAL_DEPENDENCY; repository/runtime evidence cannot prove hosted native interception.
- broader arbitrary DWG, complex HWP templates/HWPX, macros/add-ins and other production variants require task-specific evidence; they do not invalidate the verified lane.

## Next route
- Preserve this verified lane as CLOSED unless contradictory evidence appears.
- For the next material capability, reuse the same `source -> deterministic check -> delivery-surface inspection -> receipt` pattern.
- External push/merge/deploy/paid API or provider-level enforcement verification remains behind the explicit human gate.

## Canonical post-Alpha checkpoint
- `CURRENT/TAKY/TAKY_POST_ALPHA_CAPABILITY_2026-10-03.json`
- checkpoint hash: `sha256:129ae306cf0906701de00c1330bf28f6154d63a881d4b1c818aa50443d05bc2e`
- immutable HISTORY receipt created under `HISTORY/CHECKPOINTS/TAKY/TAKY_POST_ALPHA_CAPABILITY_2026-10-03/`.
- Alpha runtime manifest refreshed to v2026-10-03.8 and 32/32 PASS; prior v7 preserved in HISTORY after capability-registry promotion.

No push / merge / deploy / paid API performed.
