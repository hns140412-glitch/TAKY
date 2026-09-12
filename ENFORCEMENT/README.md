# TAKY Enforcement Harness

This directory contains deterministic checks for mechanically testable TAKY governance failures.

## Run

```bash
python ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_cases.json
```

The harness is intentionally stdlib-only. A successful replay means the repository gate correctly distinguishes the encoded historical-failure and post-fix cases. It does **not** prove live LLM behavior, live GitHub state outside the checked commit, external service behavior, or human approval.

Normative definitions live in `MASTER/FAILURE_TAXONOMY.md`; enforcement semantics live in `MASTER/ENFORCEMENT_PROTOCOL.md`.
