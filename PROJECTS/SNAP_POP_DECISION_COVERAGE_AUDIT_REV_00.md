# SNAP & POP — DECISION COVERAGE / REVERSE-VALIDATION AUDIT

Status: REV_00 / RECOVERY AUDIT / NOT RELEASED
Date: 2026-09-05
Authority: TAKY GRAND MASTER + latest explicit user decisions
Purpose: prevent HANDOFF-summary loss and prove whether recovered decisions are reflected, intentionally held, rejected, conflicted, or superseded.

## 1. Evidence Scope

Reviewed/recovered evidence includes:
- current canonical `MASTER/MASTER_LOGIC.md`
- Snap & Pop MASTER lineage recovered from REV_02~REV_10 materials, with REV_06 detailed consolidation inspected
- `Snap_Pop_V12_복구_비교표_및_명세.md`
- `Snap_and_Pop_V12_Handover.docx`
- `Snap_Pop_V13_프로젝트_인수인계_2026-09-04.md`
- `Snap_Pop_인수인계_2026-09-04.md`
- `SNAP_POP_WORK_HANDOFF_2026-09-04.md` variants
- `PWA_DEPLOY_HANDOFF_MASTER_2026-09-05.docx`
- `PWA_DEPLOY_COMMAND_HANDOFF_2026-09-05.txt`
- `Snap_Pop_UI_MASTER_LOGIC_REV_10_TAKY_REMASTER_CANDIDATE.md`
- `Snap_Pop_TAKY_REMASTER_DELTA_REPORT_20260905.md`
- latest current-conversation corrections and workflow decisions.

Important evidence boundary:
- HANDOFF is an index/recovery aid, not proof of full conversation coverage.
- Exact raw text of every historical chat turn from the very first conversation was not independently retrievable in this run.
- Therefore `FULL_RAW_CONVERSATION_EXACT_COVERAGE = UNVERIFIED`, and a zero-omission claim is prohibited.
- Recoverable decisions found in MASTER lineage, source documents, handoffs and current conversation are nevertheless traced below. If a raw historical source later becomes available, it must be reverse-compared against this matrix.

## 2. Reverse-Validation Rule

For every material source item:

`SOURCE -> DECISION -> LATEST CORRECTION -> CLASSIFICATION -> DESTINATION / HOLD REASON -> IMPLEMENTATION / TEST -> RESULT EVIDENCE`

A source item is not considered covered merely because it was read.

Allowed classifications:
- PRESERVE
- ADOPT
- ADJUST
- HOLD
- REJECT
- CONFLICT
- SUPERSEDED

Additional audit failures:
- MISSING: source decision has no destination/disposition
- HANDOFF_LOSS: decision exists in recovered source but is absent from a handoff that claimed continuity
- WRONG_REFLECTION: result contradicts the active decision
- UNJUSTIFIED_HOLD: hold has no reason/exit condition
- UNJUSTIFIED_REJECT: reject has no evidence/rationale

## 3. Core Product Coverage

| ID | Decision / detail | Current disposition | Required destination / validation |
|---|---|---|---|
| SP-001 | ORIGINAL Core is the base product | PRESERVE | Project MASTER + feature flags + regression tests |
| SP-002 | FAMILY EXPANSION is additive, not a replacement/default home | PRESERVE | Project MASTER; ORIGINAL start screen remains exploration map |
| SP-003 | `ORIGINAL_CORE=true`, default `FAMILY_EXPANSION=false` | PRESERVE | runtime feature flags |
| SP-004 | five writing tools always freely usable; no map/chapter/level unlock | PRESERVE | UI + state + regression |
| SP-005 | landmarks: 아이디어 동굴 / 감정 호수 / 묘사 숲 / 관점 전망대 / 마무리 캠프 | PRESERVE | project terminology contract |
| SP-006 | 3-step writing: 생각 꺼내기 -> 생각 넓히기 -> 표현 완성하기 | PRESERVE | interaction + state machine |
| SP-007 | child remains final editor; guide does not replace child's writing | PRESERVE | function prompt/interaction tests |
| SP-008 | completion reward occurs once only | PRESERVE | completionEventId / ledger / idempotency test |
| SP-009 | optional extra practice grants region shard +1 and no EXP, protected by bonusEventId | PRESERVE | reward ledger test |
| SP-010 | records/calendar/growth/gem/wish-blessing loop must work without FAMILY | PRESERVE | ORIGINAL full regression |

## 4. Growth / Reward / Memory Coverage

