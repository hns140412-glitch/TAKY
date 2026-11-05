# TAKY 마이닝→인덱싱→FORMING→학습→소비 독립 감사 (읽기 전용)

수정·실행·네트워크 호출은 하지 않았습니다. 임시 분석 스크립트는 `/tmp/aud`에서만 돌렸습니다. 기존 감사 산출물(`LEARNING/evidence/CLAUDE_INDEPENDENT_PIPELINE_AUDIT_20261017.md`)은 읽지 않았고 근거로 쓰지 않았습니다.

## 1. 최상위 판정 (신뢰도: 핵심 결함 높음, 하류 소비 단계는 중간)

**원문(RAW)은 잘 보존돼 있지만, 의미 단위 마이닝이 사실상 없습니다.** 118편에 대한 "학습"은 원문에서 도출된 것이 아닙니다.

- 마이너 `units_html`이 `h1~h4, p, li, blockquote`만 추출합니다. 이 글들의 핵심인 `<pre>`(명령·프롬프트), 표, 이미지, 외부 링크는 버립니다.
- 12개 LESSONS는 어시스턴트가 먼저 쓴 해석입니다. 한 단어짜리 `needle`이 들어 있는 첫 문장을 "근거 인용"으로 붙인 형태입니다.
- 최근의 방어(`verified_dynamic_source_ids`)는 오염을 막지만, 원문 이해를 늘려 주지는 않습니다. 호출자가 넘기는 집합을 믿기만 하고, 검증은 하지 않습니다.
- 지금 활성 마이닝(`SITE_MINING_EVIDENCE_ACTIVE`)은 27개 출처, 907개 단위입니다. every-ai 118편은 **0건**입니다. 검증 완료된 파이프라인이 아니라 "격리 후 빈 상태"입니다.

## 2. 실제 체인과 끊긴 지점

```
[RAW] site_watch 캡처 118건 (sha256, HTTP 200)          ← 실재·양호 (ALL_118_RAW_AUDIT.json)
   │
   ▼  MINE_SITE_EVIDENCE_UNITS_LOCAL.units_html
[MINING] p/li/h만 추출, <45자 폐기, 900자 절단           ← ✗ pre·table·img·링크 누락
   │      (활성 포인터: 27 출처, every-ai 0건)
   ▼  INDEX_SITE_WATCH_TEXT_LOCAL
[INDEX] 어휘 bag + excerpt 340자. every-ai는 접두 규칙으로 통째 제외
   │                                                      ← ✗ 원문 발견성 단절
   ▼  (끊김) 분류·관계·출처 단위 INDEX/DETAIL 없음
[FORMING] global_source_learning_feedback._forming       ← 118과 연결 안 됨
   │
   ▼  build_learning(records, verified_dynamic_source_ids)
[LEARNING] 정적 LEARNING_PATTERNS + 호출자 지정 동적 ID
   │                                                      ← ✗ 검증기 없음
   ▼
[소비] Hide & Seek 등 앱: AI_LEARNING_PROJECTION 참조 없음 ← ✗ MISSING 화살표
```

- 실제로 호출되는 사슬은 `central_review_source_intake` → `build_learning`(영수증 4건)과 `global_source_learning_feedback.technical_method_decision`입니다.
- 이 사슬은 118편이 아니라 단일 하드코딩 학습 `AI-LRN-ACCESSIBILITY-LOCAL-REVIEW-CANDIDATE`만 다룹니다.
- `CURRENT/DATA/AI_LEARNING_PROJECTION.json`은 2026-10-08 생성본(57건)이고 `pending_dynamic_learning_review` 키가 없습니다. 새 게이트 이전 산출물이 CURRENT에 남아 있습니다.
- `ai_reference_projection.py`와 `ai_learning_quest.py` 외에 이 투영을 읽는 소비자는 찾지 못했습니다. `Hide & Seek`는 `.py/.js/.cjs/.ts/.tsx`를 검색해 참조가 없었습니다.

## 3. 구체 발견 (finding)

