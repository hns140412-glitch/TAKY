# TAKY / 탐험대원 음성 제작 CURRENT

## 2026-10-13 최신 구현 결과 (이전 Ready 감사보다 우선)
- **Ready 전체 앱 실사용 첫 실행 회복 PASS.** `ready-stage-c.js`가 첫 실행 화면을 강제로 삭제하고 미완료 프로필 위에 후속 런타임을 부팅하던 문제를 수정. 신규 사용자의 첫 실행 완료까지 Core6 화면 보존·말풍선·WAV 재생 PASS. **기존 READY 프로필의 유효성·첫 실행 화면 비표시는 확인했으나 후속 전체 런타임 Boot READY 완료는 별도 검사 지연으로 OPEN** (과도한 CPU 반복검사 중단).
- 실제 Chrome 격리 프로필에서 **보호자 모드→프로필→시험용 사진→캐릭터 생성 미루기→Core6 첫 만남→두비·로리 각 SIGNATURE WAV 실재생/말풍선→로리 선택→테마 선택→READY 저장** 전 과정 통과. 증거: `staging/crew_voice_20261012/READY_INTRO_CANONICAL_CORE6_BROWSER_QA_20261013.json`.
- 새 공통 모듈: `SHARED/runtime/ready-explorer-intro-canonical-v1.js`; 앱 실제 소비: `Ready & Set/explorer-crew-voice/ready-explorer-intro-canonical-v1.js` 및 `Ready & Set/index.html`. **기존 구형 인트로 3명의 음원을 재사용하지 않는다**. 승인된 Core6 이미지·정확한 SIGNATURE 텍스트와 WAV/승인 MP3 교체 키만 사용.
- **주의:** 인트로 선택 `introPreferredCrewId/explorerId` 저장은 증명됐지만 **캐노니컬 관계 엔진의 `main_character_id`는 의도적으로 변경하지 않았다**. 친밀도/해금 없이 정식 주 동행으로 승격하는 편법을 피했으며, 첫 만남→정식 동행 승인 소비는 OPEN. 이후 Ready 홈/영어녹음의 구형 3인 표시·브라우저 TTS도 여전히 OPEN.
- 전체 9사건 인트로의 **짐 꾸리기·출발/항해·섬 도착·섬 이름·베이스캠프 이름** 전용 대사와 앱 소비는 아직 부족. **이 부분이 끝나기 전 유료 녹음 NO-GO**. 첫 만남 실재생 PASS를 인트로 전체 PASS라고 확대하지 말 것.
- Play Camp 수정, 유료 ElevenLabs 생성, push/merge/Netlify 배포는 수행하지 않았다. 앱 테스트는 격리 브라우저의 가짜 이름·합성 이미지 사용으로 사용자 실제 프로필을 수정하지 않았다.

### 첫 여정 사건 → 실제 대사·음원 소비 계약
| 사건/화면 | 현재 실제 소비 | 녹음 전 할 일 |
| --- | --- | --- |
| 1. 가족 연결·프로필 | 화면 입력 중심, 탐험대원 음성 별도 없음 | 불필요한 음성 억제 유지 |
| 2. Core6 첫 만남 | **SIGNATURE 6개**, 카드 터치마다 정확한 WAV+말풍선 PASS | 6개는 기존 24개 인사 출처에 포함, 별도 유료 녹음 승인 확인 |
| 3. 소개 탐험대원 선택 | `introPreferredCrewId` 저장 PASS, 주 동행 확정은 별개 | 첫 만남→관계·해금→`main_character_id` 정식 확정 연결, 중복 인사 금지 |
| 4. 사용자 Visual ID | 사진·캐릭터 제작 또는 제작 미루기 PASS | 탐험대원 Visual ID와 사용자 자신의 Visual ID 절대 혼동 금지 |
| 5. 짐 꾸리기 | 전용 대사·음원 소비 없음 | 확정 시안/원문 회수 후 정확한 발화 또는 무음 결정 |
| 6. 출발·낙하·항해 | 전용 대사·음원 소비 없음 | 사건 순서·캐릭터 소유·발화 키 확정 |
| 7. 섬 도착·발견 | 전용 대사·음원 소비 없음 | 장면 주인공과 음성 중재 정의 |
| 8. 섬 이름 짓기 | 탐험 테마 선택과 분리돼 있음, 전용 음원 없음 | 이름 입력·확정 시 발화/무음 결정 |
| 9. 베이스캠프 발견·이름 짓기 | 아직 소비 미확보 | 실제 캠프 이름과 UI 기록·대사 키 연결 |
| 후속 미션·귀환 | 기존 ASK/HINT/ACK 소스 일부 있음 | 사용자 실행 사건과 재회/작별 등 신규 문구 96후보 대조 |