| ID | Decision / detail | Current disposition | Validation |
|---|---|---|---|
| SP-020 | variable EXP + 25 levels are ORIGINAL updates, not FAMILY | PRESERVE | formula/data tests |
| SP-021 | level is growth/record state, not access control | PRESERVE | no-lock regression |
| SP-022 | one persistent Growth Tree; previous stages only in history | PRESERVE | UI/state regression |
| SP-023 | special event completion -> Event Memory -> growth trace/fruit -> calendar bidirectional link | PRESERVE | state/data/navigation test |
| SP-024 | early growth stages need context-appropriate trace, not forced fruit | PRESERVE | UI logic |
| SP-025 | weekend special exploration arrives as mail invitation; nonparticipation has no penalty/streak loss | PRESERVE | event scheduling/state test |
| SP-026 | 6 shards of same region -> one completed gem; remainder retained | PRESERVE | ledger/conversion test |
| SP-027 | `탐험가의 소원 상점` | PRESERVE | terminology/UI/function |
| SP-028 | `소원 사용하기 -> 축복 사용하기` are two distinct stages | PRESERVE | state machine + debit idempotency |
| SP-029 | FAMILY 응원 카드 is distinct from ORIGINAL blessing | PRESERVE | boundary regression |
| SP-030 | historical exact gem visual asset lock | HOLD / RE-REVIEW | latest UI redesign supersedes unconditional visual inheritance; functional gem meaning remains locked |

## 5. Character / Guide / Voice Coverage

| ID | Decision / detail | Current disposition | Validation |
|---|---|---|---|
| SP-040 | photo/upload-derived stable Character Master | PRESERVE | source/processed/generated asset separation |
| SP-041 | reusable face/upper/full-body assets; no independent character regeneration per screen | PRESERVE | identity regression |
| SP-042 | changing Character/Guide must not delete records, EXP, gems, growth, wishes/blessings, FAMILY records | PRESERVE | migration/regression |
| SP-043 | Guide is user-facing 길잡이/탐험 동료/이야기 길잡이, not teacher/grader/system AI | PRESERVE | copy/personality check |
| SP-044 | Guide candidates: Maltipoo / original booted exploration cat / red panda / human companion | PRESERVE as product option; visual design RE-REVIEW | identity + no third-party-IP imitation |
| SP-045 | Guide personality: 친절 + 장난 + 위트 + 약간의 시크함 + 약간의 엉뚱함 | PRESERVE | dialogue regression |
| SP-046 | reaction pattern: 관찰 -> 장난 -> 인정 -> 다음 호기심 | PRESERVE | guide behavior tests |
| SP-047 | overpraise/repeated 최고야·천재야 style discouraged | PRESERVE | copy validation |
| SP-048 | Voice Accessibility supports question listening/relisten while keeping text | PRESERVE | accessibility test |
| SP-049 | right-side walkie-talkie is common voice-input method, not one of five tools | PRESERVE | layout/function test |
| SP-050 | walkie states: idle -> transmitting/listening -> text conversion -> complete | PRESERVE | state test |

## 6. FAMILY EXPANSION Detailed Recovery

The following FAMILY details are explicitly recovered and SHALL NOT be reduced to a generic `family mode` label.

| ID | FAMILY detail | Current disposition | Notes |
|---|---|---|---|
| FAM-001 | family group and invitation | PRESERVE / expansion scope | not exposed in Stage 1 ORIGINAL |
| FAM-002 | parent/child/grandparent etc. relationships and permissions | PRESERVE / expansion scope | permission model must be separately specified before implementation |
| FAM-003 | multiple child profiles and profile switching | PRESERVE | child data must remain isolated |
| FAM-004 | per-child records / exploration / EXP / level / gem shards / completed gems / wish-blessing history | PRESERVE | `childId` ownership |
| FAM-005 | per-child Character Master / physical growth / Event Memory | PRESERVE | no shared-progress array |
| FAM-006 | private diary + lightweight diary writing | PRESERVE / expansion scope | detail UX remains to be re-audited from raw chat if recovered |
| FAM-007 | family notes / letters / pen-pal | PRESERVE / expansion scope | all family members may correspond; exact permission rules need implementation spec |
| FAM-008 | forest-path mailbox concept | PRESERVE as recovered product concept; visual treatment RE-REVIEW | UI art is not locked |
| FAM-009 | cheer cards, separate from blessing | PRESERVE | FAMILY communication object |
| FAM-010 | optional shard gift | PRESERVE as recovered feature; requires transaction/permission validation | do not silently merge with blessing |
| FAM-011 | diary-based composited scene illustration | HOLD for detailed design | concept recovered; generation/composition policy not yet fully fixed |
| FAM-012 | family shared album / family calendar / family cloud | PRESERVE / expansion scope | synchronization/permissions need implementation spec |
| FAM-013 | family shared special exploration | PRESERVE | must not alter ORIGINAL core loop |
| FAM-014 | family growth record | PRESERVE | expansion view, not replacement of personal Growth Tree |
| FAM-015 | FAMILY is entered via settings/optional post-record action; no sixth bottom tab | PRESERVE | navigation regression |
| FAM-016 | FAMILY UI cannot change five landmarks, 5-tab nav, 3-step writing, EXP formula, 25 levels, tree, 6-shard logic, wish/blessing, voice accessibility | PRESERVE | cross-mode regression |