| # | 상태 | 경로 / 함수 | 재현 가능한 설명 | 위험 | 수정 |
|---|---|---|---|---|---|
| F1 | **검증** | `MINE_SITE_EVIDENCE_UNITS_LOCAL.py` `units_html` | 셀렉터에 pre·code·table·img·a가 없습니다. 118편 원본에 같은 셀렉터를 적용해 복제한 결과, `<pre>` 826개(118,685자) 중 약 796개(약 99.5%)가 추출물에 없습니다. 표 105개, 이미지 44개도 마찬가지입니다. | 명령·프롬프트·"성공하면…" 기대결과 같은 핵심 메커니즘이 통째로 누락됩니다. | 타입별 단위 추가(§5-1) |
| F2 | **검증** | 같은 함수 | `len(txt)<45`는 짧은 줄을 버립니다(118편에서 3,158블록). `npx designlang https://stripe.com`은 33자라 prose 규칙에서도 탈락합니다. `excerpt[:900]`은 절단하고 `seen`은 텍스트 중복을 삭제합니다. | 조용한 누락(silent drop) | 코드·헤딩은 길이 제한 면제, 전문 sha+연속 청크 |
| F3 | **검증** | 같은 함수의 `source_article_completeness` | 반환값이 상수 `False`입니다. 어떤 출처도 완전하다고 표시될 수 없는, 반증 불가능한 라벨입니다. | 안티-진행 게이트, 검증 불가 라벨 | 원문 구조 인벤토리 대비 추출 대응표로 계산 |
| F4 | **검증** | `LEARNING/intake/every_ai_method_learning.py` `LESSONS` | `needle`은 '상관', 'REA', 'DevTools', '모델' 등입니다. 첫 일치 문장이 인용으로 붙습니다. 저장된 인용을 보면 `OFFICE`는 h1 제목, `MOTION`은 스킬 설치 안내, `BROWSER`는 수사 문장, `MODEL_ROUTING`은 가격 안내입니다. `insight`는 코드에 선(先) 작성돼 있습니다. | 장식용 근거로 학습 오염 | LESSONS 삭제, 타입 단위에서 결정론적 도출 |
| F5 | **검증(코드 읽기)** | 같은 파일 `main` | 격리 마커가 있으면 `SystemExit`로 종료합니다. 마커가 없어도 `build_learning(project_rows)`는 검증 집합이 없어 `learnings`가 비고, 바로 뒤 `assert ids==…`가 깨집니다. 실행은 하지 않았습니다. | 죽은 코드가 PASS처럼 보일 위험 | 파일 폐기 또는 신규 소비자로 교체 |
| F6 | **검증** | `ai_reference_projection.build_learning` | 승인 조건이 호출자가 넘긴 `frozenset(sid)` 소속뿐입니다. 영수증·sha·단위 재검증이 없습니다. 테스트 `test_explicit_verified_path…`는 임의 문자열 `SITE_WATCH:invented-source`로 admission을 통과시킵니다. | 허가 우회(permit-bypass), 자기참조 검증 | `admit_verified(sid, receipt)`가 raw·단위·런타임 영수증을 재계산 |
| F7 | **검증** | 같은 함수 | 동일 `learning_id`에 다른 `insight`가 오면 `ValueError`로 투영 전체가 중단됩니다. 다른 출처 학습까지 함께 막힙니다. | 과차단 | 충돌은 `pending`에 기록하고 계속 진행 |
| F8 | **검증** | `ai_reference_projection` 정적 `LEARNING_PATTERNS` | 어시스턴트가 쓴 `insight` 약 22개를 `_support`가 용어 부분문자열·카테고리로 연결합니다. 새 게이트는 동적 경로만 막습니다. | 같은 우회 계열이 남아 있음 | 정적 패턴도 출처 단위 anchor 필수 |
| F9 | **검증** | `INDEX_SITE_WATCH_TEXT_LOCAL.py` | 격리 마커가 있으면 `every-ai-guides.vercel.app/posts/` 접두 URL을 전부 제외합니다. 이후 신규 글도 영구 제외됩니다. | 원문 발견성 단절 | 중립 어휘 색인은 포함(`RAW_UNREVIEWED`), 학습·FORMING만 차단 |
| F10 | **검증(경로)** | `tests/ai_reference_dynamic_provenance_regression_test.py` | 재료로 삼은 폐기 산출물이 없으면 `skipTest`로 조용히 건너뜁니다. | 가짜 PASS | 필수 피처를 고정 fixture로 |
| F11 | **검증** | `CURRENT/DATA/AI_LEARNING_PROJECTION.json` | 10-08 생성본, 57건. 새 키 없음. 다시 생성하면 동적 학습이 pending으로 이동해 규모가 달라집니다. | 이력과 현재가 혼동 | 재생성 후 diff를 증거로 첨부 |

