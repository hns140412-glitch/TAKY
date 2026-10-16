'use strict';
/* Executable pre-paid freeze evaluation. Go is not a stylistic opinion:
   it needs a source-lock, usage proof and explicit scope authorization. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../..'),work=path.join(repo,'staging/crew_voice_20261012');
const read=(base,name)=>JSON.parse(fs.readFileSync(path.join(base,name),'utf8'));
const source=read(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json');
const candidate=read(work,'EXPLORER_CREW_MISSING_SCENARIO_DIALOGUES_DRAFT_20261013.json');
const cast=read(repo,'CURRENT/EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json');
const mock=read(work,'mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json');
const production=read(work,'EXPLORER_CREW_PRODUCTION_READINESS_AUDIT_20261013.json');
const approved=read(work,'EXPLORER_CREW_PLAYBACK_MANIFEST.json');
const readyIntro=read(work,'READY_SET_EXPLORER_CREW_INTRO_VOICE_AUDIT_20261013.json');
const readyNew=read(work,'READY_CORE6_FIRST_RUN_IMPLEMENTATION_DELTA_20261013.json');
const readyQA=read(work,'READY_INTRO_CANONICAL_CORE6_BROWSER_QA_20261013.json');
const items=[];
function add(id,label,state,detail){
 items.push({id,label,state,detail});
}
const lock=source.rows.length===264&&new Set(source.rows.map(x=>x.key)).size===264&&
 source.rows.every(r=>crypto.createHash('sha256').update(r.exact_text).digest('hex')===r.text_sha256);
add('S001','대사 원문·해시 264',lock?'PASS':'FAIL',lock?'고유 키·원문 SHA 일치':'불일치 존재');
const gids=new Set(cast.voice_families.map(x=>x.elevenlabs_voice_id));
add('S002','9종 Voice ID와 24명 바인딩',
 cast.voice_families.length===9&&gids.size===9&&cast.character_routes.length===24?'PASS':'FAIL',
 '실제 공급자 ID 조회에 기반한 목록, 청취 품질 승인은 별도');
add('S003','WAV 임시 목업',
 mock.clips.length===264?'PASS':'FAIL',String(mock.clips.length)+'개, 기존 승인 MP3 아님');
add('R001','Ready 전체 인트로 여정·캐릭터 소비 일치','PARTIAL',
 '활성 Core6 첫 만남·EXPLORER/THEME·준비 완료는 full Ready browser PASS. 나머지 출발·섬 진입·베이스캠프 작명·영어진행 UI·첫 만남→중앙 main 관계 연결은 OPEN; '+readyIntro.issues_count+'개 최초 감사 항목 중 일부만 해소.');
for(const app of ['HIDE_SEEK','SNAP_POP']){
 const p=path.join(work,'EXPLORER_CREW_SELECTION_TAP_QA_20261013_'+app+'.json');
 let obj;try{obj=JSON.parse(fs.readFileSync(p,'utf8'))}catch{}
 const e=obj?.results?.[0]?.events||[];
 add(app==='HIDE_SEEK'?'U001':'U002',app+' 24명 카드→말풍선→WAV',
  obj?.status==='PASS'&&e.length===24&&e.every(v=>v.latest?.status==='PLAYING_STARTED')?'PASS':'OPEN',
  'QA 증거 '+path.basename(p));
}
add('U003','Ready Core6 첫 만남 UI 터치 음성',
 readyQA.status==='PASS_FIRST_ENCOUNTER_TO_READY'&&readyNew.status.startsWith('CORE6_FIRST_ENCOUNTER_COMPLETE')?'PASS':'OPEN',
 '전체 Ready index에서 두비/로리 정확한 SIGNATURE WAV playing, 말풍선, THEME 선택, 완료된 READY 프로필, 중앙 main 미변경 검증. 전체 9사건과 main 확정은 R001/U006에서 별도 OPEN.');
add('U004','실제 ASK/HINT/ACKNOWLEDGE 이벤트의 앱별 소비','OPEN',
 'Hide·Snap ASK 버튼 playing PASS, Hide HELP_NEEDED→HINT와 Snap TASK_COMPLETED→ACK native bridge emit→playing PASS. 실제 사용자 클릭/완료 시나리오와 다른 상황별 침묵·반복 검증은 OPEN');
add('U005','탐험대원 음성 학년 제한 제거',
 'PASS','24명·9그룹 목소리 공통: 504개 ASK 동일 키 정합 + 1728개 ASK/HINT/FEEDBACK 단계별 호출 PASS. Hide E1 / Snap E3 버튼 WAV playing PASS. E5_6은 과거 원문 저장 키이지 학년 제한이 아님.');
add('U006','대사 종류와 소속·UI/주 동행 상태','PARTIAL',
 '선택 카드와 동행 확정 1경로, Native bridge HINT/ACK 2경로 확인. SCENE/MEMORY 및 실 사용자 전체 UI 흐름은 미증명');
const sourceOnly=source.rows.filter(r=>r.production_authority!=='R10_USER_PAID_BATCH_AUTHORIZED');
add('C001','첫 만남·선택 SIGNATURE 24개 유료 범위','OPEN',
 sourceOnly.filter(r=>r.kind==='SIGNATURE').length+'개 별도 승인 기록 필요');
add('C002','장면·기억 60개 유료 범위','OPEN',
 sourceOnly.filter(r=>r.kind==='SCENE'||r.kind==='MEMORY').length+'개 실제 이벤트/기억 증거 점검 필요');
add('C003','신규 96개 대사 문구의 최종 승인','OPEN',
 candidate.rows.length+'개 편집 후보, 확정 원문 및 API 대상 목록이 아님');
add('C004','재방문·작별·실패·축하·오디오 중재','OPEN',
 '정적 264만으로 모든 이벤트 충분하다는 근거 없음');
add('Q001','9그룹 발음·성격·속도 청취 승인','OPEN',
 'ElevenLabs ID 확인≠발음·음색 청취 검증');
add('Q002','녹음 MP3 포맷·키·해시·승인 검사','PARTIAL',
 'MP3 프레임/ID3 정합 검사 구현, 실제 ElevenLabs MP3 수신 전이라 실음원 검증 불가');
add('D001','배포·실기기·PWA 재생','OPEN',
 'PC 로컬 Chrome만 부분 검증, 배포/실기기 없음');
const afterRecording=new Set(['D001','Q002']);
const blockers=items.filter(i=>i.state!=='PASS'&&!afterRecording.has(i.id));
const releaseBlockers=items.filter(i=>i.state!=='PASS');
const report={
 schema_version:'TAKY_EXPLORER_CREW_PAID_VOICE_GO_NO_GO_V1',
 decision:blockers.length?'NO_GO':'GO',
 gate_purpose:'One correct batch, not repeat recording due to avoidable script/UI omissions',
 known_voice_groups:9,locked_lines:264,paid_scope_known:180,source_only:84,
 editorial_drafts:96,real_mp3:approved.clips.length,
 passed:items.filter(x=>x.state==='PASS').length,partial:items.filter(x=>x.state==='PARTIAL').length,
 blocking_open:blockers.length,post_recording_release_blocks:releaseBlockers.length,
 before_recording_blockers:blockers.map(x=>x.id),
 after_recording_blocks:[...afterRecording],
 unapproved_voice_generation_allowed:false,
 items
};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_PAID_VOICE_GO_NO_GO_CURRENT.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({decision:report.decision,passed:report.passed,partial:report.partial,
 block_count:blockers.length,blockers:blockers.map(x=>x.id),approved_mp3:report.real_mp3},null,2));
