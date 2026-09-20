# 2026-09-21 — Engineering Execution Profiles Research / Validation Record

## Scope
User-authorized TAKY improvement based on the reviewed prompt patterns:
- precision repair / root-cause + minimum diff;
- architecture preservation + SRP without forced fragmentation;
- safe database migration / RLS / referential/index reasoning;
- evidence-based security review;
- project-reference-first UI implementation;
- concise reporting without reducing internal validation.

## External evidence reviewed
Reference-only evidence was localized, not promoted as authority:
1. NIST SSDF (SP 800-218 Rev.1 draft/current 2025-2026 material): secure development practices should integrate into the development lifecycle.
2. OWASP ASVS / Cheat Sheet guidance: applicable security controls and verification evidence are preferred over arbitrary vulnerability-count theater.
3. Supabase database migration/RLS documentation: version migrations; RLS, grants and per-operation policies; authorization tests.
4. PostgreSQL CREATE INDEX documentation: ordinary index builds can block writers; CONCURRENTLY changes locking/runtime behavior and has caveats.
5. GitHub pull-request guidance: small focused changes and self-review improve reviewability and error detection.

## Canonical delta
- Added `MASTER/ENGINEERING_EXECUTION_PROFILE_PROTOCOL.md` — TKY-ENGEXEC-001.
- Linked it from `MASTER/MASTER_LOGIC.md`.
- Registered it in `MASTER/RULE_REGISTRY.json`.
- Classified it in `MASTER/MASTER_FILE_REGISTRY.json`.
- Added mechanical expression in `MASTER/ENFORCEMENT_PROTOCOL.md`.
- Extended `ENFORCEMENT/taky_gate.py`.
- Added `ENFORCEMENT/replay_engineering_profiles_v1.json`.
- Added `.github/workflows/taky-engineering-profile-gate.yml`.

## Self-validation / correction loop
Initial PR self-review and repository replay exposed two material issues before merge:
1. `MASTER/ENGINEERING_EXECUTION_PROFILE_PROTOCOL.md` was not classified in `MASTER/MASTER_FILE_REGISTRY.json`; existing global enforcement correctly failed. Fixed by registering the file as `ACTIVE_OWNER`.
2. Protocol prose allowed multiple profiles inside one record while deterministic gate accepted one. Fixed by defining one primary profile per material action record and sequencing profile-specific records for cross-concern work.
3. Common contract prose required remaining UNKNOWN state, while the deterministic gate did not. Fixed by requiring an explicit `remaining_unknowns` list and updating fixtures.

This is the intended TAKY loop:
`DELTA -> ACTUAL REPOSITORY CHECK -> DISCREPANCY -> ROOT CAUSE -> MINIMUM CORRECTION -> REPLAY`.

## Regression evidence
PR #56 head after corrections:
`78f3f67cd9f3dc74b4a551ff2cc84f500a80f584`

GitHub Actions:
- TAKY Engineering Profile Gate — PASS.
- TAKY Enforcement Replay — PASS after the registry/composition/UNKNOWN corrections.

The engineering replay covers historical-failure and compliant cases for:
- REPAIR;
- ARCHITECTURE_CHANGE;
- DATABASE_MIGRATION;
- SECURITY_REVIEW;
- UI_IMPLEMENTATION;
- concise-output/internal-validation separation.

The general `replay_cases_v5.json` is also rerun by the new profile workflow to detect regression in the pre-existing generic pre-action gate.

## Claim boundary
The evidence proves:
- canonical branch content is structurally accepted by current repository governance;
- new deterministic profile fixtures pass;
- existing generic pre-action replay still passes;
- MASTER file authority classification passes.

It does NOT prove:
- hosted ChatGPT automatically invokes these repository gates before every response;
- any specific app implementation/runtime/device is now verified;
- a limited security review proves complete security;
- a database migration is production-safe without project-specific schema/data/runtime evidence.

## Result
Repository-level reflection and regression state: PASS for the declared canonical delta, pending merge of PR #56 at the time this record is authored.