## 4. 단계별 직접 평가

- **마이닝:** 의미 마이닝이 아니라 DOM 문단 발췌입니다. 출처 주장과 검증된 사실의 분리가 없습니다. 단계·코드·결과 구조도 없습니다. `trend_signals`는 어휘 2그룹 일치에 최대 7개 상한이며, 라벨(`LEXICAL_CANDIDATE_NOT_SEMANTICALLY_VERIFIED`)은 정직합니다.
- **인덱싱:** 중립 어휘 색인이라는 점은 괜찮습니다. 그러나 118편을 통째로 빼서 "분류+관계+출처" 요구를 충족하지 못합니다. 의미 분류는 마이닝이 풍부해진 뒤에 얹어야 합니다.
- **FORMING:** 기술 방법 결정 함수는 있습니다. 하지만 118편 입력이 연결돼 있지 않습니다. 확인한 범위는 `_forming`/`technical_method_decision`의 호출부까지입니다. 내부 게이트는 읽지 않았습니다.
- **학습:** 하드코딩 해석은 이제 pending에 격리됩니다. 개선입니다. 다만 원문 비교로 기존 구현을 개선하는 경로는 존재하지 않습니다.
- **결과 비교:** 원본↔개선 비교와 사용자에게 보이는 증거가 없습니다. 행 수와 PASS 수는 학습이 아닙니다.

## 5. 격리 방안 평가

- 격리 자체는 안전합니다. RAW 보존, 파생 보고서 6건 철회, 백업 3종, `allow_auto_learning_from_prior_reports:false`는 유지할 가치가 있습니다.
- 단, `stage_eligibility.index_active=EXCLUDE_UNTIL_SOURCE_REVIEW`는 과합니다. 인덱스는 중립(RAW_UNREVIEWED)으로 되돌리는 쪽이 사용자의 "누락 없음" 요구에 맞습니다.
- 과거 파생물(`EVERY_AI_*_20261017.*`)이 진실로 오인될 수 있는 위험은 격리 마커가 있는 한 낮습니다. 다만 마커를 읽는 곳이 학습 소비자 5개와 인덱서 정도입니다. 다른 소비자는 `reviews/` 디렉터리를 직접 열면 막을 장치가 없습니다(추정).

## 6. 우선순위 수정안 (이 순서)

1. **P0 `units_html` 확장** (`MINE_SITE_EVIDENCE_UNITS_LOCAL.py`)
   - `pre`/`code`(pre 밖), `table` 행, `img`(alt·src), 외부 `a[href]`를 `unit_kind`(CODE_BLOCK, TABLE_ROW, MEDIA_REF, EXTERNAL_REF)로 추출합니다.
   - 코드와 헤딩은 길이 제한을 면제하고, 900자 절단 대신 전문 sha와 연속 청크를 둡니다.
   - 양성 테스트: `<pre>npx designlang https://stripe.com</pre>`가 정확 텍스트로 CODE_BLOCK 단위가 됩니다. #73, #12 실제 원본으로 돌립니다.
   - 음성 테스트: pre를 일부러 제거한 사본은 커버리지 불일치로 실패합니다.
2. **P0 커버리지 게이트** (같은 파일, 출처별 필드)
   - 원문 구조 인벤토리(pre, table, img 개수)와 추출물을 대조해 `source_article_completeness`를 계산합니다. 상수 `False`를 없앱니다.
   - 불일치한 출처만 `MINING_INCOMPLETE`로 표시합니다. 다른 출처는 막지 않습니다.
3. **P0 LESSONS 제거와 결정론적 "방법 카드"** (`every_ai_method_learning.py` 대체)
   - 선작성 해석을 없애고, 타입 단위에서 단계 → 명령 → "성공하면…" 기대결과 → 필요 조건(Node 버전 등) → 외부 링크를 짝지어 냅니다.
   - 양성 테스트: #12가 STEP 1~5와 명령, 기대결과가 연결된 카드를 냅니다.
   - 음성 테스트: 명령이 없는 글은 카드를 만들지 않습니다.
