(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.TakyLearningEngineCoreV2=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const VERSION='TAKY_LEARNING_ENGINE_CORE_V2_0_2';
  const clean=v=>String(v??'').trim();
  const finite=v=>Number.isFinite(Number(v))?Number(v):null;

  function scopeOf(x={}){
    return {
      member_id:clean(x.member_id),
      subject:clean(x.subject).toLowerCase(),
      concept_skill_target:clean(x.concept_skill_target).toLowerCase()
    };
  }

  function validateEvidence(e={}){
    const required=['event_id','observed_at','member_id','subject','concept_skill_target','evidence_type','source_app','instrument_version'];
    const missing=required.filter(k=>!clean(e[k]));
    return {ok:missing.length===0,missing};
  }

  function evidenceKey(e={}){
    return clean(e.event_id||e.evidence_id);
  }

  function median(values=[]){
    const xs=values.filter(Number.isFinite).slice().sort((a,b)=>a-b);
    if(!xs.length)return null;
    const i=Math.floor(xs.length/2);
    return xs.length%2?xs[i]:(xs[i-1]+xs[i])/2;
  }

  function evidenceSufficiency(count,spacedDays){
    if(count===0)return 'NONE';
    if(count>=5&&spacedDays>=3)return 'ESTABLISHED';
    if(count>=3&&spacedDays>=2)return 'EMERGING';
    return 'SPARSE';
  }

  function hasForbidden(value){
    if(!value||typeof value!=='object')return false;
    for(const [key,nested] of Object.entries(value)){
      if(['schedule_date','planner_date','due_at','due_date','calendar_time'].includes(key))return true;
      if(hasForbidden(nested))return true;
    }
    return false;
  }

  function deriveSkillState(rows=[],scopeInput={},options={}){
    const scope=scopeOf(scopeInput);
    if(!scope.member_id||!scope.subject||!scope.concept_skill_target){
      return {ok:false,reason:'SCOPE_REQUIRED',scope};
    }

    const seen=new Set();
    const accepted=[];
    const invalid=[];

    for(const raw of(Array.isArray(rows)?rows:[])){
      const e=raw&&typeof raw==='object'?raw:{};
      const s=scopeOf(e);
      if(s.member_id!==scope.member_id||s.subject!==scope.subject||s.concept_skill_target!==scope.concept_skill_target)continue;
      const checked=validateEvidence(e);
      if(!checked.ok){invalid.push({event_id:evidenceKey(e)||null,missing:checked.missing});continue;}
      const key=evidenceKey(e);
      if(seen.has(key))continue;
      seen.add(key);
      accepted.push(e);
    }

    accepted.sort((a,b)=>Date.parse(a.observed_at)-Date.parse(b.observed_at)||evidenceKey(a).localeCompare(evidenceKey(b)));

    const spacedDays=new Set(accepted.map(e=>clean(e.observed_at).slice(0,10)).filter(Boolean));
    const instrumentVersions=[...new Set(accepted.map(e=>clean(e.instrument_version)).filter(Boolean))].sort();
    const instrumentChangeDetected=instrumentVersions.length>1;

    const performanceEvidence=accepted.filter(e=>clean(e.evidence_type)!=='CHILD_SELF_REPORT');
    const memoryEvidence=performanceEvidence.filter(e=>clean(e.evidence_type)==='MEMORY_RETRIEVAL_EVIDENCE');
    const memoryStrengths=memoryEvidence.map(e=>finite(e?.memory?.average_strength)).filter(Number.isFinite);
    const latestStrength=memoryStrengths.length?memoryStrengths.at(-1):null;
    const priorMedian=memoryStrengths.length>=3?median(memoryStrengths.slice(0,-1)):null;
    const delta=Number.isFinite(latestStrength)&&Number.isFinite(priorMedian)?latestStrength-priorMedian:null;
    const trendThreshold=Number.isFinite(options.trend_delta_threshold)?Math.max(0,Number(options.trend_delta_threshold)):10;
    const trend=instrumentChangeDetected&&!options.allow_mixed_instruments
      ?'INSTRUMENT_CHANGE_HOLD'
      :!Number.isFinite(delta)
        ?'INSUFFICIENT_EVIDENCE'
        :delta<=-trendThreshold?'DECLINING'
        :delta>=trendThreshold?'IMPROVING'
        :'STABLE';

    const assisted=performanceEvidence.filter(e=>e.assisted===true||clean(e.assistance)==='ASSISTED').length;
    const unassisted=performanceEvidence.filter(e=>e.assisted===false||clean(e.assistance)==='UNASSISTED').length;
    const knownAssistance=assisted+unassisted;
    const assistanceSignal=knownAssistance===0
      ?'UNKNOWN'
      :assisted>unassisted?'ASSISTANCE_DOMINANT':'NOT_ASSISTANCE_DOMINANT';

    const priorities=memoryEvidence.flatMap(e=>Array.isArray(e?.memory?.review_advisories)?e.memory.review_advisories:[])
      .map(x=>finite(x?.nextReviewPriority??x?.priority)).filter(Number.isFinite);

    return {
      ok:true,
      core_version:VERSION,
      scope,
      model:{
        estimator_id:'OBSERVATIONAL_V1',
        estimator_version:'1.1.0',
        mastery_estimate:null,
        mastery_confidence:'UNKNOWN',
        retention_probability:null,
        scheduling_authority:false
      },
      observed:{
        unique_evidence_count:accepted.length,
        performance_evidence_count:performanceEvidence.length,
        spaced_observation_days:spacedDays.size,
        first_observed_at:accepted[0]?.observed_at||null,
        last_observed_at:accepted.at(-1)?.observed_at||null,
        assisted_count:assisted,
        unassisted_count:unassisted,
        child_self_report_count:accepted.filter(e=>clean(e.evidence_type)==='CHILD_SELF_REPORT').length,
        verified_performance_count:performanceEvidence.filter(e=>e.verified_performance===true).length,
        memory_strength_values:memoryStrengths,
        max_review_priority:priorities.length?Math.max(...priorities):null,
        instrument_versions:instrumentVersions,
        source_apps:[...new Set(accepted.map(e=>clean(e.source_app)).filter(Boolean))].sort(),
        evidence_ids:accepted.map(e=>evidenceKey(e))
      },
      inferred:{
        evidence_sufficiency:evidenceSufficiency(performanceEvidence.length,spacedDays.size),
        memory_baseline_median:Number.isFinite(priorMedian)?Math.round(priorMedian*10)/10:null,
        latest_memory_strength:latestStrength,
        memory_delta:Number.isFinite(delta)?Math.round(delta*10)/10:null,
        trend,
        instrument_change_detected:instrumentChangeDetected,
        assistance_dependency_signal:assistanceSignal,
        retention_signal:'MODEL_NOT_BOUND',
        repeated_confusion_signal:'UNMODELED'
      },
      explanation:{
        trend_basis:'latest memory strength vs prior median; disabled across mixed instrument versions unless explicitly allowed',
        mastery_basis:'not estimated until a calibrated estimator is bound',
        scheduling_basis:'Core emits no dated schedule'
      },
      invalid_evidence_count:invalid.length,
      invalid_evidence:invalid,
      policy_provenance:{
        trend_delta_threshold:trendThreshold,
        allow_mixed_instruments:options.allow_mixed_instruments===true
      },
      cannot_influence:['SCHEDULE_DATE','PLANNER_DATE','DUE_AT','DEADLINE','ASSIGNMENT_FACT']
    };
  }

  function selfValidate(state){
    const issues=[];
    if(!state?.ok)issues.push('STATE_NOT_OK');
    if(state?.model?.mastery_estimate!==null)issues.push('UNBOUND_MASTERY_MUST_BE_NULL');
    if(state?.model?.retention_probability!==null)issues.push('UNBOUND_RETENTION_MUST_BE_NULL');
    if(state?.model?.scheduling_authority!==false)issues.push('SCHEDULING_AUTHORITY_MUST_BE_FALSE');
    if(hasForbidden(state))issues.push('SCHEDULE_AUTHORITY_LEAK');
    const ids=state?.observed?.evidence_ids||[];
    if(new Set(ids).size!==ids.length)issues.push('DUPLICATE_EVIDENCE_IDS');
    return {ok:issues.length===0,issues};
  }

  return Object.freeze({
    version:VERSION,
    deriveSkillState,
    selfValidate,
    validateEvidence,
    evidenceKey,
    hasForbidden
  });
});
