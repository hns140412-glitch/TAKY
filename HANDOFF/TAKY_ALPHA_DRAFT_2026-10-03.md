# TAKY Alpha Draft — 2026-10-03
Status: ALPHA DRAFT / LOCAL ONLY / NO PUSH-MERGE-DEPLOY
Authority: current user instruction + canonical owners; this file is a synthesis draft, not a new competing semantic owner.

## Alpha objective
TAKY Alpha consolidates the existing governance into a lighter execution architecture:
HUMAN INTENT -> THINK AGAIN -> KEEP YOUR KEY -> EXECUTE -> VERIFY -> CORRECT/CONTINUE.

Core operating requirements:
- USER != DEBUGGER.
- OWNER -> EXECUTION POLICY -> REAL CONTROL -> RESULT EVIDENCE must stay connected.
- RULE WRITTEN != RULE ENFORCED.
- CURRENT is a verified resume pointer, not a second authority store.
- External knowledge may challenge CURRENT only through governed correction/promotion.
- Paid API, push, merge and deploy remain explicit human gates.

## Keep
- single semantic owner and authority boundaries;
- C2S compile / reflection / implementation / runtime state separation;
- traceability and provenance;
- deep memory, light execution;
- recovery from last verified stage;
- proportional validation;
- source preservation and reversible local work;
- Claude primary builder + independent reviewer only for material deltas.

## Corrected in this Alpha pass
- G:\ is treated as an external HDD, never inferred as Google Drive.
- F:\ is the designated Google Drive for desktop mount and is added only when actually mounted.
- Claude allowed roots are D:\Git PWA, G:\, Desktop\드라이브, plus F:\ only when present.
- NotebookLM is LEGACY_OPTIONAL / default OFF under TKY-NBLM-001.
- AI connection, SAVEY, workstation and ArchiGrow pipeline now have explicit Rule IDs and registry bindings.

## Enforcement delta already implemented
- Claude PreToolUse now covers Read/Grep as well as shell/edit/MCP actions.
- protected authority paths are normalized so relative-path edits cannot bypass the gate.
- direct edits of TAKY.md, MASTER/, .claude settings/hooks, AGENTS.md, CLAUDE.md and .mcp.json require approval.
- credential/secret reads are approval-gated.
- shell writes to protected authority surfaces are approval-gated.
- Scenario generation/workflow/write/delete actions are explicit SAVEY approval gates.
- NotebookLM projection and Claude execution contract were aligned to default OFF.

## Strong-pipeline generalization
For material multi-stage work, checkpoint receipts may carry:
INPUT refs/hashes / OUTPUT refs/hashes / CONTRACT VERSION / CHECKS / FAILURE CLASS /
NEXT ROUTE / ROLLBACK / APPROVAL SCOPE.

This extends the existing checkpoint owner instead of creating another global pipeline owner.

## Verified locally
- rule_registry_lint: PASS, 24 registered rules.
- master_file_registry_validator: PASS.
- master_surface_integrity_validator: PASS.
- system_layer_ownership_validator: PASS.
- Claude hook Python compile: PASS.
- checkpoint schema JSON parse: PASS.
- Claude settings JSON parse: PASS.
- hook replay: relative TAKY.md edit -> ASK.
- hook replay: ordinary HANDOFF edit -> silent/allowed.
- hook replay: protected credential read -> ASK.
- hook replay: PowerShell write to TAKY.md -> ASK.
- hook replay: Scenario model run -> ASK.

## Remaining Alpha OPEN
P0:
- connect trusted approval policy/state evidence to actual high-impact execution interception; current record validators and Claude hook remain separate layers.
- verify/record Scenario connection metadata or disable it if unnecessary.

P1:
- narrow broad Playwright allow-list and pin MCP package versions after local version verification.
- remove semantic duplication around CASE/STRATEGY/FRONTIER/CURRENT_BEST by keeping one owner and references elsewhere.
- align Workstation Control so project facts and legal/design authority remain domain/project-owned; workstation owns execution/storage/verification mechanics.
- extend CI/path-trigger coverage for new security/hook/pipeline owners and add regression fixtures.
- generalize executor lifecycle naming so Claude/Codex are executor identities, not hard-coded state semantics.

P2:
- separate installed capability from verified representative task capability in workstation registry.
- trim duplicate adapter prose in CLAUDE.md after owner references are stable.
- archive or ignore local backup/log artifacts only after non-destructive retention rules are confirmed.

## Alpha transition rule
Do not call Alpha COMPLETE until P0 execution-interception linkage is verified with local replay/runtime evidence.
Do not require push/merge/deploy for Alpha local completion.

## P0 closure update
- execution_state_engine no longer trusts caller-controlled merge_approval_required / production_approval_required flags to disable human gates.
- trusted policy now requires approval for every MERGED or DEPLOYED transition.
- synthetic fixture with merge_approval_required=false and no approval evidence returned HUMAN_APPROVAL_MISSING:merge as expected.
- Remaining Alpha work is P1 consolidation and broader runtime/CI coverage; no push/merge/deploy/API action was performed.

## P1/P2 consolidation update
Resolved:
- Playwright MCP pinned to 0.0.83; Chrome DevTools MCP pinned to 1.10.1.
- blanket Claude allow entries for playwright/chrome-devtools removed.
- AI connection security classification split into independent trust/action/sensitivity/cost/approval axes.
- machine-readable OS/AI_CONNECTION_AUDIT.json added; Scenario remains enabled but metered/credit actions are approval-gated and account/cost details remain unverified.
- CI path triggers now cover CLAUDE.md, .mcp.json, Claude hooks/settings, AI connection/security/audit, SAVEY, Workstation, ArchiGrow playbook/pipeline and checkpoint owners.
- ENFORCEMENT/claude_hook_regression.py added to CI; current local result 20/20 PASS.
- shell-write bypasses reproduced by independent audit (WriteAllText and Bash redirection into protected authority surfaces) are now gated and regression-covered.
- executor-neutral aliases ASSIGNED_TO_EXECUTOR / EXECUTOR_DONE are accepted while legacy CODEX-named states remain compatibility internals.
- caller-controlled merge_approval_required / production_approval_required can no longer disable human gates.
- approval evidence now declares BOUND_RECORD_ONLY and identity_authenticated=false; repository binding is not misrepresented as authenticated user identity.
- Workstation project-fact, SVG and HWP delivery roles were narrowed so domain/project sources retain semantic/legal authority.
- workstation capability evidence now distinguishes INSTALLED / LAUNCH / REPRESENTATIVE_TASK / PIPELINE verified.
- architecture learning-state semantics deduplicated back to DOMAIN/ARCHITECTURE_WORK_OS.md §7.

Validation:
- claude_hook_regression 20/20 PASS.
- execution_state_approval_binding_test 8/8 PASS.
- approval_checkpoint_resume_test 8/8 PASS.
- rule_registry_lint PASS (24 rules).
- master_file_registry_validator PASS.
- master_surface_integrity_validator PASS.
- system_layer_ownership_validator PASS.
- JSON parse checks PASS.
- git diff --check PASS.
- MCP config contains no @latest and Claude settings contain no blanket playwright/chrome-devtools allow.
- YAML parser unavailable locally (PyYAML absent); no package was installed solely for this check.

Remaining boundaries:
- authenticated proof of human identity is a host/provider capability boundary; repository records only bind evidence to exact context.
- shell hooks are defense-in-depth and cannot replace OS/sandbox permissions for arbitrary interpreter behavior.
- hosted ChatGPT/Claude automatic invocation remains UNVERIFIED.
- no push/merge/deploy/paid API was performed.
