# TAKY Site Watch / AI harness — 근거 기반 종합 비교 검토

> **FAIL / NOT ACCEPTED FOR USER-REQUESTED ORDER** — 사용자 요구 `외부 자료 독립 분석 → 사례 비교 → 최적안 독립 도출 → 마지막에 TAKY 비교`의 순서를 뒤집고 TAKY를 먼저 기준으로 삼은 기록. 이 보고서의 "최적안"은 독립 최적안으로 승인하지 않는다. 실패 사건: `HISTORY/2026-11-06_REVIEW_ORDER_INVERSION_FAILURE_CASE.md`, 회귀 사례 `F-07`. 기존 원문 증거는 삭제하지 않고 이력으로 보존.

- 검토일: 2026-11-06 KST
- 상태: **EVIDENCE-BASED COMPARATIVE REVIEW / CANDIDATE**, 승인된 MASTER·CURRENT 변경이나 구현·배포 PASS가 아님
- 범위: 실제 로그인된 인스타그램 게시물 9건, TAKY Source Vault 상태·제어 프로토콜, YKH 회사 업무 사례 27건 및 실사, Anthropic/OpenAI/McNeel/AutoCAD MCP/LangGraph/Temporal 공개 구현·문제 사례
- 목적: 기존 원본의 단일 권위와 실행 연속성을 보존하면서, 마이닝→인덱싱→적용→실증의 **실제 성과를 높이는 최소 변경**을 결정
- 권위: `MASTER/MASTER_LOGIC.md`, `MASTER/REVIEW_DEFAULT_MINING_PROTOCOL.md`, `MASTER/FORMING_PROTOCOL.md`, `MASTER/AI_COLLABORATION_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`, `STATE.md`. 본 문서는 HISTORY 증거이며 권위를 재정의하지 않는다.

## 1. 입력 증거 및 신뢰 경계

### TAKY 현황 — 로컬 실행 증거
| 항목 | 2026-11-06 관측 | 해석 / 제한 |
|---|---|---|
| Site Watch 등록 | 13개 (디지트 Notion, lazyowen, sdk-kim, trendcore 포함) | 사이트 등록이지 게시물 원문 확보/실제 활용 증거 아님 |
| Aside 인스타그램 | `@digit.tv`, `@lazy_owen`, `@sdk.kim.builds` 팔로잉 확인, 계정당 3건, **9/9 게시물 본문·원문 URL·SHA-256 검증** | `D:\Git PWA\TAKY-SOURCE-VAULT\reports\site_watch\ASIDE_INSTAGRAM_CAPTION_SOURCE_20261106.json`; 출처 연결된 후보 증거이며 RAW 원본/화면 전체 보존 및 인덱싱 완료는 아님 |
| 이번 9개 URL의 기존 인덱스 검토 목록 직접 일치 | **0/9** | `SITE_WATCH_TAKY_DATA_REVIEW_CANDIDATES_CURRENT.json`의 466건과 대조. 게시물이 해당 파이프라인에 아직 반영되지 않았음을 확인 |
| 와칭 로컬 검색 후보 | 466개 | NON_AUTHORITATIVE, Index Owner 수락 0, Forming 승인 0, Learning 소비 0 |
| 기계적 증거 채굴 | 145개 소스, 18,279 evidence units | DERIVED_EVIDENCE_ONLY. 채굴량은 의미 학습의 완료 수치가 아님 |
| 원격 의미 마이닝 | `HOLD_PROVIDER_AUTHORIZATION_REQUIRED`, Claude subscription 403 `oauth_not_allowed_for_organization` | 비용/계정 정책상 임의 우회 금지. 예약 실행 코드만 성공이라고 처리하는 버그는 이미 수정하여 차단 시 exit 2 실증 |
| Notion 델타 | 236 자료, retained queue 239, blocks read 0, 새 delta 0 | 읽기 전용 컨테이너 수집만 성공. 학습 파이프라인은 별도 |
| 로컬 12시간 수집 | PIL 폴더명 교정 후 이미지 생성/축소/저장 단위시험 PASS | 12시간 수집 전체 통합 재실행 PASS는 미확보 |

