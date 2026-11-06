# TAKY CANONICAL RUNTIME STATE

Status: ACTIVE / CANONICAL STATE SURFACE
Authority: subordinate to `MASTER/MASTER_LOGIC.md`; authoritative for current operational situation/decisions/open issues when consistent with higher canonical rules.

## Boot rule
A new conversation/session SHALL NOT reconstruct current TAKY/project state from conversational memory, a user-written summary, or a handoff summary first.

Required first recovery sequence:
`READ STATE.md -> VERIFY state_revision/source refs -> READ required canonical/history refs -> VERIFY resume evidence -> CONTINUE`.

If `STATE.md` cannot be read, current state is `STATE_REHYDRATION_BLOCKED`; do not assume remembered state is current.

## Current governance state
- repository enforcement: `REPOSITORY_EXECUTABLE + CI_ENFORCED`
- role/action/owner classification trust source: `UNVERIFIED`
- repository C2S preflight composition: `REPOSITORY_EXECUTABLE + CI_ENFORCED`
- NotebookLM legacy recovery: `INACTIVE_DEFAULT / LEGACY_REFERENCE_ONLY`; active historical recovery uses direct Drive + TAKY C2S unless explicitly re-enabled
- conversation continuity/context economy: `CANONICAL_PROTOCOL_IMPLEMENTED + CI_ENFORCED`
- saved-share transcript sanitization: `IMPLEMENTED + ACTUAL_DRIVE_PILOT_PASS + CI_ENFORCED`
- hosted ChatGPT native tool-call automatic preflight: `UNVERIFIED`
- live hosted runtime fail-closed claim: `PROHIBITED`
- P0 open architecture issue: `#2 Trusted routing authority + runtime preflight interception`
- Visual design/UI asset-source default (user decision 2026-09-29): `TKY-ASSET-001` at `MASTER/DESIGN_UI_ASSET_SOURCE_PROTOCOL.md`; original reusable assets and layers go to GitHub `TAKY-ASSETS`, app repos keep pinned manifest + verified deployment copies. Image/ZIP alone does not satisfy asset upload or UI implementation; current hosted cross-chat automatic interception remains UNVERIFIED.

## Current unresolved root issues
1. Trusted routing authority independent from executor is not implemented.
2. Hosted ChatGPT native tool dispatch does not have a repository-proven mandatory preflight interception hook.
3. Validation-only evidence must not be allowed to advance authoritative product-progress state without functional acceptance evidence.
4. Resume/context-compression must use verified canonical/history rehydration evidence rather than self-reported booleans.
5. Hosted conversation runtime still lacks repository-proven automatic C2S invocation/interception even though a repository-executable C2S bridge exists.

## Work / AI executor resource-routing policy

### 실행 PC 지정 — 2026-11-06 사용자 결정
- Claude Code CLI와 Codex CLI의 신규 실행은 기본적으로 `YKH-RENDER` (Desktop Commander deviceId `b33ddd20-100f-4d27-a658-ffaee81746de`)에서 수행한다. 기존 메인 PC는 원본 조회·조정·증거 기록 담당이며, 렌더가 오프라인이어도 확인 없이 메인에서 CLI를 대체 실행하지 않는다.
- 렌더 PC 양쪽 CLI 설치·구독 로그인 및 각각 1회의 최소 읽기 전용 응답 검증 성공. **이는 TAKY 저장소 전체 이관/실제 코드 수정 성공의 증거가 아니다.** 메인의 `D:\Git PWA\TAKY`는 미커밋 변경이 있는 원본이고 렌더에 동일 REV의 실제 작업본이 아직 없음. 소스가 필요한 실행은 권위 원본과 동일 REV가 검증되기 전 `BLOCKED_SOURCE_UNAVAILABLE`로 구분한다.
- 이 지정은 실제 Desktop Commander 장치 선택과 로컬 예약 작업에서 검증된 운영 규칙이며, ChatGPT 호스팅 전체 대화에 자동 강제되는 신뢰된 라우팅 훅의 구현을 뜻하지 않는다. 별도 유료 API, push/merge, 배포 없음.

Work, Claude and Codex SHALL be treated as scarce execution resources. TAKY SHALL NOT route a task to a model merely because the capability exists.

