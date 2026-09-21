# 2026-09-21 Architecture Profile Auto-Activation Validation

Status: VALIDATION RECORD
Scope: Close the remaining activation gap between material architecture intent and the architecture-specific TAKY execution profile.

## Trigger

After adding architecture owner/sharing boundary enforcement, one gap remained: a caller could theoretically omit `engineering_execution_profile_required=true` and therefore bypass the architecture-specific contract even though the action was plainly an architecture/shared-core/OS-boundary change.

## Correction

`ENFORCEMENT/taky_gate.py` now treats any of these declared material intents as architecture work:
- `architecture_change_planned`
- `shared_core_change_planned`
- `os_boundary_change_planned`
- `cross_domain_architecture_change_planned`
- `ownership_move_planned`

For such records the gate requires:
- `engineering_execution_profile_required=true`
- `engineering_profile=ARCHITECTURE_CHANGE`

The runtime orchestrator now exposes these activation flags and selected engineering profile in its runtime trace.

## Replay

Historical failure:
- material shared-core architecture intent declared;
- architecture profile omitted.
Expected: `RULE_NOT_APPLIED`.

Compliant case:
- same material intent;
- ARCHITECTURE_CHANGE profile selected;
- owner map, sharing classification, semantic/authority checks and counterexample supplied.
Expected: clean PASS.

## Claim boundary

This proves repository-controlled activation/replay only. Hosted ChatGPT native turns are still not proven to invoke this repository gate automatically.

END
