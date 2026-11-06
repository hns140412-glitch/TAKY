# 외부 자료·실증 사례 독립 평가와 최적안 선도출 — 2026-11-06

- 상태: **PHASE A/B/C INDEPENDENT CONCLUSION FROZEN / COMPARISON NOT YET WRITTEN**
- 목적: 소셜 게시물·공식 저장소·설치 사례·실제 검증 보고를 검토해 외부 사례 자체의 최적 구조를 먼저 판단한다.
- 절차: A 원문 독립 평가 → B 경쟁 접근 교차 비교 → C 독립 최적안 확정·해시 봉인 → **D 후속 incumbent 비교**. 이 파일의 A/B/C가 별도로 기록·해시로 봉인되기 전 incumbent 현행 구현을 평가 척도로 사용하지 않는다.
- 한계: 여기서 `원문 확인`은 개별 게시글 캡션·공식 공개 저장소 내용 확인을 뜻한다. 13개 와칭 사이트 전체 게시글 전수 의미분석, 링크로만 존재하는 27개 원자료의 완전 회수, 실무 DWG/PPT 앱 성능 벤치마크 수행을 뜻하지 않는다.

## A. 원문과 실제 사례에 대한 독립 사실 분석

### 원문 표본과 입증 수준
- 인증된 Aside UI로 본 Instagram 글 **9건 / 3개 팔로잉 계정**의 본문·원문 URL·SHA-256이 확인됨. 파일 `D:\Git PWA\TAKY-SOURCE-VAULT\reports\site_watch\ASIDE_INSTAGRAM_CAPTION_SOURCE_20261106.json`. 별도 채굴 결과에는 초벌 의견이 존재하지만 본 독립 검토에서는 **자기 원문 캡션과 외부 저장소**를 직접 평가한다.
- 별도 회사 실무 사례 색인 `WORKBENCH/REVIEW_CASES.json` 27건은 **REVIEWED 16, PARTIAL_SOURCE 6, NOT_SECURED 5**. 원문 미회수 11건은 실증 성공/실패를 확정할 수 없다. 이 색인은 독립 확인 시 **출처·파일·실행 증거의 존재 여부**에만 사용하며 선행 채택/보류 평가는 재사용하지 않음.
- 수집 후보 466건·기계적 추출 18,279개 단위와 같은 카운트는 정보량을 표현할 뿐, 각 항목을 실제 검증했다는 뜻은 아니다.