Before proposing or invoking Work, Claude or Codex, TAKY SHALL perform a usage-impact review:
1. determine whether the task can be completed in ordinary Chat with already-available connectors/tools;
2. if yes, prefer ordinary Chat and do not consume delegated model allowance;
3. if delegated AI execution is necessary, choose the smallest execution surface and smallest independently useful work unit;
4. assess expected context size, file/source count, reasoning depth, tool calls, test/runtime loops, browser/E2E loops, and likely retries;
5. classify usage risk at least as `LOW / MEDIUM / HIGH / VERY_HIGH`;
6. `HIGH` or `VERY_HIGH` work SHALL NOT be launched as a monolithic task without explicit usage-risk disclosure and a cheaper/smaller routing attempt first;
7. whole-history recovery, broad multi-repository analysis, or large Drive/chat/GitHub sweeps default to `VERY_HIGH` until demonstrated otherwise;
8. implementation sent to Claude or fallback Codex SHOULD arrive as a narrow TASK CONTRACT after TAKY has completed orchestration, scope selection, acceptance and dry-run usage estimation where practical;
9. Work SHALL NOT be the default always-on orchestrator for development loops; reserve it for tasks whose browser/file/multi-step execution materially requires Work;
10. when remaining Work/Claude/Codex allowance is not directly observable, TAKY SHALL state UNKNOWN and SHALL NOT claim that sufficient allowance remains.

### TAKY / implementation-owner role hard lock
Usage optimization SHALL NOT redefine Codex as a patch-only tool when it is the selected fallback implementation owner. Claude Code is the primary code executor, and Codex is the conditional fallback implementer or independent verifier according to `TKY-AICOLLAB-001` and actual usage evidence.

For software/product implementation work, the default role boundary is:
`USER INTENT -> TAKY WHAT/WHY/BOUNDARY/ACCEPTANCE -> CLAUDE PRIMARY (OR APPROVED CODEX FALLBACK) HOW/CODE/FOCUSED TEST -> TAKY REVIEW/OPTIONAL INDEPENDENT CODEX VERIFICATION -> HUMAN APPROVAL WHEN REQUIRED`.

Rules:
1. TAKY owns orchestration, requirement interpretation, product intent, scope, sequencing, acceptance criteria, risk/authority checks, executor routing, and post-implementation review.
2. The selected code executor owns implementation design, new code authoring, code changes, focused tests, and evidence within TAKY-approved scope. Claude is the default coding route when available; Codex is fallback only when task necessity and usage/cost analysis justify it.
3. When Codex is selected as an implementation owner, it may implement new features and is not a patch-only tool; it SHALL NOT independently certify its own code.
4. TAKY minimizes delegated usage by removing duplicate context, broad unrelated tests, needless rediscovery and repeated model calls before dispatch, not by pre-writing the implementer's product code.
5. Delegated implementation contracts SHOULD specify the goal, owner refs, known relevant files, constraints, acceptance criteria, relevant regression checks and receipt evidence.
6. Each executor MAY inspect focused extra implementation context but SHALL NOT rediscover settled user requirements or re-orchestrate the project.
7. TAKY SHALL NOT silently take over product implementation merely because subscriptions are scarce. If no authorized executor is available, report `EXECUTION_BLOCKED_NO_OWNER` or defer the implementation slice.
8. An executor completion report is evidence only: `CLAUDE_DONE != TAKY_PASS` and `CODEX_DONE != TAKY_PASS`.
9. Usage risk SHALL be assessed separately from implementation ownership: `HIGH_USAGE_RISK != TAKY_MAY_IMPLEMENT`.
10. For large tasks, decompose into independently useful slices and keep coding responsibility with the selected executor; independent verification must be author-distinct when it is required.

### Delegated model validation-budget policy
The selected executor or verifier SHALL NOT run every available validation layer on every implementation turn by default.

Default execution ladder:
`IMPLEMENT -> SMALLEST RELEVANT STATIC/CONTRACT TESTS -> REPORT EVIDENCE -> TAKY REVIEW`.

