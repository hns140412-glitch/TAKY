# TAKY EXPLORER CREW VOICE — CURRENT / PRE-LOCK — 2026-10-08

Status: MAIN_CREW LOCK_CANDIDATE / PLAY_CAMP COMMON BANK CANDIDATE / PAID GENERATION HOLD

## 1. Authority
Explorer Crew is shared across Ready / Hide / Snap / Play Camp.
It is NOT Play Camp-owned.

Canonical resume:
D:\Git PWA\TAKY\HANDOFF\TAKY_EXPLORER_CREW_NEW_CHAT_START_2026-10-08_LATEST.md

Implementation evidence repo:
D:\Git PWA\BETA_BRANCH_REVIEW_20261003\snap-crew

Production grouping:
- PLAY_CAMP
- MAIN_CREW = upper-elementary focus
- MIDDLE = later expansion pack

## 2. Runtime consumption truth
Current canonical runtime automatically resolves:
- ASK
- HINT
- ACKNOWLEDGE

Identity/runtime source also supports:
- GREET / RECONNECT -> approved signature
- Core6 sourced scene lines where applicable

Future intents such as TRY_AGAIN / SUCCESS / MEMORY / GOODBYE remain unproduced until a concrete runtime consumer exists.

## 3. MAIN_CREW E5/E6
Current implemented bank:
- 24 characters
- ASK / HINT / ACKNOWLEDGE
- 2 variants each
- 144 lines
- 144/144 unique
- total text: 5,022 characters
- Core6 first wave: 36 clips / 1,222 chars
- later 18 characters: 108 clips / 3,800 chars

Additional current shared source material:
- approved signatures: 24 clips / 411 chars
- evidence-gated memory callbacks: 30 clips / 1,001 chars
- Core6 sourced scenes: 30 clips / 677 chars

Planning envelopes at the observed ~1 credit/character technical probe assumption only:
- MAIN 144 only: ~5,022 / +10% 5,525 / +25% 6,278
- MAIN + signatures: ~5,433 / +10% 5,977 / +25% 6,792
- MAIN + signatures + memory: ~6,434 / +10% 7,078 / +25% 8,043
- all current candidate/source material incl. Core6 scenes: ~7,111 / +10% 7,823 / +25% 8,889

The earlier 4,852-char / 988-char planning numbers are stale and superseded by R9 source truth.

These are planning estimates, NOT current ElevenLabs billing authority.

## 4. MAIN_CREW quality remediation
Codex first targeted script review:
receipt:
pf:explorer-crew-main-e56-script-lock-review-20261008:3fa8effaacca0932

Verdict:
HOLD with line-local MEDIUM findings; no full rewrite requested.

Remediation:
- 30 candidate strings changed line-locally
- semantic collisions reduced
- generic/accusatory/teacher-like wording reduced
- false prior-state implication removed
- memory PROMISE_OR_PLAN generalized to evidence-backed event
- missing learner stage ASK/HINT/ACK generic fallback removed

Generic fallback fix:
- no school_stage -> LEARNER_STAGE_REQUIRED
- unavailable Script Authority -> fail closed
- no generic DERIVED ASK/HINT/ACK fallback

Post-remediation:
- 144/144 unique
- wit/relation/anti-repeat/memory gates PASS
- full Crew suite PASS

Codex remediation micro-recheck:
receipt:
pf:explorer-crew-main-e56-remediation-recheck-20261008:f7445cd3f4732486

Execution result:
OUTCOME_UNKNOWN.
Do NOT repeat same failed route blindly.

Therefore:
MAIN_CREW status = LOCK_CANDIDATE_WITH_INDEPENDENT_RECHECK_DEBT.
It is NOT final SCRIPT_LOCK yet.

## 5. Production-group runtime alignment
Old learner-band-only runtime naming was aligned to current production grouping.

Now:
- E5/E6 -> MAIN_CREW
- MIDDLE -> MIDDLE
- FOUNDATION / E1_2 / E3_4 -> PLAY_CAMP
- app_id PLAY_CAMP explicitly resolves to PLAY_CAMP

Only MAIN_CREW is currently in LOCKED_PRODUCTION_GROUPS for runtime dialogue selection.

PLAY_CAMP / MIDDLE ASK-HINT-ACK:
- SCRIPT_BAND_NOT_LOCKED
- authority_status = PRODUCTION_GROUP_NOT_LOCKED
- fail closed

