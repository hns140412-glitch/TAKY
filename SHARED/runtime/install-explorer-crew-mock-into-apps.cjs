'use strict';
/* Makes app-local non-deployable UI consumption bundle from TAKY central sources.
   Additive HTML scripts, no alteration to existing crew character logic or generic TTS. */
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const repo=path.resolve(__dirname,'../..'),work=path.join(repo,'staging/crew_voice_20261012');
const data=path.join(work,'mock_tts'),runt=__dirname;
const apps=[
 {app:'HIDE_SEEK',name:'Hide & Seek'},
 {app:'SNAP_POP',name:'Snap & Pop'},
 {app:'READY_SET',name:'Ready & Set'}
];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const registry=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PRERECORDING_ROUTING_264.json')));
const mock=JSON.parse(fs.readFileSync(path.join(data,'EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json')));
const approved=JSON.parse(fs.readFileSync(path.join(work,'EXPLORER_CREW_PLAYBACK_MANIFEST.json')));
if(registry.rows.length!==264||mock.clips.length!==264||registry.voice_groups!==9)throw Error('INPUT_MISMATCH');
const mainMocks=mock.clips.filter(x=>x.scope==='MAIN_CREW');
if(mainMocks.length!==228)throw Error('MAIN_VOICE_MOCK_SCOPE_NOT_228');
const cutoutSource='D:/Git PWA/Hide & Seek/characters/ui_cutouts';
const cutoutIds=[...new Set(registry.rows.filter(x=>x.kind==='SIGNATURE').map(x=>x.character_id))];
if(cutoutIds.length!==24)throw Error('CANONICAL_CUTOUT_ROSTER_NOT_24');
const written=[],appReports=[];
const preapproved=approved.clips.filter(x=>x.scope==='MAIN_CREW');
for(const a of preapproved){
 const row=registry.rows.find(r=>r.key===a.key);
 if(!row||row.voice_id!==a.voice_id||row.text_sha256!==a.text_sha256)
  throw Error('PRECHECK_APPROVED_CAST_OR_TEXT_DRIFT:'+a.key);
 const from=path.join(work,row.file_relative_path);
 if(!fs.existsSync(from)||sha(fs.readFileSync(from))!==a.audio_sha256)
  throw Error('PRECHECK_APPROVED_MP3_FILE_MISSING_OR_HASH_WRONG:'+a.key);
 for(const app of apps){
  const folder=path.resolve('D:/Git PWA/'+app.name);
  const relative=a.url.replace(/^\.\//,'').split('?')[0];
  const target=path.resolve(folder,relative);
  if(!target.startsWith(path.join(folder,'audio')+path.sep)||!target.endsWith('.mp3'))
   throw Error('PRECHECK_APPROVED_APP_DESTINATION_INVALID:'+a.key);
  if(fs.existsSync(target)&&sha(fs.readFileSync(target))!==a.audio_sha256)
   throw Error('PRECHECK_APPROVED_APP_ASSET_CONFLICT:'+app.app+':'+a.key);
 }
}
function writeManaged(dest,content){
 fs.mkdirSync(path.dirname(dest),{recursive:true});
 const bytes=Buffer.isBuffer(content)?content:Buffer.from(content,'utf8');
 if(fs.existsSync(dest)&&sha(fs.readFileSync(dest))===sha(bytes))return 'unchanged';
 fs.writeFileSync(dest,bytes);written.push(dest);return 'updated';
}
function emitJS(varname,obj){
 return 'globalThis.'+varname+'='+JSON.stringify(obj)+';\n';
}
for(const app of apps){
 const dir='D:/Git PWA/'+app.name,integrated=path.join(dir,'explorer-crew-voice');
 if(!fs.existsSync(path.join(dir,'index.html')))throw Error('APP_INDEX_MISSING:'+app.name);
 const htmlPath=path.join(dir,'index.html');
 const oldHtml=fs.readFileSync(htmlPath,'utf8');
 const close=oldHtml.lastIndexOf('</body>');
 if(close<0)throw Error('APP_HTML_MISSING_BODY:'+app.name);
 // Avoid editing app.js or touching existing study/general speech.
 const suffix=[
  '<!-- TAKY Explorer Crew canonical-source TTS mock consumer v1: standalone, no generic speech takeover -->',
  ...(app.app==='READY_SET'?[
   'personality-source-board-v1.js','personality-registry-v2.js','dialogue-script-authority-v1.js','dialogue-personality-v1.js'
  ].map(f=>'<script src="./explorer-crew-voice/'+f+'"></script>'):[]),
  '<script src="./explorer-crew-voice/data-registry.js"></script>',
  '<script src="./explorer-crew-voice/data-mock.js"></script>',
  '<script src="./explorer-crew-voice/data-approved.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-dialogue-voice-bridge-v1.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-tts-mock-switch-v1.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-voice-event-adapter-v1.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-learning-voice-route-v1.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-learner-voice-context-v1.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-content-owner-v1.js"></script>',
  '<script src="./explorer-crew-voice/explorer-crew-selection-preview-v1.js"></script>',
  ...(app.app==='READY_SET'?['<script src="./explorer-crew-voice/ready-explorer-intro-canonical-v1.js"></script>']:[]),
  '<script src="./explorer-crew-voice/explorer-crew-ui-voice-integration-v1.js" data-app="'+app.app+'"></script>',
 ].join('\n');
 // Reconcile each declared dependency, not only the original one-time hook.
 // The actual app HTML may predate newly added modules (e.g. learner context).
 const dependencies=suffix.split('\n').filter(line=>line.startsWith('<script '));
 const finalHook=dependencies.find(line=>line.includes('explorer-crew-ui-voice-integration-v1.js'));
 let nextHtml=oldHtml;
 if(!oldHtml.includes('explorer-crew-ui-voice-integration-v1.js')){
   nextHtml=oldHtml.slice(0,close)+suffix+'\n'+oldHtml.slice(close);
 }else{
   if(!finalHook||!nextHtml.includes(finalHook))throw Error('APP_INTEGRATION_HOOK_TAMPERED:'+app.name);
   const absent=dependencies.filter(line=>!nextHtml.includes(line));
   nextHtml=nextHtml.replace(finalHook,absent.join('\n')+(absent.length?'\n':'')+finalHook);
 }
 for(const line of dependencies){
   if(nextHtml.split(line).length!==2)throw Error('MISSING_OR_DUPLICATE_AUDIO_DEPENDENCY:'+app.name+':'+line);
 }
 if(nextHtml!==oldHtml)writeManaged(htmlPath,nextHtml);
 const sources=[
 ['explorer-crew-dialogue-voice-bridge-v1.js','explorer-crew-dialogue-voice-bridge-v1.js'],
 ['explorer-crew-tts-mock-switch-v1.js','explorer-crew-tts-mock-switch-v1.js'],
 ['explorer-crew-voice-event-adapter-v1.js','explorer-crew-voice-event-adapter-v1.js'],
 ['explorer-crew-learning-voice-route-v1.js','explorer-crew-learning-voice-route-v1.js'],
 ['explorer-crew-learner-voice-context-v1.js','explorer-crew-learner-voice-context-v1.js'],
 ['explorer-crew-content-owner-v1.js','explorer-crew-content-owner-v1.js'],
 ['explorer-crew-selection-preview-v1.js','explorer-crew-selection-preview-v1.js'],
 ...(app.app==='READY_SET'?[['ready-explorer-intro-canonical-v1.js','ready-explorer-intro-canonical-v1.js']]:[]),
 ['explorer-crew-ui-voice-integration-v1.js','explorer-crew-ui-voice-integration-v1.js']
 ];
 for(const [from,to] of sources)writeManaged(path.join(integrated,to),fs.readFileSync(path.join(runt,from)));
 if(app.app==='READY_SET'){
  const canonical='D:/Git PWA/Hide & Seek/vendor/taky/explorer-crew';
  for(const f of ['personality-source-board-v1.js','personality-registry-v2.js','dialogue-script-authority-v1.js','dialogue-personality-v1.js']){
    writeManaged(path.join(integrated,f),fs.readFileSync(path.join(canonical,f)));
  }
 }
 let cutoutsValidated=0,cutoutsCopied=0;
 for(const id of cutoutIds){
  const source=path.join(cutoutSource,id+'.png'),target=path.join(dir,'characters/ui_cutouts',id+'.png');
  if(!fs.existsSync(source))throw Error('MISSING_APPROVED_CHARACTER_CUTOUT:'+id);
  const bytes=fs.readFileSync(source);
  if(bytes.length<200||bytes.toString('hex',0,8)!=='89504e470d0a1a0a')throw Error('INVALID_CUTOUT_PNG:'+id);
  const existing=fs.existsSync(target)?fs.readFileSync(target):null;
  if(existing&&sha(existing)!==sha(bytes))throw Error('APP_CHARACTER_CUTOUT_AUTHORITY_CONFLICT:'+app.name+':'+id);
  if(!existing){writeManaged(target,bytes);cutoutsCopied++}
  cutoutsValidated++;
 }
 const bundleApproved={...approved,clips:approved.clips.filter(x=>x.scope==='MAIN_CREW')};
 writeManaged(path.join(integrated,'data-registry.js'),emitJS('TakyCrewVoiceRegistry',registry));
 writeManaged(path.join(integrated,'data-mock.js'),emitJS('TakyCrewMockManifest',mock));
 let copied=0;
 for(const row of mainMocks){
  const src=path.join(data,row.relative_path),target=path.join(dir,row.relative_path);
  const bytes=fs.readFileSync(src);
  if(sha(bytes)!==row.wav_sha256)throw Error('CENTRAL_MOCK_SOURCE_CHANGED:'+row.key);
  if(!fs.existsSync(target)||sha(fs.readFileSync(target))!==row.wav_sha256){
   writeManaged(target,bytes);copied++;
  }
 }
 for(const a of bundleApproved.clips){
  const row=registry.rows.find(r=>r.key===a.key);if(!row)throw Error('APPROVED_SCRIPT_UNKNOWN');
  const src=path.join(work,row.file_relative_path);
  if(!fs.existsSync(src)||sha(fs.readFileSync(src))!==a.audio_sha256)throw Error('BAD_APPROVED_SOURCE');
  const dest=path.join(dir,a.url.replace(/^\.\//,'').split('?')[0]);
  writeManaged(dest,fs.readFileSync(src));
 }
 // Only publish the newly active approval manifest after all matching files are present.
 writeManaged(path.join(integrated,'data-approved.js'),emitJS('TakyCrewApprovedManifest',bundleApproved));
 appReports.push({app_id:app.app,html_hook:true,source_scripts:app.app==='READY_SET'?12:8,
 mock_slots:mainMocks.length,copied_wav:copied,cutouts_validated:cutoutsValidated,cutouts_copied:cutoutsCopied,approved_mp3:bundleApproved.clips.length});
}
const out={status:'APP_LOCAL_AUDIO_CONSUMERS_PACKAGED',apps:appReports,
 written_files:written.length,source_registry:264,no_play_camp_repo_changes:true,
 note:'Real UI browser test required; script registration and asset copying alone is not audio E2E.'};
fs.writeFileSync(path.join(work,'EXPLORER_CREW_APP_BUNDLE_REPORT_20261013.json'),JSON.stringify(out,null,2));
console.log(JSON.stringify(out,null,2));
