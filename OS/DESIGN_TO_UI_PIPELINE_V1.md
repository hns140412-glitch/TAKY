# TAKY DESIGN-TO-UI PIPELINE V1

Status: DRAFT / CENTRAL EXECUTION CONTRACT / NO MAIN MERGE / NO NETLIFY / NO IMAGE GENERATION

## 목적
사용자가 시안을 확정한 뒤 실제 UI가 그 시안과 기능 계약을 따라 완성될 때까지의 **한 줄 실행 파이프라인**이다.

이 파이프라인은 디자인을 다시 만드는 절차가 아니다.
승인된 시안을 잠그고, 구현하고, 실제 브라우저 결과를 검증하고, 차이가 있으면 구현으로 되돌린 뒤 Design PASS를 발급한다.

USER != DEBUGGER.

## 최종 5단계
`1 APPROVAL LOCK → 2 UI CONTRACT → 3 IMPLEMENT → 4 VERIFY / CORRECT → 5 DESIGN PASS`

Release / Deploy는 이 파이프라인 밖의 별도 Gate다.

### 1) APPROVAL LOCK
한 번만 확정한다.
- 승인 시안 / authority
- Golden 또는 승인 reference
- SHA-256
- 승인 화면 / viewport 범위
- 승인 production asset / Visual ID
- 제외 범위

금지:
- runtime screenshot을 Golden으로 승격
- 승인되지 않은 crop/재생성물을 Golden으로 대체
- composite mockup을 production background로 사용

### 2) UI CONTRACT
구현 전에 필요한 계약을 **하나의 manifest 계보**로 잠근다.

포함:
- screen contract
- layer/asset binding
- viewport / safe area
- state fixture
- state별 `visual_policy / interaction_policy / responsive_policy`
- interaction
- responsive rule
- accessibility / motion requirement
- stable selector / component owner

authority는 `design-to-ui.json` 하나가 가리킨다.

### 3) IMPLEMENT
실제 DOM/CSS/runtime을 작성한다.

원칙:
- 기능 텍스트와 컨트롤은 live UI
- 승인 에셋은 승인된 경로/Visual ID만 사용
- missing art = `ASSET_PRODUCTION_OPEN`
- 승인 에셋 미연결 = `ASSET_IMPORT_OPEN`
- 코드/slot 미구현 = `IMPLEMENTATION_OPEN`
- placeholder를 승인 결과로 취급하지 않음

이미지 생성이 막혀 있어도 나머지 구현은 계속 가능하다.

### 4) VERIFY / CORRECT
중앙 실행기 하나가 순서대로 수행한다.

`contract validate
→ app capture adapter
→ matched-viewport Visual Compare
→ interaction evidence
→ responsive evidence
→ asset-integrity evidence`

실패 시 자동 임의수정하지 않고 owner에 라우팅해 IMPLEMENT로 되돌린다.

- source / asset mismatch → APPROVAL LOCK 또는 UI CONTRACT
- layout / typography / z-order → IMPLEMENT
- state / interaction mismatch → IMPLEMENT
- responsive clipping → UI CONTRACT 또는 IMPLEMENT
- missing evidence → 해당 adapter

Visual Compare:
- Golden과 실제 render 동일 pixel dimensions
- implicit resize/crop 금지
- full-frame + critical ROI
- diff evidence 저장
- global score 하나로 critical failure 은폐 금지

### 5) DESIGN PASS
다음 실제 evidence가 전부 PASS일 때만 Receipt 발급:
- VISUAL
- INTERACTION
- RESPONSIVE
- ASSET_INTEGRITY

수동 `--pass` 플래그는 evidence가 아니다.

## 실행 구조
중앙 TAKY가 소유:
- contract validator
- Visual Compare
- pipeline runner
- Design Receipt issuer
- 공통 schema / regression

각 앱이 소유:
- 실제 browser capture 명령
- interaction test 명령
- responsive test 명령
- asset-integrity test 명령
- capture 결과 파일과 screen/state/viewport의 매핑

앱은 PASS JSON을 만들지 않는다.
중앙 Runner가 명령의 실제 종료코드와 manifest coverage를 근거로 render-manifest / evidence / Receipt를 생성한다.

## Adapter protocol
각 앱은 `design-ui-adapter.json` 하나만 제공한다.

필수 선언:
- `capture.command`: 실제 브라우저 캡처 테스트
- `capture.artifacts[]`: 생성된 screenshot을 screen/state/viewport에 매핑
- `checks.interaction.command` + 담당 `coverage[]`
- `checks.responsive.command` + 담당 `coverage[]`
- `checks.asset_integrity.command` + 담당 `coverage[]`

명령은 shell string이 아니라 argv array다. 중앙 Runner는 `shell=False`로 실행한다.

각 check의 `coverage[]`는 manifest가 요구하는 범위와 정확히 일치해야 한다. 누락/과잉 선언은 CONTRACT_BLOCKED다. 해당 검증이 모든 state에서 `NOT_APPLICABLE`이면 빈 배열도 허용한다.

