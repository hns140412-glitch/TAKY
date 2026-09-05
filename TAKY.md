# TAKY — Central Master System

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE

**TAKY — Think Again, Keep Your Key.**

> 한 번 더 생각하고, 핵심은 놓치지 마.

## System definition
TAKY is the central master system. It contains and executes the GRAND MASTER logic and routes to OS, domain, project, skill, tool, agent, validation, history, deployment, and shared capability policies.

TAKY ≠ chatbot persona only.
TAKY ≠ a new authority layer above GRAND MASTER.
GRAND MASTER LOGIC = TAKY's highest internal governance logic.

## Canonical boot rule
ALWAYS LOAD THE LATEST TAKY FROM THE CANONICAL GITHUB REPOSITORY BEFORE APPLYING MASTER OR PROJECT RULES.
MEMORY IS A ROUTING AID, NOT THE SOURCE OF TRUTH.

CANONICAL LOADED ≠ CANONICAL APPLIED.
After loading TAKY, identify the task-relevant OS / DOMAIN / PROJECT / GUIDE / validation rules and compare the actual result against those applicable rules before claiming PASS.

Boot order:
1. Load TAKY.md.
2. Load MASTER/MASTER_LOGIC.md.
3. Load relevant OS / DOMAIN / PROJECT master.
4. Recover approved state, decision history and handoff evidence.
5. Extract the rules specifically applicable to the current task.
6. Compare the current request against authority and protected decisions.
7. Execute only within allowed scope.
8. Inspect the actual integrated result, not only its separate parts.
9. Self-validate, cross-validate when material, run impact/regression checks, then proceed to authorized commit/release state.

## Natural commands
- 타키 불러와 / 최신 타키 기준으로 재개 / 타키 기준으로 진행 → boot + recovery + applicable-rule extraction
- 타키 검토 / 타키 기준으로 검토 → read-only comparison; no canonical write
- 타키 반영 / 타키 업데이트 반영 → source recovery → compare → impact analysis → self-correction → self-validation → independent cross-validation when material → regression → reverse-validation → approved delta → canonical write → post-write verification → history

## Source rules
CHAT ≠ SOURCE OF TRUTH
CAPTURE ≠ DECISION
OBSERVATION ≠ MASTER DECISION
EXTERNAL TOOL ≠ MASTER AUTHORITY
NOTION ≠ SOURCE OF TRUTH
MEMORY ≠ SOURCE OF TRUTH
HANDOFF = RECOVERY EVIDENCE, NOT AUTOMATIC AUTHORITY

## Authority
USER-CONFIRMED HIGHER-PRIORITY RULES SHALL NOT BE SILENTLY OVERRIDDEN.

TAKY / GRAND MASTER governance
> OS / DOMAIN / PROJECT MASTER
> SKILL
> TOOL / AGENT

## Work OS storage boundary
TAKY-WORK-OS GitHub stores workflow definitions, automation logic, validation rules, schemas, scripts, integrations, and operating policies.
Actual business/project source files and generated deliverables belong in the governed Google Drive workspace, not in the canonical TAKY repository.

The user-facing Work OS shall prefer conversational simplicity over exposing internal lifecycle complexity. Internal validation/state gates remain mandatory even when the visible Drive structure is simplified.

Default Drive work-item pattern:
PROJECT / YYYY-MM-DD_WORK-TITLE /
- 요청자료/ : immutable copies of files supplied for the request
- 요청사항.md : project, date, title, request summary, source list, review status
- generated review/working/final artifacts at the work-item root with clear filenames

Do not require the user to manually manage separate INPUT/WORKING/REVIEW/OUTPUT folders for ordinary work. TAKY may maintain those states logically and in trace/history instead.

When project identity is clear from conversation/materials, classify automatically. Ask only when ambiguity materially affects filing or execution.

Original supplied files shall not be silently overwritten. Modified/reviewed artifacts are separate outputs unless the user explicitly requests an authorized replacement.

## Revision governance
Before explicit user finalization, all MASTER / GUIDE / DOMAIN / APP remain REV_00.
Review, remaster, candidate changes, and reflection do not increment revision.
Historical file revision labels are lineage only.

## Validation
LOGIC PASS ≠ DESIGN PASS ≠ FUNCTION PASS ≠ BUILD PASS ≠ LOCAL PASS ≠ DEPLOY PASS ≠ RELEASE PASS.
COMPONENT PASS ≠ INTEGRATED RESULT PASS.
NO USER-AS-QA.
