'use strict';
const assert=require('assert');
const Policy=require('./hide-vocabulary-routing-policy.js');

const e=(id,day,{mode='TRACE',correct=true,assisted=false,confusion=null,weakness=null,spaced=false}={})=>({
  event_id:id+'-'+day+'-'+mode,
  observed_at:day+'T09:00:00.000Z',
  member_id:'A',subject:'english',concept_skill_target:'vocabulary',
  learning_target_id:id,evidence_type:'MEMORY_RETRIEVAL_EVIDENCE',
  source_app:'hide-seek',instrument_version:'HIDE_V1',
  interaction_mode:mode,assisted,assistance:assisted?'ASSISTED':'UNASSISTED',
  verified_outcome:null,
  memory:{item_signal:{correct,confusion,weakness,spaced_evidence:spaced,mode}}
});

{
 const p=Policy.derive({evidence:[],current_word_ids:['n1'],past_word_ids:['p1']});
 assert.equal(p.word_policies.find(x=>x.learning_target_id==='n1').recommended_mode,'TRACE');
 assert.equal(p.past_word_mix.past_word_share,2/3);
 assert.equal(Policy.validate(p).ok,true);
}
{
 const p=Policy.derive({
  evidence:[
    e('n1','2026-10-01',{mode:'TRACE',correct:true}),
    e('n1','2026-10-02',{mode:'RECALL',correct:true,spaced:true}),
    e('n2','2026-10-01',{mode:'TRACE',correct:true}),
    e('n2','2026-10-02',{mode:'RECALL',correct:true,spaced:true}),
    e('n3','2026-10-01',{mode:'TRACE',correct:true}),
    e('n3','2026-10-02',{mode:'RECALL',correct:true,spaced:true}),
    e('n4','2026-10-01',{mode:'TRACE',correct:true}),
    e('n4','2026-10-02',{mode:'RECALL',correct:true,spaced:true})
  ],
  current_word_ids:['n1','n2','n3','n4'],past_word_ids:['p1','p2']
 });
 assert.equal(p.current_set_signal.level,'STRONG');
 assert.equal(p.past_word_mix.past_word_share,0.75);
 assert.ok(p.delayed_recall_queue.length>=4);
}
{
 const p=Policy.derive({
  evidence:[
    e('n1','2026-10-02',{mode:'TRACE',correct:false}),
    e('n2','2026-10-02',{mode:'LINK',correct:true,confusion:'accept/except'}),
    e('n3','2026-10-02',{mode:'CORE',correct:false,weakness:'ORTHOGRAPHIC'})
  ],
  current_word_ids:['n1','n2','n3'],past_word_ids:['p1']
 });
 assert.equal(p.current_set_signal.level,'WEAK');
 assert.equal(p.past_word_mix.past_word_share,0.50);
 assert.equal(p.word_policies.find(x=>x.learning_target_id==='n2').recommended_mode,'LINK');
 assert.equal(p.word_policies.find(x=>x.learning_target_id==='n3').recommended_mode,'CORE');
}
{
 const p=Policy.derive({
  evidence:[e('n1','2026-10-02',{mode:'RECALL',correct:true,assisted:true})],
  current_word_ids:['n1']
 });
 const w=p.word_policies[0];
 assert.equal(w.recommended_mode,'RECALL');
 assert.equal(w.memory_state,'ASSISTED_ONLY');
 assert.equal(w.delayed_recall.kind,'AFTER_INTERVENING_ITEMS');
}
console.log('hide-vocabulary-routing-policy.test.js PASS');
