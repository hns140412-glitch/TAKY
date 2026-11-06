# Claude system-wide Alpha remediation — 2026-10-04

Executor: Claude (implementation executor; this report is evidence only, not TAKY_PASS)
Worktree: `D:\Git PWA\TAKY_ALPHA_20261003`
Authority applied: canonical GitHub main `MASTER/RULE_REGISTRY.json` blob `b4ca9b367f08be37f358bad339900b5ea005fb56` (21 rules, includes TKY-CHECKPOINT-001). The local `D:\Git PWA\TAKY` 25-rule registry is treated as POST-FREEZE CANDIDATE lane evidence only.
Frozen Beta (`ed761ad7…5f57`), `ALPHA_INPUT/`, sibling repos and canonical owner files: not touched.
No shell, tests, network, push, merge, deploy or paid API.

## 0. Blocking event: concurrent writer on the same files

While this remediation was in progress, a second executor (the Codex run for `ALPHA_REVIEW/CODEX_SYSTEM_ALPHA_REMEDIATION_TASK_20261004.md`) wrote the same `ALPHA/*_V0_1.json` files. The harness reported on-disk changes after my writes to 11 Alpha files. `ALPHA_REVIEW/CODEX_SYSTEM_ALPHA_REMEDIATION_20261004.md`, `ALPHA_SYSTEM_WIDE_STATUS_20261004.json` and `ALPHA_SYSTEM_CLOSURE_APPLY_20261004.json` now exist.

I stopped writing shared files as soon as this was detected. Per AGENTS.md ("stop the conflicting change and report the conflict"), I did not revert or overwrite the other executor's output. I did not review its content; I only read header `schema`/`status` lines to report which version each file holds.

### Observed file state after the collision (header markers only)

| File | Version on disk | Basis |
|---|---|---|
| `ALPHA/TAKY_ALPHA_ROUTING_GRAPH_V0_1.json` | Claude | `schema_revision: 2026-10-04.system-wide-remediation`, `status: DRAFT_STRUCTURE_PENDING_DETERMINISTIC_VALIDATION` |
| `ALPHA/TAKY_ALPHA_AUTHORITY_MAP_V0_1.json` | Claude edits present | `revised: 2026-10-04.system-wide-remediation`, `engine_owner_status` rows |
| `ALPHA/TAKY_ALPHA_MIGRATION_COVERAGE_V0_1.json` | **Partial Claude edit** | status relabels + header applied; the dimension A–I / post-freeze rows edit **failed** (the anchor text had changed on disk) |
| `ALPHA/TAKY_ALPHA_CARRYOVER_OPEN_V0_1.json` | Unknown / mixed | changed on disk after my edits; header unchanged |
| `ALPHA/TAKY_ALPHA_PIPELINE_MAP_V0_1.json` | Other executor | `status: STRUCTURAL_MAP` (mine was `DRAFT_STRUCTURE_PENDING_DETERMINISTIC_VALIDATION`) |
| `ALPHA/TAKY_ALPHA_APP_ENGINE_COVERAGE_V0_1.json` | Other executor | `status: STRUCTURAL_COVERAGE` |
| `ALPHA/TAKY_ALPHA_GATE_MAP_V0_1.json` | Other executor | `status: A2B_EXPLICIT_MAP` |
| `ALPHA/TAKY_ALPHA_EVIDENCE_GRAPH_V0_1.json` | Other executor | `status: A4_STRUCTURAL_GRAPH` |
| `ALPHA/TAKY_ALPHA_OPEN_CLOSURE_PLAN_V0_1.json` | Other executor | `status: A6_CLASSIFIED` |
| `ALPHA/TAKY_ALPHA_LANE_IMPORT_LOCAL_INFRA_V0_1.json` | Other executor | `status: BOUNDED_LANE_IMPORTED` |
| `ALPHA/TAKY_ALPHA_POST_FREEZE_DELTA_V0_1.json` | Other executor | `status: VOLATILE_CANDIDATE_SNAPSHOT` |
| `ALPHA/TAKY_ALPHA_RUNTIME_CONTRACTS_V0_1.json` | Unknown | changed on disk; header not inspected |
| `ALPHA/TAKY_ALPHA_MASTER_V0_1.md`, `…VALIDATION_CONTRACT…`, `…SOURCE_TRACE…` | Not edited by Claude | work stopped before these |
| `ENFORCEMENT/alpha_coverage_depth_validator.py`, `alpha_pipeline_validator.py`, `alpha_lane_boundary_validator.py` | **Absent** | no such files exist in the worktree |
| `ENFORCEMENT/alpha_readonly_validator_v02.py` | Not edited by Claude | |

