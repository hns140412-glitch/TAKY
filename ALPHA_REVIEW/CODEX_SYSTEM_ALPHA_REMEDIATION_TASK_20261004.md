# Codex implementation contract — TAKY SYSTEM-WIDE ALPHA closure (2026-10-04)

ROLE: implementation + deterministic validation. This is the top priority. Work only in:
D:\Git PWA\TAKY_ALPHA_20261003

DO NOT push, merge, deploy, call Netlify, use paid APIs, or change product application code in sibling repos.
DO NOT reopen valid CLOSED items merely because historical files remain.
Conserve usage: no repository-wide rediscovery. Use the named Alpha/Frozen inputs and targeted owner files only.

## Authority resolution already made by TAKY
Canonical authority remains GitHub main, not the local candidate lane.
Current GitHub main MASTER/RULE_REGISTRY.json was read directly and has blob SHA:
b4ca9b367f08be37f358bad339900b5ea005fb56
It contains exactly 21 rules and includes TKY-CHECKPOINT-001.
Therefore:
- Compile Alpha A2a against the canonical 21-rule registry.
- Do NOT replace it with the 25-rule local D:\Git PWA\TAKY registry.
- The local 25-rule registry changes (CONNECTION, SAVEY, WORKSTATION, ARCHIPIPE, AICOLLAB, with CHECKPOINT divergence) are CANDIDATE / POST-FREEZE LOCAL LANE evidence only.
- Frozen Beta snapshot sha256 ed761ad71074001d967d044368f4e07cacefbc457e7b9e5cbb00f8e655a65f57 stays immutable.

## Reconcile the two prior “Alpha” lanes
1. SYSTEM-WIDE Alpha target:
   D:\Git PWA\TAKY_ALPHA_20261003\ALPHA\...
   This is the Alpha that must be completed now.
2. LOCAL infrastructure Alpha lane:
   D:\Git PWA\TAKY\HANDOFF\TAKY_ALPHA_FINAL_2026-10-03.md
   checkpoint sha256:1d556eecafcec340c0a7fd1d9237e529717a9e30478b6cc0bf7b69d60d6542f4
   status COMPLETE only for LOCAL_INFRA scope.
   Import it as a bounded lane. It MUST NOT imply whole-system Alpha COMPLETE.

## Known baseline
- Existing system Alpha is DRAFT / NON-CANONICAL / LOCAL ONLY.
- Frozen Beta regression was 132/132 PASS.
- In this worktree the same 132 suite was re-run after restoring corrupted handoff fixture bytes and is now 132/132 PASS.
- Existing Alpha V0.1 mostly has semantic owner pointers; lower app/engine/pipeline coverage is too shallow.

## Post-freeze working-delta snapshot (evidence only, NOT authority)
Record this as a separate volatile/candidate layer; do not mutate Frozen Beta:
- TAKY: head fee09fa8cdd0b863fc08d4fa6d84d72a182cbc0e, branch character-asset-behavior-separation-2026-09-30, dirty 242, frozen e7ca5c7f94f6721a8f399d8deb49f7f01d73f6a2
- Ready-Set: head 16026f41149dae5faed1c4ca2d1f2933a40ced7a, dirty 6, frozen 0c49a2d607c7c26f3ad6ea4ca6fcee4c5b2ad915
- Hide-Seek: head 5b29db8299237d41f9ce6d054256dda765f9cd09, dirty 5, frozen 5da6594510cc89341054aafef66d5f4ea47a0210
- Snap-Pop: head 94d548545b3c4bd04008d767a27c9cc9e0bcf28c, dirty 5, frozen a77e65b383df170e1124d3b9e01ca37eef334d6c
- TAKY-MOBILE: head 9bcb7d9660834818457704db2c0a5b16c9964c95, main, dirty 2, frozen 6c90045d1bc1f957325b7daef0c6079b29338f1e
- SAVEY: head 939b229e2b55bd4bf92b33bc0884872015b145bc, main, clean, frozen 5a196080b8f8ce50d188b0181d9bec5e5477a265
- TAKY-WORK-OS: head 74f47452d6bfd2d7b68f568c2f9d147040cefd10, branch runtime-hub-unification-2026-09-11, clean, frozen c82a99bd7fbd7ab979907d038e8f948d3792de90
Claim boundary: local head/dirty snapshot != GitHub main/current canonical.

