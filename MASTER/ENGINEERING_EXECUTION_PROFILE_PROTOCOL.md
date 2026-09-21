# TAKY ENGINEERING EXECUTION PROFILE PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-ENGEXEC-001
Role: Convert engineering-task intent into compact, evidence-backed execution contracts that improve implementation quality without replacing TAKY's existing authority, ownership, validation, C2S, or project-specific rules.
Authority: TAKY / GRAND MASTER > this protocol > project/domain engineering specialization.
Related: `MASTER/MASTER_LOGIC.md`, `MASTER/INTENT_EXECUTION_PROTOCOL.md`, `MASTER/ENFORCEMENT_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`, `MASTER/VALIDATION_RULES.md`, `MASTER/UI_REFERENCE_PROTOCOL.md`.

## 0. Core principle — HARD LOCK

`ROLE LABEL != EXECUTION CONTRACT`.
`"SENIOR ENGINEER" PERSONA != VERIFIED ENGINEERING BEHAVIOR`.
`CONCISE USER OUTPUT != REDUCED INTERNAL VALIDATION`.
`MINIMUM DIFF != MINIMUM THINKING`.
`ARCHITECTURE PRESERVATION != BLIND LEGACY PRESERVATION`.
`SRP != FORCED FRAGMENTATION`.
`RLS PRESENT != AUTHORIZATION CORRECT`.
`MIGRATION SCRIPT EXISTS != SAFE PRODUCTION MIGRATION`.
`SECURITY FINDING COUNT != SECURITY QUALITY`.
`EXTERNAL DESIGN STYLE != PROJECT DESIGN AUTHORITY`.

Engineering work SHALL be driven by the smallest sufficient, task-specific execution profile that binds:
`INTENT -> BASELINE/EVIDENCE -> PROTECTED STATE -> TARGET DELTA -> EXECUTION -> TARGETED VALIDATION -> REGRESSION -> RESULT REPORT`.

Profiles are operational overlays. They do not supersede project requirements, canonical authority, implementation ownership, human-approval gates, or claim ladders.

## 1. Profile selection

Select one or more profiles only when materially applicable:

- `REPAIR` — debugging, error correction, regression repair, broken behavior.
- `ARCHITECTURE_CHANGE` — module boundaries, responsibility movement, interface changes, refactoring with structural impact.
- `DATABASE_MIGRATION` — schema/data migration, RLS/grants/policies, indexes, referential actions, production database change.
- `SECURITY_REVIEW` — attack-surface review, vulnerability remediation, abuse-path validation, security-sensitive change.
- `UI_IMPLEMENTATION` — UI/UX implementation or redesign where visual/system consistency and interaction behavior matter.

For deterministic enforcement, each material action record SHALL select one primary profile. Cross-concern work MAY compose profiles by sequencing profile-specific action records/slices under the same higher-level task. Composition SHALL remain bounded to materially applicable concerns.

Do not select profiles merely to make a prompt sound expert. The selected profile SHALL change concrete execution behavior.

## 2. Common execution contract — HARD LOCK

For a material profile-driven engineering task, retain enough structured state to identify:

- `profile(s)`;
- `baseline_evidence_refs` — code/schema/design/runtime/source actually inspected;
- `protected_state` — confirmed behavior, interfaces, data/history, authority and do-not-touch constraints;
- `target_delta` — the smallest materially sufficient intended change;
- `acceptance_conditions`;
- `validation_steps`;
- `regression_scope`;
- `remaining_unknowns`;
- `report_mode`.

When the user requests a short answer, the report MAY collapse to:
`ROOT CAUSE / CHANGED SCOPE / DIFF OR ARTIFACT / VALIDATION / REMAINING UNKNOWN`.

The internal execution/validation obligations do not shrink merely because the user-facing report is concise.

## 3. REPAIR profile — Precision Repair Contract

Use when a known behavior is failing or an error must be corrected.

Required flow:
`FAILURE EVIDENCE -> FAILURE CLASS -> ROOT CAUSE -> MINIMUM SUFFICIENT DELTA -> TARGETED RETEST -> REGRESSION -> RESULT`.

Required behavior:
1. inspect the actual error/runtime/test evidence and the smallest relevant source range;
2. state a falsifiable root cause, not a symptom-only description;
3. prefer the smallest sufficient change that fixes the causal path while preserving protected behavior;
4. avoid broad rewrites unless the existing boundary itself is the demonstrated root cause;
5. re-run the smallest test that proves the failure is corrected;
6. run affected regression checks;
7. if the same approach already failed under materially unchanged conditions, do not repeat it without new evidence.

User-facing default for a repair MAY be:
- cause: one concise line;
- changed files/modules;
- exact diff or equivalent change summary;
- targeted validation result;
- remaining UNKNOWN/UNVERIFIED.

