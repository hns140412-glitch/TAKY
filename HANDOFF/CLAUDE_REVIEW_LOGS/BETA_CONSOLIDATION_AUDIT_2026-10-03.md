# TAKY Beta 통합 감사 — 2026-10-03

Status: `LOCAL_CANDIDATE_EVIDENCE / NOT_AUTHORITY / NOT_PROMOTED`
Scope: Alpha 재작성 이전의 Beta 통합 준비. 로컬 읽기 전용. 정본(CURRENT/MASTER/STATE) 미수정.
Executor: Claude (Sonnet 5.5). Author != sole reviewer → 독립 교차검토 필요(§8).
금지 준수: push / merge / deploy / commit / 유료 API / 원격 서비스 수정 없음. 이 파일 1개만 생성.

## 0. 증거 기준과 한계 (먼저 읽을 것)

| 항목 | 값 | 증거 상태 |
|---|---|---|
| 브랜치 / HEAD | `character-asset-behavior-separation-2026-09-30` / `fee09fa` ("Lock Core 6 three-sheet production contract") | VERIFIED (세션 시작 git status + `git rev-parse`) |
| 작업트리 | 수정 13개 + 미추적 다수(총 67줄) | VERIFIED |
| Alpha 산출물 커밋 여부 | `CURRENT/TAKY/`, `HANDOFF/TAKY_ALPHA_*`, `.claude/`, `.mcp.json`, `CLAUDE.md`, `OS/AI_CONNECTION_*`, `OS/SAVEY_*`, `OS/WORKSTATION_*`, `TOOLS/`, `skills-lock.json` 전부 **미추적(`??`)** | VERIFIED |
| 검증기 재실행 (`alpha_manifest_validator`, `rule_registry_lint`, `mobile_app_development_registry_validator`, `master_surface_integrity_validator`, unittest) | python 실행 권한 미승인으로 **BLOCKED** (실패 아님, 1회 시도 후 경로 변경) | BLOCKED / UNVERIFIED |
| sha256 재계산 | 보호 표면 셸 게이트에 막힘 → BLOCKED | UNVERIFIED |
| 형제 앱 저장소(Ready-Set / Snap-Pop / Hide-Seek / TAKY-MOBILE / TAKY-ASSETS) 현재 상태 | `D:\Git PWA` 상위 읽기 권한 미승인 → BLOCKED | UNVERIFIED (아래 앱 항목은 레지스트리 + 메모리 라우팅 단서만) |
| 원격 최신성(`main` 대비 ahead/behind, fetch) | 복합 명령 게이트에 막혀 미수행 | UNVERIFIED |

`ACCESS FAILURE != SOURCE ABSENCE`: 위 BLOCKED 항목을 "문제 없음" 또는 "문제 있음"으로 해석하지 않는다. Alpha 문서가 주장한 PASS(110/110 등)는 이번 감사에서 **재현되지 않았고**, 문서 주장으로만 남는다.

분류 약어: KEEP / FIX / STALE / CONFLICT / OPEN / UNVERIFIED / REMOVE-FROM-AUTHORITY (RFA).

## 1. 요약 (핵심 8)

1. Alpha "COMPLETE"는 **로컬 미커밋 작업트리** 위의 주장이다. HEAD(`fee09fa`)에는 Alpha 정본이 없다. → 커밋 전까지 "저장소 정본"이 아니다. (CONFLICT)
2. 같은 Alpha 체크포인트가 **두 경로**에 중복: `CURRENT/TAKY_ALPHA_CURRENT_2026-10-03.json` (플랫) = `CURRENT/TAKY/TAKY_ALPHA_2026-10-03.json` (네임스페이스). 참조는 후자뿐. (CONFLICT → 플랫본 RFA)
3. **매니페스트 버전 4중 불일치**: 실제 매니페스트 `.8` / CURRENT 체크 목록 `.6` / FINAL·COMPLETION 문서 `.7` / LATEST 문서 `.8`. (STALE)
4. `STATE.md`(정본 상태 표면)는 Alpha 이전(2026-09-20) 상태에 머물러 있고 미수정. 자체 규칙("같은 작업 에피소드에서 갱신") 위반. `HISTORY/SESSION_DELTA_LOG.md`에도 2026-10 항목 0건. (STALE / FIX)
5. `PROJECTIONS/ACTIVE_RULE_PROFILE.md`의 `SOURCE_CANONICAL_HEAD: 6c630a0…`, `PROFILE_VERSION 2026-09-20.5`는 현재 HEAD와 무관한 오래된 포인터. (STALE)
6. CI는 `alpha_manifest_validator.py HANDOFF/TAKY_ALPHA_LOCAL_MANIFEST_2026-10-03.json`을 실행하는데, 매니페스트가 묶는 `CLAUDE.md`, `.mcp.json`, `.claude/**`가 미추적. **일괄 커밋하지 않으면 깨끗한 체크아웃 CI는 실패할 구조**. (OPEN / 예측, 미실행)
7. 세 앱은 `DEPLOYED_STALE`, 레지스트리 스냅샷은 2026-09-21. 앱 쪽 최신 상태는 **재검증 전까지 신뢰 불가**. (STALE / UNVERIFIED)
8. 외부 경계(호스트 자동 가로채기, 인증된 인간 신원)는 올바르게 EXTERNAL_DEPENDENCY로 분류됨. 유지. (KEEP)

