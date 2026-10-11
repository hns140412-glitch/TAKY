# TAKY Voice / ElevenLabs PRE-PRODUCTION — NEW CHAT START
Date: 2026-10-07
Status: PREPRODUCTION RECONCILED / CLAUDE↔ELEVENLABS MCP+OAUTH PASS / ELEVENLABS GENERATION NOT YET CALLED / NO DEPLOY

## 0. Authority
- Existing TAKY Master Logic, CLOSED/PROMOTED, Explorer Crew Visual ID/Personality authority remain unchanged.
- This document adds voice-production rules only. It does not redefine character identity or Learning Engine ownership.
- ElevenLabs is a high-quality asset-production executor, not runtime authority.
- USER = final listening approval. TAKY = voice/dialogue/learning authority. Claude Code = production executor after MCP connection.

## 1. Voice layers and Play Camp role routing
1. CHARACTER_VOICE: Explorer Crew identity/personality/species acting.
2. LEARNING_VOICE_KO: Korean/Hangul pronunciation authority; accuracy outranks acting.
3. LEARNING_VOICE_EN: native-English phonics/CVC pronunciation authority.
4. COACH_VOICE: game/mission/turn/retry/completion; energetic, never coercive.
5. MAKER_VOICE: Paper/Spatial/making studio; bright, witty, action-timed maker host.

Play Camp runtime routing:
- Korean sound/jamo/blend/syllable/word -> KO Teacher
- English phonics/CVC/word -> EN Teacher
- Hub/mission/turn/retry/completion -> Coach
- Paper/Spatial/fold/cube-net/creation -> Maker
- Explorer Crew -> companion reaction/hint only; never pronunciation authority

One scene MUST NOT stack Teacher + Coach + Maker + Crew. Existing reaction-budget/cooldown/arbitration decides the single active speaker.

## 2. Explorer Crew 24 -> 6 Voice Families
VF01_ADVENTURE: DUBI, BELO, TOTO, TESS
- bright, quick, curious, action-forward; canine/fox/monkey rhythm may affect timing, never animal imitation.

VF02_CARE: LORI, PEACH, BORI, SEL
- warm female family; playroom-teacher quality; soft, safe, not saccharine.

VF03_OBSERVE: INK, MOCA, MARU, LUMI
- calm announcer-like female/neutral; observation, thinking, small pauses, clear diction.

VF04_LEADER: TAKE, KIRO, RIN, ZEKE
- dependable male family; friendly taekwondo-instructor quality; clear, grounded, never military/shouting.

VF05_CONNECT: NOVA, NIA, POPO, VIVI
- bright presenter family; social, playful, creative; avian/duck traits affect rhythm only.

VF06_CALM_DISCOVERY: ZERO, SOLA, MINT, RUNE
- relaxed mid-low neutral; musical/steady/adaptive; capybara calm and chameleon flexibility may affect cadence only.

## 3. Species acting rule
- Species is an acting modifier: response latency, cadence, breath, curiosity pattern, physical-energy impression.
- Species is NOT permission for animal cries, caricature, baby talk, or changing canonical personality.
- Human/Special Crew prioritize approved personality/role over species-style modifiers.

## 4. Character differentiation inside one family
Each character owns a CharacterVoiceProfile:
voice_family, energy, warmth, tempo, pause, confidence, curiosity, playfulness, calmness, strategy, empathy, acting_tags, wit_tags.
The base voice may be shared; the profile must make characters perceptibly distinct.

Dialogue differentiation is mandatory:
- personality decides observation/action/strategy/empathy framing;
- species only modifies acting rhythm/breath/reaction timing;
- wit must fit the character rather than becoming generic jokes;
- humor may never obscure a learning instruction or pronunciation;
- repeated praise templates are forbidden.

Current runtime-first authored set is maintained in TAKY_EXPLORER_CREW_VOICE_DIALOGUE_MATRIX_2026-10-08.md (signature + ASK + HINT + ACKNOWLEDGE per character, plus sourced Core6 scene lines).
Future TRY_AGAIN / SURPRISE / SUCCESS / MEMORY / GOODBYE variants MUST NOT be generated until a concrete UI/runtime consumer exists.

