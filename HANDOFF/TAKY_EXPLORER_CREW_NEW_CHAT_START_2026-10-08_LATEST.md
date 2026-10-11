# TAKY EXPLORER CREW — NEW CHAT START / LATEST
Date: 2026-10-08
Status: RESTART READY / SEPARATE SHARED AUTHORITY

## 0. Scope
이 문서는 Play Camp 전용이 아니다.
Ready / Hide / Snap / Play Camp가 공유하는 탐험대원(Explorer Crew) 공통 권위 재개문서다.
Play Camp 음성/Teacher/Coach/Maker production gate와 분리한다.

## 1. Canonical Visual ID 24
01 DUBI 두비
02 LORI 로리
03 INK 잉크
04 NOVA 노바
05 TAKE 테이크
06 ZERO 제로
07 SOLA 솔라
08 BELO 벨로
09 MOCA 모카
10 NIA 니아
11 KIRO 키로
12 PEACH 피치
13 MINT 민트
14 TOTO 토토
15 RUNE 루네
16 POPO 포포
17 MARU 마루
18 BORI 보리
19 RIN 린
20 LUMI 루미
21 TESS 테스
22 SEL 셀
23 ZEKE 제이크
24 VIVI 비비

01~06 Core6 보존.
19~24 사람형 = Special Crew.
Approved Visual ID source가 유일한 identity authority다.
Play Camp 때문에 base identity를 재생성/재해석하지 않는다.

## 2. Hard rules
- 캐릭터 별 1~5성 구조 금지. 별은 배지 전용.
- 첫 만남은 Core6 중심.
- 07~24는 이후 등장/해금/동행 선택.
- 동행 판단 = Relation / Affinity.
- Presence / Interaction 분리.
- Shared Memory / Episode는 실제 사건 증거가 있을 때만 callback.
- 가짜 추억/가짜 관계 진전 금지.
- Crew는 companion / observer / idea partner.
- Teacher / Coach / Maker의 발음·교수·미션 권위 침범 금지.
- 영어 phonics/정확 발음 권위는 Teacher EN.
- USER != DEBUGGER.
- 동일 실패 반복 금지.

## 3. Runtime authority
Canonical Logic
↔ Character Behavior Engine
↔ Relation & Affinity Engine
↔ Shared Memory & Episode Engine
↔ Crew Orchestration / Arbitration
↔ Encounter & Crew Selection
↔ Asset Engine
↔ UI Renderer

Semantic Action Command를 통해 소비한다.
Presence와 실제 Interaction을 분리한다.
Ambient 대표행동:
READ_BOOK / READ_MAP / NOTE / COMPASS / BAG / MAGNIFIER / RADIO / REST.

## 4. Relationship states
UNSEEN
FIRST_ENCOUNTER
KNOWN
AFFINITY_BUILDING
COMPANION_AVAILABLE
COMPANION
MAIN_COMPANION

Meaningful affinity / episode evidence 예:
REENCOUNTERED
SHARED_ACTIVITY
HELP_REQUEST_COMPLETED
STORY_EVENT_SHARED
CHAPTER_SHARED
SPECIAL_EVENT_SHARED

Shared Memory types 예:
FUNNY_MOMENT
DISCOVERY
PROMISE_OR_PLAN
RETURN_AFTER_ABSENCE
MEANINGFUL_SUCCESS
APP_CROSSOVER_EVENT

callback은 실제 evidence가 있을 때만 허용한다.

## 5. Character personality authority
01 DUBI — curiosity / energy
02 LORI — warm empathy
03 INK — observation / clue interpretation
04 NOVA — challenge / forward motion
05 TAKE — order / sequence / steadiness
06 ZERO — music / calm
07 SOLA — discovery
08 BELO — explorer
09 MOCA — research / evidence
10 NIA — connection
11 KIRO — making / practical problem solving
12 PEACH — healing / harmony
13 MINT — calm guide
14 TOTO — playful experiment
15 RUNE — adaptation
16 POPO — cooperation
17 MARU — focus / explore
18 BORI — memory
19 RIN — leadership / route
20 LUMI — contrast / analysis / emotional texture
21 TESS — game / team tempo
22 SEL — empathy / living-system sensitivity
23 ZEKE — strategy / condition / optimization
24 VIVI — bond / creativity

High-collision distinction:
- INK vs MOCA vs LUMI:
  INK clue interpretation / dry observation
  MOCA evidence collection / research rigor
  LUMI contrast + analysis + emotional texture
- LORI vs PEACH vs SEL:
  LORI empathic listening / perspective
  PEACH mood regulation / harmony
  SEL social/living-system sensitivity
- TAKE vs KIRO vs RIN vs ZEKE:
  TAKE order/sequence
  KIRO build/structure
  RIN route/direction
  ZEKE strategy/conditions
- DUBI vs NOVA vs TOTO vs TESS:
  DUBI curiosity burst
  NOVA challenge
  TOTO playful experiment
  TESS game/team mission tempo

