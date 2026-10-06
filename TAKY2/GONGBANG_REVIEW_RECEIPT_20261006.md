# TAKY 2.0 공방검토 Decision & Defense Receipt — 2026-10-06

Status:
- INTERNAL / BASIC GONGBANG REVIEW: CLOSE
- STRONG EXTERNAL-INDEPENDENT GONGBANG REVIEW: HOLD
- MASTER / Q001-Q003: remain CLOSED
- push / merge / deploy: NOT PERFORMED

## Scope

Target baseline:
- branch: taky-2.0-orchestrator-2026-10-05
- starting commit: 1ec0ab39e0f0a4a99cdb7b48c19d3e8a61e2d88c
- scope: validator ownership, evidence validity, DONE enforcement, independent review boundary
- protocol: TAKY2/GONGBANG_REVIEW_PROTOCOL_V1.md

## Constructive review

Completed:
- comparison review
- analysis / supplement / improvement
- deep-search case comparison
- optimization toward minimum-sufficient runtime enforcement
- error verification
- self verification
- regression verification

External practice basis used for method design:
- NIST / NASA IV&V: objective evidence and materially independent verification
- OWASP threat modeling: threat -> mitigation -> validation
- Google engineering review: small reviewable changes, tests that fail on broken behavior, design/functionality/test review

These sources informed the method only; TAKY Canonical remains authority.

## Attack -> Decision -> Defense

### ATTACK-001 — role-string fake independence
Finding:
- STRONG could claim independent_reviewer="CLAUDE" without an actual independent review artifact.
Decision: ADOPT / P1.
Defense:
- independent_review_registry introduced.
- STRONG verification requires independent_review_ref bound to receipt/result digest/authority/scope.
- primary verifier, producer and independent reviewer identities cannot collapse.
- string-only reviewer claim negative test added.

### ATTACK-002 — predicate/evidence decoupling
Finding:
- required_verifications could be listed without explicit predicate -> evidence binding.
Decision: ADOPT / P1.
Defense:
- completion_registry.verification_evidence required.
- every required predicate must map to accepted evidence.
- independent predicate must map to independent_review evidence.

### ATTACK-003 — DONE decision not retained as receipt
Finding:
- preflight gates had receipts but final DONE decision itself was not preserved.
Decision: ADOPT / P1.
Defense:
- done_gate_receipts added.
- DONE validator profile / decision / evidence / authority / report digest persisted.

### ATTACK-004 — implicit USER event acceptance
Finding:
- trusted_user_event required actor/kind/receipt/verifier but not explicit=True.
Decision: ADOPT / P1.
Defense:
- explicit=True is now mandatory.
- negative test added for non-explicit confirmation.

### ATTACK-005 — evidence laundering
Finding:
- execution verifier could potentially present review-like evidence as if it were ordinary execution evidence.
Decision: ADOPT / P1.
Defense:
- execution verifier evidence types narrowed.
- independent_review is accepted only through the independent-review path.

### ATTACK-006 — fabricated raw review receipt on reattack
Finding:
- first defense exposed a raw record-independent-review CLI accepting JSON/reviewer_id, allowing a fabricated reviewer receipt.
Decision: ADOPT / P1.
Defense:
- raw CLI ingestion removed.
- record_independent_review now requires a separate review attestation verifier callback and verifier identity.
- attestation verifier must be separate from reviewer and executor.
- negative test rejects unverified attestation.

### ATTACK-007 — external independent re-verification unavailable
Finding:
- Codex independent run unavailable because usage limit was reached.
- Claude CLI review did not produce a usable review result in this runtime despite route changes; repeated calls were stopped.
Decision: HOLD, not PASS.
Defense:
- no fake reviewer receipt generated.
- STRONG closure is withheld until a real independent-review adapter produces accepted evidence.
- internal negative tests/regression continue without burning the same external path repeatedly.

## Reattack result

Reattack discovered ATTACK-006 after the first defense, proving the review loop was not merely ceremonial.
ATTACK-006 was patched and the raw ingestion route removed.

Current enforced boundaries:
- role-name string != independent evidence
- AI/self-report != DONE evidence
- SUPERSEDED/stale evidence != current claim evidence
- verification predicate != satisfied until bound evidence is accepted
- USER_CONFIRMED != valid without explicit receipt-bound USER event
- STRONG != valid without actual independent review receipt + attestation

## Verification

Final local verification:
- TAKY2 full suite: 110 passed
- subtests: 51 passed
- py_compile: PASS
- git diff --check: PASS

## Closure decision

INTERNAL/BASIC CLOSE:
- unresolved local P0: 0
- unresolved local P1: 0
- regression: PASS
- defense survived reattack and negative tests

STRONG HOLD:
- actual external independent reviewer receipt is not available in this cycle.
- therefore STRONG PASS/CLOSE is explicitly prohibited.

Re-entry trigger:
- a real Claude/other approved independent reviewer adapter becomes available and produces an attested review receipt for the current target revision/result.
- Codex verification may be rerun when availability returns, by Necessity rather than automatic repetition.

DEEP MEMORY — LIGHT EXECUTION.
