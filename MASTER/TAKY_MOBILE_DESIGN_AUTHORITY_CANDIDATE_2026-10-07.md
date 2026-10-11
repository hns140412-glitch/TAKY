# TAKY MOBILE DESIGN AUTHORITY — CANDIDATE 2026-10-07

Status: CANDIDATE / NOT LOCKED / DOES NOT OVERRIDE EXISTING APP MASTER OR GOLDEN
Authority ID: TAKY-MOBILE-DESIGN-AUTHORITY-V1-CANDIDATE
Scope: Ready & Set / Hide & Seek / Snap & Pop / low-age Hangul-learning family / TAKY-governed mobile PWA surfaces.

## 0. Authority order — HARD CANDIDATE

When design inputs conflict, resolve in this order:

1. TAKY/project MASTER + explicit user-confirmed rules
2. User-approved GOLDEN / approved Visual ID / approved source asset
3. Golden Journey / strong candidate explicitly marked as such
4. TAKY family UI/world/interaction principles
5. Structural / IA references
6. External principles: Apple/platform guidance, Tesla interaction observations, Nintendo/learning UX references

External references never silently replace project authority.

## 1. Core TAKY design DNA

- WORLD FIRST: the user is in a place/world, not a generic card dashboard.
- SPACE = FUNCTION: location and learning/action meaning are connected.
- DIRECT INTERACTION: touch the learning object itself where practical.
- CHARACTER AS PARTICIPANT: character reacts/guides but never becomes the user's task.
- LIVE UI OVER ART: illustration, character, activity and live UI remain separately addressable.
- ONE SCREEN = ONE PRIMARY PURPOSE.
- USER != DEBUGGER: visual regressions must be caught before user acceptance.

Layer model:
L0 WORLD
L1 CHARACTER
L2 ACTIVITY
L3 LIVE UI / FEEDBACK
L4 OPTIONAL EVENT THEME OVERLAY per TKY-EVENT-THEME-001 without rewriting L0-L3 contracts.

## 2. Global UI rules

- Primary action is singular/obvious by default.
- User should understand current state and next action in about 1–2 seconds.
- Core learning/execution should fit in one viewport where practical.
- Long scroll is reserved for history, browsing, parent management and long collections.
- Cards/pills/rounded containers are not the default layout primitive.
- Hierarchy should come first from space, scale, typography, position and contrast.
- Interactive targets must respect current platform guidance; child primary controls should be generously sized.
- Every touch has immediate feedback.
- Motion explains state, causality or spatial transition; ambient motion is subordinate.
- Reduced Motion and sound-off states retain meaning.
- Device behavior inherits each app's existing MASTER/CURRENT contract; this authority does not invent a competing responsive system.
- Only 수련 캠프 (Play Camp) uses **TABLET AS PRIMARY DEVICE MODE** and has a **SEPARATE TABLET UI STANDARD**, inherited from `Play Camp/TAKY_CURRENT.md` (`tablet-first`, `tablet landscape first`, `no-scroll core scenes`).
- Play Camp tablet UI is not derived from a mobile layout. Tablet composition is the primary design source; any mobile presentation is secondary/fallback.
- Ready & Set / Hide & Seek / Snap & Pop do NOT receive a separate tablet UI product/design branch by default. They keep one app UI and adapt responsively according to their existing app MASTER contracts.
- Responsive tablet adaptation may reflow/use additional space, but it must preserve the same Golden/interaction identity rather than becoming a second UI design.
- Implementation convenience cannot simplify an approved Golden.

## 3. 수련 캠프 (Play Camp) — dedicated tablet UI exception

Source authority remains the existing Foundation CURRENT, not this document.

Inherited device/design facts:
- PRIMARY DEVICE MODE = TABLET
- SEPARATE TABLET UI STANDARD
- tablet-first concept play
- tablet landscape first
- no-scroll core scenes
- tablet layout is authoritative; mobile is secondary/fallback and may not drive tablet composition
- 1024×768 and 1180×820 verified flow baseline
- manipulate/hear → discover → name → connect

수련 캠프 (Play Camp) SHALL use a deliberately composed tablet UI as its primary UI authority rather than a stretched mobile surface.
This exception does not authorize a second island/app/account boundary; it remains the early/concrete concept-play region inside the same TAKY explorer boundary.

Naming contract:
- Korean display name: `수련 캠프`
- English display name: `Play Camp`
- Runtime/internal canonical identifier: `PLAY_CAMP`
- `Foundation Explorer` is legacy terminology only and SHALL NOT be used as the normal user-facing name.