## 6. Dialogue quality
언제 어느 때라도 캐릭터 고유의 위트와 센스를 유지한다.
위트 = 매 줄 농담이 아니다.
허용 방향:
- 캐릭터 고유 관찰
- 비유
- 타이밍/절제
- 재치 있는 재프레이밍
- 역할/소품 기반 표현
- 실제 Shared Memory callback
- 아이에게 주도권을 돌려주는 똑똑한 질문

금지:
- 반복적인 유아화: “괜찮아~ 잘했어~ 같이 해보자~”
- 능력 칭찬 남발
- 캐릭터끼리 말투가 서로 같아지는 generic copy
- 실제 증거 없는 과거 사건 세부 묘사

성격은 고정한다.
어휘 / 문장 길이 / 질문 깊이 / 인지 요구량 / 힌트 강도만 앱·레지스터에 맞춘다.

## 7. Current dialogue registers
사용자 최신 기준:
- PLAY_CAMP
- MAIN_CREW = 현재 초등 고학년 중심
- MIDDLE = 나중 확장팩

중등은 지금 전량 생산하지 않는다.
공용 가능한 인사/재회/발견/관계/기억 asset은 최대한 재사용한다.

기존 5단계 FOUNDATION/E1_2/E3_4/E5_6/MIDDLE 구상은
현재 production grouping authority가 아니다.
현재 생산 관점은 PLAY_CAMP / MAIN_CREW, 중등은 EXPANSION_MIDDLE 후순위다.

## 8. Current Main Crew dialogue implementation evidence
Repo:
D:\Git PWA\BETA_BRANCH_REVIEW_20261003\snap-crew

Observed authority baseline before latest handoff:
- E5/E6 candidate
- 24 characters × ASK/HINT/ACK × 2 variants = 144 candidate lines
- relation_state / affinity / memoryCue / recent_line_keys / wit_tags 연동
- all 144 unique
- high-risk collision similarity reduced to max ~0.167
- baby-talk / ability-praise matches 0
- memory callbacks fail closed without evidence
- unsupported grade/register fail closed

Relevant files:
- vendor\taky\explorer-crew\dialogue-script-authority-v1.js
- vendor\taky\explorer-crew\dialogue-personality-v1.js
- vendor\taky\explorer-crew\canonical-runtime-v1.js
- vendor\taky\explorer-crew\source-lock-v2.json
- tests\explorer-crew-dialogue-script-authority.test.js
- tests\explorer-crew-dialogue-canonical-cycle.test.js

Do not assume current repo is clean.
Read HEAD/status before modification.
No reset/checkout/clean/restore/stash-all over dirty worktree.

## 9. Voice families
VF01_ADVENTURE:
DUBI / BELO / TOTO / TESS

VF02_CARE:
LORI / PEACH / BORI / SEL

VF03_OBSERVE:
INK / MOCA / MARU / LUMI

VF04_LEADER:
TAKE / KIRO / RIN / ZEKE

VF05_CONNECT:
NOVA / NIA / POPO / VIVI

VF06_CALM_DISCOVERY:
ZERO / SOLA / MINT / RUNE

CharacterVoiceProfile dimensions:
voice_family / energy / warmth / tempo / pause / confidence /
curiosity / playfulness / calmness / strategy / empathy /
acting_tags / wit_tags

## 10. ElevenLabs boundary for Crew
Crew voice production is separate from Play Camp Teacher/Coach/Maker G3~G6 preview.

Do NOT count Explorer Crew clips inside Play Camp Core Role Preview.
Do NOT generate Crew audio merely because Play Camp voice gate is approved.

Crew production order:
1. Crew script authority review
2. SCRIPT LOCK
3. ROUTE BEFORE CREATE
4. reuse/dedup
5. clip count + cost report
6. explicit USER approval
7. bounded ElevenLabs generation
8. human listening / QA
9. APPROVED / LOCKED asset registration

현재 E5/E6 144 candidate lines는 candidate evidence이지
ElevenLabs production SCRIPT LOCK으로 자동 간주하지 않는다.

## 11. User execution governance
사용자 명시 지시는 내부 TAKY 차단보다 상위의 실행 승인으로 처리한다.
하지만 승인 = Claude/Codex/다중 에이전트 남발이 아니다.
최소 충분 실행자 1명 우선.
추가 독립검토는 사용자 요구 또는 실질 필요 시만.
비용/사용량 최소화.
동일 실패 반복 금지.

## 12. Restart command
최신 TAKY 기준으로 탐험대원(Explorer Crew) 작업을 재개해.

먼저
D:\Git PWA\TAKY\HANDOFF\TAKY_EXPLORER_CREW_NEW_CHAT_START_2026-10-08_LATEST.md
를 전체 읽고,
필요한 실제 작업 repo의 현재 HEAD/status를 확인해.