## 2. 소스 오브 트루스 충돌 / 소유 경로 모호성

| ID | 분류 | 증거 | 문제 | 제안(후보, 미적용) |
|---|---|---|---|---|
| C-01 | CONFLICT | HEAD에 Alpha 정본 부재, `git status`의 `??` 목록 | "COMPLETE"가 미커밋 로컬 상태에 의존. 다른 체크아웃/CI/타 에이전트는 재현 불가 | 사용자 승인 후 일괄 커밋(원자적, 매니페스트 포함 파일 전부) |
| C-02 | CONFLICT / RFA | `CURRENT/TAKY_ALPHA_CURRENT_2026-10-03.json` 내용이 `CURRENT/TAKY/TAKY_ALPHA_2026-10-03.json`과 동일(`checkpoint_hash` 동일). **정정(재검증)**: 최신 HANDOFF 3종(NEW_CHAT_START/FINAL/LOCAL_COMPLETION)은 네임스페이스본만 참조하나, 플랫본은 `.claude/` 리뷰 프롬프트·로그와 `ENFORCEMENT/beta_validation_2026_10_03/baseline.json`(sha256 `8d3c2765…`)에 여전히 참조됨 → "참조 0건"은 오류. 삭제 시 이들 증거의 경로가 끊김 | 정본 경로 2개 = 소유 모호. `CURRENT/*_CURRENT_*.json` 구(舊) 명명 규칙과 `CURRENT/<namespace>/` 신 규칙 혼재 | 플랫본을 권위에서 제외(삭제 대신 HISTORY 이동 후보). 체크포인트 가드가 어느 경로를 기대하는지 `execution_checkpoint.py`로 확인 필요(UNVERIFIED) |
| C-03 | CONFLICT | `TAKY.md` "Before explicit user finalization, all MASTER/…/APP remain REV_00" vs `PROJECTS/GUIDE_CORE6_CHARACTER.md` "Status: REV_01" | 개정 거버넌스와 직접 충돌. 사용자 확정 여부 증거는 파일 내에 없음 | 사용자에게 REV_01 확정 사실 확인(예/아니오 1건) 후 라벨 정정 또는 근거 링크 |
| C-04 | CONFLICT | `STATE.md`: Ready main `6142cfeb…`(2026-09-20) / `OS/MOBILE_APP_DEVELOPMENT_REGISTRY.json`: Ready main `488bb6aa…`(LIVE_REFRESHED_2026-09-21) | 두 정본 표면이 서로 다른 main SHA 주장. 모두 스냅샷 | 둘 다 STALE 처리, 라이브 GitHub 조회(`gh`)로 단일화 후 한 owner만 유지 |
| C-05 | CONFLICT | `STATE.md` "P0 open issue #2 …", "role/action/owner classification trust source: UNVERIFIED" vs Alpha "local work complete / external dependencies only" | Alpha 완료 선언이 STATE의 미해결 루트 이슈 5건을 닫았는지 근거 없음. 일부는 외부 경계로 재분류, 일부(3번 validation-only 진행 차단, 4번 resume 증거)는 별도 증거 없이 암묵 종결처럼 읽힘 | 5건 각각에 disposition(CLOSED+증거 / EXTERNAL / OPEN) 부여 |
| C-06 | AMBIGUITY | `HANDOFF/`에 `*_LATEST.md` 7종 + Alpha DRAFT/FINAL/COMPLETION/PREAUDIT/HOOK_PATCH/LATEST 6종 | "LATEST"가 파일명 규칙일 뿐 단일 해석자가 없음. `BADGE_VISUAL_BINDING…LATEST`는 파일 내부에 "LATEST RESUME OVERRIDE" 블록이 12회 적층 | `HANDOFF`는 "회복 증거"로 격하 유지, 도메인별 단일 CURRENT 포인터만 resume 입구로 지정 |
| C-07 | AMBIGUITY | `CURRENT/` 루트: BADGE_*, DESIGN_UI_*, LEARNING_ENGINE_* (플랫, 2026-09-2x) + `CURRENT/DATA/` + `CURRENT/TAKY/` | 네임스페이스 규칙(`CURRENT/<ns>/`)이 TAKY만 적용. 나머지는 플랫 | Beta에서 네임스페이스 규약 단일화(이동은 별도 승인 계획, 이번 감사 범위 밖) |
| C-08 | STALE | `ACTIVE_RULE_PROFILE.md` `SOURCE_CANONICAL_HEAD 6c630a0…`, `PROFILE_VERSION 2026-09-20.5` | 파생 투영이 현재 HEAD와 무관. 파일은 이번에 수정됐으나 head 포인터 미갱신 | 투영 재생성 시 HEAD 바인딩 자동화(수동 편집 금지) |

