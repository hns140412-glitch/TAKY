# TAKY Validation Rules — REV_00

## Global gate
SOURCE / APPROVED REFERENCE → IDENTITY & PROTECTED-STATE LOCK → APPLICABLE-RULE EXTRACTION → EXECUTION → ACTUAL RESULT INSPECTION → 1:1 COMPARE → INTEGRATED-RESULT CHECK → DOMAIN CHECK → IMPACT CHECK → REGRESSION CHECK → PASS / FAIL.

FAIL → do not present as completed or canonical.
PASS → may proceed only to the next authorized state.

## Rule activation gate
CANONICAL LOADED ≠ CANONICAL APPLIED.
RULE EXISTS ≠ RULE APPLIED.
RULE MENTIONED ≠ RESULT VALIDATED.

For material work, identify the rules actually applicable to the current task/domain/project and verify the real output against them. Generic UX, engineering, writing, design or implementation practice shall not substitute for a specific active MASTER / GUIDE / DOMAIN / PROJECT rule.

## Integrated-result gate
COMPONENT PASS ≠ INTEGRATED RESULT PASS.
LAYER SEPARATION ≠ COMPOSITION PASS.
NO COLLISION ≠ GOOD RELATIONSHIP.
INTENDED OVERLAP ≠ ACCIDENTAL COLLISION.

When separately produced parts are assembled, inspect the final output for applicable alignment, spacing, anchoring, hierarchy, overlap/collision, clipping, z-order, source/ownership relationships, safe areas/boundaries, state transitions and representative target conditions.

Planned overlap may PASS when intentional and task-supporting. Unplanned overlap, excessive separation, crooked/inconsistent alignment, broken anchoring or alternate-state composition failure = FAIL when it harms the intended relation or usability.

## Artifact / image rule
NAME ≠ VISUAL ID.
REFERENCE IMAGE = VISUAL ID when explicitly approved by the user.
Approved Visual ID must not be regenerated into a different species, face, hair, ears, body, gender impression, signature prop, or identity without explicit approved delta.

For composite images validate every character/object individually and positional mapping. Correct labels with wrong visual identity = FAIL.

## Validation independence
SELF-VALIDATION, CROSS-VALIDATION, IMPACT VALIDATION and REGRESSION VALIDATION are separate gates.

- SELF-VALIDATION: compare result to active contract/rules.
- CROSS-VALIDATION: use an independent evidence path, method, source, representation or validator when material.
- IMPACT VALIDATION: inspect intended and unintended downstream/upstream consequences.
- REGRESSION VALIDATION: compare protected pre-change state to post-change state.

SAME ASSERTION REPEATED ≠ CROSS-VALIDATION.
CHANGE WORKS ≠ IMPACT PASS.
NEW RULE PRESENT ≠ REGRESSION PASS.

## Validation dimensions
- Source coverage
- Authority
- Applicability / active-rule coverage
- Ownership
- Data flow
- Protected decisions / HARD LOCKs
- Identity consistency
- Functional correctness
- Result correctness
- Integrated composition / relationship correctness
- Impact
- Regression
- Omission / duplication / conflict
- Implementation evidence
- Release evidence

## Status vocabulary
PASS / FAIL / NOT PASS / UNKNOWN / UNVERIFIED / NOT PERFORMED.
Do not collapse design validation into implementation validation.
Do not claim PASS when material source coverage or reverse-validation remains UNVERIFIED.
