# TAKY2 V3 QUOTA-SAFE REMEDIATION CHECKPOINT — 2026-10-08

Status: LOCAL REMEDIATION PASS / INDEPENDENT PASS PENDING / V3 NOT PROMOTED

## Resource discipline
- User reported Claude usage at ~97% and Codex ~63% remaining.
- After that instruction: Claude calls = 0.
- Codex calls = exactly 1 bounded CODEX_VERIFY_ONLY packet review.
- All collection, editing, tests, compile, diff checks were performed with Remote/local tooling.

## Codex one-shot verifier
- packet: TAKY2/TAKY2_V3_CODEX_FINAL_PACKET_20261008.txt
- packet digest: 4545d9e78ee3cef0991c
- receipt: pf:taky2-v3-codex-final-20261008:1f948e50310c7c90
- Codex result: HOLD
- material findings: one HIGH
- Codex checked and accepted the prior remediations for:
  - QUALITY_REQUIRED acceptance binding
  - QUALITY_REQUIRED quality floor
  - persisted claim/checkpoint before invocation
  - duplicate receipt rejection
  - timeout/exception OUTCOME_UNKNOWN handling
  - paid/subscription billing binding
- remaining HIGH:
  nonzero external model-CLI termination could still be classified FAILED even when provider invocation could not be ruled out.

## HIGH remediation
TAKY2/bridges.py now treats a nonzero result from an external invocation as OUTCOME_UNKNOWN unless the runner explicitly supplies:
provider_call_confirmed_absent = true

Effect:
- uncertain external side effect/spend is not silently retryable as ordinary FAILED;
- known local/pre-provider validation failure can still be terminal FAILED when absence of provider invocation is explicitly attested.

Regression added:
1. external nonzero exit without no-provider attestation => OUTCOME_UNKNOWN
2. external nonzero exit with provider_call_confirmed_absent=true => FAILED

## Final local verification
- full TAKY2: 205 passed + 54 subtests
- compileall: PASS
- git diff --check: PASS
- only existing LF -> CRLF warning for TAKY2/NEW_CHAT_START_20261006_LATEST.md
- runtime_version: 136
- authority_digest: e48ca039a387299fb3ea

## Current verdict
The only material issue returned by the single quota-bounded Codex review was corrected and locally regression-verified.
However the independent review artifact itself remains HOLD because its finding was fixed after that review.
Do not manufacture a PASS and do not spend another model call now merely to change the label.

V3 remains NOT PROMOTED until a later compact independent recheck confirms the final delta.
The later recheck should contain only:
- the Codex HIGH finding,
- the small execute_with_receipt nonzero-external patch,
- its two regression tests,
- final 205+54 / compile / diff-check evidence.