## 3. Alpha 증거 신뢰도 / CLOSED-but-unverified

| ID | 분류 | 주장 | 이번 감사에서의 상태 |
|---|---|---|---|
| V-01 | UNVERIFIED | unittest 110/110, hook regression 20/20, manifest 32/32, rule lint 24 rules | 재실행 BLOCKED. 로그 사본은 `.claude/*.log`로 존재하나 이는 과거 실행 출력이며 현재 작업트리 리비전에 대한 증거가 아니다(리비전 바인딩 규칙 위반 위험: 매니페스트 `.6→.7→.8` 사이에 파일이 바뀜) |
| V-02 | STALE | CURRENT Alpha checks "alpha_manifest_validator 32/32 (manifest .6)" | 매니페스트는 `.8`로 갱신됨. CURRENT 체크포인트가 `.6` 기준 증거를 여전히 달고 있음 → 후속 변경이 이전 PASS를 상속(`Never let a later edit inherit an earlier PASS` 위반 후보) |
| V-03 | CONFLICT | `checkpoint_hash sha256:1d556ece…`(Alpha)가 가드 PASS로 보고됨 | 해시 대상 시점은 17:57 / 매니페스트 `.8` 및 후속 파일은 18:47~18:59. 해시가 최종 내용을 덮는지 미확인 |
| V-04 | OPEN | "Codex independent audit … P1 RESOLVED" | 근거는 `.claude/TAKY_ALPHA_P1_RECHECK_CODEX_*.log`(미추적, 로그). 독립 리뷰의 아티팩트/리비전 해시 바인딩 증거 없음 |
| V-05 | KEEP | 표현 규율: LOCAL_ALPHA_READY ≠ pushed/merged/deployed/호스트 가로채기 검증/신원 증명 | 올바른 클레임 경계. 유지 |
| V-06 | UNVERIFIED | 대표 과제 PASS(AutoCAD/Excel/HWP/PPT, delta=0) | 증거 경로가 `D:/Git PWA/TAKY_AUDIT_LOCAL/…` — 저장소 밖, 이번 감사에서 접근 불가. 레인 한정 PASS로만 취급(체크포인트 자체 `corrections`와 일치) |
| V-07 | OPEN | Alpha FINAL/COMPLETION의 "manifest .7" | 현재 `.8`. 문서 2종이 STALE이므로 최신 해석자는 `TAKY_ALPHA_NEW_CHAT_START…LATEST`뿐 |

## 4. 런타임 / UI / 데이터 / 에셋 연결 (레지스트리·메모리 단서 기반, 라이브 미검증)

출처 구분: 레지스트리(`OS/MOBILE_APP_DEVELOPMENT_REGISTRY.json`, 2026-09-21.3)는 저장소에서 직접 읽음. "메모리 단서"는 claude-mem 요약(라우팅 보조, 권위 아님)이며 **라이브 파일로 재확인 전까지 UNVERIFIED**.

