# TAKY Beta / Alpha / TAKY 2.0 comparison — 2026-10-05

Status: COMPARISON RESULT / NOT CANONICAL / NO MERGE / NO DEPLOY

## 1. Compared baselines

### Frozen Beta candidate
- Base main: `e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2`
- Immutable local snapshot identity: `ed761ad71074001d967d044368f4e07cacefbc457e7b9e5cbb00f8e655a65f57`
- Beta regression: 132/132 PASS
- SAVEY exact-main: 104/104 + typecheck + build PASS
- Adversarial closure: PASS_WITH_CONTAINED_OPEN
- Technical blockers: none
- Purpose: verified evidence/freeze boundary, not the future execution architecture.

### Alpha V1 integrated candidate
- Master: `ALPHA/TAKY_ALPHA_MASTER_V1_INTEGRATED_DRAFT.md`
- Size: 781 lines / 28 sections
- Content validation: PASS
- Coverage-depth validation: PASS
- Local adversarial validation: 7/7 detected
- Final external integration review file is empty; review gate still records that review as pending.
- Purpose: whole-system semantic/operating map consolidated from Frozen Beta and later validated results.

### TAKY 2.0 enforcement branch
- Branch: `taky-2.0-orchestrator-2026-10-05`
- Core: KEY / CONTEXT / ROUTE / COST / DONE
- Regression: 43/43 PASS
- Python compile: PASS
- diff check: PASS
- CLI E2E:
  - LOCAL_ONLY -> exit 3
  - changed task_id same unresolved route -> exit 2
  - same confirmed failure repeat -> exit 2
  - external write without verified account attestation -> exit 2
- Independent Claude adversarial review: CRITICAL 0. One Windows O_BINARY correctness patch identified and fixed.
- Purpose: small executable enforcement kernel.

## 2. Direct comparison

| Axis | Frozen Beta | Alpha V1 | TAKY 2.0 |
|---|---|---|---|
| Main purpose | evidence freeze | whole-system specification | runtime enforcement kernel |
| Breadth | very high | highest | intentionally narrow |
| Runtime hard enforcement | distributed / existing gates | mostly describes/inherits gates | direct 5-gate code |
| User intent authority | preserved in evidence/owners | explicit throughout | machine-enforced Key/provenance |
| Same-failure prevention | evidence/protocol dependent | principle documented | route ledger + normalized fingerprint |
| Task-id retry bypass | not central | documented principle | hard-blocked by trusted execution_scope+route |
| Cost/necessity economy | SAVEY + protocols | integrated policy | action-level trusted call_policy |
| Context reread economy | continuity protocols | explicit DELTA principle | hard gate blocks redundant full reread |
| DONE claim control | claim dimensions distributed | strongly documented | receipt + SUCCESS + plan/action/call-bound evidence |
| Approval replay | distributed | principle-level | approval ref consumption + reapproval supported |
| Runtime tamper/rollback | broad existing stack | inherited | HMAC + external anchor + CAS |
| Account boundary | existing auth stack | semantic distinction | verified attestation required for external writes |
| System/app/engine semantic coverage | evidence-level | strongest | intentionally not duplicated |
| Complexity | high distributed | high document breadth | low core surface |
| Current finalization | freeze-ready candidate | integrated candidate, final review incomplete | enforcement prototype complete, integrations open |

## 3. What each should own

### Beta SHALL remain
Evidence baseline and forensic freeze only:
- exact source heads,
- exact snapshot identity,
- validation proof,
- carry-over OPEN/HOLD,
- historical attack/defense evidence.

Beta SHALL NOT become the live orchestration logic.

### Alpha SHOULD remain
The broad semantic/system map:
- mission and principles,
- owner boundaries,
- Work OS / Learning OS / apps / engines / pipelines,
- lower-owner references,
- product OPEN/HOLD,
- whole-system explanation.

Alpha SHOULD NOT attempt to implement every rule itself.

### TAKY 2.0 SHOULD become the enforcement kernel candidate
Only cross-cutting invariants that must never depend on prose:
- USER Key provenance and action authority,
- context economy,
- retry/route control,
- call economy,
- evidence-backed DONE boundary.

It SHOULD NOT absorb app/domain semantics that already have owners.

## 4. Why this is better than choosing one

Using Alpha alone repeats the historical failure:
`RULE WRITTEN != RULE ENFORCED`.

Using TAKY 2.0 alone creates the opposite failure:
a strong gate system without enough semantic/product context.

Using Beta as live authority creates stale-snapshot risk.

Therefore the low-complexity composition is:

`BETA EVIDENCE FREEZE -> ALPHA SEMANTIC MAP -> TAKY2 ENFORCEMENT KERNEL -> DOMAIN/PROJECT OWNERS -> EXECUTION -> VERIFIED RESULT`

The kernel does not duplicate lower-level rules. It only decides whether an action may proceed, whether a route/call may be used, and whether a DONE claim is valid.

## 5. Current gaps before any promotion

These are integration gaps, not reasons to redesign the kernel:

1. **Authority rebind/migration**
   - authority.json changes currently invalidate runtime digest and fail closed.
   - Need an explicit authorized rebind path, not automatic acceptance.

2. **Account attestation bridge**
   - runtime template intentionally has no account attestation.
   - Connector/executor must provide a verified account assertion before external writes.

3. **Executor wrapper**
   - must obey preflight `CALL_ALLOWED / LOCAL_ONLY / BLOCKED` at actual call time.
   - must bind actual model/call count to the receipt.

4. **Verifier bridge**
   - executor CLI cannot self-assert SUCCESS.
   - independent/runtime verifier must write SUCCESS/evidence/completion bound to receipt plan/action/call.

5. **USER event bridge**
   - explicit USER confirmation must enter as a trusted receipt-bound event.
   - silence never confirms.

These five are the correct next implementation boundary. They should be built as adapters around the kernel, not by expanding the kernel into another large framework.

## 6. Judgment

### Keep
- Beta frozen evidence model.
- Alpha whole-system semantic coverage.
- TAKY 2.0 five hard gates and trust boundary.

### Do not keep
- repeated broad re-audit on every resume,
- prose-only enforcement,
- LATEST/HANDOFF as live authority,
- plan-provided approval/account/evidence claims,
- same-failure retries hidden by new task IDs,
- model calls decided only by caller claims.

### Recommended target architecture
**Alpha = what TAKY means and owns.**
**TAKY 2.0 kernel = what TAKY will permit and accept as done.**
**Beta = why the current state can be trusted.**

This is a candidate judgment only. No canonical promotion, merge, push or deployment is authorized by this comparison.
