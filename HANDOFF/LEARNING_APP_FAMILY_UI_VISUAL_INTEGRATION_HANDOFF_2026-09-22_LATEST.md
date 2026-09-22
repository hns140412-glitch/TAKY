# LEARNING APP FAMILY UI / VISUAL INTEGRATION HANDOFF — 2026-09-22 LATEST

Status: ACTIVE / PRE-MOCKUP INTEGRATION
Scope: Ready & Set / Snap & Pop / Hide & Seek
Deployment / Netlify / main merge / DEVICE_VERIFIED: NOT RUN

## 0. Resume purpose

Resume the cross-app UI/visual integration work under latest TAKY governance.

This phase is NOT high-fidelity mockup production yet.

Primary objectives:
1. recover all existing UI decisions and visual/mockup lineage;
2. preserve app-local locked decisions;
3. unify family-wide visual DNA;
4. keep Ready / Snap / Hide regional and product-specific UI differences;
5. close screen composition, state, transition and visual lineage gaps;
6. only then allow low-fi / high-fi proposals.

## 1. Read first — TAKY

Read in this exact order:

1. C2S/LEARNING_APP_FAMILY_UI_DECISION_REGISTRY_2026-09-22.md
2. C2S/LEARNING_APP_FAMILY_VISUAL_MOCKUP_INTEGRATION_REGISTRY_2026-09-22.md
3. C2S/LEARNING_APP_FAMILY_ISLAND_WORLD_UI_MOCKUP_CRITERIA_2026-09-22.md
4. C2S/LEARNING_APP_FAMILY_SCREEN_COMPOSITION_STANDARD_2026-09-22.md
5. C2S/TAKY_SHARED_BADGE_SYSTEM_CANONICAL_2026-09-22.md
6. C2S/TAKY_SHARED_BADGE_VISUAL_CONTRACT_2026-09-22.md
7. C2S/TAKY_BADGE_SHARE_LINEAGE_RECOVERY_2026-09-22.md
8. C2S/TAKY_BADGE_HISTORICAL_60_RECLASSIFICATION_2026-09-22.md
9. C2S/TAKY_SHARED_BADGE_PRODUCER_EVIDENCE_MATRIX_2026-09-22.md

## 2. App-specific read order

### Ready & Set
Repo: hns140412-glitch/Ready-Set
Branch: taky/ready-rebuild-v01-2026-09-21

Read:
1. HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md
2. C2S/READY_SET_UI_PRODUCTIZATION_C2S_CLOSURE_2026-09-22.md
3. HANDOFF/READY_SET_UI_PRODUCTIZATION_START_PROMPT_2026-09-22.md
4. Ready_Set_Ui_Master_Logic_REV_07.md
5. Ready_Set_Share_Golden_Contract_REV_01.md
6. HANDOFF/SHARED_ISLAND_WORLD_POINTER_2026-09-22.md
7. current runtime UI source only as evidence, not as final visual authority.

Current state:
- structure/productization rules strong;
- Base Camp / Island Map role locked;
- Share Golden Contract strong;
- final composition and art not frozen;
- current generic Ready “획득 별” conflicts with shared Badge Star Grade and requires review.

### Hide & Seek
Repo: hns140412-glitch/Hide-Seek
Branch: rewrite/hide-runtime-v2-2026-09-21

Read:
1. HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md
2. HANDOFF/HIDE_UI_DESIGN_HANDOFF_2026-09-22_REV2.md
3. Hide_Seek_UI_MASTER_LOGIC_REV_04.md
4. C2S/HIDE_UI_LEARNING_RECORD_MODEL_C2S_CLOSURE_2026-09-22_REV2.md
5. HANDOFF/SHARED_ISLAND_WORLD_POINTER_2026-09-22.md

Current state:
- product language locked;
- Jungle / Waterfall region locked;
- TRACE / LINK / PIECE / CATCH / Badge Book / Calendar sequence strongly defined;
- exact high-fi/final art not frozen;
- legacy generic reward/badge assets are not current authority.

### Snap & Pop
Repo: hns140412-glitch/Snap-Pop
Branch: taky/snap-pop-implementation-2026-09-20

Read:
1. HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md
2. C2S/SNAP_POP_PRODUCT_UI_ARCHITECTURE_2026-09-22.md
3. C2S/SNAP_POP_FINAL_MOCKUP_UI_DESIGN_CRITERIA_2026-09-22.md
4. Snap_Pop_UI_MASTER_LOGIC_REV_12.md
5. HANDOFF/SHARED_ISLAND_WORLD_POINTER_2026-09-22.md
6. C2S/SNAP_POP_BADGE_SOURCE_RECOVERY_2026-09-21.md
7. data/badge-system.json
8. data/badge-catalog-working.json

Current state:
- product rules strong;
- Beach region locked;
- five landmarks locked as sub-destinations;
- Home/Writing/Ask/Understand/Result criteria are LOCK_CANDIDATE;
- 4-tab nav remains PROVISIONAL;
- final visual/high-fi OPEN;
- do NOT treat previous mockups as authority unless lineage says accepted.

## 3. Family-wide locked structure

ONE ISLAND / MULTIPLE REGIONS / DISTINCT APP OWNERS / CONTINUOUS EXPLORER CONTEXT

