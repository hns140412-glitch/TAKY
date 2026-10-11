---
name: runtime-e2e
description: Run bounded end-to-end verification for TAKY features and integrations.
---
Derive E2E cases from acceptance criteria and known regression risks.
Test the integrated path, not only isolated modules.
Include restart/retry/offline/multi-device/auth cases only when applicable.
On failure, isolate root cause before changing code.
Re-run the failed case plus the smallest relevant regression set.
Distinguish IMPLEMENTED, CI_VERIFIED, RUNTIME_VERIFIED, DEVICE_VERIFIED.
