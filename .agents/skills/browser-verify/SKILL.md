---
name: browser-verify
description: Verify a web UI in the real browser instead of trusting code or build output.
---
Open the target app at the required viewport.
Inspect DOM state, visible layout, console errors, network failures, and interaction outcomes.
Exercise the critical user path and edge states.
Compare against approved visual/interaction references when available.
Record observed evidence and exact defects.
Do not call PASS when the browser/runtime was not actually observed.
