# TAKY UI 디자인게이트 실행기 (TAKY_UI_DESIGN_GATE_V1)

TAKY DESIGN_GATE 계약 중 화면(UI_IMPLEMENTATION)에 해당하는 항목을 실제로 검사하는 실행기다.
계약 원문: `D:\Git PWA\TAKY\.claude\TAKY_DESIGN_GATE_R2_SUMMARY_20261004.txt` (DG-00~10, PS-00~23).

- 로컬 전용: 업로드, 모델 호출, 배포 없음. 127.0.0.1 임시 서버로 페이지를 UTF-8로 띄운다.
- 무거운 브라우저 작업이므로 **렌더 PC에서 실행**한다.

## 실행

```
node ui_design_gate.cjs <spec.json> [--out 폴더] [--previous 이전_DG_RECEIPT.json]
```

종료 코드: 0 = PASS(경고 포함 가능), 1 = FAIL, 2 = 실행 오류.
결과: `<out>/DG_RECEIPT.json` + `<out>/shots/*.png`.

Playwright는 `PLAYWRIGHT_MODULE` → 로컬 `playwright` → 전역 `@playwright/mcp` 순서로 찾고,
브라우저는 번들 → 시스템 Chrome → Edge → `CHROME_PATH` 순서로 띄운다.

## 검사 항목 (영수증 subreceipts)

| 항목 | 계약 | 검사 |
|---|---|---|
| HARNESS_HEALTH | DG-08 | 모든 화면 준비 완료, 콘솔 오류·HTTP 4xx/5xx 0건 (favicon 제외) |
| TARGET_RENDER | DG-08 | 뷰포트별 가로 스크롤 없음, `expectText`/`forbidText` |
| INTERACTION | DG-08 | `interactions` 단계(click/press/focus → expectVisible/Hidden/Attr/Text) |
| A11Y | DG-08, PS14 | 200% 확대 리플로우, 글자 간격(WCAG 1.4.12), 터치 영역(24px 미만 FAIL·44px 미만 경고), 명암비 4.5/3.0, ARIA 오용·이름 없는 컨트롤·alt·lang, 키보드 포커스 표시 |
| VISUAL_COMPARE | PS20 | 기준 화면과 픽셀 비교. `expectedChange`가 있으면 경고로 남기고 소유자 승인 필요 |
| PERFORMANCE_CONTEXT | DG-08 | 로컬 로딩 시간·요청 수 (현장 성능 아님) |
| FONT_PRINT_PDF | DG-08 | 화면 전용이면 N/A |
| DEVICE_OR_RUNTIME | DG-08 | 항상 OPEN으로 시작. 실기기·소유자 확인을 받은 뒤 영수증에 기록 |

DG-09: `--previous`로 이전 영수증을 주면 사양·산출물 해시가 바뀐 경우 `STALE`로 표시한다.
PS23: 영수증에 사양 sha256과 산출물 sha256이 들어간다.

## 사양 파일 (spec.json)

```json
{
  "name": "화면이름",
  "serveRoot": ".",
  "artifacts": ["app/view.html"],
  "inject": "stub.js",
  "ready": "document.documentElement.dataset.ready==='1'",
  "viewports": [320, 390, 768],
  "pages": [{"id": "main", "url": "app/view.html?s=full", "expectText": ["제목"], "forbidText": ["ERROR"]}],
  "interactions": [{"name": "탭전환", "page": "main", "steps": [{"click": "#tabB"}, {"expectVisible": "#panelB"}]}],
  "baselines": [{"page": "main", "url": "baseline/view.html?s=full", "file": "baseline/view.html", "expectedChange": "변경 사유"}],
  "thresholds": {"targetMin": 24, "targetRecommended": 44, "zoom": 2}
}
```

- 경로는 사양 파일 기준 상대 경로. 페이지는 `serveRoot` 아래에 있어야 한다.
- `inject`: 서버 API(예: Apps Script `google.script.run`)를 고정 시나리오로 대신하는 스크립트.

## 자체 테스트

```
node tests/ui_design_gate.test.cjs
```

정상 화면 PASS, 결함 화면 FAIL(10가지 사유), 산출물 변경 시 이전 영수증 STALE을 확인한다.

## 한계

브라우저 하네스 결과이며 실기기 확인을 대신하지 않는다. 화면 판단(디자인 품질·브랜드 적합성)은 사람 검토가 필요하다.