## 7. FAMILY Data Isolation / Migration — HARD RECOVERY

Recovered minimum identity dimensions:
- `familyId`
- `memberId`
- `childId`

Per-child separation includes at minimum:
- writing records
- exploration progress
- EXP / level
- gem shards / completed gems
- wish/blessing history
- Character Master
- physical growth
- Event Memory
- letters / diary

Migration from ORIGINAL single-user data:
1. create read-only backup
2. link existing user data to first child profile
3. move records/EXP/gem/use history without changing values
4. compare before/after counts and totals
5. mismatch -> block FAMILY activation and rollback

Status: PRESERVE. Actual migration execution evidence remains HOLD until implementation test.

## 8. Record / Calendar / Integration Coverage

PRESERVE:
- internal exploration calendar is the primary growth/memory map
- record detail keeps final writing, original answers, region, EXP, skill elements and gem history
- edits preserve original history and never reissue completion reward
- Google Calendar is optional external integration/storage and must not block local record/exploration/gem/growth on failure
- Google Calendar connection belongs in settings/account-integration layer

HOLD until actual test evidence:
- OAuth production origin/configuration
- real Google Calendar integration
- failure/reconnect behavior on deployed PWA

## 9. Camera / Profile Coverage

Recovered behaviors:
- camera/upload flow preserved
- original / warm / vintage / forest-light / explorer filter lineage recovered
- real-photo vs illustration mode should rerender immediately
- browser filter and generative Character transformation are distinct operations
- preview and saved result must match materially
- original profile photo and processed/generated assets remain separated

Status:
- product/function principle: PRESERVE
- exact current filter implementation correctness: HOLD / regression test required

## 10. Offline / State / Error Safety Coverage

PRESERVE:
- explicit Exploration state machine with safe resume
- explicit Wish/Blessing state machine with debit idempotency
- draft/text preservation on interruption
- reward/debit committed-state protection
- distinct error taxonomy: file/photo, image processing, network, auth/external, voice permission, speech recognition, Character generation, image generation, save, migration, external calendar, transaction, PWA cache/version
- error copy must not blame user
- offline-first access to saved writing/records, gem balance, growth records, stored Character/Guide and draft
- online-dependent functions may include new Character generation, generated memory illustration, external calendar sync, server AI/voice
- service-worker/cache version, app revision and data schemaVersion managed together
- silent destructive migration forbidden
- archive and delete are distinct

## 11. UI / Art Reclassification After Latest User Decision

Latest user direction supersedes unconditional inheritance of historical UI visuals.

PRESERVE as product/quality constraints:
- premium/high-density illustration quality
- readability/premium Korean typography requirement
- Safe Area/mobile behavior
- no fake iPhone status chrome
- no runtime Korean text/numbers/buttons baked into artwork
- Character/Guide/data identity principles
- bottom-nav/product hierarchy unless later explicitly changed
- ORIGINAL/FAMILY separation

SUPERSEDED / REDESIGN:
- old mandatory Golden Reference inheritance
- old exact map composition lock
- old exact Character/Guide/Growth Tree visual appearance lock
- old typography/material/color composition lock
- old exact screen layout as immutable visual source

REFERENCE ONLY:
- historical V12 approved UI boards and V13 visual previews, unless an element is explicitly re-approved.

HOLD / RE-REVIEW:
- exact gem visual asset reuse policy
- any exact legacy illustration that may conflict with the new visual redesign scope.

## 12. Mockup / UI Asset / Preview Contract — Latest User Decision