Consequence: the worktree holds files from two authors with different schemas and vocabularies. For example, my routing graph and authority map reference artifacts and keys such as `engine_owner_status`, carryover class IDs like `BADGE_OWNER_GAP`, and `#repos.<name>` paths in the post-freeze delta. The other executor's files may not provide these: its post-freeze delta uses a `repos` array, not an object keyed by repo name. Cross-artifact consistency is unverified and likely broken.

## 1. What Claude implemented (before the collision)

- **Routing graph:**
  - Added nodes: `TAKY_MOBILE`, `TAKY_ASSETS_REPO`, `TAKY_WORK_OS_REPO`, `WORK_DOMAIN_PROJECT`, `SYNC_CONTRACT`, `OFFLINE_QUEUE`, `AUTH_SESSION` (HOLD), `FAMILY_PRIVATE_BOUNDARY`, `DRIVE_GOOGLE_CANONICAL`, `LOCAL_HTTP_BRIDGE`, `CHARACTER_ASSET_PIPELINE`, `CHARACTER_BEHAVIOR_RUNTIME`, `LOCAL_INFRA_ALPHA_LANE`.
  - Owner status:
    - PLANNER: owner set to `OS/GUIDE_FAMILY_LEARNING_OS.md` ("MAIN / PLANNER = whole-life allocation + dated placement"), with `semantic_authority: LEARNING_OS` kept.
    - BADGE and SAVEY: changed to explicit `OPEN_OWNER_GAP`.
    - BADGE's CURRENT/BADGE paths were demoted to `evidence_refs`.
  - Added edges: app evidence → Learning Engine for Ready & Set and Snap & Pop; sync, auth, family, Drive and HTTP edges; TAKY-MOBILE launch-only edges; badge reward-use edges; executor → enforcement; C2S → Learning Engine; and the lane import.
  - Added 7 invariants, including `CURRENT_OR_HISTORY_PATH_IS_NEVER_A_NODE_OWNER` and `LOCAL_INFRA_LANE_COMPLETE_DOES_NOT_IMPLY_SYSTEM_ALPHA_COMPLETE`.
  - Renamed the schema label from `V0_3` to `V0_1` to fix the label drift. The `semantic_owners` set was left unchanged so V1 stays equal to `MASTER_FILE_REGISTRY`.
- **Authority map:**
  - `canonical_rule_registry` block (GitHub main blob, 21 rules; the 25-rule candidate cannot replace canonical).
  - Additional `shared_contracts` entries.
  - `engine_owner_status`, `lanes` and `post_freeze_delta` blocks.
  - 5 new authority rules.
- **Migration coverage:**
  - `COVERED_OR_EXPLICITLY_NON_ROUTING` replaced with `ROUTED`, plus a `layer_node_alias` map.
  - Owner pointer rows relabelled `OWNER_POINTER_COVERED__NOT_DIMENSION_COVERAGE`.
  - Rule rows set to `COVERED_A2A__A2B_MAPPED`.
  - `status_vocabulary` and `forbidden_statuses` added.
  - **Missing:** the per-dimension rows and post-freeze candidate-rule rows were not applied.
- **Carryover:** added classes `SHARED_AUTH_EXTRACTION_HOLD`, `WORK_LEARNING_IDENTITY_FEDERATION_HOLD`, `BADGE_OWNER_GAP`, `SAVEY_OWNER_GAP`, `PLANNER_DEDICATED_OWNER_DOCUMENT_GAP`, `RULE_REGISTRY_COVERAGE_GAPS`, `POST_FREEZE_CANDIDATE_RULES`, `LOCAL_LANE_HOST_AUTHENTICATED_IDENTITY` and `LOCAL_LANE_REPRESENTATIVE_TASKS`. Merged the lane's hosted-interception item into the existing `HOSTED_RUNTIME_INTERCEPTION` entry. `exact_carry_over_open` and `exact_contained_open` were not altered. Whether these edits survived the collision is unknown.
- **New artifacts** (all since replaced on disk by the other executor except where noted above): pipeline map (C, D, E, Badge and G pipelines, owner-bounded, with 7 claim fields per stage), app/engine coverage, runtime contracts, gate map, lane import, post-freeze delta, OPEN closure plan, evidence graph.

## 2. Findings that apply regardless of which version is kept

