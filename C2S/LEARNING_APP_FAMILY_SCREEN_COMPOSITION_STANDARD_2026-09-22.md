# LEARNING APP FAMILY SCREEN COMPOSITION STANDARD — 2026-09-22

Status: PRE-MOCKUP SCREEN COMPOSITION STANDARD
Scope: Ready & Set / Snap & Pop / Hide & Seek
Parent: LEARNING_APP_FAMILY_ISLAND_WORLD_UI_MOCKUP_CRITERIA_2026-09-22.md
Rule: NO HIGH-FI MOCKUP until screen composition + state + transition contracts are accepted.

# 0. Composition principle

A screen is defined by:
PURPOSE
→ PRIMARY USER QUESTION
→ PRIMARY ACTION
→ SUPPORTING INFORMATION
→ WORLD INTENSITY
→ CHARACTER PRESENCE
→ META SYSTEM VISIBILITY
→ STATE MODEL
→ RETURN / RECOVERY
→ RUNTIME OWNER.

No screen may be designed by visual decoration first.

---

# 1. Global screen hierarchy

Every child-facing screen must have:

1. one clear purpose;
2. one dominant next action;
3. optional secondary actions;
4. visible current state;
5. a predictable back/return path;
6. non-happy state handling;
7. clear runtime ownership.

Avoid:
- feature-dense dashboards;
- cards for every element;
- equal visual weight for all functions;
- world illustration covering primary interaction;
- persistent character speech blocking content.

---

# 2. Shared global shell rules

## Top area
May contain:
- current region/location;
- current companion indicator;
- minimal profile/status access;
- essential session continuity indicator.

Must not become:
- currency/status strip overload;
- badge dashboard;
- developer/debug strip.

## Main content
Owns the current screen purpose.

## Bottom/navigation
Only persistent destinations with real product-level importance.
Do not mirror controller/module structure.

## Overlay
Only contextual:
- crew reaction;
- hint;
- confirmation;
- recovery.

No persistent modal-like speech layer.

---

# 3. Ready & Set — BASE CAMP HOME

SCREEN_ID: READY_BASE_CAMP

Purpose:
Common start/return point for current learning session.

Primary question:
**오늘 어디서부터 이어갈까?**

Must show:
- current/next exploration task;
- session/resume state;
- current island/base-camp identity;
- concise map/region context;
- one clear start/resume action.

May show:
- current companion;
- small exploration status;
- next region hint.

Must not show all at once:
- full records;
- full badge collection;
- full settings;
- all specialist features;
- detailed economy systems.

World intensity:
LEVEL B / REGIONAL.

Character:
MAIN_COMPANION_SLOT, contextual.
No large persistent speech bubble.

Badge:
Only small contextual acknowledgement if directly relevant.
Never badge dashboard.

Share:
Not primary on Base Camp home.

---

# 4. Ready & Set — ISLAND MAP

SCREEN_ID: READY_ISLAND_MAP

Purpose:
Spatial orientation and region navigation.

Primary questions:
- 어디에 있지?
- 어디로 갈 수 있지?
- 지금 이어갈 곳은 어디지?

Must show:
- Base Camp;
- Snap Beach;
- Hide Jungle/Waterfall;
- current location;
- active/resumable route.

May show:
- future/unavailable region only if canonical and clearly non-active.

Must not show:
- every feature as map pin;
- badge/gem/shop controls;
- full task details;
- unrelated meta systems.

World intensity:
LEVEL A / ISLAND-WIDE.

Interaction:
Large tappable regions.
No precision map interaction required for primary navigation.

---

# 5. Ready & Set — SESSION / FOCUS

SCREEN_ID: READY_SESSION

Purpose:
Execute current task/lap with minimal distraction.

Primary question:
**지금 무엇에 집중하면 되지?**

Must show:
- active task;
- current session/lap state;
- essential time information;
- pause/help/complete controls as applicable.

World intensity:
LEVEL C / TASK-LOCAL.

Character:
small contextual presence only.

Badge:
No badge collection.
If a badge-worthy action occurs, defer major acknowledgement until safe completion/transition point.

