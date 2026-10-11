# TAKY EXPLORER CREW DIALOGUE SCRIPT AUDIT — 2026-10-08

Status: REVIEW IN PROGRESS / ELEVENLABS CREW BULK PRODUCTION HOLD
Scope: Explorer Crew dialogue only. Approved signatures remain authority; ASK/HINT/ACK candidates are not locked.
Rule: characterful != childish. Grade-appropriate != baby-talk. Wit/sense is a permanent dialogue quality axis, not an optional joke layer.

## 1. Immediate verdict

Current 24-character matrix is a useful personality scaffold, but is NOT SCRIPT_LOCK quality yet.

Why:
1. Current ASK/HINT/ACK are single static lines and do not adapt to learner grade/stage.
2. Canonical Relation/Affinity and Shared Memory engines exist, but current canonical dialogue callback ignores relation state and ignores the memory cue passed by runtime-v1.
3. Current dialogue-personality-v1 groups characters into generic style families; the manually authored matrix improves this, but repeated sentence frames remain.
4. Wit/sense is inconsistent. Several lines are competent guidance but sound like generic educational assistant copy.
5. Some CARE/CALM lines skew too young because they repeatedly use “천천히 / 괜찮아 / 하나만 / 같이 보자”.
6. OBSERVE characters INK/MOCA/LUMI and LEADER/SOLVE characters TAKE/KIRO/RIN/ZEKE need sharper differentiation.
7. A single line per intent will become repetitive even with different voices.

Therefore:
APPROVED_SIGNATURE = preserve.
ASK/HINT/ACK = REVIEW/REWRITE before any 24-character production.
No Crew ElevenLabs batch generation until SCRIPT_LOCK.

## 2. Canonical runtime findings

Verified runtime order:
CONTEXT -> ENCOUNTER -> RELATION -> MEMORY -> CREW -> BEHAVIOR -> ARBITRATION -> DIALOGUE -> SCENE -> ASSET -> RENDER -> INTERACTION -> STATE_UPDATE.

Verified canonical capabilities:
- Relation states: UNSEEN / FIRST_ENCOUNTER / KNOWN / AFFINITY_BUILDING / COMPANION_AVAILABLE / COMPANION / MAIN_COMPANION.
- Meaningful affinity events include REENCOUNTERED, SHARED_ACTIVITY, HELP_REQUEST_COMPLETED, STORY_EVENT_SHARED, CHAPTER_SHARED, SPECIAL_EVENT_SHARED.
- Shared Memory types include FUNNY_MOMENT, DISCOVERY, PROMISE_OR_PLAN, RETURN_AFTER_ABSENCE, MEANINGFUL_SUCCESS, APP_CROSSOVER_EVENT.
- recallCandidates() can provide a prior memory cue to runtime.
- runtime-v1 calls dialogue(ctx, arbitrated, memoryCue).

Critical gap:
canonical-runtime-v1’s default dialogue implementation accepts only (context, action) and discards memoryCue.
It also does not pass relation_state/affinity or learner grade/stage into dialogue-personality-v1.
There is no grade/learner-stage field in the current Explorer Crew vendor dialogue path.

Conclusion:
The system has relationship/memory engines, but the current spoken line selection does not yet capitalize on them.

## 3. Required dialogue context before SCRIPT_LOCK

Do NOT invent a second learner-grade authority.
TAKY Learning already exposes learner context with school_stage (verified example: learner_context.school_stage = E5).
Explorer Crew dialogue should consume that existing Learning projection and derive only a script-selection band when necessary.

Dialogue resolution must be able to consider:
- character_id
- intent
- role: MAIN / GUEST / CHAPTER_OWNER / ACTING_CREW / AMBIENT
- app_id / scene_id
- learner_context.school_stage from Learning Engine
- subject/domain when relevant
- cognitive_mode: observe / infer / compare / plan / create / recall / explain
- child_response_state
- help_request_state
- relation_state
- affinity band
- memoryCue when callback_allowed
- recent dialogue intents / recent line keys
- interaction_mode and SILENT
- reaction budget / cooldown result

