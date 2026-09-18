# TAKY × NOTEBOOKLM CONVERSATION RECOVERY PROTOCOL

Status: REV_00 / CANONICAL OPERATIONAL PROTOCOL
Rule ID: TKY-NBLM-001
Role: Use NotebookLM as a source-grounded recovery/research assistant without allowing summary loss, unsafe source ingestion, authority inflation, or direct canonical promotion.
Authority: TAKY / GRAND MASTER > this protocol > notebook/pilot-specific prompts.
Related: `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`, `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md`, `MASTER/ENFORCEMENT_PROTOCOL.md`.

## 0. Core model — HARD LOCK

`NOTEBOOKLM = EVIDENCE-ASSIST / CONTEXT-RECOVERY ENGINE`
`TAKY = DISPOSITION / C2S / CANONICALIZATION ENGINE`

NotebookLM is useful for reading large source sets, finding chronology, corrections, repeated patterns, missing-context candidates and source-linked passages.

NotebookLM SHALL NOT be treated as:
- original evidence;
- canonical authority;
- a substitute for raw conversation;
- an automatic decision-maker for ADOPT/REJECT/SUPERSEDE;
- proof that all source coverage is complete.

`NOTEBOOKLM OUTPUT != RAW SOURCE`
`NOTEBOOKLM SUMMARY != USER DECISION`
`SOURCE-GROUNDED ANSWER != CANONICAL RULE`

## 1. Recovery pipeline

Default controlled flow:

`SOURCE INVENTORY
-> SECURITY / PROVENANCE CHECK
-> RAW-SOURCE PACK
-> NOTEBOOKLM ANALYSIS
-> OUTPUT PRESERVATION
-> TAKY RAW RECHECK
-> C2S ATOMIZATION
-> SEMANTIC DIFF
-> DISPOSITION
-> COVERAGE CLOSURE
-> REVERSE RECONSTRUCTION
-> AUTHORIZED BACKFILL`.

No step from NotebookLM output may jump directly to canonical write.

## 2. Source classes

Minimum classes:
- `RAW_CONVERSATION`
- `PRESERVED_TRANSCRIPT`
- `RECOVERY_WITNESS`
- `ORIGINAL_ATTACHMENT`
- `PAGE_CAPTURE`
- `HANDOFF`
- `DERIVED_ANALYSIS`
- `NOTEBOOKLM_OUTPUT`
- `CANONICAL_REFERENCE`.

Recovery preference remains owned by TKY-RECOVERY-001. This protocol adds NotebookLM-specific intake and authority constraints.

## 3. Source Security Gate — HARD LOCK

Before a source is eligible for NotebookLM, classify:
- content checked;
- provenance;
- conversation/actor preservation;
- completeness/coverage;
- duplicate/derived relationship;
- sensitive/session/auth data risk;
- sanitization status.

Files such as saved HTML pages, browser captures, application bootstrap pages, exported webpages or shared-page snapshots may contain content unrelated to the visible conversation, including session/account/authentication/bootstrap data.

If such data is present or cannot be excluded:
- preserve the original only as evidence when appropriate;
- set `SECURITY_HOLD / SANITIZE_REQUIRED`;
- set `notebooklm_eligible=false`;
- create a transcript-only sanitized derivative if the source is needed;
- verify the derivative before promoting it to NotebookLM input.

`RAW PRESERVATION != SAFE FOR NOTEBOOKLM`
`PAGE CONTENT VISIBLE != FILE CONTENT SAFE`

Secrets/tokens/authentication/session material SHALL NOT be copied into prompts, notebook source packs, canonical history prose, or user-visible reports.

## 4. NotebookLM input eligibility — HARD LOCK

A source may be used as direct NotebookLM input only when:
- provenance is known enough for the task;
- `content_checked=true`;
- `security_status=SAFE_FOR_NOTEBOOKLM`;
- `notebooklm_eligible=true`;
- actor/source boundaries are sufficiently preserved for the requested recovery;
- derived/summary sources are labeled and not mistaken for raw source.

HANDOFF / DERIVED_ANALYSIS may be used for comparison, but SHALL NOT replace available raw conversation.

## 5. NotebookLM output authority — HARD LOCK

Every NotebookLM result enters TAKY as:
`REFERENCE_ONLY / EVIDENCE_ASSIST`.

It may propose:
- chronology;
- candidate corrections;
- candidate decisions;
- candidate missing details;
- repeated-pattern hypotheses;
- candidate source locations;
- reverse-reconstruction gaps.

It SHALL NOT directly set:
`ADOPT / REJECT / SUPERSEDED / COMPANY_STANDARD / CURRENT_BEST / CANONICAL`.

Promotion requires raw-source recheck plus applicable TAKY C2S/recovery/authority gates.

## 6. Prompt contract

Notebook-specific prompts SHOULD request source-linked outputs and preserve:
- SOURCE;
- ACTOR;
- ORDER/DATE when available;
- ORIGINAL MEANING;
- WHY;
- relation to prior item;
- candidate status;
- confidence;
- needs-raw-check.