이 표는 **기능·녹음 준비를 위한 부족분 지도**이지 신규 문구나 유료 녹음의 자동 승인 목록이 아니다. 기존 264개 원문·9 Voice ID 잠금 유지.



## 최우선 보정 — 2026-10-13 Ready & Set 인트로 실소비 정밀 감사
**현재 NOT READY, 유료 녹음 NO-GO.** Ready 첫 실행·인트로 연결 결함 8개(중대 4/높음 4)를 확인했다. 앞서 264개 대사/9음색 정합 PASS는 **인트로 여정 구현·대사 준비 완료가 아니다**. 활성 index.html은 4~5단계 후속 온보딩 소스를 불러오지 않고, 실제 화면/영어녹음/목소리 미리듣기는 구형 루미·피코·모리 3인 길잡이와 브라우저 TTS를 부분 사용한다. 공통 24명 선정/음원 오버레이와 화면 주인공, 인트로 FIRST_MEET 이벤트가 통합되지 않았다. MAIN_CREW 228/Play Camp Core6 36의 기존 264키에 인트로 출발/짐 꾸리기/도착/섬·베이스캠프 이름짓기 전용 음원 키는 없다. **확정 9사건 인트로 여정과 앱/대사/UI/음원 파일을 대조한 다음 새 대사 원문을 확정**해야 한다. 임의로 구형 안내를 새 승인 대사로 덮거나 기존 264를 재녹음하지 않는다.

증거·설계/소비 복원: `staging/crew_voice_20261012/READY_SET_EXPLORER_CREW_INTRO_VOICE_AUDIT_20261013.json` 및 `staging/crew_voice_20261012/READY_SET_INTRO_VOICE_RECONCILIATION_20261013.md`.
아래 기존 검증 수치는 인트로를 검증한 것이 아니라 앱 카드/부분 이벤트 경로 검증으로만 해석한다.

기준일: 2026-10-13
단일 실행 기준. 이전 검토 내용은 `staging/crew_voice_20261012/HISTORY/EXPLORER_CREW_VOICE_PRE_GRADE_RULE_CLEANUP_20261013.md`에 기록용 보존한다. 이전 기록의 학년별 음성 차단 설명은 적용하지 않는다.

