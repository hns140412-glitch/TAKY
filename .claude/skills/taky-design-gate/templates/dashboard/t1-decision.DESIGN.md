---
version: alpha
name: t1-decision dashboard template
taky:
  mode: EXPLORE
  design_system_id: TAKY_DASH_TEMPLATE_T1_DECISION
  version: 0.1.0
  source_commit: candidate
  thresholds:
    min_font_px: 13
colors:
  bg: "#f9fbfa"
  surface: "#ffffff"
  line: "#e6ecea"
  text: "#14201f"
  sub: "#5f6e72"
  teal: "#0f6e6a"
  ok: "#1d8f55"
  warn: "#a85d12"
  over: "#b3261e"
typography:
  body:
    fontFamily: Noto Sans KR
    fontSize: 15px
dashboard:
  template: T1_DECISION
  question: "이번 달 계획 안에 있나? 답 문장 → 남은 돈 → 범주별 남은 예산 → 예외 → 기록 1개."
  decision_metric: see Layout
  max_focal_points: 2
  max_kpis_first_viewport: 3
  max_filled_cta: 1
---

## Layout

이번 달 계획 안에 있나? 답 문장 → 남은 돈 → 범주별 남은 예산 → 예외 → 기록 1개. Summary before detail. One accent use per screen.

## Do's and Don'ts

- Don't show a false zero; explain missing data.
- Never use colors outside the palette, gradients, text shadows or card grids for progress.