Suggested learner bands for script authority:
- FOUNDATION
- E1_2
- E3_4
- E5_6
- MIDDLE

Do not pre-generate every band for every character now.
Define all bands in script authority, but produce only currently needed bands/runtime consumers.

## 4. Wit / sense hard rule

“위트와 센스” is not “tell a joke every line.”

Every spoken Crew line should carry at least one character spark:
- a character-specific observation,
- a concise metaphor,
- timing/understatement,
- playful reframing,
- prop/role flavored phrasing,
- a callback to an actual shared memory,
- or a clever question that returns initiative to the learner.

Forbidden:
- generic praise dressed up with exclamation marks,
- baby-talk,
- forced jokes,
- jokes that obscure learning,
- identical joke rhythm across characters,
- fake memories or callbacks not present in Shared Memory.

High-affinity wit should become more relational:
KNOWN -> personality only.
AFFINITY_BUILDING -> mild familiar phrasing.
COMPANION -> shared-event callback allowed.
MAIN_COMPANION -> callback + established running motif allowed when memory evidence exists.

## 5. 24-character first-pass disposition

Legend:
A = strong personality base; refine, not rebuild.
B = usable concept but generic/repetitive; rewrite before production.
C = currently too generic/young/overlapping; substantial rewrite.

01 DUBI — A-
- Strength: action-first curiosity is clear.
- Risk: “한 군데만 더 봐봐” is generic.
- Wit source: impulsive discovery / clue unexpectedly “showing itself”.
- Rewrite HINT/ACK by grade band.

02 LORI — C
- Current wording leans too often on “천천히 / 괜찮아 / 같이”.
- Empathy must remain perceptive, not preschool-soothing.
- Wit source: noticing what the learner did not say, gentle perceptive turn.
- Rewrite ASK/HINT/ACK.

03 INK — A
- Strong observe-first identity.
- “기록해두자” is usable but MOCA/LUMI overlap.
- Wit source: dry observation; tiny details “talking too much”.
- Refine HINT/ACK.

04 NOVA — B
- Action energy is present, but lines could belong to many action characters.
- Wit source: challenge/experiment banter, “let’s poke the system and see what moves”.
- Rewrite all three lightly.

05 TAKE — B
- Structure/sequence identity is clear.
- Current lines feel teacher-like.
- Wit source: understated organization humor; turning mess into an orderly queue.
- Rewrite ASK/HINT/ACK with older-grade naturalness.

06 ZERO — A
- Music/rhythm identity is distinct.
- Avoid therapeutic “네 속도로” repetition.
- Wit source: rhythm, beat, pause, tempo metaphors.
- Refine ACK and provide grade variants.

07 SOLA — A-
- Light/nature discovery language fits.
- Risk: overly poetic/vague during academic tasks.
- Wit source: small signals behaving like hidden trail markers.
- Keep concept, sharpen task specificity.

08 BELO — B
- Map/exploration frame is good.
- Current ASK/HINT/ACK are functional but predictable.
- Wit source: route choice, detour, map refusing to give away the answer.
- Rewrite with more character spark.

09 MOCA — B
- Research/record identity exists.
- Overlaps INK/LUMI heavily.
- Wit source: evidence, field-note skepticism, “one observation is not a conclusion”.
- Rewrite to researcher rather than generic observer.

10 NIA — B
- Connection identity exists but language is abstract.
- Wit source: link/network/relay perspective and social awareness.
- Rewrite with concrete connections and grade-aware abstraction.

11 KIRO — A-
- Structure/maker/problem-solving identity is strong.
- Risk: generic “one piece at a time”.
- Wit source: engineering understatement, fit/load/structure metaphors.
- Refine, especially E5_6/MIDDLE.

12 PEACH — C
- Too easily falls into soft reassurance.
- Must not become “healing mascot”.
- Wit source: easing tension with a smart reframing, not babying.
- Rewrite all three.

13 MINT — C
- Current “천천히” identity is overused and can feel infantilizing.
- Calmness should be confidence, not slowness.
- Wit source: dry calm, unbothered route judgment, low-reactivity humor.
- Substantial rewrite.