1. **P1 — latent defect in the read-only validator (V2).** `ENFORCEMENT/alpha_readonly_validator_v02.py` compares `('rule_id','owner','scope')` between `MASTER/RULE_REGISTRY.json` and `ALPHA/TAKY_ALPHA_RULE_COMPILE_V0_1.json`. The compile file deliberately omits `scope` (reference-only, per `alpha_audit_fixes_v03.py`), and the registry has `scope` on every rule. A fresh run should therefore fail with `V2_RULE_ENTRY_MISMATCH` for all 21 rules. The stored PASS in `ALPHA_REVIEW/ALPHA_READONLY_VALIDATION_20261003.json` predates that compile change. **Fix:** compare `rule_id` and `owner` only, and fail if a compiled row carries `scope` (semantic copy).
2. **P1 — registry equivalence is unproven.** The worktree `MASTER/RULE_REGISTRY.json` has the same 21 rule IDs as the canonical set, but nobody has checked that it is byte-equal to GitHub main blob `b4ca9b36…`. A validator should compute `sha1(b"blob %d\0" % len(bytes) + bytes)` over the worktree file and compare it to the canonical blob.
3. **P1 — Planner and Ready & Set wording conflict.** `MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json` gives the READY_SET layer ownership of "Planner/TODAY execution projection", while LEARNING_OS owns allocation semantics. Alpha should treat Ready & Set as owning the projection surface only, never Planner authority.
4. **Correction to my audit.** The "shared sync conflict contract v1" from commit e7ca5c7 is `TAKY_SYNC_CONTRACT_V1.md` itself, not a separate unreferenced file. My audit's P1-5 claim that it was "not referenced anywhere" was wrong; no separate node is needed.
5. **P2 — the gate map must not overcount.** Only 9 of the 21 canonical rules have an owner-declared or rule-ID-referenced executable gate. CONTINUITY, DRIVEC2S and CHECKPOINT match a script only by filename, and 9 rules have no gate. Count filename-only matches as unverified, never as enforced.
6. **P2 — the PR #209 CI evidence is narrow.** It proves the enforcement replay ran at historical head `4e13ae33`. It is not per-stage `CI_VERIFIED` evidence for the C2S, task-contract or checkpoint stages, nor for any app or engine.
7. **P2 — the TAKY-MOBILE deploy claim is stale.** The mobile registry records Netlify `deployed_commit 7ad757ef` as `DEPLOYED_STALE`. That supports only a STALE deploy claim and must not be read as DEPLOYED.

## 3. Product and runtime gaps that stay OPEN/HOLD

All of the following stay OPEN or HOLD:
- Explorer Crew PR #191, plus Hide v2 (PR #28) and Snap v2 (PR #18).
- Badge central PR #196 and app PRs 143/29/20; 13 producer-QA OPEN, 0 active; hosted e2e OPEN.
- Design-to-UI PR #194, and TAKY-ASSETS PR #4 (HOLD, no merge).
- Family profile/radio UX, including the unresolved tap-vs-hold-to-talk gesture.
- Snap legacy browser closure: UNVERIFIED.
- SAVEY live Google binding and data population. Also, SAVEY local main `939b229e` differs from the validated `5a196080`.
- Shared auth extraction and Work↔Learning identity federation: HOLD.
- Hosted interception: UNVERIFIED_CONTAINED.
- Deployment: HOLD.
- LOCAL lane: host-authenticated identity and CAD/Excel/HWP representative tasks.
- Owner gaps: Badge and SAVEY (these block canonical promotion), and the dedicated Planner owner document.

The LOCAL_INFRA lane is COMPLETE for its own scope only; that never makes system-wide Alpha COMPLETE.

## 4. Gates

| Gate | State |
|---|---|
| A0 input lock | unchanged; not re-run |
| A1–A7 | structure partially written by two executors; **inconsistent**; not validated |
| Deterministic validators (new) | **not present in worktree** |
| A8 independent cross-validation | PENDING |
| A9 regression/adversarial | PENDING (no tests run by Claude, per instruction) |
| A10 human promotion | PENDING |

The progress-tracking tool (`work_state_write`) was denied: this session had no way to answer its approval prompt. The task did not depend on it.

## 5. Required next action (for TAKY)

1. Choose a **single writer** for `ALPHA/` and `ENFORCEMENT/alpha_*`. Do not run Claude and Codex remediation against the same worktree at the same time.
2. Take one coherent artifact set as the base. Either:
   - keep the Codex set and apply the four Claude-unique items from §2 (findings 1–3, 5) plus the owner-status and lane rules from §1, or
   - restore the Claude set and finish it.

   Then reconcile the routing graph and authority map against whichever pipeline, coverage and lane schemas are kept.
3. Add or verify the three validators and the V2 fix, then run deterministic validation once, on a quiescent tree.
4. Only after that move to A8 independent audit. A10 human promotion stays pending.

REWORK_REQUIRED
