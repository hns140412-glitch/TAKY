# 2026-09-13 — Gemini + Claude + TAKY Enforcement v2 Integration

Status: HISTORY / CROSS-VALIDATION INTEGRATION RECORD

## 1. Inputs reviewed

This integration reconciled:
- current TAKY canonical state after the 6aa raw-source comparison;
- Gemini recommendations concerning self-contained Handoff portability, Notion/reference isolation, no-user-as-QA pre-response recovery, and rule single-source ownership;
- Claude's six-file patchset: README/limitations, unified taxonomy proposal, pre-response checklist, textual replay log, Handoff portability requirements, and HISTORY claim correction;
- prior deterministic F-01~F-06 replay and current repository implementation.

External proposals were treated as `REFERENCE_ONLY / CANDIDATE` until compared against current canonical. They were not copied into canonical merely because an external validator recommended them.

## 2. Disposition

### ADOPT
- actual self-contained Handoff bundle closure, including physical artifact presence, SHA-256 verification, manifest pointer resolution, authority/freshness classification, and resume simulation;
- pre-user-request recovery exhaustion so the user is not the default searcher/debugger;
- structured REFERENCE_ONLY isolation for Notion/external material;
- explicit human approval where promotion policy requires it;
- machine-readable single-owner Rule Registry;
- CI execution of deterministic replay + registry lint + bundle-closure fixture;
- conditional/status-accurate history wording.

### ADJUST
- Claude/Gemini fixed “3 recovery paths” concept: use at least 3 materially distinct recovery families when 3+ are available; if fewer exist, exhaust all. Repeated keyword attempts inside one source do not count as distinct families.
- Claude “3 resume questions” concept: replace fixed count with coverage of every materially required canonical owner.
- Claude “do not mix CURRENT/HISTORICAL/etc. in one table”: mixing is allowed when every artifact is explicitly classified; unclassified mixing is the failure.
- Gemini/Claude proposed new package/user-QA labels: retain existing canonical semantic classes (`HANDOFF_LOSS`, `USER_AS_QA`) and use detailed reason codes rather than duplicating taxonomy.

### SUPERSEDED / DO NOT MERGE LITERALLY
- Claude's unified taxonomy file is superseded by current `MASTER/FAILURE_TAXONOMY.md`, which includes additional enforcement classes and intentionally distinguishes `MISSING` from `FALSE_MISSING_DECLARATION` and `UNRESOLVED_CONFLICT` from `UNCLASSIFIED_CONFLICT`.
- Claude's F-03/F-06 FAIL result remains valid evidence for the older isolated audit package, but it is not the current repository-state verdict after deterministic enforcement was added.
- Claude patches targeting package-local `MASTER_VALIDATION_CONTEXT_TARGET_EXCERPTS.md`, `HISTORY_GLOBAL_AUDIT.md`, or `meta/STATE.json` are historical package corrections, not current TAKY canonical file replacements.

## 3. Canonical/enforcement changes applied

- `MASTER/RULE_REGISTRY.json`: machine-readable semantic owner registry.
- `ENFORCEMENT/rule_registry_lint.py`: verifies unique Rule IDs and owner-file existence.
- `MASTER/FAILURE_TAXONOMY.md`: adds `AUTHORITY_BOUNDARY_VIOLATION`; Q-01/A-01/B-01 fixture mapping.
- `MASTER/ENFORCEMENT_PROTOCOL.md`: adds recovery-exhaustion/no-user-as-QA gate, bundle-closure gate, reference-only authority isolation, rule registry, and pre-response bridge boundary.
- `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`: adds recovery-family exhaustion before user evidence/debug request.
- `MASTER/OPERATIONAL_WORKSPACE_PROTOCOL.md`: adds structured Reference Authority Envelope and governed promotion path.
- `OS/NOTION_OPS.md`: defaults collected reference material to `REFERENCE_ONLY / NON_EXECUTABLE` and blocks direct canonical execution promotion.
- `MASTER/HANDOFF_PROTOCOL.md`: adds machine-verifiable `MANIFEST.json` bundle closure and owner-coverage resume simulation.
- `ENFORCEMENT/handoff_bundle_validator.py`: validates actual bundle files, SHA-256, classifications, pointer IDs, required-owner resume coverage, and coverage boundary.
- `ENFORCEMENT/taky_gate.py`: enforces Q-01 user-QA, A-01 authority isolation, and B-01 bundle closure contract fields.
- `ENFORCEMENT/replay_cases_v2.json`: six failure/compliant cases for Q-01/A-01/B-01.
- `ENFORCEMENT/fixtures/handoff_bundle_pass/*`: actual passing self-contained bundle fixture.
- `.github/workflows/taky-enforcement.yml`: compiles enforcement tools, lints Rule Registry, runs baseline + v2 replay, and validates the bundle fixture.
- `TAKY.md`: routes boot/execution through these gates.

## 4. Validation boundary

The repository now contains concrete deterministic enforcement for the added machine-representable conditions.

What repository checks can prove:
- encoded replay cases are classified as expected;
- declared Rule Registry owners exist and Rule IDs are unique;
- the fixture Handoff bundle is physically closed and hash-consistent;
- REFERENCE_ONLY promotion and premature user-QA conditions can be rejected when represented in the pre-response record.

What they do NOT prove by themselves:
- that every general ChatGPT response automatically invokes `taky_gate.py` before display;
- that every external AI/tool uses TAKY's validator;
- that a snapshot remains identical to current live external state after packaging;
- that a real future Handoff bundle passes until that actual bundle is validated;
- that a Notion workspace/runtime has implemented the structured authority metadata merely because the canonical rule exists.

Therefore:
`DETERMINISTIC REPOSITORY ENFORCEMENT PASS ≠ LIVE LLM RUNTIME AUTO-INVOCATION PASS`.
`OFFLINE_RECONSTRUCTION_PASS ≠ LIVE_STATE_CURRENT`.
`REFERENCE ISOLATION RULE PRESENT ≠ NOTION RUNTIME IMPLEMENTATION VERIFIED`.

## 5. Remaining improvement direction

The highest-value remaining integration is a runtime pre-response bridge in TAKY-controlled agents/apps that always emits an execution/recovery record and calls `taky_gate.py` before the user-visible response/action is released. Until such a runtime is demonstrated, live conversational enforcement remains `UNVERIFIED` even though repository enforcement is concrete.

A secondary cleanup remains desirable: gradually reduce explanatory duplication inside `MASTER/VALIDATION_RULES.md`, keeping it as a validation-composition/index layer while semantic ownership remains with the Rule Registry owners. Existing duplicate wording is subordinate to the declared owner and SHALL NOT override it.

END