Share:
No intrusive share prompt mid-session.

---

# 6. Ready & Set — SESSION RESULT / WRAP-UP

SCREEN_ID: READY_RESULT

Purpose:
Close the current exploration segment and guide next action.

Must show:
- what was completed;
- actual result/context;
- next/resume/return action;
- relevant badge/history acknowledgement if canonical.

Must not become:
- analytics dashboard;
- score/rank board;
- reward explosion.

Badge:
May show one associated canonical badge or badge grade change where relevant.

Star conflict rule:
Generic Ready “획득 별” must not be visually or semantically confused with BADGE_STAR_GRADE.

Share:
탐험 완료 공유 may originate here.

---

# 7. Snap & Pop — BEACH HOME

SCREEN_ID: SNAP_BEACH_HOME

Purpose:
Entry into thought/expression exploration.

Primary question:
**어떤 생각을 꺼내볼까 / 어디서 표현을 시작할까?**

Must show:
- Beach regional identity;
- five expression landmarks;
- resume state if an unfinished expression exists;
- Ask / Imagination access only where hierarchy is clear.

Must not show:
- full Growth dashboard;
- full Badge collection;
- Wish shop inventory;
- Family expansion controls.

World intensity:
LEVEL B.

Landmarks:
- 아이디어 동굴
- 감정 호수
- 묘사 숲
- 관점 전망대
- 마무리 캠프

They are equal-access sub-destinations, not level-locked stages.

Character:
MAIN_COMPANION_SLOT can be visible.
Crew reaction remains contextual.

---

# 8. Snap & Pop — WRITING

SCREEN_ID: SNAP_WRITING

Purpose:
Child-authored expression.

Primary question:
**내 생각을 어떻게 내 말로 남길까?**

Visual center:
the child's current draft / expression.

Must show:
- current expression step;
- prompt/question;
- writing/speaking input;
- one dominant next action;
- optional hint/help.

Must not show:
- reward totals;
- shop;
- full map;
- unrelated badge collection;
- persistent large character.

World intensity:
LEVEL C.

Crew:
CREW_REACTION_SLOT only.
Never cover input.
Intervention ladder remains observe → wait → short reaction → question → hint → minimal re-question.

Badge:
Observation may be recorded internally.
Do not interrupt writing with award animation.

---

# 9. Snap & Pop — ASK

SCREEN_ID: SNAP_ASK

Purpose:
Child curiosity input.

Primary question:
**진짜로 알고 싶은 게 뭐지?**

Must distinguish from Imagination.

Must show:
- child's question;
- clear submit/listen/speak actions;
- return context.

World intensity:
LEVEL C.

Crew:
answer subject/presentation layer.
OpenAI/provider identity remains internal.

Badge:
No automatic “curiosity badge” unless canonical evidence rule exists.

---

# 10. Snap & Pop — UNDERSTAND

SCREEN_ID: SNAP_UNDERSTAND

Purpose:
Present child-friendly understanding while preserving truth state.

Must support:
- VERIFIED
- PARTIAL
- INSUFFICIENT

Must show:
- answer/explanation;
- truth/uncertainty state in child-appropriate language;
- optional next curiosity;
- optional return-to-expression action.

Must not:
- visually upgrade uncertain answer into certainty;
- turn answer into test/score.

World intensity:
LEVEL C.

---

# 11. Snap & Pop — IMAGINATION

SCREEN_ID: SNAP_IMAGINATION

Purpose:
Expand scene/feeling/idea when useful.

Must preserve:
- source session;
- source landmark;
- source step;
- source draft;
- return target.

Must not:
- become separate mini-game;
- replace child's final wording;
- lose original writing context.

World intensity:
LEVEL C with slightly richer imaginative accent allowed.

---

# 12. Snap & Pop — RESULT

SCREEN_ID: SNAP_RESULT

Purpose:
Closure of one expression journey.

Must show:
- child-authored final expression;
- concise reflection/strength cue;
- next action;
- relevant records linkage;
- canonical badge acknowledgement if applicable.