`SHORT EXPLANATION != SKIPPED ROOT-CAUSE WORK`.
`SAME FAILED APPROACH + NO NEW EVIDENCE != ITERATION`.

## 4. ARCHITECTURE_CHANGE profile — Preservation + Minimum Sufficient Complexity

Required flow:
`EXISTING PATTERN/OWNER -> CHANGE DRIVER -> RESPONSIBILITY DELTA -> BOUNDARY/INTERFACE IMPACT -> MINIMUM SUFFICIENT STRUCTURE -> INTEGRATION CHECK -> REGRESSION`.

Required behavior:
- recover current architecture/pattern before changing it;
- identify semantic owner and responsibility movement explicitly;
- preserve compatible interfaces unless incompatibility is part of the authorized change;
- use SRP/cohesion/coupling as design evidence, not as an absolute file-splitting rule;
- reject abstraction, indirection or module splitting that adds complexity without measurable ownership, testability, reuse, security or maintainability benefit;
- detect downstream holes and upstream orphans after responsibility movement;
- validate the integrated relationship, not only isolated modules.

`MODULARITY WHEN BENEFICIAL != FORCED FRAGMENTATION`.
`NEW MODULE COUNT != ARCHITECTURAL QUALITY`.

`EXISTING PATTERN != IMMUTABLE PATTERN`; demonstrated defects may justify an authorized structural change.

### 4.1 Architecture boundary compilation — HARD LOCK

Before proposing or implementing a material shared-core, cross-domain, OS split/merge, ownership move, or common-capability extraction, compile the architecture boundary before selecting the structure.

Required pre-structure model:
1. `OWNER MAP` — identify which layer/domain owns the meaning, authority, lifecycle and mutation rights for each material responsibility;
2. `SHARING CLASS` — classify each candidate as one of:
   - `SHARED_TECHNICAL_PRIMITIVE` — transport/storage/sync/runtime mechanism with minimal domain meaning;
   - `DOMAIN_OWNED_SEMANTIC` — meaning/role/authority/state owned by one domain/OS and not globally shared;
   - `EXPLICIT_FEDERATION` — separately owned identities/states linked through a scoped contract, consent/authority and revocation where applicable;
   - `NOT_SHARED` — intentionally isolated;
3. `PROTECTED BOUNDARIES` — identity, role, permission, ownership, data authority, child/family/work/tenant boundaries and other materially protected semantics as applicable;
4. `COUNTEREXAMPLE CHECK` — test at least one realistic case where the same actor/entity participates in different domains or where shared infrastructure could accidentally transfer authority/meaning;
5. only then select the minimum sufficient shared structure.

Default:
`SHARE MECHANISM BEFORE MEANING`.
A common login/account, database, event bus, identifier or storage layer SHALL NOT imply common domain identity, role, permission, ownership or authority.

`SAME PERSON != SAME DOMAIN IDENTITY`.
`ACCOUNT LINK != AUTHORITY LINK`.
`SHARED ENGINE != SHARED DATA != SHARED SEMANTICS != SHARED AUTHORITY`.
`COMMON CAPABILITY != COMMON OWNER`.

A shared layer SHOULD remain semantic-light. Cross-domain semantic/authority linkage requires an explicit federation contract rather than implicit inheritance.

If a proposed common layer would cause one domain's administrator/owner/role to gain authority in another domain merely from shared identity or infrastructure, the proposal fails the architecture boundary check.


## 5. DATABASE_MIGRATION profile — Safe Schema/Data Change

Required flow:
`CURRENT SCHEMA/DATA/ACCESS MODEL -> TARGET DELTA -> COMPATIBILITY/LOCK IMPACT -> REFERENTIAL/ACCESS/INDEX STRATEGY -> MIGRATION ARTIFACT -> TEST -> ROLLBACK OR FORWARD-FIX -> POST-MIGRATION VERIFY`.

Required behavior when applicable:
- use versioned migration artifacts rather than untracked ad-hoc production edits;
- distinguish schema compatibility, data backfill, constraint enforcement and application rollout ordering;
- explicitly justify `CASCADE / RESTRICT / SET NULL / NO ACTION` from entity lifecycle/history semantics;
- do not apply cascade deletion by template when completed/history records must remain stable;
- for exposed Supabase/Postgres tables, evaluate RLS, grants and operation-specific policies together;
- test both intended allow and deny authorization paths where access control is material;
- evaluate index necessity from query/workload evidence and account for production lock/runtime impact;
- for large/live PostgreSQL tables, consider non-blocking/concurrent index strategies and their caveats rather than assuming ordinary index creation is harmless;
- define rollback or a safe forward-fix path;
- verify post-migration schema/data/access state.

`FOREIGN KEY PRESENT != CORRECT DELETE SEMANTICS`.
`CREATE INDEX != ZERO-DOWNTIME`.
`POLICY EXISTS != ALLOW/DENY BEHAVIOR VERIFIED`.