| ID | 분류 | 내용 | 근거 |
|---|---|---|---|
| R-01 | STALE | Ready-Set / Snap-Pop / Hide-Seek / TAKY-MOBILE 모두 `DEPLOYED_STALE`, 배포 커밋 ≠ main | 레지스트리 L72/315/368/430 (VERIFIED as of 2026-09-21) |
| R-02 | UNVERIFIED | 세 앱이 feature 브랜치에서 main과 크게 분기, 미커밋 변경 존재 | 메모리 단서 #58 |
| R-03 | UNVERIFIED | `outbox`가 sessionStorage에 쌓이나 flush 소비자 미발견 → 앱 간 피드백 경로 단절 가능 | 메모리 단서 #54 |
| R-04 | UNVERIFIED | Ready&Set origin 허용 목록이 localhost/Cloudflare 터널만 허용 → Netlify 프로덕션 도메인에서 postMessage 브리지 거부 가능 | 메모리 단서 #52 |
| R-05 | UNVERIFIED | Snap&Pop에 서비스워커 2종(캐시 버전 상이), 등록 대상 불명 | 메모리 단서 #53 |
| R-06 | UNVERIFIED | 공용 런타임 기반(`SHARED/runtime`)은 테스트 PASS하나 앱들이 import하지 않음 | 메모리 단서 #39, #45 |
| R-07 | UNVERIFIED | 인증: 이전 테스트가 신선한 원격 인증이 아닌 재사용 로컬 응답 | 메모리 단서 #47 |
| R-08 | KEEP | Core 6: 3시트 생산 패키지 HARD LOCK(TURNAROUND/EXPRESSION/ACTION), 시트 승인 ≠ 런타임 크롭 승인, 생산은 HOLD | `PROJECTS/GUIDE_CORE6_CHARACTER.md` (VERIFIED, 직접 읽음) |
| R-09 | OPEN | 에셋 연결: `TKY-ASSET-001`은 원본 에셋을 `TAKY-ASSETS`에 두고 앱은 pinned manifest 보유. Core 6 시트 파일의 실제 위치/해시/매니페스트 존재는 이번에 확인 못 함 | `STATE.md`, 레지스트리 TAKY-ASSETS `8d902a93…` (스냅샷) |
| R-10 | STALE | 레지스트리 `registry_version 2026-09-21.3` 이후 12일 경과, 레지스트리 자체 불변식 "REGISTRY_SNAPSHOT != LIVE_CURRENT_STATE" | 레지스트리 L22 |

## 5. 외부 경계 / 비용·배포 안전

| ID | 분류 | 내용 |
|---|---|---|
| X-01 | KEEP | 인증된 계정 세션 ≠ 인증된 인간 신원; 저장소 집행 PASS ≠ 호스트 자동 가로채기 PASS. `EXTERNAL_DEPENDENCY`로 분리 (체크포인트 `TAKY_EXTERNAL_BOUNDARY`) |
| X-02 | KEEP | push/merge/deploy/유료 API는 명시 승인 필요; 승인 증거는 `BOUND_RECORD_ONLY, identity_authenticated=false` |
| X-03 | OPEN | Scenario MCP(유료 생성) 연결 존재. 인벤토리/게이트는 Alpha 문서가 주장하나 `.mcp.json`·`settings.json` 재확인 불가 → 비용 행동 게이트는 UNVERIFIED |
| X-04 | OPEN | `.mcp.json`, `.claude/settings*.json`이 정본 표면(보호 대상)이면서 미추적. 버전 고정(Playwright 0.0.83 / DevTools 1.10.1) 주장은 재검증 필요 |
| X-05 | KEEP | NotebookLM = LEGACY_OPTIONAL / 기본 OFF (`TKY-NBLM-001`), 규칙 ID 레지스트리 존재 확인 |
| X-06 | OPEN | Netlify·Notion MCP는 이번 세션에서 미인증. 배포 상태 라이브 검증 불가(= 인증 필요, 비실패) |
| X-07 | FIX | 반복 실패 지문 `RUNTIME:PowerShell:npm[e377b12a…]`: 동일 경로 재시도 금지. 이번 세션에서 npm 미사용 |

## 6. 정리 후보 (REMOVE-FROM-AUTHORITY 포함)