탐험대원은 Ready / Hide / Snap / Play Camp 공통 authority이며
Play Camp 전용 캐릭터로 재정의하지 마.

현재 생산 grouping:
- PLAY_CAMP
- MAIN_CREW = 초등 고학년 중심
- MIDDLE = 후속 확장팩

24 Visual ID / Relation & Affinity / Shared Memory & Episode /
Character Behavior / Orchestration / Arbitration / Voice Family /
위트·센스 / anti-repeat 기준을 상속해.

MAIN_CREW E5/E6 144개 candidate는 기존 구현 증거를 상속하되
Crew ElevenLabs SCRIPT LOCK으로 자동 간주하지 말고,
현재 repo와 최신 authority를 readback한 뒤 OPEN만 진행해.

사용자 명시 지시는 내부 차단보다 상위 승인으로 처리하되
다중 호출 남발 금지 / 최소 충분 경로 우선.
paid generation / push / merge / deploy는 명시 승인 전 금지.

## 2026-10-08 CURRENT VOICE PRE-LOCK UPDATE

Read first:
D:\Git PWA\TAKY\HANDOFF\TAKY_EXPLORER_CREW_VOICE_CURRENT_2026-10-08.md

Current dialogue source lock:
EXPLORER_CREW_V2_SOURCE_LOCK_20261008_DIALOGUE_CANDIDATE_R9

MAIN_CREW:
- E5/E6
- 24 × ASK/HINT/ACK × 2 = 144 lines
- 5,022 chars
- Codex first review HOLD -> 30 line-local remediations completed
- full Crew regression 6/6 PASS
- remediation micro recheck execution OUTCOME_UNKNOWN
- status = LOCK_CANDIDATE_WITH_INDEPENDENT_RECHECK_DEBT
- NOT final SCRIPT LOCK

Production group alignment:
- PLAY_CAMP
- MAIN_CREW
- MIDDLE
Only MAIN_CREW currently runtime-enabled for ASK/HINT/ACK.
PLAY_CAMP / MIDDLE fail closed as PRODUCTION_GROUP_NOT_LOCKED.

PLAY_CAMP Core6:
- common candidate bank only
- 6 × 3 intents × 2 variants = 36 lines
- 994 chars
- 36/36 unique
- NOT SCRIPT_LOCKED
- NOT runtime-enabled
- NOT ElevenLabs production scope yet
- presentationBand consumer contract PASS:
  EARLY_EXPLORER / LOWER_PRIMARY → PLAY_CAMP
  UPPER_PRIMARY → MAIN_CREW
  SECONDARY → MIDDLE
- Play Camp browser smoke verifies production_group=PLAY_CAMP without inventing school_stage.
TAKY content review = PASS_WITH_FIXES (6 abstract phrases simplified). Remaining blocker = independent targeted recheck + SCRIPT LOCK.

Do not merge Play Camp 49 core-role SCRIPT LOCK with Crew dialogue authority.
No paid Crew generation before the relevant Crew SCRIPT LOCK and USER approval.

## 2026-10-08 R9 FINAL LOCAL UPDATE

Current source lock:
EXPLORER_CREW_V2_SOURCE_LOCK_20261008_DIALOGUE_CANDIDATE_R9

R9 adds:
- presentationBand → production-group contract
- PLAY_CAMP context E2E PASS
- Core6 Play Camp common bank TAKY content review PASS_WITH_FIXES
- sourced Core6 scene-line fail-closed gate so PLAY_CAMP cannot consume MAIN scene lines
- full Crew suite 6/6 PASS

Current source truth:
- MAIN_CREW 144 lines / 5,022 chars
- MAIN Core6 first wave 36 / 1,222 chars
- MAIN later18 108 / 3,800 chars
- PLAY_CAMP Core6 common bank 36 / 994 chars
- signatures 24 / 411 chars
- memory callbacks 30 / 1,001 chars
- Core6 MAIN scene lines 30 / 677 chars

Independent recheck:
- receipt: pf:explorer-crew-r9-final-targeted-recheck-r2-20261008:b055a92ef94f4a21
- actual_calls=1
- returncode=1
- stdout/stderr empty
- status=OUTCOME_UNKNOWN
- DO NOT RETRY BLINDLY
- evidence: D:\Git PWA\TAKY\HANDOFF\TAKY_EXPLORER_CREW_R9_INDEPENDENT_RECHECK_RECEIPT_2026-10-08.md

Voice production master:
D:\Git PWA\TAKY\HANDOFF\TAKY_VOICE_PRODUCTION_MASTER_2026-10-08.md

No paid ElevenLabs generation.
No push / merge / deploy.
MAIN_CREW = LOCK_CANDIDATE_WITH_INDEPENDENT_RECHECK_DEBT.
PLAY_CAMP Core6 = TAKY_CONTENT_REVIEW_PASS_WITH_FIXES / INDEPENDENT_RECHECK_PENDING / NOT SCRIPT_LOCKED.
