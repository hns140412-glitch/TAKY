# Ready & Set C2S Resume Reflection — 2026-09-19

Status: C2S COMPILE / DEVICE GATE READY  
Ledger: `HISTORY/2026-09-19_READY_SET_C2S_LEDGER.json`

## Current product truth
- Ready & Set safe/runtime commit held fixed for device validation: `3d96878ada0458196ff8bfc68fdcf7087ea4d1ca`.
- Five current product regression workflows: SUCCESS.
- Exact-head package workflow: SUCCESS.
- Confirmed timer UI remains locked.
- Main merge / production deploy remain HUMAN APPROVAL gates.

## Dedicated staging auth issue — superseded as device blocker
The dedicated project `ready-set-staging-taky` still cannot be updated from GitHub Actions because `NETLIFY_AUTH_TOKEN` is absent. Its fail-closed workflow remains valid evidence that no stale or unauthorized deploy occurred.

However this no longer blocks device validation.

## Git-backed Deploy Preview workaround — READY
Existing Git-backed Netlify project:
`profound-ganache-902032`

A staging-only branch and Draft PR were created without changing main:
- branch: `taky-staging-device-2026-09-19`
- Draft PR: #5 — STAGING ONLY / DO NOT MERGE
- source commit: `3d96878ada0458196ff8bfc68fdcf7087ea4d1ca`
- Netlify deploy id: `6aadb57c9d58a60008f93fae`
- context: `deploy-preview`
- review_id: `5`
- state: `ready`
- alias: `https://deploy-preview-5--profound-ganache-902032.netlify.app`

Netlify reports the exact commit_ref and branch. The deployed source uses `netlify.toml` with `publish="."` and no build command, so static runtime files are published from that exact Git tree.

Expected source parity at that commit:
- app version: `0.9.4-rc25`
- cache: `ready-set-v094-rev07-staging28-runtime-hardening-v1`
- rejected `ready-focus-tools-v1.js`: absent from index and service-worker precache
- current runtime and recording modules: present in service-worker precache
- Netlify functions deployed: character-candidates / homework-analysis / time

Automated direct HTTP spot-fetch of the preview URL is unavailable from the current tool runtime. This limitation is recorded and is not misrepresented as a live browser fetch.

## Active gate
`SOURCE/CI PASS -> GIT-BACKED DEPLOY PREVIEW READY -> IPHONE/PWA DEVICE VALIDATION`

Actual iPhone/PWA behavior is the next active gate.

Device-only checks:
- background / foreground continuity
- screen lock / restore
- reload with active session
- native share sheet / Kakao handoff where available
- iOS recording MIME/container and filename truth
- original + transfer recording behavior
- microphone acoustics / local DSP observation
- actual BGM playback
- PWA cache/update behavior

The user is not to be used as a developer/debugger. Only narrow product-use confirmations should be requested.

## Preserved HOLD
Weekly/daily schedule structure direction remains known but final visual design is still HOLD and must not be silently promoted.

## Coverage closure
- material atoms: 14
- mapped material: 14
- unmapped material: 0
- silent loss: 0
- false convergence: 0
- unresolved OPEN/HOLD: 2

Reverse reconstruction: PASS for this declared resume scope.

END


## Correction — false Home Screen PASS revoked
An earlier assistant judgment incorrectly treated a Home Screen screenshot as proof that the staging PWA had been installed. The user correctly identified that the icon launched the existing main/production PWA.

Root cause:
- production/main and preview used the same visible app identity: `Ready & Set`
- same icon
- same Apple web app title
- therefore screenshot-only visual confirmation could not prove staging provenance

The PASS was revoked.

## Staging-only PWA identity overlay
To remove ambiguity without modifying the product runtime branch, Draft PR #5's staging branch now carries a staging-only identity overlay:

- branch HEAD: `f1d057ee493d95f12e25ed74ad0ee7e2727ac4c0`
- manifest id: `ready-set-staging-preview-5`
- name: `Ready & Set STAGING`
- short name: `R&S STAGING`
- start URL: `./?staging=preview-5`
- Apple web app title: `R&S STAGING`
- deploy id: `6aadb800fee3ea0008aee104`
- Netlify state: `ready`
- GitHub Netlify status: `success`
- PR #5 remains Draft / OPEN / UNMERGED
- main and production remain unchanged

Device validation should use the immutable deploy permalink for this deploy rather than the production PWA or an ambiguous Home Screen icon.
