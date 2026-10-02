# TATOEBA_HIDE_SNAP_NEW_CHAT_START_2026-10-02_LATEST

## STATUS
- UPDATED: 2026-10-02
- REPOSITORY: hns140412-glitch/TAKY
- MAIN_HEAD_AFTER_MERGE: 598ebbafd1854ed951a79915924662058ad7e94d
- PR: #197
- PR_STATE: MERGED / CLOSED
- TATOEBA_SCOPE: LANGUAGE_USAGE / EXAMPLE_SENTENCE
- AUTHORITY: EXTERNAL INDEX EVIDENCE ONLY
- SOURCE_ID: LANGUAGE_TATOEBA_TEXT_2026
- SOURCE_REF: INDEX:LANGUAGE_TATOEBA_TEXT_2026

## CLOSED
1. Tatoeba v1 read-only transport implemented.
2. Provider item normalization implemented.
3. Item-level fail-closed filtering implemented.
4. Actual item-level license/owner provenance validation implemented.
5. Structured child-facing curation receipt implemented and bound to exact sentence SHA-256.
6. Hide & Seek / Snap & Pop bounded consumer handoff implemented.
7. Existing Mining -> Indexing -> Learning regression path preserved.
8. PR #197 pre-merge CI PASS:
   - TAKY Mining Indexing Learning Integration
   - TAKY Tatoeba Live Provider Validation
   - TAKY Enforcement Replay
9. PR #197 merged to main.
10. Main contains Tatoeba transport/filter/curation/consumer-handoff modules.

## INVARIANTS / AUTHORITY GUARDS
- Tatoeba example sentence != normative usage authority.
- Occurrence != frequency evidence.
- Example exposure != learner mastery.
- Hide exposure != recall or memory-strength evidence.
- Snap reference != learner-authored output.
- Provider output cannot grant Index-owner authority.
- Plain string receipt cannot approve child-facing use.
- Child-facing approval requires structured receipt with PASS for:
  - naturalness/correctness
  - context/sense fit
  - safety/age fit
  - license/attribution
- Receipt must bind exact sentence text SHA-256.
- Hide/Snap handoff is reference-only and cannot auto-credit learner performance.

## HOLD
- CURRENT pointer mutation.
- Canonical promotion.
- Bulk corpus ingest.
- Audio retrieval.
- Direct write into Hide/Seek or Snap/Pop app repositories.
- Netlify / production deployment.
- Any interpretation of Tatoeba as curriculum membership, grade alignment, frequency authority, normative authority, learner mastery, or causal learning-effectiveness evidence.

## IMPORTANT CI NOTE
- PR-stage CI evidence is PASS.
- The Mining Indexing Learning Integration workflow currently does not run on main push; therefore no post-merge main-push run exists for merge commit 598ebbafd1854ed951a79915924662058ad7e94d.
- This does not invalidate the PR-stage regression evidence, but post-merge-main execution evidence remains distinct and must not be invented.

## NEXT OPEN
1. Decide whether a dedicated post-merge main validation path is required.
2. If required, add a non-deployment main validation route and re-run the same regression gates.
3. Keep CURRENT/Canonical and deployment HOLD unless separately approved.
4. After any further Tatoeba work, preserve this authority boundary and update this handoff rather than creating a conflicting LATEST.

## RESUME COMMAND
최신 TAKY 기준으로 Tatoeba 학습근거 작업 재개

## RESUME RULE
- Inherit CLOSED.
- Do not repeat completed PR #197 work.
- Work only on NEXT OPEN.
- CURRENT/Canonical/deployment remain HOLD unless explicit later approval changes them.