14 TOTO — A
- Mischievous experimentation is already visible.
- Must avoid random clowning.
- Wit source: controlled mischief, reverse-test, playful hypothesis.
- Refine by grade band.

15 RUNE — A-
- Adaptation/change identity is clear.
- Wit source: changing method like changing color/angle, without species caricature.
- Refine to avoid repetitive “one thing change”.

16 POPO — B
- Team/companion identity exists, but generic togetherness.
- Wit source: coordination, relay, “two pieces behaving better together”.
- Rewrite.

17 MARU — A
- Hidden-clue/persistence identity is distinct.
- Wit source: quiet deadpan about clues hiding badly.
- Strong candidate for SCRIPT_LOCK after grade pass.

18 BORI — B
- Memory identity is useful and directly compatible with Shared Memory.
- Current line does not exploit real callback evidence.
- Wit source: callback to actual prior event; memory noticing patterns.
- Rewrite around evidence-backed memory.

19 RIN — B
- Leader/navigation identity is clear but generic.
- Wit source: decisive route judgment, concise tactical navigation.
- Rewrite to avoid “leader = command voice”.

20 LUMI — B
- Analytic + sensitive potential is good.
- Currently overlaps INK/MOCA.
- Wit source: contrast, before/after, subtle pattern with a reflective twist.
- Rewrite.

21 TESS — C+
- Energy/game identity is present but “mission” copy is generic.
- Wit source: game-state banter, team tempo, challenge framing.
- Rewrite all three; no cheerleader cliché.

22 SEL — C
- Empathy/healing language overlaps LORI/PEACH.
- Wit source: sensing change, living-system metaphor, calm social intelligence.
- Rewrite with sharper identity.

23 ZEKE — A
- Strategy/conditions/method comparison is the strongest non-Core6 candidate.
- Wit source: dry strategic line, constraint spotting, “which condition is pretending to be important?”
- Refine, preserve concise intelligence.

24 VIVI — B
- Creativity/social connection is clear but current lines are generic.
- Wit source: remix, framing, camera/memory composition, playful creative edit.
- Rewrite.

First-pass count:
A/A-: 9
B: 9
C/C+: 6
No ASK/HINT/ACK row is SCRIPT_LOCK yet because grade/relation/memory axes are absent.

## 6. Cross-character collision findings

High collision phrases/concepts:
- “하나만 / 하나부터 / 하나 골라”
- “천천히”
- “찾아봐 / 살펴봐”
- “다음으로 / 다음 걸”
- “같이 / 함께”
- “기록해두자”
- generic “됐네 / 보였네 / 찾았네”

These are not forbidden words, but current density makes characters converge.

Collision clusters requiring explicit separation:
- INK vs MOCA vs LUMI
  - INK = clue interpretation / dry observation
  - MOCA = evidence collection / research rigor
  - LUMI = contrast + analysis + emotional texture
- LORI vs PEACH vs SEL
  - LORI = empathic listening / perspective
  - PEACH = mood regulation / harmony / light reframing
  - SEL = social/living-system sensitivity / relational sensing
- TAKE vs KIRO vs RIN vs ZEKE
  - TAKE = order / sequence / steadiness
  - KIRO = build / structure / practical repair
  - RIN = route / direction / leadership
  - ZEKE = condition / strategy / optimization
- DUBI vs NOVA vs TOTO vs TESS
  - DUBI = curiosity burst / first discovery
  - NOVA = challenge / forward motion
  - TOTO = playful experiment / inversion
  - TESS = game/team tempo / mission framing

## 7. Grade adaptation examples — same character, same personality

ZEKE HINT:
FOUNDATION: “바꿀 수 있는 건 뭐가 있을까? 하나만 골라보자.”
E3_4: “조건 하나만 바꿔보자. 뭐가 달라지는지 보자.”
E5_6: “조건이 여러 개면 하나씩 분리해야 보여. 먼저 바꿀 수 있는 조건부터 잡아보자.”
MIDDLE: “변수를 한꺼번에 건드리면 원인을 못 잡아. 하나만 바꾸고 결과를 비교해보자.”

