# C2S Evidence Recovery Regression — 2026-09-20

## Incident

Snap & Pop 탐험대 Core 6 복원 과정에서 과거 확정 Visual ID가 존재했음에도 초기 복구가 현재 이름/문서 중심 검색에 치우쳐 `미회수 / OPEN`으로 남았다.

사용자가 이후 직접 제공한 과거 이미지 보드에는 다음이 명시되어 있었다:
- `6명의 Visual ID (확정)`
- `Visual ID Lock`
- Core 6: 두비 → 로리 → 잉크 → 노바 → 테이크 → 제로
- 01~06 개별 PASS

따라서 초기 상태는 **증거 부재가 아니라 복구 실패**였다.

## Failure Pattern

`CURRENT TERM SEARCH → MISS → OPEN/UNRECOVERED`

누락된 복구 차원:
- legacy/superseded terms;
- decision markers;
- image/attachment/ZIP/manifest lineage;
- parent/sibling folder traversal;
- reverse trace from later Handoff/summary claims;
- multiple recovery families.

Normative correction:

`NO_EVIDENCE_FOUND != EVIDENCE_ABSENT`

## Canonical Correction

Branch: `taky/c2s-evidence-recovery-2026-09-20`

Updated:
- `MASTER/CONVERSATION_TO_SYSTEM_PROTOCOL.md` — Evidence Recovery Pass before unresolved/missing classification.
- `MASTER/RECOVERY_FORENSICS_PROTOCOL.md` — bounded targeted C2S recovery specialization.
- `MASTER/ENFORCEMENT_PROTOCOL.md` — structured recovery gate.
- `ENFORCEMENT/taky_gate.py` — deterministic fail conditions.
- `ENFORCEMENT/replay_cases_v5.json` — `C2S-RECOVERY-01` historical-failure + post-fix fixture.

## Replay Evidence

Historical failure fixture:
- prior existence asserted by user = true
- Evidence Recovery Pass = false
- only current-term/current-document search
- strong absence claim after incomplete recovery

Expected/detected:
- `RECOVERY_FAILED`
- `FALSE_MISSING_DECLARATION`

Post-fix fixture:
- Evidence Recovery Pass performed
- current + legacy + semantic + decision-marker + attachment-lineage + reverse-trace modes
- four materially distinct source families
- result = `RECOVERED_DIRECT`
- no absence claim

Expected/detected:
- no failure tokens

Targeted deterministic replay result: **PASS**.

## Claim Boundary

This replay proves the added deterministic gate logic for the encoded failure pattern. It does not prove hosted ChatGPT auto-invokes repository enforcement in every conversation. That runtime boundary remains separately governed.

## Downstream Project Propagation

Snap & Pop branch `taky/snap-pop-implementation-2026-09-20` was corrected so that:
- Core 6 Visual ID is recovered from direct user evidence;
- stale “Visual ID unrecovered” wording is removed;
- Character Identity is separated from Behavior Archetype / Interaction Mode;
- Lori/Tori romanization remains explicit OPEN correction check;
- age-label semantics remain OPEN rather than guessed.