| 대상 | 판정 | 사유 |
|---|---|---|
| `CURRENT/TAKY_ALPHA_CURRENT_2026-10-03.json` | RFA | C-02 중복 |
| `CLAUDE.md.20261003_001449.ko.bak`, `…002205.ko-ui.bak` | RFA (삭제 아님) | 백업 사본이 루트에 미추적으로 존재. 권위 오독 위험. 소스는 복구 가능하게 HISTORY로 이관 후보 |
| `TOOLS/*.bak*`, `TAKY_SETUP_CHECK.ps1.taky_backup_20261002` 등 | RFA | 동일 사유 |
| `HANDOFF/TAKY_ALPHA_DRAFT / PREAUDIT / HOOK_PATCH_CANDIDATE` | KEEP as evidence | 이력 증거. 정본 아님을 명시 |
| `HANDOFF/TAKY_ALPHA_FINAL / LOCAL_COMPLETION` | STALE | 매니페스트 `.7` 기재 |
| `ENFORCEMENT/__pycache__/`, `TOOLS/__pycache__/` | REMOVE(커밋 제외) | 생성물, `.gitignore` 부재(루트에 `.gitignore` 없음 — 확인됨) |
| `skills-lock.json`, `REFERENCE/CLAUDE_SKILLS` | UNVERIFIED | 출처/버전 고정 정책 미확인 |

## 7. Beta 통합 전 우선순위 (제안, 미실행)

P0 (사용자 결정 필요, 외부 전이 아님):
1. Alpha 산출물 원자적 커밋 범위 결정(승인 후에만). 커밋 전 검증기 일괄 재실행(`python` 권한 허용 필요).
2. `CURRENT` 경로 단일화: C-02 판정.
3. C-03 REV 라벨 확인 질의 1건.

P1 (로컬, 승인 불필요한 후보 작업):
4. `STATE.md` 델타 + `SESSION_DELTA_LOG.md` 항목을 **거버넌스 후보**로 제출(직접 승격 금지).
5. 매니페스트 버전 포인터 단일 해석자 정의 + FINAL/COMPLETION에 STALE 표지.
6. 레지스트리 라이브 갱신(`gh` 조회) — 앱 저장소 접근 권한 필요.

P2 (앱 런타임, 라이브 증거 필요):
7. R-03/R-04/R-05/R-06 각각 실제 파일로 재현 확인 후 FIX/KEEP 확정.

## 8. 독립 교차검토 필요 지점

`AUTHOR != SOLE REVIEWER`. 이 감사를 만든 것은 Claude 단독이므로, 승격 전에 `TOOLS/TAKY_MODEL_REVIEW.ps1`을 통한 Codex/Gemini 검토 1회를 권고(구독/로컬 경로만, API 키 폴백 금지). 이 파일의 해시는 검토 시점에 바인딩할 것.

## 9. 공격적 검증 실패 모드 — 방어 응답표