Escalate to browser/mobile/E2E only when at least one of the following applies:
- the changed behavior cannot be established by focused automated evidence;
- the task is at an integration/acceptance checkpoint;
- TAKY explicitly marks runtime/mobile evidence as required for that slice;
- prior evidence indicates a browser/runtime-specific regression risk.

Rules:
1. Previously obtained valid runtime evidence SHALL be reused when the subsequent change cannot affect that path; do not rerun expensive browser flows mechanically.
2. Browser/mobile/E2E verification SHOULD be batched at meaningful integration checkpoints rather than repeated after every small implementation edit.
3. Baseline failures SHALL be compared against the recorded start HEAD with the smallest possible command/test set; do not rerun the full suite merely to classify a known failure.
4. A usage-limit interruption SHALL preserve work state. Resume from existing changes/results and run only unfinished checks; never restart the whole contract by default.
5. Selected-executor reports SHALL separate `IMPLEMENTATION COMPLETE`, `FOCUSED TEST PASS`, `RUNTIME VERIFIED`, `RUNTIME UNVERIFIED`, and `BLOCKED_BY_USAGE_LIMIT` rather than converting missing expensive validation into failure or fabricated PASS.
6. Expensive validation is evidence work, not code-authoring authority. Deferring it does not transfer implementation ownership from the selected executor to TAKY.

### Delegated executor workspace bootstrap policy
A Claude or Codex implementation contract SHOULD identify repository, canonical work branch, and task-contract path before dispatch. The selected executor SHALL bootstrap/fetch the named repository/branch when it has authorized repository access instead of asking the user to manually discover task-file paths. User intervention is reserved for genuine authentication, permission, network, or filesystem boundaries that Codex cannot resolve itself.

Current resource condition — 2026-09-14:
- user-visible Codex 5-hour allowance reached 0% during `RNS-P0-DAILY-LOOP-001` after approximately 16m30s of implementation/Chrome/runtime/test activity;
- user reported approximately three hours until Codex can be used again;
- visible weekly allowance remained available, but exact future consumption is not predictable from TAKY;
- observed interrupted evidence: 17 related checks, 12 passing and 5 failing; Codex was attempting start-HEAD baseline comparison when usage stopped; Chrome/mobile-width PARTIAL and parent/replanning behavior had already been exercised;
- authoritative lifecycle remains `CODEX_INTERRUPTED_BY_USAGE_LIMIT / WORK_PRESERVED / TAKY_REVIEW_NOT_READY` until repository evidence is inspected and the unfinished implementation/validation is resumed;
- during the cooldown, TAKY SHALL continue orchestration, GitHub inspection, acceptance refinement, evidence classification, contract decomposition, and non-product-code governance work using ordinary Chat/connectors. TAKY SHALL NOT take over product implementation code.

Claim boundary:
`CAPABILITY AVAILABLE != RESOURCE-AFFORDABLE`
`WORK/CODEX AVAILABLE != WORK/CODEX SHOULD_BE_USED`
`TASK DISPATCHED != USAGE SAFE`
`USAGE OPTIMIZATION != ROLE REASSIGNMENT`
`TAKY ORCHESTRATION != PRODUCT CODE AUTHORING`
`CODEX IMPLEMENTER != PATCH-ONLY TOOL`
`BROWSER E2E AVAILABLE != BROWSER E2E REQUIRED EVERY TURN`
`USAGE LIMIT INTERRUPTION != RESTART FROM ZERO`

## Ready learning-engine current main — 2026-09-20
- repository: `hns140412-glitch/Ready-Set`
- merged PR: #68
- current reflected main SHA: `6142cfeb5599a625d61ffa1faca866b2b6817cc8`
- state: `READY_MAIN_CURRENT / CODED / CI_VERIFIED / RUNTIME_VERIFIED`
- exact-main evidence: Integration CI #119 PASS; TAKY Codex Worker Self-Test #322 PASS; Ready Runtime E2E #205 PASS
- learning versions: Subject Master 0.2.1 / Unit Map 0.2.2 / Standard Matcher 0.4.1 / Learning Master 0.5.1
- canonical reflection: `PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md §6.1–6.2`
- review evidence: `HISTORY/2026-09-20_READY_LEARNING_ENGINE_FINAL_REVIEW_PR68.json`
- device verification: NOT_RUN
- production verification: NOT_VERIFIED; Netlify current deploy still points to pre-merge Ready main evidence and must be verified after deployment refresh.
- hard boundary: `RUNTIME_VERIFIED != DEVICE_VERIFIED != PRODUCTION_VERIFIED`.

