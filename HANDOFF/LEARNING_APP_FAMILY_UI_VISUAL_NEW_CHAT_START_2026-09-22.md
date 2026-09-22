최신 TAKY 기준으로 Learning App Family UI/Visual 통합 시안 작업을 재개해.

이번 재개는 “새 디자인을 처음부터 만드는 작업”이 아니다.
기존에 잘 잡혀 있던 시안/캐릭터/탐험대/섬 세계관을 실제 자산에서 복원한 뒤,
사용자가 지적한 누락·중복·오류만 DELTA 수정하는 작업이다.

먼저 TAKY repo `hns140412-glitch/TAKY`,
branch `taky/c2s-learning-material-utilization-2026-09-21`를 live refresh해.

READ FIRST:
1. `C2S/LEARNING_APP_FAMILY_UI_VISUAL_RESUME_C2S_2026-09-23.md`
2. `C2S/LEARNING_APP_FAMILY_UI_VISUAL_RESUME_ATOMS_2026-09-23.json`
3. `C2S/LEARNING_APP_FAMILY_INTEGRATED_LOGIC_UI_CANONICAL_2026-09-22.md`
4. `C2S/LEARNING_APP_FAMILY_UI_DECISION_REGISTRY_2026-09-22.md`
5. `C2S/LEARNING_APP_FAMILY_VISUAL_MOCKUP_INTEGRATION_REGISTRY_2026-09-22.md`
6. `HANDOFF/LEARNING_APP_FAMILY_UI_VISUAL_INTEGRATION_HANDOFF_2026-09-22_LATEST.md`
   - LATEST RESUME OVERRIDE — 2026-09-23 우선

그 다음 Library/대화 자산에서 아래 4개를 실제로 찾아 이미지와 내용을 확인해.

1. `함께 준비하는 탐험대 여정.png`
2. `가이드☆ 여섯 친구의 찬란한 여정.png`
3. `나만의 섬, 더 많은 이야기.png`
4. `imagegen.png` + 연결된 사용자 원문

어느 한 장을 통째로 정본이라고 가정하지 마.
각 자산에서 요소별로:
- ACCEPTED
- REFERENCE_ONLY
- REJECTED
- SUPERSEDED
를 복원해.

최근 이 대화에서 만들어진 아래 결과는 최종 시안 기준에서 제외해.
- generic multi-phone high-fi poster
- 임의 Crew/아이 캐릭터를 만든 iPhone 시안
- placeholder 중심 온보딩 와이어프레임
- 기존 이미지를 crop/overlay한 delta patch PNG

이들은 FAILURE EVIDENCE일 뿐 BASE가 아니다.

현재 작업 방식:
`기존 최선 BASE 복원 → 정확한 DELTA MAP → 그 부분만 수정`

먼저 이미지를 만들지 마.
가장 먼저 아래를 보고해:
1. 실제로 찾은 기존 BASE 후보
2. 화면별로 무엇을 그대로 보존할지
3. 무엇만 수정할지
4. 서로 충돌하는 과거 시안은 무엇인지
5. 현재 OPEN은 무엇인지

그 다음에만 수정 시안을 만든다.

온보딩 의미 흐름:
탐험대원 6명 첫 만남/친숙화
→ 첫 동행 탐험대원 선택
→ 호칭/이름 설정이 현재 계보에 있으면 유지
→ 사진 촬영/보관함
→ Signature Item
→ 현재 canonical의 방향 선택
→ A/B/C 같은 아이 캐릭터
→ 선택/닮음 보정/Visual ID
→ 우리 탐험 색(Shared Expedition Accent)
→ Voyage / Drop
→ 섬을 처음 발견
→ 섬 이름 짓기
→ Base Camp로 이동
→ Base Camp 이름 짓기
→ Ready 진입

Core 6:
두비 / 로리 / 잉크 / 노바 / 테이크 / 제로.
기존 Visual ID 계보를 먼저 회수하고 임의 대체하지 마.
최종 Visual ID 1:1 검증이 미완이면 OPEN으로 표시해.

Ready는 정확히 세 개의 primary 화면:
1. 이번 주 여정
2. 오늘의 탐험길
3. 그냥! 지금 하면 돼! Timer

Ready Weekly:
- Planner-first
- Mon–Sun
- 고정 일정
- Planner DATED TODO
- 실제 자유시간
- today marker
- 등교 전 할 일이 실제 데이터에 있으면 포함
- Base Camp/섬은 맥락 배경
- Planner가 화면의 주인공

Timer는 기존 LOCKED 시안을 건드리지 마.

결과 시안 단계가 되면:
- iPhone 390×844
- 한 화면씩
- BASE 비주얼 계보 유지
- 새로운 디자인 언어를 임의로 만들지 말 것.

사용자를 테스터/디버거로 쓰지 마.
알고 있는 기준 위반은 제시 전에 자체 검토해.

배포 / Netlify / main merge / 실기기 PASS는 현재 범위가 아니다.

이번 재개의 첫 실행은 “새 시안 생성”이 아니라:
`SOURCE RECOVERY + BASE SELECTION + DELTA MAP`

TAKY:
Think Again, Keep Your Key.
한 번 더 생각하고, 핵심은 놓치지 마.