앱이 직접 만들 필요가 없는 것:
- render-manifest
- VISUAL evidence
- INTERACTION evidence
- RESPONSIVE evidence
- ASSET_INTEGRITY evidence
- Design Receipt

이들은 모두 중앙 Runner가 생성한다. 따라서 기존처럼 실제 테스트 후 `--interaction-pass` 등을 다시 주입하는 이중 판정은 제거한다.

## 최소 파일
필수:
- `design-to-ui.json`
- `design-ui-adapter.json`
- manifest가 참조하는 screen/layer/fixture contracts

자동 생성:
- `ui-audit/contract-validation.json`
- `ui-audit/render-manifest.json`
- `ui-audit/visual-result.json`
- `ui-audit/interaction-result.json`
- `ui-audit/responsive-result.json`
- `ui-audit/asset-result.json`
- `ui-audit/design-receipt.json`
- `ui-audit/pipeline-status.json`

`ui-audit/`는 실행 시작 시 중앙 Runner가 **전체 삭제 후 재생성**한다. 이전 실행의 screenshot/evidence/receipt는 재사용하지 않는다. capture artifact 경로도 `ui-audit/` 아래만 허용한다.

## Revision binding
중앙 Runner는 실행 시 실제 Git HEAD와 worktree 상태를 기록한다.

- 모든 Evidence에 `tested_revision` 저장
- 모든 Evidence에 `worktree_dirty` 저장
- 서로 다른 revision의 Evidence 혼합 금지
- dirty worktree에서도 가능한 검증은 수행할 수 있으나 최종 Design Receipt는 발급 금지
- Git revision을 확인할 수 없는 환경에서도 독립 검증은 가능하지만 Design PASS는 금지

`source_commit`은 manifest가 가리키는 구현/authority 계보이고, `tested_revision`은 **이번 검증이 실제로 실행된 repository revision**이다. 둘을 같은 개념으로 취급하지 않는다.

## Pipeline status
중앙 runner는 다음 중 하나만 기록한다.
- `CONTRACT_BLOCKED`
- `CAPTURE_BLOCKED`
- `VISUAL_BLOCKED`
- `INTERACTION_BLOCKED`
- `RESPONSIVE_BLOCKED`
- `ASSET_BLOCKED`
- `RECEIPT_BLOCKED`
- `DESIGN_PASS`

이 상태가 작업 위치다. 별도 중복 상태표를 만들 필요가 없다.

실패 상태에는 `routing`을 함께 기록한다:
- `return_to_stage`: APPROVAL_LOCK / UI_CONTRACT / IMPLEMENT / VERIFY_CORRECT
- `owner`: AUTHORITY / UI_CONTRACT / ASSET_CONTRACT / UI_IMPLEMENTATION / APP_ADAPTER / PIPELINE
- `next_action`: 다음 수정 작업

부분 재개 체크포인트는 만들지 않는다. 수정 후에는 항상 전체 Runner를 다시 실행한다. 앞 단계는 결정적 검증이므로 재실행 비용보다 상태 분기/중복을 줄이는 것을 우선한다.

### OPEN 처리 원칙
`ASSET_PRODUCTION_OPEN`, `ASSET_IMPORT_OPEN`, `IMPLEMENTATION_OPEN`, `GOLDEN_IMPORT_OPEN`은 **최종 Design PASS 차단 사유**이지, 무조건 전체 작업 중단 사유가 아니다.

- contract 자체가 invalid하면 즉시 중단
- contract는 valid하지만 OPEN blocker가 있으면 가능한 독립 검증은 계속 수행
- blocker 때문에 의미 없는 Visual Compare는 `deferred` 처리
- interaction / responsive / asset-integrity 등 독립 검증은 계속 수행
- 최종 Receipt는 blocker가 0개일 때만 발급

즉 이미지 생성이 제한되어도 나머지 파이프라인은 전진할 수 있다.

## 범위 밖
Design-to-UI Pipeline이 판단하지 않는 것:
- OCR 정확도
- Planner/Learning 정책
- IndexedDB/business data correctness
- 인증
- PWA/offline
- Netlify
- release/deployment

이들은 Design Receipt 이후 별도 Release Gate가 소비한다.

## Hard failures
- 승인 source/SHA 불일치
- runtime render의 Golden 승격
- flattened mockup을 interactive production UI로 사용
- production asset provenance/hash 없음
- required state/viewport capture 누락
- critical ROI 실패
- evidence 파일 없이 수동 PASS
- 이전 실행의 ui-audit/evidence 재사용
- capture artifact가 ui-audit 밖에 존재
- 최종 Receipt 발급 시 Git revision 미확인 또는 dirty worktree
- 서로 다른 tested_revision evidence 혼합
- 앱 adapter 결과 schema 불충족
- Design PASS를 Release PASS로 취급
- 사용자를 구현 디버거로 사용

## 현재 HOLD
- image generation: HOLD
- main merge: HOLD
- Netlify/deployment: HOLD
- release claim: HOLD

이 HOLD들은 파이프라인 자체 구축과 검증을 막지 않는다.
