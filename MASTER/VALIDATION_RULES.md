# TAKY Validation Rules — REV_00

## Global gate
SOURCE / APPROVED REFERENCE → IDENTITY & PROTECTED-STATE LOCK → EXECUTION → ACTUAL RESULT INSPECTION → 1:1 COMPARE → DOMAIN CHECK → REGRESSION CHECK → PASS / FAIL.

FAIL → do not present as completed or canonical.
PASS → may proceed only to the next authorized state.

## Artifact / image rule
NAME ≠ VISUAL ID.
REFERENCE IMAGE = VISUAL ID when explicitly approved by the user.
Approved Visual ID must not be regenerated into a different species, face, hair, ears, body, gender impression, signature prop, or identity without explicit approved delta.

For composite images validate every character/object individually and positional mapping. Correct labels with wrong visual identity = FAIL.

## Validation dimensions
- Source coverage
- Authority
- Ownership
- Data flow
- Protected decisions / HARD LOCKs
- Identity consistency
- Functional correctness
- Result correctness
- Regression
- Omission / duplication / conflict
- Implementation evidence
- Release evidence

## Status vocabulary
PASS / FAIL / NOT PASS / UNKNOWN / UNVERIFIED / NOT PERFORMED.
Do not collapse design validation into implementation validation.