Ready:
BASE CAMP / ISLAND MAP

Hide:
JUNGLE / WATERFALL

Snap:
BEACH

Rules:
- island geography direction fixed;
- app switch is movement through the island, not a disconnected universe;
- current companion persists;
- island/base-camp names persist;
- app-specific ownership remains distinct;
- drop/voyage are approaches to the same island;
- Snap five landmarks are Beach sub-destinations;
- Hide caves/ruins/trails/etc. are Jungle/Waterfall sub-environments unless later promoted by canonical topology.

## 4. Shared UI / visual model

Three layers:

A. SHARED VISUAL DNA
- same island family;
- high-density illustration on world screens;
- calm action layer on task screens;
- runtime character slots;
- no emoji-first UI;
- no generic card wall;
- one dominant action;
- shared badge/share/crew semantics;
- 390×844 baseline.

B. REGIONAL DIALECT
- Ready = operational base camp / planning / route
- Snap = beach / expression / writing
- Hide = jungle-waterfall / trail / clue / retrieval

C. SCREEN-SPECIFIC COMPOSITION
- Ready planner/focus density;
- Snap writing field prominence;
- Hide clue/retrieval interaction.

Same family does not mean same screen.

## 5. UI decision status model

Use:
- LOCKED
- LOCK_CANDIDATE
- PROVISIONAL
- OPEN
- SUPERSEDED
- RUNTIME_VERIFIED
- DEVICE_OPEN

Do not flatten all apps to one maturity level.

## 6. Mockup lineage model

Every material mockup/reference must be registered as:

MOCKUP_ID
APP
SCREEN
DATE
SOURCE
STATUS = REFERENCE / CANDIDATE / ACCEPTED / SUPERSEDED / REJECTED
WHAT_IS_VALID
WHAT_IS_NOT_VALID
VISUAL_DNA_CONTRIBUTION
APP_LOCAL_ONLY
CROSS_APP_REUSE
SUPERSEDES
NOTES

A screenshot is never self-authoritative.

Visual freeze levels:
V0 REFERENCE ONLY
V1 DIRECTION CANDIDATE
V2 COMPOSITION LOCK
V3 VISUAL SYSTEM LOCK
V4 SCREEN FAMILY LOCK
V5 FINAL VISUAL FREEZE

## 7. Badge / share locks

Badge:
- family-wide experience/history system;
- not score/power;
- Tier = GREEN / BLUE / RED / GOLD / PLATINUM;
- Star Grade = 성급 1–5;
- Badge Star Grade != generic reward star;
- Badge != Snap Wish Gem.

Badge share:
- actual result/record first;
- badge/history context second;
- tier + star grade;
- profile character/theme if allowed;
- island scenery supports, never dominates.

## 8. Current major open gaps

1. exact family island topology art/relative placement;
2. central island-world canonical file needs final reconstruction/closure;
3. Ready final Home/TODAY composition;
4. Hide final high-fi screen family;
5. Snap final Home/nav/result composition;
6. family typography/icon/control system;
7. family visual asset lineage;
8. accepted/rejected mockup recovery from prior conversations;
9. shared badge collection entry point;
10. Ready generic star vs Badge Star Grade conflict;
11. cross-app transition visual choreography;
12. device verification remains NOT RUN.

## 9. Required next execution sequence

Do NOT start with a new mockup.

Execute in this order:

1. live refresh TAKY + Ready + Hide + Snap branches;
2. restore exact current HEADs;
3. recover user-accepted / corrected / rejected mockups and UI references from each app;
4. create/update Mockup Lineage Registry entries;
5. separate accepted composition from merely liked atmosphere/style;
6. create comparative matrix:
   - Ready Home
   - Snap Home
   - Hide Home
7. identify:
   - shared Visual DNA
   - regional differences
   - app-local screen grammar
8. close central Island World topology gaps;
9. produce Screen Inventory / State Matrix / Transition-Return Matrix;
10. produce Family Visual System Skeleton;
11. only after those gates are closed, create low-fi;
12. high-fi only after low-fi + visual-system gate.

## 10. Regression prohibitions

Do not:
- create a disconnected island per app;
- flatten the three apps into identical UI;
- let an app-local visual solution become family-wide authority automatically;
- revive rejected white-card-wall UI;
- cover the island with opaque timetable tiles;
- use generic forest wallpaper without spatial meaning;
- hard-code one character into layout;
- merge Badge / Growth / Gem / Affinity;
- use Badge Star Grade as generic reward stars;
- import Snap Wish economy into Ready/Hide;
- treat Special as rarity/power;
- let scenery dominate writing/recall/focus;
- use a high-fi screenshot as proof of product completion;
- call Netlify / deploy / main merge.

## 11. Reporting

At every major checkpoint report separately:

- FUNCTION_IMPLEMENTATION
- UI_STRUCTURE_DEFINITION
- UI_FUNCTION_INTEGRATION
- USER_FACING_PRODUCT_MATURITY
- VISUAL_FREEZE_LEVEL
- CODED
- STATIC/CI
- RUNTIME
- DEVICE
- OPEN_GAPS
- NEW_REQUIREMENTS
- REGRESSION_RISKS

Do not inflate completion because backend/runtime is mature.

END
