# RA rework execution and projection review

Task: TAKY_AI_HARDENING_CODEX_REWORK_2026-10-04.
Repository: D:/Git PWA/TAKY; target: existing branch
`character-asset-behavior-separation-2026-09-30`.
Verified base HEAD: `fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e`.
Authority: current user contract and CODEX_AI_HARDENING_REAUDIT_FINAL_2026-10-04.md.

Preflight: fix only RA-01 compensated retry evidence/identity, RA-02 approval/effect
cross-binding, and RA-03 reviewed projection freshness. Priority: fail closed before
authorization mutation, preserve legitimate retries and existing history/CAS, then
attest the current owner/body pair. Protect all pre-existing worktree changes and
unrelated CLOSED work. Reuse evidence_ref_validator, runtime_orchestrator,
side_effect_ledger and active_rule_profile_freshness_validator as existing owners.
Next action: implement focused regressions and minimal fixes, compare projection
owners with the prior attestation basis, then run required validation.
Stop conditions: conflicting requirements, unverifiable review basis, or failed
required checks; none may be reported as closure.

Allowed scope: the two runtime owners, their focused tests, profile metadata/body
if semantically needed, existing registry projection binding, and review evidence.
Forbidden: unrelated edits, reset/clean/revert, push, merge, deployment, Netlify,
paid API or external side effects. Local implementation is authorized. No merge
or deployment approval is requested or implied.

Acceptance: one verified compensated retry only per evidence identity despite
metadata refresh; nonexistent/unverifiable evidence denied; approval action,
canonical payload hash and target equal the effect before claim/consume; current
profile validated against a newly reviewed content-addressed receipt.

Required commands: `python -B -m unittest` for side_effect_ledger_test,
runtime_hardening_integration_test, approval_checkpoint_resume_test,
execution_state_approval_binding_test, active_rule_profile_freshness_validator_test,
ai_connection_trust_validator_test and result_preview_gate_test;
`python -B -m unittest discover -s ENFORCEMENT -p '*_test.py'`;
`python -m py_compile` on touched Python; `git diff --check`.
Runtime coverage is local integration and durable filesystem tests; mobile is not
applicable. Executor completion requests TAKY_REVIEW, never TAKY_PASS.

## RA-03 owner-to-body comparison

Prior receipt: `ACTIVE_RULE_PROFILE_90ded3b6382bc5fc95ebf40e93fbc459848101610697439af057a17ab624542e.json`.
Its reviewed owner fingerprint is
`sha256:6109116ae1e8f12664ed23d693ba2cdecf555dc5af0aa77291034b43e2379b2e`.
The prior basis was reconstructed in memory, without changing owners: remove only
the final `## Shared-log shortcut` section from AGENTS.md and TAKY.md, preserve one
terminal newline and CRLF encoding, and use all other current owner bytes. The
existing validator's sorted path/NUL/SHA256/newline fingerprint calculation
exactly reproduces that prior fingerprint. RULE_REGISTRY uses the validator's
existing semantic serialization excluding projection_bindings. Thus this is a
cryptographically checked byte comparison, not an inference from the old HEAD.

Current fingerprint:
`sha256:72636514fd682bad39abaabaa1ae956cf821982e2a042b9f4b259722e97ff7b4`.
The only owner deltas are the shared-log shortcut additions (and their file line
ending representation). Both additions require CURRENT-first recovery, only the
unread caller log delta as needed, and no promotion of log content to authority.
Existing profile rules 3, 4, 6 and 7 remain consistent. The delegated bootstrap
now includes the exact shortcut and source/delta boundary. No other body changes
are needed: compensation evidence and exact approval/action identity are already
required by EXECUTION_CHECKPOINT_PROTOCOL section 2.1 and ENFORCEMENT_PROTOCOL's
approval binding, and remain consistent with profile rules 16–18.

Review covers the current owner/body pair under the existing attestation
contract. The new receipt retains the old receipt intact and stores per-owner
current and reconstructed-basis digests for future comparison. This projection
review is not a TAKY lifecycle acceptance of the implementation.