## 1. 사용자 확정 음성 정책
- 탐험대원은 **24명, ElevenLabs 확정 음성 9개 그룹(VF01~VF06, SP01~SP03)**이다. 인간형 6명은 기존 SP 3그룹을 공유한다. 캐릭터 Visual ID, 성격, 음성 그룹은 학년별로 분리하지 않는다.
- **MAIN_CREW/PLAY_CAMP는 앱과 대사 콘텐츠의 소유 구분**이지 저학년·고학년 구분이 아니다. Play Camp 저장소 변경 금지.
- **학년 무관 회귀 증거(2026-10-13):** 24명 × 3개 앱 × 8개 학년/미상 × ASK·HINT·FEEDBACK = 1,728개 정적 호출 조합에서 같은 캐릭터/의도 원문 키 유지. PC 브라우저 실제 초2(E2) 세션에서 Hide/두비 `MAIN_CREW:dubi:ASK:1`, Snap/린 `MAIN_CREW:guide-19:ASK:1` WAV `playing`·HTTP 200 재검증 PASS. 57/57 공통 단위 테스트 PASS. Ready 전체 인트로/미디어 소비는 여전히 OPEN이고 녹음 NO-GO를 변경하지 않는다.
- 현재 메인 대사 원문의 `E5_6` 표시는 기존 144개 원문을 찾아가는 **레거시 데이터 키**다. 실제 학습자 학년이 아니며 UI 라우팅 조건으로 사용하지 않는다.
- 학년, 학습자, 세션 데이터는 학습·리포트용 메타데이터다. 학년 미상, E1~E6, 중등 확장 여부로 탐험대원 목소리와 인사를 차단하지 않는다. 다만 앱의 실제 캐노니컬 주 동행·만남·해금·첫 실행/프로필 준비 조건은 그대로 따른다.
- 기존 승인 문구와 음원은 임의 수정·재제작하지 않는다. 승인 MP3가 정확한 대사 키에 등록되면 우선 재생, 없으면 기존 TTS WAV를 사용한다.

## 2. 콘텐츠·제작 범위
| 범위 | 수량 | 상태 |
| --- | ---: | --- |
| 기존 원문/음원 키 | 264 | 잠금 원문·해시·TTS 목업 있음 |
| 유료 녹음 승인 본대사(R10) | 180 | 파일별 합성/청취 전 |
| 별도 출처 대표 인사(SIGNATURE) | 24 | 선택 UI 실제 사용. 추가 유료 범위 확정 필요 |
| 별도 출처 Core6 장면/기억 | 60 | 조건부 소비. 유료 범위 확정 필요 |
| 신규 재회/작별/재도전/축하 후보 | 96 | 편집 초안. 사용자 원문 확정 전 제작 금지 |
| 실제 승인 ElevenLabs MP3 | 0 | 아직 생성/승인 안 됨 |

정확한 264행 문구·캐릭터·음성 ID·해시·연출은 `staging/crew_voice_20261012/EXPLORER_CREW_PRODUCER_LINE_LEDGER_20261013.json`과 `EXPLORER_CREW_RECORDING_264_SOURCE_SHEET_20261013.csv`가 기준이다. 현재 WAV는 Windows Microsoft Heami 한 음성에 9개 연출 프로필을 적용한 목업이며 ElevenLabs 9종 음질 검증으로 취급하지 않는다.

## 3. 실제 구현 및 검증
- 중앙: `SHARED/runtime/explorer-crew-learner-voice-context-v1.js`는 학년을 선택적 메타데이터로만 유지. `explorer-crew-content-owner-v1.js`가 MAIN_CREW 고정 원문 키를 앱/캐릭터 기준으로 조회한다. `explorer-crew-ui-voice-integration-v1.js`는 이 두 모듈을 실제 음성 이벤트와 연결한다.
- Ready & Set / Hide & Seek / Snap & Pop HTML에 중앙 콘텐츠 소유 모듈을 각각 정확히 1회 등록. 설치기 `SHARED/runtime/install-explorer-crew-mock-into-apps.cjs`는 재호출 멱등성(변경 파일 0)을 검증했다.
- 단위·경로 검증: 학년별 동일 ASK 키 **24명 × 3개 앱 × 7조건 = 504건** 정합. 콘텐츠/컨텍스트/브리지/오디오·네이티브 이벤트 회귀테스트 **57/57 PASS**. 제작 기초 17항목 정합 PASS.
- 실제 브라우저: Hide 초1 두비 `MAIN_CREW:dubi:ASK:1`, Snap 초3 린 `MAIN_CREW:guide-19:ASK:1`가 UI 클릭 → WAV HTTP 200 → `playing` PASS. Hide/Snap 캐릭터 선택 24명/24명마다 인사·말풍선 실재생 PASS.
- 네이티브 학습 이벤트 소비: Hide의 `HideSeekBridge.emit(HELP_NEEDED, crew_voice_requested=true)` → 두비 `HINT:1`, Snap의 `SnapPopBridge.emit(TASK_COMPLETED, child_authored=true)` → 린 `ACKNOWLEDGE:1`은 실제 동일 창의 학습 이벤트 전송 → WAV `playing` PASS. **단, 실제 아이의 도움/완료 조작 전체를 통한 E2E가 아니라 브라우저 내부의 정식 앱 브리지 호출 검증**이다. Snap 원래 브리지가 같은 창 이벤트를 통지하지 않아 수정했으며, 무전 중복 호출 방지 및 이벤트별 학습자·세션 일치 검사를 추가했다.
- Ready: 실제 학습자 프로필 준비/선택 카드/대사 말풍선 로드 확인. **전체 Ready 브라우저 `playing` 검증 미완료**. 별도 19초 테스트가 실행 대기 상태로 끝나 교착 원인을 확보하지 못했으며, 동일 고부하 테스트 반복은 중단했다.
- 추가로 모든 앱 이벤트 실소비를 증명한 것은 아니다. 앱 이벤트 행 18개 중 재생 근거를 가진 경로는 **6개**, 나머지 **12개는 OPEN/조건부/범위 밖**이다. `staging/crew_voice_20261012/EXPLORER_CREW_REAL_APP_EVENT_TO_VOICE_MATRIX_20261013.json` 참조. 음성 파일이 있다는 이유만으로 미연결 이벤트를 PASS 처리하지 않는다.