## 4. Ready & Set

Protected:
- Ready project MASTER and UI Freeze procedure.
- Latest user-confirmed YELLOW Phone + Tablet Timer Golden.
- Execution-first hierarchy.

Strong candidate:
- Week / Day planner visual direction and goal-setting flow, pending full visual acceptance/binding.

Structure-only:
TODAY -> Mission -> Focus -> Wrap-up -> Result -> Carry-over.

Rule:
Planner plans; Ready executes. TODAY is a Base Camp into action, not a productivity dashboard.

## 5. Hide & Seek

Protected:
- approved forest / soft moss / stepped-waterfall environment Visual ID
- TRACE / LINK / CORE / RECALL learning modes
- approved character Visual IDs
- learning remains primary over gamification

Preserve/refine:
- mode as place/action, not generic menu tile
- exploration feeling
- character hint participation
- target word/learning object dominates the active screen

## 6. Snap & Pop

Protected:
- approved bright coastal / beach / pier environment Visual ID
- Ultra-density illustration + Live Web UI separation
- user-authored expression as the central result

Preserve/refine:
- thinking stages expressed through spatial metaphor
- input connected directly to the object/scene being explored
- world remains visible; UI does not cover it unnecessarily

## 7. Child / Parent split

Child:
LOOK -> TOUCH -> RESPONSE -> UNDERSTAND.
Prefer tap/drag/trace/connect/listen/speak/choose/discover over long instructions.

Parent:
same DNA, higher information density; planning/edit/approval/history/comparison/settings allowed.
Generic admin dashboard convergence remains prohibited.

## 8. Event Theme Engine

Event themes are governed by:
- MASTER/EVENT_THEME_PROTOCOL_CANDIDATE_2026-10-07.md
- MASTER/EVENT_THEME_REGISTRY_CANDIDATE_2026-10-07.json

Invariant:
EVENT MAY DECORATE THE EXPERIENCE, BUT MUST NOT REWRITE THE EXPERIENCE.

Themes may alter atmosphere/accent/decorative props/ambient motion/short copy/sound/optional accessory/reward skin.
They may not alter Golden layout, navigation, learning logic, primary action hierarchy, touch targets, character identity/Visual ID, timer/planner semantics or live data authority.

National commemorations and memorial days use restrained/respectful tone. Memorial tone suppresses confetti/fireworks/fanfare/reward multipliers/high-energy motion.

## 9. Claude Design role

Claude Design is an executor/reviewer, not authority.

Input:
CURRENT authority + exact Golden/Visual IDs + app override + exact DELTA + prohibited changes.

Output:
candidate screens + tokens/components used + motion/interaction spec + self-review.

Do not regenerate entire app for a local change.

## 10. Delta model

PATCH:
screen-local geometry/copy/spacing change that does not alter global authority.

MINOR:
backward-compatible shared rule/token improvement; requires targeted cross-app impact review.

MAJOR:
Design DNA/interaction-model change; requires explicit authority revision and broad impact review.

Apps pin authority/Golden/event-theme revisions. A central update does not auto-mutate every app.

## 11. Design Gate

Before promotion:
1. Load applicable MASTER and current Golden/Visual IDs.
2. Classify every reference: LOCKED / GOLDEN / STRONG_CANDIDATE / STRUCTURE_ONLY / HOLD_REJECT / EXTERNAL_REFERENCE.
3. Generate only bounded candidate surfaces.
4. Compare rendered candidate with protected baseline.
5. Classify: PRESERVED / IMPROVED / CHANGED / REGRESSED / UNKNOWN.
6. REGRESSED blocks promotion. Material UNKNOWN blocks LOCK.
7. Verify responsive, accessibility, reduced-motion, sound-off and actual interaction states.
8. Only approved result becomes Golden / locked authority revision.

## 12. Storage and update boundary

Human-readable design authority and approved reusable source assets follow current Drive routing from TKY-ASSET-001.
Git stores protocols, schemas, registries, gate rules, version pins and runtime contracts.
App repositories consume pinned authority/asset/event-theme versions rather than becoming a second canonical authority.

Current Drive authority route remains resolved by OS/DRIVE_STORAGE_MAP.json and CURRENT/DESIGN_UI_ASSET_SOURCE_DEFAULT_2026-09-29.json.

## 13. Promotion boundary

This file is CANDIDATE only.
It does not rewrite:
- Ready/Snap/Hide existing MASTERs
- approved Golden UI
- approved Visual IDs
- CURRENT owners
- runtime bindings
- deploy state

Promotion requires explicit impact review and user approval.