## Ready renewal candidate — 2026-09-20
- Ready main remains `6142cfeb5599a625d61ffa1faca866b2b6817cc8` and remains current implementation truth.
- renewal branch: `taky/ready-renewal-v01`
- Draft PR: #73
- candidate scope: refresh exact-main validation/version truth; rebuild decision ledger; align runtime/product authority; add PRE-ACTION/branch-first workflow; define P0→P7 renewal implementation order.
- TAKY Ready owner updated: `PROJECTS/READY_WHOLE_IMPLEMENTATION_CONTRACT.md §22 / §25`
- promotion state: CANDIDATE / NOT_MERGED
- hard boundary: `RENEWAL_CANDIDATE != READY_MAIN_CURRENT`.
- next implementation after renewal promotion: P1 Planner reality engine, then P2 Child FACT confirmation, P3 cross-app continuity, P4 UI/product-language consolidation, P5 legacy cleanup, P6 device, P7 production.

## Ready renewal C2S closure — 2026-09-20
- continuity evidence read first: Google Drive `READY_SET_HANDOFF_2026-09-20_LATEST`.
- Ready main reverified: `6142cfeb5599a625d61ffa1faca866b2b6817cc8`.
- renewal branch: `taky/ready-renewal-v01`, Draft PR #73.
- reviewed implementation snapshot: `450caf84b23788b40a93e070742d86edc0165baa`.
- branch evidence at reviewed snapshot: Ready Integration CI #130 PASS / Worker Self-Test #331 PASS / Runtime E2E #216 PASS, 45/45.
- P1 Planner reality engine: CODED + CI_VERIFIED + RUNTIME_VERIFIED on candidate; main promotion pending.
- P1 semantics: confirmed availability profiles + commitments + travel/prep/meal/rest-compatible blocking + before/after buffers; zero-executable-window dates excluded; availability is an executability gate, never study-volume authority.
- next unresolved implementation gate: P2 generic `CHILD INPUT → PARENT REVIEW/CONFIRM → FACT → LEARNING MASTER → PLANNER → TODAY`.
- external hosting was not used for this review/C2S closure.
- deployment candidate remains NOT_FROZEN; Netlify/external deployment remains blocked until exact frozen candidate + TAKY external-resource gate.
- `REVIEW_SNAPSHOT_CLOSED != MAIN_MERGED != DEVICE_VERIFIED != PRODUCTION_VERIFIED`.

## State mutation rule
Material state changes SHALL update this file or a referenced canonical state owner in the same work episode.
Conversation text alone is not durable state.

Each session/conversation SHALL append only its material delta to `HISTORY/SESSION_DELTA_LOG.md` rather than regenerating a synthetic full-history summary.

## Resume gate
`resume_simulation_passed` SHALL NOT be accepted as a naked boolean.
A valid resume claim requires machine-verifiable resume evidence identifying at minimum:
- state source path;
- exact state SHA-256 or immutable revision;
- state read/verification timestamp or execution record;
- required canonical/history sources recovered;
- reconstruction assertions;
- evidence file SHA-256.

No resume evidence -> no verified resume.

## Claim boundary
`STATE FILE EXISTS != STATE READ`
`STATE READ != REQUIRED SOURCES VERIFIED`
`MANIFEST says PASS != RESUME VERIFIED`
`HANDOFF SUMMARY != CURRENT STATE`

