# TAKY NOTEBOOKLM ↔ C2S ROUNDTRIP PROTOCOL

Status: REV_00 / OPERATIONAL
Rule ID: TKY-C2S-ROUNDTRIP-001

## 0. Purpose

Close the recovery loop:

`RAW / DRIVE → NOTEBOOKLM → CANDIDATE OUTPUT → RAW RECHECK → C2S ATOMS → CANONICAL OWNER → CONTEXT MANIFEST → REVERSE RECONSTRUCTION`

NotebookLM is a recovery/indexing assistant. It is never canonical authority.

## 1. Input gate

Before adding a source to a NotebookLM pack:
- unique source_id
- source_class
- content_checked=true
- security_status=SAFE_FOR_NOTEBOOKLM
- notebooklm_eligible=true
- authority_status correctly classified
- no session/auth secret material

Derived/Handoff sources may assist discovery but may not masquerade as DIRECT_SOURCE.

## 2. NotebookLM output contract

NotebookLM output MUST enter C2S as:
- authority = REFERENCE_ONLY or EVIDENCE_ASSIST
- canonical_status = NOT_CANONICAL or PENDING_RAW_RECHECK
- explicit source_refs
- actor classification
- semantic candidate
- candidate disposition
- needs_raw_recheck = true

NotebookLM confidence is not TAKY confidence.

## 3. Raw recheck gate

Any NotebookLM candidate that can alter canonical state MUST be checked against:
1. raw/original source;
2. actor identity;
3. chronology;
4. later user correction;
5. duplicate/derived-source lineage.

If raw source is unavailable:
- do not canonicalize;
- retain as UNVERIFIED_SOURCE_COVERAGE / HOLD / OPEN as appropriate.

## 4. C2S semantic integrity

C2S compile cannot PASS when:
- a correction lacks supersedes/affects linkage;
- OPEN/CONFLICT is silently resolved;
- multiple atoms are merged without equivalence evidence;
- inaccessible source ranges coexist with FULL coverage claims;
- NotebookLM output is treated as canonical without raw recheck;
- reverse reconstruction cannot recover latest corrections, open items, WHY or intent.

## 5. Roundtrip completion

A project recovery cycle is complete only when:
- NotebookLM input registry PASS;
- NotebookLM output intake PASS;
- raw recheck done for canonical-impact candidates;
- conversation coverage validator PASS;
- semantic integrity validator PASS;
- project context gate PASS;
- reverse reconstruction PASS.

## 6. Automation boundary

Current ChatGPT environment has Google Drive access but no direct NotebookLM connector.

Therefore current operational bridge is:
`Drive source pack → NotebookLM consumer UI → export/save structured output to Drive output folder → TAKY reads output → validators/raw recheck/C2S`.

This is an explicit product boundary, not a hidden automation claim.

END
