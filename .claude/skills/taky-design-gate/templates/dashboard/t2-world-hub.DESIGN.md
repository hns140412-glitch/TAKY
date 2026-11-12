---
version: alpha
name: t2-world-hub dashboard template
taky:
  mode: EXPLORE
  design_system_id: TAKY_DASH_TEMPLATE_T2_WORLD_HUB
  version: 0.1.0
  source_commit: candidate
  thresholds:
    min_font_px: 13
colors:
  sky: "#e3f5fc"
  sea: "#1d87a8"
  ink: "#0f2e36"
  sub: "#4a6066"
  lit: "#e8743b"
  white: "#ffffff"
typography:
  body:
    fontFamily: Noto Sans KR
    fontSize: 15px
dashboard:
  template: T2_WORLD_HUB
  question: "오늘 어디로 갈까? 섬 지도 위 구역별 등불 → 탐험 시작 1개."
  decision_metric: see Layout
  max_focal_points: 2
  max_kpis_first_viewport: 3
  max_filled_cta: 1
---

## Layout

오늘 어디로 갈까? 섬 지도 위 구역별 등불 → 탐험 시작 1개. Summary before detail. One accent use per screen.

## Do's and Don'ts

- Don't show a false zero; explain missing data.
- Never use colors outside the palette, gradients, text shadows or card grids for progress.
