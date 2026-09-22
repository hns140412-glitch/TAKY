최신 TAKY 기준으로 Learning App Family의 UI/Visual 통합 작업을 재개해.

이번 작업은 Ready & Set / Snap & Pop / Hide & Seek의 시안과 UI를 “똑같이 만드는 작업”이 아니라,
각 앱에서 이미 검토·고정·수정된 UI/시안 기준을 중앙 TAKY 기준으로 취합하고,
공통 Visual DNA와 앱별 Regional Dialect를 분리해서 관리하는 작업이다.

먼저 TAKY repo `hns140412-glitch/TAKY`,
branch `taky/c2s-learning-material-utilization-2026-09-21`를 live refresh하고,
아래를 순서대로 읽어 현재 상태를 복원해.

1. `HANDOFF/LEARNING_APP_FAMILY_UI_VISUAL_INTEGRATION_HANDOFF_2026-09-22_LATEST.md`
2. `C2S/LEARNING_APP_FAMILY_UI_DECISION_REGISTRY_2026-09-22.md`
3. `C2S/LEARNING_APP_FAMILY_VISUAL_MOCKUP_INTEGRATION_REGISTRY_2026-09-22.md`
4. `C2S/LEARNING_APP_FAMILY_ISLAND_WORLD_UI_MOCKUP_CRITERIA_2026-09-22.md`
5. `C2S/LEARNING_APP_FAMILY_SCREEN_COMPOSITION_STANDARD_2026-09-22.md`
6. `C2S/TAKY_SHARED_BADGE_SYSTEM_CANONICAL_2026-09-22.md`
7. `C2S/TAKY_SHARED_BADGE_VISUAL_CONTRACT_2026-09-22.md`
8. `C2S/TAKY_BADGE_SHARE_LINEAGE_RECOVERY_2026-09-22.md`

그 다음 Ready / Hide / Snap의 최신 UI handoff와 master를 각각 읽어.

Ready:
- repo: `hns140412-glitch/Ready-Set`
- branch: `taky/ready-rebuild-v01-2026-09-21`
- `HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md`
- `C2S/READY_SET_UI_PRODUCTIZATION_C2S_CLOSURE_2026-09-22.md`
- `HANDOFF/READY_SET_UI_PRODUCTIZATION_START_PROMPT_2026-09-22.md`
- `Ready_Set_Ui_Master_Logic_REV_07.md`
- `Ready_Set_Share_Golden_Contract_REV_01.md`

Hide:
- repo: `hns140412-glitch/Hide-Seek`
- branch: `rewrite/hide-runtime-v2-2026-09-21`
- `HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md`
- `HANDOFF/HIDE_UI_DESIGN_HANDOFF_2026-09-22_REV2.md`
- `Hide_Seek_UI_MASTER_LOGIC_REV_04.md`

Snap:
- repo: `hns140412-glitch/Snap-Pop`
- branch: `taky/snap-pop-implementation-2026-09-20`
- `HANDOFF/TAKY_UI_DECISION_REGISTRY_POINTER_2026-09-22.md`
- `C2S/SNAP_POP_PRODUCT_UI_ARCHITECTURE_2026-09-22.md`
- `C2S/SNAP_POP_FINAL_MOCKUP_UI_DESIGN_CRITERIA_2026-09-22.md`
- `Snap_Pop_UI_MASTER_LOGIC_REV_12.md`

핵심 전제:

- Ready = BASE CAMP / ISLAND MAP
- Hide = JUNGLE / WATERFALL
- Snap = BEACH
- 하나의 동일한 섬 세계를 공유한다.
- 같은 제품군이지만 화면은 동일하게 만들지 않는다.
- 공통 Visual DNA + 앱별 Regional Dialect + 화면별 Composition으로 관리한다.
- Ready/Hide에서 이미 LOCKED된 UI를 Snap 작업 때문에 흔들지 않는다.
- Snap의 PROVISIONAL UI를 전체 family lock으로 올리지 않는다.
- Badge Tier와 성급 1~5는 공통 체계다.
- Badge Star Grade는 generic reward star가 아니다.
- 배지/공유/탐험대/캐릭터 continuity는 전체 앱에서 일관되게 적용한다.
- 시안 한 장 전체를 통째로 승인/폐기하지 말고, 구도/배경/캐릭터/정보구조/시각언어 요소별로 WHAT_IS_VALID / WHAT_IS_NOT_VALID를 분리한다.
- 이전에 REJECTED/SUPERSEDED된 시안 요소가 다시 살아나지 않게 한다.
- 사용자에게 이미 승인받은 UI/시안 요소를 새 제안처럼 다시 만들지 않는다.
- 사용자를 테스터/디버거로 쓰지 않는다.
- Netlify / deploy / main merge 금지.

이번 재개 후 첫 작업은 새 시안을 만드는 것이 아니다.

아래 순서로 진행해:

1. Ready / Hide / Snap의 기존 시안·UI 검토 결과를 전수 회수
2. 각 시안을 V0~V5로 분류
   - V0 Reference
   - V1 Direction Candidate
   - V2 Composition Lock
   - V3 Visual System Lock
   - V4 Screen Family Lock
   - V5 Final Visual Freeze
3. 각 시안에서
   - ACCEPTED
   - REFERENCE_ONLY
   - REJECTED
   - SUPERSEDED
   를 요소별로 분리
4. Ready Home / Snap Home / Hide Home을 비교표로 정리
5. Shared Visual DNA와 Regional Dialect를 분리
6. Family Visual System Skeleton 작성
7. Screen Inventory / State Matrix / Transition-Return Matrix 보완
8. 이 기준들이 닫힌 뒤에만 Low-fi 진입
9. High-fi는 Low-fi와 Visual System 검증 후에만 진행

항상 답변 마지막에:
- 각 앱 UI 상태
- VISUAL_FREEZE_LEVEL
- 새로 LOCK된 것
- OPEN
- CONFLICT
- SUPERSEDED
- REGRESSION_RISK
- 다음 단계
를 보고해.

시안부터 만들지 마.
먼저 기존 시안과 기준을 정확히 복원·통합해.
