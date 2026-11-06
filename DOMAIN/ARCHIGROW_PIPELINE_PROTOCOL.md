# ARCHIGROW STRONG PIPELINE PROTOCOL

Status: ACTIVE / 2026-10
Rule ID: `TKY-ARCHIPIPE-001`
Purpose: Make architecture-production pipelines resumable, verifiable, replaceable and quality-driven.

## 1. Core rule
`PIPELINE CONNECTED != PIPELINE RELIABLE`.
A production pipeline is strong only when each stage has a clear input contract, output artifact, validation evidence, failure classification, recovery route and promotion rule.

Default lifecycle:
`SOURCE LOCK -> INPUT CONTRACT -> TRANSFORM -> STAGE OUTPUT -> VALIDATE -> PASS/HOLD/FAIL -> NEXT STAGE -> FINAL QUALITY GATE -> LEARN`.

## 2. Mandatory properties
- source preservation and immutable source fingerprint/hash where practical;
- stage-specific input/output contract;
- deterministic checks before subjective review where possible;
- versioned intermediate artifacts, not hidden transient state;
- idempotent/re-runnable stages where practical;
- restart from last verified stage instead of full rerun;
- explicit fallback route when primary tool/path fails;
- no silent format loss or rasterization;
- no silent geometry/formula/law interpretation drift;
- rollback path for reversible writes;
- final artifact must be checked in its actual delivery surface.

## 3. Stage receipt
Every material stage SHOULD emit a compact receipt:
`PIPELINE_ID / STAGE_ID / INPUT_REF+HASH / TOOL+VERSION / OUTPUT_REF+HASH / CHECKS / STATUS / FAILURE_CLASS / NEXT_ROUTE`.

Allowed status: `PASS / HOLD / FAIL / BLOCKED / NEEDS_HUMAN`.
`BLOCKED != FAILED` and `TOOL FAILURE != RESULT IMPOSSIBLE`.

## 4. Recovery logic
On failure:
`ROOT CAUSE -> AFFECTED STAGE -> PRESERVE LAST PASS -> TRY MINIMAL FIX -> RETEST -> FALLBACK TOOL/ROUTE -> ESCALATE ONLY IF HUMAN-ONLY`.
Do not repeat the same failed command/path without materially new evidence.

Fallback examples:
- CAD GUI failure -> Core Console / script / DXF intermediary;
- direct SVG export failure -> PDF/EMF/vector intermediary -> SVG normalization;
- HWP automation failure -> structured data + template merge / alternate HWP automation path;
- Office COM failure -> direct OOXML manipulation where fidelity permits;
- render engine unavailable -> preserve verified 3D/model package and switch engine without rebuilding source geometry.

## 5. Cross-format integrity
Critical facts must survive format transitions:
- CAD geometry/dimensions/areas;
- Excel formulas/units/KPIs;
- HWP law citations/applicability/review result;
- SVG vector hierarchy/text/scale;
- PPT placement/crop/readability;
- 3D mass/openings/floor count/camera assumptions.

If a downstream format cannot preserve a critical property, the pipeline must retain the canonical upstream artifact and mark the derivative limitation.

## 6. Final quality gate
A pipeline is not complete because the last file exists.
Final review asks:
`Does the delivered artifact satisfy the intended result at the actual delivery scale/surface, with source facts and design intent preserved?`

Final PASS requires the smallest sufficient combination of:
- structural/numeric checks;
- visual/render inspection;
- source-to-output comparison;
- cross-format consistency;
- project-specific acceptance criteria.

## 7. Learning
Learning-state semantics are owned by `DOMAIN/ARCHITECTURE_WORK_OS.md` §7. Pipeline evidence may feed a `CASE / STRATEGY / FRONTIER / CURRENT_BEST / FAILURE_LESSON` candidate, but this protocol does not define or approve promotion.
Capture the implementation method and evidence, not just the finished image/file.