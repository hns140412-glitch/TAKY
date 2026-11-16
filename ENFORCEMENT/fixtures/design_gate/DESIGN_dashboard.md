---
version: alpha
name: Gate Fixture
taky:
  mode: EXECUTE
  design_system_id: GATE_FIXTURE
  version: 1.0.0
  source_commit: fixture
colors:
  ink: "#1A1C1E"
  paper: "#FFFFFF"
  accent: "#B8422E"
dashboard:
  template: T1_DECISION
  question: "이번 달 계획 안에 있나?"
  decision_metric_selector: ".left"
  status_check:
    status: ".status"
    burn_pct: ".bar@aria-valuenow"
    elapsed_pct: ".pace@style"
typography:
  body:
    fontFamily: DejaVu Sans
    fontSize: 16px
---

## Layout

Single column, max 640px, left aligned. One accent use per screen.

## Do's and Don'ts

- Do keep one focal point per screen.
- Don't use gradients, gradient-clipped text or mask-image.
- Never introduce colors outside the palette.
