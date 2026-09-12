# 2026-09-13 — 6aa Source-Family Raw Conversation Comparison

Status: HISTORY / SOURCE-FAMILY FORENSIC COMPARISON
Scope: 20 Google Drive HTML files whose filenames begin with `6aa`, discovered in the 2026-09-13 KST import window and materially accessible in this review.
Canonical comparison points: pre-fix `8b8e1206f70cfd340e9f9df40ef8ead58122c157`; enforcement/boot fixes `076a859aeee1fdca19e32a845e54e4078044deb9` and `990c577d060a38eb62a994e8f84eda8fab380ce0`.
Coverage boundary: this is a raw-source comparison of the accessible `6aa` source family, not a byte-for-byte ChatGPT account export and not proof that every external URL mentioned inside the conversations was re-fetched live.

## 1. Source-family inventory

The raw ChatGPT-share HTML payloads were decoded from their embedded conversation mapping rather than treated as screenshots, titles, Handoff summaries, or search snippets. Across the 20 files, 1,383 non-empty user messages were available to the parser.

1. `6aa5d955-1510-83ee-9b36-f6b00f50101e.html` — 최신 타키 기준 재개 — 47 user messages
2. `6aa5d985-6238-83e8-831b-8bebc559eb14.html` — TAKY 반영 준비 알림 — 246
3. `6aa5d9cc-6620-83ee-b995-e9371e11941c.html` — 노션 링크 폴더 만들기 — 5
4. `6aa5d9f6-a5b4-83e8-8d49-7850a56dcef2.html` — 유튜브 요약 AI 추천 — 5
5. `6aa5da23-78d0-83ee-ba9b-95e42aa7ee55.html` — 설계개요 엑셀 작성 — 130
6. `6aa5da47-c8b0-83e8-a603-f4e55d86e169.html` — 재개 상태 요약 — 10
7. `6aa5da62-dbc0-83ee-a6e2-5dc94bc5b83e.html` — 마스터 로직 OLD — 110
8. `6aa5da84-cf54-83e8-bd0e-6eac86a613e9.html` — AI WORK OS 변화 감시 — 332
9. `6aa5dacb-dd40-83ee-a890-8ad43db2bee6.html` — 문구 검토 Translate — 14
10. `6aa5dadd-ee10-83ee-82f6-a09eca4d4ef2.html` — 타키 기준 불러오기 — 12
11. `6aa5daf5-3e74-83ee-9904-8e1fd63a3bc6.html` — AI WORK OS 변화 감시 — 3
12. `6aa5db11-0384-83e8-b10e-3f7930dc34ec.html` — 모바일 기능 연결 — 13
13. `6aa5db28-4fb8-83ee-9fa8-d900c73ec144.html` — 대화 복구 진행 — 134
14. `6aa5db60-7a18-83ee-9e30-6b9f1c2b810f.html` — 노션 구조 수정 재개 — 5
15. `6aa5db78-f6fc-83ee-904c-c500460d5bd3.html` — "TAKI" SETTING — 27
16. `6aa5db99-0e68-83ee-b6fd-98077eacb493.html` — 탐험 도우미 이름 추천 — 5
17. `6aa5dbd1-7a88-83e8-93d9-93183c6ac14e.html` — 노션 연결 방법 안내 — 109
18. `6aa5dbfe-70dc-83ee-ade9-5f07ace4058e.html` — Plus 기능 활용법 — 1
19. `6aa5dc43-3040-83e8-af76-68050ef2fa84.html` — 사업계획 일정 플로우 작성 — 87
20. `6aa5dc7a-3b80-83ee-aaf6-f7792abef303.html` — 최신 타키 기준 재개 — 88

## 2. First-pass recurrent patterns

The recurring governance failures/requirements are not isolated to one Ready & Set conversation. Cross-file recurrence shows:

- raw/original conversation must outrank compressed Handoff/summary as recovery evidence; `전체/모든/원문/누락없이` requests recur across at least 12 files;
- a missed search result must not become a nonexistence claim; user-forced recovery by old-chat search/screenshot is explicitly described;
- user repeatedly requests orchestration rather than being made the debugger/searcher; tool/agent work should be routed while the chat continues where possible;
- `결과물/완성본/실제/실행/반영` repeatedly means concrete artifact/action, not another plan or promise;
- established whole-system context must be applied, not repeatedly rebuilt from a local fragment; partial/local reinterpretation caused repeated drift;
- Handoff SHA/state must be rechecked against current GitHub HEAD/actual runtime rather than blindly trusted;
- review and apply/write are distinct authorization states;
- post-write/readback and actual-result validation are expected rather than self-asserted completion.

These patterns substantially corroborate F-01 through F-06 and the intent/recovery contracts already present in TAKY. The audit criticism that the rules were prose-only was therefore a recurrence-prevention defect, not merely a documentation preference.

## 3. Second semantic pass

A second pass used newly recovered recurrence concepts rather than the initial broad keyword set. It specifically searched for user correction patterns around stopping, debugging delegation, result-vs-promise, full/raw coverage, arbitrary reinterpretation, and whole-system context.

Material new global pattern:

### `PREMATURE_STOP`