INK HINT:
FOUNDATION: “작은 차이 하나가 숨어 있네. 어디일까?”
E3_4: “둘이 비슷해 보여도 작은 차이가 있어. 모양부터 비교해볼까?”
E5_6: “거의 같아 보이는 쪽이 오히려 단서를 숨기기 좋아. 차이가 나는 지점만 좁혀보자.”
MIDDLE: “전체보다 차이를 먼저 보자. 예외 하나가 구조를 설명할 때가 있어.”

The character remains the same; vocabulary, reasoning depth and compression change.

## 8. Relationship/memory callback examples

No fake callback. A fixed clip may refer to the verified event type, but must not invent how the earlier event happened unless that exact fact is encoded in a dedicated approved callback asset.

BORI, with actual prior DISCOVERY memory:
“지난번 발견 기억나? 이번 단서도 기억 속 패턴과 닮았는지 볼까?”

TOTO, with actual FUNNY_MOMENT memory:
“지난번 웃긴 순간 기억나? 이번 문제도 한번 당황시켜볼까?”

ZEKE, with actual PROMISE_OR_PLAN memory:
“아까 세운 계획 기억나? 이번엔 조건부터 확인해보자.”

These callbacks are selectable only when memoryCue.callback_allowed=true and relation state is COMPANION or MAIN_COMPANION.
Unsupported learner bands remain fail-closed before memory callback selection.

## 9. Production gate correction

Before ElevenLabs Crew production:
1. SCRIPT_AUTHORITY_SCHEMA updated with grade band / relation band / wit tag / memory callback policy.
2. dialogue resolver consumes grade + relation + memoryCue.
3. each currently used intent has at least a small anti-repeat line bank or deterministic variation key.
4. name-blind character distinctiveness review.
5. cross-character collision review.
6. grade appropriateness review.
7. Teacher/Coach/Maker authority collision review.
8. runtime budget/cooldown/SILENT regression.
9. only then SCRIPT_LOCK -> ElevenLabs bounded production.

The successful ElevenLabs technical TTS probe does not change this gate.

## 10. Implemented candidate evidence — E5/E6

Implemented locally in Snap Explorer Crew candidate runtime:
- new dialogue-script-authority-v1.js
- E5/E6: 24 characters × ASK/HINT/ACK × 2 variants = 144 candidate lines
- 144/144 unique lines
- all 24 characters have >=2 wit tags
- all 24 have evidence-gated DISCOVERY memory callback
- relation state changes default variant selection
- recent_line_keys prevents immediate repeat
- learner_context.school_stage is consumed from existing Learning authority; no duplicate grade authority introduced
- unsupported E1-4 / MIDDLE / FOUNDATION bands fail closed
- Core6 sourced thinking/learning scene lines also pass the grade gate; approved GREET/RECONNECT signatures remain identity lines
- canonical cycle verified: E5 -> relation/affinity -> recalled Shared Memory -> dialogue callback
- four high-risk collision clusters automatically constrained below 0.20 token-set similarity; observed maximum after rewrite = 0.167
- generic ACK opening '좋아' reduced from 16 occurrences to effectively zero as a stock response
- no baby-talk / ability-praise patterns in the 144 candidate lines
- source lock: EXPLORER_CREW_V2_SOURCE_LOCK_20261008_DIALOGUE_CANDIDATE, 35 files
- all current snap-crew *.test.js PASS; git diff --check PASS

## 11. Current production verdict

Teacher technical probe: PASS as connectivity proof only; actual reported cost 15.9984 credits, one generation, zero retries.
E5/E6 Crew script/runtime: CANDIDATE IMPLEMENTED + REGRESSION PASS, NOT SCRIPT_LOCKED.
Other learner bands: HOLD / FAIL-CLOSED.
Crew ElevenLabs ASK/HINT/ACK production: HOLD.
Old 126-clip production instruction: REVOKED.

Next quality gate before SCRIPT_LOCK:
1. human/content review of the E5/E6 candidate voice script,
2. then bounded grade-band expansion without changing character identity,
3. only SCRIPT_LOCKED currently-consumed assets may enter ElevenLabs production.

END OF AUDIT.
