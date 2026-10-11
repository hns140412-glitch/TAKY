# TAKY VOICE — ELEVENLABS DRY-RUN + DIALOGUE REVIEW
Date: 2026-10-08
Status: PRE-PRODUCTION REVIEW COMPLETE / MCP AUTH CONFIRMED BY LATEST CLAUDE SESSION / NO BULK GENERATION

## 1. Current truth
- Claude Code ElevenLabs user-scope MCP is registered and the latest sessions show Connected after OAuth.
- Do not use the older "Needs authentication" record as current authority.
- No API key is required/copied for Hosted MCP OAuth.
- Bulk production is still HOLD until dry-run usage is measured.

## 2. Critical implementation findings
### Explorer Crew
Actual current dialogue runtime consumes:
- GREET / RECONNECT -> approved signature
- ASK / HINT / ACKNOWLEDGE -> derived personality line
- Core6 sourced scene lines: IDEA / EMOTION / DESCRIPTION / VIEWPOINT / FINAL
Therefore producing all 20 future intents now would create unused voice assets.

### Hangul Play
Current code still contains DEV-era consonant approximations:
- ㄱ=그, ㄴ=느, ㄷ=드, ㄹ=르, ㅁ=므, ㅂ=브, etc.
Current audio fallback can speak these through browser SpeechSynthesis.
This conflicts with the user-locked rule:
LETTER_NAME != LETTER_SOUND and consonant phoneme != consonant+ㅡ.

Current legacy generator also creates 175 clips for female + 175 clips for male.
This duplicates the same learning phoneme/syllable/word layer even though:
- HANGUL_TEACHER_F owns precise learning audio.
- HANGUL_COACH_M owns mission/game/encouragement only.
Do not reproduce this 350-asset duplication in ElevenLabs.

## 3. Revised architecture
Keep:
- VF01 ADVENTURE: DUBI / BELO / TOTO / TESS
- VF02 CARE: LORI / PEACH / BORI / SEL
- VF03 OBSERVE: INK / MOCA / MARU / LUMI
- VF04 LEADER: TAKE / KIRO / RIN / ZEKE
- VF05 CONNECT: NOVA / NIA / POPO / VIVI
- VF06 CALM_DISCOVERY: ZERO / SOLA / MINT / RUNE
- HANGUL_TEACHER_F
- HANGUL_COACH_M

Important refinement:
Voice Family = casting/acting family, not a permanent requirement that all four characters share one identical timbre.
Start with one anchor voice per family. After listening, only create additional character-specific voices where identity collisions remain.
This preserves quality without wasting voice slots/operations.

Species is an acting modifier only:
reaction speed / cadence / breath / pause / confidence / physical-energy impression.
Never animal cries or caricature.

## 4. Crew production scope V1 — SCRIPT GATE UPDATED
The former 126-clip estimate is REVOKED as a production instruction.

Reason:
- ASK/HINT/ACK must vary by learner school_stage and character relationship state.
- Shared Memory callbacks are part of the Explorer Crew canonical behavior.
- Current E5/E6 candidate authority contains two variants per ASK/HINT/ACK for all 24 characters plus evidence-gated memory callbacks.
- Other learner stages are intentionally fail-closed until their scripts are reviewed.
- Approved signatures remain valid identity lines.
- Core6 sourced scene lines remain source material but grade gating applies before learning/thinking dialogue is used.

Current rule:
DO NOT batch-generate Crew ASK/HINT/ACK from the old matrix.
Produce only after the requested learner band is SCRIPT_LOCKED and runtime consumption is verified.
Future intents such as TRY_AGAIN / SUCCESS / MEMORY / GOODBYE remain unproduced until concrete runtime consumers exist.

## 5. Dialogue quality gates
- One thought/action per utterance.
- Prefer 2-7 seconds.
- No lecture before interaction.
- No "천재야 / 최고야 / 역시 너야" ability praise.
- Prefer evidence/action feedback.
- Incorrect response -> one clue, never direct answer dump.
- One speaker / one question / one hint at a time.
- Respect reaction budget, cooldown, and SILENT mode.
- interaction_mode and delivery_mode remain separate axes.

## 6. Hangul production authority
Teacher owns:
- consonant phoneme cues
- vowels
- blends
- syllables
- words
- pronunciation instruction

Coach owns:
- ready/start
- turn-taking
- retry
- mission transitions
- completion
- short physical/game encouragement

Child tap:
grapheme tap -> LOCKED local phoneme asset immediately.
No child-runtime ElevenLabs call.
No incorrect browser TTS fallback for consonant phonemes.

Core Korean phoneme QA:
PHONETIC_CORRECTNESS
NO_ADDED_VOWEL
NO_LETTER_NAME_LEAK
POSITION_CORRECTNESS
CHILD_CLARITY
CONSISTENT_VOICE

If Eleven v4 IPA cannot produce a clean isolated Korean stop consonant without a following vowel:
FAIL that TTS asset. Do not fake with 그/드/브.
Fallback route = native reference articulation -> Voice Changer / human-approved fixed asset, not ordinary letter-name TTS.

