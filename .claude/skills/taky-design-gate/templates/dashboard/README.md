# Dashboard templates (DGC-30)

`MASTER/UI_REFERENCE_PROTOCOL.md` §20.1e. Status: `PILOT_FIXTURE_ONLY` (EXPLORE). Pick by audience, then replace tokens, copy and art with the app's approved ones.

| File | Audience | Question it answers | Decision metric |
|---|---|---|---|
| `t1-decision.html` | Parent / household money (SAVEY-type) | Are we on plan this month? | Money left, with month-pace marker |
| `t2-world-hub.html` | Child (Play Camp / Hide hub type) | Where do I go today? | Next place on the trail; lanterns 7/12 |
| `t3-ops-board.html` | Operations / Taky | What do I need to decide now? | Decisions waiting; per-app ladder IMPLEMENTED → VERIFIED → DEVICE → RELEASED |

All numbers are example values. T3 rows were copied from TAKY_AI_CURRENT DELTA 2026-11-11 and must be re-read before use.

Check one:

```bash
python3 ENFORCEMENT/design_gate_harness.py --design .claude/skills/taky-design-gate/templates/dashboard/t1-decision.DESIGN.md \
  --target .claude/skills/taky-design-gate/templates/dashboard/t1-decision.html --out /tmp/t1 \
  --viewports '[{"id":"phone","width":390,"height":844}]'
```

Harness PASS is mechanical only. The reviewer still checks DGC-25 (decision metric largest), DGC-26 (statement and numbers agree) and DGC-29 (one symbol, one meaning).