## 5. Dialogue intents
ENCOUNTER, GREETING, START, CURIOUS, DISCOVERY, ASK, LISTEN, THINK,
HINT_1, HINT_2, TRY_AGAIN, ENCOURAGE, SURPRISE, SUCCESS, COMPLETE,
WAIT, RETURN, MEMORY, GOODBYE.
- Dialogue is authored by intent first, then character-derived variation.
- No ridicule, grading tone, answer dump, or repetitive exaggerated praise.
- Prefer evidence/action feedback: "찾았네", "다른 방법을 썼네", "그 단서를 발견했네".

## 6. Learning / Coach / Maker voice authority
HANGUL_TEACHER_F / PLAY_CAMP_TEACHER_KO:
- warm female, playroom teacher + announcer quality.
- owns Korean phoneme cues, blending, syllables, words, pronunciation instruction.
- stable Voice ID/settings after approval.

PLAY_CAMP_TEACHER_EN:
- native-English pronunciation authority for phonics/CVC.
- owns English phoneme, blend and word exemplars.
- MUST NOT reuse Korean-accented TTS merely to reduce Voice IDs.
- stable Voice ID/settings after approval.

HANGUL_COACH_M / PLAY_CAMP_COACH:
- friendly taekwondo-instructor energy.
- owns game start, turn-taking, mission, retry, completion.
- never owns canonical KO/EN phoneme exemplars.

PLAY_CAMP_MAKER:
- distinct energetic maker-host voice for Paper/Spatial/creation.
- bright, playful, witty and clear; never shouting.
- one physical action per utterance, then enough silence for the child to act.
- does not replace Teacher pronunciation authority.

## 7. Hangul learning principle
LETTER_NAME != LETTER_SOUND.
Primary route: SOUND -> BLEND -> SYLLABLE -> WORD -> SENTENCE/STORY.
Letter names (기역/니은/디귿...) are secondary metadata, not the first sound cue.
Never teach consonant phonemes by adding ㅡ ("그/느/드/브") as if that were the consonant itself.

Required asset distinction:
- letter_name
- onset_phoneme_cue
- coda_phoneme_cue where applicable
- vowel
- blend
- syllable
- word
- sentence/story

Examples:
- ㄱ: onset cue separately approved; coda /k̚/-type cue separately approved where needed.
- ㅇ: onset = no consonant sound; coda = /ŋ/ asset. Never reuse one asset for both.
- ㄹ and other position-sensitive sounds require position-aware QA.

## 8. Hangul production packs
PACK_A_CORE_SOUND: 14 basic consonants + 10 basic vowels, position-aware where required.
PACK_B_BLEND: high-frequency CV combinations.
PACK_C_SYLLABLE: high-frequency child-usable syllables.
PACK_D_WORD: familiar nouns/actions from child's real life and app content.
PACK_E_INSTRUCTION: listen, choose, combine, trace/write, retry, repeat.
PACK_F_GAME_FEEDBACK: start, hint, discovery, success, transition.
PACK_G_DYNAMIC_STORY: today's daycare message / read book / child's question; dynamic layer only when needed.

## 9. Pronunciation QA hard gates
PHONETIC_CORRECTNESS, NO_ADDED_VOWEL, NO_LETTER_NAME_LEAK,
POSITION_CORRECTNESS, CHILD_CLARITY, NATURALNESS, CONSISTENT_VOICE,
VOLUME, START_TRIM, END_TRIM.
Any core sound asset failing one gate = REJECT. No runtime fallback to model-generated speech.

## 10. Asset state + ROUTE BEFORE CREATE HARD RULE
CANDIDATE -> QA_PASS -> USER_APPROVED -> LOCKED.
LOCKED core phoneme/syllable/dialogue assets are file playback only.

