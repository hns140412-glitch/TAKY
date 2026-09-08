# TAKY ↔ 3 MOBILE LEARNING PWA — DETAILED COMPARISON HANDOFF

Status: READY FOR NEW CHAT / READ-COMPARE FIRST / NO AUTO-WRITE
Date: 2026-09-07
Primary command: `최신 타키 기준으로 재개. 3개 모바일 웹앱의 상세 기능·기준·규칙을 MASTER와 실제 구현까지 대조해줘.`

## 1. OBJECTIVE

Compare the current TAKY governance/shared learning rules against the detailed product rules and actual mobile PWA implementation of:

1. Ready & Set
2. Hide & Seek
3. Snap & Pop

This is not a short summary comparison.
The goal is a detailed rule/function inventory and cross-owner reconciliation.

## 2. REQUIRED TAKY SOURCES

Repository: `hns140412-glitch/TAKY`

Load in this order (routing corrected 2026-09-08 to inherit TAKY.md; historical decisions remain preserved):
1. `TAKY.md`
2. `MASTER/MASTER_LOGIC.md`
3. `MASTER/REVISION_GOVERNANCE.md`
4. `OS/GUIDE_FAMILY_LEARNING_OS.md`
5. `OS/GUIDE_CHARACTER_RELATIONSHIP.md`
6. `MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md` (historical filename; official status REV_00)
7. `MASTER/TRACEABILITY_PROTOCOL.md`
8. `MASTER/VALIDATION_RULES.md`
9. `HISTORY/2026-09-07_GLOBAL_FORENSIC_RECOVERY_INTEGRATION.md`
10. this Handoff

Only when a historical omission/dispute materially appears, load:
- `MASTER/RECOVERY_FORENSICS_PROTOCOL.md`

Do not run full forensic recovery by default.

## 3. READY & SET SOURCES

Repository: `hns140412-glitch/Ready-Set`

Current master delta:
- `Ready_Set_Ui_Master_Logic_REV_07.md`

Inherited detailed baseline:
- `Ready_Set_Ui_Master_Logic_REV_06.md`

REV_07 explicitly inherits REV_06 unless overridden, therefore comparing REV_07 alone is insufficient for detailed function/rule coverage.

Actual implementation/evidence to inspect as applicable:
- `index.html`
- `app.js`
- `manifest.json`
- `manifest.webmanifest`
- service worker file if present
- `config.js`
- `VERSION.json`
- `VALIDATION_REPORT.md`
- deployment/readme/test files where they materially claim current behavior

## 4. HIDE & SEEK SOURCES

Repository: `hns140412-glitch/ZPD-Word`
Current product/master:
- `Hide_Seek_UI_MASTER_LOGIC_REV_03.md`

Actual implementation/evidence:
- `index.html` when present
- `app.js`
- manifest/service-worker files
- `README.md`
- `SELF_VERIFICATION.md`
- current asset map / current assets when UI/world behavior is material

Historical detailed learning-core source is not fully represented by the short current REV_03 file.
Use the recoverable Library source when detail is required:
- `## ZPD Word Ui Master Logic REV_07##.md`

Migration rule:
- ZPD product name / police-capture child-facing world = SUPERSEDED
- validated learning/OCR/retrieval/data/QA rules may survive only after semantic comparison with current Hide & Seek master and current implementation
- do not revive old world/branding merely because the historical detailed master contains it

Treat historical ZPD detailed rules as `LINEAGE EVIDENCE`, not automatic current authority.

## 5. SNAP & POP SOURCES

Repository: `hns140412-glitch/Snap-Pop`

Current master delta:
- `Snap_Pop_UI_MASTER_LOGIC_REV_11.md`

Inherited detailed baseline:
- `Snap_Pop_UI_MASTER_LOGIC_REV_10.md`

REV_11 explicitly inherits REV_10 unless overridden; detailed comparison must read both.

Actual implementation/evidence:
- `index.html`
- `app.js`
- manifest/service-worker files
- `README.md`
- `README_DEPLOY.txt`
- current asset manifest and relevant current assets

Important stale-document check:
old deploy/readme language must not override current master where old map/tool unlock behavior conflicts with free access to the five ORIGINAL places.

## 6. COMPARISON AXES — REQUIRED

For TAKY and each app, build a detailed matrix across at least:

### A. Authority / Ownership
- global vs shared vs project owner
- duplicated authority
- missing owner
- accidental ownership transfer

### B. Product Purpose / Identity
- child-facing purpose
- what the app is NOT
- relation to Learning Island / Base Camp

### C. Session / Task / Lap / Timer
- session owner
- app switch semantics
- task completion vs session end
- timer persistence / pause rules
- return target / state handoff

### D. GUIDE / Character / Relationship
- shared Guide identity
- project role skin
- Main / Guest / Special Friend boundaries
- voice/name/personality/lifecycle
- Guide presentation and intervention

