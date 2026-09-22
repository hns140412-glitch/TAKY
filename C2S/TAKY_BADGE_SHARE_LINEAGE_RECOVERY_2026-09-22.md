# TAKY BADGE SHARE LINEAGE RECOVERY — 2026-09-22

Status: RECOVERED EXISTING RULES / CROSS-APP RECONCILIATION
Purpose: recover already-defined badge/share rules before any new UI proposal.

## 1. Source lineage recovered

Primary recovered share authority:
- Ready & Set Share Golden Contract REV_01 (2026-09-14)
- Ready UI Master lineage
- Snap badge source recovery + current badge visual/runtime contracts
- current Ready share-card runtime

This document does not invent a new sharing concept.

## 2. Existing share structure — recovered

Ready & Set already defines two canonical share moments:
1. 탐험 시작 공유
2. 탐험 완료 공유 / 탐험 기록

Share is:
- compact image + short text / feed-style presentation;
- information-and-reaction surface;
- not a decorative poster;
- driven by actual exploration/result context;
- dynamic copy under 탐험대/Guide behavior;
- profile theme inherited automatically;
- profile avatar/character inherited automatically subject to privacy/share permission;
- no theme picker at share time;
- no arbitrary replacement character.

## 3. Existing badge/share meaning — recovered

Badge sharing is not a new feature proposal.

Recovered intent:
- a badge can accompany a shared exploration/result/record;
- the badge gives context to an achievement, unusual process, recovery moment or funny/meaningful history;
- sharing can communicate both result and story/history;
- badge acts as experience metadata / story marker, not a score table;
- parent/family consumption is support/encouragement-oriented, not grading/surveillance;
- sharing is optional and non-punitive.

## 4. Badge representation in share

When a canonical badge is eligible to appear, the share representation may include:

BADGE_IDENTITY
+ BADGE_NAME
+ BADGE_TIER
+ BADGE_STAR_GRADE
+ EXPERIENCE/RECORD CONTEXT

The badge's star count means:
**Badge Star Grade / 성급 1–5**.

Tier:
GREEN → BLUE → RED → GOLD → PLATINUM.

Star grade must not be reinterpreted as generic reward stars.

## 5. Critical terminology lock

Badge star = BADGE_STAR_GRADE / 성급.

It is not:
- generic star currency;
- task completion points;
- Ready mission reward stars;
- Snap wish gem;
- child ability rating.

A share UI must never show an unrelated generic “획득 별” next to a badge star-grade in a way that makes the two appear equivalent.

## 6. Recovered Ready share rules that remain authoritative

### Dynamic content
Share content may reflect actual:
- task/exploration context;
- completion/progress;
- target/focus time where appropriate;
- continuity/achievement context;
- recording/event result;
- profile theme;
- profile avatar/character;
- allowed main/guest exploration-crew presence.

### Tone
Exploration crew is companion, not grader.
Do not:
- shame;
- scold;
- exaggerate failure;
- turn slower result into red-failure treatment.

### Theme
Profile theme is inherited from profile.
No re-selection at share time.
Theme changes expression, not data hierarchy/product purpose.

### Avatar/profile
Inherited from profile.
No share-time avatar picker.
Respect privacy/share opt-in and use non-identifying fallback when needed.

### Information priority
Actual exploration/result information comes before decorative background.

## 7. Badge-sharing content priority

Recommended canonical ordering recovered from the combined lineage:

1. actual shared artifact/result/experience;
2. concise context/reaction;
3. associated canonical badge when relevant;
4. badge tier + star grade;
5. profile character/theme expression if share permission allows;
6. secondary supporting visual/world context.

Badge does not replace the actual shared result.

## 8. Sharing states

A badge may be included only when its state is canonical and child-facing.

Allowed:
- newly awarded canonical badge;
- progressed canonical badge;
- existing canonical badge associated with the shared history.

Forbidden:
- WORKING_DRAFT_NOT_ACTIVE badge;
- REVIEW_REQUIRED candidate;
- unverified inferred badge;
- hidden internal evidence status;
- internal provider/model confidence.

## 9. Cross-app share rule

Ready / Snap / Hide may each create a share payload from their own product result, but the badge representation must follow the same shared Badge Visual/Grade contract.

App owns:
- local result/artifact;
- app-specific share context;
- privacy permission check.

Shared badge layer owns:
- badge identity;
- tier;
- star grade;
- canonical visual semantics;
- badge provenance reference.

Apps must not invent a second local badge identity or star-grade meaning.

## 10. Current fragmentation found

### GAP-BS-01 — Ready generic “획득 별” conflicts with badge star-grade
Current Ready `src/views/share-card-runtime.js` computes:
- generic stars from completion count;
- displays `획득 별`.

This is not currently linked to canonical badge star-grade.

Risk:
- generic reward star can be confused with badge 성급;
- same “star” symbol can carry two incompatible meanings.

Disposition:
**RECONCILIATION_REQUIRED.**

Do not silently relabel existing generic stars as badge stars.
First determine whether the generic Ready star reward remains valid under current Ready authority.
If retained, use a visually/semantically distinct unit.
If not retained, remove through Ready-owned product review.

### GAP-BS-02 — current share runtime does not consume shared badge payload
Ready share renderer currently receives result/profile/theme information but not canonical badge data.

Disposition:
producer/consumer integration OPEN.

### GAP-BS-03 — share badge selection rule not yet canonicalized
Existing intent supports badge-with-share, but exact automatic/manual badge selection rule needs recovery/closure.

Do not invent a picker until historical source recovery is exhausted.

### GAP-BS-04 — acquisition-time vs current grade representation remains unresolved
If an old record is reshared later:
- show grade at that historical moment?
- show current badge grade?
Existing source retrieved so far does not fully close this.

Status: OPEN / RECOVERY FIRST.

## 11. UI implication before mockup

Before any new share mockup:
- recover existing badge share visual references where available;
- preserve Ready Share Golden Contract layout purpose;
- integrate badge as contextual experience/history marker;
- never turn share card into badge dashboard;
- distinguish BADGE_STAR_GRADE from every other star/gem system;
- preserve optional sharing and privacy.

## 12. Current locked vocabulary

- 배지
- 티어
- 성급 (1–5성)
- 탐험 시작 공유
- 탐험 완료 공유
- 탐험 기록

Avoid inventing a new “achievement score” vocabulary.

END
