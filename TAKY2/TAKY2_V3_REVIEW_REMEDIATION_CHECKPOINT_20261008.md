# TAKY2 V3 REVIEW REMEDIATION CHECKPOINT — 2026-10-08

Status: HOLD — runtime remediation in progress; latest edits not yet regression-verified.

## Last verified baseline
- Full TAKY2 regression: 186 passed + 54 subtests.
- Authority digest: dc263139896484f034a7.
- Runtime: v58.
- KEY_AMEND=false.
- review:external-model authority is Sonnet-only, PACKET_ONLY, SUBSCRIPTION_QUOTA via model_billing.
- PACKET_ONLY hardening already present: pinned claude.exe, exact argv template, packet digest, bridge-owned temp cwd, minimal environment, tempfile stdin, strict MCP, empty tools/prompts/settings sources/settings, no session persistence, model/effort binding.
- External billing is explicit; capability/model binding and capability-required skip evidence are enforced.

## Claude independent review evidence
First remediation review returned HOLD.
Material findings included:
1. duplicate-call / persisted pre-run claim gap;
2. environment/config isolation gap;
3. exact argv / duplicate-flag hardening;
4. external model/effort binding;
5. single-call consistency.

Current code has already addressed items 2–5 and most of item 1 in bridge-local execution:
- duplicate receipt check occurs before runner;
- runner exceptions consume the receipt in returned runtime;
- execution call state moves CALLING -> RETURNED/FAILED;
- active attempt state is now synchronized CALLING -> RETURNED/FAILED;
- preclaimed execution path support was added in bridges.py;
- stale PENDING route ownership can be ignored only when a matching execution_call has settled RETURNED/FAILED evidence.

## Remaining OPEN / blocker
Production orchestrator CLI has NOT yet been connected to:
claim_execution_receipt -> signed save_runtime -> execute_with_receipt(preclaimed=True) -> signed final save / reconcile.
Therefore crash/concurrent-process atomicity before the runner is not yet proven closed.

Four prior Claude review attempts remain as historical active_attempt records with PENDING status, while matching execution_calls contain returned results. Do not delete history. The new preflight evidence check treats a PENDING owner as stale only when the matching execution_call is settled.

## Tooling interruption
After the latest bridge/preflight edits, Remote Desktop Commander platform safety checks began blocking:
- pytest execution wrapper,
- packet generation wrapper,
- official record-failure CLI.
These blocks were not bypassed.

Therefore:
- 186 passed + 54 subtests is the LAST VERIFIED regression baseline BEFORE the newest preclaimed/active-status/stale-route edits.
- The newest edits are READBACK-CONFIRMED but NOT regression-verified.
- Second Claude review after these newest edits was NOT executed.
- V3 remains NOT PROMOTED.

## Next exact sequence
1. Restore allowed local execution path without bypassing platform safety.
2. Run full TAKY2 regression + compileall + git diff --check.
3. Connect production CLI persisted claim path and add regression for process/concurrency one-call semantics.
4. Re-run full regression.
5. Generate fresh compact review packet.
6. One hardened Claude PACKET_ONLY second review.
7. Receipt-bound Codex verifier review.
8. If no material findings, decide V3 promotion.