4. **P1 admission 검증기** (`build_learning` + 두 호출부)
   - `verified_dynamic_source_ids`를 `{sid: receipt}`로 바꿉니다. `build_learning`이 raw sha, 단위 sha, 런타임 영수증을 재계산합니다.
   - ID 충돌은 pending으로 보냅니다.
   - 음성 테스트: 임의 sid는 pending이 됩니다. 양성 테스트: 기존 `central_review_source_intake` 영수증 경로는 그대로 통과합니다.
5. **P1 인덱스 중립 포함** (`INDEX_SITE_WATCH_TEXT_LOCAL.py` 접두 제외 규칙)
   - 격리 단계의 인덱스 항목을 `RAW_UNREVIEWED`로 포함하고, 학습·FORMING 입력에서만 제외합니다.
   - 검증: 118편이 색인에서 검색되는지, 학습 투영에는 0건인지를 둘 다 확인합니다.

**해체하면 안 되는 것:** RAW 캡처와 sha 감사, 세대(generation)+sha 포인터 방식, 격리 마커와 백업, `pending_dynamic_learning_review` 회계, 영수증 4건 기반 `central_review_source_intake` 경로, 기존 테스트 자산.

**대표 비교 후보:** #73 designlang(`npx designlang <URL>` → DTCG 토큰·Tailwind·DESIGN.md)을 Hide & Seek의 `styles.css`/`hide-runtime.css` 토큰과 비교하는 것입니다.
- 확인된 것: `styles.css`에 CSS 커스텀 프로퍼티 선언이 5개 있습니다.
- 아직 안 열어본 것: 실제 값, 그리고 designlang 실행 가능 여부(설치·네트워크 필요).
- 설치 없이도 기존 CSS에서 DTCG 토큰 JSON을 만들어 전/후 diff로 보이는 비교는 가능해 보입니다(추정).

## 7. 기존 게이트: 실제 강제 vs 우회 vs 거짓 성공

- **실제 강제:** 격리 마커 검증(스키마·상태), `build_learning`의 비-검증 동적 주장 pending 격리, 정규 승인 전 `canonical_promotion:false`.
- **우회 가능:** 호출자가 집합만 넘기면 admission, 정적 패턴(부분문자열 매칭), 격리 마커 밖 경로의 `reviews/` 직접 읽기.
- **거짓 성공 위험:** `skipTest`, 자기참조 검증 테스트, `source_article_completeness` 상수, `evidence_extracted:True`(문단 발췌만 한 상태).

## 8. 이전 "완료" 학습은 진짜였나

**아니요.** 직접 확인한 근거는 세 가지입니다.
- `insight`가 코드에 선작성돼 있습니다.
- 인용이 제목·수사 문장이라 주장과 맞지 않습니다.
- 원문의 실제 메커니즘(`<pre>`)이 마이닝에서 빠졌습니다.

격리 마커(`why`)도 같은 결론을 기록합니다.

## 9. 추가 조사 필요 (전체 118편 의미 검토는 하지 않음)

- 이전 마이닝 세대(`SITE_MINING_EVIDENCE.71d77e…`)에 118편이 실제로 있었는지, 열어보지 않았습니다.
- `taky_gate.py`, `runtime_orchestrator.py`의 학습 관련 강제 범위, 그리고 FORMING 내부 게이트.
- `INDEX_OWNER_REVIEW_QUEUE_ACTIVE`가 가리키는 세대 내용.
- #20(모션)의 이미지 13장이 실제 재생 가능한 클립인지.
- #7, #31, #75, #106의 본문 의미 분석은 구조 수치(pre·표 개수)만 확인했습니다.

