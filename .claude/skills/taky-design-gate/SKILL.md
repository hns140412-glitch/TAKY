---
name: taky-design-gate
description: TAKY design gate for UI, web pages and HTML slides. Use when building or revising a screen, landing page, app UI or HTML/PPT deck in a TAKY project, or when asked to review design quality, remove the "AI look", or check a design before handoff. Runs DESIGN.md spec → 2-sample pilot → freeze → real-browser render loop → receipt, per MASTER/UI_REFERENCE_PROTOCOL.md §20 (DGC-01..21).
---

# TAKY Design Gate

Owner rule: `MASTER/UI_REFERENCE_PROTOCOL.md` §20 (TKY-UIREF-001). This skill is the procedure; the rule wins on conflict.
Core: **criteria + context + feedback**. Rules alone don't fix design; looking at the real render does.

`REFERENCE != AUTHORITY` · `TOKEN MATCH != DESIGN PASS` · `EXPORT SUCCESS != EDITABLE PASS` · `CODE DONE != VALUE DELIVERED`

## 00. Read the project's contract first (DGC-22)
Find and read the project's screen contract, design-gate review and approved visual direction before proposing anything. List each required element; every candidate must keep all of them unless the USER approved a contract change.

## 0. Mode (DGC-01)
- Approved direction + token manifest exist → `EXECUTE`.
- Otherwise → `EXPLORE`. Output is `PILOT_FIXTURE_ONLY` and never ships until the user picks a direction.
- Write the mode into DESIGN.md `taky.mode`.

## 0b. Replica study (EXPLORE)
To learn from a reference product, run the replica skills: `replica-recon` (screens, flows, components, data model) → `replica-design` (measured tokens) → build a replica → `replica-diff` (layout score ≥ 90 shows the structure was understood). Then take it apart: what works, what users complain about (`replica-entrepreneur`), and what TAKY's bar requires.
The replica is PILOT_FIXTURE_ONLY. The result is a new design that clears the TAKY bar and beats the replica on named axes. Rule: §20.1d.

## 1. Spec: DESIGN.md (DGC-02, DGC-18)
Use the google-labs-code/design.md format (YAML tokens + prose). It must contain:
- `colors` and `typography` tokens (fontFamily named explicitly; Korean text names Pretendard / Noto Sans KR or the project font, DGC-19).
- `## Layout` (composition rules, not just values).
- `## Do's and Don'ts` with real prohibitions: colors/gradients/shadows/icons not in the spec, generic defaults (see the frontend-design tells), gradient-clipped text and mask-image (print-unsafe).
- `taky:` block: `mode`, `design_system_id`, `version`, `source_commit` (required in EXECUTE). Brand DESIGN.md files copied from galleries are `REFERENCE`, never authority; strip brand identity before use (§0, §6).

## 2. Requirements and deletion (DGC-04, DGC-06)
- Every element needs an owner reason. No owner → candidate for removal.
- Before freeze, record `DELETION_PASS {removed[], reason, re-added[]}`. Zero removed needs a reason. Never delete safety or accessibility affordances.

## 3. Pilot (DGC-05, DGC-21)
- EXPLORE: show ≥3 materially different candidates (IA, hierarchy, palette role, type scale, component set or density class). State the cost budget first.
- Build **2 representative samples first**, not the cover/hero: a screen or slide with a diagram/table and one with numbers/charts. Do not generate the rest until the user confirms.
- Then fix the rules: title position/size, page number, background/accent (one accent use per screen), fonts and minimum size, margins/spacing, diagram border/radius/fill.

## 4. Freeze (DGC-07, DGC-08)
Freeze = DESIGN.md hash + render-level reference screenshot hash. Handoffs (Claude Design → Claude Code, or between agents) carry this `spec_sha256`. Without it, do not start implementation.

## 5. Build → see → fix loop (DG-08)
Run the harness after each meaningful change, at least 2 loops:

```bash
python3 ENFORCEMENT/design_gate_harness.py --design DESIGN.md --target <file-or-url> --out <dir>
```

Slides: add `--viewports '[{"id":"slide","width":1920,"height":1080}]'`. Native app or other form factors: declare their own viewports (DGC-16).
Read the screenshots in `<dir>` yourself. Fix the most severe issue first, then rerun.
Compare with a reference screenshot: `--reference <dir>/desktop.png` (file name = viewport id). Replica stage uses the original; result stage uses the approved TAKY reference.
Exit 0 PASS / 1 FAIL / 3 HOLD. HOLD = harness or environment problem, so fix the harness, do not call the product failed.
For interactive checks (click, input, state), use the Playwright MCP from `.mcp.json` if it is connected.

## 6. Independent review
Hand the receipt plus screenshots to the `design-gate-reviewer` agent. It never sees your reasoning, only the artifacts.

## 7. Report
Report verdict, mode/claim ceiling, failed sub-receipts, DELETION_PASS and receipt path. Keep these separate: harness PASS ≠ approved-reference visual compare (`ENFORCEMENT/design_gate_receipt.py`) ≠ user approval ≠ released.

## Limits
- GENERIC_TELLS is advisory. Taste is judged by a reviewer, not by a regex (DGC-12).
- The harness checks the mechanical parts only: overflow per viewport, off-token colors, font actually rendered, print-unsafe CSS, PDF produced, minimum text size and target size.
- Third-party: only replica-skill is vendored (MIT, USER-approved 2026-11-06 for replica study). Others stay on hold (RVR-121).
