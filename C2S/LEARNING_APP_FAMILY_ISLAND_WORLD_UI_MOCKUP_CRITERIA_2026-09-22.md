# LEARNING APP FAMILY ISLAND WORLD / UI MOCKUP CRITERIA — 2026-09-22

Status: PRE-MOCKUP CANONICAL CRITERIA
Scope: Ready & Set / Snap & Pop / Hide & Seek
Rule: NO MOCKUP / NO HIGH-FI until this criteria set is accepted.
Deployment / Netlify / main merge: NOT_RUN

# 0. TAKY order lock

SOURCE / CURRENT RULES
→ ISLAND WORLD CANONICAL
→ APP REGION OWNERSHIP
→ SPATIAL IA
→ USER JOURNEY
→ STATE / TRANSITION / RETURN
→ CHARACTER / BADGE / SHARE RELATION
→ VISUAL INTENSITY RULES
→ LOW-FI CRITERIA
→ ONLY THEN MOCKUP

Do not start from a pretty island illustration.

---

# 1. Island = spatial IA, not background art

The island is the common spatial world for the Learning App Family.

It is not:
- decorative wallpaper;
- one app's private world;
- a loose metaphor that changes per screen;
- a collection of disconnected mini-worlds.

It is:
- the persistent spatial identity of the learning family;
- the user's exploration world;
- the visual and navigational layer that connects apps;
- the world context for companion continuity, records, badges and sharing.

Core principle:
**ONE ISLAND / MULTIPLE REGIONS / DISTINCT APP OWNERS / CONTINUOUS EXPLORER CONTEXT**

---

# 2. Fixed top-level topology

## Ready & Set
Region:
**BASE CAMP / ISLAND MAP**

Role:
- session/orchestration hub;
- common start and return point;
- shows island-wide navigation context;
- owns Planner/session/timer and routing context.

## Hide & Seek
Region:
**JUNGLE / WATERFALL**

Role:
- vocabulary discovery/retrieval region;
- hidden-word exploration;
- trails, clues, caves, ruins, trees, rocks, secret boxes etc. are sub-environments within this region.

## Snap & Pop
Region:
**BEACH**

Role:
- thought/expression region;
- writing, curiosity, imagination and expression journeys;
- five expression landmarks are sub-destinations within the Beach region, not separate islands.

Hard lock:
Do not redesign any app as a disconnected standalone world.

---

# 3. Geography rule

Island geography is fixed at the family-world level.

Meaning:
- major region positions do not reshuffle by app launch;
- the child should form a stable mental map;
- returning to the island should feel like returning to the same place;
- app updates may refine art/detail, but not silently relocate regions.

Open until exact topology evidence is recovered:
- precise relative placement;
- exact roads/trails;
- exact coastline silhouette;
- exact scale between regions.

Therefore:
**FIXED TOPOLOGY DIRECTION ≠ arbitrary pixel-perfect map lock yet.**

---

# 4. Onboarding world sequence

Canonical order:

1. exploration crew setup
2. choose/experience approach mode: drop or voyage
3. island entry
4. island naming
5. Ready & Set base-camp entry
6. base-camp naming
7. first exploration routing

Rules:
- drop/voyage are approach themes to the same island;
- drop is not a floating sky-island universe;
- voyage is not a separate ocean-only world;
- the island identity remains the same after onboarding.

---

# 5. Naming contract

## Island name
- child-defined presentation identity.
- persists across apps.
- renaming must not reset progress/history.

## Base camp name
- child-defined presentation identity.
- Ready-owned operational surface.
- renaming must not reset session/history.

Name changes are identity presentation changes, not new-world creation.

---

# 6. App-region ownership

World continuity does not merge functional ownership.

### Ready owns
- session;
- planner;
- timer;
- task/lap orchestration;
- base-camp operation;
- island-map routing.

### Snap owns
- thought/expression experience;
- five writing/expression landmarks;
- Snap exploration crew behavior presentation in its region;
- gem/wish/blessing economy;
- Snap records/growth surfaces.

### Hide owns
- vocabulary discovery/retrieval experience;
- jungle/waterfall learning flow;
- Hide-specific memory/retrieval surfaces.

### TAKY shared layer owns
- common island-world topology;
- cross-app continuity rules;
- shared badge semantics;
- shared technical handoff contracts;
- cross-app provenance.

---

# 7. Companion continuity

The current companion persists across app regions unless an explicit product rule changes the companion.