## Historical recovery checkpoint — 2026-09-14
- state_revision: 2026-09-14-source-backfill-01
- recovery_status: PARTIAL_BACKFILL / FULL_REVIEW_PENDING
- recovery evidence owner: HISTORY/2026-09-14_SOURCE_BACKFILL_CHECKPOINT_01.md
- conversation inventory: HISTORY/2026-09-14_SOURCE_INVENTORY_01.json
- 24 original share exports extracted; full semantic reading and attachment recovery are incomplete. Extraction is not full review.
- source TAKY main inspected at 995805ec2d38fcac7911f9b2316554d0d2b58868; this is a pre-backfill snapshot, not an evergreen latest SHA.
- Ready work branch runtime-session-bridge-2026-09-10 observed at a098ffac8b5d6f0aeb22b5e61250f70330d555c7. Historical checkpoint said READY_FOR_CODEX / NOT_DISPATCHED; this is superseded for current execution by the interrupted Codex state above.
- Repository handoff resume evidence binding is implemented at aee98e436c815f638f7b9bb2a98a200c2282f9ae; hosted automatic state read, semantic rehydration, and trusted routing remain UNVERIFIED.
- Full-review completion gate: NOT_PASSED. No product-progress advancement or deployment is implied.

## 2026-11-06 — Site Watch / Mining 현장 점검 및 차단 상태
- 기존 `D:\Git PWA\TAKY-SOURCE-VAULT` 기준 사이트 레지스트리 13개 활성. `digittv.notion.site`, `lazyowen.com`, `sdk-kim-builds.com`, `www.trendcore.co.kr`가 포함됨. Instagram 팔로우 피드의 실제 계정 목록/새 게시물 자동 접근은 검증되지 않음.
- Site Watch 2026-11-06 13:15 예약 실행 `SKIP_GLOBAL_GATE` (다음 허용 시각 13:48 KST), `exit 0`은 그 시간대 신규 RAW 수집 성공을 의미하지 않음. 10:15 현장 기록은 `new_raw_handoffs=0`, 기존 505건 재사용.
- 12시간 로컬 수집 12:45 실행 실패 원인: `COLLECTOR_VISUAL_EVIDENCE.py`가 `PIL` 미발견. `C:\Python314` 사용자 site-packages 폴더가 소문자 `pil`로 저장돼 있어 `PIL` 이름 검색에 실패한 것을 확인. 폴더 이름만 `PIL`로 교정하여 `Image/ImageOps` import 및 임시 이미지 축소·JPEG 저장 시험 PASS. **전체 12시간 수집 단계 E2E 재실행 미검증**.
- `TAKY Mining Queue Worker`는 `oauth_not_allowed_for_organization` 403 / `CLAUDE_SUBSCRIPTION_BLOCKED_BY_ORGANIZATION_POLICY`로 `HOLD_PROVIDER_AUTHORIZATION_REQUIRED` 상태; 자동 재시도 금지·모델 호출 0. 기존 `RUN_MINING_QUEUE_WORKER_SCHEDULED.ps1` 수정해 HOLD이면 `exit 2`로 보고. 스크립트 파서 0오류·실제 차단 구동 `MiningQueueExitCode=2` 검증. 인증/키/과금 경로 임의 우회하지 않음.
- 기존 사이트 파생 자료: 로컬 검색 인덱스 후보 466, Index Owner 검토 대기 145, 추출 증거 유닛 18,279. `owner_approved=0`, `forming_approved=0`, `learning_consumed=0`. 이 중 미승인 상태는 의도된 승인 게이트이며 의미 마이닝 성공이나 최종 기능 적용으로 해석 금지.
- Notion 로컬 관측 2026-11-06 13:00: `notion_total=236`, `queue_count=239`, `notion_blocks_read=0`, 신규 변경 0, `CollectorExitCode=2` (별도 원인 분석 필요). YKH 별도 `WORKBENCH/MINING` 공개 소스 7건 기초 텍스트 추출 성공은 본 TAKY Site Watch의 인덱싱·학습 승인과 혼동 금지.
- OPEN: 유효한 구독 CLI 경유 의미 분석 및 렌더 PC 소스 동기화/적법한 권한 경로 검증 필요. 메인 PC 저장소와 렌더 경로가 동일 REV가 아니므로 병렬 변경 금지. 유료 API·push·merge·배포 없음.