### 1. 인스타그램 원문 9건
| 외부 사례 | 원문이 증명하는 것 | 검증되지 않은 것 / 오류 위험 | 독립적 재사용 가치 |
|---|---|---|---|
| [김스득 — 스킬/매뉴얼](https://www.instagram.com/p/DerPUzhzDH5/) | 반복 절차를 업무 매뉴얼과 자체 검증 기준으로 만들어 재사용하라는 실무 주장을 담음 | 첫 스킬 30분/80% 등은 작성자 경험·홍보 성격, 보편적 benchmark 아님. 매뉴얼만 있다고 재실행이 보장되진 않음 | **HIGH**: 표준 입출력과 기준을 기능과 함께 운영할 때 |
| [김스득 — Claude-Mem](https://www.instagram.com/p/DfV6kMYirUU/) | 세션 기록·재주입을 통한 연속성 방법 설명 | 별도 워커/observer·인증·개인정보 저장·요금과 장애 위험. 플러그인 설치가 내용 유효성 보장 아님 | **CONDITIONAL**: 기억을 조회하는 용도, 권위 있는 결정 기록을 대체하면 위험 |
| [김스득 — PPT Master](https://www.instagram.com/p/DfGd0Twit7K/) | 편집 가능한 PPT 산출물 주장 | 출처 캡션만으로는 실제 텍스트/차트/테이블 편집성 불확정 | **HIGH EXPERIMENT**: 독립 `hugohe3/ppt-master` 공식 저장소에서 네이티브 DrawingML, 템플릿·차트 출력 기능 확인. 실제 국문 회사 양식 시험 필요 |
| [게으른 빌더 — Claude Court](https://www.instagram.com/p/DeeH-bVMldM/) | 반박·의견 분산을 통한 의사결정 방법 | 공개 구현 `alexyc9381/court-skill` 기본 12 jurors 및 17 sub-agent calls. 투표 다수는 사실 검증 아님 | **SPECIALIZED**: 반대 논거와 가정 탐색, 자주 반복하는 코딩 검증의 기본 수단은 아님 |
| [게으른 빌더 — 2일 세팅 로드맵](https://www.instagram.com/p/DfJ_No7M7cB/) | 프로젝트·메모리·MCP·스킬 구축 개요 | "90% 이상"을 뒷받침하는 독립 비교 데이터 부재. 실제 세팅 문서는 DM gated | **LOW-MEDIUM**: 초보 환경 구성 체크리스트 정도 |
| [게으른 빌더 — 플러그인 10종](https://www.instagram.com/p/De_qY6Tz_KN/) | 존재한다고 주장하는 툴 목록 자료를 안내 | 세부 10개 도구·벤치마크·권한·라이선스·실제 산출 미공개 | **NOT VERIFIABLE**: 공개된 본문만으로는 설치 권고 불가 |
| [디지트 — 모델링 지시 7항목](https://www.instagram.com/p/DfGrHJ9gaAw/) | 목표·조건·단계·규칙·검수·보고·제한을 명시하고, 수정 시 위치·차이 근거를 제시하는 작업법 | DM gated PDF 지시서·Rhino 8 3dm은 수집되지 않음. 7항목이 실제 모델 정확도를 높인다는 반복 측정치 없음 | **HIGH**: 기하/문서화 작업의 결과 조건을 관찰 가능하게 정의 |
| [디지트 — 도면 축척별 표현](https://www.instagram.com/p/DfWEljrAR9j/) | 1/500→1/20 표현·마감·창호·재료 정보 수준 차이를 설명 | 2006 협회 지침의 자체 요약이며 법적 의무 아님. 표준 원문·도면 샘플 대조 미진행 | **DOMAIN CONDITIONAL**: 도면 scale별 QA 후보 |
| [디지트 — 계단 기하·면적](https://www.instagram.com/p/DfYpYo4gfVJ/) | 계단 유형 다섯 가지와 치수 예제 제시. 175×16=2,800mm, 4840×1200=5.808㎡, 3020×2400=7.248㎡ 산술 확인 | 실제 법령/계단참 요구·원형/나선형 면적은 원문·평면 검증 필요. 바운딩 박스 면적과 실제 점유 면적을 혼동하면 실패 | **DOMAIN CONDITIONAL**: 기하 계산·도형 조건 검증 예제 |

### 2. 독립 구현 및 실패 증거 — 공식/공개 소스
- [Anthropic, Building effective agents](https://www.anthropic.com/research/building-effective-agents): 복잡한 agent가 항상 낫지 않으며 결정적 workflow·evaluator/optimizer·orchestrator-workers 각자 성립 조건이 다름. 실행 결과를 환경에서 관찰해야 함.
- [Anthropic, Building agents when to fold subagents (2026-10-22)](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop): 기업 현장 비교에서 일부 다중 에이전트 역할을 main loop와 동적 도구 로딩으로 합쳤을 때 품질/지연/비용 개선 사례. **독립 검증/권한 분리/병렬 탐색은 서브에이전트 유지할 이유**라고 명시. 특정 사례의 효과를 타 제품에 일반화 금지.
- [Anthropic customization guidance](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more): 상시 정체/경계=기본 설정; 반복 업무=필요시 로드하는 Skill; deterministic 이벤트=Hook; 격리 작업=Subagent로 분리. 선언식 가이드와 기계적 작동은 다름.
- [OpenAI Codex plugin for Claude Code](https://github.com/openai/codex-plugin-cc): read-only review / adversarial review / transfer-status-result; 기본 자동 Stop review gate는 **장시간 루프와 사용량 소모 위험**을 명시. 플러그인 기능은 실행 결과 증거와 다름.
- [김스득 Claudex-loop의 재현 가능한 계획검토](https://sdk-kim-builds.com/guides/claudex-loop-cross-model-plan-review/): 계획 검토에 SHA256 결속, 변경 시 재승인, 구현 이후 별도 변경분 해시와 독립 inspect, 반복 상한 5/2 등의 범위제한. **파일 지문 변경 시 이전 승인 폐기**라는 기술 방식은 검증 가능한 장점. 작성자가 설명하는 시나리오이며 외부 성능 측정 아님.
- [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master): 실제 PPTX DrawingML/네이티브 구조, 회사 템플릿·PDF/Word 문서 입력·도표·차트와 선택적 PowerPoint Chart/Table. 기본 shapes와 native chart는 서로 다름. 편집성은 실제 PowerPoint 열어서 수정·저장·재열기 PASS 전까지 후보.
- [tobi/qmd](https://github.com/tobi/qmd): BM25 FTS + 벡터 + 쿼리 확장/재순위. 기존 별도 로컬 시험 기록은 BM25 850~900ms vs rg 180~350ms 및 한국어 검색 품질 저하(10개 질의, 모델/코퍼스 제한). **의미 검색의 장점은 미검증**이므로 벤치마크 필요.
- [Vercel agent-desktop](https://github.com/vercel-labs/agent-desktop): Windows UIA 접근성 트리 기반의 상태 조회·제한된 GUI 제어. 별도 현장 시험에서 AutoCAD 모델 뷰는 부분적으로만 접근 가능하고 트리 잘림/명령 입력 실패 관찰. 앱 지원=CAD 생산성 보장 아님.
- [U-C4N AutoCAD MCP](https://github.com/U-C4N/Autocad-MCP): COM/live와 ezdxf/headless 분리, 248 등록 도구, tool-packs/검색 로딩, revision-bound preview/apply와 **저장한 DXF 재열기/실측 요구량 검증** 제공. 프로젝트 자가 시험 결과는 별도 환경에서 재현 필요; [COM rollback hang 이슈](https://github.com/U-C4N/Autocad-MCP/issues/7)도 존재.
- [McNeel RhinoAI](https://mcneel.github.io/RhinoAI/docs/getting-started/cc-plugin/): 공식 Rhino MCP는 **Rhino 8+** 전제. 특정 버전 미만에는 실행 가용성 없음.
- [Claude-Mem worker](https://github.com/thedotmack/claude-mem/blob/main/docs/public/troubleshooting.mdx): 로컬 Bun worker·SQLite·observer·검색. Windows 오류/이전 세션 재처리·메모리/비용 문제. 설치 성공과 세션 기억 생성 정상은 다른 상태.
- [LangGraph persistence](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx): thread checkpoints와 cross-thread stores 분리, resume / HITL. `checkpoint restored`≠외부 부작용 재실행 허가.
- [Temporal error handling](https://github.com/temporalio/documentation/blob/main/docs/best-practices/error-handling.mdx): retryable vs nonretryable, idempotent activity, saga compensation. 취소/실패/중복 호출의 실제 결과를 읽고 정책을 적용해야 함.
- [Beads quickstart](https://github.com/gastownhall/beads/blob/main/docs/getting-started/quickstart.md): 의존성/이슈 관리용 Dolt DB와 hook. 초기화가 별도 저장소 및 훅을 만들므로 현재 시스템과 함께 쓰면 충돌/2개 진실이 될 가능성. 설치 전 조직의 단일 작업 기록 권위와 충돌 점검 필요.
- [Matt Pocock grilling](https://github.com/mattpocock/skills/blob/main/docs/productivity/grilling.md): 불확실한 의사결정을 decision tree/frontier 질문으로 다룸. 사용자에게 사실 확인/설치 디버깅까지 넘기면 효율 저하; 선택 결정만 분리하는 게 적합.

## B. 독립 경쟁 대안 비교

**공통 평가 기준을 먼저 고정**한다: (1) 실제 과제 달성·출력 검산 가능성, (2) 원본/근거 재현성, (3) 오류 복구·중복 부작용 안전성, (4) 컨텍스트·모델 호출·PC 자원 비용, (5) 설치/유지·작업자 부담, (6) 건축·문서 같은 전문 분야 확장성. 홍보 조회수·별점은 최적화 점수가 아니다.

| 접근 | 강점 | 약점/실패 조건 | 적합한 조건 |
|---|---|---|---|
| I. 한 AI + 스킬·절차 | 단순, 적은 시작 컨텍스트, 반복업무 표준화 | 자기 계획·결과를 스스로 검수하면 편향/재현 없는 승인 가능 | 정형 문서 생성, 중저위험 반복 작업 |
| II. 병렬 다중 에이전트/12인 배심 | 다양한 관점과 반례 탐색 | 다수 호출·비용·일정 상승, 투표는 증거·사실 검증 아님 | 복잡한 의사결정의 한정 비교·예외적 감사 |
| III. 두 모델 교차 계획·코드 검토 | 독립 작성·검토, 해시로 승인 고정, 위험에 비례한 보강 | 주력 모델 두 개 사용, 실패 반복 시 폭증, 같은 입력이 틀리면 둘 다 오판 | 보안/법적 판단/다수 파일 변경/수정 전 독립 검증 |
| IV. 완전 결정론적 정적 파이프라인 | 빠르고 재현 가능, 적은 호출, 오류 원인 분리 | 의미 추론·도메인 판단·모호한 컨텐츠 비교에 취약 | 변경 감지, 해시, 중복/수치/형식 검증 |
| V. 완전 동적 자율 에이전트 | 미지 자료 탐색·복합 오류 대처 유연성 | 비용·예측/권한/중단/상태 복원 어려움, 결과 과장 가능 | 성공 기준이 불명확한 한정 연구/샌드박스 |

**비교 결론**: 하나의 모델/엔진 패턴만 기본값으로 절대화하는 대신, IV(결정론적 증거 처리)를 기반으로 I(업무별 스킬)를 붙이고, **III(교차 검증)를 고위험·불확실성 높은 구간에만 호출**하는 정책이 여섯 기준을 가장 균형 있게 충족한다. 정보수집의 일부는 실물 UI/인증 제약 때문에 동적 탐색(V)의 좁은 범위를 허용하되 결과를 곧바로 사실로 승격하지 않는다. II(다중 배심)는 일반 시스템 기본값으로 부적합하나 결정 탐색을 위한 예외적인 값이 있다.

## C. 독립 최적안 — INDEPENDENT_OPTIMAL_OPTION (TAKY와 비교하기 전에 확정)

**결론: "원문 증거 주도형·위험 적응형 업무 실행 시스템"**. 특정 AI/프레임워크의 홍보를 최적안으로 선택하지 않는다.

1. **Evidence Intake**: 일반 웹/공식 저장소/인증 브라우저/문서/사람의 소스 입력을 채널별로 수집. URL·원본(또는 검증 가능한 제한적 증거)·취득시각·작성자·권리·SHA·출처 수준을 분리. 재방문은 URL과 normalized content hash로 version/dedup; 미확보는 없는 자료로 오인 금지.
2. **Evidence Decomposition**: 캡션·글에서 "주장/방법/측정치/적용 조건/불확실성/실패 사례"를 서로 나눔. 개발자나 제작자의 self-claim은 사실 확인과 분리. 기계적 수치/스키마 검산을 먼저 하고, 의미 검토는 해당 근거 packet만 사용.
3. **Independent Cross-case Evaluation**: 비교 기준을 평가 전 고정하고 경쟁 도구/접근의 대안·반례를 포함. 실행 전 비가역/권한/비용 게이트. 도입 여부는 **실제 산출물, 관련 소스 readback, 테스트 재현성**으로 결정.
4. **Execution Contract + Risk-tiering**: 반복 업무는 온디맨드 스킬과 명시된 단위/REV/산출/완료조건을 사용. 낮은 위험은 결정적 검사, 중간 위험은 1 실행자+자기 출력 검증, 높은 위험은 작성자와 다른 모델/검증자를 별도로 호출. 두 모델 무조건 호출·자동 Stop 반복 리뷰는 사용량 폭증이므로 기본 OFF.
5. **Artifact-centric Real Verification**: 코드 diff와 exit0만이 아니라 결과 파일을 재열어 네이티브 PPT 객체, 실제 CAD 엔티티/공간·레이어, 엑셀 수식·값 등 **소비자가 쓰는 형태**로 검증. 코드/샘플/GUI/법규의 검증 상태는 서로 독립.
6. **Durable State + Recovery**: 단위 작업마다 input hash/REV, owner, 단계, 명시적 PASS/HOLD/FAIL, next, receipt, 상태를 기록. 외부 쓰기/배포/승인 등 부작용은 idempotency/approval/rollback 별도 관리. 프로세스 종료코드 0을 소비 성공으로 치지 않음.
7. **Operational Cost & Authority**: 도구를 상시 모두 로딩하지 않고 능력별 최소 등록; 인증 자료는 원래 허가된 환경에 유지, CPU/RAM 부하 큰 파싱/컴파일은 적절한 다른 워커로 이동. 실제 원본/같은 revision 확인이 없으면 구현·통합 완료를 기록하지 않음.
8. **Measured Acceptance**: 대표 10개 과제에서 소스 회수율, 출처/해시 추적률, 잘못된 승인 0, 실제 산출 재열기 PASS, 재시도 중복 0, 업무 시간·모델 호출·메모리, 사용자 확인 대기, 오류 복구 후 일관성 등을 기준으로 기존 방법과 A/B 비교. 통과 없는 기능은 CANDIDATE/HOLD로 유지.

**선택 대상 사례**: 스킬 재사용/검증 가능한 결과, 클로덱스의 계획·diff 해시와 독립 inspector, 도메인 검증(디지트의 7개 필드와 기하 검산), PPT Master 실제 네이티브 객체, 파일·워크플로의 durable event/idempotent 처리, 필요한 시기에만 context/MCP 로딩. 
**비선택**: 홍보성 10종 묶음/17번 매건 review 호출/단순 통합형 메모리 전체 위임/도면 GUI 자동 조작을 위한 원본 미확인 도구 도입.
**반대 가능성**: 대규모 병렬 조사는 subagent 병렬이 빠를 수 있으며, 수백 건의 중단/재개 장기 workflow는 LangGraph/Temporal 같은 전용 durable execution이 이득일 수 있다. 이는 동일한 10개 업무 과제에 대한 처리량·장애 복구 테스트가 달라질 때 채택할 대안.
**판정 신뢰도**: 운영 원리 HIGH(공식 사례 다수), 사용자 환경 성능 UNKNOWN(여기서 신규 실무 워크플로를 실제로 실행하지 않음), 특정 전문도구 도입 CONDITIONAL. 최적안은 **독립 비교에 근거한 설계 선택**이며 특정 PC에서 구현 완료했다는 주장이 아님.

**FREEZE BOUNDARY: END OF INDEPENDENT SOURCE / CROSS-CASE / OPTIMUM ANALYSIS. NEXT SECTION (D) MAY COMPARE TO INCUMBENT ONLY AFTER THIS PORTION IS SAVED + SHA-256 READBACK.**

## D. 외부 독립 최적안 확정 **후** TAKY 현행과 비교

### 비교 선행 증거 (순서 보장)
- 독립 A/B/C 내용은 TAKY 현행을 평가하기 **전에** 같은 파일에 먼저 저장·재읽기 확인됨.
- **A/B/C 원문 원본 해시 SHA-256:** `012337A07B9289E33A174049E9937A2479B53EE470B0B601E4E5F77626BA4001`, **원본 바이트 수 16,803**. 본 D는 그 이후 뒤에만 추가됨. 검증기는 파일의 처음 16,803 bytes에 대한 SHA가 일치해야 통과.
- 비교 당시 기준 자료: `STATE.md`, `MASTER/MASTER_LOGIC.md`, `MASTER/REVIEW_DEFAULT_MINING_PROTOCOL.md`, `MASTER/FORMING_PROTOCOL.md`, `MASTER/AI_COLLABORATION_PROTOCOL.md`, `MASTER/EXECUTION_CHECKPOINT_PROTOCOL.md`, `MASTER/TRACEABILITY_PROTOCOL.md`; Site Watch 13개 레지스트리·Aside 캡션 9개·파생 인덱스 466개·채굴단위 18,279개·YKH 27개 사례.

### 원리/실제기능 분리 비교

| 독립 최적안 요구 | TAKY 현행 진실 | 차이 판정 | 구체적 개선안·우선도 |
|---|---|---|---|
| 출처별 RAW→본문 evidence/해시→중복 버전→다음 심사로 실제 인계 | `REVIEW_DEFAULT_MINING_PROTOCOL`에 원리 규정; Aside 소스 9/9 SHA 실재. Site Watch `INDEX REVIEW` 후보 466건과 게시물 URL 일치 **0/9**, 자동 consumer 인계 증거 없음 | **GAP_IMPLEMENTATION** | P0: 기존 Intake adapter에서 인증 캡션의 `SOURCE_BOUND` packet만 읽고 후보 증거에 9건 연결. 원본 전체 RAW 미확보는 `INCOMPLETE_RAW_PRESERVATION`으로 남김. 신규 원본 수집기 생성보다 전송·검증을 구현 |
| 생성자 주장과 근거/반례를 분리한 독립 최적안 | `MASTER`에 출처·의도·권한 구분은 있음. 그러나 이전 검토에서 TAKY 결론 선제시, 실패 기록 F-07 등록 | **BETTER_EXTERNAL_METHOD / PREVIOUS_FAIL** | P0: 독립 A/B/C 파일 및 해시 먼저 저장 → D 비교에 이 해시 요구. F-07은 문구 등록만 아니라 동일 요청 재실행으로 회귀 판정 |
| 실제 교차검증 + 수정 시 재승인 | Claude 주 실행·Codex 검증의 역할 정책과 플러그인 설치는 있음. **Claude→Codex→수정→새 증거 E2E 미검증** | **BETTER_EXTERNAL_MECHANISM / GAP_RUNTIME** | P1: Claudex의 `plan_sha + reviewed_commit/diff_sha + reviewer/decision`처럼 변경 시 평가 무효화. 기존 executor receipt/검증 경계에 결속해 한정 E2E. 자동 무한 Stop gate 기본 OFF |
| 작업 구분과 개인정보·외부 부작용 안전 | `MASTER_LOGIC`, `AI_COLLABORATION`, checkpoint/side effect ledger에 강한 소유권·승인/재실행 규칙 존재 | **BETTER_TAKY_POLICY / RUNTIME_NOT_VERIFIED** | 기존 권위 유지하되 영수증 없는 CLAIM=PASS 금지. 호스팅 전체 강제 게이트 존재를 주장하지 않음 |
| 반복 업무 스킬의 자동 발동/수용조건 | `CLAUDE.md` 및 여러 사용자/프로젝트 스킬·에이전트 존재, 일부 복제 테스트 완료 | **SAME_INTENT / GAP_ACCEPTANCE** | P1: 기존 업무 스킬당 실제 10개 대표 상황에서 호출·출력·한계·오호출 테스트. 문서 문장만으로 동작하지 않는다 |
| 진짜 산출 파일 재열기·수정/저장 후 회귀 | 렌더 `dxf-check.py` 임시 20㎡ 격자 시험 PASS, 실제 DWG 원본 수준 검증 미완료; PPT Master 작업 환경 설치/실물 편집 PASS 미확보 | **BETTER_EXTERNAL_CANDIDATES** | P1: PPT Master는 공식 네이티브 개체 출력이 있음: 라이선스·의존성 검토 후 **임시 1장** 작성/편집/재열기 A/B 시험. CAD는 실무 도면 사본으로 geometry requirement → 저장 DXF reopen parity/레이어·블록·면적 비교 후보. 직접 COM 실도면 조작은 별도 검증 |
| 도메인별 기하/치수/법령 검증 | YKH 실무 별도 권위로 ArchiGrow 파이프라인 운영 목표가 있으나 실제 이미지→공간 구조→DWG 샘플 PASS 미확보 | **GAP_DOMAIN_OUTPUT** | P1: 공간 구획·직교/50mm snap을 우선 검증하고 창호/블록은 구조 게이트 후. 디지트 계단 예시는 산술·법규·실제 도형 검증을 분리. YKH·학습앱 데이터 소유권 섞지 않음 |
| 복구 가능한 상태·중복 없는 재시도 | `EXECUTION_CHECKPOINT_PROTOCOL` CURRENT/HISTORY + side-effect ledger 구조가 기존 존재. 로컬 UI/호스팅/원격 실행 통합의 강제력은 미입증 | **SAME_DESIGN / GAP_EXECUTION** | P1: 종료코드 0·SKIP·HOLD·EXTERNAL_SIDE_EFFECT를 구분한 실제 기록. 중단 후 동일 수집/저장 재실행 시 중복 0 시험. LangGraph/Temporal 신규 도입은 이 요구를 기존 실행코드가 이행 못 한다고 입증한 뒤 평가 |
| 비용/메모리·MCP 최소 로딩 | `SAVEY` 소비량 정책과 로컬 우선 원칙 존재. 메인에 Claude 프로세스 다수, 렌더 Claude-Mem Bun 누락·워커 실패, 사전부하 모니터링 불완전 | **GAP_OPERATIONAL** | P1: 메인 GUI 업무 우선, 렌더 코딩/워크트리/파싱, Aside 계정 세션은 메인. 사전/사후 CPU RAM+Claude/Codex 사용량을 측정. 불명확한 셋업/유료 기억 자동추가 금지 |
| 외부 문서·학습 내용의 최종 소비 | Site Watch `index_owner_accepted=0`, `forming_approved=0`, `learning_consumed=0`. Notion 자료 236, queue 239, blocks read 0. Claude subscription 조직정책 403으로 의미 worker HOLD | **CRITICAL_OUTCOME_GAP** | P0: 권한 승인 범위에서 예제 1건을 기존 Index Owner에 넣어 승인/HOLD의 정당성을 확인하고, 승인된 분야별 consumer까지 실제 읽기/동작 시험. 인증 우회/유료 API 자동 전환 금지 |

### 외부 사례가 더 나은 부분 — 기존 원칙으로 덮어쓰지 않음

1. **클로덱스 리뷰의 계획/구현 지문**은 `역할 분리` 선언보다 엄격한 **계획 변조 후 검토 무효화** 동작. 구현이 확보돼야 한다.
2. **AutoCAD MCP의 요구조건-실제형상-저장파일 재열기 일치 검사**는 임시 사각형 20㎡ 검산보다 강한 산출 검증법. 현장 DWG와 COM 버전·권한 문제로 도입 여부는 시험 후 결정한다.
3. **PPT Master 네이티브 PPT 객체/표/차트 지원**은 단순 PPT 스크린샷 생성과 다르다. 실제 제품이 존재하며 기능을 무시/미존재 처리하면 안 된다. 다만 샘플/Office 직접 편집 시험이 선행한다.
4. **위험도 기반 서브에이전트 사용/컨텍스트 온디맨드 노출**은 하네스 규칙을 실제 도구 로드·모델 호출 절감으로 측정해야 한다. 문서에 절감 원칙이 존재한다고 절감이 발생한 것은 아니다.

### TAKY가 독립안보다 보호하는 영역
- 분야/프로젝트/사용자/실제 실행 권위를 나눈 구조, human 승인 및 소스 원본 불변, 일방향 호스팅 호출의 실제 권한을 과장하지 않도록 하는 경계는 유지가 필요하다.
- 단, 이 항목은 **규정된 강점**이지 현재 전 작업에서 자동 강제가 이루어진다는 증거는 아니다.

## E. 종합 판정·후속 실행 순서 (비교 이후 결정)

- **독립 최적안 수정 필요 없음**: 단일 AI+온디맨드 스킬+결정론적 증거 처리+위험에 따른 독립 검증+산출 실증+durable resume. 현행 운영에서 만족시킨 부분은 유지하고, 실증이 없는 곳을 `GAP`으로 낮춰야 한다.
- **실제 첫 성과 목표:** 원문 캡션 9개 중 **1개를 기존 Intake→Index Owner에 정확한 소스/해시/HOLD 상태로 넘긴 증거**. 그 뒤 소비자까지 1건 실제 결과를 통과시켜 단계별 PASS만 별도 승격한다. 9건 입력/1건 소비는 실행 단위의 우선순위이지 나머지 8건을 임의로 버리라는 뜻이 아니다.
- **두 번째 목표:** 실제 코딩 작업 1건의 `PLAN_REV/PRE_DIFF/CLAUDE_IMPL/INDEPENDENT_CODEX/DX_TEST/RESULT`을 같은 파일 revision으로 재현. 한계·사용량·도구 실패도 보고한다.
- **세 번째 목표:** 실무 CAD/Office의 실제 유용한 산출물 1개씩 재열어 수정 가능한 결과 확인. Rhino 7에 Rhino 8+ 공식 MCP 설치 금지.
- **거버넌스/비용 권위:** 기존 GitHub canonical master/사용자 승인/비밀 보호, 유료 API·push·merge·Netlify 배포 금지 상태 유지. 소스·안전 권한 검토는 사전할 수 있으나 외부 분석의 정답을 사전에 정하는 근거로 사용하지 않는다.
- **실제 구현 현황:** 본 비교는 검토와 결과 선택의 실행이다. 기존 앱 코드 편집·9건 인덱스 소비·이중 모델 자동 교차검증의 통합 성공은 수행하지 않았다. 별도 코드 구현 PASS 또는 production PASS를 주장하지 않는다.
- **실패 사건 F-07 범위:** 사용자 지시의 A→B→C→D 순서를 이번 문서에서 별도 기록·해시 봉인했는지 회귀 재현으로 확인한다. 성공하더라도 호스팅 전체 chat에서 자동 차단을 달성한 것은 아님.
