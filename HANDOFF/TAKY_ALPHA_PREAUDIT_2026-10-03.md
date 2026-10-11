# TAKY Alpha Pre-Audit
Date: 2026-10-03
Status: EVIDENCE / CANDIDATE — not authority. CURRENT owners win on conflict.
Prompt source: `.claude/CLAUDE_TAKY_ALPHA_PROMPT.txt`

## Scope read
TAKY.md, AGENTS.md, PROJECTIONS/ACTIVE_RULE_PROFILE.md, CLAUDE.md, OS/{AI_CONNECTION_SECURITY,SAVEY_AI_ECONOMY,WORKSTATION_CONTROL,WORKSTATION_CAPABILITY_REGISTRY}.md, DOMAIN/*.md, MASTER/ENFORCEMENT_PROTOCOL.md (headings + §4.4–§5.1, §8–§10), MASTER/RULE_REGISTRY.json (head), .claude/settings.json, .claude/hooks/taky_hook.py, .mcp.json.
Not run (BLOCKED, approval pending): `ENFORCEMENT/{rule_registry_lint,master_file_registry_validator,system_layer_ownership_validator,taky_gate --replay}`. Findings below are static only.

## Disposition table
| ID | Item | Disposition | Evidence / action |
|---|---|---|---|
| A1 | New owners (AI_CONNECTION_SECURITY, SAVEY_AI_ECONOMY, WORKSTATION_CONTROL, ARCHIGROW_PIPELINE_PROTOCOL) absent from `RULE_REGISTRY.json` / `MASTER_FILE_REGISTRY.json` / `SYSTEM_LAYER_OWNERSHIP_MAP.json`; referenced only by TAKY.md, CLAUDE.md, 2 skills | IMPLEMENT | RULE WRITTEN != ENFORCED. Add rule IDs (e.g. TKY-CONNECTION-001, TKY-SAVEY-001, TKY-WORKSTATION-001, TKY-PIPELINE-001) then run `rule_registry_lint.py`. MASTER/ edit needs user approval (hook gate). |
| A2 | Status wording `ACTIVE` on unregistered files vs REV_00 governance | IMPLEMENT | Until A1 lands, treat as `ACTIVE_UNREGISTERED`. |
| A3 | Architecture domain owner had no pointer to Playbook / Pipeline / Workstation docs (Claude-only discoverability via CLAUDE.md) | DONE | `DOMAIN/ARCHITECTURE_WORK_OS.md` §8 pointer added. |
| A4 | `CURRENT_BEST` auto-promotion by "repeated success" (GROWTH_MAP §8) conflicts with WORK_OS §7 "presently approved standard" | DONE | GROWTH_MAP line corrected to "candidate; approval per WORK_OS §7". |
| A5 | CASE/STRATEGY/FRONTIER/CURRENT_BEST vocabulary restated in WORK_OS §7, GROWTH_MAP §8, PLAYBOOK §2, PIPELINE §7, WORKSTATION §6 | MERGE | Owner = WORK_OS §7. Others should reference, not redefine (next small delta; not rewritten now). |
| A6 | SAVEY call-budget text overlaps ENFORCEMENT §4.5 (external call budget) and §5 (approval gate) | MERGE | SAVEY should cite §4.5/§5 as enforcement owner; keep only routing preference. |
| A7 | AI_CONNECTION §3 knowledge flow (EVIDENCE->INDEX->LEARNING->CURRENT) vs ENFORCEMENT §5.1 (REFERENCE_ONLY->CANDIDATE->...->CANONICAL_WRITE) = two promotion chains | MERGE | Make §5.1 the gate owner; §3 = discovery-side routing that terminates at CANDIDATE. |
| A8 | CLAUDE.md restates TAKY authority order, knowledge flow, Reality Locked, CAD->SVG route | KEEP (adapter) / trim later | Valid as Claude adapter; must not diverge. CLAUDE.md boot order skips MASTER_LOGIC (TAKY.md step 2). CLAUDE.md names RAW/INDEX/DETAIL dirs; only HISTORY/HANDOFF/CURRENT/LEARNING exist at repo root -> MISSING_NAMESPACE (verify or relabel). |
| A9 | ArchiGrow pipeline principles worth generalizing TAKY-wide | IMPLEMENT (map, not new owner) | (1) PIPELINE CONNECTED != RELIABLE; (2) stage receipt INPUT_REF+HASH/TOOL/OUTPUT_REF+HASH/STATUS/FAILURE_CLASS/NEXT_ROUTE -> extend `EXECUTION_CHECKPOINT_PROTOCOL` (currently only optional parent hash); (3) restart from last verified stage; (4) deterministic before subjective check; (5) derivative-limitation retains canonical upstream; (6) verify at actual delivery surface. Owners exist: EXECUTION_CHECKPOINT / TRACEABILITY / VALIDATION_RULES — do not add a parallel owner. |
| S1 | Hook gate is keyword-heuristic. `mcp__scenario__model_run` / `workflow_run` (credit-consuming, T4) are not gated | IMPLEMENT | Add cost terms for scenario to hook ask list. |
| S2 | `scenario` MCP enabled in `.mcp.json` but absent from setup handoff "verified MCP" list and has no AI_CONNECTION §6 audit record | HOLD | Record CONNECTION/PURPOSE/TRUST_CLASS/SCOPE/AUTH/COST/GATE/OWNER/LAST_VERIFY or disable. |
| S3 | Hook protects Edit/Write paths only; Bash/PowerShell/Read of `.env`/credentials and edits to `.claude/hooks/` , `AGENTS.md`, `CLAUDE.md` are ungated (hook can be self-modified) | IMPLEMENT | Add `/.claude/hooks/`, `/agents.md`, `/claude.md` to ask paths; add secret-file read patterns. Hook edits need a runnable test (hook crash = fail-open). |
| S4 | `npx -y ...@latest` for playwright / chrome-devtools MCP: unpinned supply chain | HOLD | Pin versions after verifying current ones. Classed T0 in practice but is remote code. |
| S5 | `mcp__playwright` allow-listed wholesale incl. arbitrary-code tools (`browser_run_code_unsafe`, `browser_evaluate`) and untrusted page content | HOLD | Narrow allow list or gate unsafe tools; page content is DATA per AI_CONNECTION §1. |
| S6 | Hook command path hard-coded `D:/Git PWA/TAKY`; python failure silently disables gating | HOLD | Note only; portability/fail-open risk. |
| R1 | Untracked backups: `CLAUDE.md.*.bak` x2, `TOOLS/*.bak*` x several | REMOVE (deferred) | Non-destructive: do not delete without approval; add ignore or move to archive. |
| R2 | `.claude/TAKY_ALPHA_CLAUDE_AUDIT.log` is 0 bytes; `TAKY_ALPHA_CODEX_AUDIT.log` is an ad-hoc `codex exec -a` CLI error | KEEP as evidence | Governed path `TOOLS/TAKY_MODEL_REVIEW.ps1` uses `codex exec --sandbox read-only` (correct); ad-hoc call was the fault. |
| C1 | CAD/Excel/HWP/PC: WORKSTATION_CONTROL classes W0–W4 + action authority consistent with AI_CONNECTION T0–T4 | KEEP | No security conflict found. Capability registry lists tools as installed paths only (no runtime invocation evidence). |

## Update (2nd pass, same day)
- A6 DONE: SAVEY now cites ENFORCEMENT §4.5/§5 as gate owner (section existence verified).
- A7 DONE: AI_CONNECTION §3 declared discovery-side, terminating at LEARNING CANDIDATE; promotion owned by ENFORCEMENT §5.1.
- S1/S3 BLOCKED (permission): `.claude/hooks/` edit denied by harness; patch + replay cases in `HANDOFF/TAKY_ALPHA_HOOK_PATCH_CANDIDATE_2026-10-03.md`. Matcher also omits `Read|Grep` (secret reads ungated; needs settings.json approval).
- 4 validators still BLOCKED (python run needs approval); no enforcement PASS claimed.
- A5 (vocabulary dedupe across 5 files) remains open; not rewritten without a diff review.

## Alpha readiness
PARTIAL. Policy text is coherent; enforcement linkage is incomplete (A1, S1, S3). No claim of runtime/enforcement PASS.

## Recommended Alpha order
1. Approve & land A1 registry entries -> run the 4 blocked validators.
2. S1/S3 hook hardening with a runnable hook test (stdin JSON samples).
3. S2 scenario connection record or disable; S4/S5 pinning/narrowing.
4. A5–A7 MERGE edits (reference-only trims).
5. A9: extend EXECUTION_CHECKPOINT stage receipt; add one replay case.
6. R1 backup cleanup with approval.
