---
name: mobile-webapp-build
description: Build TAKY mobile web-app features from approved contracts through runtime verification.
---
Load approved project contract, design/asset authority, and mobile registry.
Do not regenerate approved assets or redesign locked UI.
Translate requirements into acceptance tests before implementation.
Implement the smallest sufficient diff.
Validate lint/typecheck/build/tests plus actual mobile viewport output.
Navigation/open alone is not render verification: observe a screenshot/snapshot/DOM result at the target viewport.
When the requested feature is interactive, exercise the critical click/tap/input/transition path and observe the resulting state.
Check safe-area, touch targets, keyboard, navigation, persistence/offline behavior when applicable.
A screenshot alone proves appearance only; a successful build alone proves buildability only. Neither is full runtime PASS.
