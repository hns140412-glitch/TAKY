import fs from 'node:fs';
import path from 'node:path';

const root=process.cwd();
const readyDir=process.env.READY_DIR||path.join(root,'_integration/Ready-Set');
const hideDir=process.env.HIDE_DIR||path.join(root,'_integration/Hide-Seek');
const snapDir=process.env.SNAP_DIR||path.join(root,'_integration/Snap-Pop');

const read=(dir,file)=>fs.readFileSync(path.join(dir,file),'utf8');
const contract=JSON.parse(fs.readFileSync(path.join(root,'MASTER/READY_LEARNING_CONTEXT_V1.json'),'utf8'));
const ready=read(readyDir,'ready-runtime-v07.js');
const planner=read(readyDir,'ready-planner-v01.js');
const hide=read(hideDir,'hide-bridge.js');
const snap=read(snapDir,'snap-bridge.js');
const snapLearning=read(snapDir,'learning-context-runtime.js');
const vocab=read(snapDir,'vocabulary-material-runtime.js');

function ok(name,value){
  if(!value) throw new Error('FAIL '+name);
  console.log('PASS '+name);
}
function hasAll(text,values){return values.every(v=>text.includes(v));}

ok('central-version',contract.contract_version==='READY_LEARNING_CONTEXT_V1');
ok('central-owner',contract.owner==='LEARNING_APP_FAMILY');

for(const field of contract.required_fields){
  ok('ready-produces-'+field,ready.includes(field));
  ok('hide-consumes-'+field,hide.includes(field));
  ok('snap-consumes-'+field,snap.includes(field)&&snapLearning.includes(field));
}
ok('ready-encodes-central-version',ready.includes("contract_version: 'READY_LEARNING_CONTEXT_V1'"));
ok('hide-fail-closed-version',hide.includes("value.contract_version !== 'READY_LEARNING_CONTEXT_V1'"));
ok('snap-fail-closed-version',snap.includes("value.contract_version!=='READY_LEARNING_CONTEXT_V1'"));

const forbidden=['role','permission','planner_authority','allocation_authority','dated_todo_authority','hanja_grade_inference','hanja_level_inference'];
for(const field of forbidden){
  ok('no-ready-authority-field-'+field,!ready.includes('learning_context.'+field));
  ok('no-hide-authority-consumption-'+field,!hide.includes('value.'+field));
  ok('no-snap-authority-consumption-'+field,!snap.includes('value.'+field));
}

const transportIds=['session_id','goal_id','task_id','lap_id'];
for(const id of transportIds){
  ok('ready-to-specialist-'+id,ready.includes(`url.searchParams.set('${id}'`));
  ok('hide-return-'+id,hide.includes(`url.searchParams.set('${id}'`));
  ok('hide-to-snap-'+id,hide.includes(`url.searchParams.set('${id}'`));
  ok('snap-return-'+id,snap.includes(`url.searchParams.set('${id}'`));
}
ok('ready-sends-return-target',ready.includes("url.searchParams.set('return_target'"));
ok('hide-preserves-return-target-to-snap',hide.includes("url.searchParams.set('return_target', context.return_target)"));
ok('snap-consumes-return-target',snap.includes("'return_target'")&&snap.includes('context.return_target'));

ok('help-needed-to-parent',ready.includes("raw === 'HELP_NEEDED') return 'WAITING_FOR_PARENT'")&&ready.includes("e.type === 'HELP_NEEDED' ? 'WAITING_FOR_PARENT'"));
ok('explicit-blocked-remains-blocked',ready.includes("e.type === 'BLOCKED' ? 'BLOCKED'"));
ok('specialist-event-id-preserved',ready.includes('last_specialist_result')&&ready.includes('event_id: event_id || null'));

ok('planner-at-most-one-runtime-check',ready.includes('activePlannerTodos.length <= 1'));
ok('planner-single-progress-ownership',planner.includes("mapped==='IN_PROGRESS'")&&planner.includes('SESSION_OWNERSHIP_CONFLICT'));

const inboundStart=ready.indexOf('function applyInboundResult');
const inboundEnd=ready.indexOf('function consumeReturnQuery',inboundStart);
const inbound=ready.slice(inboundStart,inboundEnd);
ok('specialist-return-does-not-end-ready-session',!inbound.includes('SESSION_END')&&!inbound.includes('SESSION_ENDED')&&!inbound.includes('finalizeSession'));
ok('hide-specialist-no-session-end',!hide.includes("'SESSION_END'")&&!hide.includes("'SESSION_ENDED'"));
ok('snap-specialist-no-session-end',!snap.includes("'SESSION_END'")&&!snap.includes("'SESSION_ENDED'"));

ok('hide-context-is-resolved-only',hide.includes('function learningContext()')&&hide.includes('decodeLearningContext(getContext().learning_context)'));
ok('hide-does-not-infer-hanja-grade',!hide.includes('hanja_grade')&&!hide.includes('hanja_level'));
ok('hide-memory-advisory-boundary',hide.includes("specialistAuthority: 'SPECIALIST_MEMORY_ADVISORY_ONLY'"));

ok('vocabulary-source-owner',vocab.includes('sourceOwner'));
ok('vocabulary-expression-material-only',vocab.includes('role:"EXPRESSION_MATERIAL_ONLY"'));
ok('vocabulary-no-auto-insert',vocab.includes('autoInsertAllowed:false'));
ok('vocabulary-no-mastery-mutation',vocab.includes('masteryMutationAllowed:false'));
ok('vocabulary-no-ownership-transfer',vocab.includes('vocabularyOwnershipTransferred:false'));

console.log('LEARNING_APP_FAMILY_CROSS_APP_CONTRACT_PASS');