## 6. SECURITY_REVIEW profile — Evidence-Based Security Review

Required flow:
`ASSET/TRUST BOUNDARY -> ATTACK SURFACE -> APPLICABLE CONTROLS -> FINDING EVIDENCE -> SEVERITY/REACHABILITY -> MINIMUM PATCH -> ABUSE/SECURITY REGRESSION -> RESIDUAL RISK`.

Required behavior:
- inspect applicable attack surface rather than searching for a fixed arbitrary number of vulnerabilities;
- distinguish exploitable/material findings from speculative possibilities;
- prioritize by likely impact, reachability, privilege/data boundary and ease of abuse;
- check authorization, injection/input handling, output encoding, secrets, data isolation, dependency/supply-chain and resource-abuse classes when applicable;
- use project/context-relevant verification requirements rather than cargo-cult checklists;
- patch the causal security weakness and add a representative abuse/regression test where feasible;
- do not claim the product is "secure" merely because a limited review found no issue.

`FIND EXACTLY 3 VULNERABILITIES` is not a valid completeness criterion.
A review MAY return zero findings if the inspected scope/evidence supports that result, while remaining explicit about scope limits.

## 7. UI_IMPLEMENTATION profile — Project Reference First

Required flow:
`PROJECT GOLDEN/APPROVED REFERENCE -> DESIGN TOKENS/COMPONENT CONTRACT -> SCREEN/STATE BEHAVIOR -> RESPONSIVE/ACCESSIBILITY -> IMPLEMENTATION -> REPRESENTATIVE RENDER/INTERACTION CHECK`.

Required behavior:
- project-approved visual identity and interaction rules outrank generic "Apple/Stripe/etc." role prompts;
- external design systems are REFERENCE_ONLY unless promoted through the applicable UI-reference process;
- extract transferable principles such as hierarchy, spacing, typography, density, feedback and clarity; do not silently copy unrelated brand identity;
- preserve project design tokens and semantic component behavior;
- define representative responsive and error/empty/loading/disabled states when material;
- include accessibility/legibility/touch-target considerations appropriate to the target platform;
- compare representative rendered result against the approved project reference where available.

`COMPARE TO LEARN, NOT TO COPY`.

## 8. Validation depth and report compression — HARD LOCK

Profile-driven execution SHALL use proportionate validation.

Default:
`TARGETED CHECK FIRST -> AFFECTED REGRESSION -> BROADER CHECK ONLY WHEN SHARED STATE/BOUNDARY/RISK REQUIRES IT`.

A one-line cause and small diff are valid output choices only when supported by adequate internal evidence.

If a concise report would hide a material failed/unknown gate, the UNKNOWN/FAIL state must remain visible.

## 9. Optimization rule

The profile exists to improve useful engineering output, not to add process ceremony.

Prefer:
- higher causal certainty;
- smaller reviewable deltas;
- preserved ownership/architecture;
- reproducible migration/security behavior;
- representative regression evidence;
- lower unnecessary external/tool cost;
- better future reuse through stable contracts/tests.

Do not add profile fields that never change execution or validation.

## 10. External engineering evidence basis

This protocol localizes, rather than copies, external engineering guidance:
- NIST SSDF: integrate secure development practices into the development lifecycle;
- OWASP ASVS/Cheat Sheet guidance: verify applicable security controls instead of relying on generic vulnerability theater;
- Supabase database guidance: version migrations, apply RLS/grants/policies deliberately, and test authorization behavior;
- PostgreSQL documentation: production index creation has lock/transaction/concurrency trade-offs;
- GitHub review guidance: small, focused diffs and self-review improve reviewability and defect detection.

External guidance remains evidence/reference. TAKY/project authority controls the actual adopted behavior.

## 11. Enforcement expression

When `engineering_execution_profile_required=true`, `ENFORCEMENT/taky_gate.py` SHALL verify:
- a known profile is selected;
- common contract evidence is present;
- selected profile-specific minimum contract fields are satisfied;
- concise-output mode did not reduce required internal validation;
- known anti-patterns such as unchanged failed-approach repetition, unjustified cascade deletion, arbitrary vulnerability quotas, or external-style authority substitution are blocked.

Representative replay:
`python ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_engineering_profiles_v1.json`.

Repository-gate PASS proves only the encoded contract/replay behavior. It does not prove hosted ChatGPT auto-invocation, production runtime correctness, security completeness or physical-device verification.

## 12. Boundary

This protocol owns the reusable engineering execution-profile semantics only.

It does NOT:
- move product-specific UI/feature/data requirements into GRAND MASTER;
- replace project architecture or data ownership;
- grant implementation authority to an orchestrator that lacks it;
- authorize deployment/external side effects;
- convert external guidance into canonical authority by citation alone.

END