| # | 실패 모드 | 이번 감사 관측 | 방어 응답 (탐지 → 조치) | 게이트/소유자 |
|---|---|---|---|---|
| F1 | 미커밋 상태를 "정본 완료"로 주장 | Alpha COMPLETE vs HEAD 부재 | `git status` 미추적 목록을 완료 선언의 필수 입력으로 요구; 미추적 정본 파일 존재 시 `COMPLETE`를 `LOCAL_UNCOMMITTED`로 강등 | checkpoint 가드(신규 후보) |
| F2 | 이후 편집이 이전 PASS를 상속 | 매니페스트 .6→.8, CURRENT는 .6 체크 보유 | 체크 항목마다 대상 파일 sha256/매니페스트 버전 바인딩; 불일치 시 해당 PASS 무효 | `alpha_manifest_validator` 확장 후보 |
| F3 | 동일 사실의 정본 중복(플랫 vs 네임스페이스) | C-02 | `CURRENT` 내 동일 `task_id`/`checkpoint_hash` 중복 탐지 → 하나만 소유자로, 나머지 RFA | CURRENT 린트 후보 |
| F4 | LATEST 이름이 최신을 보장하지 않음 | C-06 (7종 + 적층 OVERRIDE) | 도메인당 단일 포인터 파일 + 포인터가 가리키는 해시 검증; `LATEST` 문자열은 권위 아님 | HANDOFF 프로토콜 |
| F5 | 문서 간 버전 표류 | .6/.7/.8 | 버전 문자열을 매니페스트에서만 파생; 문서는 참조만(복제 금지) | Alpha 매니페스트 |
| F6 | 정본 상태 표면 미갱신 | STATE.md, SESSION_DELTA_LOG | 에피소드 종료 시 "STATE 델타 또는 NO_STATE_DELTA 사유" 필수 | STATE 갱신 규칙 |
| F7 | 접근 실패를 부재/PASS로 오독 | python·형제 저장소 BLOCKED | 상태 `BLOCKED`로 기록, 증거 레벨 상한 고정, 임의 PASS 금지; 권한 요청 1건으로 해소 | `ACCESS FAILURE != SOURCE ABSENCE` |
| F8 | 로그 존재를 검증으로 취급 | `.claude/*.log` | 로그 = 과거 증거; 현재 리비전 재실행 또는 해시 바인딩 없으면 UNVERIFIED | EXECUTION TRUTHFULNESS |
| F9 | 저장소 밖 증거 의존 | `TAKY_AUDIT_LOCAL` | 외부 경로 증거는 매니페스트 해시를 `HISTORY`에 복사본으로 고정; 아니면 레인 한정 | 증거 이식성 |
| F10 | 레지스트리 스냅샷이 라이브로 오인됨 | 12일 경과 `.3` | 휘발성 필드에 `verified_at` 만료(예: 7일) 후 자동 STALE | 모바일 레지스트리 불변식 |
| F11 | 개정 라벨 임의 승격 | REV_01 vs REV_00 | REV 변경은 사용자 확정 증거 링크 필수; 없으면 라벨 거부 | 개정 거버넌스 |
| F12 | 비용 행동(Scenario 유료) 우회 | X-03 | 훅 회귀 케이스 + `.mcp.json` 정적 검사; 승인 기록은 `BOUND_RECORD_ONLY`로 신원 주장 금지 | AI 연결 보안 |
| F13 | 보호 표면 셸 쓰기 우회 | 이번에도 보호 게이트가 해시/읽기를 차단(정상 동작 관측) | 게이트 차단 시 도구 경로 전환(Read/Grep), 동일 명령 3회 재시도 금지 | anti-loop ladder |
| F14 | 독립 리뷰 부재/비바인딩 | V-04 | 리뷰 결과에 대상 아티팩트 sha256 포함, 변경 시 무효 | cross-model-review |
| F15 | CI가 미추적 파일에 의존 | C-01/§1-6 | 커밋 전 깨끗한 워크트리/클론에서 CI 동등 검증 | CI 재현 |
| F16 | 앱 간 이벤트가 소비되지 않음(사일런트 실패) | R-03 (UNVERIFIED) | outbox 소비/flush E2E 프로브 + 실패 시 가시 신호 | runtime-e2e |
| F17 | 프로덕션 오리진 차단(환경별 허용 목록) | R-04 (UNVERIFIED) | 허용 오리진을 환경 설정 + 배포 시점 프로브 | 앱 계약 |
| F18 | 에셋 "존재" 가정(이미지/ZIP만으로 완료) | R-09 | `TKY-ASSET-001`: 업로드 + pinned manifest + 배포 복사본 해시 일치 확인 | TAKY-ASSETS |
| F19 | 정본 신규 발견의 직접 승격 | 이 감사 자체 | 이 파일은 CANDIDATE 증거; CURRENT 반영은 governed promotion만 | Knowledge flow |
| F20 | 사용자를 디버거로 만듦 | 권한 필요 항목 | 사용자에게는 "python 실행 허용 + `D:\Git PWA` 읽기 허용" 단일 액션만 요청 | USER != DEBUGGER |

## 9A. 누락 보정 — 동일 날짜 Beta 코드 트랙 증거 (재검증으로 추가)

출처: `ENFORCEMENT/beta_validation_2026_10_03/REPORT.md` (미추적, 읽기 완료). 과제 `TAKY-BETA-CODE-2026-10-03`, HEAD `fee09fa`. 자체 결론: "overall suite is **not green**, TAKY_PASS 미주장". 이 문서는 이 감사 §3의 Alpha 수치(110/110)와 **직접 충돌**한다.

