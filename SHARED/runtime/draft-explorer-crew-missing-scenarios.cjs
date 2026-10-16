'use strict';
/* Candidate-only extension. These are editorial suggestions, not authority, runtime lines, or permission to synthesize. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),work=path.join(root,'staging/crew_voice_20261012');
const base=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json'),'utf8'));
const board=require('D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew/personality-source-board-v1.js');
const slots=new Map(base.rows.filter(x=>x.kind==='SIGNATURE').map(x=>[x.character_id,x]));
const draft={
 dubi:['어, 또 왔네! 이번에는 어떤 단서를 발견할까?','이제 돌아갈 시간이야? 다음 단서도 기대할게!','잠깐, 다른 쪽을 살펴보면 재미있는 게 보일지도 몰라.','네가 직접 찾아냈구나! 나도 덩달아 신나는걸!'],
 lori:['다시 만나서 반가워. 오늘은 어떤 마음으로 시작할까?','오늘도 함께해 줘서 고마워. 편안히 쉬어.','괜찮아. 지금까지 해본 것도 소중한 단서야.','스스로 해낸 순간이네. 네가 정말 기뻤으면 좋겠어.'],
 ink:['다시 왔구나. 지난번과 달라진 점이 있을까?','오늘 발견한 단서는 잘 남겨둘게. 다음에 보자.','어디서 달라졌는지 한 군데만 다시 관찰해 보자.','좋아, 네 관찰이 멋진 발견으로 이어졌어.'],
 nova:['돌아왔구나! 오늘도 새로운 도전이 기다리고 있어!','오늘은 여기까지! 다음 도전에서 또 만나자!','한 번 더 시도해 보자. 다른 순서로 해보면 어떨까?','와, 해냈어! 네 도전이 빛났어!'],
 take:['다시 만났네. 오늘 할 일을 하나씩 살펴보자.','수고했어. 남은 건 다음에 차근차근 해보자.','서두르지 말고 순서부터 다시 맞춰보자.','한 단계씩 완성했네. 침착하게 잘 이어 왔어.'],
 zero:['어서 와! 다시 우리의 리듬을 찾아볼까?','오늘의 박자는 여기까지. 다음에 또 들려줘!','잠깐 박자를 바꾸듯 방법을 바꿔보자.','좋아! 네가 만든 멋진 리듬이야!'],
 'guide-07':['반가워! 오늘은 어떤 작은 빛이 길을 알려줄까?','오늘 찾은 빛을 기억하며 다음 숲에서 만나자.','작은 신호부터 다시 살펴보면 길이 보일 거야.','네가 작은 빛을 발견했구나. 정말 반짝이는 순간이야.'],
 'guide-08':['돌아왔네! 새 지도를 펼쳐서 다음 길을 찾아볼까?','오늘 지나온 길을 지도에 남기자. 다음에 또 보자!','길이 막혔으면 다른 방향으로 한 발 가보자.','우와! 네가 직접 길을 찾아냈어!'],
 'guide-09':['다시 만났구나. 새로운 관찰 기록을 남겨볼까?','오늘의 관찰 노트는 여기까지. 다음에 이어 쓰자.','기록을 다시 보면 놓친 단서가 보일 수도 있어.','좋은 발견이야. 오늘 기록에 꼭 남겨두자.'],
 'guide-10':['다시 만나 반가워! 새로운 이야기를 서로 전해볼까?','오늘은 인사를 나누고, 다음 바람이 불 때 만나자.','다른 친구의 생각도 들어보면 길이 열릴 거야.','네 생각이 모두를 이어 줬어. 참 멋진 소통이었어.'],
 'guide-11':['잘 돌아왔어. 오늘도 필요한 도구부터 살펴보자.','도구를 잘 정리했네. 다음 제작에서 만나자.','연결이 잘 안 되면 부품 하나씩 확인해 보자.','차근차근 만든 결과물이야. 아주 튼튼한 생각이었어.'],
 'guide-12':['다시 만나서 행복해! 오늘은 마음이 좀 어때?','오늘도 함께 웃어서 좋았어. 편히 쉬고 또 만나자.','괜찮아, 쉬었다가 다시 해도 좋아. 내가 곁에 있을게.','네가 해냈네! 그 기쁨을 함께 나눠도 될까?'],
 'guide-13':['다시 왔구나. 오늘도 우리 속도로 천천히 가자.','오늘은 여기서 쉬자. 좋은 길은 또 찾을 수 있어.','급하지 않아. 한 걸음씩 다른 길을 찾아보자.','차분히 살핀 덕분에 좋은 길을 찾았어.'],
 'guide-14':['헤헤, 다시 왔네! 이번엔 뭘 실험해 볼까?','아쉽지만 오늘 놀이는 끝! 다음에 또 도전하자!','앗, 예상과 다르네! 그럼 다른 방법을 시험해 보자.','야호! 해보니까 진짜 되는걸!'],
 'guide-15':['어서 와! 오늘은 어떤 변화가 기다릴까?','오늘 모습은 여기까지! 다음엔 새로운 모습으로 만나자.','상황이 바뀌었네. 우리 방법도 조금 바꿔볼까?','바뀐 상황에 잘 맞췄어. 멋진 적응이었어!'],
 'guide-16':['다시 만나 반가워! 오늘도 모두 함께 움직이자.','함께여서 즐거웠어. 다음에도 같이 가자!','혼자 막힐 땐 함께 다른 방법을 찾아보자.','우리가 힘을 모아 해냈어! 너의 역할이 컸어.'],
 'guide-17':['다시 왔군. 숨어 있는 단서를 또 찾아볼까?','오늘 숨은 길은 여기까지야. 다음에 더 찾아보자.','아직 안 보인다면 조금 더 깊이 들여다보자.','끝까지 찾아냈네. 네 끈기가 빛났어.'],
 'guide-18':['반가워. 오늘은 어떤 좋은 기억을 담아볼까?','오늘의 좋은 순간을 마음에 담고 쉬자.','지난 순서를 되짚으면 다음 방법이 떠오를지도 몰라.','기억에 남을 멋진 순간이야. 함께해 줘서 고마워.'],
 'guide-19':['다시 만났네. 오늘 탐험의 방향을 함께 정해보자.','오늘의 탐험은 여기까지. 다음 길에서 만나자.','계획을 조금 바꿔보자. 다른 길도 분명 있을 거야.','방향을 잘 선택했어. 네 판단으로 길이 열렸네.'],
 'guide-20':['돌아왔구나. 오늘은 어떤 차이를 발견할 수 있을까?','오늘 남긴 기록을 간직할게. 다음에 만나자.','조용히 다시 보면 놓친 부분이 보일 수도 있어.','그 차이를 발견했구나. 정말 섬세한 관찰이야.'],
 'guide-21':['왔구나! 오늘은 어떤 재미난 미션에 도전할까?','오늘은 여기까지! 에너지를 채우고 또 만나자!','괜찮아! 이번엔 새로운 작전으로 뛰어들어 보자!','해냈다! 역시 팀워크가 최고야!'],
 'guide-22':['다시 만나 반가워. 오늘 마음은 괜찮아?','오늘도 함께해서 좋았어. 편안한 시간 보내.','잠깐 쉬었다 해도 괜찮아. 네 마음부터 살펴보자.','네가 해낸 일이 참 소중해. 기쁨을 오래 기억하자.'],
 'guide-23':['돌아왔네. 오늘 문제의 핵심부터 함께 짚어볼까?','오늘의 계획은 정리했어. 다음에 이어 보자.','방법이 안 맞으면 조건부터 다시 확인해 보자.','좋은 해결이었어. 네 전략이 제대로 통했네.'],
 'guide-24':['또 만나네! 오늘은 어떤 재미난 걸 만들어 볼까?','오늘의 특별한 순간은 간직했어. 다음에 또 놀자!','앗, 뜻대로 안 됐어? 새로운 아이디어를 하나 붙여보자!','정말 재미있는 결과야! 네 상상이 반짝였어!']
};
const categories=['RETURN','FAREWELL','RETRY_AFTER_FAILURE','CELEBRATE'];
const rows=[],errors=[];
const texts=new Set(base.rows.map(x=>x.exact_text));
for(const [id,lines] of Object.entries(draft)){
 const profile=board.get(id),signature=slots.get(id);
 if(!profile||!signature||lines.length!==4)errors.push('SOURCE_CHARACTER_MISMATCH:'+id);
 for(let n=0;n<lines.length;n++){
  const text=lines[n],event=categories[n];
  if(texts.has(text)||!text||text.length>95)errors.push('DUPLICATE_OR_BAD_CANDIDATE:'+id+':'+event);
  texts.add(text);
  rows.push({candidate_key:'CANDIDATE:'+id+':'+event+':0',
    character_id:id,character_name:profile.name_ko,personality_keywords:profile.keywords,
    voice_family:signature.voice_family,verified_elevenlabs_voice_id:signature.voice_id,
    event,exact_candidate_text:text,text_sha256:require('crypto').createHash('sha256').update(text).digest('hex'),
    status:'EDITORIAL_DRAFT__NOT_USER_APPROVED',
    audio_status:'NOT_RECORDED',synthesizer_permission:'NOT_AUTHORIZED',
    app_consumer_status:'NOT_CONNECTED',source:'TAKY_SCRIPT_EXTENSION_CANDIDATE_20261013'});
 }
}
if(rows.length!==96||new Set(rows.map(x=>x.candidate_key)).size!==96)errors.push('CANDIDATE_SCOPE_NOT_96');
const output={
 schema_version:'TAKY_CREW_SCRIPT_EXTENSIONS_EDITORIAL_DRAFT_V1',
 source_notice:'Original 264 texts and R10 authority remain untouched. These are new editorial drafts for recording scope consideration, not approved lines.',
 status:errors.length?'FAIL':'CANDIDATES_PREPARED_NOT_APPROVED',existing_locked:264,candidate_count:rows.length,
 per_event:categories.reduce((o,k)=>(o[k]=rows.filter(x=>x.event===k).length,o),{}),
 estimated_additional_total_characters:rows.reduce((n,r)=>n+r.exact_candidate_text.length,0),
 errors,rows
};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_MISSING_SCENARIO_DIALOGUES_DRAFT_20261013.json'),JSON.stringify(output,null,2));
console.log(JSON.stringify({status:output.status,counts:output.per_event,chars:output.estimated_additional_total_characters,errors},null,2));
if(errors.length)process.exitCode=2;