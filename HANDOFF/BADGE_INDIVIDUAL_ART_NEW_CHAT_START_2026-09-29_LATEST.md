# TAKY / BADGE 60 — New chat handoff (2026-09-29, latest)

## Purpose / handoff-only execution
This document is an actual resume handoff, **not** a request to produce more art. On `재개준비`, write and verify HANDOFF + update logical CURRENT pointer; STOP. No image generation, arbitrary edits, merge, deploy, activation. On new chat, first restore authority and report OPEN, then wait for a separate execution instruction.

## Authority and snapshot at time of handoff
- Repo: `hns140412-glitch/TAKY`.
- Live main EXACT HEAD observed: `09df3d4f011e815e56d41433139bc2fcc7e1a97e`. Re-fetch; do not freeze this as eternal authority.
- Badge Draft PR: [#163](https://github.com/hns140412-glitch/TAKY/pull/163), open/draft/unmerged, head branch `taky/badge-60-independent-scene-art-20260927`, parent PR #160 branch `taky/badge-optional-child-overlay-20260927`. Snapshot **before this HANDOFF write**: `2fa9eca237981ff801d5645719de321c7edca73a`, base snapshot `6aac6fec05fb9c5fe29580165d4831cb963b9222`. Re-fetch the post-handoff exact HEAD and CI on resume.
- At `2fa9eca...`, GitHub Actions "Badge Visual Registry Validation" and "Badge UI contract checks" both SUCCESS. These tests validate source/registry integrity and structural drafts, NOT final painterly visual parity.
- Closed source authority is `BADGE/badge-60-story-20-history-working.json` (60 immutable source IDs, stable titles, storylines, motifs), alongside `BADGE/badge-wow-inspired-copyworking.json` (proposed display titles/flavor texts, **not automatically final runtime names**), approved six-screen reference/art. Original source motif wins over invented interpretation.
- Existing work documents: `CURRENT/BADGE_INDIVIDUAL_ART_CURRENT_2026-09-27.json`; `BADGE/assets/BADGE_60_PAINTERLY_VISUAL_QA_2026-09-27.md` including 2026-09-28 addendum; `BADGE/assets/visual-rework-queue-working.json`; `BADGE/assets/rework-batch-01-source-locked.json`; `BADGE/assets/verify_visual_rework_queue.py` and its negative tests; older `HANDOFF/BADGE_INDIVIDUAL_ART_NEW_CHAT_START_2026-09-27_LATEST.md` (historical, this file overrides only where newer).

## Honest stage / quantified invariants
- Original first-pass scene screening: **29 CONDITIONAL candidates**, **31 correction IDs**. This is a *partition of the first reviewed 60*, not 29 accepted final badges and not 31 remaining to physically create from zero.
- Correction IDs: `001,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,020,021,025,028,033,034,040,042,043,044,046,053,055,058,060`.
- Original conditional IDs: `002,003,019,022,023,024,026,027,029,030,031,032,035,036,037,038,039,041,045,047,048,049,050,051,052,054,056,057,059`.
- More individual art images have subsequently been generated inside ChatGPT; none is automatically passed, registered, uploaded to GitHub, or bound. **Do not compute "32/60 completed" by adding a selected 012 or 008/046 conditional art**. Verify actual files and per-ID evidence before changing progress.
- As verified repository authority: **final visually approved painterly art 0/60; painterly PNG production bindings 0/60; active 0; real awards 0**. The 60 dev bindings and 120 candidate SVG layers are old flat, visually rejected drafts. Their CI success is not visual acceptance. Existing newer painterly independent PNG candidates are not proven committed to PR and are generally flattened files, not independently authored background/interior/foreground.
- **012** ("연필 참모총장", flavor "하고 싶은 순서를 직접 짜 본 날.", motif "접이식 작전지도와 연필"): user selected a rendition to continue with; this is **USER_SELECTED_CANDIDATE_QA_OPEN, NOT FINAL**. One inspected candidate conveyed pencil+three order cards at full size, but sequence/wit was unclear at 64px; verify *exact selected file identity* before any binding. Preserve direction rather than indiscriminately recreating.
- **040** ("멈춤도 실력입니다", flavor "멈춰야 할 때 잘 마무리한 경험.", motif "안전하게 접힌 캠프 지도"): latest prior art overloaded with opened map/camp props; story of deliberately closing and safely putting away today's journey is not legible. **LATEST_REJECTED_REWORK_OPEN**. Previously produced 8-up mascot/contact sheet entirely rejected.
- A set of 8 individual candidates `001/005/034/040/042/043/055/060` was generated in chat, later another per-ID retry and 040 alone: **none constitutes acceptance**. Their exact original binary/path must be verified before reusing. A previous assistant generated artwork even after a `재개준비` command; these images were unsolicited and must not be inferred as new approved content. No arbitrary reconstruction of lost candidate images from names.

## Latest executable source-grounded guard (PR #163 at pre-handoff HEAD 2fa9eca...)
Seven later commits since prior QA note added:
- `BADGE/assets/visual-rework-queue-working.json`: exact 31/29, special 012/040 status, all approval/binding/activation/award counters zero and release HOLD.
- `BADGE/assets/rework-batch-01-source-locked.json`: source-locked, proposal-preserving briefs for first ten source correction IDs **001,004,005,006,007,008,009,010,011,012**. This is a generation specification, **not** ten remade/approved PNGs. The first-ten queue is a reference, not a demand to repeat already tried 001–012 instead of selecting genuine OPEN items.
- `BADGE/assets/verify_visual_rework_queue.py` and `BADGE/assets/verify_visual_rework_queue_test.py`, plus `.github/workflows/badge-ui-contract.yml`, enforce source semantics, fail-closed false approval and 012/040 special states. Negative fixtures included. Rerun exact HEAD CI on resume.

## User-governed art contract, non-negotiable
1. Before any image: retrieve exact source ID + original stable name, proposed display title + flavor text, original storyline and original motif; compare against existing individual candidate and approved user-provided soft pastel hand-painted example.
2. Preserve original motif and achievement; make ONE unique witty act readable at **64px**, not a generic repeated shoe/clock/map/sunrise/camp landscape. Color and palette may vary by badge while painting style stays unified. No invented child, Crew, flag/country emblem, or arbitrary scene. 012 chosen direction is not blanket final approval.
3. One **independent** interior-scene art file per badge; no collage/contact sheet/cropping multi-icon sheet. Outside circular scene transparent PNG; inner scenic background allowed; common rim/shadow/star count/tier/lock/typography independent assets, optional approved user/Crews separate overlays. Maintain honest independently authored background/interior layer evidence, do not claim layer separation from flat PNG or automatic split.
4. Independently inspect actual file at 64/120/200/320, style parity, source meaning, peer distinctiveness, correct RGBA transparent outside and circular silhouette, identity/path/hash evidence, actual UI composition/regression; correction remains OPEN until all gates pass.
5. The user is NOT the debugger. Assistant owns visual/technical self-QA, remediation, faithful implementation. DO NOT ask for 60 repetitive user approvals or turn a visual proposal into approved without evidence.
6. NEVER infer approvals/completion from file presence, app preview/CI, user saying "좋아", or user-selected option. Only publish verifiable actual status.
7. No main merge, Netlify deployment, Work OS or real badge awarding/activation without applicable gates and explicit authorization.

## Exact resumption protocol
1. Read this logical CURRENT pointer → **live main EXACT HEAD** → PR #163 actual latest head/base and CI → this HANDOFF → source JSONs and latest QA/queue/batch.
2. Inherit CLOSED; compare conflicting histories in favor of newer source-grounded verified evidence. Confirm current files actually accessible. Summarize newly OPEN only, disambiguate 012 user choice and 040 fail, show real 60-based progress with no false count.
3. If the new user's instruction is only `재개준비`, create/update HANDOFF and CURRENT and STOP. If new user's instruction is `재개`, report restored state first. Only generate images/implement on explicit execution instruction; select actual deficient IDs rather than auto-restart first ten. One file per badge and source-grounded QA before binding.
4. Treat historical SHAs as snapshots. Do not upload generic image assets, modify main, create duplicate handoff versions, or deploy during resume.

## Suggested new-chat user message
"최신 TAKY 기준으로 배지 60종 개별 원화 작업을 재개해. CURRENT → live main EXACT HEAD → Draft PR #163 실제 최신 HEAD·CI → HANDOFF/BADGE_INDIVIDUAL_ART_NEW_CHAT_START_2026-09-29_LATEST.md → 원본 60종과 최신 QA/31개 rework queue 순서로 복원해. 012는 사용자 선택 후보이며 최종 승인 아님, 040은 수정 OPEN. 기존 조건부 29/수정 대상 31 기준을 증거 없이 완료율로 전환하지 마. 원본 ID/표시명 제안/핵심 상세설명/storyline/motif와 첨부 화풍을 검증하고 실제 미완료만 개별 투명 PNG로 작업해. 먼저 상태·OPEN을 보고하고 다음 실행 지시를 기다려. USER != DEBUGGER. 메인 병합·Netlify 배포·임의 승인 금지."