## Required whole-system coverage
A. Apps: Ready & Set, Hide & Seek, Snap & Pop, TAKY-MOBILE
B. Engines: Learning Engine, Planner, Explorer Crew/character runtime, Badge/reward, SAVEY
C. Learning/data pipeline:
capture/source -> mining -> atomize -> index/search -> relate -> learning -> grow -> Planner -> app execution -> result/evidence -> carry-over/current
D. Work OS/ArchiGrow:
source intake -> analysis -> artifact/output -> validation -> learning/growth
E. Design/UI/assets:
approved source -> screen contract -> asset layers/binding -> UI runtime -> visual/regression evidence
F. Shared runtime:
auth/family/private boundaries, sync/offline queue, Drive/Google canonical data, local HTTP/runtime bridges
G. Governance:
C2S, CURRENT/checkpoint, handoff, enforcement, executor lifecycle
H. Claim dimensions remain independent:
DOCUMENTED / CODED / CI_VERIFIED / RUNTIME_VERIFIED / DEVICE_VERIFIED / DEPLOYED / PRODUCTION_VERIFIED

## Implement
Prefer anti-bloat: repair existing V0_1 files in place; do not create V0_2 duplicates just to version work.

1. Update:
- ALPHA/TAKY_ALPHA_MASTER_V0_1.md
- ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json
- ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json
- ALPHA/TAKY_ALPHA_MIGRATION_COVERAGE_V0_1.json
- ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json
- ALPHA/TAKY_ALPHA_VALIDATION_CONTRACT_V0_1.json
- ALPHA/TAKY_ALPHA_SOURCE_TRACE_V0_1.json

2. Add only these missing machine-readable artifacts:
- ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json
- ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json
- ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json
- ALPHA/TAKY_ALPHA_GATE_MAP_V0_1.json
- ALPHA/TAKY_ALPHA_EVIDENCE_GRAPH_V0_1.json
- ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json
- ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json
- ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json

3. Add validators:
- ENFORCEMENT/alpha_coverage_depth_validator.py
- ENFORCEMENT/alpha_pipeline_validator.py
- ENFORCEMENT/alpha_lane_boundary_validator.py
And extend ENFORCEMENT/alpha_readonly_validator_v02.py.
Requirements:
- A–F cannot be called structurally covered by POINTER_ONLY.
- Every app/engine row must have owner/owner-gap, source, implementation/evidence pointer, OPEN refs, and independent claim fields.
- Pipeline stages must be contiguous and owner-bounded.
- LOCAL_INFRA COMPLETE cannot set system-wide COMPLETE.
- Post-freeze delta cannot overwrite frozen/canonical state.
- Ambiguous COVERED_OR_EXPLICITLY_NON_ROUTING is forbidden.
- BADGE/PLANNER/SAVEY must have a real canonical owner reference or explicit OPEN_OWNER_GAP; never use CURRENT/HISTORY as semantic owner.
- TAKY-MOBILE, TAKY-ASSETS, TAKY-WORK-OS must be represented.
- shared sync/auth/private/Drive/HTTP runtime contracts must be represented without overstating runtime proof.

4. Product/runtime gaps remain explicit OPEN/HOLD and DO NOT block Alpha structural completion:
Explorer Crew PR191/Hide/Snap promotion, Badge central and 13 producer-QA OPEN/0 active, Design-to-UI/assets candidates, family profile/radio UX and tap-vs-hold unresolved, Snap legacy browser UNVERIFIED, SAVEY live Google binding/data population if still unverified, shared auth extraction/identity-federation HOLD, hosted interception UNVERIFIED, deployment HOLD, LOCAL lane identity and CAD/Excel/HWP representative tasks.

5. Build-stage mapping:
A0 input lock
A1 authority compile
A2a rule owner compile against canonical 21-rule registry
A2b gate map
A3 routing
A4 pipeline + evidence graph
A5 runtime + app/engine coverage
A6 OPEN closure plan
A7 self-validation + migration coverage
A8 independent cross-validation (do not fake; record pending if not run)
A9 adversarial/regression
A10 human promotion gate (must remain pending)

## Validation
Run focused new validators first.
Then run the existing Alpha read-only validation.
Then run the 132-case Frozen Beta regression suite once, not repeatedly.
Run git diff --check.
Do not run browser/device/deploy validation.

## Completion output
Write:
ALPHA_REVIEW/CODEX_SYSTEM_ALPHA_REMEDIATION_20261004.md
and
ALPHA_REVIEW/ALPHA_SYSTEM_WIDE_STATUS_20261004.json

Report:
- changed/added files
- validator results
- regression count
- remaining OPEN/HOLD
- exact status among:
  SYSTEM_ALPHA_STRUCTURAL_PASS_AWAITING_INDEPENDENT_AUDIT
  SYSTEM_ALPHA_REWORK_REQUIRED
Never claim canonical promotion, deployment, or product gaps closed.