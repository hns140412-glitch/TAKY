'use strict';
const assert=require('node:assert/strict'),fs=require('fs'),path=require('path');
const base='D:/Git PWA/TAKY/staging/crew_voice_20261012';
const read=n=>JSON.parse(fs.readFileSync(path.join(base,n),'utf8'));
const record=read('EXPLORER_CREW_RECORDING_EXECUTION_ORDER_20261013.json'),
  lines=read('EXPLORER_CREW_PRODUCER_LINE_LEDGER_20261013.json').rows,
  drafted=read('EXPLORER_CREW_MISSING_SCENARIO_DIALOGUES_DRAFT_20261013.json').rows,
  mock=read('mock_tts/EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json').clips;
const lookup=new Map(lines.map(r=>[r.script_key,r])),problems=[];
let checks=0;
function check(name,condition){checks++;if(!condition)problems.push(name)}
check('PRIMARY_264',lines.length===264);
check('DRAFT_96',drafted.length===96);
check('NO_DRAFT_IN_RUNTIME',drafted.every(r=>!lookup.has(r.candidate_key)));
check('PAID_AUTHORIZED_180',lines.filter(r=>r.production_permission==='R10_PAID_BATCH_AUTHORIZED').length===180);
check('SIGNATURE_SOURCE_ONLY_24',lines.filter(r=>r.kind==='SIGNATURE'&&r.production_permission!=='R10_PAID_BATCH_AUTHORIZED').length===24);
check('CONDITIONAL_EXTRA_60',lines.filter(r=>['MEMORY','SCENE'].includes(r.kind)&&r.production_permission!=='R10_PAID_BATCH_AUTHORIZED').length===60);
check('PILOT_12',record.pilot_ids.length===12&&new Set(record.pilot_ids).size===12);
check('PILOT_AUTHORIZED_ONLY',record.pilot_ids.every(k=>lookup.get(k)?.production_permission==='R10_PAID_BATCH_AUTHORIZED'));
check('PILOT_NINE_GROUPS',new Set(record.pilot_ids.map(k=>lookup.get(k).voice_family)).size===9);
check('MOCK_SOURCE_MATCH',mock.length===264&&mock.every(x=>{
 const line=lookup.get(x.key);
 return !!line&&x.text_sha256===line.text_sha256&&x.target_elevenlabs_voice_id===line.elevenlabs_voice_id
}));
for(const app of ['Ready & Set','Hide & Seek','Snap & Pop']){
 const dir='D:/Git PWA/'+app;
 const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
 check('APP_PICKER_SCRIPT_'+app,html.includes('explorer-crew-selection-preview-v1.js'));
 check('APP_24_CUTOUTS_'+app,lines.filter(x=>x.kind==='SIGNATURE').every(x=>
  fs.existsSync(path.join(dir,'characters/ui_cutouts',x.character_id+'.png'))));
}
const selection=read('EXPLORER_CREW_ACTUAL_SELECTION_COMMIT_BROWSER_QA_20261013.json');
check('CONSUMER_SELECTION_COMMIT',selection.status==='PASS');
const result={status:problems.length?'FAIL':'PASS_PREP_MATERIAL_INTEGRITY',checked:checks,problems,
 script_lines:264,authorized:180,signature_not_authorized:24,conditional_not_authorized:60,
 new_drafts_not_authorized:96,acoustic_pilot_order:12,actual_mp3:0,
 ready_e2e_open:true,provider_acoustic_approval_open:true};
fs.writeFileSync(path.join(base,'EXPLORER_CREW_PREPAID_PRODUCTION_QA_20261013.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));if(problems.length)process.exitCode=2;