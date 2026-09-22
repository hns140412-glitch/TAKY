최신 TAKY 기준으로 BETA 전체 구조개편 검토를 이어서 진행해.

GitHub `hns140412-glitch/TAKY`의 `taky/system-architecture-realignment-2026-09-22` 브랜치를 먼저 live refresh하고, **현재 exact HEAD를 확인한 뒤** 아래를 순서대로 읽어 현재 상태를 복원해.

1. `C2S/TAKY_BETA_ARCHITECTURE_CONVERGENCE_C2S_CLOSURE_2026-09-22.md`
2. `C2S/TAKY_BETA_ARCHITECTURE_CONVERGENCE_ATOMS_2026-09-22.json`
3. `HANDOFF/TAKY_BETA_ARCHITECTURE_CONVERGENCE_HANDOFF_2026-09-22_LATEST.md`
4. `BETA/TAKY_BETA_RESTRUCTURE_PROGRAM_2026-09-22.md`
5. `BETA/TAKY_BETA_ARCHITECTURE_PLAN_2026-09-22.md`
6. `BETA/TAKY_BETA_LOSSLESS_C2S_PLAN_2026-09-22.md`
7. `BETA/TAKY_BETA_EXECUTION_ROUTING_CLEANUP_GATE_2026-09-22.md`
8. `MASTER/SYSTEM_LAYER_OWNERSHIP_MAP.json`
9. `MASTER/LEARNING_APP_FAMILY_MASTER_REV_01.md`
10. `OS/GUIDE_CHARACTER_RELATIONSHIP.md`
11. `OS/GUIDE_FAMILY_LEARNING_OS.md`

이번 단계는 **구조개편 실행 전에 기준을 최종 수렴시키는 consulting / attack-review 단계**다.

중요:
- 아직 코드 정리/구조개편/대량 문서 수정/Codex dispatch/merge/deploy/Netlify를 하지 마.
- UI 검토, C2S/원자료 확보, Learning Data 완결성, 각 앱 UI/기능 검토가 다른 대화에서 병렬 진행 중이므로 새 evidence가 들어오면 전체 초기화하지 말고 영향받은 owner/contract/consumer/validator만 다시 열어.
- 탐험대 규칙과 뱃지 시스템은 Ready / Hide / Snap 전체를 관통해 일관되게 적용되어야 한다.
- 다만 cross-app 사용 != Family/TAKY ownership이다.
- `Exploration Crew Domain`은 Snap이 현재 steward/incubator/canonical host 역할을 하되 Snap 앱 lifecycle과 영구 semantic ownership을 동일시하지 않는 후보 구조다.
- `Badge Experience Domain`은 cross-app logical domain 후보이며, 앱은 fact/explicit experience event를 발행하고 Badge Domain이 award/progression을 해석한다.
- Badge star는 성급/grade이며 Gem/Wish/EXP/Power와 분리한다.
- Learning History / Badge History / Crew Relationship Memory / Wish Economy Ledger는 별개로 유지한다.
- `ONE EVENT — MANY VALID INTERPRETERS — NO CROSS-OWNER DIRECT MUTATION`.
- `ONE CHANGE — MANY AFFECTED CONSUMERS — TARGETED VALIDATION`.
- `DEEP MEMORY — LIGHT EXECUTION`.

현재 root-cause 우선순위:
1. OWNER TYPE COLLAPSE
2. CANONICAL GENERATION DRIFT
3. SHADOW CURRENT STATE / PROJECTION
4. OPERATIONAL EXPRESSION PROLIFERATION
5. GOVERNANCE ACTIVATION GAP
6. INCIDENT -> GLOBAL RULE LEAK은 중~약으로 하향
7. C2S 자체 원인 가설은 약함/기각

다음 작업:
1. MASTER / OS / STATE / PROJECTIONS / ENFORCEMENT / CI 전체를
   `KEEP_OWNER / KEEP_SUPPORT / CONDITIONAL_ACTIVATION / ROLE_CHANGE / POINTERIZE / CONSOLIDATE / RETIRED_COMPATIBILITY`
   분석 분류로 매트릭스화해.
2. 각 ROLE_CHANGE / CONSOLIDATE / POINTERIZE 후보마다 loss test를 해:
   - 고유 의미가 사라지는가?
   - 어떤 consumer가 깨지는가?
   - recovery path가 사라지는가?
   - 다른 shadow canonical이 생기는가?
3. Exploration Crew / Badge Experience 후보를 UI/Data/C2S의 최신 evidence와 다시 교차검증해.
4. 새 registry를 만들지 않고 `SYSTEM_LAYER_OWNERSHIP_MAP`의 first-class semantic node + pointer로 충분한지 공격검증해.
5. ACTIVE_RULE_PROFILE의 실제 consumer를 추적한 뒤 persistent projection 유지/폐기를 판단해.
6. STATE.md를 small current state + history pointers 구조로 바꾸는 후보안을 검토해.
7. 현재 59-step 단일 enforcement CI를 ALWAYS-RUN AGGREGATOR + FAST CORE + AFFECTED SUITES 구조로 바꾸는 후보를 required-check 안전성까지 포함해 설계해.
8. 충분히 수렴했을 때만 BETA FREEZE CANDIDATE를 작성해.
9. freeze 전에는 Codex 실행 금지.

공격적으로 검증하고, 선호안의 반례와 실패경로를 반드시 찾아.  
파일 수 감소나 validator 수 감소 자체를 성공기준으로 삼지 말고, **현재 의미 단일화 / semantic owner 명확화 / 활성 context 최소화 / targeted validation / reversible migration / silent loss 0**을 성공기준으로 삼아.

항상 새 evidence가 기존 결론을 깨면 이전 결론을 방어하지 말고 수정해.
