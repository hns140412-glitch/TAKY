# EXECUTION PATH ENFORCEMENT PROTOCOL

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE

## Purpose

Prevent a governed system from being bypassed by ad-hoc implementation when a result-producing engine already exists.

## Hard locks

1. `ENGINE_AVAILABLE + BYPASS_USED = GOVERNANCE_FAILURE`.
2. A material `PREVIEW / FINAL / USER_FACING` artifact SHALL carry an executable route attestation from the authorized project/domain engine.
3. One-off scripts, ad-hoc Python, generic HTML, ReportLab, direct generative redraws, or equivalent local workarounds are `EXPERIMENT / DIAGNOSTIC` unless explicitly promoted into the authorized engine with tests and owner reflection.
4. `RULE WRITTEN != RULE ENFORCED`. A policy document cannot satisfy an enforcement requirement by itself.
5. `CODE EXISTS != ROUTE USED`. Engine implementation does not prove the engine was used for the actual artifact.
6. For material user-facing artifacts, the applicable pre-user validation suite is blocking: `NO PASS -> NO SHOW`.
7. HUMAN APPROVAL is for intent, trade-offs, final choice, and authorized exceptions. It SHALL NOT substitute for recoverable defect detection. `HUMAN IS THE KEY != HUMAN IS THE DEBUGGER`.

## Required execution chain

`USER INTENT -> ROUTER -> AUTHORIZED ENGINE -> AUTHORITY LAYERS -> VALIDATION -> USER EXPOSURE GATE -> OUTPUT`

The exact engine and validation suite are owned by the applicable domain/project implementation.

## Bypass exception

A one-off path may be used internally when:
- the authorized engine genuinely cannot perform the diagnostic/experiment;
- no production claim is made;
- the artifact is marked INTERNAL / EXPERIMENTAL;
- the result cannot be shown as final or production preview;
- any useful capability is migrated into the engine before production use.

## Exposure contract

Before user exposure, the runtime must be able to answer:
- which engine produced the artifact?
- which source/revision/content identity was used?
- which blocking gates ran?
- did every applicable blocking gate pass?
- is any result based only on heuristic inference?
- is the artifact experimental or production?
- is the output effect claimed beyond actual evidence?

If these cannot be answered, production exposure is prohibited.

## Handoff / resume boundary

Handoff has three materially distinct modes:
- RESUME — continue a valid execution structure.
- RETROSPECTIVE — analyze prior work; prior execution pointers are evidence only.
- SURGERY — invalidate/rebuild defective architecture; prior production pointers are non-executable until revalidated.

A user request for structural failure analysis, confirmed engine bypass, repeated USER_AS_DEBUGGER recurrence, or post-correction recurrence activates SURGERY rather than ordinary RESUME.