## 4. 녹음 전 기술·콘텐츠 현황
- 사전판정 생성기: `SHARED/runtime/preflight-explorer-crew-paid-recording.cjs`
- 현재 판정: **NO_GO**, 학년별 음성 차단(U005)은 **PASS**로 종료. Hide/Snap 네이티브 HINT·ACK 일부 실재생은 추가 PASS지만, 이것이 전체 앱 상황별 사용 완성을 의미하지 않는다. 선행 미해결 8항목: `U003` Ready 실제 재생, `U004` 상황별 질문/힌트/피드백 소비, `U006` 콘텐츠/UI·관계 소비 정합, `C001` 대표 인사 24개 추가 제작 범위, `C002` 조건부 60개 제작 범위, `C003` 새 대사 96개 원문 확정, `C004` 재회·작별·오답·축하·중재, `Q001` 실제 9개 음색 청취 승인.
- 실제 MP3 입고 검증과 실기기/배포 검증은 제작 **이후** 별도로 수행한다. 전자를 완수했다고 후자까지 PASS 처리하지 않는다.
- 녹음 승인 이후: 원문·Voice ID·승인증거·MP3 SHA 및 MPEG Layer III 파일 검사 → 앱별 실제 음원 복사 → 마지막에 승인 매니페스트 변경. 원본 WAV 유지, 올바른 파일 재녹음 금지.
- 최종 목표는 **누락 없는 한 번의 일괄 녹음**이다. 녹음 자체는 시작하지 않는다. 사용자 확인이 필요한 것은 대사 최종 문구·유료 추가 범위 등 주요 결정만이다.

## 5. 수정/배포 경계
Play Camp 저장소 수정, 기존 캐릭터 원화·확정 음성 그룹 변경, ElevenLabs 유료 TTS, Git push/merge, Netlify 배포, 사용자 프로필 초기화는 모두 하지 않는다. 테스트는 격리 브라우저 프로필로 수행한다.

## 2026-10-13 대청소 소스 경로 (로컬 코드 반영)
- 제작 소스·WAV 파일 264개는 활성 경로 `TAKY/staging/crew_voice_20261012`에 그대로 둔다.
- 검증된 264개 대사 해시/264개 WAV 해시/9 음색 그룹의 **파생 위치 인덱스**: `TAKY_AI_WORKBENCH/00_CONTROL/TAKY_CREW_VOICE_SOURCE_INDEX.json`. 원본 복사나 승인 승격 없음.
- 승인 MP3는 해당 제작 소스 경로에서 0개. 유료 녹음 NO-GO 및 첫 여정 연결 OPEN을 유지.
