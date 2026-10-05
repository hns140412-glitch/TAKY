# TAKY 2.0 — CLAUDE SHARED-DRIVE COMPARISON PATCH / 2026-10-05

## PURPOSE
Compare the current executable TAKY2 kernel against the Claude/shared-Google-Drive TAKY 2.0 drafts and canonical-labeled documents, then adopt only improvements that strengthen enforcement without re-expanding TAKY2 into a semantic mega-framework.

## LOCAL BASELINE
- Branch: `taky-2.0-orchestrator-2026-10-05`
- Comparison baseline: `e4256a0675abc81e5d61199e6cea4daace78988e`
- Push / merge / deploy: NOT AUTHORIZED / NOT DONE.

## DRIVE SOURCES REVIEWED
1. `01_UNIFIED_STANDARDS_AND_RULES [Q001 ✅ Q002 ✅ Q003 ✅ CANONICAL]`
   - document_id: `1RTq8NIc82F4QVFpwGjL9wb3vlrglIEQjls7Dg4VQ_7E`
   - reviewed revision: `ANLCKQlPmRIpEbCq-lHZ7_55nGBoiEWZwq2w7Kte0T-kyH-_r_wwkqZrW1gDSAcP_oV-ZuqLbbi8M1OWEUZkkFAj40Be3t5EnqCekh1pEbM`
2. `TAKY_2.0_NEW_CHAT_START_AND_WORKING_PREMISE`
   - document_id: `11BG91-phb11WmmIHoF6rS2TfWFK6yuJJEszFTsQ7B9M`
   - reviewed revision: `AHj4eMQR0P0h-D1HJjrwGy9Y5FlzVCxMHjk3gKJ9OpFDJmI781zct0Luc5EJ_Z78pqXRiUJE4DZhcXPlH_AAyMK_MtXC2nHvQuE-4vkK5eY`
3. `TAKY_역할구조_실행흐름_통합검토안_2026-10-05`
   - document_id: `19WgSgRgMweVJJc3FgUskadBc0iK9iquKw3tBJbHN21U`
   - reviewed revision: `ANLCKQn776sr7ZTHdgHJTDcW5gHUaFNTEX8fwG3XqlEB2HxRjEQU9PlRsLVuNeWj25-jvxW4i0R_ZeTopx-RF4f2BOUnLPH1BYgPomnSPBg`

## SOURCE STATUS CAUTION
The first document title says Q001/Q002/Q003 CANONICAL, but its body still contains sections marked DRAFT / USER CONFIRMATION REQUIRED / NOT CANONICAL / PENDING. Therefore the whole document was NOT treated as blanket runtime authority. Only clauses consistent with current USER authority and the existing closed 5 HARD GATE design were adopted.

## AGREEMENT — ALREADY STRONGER OR ALREADY IMPLEMENTED LOCALLY
- USER != DEBUGGER.
- KEY / CONTEXT / ROUTE / COST / DONE remain the only five hard gates.
- Necessity Check stays inside COST; it is not a sixth gate.
- repeated full-context reread is blocked.
- transient failures are separated from structural route failures.
- different-route budget is bounded.
- NO EVIDENCE, NO DONE.
- silence does not equal USER confirmation.
- actual executor cannot self-certify SUCCESS.
- evidence/completion are receipt-bound.
- external write account attestation fails closed.
- runtime HMAC + external rollback anchor + CAS are stronger than the prose-only shared-drive version.
- actual invocation wrapper/provider-model binding is stronger than the prose-only shared-drive version.

## ADOPTED FROM CLAUDE / SHARED-DRIVE VERSION

### A. VERSIONED KEY + KEY_AMEND — ADOPTED
Shared-drive improvement:
- each binding Key field carries value/provenance/scope/version.
- Key changes require USER-authorized KEY_AMEND, version progression, and old/new diff.

