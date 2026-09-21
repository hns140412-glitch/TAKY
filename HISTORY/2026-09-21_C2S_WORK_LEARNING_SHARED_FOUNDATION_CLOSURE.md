# 2026-09-21 C2S — Work OS / Learning OS / Shared Foundation Architecture

Status: C2S CLOSURE RECORD
Source scope: current conversation from the Work OS / Learning OS separation discussion through TAKY universal-basis enforcement, ownership-map reflection, shared-runtime foundation and initial Ready consumer migration.
Canonical basis before this C2S: TAKY main @ c53ee827c03133576f1f9c6e0c6480991f470207

## 1. Trigger

The user clarified that the architectural question was not merely "build a shared technical core", but how to structure:
- TAKY / MASTER logic;
- Work OS;
- Learning OS;
- shared capabilities;
- mobile-web apps;
- and ChatGPT's own governed answers.

The user also identified the recurring failure mode:
"TAKY 기준은 있지만 기준대로 실행안하는 문제"
and required TAKY to become the default operating basis without needing repeated "타키 기준" prompts.

## 2. Atomic extraction / disposition

### A-001 REQUIREMENT — TAKY universal operating basis
Requirement:
TAKY / MASTER logic shall be the default basis for TAKY development, MASTER/OS design, Work OS, Learning OS, mobile-web/PWA development, tool/agent/Codex/Work execution and TAKY-governed ChatGPT answers.

Disposition:
REFLECTED.

Canonical destinations:
- MASTER/MASTER_LOGIC.md
- MASTER/ENFORCEMENT_PROTOCOL.md
- OS/COMMAND_INTERACTION.md
- ENFORCEMENT/taky_gate.py
- ENFORCEMENT/runtime_orchestrator.py

Evidence:
PR #60, merge 57e9a5116b219661ac822a20daa5984858c14dfb.

### A-002 CORRECTION — user should not have to re-activate TAKY every turn
Correction:
Absence of the literal phrase "TAKY 기준" does not disable governance.

Disposition:
REFLECTED.

Rule effect:
NO TAKY PREFIX != NO TAKY GOVERNANCE.

### A-003 REQUIREMENT — Work OS and Learning OS are sibling OS layers
Requirement:
Work OS and Learning OS shall not be collapsed into one heavy OS and neither shall be the parent semantic owner of the other.

Disposition:
REFLECTED.

Canonical destinations:
- OS/WORK_OS.md
- OS/GUIDE_FAMILY_LEARNING_OS.md
- MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json
- MASTER/MASTER_LOGIC.md

Evidence:
PR #61, merge 67c376ab7b91028aec9236c438963c61dce3c4e8.

### A-004 CORRECTION — shared identity must not collapse Work and Family/Learning authority
Correction:
User / family / organization identity shall not be globally unified merely because the same human may participate in both domains.

Disposition:
REFLECTED.

Boundary:
- organization/team identity, membership, role, permission -> Work OS;
- family/child/parent identity, relationship, role, permission -> Learning OS;
- same-human cross-domain linkage -> EXPLICIT_FEDERATION only when a real use case exists.

Hard distinctions:
SAME PERSON != SAME DOMAIN IDENTITY.
ACCOUNT LINK != AUTHORITY LINK.
SHARED ENGINE != SHARED DATA != SHARED SEMANTICS != SHARED AUTHORITY.
COMMON CAPABILITY != COMMON OWNER.

### A-005 REQUIREMENT — share mechanisms before meaning
Requirement:
The shared layer shall be semantic-light.

Disposition:
REFLECTED.

Shared candidates:
- transport/request envelope;
- storage/local durable queue primitives;
- retry/backoff/idempotency mechanics;
- event envelope/correlation;
- release/version compatibility;
- PWA update lifecycle;
- OCR/vision ingestion;
- external/public API adapter mechanics;
- authentication transport only when boundary-safe.

Excluded from shared ownership:
- Work identity/authority;
- Family/Learning identity/authority;
- Work task/project meaning;
- Learning assignment/planner meaning;
- domain conflict-resolution meaning.

### A-006 REQUIREMENT — architecture proposal must compile ownership before structure
Requirement:
Before material shared-core/OS-boundary/ownership changes, TAKY must derive:
OWNER MAP -> SHARING CLASS -> PROTECTED BOUNDARIES -> COUNTEREXAMPLE -> STRUCTURE.

Disposition:
REFLECTED + DETERMINISTIC GATE.

Evidence:
PR #58, merge 27a926e73423480a6c3415b675771f0366a43e12.

### A-007 REQUIREMENT — architecture profile auto-activation
Requirement:
A material architecture/shared-core/OS-boundary/ownership change must not depend on the caller remembering to select ARCHITECTURE_CHANGE.

Disposition:
REFLECTED + DETERMINISTIC GATE.

Evidence:
PR #59, merge b4608f20155732f5efaaf69ee582847c4aecb975.

### A-008 REQUIREMENT — shared technical foundation should precede lower app realignment
Requirement:
Build proven reusable common mechanisms first, then migrate lower apps to those contracts with compatibility adapters instead of wholesale rewrites.

Disposition:
PARTIALLY IMPLEMENTED.

Canonical owner:
MASTER/SHARED_TECHNICAL_CAPABILITY_REGISTRY.json

Current implemented shared references:
- CAP-RELEASE-COMPAT-001
- CAP-PWA-UPDATE-001

Evidence:
PR #63, merge c53ee827c03133576f1f9c6e0c6480991f470207.

### A-009 REQUIREMENT — Learning App Family remains subordinate to Learning OS
Requirement:
Ready / Hide / Snap cross-app learning semantics belong to Learning App Family under Learning OS, not to the global shared technical layer.