BEGIN_AUDIT_JSON
{
 "status": "FAIL_UNVERIFIED_LEARNING_NOT_GENUINE",
 "findings": [
  {"severity":"P0","file":"TAKY-SOURCE-VAULT/MINE_SITE_EVIDENCE_UNITS_LOCAL.py::units_html","defect":"셀렉터가 pre/code/table/img/a를 제외. 118편 복제 시 pre 826개 중 약 796개(약 99.5% 문자) 누락, 표 105, 이미지 44 미추출","remedy":"unit_kind 타입 단위 추가, 코드·헤딩 길이 제한 면제, 전문 sha+연속 청크"},
  {"severity":"P0","file":"TAKY-SOURCE-VAULT/MINE_SITE_EVIDENCE_UNITS_LOCAL.py::units_html","defect":"len<45 폐기(3158블록), excerpt[:900] 절단, 텍스트 dedupe, source_article_completeness 상수 False","remedy":"원문 구조 인벤토리 대조 커버리지 게이트로 완전성 계산"},
  {"severity":"P0","file":"TAKY/LEARNING/intake/every_ai_method_learning.py::LESSONS","defect":"선작성 해석 12개를 1단어 needle 첫 일치 문장으로 근거화(제목·수사 문장 인용)","remedy":"LESSONS 제거, 타입 단위에서 결정론적 방법 카드(단계·명령·기대결과·요건·링크) 도출"},
  {"severity":"P1","file":"TAKY/ENFORCEMENT/ai_reference_projection.py::build_learning","defect":"verified_dynamic_source_ids는 호출자 제공 집합일 뿐 영수증·sha 재검증 없음. 임의 sid가 admission 통과 가능","remedy":"admit_verified(sid, receipt)로 raw·단위·런타임 영수증 재계산"},
  {"severity":"P1","file":"TAKY/ENFORCEMENT/ai_reference_projection.py::build_learning","defect":"동일 learning_id 다른 insight 충돌 시 ValueError로 투영 전체 중단(과차단)","remedy":"충돌은 pending_dynamic_learning_review에 기록하고 계속"},
  {"severity":"P1","file":"TAKY/ENFORCEMENT/ai_reference_projection.py::LEARNING_PATTERNS/_support","defect":"정적 약 22개 해석이 부분문자열·카테고리로 연결되는 동일 우회 계열이 미처리","remedy":"정적 패턴에도 출처 단위 anchor 요구"},
  {"severity":"P1","file":"TAKY-SOURCE-VAULT/INDEX_SITE_WATCH_TEXT_LOCAL.py","defect":"격리 시 every-ai 접두 URL을 색인에서 전부 영구 제외, 신규 글도 제외","remedy":"중립 어휘 색인에 RAW_UNREVIEWED로 포함, 학습·FORMING 입력에서만 제외"},
  {"severity":"P1","file":"TAKY/LEARNING/intake/every_ai_method_learning.py::main","defect":"격리 마커로 SystemExit. 마커 없이도 build_learning에 검증 집합이 없어 마지막 assert가 실패할 것으로 읽힘(미실행)","remedy":"파일 폐기 또는 신규 소비자로 교체"},
  {"severity":"P1","file":"TAKY/ENFORCEMENT/ai_reference_dynamic_provenance_regression_test.py","defect":"폐기 산출물 부재 시 skipTest, 임의 문자열 sid로 admission 통과를 정상으로 기대","remedy":"고정 fixture로 교체, 영수증 없는 sid의 pending 이동을 음성 테스트로"},
  {"severity":"P1","file":"TAKY/CURRENT/DATA/AI_LEARNING_PROJECTION.json","defect":"2026-10-08 생성본(57건), pending_dynamic_learning_review 키 없음. 새 게이트 이전 산출물이 CURRENT에 존재","remedy":"재생성 후 diff를 증거로 보존"},
  {"severity":"P1","file":"Hide & Seek / TAKY (소비 단계)","defect":"AI_LEARNING_PROJECTION을 읽는 앱 소비자를 확인하지 못함. 학습→소비 화살표 없음","remedy":"디자인 토큰 비교 같은 대표 사례로 전/후 증거를 만드는 소비 단계 연결"}
 ],
 "verified_scope": [
  "units_html 셀렉터와 118편 원본 대조(복제, pre/table/img 통계)",
  "LESSONS와 저장된 인용 12건",
  "build_learning의 admission·pending 로직과 호출부 3곳",
  "SITE_MINING_EVIDENCE_ACTIVE 포인터(27출처, every-ai 0)",
  "INDEX_SITE_WATCH_TEXT_LOCAL 격리 처리",
  "격리 마커 stage_eligibility",
  "#12 REA, #73 designlang 본문 구조"
 ],
 "untested_scope": [
  "이전 마이닝 세대 71d77e…의 118편 포함 여부",
  "taky_gate.py·runtime_orchestrator.py·FORMING 내부 게이트",
  "INDEX_OWNER_REVIEW_QUEUE 세대 내용",
  "#7, #20, #31, #75, #106 본문 의미 분석(구조 수치만 확인)",
  "Hide & Seek 토큰 값과 designlang 실행 가능 여부",
  "118편 전체 의미 검토(수행하지 않음)"
 ]
}
END_AUDIT_JSON
