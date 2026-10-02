# TAKY PWA STORAGE & DISTRIBUTION SYNC POLICY — 2026-10-02

Status: BETA CONTRACT / NO DEPLOY AUTHORIZATION

## Fixed ownership
- GitHub: code, schema, manifest pointers, governance.
- Netlify: PWA shell/runtime delivery only. Not primary DB or Drive authority.
- HNS Drive / TAKY: admin/internal master, long-term sources, curated learning and ARCHIGROW data, COMMON/CURRENT/HANDOFF, temp and delete-pending review.
- SIEZEALL Drive / TAKY: approved app-internal distribution, changed packages, user-sync material.
- SAVEY: separate top-level root in both accounts. No implicit TAKY routing.
- Device local DB: interaction state, offline data, pending outbox, cached projections and installed package metadata.
- Cache Storage: URL-addressable static assets only; not authoritative user data.

## PWA runtime rule
PWA interaction must remain usable from local state. Remote synchronization must not block ordinary user interaction.

Write path:
DEVICE LOCAL COMMIT -> SYNC_QUEUE -> authenticated/approved sync adapter -> ACK -> local projection update.

Package/update path:
HNS APPROVED MASTER -> SIEZEALL DISTRIBUTION PACKAGE -> manifest/version comparison -> changed package only -> SHA-256 verification -> safe-point activation -> atomic swap -> retain previous known-good package.

## Wi-Fi gate
Automatic package download is allowed only when Wi-Fi is positively confirmed.
- confirmed Wi-Fi: automatic download may proceed.
- offline: wait.
- cellular/other: wait.
- online but network type unknown: automatic package download waits.
- Save-Data enabled: wait.
- explicit user action may be handled separately by product UX, but must never reveal provider credentials or Drive folder structure.

Browser network APIs are advisory capability signals, not trust/security boundaries. If Wi-Fi cannot be proven, fail closed for automatic package download and continue using the installed local package.

## Visibility/security boundary
The user sees app-level states only: update available / waiting / updated / retry.
The app must not surface Drive folder paths, account internals, refresh tokens, privileged download URLs or provider credentials.
A PWA bundle must never contain HNS or SIEZEALL privileged credentials. Private Drive access requires an authorized adapter; public/shared package delivery still follows manifest/hash validation.

## Data retention
- durable: learning results, wrong-answer/weakness signals, badge/progress history, Planner results, important questions.
- short-lived: OCR/source captures after validated extraction, transient downloads, temporary generated files.
- cache eviction never deletes authoritative durable records.
- delete candidates are staged, never silently destroyed.

## Regression locks
1. TAKY data must remain under TAKY root.
2. SAVEY must remain a separate top-level root.
3. LEARNING and ARCHIGROW storage domains remain distinct.
4. SIEZEALL is distribution/user-sync, not internal master authority.
5. automatic remote package download requires confirmed Wi-Fi.
6. latest file != semantic CURRENT until validation/promotion.
7. Netlify deploy/release remains separately authorized.