## 7. Dry-run plan — hard cap
Goal: prove connection, audio quality, pronunciation route, and real credit delta before batch work.

HARD CREDIT CAP: 500 credits for the first technical dry-run.
No batch generation.
No 6-family generation in the first run.

### DR0 — READ ONLY
Record:
- timestamp
- plan/tier if exposed
- credits/usage before if exposed
- custom voice slots used/limit if exposed
- voice operation count if exposed
- current overage/PAYG state if exposed

### DR1 — EXISTING VOICE TTS
Use one existing/default Korean voice.
Generate one short natural Korean test line with Eleven v4.
Purpose:
- confirm MCP TTS path
- confirm returned/downloaded audio
- measure usage delta
- do not create a voice

### DR1.5 — MCP CAPABILITY PROBE
Inspect the connected ElevenLabs Hosted MCP tool list without generating audio.
- If Voice Design is exposed through the current OAuth connection, continue to DR2.
- If Voice Design is NOT exposed, STOP Voice Design work and report the missing capability.
- Do not create/copy/extract an API key automatically.
- TTS over Hosted MCP may still continue independently.

### DR2 — HANGUL_TEACHER_F VOICE DESIGN (CONDITIONAL)
Run exactly ONE Voice Design call only when DR1.5 proves the connected route exposes Voice Design.
Model: eleven_ttv_v3 unless the connected tool exposes a newer supported Voice Design model.
Preview text length: 100-160 chars.
Expected: three previews from one generation.
Do not save all three.
Do not create three voice slots.

Teacher design direction:
Native standard Korean female educator; warm daycare-teacher + broadcast diction;
clear and restrained; medium-slow; precise articulation; no baby-talk;
no exaggerated praise; calm repetition-friendly delivery.

Preview script:
"잘 들어봐. 소리는 짧고 또렷하게 들려줄게. 가, 나, 다, 마. 이번에는 천천히 이어서 들어보자. 가방의 가, 나무의 나, 다리의 다, 마음의 마. 헷갈려도 괜찮아. 다시 눌러서 소리를 듣고, 네가 들은 소리를 따라 해보면 돼."

Return all 3 preview files/links as CANDIDATE_A/B/C.
Do not LOCK.

### DR3 — USAGE AFTER
Read usage again.
Receipt:
credits_before
credits_after
actual_delta
operations_delta
voice_slots_delta
generation_count
input_character_count
model
audio duration
latency
errors/retries

STOP if:
- total actual delta > 500
- unexpected overage/PAYG charge path appears
- MCP tool reports permission mismatch
- generation retries begin looping

## 8. Second dry-run after Teacher candidate chosen
Only after human listening chooses one Teacher candidate:
- save exactly one voice
- test Eleven v4 natural Korean
- test vowels
- test syllables
- test isolated IPA phoneme candidates

Critical pilot set:
vowels: /a/ /ʌ/ /o/ /u/ /ɯ/ /i/
easy continuants/sonorants: /n/ /m/ /s/ /h/
critical stops: Korean ㄱ / ㄷ / ㅂ class
special: onset ㅇ = silence, coda ㅇ = /ŋ/ only when coda pack opens

Do not promote IPA notation itself as child-facing UI.
IPA is production/QA metadata.

## 9. Usage reasoning
Current legacy Hangul generator:
- 175 female clips + 175 male clips = 350 files
- measured source text total = 622 text characters
The issue is not mainly raw text credits; it is duplicate assets, QA workload, voice operations, and future maintenance.

Revised structure removes duplicated male learning assets.
Teacher learning pack is single-authority.
Coach is a much smaller game/system pack.

Official ElevenLabs behavior to validate with the actual account:
- Voice Design returns 3 previews for one generation and charges preview text once.
- Creator normally has 30 custom voice slots and 95 voice operations/month.
- TTS credit cost depends on model/API route.
Always trust account before/after delta over estimates.

## 10. Production model choice
- Voice Design: use supported Text-to-Voice model; first candidate test with eleven_ttv_v3.
- Fixed final character/teacher assets: test eleven_v4 first for quality.
- Real-time runtime is NOT needed for fixed learning clips.
- Flash/low-latency models are not the default for LOCKED production assets.
- Pronunciation dictionaries / inline IPA are production controls; each critical Korean sound still requires listening QA.

## 11. Current gates
G0 Voice architecture: PASS
G1 Claude Code <-> ElevenLabs MCP + OAuth: PASS
G2 Runtime dialogue scope audit: PASS
G3 Hangul legacy-cue conflict audit: PASS / CODE CORRECTION OPEN
G4 First <=500-credit technical dry-run: PASS — 1 generation, 0 retries, 15.9984 reported credits, 6.50s MP3; no Voice Design / no batch
G5 Teacher human listening / voice selection: WAIT
G6 Core Korean phoneme pilot: WAIT
G7 Explorer Crew script gate: E5/E6 CANDIDATE IMPLEMENTED + REGRESSION PASS / SCRIPT_LOCK WAIT; all other grade bands FAIL-CLOSED
G8 Crew / learning batch production: HOLD

No deploy / push / merge.