Definitions:
- `DESIGN_MOCKUP` = static design image used to decide visual direction.
- `UI_IMPLEMENTATION` = web reconstruction based on the approved mockup using separately produced assets and live DOM components.
- `UI_PREVIEW` = real mobile-browser executable preview URL.
- `FUNCTION_PREVIEW` = executable preview URL with actual functions connected.
- `PRODUCTION` = existing approved production URL/PWA.

Hard rules:
- approved mockup image is a reference, not a production asset sheet.
- do NOT crop/slice the mockup and use those slices as final PWA assets.
- background/environment/landmarks/Character/Guide/Gem/Tree/decorative elements required by the final UI are produced as separate fit-for-purpose high-density illustration assets.
- text, buttons, navigation, progress, counts, inputs, state, errors and dynamic data are live HTML/CSS/DOM components.
- baked runtime Korean text/buttons/data in imagery = DESIGN FAIL.

## 13. User Command -> Deliverable Contract

- `시안 만들어줘` -> produce and self-validate a DESIGN_MOCKUP image.
- `시안 수정해줘` -> revise the same design direction; provide the revised image.
- `UI 구현해줘` / equivalent -> implement the approved mockup using separate high-density illustration assets + live DOM; deploy UI preview; provide current screenshot image + mobile-openable preview URL.
- `UI 수정해줘` -> revise implementation; regression-check; provide updated screenshot image + updated preview URL.
- `UI 승인` -> freeze approved UI scope/evidence; function implementation becomes allowed.
- `기능 구현해줘` / `기능 수정해줘` -> implement against UI_FREEZE; self-test and regression-test; provide screenshot image + actual function preview URL.
- `기능 승인` -> explicit trigger authorizing the routine production pipeline below without repeated mechanical approval prompts.

`기능 승인` pipeline:
`PWA BUILD -> syntax/build -> local browser tests -> automated tests -> function regression -> UI layout/overlap/truncation -> Korean/English typo/copy -> touch/interaction -> data/IndexedDB -> offline/online recovery -> service worker/cache -> manifest/installability -> migration/data preservation -> severity gate -> GitHub production update -> Netlify Git auto-deploy -> existing production URL verification -> installed-PWA/cache/update verification -> RELEASE PASS`

If BLOCKER/CRITICAL/MAJOR remains, production publication stops. TAKY may self-correct and rerun validation when the correction does not change protected product decisions. Product decision changes, destructive actions, ambiguous targets or unresolved major defects -> HOLD / human decision.

## 14. Deployment Preservation

PRESERVE:
- existing production URL
- existing home-screen-installed PWA relationship
- GitHub as central deployment source
- Netlify Git-based automatic deployment
- user data across updates
- managed-file synchronization while preserving deployment/configuration files

Deployment success is not Release Pass. The existing production URL and installed PWA update/cache/data behavior must be checked after deployment.

## 15. Identified Handoff-Loss Risk

A generic handoff phrase such as `FAMILY = diary/letters/multi-child` is insufficient because recovered source contains additional details such as:
- relations/permissions
- family group/invitation
- forest mailbox
- cheer cards
- optional shard gift
- shared album/calendar/cloud
- shared special exploration
- family growth record
- explicit familyId/memberId/childId isolation and rollback migration.

Therefore future HANDOFF must preserve either these decisions or exact recoverable source pointers. Missing them while claiming continuity = HANDOFF_LOSS.

## 16. Current Audit Result

- Core product/function recovery: PASS_WITH_CONDITIONS
- FAMILY existence/boundary recovery: PASS
- FAMILY detailed recovery from available documents: PASS_WITH_CONDITIONS
- Exact first-chat-to-current raw-message coverage: UNVERIFIED
- Historical visual lock compatibility with latest redesign: CONFLICT RESOLVED by latest user direction; old mandatory visual inheritance is SUPERSEDED
- Actual UI final: NOT YET
- Actual function implementation validation: NOT YET
- Actual FAMILY migration proof: NOT YET
- Actual Google Calendar proof: NOT YET
- Actual deployed PWA regression proof: NOT YET

No `누락 0건` claim is allowed until full-source exact coverage is independently proven.

## 17. Next Required Gate

Before any new Snap & Pop mockup is promoted to an approval candidate:
1. re-check this audit against latest project MASTER/workflow
2. ensure all recovered material items have an active disposition
3. resolve any new MISSING / CONFLICT / HANDOFF_LOSS
4. create mockup
5. real-output self-validation
6. only then show user.
