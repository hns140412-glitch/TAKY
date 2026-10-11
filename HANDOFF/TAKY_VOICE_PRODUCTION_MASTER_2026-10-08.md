# TAKY VOICE PRODUCTION MASTER — 2026-10-08

Status: PLANNING CURRENT / PAID GENERATION NOT AUTHORIZED

## Authority
- Play Camp core-role script lock: PLAY_CAMP_DIALOGUE_SCRIPT_LOCK_2026-10-08.json
- Explorer Crew candidate source lock: EXPLORER_CREW_V2_SOURCE_LOCK_20261008_DIALOGUE_CANDIDATE_R9
- Route policy: ROUTE BEFORE CREATE
- Production principle: create only after exact scope, reuse check, bounded cost, explicit USER approval and listening QA.

## Cost assumption
Current planning uses the previously observed technical probe rate of approximately 1 ElevenLabs credit per input character.
This is an execution-planning assumption only.
Every paid call must still record usage before/after and stop on uncertain billing.

## Recommended production order

### P1 — Play Camp Core Role casting preview
Teacher / Coach / Maker only.

Current bounded preview:
- 18 calls
- 3 candidates for each of 6 role/locale sample slots
- 429 total input characters
- existing hard cap: 500 credits
- selected assets after QA: 6

Reuse:
- 5 selected preview scripts are already among the 25 locked production scripts
- reusable selected production text = 124 characters
- after preview reuse, remaining locked production = 20 clips / 607 characters

Expected Core Role total:
- preview: 429
- residual production: 607
- expected total: 1,036 credits
- bounded planning cap: 500 + 668 = 1,168 credits

Excluded:
- 24 deferred scripts
- 11 pronunciation assets
- Explorer Crew

Current execution status:
PREFLIGHT_INCOMPLETE_NOT_AUTHORIZED.
Missing Voice IDs/model/settings/output format/bounded executor remain unresolved.

### P2 — Explorer Crew Voice Family casting
Use one approved Core6 signature as the casting phrase for each Voice Family:
- VF01 DUBI
- VF02 LORI
- VF03 INK
- VF04 TAKE
- VF05 NOVA
- VF06 ZERO

3 candidates per family:
- 18 calls
- unique sample text: 75 characters
- expected: 225 credits
- 10% planning cap: 248 credits

Selected 6 signature samples are reusable as those characters' approved greeting assets.
Do not cast 24 separate voices before family-anchor listening QA proves a split is necessary.

### P3 — PLAY_CAMP Explorer Crew Core6
Current candidate bank:
- 36 clips
- 994 characters
- 36/36 unique
- TAKY content review: PASS_WITH_FIXES
- R9 runtime boundary regression: 6/6 PASS

Expected after SCRIPT LOCK:
- 994 credits
- 10% planning cap: 1,094 credits

Current status:
NOT SCRIPT_LOCKED / NOT runtime-enabled / NOT generation-authorized.
Independent targeted recheck is still required before lock.

### P4 — MAIN_CREW Core6 first wave
Current R9 MAIN Core6:
- 6 characters
- 36 ASK/HINT/ACKNOWLEDGE clips
- 1,222 characters

Expected:
- 1,222 credits
- 10% planning cap: 1,345 credits

Reason to split:
Core6 are the first-meeting crew. Produce them before 07–24 so unused future-character assets are not prepaid.

### P5 — MAIN_CREW 07–24 expansion
Remaining 18 characters:
- 108 ASK/HINT/ACKNOWLEDGE clips
- 3,800 characters

Expected:
- 3,800 credits
- 10% planning cap: 4,180 credits

Only execute after Core6 listening/runtime QA proves the Voice Family policy works.

## Current MAIN_CREW truth
R9 source truth:
- all 24 MAIN_CREW ASK/HINT/ACK lines = 144 clips
- current text = 5,022 characters
- 10% planning cap = 5,525 credits

Previous 4,852-character planning figures are stale and must not be used.

Additional shared source material:
- 24 approved signatures = 411 chars
- 30 evidence-gated memory callbacks = 1,001 chars
- 30 Core6 sourced scene lines = 677 chars

These are not automatically part of the first production batch.

Because the six Voice Family casting samples reuse six signatures:
- remaining signatures after casting selection = 336 chars

Optional later envelopes:
- remaining signatures: 336 expected / ~370 at 10%
- memory callbacks: 1,001 expected / ~1,102 at 10%
- Core6 MAIN scene lines: 677 expected / ~745 at 10%

Each remains subject to runtime-need and independent lock review.

## Runtime boundary fixed before production
R9 closes a leakage path:
- PLAY_CAMP presentation_band can no longer consume MAIN sourced Core6 scene lines
- scene lines require a valid learner stage + locked production group
- E5 MAIN path still resolves correctly
- PLAY_CAMP / unlocked groups fail closed

## Combined planning envelope
Do NOT execute as one batch.

If all currently prioritized stages P1–P5 were eventually approved:
- expected: 1,036 + 225 + 994 + 1,222 + 3,800 = 7,277 credits
- bounded stage caps: 1,168 + 248 + 1,094 + 1,345 + 4,180 = 8,035 credits

This excludes:
- pronunciation assets
- deferred 24 Play Camp scripts
- optional remaining signatures/memory/scene lines
- retries beyond explicitly approved bounded policy

## Hard boundary
No paid ElevenLabs generation now.
No pronunciation generation now.
No Crew batch generation now.
No push / merge / deploy.

Next approval-ready work:
1. finish independent targeted Crew recheck
2. lock relevant Crew scope
3. fill concrete Voice IDs / model / settings / output format
4. rerun exact preflight
5. report exact calls + hard cap
6. request explicit USER approval
7. generate one bounded stage only
8. listening QA before expansion