This prevents MAIN_CREW lines from leaking into Play Camp merely because a learner has an E5 stage.

## 6. PLAY_CAMP Core6 common candidate bank
A bounded candidate bank was authored for initial Core6 only:
- DUBI
- LORI
- INK
- NOVA
- TAKE
- ZERO

Structure:
6 characters × ASK/HINT/ACK × 2 variants
= 36 candidate lines

Measured:
- 36/36 unique
- 994 total characters
- automated banned baby-talk / ability-praise scan PASS
- length bounds PASS
- current token-set cross-character collision maximum = 0 in measured pairs

Important:
PLAY_CAMP_CANDIDATE_SCOPE =
COMMON_NEUTRAL_BANK__NOT_SCRIPT_LOCKED__NOT_RUNTIME_ENABLED

Current consumer contract:
- Play Camp reuses ExplorerProfile.presentationBand; it does NOT invent a new school_stage authority.
- EARLY_EXPLORER / LOWER_PRIMARY → PLAY_CAMP
- UPPER_PRIMARY → MAIN_CREW
- SECONDARY → MIDDLE
- Play Camp publishes TAKY_PLAY_CAMP_EXPLORER_CREW_CONTEXT_V1 with app_id, presentation_band, production_group and active_crew_ids.
- browser smoke PASS at 1024×768 and 1180×820 confirms EARLY_EXPLORER → PLAY_CAMP and no school_stage field is invented.

Therefore these 36 lines remain NOT SCRIPT_LOCKED and NOT runtime-enabled because content/production approval is still open, not because context is missing.

Do NOT generate these 36 in ElevenLabs yet.

Current TAKY content review:
- PASS_WITH_FIXES
- six abstract phrases simplified for EARLY_EXPLORER readability
- 36/36 unique
- 994 chars
- collision max 0
- full Crew suite 6/6 PASS
- evidence: HANDOFF/TAKY_EXPLORER_CREW_PLAY_CAMP_CORE6_CONTENT_REVIEW_2026-10-08.md

Next Play Camp Crew gate:
1. independent targeted recheck when a reliable reviewer route is available
2. PLAY_CAMP SCRIPT LOCK
3. ROUTE BEFORE CREATE / dedup
4. exact clip/chars/cost
5. explicit USER approval
6. bounded generation + listening QA

## 7. Source lock
Current candidate source lock:
EXPLORER_CREW_V2_SOURCE_LOCK_20261008_DIALOGUE_CANDIDATE_R9

R9 covers:
- MAIN_CREW production-group alignment
- app_id + presentation_band propagation into dialogue resolver
- ExplorerProfile GrowthBand → PLAY_CAMP / MAIN_CREW / MIDDLE mapping
- generic fallback removal
- Codex line-local remediation
- PLAY_CAMP Core6 common candidate bank
- TAKY content review six-line readability remediation
- fail-closed Core6 scene-line production-group gate: PLAY_CAMP can no longer consume MAIN sourced scene lines
- PLAY_CAMP remains NOT runtime enabled until SCRIPT LOCK

Current full snap-crew regression:
6/6 PASS

git diff --check:
PASS except normal LF->CRLF warning on source-lock JSON.

## 8. Voice Family / reuse rule
Voice Family remains casting/acting family, not mandatory identical timbre.

VF01 ADVENTURE:
DUBI / BELO / TOTO / TESS

VF02 CARE:
LORI / PEACH / BORI / SEL

VF03 OBSERVE:
INK / MOCA / MARU / LUMI

VF04 LEADER:
TAKE / KIRO / RIN / ZEKE

VF05 CONNECT:
NOVA / NIA / POPO / VIVI

VF06 CALM_DISCOVERY:
ZERO / SOLA / MINT / RUNE

Start with one anchor Voice ID per family.
Only split character-specific Voice IDs if listening QA finds identity collision.

Common greeting/reunion/relation/memory assets should be reused across apps where semantic meaning is identical.

## 9. Hard production boundary
No paid Crew generation now.

MAIN_CREW:
independent recheck debt remains before final SCRIPT LOCK.

PLAY_CAMP:
presentationBand consumer contract PASS; TAKY content review PASS_WITH_FIXES; independent recheck + SCRIPT LOCK remain.

MIDDLE:
deferred expansion.

Teacher / Coach / Maker pronunciation, teaching and mission authority remains separate.
No Crew clip may replace canonical pronunciation assets.

No push / merge / deploy.
