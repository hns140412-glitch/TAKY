# TAKY 2.0 — Minimal Enforcement Branch

Branch: `taky-2.0-orchestrator-2026-10-05`

This branch is intentionally separate from existing Alpha/Beta work.

## Slogans

- **Think Again, Keep Your Key!** — 핵심을 놓치지 말고 생각해라.
- **Think Again, You’re The Key!** — 너는 이미 답을 가지고 있으니 방법을 찾고 결과를 가져와라.

Key owner / final authority = USER.
Execution / solution duty = AI.
USER != DEBUGGER.

## 5 hard gates

1. **KEY** — trusted USER intent + registered action + verified account attestation.
2. **CONTEXT** — premise/snapshot once, then DELTA; repeated full reread blocked.
3. **ROUTE** — same confirmed failure blocked; transient retries capped; distinct routes capped at 3 per trusted execution scope.
4. **COST** — call necessity/mode/model/effort/count come from the trusted action policy. Plan claims cannot upgrade them.
5. **DONE** — SUCCESS + receipt-bound plan/action/call + verified evidence/completion. Silence is not confirmation.

## Trust boundary

- `state/authority.json`: USER authority, trusted action registry and call policy. Runner never mutates it.
- `state/runtime.example.json`: portable initial runtime template.
- `state/runtime.json`: local mutable runtime state; git-ignored.
- Runtime is HMAC-protected with a key outside the repo.
- An external signed anchor pins the latest runtime version/MAC; old signed runtime rollback is rejected.
- Deleting runtime does not permit reinitialization while the external anchor exists.
- Runtime writes use lock + CAS version + fsync + atomic replace.
- External writes require a verified account attestation; the template starts with none.
- Plans cannot define their own Key, action, account, approval, ledger, evidence, or completion authority.

## Route enforcement

- Active attempt ownership is keyed by **trusted execution_scope + normalized route**, not by plan `task_id`.
- Changing `task_id` cannot bypass an unresolved attempt.
- Route fingerprints normalize target/tool strings.
- Route ledgers are scoped per trusted action execution scope, so unrelated tasks do not consume each other's route budget.
- Failure reporting updates the stored attempt chosen at preflight; callers cannot replace the route when reporting failure.

## Cost enforcement

Each trusted action declares a `call_policy`:

- `LOCAL_ONLY` → external AI/CLI call is forbidden for that task path.
- `EXTERNAL_REQUIRED` → only trusted models/effort/call count are allowed.
- `EXTERNAL_OPTIONAL` → requires explicit trusted approval.

Preflight returns:

- `mode=CALL_ALLOWED`, exit `0`: external call allowed.
- `mode=LOCAL_ONLY`, exit `3`: task may continue, but the external call must be skipped.
- blocked, exit `2`.

Receipt stores the exact `call_digest` as well as plan/action digests.

## Approval enforcement

Approvals are consumed by **approval key + USER approval reference**. Reusing the same approval reference is blocked; a new USER approval reference can authorize the same action again.

## CLI

Initialize local runtime once:

```powershell
python -m TAKY2.orchestrator init-state
```

Run:

```powershell
python -m TAKY2.orchestrator preflight <plan.json>
python -m TAKY2.orchestrator record-failure <receipt_id> <FAILURE_CLASS>
python -m TAKY2.orchestrator done <report.json>
```

The executor-facing CLI intentionally has **no generic SUCCESS command** and no command that can self-create USER confirmation, independent-verifier evidence, or completion attestations.

## Completion boundary

DONE requires:

- valid unconsumed receipt,
- SUCCESS recorded through the verifier integration boundary,
- completion attestation matching receipt plan/action/call,
- verified evidence matching the same receipt plan/action/call,
- Key match and required verification pass,
- explicit USER confirmation event bound to that receipt for `USER_CONFIRMED`.

## Tests

```powershell
python -m unittest discover -s TAKY2 -p "test_*.py" -v
```

Python standard library only.