| ID | 분류 | 내용 |
|---|---|---|
| B-01 | CONFLICT | Alpha 완료 문서: unittest 110/110. Beta 트랙 베이스라인: 133개 로컬 명령 중 **25개 비정상 종료**. 두 주장은 환경(임시 디렉터리 권한) 또는 범위가 다르며, 어느 쪽도 현재 리비전의 단일 정본이 아님 → Alpha "COMPLETE" 상향 금지, UNVERIFIED 유지 |
| B-02 | OPEN | 16개 Python 테스트가 `tempfile.TemporaryDirectory`에서 WinError 5(권한)로 실행 불가(TEMP를 작업 디렉터리로 돌려도 재현). 해당 16개의 통합 결과는 **미검증**. 테스트 약화·ACL 변경 없음(올바른 처리) |
| B-03 | OPEN | BADGE JS 7개 실패, 대표 케이스에서 `fs.fsyncSync` EPERM 재현. 나머지 6개의 동일 원인은 미증명. 내구성 보장을 바꿀 수 있어 폴백 미선택 → **사람 결정 필요** |
| B-04 | FIX/CONFLICT | `evidence_bridge_regression.py`: 증거 seed 기대 해시 `d8e0e35d…` vs 로컬 CRLF 바이트 `26caecc5…`(LF 변환 시 일치). 원시 바이트 검증이 올바르게 거부 중. `.gitattributes`/정규화 정책 부재가 원인 후보(루트 `.gitignore`도 없음) → 정책 결정 필요 |
| B-05 | OPEN | `handoff_bundle_validator` 기대-양성 fixture(`handoff_bundle_pass`)가 선언 해시/resume 상태 바인딩에서 거부됨. 즉 handoff 무결성 검증기의 PASS 경로가 현재 체크아웃에서 입증되지 않음. 증거 재생성 금지 상태 유지 |
| B-06 | KEEP | 검증기 우회 2건 수정과 회귀 11건: (a) `evidence_ref_validator`의 `HISTORY/../TAKY.md` 접두사 우회, (b) `execution_checkpoint`가 task_id/namespace를 안 묶어 올바른 해시의 타 과제 레코드가 통과. 수정 전 7개 실패 → 후 11/11 통과로 보고. 이는 이 감사의 F-13 계열(검증 우회) 실사례이며 **보고서가 로그를 보존**(`regression_before.json` 등). 단 CI 워크플로에는 새 테스트 2종이 **연결되지 않음**(보고서 §6) → 회귀 방지 미완 |
| B-07 | OPEN | 새 회귀 테스트 `evidence_history_boundary_test.py`, `execution_checkpoint_identity_test.py`는 독립 스크립트이며 CI 미배선 → 다음 변경 시 우회가 재발해도 CI가 못 잡음 |
| B-08 | UNVERIFIED | 런타임/UI/데이터/에셋 연결은 로컬 테스트(3앱 캐릭터 런타임, 로컬 에셋 HTTP)로만 근거. 실제 브라우저·모바일 기기·원격 런타임 검증 없음 → §4의 R-항목 상태 변경 없음 |

보정된 결론: Alpha 문서의 "로컬 완료"는 같은 날짜 독립 트랙의 베이스라인과 합치되지 않는다. Beta 진입 기준 수치는 어느 한쪽이 아니라 **동일 리비전에서 재실행한 단일 결과**여야 한다(§11 증거 1번).

## 10. 이번 감사가 실제로 한 일 / 하지 않은 일

한 일: 저장소 상태 읽기, TAKY.md / STATE.md / ACTIVE_RULE_PROFILE / CURRENT 4파일 / HANDOFF 6파일 / 모바일 레지스트리 / Core 6 문서 / CI 워크플로 grep 비교.
하지 않은 일: 검증기 실행, 해시 재계산, 형제 앱 파일 열람, 원격 조회, 정본 수정, 커밋. 위 4개 BLOCKED는 권한이 풀리면 같은 감사를 이어서 UNVERIFIED → 확정으로 전환할 수 있다.
재검증 패스(이 파일 갱신 시): Grep/Read로 매니페스트 버전 분포(7개 파일에 `2026-10-03.N` 각 1회), `ACTIVE_RULE_PROFILE` HEAD 포인터(`6c630a0…` 확인), 체크포인트 경로 참조(C-02 정정), `beta_validation_2026_10_03/REPORT.md` 읽기를 수행. 셸 명령은 보호 표면 게이트가 비읽기 전용으로 판정해 차단(재시도 안 함, 도구 경로로 전환). 쓰기 대상은 이 파일 1개뿐.

## 11. 최종 요약

### 11.1 Beta 전 차단 요소 (BLOCKERS)
1. **단일 리비전 검증 결과 부재** — Alpha 110/110 vs Beta 트랙 25/133 비정상(B-01), 16개 테스트는 임시 디렉터리 권한으로 실행 불가(B-02). 이 상태로 Beta 기준선을 못 잡는다.
2. **정본이 미커밋** — HEAD에 Alpha 산출물·`CLAUDE.md`·`.mcp.json`·`.claude/**` 없음(C-01). 깨끗한 체크아웃 CI는 실패 구조(§1-6, 예측).
3. **버전·경로 이중화** — 매니페스트 `.6/.7/.8` 표류(V-02/V-07), 체크포인트 플랫/네임스페이스 이중(C-02).
4. **검증 우회 회귀 미배선** — 수정은 됐으나 새 테스트 2종 CI 미연결(B-07).
5. **handoff 무결성 검증기 PASS 경로 미입증**(B-05)과 **증거 seed 해시 정책 부재**(B-04).
6. **STATE.md / SESSION_DELTA_LOG 미갱신**(C-05, 요약 4) — 루트 이슈 5건 disposition 없음.