Must not become:
- Growth dashboard;
- Badge collection;
- Gem shop;
- multi-panel analytics page.

World intensity:
LEVEL B→C transition.

Badge:
One primary relevant badge/progression acknowledgement max by default.
No unrelated badge carousel.

Share:
May create share payload with expression/result + badge/history context.

---

# 13. Snap & Pop — RECORDS

SCREEN_ID: SNAP_RECORDS

Purpose:
Return to prior authored expression/history.

Must distinguish:
- original;
- revision;
- Special memory;
- curiosity/imagination history where applicable.

Must not:
- score writing;
- overwrite original with revision;
- re-award rewards on edit.

Badge:
Can act as history index/tag where canonical.

World intensity:
LEVEL B low-intensity / archive-like.

---

# 14. Snap & Pop — GROWTH

SCREEN_ID: SNAP_GROWTH

Purpose:
Show continuity of exploration over time.

Must distinguish from Badge.

May show:
- growth-tree continuity;
- broad activity history;
- badge preview/link as separate module.

Must not imply:
- child ability score;
- badge = growth;
- gem = growth;
- affinity = growth.

Current language review:
evaluative stage labels such as “대작가” remain REVIEW_REQUIRED before final visual lock.

---

# 15. Snap & Pop — TREASURE / WISH

SCREEN_ID: SNAP_TREASURE

Purpose:
View Snap-owned gem/wish economy.

Must distinguish:
- SNAP_WISH_GEM;
- wish;
- blessing execution.

Must not show:
- badge star grade as currency;
- character power;
- rarity;
- family-wide currency.

World intensity:
LEVEL B / Snap region.

---

# 16. Snap & Pop — CREW

SCREEN_ID: SNAP_CREW

Purpose:
Relationship/identity view for exploration crew.

Must show:
- known friends;
- current companion;
- relationship expressions/memories where applicable.

Must not show:
- power stats;
- rarity;
- learning bonus;
- reward multiplier.

Affinity = relationship distance only.

---

# 17. Snap & Pop — SPECIAL

SCREEN_ID: SNAP_SPECIAL

Purpose:
Optional unusual encounter / micro-event.

Must feel:
- surprising;
- contextual;
- world-connected.

Must not feel:
- rare loot;
- limited-time FOMO;
- stronger character;
- premium event.

Skip = no penalty.

---

# 18. Hide & Seek — JUNGLE/WATERFALL HOME

SCREEN_ID: HIDE_JUNGLE_HOME

Purpose:
Entry into vocabulary discovery/retrieval exploration.

Must show:
- current mission/word set;
- resume/next action;
- regional identity;
- access to capture/mission management/memory ladder as subordinate actions.

Must not show:
- legacy police/detective/arrest framing;
- generic reward dashboard;
- Snap gem/wish economy.

World intensity:
LEVEL B.

Character:
current companion persists.

---

# 19. Hide & Seek — LEARNING / SEEK

SCREEN_ID: HIDE_SEEK

Purpose:
Retrieve/find hidden word or meaning.

Must show:
- clue/current retrieval task;
- one primary response action;
- progress only as needed;
- answer-safe crew support.

Must not:
- reveal answer through crew;
- overload with world art;
- show unrelated achievements.

World intensity:
LEVEL C.

Badge:
Events such as retry/help/return may be observed internally.
No mid-recall award interruption.

---

# 20. Hide & Seek — MEMORY LADDER

SCREEN_ID: HIDE_MEMORY

Purpose:
Understand what needs another retrieval and what is stabilizing.

Must show:
- memory state;
- reason/evidence where child-appropriate;
- next recall action.

Must not:
- become rank/ability report;
- revive old arbitrary UI-only thresholds.

Badge:
Separate from memory strength.
A badge may reference a meaningful behavior but must not imply vocabulary mastery.

---

# 21. Hide & Seek — COMPLETION

SCREEN_ID: HIDE_RESULT

Purpose:
Close current vocabulary exploration and guide next step.

May show:
- what was explored;
- meaningful retrieval result;
- next action;
- relevant canonical badge/history context.

