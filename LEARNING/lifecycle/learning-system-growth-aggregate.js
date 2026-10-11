'use strict';

const crypto=require('node:crypto');
const GrowLineage=require('./grow-lineage-packet.js');
const clean=v=>String(v??'').trim();

function hashRef(value){
  return 'agg:'+crypto.createHash('sha256').update(clean(value)).digest('hex').slice(0,16);
}

function aggregate(rows=[],options={}){
  const minMembers=Math.max(3,Number(options.min_members)||3);
  const minVerified=Math.max(minMembers,Number(options.min_verified_outcomes)||6);
  const normalized=(rows||[]).filter(x=>x&&typeof x==='object').map(x=>({
    member_ref:clean(x.member_id||x.member_ref),
    subject:clean(x.subject).toLowerCase(),
    target:clean(x.concept_skill_target).toLowerCase(),
    verified_outcomes:Number(x.verified_outcomes||x.verified_outcome_count||0),
    success:Number(x.success||x.success_count||0),
    failure:Number(x.failure||x.failure_count||0),
    mining_candidates:Number(x.mining_candidates||x.mining_candidate_count||0)
  })).filter(x=>x.member_ref&&x.subject&&x.target);

  const groups=new Map();
  for(const row of normalized){
    const key=row.subject+'::'+row.target;
    const g=groups.get(key)||{subject:row.subject,target:row.target,members:new Set(),verified:0,success:0,failure:0,mining:0};
    g.members.add(row.member_ref);
    g.verified+=row.verified_outcomes;
    g.success+=row.success;
    g.failure+=row.failure;
    g.mining+=row.mining_candidates;
    groups.set(key,g);
  }

  const candidates=[];
  for(const [key,g] of groups){
    if(g.members.size<minMembers||g.verified<minVerified)continue;
    const successRate=g.verified?g.success/g.verified:0;
    const direction=g.failure>g.success?'REVIEW_RECOVERY_STRATEGY':'REVIEW_PRESERVE_OR_ADVANCE_STRATEGY';
    const aggregateEvidenceRef='AGGREGATE_EVIDENCE:'+hashRef(
      [key,g.members.size,g.verified,g.success,g.failure,g.mining].join('|')
    );
    const event=GrowLineage.makeEvent({
      grow_domain:'LEARNING_GROW',
      stage:'GROWTH',
      producer:'learning-system-growth-aggregate',
      source_ref:'LEARNING_SYSTEM_AGGREGATE:'+hashRef(key+'|'+g.members.size+'|'+g.verified),
      parent_refs:[aggregateEvidenceRef],
      authority:'LEARNING_SYSTEM_GROWTH_CANDIDATE_ONLY',
      payload:{
        scope_kind:'SYSTEM_AGGREGATE',
        subject:g.subject,
        concept_skill_target:g.target,
        member_count:g.members.size,
        verified_outcome_count:g.verified,
        success_count:g.success,
        failure_count:g.failure,
        success_rate:Number(successRate.toFixed(4)),
        mining_candidate_count:g.mining,
        suggested_review:direction,
        strategy_change_authorized:false
      }
    });
    candidates.push({
      scope_key:key,
      member_count:g.members.size,
      verified_outcome_count:g.verified,
      suggested_review:direction,
      promotion_authorized:false,
      grow_lineage_event:event
    });
  }
  return {
    ok:true,
    candidate_count:candidates.length,
    min_members:minMembers,
    min_verified_outcomes:minVerified,
    privacy:'NO_MEMBER_IDENTIFIERS_IN_OUTPUT_PAYLOAD',
    strategy_change_authorized:false,
    candidates
  };
}

function validate(result={}){
  const issues=[];
  if(result.ok!==true)issues.push('AGGREGATE_NOT_OK');
  for(const [i,c] of (result.candidates||[]).entries()){
    const p=c.grow_lineage_event?.payload||{};
    if('member_id' in p||'member_ref' in p)issues.push('MEMBER_ID_LEAK:'+i);
    if(c.member_count<Math.max(3,Number(result.min_members)||3))issues.push('K_THRESHOLD_BYPASS:'+i);
    const v=GrowLineage.validateEvent(c.grow_lineage_event||{});
    if(!v.ok)issues.push(...v.issues.map(x=>'LINEAGE:'+i+':'+x));
    if(c.promotion_authorized!==false)issues.push('AUTO_PROMOTION_FORBIDDEN:'+i);
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({aggregate,validate});