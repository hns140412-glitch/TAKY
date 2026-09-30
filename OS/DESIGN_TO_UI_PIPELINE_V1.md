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
- browser capture adapter
- interaction adapter
- responsive adapter
- asset-integrity adapter

앱 adapter는 UI를 판정하지 않고 정해진 schema의 결과 파일만 만든다.
최종 판정은 중앙 runner가 한다.

## Adapter protocol
각 앱은 `design-ui-adapter.json` 하나만 제공한다.

필수 command:
- `capture`
- `interaction`
- `responsive`
- `asset_integrity`

명령은 shell string이 아니라 argv array로 선언한다.
중앙 runner는 shell을 사용하지 않는다.

고정 출력:
- `ui-audit/render-manifest.json`
- `ui-audit/interaction-result.json`
- `ui-audit/responsive-result.json`
- `ui-audit/asset-result.json`

VISUAL evidence는 중앙 Visual Compare가 생성한다.

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
- 앱 adapter 결과 schema 불충족
- Design PASS를 Release PASS로 취급
- 사용자를 구현 디버거로 사용

## 현재 HOLD
- image generation: HOLD
- main merge: HOLD
- Netlify/deployment: HOLD
- release claim: HOLD

이 HOLD들은 파이프라인 자체 구축과 검증을 막지 않는다.