### 11.2 안전한 수정 (승인 불필요, 로컬, 정본 미수정 — 후보로만)
- 이 감사 파일을 기준으로 STATE/SESSION_DELTA 델타 **후보 문서** 작성(직접 반영 금지).
- FINAL/LOCAL_COMPLETION 문서에 STALE 표지 후보 제안서 작성.
- `ACTIVE_RULE_PROFILE`의 HEAD 포인터는 수동 편집하지 말고 투영 재생성 경로로만 갱신.
- 새 회귀 테스트 2종의 CI 배선 **패치 제안서**(적용은 별도 승인; 워크플로는 보호 표면).
- 루트 `.gitignore`(`__pycache__`, `*.bak`, `tmp/`) 및 줄바꿈 정책(`.gitattributes`) **제안서**.

### 11.3 사람 승인이 필요한 결정
1. Alpha 산출물의 원자적 **커밋 범위/시점**(커밋은 이번 범위 밖, 승인 필요).
2. 체크포인트 정본 경로: `CURRENT/TAKY/` 채택 및 플랫본 처리(C-02; baseline.json 등 증거 경로 영향 있음).
3. Core 6 `REV_01` 라벨: 사용자 확정 사실 여부(C-03, 예/아니오 1건).
4. CRLF/LF 정책 → evidence seed 해시 기대값을 바꿀지 바이트 정책을 바꿀지(B-04).
5. BADGE `fsync` EPERM: 내구성 폴백 허용 여부 vs Windows 한정 환경 제외(B-03).
6. 임시 디렉터리 권한(WinError 5) 해소 방식 — ACL 변경은 환경 변경이므로 승인 필요(B-02).
7. 형제 앱 저장소(`D:\Git PWA` 상위) 읽기 허용 및 `python` 실행 허용(감사 확정 전환용).
8. 독립 교차검토(Codex/Gemini, 구독·로컬 경로만) 실행 여부.

### 11.4 필요한 정확한 증거/테스트 (닫는 기준)
1. 동일 HEAD+작업트리 해시에서 **전체 enforcement 일괄 1회 재실행** 결과 JSON: `alpha_manifest_validator`(.8, 32/32), `rule_registry_lint`, `mobile_app_development_registry_validator`, `master_surface_integrity_validator`, `claude_hook_regression`, `outcome_hook_regression`(`PYTHONUTF8=1`), `unittest discover`; 각 항목에 argv/exit/stdout, 실행 시점 `git status` 해시 첨부. 25개 비정상은 항목별 원인 분류(환경 vs 코드).
2. 임시 디렉터리 해소 후 16개 테스트 재실행 결과, 또는 해소 불가 시 `ENVIRONMENT_BLOCKED` 공식 기록.
3. 깨끗한 클론/워크트리(커밋 전 후보 브랜치)에서 CI 동등 명령 실행 → 미추적 의존 파일 0건 입증.
4. C-02: `execution_checkpoint.py`가 기대하는 CURRENT 경로 확인 + 플랫본 제거 전후 `baseline.json`/가드 재실행.
5. C-04/R-10: `gh api`로 각 앱 저장소 main SHA·배포 SHA 라이브 조회 → 단일 owner 갱신 후 `verified_at`.
6. R-03/R-04/R-05/R-06: 실제 브라우저(playwright)로 outbox flush, 프로덕션 오리진 postMessage, 서비스워커 등록 대상, `SHARED/runtime` import 여부 재현 스크린샷/DOM/네트워크 로그.
7. X-03/F12: `.mcp.json`·`settings*.json` 정적 검사 + Scenario 유료 호출이 승인 없이 차단되는 훅 회귀 케이스.
8. 독립 리뷰 결과에 이 파일의 sha256을 바인딩(파일 변경 시 무효).
9. R-09/F18: Core 6 시트의 TAKY-ASSETS 업로드 + pinned manifest + 앱 복사본 해시 일치.