Rules:
- app switch does not silently replace companion;
- region art may change outfit/props/expression;
- Explorer_ID / identity remains stable;
- companion presence can be contextual and does not need to be visible at all times;
- companion never gains app-specific power advantage.

Visual principle:
**same friend, different region context.**

---

# 8. Region-to-screen mapping

The island world does not mean every screen must show the full island.

## World surfaces
High world visibility:
- Ready home/base camp;
- island map;
- Snap beach home/map;
- Hide jungle/waterfall home;
- transitions between app regions;
- major return/completion moments.

## Task surfaces
Low world visibility:
- writing;
- Ask/Understand;
- word recall;
- OCR review;
- record editing;
- settings.

Task screen rule:
World context may remain through:
- horizon;
- material texture;
- subtle environmental frame;
- location label;
- companion cue;
- small landmark cue.

Never let scenery overpower the task.

---

# 9. Snap Beach sub-structure

Snap's five landmarks are functional expression lenses inside the Beach region.

- 아이디어 동굴
- 감정 호수
- 묘사 숲
- 관점 전망대
- 마무리 캠프

These are:
- sub-destinations;
- always accessible;
- not level-locked;
- not separate apps;
- not separate islands.

Beach is the macro-region.
Five landmarks are micro-destinations.

UI implication:
Snap Home can show a Beach-region exploration map with five destinations while still belonging to the same family island.

---

# 10. Hide Jungle / Waterfall sub-structure

Hide's possible environments include:
- forest;
- cave;
- ruins;
- underground;
- secret box;
- trees;
- rocks;
- trails;
- clue points.

Interpretation:
These are sub-environments within the Jungle / Waterfall region unless later canonical topology explicitly promotes one to a major family-world region.

Do not use Snap Beach as Hide's primary home region.

---

# 11. Ready Base Camp structure

Ready is the operational center.

Base camp should communicate:
1. today's exploration state;
2. active/next task;
3. where the child is in the island;
4. where they can go next;
5. return/resume state.

Base camp is not a dashboard full of app icons.

Preferred mental model:
**camp → map → region → specialist experience → return to camp**

---

# 12. Cross-app movement contract

A region transition must preserve meaningful context.

Minimum continuity payload where applicable:
- explorer/profile identity;
- current companion;
- island identity;
- base-camp identity;
- session context;
- task/lap identifiers;
- return target;
- relevant specialist context.

Rules:
- APP_SWITCH != PAUSE.
- APP_SWITCH != SESSION_END.
- return must restore the meaningful prior state.
- specialist app must not silently close Ready session.
- back/return destination must be explicit in UI contract.

---

# 13. Visual world consistency

Shared island identity should remain recognizable through:

- coastline/world geometry;
- horizon/light logic;
- environmental material family;
- navigation markers;
- region signage;
- map language;
- shared exploration symbols;
- companion continuity.

Apps may vary:
- local palette emphasis;
- local vegetation/material;
- landmark density;
- task-surface calmness;
- local motion language.

Apps may not:
- invent a new unrelated art universe;
- change the child avatar identity;
- redefine exploration crew roles;
- replace island vocabulary with app-specific disconnected metaphors.

---

# 14. World-detail intensity

## Level A — Island-wide
Used for:
- onboarding arrival;
- island map;
- major transitions.

Shows:
- multiple regions;
- geography;
- orientation;
- base camp.

## Level B — Regional
Used for:
- Ready base camp;
- Snap beach home;
- Hide jungle/waterfall home.

Shows:
- region identity;
- local routes;
- local landmarks;
- companion/world activity.

## Level C — Task-local
Used for:
- writing;
- recall;
- Ask/Understand;
- editing.

Shows:
- only enough world context to maintain place identity.

This hierarchy prevents over-illustration.

---

# 15. Character / crew integration

Character is not structural wallpaper.

UI provides slots:
- CHARACTER_SLOT
- MAIN_COMPANION_SLOT
- CREW_REACTION_SLOT
- GUEST_SLOT

Runtime decides identity.

World screen:
character may be more visible.

Task screen:
character becomes smaller/contextual.

Reaction:
- brief;
- non-blocking;
- never covers primary input;
- never acts as teacher/grader.

---

# 16. Badge integration with island world

Badge is a shared experience-history system across the island.

Badge can reference:
- region;
- exploration;
- meaningful event;
- recovery;
- special moment;
- self-directed behavior.

Badge is not tied to only one region/app.

A shared badge may show theme expression related to where the event occurred, while keeping:
- badge identity;
- tier;
- star grade;
- child identity;
- canonical meaning stable.

