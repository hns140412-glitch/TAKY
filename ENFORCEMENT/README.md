# TAKY Enforcement Harness

This directory contains deterministic checks for mechanically testable TAKY governance failures.

## Run

```bash
python ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_cases.json
```

The harness is intentionally stdlib-only. A successful replay means the repository gate correctly distinguishes the encoded historical-failure and post-fix cases. It does **not** prove live LLM behavior, live GitHub state outside the checked commit, external service behavior, or human approval.

Normative definitions live in `MASTER/FAILURE_TAXONOMY.md`; enforcement semantics live in `MASTER/ENFORCEMENT_PROTOCOL.md`.

## Conversation-to-System coverage

Validate a compiled conversation coverage ledger:

```bash
python ENFORCEMENT/conversation_coverage_validator.py ENFORCEMENT/fixtures/conversation_coverage_pass.json
```

The failure fixture is expected to be rejected. This gate proves structural coverage claims within the declared recovered scope only; it does not prove live LLM automatic invocation or semantic correctness of inaccessible material.
