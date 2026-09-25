'use strict';

const clean=v=>String(v??'').trim();
const REQUIRED=['event_id','observed_at','member_id','subject','concept_skill_target','evidence_type','source_app','instrument_version'];

function validateEvent(e={}){
  const issues=[];
  for(const k of REQUIRED) if(!clean(e[k])) issues.push('MISSING_'+k.toUpperCase());
  const t=Date.parse(e.observed_at||'');
  if(!Number.isFinite(t)) issues.push('INVALID_OBSERVED_AT');
  if(e.evidence_type==='CHILD_SELF_REPORT'&&e.verified_performance===true) issues.push('SELF_REPORT_CANNOT_BE_VERIFIED_PERFORMANCE');
  return {ok:issues.length===0,issues,time:t};
}

function buildReplayDataset(events=[],options={}){
  const rows=[],invalid=[],seen=new Set(),duplicates=[];
  for(const raw of(Array.isArray(events)?events:[])){
    const e=raw&&typeof raw==='object'?raw:{};
    const v=validateEvent(e);
    if(!v.ok){invalid.push({event_id:clean(e.event_id)||null,issues:v.issues});continue;}
    const id=clean(e.event_id);
    if(seen.has(id)){duplicates.push(id);continue;}
    seen.add(id);
    rows.push({...e,__time:v.time});
  }
  rows.sort((a,b)=>a.__time-b.__time||clean(a.event_id).localeCompare(clean(b.event_id)));

  const grouped=new Map();
  for(const e of rows){
    const key=[clean(e.member_id),clean(e.subject).toLowerCase(),clean(e.concept_skill_target).toLowerCase()].join('::');
    if(!grouped.has(key)) grouped.set(key,[]);
    grouped.get(key).push(e);
  }

  const minTrain=Number.isFinite(options.minimum_train_events)?Math.max(1,Math.floor(options.minimum_train_events)):3;
  const minHeld=Number.isFinite(options.minimum_held_out_events)?Math.max(1,Math.floor(options.minimum_held_out_events)):1;
  const synthetic=options.synthetic===true;
  const groups=[];

  for(const [scope_key,items] of grouped.entries()){
    const flags=[];
    if(items.length<minTrain+minHeld) flags.push('SPARSE_HISTORY');
    if(items.every(x=>x.evidence_type==='CHILD_SELF_REPORT')) flags.push('SELF_REPORT_ONLY');
    if(items.some(x=>x.verified_outcome!==0&&x.verified_outcome!==1)) flags.push('MISSING_VERIFIED_OUTCOME');

    let split=Math.max(minTrain,items.length-minHeld);
    split=Math.min(split,items.length);
    const train=items.slice(0,split);
    const held_out=items.slice(split);

    if(train.length&&held_out.length&&train.at(-1).__time>=held_out[0].__time) flags.push('HELD_OUT_LEAKAGE');

    const instrument_changes=[];
    for(let i=1;i<items.length;i++){
      if(clean(items[i].instrument_version)!==clean(items[i-1].instrument_version)){
        instrument_changes.push({at_event_id:items[i].event_id,from:items[i-1].instrument_version,to:items[i].instrument_version});
      }
    }
    if(instrument_changes.length) flags.push('INSTRUMENT_CHANGE_BOUNDARY');
    if(synthetic) flags.push('SYNTHETIC_ONLY');

    groups.push({
      scope_key,
      member_id:items[0]?.member_id||null,
      subject:items[0]?.subject||null,
      concept_skill_target:items[0]?.concept_skill_target||null,
      event_count:items.length,
      train:train.map(stripInternal),
      held_out:held_out.map(stripInternal),
      instrument_changes,
      quality_flags:[...new Set(flags)].sort()
    });
  }

  return {
    ok:invalid.length===0&&duplicates.length===0,
    dataset_contract:'TAKY_LEARNING_REPLAY_DATASET_V1',
    synthetic,
    promotion_eligible:false,
    invalid_events:invalid,
    duplicate_event_ids:[...new Set(duplicates)].sort(),
    groups,
    summary:{
      accepted_events:rows.length,
      invalid_events:invalid.length,
      duplicate_event_ids:[...new Set(duplicates)].length,
      skill_groups:groups.length,
      promotion_block_reason:synthetic?'SYNTHETIC_ONLY':'HUMAN_REVIEW_REQUIRED'
    }
  };
}

function stripInternal(e){const x={...e};delete x.__time;return x;}

function selfValidate(ds){
  const issues=[];
  if(!ds||ds.dataset_contract!=='TAKY_LEARNING_REPLAY_DATASET_V1') issues.push('CONTRACT_MISSING');
  if(ds?.promotion_eligible!==false) issues.push('AUTO_PROMOTION_FORBIDDEN');
  if((ds?.duplicate_event_ids||[]).length) issues.push('DUPLICATE_EVENT_ID');
  for(const g of ds?.groups||[]){
    const train=g.train||[],held=g.held_out||[];
    if(train.length&&held.length&&Date.parse(train.at(-1).observed_at)>=Date.parse(held[0].observed_at)) issues.push('HELD_OUT_LEAKAGE');
    for(const row of [...train,...held]){
      for(const k of ['schedule_date','planner_date','due_at','due_date']) if(Object.prototype.hasOwnProperty.call(row,k)) issues.push('SCHEDULE_AUTHORITY_LEAK');
    }
  }
  return {ok:issues.length===0,issues};
}

module.exports=Object.freeze({validateEvent,buildReplayDataset,selfValidate});
