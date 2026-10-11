---
name: cross-model-review
description: Use Codex or Gemini as an independent reviewer only when a material delta justifies cross-validation.
---
Use this only for a specific material delta, not as a default duplicate-agent loop.
Default reviewer: Codex for code/diff/implementation attack review.
Use Gemini for materially useful long-context/research/alternative synthesis review.
Route both through `TOOLS/TAKY_MODEL_REVIEW.ps1` so provider API-key fallbacks are disabled.
Give the reviewer a compact task contract, changed files/diff, acceptance criteria, and known risks.
Ask it to attack assumptions, scope drift, regressions, and missing tests.
The builder must classify each finding as ACCEPT / REJECT / HOLD with evidence.
Do not let any model promote product requirements or CURRENT authority.
Do not repeat cross-review unless there is a new material delta, failure signal, or unresolved disagreement.