Kernel patch:
- KEY validation now requires scope + version.
- authority rebind now receives current authority explicitly.
- current authority digest must match the bound runtime digest.
- binding-field change requires explicit `key_amend=true`.
- existing field version must increment exactly by +1.
- new field starts at version 1.
- deletion requires explicit authorized deletion.
- changed fields require USER_STATED/USER_CONFIRMED provenance and source_ref that resolves to USER evidence in the new authority source_registry.
- signed rebind request/history stores key diff.

### B. RISK-BASED VERIFICATION TIER — ADOPTED
Shared-drive improvement:
- irreversible / external-facing-or-write / meaning-or-authority-changing work requires STRONG verification.

Kernel patch:
- receipt now stores `verification_tier`.
- external/irreversible or explicitly authority/meaning-changing actions become STRONG.
- STRONG minimum checks: structural + technical + intent + independent.
- STANDARD minimum checks: technical + intent.
- verifier and DONE gate both fail closed if the required tier is under-specified.

### C. EXPLICIT USER STOP → ABANDONED — ADOPTED
Shared-drive improvement:
- explicit USER stop may terminate active or delivered-unconfirmed work.

Kernel patch:
- verified receipt-bound USER `stop` event is accepted.
- receipt becomes consumed.
- active execution ownership is released.
- execution outcome becomes `ABANDONED`.
- DONE reports ABANDONED rather than pretending NOT_DONE/SUCCESS.

### D. ESCALATION PACKET — ADOPTED
Shared-drive improvement:
- escalation should give USER only the decision/info needed, not debugging work.

Kernel patch:
- when route budget/transient cap requires USER decision, preflight emits:
  - cause
  - prior attempts + failure class
  - remaining options
  - recommendation
  - single user_decision_or_info
  - blocked attempt
- this preserves EXHAUST THEN ESCALATE and USER != DEBUGGER.

## DELIBERATELY NOT ADOPTED

### Fixed “Claude = Primary Executor”
Not adopted.
Reason:
- conflicts with Necessity/Route gates.
- executor must be selected per capability, cost, evidence, and necessity.
- Claude/Codex/Remote are routes, not permanent authority owners.

### 24-hour Snapshot Expiry
Not adopted.
Reason:
- appears as a pending parameter in the source.
- age alone does not prove context staleness.
- current verified snapshot + DELTA/change evidence is safer than an arbitrary clock TTL.

### Transient Retry = 3
Not adopted.
Reason:
- shared-drive text presents this as example/pending.
- existing kernel limit remains 2 until USER authority changes it.

### Loosening Route Identity
Not adopted.
Reason:
- current normalized target+method route identity deliberately prevents task_id/alias retry bypass.
- adding caller-controlled `failure_point_addressed` to identity could create a bypass unless independently verified.

### Blanket CANONICAL Promotion From Document Title
Not adopted.
Reason:
- title/body status conflict.
- USER authority and executable evidence take precedence over a label.

## REGRESSION AFTER PATCH
- unit tests: 60/60 PASS
- py_compile: PASS
- git diff --check: PASS
- Claude/Codex calls: 0 (Necessity Gate = NO; Drive source + local code were sufficient)
- Remote: used only for authorized local branch inspection/edit/test
- push / merge / deploy: NOT DONE

## REMAINING OPEN
Production ACCOUNT TARGET BINDING remains fail-closed:
- current Key target is USER_STATED `HNS`.
- existing central Google/family auth can produce authenticated session evidence.
- reviewed material refers to the hns140412 account/workspace, but no explicit authority mapping of `HNS` alias to a concrete authenticated family/session identity was found that is strong enough to silently bind.
- do not guess this mapping.

## VERDICT
The shared-drive Claude version materially improves the current kernel in four places: KEY_AMEND, verification tiering, ABANDONED, and escalation packets.
The local TAKY2 kernel remains stronger on executable enforcement, receipt binding, independent verification, invocation control, and state integrity.
Result: adopt the four compatible improvements; reject role rigidity and pending/ambiguous parameters.
