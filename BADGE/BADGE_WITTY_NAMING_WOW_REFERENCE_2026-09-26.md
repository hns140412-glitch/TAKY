# ORIGINAL WITTY ACHIEVEMENT NAMING — WoW-inspired reference — 2026-09-26

## Direction
Direct user request: borrow the *writing technique* behind witty World of Warcraft achievement titles and weave that wit into the TAKY exploration badge catalogue. Not a request to copy proprietary WoW titles or convert this into a Blizzard game. The original catalogue of 60 and child-history discovery templates of 20 remain the source authority.

Background references:
- https://www.reddit.com/r/wow/comments/c1bzq9 — community appreciates unexpected, punny quest/achievement wording.
- https://www.reddit.com/r/wow/comments/124byun — comments describe surprise, memorable achievement moments.
- https://www.reddit.com/r/wow/comments/1vxp4p1/ — ordinary personal achievement can be meaningful regardless of competitive rarity.

## Three-piece Korean copy structure
`display_title_proposal` (short, instantly memorable) → `unlock_toast_proposal` (situational punchline revealed ONLY after an actual verified award) → `flavor_text_proposal` (warm narrative that honors what really happened).

80 independent, original Korean proposals are mapped 1:1 in `BADGE/badge-wow-inspired-copyworking.json`:
- 60 preserved `source_draft_id` + `canonical_title`, 60 alternate proposed titles, toasts, flavor descriptions.
- 20 preserved `template_id` + `canonical_title`, 20 alternate proposed titles, toasts, flavor descriptions.
- QA: `BADGE/badge-wow-inspired-copy-validator.js` and test preserve source identity, count, uniqueness and approval boundary.

## Humor devices / tone guard
- SITUATIONAL_TWIST: a tiny action is treated like an expedition report. E.g. original `해뜰락말락` → proposed `이불 왕국 탈출기`; toast `해가 뜨기 전에 내가 먼저 떴다!`.
- TALKING_OBJECT: a clock, hint card, desk or map gets one amusing line. `꼬끼오 출발` → `알람보다 한발 먼저`; toast `꼬끼오는 오늘 휴가입니다.`.
- PUN_WORDPLAY: Korean double meaning rather than literal imported English puns. `시간 발견자` → `잃어버린 분을 찾습니다`.
- SELF_AWARE: understated meta humor. `몰래 시작` → `아무도 안 시켰는데요?`.
- CONTRAST: apparent weakness reverses into a positive insight. `그래도 출발` → `준비 덜 됐어도 출항`.
- QUIET_PRIDE: dignity and meaning without a competitive title. `오늘은 여기까지` → `멈춤도 실력입니다`.
- MYSTERY_REVEAL: a clue is revealed at the moment of acquisition. `범인은 여기!` → `범인은 3번째 줄`.
- CALLBACK: a line gains meaning from the child's own earlier learning history. `힌트 졸업식` history template → `힌트 카드 졸업식`.

Don't turn mistakes, slow learning, assistance, rest, or failing to get a badge into ridicule or punishment. Avoid productivity pressure, rankings, scores, excessive grinding, or badges awarding from AI-invented history. Keep names child-friendly and accessible; punchline should not rely on a topical meme to make sense.

## Four moment ranks are separate from reaward tiers
POCKET / FIELD / EXPEDITION / SECRET shape illustration and reveal character, not personal value, rarity odds or a power ranking. Reacquisition remains first verified award = unlock + zero stars; each distinct approved reaward = one star, five stars = tier-up. No new/replaced gameplay rule from a humorous name. Both recovered candidate image sheets remain unapproved.

## Integration / approval boundary
All `display_title_proposal` etc. are `COPY_PROPOSAL_NOT_RUNTIME_APPROVED`. Do not override source stable names or localizations until a distinct editorial/visual binding decision. A completed learning-history discovery **candidate** cannot fire an `unlock_toast`. Only an authenticated child-scoped approved Award Ledger receipt plus approved visual asset can render actual achievement acquisition. Family praise badges and gems are separate; Parent has no personal locked/unearned atlas; gem gift limit remains 1..5 per transaction.

No runtime catalogue activation, approval of 60 historical drafts or images, new Award Ledger receipts, Gem Wallet change, app import, Netlify deployment or Ready main merge in this slice.