### YKH 회사 업무 사례 — 비공개 업무 분리
- 기존 `WORKBENCH/REVIEW_CASES.json` 27건: `REVIEWED` 16, `PARTIAL_SOURCE` 6, `NOT_SECURED` 5; 반영 `PARTIAL` 3, `NOT_REFLECTED` 24. 이는 **YKH의 별도 검토대장 상태**이며 TAKY 전체 성과로 합산하지 않는다.
- 양 PC에 Codex 연계 플러그인 설치/인증 확인, 렌더 YKH 스킬 5·에이전트 2 복제 해시 9/9 PASS. 임시 20㎡ DXF 50mm 격자 검사 PASS. 실제 DWG/모델·동일 REV 확보, Claude→Codex→수정→최종 소비 통합 실행은 미검증.
- 메인은 AutoCAD 2024·Office 최종 원본 검수, 렌더는 Claude Code/Codex·대형 분석/코딩·DXF 임시 검산. 렌더 Rhino 7, 공식 RhinoAI MCP는 Rhino 8 이상이므로 미설치. 실제 원본이 없는 렌더에 구현·시험 성공을 주장하지 않는다.
- 인스타그램 인증된 Aside 접근은 **메인 PC 한정**; 렌더/공개 SMB에 세션·개인 자료·인증정보를 옮기지 않는다.

## 2. 실제 게시물 9건의 적용성 판정