Must not:
- equate completion badge with mastery;
- use legacy reward assets as automatic active badges.

Share:
May create app-owned result share payload using shared badge representation if applicable.

---

# 22. Shared BADGE COLLECTION

SCREEN_ID: SHARED_BADGE_COLLECTION

Ownership:
TAKY shared semantic system; presentation may be surfaced from authorized app/profile shell.

Purpose:
Browse meaningful learning/process history through badges.

Must show:
- canonical active badges only;
- badge name;
- tier;
- star grade 1–5;
- associated experience/history references where available.

Must not show:
- WORKING_DRAFT items as earnable;
- candidate/review internals;
- leaderboard;
- ability ranking;
- EXP/gem conversion.

Visual:
recovered circular hand-drawn/pastel contract.
Profile Character as protagonist.

Open:
exact primary entry surface remains to be finalized.

---

# 23. Shared BADGE DETAIL

SCREEN_ID: SHARED_BADGE_DETAIL

Purpose:
Explain the badge as lived history.

Should answer:
- 이 배지는 어떤 경험을 뜻하지?
- 언제/어디에서 이런 순간이 있었지?
- 현재 Tier/성급은 무엇이지?

May show:
- related Ready/Snap/Hide records;
- island region/context;
- share action.

Must not:
- expose opaque trigger math;
- label child ability;
- encourage farming.

---

# 24. Shared SHARE CARD composition

SCREEN_ID: SHARED_SHARE_CARD

Purpose:
Share an exploration/result/history in a compact understandable form.

Priority:
1. actual result/record;
2. contextual reaction;
3. associated badge/history if relevant;
4. tier + star grade;
5. profile character/theme if privacy allows;
6. regional/island supporting visual.

Must not:
- let scenery dominate;
- invent result numbers;
- expose internal evidence;
- confuse badge star grade with generic stars;
- require re-picking avatar/theme.

---

# 25. Settings

SCREEN_ID: APP_SETTINGS

Purpose:
Configuration only.

World intensity:
LEVEL C/minimal.

Must not be a storage place for unresolved product functions.

Settings must not contain primary child journeys that have no proper IA home.

---

# 26. Non-happy state composition

Every material screen needs relevant variants:

LOADING
EMPTY
READY
SUCCESS
PARTIAL
BLOCKED
RETRY
OFFLINE
STALE
RECOVERY

Rule:
Non-happy states retain the same screen purpose and ownership.
Do not replace them with generic technical error pages where a product-specific recovery is possible.

---

# 27. Character visibility rule by screen type

WORLD SCREEN:
large/medium contextual character presence allowed.

TRANSITION SCREEN:
character can guide direction.

TASK SCREEN:
small/non-blocking.

RESULT SCREEN:
brief acknowledgement.

RECORD/SETTINGS:
minimal or absent unless contextually useful.

No character presence merely to fill empty space.

---

# 28. Meta-system visibility rule

HOME / MAP:
only current/relevant meta signals.

TASK:
almost none.

RESULT:
relevant outcome only.

RECORD:
history-linked meta only.

GROWTH:
growth only + separated badge preview.

TREASURE:
gem/wish only.

BADGE COLLECTION:
badge only.

This prevents semantic collapse.

---

# 29. Screen acceptance checklist

Before low-fi approval, every screen must answer:

1. What is the purpose?
2. What is the child's primary question?
3. What is the primary action?
4. What must always be visible?
5. What must never dominate?
6. What world intensity level applies?
7. Where can the crew appear?
8. Which meta systems may appear?
9. Which states exist?
10. What is back/return?
11. Who owns the runtime state?
12. What data persists?
13. What happens offline/blocked?
14. Does it accidentally imply score/power/rank?
15. Does it create a new requirement?

If any answer is missing:
DO NOT HIGH-FI.

---

# 30. Next artifact after this standard

After approval, produce:
A. Screen Inventory
B. Screen State Matrix
C. Transition / Return Matrix
D. Component Responsibility Map
E. Low-fi wireframes

Only then:
Design Direction → High-fi Mockups.

END