Across multiple distinct conversations, the user explicitly delegates continued execution with wording equivalent to `확인이 필요할 때까지 진행`, `계속 진행`, `멈추지 마`, `쭉 진행`, or `달려`. The same conversations show frustration when execution stops at an intermediate explanation although an authorized next action remains.

This is not identical to `PREMATURE_PASS`: a response can stop too early without falsely claiming completion. Therefore `PREMATURE_STOP` is adopted as a separate intent/result discrepancy class and receives a deterministic gate.

### Result-not-narration enforcement

The raw sources repeatedly distinguish an actual artifact/action from narration: actual HTML, server replacement, update execution, result package, or completed handoff is requested while plans/status text are rejected as substitutes. Existing `SUBSTITUTE_RESULT / OUTPUT_FORM_MISMATCH` semantics are sufficient; no new taxonomy token is required. The enforcement harness is extended so an explanation-only response can mechanically trigger those existing classes when a concrete authorized result was required.

## 4. Disposition against current TAKY

### PRESERVE / ALREADY COVERED

- original/raw recovery before summary-only inference;
- latest user correction priority;
- source-family inventory and second-pass omission check for explicit full/global scans;
- `NO USER-AS-QA`;
- `CANONICAL LOADED ≠ CANONICAL APPLIED`;
- review vs apply authorization separation;
- all/maximum/full literal-scope semantics;
- artifact-first execution and result-form fidelity;
- forward/reverse traceability;
- GitHub canonical authority and live-head recheck over stale Handoff implementation snapshots;
- human approval as a separate gate where required.

### ADOPT / ENFORCEMENT UPGRADE

- one normative failure/discrepancy taxonomy;
- executable negative-existence gate;
- executable maximum/full handoff portability gate;
- checksum truth boundary;
- state/history claim consistency gate;
- actual F-01~F-06 replay evidence;
- `PREMATURE_STOP` gate for delegated continuation;
- result-not-narration gate using existing substitute/output-form classes;
- repository CI definition for deterministic replay.

### ADJUST

- recovery and intent protocols may list only local activation subsets; token meanings belong to `MASTER/FAILURE_TAXONOMY.md`;
- F-03 maximum/full portability requires full source snapshots or reconstructable diff+complete base for a recipient without repository access; SHA/blob pointers are evidence pointers, not portable reconstruction;
- internal ZIP/checksum integrity must not be described as independent verification of live GitHub HEAD/blob state.

### LOWER-LAYER / DO NOT PROMOTE GLOBALLY

Many recovered rules are valid but project/domain-specific: Ready & Set timer/session/card-selection/UI details; Snap & Pop growth/shop ownership; character Visual ID and Guide behavior; A3 architecture/Excel layout and statutory review details; capture/OCR wording; Notion page-specific retrieval details. These belong to their OS/DOMAIN/PROJECT owners and are evidence for the global anti-omission mechanism, not new GRAND MASTER invariants by themselves.

### HOLD / UNVERIFIED RUNTIME BOUNDARY

The repository now has deterministic enforcement and a boot route to it. However, live conversational/runtime automatic invocation of the machine-auditable record is not independently demonstrated merely by committing the protocol/harness. Live-model recurrence prevention therefore remains `UNVERIFIED` until the actual runtime emits/validates those records or equivalent gates automatically.

## 5. External audit findings reconciliation

- Prose-only enforcement: corrected at repository level with executable harness + replay + CI definition.
- No replay: corrected with executed deterministic cases.
- F-03 self-contradiction: corrected normatively; future isolated maximum/full packages must carry portable source or reconstructable diff+base. Previous pointer-only packages remain historical failures, not retroactively upgraded.
- Checksums: explicitly limited to internal/package integrity unless live external state is independently verified.
- Duplicate/disconnected taxonomies: consolidated under one normative owner; local protocols are activation subsets.
- Prime Agent/human approval: human approval requires an explicit recoverable approval record; naming an agent/validation state is not approval.
- HISTORY wording vs PENDING state: completion wording is bounded by governing state; PENDING external validation blocks unqualified whole-program completion claims.

## 6. Deterministic replay after second pass

Harness: `ENFORCEMENT/taky_gate.py`
Fixtures: `ENFORCEMENT/replay_cases.json`
Fixture version: `2026-09-13.2`
Cases: 16
Passed: 16
Failed: 0

The original 12 F-01~F-06 failure/compliant pairs remain passing. Four additional cases validate:
- `C-01`: delegated continuation stops before blocker → `PREMATURE_STOP`; compliant blocker/decision stop → clean.
- `R-01`: concrete authorized result requested but explanation-only/no result delivered → `SUBSTITUTE_RESULT / OUTPUT_FORM_MISMATCH`; actual delivery → clean.

`16/16 DETERMINISTIC REPLAY PASS ≠ LIVE LLM RUNTIME PASS`.

## 7. Coverage boundary / unresolved

This comparison proves what was found within the 20 materially accessible `6aa` raw conversation files and current TAKY repository state used for comparison. It does not claim account-wide byte-for-byte coverage outside this source family. External links/Notion/web content quoted or referenced inside those conversations remain historical source mentions unless separately re-fetched and revalidated. Any inaccessible original source remains `UNVERIFIED_SOURCE_COVERAGE`, never silently converted to absence.

END