## 2026-11-06 — Site Watch 게시물 본문 우선 검토 범위 (사용자 지시)
- `검토해` 및 팔로우 사이트 와칭의 **일차 대상은 글/게시물 제목·발행/수정일·공개 본문·원문 링크**다. 인스타그램 영상 다운로드, 전체 이미지/OCR, 포괄적 브라우저 시뮬레이션 등은 필수 단계가 아니다. 텍스트로 판단 불가한 건축 도면·UI·작업 시연만 개별적으로 시각 검증한다.
- 기존 `SITE_WATCH_REGISTRY` 13개와 등록된 seed, `SOURCE_HTML_EVIDENCE_V2` 및 `MINE_SITE_EVIDENCE_UNITS_LOCAL`을 재사용하고, 1회 검토 최대 10건·변경 없는 문서 재처리 금지. `게시글 링크/작성일 → 본문 핵심 주장 → 출처 사실성 → 기존 하네스/CLI/MCP 중복 여부 → 실증 가능한 적용안 → BLOCKED/보류`로 보고. 읽지 못한 원문은 UNKNOWN으로 둔다.
- 웹 공개 글 검토의 최초 4건은 기존 YKH `WORKBENCH/MCP_SKILL_AGENT_CASE_RESEARCH_20261106.md`에도 근거와 함께 보존. 다만 개인 TAKY 와칭의 자료/승인 권위와 YKH 회사 도구 도입의 권위를 섞지 않는다. 이는 **검토 기준 적용**이며 사이트 파이프라인의 의미 마이닝 자동 복구, 인스타그램 로그인·팔로우 목록·게시물 전체 취합 성공의 근거가 아니다.

## 2026-11-06 — Aside 인스타그램 본문 근거 확보와 기초 마이닝
- 메인 PC Aside Browser CLI `aside repl --host local`의 실제 브라우저 세션에서 인스타그램 게시물 화면 접근 정상 확인. 기존 DM 창이 게시물 상세를 가려 읽기 실패를 일으켰고, DM 창을 닫은 뒤 접근 복구. 메인 Aside 응용프로그램의 메인 창은 1개로 관찰됨. 메시지/댓글 작성, 팔로우 변경, 좋아요, 외부 공유 없음.
- **실물 검증**: `@sdk.kim.builds`(김스득), `@lazy_owen`(게으른 빌더), `@digit.tv`(디지트) 3개 계정 모두 실제 팔로잉 버튼 확인. 공개 게시물 9건(계정별 3건)의 제목/본문(Caption)과 직접 게시물 URL을 UI에서 읽어 각각 SHA-256 봉인. `D:\Git PWA\TAKY-SOURCE-VAULT\reports\site_watch\ASIDE_INSTAGRAM_CAPTION_SOURCE_20261106.json`에 수집 본문, 원문 URL, 해시, 1차 검토/보류 사유를 한 번에 기록. 전체 파일 최종 SHA-256 `b164ba27c4e2b037732f5e977539588ba9100c49822a4ffc12a873513e4470f3`. 본문/해시 9/9 재검산, 중복 URL 0.
- **분석 결과**: 우선 검토 4건(업무별 스킬·완료 조건, 디지트의 7항목 모델링 지시서, CAD 축척별 표현, 계단 유형별 치수/면적); 재사용 1건(기존 Claude 세팅); 기존 설치 검증 1건(Claude-Mem); 저장소 및 실제 수정가능 PPT 검증 1건; 12인 배심원형 과다 에이전트·실명 없는 플러그인 10종은 보류 2건. 계단 산술 예시 175×16=2800mm, (7×260×2+1200)×1200=5.808㎡, 3020×2400=7.248㎡ 검산(현재 법규·실제 도면 정합 증거 아님).
- **권위 게이트**: 인스타그램 본문 읽기/기초 분석을 확인한 것과 광범위한 인스타그램 전체 팔로우 피드 수집, 승인된 Index·Forming·Learning 적용, 하네스 최종 구현은 다르다. 본문은 `NON_AUTHORITATIVE_SOURCE_EVIDENCE`, 분석은 `SOURCE_BOUND_PRELIMINARY_TRIAGE`, `canonical_promoted=false`, `learning_consumed=false`로 유지. 새 엔진/플러그인·유료 API·Git push/merge/배포 없음.
- **장치 경계**: Aside 로그인 브라우저는 메인 PC에서 작동, 렌더 PC에는 Aside 설치·해당 세션 원격 접근 없음. 개인 브라우저 로그인·민감 피드를 공개 SMB 브리지로 복제하지 않는다. 기존 SITE WATCH/Mining 입력 파이프라인의 자동 승인·의미 재마이닝은 별도 OPEN으로 남김.