**ROUTE BEFORE CREATE is mandatory.** TAKY should shepherd the executor to the best route instead of merely blocking work.
Before any ElevenLabs generation:
1. resolve semantic asset key = role + locale + character/voice_family + intent + script/meaning + state;
2. search manifest/registry for an existing semantic equivalent;
3. LOCKED / USER_APPROVED / QA_PASS -> `REUSE_EXISTING`: bind the existing asset and continue;
4. CANDIDATE -> `REVIEW_EXISTING_CANDIDATE`: listen/review first, then approve/reject/revise;
5. REJECTED -> `REGENERATE_WITH_REASON`: carry forward rejection reason + predecessor and generate one corrected candidate;
6. no equivalent -> `CREATE_NEW`: create one bounded candidate and return to QA before expansion.

The system should not leave the executor at a dead end. Every non-generation decision must return the correct next action.
Automatic duplicate recreation for variation, a new chat, renamed UI, another app surface, or executor convenience is not a valid route.
Same semantic line used in Play Camp / Ready / Hide / Snap should reuse the same approved asset where role/locale/meaning match.

Production receipt MUST record:
asset_key, source_voice_id, model/settings, script, predecessor_asset_id if any, reason_for_new_generation, credit_delta, QA state.

Implemented enforcement:
- `OS/VOICE_ASSET_MANIFEST_SCHEMA_V2.json` — semantic key / locale / role / predecessor / reason / cost receipt schema
- `CURRENT/VOICE_ASSET_REGISTRY_CURRENT.json` — central semantic asset registry
- `ENFORCEMENT/voice_asset_reuse_router.py` — REUSE / REVIEW / REGENERATE_WITH_REASON / CREATE_NEW shepherding router
- `ENFORCEMENT/voice_dryrun_planner.py` — <=500-credit dry-run route/call-budget preflight
- current router+planner regression: 6/6 PASS

## 11. File naming
crew/{visual_id}_{code}/{intent}_{variant}.mp3
hangul/sound/onset/{jamo}_{variant}.wav
hangul/sound/coda/{jamo}_{variant}.wav
hangul/vowel/{jamo}_{variant}.wav
hangul/blend/{key}.wav
hangul/syllable/{syllable}.wav
hangul/word/{word_id}.wav
hangul/system/{intent}_{variant}.mp3

## 12. ElevenLabs execution gates
G0 PREPRODUCTION SPEC COMPLETE — PASS
G1 Claude Code <-> ElevenLabs MCP + OAuth — PASS
G2 explicit technical dry-run allowance:
- exactly one short TECHNICAL_TTS call
- <=500-credit hard ceiling
- <=60 text characters
- zero retries
- usage BEFORE is preferred but NOT a blocker when the MCP does not expose it
- usage AFTER is recorded when exposed
- the technical clip is NOT a production candidate and bypasses semantic-asset reuse routing only for connectivity verification
G3 KO Teacher x 3 previews
G4 EN Teacher x 3 previews
G5 Coach x 3 previews
G6 Maker x 3 previews
G7 6 Voice Family anchor x 3 previews
G8 human comparative listening -> base role/family voices LOCK only where needed
G9 KO/EN core phoneme pilot + pronunciation QA
G10 small syllable/blend/word pilot
G11 current-runtime Crew signature/ASK/HINT/ACK pilot
G12 only after PASS + REUSE scan: bounded batch production
No gate skipping. AI generation != approval.
Do not create 24 unique Crew Voice IDs up front; start from six family anchors and split only where listening proves identity collision.

## 13. Cost/necessity
- Fixed dialogue and core learning audio are generated once, approved, stored, and replayed locally.
- ElevenLabs runtime calls are reserved for genuinely dynamic text only.
- Do not regenerate an approved asset merely for variation.
- Creator subscription month is treated as production month; asset library should minimize future recurring cost.

## 14. Next execution
1. Treat MCP+OAuth connection as already PASS; do not reconnect/re-register unless status actually fails.
2. Technical connectivity dry-run uses EXPLICIT_DRYRUN_ALLOWANCE and does not require semantic asset reuse routing.
3. Attempt usage BEFORE; if NOT_EXPOSED, record that and continue with exactly one short TTS call.
4. Do not retry a failed generation call.
5. Record usage AFTER when exposed and stop the run.
6. Voice Design, phoneme production, Crew production, and batch generation remain outside this technical allowance and return to normal ROUTE BEFORE CREATE gates.
7. No 24-character unique-voice set.
8. Stop for comparative listening/approval before expanding.
