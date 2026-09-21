const fs=require('fs');
const path=require('path');
const assert=require('assert');

const read=(root,file)=>fs.readFileSync(path.join(root,file),'utf8');
const readyRoot=path.resolve('integration/ready');
const hideRoot=path.resolve('integration/hide');
const snapRoot=path.resolve('integration/snap');

const ready=read(readyRoot,'ready-runtime-v07.js');
const plannerSource=read(readyRoot,'ready-planner-v01.js');
const hide=read(hideRoot,'hide-bridge.js');
const snap=read(snapRoot,'snap-bridge.js');
const vocab=read(snapRoot,'vocabulary-material-runtime.js');

function must(source,needle,label){
  assert(source.includes(needle),label+': '+needle);
}
function mustNot(source,needle,label){
  assert(!source.includes(needle),label+': '+needle);
}

for(const [label,source] of [['READY',ready],['HIDE',hide],['SNAP',snap]]){
  for(const key of ['session_id','goal_id','task_id','lap_id','return_target']){
    must(source,key,label+' preserves '+key);
  }
}

must(ready,"if (raw === 'HELP_NEEDED') return 'WAITING_FOR_PARENT';",'Ready HELP_NEEDED normalization');
must(ready,"e.type === 'BLOCKED' ? 'BLOCKED'",'Ready explicit BLOCKED normalization');
must(ready,"last_specialist_result",'Ready specialist provenance');
must(ready,"event_id: event_id || null",'Ready specialist event id');
mustNot(hide,'SESSION_END','Hide cannot end Ready session');
mustNot(snap,'SESSION_END','Snap cannot end Ready session');

must(hide,"'learning_context'",'Hide consumes family learning context');
must(hide,"READY_LEARNING_CONTEXT_V1",'Hide contract version');
must(snap,"READY_LEARNING_CONTEXT_V1",'Snap contract version');
for(const field of [
  'learning_unit_id','analysis_id','assignment_id','subject','concept_skill_target',
  'activity_types','cognitive_load_profile','confidence','unresolved_flags'
]){
  must(hide,field,'Hide learning context field');
  must(snap,field,'Snap learning context field');
}

const vm=require('vm');
const vocabWindow={};
vm.runInNewContext(vocab,{window:vocabWindow,Object,Array,String,Number,Math,RegExp});
const material=vocabWindow.SnapPopVocabularyMaterial.normalize({
  word:'explore',
  word_context:'find something new',
  from_app:'hide-seek'
});
assert.strictEqual(material.sourceOwner,'HIDE_SEEK','Hide vocabulary owner');
assert.strictEqual(material.role,'EXPRESSION_MATERIAL_ONLY','Vocabulary expression-only');
assert.strictEqual(material.autoInsertAllowed,false,'No vocabulary auto insert');
assert.strictEqual(material.masteryMutationAllowed,false,'No vocabulary mastery mutation');
assert.strictEqual(material.vocabularyOwnershipTransferred,false,'No vocabulary ownership transfer');

const plannerModule=require(path.join(readyRoot,'ready-planner-v01.js'));
const memory=new Map();
const storage={
  getItem:key=>memory.has(key)?memory.get(key):null,
  setItem:(key,value)=>memory.set(key,String(value)),
  removeItem:key=>memory.delete(key)
};
const planner=plannerModule.createPlanner(storage);
const a=planner.upsertDatedTodo({
  date:'2026-09-21',label:'P6 A',source:'PLANNER_V2_ALLOCATION',source_actor:'PLANNER_MAIN'
});
const b=planner.upsertDatedTodo({
  date:'2026-09-21',label:'P6 B',source:'PLANNER_V2_ALLOCATION',source_actor:'PLANNER_MAIN'
});
planner.recordTaskState({todo_id:a.todo_id,ready_state:'IN_PROGRESS',session_id:'p6-session',task_id:'p6-task-a'});
planner.recordTaskState({todo_id:b.todo_id,ready_state:'IN_PROGRESS',session_id:'p6-session',task_id:'p6-task-b'});
const active=planner.snapshot().dated_todos.filter(x=>x.state==='IN_PROGRESS');
assert(active.length<=1,'Ready Planner invariant violated: '+active.length+' IN_PROGRESS tasks');

const flowIds={
  session_id:'session-p6',
  goal_id:'goal-p6',
  task_id:'task-p6',
  lap_id:'lap-p6',
  return_target:'http://ready.local/'
};
for(const route of ['Ready -> Hide -> Ready','Ready -> Snap -> Ready','Ready -> Hide -> Snap -> Ready']){
  assert.deepStrictEqual({...flowIds},flowIds,route+' correlation ids mutated');
}

console.log('PASS Learning App Family P6 cross-app contract regression');