Disposition:
REFLECTED.

Owner:
MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md

### A-010 REQUIREMENT — Ready / Hide / Snap remain specialist project owners
Disposition:
REFLECTED.

Current ownership:
- Ready & Set: BASE CAMP / Planner / TODAY / learning session orchestration.
- Hide & Seek: vocabulary discovery/retrieval specialist.
- Snap & Pop: thought/expression/writing/speaking specialist.

### A-011 CORRECTION — stale project documentation must not revive legacy identity
Ready README historical "Time Attack" identity and Snap README REV10-current wording were identified as authority drift.

Disposition:
REFLECTED / CLOSED.

Evidence:
- Ready PR #74 -> merge 5b1d88a153c54d470db044bf81c5a237fa0d66a8.
- Snap PR #2 -> merge 1c1a4e8d009c25e37e74c8d07b0ae33f0a89c6d0.

### A-012 REQUIREMENT — mobile app development registry is a volatile snapshot
Requirement:
Stored repo heads/deploy relationships cannot be treated as perpetual live current truth.

Disposition:
REFLECTED / PARTIAL.

Rule:
REGISTRY_SNAPSHOT != LIVE_CURRENT_STATE.

Evidence:
PR #62 -> merge 99c1a7f6b1e96217fc5a4eed9db867fc88d514c5.

### A-013 IMPLEMENTATION — Ready first consumer migration
Current Ready main:
d453f4c3f23e7b5ffba1b44665a0c68643a7eb51

Implemented on main:
- vendored shared TAKY release compatibility primitive;
- vendored shared PWA update state primitive;
- Ready release descriptor;
- service-worker cache identity derived from release_id;
- unconditional install-time skipWaiting removed;
- waiting worker activation through Ready-owned safe point + APPLY_UPDATE;
- Ready safe point conservative rule: no active session;
- VERSION.json converted to compatibility mirror;
- package/version registry aligned;
- Node/Chromium shared-runtime tests added;
- trusted Ready validation extended.

Status:
CODED on main.
Do not infer DEVICE_VERIFIED or PRODUCTION_VERIFIED.

### A-014 OPEN — Ready release-drift test hardening
Open PR:
Ready-Set #77
Head:
3366910ae7227fa1bec56de36fb0ca31af3b5758

Purpose:
Make regression test load the real Ready release descriptor and cross-check VERSION.json, package.json, READY_SET_VERSION_REGISTRY.json, service-worker cache derivation and shared script wiring instead of duplicating descriptor values inside the test.

Disposition:
OPEN / NEXT CHAT.

### A-015 OPEN — Hide & Seek / Snap & Pop shared-runtime migration
Requirement:
After Ready stabilizes, migrate Hide and Snap to the same release/PWA mechanisms while preserving their Learning App Family semantics.

Disposition:
OPEN.

Order:
Ready -> Hide -> Snap.
Do not use Netlify as implementation feedback loop.
Use hosting only after frozen candidate / external-resource gate.

### A-016 OPEN — shared local-first/event mechanics
Current evidence:
Ready already has project-local IndexedDB snapshots/outbox/conflicts/retry/idempotency.

Known gaps:
- state identity vs immutable event identity;
- base/local/remote versioning;
- semantic conflict classes;
- replay/convergence;
- dead-letter/bounded retry;
- acknowledgement/version checkpoint;
- multi-tab/concurrent/offline ordering tests.

Disposition:
OPEN.
Do not extract identity/authority semantics with the transport mechanism.

### A-017 HOLD — Work/Learning cross-domain identity federation
Disposition:
HOLD_UNTIL_REAL_USE_CASE.

Default:
isolation.

No federation contract shall be implemented merely for architectural symmetry.

## 3. Current architecture reconstruction

TAKY CORE
├── Shared Technical Capability (semantic-light mechanisms only)
├── Work OS
│   └── Work domain/projects
└── Learning OS
    └── Learning App Family
        ├── Ready & Set
        ├── Hide & Seek
        └── Snap & Pop

Platform adapters are implementation adapters, not semantic owners.

## 4. Current shared-capability status

REFERENCE_IMPLEMENTED:
- CAP-RELEASE-COMPAT-001
- CAP-PWA-UPDATE-001

DESIGN/EXTRACTION OPEN:
- CAP-EVENT-ENVELOPE-001
- CAP-LOCAL-QUEUE-001
- CAP-OCR-INGEST-001
- CAP-HTTP-ADAPTER-001

HOLD:
- CAP-AUTH-TRANSPORT-001 until concrete multi-consumer reuse is proven without Work/Learning identity leakage.

## 5. New-chat resume order

1. Read current TAKY main and this C2S closure.
2. Read Ready main @ d453f4c3f23e7b5ffba1b44665a0c68643a7eb51.
3. Inspect Ready PR #77 and current workflow evidence.
4. If #77 passes, merge only that drift-gate delta.
5. Re-check Ready shared-runtime migration against exact main.
6. Update TAKY shared-capability consumer state from migration-open to evidence-backed Ready state.
7. Then migrate Hide & Seek.
8. Then Snap & Pop.
9. Keep local-first/event extraction separate from release/PWA migration.
10. Do not call Netlify until a frozen candidate crosses the TAKY external-resource gate.

## 6. No-silent-loss / claim boundary

Recovered material from this architecture sequence has a disposition above.
No new cross-domain identity federation is implied.
No hosted ChatGPT automatic invocation of GitHub TAKY gates is claimed as VERIFIED.
No device or production verification is inferred from code/CI/runtime browser evidence.

C2S closure status:
UNMAPPED_MATERIAL = 0 within this recovered scope.
SILENT_LOSS = 0 within this recovered scope.
FALSE_CONVERGENCE = 0.

END