## 2026-11-06 — 외부 사례/인스타그램 마이닝 × TAKY 현황 비교 검토 (CANDIDATE)
- 기존 CURRENT·MASTER 소유 규칙을 변경하지 않고, 근거 기반 비교 문서 `HISTORY/2026-11-06_SITE_WATCH_HARNESS_COMPARATIVE_REVIEW.md` 작성 및 readback 확인. 이는 권위 승격/구현 PASS가 아니라 검토 증거임.
- 핵심: 인증된 Aside Instagram 게시물 9/9 본문 SHA 확인, `SITE_WATCH_TAKY_DATA_REVIEW_CANDIDATES_CURRENT.json` 466개와 일치 URL 0/9, Index Owner accepted 0 / Forming approved 0 / Learning consumed 0. 게시물만 확보했다고 Closed 아님.
- 권고: 기존 SOURCE/RAW/INDEX/FORMING/LEARNING 권위 유지, Instagram Aside 캡션을 `SOURCE_BOUND_PRELIMINARY_TRIAGE`로 기존 Intake에 전송, 원본 완전 보존 미확인은 `INCOMPLETE_RAW_PRESERVATION`으로 구분. 가장 작고 유효한 후보 1건에서 Index Owner→실행 consumer→증거 연결 우선. 독립 에이전트 남발/새 하네스·MCP·LangGraph/Temporal 설치 불필요.
- YKH 회사 27건 검토대장은 독립 소유; 16 reviewed/6 partial source/5 not secured, reflection 3 partial/24 not reflected. 디지트 건축 지시서·축척·계단 사례는 YKH 도메인 검증 후보이지 TAKY 전역 법령/학습 규칙으로 직접 승격 금지.
- 실행제약: 렌더 TAKY 원본 소스/REV 미확보, Claude 구독 의미 마이닝 조직 정책 403 HOLD, 메인/렌더 CLAUDE-MEM 의존성 차이 및 AutoCAD 실무 원본 불일치. 신규 유료 API·push/merge/배포/Instagram 댓글·DM 작성 없음.

## 2026-11-06 — 사용자 지시 순서 역전 및 사후 합리화 실패 박제
- **실제 사고 = FAIL / REWORK_REQUIRED**. 사용자 요청 `독립 원문/기존자료 분석 → 사례별 독립 교차검토 → 최적안 선도출 → 마지막 TAKY 비교`를 어기고, TAKY를 먼저 정답처럼 전제해 사례를 맞춰 평가·합리화한 실패.
- **실패 원문 및 원인**: `HISTORY/2026-11-06_REVIEW_ORDER_INVERSION_FAILURE_CASE.md`. 원래 비교 보고서 `HISTORY/2026-11-06_SITE_WATCH_HARNESS_COMPARATIVE_REVIEW.md` 맨 앞을 **FAIL / NOT ACCEPTED**로 표시해 기왕의 "최적안" 명칭을 승인된 독립 최적안으로 재사용하지 못하도록 함.
- **규칙 권위**: 기존 `TKY-INTENT-001` 의미 그대로, `MASTER/REVIEW_DEFAULT_MINING_PROTOCOL.md`에 **INDEPENDENT SOURCE → CASE-BASED CROSS-ANALYSIS → INDEPENDENT OPTIMAL OPTION → TAKY COMPARE LAST → VALIDATE** 고정. 사용자 명령의 순서는 권고가 아닌 수락 조건이며, 기존 TAKY 원칙으로 결과를 사후 합리화하는 행동은 FAIL.
- **재발 방지 검증**: 기존 `MASTER/EXECUTION_REGRESSION_FIXTURES.md`에 `F-07` 실패 재현 시나리오·PASS/FAIL 수락 기준 작성. 현재 상태는 `RULE_WRITTEN / FIXTURE_REGISTERED / REPLAY_NOT_PERFORMED`. 규칙 문서 저장은 호스팅 응답 자동 강제 구현이나 실제 재검증 통과가 아님.