Default passes for conversation recovery:
1. chronology/context;
2. user correction / BEFORE→CORRECTION→AFTER;
3. decision vs assistant-proposal vs frontier/open/hold/conflict;
4. omission/detail candidate scan;
5. reverse reconstruction / missing-context scan.

Do not ask NotebookLM for a single compact “final truth” summary as the primary recovery artifact.

## 7. Drive operating surface

Default logical workspace:
`TAKY-WORK-OS / SOURCE_ARCHIVE / NOTEBOOKLM_RECOVERY`

Recommended layers:
- `00_SOURCE_REGISTRY`
- `01_RAW_SOURCE_PACKS`
- `02_NOTEBOOKLM_WORKING`
- `03_NOTEBOOKLM_OUTPUT`
- `04_TAKY_C2S_REVIEW`
- `05_ACCEPTED_BACKFILL`
- `90_UNVERIFIED_SOURCE`

The registry stores pointers/classification; it SHOULD avoid unnecessary duplicate copies of already durable originals.

## 8. C2S recovery gate

NotebookLM-assisted recovery is complete only after:
- NotebookLM claims used for system change have raw-source support;
- Assistant proposals are not mislabeled as user decisions;
- latest user corrections are linked;
- distinct alternatives are not falsely converged;
- material recovered items are dispositioned;
- TKY-C2S coverage closure passes for the declared recovered scope.

NotebookLM output may remain useful even when canonical backfill is not yet authorized; preserve it as REFERENCE_ONLY with open verification needs.

## 9. Duplicate / derived source handling

Multiple archived copies of the same conversation SHALL NOT be counted as independent corroboration merely because filenames/locations differ.

Track:
- `duplicate_of`;
- `derived_from`;
- source class;
- content-check status;
- coverage overlap.

`THREE COPIES OF ONE TRANSCRIPT != THREE INDEPENDENT SOURCES`.

## 10. Consumer NotebookLM vs API automation

The default consumer workflow may require a human to create/select a NotebookLM notebook and choose Drive sources. This is an operational UI step, not a TAKY reasoning step.

If a trusted supported NotebookLM/Notebook Enterprise API becomes available and is authorized, automation may manage notebooks/sources while preserving every gate in this protocol.

API availability does not relax source security or authority boundaries.

## 11. Completion / claim boundaries

Allowed:
- `SOURCE REGISTRY CREATED`
- `PILOT SOURCE PACK READY`
- `NOTEBOOKLM OUTPUT RECEIVED / REFERENCE_ONLY`
- `RAW RECHECK PASS`
- `C2S COVERAGE PASS WITHIN DECLARED SCOPE`
- `BACKFILL WRITTEN + VERIFIED`.

Disallowed:
- “원대화 전체 복원 완료” when inaccessible ranges remain;
- “TAKY 반영 완료” from NotebookLM output alone;
- “안전한 원문” before source security inspection;
- “독립 검증” when several files are duplicates/derivatives of one source.


## 12. Context economy / selective activation

NotebookLM use for conversational continuity SHALL follow `MASTER/CONVERSATION_CONTINUITY_PROTOCOL.md` (TKY-CONTINUITY-001).

NotebookLM is an L2 targeted recovery layer, not a permanent always-on context layer.

Use it only when L0 current context + L1 canonical continuity are insufficient for a material historical/context question.

`NOTEBOOKLM AVAILABLE != NOTEBOOKLM REQUIRED`
`GLOBAL NOTEBOOK != DEFAULT RESUME PATH`
`TARGETED RECOVERY > FULL HISTORY RELOAD`


## 13. Saved ChatGPT share-page transcript sanitization

When a saved ChatGPT share-page HTML contains usable shared-conversation data but also session/bootstrap/auth/application state, the original remains `PAGE_CAPTURE / SANITIZE_REQUIRED / notebooklm_eligible=false`.

A derived NotebookLM input may be created only through a transcript-only extraction that:
- decodes the share page's declared `linear_conversation`;
- emits only USER and ASSISTANT messages;
- excludes SYSTEM / DEVELOPER / TOOL / application/bootstrap/session/auth data;
- preserves source node IDs and timestamps when available;
- marks non-text parts explicitly rather than silently dropping them;
- retains `derived_from` lineage to the original page capture;
- passes a post-output forbidden-pattern/security scan.

Reference implementation:
- `ENFORCEMENT/chatgpt_share_transcript_sanitizer.py`
- `ENFORCEMENT/chatgpt_share_transcript_validator.py`.

A successful derivative is `RECOVERY_WITNESS_EVIDENCE`, not the original HTML and not proof of complete account-history coverage.

`SAFE DERIVATIVE != ORIGINAL SOURCE REPLACED`
`LINEAR CONVERSATION RECOVERED != ALL ACCOUNT HISTORY RECOVERED`

END