Badge star count = **star grade / 성급 1–5**.
Not generic reward stars.

---

# 17. Share integration with island world

Share should communicate:
- actual exploration/result;
- where/what context it came from;
- meaningful badge/history when applicable;
- profile character/theme if sharing permission allows.

Island scenery is supporting context only.

Do not let:
- giant background;
- decorative map;
- app logo;
- generic reward symbols

become more important than the actual shared record.

---

# 18. Gem / Wish / Blessing relationship to world

Snap's gem/wish/blessing economy remains Snap-owned even inside the shared island.

Rules:
- island-wide world does not make Snap gems a family-wide currency;
- Ready/Hide do not spend Snap gems;
- Wish Shop belongs to Snap region/system;
- blessing is explicit wish execution;
- no island map UI should imply universal currency unless a later shared economy is separately approved.

---

# 19. Special encounter relationship to world

Special encounter means:
- unusual meeting;
- world event;
- encounter route;

not:
- stronger character;
- rarity tier;
- premium region;
- FOMO event.

Special may use island geography for clues and encounters, but no penalty for missing it.

---

# 20. State continuity

Every region/home must define:
- LOADING
- READY
- RESUME
- OFFLINE
- PARTIAL
- BLOCKED
- STALE
- RECOVERY

World transition failure must not:
- reset island identity;
- lose current companion;
- end Ready session;
- duplicate reward;
- lose child-authored draft.

---

# 21. Map/navigation rules

Map must prioritize orientation.

Map asks:
- where am I?
- where can I go?
- what is active?
- what can I resume?

Avoid:
- excessive feature buttons;
- unrelated meta systems on map;
- card stacks covering geography;
- decorative pins without semantic purpose;
- every destination having equal visual priority.

Map is spatial navigation, not a feature dashboard.

---

# 22. Mobile 390×844 world-screen baseline

On phone:
- geography/background can be immersive;
- primary interactive region remains reachable without precise tiny taps;
- region labels remain legible;
- one dominant next action;
- bottom navigation must not cover core map actions;
- companion speech must not block navigation;
- map cannot require pinch/zoom to perform the primary journey unless separately designed and tested.

---

# 23. Motion criteria

Allowed:
- arriving at island;
- moving between regions;
- returning to base camp;
- companion arrival/departure;
- subtle environmental life.

Forbidden:
- constant camera drift that harms readability;
- forced long transitions;
- motion required to identify destination;
- animation that hides loading/error state;
- motion interrupting writing/recall.

Reduced motion must preserve meaning.

---

# 24. World-copy criteria

Preferred:
- 탐험
- 오늘의 섬
- 베이스캠프
- 탐험대
- 탐험대원
- 이동/출발/돌아가기
- 지역-specific natural names

Avoid reintroducing:
- generic app-switch/developer language;
- mission-control jargon;
- police/detective/arrest world in Hide;
- gacha/rank language for crew/special;
- score/power language for badges.

---

# 25. Low-fi mockup criteria

Low-fi must prove structure only.

Required low-fi set before visual design:

1. Island onboarding arrival
2. Island naming
3. Base-camp naming
4. Ready base camp home
5. Island map
6. Snap beach home
7. Hide jungle/waterfall home
8. Ready → Snap transition
9. Ready → Hide transition
10. specialist → Ready return
11. resume state
12. offline/recovery transition
13. companion continuity example
14. badge/share context example without art styling

Low-fi should use boxes, labels and arrows only.

No final illustration direction at this stage.

---

# 26. Mockup entry gate

NO high-fi mockup until all are true:

- island topology role LOCKED;
- app-region ownership LOCKED;
- onboarding order LOCKED;
- island/base-camp naming persistence LOCKED;
- companion continuity LOCKED;
- Ready/Snap/Hide region relation LOCKED;
- screen inventory created;
- transition table created;
- return/recovery paths defined;
- badge/share/world interaction defined;
- Gem/Wish boundaries protected;
- unresolved topology details explicitly marked OPEN.

---

# 27. Fail conditions

FAIL if:
- each app gets its own disconnected island;
- Ready becomes only an app menu;
- Snap's five landmarks become five independent worlds;
- Hide's sub-environments override Jungle/Waterfall home;
- current companion resets during app movement;
- island/base-camp rename resets progress;
- drop/voyage become different universes;
- scenery dominates core task screens;
- badge stars become generic reward stars;
- Snap gem becomes shared island currency without approval;
- Special is portrayed as rare/powerful;
- app transition behaves like session end.

END