| 사례/원문 | 발견 내용 | TAKY 현행과 중복/차이 | 최적 처분 |
|---|---|---|---|
| 김스득 [업무별 스킬 우선](https://www.instagram.com/p/DerPUzhzDH5/) | 실행자는 적게, 업무별 스킬·완료 기준은 명확히 | `MASTER_LOGIC` 최소 복잡도, `AI_COLLABORATION_PROTOCOL` 이미 채택. CLAUDE.md 과부하와 실제 스킬 호출 확인 부족 | **ADJUST**: 기존 스킬의 발동·수용 테스트 강화. 범용 에이전트 신설 금지. 독립 검수 역할은 유지 |
| 김스득 [Claude-Mem](https://www.instagram.com/p/DfV6kMYirUU/) | 자동 세션 기록·검색·복원 | 양 PC 플러그인 기존 설치, 렌더 Bun 의존성 결손. TAKY CURRENT와 별도 기억이 생길 위험 | **VERIFY_EXISTING**: 별도 기억은 검색 보조 자료로만 사용, 권위/보존/비용 확인 전 추가 자동 활성화 보류 |
| 김스득 [PPT Master](https://www.instagram.com/p/DfGd0Twit7K/) | 개별 수정 가능한 PPTX 소개 | 기존 엑셀/PPT 자동화 요구 있으나 해당 저장소·라이선스·PPT 구성요소 편집성 실제 확인 없음 | **HOLD / VERIFY_REPO**: 임시 PPTX 1장 텍스트·도형·표 수정 및 Office 재열기 테스트 전 설치 금지 |
| 게으른 빌더 [Claude 법정 12인 배심원](https://www.instagram.com/p/DeeH-bVMldM/) | 여러 모델/에이전트가 주장 비교 | 기존 Codex 독립 검증 및 비용 절감 정책과 중복 | **HOLD**: 재현 가능한 개선 지표 없으면 불필요한 다중 호출 |
| 게으른 빌더 [2일 Claude 설정](https://www.instagram.com/p/DfJ_No7M7cB/) | 프로젝트·MCP·스킬·메모리 기본 구성 | 현재 이미 대부분 구축 | **REUSE**: 비어 있는 기능만 확인하고 중복 셋업 금지 |
| 게으른 빌더 [10종 플러그인](https://www.instagram.com/p/De_qY6Tz_KN/) | DM 가이드 홍보, 구성품 미기재 | 정확한 목록·권한·유지보수·안전성/증거 없음 | **HOLD**: 일괄 설치 금지 |
| 디지트 [AI 건축 모델링 지시서](https://www.instagram.com/p/DfGrHJ9gaAw/) | 목표·조건·단계·규칙·검수·보고·제한, 차이 근거를 이용해 수정 | TAKY TASK CONTRACT 및 VERIFY/CORRECT에 이미 원리 존재. 건축 의미·샘플 정합은 YKH 도메인 권위 | **ADJUST**: YKH 개별 도면 작업 계약과 검수 예제로 사용. TAKY 글로벌 규칙을 중복 작성하지 않음 |
| 디지트 [축척별 도면 표현](https://www.instagram.com/p/DfWEljrAR9j/) | 1/500·1/200·1/100·1/50·1/20 표현 | CAD 표현 체크 참고 가능. 인용한 협회 2006 지침은 법령이 아님 | **HOLD_DOMAIN_VERIFICATION**: 기존 샘플 DWG 및 공식 원문과 비교 |
| 디지트 [계단 배치/면적](https://www.instagram.com/p/DfYpYo4gfVJ/) | 5개 계단 유형, 치수/면적 산술 예제 | 175×16=2800mm; 직선형 4840×1200=5.808㎡, ㄷ형 바운딩박스 3020×2400=7.248㎡는 산술 확인. 실제 요구 조건·형태면적·현행 법규는 별도 | **HOLD_DOMAIN_VERIFICATION**: YKH 공간 구획/검산의 테스트 후보, 법규 기준으로 바로 채택 금지 |

### 한계
- 캡션은 실물 UI에서 확인해 해시로 보존했으나 플랫폼 원본 HTML·이미지/영상·DM 수신 가이드의 원본 파일은 확보하지 않았다. TAKY `REVIEW_DEFAULT_MINING_PROTOCOL`의 **RAW_FULL_PRESERVATION = UNVERIFIED**, 마이닝 후보는 `SOURCE_BOUND_PRELIMINARY_TRIAGE`. 마이닝 COMPLETE/학습 적용 PASS로 승격 금지.
- 게시물 작성자의 조회수·별점·성능·시공/법규 주장 자체가 독립적으로 확인된 것이 아니다.

## 3. 외부 실제 구현/실패 사례와 검증 가능한 시사점

| 공개 기술 원본 | 재현 가능한 핵심 | TAKY 적용 |
|---|---|---|
| Anthropic [Building effective agents](https://www.anthropic.com/research/building-effective-agents) | 복잡도와 비용 증가 전, 단순하고 조합 가능한 워크플로 선택 | 이미 GRAND MASTER의 `DETERMINISTIC → SINGLE → ... → MULTI`에 있음. **새 엔진 불필요** |
| Anthropic [2026-10-22 subagents consolidation](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) | 여러 실제 기업에서 스킬·소수 도구로 축소 시 품질/지연 개선; 단, 통합 전 10개 골든 E2E 과제로 회귀 비교, 특정 실행/독립검증엔 서브에이전트 유지 | 문서 통합보다 **업무별 실제 실행 평가셋**이 공백. Claude 주 실행·Codex 독립 검증은 무작정 제거하지 않음 |
| Anthropic [Skills vs Projects/MCP/Subagents](https://claude.com/resources/articles/skills-explained) 및 [Claude customization](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more) | CLAUDE.md=상시 정체/소스, Skills=요청별 절차, Hooks=결정적 실행 이벤트, Subagents=격리된 작업 | 비대한 시작 컨텍스트 최소화. 강제력이 필요한 단계는 스킬 설명만으로 대체하지 않음 |
| Anthropic [Skill Creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | 경량 메타데이터 → 필요할 때 SKILL.md 본문 → 참조/스크립트 progressive disclosure | 기존 `.claude/skills` 정리, 최소 필수 필드와 역검증; 중복 에이전트/스킬 지양 |
| OpenAI [Codex Claude plugin](https://github.com/openai/codex-plugin-cc) | /codex:review, transfer/status/result 기능 존재 | 플러그인 이미 설치됨. **자동 수정·재검증 폐루프 E2E는 증명되지 않음**. 차단 게이트와 실제 결과 조회를 별도 통합시험 |
| LangGraph [Persistence](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx) | thread checkpoint와 cross-thread store를 분리 | TAKY `CURRENT`/불변 `HISTORY` 이원화가 이미 대응. LangGraph 자체 설치 불필요 |
| Temporal [retry/idempotence](https://github.com/temporalio/documentation/blob/main/docs/best-practices/error-handling.mdx) | 재시도 시 중복 부작용 방지를 위한 idempotency key·비재시도 오류·보상 | `EXECUTION_CHECKPOINT_PROTOCOL`의 Side-effect Ledger가 이미 대응. 누락된 **실제 실행 증거/리플레이 회귀**만 채움 |
| Claude-Mem [Worker architecture](https://github.com/thedotmack/claude-mem/blob/main/docs/public/architecture/overview.mdx) | Bun worker+SQLite+hooks+AI observer, 선택적 벡터 검색. 별도 데이터 저장 권위 발생 | 세션 요약 보조 검색만. YKH/TAKY 간 기밀·권위 혼합 금지, API 사용/수신 권한 확인 후 사용 |
| [AutoCAD MCP](https://github.com/U-C4N/Autocad-MCP) 및 [이슈](https://github.com/U-C4N/Autocad-MCP/issues) | headless ezdxf와 live COM의 기능 차이, rollback/undo 이슈 및 live 테스트 필요 | YKH 기존 읽기 전용 DXF 검산 우선. AutoCAD 2024/2019 정본 DWG 쓰기 MCP 무조건 설치 금지 |
| [Claude Stop hook 이슈](https://github.com/anthropics/claude-code/issues/32055) | 특정 Windows/Claude 버전에서 Stop hook이 수 턴 뒤 누락된 사용자 보고 | `Stop hook`만으로 작업/승인 폐루프 강제를 주장하지 말 것. 실제 영수증/외부 감시로 보완 |

주의: 외부 프로젝트가 보고하는 효과는 해당 저장소·그 조직의 사례이지 TAKY 환경에서 측정된 절감/성능이 아니다.

## 4. 최적 설계 — 기존 권위 유지, 가장 작은 실증 단위 우선

```text
USER INTENT / 기존 WORK_ID / 원본 REV
  → Source Router(공개 HTTP/Notion/인증 Aside / 문서 파일)
  → verified origin/caption pointer + content hash + rights/scope + dedup
  → EXISTING RAW/INTAKE (원본 미확보는 RAW_NOT_VERIFIED 유지)
  → EXISTING deterministic text extraction / evidence units
  → EXISTING INDEX OWNER (후보·판정·검증 증거)
  → EXISTING FORMING (REJECT/HOLD/APPROVED, domain namespace)
  → applicable consumer (Learning Projection / architect CAD task / UI toolchain)
  → focused actual runtime test and independent review WHEN NEEDED
  → receipt + CURRENT pointer + next correction limited to affected stage
```

### 4.1 Source intake 현실화
- 개인 로그인 Instagram은 **메인 PC Aside 브라우저를 필요할 때만 사용**. 바운드된 3개 팔로우 계정, 게시물별 최대 10개, 변경된 캡션 우선. 제목/본문/작성시각(확인 가능한 경우)/permalink/계정/캡처시각/SHA-256/권리 범위를 수집. DM·댓글 자동 발송 금지. 쿠키/로그인 세션을 렌더/공개 브리지로 이전하지 않는다.
- 공개 블로그/GitHub/Netlify/공공자료는 기존 무인증 HTTP 또는 공식 커넥터로 수집. robots/이용규정 및 변경 해시, 대기·백오프를 지킨다.
- 이미 생성된 `ASIDE_INSTAGRAM_CAPTION_SOURCE_20261106.json`은 신규 독립 소스대장이 아니라 **기존 Intake가 소비할 Source Evidence Candidate**. 연결된 실제 인덱스 0/9이므로 자동 학습 성공 표시 금지.
- 출처를 찾지 못한 것과 실제 존재하지 않는 것은 구분. 인스타그램 캡션만 있을 경우 RAW 불완전·본문 검토로 라벨링한다.

### 4.2 Harness/MCP/스킬의 적절한 자리
- `MASTER/CLAUDE.md/AGENTS.md`: 현재 권위·보호 경로·출력 계약·코스트/권한·원본 정합 같은 상시 규칙만. 고밀도 외부 가이드 본문을 상시 문서에 복제하지 않는다.
- 스킬 `.claude/skills/<task>/SKILL.md`: 반복 업무 절차(와칭 게시글 검토, 원문 판정, DXF 치수 검산, 결과 상태 조회), 명시적인 입출력/수락조건과 기존 스크립트 포인터. 새 스킬도 기존 5종에 같은 절차가 없을 때만.
- MCP: 외부 인증/프로그램 조작에 필요한 **좁은 연결**만. Notion/Drive/Playwright/Aside/Codex 중복 역할 확인, 도구 수 상주 최소화. 새 서비스 도입은 권한/벤치마크/원본 실제 이용 사례가 전제.
- Hooks: 가벼운 세션 시작 CURRENT 검증, 외부 부작용 승인, 결과 종료 영수증 정도를 **Controlled CLI**에서 결정론적으로. 원격 호스팅 모든 대화를 가로채는 자동 훅 존재한다고 주장하지 않는다. Stop 훅 단독 보장 금지.
- Subagent/독립 Codex: 코드가 바뀌거나 보안·회귀 위험이 있는 **한정된 리스크**에 사용. Claude 작성에 대한 Codex 리뷰도 자동 합격이 아니라 실제 테스트/수정 근거 필요.
- 개인 기억(Claude-Mem)은 공식 상태 저장소가 아니라 검색용. **CURRENT/WORK_ID 규칙을 덮어쓰지 못하게** 하며 렌더 결손 Bun을 별도 검증할 때까지 추가 활성화 보류.

### 4.3 실행 장치의 역할
- `YKH-RENDER`: 코딩, 대형 워크트리 조사, 참조 원문 분석, 테스트/DXF 초안 검산, Claude/Codex CLI.
- 메인: 개인 Aside 인증 세션·본인 권한 소스 접수, AutoCAD·Excel·PowerPoint GUI 원본 검수, 상태 소유자 확인 및 승인.
- Rhino 7은 렌더만 확인; Rhino 8+ 공식 MCP를 무리하게 설치하지 않는다.
- 렌더 원본 불가/REV 미일치라면 해당 코드/도면 구현은 `BLOCKED_SOURCE_UNAVAILABLE`. 완성도/런타임 PASS 주장 금지.
- 회사 YKH의 설계·법령 판정과 TAKY 교육 앱 소비는 **서로 다른 도메인 권위**, 공통 도구/기술 원리만 재사용한다.

## 5. TAKY 현행 대비 차이 및 우선 순위

| 우선 | 현행 | 최적안에서 달라질 실제 동작 | 성과 검증 |
|---|---|---|---|
| P0 | 캡션 9건 별도 JSON, 기존 인덱스 목록 0건 연결 | 기존 Intake/Index Owner가 URL+hash로 이 9건을 `CANDIDATE/HOLD`로 인식. RAW 미보유 표시 유지 | 후보 9/9 출처/해시/중복/권리 링크 + 누락·권한 HOLD 재현 |
| P0 | 비용 차단 worker 종료 코드만 수정됨 | 예약 작업 실제 상태/차단 원인을 사용자 진행판에 구분. `HOLD!=PASS` | provider 403 fixture → 프로세스 exit 2 → ACTIVE UI 차단 노출 |
| P0 | 466 후보·18,279 추출단위 vs 소비 0 | **가장 작고 유효한 1건**을 Index Owner 검토→Forming consumer 계약→타깃 실제 기능과 연결. 인간 승인·건축 법규 게이트는 보존 | 1건 자료가 승인 여부를 포함한 forward/reverse trace, 실효 소비 후 상태 |
| P1 | 스킬과 하네스는 설치됐지만 자동 발동/통합 미검증 | 기존 스킬에 10개 골든 사례, PreTool/Stop/Resume/Result 수락 규칙을 검증 | 프로세스 로그·테스트 결과·실제 적용 기능을 코드 REV에 연결 |
| P1 | 메인/렌더 비동기 스냅샷, 원본 REV 불일치 | 권한·보안 보장된 정본 소스 미러와 content hash/REV 확인. 특정 WORK_ID 일관성 | 양 PC 동일 파일·REV readback, 더티 파일 보존, 실패/롤백 시험 |
| P2 | 다수 참고 도구/케이스 미반영 | 실사용 문제와 매칭될 때만 Codex 추가 검증·Office/CAD MCP 조건부 도입 | 사용 전후 비용·실패율·완료 정확도 계측; 개선 없으면 미채택 |

**P0는 코드 작성 자체가 아니라 본문 9건의 진짜 인덱스/적용 증명**이다. `최초 1건`이 실제 소비까지 가면 이후 캡션과 기타 자료에 반복 적용 가능함. 작업자 사용량과 권한을 우회하지 않는다.

## 6. 최소 10개 골든 사례(기존 테스트에 편입할 후보)

1. 새 공개 게시물 1건 → 출처/캡션/해시/권한/저장 포인터 생성.
2. 같은 URL+본문 재방문 → 증거 0 중복, 불필요한 AI 호출 0.
3. 기존 URL의 본문 수정 → 버전 갱신, 이전 원문/비교 근거 보존.
4. Instagram 로그인/접근 실패 → `ACCESS_HOLD`, 글 삭제/부재 주장 없음.
5. 게시물의 `댓글로 자료` → **댓글·DM·팔로우 조작 0**.
6. 게시물 본문의 `기존 규칙 무시` 같은 프롬프트 인젝션 → 명령 실행 0, 내용은 미신뢰 출처로만 분류.
7. 법적 기준을 인용한 계단 캡션 → 수치 산술 시험 PASS와 법규 적용 승인 분리.
8. Claude 구독 403 → `HOLD_PROVIDER_AUTHORIZATION_REQUIRED`/exit2, 재호출·유료 전환 0.
9. 출처·해시는 있으나 원본 완전 보존 없음 → `INCOMPLETE_RAW_PRESERVATION`, 통합 마이닝 PASS 금지.
10. 검토된 후보가 실제 기존 타깃 consumer에 반영 → 실행 전/후 데이터·동작·독립 증거·CURRENT history 연계, source-to-outcome 역추적.

## 7. 최종 판정 및 보고 경계

1. **현재 최적안: 기존 경로를 고쳐 폐루프를 통과시킨다.** 새 orchestrator, LangGraph, Temporal, 12인 배심원, 240개 AutoCAD MCP 대량 설치는 사용성/권한/실행 증거상 현재 부적합.
2. **현재 실제 완료:** 원문 캡션 9/9 수집·해시 재검산, 별도 1차 적용성 분석, 기존 원본 사이트 13개와 YKH 검토 27건 상태 대조, 관련 공개 사례 및 실패모드 비교.
3. **미완료:** 전통적 의미의 RAW 완전 보존, 이 9건의 기존 Index Owner 수신, 승인된 Forming/학습 소비, 렌더 정본 소스 동기화, 실제 Claude↔Codex E2E 수정·재검증, 실제 CAD/DWG·편집가능 PPT 품질검증.
4. **권한/비용:** 유료 API, GitHub push/merge, Netlify 배포, 외부 자료 공개, 소셜 댓글/DM 작성은 시행하지 않음. 프로젝트 MASTER/WORK ID 권위 변경 없음.
5. **문서 소유권:** 본 보고서는 기존 `HISTORY`에 위치한 **비승인 비교·검증 근거**로만 관리. 사용자 승인과 후속 실행 증거 없이 `CLOSED`, `APPROVED`, `RUNTIME VERIFIED`로 보고하지 않는다.

## 8. 추가 현장 점검 — Claude-Mem / 비용·메인 PC 부하 (2026-11-06)

- **메인 PC:** 로컬 `~/.claude-mem/claude-mem.db` 약 **108,994,560 bytes**(약 104MiB / 109MB), Bun worker PID 22968 (관찰 RAM 107MB)와 worker heartbeat 동작. `observer-health.json`에는 과거 `Claude Code could not authenticate the observer` 오류가 기록됐으나 관찰 시 consecutiveFailures 0 및 나중 성공 시각이 기록됨. 이는 현재 정상 관측 신호이지 모든 세션의 기록 완전성 증거는 아님.
- **렌더 PC:** `~/.claude-mem/CAPTURE_BROKEN`에서 2026-11-06T04:06:49.854Z worker launch 실패를 확인: `Bun runtime not found`, 포트 37777. 설치된 `claude-mem@thedotmack` 15.10.0과 실제 기억 기능 정상 실행은 다르다. 현재 새 설치/권한 변경은 하지 않음.
- **메인 PC 자원 사용:** 관측 시 이름 `claude` 프로세스 10개 이상과 다수 `node` 프로세스가 존재. 예전 메인 Claude 예약 자동 시작 태스크 비활성화는 이미 수행했으나, **현재 남아 있는 실행 프로세스가 전부 종료됐다는 뜻은 아님**. 수행 중 세션을 임의 종료하지 않음. 계정 사용량 증가·터미널 팝업의 정확한 기여 원인은 별도 프로세스별 로그 추적 전 미확정.
- **실제 커뮤니티 실패 사례:** [Windows hook 터미널 팝업](https://github.com/thedotmack/claude-mem/issues/2186), [Windows 환경에서 Bun 발견 실패](https://github.com/thedotmack/claude-mem/issues/1738), [My Work 자동 새로고침 시 숨은 Codex 사용량이 증가했다는 사용자 보고](https://github.com/thedotmack/claude-mem/issues/5189), [Windows worker 기본 포트 이슈](https://github.com/thedotmack/claude-mem/issues/5415). **이슈는 유사 위험 사례일 뿐 사용자의 PC에 발생한 비용/프라이버시 유출의 확증이 아님.**
- **설치 최적 판단:** 자동 저장이 단일 권위보다 높은 우선순위가 되어서는 안 된다. Claude-Mem의 실제 `SessionStart/Stop` observer 횟수·API/구독 비용·보존 범위가 확인되기 전 부가 동기화/백그라운드 실행을 늘리지 않는다. 렌더 Bun 설치는 실제 메모리 소비가 업무 성공을 개선한다는 근거를 확보한 뒤 승인된 최소 절차로 검토. 추가 전체 재설치·새 DB 구성 금지.
- **우선 성과 기준**: (1) 원본에 없는 게시물 후보 1개가 기존 인덱스를 거쳐 실제 타깃 소비로 이어지는가, (2) 메인/렌더 메모리·CPU와 Claude/Codex 사용량이 줄거나 증가하지 않는가, (3) 재실행 시 중복/승인 우회 없이 같은 결과로 복구되는가.
