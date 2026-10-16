'use strict';
/* TAKY Explorer Crew producer ledger from immutable scripts; no paid calls, no source mutation.
   Purpose: make recording inputs and actual consumption gaps explicit BEFORE recording. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const work=path.join(root,'staging','crew_voice_20261012');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const source=read(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'));
const cast=read(path.join(root,'CURRENT','EXPLORER_CREW_SCRIPT_VOICE_MATCH_CURRENT.json'));
const mock=read(path.join(work,'mock_tts','EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json'));
const approved=read(path.join(work,'EXPLORER_CREW_PLAYBACK_MANIFEST.json'));
const person=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/personality-source-board-v1.js');
const voiceStyle={
 VF01:{tone:'호기심 있고 경쾌한 모험가',direction:'발견 전 기대감을 짧게 올리고 문장 끝을 가볍게 마무리; 과장된 소리 지르기 금지'},
 VF02:{tone:'다정하고 차분한 동행자',direction:'아이의 대답을 기다리는 듯한 온기, 낮은 압박감; 교사식 평가 어조 금지'},
 VF03:{tone:'신중하고 관찰력 높은 탐구자',direction:'단서와 대비어를 명료하게, 생각하는 짧은 여백; 로봇식 단조로움 금지'},
 VF04:{tone:'든든하고 침착한 리더',direction:'안정적인 템포와 단호한 핵심어, 위압감 없는 격려'},
 VF05:{tone:'친근하고 발랄한 팀 동료',direction:'밝고 자연스러운 리듬, 문장 끝 과도한 상승 금지'},
 VF06:{tone:'따뜻하고 상상력 있는 발견가',direction:'발견 감정을 가볍게 살리고 잔잔하게 이어가기'},
 SP01:{tone:'침착한 인간형 전략·리더 동료',direction:'생각이 먼저 전달되는 자연스러운 성인형 대화; 캐릭터별 원문 차이를 살림'},
 SP02:{tone:'섬세한 인간형 관찰·공감 동료',direction:'세밀한 관찰과 낮은 긴장감, 말 사이 호흡; 감성 과장 금지'},
 SP03:{tone:'활기찬 인간형 행동·창의 동료',direction:'순간적 즐거움과 행동 유도, 과도한 고음·외침 금지'}
};
const intentDirection={
 ASK:'호기심을 던지고 답할 시간을 남김; 정답 공개하지 않음',
 HINT:'정답 유도나 압박 없이 단서만 제시; 중간의 의미 단어를 명료하게',
 ACKNOWLEDGE:'행동·발견을 인정하지만 성적·등급 평가처럼 말하지 않음',
 SIGNATURE:'첫 만남/선택 미리듣기의 짧은 대표 인사; 현재 재회에도 같은 음원 재사용됨',
 SCENE:'특정 Core6 학습 장면을 설명 대신 관찰·상상 쪽으로 연결',
 MEMORY:'실제 보존된 학습/관계 사건이 있을 때만 회상; 가짜 기억을 암시하는 자동 재생 금지'
};
const family=new Map(cast.voice_families.map(v=>[v.family,v]));
const mockByKey=new Map(mock.clips.map(x=>[x.key,x]));
const recorded=new Map(approved.clips.map(x=>[x.key,x]));
const errors=[],producer=[],counts={},matrix={};
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
for(const row of source.rows){
 const v=family.get(row.voice_family);
 const profile=person.get(row.character_id);
 const m=mockByKey.get(row.key);
 if(!v?.voice_id_verified||v.elevenlabs_voice_id!==row.voice_id||!profile||!voiceStyle[row.voice_family])errors.push('PERSONA_CAST_MISMATCH:'+row.key);
 if(sha(row.exact_text)!==row.text_sha256||!m||m.text_sha256!==row.text_sha256||
    m.target_elevenlabs_voice_id!==row.voice_id||m.exact_text!==row.exact_text)
    errors.push('TEXT_HASH_OR_MOCK_MISMATCH:'+row.key);
 if(row.kind==='SIGNATURE'&&profile?.signature!==row.exact_text)errors.push('SIGNATURE_SOURCE_DRIFT:'+row.key);
 const r=recorded.get(row.key);
 if(r&&(!['USER_APPROVED','LOCKED'].includes(r.status)||r.text_sha256!==row.text_sha256||
   r.voice_id!==row.voice_id||r.exact_text!==row.exact_text))errors.push('RECORDED_TEXT_OR_VOICE_DRIFT:'+row.key);
 const authorized=row.production_authority==='R10_USER_PAID_BATCH_AUTHORIZED';
 const cueType=row.kind==='LOCKED_INTENT'?row.intent:row.kind;
 const group=voiceStyle[row.voice_family];
 const qa={
   exact_script:'LOCKED_TEXT_UNCHANGED',
   voice_identity:'PROVIDER_VOICE_ID_LISTED__ACOUSTIC_APPROVAL_NOT_DEMONSTRATED',
   text_sha256:row.text_sha256,
   pronunciation_review:'NOT_LISTEN_VERIFIED',
   acting_review:'NOT_LISTEN_VERIFIED',
   mp3_hash:r?.audio_sha256||null,
   asset_status:r?'INDIVIDUAL_APPROVED_RECORDING':'TTS_MOCK_ONLY',
   app_e2e:'NOT_PROVEN_FOR_THIS_SPECIFIC_EVENT'
 };
 producer.push({
  script_key:row.key,character_id:row.character_id,character_name:profile.name_ko,
  personality_keywords:profile.keywords||[],approved_profile_source:profile.source,
  kind:row.kind,event_intent:row.intent,scene_id:row.scene_id||null,memory_event:row.memory_event||null,
  scope:row.scope,allowed_apps:row.allowed_app_contexts,
  source_authority:row.source,production_permission:authorized?'R10_PAID_BATCH_AUTHORIZED':'EXTRA_SOURCE_PAID_APPROVAL_PENDING',
  text_exact:row.exact_text,text_sha256:row.text_sha256,
  voice_family:row.voice_family,voice_design_name:v.provider_display_name,elevenlabs_voice_id:v.elevenlabs_voice_id,
  original_audio_file:row.file_relative_path,mock_audio_file:m?.relative_path||null,
  voice_cue:group.tone,group_directing:group.direction,line_directing:intentDirection[cueType],
  qa
 });
 counts[cueType]=(counts[cueType]||0)+1;
 matrix[row.scope]??={};matrix[row.scope][cueType]=(matrix[row.scope][cueType]||0)+1;
}
const missingEvents=[
 {event:'FIRST_MEET',existing_script:'SIGNATURE',status:'COVERED_AS_PREVIEW',count:24,note:'첫 만남 자체의 사건 맥락은 별도 검증 필요'},
 {event:'RETURN',existing_script:'SAME_SIGNATURE',status:'DIALOGUE_CONTEXT_GAP',count:0,note:'첫 만남 문구 반복; 재회 전용 대사 없음'},
 {event:'ASK',existing_script:'LOCKED_INTENT',status:'SCRIPTS_EXIST__APP_EVENT_TRACES_NOT_ALL_PROVEN',count:60,note:'MAIN 48+PLAY_CAMP Core6 12; 앱별 사용 이벤트 제한'},
 {event:'HINT',existing_script:'LOCKED_INTENT',status:'SCRIPTS_EXIST__APP_EVENT_TRACES_NOT_ALL_PROVEN',count:60,note:'학습 상태/힌트 요청 연결 부분별 미검증'},
 {event:'ACKNOWLEDGE',existing_script:'LOCKED_INTENT',status:'SCRIPTS_EXIST__APP_EVENT_TRACES_NOT_ALL_PROVEN',count:60,note:'성취/실패/중립 반응을 하나로 통합하면 맥락 오류 위험'},
 {event:'SCENE',existing_script:'CORE6_SCENE',status:'SCOPE_LIMITED',count:30,note:'IDEA/EMOTION/DESCRIPTION/VIEWPOINT/FINAL만 MAIN에서 허용'},
 {event:'MEMORY',existing_script:'MEMORY_CALLBACK',status:'EVIDENCE_ONLY',count:30,note:'실제 기억증거 기반으로만 호출, 일반 회상에 자동 사용 금지'},
 {event:'FAREWELL',existing_script:null,status:'CONTENT_MISSING',count:0,note:'탐험 종료/동행 종료/앱 종료 상황의 대사 없음'},
 {event:'RETRY_AFTER_FAILURE',existing_script:null,status:'CONTENT_MISSING',count:0,note:'오답 후 공감·재도전과 중립 ACK 구분 필요'},
 {event:'CELEBRATE',existing_script:null,status:'CONTENT_MISSING',count:0,note:'도감/업적/탐험 결과용 개별 축하 대사 확인되지 않음'},
 {event:'WAIT_OR_REST',existing_script:null,status:'CONTENT_MISSING_AND_MAY_BE_SILENT',count:0,note:'Ambient 대표행동은 침묵 우선; 필수 음성 여부 실제 UX 기준 판단'},
 {event:'COMPANION_CHANGED',existing_script:null,status:'EVENT_CONNECTION_UNVERIFIED',count:0,note:'동행 확정 후 인사·전환 음성 소비 증거 불충분'},
 {event:'DUO_OR_TEAM',existing_script:null,status:'CONTENT_MISSING_AND_MAY_BE_TEXT_ONLY',count:0,note:'Crew arbitration을 우회해 동시재생하지 말 것'}
];
if(producer.length!==264||new Set(producer.map(x=>x.script_key)).size!==264
 ||new Set(producer.map(x=>x.text_sha256)).size!==264)errors.push('SOURCE_264_UNIQUE_CONTRACT_FAILED');
const known=producer.filter(x=>x.production_permission==='R10_PAID_BATCH_AUTHORIZED');
const extras=producer.filter(x=>x.production_permission!=='R10_PAID_BATCH_AUTHORIZED');
if(known.length!==180||extras.length!==84||mock.clips.length!==264)errors.push('180_84_SCOPE_MISMATCH');
const report={
 schema_version:'TAKY_CREW_VOICE_PRODUCTION_PREFLIGHT_V2',
 status:errors.length?'FAIL':'SCRIPTS_INDEXED__NOT_RECORDING_READY',
 owner:'TAKY_SHARED_EXPLORER_CREW',recording_authorized_now:180,additional_source_only:84,
 total_known_lines:producer.length,voice_groups:family.size,characters:24,
 automatic_synthesis_allowed:false,existing_approved_mp3:approved.clips.length,
 voice_id_is_not_audition_approval:true,
 script_completeness:'PARTIAL_WITH_DOCUMENTED_MISSING_EVENTS',
 group_casting_stable:true,
 counts_by_intent:counts,counts_by_scope:matrix,
 life_cycle_coverage:missingEvents,errors,
 app_status:{
  HIDE_SEEK:'TAP_SELECTION_24_OF_24_BROWSER_MEDIA_PLAYING',
  SNAP_POP:'TAP_SELECTION_24_OF_24_BROWSER_MEDIA_PLAYING',
  READY_SET:'CARD_UI_AND_POPUP_RENDER; COMPLETE_BROWSER_MEDIA_PLAYING_NOT_PROVEN',
  PLAY_CAMP:'NOT_MODIFIED__CORE6_CONSUMPTION_NOT_CHECKED_IN_THIS_AUDIT'
 },
 open_items:[
 'READY_PICKER_MEDIA_PLAYING_E2E',
 'NATIVE_SELECTION_COMMIT_PERSISTENCE_AND_RETURN_EVENT',
 'AGE_AND_SCHOOL_STAGE_ACTUAL_UI_CONTEXT_NOT_HARDCODED',
 'EVENT_COVERAGE_FOR_HINT_ACK_RETRY_SUCCESS_FAREWELL',
 'RECONNECT_SPECIFIC_DIALOGUE_DECISION',
 '9_PROVIDER_VOICES_AUDITIONED_PER_GROUP_AND_HUMAN_SPECIAL_CADENCE',
 'TEST_264_CLIPS_BY_APP_EVENT_INSTEAD_OF_STANDALONE_AUDIO',
 'TTS_MOCK_TO_MP3_SWAP_IN_INSTALLED_APPS_TEST'
 ]
};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_PRODUCER_LINE_LEDGER_20261013.json'),JSON.stringify({schema_version:report.schema_version,rows:producer},null,2));
fs.writeFileSync(path.join(work,'EXPLORER_CREW_PRODUCTION_READINESS_AUDIT_20261013.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({status:report.status,total:producer.length,authorized:known.length,extras:extras.length,voice_groups:family.size,by_intent:counts,errors,coverage_events:missingEvents.map(x=>[x.event,x.status])},null,2));
if(errors.length)process.exitCode=2;