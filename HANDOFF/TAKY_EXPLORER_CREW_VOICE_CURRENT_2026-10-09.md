# TAKY EXPLORER CREW VOICE — CURRENT — 2026-10-09

Status: MAIN_CREW SCRIPT_LOCKED / PLAY_CAMP CORE6 SCRIPT_LOCKED + RUNTIME_ENABLED / MIDDLE HOLD / PAID GENERATION HOLD

Authority:
- Explorer Crew shared authority remains unchanged.
- Source lock: EXPLORER_CREW_V2_SOURCE_LOCK_20261009_SCRIPT_LOCK_R10
- Execution receipt: HANDOFF/TAKY_EXPLORER_CREW_SCRIPT_LOCK_R10_EXECUTION_2026-10-09.md
- Independent review: HANDOFF/CODEX_EXPLORER_CREW_R9_DIRECT_RECHECK_2026-10-09.md

MAIN_CREW:
- E5/E6
- 24 × ASK/HINT/ACKNOWLEDGE × 2 = 144 lines
- 144/144 unique
- 5,022 chars
- SCRIPT_LOCKED_MAIN_CREW_E5_6_2026-10-09
- runtime enabled

PLAY_CAMP:
- initial Core6 only
- 6 × ASK/HINT/ACKNOWLEDGE × 2 = 36 lines
- 36/36 unique
- 994 chars
- SCRIPT_LOCKED_PLAY_CAMP_CORE6_2026-10-09
- COMMON_NEUTRAL_BANK__SCRIPT_LOCKED__RUNTIME_ENABLED
- later18 ASK/HINT/ACK remains fail-closed as PLAY_CAMP_CORE6_ONLY

Runtime boundary:
- sourced Core6 scene lines are MAIN_CREW-only
- PLAY_CAMP cannot consume MAIN sourced scene text
- E3/lower sourced scene request fails closed
- E5 MAIN sourced scene remains allowed

Verification:
- Codex content recheck: MAIN PASS / PLAY_CAMP Core6 PASS
- Codex runtime finding closed by MAIN_CREW-only sourced-scene guard
- permanent guard regression PASS
- Explorer Crew suite 6/6 PASS
- R10 normalized source lock 35/35 PASS
- Ready / Hide / Snap common vendor R10 drift 0

MIDDLE:
- expansion pack / not script locked / runtime fail-closed

Voice production:
- no ElevenLabs generation authorized by this lock alone
- route-before-create, reuse/dedup, exact cost, explicit USER approval still required
- no push / merge / deploy