### E. Input / Capture / Creation
- camera/photo/OCR
- voice/STT/TTS
- writing / speaking / problem execution
- Review-before-Commit

### F. Learning Logic
- retrieval / understanding / expression
- weak-item detection
- help/hint/check
- retry/relearn
- reflection
- child ownership

### G. Data / Storage / History
- local state
- shared learning history
- app-specific registry/history
- isolation boundaries
- migration / rollback

### H. Offline / PWA / Update
- offline state
- service worker/cache
- version/update behavior
- active-session safe apply
- install/icon/manifest behavior

### I. Reward / Progression
- rewards
- progression
- gates
- app-specific economy
- prohibited cross-app copying

### J. UI / Interaction / Accessibility
- primary action hierarchy
- character prominence
- dialogue anchor/task clearance
- reduced motion
- mobile install/runtime assumptions

### K. Validation / Release
- MASTER PASS
- DESIGN PASS
- FUNCTION/DATA PASS
- PWA PASS
- DEPLOY/INSTALL/OFFLINE/CACHE PASS
- actual result evidence

## 7. STATUS TAXONOMY — REQUIRED

Each detailed function/rule should receive one or more statuses:

- `MASTER_CONFIRMED`
- `SHARED_CONFIRMED`
- `PROJECT_CONFIRMED`
- `IMPLEMENTED`
- `PARTIAL_IMPLEMENTATION`
- `MISSING_IMPLEMENTATION`
- `EXTRA_IMPLEMENTATION`
- `STALE_DOCUMENTATION`
- `STALE_CANONICAL_REFERENCE`
- `DUPLICATE_RULE`
- `OWNER_CONFLICT`
- `SUPERSEDED`
- `HOLD`
- `RECOVERY_REQUIRED`
- `UNVERIFIED`

Do not collapse these to a single PASS/FAIL.

## 8. REQUIRED OUTPUTS

Output 1 — **4-way Rule Matrix**
`TAKY Shared / Ready & Set / Hide & Seek / Snap & Pop`

Output 2 — **Per-app Detailed Function Inventory**
Function → governing rule → master source → implementation location → current result → status.

Output 3 — **Cross-App Shared Engine Matrix**
Identify KEEP / SHARE / MOVE / MERGE / CALL / REJECT candidates without rewriting project identity.

Output 4 — **Conflict / Omission / Regression Ledger**
Include stale labels, stale readmes, lost inherited rules, implementation-only behavior, missing implementation and conflicting owners.

Output 5 — **Proposed owner corrections**
Do not write yet. Produce patch candidates only unless the user explicitly says `/반영`.

## 9. IMPORTANT CURRENT CORRECTIONS

- Current vocabulary app name = `Hide & Seek`; ZPD user-facing name/world is superseded.
- Ready & Set = Base Camp / session orchestrator, not only Time Attack.
- Snap & Pop = thought-to-expression specialist, not only Korean writing.
- Five Snap ORIGINAL help places remain freely available; old unlock logic is superseded.
- Guide Character/Relationship shared rules are in `OS/GUIDE_CHARACTER_RELATIONSHIP.md`.
- Special Friend existence is user-confirmed but detailed rules remain `RECOVERY_REQUIRED`.
- Golden Reference higher-order authority is released; Core6 current user-confirmed identities remain subject to source-level lineage review.
- Product historical REV labels are lineage; TAKY official governance remains REV_00 until explicit finalization.

## 10. STOP / WRITE RULE

This comparison starts READ-ONLY.

`COMPARE ≠ WRITE`
`GOOD RESULT ≠ COMPLETE COVERAGE`
`CURRENT MASTER ≠ FULL INHERITED DETAIL`
`IMPLEMENTATION EXISTS ≠ MASTER AUTHORITY`

Only after the user reviews the comparison and explicitly requests `/반영` may canonical owners be modified.

## 11. NEW-CHAT BOOTSTRAP TEXT

Use this exact prompt if useful:

> 최신 TAKY canonical을 먼저 불러와. `HISTORY/2026-09-07_APP_FAMILY_COMPARISON_HANDOFF.md`를 기준으로 Ready & Set, Hide & Seek, Snap & Pop 3개 모바일 PWA의 최신 MASTER와 상속된 상세 MASTER, 실제 HTML/JS/PWA 구현을 모두 대조해. 요약하지 말고 기능·기준·규칙 단위로 4-way matrix와 앱별 상세 기능 inventory를 만들어. 현재 MASTER에 없는 과거 상세 규칙은 자동 부활시키지 말고 lineage evidence로 비교하고, `MASTER_CONFIRMED / IMPLEMENTED / MISSING / EXTRA / STALE / SUPERSEDED / HOLD / RECOVERY_REQUIRED / UNVERIFIED`를 구분해. 먼저 읽기·비교만 하고 canonical은 수정하지 마.

END — APP FAMILY COMPARISON HANDOFF
