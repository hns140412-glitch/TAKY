---
version: alpha
name: t3-ops-board dashboard template
taky:
  mode: EXPLORE
  design_system_id: TAKY_DASH_TEMPLATE_T3_OPS_BOARD
  version: 0.1.0
  source_commit: candidate
  thresholds:
    min_font_px: 13
    premium:
      chars: 600   # ops board is a dense table by design (T3)
colors:
  bg: "#f6f7f8"
  surface: "#ffffff"
  ink: "#16191c"
  sub: "#596168"
  accent: "#2f5bd3"
  done: "#1f7a4d"
  open: "#9a5b00"
typography:
  body:
    fontFamily: Noto Sans KR
    fontSize: 15px
dashboard:
  template: T3_OPS_BOARD
  question: "Taky가 지금 결정할 것은? 결정 대기 → 앱별 상태 사다리 한 줄."
  decision_metric: see Layout
  max_focal_points: 2
  max_kpis_first_viewport: 3
  max_filled_cta: 1
---

## Layout

Taky가 지금 결정할 것은? 결정 대기 → 앱별 상태 사다리 한 줄. Summary before detail. One accent use per screen.

## Do's and Don'ts

- Don't show a false zero; explain missing data.
- Never use colors outside the palette, gradients, text shadows or card grids for progress.
