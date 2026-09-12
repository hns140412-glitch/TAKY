# 2026-09-13 TAKY Execution Enforcement / Replay Evidence

Status: HISTORY / DETERMINISTIC REPLAY EVIDENCE
Canonical base inspected: `8b8e1206f70cfd340e9f9df40ef8ead58122c157`
Raw comparison evidence: Google Drive ChatGPT-share HTML `6aa5dc7a-3b80-83ee-aaf6-f7792abef303` (stored 2026-09-13 KST; title `최신 타키 기준 재개`).
Trigger: full/raw conversation comparison plus external validation feedback identifying prose-only enforcement, absent executed replay, F-03/F-06 self-failure, taxonomy duplication, package portability weakness, and claim-state mismatch risk.

## 1. What was rechecked

The latest recoverable raw conversation was compared against the current TAKY canonical base rather than against Handoff/summary alone.
The raw conversation repeatedly shows the same operational expectations already partly represented in TAKY: orchestrate rather than push debugging/search burden to the user; produce the requested result instead of an easier substitute; interpret `모든/전체/최대한/원문/실제/완성본/결과물/반영/실행/검증` literally within authority/capability boundaries; recover prior evidence before declaring it absent; and make handoff independently recoverable when maximum/full transfer is requested.

Current canonical text already contains strong prose rules for those failure classes, including the F-01 through F-06 fixture definitions. The remaining defect was that the repository could describe recurrence prevention without having a deterministic enforcement expression or completed replay evidence.

## 2. Adopted structural corrections

1. `MASTER/FAILURE_TAXONOMY.md`
   - establishes one normative taxonomy across intent/result, recovery/evidence, reflection/handoff, and enforcement axes;
   - maps overlapping prior class lists instead of treating them as unrelated vocabularies;
   - prevents `UNVERIFIED_SOURCE_COVERAGE` from hiding known recovery failures.

2. `MASTER/ENFORCEMENT_PROTOCOL.md`
   - defines fail-closed pre-response/pre-execution gates;
   - adds concrete maximum/full handoff portability requirements;
   - distinguishes package checksum integrity from live repository verification;
   - requires representative replay for recurrence-prevention claims;
   - adds human-approval and state/history consistency gates;
   - explicitly applies the portability rule to TAKY's own validation packages.

3. `ENFORCEMENT/taky_gate.py`
   - stdlib-only deterministic validator suitable for local/CI execution;
   - detects mechanically representable F-01~F-06 failure conditions and completion overclaims.

4. `ENFORCEMENT/replay_cases.json`
   - contains a historical-failure and post-fix-compliant case for each F-01 through F-06.

5. `.github/workflows/taky-enforcement.yml`
   - runs syntax compilation and deterministic F-01~F-06 replay on relevant push/pull-request changes.

## 3. Actual replay executed before canonical write

Command:

`python ENFORCEMENT/taky_gate.py --replay ENFORCEMENT/replay_cases.json`

Result:
- fixture version: `2026-09-13.1`
- cases: `12`
- passed: `12`
- failed: `0`

Historical-failure detection:
- F-01 → `RECOVERY_FAILED / FALSE_MISSING_DECLARATION / USER_FORCED_RECOVERY / USER_AS_QA / PREMATURE_PASS`
- F-02 → `OMISSION / REPLAY_NOT_PERFORMED / PREMATURE_PASS`
- F-03 → `HANDOFF_LOSS / SCOPE_SHRINKAGE / SUBSTITUTE_RESULT / OMISSION / UNCLASSIFIED_CONFLICT / PREMATURE_PASS`
- F-04 → `STALE_STATE / WRONG_REFLECTION / PREMATURE_PASS`
- F-05 → `SCOPE_SHRINKAGE / SUBSTITUTE_RESULT / OUTPUT_FORM_MISMATCH / PREMATURE_PASS`
- F-06 → `ENFORCEMENT_MISSING / RULE_NOT_APPLIED / REPLAY_NOT_PERFORMED / PREMATURE_PASS`

Every paired post-fix-compliant case produced no failure token.

## 4. What this replay proves

It proves that the committed deterministic gate, for the encoded execution-state contracts, identifies the targeted historical failure conditions and accepts the paired compliant states.
It also proves that F-03 is no longer treated as a merely descriptive handoff rule in the harness: no-repository-access + pointer-only/non-portable source transfer is mechanically rejected.
F-06 likewise rejects both prose-only enforcement for a mechanically checkable rule and rule-cited/result-violates-rule behavior.

## 5. What this replay does NOT prove

`DETERMINISTIC GATE PASS ≠ LIVE LLM RUNTIME PASS`.

This replay does not prove:
- that every future ChatGPT/agent response will invoke the gate automatically;
- that every external AI/runtime uses these repository rules;
- that a referenced GitHub live HEAD is independently verified by an offline recipient;
- that human approval occurred unless an approval record is actually supplied;
- that every historical conversation has byte-for-byte account-export coverage.

Those boundaries remain explicit rather than being upgraded to PASS.

## 6. F-03 / package rule correction

A maximum/full isolated package must include either full canonical source snapshots or a reconstructable diff plus complete base, together with a source manifest, authority/time classification, and resume simulation. SHA/blob/checksum pointers alone are insufficient when the recipient lacks repository access.

Package checksum semantics are limited to package/internal integrity unless external live repository state was independently verified.

## 7. Taxonomy correction

Previous TAKY material used a recovery-failure list, an intent/result discrepancy list, and reflection discrepancy classes in different documents. They are now modeled as distinct axes under one normative taxonomy with explicit cross-axis mappings. Existing documents may retain tokens as contextual references, but semantic ownership is centralized in `MASTER/FAILURE_TAXONOMY.md`; future edits must not redefine them independently.

## 8. State-claim correction

A completed local/canonical delta may be described as completed even while an independent/external validation remains PENDING, but the entire validation program must not be worded as unqualified complete. The deterministic gate classifies such overclaim as `STATE_CLAIM_MISMATCH` and normally `PREMATURE_PASS`.

## 9. Remaining boundary

The major gap is reduced from “prose only” to “deterministic repository gate + replay + CI”, but live assistant/runtime invocation remains a separate integration problem. Until the conversational/runtime layer actually emits and validates the machine-auditable execution record, recurrence prevention at live-model level remains `UNVERIFIED`, not PASS.

END
